# Universal Model Contract (UMC) v1 — Implementation Notebook

**Status:** design and read-only preparation
**Authority:** UMC v1 low-level design supplied by Stick, 2026-07-11
**Production mutation:** not authorized by this notebook
**Primary principle:** operational guarantees belong to runtime control-plane code, never to the selected model.

## Purpose

Make owner-turn behaviour invariant across every control surface and route:

- `token-broker-vmesh/auto` and future broker lanes;
- GPT-5.5, GPT-5.6 Terra/Luna/Sol and future GPT-5.6 variants;
- token-solver v2/v3/v4/vMesh lanes;
- channel preferences, session preferences, user directives, queued/resumed/post-dispatch turns;
- qualified fallbacks.

A model may vary in reasoning quality and wording. It must not vary memory prefetch, tool authority, action verification, fallback eligibility, deterministic delivery, or terminal closeout.

## Current known routing defect

The live system has competing model-selection authorities:

1. default broker route (`token-broker-vmesh/auto`);
2. channel model override;
3. session provider/model override or pin.

Direct channel/session bindings can bypass the broker route. Treat all model/channel/session selection as `RouteIntent`, never as an execution binding.

## Non-negotiable invariants

| ID | Invariant |
|---|---|
| UMC-I1 | Only the broker contract router may issue a production route. |
| UMC-I2 | Owner production execution may not begin with only `{provider, model}`. |
| UMC-I3 | Execution requires broker-issued opaque `VerifiedRoute`. |
| UMC-I4 | Admission, required capabilities, envelope, tool registry, fallback set and delivery policy are fixed before provider execution. |
| UMC-I5 | Required actions cannot finish as prose-only success. |
| UMC-I6 | Fallbacks must satisfy the same or stronger capability contract. |
| UMC-I7 | Model preferences are route intents, not route authority. |
| UMC-I8 | Runtime owns final sanitation, threading, media normalization, dedupe and delivery verification. |
| UMC-I9 | Every admitted owner turn has exactly one PASS/HOLD/FAIL terminal receipt. |
| UMC-I10 | Debug direct-provider mode is isolated, labelled, no-send, no-memory-write and excluded from production metrics. |

## Core contract objects

```ts
type RouteIntent = {
  preferredLane?: string;
  preferredModelFamily?: string;
  requestedReasoning?: "low" | "medium" | "high" | "xhigh" | "max";
  source: "default" | "channel_policy" | "session_preference" | "user_directive" | "operator_debug";
  hardPreference: false;
};

type VerifiedRoute = Readonly<{
  contractVersion: "umc.v1";
  routeId: string;
  lane: string;
  provider: string;
  model: string;
  adapter: string;
  required: RequiredCapabilities;
  toolProtocolVerified: boolean;
  memoryEnvelopeVerified: boolean;
  deliveryHandoffVerified: boolean;
  manifestHash: string;
  fallbackSet: readonly VerifiedFallbackRef[];
  directBypass: false;
  issuedAt: string;
  expiresAt: string;
}>;
```

`VerifiedRoute` must be branded/private to the broker package or backed by a broker-signed route token for cross-process execution. A structurally similar object is not valid.

## Required capability policy

`ContractAdmission` deterministically derives:

- `memoryPrefetch`: required / eligible / forbidden / not_required;
- `contextBridge`: required / eligible / forbidden / not_required;
- `toolExecution`, `artifactWrite`, `externalSend`, `elevatedExecution` with the same values;
- `responseMode`: answer / action / artifact / external_send / clarification / hold_only;
- concrete required postconditions.

Ambiguous possible side effects become clarification or HOLD. They never downgrade to answer-only.

## Target execution sequence

```text
IngressNormalizer
  -> ContractAdmission
  -> RouteIntentResolver
  -> CapabilityManifestRegistry
  -> VerifiedRouteResolver + DirectBypassFirewall
  -> ContractEnvelopeBuilder
       -> MemoryPrefetchCoordinator
       -> ContextBridgeReader
       -> CanonicalToolRegistry
       -> AuthorityPolicyResolver
       -> DeliveryPolicyResolver
  -> ProviderAdapterExecutor
  -> ToolExecutionSupervisor
  -> PostconditionVerifier
  -> ResponseAssembler
  -> DeliverySupervisor
  -> ReceiptEmitter
```

Provider adapters only normalize provider protocol events. They may not execute tools, write memory, select fallback, or deliver messages.

## Capability manifest eligibility

A selectable lane needs current proof, not merely a model name.

```text
manifest current
+ supports umc.v1
+ adapter supports required tool protocol
+ memory/context envelope compatible
+ canonical tool registry hash matches
+ deterministic delivery handoff verified
+ qualification evidence current
= eligible
```

Any failed predicate is `HOLD_CONTRACT_UNAVAILABLE`; it never triggers raw fallback.

## Initial implementation lane

Create a broker-owned virtual lane:

```text
token-broker-vmesh/contract-build
  -> qualified GPT-5.5 adapter only, initially
```

This is not a raw GPT-5.5 route. GPT-5.5 is the first worker inside a UMC-controlled lane. Terra/Luna/Sol and other models get separate shadow-only manifests, then individual qualification.

## Milestones and gates

### M0 — Freeze and map (read-only)

Deliver:

- selection-authority map;
- agent/provider entrypoint map;
- tool and delivery call-site map;
- fallback map;
- native-command-surface map;
- prechange config/route snapshot and mutation sentinel.

**Gate G0:** every default, channel, session, directive, queued, resumed, scheduled and post-dispatch route is mapped to file/function/precedence. No mutation.

### M1 — Contract schema and fixtures

Deliver versioned schemas for admission, manifest, route, envelope, tool/delivery/terminal receipts; error registry; hashed fixture corpus; adversarial review.

**Gate G1:** schemas round-trip; direct bypass fixed false for production schema; PASS/HOLD/FAIL representable; required capabilities cannot be omitted.

### M2 — Admission and route interceptor

Add `ContractAdmission`, `RouteIntentResolver`, manifest registry, branded `VerifiedRoute`, direct-bypass firewall, and static import/AST enforcement.

**Gate G2:** zero unapproved raw execution sites; forged route rejected; all queued/resumed/post-dispatch paths pass.

**Gate G3:** no selectable lane lacks current manifest and qualification evidence.

### M3 — Envelope, tools and delivery supervision

Build envelope, runtime memory/context injection, canonical tool registry, authority grants, tool supervisor, postcondition verifier, success-language firewall, delivery supervisor, terminal receipts.

**Gates G4–G6/G8:** tool parity, memory parity, no prose-only action success, deterministic verified delivery.

### M4 — GPT-5.5 contract-build no-send qualification

Owner Web and Telegram fixtures only. Read/local write/artifact/approval/no-send are eligible; unqualified external sends and elevated execution HOLD.

**Exit:** G3–G6/G8 PASS; no direct provider execution; receipt coverage 100%.

### M5 — Per-model eligibility matrix

Qualify separately: GPT-5.5, Terra, Luna, Sol, then other approved lanes. Failed lanes stay `shadow_only` or `blocked`.

**Gate G9:** model-switch matrix must preserve operational receipts across GPT-5.5 ↔ Terra ↔ Luna ↔ Sol ↔ verified fallback.

### M6 — Shadow enforcement

UMC computes receipts for owner turns without changing visible routing. Classify all direct paths and every would-be HOLD.

**Gate G10:** no unexplained divergence; complete receipts; corpus coverage, not elapsed time alone.

### M7 — Enforced owner canary and rollout

Direct pins become intents, default owner route becomes `contract-build`, and manifest-only fallback is enforced. One hash-locked rollback policy switch is proven first.

**Gate G11:** zero direct bypass, unmanifested selections, required-memory omissions, prose-success violations and missing receipts. Any non-zero condition rolls back.

### M8 — Continuous regression

Requalify affected lanes on OpenClaw/runtime, adapter, model, tool schema, authority, memory/context envelope, delivery, admission or fallback changes.

## Required health signals

Per owner turn, emit a non-sensitive receipt:

```json
{
  "contract":"umc.v1",
  "route":"token-broker-vmesh/contract-build",
  "directBypass":false,
  "memory":"injected|not_required|forbidden|hold",
  "tools":"registered|not_required|forbidden|hold",
  "requiredAction":"verified|not_required|clarification|hold|failed",
  "fallback":"none|verified|exhausted|not_allowed",
  "delivery":"deterministic_verified|not_attempted_hold|failed",
  "closeout":"PASS|HOLD|FAIL"
}
```

Severity-one rollback triggers: production direct bypass; unmanifested lane selected; required memory omission; success without postcondition; missing terminal receipt; PASS delivery without delivery receipt; accepted manifest/runtime-hash mismatch.

## Milestone state as of 2026-07-11T02:49Z

- `M0_DISCOVERY`: `PASS_DISCOVERY_COMPLETE_NO_MUTATION` — all execution/selection/delivery boundaries mapped; no production mutation.
- `M1_SCHEMA_AND_FIXTURE_CONTRACT`: `PASS_SCHEMA_FIXTURE_CONTRACT` — schemas and fixtures validate; no runtime mutation.
- `M2_ADMISSION_AND_ROUTE_INTERCEPTOR`: `STARTED` — implement fail-closed owner-scope route admission/interceptor with backups, tests, controlled restart and explicit closeout.

Durable documentation rule: every milestone PASS/HOLD/FAIL must refresh `UMC_V1_MILESTONE_LEDGER.md`, this notebook, `UMC_V1_REHYDRATOR.md`, and `UMC_V1_HANDOFF.json`; troubleshooting notebook must also be refreshed for diagnostics/repairs. A chat message alone is never a milestone closeout.

## Safe next action

Next safe UMC action is `M3M_INSTALLED_OBSERVE_ONLY_SHADOW_SOAK_NO_SEND_RETRY_R2`: rerun the installed observe-only no-send shadow soak with the same no-authority boundary, plus the repaired early-abort sentinel and added reachability probes. Do not advance to M3N/M4/enforcement and do not mutate runtime/config/route/fallback/session authority from the M3M R1 abort preservation package.

## M3M soak abort preservation closeout — 2026-07-13T10:04:21Z

**Closeout:** `PASS_M3M_SOAK_ABORT_PRESERVED_GATEWAY_BLIP_DIAGNOSED_R2_READY`

M3M R1 installed observe-only no-send shadow soak aborted fail-closed at checkpoint `0005` with `GATEWAY_UNREACHABLE`. Abort evidence was rehydrated and preserved. Diagnostic evidence classified the event as `GATEWAY_RPC_TRANSIENT_TIMEOUT`: the Gateway PID remained stable, RPC was OK at the abort checkpoint, and listener/RPC/Telegram recovered during the post-abort window.

Validation completed:

- 30-minute post-abort health stability window: `6/6` probes PASS, `0` failed.
- Safety counters clean: Telegram sends `0`, external sends `0`, provider/model shadow calls `0`, real write tools `0`, runtime/config/route/fallback/memory/Context Bridge mutation `0`.
- No M3N, M4, VerifiedRoute enforcement, or authority promotion started.
- R2 plan prepared with unchanged 12h/24-checkpoint no-send/no-authority boundary, an early-abort sentinel, and added loopback/retry reachability probes.
- Observer harness `check` path repaired to scan abort artifacts instead of reporting stale-only status.

Evidence:

```text
m3m_installed_shadow_soak_retry/M3M_POST_ABORT_HEALTH_STABILITY_SUMMARY.json
m3m_installed_shadow_soak_retry/M3M_SOAK_ABORT_SAFETY_COUNTER_VALIDATION.json
m3m_installed_shadow_soak_retry/M3M_INSTALLED_SHADOW_SOAK_NO_SEND_RETRY_R2_PLAN.json
m3m_installed_shadow_soak_retry/M3M_SOAK_ABORT_VALIDATION.json
m3m_installed_shadow_soak_retry/M3M_SOAK_ABORT_PRESERVATION_FINAL_CLOSEOUT.json
```

Next milestone: `M3M_INSTALLED_OBSERVE_ONLY_SHADOW_SOAK_NO_SEND_RETRY_R2`. R1 remains an aborted run; do not advance to M3N from it.

## M2 checkpoint — 2026-07-11T04:50Z

**Closeout:** `HOLD_RESTARTED_NO_SEND_ROUTE_INTENT_PASS_LIVE_ASYNC_PENDING`

The installed runtime target lacked the previously recorded M2 helper/call sites, so M2 was reapplied against `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/get-reply-DGnDV9U-.js` with a fresh rollback backup at `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/get-reply-DGnDV9U-.js.bak-umc-m2-reapply-20260711T0448Z`.

Validation completed:

- `node --check` passed for the patched target.
- Static grep found helper/call-site markers: helper lines 170/179/213/218; call sites 3772/3890.
- Gateway restart signal was sent to load the runtime patch.
- No-send synthetic owner-direct smoke passed: raw session preference `openai/gpt-5.5` was persisted as `umcV1RouteIntent`; executable route was forced to default `openai-codex/gpt-5.5`; `directBypass=false`; `externalSend=false`.

Evidence:

```text
m2_admission_route_interceptor/M2_REAPPLY_RECORD.json
m2_admission_route_interceptor/M2_NO_SEND_ROUTE_INTENT_SMOKE.json
m2_admission_route_interceptor/M2_CHECKPOINT_CLOSE_SUMMARY.md
```

Full M2 remains HOLD pending live owner-route smoke and queued/resumed/post-dispatch coverage. Do not proceed to M3 until M2 closes explicitly.

## M2 directive-only repair checkpoint — 2026-07-11T05:10Z

**Closeout:** `PASS_NO_SEND_SESSION_AND_DIRECTIVE_ROUTE_INTENT_REPAIR_HOLD_LIVE_ASYNC_PENDING`

The previous post-`/model` HOLD was narrowed: the residual-text smoke (`/model openai/gpt-5.5 Reply exactly ...`) was not a valid directive path because legacy parsing intentionally clears model directives when residual non-directive text remains. The actual directive-only `/model` branch returns early after persisting model selection, so M2 needed a pre-return RouteIntent hook there.

Repair added a directive-only `/model` call to `applyUmcV1OwnerRouteInterceptor()` before the early return in `get-reply-DGnDV9U-.js`.

Validation completed pre/post Gateway restart:

- `node --check` passed.
- Session-preference no-send smoke passed: raw `openai/gpt-5.5` persisted as `source=session_preference`, executable `openai-codex/gpt-5.5`, `directBypass=false`, `externalSend=false`.
- Directive-only no-send smoke passed with owner metadata: raw `/model openai/gpt-5.5` persisted as `source=user_directive`, executable `openai-codex/gpt-5.5`, `directBypass=false`, `externalSend=false`.
- Default-route exact-token smoke passed post-restart: `UMC_M2_POST_RESTART_ROUTE_OK_20260711J` via `openai-codex/gpt-5.5`.

Evidence:

```text
m2_admission_route_interceptor/M2_DIRECTIVE_ROUTE_INTENT_SMOKE.json
m2_admission_route_interceptor/M2_POST_RESTART_VALIDATION.json
m2_admission_route_interceptor/M2_CHECKPOINT_CLOSE_SUMMARY.md
```

Remaining blocker: full all-surface M2 still requires live owner directive proof and queued/resumed/post-dispatch validation. Do not proceed to M3.

## M2Q queue admission guard — 2026-07-11T05:46Z

**Closeout:** `PASS_M2Q_QUEUE_ADMISSION_GUARD_WIRED_NO_SEND_STATIC`

After reading the UMC M2 Gateway/Telegram lesson preflight, the queued/follow-up runtime was patched at the owning boundary rather than by changing global routes or sending Telegram probes.

Implementation:

- Created rollback backup: `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/agent-runner.runtime-a09vVD0N.js.bak-umc-m2q-20260711T0538Z` (`2732df7cfb991b88636f187e74596f46cc7e24c94cf39e401fdb1d2c5f384b61`).
- Added exported no-send seam `applyUmcV1QueuedRouteAdmission` to classify owner-direct queued/follow-up raw provider/model as RouteIntent.
- Wired the seam in `createFollowupRunner()` before `runWithModelFallback()` and `runEmbeddedPiAgent()`.
- Owner-direct queued raw `openai/gpt-5.5` is forced to configured default executable `openai-codex/gpt-5.5`; non-owner and group fixtures remain out of scope.

Validation completed pre/post Gateway restart:

- `node --check` passed.
- Pure queue-admission no-send smoke passed: `source=queued_followup`, requested `openai/gpt-5.5`, executable `openai-codex/gpt-5.5`, `directBypass=false`, `externalSend=false`.
- Static order check passed: queue admission call occurs before queued `runWithModelFallback()` / `runEmbeddedPiAgent()`.
- Direct M2 session-preference and directive-only no-send regressions passed.
- Default-route exact-token smoke passed pre-restart (`UMC_M2Q_PRE_RESTART_ROUTE_OK_20260711L`) and post-restart (`UMC_M2Q_POST_RESTART_ROUTE_OK_20260711M`) via `openai-codex/gpt-5.5`.
- Telegram direct readback remains `openai-codex/gpt-5.5`, fallback `ollama/deepseek-v4-pro:cloud`, queue depth 0.

Evidence:

```text
m2_admission_route_interceptor/M2Q_PRE_RESTART_QUEUE_ADMISSION_VALIDATION.json
m2_admission_route_interceptor/M2Q_POST_RESTART_QUEUE_ADMISSION_VALIDATION.json
```

Non-claim: no live Telegram queued delivery probe was sent; VerifiedRoute branding/manifest registry is still not implemented. Do not proceed to M3 until Stick accepts this no-send/static-wired M2Q closeout or requests a controlled queued-delivery fixture.

## M2R queued-delivery fixture prompt intake — 2026-07-11T06:01Z

**Status:** `PROMPT_INTAKE_PENDING_BANANA_TERMINATOR`

Stick started a split prompt for the remaining M2 evidence gap: prove one controlled, end-to-end queued-delivery path after restart. The prompt explicitly says to persist chunks to notebooks and memories and not begin execution until the full prompt is received. Chunk 1 is stored at:

```text
memory/notebooks/umc-m2r-queued-delivery-prompt-chunks.md
```

Captured objective/boundaries so far:

- Close the M2 evidence gap with one controlled queued-delivery fixture.
- If and only if the fixture passes cleanly, mark M2/M2Q accepted and begin M3 planning/implementation.
- Keep VerifiedRoute branding and full capability-manifest registry outside M2R; preserve clean M2/M3 boundary.
- Phase A requires rehydration, repository/branch/working-tree/Gateway/Telegram/runtime hash/route/queue/rollback checks, guard-order confirmation, no unrelated local changes, and a fresh pre-fixture snapshot.
- Mutations are frozen for default route, channel model config, session pinning, fallbacks, provider credentials, Gateway config, tool registry, memory authority, Context Bridge authority, Runtime Kernel authority, delivery policy, and production routing authority.
- Phase B fixture must default dry-run/no-send, require explicit live-send flag, permit exactly one queued Telegram owner-direct delivery, use an exact unique token, prevent repeats, capture full evidence, clean up, leave runtime config unchanged, emit JSON and human closeout.

Do not build or run the fixture until the remaining prompt arrives with the final `Banana` terminator.

### M2R prompt chunk 2 captured — 2026-07-11T06:01Z

**Status:** `PROMPT_INTAKE_PENDING_BANANA_TERMINATOR`

Chunk 2 continues the controlled queued-delivery fixture definition and remains incomplete, ending mid-sentence in M3.0 after `map the current memory-prefetch path;`. Captured additions:

- Exact fixture token: `UMC_M2R_SINGLE_QUEUED_DELIVERY_OK_20260711O`.
- Delivered Telegram message must contain only the token or the minimal line `UMC M2 queued-delivery fixture: UMC_M2R_SINGLE_QUEUED_DELIVERY_OK_20260711O`.
- No commentary, debug dumps, stack traces, internal paths, provider metadata, or multiple Telegram messages.
- Fixture PASS requires independent verification of:
  - intended queued-delivery path;
  - guard execution before fallback/model execution;
  - no queued/post-dispatch bypass;
  - queue admission exactly once;
  - queue execution exactly once;
  - observed route/provider/model/fallback/direct-execution/guard decision/execution result;
  - exactly one Telegram owner-chat message with correct destination/account and acknowledgment;
  - no duplicate/unrelated delivery and no dry-run delivery;
  - protected-state equality for runtime hash, OpenClaw/Gateway config, default route, Telegram route state, fallback chain, tool registry, memory authority, Context Bridge authority, Runtime Kernel authority, queue state, and service health.
- Allowed closeouts are the explicit `PASS_M2R...`, `FAIL_M2R...`, or `BLOCKED_M2R...` enum set from the prompt; ambiguous/unverified cannot PASS.
- If the fixture passes, mark M2/M2Q accepted with status `UMC_M2_ACCEPTED_GUARD_ORDER_RESTART_AND_SINGLE_QUEUED_DELIVERY_PROVEN` and start M3 as a separate bounded milestone.
- M2 accepted scope proves direct session/directive guards, queue no-send admission, guard order before fallback/agent execution, restart persistence, one live queued Telegram delivery, and no protected runtime mutation.
- M2 explicitly does not prove opaque/branded VerifiedRoute, capability-manifest qualification, universal contract-envelope parity, runtime-owned tool authority, postcondition verification, universal deterministic delivery receipts, or model-equivalent fallback.
- M3 objective captured so far: runtime-owned contract envelope, canonical tool authority/registration, action-required supervision, postcondition verification, deterministic delivery receipts, and prose-success prevention; no model promotion or production authority broadening.

Do not begin execution until the prompt terminator arrives.

### M2R/M3 prompt chunk 3 captured — 2026-07-11T06:01Z

**Status:** `PROMPT_INTAKE_PENDING_BANANA_TERMINATOR`

Chunk 3 continues M3.0/M3.1 requirements and remains incomplete, ending mid-sentence after `restore exact pre-change state;`. Captured additions:

- M3.0 must map Context Bridge injection, canonical tool-list construction, tool execution/approval boundaries, artifact-write and external-send paths, final response rendering, Telegram/Web delivery and duplicate suppression, and all model-implied-completion-without-runtime-proof sites.
- M3.0 must reconcile those paths with `UNIVERSAL_MODEL_CONTRACT_UMC_V1_LLD_IMPLEMENTATION_PLAN.md`.
- Required M3.0 outputs:
  - `M3_COMPONENT_AND_CALL_PATH_MAP.json`
  - `M3_SCOPE_AND_MUTATION_CONTRACT.md`
  - `M3_FIXTURE_CORPUS.json`
  - `M3_ROLLBACK_PLAN.md`
- M3.1 initial implementation slice must be a complete runtime-owned vertical path: admitted turn → contract-envelope builder → canonical tool registry snapshot → provider adapter → proposed tool call → tool supervisor → tool receipt → postcondition verifier → response assembler → deterministic delivery receipt → terminal UMC receipt.
- Begin M3.1 with mock-provider and no-send fixtures; no live external sends.
- Required/formalized runtime types: `ContractEnvelope`, `CanonicalToolDefinition`, `ToolAuthorityGrant`, `ProposedToolCall`, `ToolExecutionReceipt`, `RequiredPostcondition`, `PostconditionEvidence`, `DeliveryReceipt`, `UniversalContractReceipt`.
- Hard behavior for action-required turns maps valid tool/postcondition to PASS; missing proposal/tool/approval/postcondition to HOLD variants; tool/delivery failure to FAIL. Model prose such as “done/sent/updated/created/fixed” can never close PASS without matching runtime receipt.
- M3 exit criteria require mock/no-send proof of runtime-owned envelope, fixed memory/tool/delivery policy before provider execution, canonical tools, runtime-owned authority, schema-validated proposals, HOLD for missing proposal, independent postconditions, truthful final status, deterministic delivery receipt, no adapter direct tool/delivery calls, and protected runtime state unchanged outside approved mutation set.
- Evidence discipline: immutable hash-addressed evidence, command/exit/stdout/stderr/timestamps/hashes/observed state, expected-vs-observed distinction, preserve failures, accurate provider/model and sent-message records, no credentials/private IDs/secrets, rollback available, clean working tree, scoped commits only, no push unless authorized.
- Scope discipline: no unrelated routing refactor, production model/fallback change, raw provider escape, memory expansion, cache/artifact-memory promotion, Telegram config change, more than one queued-delivery fixture message, mixed M2/M3 mega-patch, or VerifiedRoute/manifest completion claim.

Final terminator `Banana` arrived at 2026-07-11T06:01Z. Phase A preflight ran and failed closed as `BLOCKED_M2R_PREFLIGHT_OR_AUTHORITY_UNAVAILABLE`: the repository working tree contained 1329 unrelated local changes, violating the prompt's no-unrelated-local-changes gate. No fixture build, dry-run, live Telegram send, config/route/Gateway mutation, M2 acceptance, or M3 implementation occurred. Evidence: `m2_admission_route_interceptor/m2r_single_queued_delivery/M2R_PREFLIGHT_SNAPSHOT.json` and `M2R_BLOCKED_PREFLIGHT_OR_AUTHORITY_UNAVAILABLE.json`.

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
