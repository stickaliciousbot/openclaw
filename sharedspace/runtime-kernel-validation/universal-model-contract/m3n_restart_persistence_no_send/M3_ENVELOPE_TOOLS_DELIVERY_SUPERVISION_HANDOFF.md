# M3 Envelope / Tools / Delivery Supervision Handoff

Status: HANDOFF_READY_NO_IMPLEMENTATION_STARTED

## Authoritative prior state

- M3N is complete: `PASS_M3N_INSTALLED_SHADOW_OBSERVE_ONLY_RESTART_PERSISTENCE_NO_SEND`.
- M3O is correctly blocked: `BLOCKED_M3O_OWNER_TURN_SHADOW_M3_ENVELOPE_RECEIPTS_NOT_IMPLEMENTED`.
- The redundant M3O H1 runtime patch was rolled back and must not be reinstalled.

## Correct root cause

The UMC v1 production hook already exists at M2 route-admission level. It is not the missing piece.

Installed M2 hook locations:

- `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/agent-runner.runtime-a09vVD0N.js`
- `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/get-reply-DGnDV9U-.js`

M2 implementation vocabulary:

- `resolveUmcV1DefaultRouteFromConfig`
- `isUmcV1QueuedOwnerScope`
- `applyUmcV1QueuedRouteAdmission`
- `umcV1QueuedRouteIntent`

## Missing M3 work

M3 must implement envelope, tool supervision, delivery receipt, UniversalContractReceipt, and terminal closeout on top of the existing M2 route-admission hook.

Minimum M3 artifacts/capabilities:

1. `ContractEnvelope` for owner-turn shadow observation.
2. Tool supervision boundaries for observe-only/no-send execution.
3. `DeliveryReceipt` with explicit `mode: no_send` for shadow delivery paths.
4. `UniversalContractReceipt` tying route intent, envelope, tool observations, and delivery receipt together.
5. Terminal closeout materialized into canonical artifacts with explicit PASS/HOLD/FAIL/ABORT status.

## Safety requirements

- M3 implementation must begin observe-only/no-send.
- No Telegram send/probe during implementation validation unless separately authorized.
- No external send.
- No provider/model live shadow call.
- No route/fallback/config production mutation.
- No production authority change.
- No M3O rerun until M3 artifacts are installed and verified.
- No M3P, M4, or enforcement until M3O passes on real evidence.

## Rerun gate for M3O

M3O may be rerun only after:

1. M3 envelope/receipt/delivery supervision exists in the installed/runtime path or an explicitly approved test seam.
2. Local no-send fixtures prove `ContractEnvelope`, `DeliveryReceipt mode=no_send`, `UniversalContractReceipt`, and terminal closeout are emitted.
3. Runtime readback confirms the existing M2 hook remains present and is not replaced by a redundant hook.
4. Safety counters remain zero for Telegram sends, external sends, provider/model shadow calls, memory mutation, Context Bridge mutation, route/config mutation, production authority, M3P, M4, and enforcement.

Exact next milestone: `M3_ENVELOPE_TOOLS_DELIVERY_SUPERVISION`.
