# UMC v1 — Universal Model Contract Rehydrator

**Purpose:** re-establish trustworthy project state after any model, channel, session, compaction, restart, queued/resumed run, or operator handoff changes context.

**Rule:** this artifact is operational context, not route authority. It never authorizes production mutation by itself.

## When to run

Run before planning, coding, diagnosing, approving, resuming or reporting Universal Model Contract work when any of these is true:

- active model/lane/provider/adapter changed;
- the turn arrived via a different control surface;
- session was compacted, restarted, resumed or handed off;
- a UMC job/observer reports a completion, failure, timeout or missing evidence;
- prior work is only described in conversation memory;
- an implementation or repair decision is about to be made.

## Mandatory rehydration sequence

### Step 1 — Read governing artifacts in this order

1. `UMC_V1_REHYDRATOR.md` (this file);
2. `UMC_V1_IMPLEMENTATION_NOTEBOOK.md`;
3. `UMC_V1_TROUBLESHOOTING_AND_REPAIR_NOTEBOOK.md`;
4. latest UMC milestone evidence under this directory;
5. relevant canonical runtime state, receipts and route/config snapshots.

Do not begin by relying on model recollection, a summary, a channel model label, or a session pin.

### Step 2 — Establish live control-plane facts

Read-only checks only unless an approved milestone says otherwise:

```text
A. active session: provider/model, thinking level, execution mode, session override
B. configured default route and fallback chain
C. channel model policy / route-intent state
D. session model preference / route-intent state
E. current UMC mode: off / observe / shadow / canary / enforced
F. selectable lane manifests: qualification state, evidence freshness, hashes
G. runtime compatibility: OpenClaw build, adapter hashes, tool registry hash,
   memory/context envelope version, delivery handoff version
H. latest terminal receipts and health counters
I. current rollback target and mutation-sentinel state
```

Redact secrets and raw private source content. Facts without canonical source evidence are `UNKNOWN`.

### Step 3 — Reconcile declared state

Build this compact table before acting:

| Field | Canonical value | Evidence | Status |
|---|---|---|---|
| Current milestone | | path/hash | PASS/HOLD/FAIL/UNKNOWN |
| UMC mode | | config/runtime readback | |
| Owner execution authority | | route evidence | |
| Direct-bypass count | | receipts/metrics | |
| Qualified lanes | | manifest evidence | |
| Active lane/model | | session + route evidence | |
| Tool registry hash | | runtime snapshot | |
| Memory envelope state | | runtime/receipt evidence | |
| Delivery contract state | | receipt evidence | |
| Open incident/repair | | repair packet | |
| Rollback readiness | | rollback packet | |
| Next gate | | implementation notebook | |

If a required field is missing, null, empty or `UNKNOWN`, stop at `HOLD_REHYDRATION_INCOMPLETE`. Do not infer a PASS.

### Step 4 — Classify the current work

Choose exactly one:

```text
M0_DISCOVERY
M1_SPECIFICATION
M2_INTERCEPTOR
M3_ENVELOPE_TOOLS_DELIVERY
M4_GPT55_QUALIFICATION
M5_MODEL_ELIGIBILITY
M6_SHADOW
M7_ENFORCED_CANARY
M8_CONTINUOUS_REGRESSION
INCIDENT_TRIAGE
REPAIR_VALIDATION
NO_ACTIVE_UMC_WORK
```

Then state the active hard gate, permitted mutation class, test required for exit, and explicit rollback condition.

### Step 5 — Enforce model-independence

Before accepting any claim based on the active model:

```text
1. Is execution broker-issued VerifiedRoute or direct?
2. Is the model/lane currently qualified for the required capability set?
3. Are memory, tools, postconditions and delivery runtime-owned in this path?
4. Is a terminal receipt present and explicit?
5. Would the same result survive a GPT-5.5 ↔ GPT-5.6-x ↔ vMesh fallback switch?
```

Any `no` or `unknown` is a HOLD, not an invitation to pin a raw provider/model.

## Model-switch protocol

A model switch is a route-intent change, never proof of eligibility.

When GPT-5.5, Terra, Luna, Sol, any future GPT-5.6-x, `token-solver-vmesh/auto`, or another lane becomes active:

1. record selected provider/model/lane/adapter and control surface;
2. resolve whether it passed `VerifiedRouteResolver`;
3. verify current manifest qualification and runtime compatibility hashes;
4. keep it `shadow_only` if no current evidence exists;
5. run the applicable fixture and model-switch regression before production eligibility;
6. do not alter tool authority, memory scope, approval policy, postconditions or delivery semantics based on the selected model;
7. issue a receipt-backed PASS/HOLD/FAIL closeout.

## Current rehydration packet — 2026-07-13T10:04Z

**Active milestone:** `M3M_INSTALLED_OBSERVE_ONLY_SHADOW_SOAK_NO_SEND_RETRY_R2`

**Current closeout:** `PASS_M3M_SOAK_ABORT_PRESERVED_GATEWAY_BLIP_DIAGNOSED_R2_READY`

**Last closed M3M state:** R1 installed observe-only no-send shadow soak aborted fail-closed at checkpoint `0005` with `GATEWAY_UNREACHABLE`; abort preservation, Gateway blip diagnostic, post-abort stability, safety counters, validation, R2 plan, and final closeout all completed. Evidence: `m3m_installed_shadow_soak_retry/M3M_POST_ABORT_HEALTH_STABILITY_SUMMARY.json`, `M3M_SOAK_ABORT_SAFETY_COUNTER_VALIDATION.json`, `M3M_INSTALLED_SHADOW_SOAK_NO_SEND_RETRY_R2_PLAN.json`, `M3M_SOAK_ABORT_VALIDATION.json`, and `M3M_SOAK_ABORT_PRESERVATION_FINAL_CLOSEOUT.json`.

**Gate state:** 30-minute post-abort health stability PASS (`6/6` probes, `0` failed); safety counters clean (`0` Telegram sends, external sends, provider/model shadow calls, real write tools, runtime/config/route/fallback/memory/Context Bridge mutation); no M3N/M4/enforcement/authority promotion started.

**Diagnostic:** Gateway event classified as `GATEWAY_RPC_TRANSIENT_TIMEOUT`, not a process crash; same PID persisted and Telegram recovered healthy.

**Next safe action:** run only `M3M_INSTALLED_OBSERVE_ONLY_SHADOW_SOAK_NO_SEND_RETRY_R2` with unchanged observe-only no-send/no-authority boundary, early-abort sentinel, and added reachability probes. Do not advance to M3N from R1 and do not mutate runtime/config/route/fallback/session authority.

**Rollback:** not applicable for the preservation package; no runtime/config mutation was made by Phases E-F-G.

## Prior rehydration packet — 2026-07-11T05:10Z

**Active milestone:** `M2_ADMISSION_AND_ROUTE_INTERCEPTOR`

**Current closeout:** `HOLD_QUEUE_RESUME_POST_DISPATCH_RAW_EXECUTION_SURFACES_NOT_INTERCEPTED`

**Last closed milestones:**

- `M0_DISCOVERY` → `PASS_DISCOVERY_COMPLETE_NO_MUTATION`; evidence `m0_freeze_map/M0_FINAL_MILESTONE_CLOSE_SUMMARY.md` and `m0_freeze_map/M0_G0_ALL_SURFACES_READBACK.json`.
- `M1_SCHEMA_AND_FIXTURE_CONTRACT` → `PASS_SCHEMA_FIXTURE_CONTRACT`; evidence `m1_schema_fixture_contract/M1_MILESTONE_CLOSE_SUMMARY.md` and `m1_schema_fixture_contract/M1_G1_READBACK.json`.

**M2 current state:** installed runtime patch reapplied to `get-reply-DGnDV9U-.js`; directive-only `/model` RouteIntent hook added before the early return; syntax/static checks passed; Gateway restart signal sent; pre/post-restart no-send synthetic owner-direct route-intent smokes passed for both session-preference and directive-only user-directive inputs. Default route exact-token smoke passed via `openai-codex/gpt-5.5`. Evidence: `m2_admission_route_interceptor/M2_REAPPLY_RECORD.json`, `m2_admission_route_interceptor/M2_NO_SEND_ROUTE_INTENT_SMOKE.json`, `m2_admission_route_interceptor/M2_DIRECTIVE_ROUTE_INTENT_SMOKE.json`, `m2_admission_route_interceptor/M2_POST_RESTART_VALIDATION.json`, and `m2_admission_route_interceptor/M2_CHECKPOINT_CLOSE_SUMMARY.md`.

**M2 blocker:** full all-surface M2 PASS remains blocked on live owner directive proof and queued/resumed/post-dispatch route-interceptor validation. Read-only M2Q classification confirmed queued/follow-up execution bypasses the direct `getReplyFromConfig()` interceptor: `agent-runner.runtime-a09vVD0N.js` can pass queued raw provider/model into `runWithModelFallback()`/`runEmbeddedPiAgent()`, and queue delivery can call `routeReply()`. Evidence: `m2_admission_route_interceptor/M2Q_QUEUE_RESUME_POST_DISPATCH_HOLD.json` and `M2Q_QUEUE_RESUME_REPAIR_PLAN.md`. Next safe step is to create a no-send queue admission harness/test seam before any queue runtime patch. Do not proceed to M3.

**Rollback:** restore `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/get-reply-DGnDV9U-.js.bak-umc-m2-reapply-20260711T0448Z`, run syntax check, restart Gateway.

**Durable milestone-update rule:** every milestone PASS/HOLD/FAIL must refresh `UMC_V1_MILESTONE_LEDGER.md`, `UMC_V1_IMPLEMENTATION_NOTEBOOK.md`, this rehydrator, and `UMC_V1_HANDOFF.json`; refresh troubleshooting notebook when any diagnostic/repair happened. Do not continue to the next milestone until these are updated and read back.

**Production state:** runtime UMC enforcement is partially patched for owner-direct route intent only. Full VerifiedRoute, M3 envelope/tool/delivery terminal receipts, model qualification, and external-send qualification are not implemented/qualified.

## Milestone close-summary contract

Every UMC milestone, observation window, repair, model qualification, model switch and production canary must close with a durable summary artifact before work moves on. Chat progress is not a substitute.

Required sections, in this order:

```text
Closeout: PASS | HOLD | FAIL | ABORT
Scope closed
Evidence paths and hashes
Mutation list (or none)
Invariant/sentinel results
Gate table
Known gaps and why they fail closed
Next gate and only permitted next work
Blocked work
Rollback state
```

Rules:

- Missing/empty/`UNKNOWN` closeout is `HOLD`.
- A partial scope may be `PASS` only if its excluded scope and next blocking gate are explicit; it cannot promote the wider milestone.
- Report the closeout immediately to Stick, then preserve the artifact and refresh the handoff packet.
- Do not continue repair or rollout behind an unresolved closeout.

## Minimum UMC handoff packet

Every milestone, model switch, troubleshooting event and repair must append or refresh a compact packet:

```json
{
  "project": "universal-model-contract",
  "contractVersion": "umc.v1",
  "timestamp": "<UTC ISO-8601>",
  "milestone": "M0..M8|INCIDENT|REPAIR",
  "closeoutStatus": "PASS|HOLD|FAIL|ABORT",
  "activeLane": "<lane or none>",
  "activeProviderModel": "<redacted-safe identifier or none>",
  "executionAuthority": "broker_verified_route|legacy_direct|unknown",
  "directBypass": false,
  "manifestStatus": "qualified|shadow_only|blocked|unknown",
  "requiredCapabilities": ["..."],
  "evidence": ["relative/path-or-hash"],
  "mutation": "none|approved bounded description",
  "rollback": "ready|not_applicable|blocked",
  "nextGate": "UMC_G#",
  "nextSafeAction": "one bounded action",
  "blocker": "none|explicit reason"
}
```

Do not use generic `status` as a replacement for `closeoutStatus`; missing closeout fails closed.

## Current initial state — 2026-07-11

```text
UMC status: design and read-only preparation
Production UMC mode: not implemented / no production mutation authorized
Known architectural issue: default broker route competes with channel direct override and session pins; direct execution can bypass selector contract
Known reliable worker for initial qualification: GPT-5.5 only inside a broker-owned contract-build lane, never as raw execution authority
Initial target lane: token-broker-vmesh/contract-build
Active initial milestone: M0 — freeze and map
Next hard gate: UMC_G0 — complete selection-authority and execution-site inventory
Permitted mutation: none; read-only discovery and notebook/evidence creation only
Do not: alter model routing, fallbacks, session/channel pins, provider auth, Gateway, memory routes, tool policy, external sends, or delivery behaviour
```

## Current state — 2026-07-11T05:46:30Z

```text
UMC status: M2Q restart-sentinel rerun PASS in no-send/static-wired scope
Production UMC mode: partial installed runtime guards only; full VerifiedRoute branding/manifest registry not implemented
Active route: openai-codex/gpt-5.5 with fallback ollama/deepseek-v4-pro:cloud
Owner execution authority: legacy direct plus M2 RouteIntent interceptor plus M2Q queued admission guard
Direct-bypass state: false in direct/session/directive and queued admission no-send fixtures
Latest evidence: m2_admission_route_interceptor/M2Q_RESTART_SENTINEL_RERUN_VALIDATION.json
Latest target hash: agent-runner.runtime-a09vVD0N.js sha256 6567099cf446f8675a00dd6a800b786013d0effbaae5c1b633d528272c0ab014
Rollback: agent-runner.runtime-a09vVD0N.js.bak-umc-m2q-20260711T0538Z sha256 2732df7cfb991b88636f187e74596f46cc7e24c94cf39e401fdb1d2c5f384b61
No-send gates: PASS for owner queued raw openai/gpt-5.5 → executable openai-codex/gpt-5.5, non-owner/group out of scope, direct M2 regressions, exact-token route smoke UMC_M2Q_RESTART_SENTINEL_ROUTE_OK_20260711N
Non-claim: no live Telegram queued delivery probe was sent
Next gate: M2 final scope decision or controlled queued-delivery fixture before M3
Do not: start M3 envelope/tool/delivery supervision until Stick explicitly accepts this M2Q scope or requests the queued-delivery fixture
```

## Pending prompt intake — M2R controlled queued-delivery fixture — 2026-07-11T06:01Z

```text
Prompt status: chunks 1-4 captured, final Banana terminator received; Phase A preflight BLOCKED
Chunk notebook: memory/notebooks/umc-m2r-queued-delivery-prompt-chunks.md
Requested next gate: M2R one controlled end-to-end queued-delivery fixture after restart
Fixture token: UMC_M2R_SINGLE_QUEUED_DELIVERY_OK_20260711O
Delivery constraint: exactly one owner Telegram queued message, token-only or minimal line, no commentary/debug/provider/internal metadata
PASS requirements: intended queued path, admission exactly once, execution exactly once, guard-before-fallback ordering, no bypass, observed route/provider/model/fallback/direct-execution/guard decision/execution result, delivery ack, no duplicate/wrong destination, no dry-run delivery, protected-state equality and queue-depth rest
Boundary: VerifiedRoute branding and full capability-manifest registry stay outside M2R
Execution hold: re-applied after Phase A preflight blocker; do not build fixture, dry-run, live-send, accept M2, or start M3 until unrelated working-tree changes are resolved/isolated and preflight is rerun cleanly
Required preflight failure status: UMC_M2R_QUEUED_DELIVERY_FIXTURE_BLOCKED_PREFLIGHT
Mutation freeze while preparing: no route/channel/session/fallback/provider/Gateway/tool/memory/Context Bridge/Runtime Kernel/delivery-policy/production-routing authority mutation
M2 acceptance if fixture passes: UMC_M2_ACCEPTED_GUARD_ORDER_RESTART_AND_SINGLE_QUEUED_DELIVERY_PROVEN
Current M2R closeout: BLOCKED_M2R_PREFLIGHT_OR_AUTHORITY_UNAVAILABLE because preflight found 1329 unrelated local changes before any fixture build/send
M3 gate: start separately only after M2 acceptance; no model promotion or broader production authority
M3.0 outputs required after M2 acceptance: M3_COMPONENT_AND_CALL_PATH_MAP.json, M3_SCOPE_AND_MUTATION_CONTRACT.md, M3_FIXTURE_CORPUS.json, M3_ROLLBACK_PLAN.md
M3.1 starts mock/no-send only with runtime-owned vertical path: envelope -> tool registry snapshot -> provider adapter -> proposed tool call -> supervisor -> receipt -> postcondition -> response assembler -> delivery receipt -> terminal UMC receipt
M3 hard rule: model prose completion never PASS without runtime receipt
Evidence/scope: immutable hash evidence, preserve failures, clean scoped closeout, no unrelated route/model/fallback/memory/cache/Telegram config changes
```

## Required response format after rehydration

```text
UMC REHYDRATED — PASS|HOLD
Milestone: <...>
Live authority: <broker_verified_route|legacy_direct|unknown>
Active lane/model: <...>
Qualification: <...>
Evidence: <paths/hashes>
Mutation: none|<approved bounded change>
Next gate: <...>
Next safe action: <...>
Blocker: none|<...>
```

No action may follow a `HOLD` until the stated missing evidence or authorization is resolved.

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
