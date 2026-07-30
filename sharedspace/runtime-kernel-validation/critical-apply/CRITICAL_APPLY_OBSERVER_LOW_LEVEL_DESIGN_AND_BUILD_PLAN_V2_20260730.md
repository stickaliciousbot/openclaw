# Critical Apply Observer v2.0 — Low-Level Design, Contract, and Universal Runtime Kernel Build Plan

**Date:** 2026-07-30  
**Owner context:** Stick / Stickbot OpenClaw runtime operations  
**Status:** DESIGN CONTRACT — no production mutation authorised  
**Architecture dependency:** `critical-apply-observation-harness-architecture-v2.0-2026-07-30.md`

## 0. Purpose and acceptance posture

This document converts the locked critical-apply architecture into an implementable, testable contract suitable for completing the remaining Universal Runtime Kernel work.

The initial production plugin remains OpenClaw global npm package apply/recovery. The core, however, is designed as a reusable mutation kernel for later Gateway restart, config, guarded cron, protected-memory writer, and route/model operations.

Nothing in this document authorises a live deploy, install, restart, cron mutation, provider call, package mutation, or protected-memory change.

## 1. Non-negotiable rules

1. No critical production mutation is governed by foreground chat/session execution.
2. Production requires Harness Resiliency Level 3 (HRL-3).
3. The observer is a pre-existing supervisor-managed service, not `nohup`, `disown`, ad hoc `setsid`, a background shell, or a raw detached subprocess.
4. Mutation child release occurs only after durable intent, spawn, authority-consumption, and final precondition receipts.
5. A command exit code is evidence, not system truth.
6. Restore eligibility is checked at mutation release. It does not expire mid-transaction.
7. Automatic recovery is bounded to the exact recovery write set and occurs at most once.
8. Package apply, Gateway restart, and functional smoke are separate transactions and approvals.
9. No unknown state is converted to PASS.
10. If the critical apply service or plugin is absent, stale, unsealed, or unproven, stop at preparation.

## 2. Threat and failure model

The implementation SHALL assume:

- initiating chat, terminal, or tool call can disappear at any time;
- the observer process can be SIGKILLed;
- WSL or the host can reboot mid-phase;
- PID reuse can occur;
- system clock can jump;
- stdout/stderr can be huge or truncated in chat;
- filesystem writes can be partial or fail with `ENOSPC`;
- restore artifacts can be stale, substituted, corrupt, or path-unsafe;
- candidate package, runner code, plugin code, or pre-state can change after approval;
- npm can exit nonzero after moving or partially replacing the official root;
- npm can leave hidden `.openclaw-*` generations;
- Gateway can continue running from a prior or hidden generation;
- a child can fork descendants;
- unrelated cron, memory, route, config, or global-package state can drift;
- an interrupted recovery can be retried accidentally;
- a malicious or accidental manual edit can alter evidence;
- service-manager user-session infrastructure can be unavailable.

The contract SHALL make every one of these states classifiable and fail closed.

## 3. Runtime topology

### 3.1 Production components

```text
foreground assistant / operator
        |
        | prepare, approve, status only
        v
critical_apply_ctl.py
        |
        | Unix domain socket / sealed inbox
        v
openclaw-critical-apply.service
  critical_applyd.py
        |
        +-- transaction journal/projections
        +-- global and surface lock manager
        +-- supervisor adapter
        +-- transaction worker
              |
              +-- blocked child launch gate
              +-- exact argv exec
              +-- stdout/stderr files
              +-- postcheck/recovery
```

The system service SHALL run under the intended OpenClaw filesystem identity, or under a tightly scoped privileged helper model. It SHALL use the system service manager, not the per-user systemd session bus.

### 3.2 Supervisor service requirements

Recommended system-unit properties:

```ini
[Service]
Type=simple
User=stickai
Group=stickai
UMask=0077
ExecStart=/usr/bin/python3 /home/stickai/.openclaw/workspace/scripts/critical_applyd.py
Restart=on-failure
RestartSec=2
KillMode=control-group
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/home/stickai/.openclaw/artifacts/critical-apply
ReadWritePaths=/home/stickai/.openclaw/locks
ReadWritePaths=/home/stickai/.openclaw/restore-points
ReadWritePaths=/home/stickai/.npm-global/lib/node_modules
ReadWritePaths=/home/stickai/.npm-global/bin
```

The exact hardening profile must be validated against required paths before installation. The unit file and all executable dependencies are checksum-bound to approval.

### 3.3 Bootstrap contract

Installing or enabling the service is a separate `CRITICAL_APPLY_BOOTSTRAP` milestone governed by the previously proven parent-thread observation harness. It may mutate only:

- the critical-apply code installation path;
- its system service unit and approved service-manager metadata;
- its evidence/lock/restore directories.

It may not mutate OpenClaw package, Gateway, cron, protected memory, routes, provider state, or delivery surfaces.

The bootstrap transaction must itself have a restore point and rollback instructions. Production OpenClaw mutation remains blocked until the service survives a forced observer failure and rehydrates correctly.

## 4. Repository and code deliverables

```text
scripts/
  critical_apply_ctl.py
  critical_applyd.py
  critical_apply_worker.py
  critical_apply_contracts.py
  critical_apply_journal.py
  critical_apply_atomic_io.py
  critical_apply_authority.py
  critical_apply_locking.py
  critical_apply_process.py
  critical_apply_manifest.py
  critical_apply_reconcile.py
  critical_apply_check.py
  critical_apply_plugins/
    __init__.py
    base.py
    openclaw_npm_package.py
    filesystem_restore.py
    gateway_restart.py                 # later promotion
    gateway_config_apply.py            # later promotion
    cron_guarded_update.py             # later promotion
    protected_memory_writer_state.py   # later promotion
    model_route_apply.py               # later promotion
  tests/
    fixtures/
    test_contracts.py
    test_journal.py
    test_atomic_io.py
    test_authority.py
    test_locking.py
    test_process_gate.py
    test_reconcile.py
    test_restore_points.py
    test_openclaw_npm_package.py
    test_recovery_matrix.py
    test_boundary_separation.py
    test_shadow_end_to_end.py
```

Documentation:

```text
sharedspace/runtime-kernel-validation/critical-apply/
  CRITICAL_APPLY_ARCHITECTURE_V2.md
  CRITICAL_APPLY_CONTRACT_V2.md
  CRITICAL_APPLY_OPERATOR_RUNBOOK_V2.md
  CRITICAL_APPLY_THREAT_MODEL_V2.md
  CRITICAL_APPLY_BOOTSTRAP_PLAN_V2.md
  CRITICAL_APPLY_PLUGIN_AUTHORING_GUIDE_V2.md
```

## 5. Filesystem layout

```text
/home/stickai/.openclaw/
  artifacts/critical-apply/<transaction-id>/
  restore-points/critical-apply/<restore-id>/
  locks/critical-apply.global.lock
  locks/critical-apply-surfaces/
  runtime/critical-apply/
```

Transaction directory:

```text
<transaction-id>/
  spec/
    transaction-spec.json
    scope.json
    candidate-authority.json
    recovery-policy.json
    resource-policy.json
    environment-policy.json
  authority/
    approval-boundary.json
    approval-receipt.json
    approval-consumed.json
  journal/
    events.jsonl
    journal-head.json
  receipts/
    prepare.json
    restore-point.json
    precheck.json
    plan-seal.json
    commit-locks.json
    commit-revalidation.json
    apply-intent.json
    apply-spawned-blocked.json
    apply-release.json
    apply-exit.json
    postcheck.json
    recovery-decision.json
    recovery-intent.json
    recovery-action.json
    post-recovery-check.json
    runner-error.json
    final-report.json
  projections/
    transaction.json
    status.json
  logs/
    apply.stdout.log
    apply.stderr.log
    recovery.stdout.log
    recovery.stderr.log
    observer.log
  manifests/
    evidence-manifest.json
    evidence-manifest.sha256
    terminal-seal.json
```

All directories use mode `0700`; files use `0600`; umask is `077`.

## 6. Core data contracts

### 6.1 Transaction ID and campaign ID

```text
critical-apply-<plugin>-<YYYYMMDDTHHMMSSZ>-<random128>
critical-campaign-<purpose>-<YYYYMMDDTHHMMSSZ>-<random128>
```

Random suffixes must provide at least 128 bits of entropy. IDs are never reused.

### 6.2 Transaction phase enum

```python
class Phase(str, Enum):
    CREATED = "CREATED"
    PREPARING = "PREPARING"
    RESTORE_POINT_READY = "RESTORE_POINT_READY"
    PRECHECK_PASS = "PRECHECK_PASS"
    PLAN_SEALED = "PLAN_SEALED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVAL_RECORDED = "APPROVAL_RECORDED"
    COMMIT_LOCKS_ACQUIRED = "COMMIT_LOCKS_ACQUIRED"
    COMMIT_REVALIDATING = "COMMIT_REVALIDATING"
    COMMIT_VALIDATED = "COMMIT_VALIDATED"
    APPLY_INTENT_DURABLE = "APPLY_INTENT_DURABLE"
    APPLY_CHILD_SPAWNED_BLOCKED = "APPLY_CHILD_SPAWNED_BLOCKED"
    MUTATION_RELEASED = "MUTATION_RELEASED"
    APPLY_RUNNING = "APPLY_RUNNING"
    APPLY_EXIT_OBSERVED = "APPLY_EXIT_OBSERVED"
    APPLY_EXIT_UNKNOWN = "APPLY_EXIT_UNKNOWN"
    POSTCHECK_RUNNING = "POSTCHECK_RUNNING"
    RECOVERY_DECIDING = "RECOVERY_DECIDING"
    RECOVERY_INTENT_DURABLE = "RECOVERY_INTENT_DURABLE"
    RECOVERY_RUNNING = "RECOVERY_RUNNING"
    POST_RECOVERY_CHECK = "POST_RECOVERY_CHECK"
    FINALIZING = "FINALIZING"
    TERMINAL = "TERMINAL"
```

### 6.3 Terminal enum

```python
class Terminal(str, Enum):
    CANCELLED_NO_APPROVAL = "CANCELLED_NO_APPROVAL"
    APPROVAL_EXPIRED_REPREPARE_REQUIRED = "APPROVAL_EXPIRED_REPREPARE_REQUIRED"
    APPROVED_NOT_STARTED = "APPROVED_NOT_STARTED"
    PRECONDITION_DRIFT_BLOCKED = "PRECONDITION_DRIFT_BLOCKED"
    APPLY_STATE_UNKNOWN_OPERATOR_REQUIRED = "APPLY_STATE_UNKNOWN_OPERATOR_REQUIRED"
    FAIL_SAFE_NO_MUTATION = "FAIL_SAFE_NO_MUTATION"
    APPLY_EFFECTIVE_EXIT_NONZERO_HOLD = "APPLY_EFFECTIVE_EXIT_NONZERO_HOLD"
    PASS_PACKAGE_INSTALLED_HOLD_FOR_SEPARATE_RESTART = "PASS_PACKAGE_INSTALLED_HOLD_FOR_SEPARATE_RESTART"
    FAIL_MUTATION_PARTIAL_RECOVERY_REQUIRED = "FAIL_MUTATION_PARTIAL_RECOVERY_REQUIRED"
    RECOVERY_PASS_HOLD_FOR_SEPARATE_RESTART = "RECOVERY_PASS_HOLD_FOR_SEPARATE_RESTART"
    RECOVERY_PASS_WITH_GUARD_WARNING_OPERATOR_HOLD = "RECOVERY_PASS_WITH_GUARD_WARNING_OPERATOR_HOLD"
    RECOVERY_BLOCKED_STATE_UNKNOWN = "RECOVERY_BLOCKED_STATE_UNKNOWN"
    ROLLBACK_FAIL_OPERATOR_REQUIRED = "ROLLBACK_FAIL_OPERATOR_REQUIRED"
    EVIDENCE_TAMPERED_OR_INCOMPLETE_HOLD = "EVIDENCE_TAMPERED_OR_INCOMPLETE_HOLD"
    PASS_CONTROLLED_GATEWAY_RESTART = "PASS_CONTROLLED_GATEWAY_RESTART"
    PASS_FUNCTIONAL_SMOKE = "PASS_FUNCTIONAL_SMOKE"
    FUNCTIONAL_SMOKE_FAIL_NO_PACKAGE_RECOVERY = "FUNCTIONAL_SMOKE_FAIL_NO_PACKAGE_RECOVERY"
```

### 6.4 State-vector enums

```python
class ExecutionState(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    RUNNING = "RUNNING"
    EXIT_ZERO = "EXIT_ZERO"
    EXIT_NONZERO = "EXIT_NONZERO"
    SIGNALLED = "SIGNALLED"
    TIMEOUT_KILLED = "TIMEOUT_KILLED"
    EXIT_UNKNOWN = "EXIT_UNKNOWN"

class OfficialPackageState(str, Enum):
    MISSING = "MISSING"
    EMPTY = "EMPTY"
    INCOMPLETE = "INCOMPLETE"
    COHERENT_PRE_GENERATION = "COHERENT_PRE_GENERATION"
    COHERENT_CANDIDATE_GENERATION = "COHERENT_CANDIDATE_GENERATION"
    COHERENT_OTHER_GENERATION = "COHERENT_OTHER_GENERATION"
    UNKNOWN = "UNKNOWN"

class PackageSubstrateState(str, Enum):
    COHERENT = "COHERENT"
    DEGRADED = "DEGRADED"
    BROKEN = "BROKEN"
    UNKNOWN = "UNKNOWN"

class GuardState(str, Enum):
    UNCHANGED = "UNCHANGED"
    ALLOWED_DRIFT = "ALLOWED_DRIFT"
    FORBIDDEN_DRIFT = "FORBIDDEN_DRIFT"
    UNKNOWN = "UNKNOWN"

class RecoveryState(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    AUTHORISED_PENDING = "AUTHORISED_PENDING"
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    NOT_AUTHORISED = "NOT_AUTHORISED"
```

Terminal classification is a pure function of the complete state vector and policy. Plugins may contribute facts but may not directly assert PASS.

## 7. Journal and atomic I/O

### 7.1 Event schema

```json
{
  "schema": "critical_apply.event.v2",
  "transaction_id": "critical-apply-openclaw-npm-package-...",
  "sequence": 42,
  "event_type": "MUTATION_RELEASED",
  "phase": "APPLY_RUNNING",
  "wall_time_utc": "2026-07-30T06:25:00.000000Z",
  "monotonic_ns": 1234567890,
  "boot_id": "...",
  "actor": {
    "component": "critical_apply_worker",
    "pid": 1234,
    "start_ticks": 5678,
    "uid": 1001
  },
  "payload_path": "receipts/apply-release.json",
  "payload_sha256": "...",
  "previous_event_sha256": "...",
  "event_sha256": "..."
}
```

Event hash is computed over canonical JSON excluding `event_sha256`.

### 7.2 Atomic write API

```python
def atomic_write_json(
    path: Path,
    value: Mapping[str, Any],
    *,
    mode: int = 0o600,
    fsync_parent: bool = True,
) -> ArtifactDigest: ...
```

Implementation requirements:

- create with `O_CREAT|O_EXCL|O_NOFOLLOW`;
- write canonical UTF-8 JSON;
- reject NaN/Infinity and duplicate keys;
- `fsync` file;
- atomic `renameat`;
- `fsync` parent;
- verify final inode is regular file;
- return SHA-256, bytes, inode, device.

### 7.3 Journal append API

Journal append uses a single-writer lock, validates the prior head, appends one newline-terminated canonical event, `fdatasync`s, then atomically updates `journal-head.json`.

A torn final line is never ignored silently. Reconciliation reports it and recovers only to the last sealed event when that is provably safe.

### 7.4 Projection rules

`projections/transaction.json` and `status.json` are rebuilt from the journal. Manual changes are detected as projection mismatch. Readers must not trust projections without journal validation.

### 7.5 Terminal seal

`terminal-seal.json` contains:

```json
{
  "schema": "critical_apply.terminal_seal.v2",
  "transaction_id": "...",
  "terminal": "...",
  "journal_head_sha256": "...",
  "evidence_manifest_sha256": "...",
  "runner_code_bundle_sha256": "...",
  "sealed_at_utc": "...",
  "boot_id": "..."
}
```

The evidence manifest excludes itself, its sidecar hash, and terminal seal from its governed list to avoid circularity. The seal then binds those final hashes.

## 8. Authority and approval

### 8.1 Authority envelope schema

```json
{
  "schema": "critical_apply.authority_envelope.v2",
  "transaction_id": "...",
  "campaign_id": "...",
  "owner": "Stick",
  "approval_nonce": "...",
  "issued_at_utc": "...",
  "expires_at_utc": "...",
  "transaction_spec_sha256": "...",
  "runner_bundle_sha256": "...",
  "plugin_bundle_sha256": "...",
  "interpreter_identity_sha256": "...",
  "supervisor_unit_sha256": "...",
  "candidate_authority_sha256": "...",
  "apply_exec_spec_sha256": "...",
  "restore_point_id": "...",
  "restore_manifest_sha256": "...",
  "restore_method": "filesystem_atomic_restore",
  "surface_sets_sha256": "...",
  "resource_policy_sha256": "...",
  "network_policy_sha256": "...",
  "recovery_policy_sha256": "...",
  "restart_authorised": false,
  "functional_smoke_authorised": false,
  "max_primary_mutations": 1,
  "max_automatic_recoveries": 1
}
```

### 8.2 Approval receipt

Approval receipt must bind the authority-envelope hash and exact approval phrase or trusted approval event identity. It includes one-time nonce and expiry.

### 8.3 Approval consumption

Approval is consumed in an atomic compare-and-swap operation immediately before mutation release. If consumption cannot be durably proven, the gate remains closed.

A transaction with a consumed approval SHALL never launch a second primary mutation.

### 8.4 Drift invalidation

The following require reprepare and reapproval:

- candidate hash/path/version/source commit changes;
- runner, plugin, contracts, interpreter, or unit hash changes;
- restore-point ID or manifest changes;
- restore point is stale at mutation release;
- official package pre-state fingerprint changes;
- guard baseline changes outside signed allowed drift;
- executable path or npm prefix changes;
- transaction spec, argv, env policy, timeout, network policy, or recovery policy changes;
- host/boot/mount identity changes where policy requires same-boot execution.

## 9. Locking and concurrency

### 9.1 Lock order

```text
global critical-apply lock
  -> package-manager/global-prefix lock
  -> plugin surface locks in lexicographic canonical order
  -> transaction-local journal lock
```

Acquiring out of order is a contract error.

### 9.2 Lock implementation

Use a held `flock` on a regular non-symlink file, with holder receipt containing:

- transaction ID;
- PID/start ticks/boot ID;
- cgroup/service unit;
- acquired wall and monotonic times;
- surface set hash.

JSON metadata without a held kernel lock is not sufficient.

### 9.3 Approval wait

No production mutation lock remains held during `AWAITING_APPROVAL`. Commit reacquires locks and revalidates every bound precondition.

### 9.4 Conflicting processes

Precheck detects active npm/pnpm/yarn/global-prefix writers, OpenClaw package recovery, Gateway restart, and other critical apply transactions. It does not kill them. Unknown or conflicting writers block commit.

## 10. Restore point subsystem

### 10.1 Restore-point schema

```json
{
  "schema": "critical_apply.restore_point.v2",
  "restore_point_id": "...",
  "created_at_utc": "...",
  "created_monotonic_ns": 0,
  "created_boot_id": "...",
  "source_generation": {
    "version": "...",
    "source_commit": "...",
    "tree_sha256": "...",
    "device": 0,
    "inode": 0
  },
  "archive_path": "...",
  "archive_sha256": "...",
  "inventory_path": "...",
  "inventory_merkle_sha256": "...",
  "bin_link_state_sha256": "...",
  "npm_substrate_state_sha256": "...",
  "guard_baseline_sha256": "...",
  "restore_method": "filesystem_atomic_restore",
  "recovery_write_set_sha256": "...",
  "verified": true,
  "verification_receipt_sha256": "..."
}
```

### 10.2 Freshness algorithm

At `MUTATION_RELEASE`:

- calculate age from trusted wall clock;
- when same boot, cross-check monotonic age;
- reject negative age, excessive clock skew, unknown boot transition, or age > 3,600 seconds;
- write measured age and both clock sources to `apply-release.json`.

After release, recovery verifies the recorded release-time eligibility and current artifact integrity. It does not reapply the one-hour wall-clock rule.

### 10.3 Inventory

Inventory records relative path, file type, mode, uid, gid, size, SHA-256 for regular files, symlink target, device/inode, and approved xattr policy. It rejects unexpected special files and unsafe links.

### 10.4 Restore verification

Before a restore point is marked verified, required critical surfaces must be reconstructed into an isolated verification directory or proven from a filesystem-native snapshot mechanism, then classified coherent against the inventory.

### 10.5 Filesystem recovery algorithm

1. Verify recovery authority, idempotency key, and apply cgroup quiescence.
2. Verify restore point release-time eligibility and current artifact seal.
3. Create a same-filesystem sibling restore staging directory.
4. Reconstruct using no-follow, dirfd-relative operations.
5. Verify complete inventory and critical surfaces.
6. Inspect official path and all live process references.
7. If official path is damaged and safe to move, atomically move it to the transaction quarantine area.
8. Atomically rename verified restored staging into the official path.
9. Recreate/verify authorised bin link and metadata only.
10. fsync affected parent directories.
11. Postcheck complete write and guard sets.
12. Write recovery action and post-recovery receipts.
13. Never delete quarantined or hidden generations automatically.

If any step is uncertain, stop and classify operator HOLD.

## 11. Process supervision and launch gate

### 11.1 Process identity

```json
{
  "pid": 12345,
  "start_ticks": 67890,
  "boot_id": "...",
  "pgid": 12345,
  "sid": 100,
  "cgroup": "...",
  "uid": 1001,
  "gid": 1001,
  "cmdline_sha256": "...",
  "exe_realpath": "...",
  "exe_device": 0,
  "exe_inode": 0
}
```

Use pidfd when available. All identity checks compare PID plus start ticks and boot ID.

### 11.2 Exact exec specification

```json
{
  "schema": "critical_apply.exec_spec.v2",
  "executable": "/usr/bin/npm",
  "executable_realpath": "/usr/share/nodejs/npm/bin/npm-cli.js",
  "executable_sha256": "...",
  "argv": [
    "/usr/bin/npm",
    "install",
    "-g",
    "--offline",
    "--no-audit",
    "--no-fund",
    "/verified/path/openclaw.tgz"
  ],
  "cwd": "/home/stickai/.openclaw/workspace",
  "uid": 1001,
  "gid": 1001,
  "umask": "0077",
  "environment_allowlist": {
    "HOME": "/home/stickai",
    "PATH": "/usr/bin:/bin",
    "npm_config_prefix": "/home/stickai/.npm-global",
    "npm_config_offline": "true",
    "npm_config_audit": "false",
    "npm_config_fund": "false",
    "npm_config_update_notifier": "false"
  },
  "network_policy": "offline_no_registry_no_provider",
  "timeout_seconds": 900,
  "term_grace_seconds": 20
}
```

No shell, command substitution, glob expansion, mutable PATH lookup, or uncontrolled environment inheritance is allowed.

### 11.3 Launch sequence

1. Write/fsync `apply-intent.json`.
2. Create one-way gate pipe.
3. Fork child into a dedicated process group/cgroup.
4. Child closes unrelated file descriptors and blocks before `execve`.
5. Parent captures PID/start ticks/PGID/cgroup.
6. Write/fsync `apply-spawned-blocked.json`.
7. Revalidate authority, candidate, restore point, guard baseline, locks, mount identity, and resource reserve.
8. Atomically consume approval.
9. Write/fsync `apply-release.json`.
10. Send release byte.
11. Child `execve`s exact executable and argv.
12. Parent captures stdout/stderr to files and waits.
13. On timeout, terminate cgroup, wait bounded interval, then kill.
14. Write/fsync `apply-exit.json`.
15. Run postcheck regardless of exit status.

### 11.4 Observer failure

- Before release: blocked child is killed; terminal or resumable status is `APPROVED_NOT_STARTED`; no mutation replay.
- After release and child running: supervisor restart scans cgroup and observes or terminates according to timeout; never launches again.
- After child exit but before exit receipt: execution state is `EXIT_UNKNOWN`; postcheck determines actual state.
- During recovery: idempotency marker and actual filesystem state determine whether to continue verification or stop; the recovery mutation is not repeated blindly.

## 12. OpenClaw npm package plugin

### 12.1 Plugin interface

```python
class CriticalApplyPlugin(Protocol):
    plugin_name: str
    plugin_version: str

    def declare_surfaces(self, spec: Mapping[str, Any]) -> SurfaceSets: ...
    def validate_inputs(self, spec: Mapping[str, Any]) -> ValidationResult: ...
    def prepare_candidate(self, ctx: ReadOnlyContext) -> CandidateAuthority: ...
    def create_or_select_restore_point(self, ctx: RestoreContext) -> RestorePoint: ...
    def precheck(self, ctx: ReadOnlyContext) -> PrecheckResult: ...
    def build_exec_spec(self, ctx: SealedContext) -> ExecSpec: ...
    def classify_post_state(self, ctx: ReadOnlyContext) -> StateVector: ...
    def plan_recovery(self, ctx: ReadOnlyContext, state: StateVector) -> RecoveryPlan: ...
    def execute_recovery(self, ctx: RecoveryCapability, plan: RecoveryPlan) -> RecoveryResult: ...
    def classify_terminal(self, ctx: ReadOnlyContext, state: StateVector) -> TerminalDecision: ...
```

The core, not the plugin, validates authority, locks, journal transitions, approval consumption, resource policy, and terminal seal.

### 12.2 Package authority

Required inputs:

```json
{
  "package_path": "/verified/path/openclaw-2026.5.7.tgz",
  "expected_sha256": "...",
  "expected_name": "openclaw",
  "expected_version": "2026.5.7",
  "expected_source_commit": "...",
  "build_manifest_path": "...",
  "build_manifest_sha256": "...",
  "required_surfaces_manifest_path": "...",
  "required_surfaces_manifest_sha256": "..."
}
```

Checks:

- regular file, not symlink, trusted parent path;
- exact SHA-256;
- safe tar entries;
- no absolute path, `..`, device, FIFO, socket, unsafe hardlink/symlink, setuid/setgid;
- package name/version/source commit match;
- build manifest and candidate-source hashes match;
- required surfaces are present;
- lifecycle scripts are enumerated and policy-approved;
- package can be unpacked and classified in an isolated candidate directory;
- package is not superseded by a newer owner-approved candidate record.

### 12.3 Package-manager substrate classifier

Separate from OpenClaw package-root health:

```json
{
  "node": {"realpath": "...", "version": "...", "coherent": true},
  "npm": {"realpath": "...", "version": "...", "coherent": true},
  "global_prefix": {"path": "...", "device": 0, "writable": true},
  "bin_directory": {"path": "...", "writable": true},
  "active_conflicts": [],
  "classification": "COHERENT"
}
```

A broken npm substrate selects filesystem restore, not npm reinstall.

### 12.4 Generation vector

```json
{
  "candidate": {"version": "...", "source_commit": "...", "tree_sha256": "..."},
  "restore": {"version": "...", "source_commit": "...", "tree_sha256": "..."},
  "official": {
    "classification": "COHERENT_CANDIDATE_GENERATION",
    "version": "...",
    "source_commit": "...",
    "tree_sha256": "...",
    "device": 0,
    "inode": 0
  },
  "running": {
    "gateway_process": {"pid": 0, "start_ticks": 0, "boot_id": "..."},
    "generation_path": "...",
    "generation_kind": "OFFICIAL|HIDDEN_STAGING|UNKNOWN",
    "version": "...",
    "source_commit": "..."
  },
  "staging": []
}
```

### 12.5 Official package-root classifier

Minimum built-in critical surfaces:

- `package.json`
- `openclaw.mjs`
- primary dist entrypoint
- runtime build/source identity
- required speech runtime surface when present in the authority manifest
- package bin target

The authority manifest, not a permanent hard-coded list alone, defines version-specific required surfaces.

`EMPTY` means the root exists but lacks meaningful package content under a documented threshold. The threshold must be deterministic and tested. Conflicting evidence is `UNKNOWN`, never guessed.

### 12.6 Speech/import surface

Static import verification SHALL:

- resolve literal relative imports inside the package root;
- reject escape outside the authorised root;
- classify missing modules, syntax errors, unsafe symlinks, and unresolved dynamic imports separately;
- use the candidate’s required-surface manifest to decide whether unresolved dynamic imports block coherence.

No live provider or TTS/STT call is part of package postcheck.

### 12.7 Staging/process-reference inspection

For every direct sibling matching npm’s staging pattern:

- use `lstat`, not path-following `stat`;
- record device/inode/type;
- reject symlinks and suspicious names;
- scan `/proc` maps, fd, cwd, root, exe, cmdline, and cgroup;
- match PID plus start ticks;
- repeat scan or use stable pidfds to reduce race;
- classify permission-denied or unstable results as unknown.

Classifications:

- NONE
- INACTIVE_VALID
- LIVE_REFERENCED_LEAVE_UNTOUCHED
- SUSPICIOUS_BLOCK
- UNKNOWN_BLOCK

No automatic deletion exists.

### 12.8 Guard set

For package-only apply, the default guard set includes:

- strict `jobs.json`;
- protected writer enabled/schedule/execution fields;
- protected writer run-log hashes and sizes;
- `MEMORY.md`;
- current daily protected-memory file;
- Gateway config and route hashes;
- global package siblings and unrelated bin links;
- service process identity, with expected “no restart” policy;
- provider/delivery invocation counters when available.

Volatile state may drift only under an explicit field-level signed drift policy. Whole-file “ignore timestamp changes” is insufficient.

## 13. Postcheck and terminal derivation

Postcheck always runs, including exit zero.

### 13.1 PASS package-only

Requirements:

- official package is exactly candidate generation;
- package-manager substrate coherent;
- bin link and metadata coherent;
- required surfaces/imports pass;
- unrelated global packages/links unchanged;
- guard set unchanged or only allowed field-level drift;
- no Gateway restart/PID change caused by transaction;
- no provider/delivery/cron mutation;
- evidence complete.

Terminal:

```text
PASS_PACKAGE_INSTALLED_HOLD_FOR_SEPARATE_RESTART
```

Running Gateway may remain on the prior generation and must be reported explicitly.

### 13.2 Nonzero but effective apply

If exit is nonzero but official package is exactly the candidate, all guards pass, and no recovery is required:

```text
APPLY_EFFECTIVE_EXIT_NONZERO_HOLD
```

No automatic rollback occurs merely to make exit status look clean. Operator review decides the next transaction.

### 13.3 Fail safe no mutation

Allowed only when:

- official package equals exact pre-generation;
- bin link/npm metadata equal pre-state;
- all in-scope write-set inventories equal pre-state;
- all guard sentinels equal or allowed drift;
- no recovery action occurred;
- package-manager logs and process evidence do not show an unresolved mutation.

Otherwise use partial/unknown classifications.

### 13.4 Recovery-required states

Missing, empty, incomplete, unknown, or forbidden official generation; broken link; forbidden guard drift; or released transaction with unsafe unknown state enters recovery decision.

## 14. Recovery decision matrix

| Execution | Official root | Substrate | Guards | Staging/process state | Decision |
|---|---|---|---|---|---|
| not released | any | any | unchanged | any | cancel blocked child; no recovery |
| nonzero | exact pre | coherent | unchanged | any | `FAIL_SAFE_NO_MUTATION` only after full equality proof |
| nonzero | exact candidate | coherent | unchanged | any | `APPLY_EFFECTIVE_EXIT_NONZERO_HOLD` |
| any | missing/empty/incomplete | coherent | unchanged | live hidden generation | leave hidden untouched; filesystem restore official path |
| any | missing/empty/incomplete | broken | unchanged | any known-safe | filesystem restore; do not call npm |
| any | missing/empty/incomplete | coherent | unchanged | inactive valid collision | quarantine only if required; filesystem restore |
| any | unknown | any | any | suspicious/unknown | recovery blocked; operator required |
| any | damaged | any | forbidden drift | any | restore declared package write set only if safe; operator HOLD remains |
| any | damaged | any | any | apply cgroup not quiescent | wait/terminate under timeout; no concurrent restore |
| any | damaged | any | any | restore invalid/substituted/not valid at release | rollback fail; operator required |

Automatic recovery count is one. Recovery action is idempotency-keyed and never reissued if its commit status is uncertain; actual state is inspected first.

## 15. Resource and environment policy

Required pre-release checks:

- free disk bytes and inodes above configured worst-case estimate plus reserve;
- restore staging and official root on expected filesystem;
- evidence path fsync test;
- emergency terminal-receipt reserve file present;
- bounded log quota;
- file descriptor/process limits;
- no clock rollback or invalid age;
- expected boot ID and mount IDs;
- exact UID/GID/groups;
- canonical executable and package paths;
- no uncontrolled proxy/registry/provider environment variables;
- offline network policy active;
- no package manager audit/fund/update-notifier side effects.

If log quota is reached, the observer terminates the apply under policy and continues classification; it never silently drops evidence.

## 16. Reconciliation algorithm

On daemon start:

1. validate service code bundle and configuration;
2. acquire reconciliation lock;
3. enumerate nonterminal transaction directories without following symlinks;
4. validate journal chain and projections;
5. determine last durable transition;
6. validate lock holder/cgroup/process identities;
7. apply phase-specific reconciliation:

| Last durable phase | Reconciliation |
|---|---|
| before approval | remain awaiting/cancel on expiry |
| approved, before child spawn | require commit revalidation |
| child spawned blocked, before release | kill blocked child; `APPROVED_NOT_STARTED` |
| mutation released, child running | observe/timeout; never re-exec |
| mutation released, child absent, no exit receipt | `EXIT_UNKNOWN`; postcheck |
| recovery intent, no proof of action | inspect idempotency marker and actual paths before writing |
| final report, no valid terminal seal | evidence-integrity HOLD |
| terminal seal valid | immutable terminal |

8. write reconciliation receipt and journal event;
9. release reconciliation lock.

No reconciliation path restarts Gateway, runs smoke, mutates cron, or calls providers unless that exact transaction type and authority already released before the crash.

## 17. CLI contract

```bash
critical_apply_ctl.py prepare --spec <transaction-spec.json>
critical_apply_ctl.py show-approval --transaction <id>
critical_apply_ctl.py approve --transaction <id> --approval-file <approval.json>
critical_apply_ctl.py execute --transaction <id>
critical_apply_ctl.py status --transaction <id> --verify
critical_apply_ctl.py reconcile --transaction <id> --read-only
critical_apply_ctl.py cancel --transaction <id>
critical_apply_ctl.py final-report --transaction <id> --verify-seal
critical_apply_ctl.py validate --transaction <id>
```

`execute` submits to the daemon. It does not execute the mutation in the CLI process.

There is no `--execute-foreground`, `--shell`, `--force`, `--ignore-drift`, `--break-lock`, or `--skip-restore` option.

## 18. Transaction spec example

```json
{
  "schema": "critical_apply.transaction_spec.v2",
  "transaction_type": "OPENCLAW_NPM_PACKAGE_APPLY",
  "campaign_id": "critical-campaign-urk-...",
  "plugin": "openclaw_npm_package",
  "candidate": {
    "package_path": "/verified/path/openclaw.tgz",
    "expected_sha256": "...",
    "expected_version": "...",
    "expected_source_commit": "...",
    "authority_manifest_path": "...",
    "authority_manifest_sha256": "..."
  },
  "restore_policy": {
    "max_age_seconds_at_mutation_release": 3600,
    "create_if_missing": true,
    "method": "filesystem_atomic_restore"
  },
  "timeouts": {
    "apply_seconds": 900,
    "term_grace_seconds": 20,
    "recovery_seconds": 900
  },
  "network_policy": "offline_no_registry_no_provider",
  "restart_in_scope": false,
  "functional_smoke_in_scope": false,
  "automatic_recovery": {
    "enabled": true,
    "max_attempts": 1,
    "conditions": [
      "OFFICIAL_MISSING",
      "OFFICIAL_EMPTY",
      "OFFICIAL_INCOMPLETE"
    ]
  },
  "forbidden": [
    "gateway_restart",
    "cron_mutation",
    "protected_memory_mutation",
    "route_config_mutation",
    "provider_call",
    "delivery_smoke"
  ]
}
```

## 19. Hard validation gates

### Gate group A — architecture, schemas, and authority

**A1 — No foreground or generic mutation path**

- source/doc audit finds no foreground critical mutation instruction;
- no shell execution path;
- no generic arbitrary command plugin;
- daemon unavailable causes block.

Terminal:

```text
A1_PASS_NO_FOREGROUND_OR_GENERIC_CRITICAL_MUTATION_PATH
```

**A2 — Schema and canonicalisation**

- valid schemas pass;
- duplicate JSON keys, unknown enums, NaN, missing required hashes, and unknown fields under strict schemas fail;
- canonical hash stable across runs.

```text
A2_PASS_STRICT_SCHEMA_AND_CANONICAL_HASH
```

**A3 — State-machine totality**

- every transition enumerated;
- illegal transition rejected;
- every exception path yields durable error or terminal;
- no PASS without a seal.

```text
A3_PASS_STATE_MACHINE_TOTALITY
```

**A4 — Authority binding and one-time consumption**

- stale approval, wrong nonce, expired approval, changed spec/code/plugin/candidate/restore/pre-state all block;
- consumed approval cannot launch again.

```text
A4_PASS_AUTHORITY_BINDING_ONE_TIME_CONSUMPTION
```

### Gate group B — journal and evidence durability

**B1 — Atomic receipt durability**

Crash injection before write, during write, before rename, after rename, before parent fsync, and after parent fsync produces either the old complete state or new complete state, never accepted partial truth.

```text
B1_PASS_ATOMIC_RECEIPT_CRASH_MATRIX
```

**B2 — Journal chain and projection parity**

Tamper, deleted line, duplicate sequence, torn line, wrong previous hash, and projection edit all fail closed.

```text
B2_PASS_HASH_CHAIN_AND_PROJECTION_PARITY
```

**B3 — Terminal seal**

No terminal PASS without closed logs, complete manifest, journal head, and valid seal.

```text
B3_PASS_TERMINAL_SEAL_NON_CIRCULAR_MANIFEST
```

**B4 — Disk-full evidence reserve**

`ENOSPC` before release blocks; `ENOSPC` after release releases reserve and writes terminal/recovery evidence.

```text
B4_PASS_DISK_FULL_EVIDENCE_FAILSAFE
```

### Gate group C — restore points

**C1 — Freshness at mutation release**

- fresh at prepare but stale at release blocks;
- fresh at release proceeds;
- clock rollback/negative age blocks;
- same-transaction recovery after >1 hour remains eligible if release receipt and artifact seal verify.

```text
C1_PASS_RELEASE_TIME_RESTORE_FRESHNESS
```

**C2 — Restore create/verify/path safety**

- inventory complete;
- archive traversal, unsafe links, devices, ownership, mount mismatch fail;
- isolated reconstruction proves coherence.

```text
C2_PASS_RESTORE_CREATE_VERIFY_PATH_SAFETY
```

**C3 — Atomic restore drill**

Damage fixture root, reconstruct sibling, verify, atomic rename, fsync, exact post-state, no out-of-bound mutation.

```text
C3_PASS_ATOMIC_FILESYSTEM_RESTORE_DRILL
```

**C4 — Recovery idempotency**

Crash before/after quarantine, before/after rename, before/after link restore, and before receipt; rerun inspects state and does not duplicate mutation.

```text
C4_PASS_RECOVERY_IDEMPOTENCY_CRASH_MATRIX
```

### Gate group D — observer and process control

**D1 — HRL-3 supervisor survival**

Killing foreground client has no effect. Killing observer causes service restart and correct phase reconciliation.

```text
D1_PASS_HRL3_SUPERVISOR_SESSION_AND_PROCESS_LOSS
```

**D2 — Receipt-before-mutation gate**

Child cannot create mutation marker before `apply-spawned-blocked` and `apply-release` are fsynced.

```text
D2_PASS_BLOCKED_CHILD_RECEIPT_BEFORE_MUTATION
```

**D3 — PID reuse and process identity**

Fake PID reuse with different start ticks/boot ID is rejected. pidfd/cgroup identity is preferred.

```text
D3_PASS_PROCESS_IDENTITY_PID_REUSE_SAFE
```

**D4 — Timeout and descendant control**

Child ignores SIGTERM and forks descendants; cgroup termination removes all transaction descendants before recovery.

```text
D4_PASS_TIMEOUT_DESCENDANT_QUIESCENCE
```

**D5 — Reboot reconciliation**

Crash/reboot fixtures at every post-release phase never re-execute apply and reach a safe classification.

```text
D5_PASS_REBOOT_RECONCILIATION_NO_REPLAY
```

### Gate group E — package and generation classification

**E1 — Candidate authority**

Valid, wrong SHA, wrong version, wrong commit, unsafe archive, superseded candidate, changed-after-approval, and unapproved lifecycle scripts.

```text
E1_PASS_CANDIDATE_AUTHORITY_MATRIX
```

**E2 — Package-manager substrate**

Coherent node/npm/prefix, broken npm, wrong prefix, alias/path substitution, unwritable prefix, active conflict.

```text
E2_PASS_PACKAGE_SUBSTRATE_CLASSIFIER
```

**E3 — Official package root**

Missing, empty, incomplete, coherent pre, coherent candidate, coherent other, and unknown.

```text
E3_PASS_OFFICIAL_PACKAGE_STATE_MATRIX
```

**E4 — Generation vector**

Official old/new, running official/hidden/unknown, multiple staging generations, and mixed-generation success are correctly represented.

```text
E4_PASS_PACKAGE_GENERATION_VECTOR
```

**E5 — Staging process references**

maps/fd/cwd/root/exe/cmdline/cgroup references; suspicious symlink; permission denied; unstable scan.

```text
E5_PASS_STAGING_REFERENCE_FAIL_CLOSED
```

**E6 — Required runtime/import surfaces**

Version-specific manifest, minimum entrypoints, speech surface, relative import escape, syntax error, unresolved dynamic import policy.

```text
E6_PASS_REQUIRED_RUNTIME_SURFACE_MATRIX
```

**E7 — Adjacent guards**

Strict jobs, field-level volatile policy, protected writers, run logs, protected memory, config/routes, unrelated globals, no restart/provider.

```text
E7_PASS_ADJACENT_PROTECTED_SURFACE_GUARDS
```

### Gate group F — outcome and recovery

**F1 — Fail-safe no mutation proof**

Nonzero with exact full pre-state equality classifies safe; any unknown or unrelated delta blocks that terminal.

```text
F1_PASS_FAIL_SAFE_REQUIRES_FULL_EQUALITY
```

**F2 — Effective apply despite nonzero exit**

Candidate coherent with all guards unchanged yields hold, not blind rollback.

```text
F2_PASS_EFFECTIVE_APPLY_EXIT_NONZERO_CLASSIFICATION
```

**F3 — Missing/empty/incomplete auto restore**

Each state restores official path from bound verified restore point, no restart.

```text
F3_PASS_AUTO_RESTORE_DAMAGED_OFFICIAL_ROOT
```

**F4 — Broken npm substrate uses filesystem restore**

No npm invocation during recovery when substrate is broken/unknown.

```text
F4_PASS_FILESYSTEM_RECOVERY_WHEN_NPM_UNSAFE
```

**F5 — Live hidden generation untouched**

Running Gateway references hidden generation; recovery restores official path and leaves hidden path unchanged.

```text
F5_PASS_LIVE_HIDDEN_GENERATION_UNTOUCHED
```

**F6 — Unknown state blocks recovery**

Uncertain process/path/restore/guard evidence produces operator HOLD.

```text
F6_PASS_UNKNOWN_STATE_FAILS_CLOSED
```

### Gate group G — boundary separation and campaign chaining

**G1 — Package apply cannot restart**

No service-manager restart command, PID change caused by transaction, or readiness smoke in package transaction.

```text
G1_PASS_PACKAGE_APPLY_RESTART_BOUNDARY
```

**G2 — Restart has separate authority and predecessor seal**

New transaction, restore point, nonce, approval, locks, and a sealed package-apply predecessor.

```text
G2_PASS_RESTART_SEPARATE_TRANSACTION
```

**G3 — Smoke has separate provider/delivery authority**

No package/config mutation and no implicit rollback trigger.

```text
G3_PASS_FUNCTIONAL_SMOKE_SEPARATE_TRANSACTION
```

**G4 — No authority inheritance**

`next_allowed_transactions` is advisory only; predecessor cannot start successor.

```text
G4_PASS_NO_CROSS_TRANSACTION_AUTHORITY_INHERITANCE
```

### Gate group H — isolation and live-state promotion

**H1 — Shadow target path fence**

Every write resolves inside isolated prefix; symlink swap and realpath escape block.

```text
H1_PASS_SHADOW_TARGET_PATH_FENCE
```

**H2 — No production sentinel drift during shadow**

Official package, Gateway, cron, memory, routes, provider counters unchanged.

```text
H2_PASS_SHADOW_NO_PRODUCTION_MUTATION
```

**H3 — Live read-only classifier**

Current production state classified with evidence only.

```text
H3_PASS_LIVE_READ_ONLY_PRECHECK
```

**H4 — Restore-point-only live transaction**

Fresh verified restore point, no package/apply/restart/cron/provider mutation.

```text
H4_PASS_LIVE_RESTORE_POINT_ONLY
```

## 20. Build and promotion milestones

### M0 — Threat model, invariants, and strict contracts

Deliver:

- architecture v2;
- threat model;
- schemas/enums;
- transition table;
- terminal derivation table;
- authority and surface-set contracts;
- no mutation code.

Gates: A1–A4.

```text
M0_PASS_CRITICAL_APPLY_V2_CONTRACT_FINALIZED_NO_MUTATION
```

### M1 — Atomic journal, projections, manifest, and seal

Deliver:

- atomic I/O;
- append-only hash-chain journal;
- projections;
- manifest and terminal seal;
- crash-injection fixtures.

Gates: B1–B4.

```text
M1_PASS_CRASH_CONSISTENT_EVIDENCE_KERNEL
```

### M2 — Locks, authority, and commit revalidation

Deliver:

- kernel locks and lock order;
- approval receipt/consumption;
- prepare/approve/commit split;
- drift invalidation matrix.

Gates: A4, C1, concurrency tests.

```text
M2_PASS_ONE_TIME_AUTHORITY_AND_COMMIT_FENCING
```

### M3 — Restore-point subsystem

Deliver:

- inventory/Merkle;
- safe snapshot/archive;
- release-time freshness;
- atomic filesystem restore;
- idempotent crash recovery.

Gates: C1–C4.

```text
M3_PASS_VERIFIED_RESTORE_AND_IDEMPOTENT_RECOVERY_FIXTURES
```

### M4 — HRL-3 observer supervisor and launch gate

Deliver:

- daemon/client;
- supervisor adapter;
- blocked-child launch;
- process/cgroup identity;
- timeout and reconciliation.

Gates: D1–D5.

```text
M4_PASS_HRL3_OBSERVER_EXECUTION_AND_REHYDRATION_FIXTURES
```

### M5 — OpenClaw package read-only classifiers

Deliver:

- candidate authority;
- npm substrate;
- official/generation/staging classifiers;
- import/speech surfaces;
- adjacent guards.

Gates: E1–E7.

```text
M5_PASS_OPENCLAW_PACKAGE_CLASSIFIER_MATRIX_READ_ONLY
```

### M6 — Recovery decision and fixture matrix

Deliver:

- pure terminal derivation;
- effective-nonzero handling;
- missing/empty/incomplete restore;
- broken npm filesystem recovery;
- live hidden generation preservation;
- unknown-state block.

Gates: F1–F6.

```text
M6_PASS_OBSERVER_OWNED_RECOVERY_MATRIX
```

### M6B — Critical apply service bootstrap

Preconditions:

- M0–M6 PASS;
- checksum-pinned service bundle;
- existing proven parent-thread observation harness;
- owner approval for bootstrap-only surfaces.

Allowed:

- critical-apply code/service/evidence/lock/restore infrastructure only.

Forbidden:

- OpenClaw package, Gateway, cron, protected memory, routes, provider/delivery.

Gates:

- service install receipt;
- service code/unit hashes;
- forced observer crash and restart;
- status after foreground/session loss;
- rollback of service bootstrap proven.

```text
M6B_PASS_HRL3_SERVICE_BOOTSTRAPPED_NO_OPENCLAW_RUNTIME_MUTATION
```

### M7 — Apply/restart/smoke plugin boundaries

Deliver package transaction enforcement, restart plugin skeleton, smoke transaction schema, campaign chaining.

Gates: G1–G4.

```text
M7_PASS_TRANSACTION_BOUNDARY_AND_CAMPAIGN_ENFORCEMENT
```

### M8 — Live read-only precheck

Allowed reads and evidence only. No restore creation in this milestone.

Gates: H3 plus E classifiers on live state.

```text
M8_PASS_LIVE_READ_ONLY_PRECHECK_NO_MUTATION
```

### M9 — Restore-point-only live transaction

Allowed verified restore-point creation and evidence only.

Gates: H4, C2 live, protected sentinels unchanged.

```text
M9_PASS_LIVE_RESTORE_POINT_ONLY_NO_APPLY
```

### M10 — Shadow end-to-end on isolated current package copy

- isolated npm prefix/path fence;
- full success, failure, crash, and recovery matrix;
- no production mutation.

Gates: H1, H2, D5, F1–F6.

```text
M10_PASS_SHADOW_CRITICAL_APPLY_RECOVERY_NO_PRODUCTION_MUTATION
```

### M11 — Owner-approved production package-only canary

Preconditions:

- M0–M10 PASS and sealed;
- service HRL-3 healthy;
- fresh restore point at release;
- exact candidate and code authority;
- no stale approvals or active conflicts;
- owner approves exact package-only authority envelope.

Allowed:

- official OpenClaw package root;
- authorised bin link and npm metadata;
- transaction evidence;
- one automatic filesystem recovery if authorised.

Forbidden:

- Gateway restart/reload;
- cron calls/mutations;
- protected-memory changes;
- route/config changes;
- provider/delivery/smoke;
- unrelated global packages;
- activation follow-ons.

Success:

```text
M11_PASS_PRODUCTION_PACKAGE_ONLY_HOLD_FOR_SEPARATE_RESTART
```

Recovered:

```text
M11_RECOVERY_PASS_PACKAGE_ONLY_HOLD_FOR_SEPARATE_RESTART
```

Blocked:

```text
M11_HOLD_OPERATOR_REQUIRED_NO_UNVERIFIED_CONTINUATION
```

### M12 — Separately approved Gateway restart

Preconditions:

- sealed M11 terminal permits restart preparation;
- new restore point/authority/nonce;
- owner approval.

Gates:

- old/new PID/start ticks/cgroup;
- new process maps intended official generation;
- service active;
- port bound;
- HTTP 200 text/html;
- LAN-origin WebSocket 101 where in scope;
- no provider/delivery smoke;
- no package reinstall trigger from HTTP-only warning.

```text
M12_PASS_CONTROLLED_GATEWAY_RESTART_OBSERVED
```

or:

```text
M12_HOLD_RESTART_HEALTH_WARNING_NO_AUTOMATIC_PACKAGE_REPAIR
```

### M13 — Separately authorised functional smoke

Explicit target/content/provider/delivery authority only.

```text
M13_PASS_FUNCTIONAL_SMOKE_SEPARATE_TRANSACTION
```

or:

```text
M13_FUNCTIONAL_SMOKE_FAIL_NO_AUTOMATIC_PACKAGE_RECOVERY
```

### M14+ — Remaining Universal Runtime Kernel plugins

Each later plugin follows the same promotion ladder:

```text
contract -> fixtures -> crash matrix -> shadow -> live read-only
-> restore/rollback-only proof -> owner-approved bounded canary
-> separate downstream transaction
```

No plugin inherits production readiness from the npm plugin.

## 21. Minimum automated test counts

Counts are floors, not targets.

| Group | Minimum |
|---|---:|
| Strict schema/canonicalisation/state transitions | 35 |
| Authority/approval/drift | 25 |
| Atomic I/O/journal/seal crash injection | 35 |
| Locks/concurrency/stale holder | 20 |
| Restore create/path safety/freshness | 30 |
| Restore idempotency crash matrix | 30 |
| Process gate/cgroup/PID reuse/reboot | 35 |
| Candidate/package substrate | 25 |
| Official/generation/staging classifiers | 35 |
| Runtime/import/speech surfaces | 15 |
| Guard policies | 20 |
| Recovery terminal matrix | 30 |
| Boundary/campaign separation | 15 |
| Shadow end-to-end | 12 |

All tests write machine-readable JSON or JUnit and a human summary. Test result manifests bind code hashes and fixture hashes.

## 22. Production approval presentation

Before a production mutation, the foreground assistant presents:

1. transaction and campaign IDs;
2. transaction type and plugin version/hash;
3. exact write, recovery-write, guard, and forbidden sets;
4. exact argv and argv hash;
5. environment/network/timeout policy hashes;
6. candidate path, version, commit, and SHA;
7. restore point ID, release-time maximum age policy, manifest hash, and method;
8. current pre-state and generation vector;
9. automatic recovery conditions and maximum attempt count;
10. explicit statement that restart and smoke are excluded;
11. approval expiry and one-time nonce;
12. expected terminals.

Example:

```text
APPROVE CRITICAL APPLY TRANSACTION <id> PACKAGE-ONLY
AUTHORITY ENVELOPE SHA <sha>
ALLOW EXACT APPLY EXEC SPEC SHA <sha>
ALLOW AT MOST ONE FILESYSTEM PACKAGE RESTORE FROM RESTORE POINT <restore-id>
ONLY IF THE OFFICIAL OPENCLAW ROOT IS MISSING, EMPTY, OR INCOMPLETE
NO GATEWAY RESTART
NO CRON
NO PROTECTED MEMORY
NO ROUTE OR CONFIG CHANGE
NO PROVIDER OR DELIVERY
NO FUNCTIONAL SMOKE
```

The approval is not a command and cannot be reused.

## 23. Operator runbook rules

- `status --verify` is safe and read-only.
- A missing heartbeat is not by itself a failure; journal, cgroup, and phase truth govern.
- Never manually delete hidden npm directories during an active or unknown transaction.
- Never rerun npm because stdout “looks stuck”.
- Never restart Gateway to test a damaged official root.
- Never edit transaction evidence.
- Never substitute a new restore point into an approved transaction.
- Never break a stale lock without the dedicated reconciliation report.
- If the final seal is absent or invalid, treat the transaction as nonterminal HOLD.
- `next_allowed_transactions` is guidance, not authority.

## 24. Non-goals for v2 initial production promotion

- no arbitrary command execution;
- no automatic hidden-directory deletion;
- no automatic service restart after package apply;
- no provider/network smoke in package/restart transaction;
- no multi-node distributed consensus;
- no cross-host automatic failover;
- no automatic stale-lock break;
- no generic self-healing beyond explicitly declared recovery plans;
- no production mutation before all predecessor gates pass.

## 25. Final acceptance criteria

The critical apply substrate may govern the remaining Universal Runtime Kernel only when:

1. M0–M10 are sealed PASS;
2. HRL-3 service bootstrap is sealed and observer restart is proven;
3. journal and terminal evidence survive crash, disk-full, and reboot injection;
4. approval is one-time and bound to code, candidate, restore, policy, and pre-state;
5. child release is impossible before durable spawn and release receipts;
6. restore is fresh at mutation release and remains transaction-bound afterward;
7. official/running/staging/candidate/restore generations are independently classified;
8. broken npm substrate selects filesystem restore;
9. live hidden generations are left untouched;
10. recovery is idempotent and at most once;
11. unknown process, path, guard, or evidence state blocks;
12. package apply cannot restart;
13. restart cannot smoke;
14. smoke cannot trigger package recovery by default;
15. every later Universal Runtime Kernel mutation plugin repeats the same promotion ladder.

Failure of any criterion keeps production critical apply blocked.

## 26. Recommended next action

Start **M0 only**: strict contract, threat model, schemas, transition table, authority envelope, and terminal derivation. No mutation code and no production action.

Owner-ready notice:

```text
STARTED M0 Critical Apply v2 Contract Finalization.
Scope: architecture, threat model, strict schemas, state transition table,
authority binding, surface sets, and terminal derivation only.
No deploy, install, service activation, Gateway restart, cron call,
provider call, package mutation, protected-memory change, or production recovery.
```
