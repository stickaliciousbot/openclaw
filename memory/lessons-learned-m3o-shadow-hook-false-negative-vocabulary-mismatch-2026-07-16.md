# Lessons Learned — M3O Shadow Hook False-Negative Diagnosis (2026-07-16)

## Incident

During M3O (`M3O_OWNER_TURN_SHADOW_OBSERVATION_NO_SEND`), the assistant declared the UMC v1 shadow hook was not installed in the production runtime and blocked M3O with `BLOCKED_M3O_OWNER_TURN_SHADOW_HOOK_NOT_INSTALLED_IN_RUNTIME`.

## Root cause

The assistant searched the installed runtime dist for **M3-level contract specification vocabulary** (`ContractEnvelope`, `UniversalContractReceipt`, `DeliveryReceipt`, `umc.shadow`, `UMC_SHADOW`) and found zero matches. It then concluded the hook was absent.

The actual production hook IS installed — it's the **M2 admission and route interceptor** in `agent-runner.runtime-a09vVD0N.js`. It uses **M2-level implementation vocabulary**:

- `resolveUmcV1DefaultRouteFromConfig` — resolves the default broker route from config
- `isUmcV1QueuedOwnerScope` — detects owner-scoped queued turns
- `applyUmcV1QueuedRouteAdmission` — intercepts raw provider/model selections and forces them through the default broker route
- `umcV1QueuedRouteIntent` — the route intent record written to session state
- System event: `UMC v1 queued route intent captured; execution forced through ...`

The assistant actually **read these terms** when inspecting `agent-runner.runtime-a09vVD0N.js` (lines 201-270) but did not recognize them as the production hook because it was looking for M3 contract vocabulary.

## Why it happened

1. **Milestone-level vocabulary mismatch:** The assistant searched for M3 contract terms (`ContractEnvelope`, `UniversalContractReceipt`, `DeliveryReceipt`) but the installed hook is at M2 level (route admission/interception). M3 envelope/receipt/delivery supervision has not been implemented yet.

2. **Read-but-didn't-recognize:** The assistant read the M2 interceptor code in `agent-runner.runtime-a09vVD0N.js` and saw `resolveUmcV1DefaultRouteFromConfig`, `isUmcV1QueuedOwnerScope`, `applyUmcV1QueuedRouteAdmission`, and `umcV1QueuedRouteIntent` — but classified them as "UMC v1 functions" without recognizing them as the installed production hook.

3. **Single negative result treated as conclusive:** A grep returning zero matches for M3 vocabulary was treated as proof of hook absence, rather than a signal to check what milestone level the installed hook actually implements.

4. **No pre-search milestone-level check:** Before declaring the hook absent, the assistant did not check which UMC milestone level the installed runtime actually implements (M2, not M3).

## Correct diagnosis

- **Hook installed:** YES — M2 admission and route interceptor in `agent-runner.runtime-a09vVD0N.js`
- **Hook level:** M2 (route admission/interception)
- **M3 receipts:** NOT IMPLEMENTED — `ContractEnvelope`, `UniversalContractReceipt`, `DeliveryReceipt` are M3-level artifacts that haven't been built yet
- **M3O status:** BLOCKED not because the hook is missing, but because the installed hook is at M2 level and M3 envelope/receipt/delivery supervision must be implemented before M3O can observe owner-turn shadow receipts

## Durable rule (added to AGENTS.md)

**Before declaring a production hook/component absent from the installed runtime:**

1. Determine what **UMC milestone level** the installed runtime actually implements by reading the implementation notebook (`UMC_V1_IMPLEMENTATION_NOTEBOOK.md`) and the most recent milestone closeout artifacts.
2. Search the runtime dist using the **vocabulary appropriate to that milestone level**, not vocabulary from future milestones.
3. If the installed hook is at M2 level, search for M2 terms (`umcV1QueuedRouteIntent`, `resolveUmcV1DefaultRouteFromConfig`, `isUmcV1QueuedOwnerScope`, `applyUmcV1QueuedRouteAdmission`), not M3 terms.
4. If you read hook code and see UMC-prefixed functions, **recognize them as the hook** even if they don't match the vocabulary of the milestone you're currently working on.
5. Never block a milestone on "hook not installed" without first confirming which milestone level the installed hook implements and whether the required receipts/artifacts for the current milestone exist at that level.

## Impact

- M3O was incorrectly blocked with the wrong root cause.
- 11 M3O blocked-closeout artifacts were written and committed under a partially incorrect diagnosis (hook absent vs. hook at wrong milestone level).
- A redundant staged hook implementation was created.
- An unnecessary runtime patch approval was prepared.
- Time was wasted on H0–H4 when the hook was already installed (just at M2 level, not M3).

## Recovery

1. Reclassify M3O root cause: hook IS installed at M2 level; M3 envelope/receipt/delivery supervision must be implemented before M3O can proceed.
2. Update M3O blocked closeout artifacts with the corrected diagnosis.
3. Retract the redundant H1–H4 artifacts.
4. Next milestone: implement M3 envelope/receipt/delivery supervision, then rerun M3O.

## Prevention

Added to:
- `AGENTS.md` — "Production Hook Vocabulary Check" rule (milestone-level aware)
- `MEMORY.md` — durable lesson
- Observer harness — explicit pre-grep milestone-level discovery step
