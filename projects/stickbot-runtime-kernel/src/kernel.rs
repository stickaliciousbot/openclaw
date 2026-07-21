use crate::journal::EventJournal;
use crate::leases::{Lease, LeaseManager};
use crate::projection::{write_json_atomic, ProjectionWriter};
use crate::types::{HealthColor, KernelHealth, NewRuntimeEvent, RegistryConfig, RestartAuthority, ServiceKind, ServiceStatus, Severity, WorkerHeartbeat, WorkerHeartbeatAck, Ownership};
use anyhow::{bail, Context, Result};
use chrono::{DateTime, Utc};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::collections::BTreeMap;
use std::fs::{self, OpenOptions};
use std::path::{Path, PathBuf};
use std::process::Stdio;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::process::{Child, Command};
use tokio::sync::{broadcast, Mutex, RwLock};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct SupervisedWorkerRuntime {
    pub service_id: String,
    pub lease: Option<Lease>,
    pub expected_pid: Option<u32>,
    pub worker_instance_id: Option<String>,
    pub accepted_heartbeats: u64,
    pub rejected_heartbeats: u64,
    pub duplicate_detected: bool,
    pub restart_attempts: u64,
    pub restart_budget: u64,
    pub quarantined: bool,
}

const POLLER_POLICY_VERSION: &str = "p4e_v1_bounded_retry_hysteresis";
const CONNECT_TIMEOUT_SECONDS: u64 = 2;
const REQUEST_TIMEOUT_SECONDS: u64 = 8;
const MAX_ATTEMPTS_PER_CYCLE: u32 = 2;
const RETRY_BACKOFF_MS: u64 = 500;
const RETRY_JITTER_MS: u64 = 250;
const CRITICAL_FAILURE_CYCLES: u32 = 3;
const RECOVERY_SUCCESS_CYCLES: u32 = 2;
const POLLER_LOCK_FILE: &str = "poller-cycle.lock";
const POLLER_STATE_FILE: &str = "poller-state.json";
const FIXTURE_HEARTBEAT_INTERVAL_MS: u64 = 1_000;
const FIXTURE_HEARTBEAT_LEASE_TTL_MS: i64 = 10_000;
const FIXTURE_HEARTBEAT_RESTART_BUDGET: u64 = 5;
const FIXTURE_HEARTBEAT_RESTART_BACKOFF_MS: u64 = 1_000;

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
struct PollerServiceState {
    consecutive_failed_cycles: u32,
    consecutive_successful_cycles: u32,
    last_success_at: Option<DateTime<Utc>>,
    last_failure_at: Option<DateTime<Utc>>,
    last_color: Option<String>,
}

#[derive(Debug)]
struct PollCycleFileLock {
    path: PathBuf,
}

impl Drop for PollCycleFileLock {
    fn drop(&mut self) {
        let _ = fs::remove_file(&self.path);
    }
}

fn poller_state_path(state_dir: &Path) -> PathBuf {
    state_dir.join(POLLER_STATE_FILE)
}

fn poller_lock_path(state_dir: &Path) -> PathBuf {
    state_dir.join(POLLER_LOCK_FILE)
}

fn load_probe_states(state_dir: &Path) -> BTreeMap<String, PollerServiceState> {
    let path = poller_state_path(state_dir);
    let Ok(data) = fs::read_to_string(path) else { return BTreeMap::new(); };
    serde_json::from_str(&data).unwrap_or_default()
}

fn acquire_poll_cycle_file_lock(state_dir: &Path, poll_interval_ms: u64) -> Result<PollCycleFileLock> {
    fs::create_dir_all(state_dir)?;
    let path = poller_lock_path(state_dir);
    if path.exists() {
        let stale_after = Duration::from_millis((poll_interval_ms * 2).max(30_000));
        let stale = fs::metadata(&path)
            .and_then(|m| m.modified())
            .ok()
            .and_then(|modified| modified.elapsed().ok())
            .map(|age| age > stale_after)
            .unwrap_or(false);
        if stale {
            let _ = fs::remove_file(&path);
        }
    }
    match OpenOptions::new().write(true).create_new(true).open(&path) {
        Ok(mut f) => {
            use std::io::Write;
            writeln!(f, "pid={} acquired_at={}", std::process::id(), Utc::now().to_rfc3339())?;
            Ok(PollCycleFileLock { path })
        }
        Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => {
            bail!("poll_cycle_overlap_rejected lock={}", path.display())
        }
        Err(e) => Err(e).with_context(|| format!("create poll cycle lock {}", path.display())),
    }
}

#[derive(Debug, Clone)]
struct HttpProbeResult {
    ok: bool,
    explicit_unready: bool,
    transport_failure: bool,
    http_status: Option<u16>,
    error_class: String,
    error_detail_code: Option<String>,
    attempts: u32,
    successful_attempt: Option<u32>,
    latency_ms: u128,
    attempt_latencies_ms: Vec<u128>,
}

async fn probe_http(client: &Client, url: &str) -> HttpProbeResult {
    let started = Instant::now();
    let mut attempt_latencies_ms = Vec::new();
    let mut last = HttpProbeResult {
        ok: false,
        explicit_unready: false,
        transport_failure: true,
        http_status: None,
        error_class: "PROBE_CONNECTION_ERROR".into(),
        error_detail_code: Some("not_attempted".into()),
        attempts: 0,
        successful_attempt: None,
        latency_ms: 0,
        attempt_latencies_ms: Vec::new(),
    };
    for attempt in 1..=MAX_ATTEMPTS_PER_CYCLE {
        let attempt_started = Instant::now();
        match client.get(url).send().await {
            Ok(resp) => {
                let status = resp.status();
                let status_u16 = status.as_u16();
                attempt_latencies_ms.push(attempt_started.elapsed().as_millis());
                if !status.is_success() {
                    last = HttpProbeResult {
                        ok: false,
                        explicit_unready: true,
                        transport_failure: false,
                        http_status: Some(status_u16),
                        error_class: "PROBE_EXPLICIT_UNREADY".into(),
                        error_detail_code: Some(format!("http_status_{}", status_u16)),
                        attempts: attempt,
                        successful_attempt: None,
                        latency_ms: started.elapsed().as_millis(),
                        attempt_latencies_ms: attempt_latencies_ms.clone(),
                    };
                }
                else if url.ends_with("/ready") {
                    match resp.text().await {
                        Ok(body) => match serde_json::from_str::<serde_json::Value>(&body) {
                            Ok(json) if json.get("ready").and_then(|v| v.as_bool()) == Some(true) => {
                                return HttpProbeResult { ok: true, explicit_unready: false, transport_failure: false, http_status: Some(status_u16), error_class: "PROBE_SUCCESS".into(), error_detail_code: None, attempts: attempt, successful_attempt: Some(attempt), latency_ms: started.elapsed().as_millis(), attempt_latencies_ms };
                            }
                            Ok(json) => {
                                let failing = json.get("failing").cloned().unwrap_or_else(|| json!([]));
                                last = HttpProbeResult {
                                    ok: false,
                                    explicit_unready: true,
                                    transport_failure: false,
                                    http_status: Some(status_u16),
                                    error_class: "PROBE_EXPLICIT_UNREADY".into(),
                                    error_detail_code: Some(format!("ready_false_or_missing failing={}", failing)),
                                    attempts: attempt,
                                    successful_attempt: None,
                                    latency_ms: started.elapsed().as_millis(),
                                    attempt_latencies_ms: attempt_latencies_ms.clone(),
                                };
                            }
                            Err(e) => {
                                last = HttpProbeResult {
                                    ok: false,
                                    explicit_unready: false,
                                    transport_failure: false,
                                    http_status: Some(status_u16),
                                    error_class: "PROBE_INVALID_RESPONSE".into(),
                                    error_detail_code: Some(format!("ready_json_parse_error:{}", e)),
                                    attempts: attempt,
                                    successful_attempt: None,
                                    latency_ms: started.elapsed().as_millis(),
                                    attempt_latencies_ms: attempt_latencies_ms.clone(),
                                };
                            }
                        },
                        Err(e) => {
                            last = HttpProbeResult { ok: false, explicit_unready: false, transport_failure: false, http_status: Some(status_u16), error_class: "PROBE_INVALID_RESPONSE".into(), error_detail_code: Some(format!("ready_body_read_error:{}", e)), attempts: attempt, successful_attempt: None, latency_ms: started.elapsed().as_millis(), attempt_latencies_ms: attempt_latencies_ms.clone() };
                        }
                    }
                } else {
                    return HttpProbeResult { ok: true, explicit_unready: false, transport_failure: false, http_status: Some(status_u16), error_class: "PROBE_SUCCESS".into(), error_detail_code: None, attempts: attempt, successful_attempt: Some(attempt), latency_ms: started.elapsed().as_millis(), attempt_latencies_ms };
                }
            }
            Err(e) => {
                attempt_latencies_ms.push(attempt_started.elapsed().as_millis());
                let error_class = if e.is_timeout() { "PROBE_TIMEOUT" } else if e.is_connect() { "PROBE_CONNECTION_ERROR" } else { "PROBE_CONNECTION_ERROR" };
                last = HttpProbeResult { ok: false, explicit_unready: false, transport_failure: true, http_status: None, error_class: error_class.into(), error_detail_code: Some(e.to_string()), attempts: attempt, successful_attempt: None, latency_ms: started.elapsed().as_millis(), attempt_latencies_ms: attempt_latencies_ms.clone() };
            }
        }
        if attempt < MAX_ATTEMPTS_PER_CYCLE {
            let jitter = (Utc::now().timestamp_subsec_millis() as u64) % (RETRY_JITTER_MS + 1);
            tokio::time::sleep(Duration::from_millis(RETRY_BACKOFF_MS + jitter)).await;
        }
    }
    last.latency_ms = started.elapsed().as_millis();
    last.attempt_latencies_ms = attempt_latencies_ms;
    last
}

#[derive(Clone)]
pub struct KernelState {
    pub registry: Arc<RegistryConfig>,
    pub journal: EventJournal,
    pub projections: ProjectionWriter,
    services: Arc<RwLock<Vec<ServiceStatus>>>,
    probe_states: Arc<RwLock<BTreeMap<String, PollerServiceState>>>,
    poll_lock: Arc<Mutex<()>>,
    leases: Arc<RwLock<LeaseManager>>,
    supervised: Arc<RwLock<BTreeMap<String, SupervisedWorkerRuntime>>>,
    tx: broadcast::Sender<crate::types::RuntimeEvent>,
}

impl KernelState {
    pub async fn new(registry: RegistryConfig, journal: EventJournal, projections: ProjectionWriter) -> Result<Self> {
        let (tx, _) = broadcast::channel(512);
        let probe_states = load_probe_states(projections.state_dir());
        let statuses = registry.services.iter().map(|s| ServiceStatus {
            id: s.id.clone(),
            display_name: s.display_name.clone(),
            kind: s.kind.clone(),
            critical: s.critical,
            ownership: s.ownership.clone(),
            criticality: s.criticality.clone(),
            write_domain: s.write_domain.clone(),
            restart_authority: s.restart_authority.clone(),
            color: match s.kind {
                ServiceKind::ExternalObserved => HealthColor::ExternalObserved,
                ServiceKind::FixtureSupervised => HealthColor::Yellow,
            },
            live: false,
            ready: false,
            fresh: false,
            degraded_reason: Some("not_checked_yet".into()),
            last_checked: None,
            last_event_seq: None,
            capabilities: s.capabilities.clone(),
            metadata: BTreeMap::new(),
        }).collect();
        let state = Self {
            registry: Arc::new(registry),
            journal,
            projections,
            services: Arc::new(RwLock::new(statuses)),
            probe_states: Arc::new(RwLock::new(probe_states)),
            poll_lock: Arc::new(Mutex::new(())),
            leases: Arc::new(RwLock::new(LeaseManager::default())),
            supervised: Arc::new(RwLock::new(BTreeMap::new())),
            tx,
        };
        let event = state.append_event(NewRuntimeEvent {
            source: "runtime-kernel".into(),
            event_type: "kernel.started".into(),
            service_id: None,
            correlation_id: None,
            severity: Severity::Info,
            payload: json!({"mode": state.registry.kernel.mode}),
            dedupe_key: None,
            schema_version: 1,
        }).await?;
        let _ = event;
        Ok(state)
    }

    pub fn subscribe(&self) -> broadcast::Receiver<crate::types::RuntimeEvent> {
        self.tx.subscribe()
    }

    pub async fn append_event(&self, event: NewRuntimeEvent) -> Result<crate::types::RuntimeEvent> {
        let saved = self.journal.append(event)?;
        self.projections.append_event(&saved)?;
        let _ = self.tx.send(saved.clone());
        Ok(saved)
    }

    pub async fn services(&self) -> Vec<ServiceStatus> {
        self.services.read().await.clone()
    }

    pub async fn supervised_runtime(&self, service_id: &str) -> Option<SupervisedWorkerRuntime> {
        self.supervised.read().await.get(service_id).cloned()
    }

    pub async fn issue_worker_lease(&self, service_id: &str, ttl_ms: i64, restart_budget: u64) -> Result<Lease> {
        let service = self.registry.services.iter().find(|s| s.id == service_id)
            .with_context(|| format!("unknown service_id {}", service_id))?;
        if service.ownership != Ownership::KernelSupervised || service.restart_authority != RestartAuthority::RuntimeKernel {
            bail!("supervision_rejected service_id={} ownership={:?} restart_authority={:?}", service.id, service.ownership, service.restart_authority);
        }
        {
            let supervised = self.supervised.read().await;
            if supervised.get(service_id).map(|s| s.quarantined).unwrap_or(false) {
                bail!("worker_quarantined service_id={}", service_id);
            }
            if supervised.get(service_id).and_then(|s| s.expected_pid).is_some() {
                bail!("duplicate_worker_start_rejected service_id={}", service_id);
            }
        }
        let lease = self.leases.write().await.issue(service_id, ttl_ms);
        let mut supervised = self.supervised.write().await;
        let entry = supervised.entry(service_id.to_string()).or_insert_with(|| SupervisedWorkerRuntime {
            service_id: service_id.to_string(),
            restart_budget,
            ..Default::default()
        });
        entry.lease = Some(lease.clone());
        entry.restart_budget = restart_budget;
        Ok(lease)
    }

    pub async fn register_worker_process(&self, service_id: &str, pid: u32, worker_instance_id: String) -> Result<()> {
        let mut supervised = self.supervised.write().await;
        let entry = supervised.get_mut(service_id).with_context(|| format!("supervised runtime missing for {}", service_id))?;
        if entry.quarantined {
            bail!("worker_quarantined service_id={}", service_id);
        }
        if entry.expected_pid.is_some() {
            entry.duplicate_detected = true;
            bail!("duplicate_worker_detected service_id={}", service_id);
        }
        entry.expected_pid = Some(pid);
        entry.worker_instance_id = Some(worker_instance_id.clone());
        drop(supervised);
        self.append_event(NewRuntimeEvent {
            source: "runtime-kernel".into(),
            event_type: "worker.started".into(),
            service_id: Some(service_id.to_string()),
            correlation_id: Some(worker_instance_id),
            severity: Severity::Info,
            payload: json!({"pid": pid}),
            dedupe_key: None,
            schema_version: 1,
        }).await?;
        Ok(())
    }

    pub async fn record_worker_exit(&self, service_id: &str, pid: u32, exit_reason: &str) -> Result<()> {
        let mut quarantine_now = false;
        {
            let mut supervised = self.supervised.write().await;
            let entry = supervised.get_mut(service_id).with_context(|| format!("supervised runtime missing for {}", service_id))?;
            if entry.expected_pid == Some(pid) {
                entry.expected_pid = None;
            }
            entry.restart_attempts += 1;
            if entry.restart_attempts >= entry.restart_budget {
                entry.quarantined = true;
                quarantine_now = true;
            }
        }
        self.append_event(NewRuntimeEvent {
            source: "runtime-kernel".into(),
            event_type: if quarantine_now { "worker.quarantined" } else { "worker.exited" }.into(),
            service_id: Some(service_id.to_string()),
            correlation_id: None,
            severity: if quarantine_now { Severity::Warn } else { Severity::Info },
            payload: json!({"pid": pid, "reason": exit_reason}),
            dedupe_key: None,
            schema_version: 1,
        }).await?;
        self.update_service_from_supervision(service_id).await?;
        Ok(())
    }

    pub async fn accept_worker_heartbeat(&self, service_id: &str, heartbeat: WorkerHeartbeat) -> WorkerHeartbeatAck {
        let service_known = self.registry.services.iter().any(|s| s.id == service_id);
        if !service_known {
            return WorkerHeartbeatAck { accepted: false, service_id: service_id.to_string(), reason: "unknown_service".into() };
        }
        let lease_result = self.leases.read().await.validate_write(service_id, &heartbeat.lease_id, heartbeat.lease_epoch);
        if let Err(e) = lease_result {
            self.bump_rejected(service_id).await;
            return WorkerHeartbeatAck { accepted: false, service_id: service_id.to_string(), reason: e.to_string() };
        }
        {
            let mut supervised = self.supervised.write().await;
            let Some(entry) = supervised.get_mut(service_id) else {
                return WorkerHeartbeatAck { accepted: false, service_id: service_id.to_string(), reason: "supervised_runtime_missing".into() };
            };
            if entry.quarantined {
                entry.rejected_heartbeats += 1;
                return WorkerHeartbeatAck { accepted: false, service_id: service_id.to_string(), reason: "worker_quarantined".into() };
            }
            if entry.expected_pid != Some(heartbeat.worker_pid) {
                entry.duplicate_detected = true;
                entry.rejected_heartbeats += 1;
                return WorkerHeartbeatAck { accepted: false, service_id: service_id.to_string(), reason: "duplicate_worker_detected".into() };
            }
            entry.accepted_heartbeats += 1;
        }
        let _ = self.mark_service_heartbeat(service_id, &heartbeat).await;
        WorkerHeartbeatAck { accepted: true, service_id: service_id.to_string(), reason: "current_lease_accepted".into() }
    }

    async fn bump_rejected(&self, service_id: &str) {
        let mut supervised = self.supervised.write().await;
        if let Some(entry) = supervised.get_mut(service_id) {
            entry.rejected_heartbeats += 1;
        }
    }

    async fn mark_service_heartbeat(&self, service_id: &str, heartbeat: &WorkerHeartbeat) -> Result<()> {
        let mut statuses = self.services.write().await;
        if let Some(status) = statuses.iter_mut().find(|s| s.id == service_id) {
            status.color = HealthColor::Green;
            status.live = true;
            status.ready = true;
            status.fresh = true;
            status.degraded_reason = None;
            status.last_checked = Some(Utc::now());
            status.metadata.insert("lease_id".into(), json!(heartbeat.lease_id));
            status.metadata.insert("lease_epoch".into(), json!(heartbeat.lease_epoch));
            status.metadata.insert("worker_pid".into(), json!(heartbeat.worker_pid));
            status.metadata.insert("worker_instance_id".into(), json!(heartbeat.worker_instance_id));
        }
        drop(statuses);
        self.write_projection().await?;
        Ok(())
    }

    async fn update_service_from_supervision(&self, service_id: &str) -> Result<()> {
        let supervised = self.supervised.read().await.get(service_id).cloned();
        let mut statuses = self.services.write().await;
        if let Some(status) = statuses.iter_mut().find(|s| s.id == service_id) {
            if supervised.as_ref().map(|s| s.quarantined).unwrap_or(false) {
                status.color = HealthColor::Quarantined;
                status.live = false;
                status.ready = false;
                status.fresh = true;
                status.degraded_reason = Some("restart_budget_exhausted_quarantined".into());
            } else if supervised.as_ref().and_then(|s| s.expected_pid).is_none() {
                status.color = HealthColor::Yellow;
                status.live = false;
                status.ready = false;
                status.fresh = true;
                status.degraded_reason = Some("worker_exited_pending_replacement".into());
            }
        }
        drop(statuses);
        self.write_projection().await?;
        Ok(())
    }

    async fn refresh_fixture_status(&self, service_id: &str) -> Result<()> {
        let supervised = self.supervised.read().await.get(service_id).cloned();
        let mut statuses = self.services.write().await;
        if let Some(status) = statuses.iter_mut().find(|s| s.id == service_id) {
            status.fresh = true;
            status.last_checked = Some(Utc::now());
            status.metadata.insert("supervision_scope".into(), json!("fixture_only"));
            status.metadata.insert("heartbeat_policy".into(), json!("kernel_supervised_child_process"));
            status.metadata.insert("heartbeat_interval_ms".into(), json!(FIXTURE_HEARTBEAT_INTERVAL_MS));
            status.metadata.insert("lease_ttl_ms".into(), json!(FIXTURE_HEARTBEAT_LEASE_TTL_MS));
            status.metadata.insert("restart_budget".into(), json!(FIXTURE_HEARTBEAT_RESTART_BUDGET));
            status.metadata.insert("accepted_heartbeats".into(), json!(supervised.as_ref().map(|s| s.accepted_heartbeats).unwrap_or(0)));
            status.metadata.insert("rejected_heartbeats".into(), json!(supervised.as_ref().map(|s| s.rejected_heartbeats).unwrap_or(0)));
            status.metadata.insert("restart_attempts".into(), json!(supervised.as_ref().map(|s| s.restart_attempts).unwrap_or(0)));
            status.metadata.insert("expected_pid".into(), json!(supervised.as_ref().and_then(|s| s.expected_pid)));
            if supervised.as_ref().map(|s| s.quarantined).unwrap_or(false) {
                status.color = HealthColor::Quarantined;
                status.live = false;
                status.ready = false;
                status.degraded_reason = Some("restart_budget_exhausted_quarantined".into());
            } else if supervised.as_ref().map(|s| s.expected_pid.is_some() && s.accepted_heartbeats > 0).unwrap_or(false) {
                status.color = HealthColor::Green;
                status.live = true;
                status.ready = true;
                status.degraded_reason = None;
            } else if supervised.as_ref().and_then(|s| s.expected_pid).is_some() {
                status.color = HealthColor::Yellow;
                status.live = true;
                status.ready = false;
                status.degraded_reason = Some("worker_started_awaiting_heartbeat".into());
            } else {
                status.color = HealthColor::Yellow;
                status.live = false;
                status.ready = false;
                status.degraded_reason = Some("fixture_worker_not_started".into());
            }
        }
        Ok(())
    }

    async fn start_heartbeat_worker_process(&self, service_id: &str, runtime_url: &str) -> Result<Child> {
        let lease = self.issue_worker_lease(service_id, FIXTURE_HEARTBEAT_LEASE_TTL_MS, FIXTURE_HEARTBEAT_RESTART_BUDGET).await?;
        let exe = std::env::current_exe()?;
        let mut cmd = Command::new(exe);
        cmd.arg("heartbeat-worker")
            .env("STICK_SERVICE_ID", service_id)
            .env("STICK_LEASE_ID", &lease.lease_id)
            .env("STICK_LEASE_EPOCH", lease.epoch.to_string())
            .env("STICK_RUNTIME_URL", runtime_url)
            .env("STICK_HEARTBEAT_INTERVAL_MS", FIXTURE_HEARTBEAT_INTERVAL_MS.to_string())
            .env("STICK_LEASE_TTL_MS", FIXTURE_HEARTBEAT_LEASE_TTL_MS.to_string())
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .kill_on_drop(true);
        let child = cmd.spawn().context("spawn runtime-heartbeat-worker")?;
        let pid = child.id().context("spawned worker pid")?;
        self.register_worker_process(service_id, pid, format!("managed_{}", Uuid::new_v4().simple())).await?;
        Ok(child)
    }

    pub fn spawn_supervised_fixture_workers(&self, runtime_url: String) {
        let service_ids: Vec<String> = self.registry.services.iter()
            .filter(|s| s.kind == ServiceKind::FixtureSupervised
                && s.ownership == Ownership::KernelSupervised
                && s.restart_authority == RestartAuthority::RuntimeKernel)
            .map(|s| s.id.clone())
            .collect();
        for service_id in service_ids {
            let state = self.clone();
            let runtime_url = runtime_url.clone();
            tokio::spawn(async move {
                tokio::time::sleep(Duration::from_millis(250)).await;
                loop {
                    if state.supervised_runtime(&service_id).await.map(|s| s.quarantined).unwrap_or(false) {
                        break;
                    }
                    match state.start_heartbeat_worker_process(&service_id, &runtime_url).await {
                        Ok(mut child) => {
                            let pid = child.id();
                            let exit_reason = match child.wait().await {
                                Ok(status) => format!("heartbeat_worker_exit_status={}", status),
                                Err(e) => format!("heartbeat_worker_wait_error={}", e),
                            };
                            if let Some(pid) = pid {
                                let _ = state.record_worker_exit(&service_id, pid, &exit_reason).await;
                            }
                        }
                        Err(e) => {
                            let _ = state.append_event(NewRuntimeEvent {
                                source: "runtime-kernel".into(),
                                event_type: "worker.start_failed".into(),
                                service_id: Some(service_id.clone()),
                                correlation_id: None,
                                severity: Severity::Warn,
                                payload: json!({"error": e.to_string(), "supervision_scope": "fixture_only"}),
                                dedupe_key: None,
                                schema_version: 1,
                            }).await;
                        }
                    }
                    tokio::time::sleep(Duration::from_millis(FIXTURE_HEARTBEAT_RESTART_BACKOFF_MS)).await;
                }
            });
        }
    }

    pub async fn health(&self) -> KernelHealth {
        let services = self.services.read().await;
        let mut green = 0;
        let mut yellow = 0;
        let mut red = 0;
        let mut quarantined = 0;
        let mut critical_red = 0;
        for s in services.iter() {
            match s.color {
                HealthColor::Green | HealthColor::ExternalObserved if s.live && s.ready => green += 1,
                HealthColor::Yellow | HealthColor::ExternalObserved => yellow += 1,
                HealthColor::Red => {
                    red += 1;
                    if s.critical { critical_red += 1; }
                }
                HealthColor::Quarantined => quarantined += 1,
                HealthColor::Green => green += 1,
            }
        }
        let status = if critical_red > 0 {
            HealthColor::Red
        } else if red > 0 || yellow > 0 || quarantined > 0 {
            HealthColor::Yellow
        } else {
            HealthColor::Green
        };
        KernelHealth {
            kernel_id: self.registry.kernel.id.clone(),
            status,
            mode: self.registry.kernel.mode.clone(),
            services_total: services.len(),
            services_green: green,
            services_yellow: yellow,
            services_red: red,
            services_quarantined: quarantined,
            critical_red,
            event_journal_writable: self.journal.last_seq().is_ok(),
            projection_writable: self.projections.state_dir().exists(),
            last_event_seq: self.journal.last_seq().unwrap_or(0),
            generated_at: Utc::now(),
        }
    }

    pub async fn write_projection(&self) -> Result<()> {
        let health = self.health().await;
        let services = self.services().await;
        self.projections.write_health(&health, &services)
    }

    async fn save_probe_states(&self) -> Result<()> {
        let states = self.probe_states.read().await.clone();
        write_json_atomic(&poller_state_path(self.projections.state_dir()), &states)
    }

    pub async fn poll_once(&self) -> Result<()> {
        let _memory_guard = match self.poll_lock.try_lock() {
            Ok(guard) => guard,
            Err(_) => {
                let _ = self.append_event(NewRuntimeEvent {
                    source: "runtime-kernel".into(),
                    event_type: "health.poll_skipped".into(),
                    service_id: None,
                    correlation_id: None,
                    severity: Severity::Warn,
                    payload: json!({"reason":"poll_cycle_overlap_rejected", "policy_version": POLLER_POLICY_VERSION}),
                    dedupe_key: None,
                    schema_version: 1,
                }).await;
                return Ok(());
            }
        };
        let _file_guard = match acquire_poll_cycle_file_lock(self.projections.state_dir(), self.registry.kernel.poll_interval_ms) {
            Ok(guard) => guard,
            Err(e) => {
                let _ = self.append_event(NewRuntimeEvent {
                    source: "runtime-kernel".into(),
                    event_type: "health.poll_skipped".into(),
                    service_id: None,
                    correlation_id: None,
                    severity: Severity::Warn,
                    payload: json!({"reason":"poll_cycle_overlap_rejected", "error": e.to_string(), "policy_version": POLLER_POLICY_VERSION}),
                    dedupe_key: None,
                    schema_version: 1,
                }).await;
                return Ok(());
            }
        };
        let cycle_started_at = Utc::now();
        let cycle_started_instant = Instant::now();
        let client = Client::builder()
            .connect_timeout(Duration::from_secs(CONNECT_TIMEOUT_SECONDS))
            .timeout(Duration::from_secs(REQUEST_TIMEOUT_SECONDS))
            .build()?;
        let services = self.registry.services.iter().cloned().collect::<Vec<_>>();
        for service in services {
            if service.kind == ServiceKind::FixtureSupervised {
                self.refresh_fixture_status(&service.id).await?;
                continue;
            }
            let Some(url) = service.health_url.clone() else { continue; };
            let checked_at = Utc::now();
            let probe = probe_http(&client, &url).await;
            let mut statuses = self.services.write().await;
            let mut probe_states = self.probe_states.write().await;
            let Some(status) = statuses.iter_mut().find(|s| s.id == service.id) else { continue; };
            let state = probe_states.entry(status.id.clone()).or_default();
            let previous_color = status.color.clone();
            let previous_failed_cycles = state.consecutive_failed_cycles;
            let max_last_success_age_seconds = (30_i64).max(((self.registry.kernel.poll_interval_ms * 3) / 1000) as i64);
            let last_success_age_seconds = state.last_success_at.map(|ts| (checked_at - ts).num_seconds().max(0));
            let last_success_stale = last_success_age_seconds.map(|age| age > max_last_success_age_seconds).unwrap_or(false);
            let has_bounded_last_known_good = state.last_success_at.is_some() && !last_success_stale;

            status.metadata.insert("probe_attempts".into(), json!(probe.attempts));
            status.metadata.insert("successful_attempt".into(), json!(probe.successful_attempt));
            status.metadata.insert("latency_ms".into(), json!(probe.latency_ms));
            status.metadata.insert("attempt_latencies_ms".into(), json!(probe.attempt_latencies_ms));
            status.metadata.insert("error_class".into(), json!(probe.error_class));
            status.metadata.insert("error_detail_code".into(), json!(probe.error_detail_code));
            status.metadata.insert("health_url".into(), json!(url));
            status.metadata.insert("policy_version".into(), json!(POLLER_POLICY_VERSION));
            status.metadata.insert("configured_connect_timeout_seconds".into(), json!(CONNECT_TIMEOUT_SECONDS));
            status.metadata.insert("configured_timeout_seconds".into(), json!(REQUEST_TIMEOUT_SECONDS));
            status.metadata.insert("configured_max_attempts".into(), json!(MAX_ATTEMPTS_PER_CYCLE));
            status.metadata.insert("retry_backoff_ms".into(), json!(RETRY_BACKOFF_MS));
            status.metadata.insert("retry_jitter_ms".into(), json!(RETRY_JITTER_MS));
            status.metadata.insert("critical_failure_cycles".into(), json!(CRITICAL_FAILURE_CYCLES));
            status.metadata.insert("recovery_success_cycles".into(), json!(RECOVERY_SUCCESS_CYCLES));
            status.metadata.insert("max_last_success_age_seconds".into(), json!(max_last_success_age_seconds));
            status.metadata.insert("poll_cycle_started_at".into(), json!(cycle_started_at));
            status.metadata.insert("producer_identity".into(), json!("stickbot-runtime-kernel:poll_once"));
            if let Some(http_status) = probe.http_status {
                status.metadata.insert("http_status".into(), json!(http_status));
            } else {
                status.metadata.remove("http_status");
            }
            if probe.ok {
                state.consecutive_failed_cycles = 0;
                state.consecutive_successful_cycles += 1;
                state.last_success_at = Some(checked_at);
                status.live = true;
                status.ready = true;
                status.fresh = true;
                if previous_failed_cycles > 0 && state.consecutive_successful_cycles < RECOVERY_SUCCESS_CYCLES {
                    status.color = HealthColor::Yellow;
                    status.degraded_reason = Some("GATEWAY_READINESS_RECOVERY_CONFIRMING".into());
                } else {
                    status.color = HealthColor::ExternalObserved;
                    status.degraded_reason = None;
                }
            } else {
                state.consecutive_failed_cycles += 1;
                state.consecutive_successful_cycles = 0;
                state.last_failure_at = Some(checked_at);
                status.ready = false;
                status.fresh = true;
                if status.id == "telegram-channel" || !service.critical {
                    status.live = probe.http_status.is_some();
                    status.color = HealthColor::Yellow;
                    status.degraded_reason = Some(if status.id == "telegram-channel" { "TELEGRAM_ADVISORY_PROBE_ERROR" } else { "NONCRITICAL_PROBE_ERROR" }.into());
                    status.metadata.insert("independent_telegram_health_proven".into(), json!(false));
                } else if probe.explicit_unready {
                    status.live = probe.http_status.is_some();
                    status.color = HealthColor::Red;
                    status.degraded_reason = Some("GATEWAY_READINESS_EXPLICIT_UNREADY_CONFIRMED".into());
                } else if probe.transport_failure || probe.error_class == "PROBE_INVALID_RESPONSE" {
                    let sustained = state.consecutive_failed_cycles >= CRITICAL_FAILURE_CYCLES || last_success_stale;
                    status.live = has_bounded_last_known_good || probe.http_status.is_some();
                    status.ready = has_bounded_last_known_good && !sustained;
                    if sustained {
                        status.color = HealthColor::Red;
                        status.degraded_reason = Some(if last_success_stale { "PROBE_STALE_LAST_SUCCESS" } else { "GATEWAY_READINESS_SUSTAINED_PROBE_FAILURE" }.into());
                    } else {
                        status.color = HealthColor::Yellow;
                        status.degraded_reason = Some(if state.consecutive_failed_cycles == 1 { "GATEWAY_READINESS_TRANSIENT_PROBE_ERROR" } else { "GATEWAY_READINESS_PROBE_FAILURE_CONFIRMING" }.into());
                    }
                } else {
                    status.live = probe.http_status.is_some();
                    status.color = if service.critical { HealthColor::Red } else { HealthColor::Yellow };
                    status.degraded_reason = Some("PROBE_INVALID_RESPONSE".into());
                }
            }
            state.last_color = Some(format!("{:?}", status.color));
            status.metadata.insert("consecutive_failed_cycles".into(), json!(state.consecutive_failed_cycles));
            status.metadata.insert("consecutive_successful_cycles".into(), json!(state.consecutive_successful_cycles));
            status.metadata.insert("last_success_at".into(), json!(state.last_success_at));
            status.metadata.insert("last_success_age_seconds".into(), json!(last_success_age_seconds));
            status.metadata.insert("last_failure_at".into(), json!(state.last_failure_at));
            status.metadata.insert("using_last_known_good".into(), json!(has_bounded_last_known_good && !probe.ok && status.ready));
            status.metadata.insert("freshness_state".into(), json!(if last_success_stale { "stale_last_success" } else { "fresh" }));
            status.metadata.insert("state_transition".into(), json!(format!("{:?}->{:?}", previous_color, status.color)));
            status.metadata.insert("state_transition_reason".into(), json!(status.degraded_reason));
            status.last_checked = Some(checked_at);
        }
        self.save_probe_states().await?;
        let cycle_completed_at = Utc::now();
        let cycle_duration_ms = cycle_started_instant.elapsed().as_millis();
        let event = self.append_event(NewRuntimeEvent {
            source: "runtime-kernel".into(),
            event_type: "health.polled".into(),
            service_id: None,
            correlation_id: None,
            severity: Severity::Info,
            payload: json!({
                "services": self.services().await.len(),
                "poll_cycle_started_at": cycle_started_at,
                "poll_cycle_completed_at": cycle_completed_at,
                "poll_cycle_duration_ms": cycle_duration_ms,
                "producer_identity": "stickbot-runtime-kernel:poll_once",
                "policy_version": POLLER_POLICY_VERSION,
                "configured_connect_timeout_seconds": CONNECT_TIMEOUT_SECONDS,
                "configured_timeout_seconds": REQUEST_TIMEOUT_SECONDS,
                "configured_max_attempts": MAX_ATTEMPTS_PER_CYCLE,
            }),
            dedupe_key: None,
            schema_version: 1,
        }).await?;
        let mut statuses = self.services.write().await;
        for s in statuses.iter_mut() {
            s.last_event_seq = Some(event.seq);
        }
        drop(statuses);
        self.write_projection().await?;
        Ok(())
    }

    pub fn spawn_poll_loop(&self) {
        let state = self.clone();
        let interval_ms = state.registry.kernel.poll_interval_ms;
        tokio::spawn(async move {
            let mut interval = tokio::time::interval(std::time::Duration::from_millis(interval_ms));
            loop {
                interval.tick().await;
                let _ = state.poll_once().await;
            }
        });
    }
}
