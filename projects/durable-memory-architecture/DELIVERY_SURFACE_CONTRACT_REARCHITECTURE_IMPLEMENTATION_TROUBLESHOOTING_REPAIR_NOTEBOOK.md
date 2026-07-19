# Delivery Surface Contract Rearchitecture — Implementation, Troubleshooting and Repair Notebook

Status: **started; design/rehydration only; no runtime apply**
Started: 2026-07-19 AEST after M25H pushed blocked closeout
Current boundary: do not start M26 or a production implementation milestone without explicit owner authorization.

## 0. Purpose

M25H proved that a narrow handler predicate repair is insufficient. The local handler can produce the intended sanitized reply for the live cron session-key shape, but live cron still collapses to `NO_REPLY` and produces no delivery. The next repair should therefore be a broad contract design rearchitecture covering runtime reply payloads, cron execution, boundary handler decisions, surface delivery, dedupe and receipts.

This notebook is the implementation/troubleshooting/repair spine for that design work. It is not an apply plan and does not authorize code/config/runtime mutation.

## 1. Current accepted state

- Pushed terminal: `M25H_PUSHED_BLOCKED_REPAIRED_DELIVERY_STILL_NO_REPLY`.
- Local blocked terminal: `M25H_BLOCKED_REPAIRED_DELIVERY_STILL_NO_REPLY`.
- Restart-sentinel validation: `PASS_RESTART_SENTINEL_BLOCKED_CLOSEOUT_STILL_SAFE`.
- Evidence root: `sharedspace/runtime-kernel-validation/memory-ledger/m25h_delivery_contract_repair_final_proof_20260719T153336+1000`.
- Evidence manifest SHA: `06954e9e7a5ff9c389e7195903a6d91cb81871f42a18893d6fd9fa5a560fc945`.
- Pushed commit: `6c62cf22dddbe828de523d3eb823908b5cb599b3`.
- Handler ended dormant/unarmed.
- M25E/M25G/M25H jobs absent/not runnable.
- M25E/M25G/M25H run counts each exactly one.
- M25H result: `NO_REPLY`, `delivered=false`, `deliveryStatus=not-delivered`.
- Delivery/Telegram sends: 0.
- Ledger mutation: 0.
- Context Bridge mutation: 0.
- Route/model/fallback mutation: none.
- Authority promotion: 0.
- M26: not started.

## 2. Compaction-gap rehydration anchor

The local compaction-gap rehydrator was run as the first context restoration step:

```bash
python3 projects/durable-memory-architecture/scripts/compaction_gap_rehydrate.py --status --strict
```

Result:

- status: PASS;
- source count: 7;
- warnings/errors: 0/0;
- packet: `state/durable-memory-architecture/compaction-gap-hydration/latest.md`;
- manifest: `state/durable-memory-architecture/compaction-gap-hydration/latest.json`;
- packet SHA: `a27288818fdee25899f50a525627bc50e25858336162792a0b3181859b0a8b05`;
- manifest SHA: `c606178015514fd8b795e4be9467409bb2363a9865ec7f37413b936f88ef2fb9`.

Important rehydrated reality: M24 is now ABORT (`MEMORY_LEDGER_V0_1_M24_ABORT_SANITIZED_DEFAULT_NOT_USED`), not RUNNING. New contract work must treat the old seven-milestone plan as design reference that requires rebaselining, not as a current apply plan.

## 3. Problem class

The failure class is **delivery contract ambiguity across runtime layers**:

```text
cron job/run/session
-> agent turn/session key
-> before_agent_reply hook
-> handler decision/result
-> runtime reply text normalization
-> NO_REPLY/silent policy
-> message_sending gate
-> delivery runtime announce/send
-> message_sent receipt
-> closeout evidence
```

A valid delivery-required proof must never depend on an implicit missing-reply fallback. Every boundary needs a typed status and receipt.

## 4. Required contract objects to design

Initial vocabulary candidates:

- `DeliveryContractEnvelope`
- `DeliveryIntent`
- `RunIdentityBinding`
- `BoundaryDecisionReceipt`
- `ReplyPayloadDecision`
- `NoReplyPolicyDecision`
- `SurfaceRenderPacket`
- `MessageSendingGateDecision`
- `DeliveryInvocationReceipt`
- `MessageSentReceipt`
- `DeliveryCloseoutReceipt`
- `DeliveryDedupeKey`
- `DeliveryAbortReceipt`

Each object should bind IDs/hashes across job, run, session, surface, render, delivery and closeout.

## 5. Design requirements

### 5.1 Reply payload semantics

- Missing reply, explicit silent `NO_REPLY`, explicit HOLD no-delivery, and successful sanitized deliverable must be distinct typed outcomes.
- A handler returning `handled=true` without a reply should not silently become delivery-required success.
- A delivery-required path must fail closed if a sanitized payload is absent.
- User-visible prose must not claim delivery/source success without postcondition receipts.

### 5.2 Boundary handler semantics

- `before_agent_reply` decides whether a sanitized closeout payload exists and is allowed.
- `message_sending` enforces exact payload/session/run binding and cancels anything outside the prepared payload.
- `message_sent` records typed send result receipts.
- Duplicate attempts are blocked by a stable dedupe key.
- Unarmed/dormant handler state must be unambiguous and read back after restarts.

### 5.3 Cron/runtime semantics

- Cron must carry a stable run identity into the agent session and all delivery receipts.
- `NO_REPLY` is acceptable only for explicit no-delivery jobs, not as an accidental fallback for delivery-required proofs.
- Announce mode, explicit channel/target, and best-effort behavior must be visible in the contract and evidence.
- Delete-after-run and job absence must not erase the run/receipt audit path.

### 5.4 Surface semantics

- Surface policy determines identity, privacy, rendering profile, approval needs, dedupe and send boundary.
- Surface policy may narrow delivery and disclosure; it must not broaden source authority or runtime capability.
- Telegram owner-direct is one surface cell, not a universal delivery bypass.
- Group/shared surfaces remain deny-by-default for private memory.

## 6. Troubleshooting map

| Symptom | Likely class | Required evidence before repair |
|---|---|---|
| Live run returns `NO_REPLY` while local probe returns sanitized reply | plugin deployment/hook invocation/result propagation mismatch | loaded plugin hash, hook registration path, hook call trace, result mapping, cron session key, runtime reply object |
| `handled=true` with no payload | ambiguous handler result | typed decision receipt showing HOLD/ABORT vs deliverable |
| Delivery runtime says `not-delivered` | silent/no-payload policy or delivery target missing | reply payload, delivery config, announce mode, surface policy, send attempt receipt |
| Duplicate or unexpected send | dedupe missing or surface bypass | dedupe key, message_sending decisions, delivery receipts, surface send logs |
| Sanitized content disappears | render/payload normalization mismatch | render packet hash, reply text hash, runtime normalized reply hash |
| Closeout prose delivered on failure | HOLD/ABORT render policy bug | abort receipt, surface render policy, delivery-required flag |

## 7. Repair protocol for the next authorized milestone

1. STARTED notice with scope, pass criteria, abort triggers and expected artifacts.
2. Rehydrate from this notebook, compaction-gap packet, M25H evidence, local runtime source and current config readbacks.
3. Map actual runtime hook and delivery contracts from source/tests, not assumptions.
4. Define typed contract objects and negative fixtures before implementation.
5. Implement the smallest no-send/local fixture path first.
6. Add tests for deliverable, explicit silent, HOLD no-delivery, malformed binding, duplicate, missing surface, message_sending cancel and message_sent receipt.
7. Run no-send and fixture validations before any Gateway/plugin/retry mutation.
8. Only after a separate owner approval decision, perform exactly one bounded live proof, then disarm/remove and close.
9. Preserve sanitized evidence only; push only with explicit authorization.

## 8. Initial hard gates

- DSG-01 no runtime/config/Gateway mutation during design rehydration.
- DSG-02 no handler arming, retry scheduling, cron run, delivery or Telegram send during design rehydration.
- DSG-03 M25H pushed blocked evidence is read-only and unchanged.
- DSG-04 `NO_REPLY`, HOLD, ABORT and deliverable reply are typed distinctly in the design.
- DSG-05 exactly-one delivery and duplicate prevention are first-class contract fields.
- DSG-06 surface identity/privacy/rendering policy is separate from source authority.
- DSG-07 UMC prose-success prevention requires delivery/source receipts.
- DSG-08 tracked evidence contains no raw private packets, tokens, auth headers or raw surface IDs.
- DSG-09 no Ledger/Context Bridge/model/route/authority/M26 mutation.
- DSG-10 no successor milestone starts automatically.

## 9. Rehydrator

Started script:

```bash
python3 projects/durable-memory-architecture/scripts/delivery_surface_contract_rehydrate.py --status --strict
```

Generated output:

```text
state/durable-memory-architecture/delivery-surface-contract-rehydration/latest.json
state/durable-memory-architecture/delivery-surface-contract-rehydration/latest.md
```

Validation expectations:

- `python3 -m py_compile projects/durable-memory-architecture/scripts/delivery_surface_contract_rehydrate.py` must pass.
- `python3 projects/durable-memory-architecture/scripts/delivery_surface_contract_rehydrate.py --check-only --strict` must pass with source count 11 and warnings/errors 0/0.
- `python3 projects/durable-memory-architecture/scripts/delivery_surface_contract_rehydrate.py --status --strict` must generate the packet under `state/durable-memory-architecture/delivery-surface-contract-rehydration/`.

Final generated hashes are intentionally not embedded in this notebook because the notebook is an input source for the rehydrator; embedding them would create self-referential packet drift. Record final run hashes in daily memory and/or closeout summaries instead.

The script remains read-only over allowlisted sources and writes only generated state. It must not inject prompts, mutate memory routes, alter Gateway/config, arm handlers, schedule jobs, run delivery or start a milestone.

## 10. Open design questions

1. What exact runtime type should replace accidental `NO_REPLY` fallback for delivery-required proofs?
2. Where should `BoundaryDecisionReceipt` be persisted for a one-shot cron proof without leaking private payloads?
3. Should cron jobs declare `delivery_required: true|false`, or should that be inferred from delivery mode and payload kind?
4. What is the minimal plugin/runtime hook trace needed to prove hook invocation without raw logs?
5. How should a late `message_sent` receipt be quarantined if cancellation/deadline already closed the run?
6. How does the Surface Service Broker bind dedupe keys across retries, restarts and delete-after-run jobs?
7. How should Telegram owner-direct policy migrate into SSB without becoming a pre-SSB reusable shim?

## 11. Current next boundary

Stop after creating the notebook/rehydrator and validating that the design rehydration packet can be generated. Do not implement a production repair until Stick explicitly authorizes the next milestone.

## M25I-A architecture baseline — 2026-07-19 16:40 AEST

- Baseline status target: `M25I_A_ARCHITECTURE_BASELINE_IMPLEMENTATION_READINESS_PASS_NO_APPLY`.
- Owner LLD copied unchanged to `projects/durable-memory-architecture/DURABLE_MEMORY_LEDGER_CONTEXT_CONTRACT_SURFACE_BROKER_LLD.md` with SHA-256 `edd7284f2f591517b3536300ba476ab9b06abd0d01a02ec3b1500cc748f66de1`.
- Current systemic blocker: delivery-required cron/proof work can still collapse to `NO_REPLY`/not-delivered despite handler-local repair, so the architecture now requires explicit job/run/session, boundary, payload, SSB, adapter and UMC receipt binding.
- Boundaries preserved: no jobs, no handler arming, no Gateway reload/restart, no Telegram/delivery adapter, no Ledger/Context Bridge/model-route mutation, no authority promotion, no M25J/M26 start.
