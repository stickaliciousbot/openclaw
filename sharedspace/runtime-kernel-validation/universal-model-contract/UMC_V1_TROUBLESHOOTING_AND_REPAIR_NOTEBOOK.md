# Universal Model Contract (UMC) v1 — Troubleshooting and Repair Notebook

## 2026-07-11T02:49Z — Handoff JSON comma repair

**Symptom:** `UMC_V1_HANDOFF.json` readback showed missing comma after `closeoutStatus: "STARTED"`, making the handoff invalid JSON.

**Repair:** inserted the comma and read back the corrected file.

**Impact:** documentation/handoff artifact only; no runtime/config/route/session/provider mutation.

**Prevention rule:** after every handoff edit, validate or direct-read the JSON before using it as a gate artifact.

## 2026-07-11T04:50Z — M2 active-runtime patch missing, reapplied

**Symptom:** `M2_APPLY_RECORD.json` claimed the M2 helper and call sites were present, but static grep on the active installed runtime returned no `applyUmcV1OwnerRouteInterceptor`, `isUmcV1OwnerDirectScope`, or `umcV1RouteIntent` markers. The active installed file therefore did not match the recorded M2 apply state.

**Repair:** created fresh backup `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/get-reply-DGnDV9U-.js.bak-umc-m2-reapply-20260711T0448Z`, reapplied the M2 helper and two call sites to `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/get-reply-DGnDV9U-.js`, ran syntax/static checks, requested Gateway restart, and ran a synthetic owner-direct no-send route-intent smoke.

**Impact:** installed runtime mutation; no external send during smoke. No provider credentials, default route, fallback, session/channel policy, memory route, tool policy, or external-send qualification changed in this repair.

**Validation:** target SHA `3a50e82a1e7f18bdd00faea3ee89a7711678797342ff3673be938ce08a217597`; backup SHA `d3b56d10ce810b8fd947fbac60d369bd22de3efe3d58b4e0b35989dc1dcda907`; no-send smoke evidence `M2_NO_SEND_ROUTE_INTENT_SMOKE.json` showed raw `openai/gpt-5.5` session preference captured as RouteIntent and executable route forced to default `openai-codex/gpt-5.5`, `directBypass=false`, `externalSend=false`.

**Status:** `HOLD_RESTARTED_NO_SEND_ROUTE_INTENT_PASS_LIVE_ASYNC_PENDING` — full M2 remains blocked on live owner smoke and queued/resumed/post-dispatch validation.

## 2026-07-11T05:10Z — M2 directive-only RouteIntent capture repaired

**Symptom:** synthetic post-`/model` smoke initially remained HOLD: the observed `umcV1RouteIntent` stayed `source=default` instead of capturing requested raw `openai/gpt-5.5` as `source=user_directive`.

**Diagnosis:** the failing residual-text smoke (`/model openai/gpt-5.5 Reply exactly ...`) was not a valid directive path because legacy parsing clears model directives when residual non-directive text remains. A valid directive-only `/model openai/gpt-5.5` smoke also required owner metadata; unauthorized synthetic senders do not persist `/model` changes. The real repair target was the directive-only `/model` branch, which returns early after persisting a model switch acknowledgement.

**Repair:** added a pre-return call to `applyUmcV1OwnerRouteInterceptor()` inside the directive-only `/model` branch in `get-reply-DGnDV9U-.js`.

**Validation:** pre/post restart `node --check` passed; session-preference no-send smoke passed; directive-only owner-metadata no-send smoke passed with `source=user_directive`, requested `openai/gpt-5.5`, executable `openai-codex/gpt-5.5`, `directBypass=false`, `externalSend=false`; default-route exact-token smoke returned `UMC_M2_POST_RESTART_ROUTE_OK_20260711J` via `openai-codex/gpt-5.5`.

**Status:** `PASS_NO_SEND_SESSION_AND_DIRECTIVE_ROUTE_INTENT_REPAIR_HOLD_LIVE_ASYNC_PENDING` — no-send M2 owner-direct session/directive repair passed, but full all-surface M2 remains blocked on live owner directive proof and queued/resumed/post-dispatch validation.

**Status:** operational playbook; no production mutation authority
**Use when:** model changes, a selector/direct route differs, tools/memory/delivery drift, a receipt is absent, or an action is reported complete without proof.

## Prime directive

Never repair a model-quality symptom by adding another raw channel/session/provider pin. First determine whether the turn crossed UMC admission, route verification, envelope, tool/postcondition, delivery and receipt boundaries.

A model may fail. The contract must fail closed.

## Rapid triage order

1. **Protect:** freeze proposed route/config mutation; preserve logs and receipts; do not resend external messages.
2. **Classify:** is this a model-quality issue, a direct-bypass issue, a capability-manifest issue, a runtime contract issue, a tool/postcondition issue, or a delivery issue?
3. **Establish provenance:** capture turn ID, trace ID, channel, session, selected route/provider/model/adapter, contract version, receipt ID, and timestamp.
4. **Check terminal truth:** PASS requires verified postconditions and deterministic delivery receipt. Missing/empty/unknown is HOLD.
5. **Contain:** remove the affected lane from eligibility or set it shadow-only; do not silently fall back raw.
6. **Repair:** make the smallest change at the owning control-plane boundary.
7. **Prove:** rerun the exact failed fixture plus the nearest model-switch and fallback regressions.
8. **Close loop:** issue explicit PASS/HOLD/FAIL, evidence path, mutation list, and rollback state before further work.

## Triage matrix

| Symptom | Likely class | Immediate action | Terminal safety state |
|---|---|---|---|
| Different behaviour after switching GPT-5.5 to Terra/Luna/Sol | route intent bypass / unqualified manifest | compare receipts and route provenance; mark lane shadow-only | HOLD_MODEL_CONTRACT_REGRESSION |
| `Execution: direct` on owner production turn | direct-bypass | block promotion; trace channel/session/directive precedence | HOLD_DIRECT_BYPASS_DETECTED |
| Tools visible but model replies prose instead of acting | required-action supervision missing or model protocol failure | prohibit success language; verify `requiredAction`; no blind retry | HOLD_REQUIRED_ACTION_NOT_PROPOSED |
| Model proposes unknown tool | adapter/model protocol mismatch | reject proposal; preserve canonical registry hash | HOLD_INVALID_TOOL_CALL |
| Required memory absent | prefetch/envelope failure | do not call provider; isolate source/selector cause | HOLD_MEMORY_PREFETCH_UNAVAILABLE |
| Fallback works but tools/memory differ | fallback equivalence failure | reject fallback route and hold | HOLD_FALLBACK_CONTRACT_DRIFT |
| “Done/Sent/Created” without evidence | response assembler / postcondition fault | block/rewrite success response; inspect tool receipts | HOLD_POSTCONDITION_UNVERIFIED |
| Reply reached wrong chat/thread or duplicates | deterministic-delivery fault | suppress further sends; inspect delivery receipt/dedupe key | FAIL_DELIVERY |
| Terminal receipt missing/UNKNOWN | closeout projector/readback fault | fail closed; repair projector before promotion | HOLD_RECEIPT_MISSING |
| Manifest valid yesterday but adapter/runtime changed | stale qualification | invalidate lane immediately | HOLD_MANIFEST_STALE |

## Evidence pack — minimum before diagnosis

Create a sanitized evidence bundle containing:

```text
turn/trace identifiers
normalized-origin summary
admission decision and policy hash
route intent sources and resolved precedence
VerifiedRoute reference and manifest hash
runtime compatibility snapshot
contract envelope hash and stage states
canonical tool-registry hash
all tool receipts and postcondition references
fallback attempt references
delivery receipt
total terminal receipt
relevant non-secret logs
before/after route/config hashes if a mutation occurred
```

Never include API keys, tokens, raw private memory, raw context bridge sources, unredacted personal identifiers, or full inbound message dumps.

## Deterministic diagnosis procedures

### A. “It works on GPT-5.5 but not model X”

1. Confirm both turns were owner turns with comparable admission requirements.
2. Compare `directBypass`, route/lane, adapter, manifest hash, tool registry hash, envelope hash, fallback set and receipt fields.
3. If the route differs, this is a routing/eligibility problem before it is a model problem.
4. If route/envelope/tool hashes match but canonical model events differ, run the model's fixture corpus in shadow.
5. Keep model X `shadow_only` until G3–G9 pass. Do not make GPT-5.5 a hidden direct fallback.

### B. Direct provider or model pin detected

1. Identify source: default config, channel override, session override, user directive, queued/resumed state, or plugin path.
2. Confirm whether it crossed `VerifiedRouteResolver`.
3. In enforced scope, terminate before provider request and emit attempted-bypass telemetry.
4. In observe scope, preserve the live result but issue a shadow HOLD and record migration target as `RouteIntent`.
5. Repair the source precedence or wrapper, then run forged-route, channel-intent, session-intent and post-dispatch fixtures.

### C. Tool/action completion fault

1. Determine whether `toolExecution` or a postcondition was required by admission.
2. Verify canonical tool definition and authority policy snapshots.
3. Verify argument-schema outcome, idempotency key, execution status, and postcondition evidence.
4. If no valid tool proposal occurred, return `HOLD_REQUIRED_ACTION_NOT_PROPOSED`; do not report success.
5. If a side effect is uncertain, return `HOLD_POSTCONDITION_UNVERIFIED`; no automatic retry unless idempotency is proven.
6. Run prose-trap, invalid-tool, malformed-argument, no-tool-proposal and the relevant side-effect fixture.

### D. Memory/context fault

1. Check admission policy: required, eligible, forbidden, or not_required.
2. For required, a missing prefetch must stop before provider execution.
3. Check only bounded source references/hashes and omission counts; do not copy raw sources into troubleshooting artifacts.
4. Validate owner/direct scope and exclusion of cron, heartbeat, groups, memory-flush and silent turns.
5. Run Web and Telegram memory-parity fixtures; inspect no-leak scan.

### E. Fallback fault

1. Capture the precomputed `fallbackSet` from `VerifiedRoute`; never reconstruct from provider strings.
2. Check every fallback candidate against the original required capability set and contract version.
3. Confirm envelope and canonical tool-registry hashes remain unchanged.
4. If no equivalently qualified route exists, close `HOLD_CONTRACT_UNAVAILABLE`.
5. Run primary-unavailable, adapter-protocol-fail and fallback-mismatch fixtures.

### F. Delivery/closeout fault

1. Confirm destination/thread derive from normalized ingress, not model text.
2. Verify sanitation, duplicate suppression key, payload hash, channel acceptance and delivery receipt.
3. Missing receipt, `UNKNOWN`, null or empty closeout is a failed-closed HOLD—not PASS.
4. Do not resend merely to obtain evidence. Repair the receipt/delivery code path and use a no-send fixture.

## Repair rules

- One defect class, one bounded repair hypothesis, one validation packet.
- Preserve a snapshot before mutation and an exact rollback target.
- Prefer a wrapper/interceptor at the control-plane boundary over scattered model-specific prompt patches.
- No provider, model, channel, session, fallback, memory, tool or delivery configuration change without explicit authorization for that mutation class.
- A code repair cannot promote a lane; qualification evidence is separate.
- Never treat “the model answered well” as tool, memory, delivery or postcondition evidence.
- Never downgrade `max`, required memory, external-send authority, or required postconditions silently.

## Repair packets

Every repair records:

```text
incident ID and severity
symptom and affected turn classes
root cause, owning component, and failed invariant
containment taken
exact changed files/config keys
before/after hashes
fixture IDs and results
model/lane matrix affected
receipt readback
rollback command/policy state
explicit terminal PASS/HOLD/FAIL
follow-up qualification requirement
```

## Regression matrix after any repair

Minimum required:

1. selected failed fixture;
2. no-bypass/forged-route test;
3. required-memory test when owner memory is in scope;
4. prose-only action trap if actions/tools are affected;
5. fallback-equivalence fixture if selection/adapters changed;
6. Web and Telegram delivery/receipt fixture if ingress/delivery changed;
7. model-switch test: GPT-5.5 ↔ affected GPT-5.6 lane ↔ verified fallback;
8. readback confirming no unexpected mutation.

## Escalation statuses

```text
PASS_REPAIRED_AND_REGRESSION_VERIFIED
HOLD_ROOT_CAUSE_UNCONFIRMED
HOLD_CONTRACT_UNAVAILABLE
HOLD_POSTCONDITION_UNVERIFIED
HOLD_MANIFEST_STALE
FAIL_SIDE_EFFECT_UNCERTAIN
FAIL_DELIVERY
ABORT_UNAUTHORIZED_MUTATION_REQUIRED
```

## Anti-patterns

- Fixing an unreliable model by setting it as raw primary or channel pin.
- Repeating a send after delivery evidence is unclear.
- Treating a direct model's good prose as a contract pass.
- Allowing a fallback without fresh manifest evidence.
- Leaving terminal receipts missing/UNKNOWN.
- Repairing only the normal route while queued/post-dispatch routes remain direct.
- Changing a model, reasoning level, adapter and selector together; isolate one variable.

## 2026-07-11T05:46Z — M2Q queued/follow-up raw route guard repaired

**Symptom:** M2 direct owner session/directive RouteIntent smokes passed, but queued/follow-up code in `agent-runner.runtime-a09vVD0N.js` could still pass queued raw `provider`/`model` into `runWithModelFallback()` and then `runEmbeddedPiAgent()`.

**Preflight:** read `memory/lessons-learned-umc-m2-routing-telegram-gateway-2026-07-11.md` before editing/restarting. This preserved the required Gateway/Telegram safety workflow: inspect active installed code, prefer no-send smokes, avoid Telegram spam, and close out immediately.

**Repair:** backed up the installed agent-runner runtime, added exported no-send seam `applyUmcV1QueuedRouteAdmission`, and wired it inside `createFollowupRunner()` before queued fallback/provider execution. Owner-direct queued raw `openai/gpt-5.5` is captured as `source=queued_followup` RouteIntent and forced to executable default route `openai-codex/gpt-5.5`. Non-owner and group queued fixtures remain out of scope.

**Validation:** pre/post restart syntax checks passed; pure no-send queue-admission smoke passed with `directBypass=false`, `externalSend=false`; static order check proved admission occurs before `runWithModelFallback()` / `runEmbeddedPiAgent()`; direct session/directive no-send regressions passed; default route exact-token smoke returned `UMC_M2Q_POST_RESTART_ROUTE_OK_20260711M`; Telegram direct session readback remained `openai-codex/gpt-5.5`, fallback `ollama/deepseek-v4-pro:cloud`, queue depth 0.

**Status:** `PASS_M2Q_QUEUE_ADMISSION_GUARD_WIRED_NO_SEND_STATIC`. No live Telegram queued delivery probe was sent. M3 remains gated on Stick accepting this M2Q scope or requesting a controlled queued-delivery fixture.

## 2026-07-11T06:01Z — M2R controlled queued-delivery prompt intake pending

**Status:** `PROMPT_INTAKE_PENDING_BANANA_TERMINATOR`

Stick began a split prompt authorizing/defining the next M2R controlled queued-delivery fixture, but the prompt is incomplete and ended mid-sentence after the exact fixture-token instruction. Current chunk is preserved in `memory/notebooks/umc-m2r-queued-delivery-prompt-chunks.md`.

Troubleshooting constraints already captured:

- Do not treat M2Q no-send/static PASS as live queued-delivery proof.
- Do not send anything until full prompt and terminator arrive.
- Any preflight failure must fail closed as `UMC_M2R_QUEUED_DELIVERY_FIXTURE_BLOCKED_PREFLIGHT`.
- Fixture must prevent repeated Telegram delivery and must leave runtime/config/route/fallback/tool/memory/Context Bridge/Runtime Kernel/delivery policy authority unchanged.
- VerifiedRoute branding/manifest registry are explicitly out of M2R scope.

No runtime/config/Gateway/Telegram mutation was performed during prompt intake.

### Chunk 2 intake addendum — 2026-07-11T06:01Z

**Status:** `PROMPT_INTAKE_PENDING_BANANA_TERMINATOR`

Chunk 2 supplied the exact fixture token `UMC_M2R_SINGLE_QUEUED_DELIVERY_OK_20260711O`, delivery minimalism constraints, required independent assertions, closeout enum set, M2/M2Q acceptance criteria, and initial M3 objective. It remains incomplete and ended mid-sentence at M3.0 discovery.

Failure/hold rules now captured for the future fixture:

- PASS requires proof of intended queued path, exactly-once admission/execution, guard-before-fallback ordering, no bypass, observed route/provider/model/fallback/direct-execution/guard decision/execution result, exactly one correct Telegram owner delivery, no duplicate/wrong destination, no dry-run delivery, and protected-state equality.
- Closeout must be one of the prompt's explicit enums; ambiguous/unverified is never PASS.
- If fixture fails or blocks, do not mark M2 accepted and do not begin M3.
- If fixture passes, M2 accepted scope and M2 non-claims must both be documented; M3 starts separately and must not include model promotion or broader production authority.

No runtime/config/Gateway/Telegram mutation or send was performed during chunk 2 intake.

### Chunk 3 intake addendum — 2026-07-11T06:01Z

**Status:** `PROMPT_INTAKE_PENDING_BANANA_TERMINATOR`

Chunk 3 supplied detailed M3 mapping, implementation-slice, hard-behavior, exit-criteria, evidence-discipline, and scope-discipline requirements. It remains incomplete and ended mid-sentence at the hard-gate failure recovery clause.

Troubleshooting/repair implications captured:

- M3 must explicitly find every path where model prose can imply completion without runtime proof.
- Action-required turns must fail closed to HOLD/FAIL statuses rather than pass on prose.
- Provider adapters must not directly call tools or delivery; runtime supervisor/receipts own authority.
- Evidence must preserve failed attempts and observed values; no PASS by inference.
- Protected runtime/config/route/fallback/tool/memory/Context Bridge/Runtime Kernel/delivery state must remain unchanged outside approved M3 mutation set.
- If any hard gate fails in M2R or M3, stop the affected phase, preserve evidence, and restore exact pre-change state.

No runtime/config/Gateway/Telegram mutation, fixture build, or send was performed during chunk 3 intake.

### Chunk 4 terminator received — 2026-07-11T06:01Z

**Status:** `READY_FOR_M2R_PHASE_A_PREFLIGHT`

Final terminator `Banana` arrived. Phase A preflight then failed closed as `BLOCKED_M2R_PREFLIGHT_OR_AUTHORITY_UNAVAILABLE`: the working tree had 1329 unrelated local changes. This is a hard preflight blocker under the prompt. No Telegram send, fixture build, dry-run, Gateway/config/route/fallback/session mutation, M2 acceptance, or M3 work occurred. Runtime rollback remained available and was not needed because no post-preflight runtime mutation occurred. Evidence: `m2_admission_route_interceptor/m2r_single_queued_delivery/M2R_PREFLIGHT_SNAPSHOT.json` and `M2R_BLOCKED_PREFLIGHT_OR_AUTHORITY_UNAVAILABLE.json`.

## 2026-07-13T10:04Z — M3M abort preservation and Gateway transient diagnostic

**Symptom:** M3M installed observe-only no-send shadow soak R1 aborted at checkpoint `0005` with `GATEWAY_UNREACHABLE` after four clean checkpoints.

**Diagnosis:** abort evidence and post-abort probes classify the event as `GATEWAY_RPC_TRANSIENT_TIMEOUT`, not authority drift or a failed safety boundary. Gateway PID remained stable, RPC was OK at abort readback, listener/RPC/Telegram were healthy through the 30-minute stability window, and the abort did not start M3N/M4/enforcement.

**Validation:** `M3M_POST_ABORT_HEALTH_STABILITY_SUMMARY.json` reports `PASS_M3M_POST_ABORT_HEALTH_STABILITY_CONFIRMED` with `6/6` probes and `0` failed. `M3M_SOAK_ABORT_SAFETY_COUNTER_VALIDATION.json` reports clean counters: `0` Telegram sends, external sends, provider/model shadow calls, real write tools, runtime/config/route/fallback/memory/Context Bridge mutations. `M3M_SOAK_ABORT_VALIDATION.json` reports JSON validation and diff-check PASS for the scoped package.

**Repair/plan:** no runtime/config/route/fallback mutation was made. The observer harness `check` command now scans abort artifacts so child aborts report `LONG_RUNNING_CRON_OBSERVER_ABORTED` instead of stale-only status. R2 plan keeps the same 12h/24-checkpoint no-send/no-authority boundary and adds an independent early-abort sentinel plus loopback/retry reachability probes.

**Status:** `PASS_M3M_SOAK_ABORT_PRESERVED_GATEWAY_BLIP_DIAGNOSED_R2_READY`. Next allowed milestone is `M3M_INSTALLED_OBSERVE_ONLY_SHADOW_SOAK_NO_SEND_RETRY_R2`; do not advance to M3N from R1.

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
