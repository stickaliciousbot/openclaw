# UMC v1 — Milestone Ledger

This ledger is append-only for milestone closeouts. Every milestone PASS/HOLD/FAIL must update:

- this ledger;
- `UMC_V1_IMPLEMENTATION_NOTEBOOK.md`;
- `UMC_V1_TROUBLESHOOTING_AND_REPAIR_NOTEBOOK.md` when any repair/diagnostic occurred;
- `UMC_V1_REHYDRATOR.md` current-state packet;
- `UMC_V1_HANDOFF.json`.

## 2026-07-11T02:40:00Z — M0 discovery

**Closeout:** `PASS_DISCOVERY_COMPLETE_NO_MUTATION`

**Evidence:**

```text
m0_freeze_map/M0_FINAL_MILESTONE_CLOSE_SUMMARY.md
m0_freeze_map/M0_G0_ALL_SURFACES_READBACK.json
m0_freeze_map/M0_ALL_SURFACES_EXECUTION_MAP.md
```

**Result:** all selection, directive, reset, direct, queued/resumed, scheduled, fallback and post-dispatch delivery boundaries mapped read-only. No production mutation.

## 2026-07-11T02:47:00Z — M1 schema and fixture contract

**Closeout:** `PASS_SCHEMA_FIXTURE_CONTRACT`

**Evidence:**

```text
m1_schema_fixture_contract/M1_MILESTONE_CLOSE_SUMMARY.md
m1_schema_fixture_contract/M1_G1_READBACK.json
m1_schema_fixture_contract/UMC_V1_CONTRACT_SCHEMAS.json
m1_schema_fixture_contract/UMC_V1_ERROR_REGISTRY.json
m1_schema_fixture_contract/fixtures/PASS_QUALIFIED_NO_SEND.json
m1_schema_fixture_contract/fixtures/HOLD_MANIFEST_MISSING.json
m1_schema_fixture_contract/fixtures/FAIL_DIRECT_BYPASS.json
```

**Result:** schemas and fixtures validate with no optional date-format dependency; direct bypass, omitted capability, UNKNOWN closeout and invalid timestamp reject. No runtime/config/route/session/provider mutation.

## Active — M2 admission and route interceptor

**Status:** `HOLD_QUEUE_RESUME_POST_DISPATCH_RAW_EXECUTION_SURFACES_NOT_INTERCEPTED`

**Current rule:** no M2 PASS may be reported until implementation notebook, troubleshooting notebook (if applicable), rehydrator, handoff, and this ledger all name the final evidence and closeout.

## 2026-07-11T04:50:00Z — M2 interceptor reapply checkpoint

**Closeout:** `PASS_NO_SEND_SESSION_AND_DIRECTIVE_ROUTE_INTENT_REPAIR_HOLD_LIVE_ASYNC_PENDING`

**Evidence:**

```text
m2_admission_route_interceptor/M2_REAPPLY_RECORD.json
m2_admission_route_interceptor/M2_NO_SEND_ROUTE_INTENT_SMOKE.json
m2_admission_route_interceptor/M2_DIRECTIVE_ROUTE_INTENT_SMOKE.json
m2_admission_route_interceptor/M2_POST_RESTART_VALIDATION.json
m2_admission_route_interceptor/M2_CHECKPOINT_CLOSE_SUMMARY.md
```

**Result:** active installed runtime had lost/lacked the recorded M2 helper/call sites, so the M2 patch was reapplied with a fresh rollback backup. `node --check` passed; helper/call-site grep passed; Gateway restart signal was sent. Synthetic owner-direct no-send smoke with raw `openai/gpt-5.5` session preference persisted `umcV1RouteIntent`, forced executable route to default `openai-codex/gpt-5.5`, and reported `directBypass=false`, `externalSend=false`. A follow-up directive-only `/model openai/gpt-5.5` hook was added before the directive-only early return; pre/post-restart no-send smokes then persisted `source=user_directive`, requested `openai/gpt-5.5`, executable `openai-codex/gpt-5.5`, `directBypass=false`, `externalSend=false`, and default-route exact-token smoke returned `UMC_M2_POST_RESTART_ROUTE_OK_20260711J` via `openai-codex/gpt-5.5`. Full all-surface M2 remains HOLD pending live owner directive proof and queued/resumed/post-dispatch validation.

## 2026-07-11T05:30:00Z — M2Q queue/resume/post-dispatch classification

**Closeout:** `HOLD_QUEUE_RESUME_POST_DISPATCH_RAW_EXECUTION_SURFACES_NOT_INTERCEPTED`

**Evidence:**

```text
m2_admission_route_interceptor/M2_RESTART_SENTINEL_RERUN_VALIDATION.json
m2_admission_route_interceptor/M2Q_QUEUE_RESUME_POST_DISPATCH_HOLD.json
m2_admission_route_interceptor/M2Q_QUEUE_RESUME_REPAIR_PLAN.md
```

**Result:** direct owner session/directive no-send gates remain PASS, but read-only classification confirmed queued/follow-up execution is separate from `getReplyFromConfig()`: `agent-runner.runtime-a09vVD0N.js` builds queued work in `createFollowupRunner()`, calls `runWithModelFallback()`, then calls `runEmbeddedPiAgent()` with queued raw `provider`/`model`; queue delivery can call `routeReply()` to the origin. The queue helper is not exported for a safe no-send fixture; only the full `runReplyAgent` export exists and can deliver. Therefore full all-surface M2 must HOLD until an M2Q no-send queue admission harness/test seam exists and a scoped queue guard passes.

## 2026-07-11T05:46:30Z — M2Q queue admission guard

**Closeout:** `PASS_M2Q_QUEUE_ADMISSION_GUARD_WIRED_NO_SEND_STATIC`

**Evidence:**

```text
m2_admission_route_interceptor/M2Q_PRE_RESTART_QUEUE_ADMISSION_VALIDATION.json
m2_admission_route_interceptor/M2Q_POST_RESTART_QUEUE_ADMISSION_VALIDATION.json
```

**Result:** after lesson preflight, installed `agent-runner.runtime-a09vVD0N.js` was backed up and patched with exported no-send seam `applyUmcV1QueuedRouteAdmission` plus a queued/follow-up guard in `createFollowupRunner()` before `runWithModelFallback()` and `runEmbeddedPiAgent()`. Pre/post restart `node --check`, pure owner queued raw `openai/gpt-5.5` → executable `openai-codex/gpt-5.5` no-send smoke, non-owner/group negative fixtures, static ordering check, direct session/directive no-send regressions, and default-route exact-token smoke all passed. Post-restart route smoke returned `UMC_M2Q_POST_RESTART_ROUTE_OK_20260711M`; Telegram direct session readback remains `openai-codex/gpt-5.5`, fallback `ollama/deepseek-v4-pro:cloud`, queue depth 0. No live Telegram queued delivery probe was sent. M3 remains blocked until Stick accepts this no-send/static-wired M2Q closeout or asks for a controlled queued-delivery fixture.

## 2026-07-11T05:56:00Z — M2Q restart-sentinel rerun validation

**Closeout:** `PASS_M2Q_RESTART_SENTINEL_RERUN_VALIDATION`

**Evidence:**

```text
m2_admission_route_interceptor/M2Q_RESTART_SENTINEL_RERUN_VALIDATION.json
```

**Result:** after Gateway restart sentinel, validation was rerun fresh. Gateway status showed reachable loopback service, systemd user service enabled/running, Telegram ON/OK, events none, and tasks 0 active/queued/running. Telegram direct session `agent:main:telegram:direct:8495203551` read back `openai-codex/gpt-5.5`, fallback `ollama/deepseek-v4-pro:cloud`, queue depth 0. `node --check`, queue-admission pure no-send smoke, static order check, direct M2 session/directive no-send regressions, and default-route exact-token smoke all passed; route smoke returned `UMC_M2Q_RESTART_SENTINEL_ROUTE_OK_20260711N` via `openai-codex/gpt-5.5`. No live Telegram queued-delivery probe was sent.

## 2026-07-11T06:12:30Z — M2R controlled queued-delivery fixture preflight

**Closeout:** `BLOCKED_M2R_PREFLIGHT_OR_AUTHORITY_UNAVAILABLE`

**Evidence:**

```text
m2_admission_route_interceptor/m2r_single_queued_delivery/M2R_PREFLIGHT_SNAPSHOT.json
m2_admission_route_interceptor/m2r_single_queued_delivery/M2R_BLOCKED_PREFLIGHT_OR_AUTHORITY_UNAVAILABLE.json
```

**Result:** final `Banana` terminator was received, but Phase A preflight failed closed before any fixture build, dry run, live Telegram send, config mutation, Gateway mutation, route/fallback/session change, or M3 work. Guard ordering, syntax, route config, Gateway status, and runtime rollback readiness were OK, but repository preflight found 1329 unrelated local changes in the working tree. Because the prompt requires confirming no unrelated local changes and failing closed before sending if preflight is not clean, the live queued-delivery fixture was not run. M2/M2Q is not accepted; M3 has not started.

## 2026-07-11T05:00:00Z — M3M plugin manifest repair

**Closeout:** `PASS_M3M_PLUGIN_MANIFEST_REPAIR_GATEWAY_TELEGRAM_RECOVERED`

**Evidence:**

```text
m3m_plugin_manifest_repair/M3M_PLUGIN_MANIFEST_REPAIR_CLOSEOUT.json
```

**Result:** restored missing Zalo and Zalouser plugin manifests to installed dist; Gateway and Telegram recovered; no M3N started.

## 2026-07-13T06:57:15Z — M3M installed observe-only shadow soak R1

**Closeout:** `FAIL_M3M_INSTALLED_SHADOW_SOAK_RETRY_ABORTED`

**Evidence:**

```text
m3m_installed_shadow_soak_retry/M3M_RETRY_ABORT.json
m3m_installed_shadow_soak_retry/M3M_RETRY_CHECKPOINT_0001.json through 0005.json
```

**Result:** 12h / 24 checkpoint observe-only no-send soak aborted at checkpoint 0005 with `GATEWAY_UNREACHABLE`. Last clean checkpoint: 0004. Safety counters remained clean (0 Telegram sends, 0 external sends, 0 provider/model shadow calls, 0 runtime/memory/Context Bridge mutation). Gateway and Telegram later recovered healthy. Do not advance to M3N from this run.

## 2026-07-13T10:04:21Z — M3M soak abort preservation and Gateway blip diagnostic

**Closeout:** `PASS_M3M_SOAK_ABORT_PRESERVED_GATEWAY_BLIP_DIAGNOSED_R2_READY`

**Evidence:**

```text
m3m_installed_shadow_soak_retry/M3M_SOAK_ABORT_REHYDRATION_RESULT.json
m3m_installed_shadow_soak_retry/M3M_INSTALLED_SHADOW_SOAK_ABORT_CLOSEOUT.json
m3m_installed_shadow_soak_retry/M3M_INSTALLED_SHADOW_SOAK_ABORT_SUMMARY.md
m3m_installed_shadow_soak_retry/M3M_GATEWAY_REACHABILITY_BLIP_DIAGNOSTIC.json
m3m_installed_shadow_soak_retry/M3M_GATEWAY_REACHABILITY_BLIP_DIAGNOSTIC.md
m3m_installed_shadow_soak_retry/M3M_POST_ABORT_HEALTH_STABILITY_SUMMARY.json (6/6 probes PASS)
m3m_installed_shadow_soak_retry/M3M_SOAK_ABORT_SAFETY_COUNTER_VALIDATION.json
m3m_installed_shadow_soak_retry/M3M_INSTALLED_SHADOW_SOAK_NO_SEND_RETRY_R2_PLAN.json
m3m_installed_shadow_soak_retry/M3M_SOAK_ABORT_VALIDATION.json
m3m_installed_shadow_soak_retry/M3M_SOAK_ABORT_PRESERVATION_FINAL_CLOSEOUT.json
```

**Result:** abort evidence rehydrated and preserved; Gateway blip classified as `GATEWAY_RPC_TRANSIENT_TIMEOUT` (same PID throughout, RPC OK at abort, listener OK post-abort); 30-min post-abort health stability window confirmed (6/6 probes PASS, 0 failed); safety counters validated clean; R2 retry plan prepared with early-abort sentinel and additional reachability probes; observer harness fixed to scan for abort artifacts in `check` command. No M3N, M4, or enforcement started. No runtime/config mutation. Next milestone: `M3M_INSTALLED_OBSERVE_ONLY_SHADOW_SOAK_NO_SEND_RETRY_R2`.

## 2026-07-13T10:27:33Z — M3M R2 installed observe-only shadow soak retry

**Closeout:** `FAIL_M3M_R2_INSTALLED_SHADOW_SOAK_ABORTED`

**Evidence:**

```text
m3m_r2_installed_shadow_soak/M3M_R2_INSTALLED_SHADOW_SOAK_PREFLIGHT.json
m3m_r2_installed_shadow_soak/M3M_R2_INSTALLED_SHADOW_SOAK_BOUNDS.json
m3m_r2_installed_shadow_soak/M3M_R2_CHECKPOINT_0001.json
m3m_r2_installed_shadow_soak/M3M_R2_INSTALLED_SHADOW_SOAK_ABORT.json
m3m_r2_installed_shadow_soak/M3M_R2_INSTALLED_SHADOW_SOAK_CLOSEOUT.json
m3m_r2_installed_shadow_soak/M3M_R2_INSTALLED_SHADOW_SOAK_VALIDATION.json
m3m_r2_installed_shadow_soak/M3M_R2_INSTALLED_SHADOW_SOAK_EVIDENCE_MANIFEST.json
```

**Result:** R2 preflight passed and launched a fresh 12h/24-checkpoint observe-only/no-send soak, but checkpoint 0001 aborted fail-closed with `FAIL_M3M_R2_ROUTE_PROVIDER_FALLBACK_DRIFT`. Gateway, Telegram, queue, installed hashes, manifest hashes, logs, safety counters, and rollback readiness were clean. Production config hash was unchanged; the route/fallback drift was classified as observer/preflight route-fingerprint shape mismatch, so this is a validation implementation abort, not a PASS. M3N remains locked. Next safe action: repair route fingerprint parity and rerun M3M R2 fresh.

## 2026-07-14T07:45:34Z — M3N post-restart health failure preserved

**Closeout:** `FAIL_M3N_CURRENT_HEALTH_UNSTABLE_AFTER_N3_FAILURE`

**Evidence:**

```text
m3n_restart_persistence_no_send/M3N_N3_FAILURE_REHYDRATION_RESULT.json
m3n_restart_persistence_no_send/M3N_POST_RESTART_HEALTH_FAIL_CLOSED_CLOSEOUT.json
m3n_restart_persistence_no_send/M3N_POST_RESTART_HEALTH_SIGNAL_CLASSIFICATION.json
m3n_restart_persistence_no_send/M3N_CURRENT_HEALTH_RECHECK_AFTER_N3_FAILURE.json
m3n_restart_persistence_no_send/M3N_POST_RESTART_HEALTH_ROOT_CAUSE_CLASSIFICATION.json
m3n_restart_persistence_no_send/M3N_POST_RESTART_HEALTH_REPAIR_AND_RETRY_PLAN.json
```

**Result:** M3N Gateway restart passed, but N3 post-restart health failed closed. Scanner false positives were separated from real Gateway log liveness/Telegram instability. Current health recheck remains unstable, so M3N persistence verification, M3O, M4 and enforcement remain locked. No restart, probe send, provider/model shadow call, route/config/memory/Context Bridge mutation, or production authority change occurred in this preservation pass. Next milestone: `M3N_POST_RESTART_HEALTH_SCANNER_AND_LIVENESS_REPAIR_THEN_N2_N3_RETRY`.

## 2026-07-14T07:54:34Z — M3N post-restart health scanner/liveness repair attempt

**Closeout:** `FAIL_M3N_POST_REPAIR_PRODUCTION_HEALTH_UNSTABLE`

**Milestone:** `M3N_POST_RESTART_HEALTH_SCANNER_AND_LIVENESS_REPAIR_THEN_N2_N3_RETRY`

**Evidence:**

```text
m3n_restart_persistence_no_send/M3N_N3_FAILURE_PRESERVATION_BRANCH_SCOPE_VALIDATION.json
m3n_restart_persistence_no_send/M3N_N3_FAILURE_PRESERVATION_TARGET_DECISION.json
m3n_restart_persistence_no_send/M3N_POST_RESTART_HEALTH_SCANNER_REPAIR_RESULT.json
m3n_restart_persistence_no_send/M3N_POST_RESTART_LIVENESS_REPAIR_RESULT.json
m3n_restart_persistence_no_send/M3N_POST_RESTART_HEALTH_REPAIR_FIXTURE_RESULTS.json
m3n_restart_persistence_no_send/M3N_POST_REPAIR_PRODUCTION_RECHECK.json
m3n_restart_persistence_no_send/M3N_POST_RESTART_HEALTH_REPAIR_EVIDENCE_MANIFEST.json
```

**Result:** Preservation branch target was corrected to `evidence/umc-m3n-post-restart-health-failclosed-20260713`; scanner repair and liveness policy fixtures passed without sends or authority mutation. Read-only production recheck failed because fresh bounded runtime-log evidence still showed Telegram/liveness instability, so no N2/N3 retry approval was requested and no Gateway restart occurred. M3N persistence verification, M3O, M4 and enforcement remain locked.

## 2026-07-14T08:46:57Z — M3N current Telegram liveness blocker diagnosis/watch

**Closeout:** `FAIL_M3N_CURRENT_TELEGRAM_LIVENESS_STILL_UNSTABLE`

**Diagnostic classification:** `LIVENESS_NETWORK_OR_TRANSPORT_PROBLEM`

**Watch:** `FAIL_M3N_CURRENT_TELEGRAM_LIVENESS_STILL_UNSTABLE` across `6` probes. Fresh liveness warnings: `1`.

**Recovery decision:** `PATH_F_BLOCKED_PERSISTENT_PLUGIN_INSTABILITY`. No recovery action executed; no Telegram send, Gateway restart, config mutation, route/fallback mutation, memory mutation, Context Bridge mutation, provider/model call, N2/N3 retry, persistence verification, M3O/M4/enforcement.

**Next phase:** `HOLD_REPAIR_CURRENT_TELEGRAM_LIVENESS_BEFORE_N2_N3_RETRY`.

## 2026-07-14T09:20:36Z — M3N event-loop / Telegram transport diagnostic and recovery plan

**Closeout:** `HOLD_M3N_EVENT_LOOP_TRANSPORT_RECOVERY_AWAITING_APPROVAL`

**Event-loop classification:** `EVENT_LOOP_DELAY_FROM_LONG_RUNNING_OBSERVER`

**Telegram transport classification:** `TELEGRAM_TRANSPORT_TIMEOUT_CORRELATED_WITH_EVENT_LOOP_DELAY`

**Mini-watch:** `FAIL_M3N_EVENT_LOOP_TRANSPORT_STILL_UNSTABLE`; event-loop delay `0`, getMe timeout `0`, gateway timeout `0`, context overflow `0`.

**Recovery path:** `PATH_C_TARGETED_STALE_OBSERVER_OR_JOB_CLEANUP_REQUIRES_APPROVAL`. Approval required: `True`. No Telegram probe/send, external send, provider/model shadow call, config mutation, route/fallback mutation, memory mutation, Context Bridge mutation, production authority change, Gateway restart, N2/N3 retry, persistence verification, M3O, M4, or enforcement was run by the repair lane.

**Next phase:** `APPROVE_M3N_EVENT_LOOP_TRANSPORT_RECOVERY_ACTION`.
