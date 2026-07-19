# Delivery Surface Contract Rearchitecture — Compaction-Gap Chunks

Status: started 2026-07-19 AEST after M25H pushed blocked closeout. This notebook is a memory/navigation aid, not implementation authority.

## Chunk 0 — Rehydration source and current boundary

- Ran the local compaction-gap rehydrator: `projects/durable-memory-architecture/scripts/compaction_gap_rehydrate.py --status --strict`.
- Result: PASS, 7 sources, 0 warnings, 0 errors.
- Generated packet: `state/durable-memory-architecture/compaction-gap-hydration/latest.md`.
- Generated manifest: `state/durable-memory-architecture/compaction-gap-hydration/latest.json`.
- Packet SHA: `a27288818fdee25899f50a525627bc50e25858336162792a0b3181859b0a8b05`.
- Manifest SHA: `c606178015514fd8b795e4be9467409bb2363a9865ec7f37413b936f88ef2fb9`.
- The rehydrator correctly reflected post-design reality: M24 terminal is ABORT (`MEMORY_LEDGER_V0_1_M24_ABORT_SANITIZED_DEFAULT_NOT_USED`), not the original design-time RUNNING state.

## Chunk 1 — Scope expansion accepted conceptually, not applied

Stick wants to expand from a narrow compaction-gap/delivery repair into one broad contract-design rearchitecture that fixes the systemic classes together:

- compaction-gap recovery and source authority;
- Memory Ledger continuity and source/claim record shape;
- Runtime Service Broker grants, health, cancellation and receipts;
- UMC turn envelopes, postconditions and prose-success prevention;
- Surface Service Broker identity, privacy, rendering, dedupe and delivery receipts;
- cron/agent/runtime reply-payload semantics and `NO_REPLY` handling;
- Telegram/direct owner surface behavior without manual-send bypasses.

No runtime apply, handler arming, retry, delivery, Ledger mutation, Context Bridge mutation, route/model mutation, authority promotion or M26/M2 implementation start is implied by this chunk.

## Chunk 2 — M25H live blocker that motivates the delivery-surface contract repair

Accepted pushed state:

- terminal: `M25H_PUSHED_BLOCKED_REPAIRED_DELIVERY_STILL_NO_REPLY`;
- local blocker terminal: `M25H_BLOCKED_REPAIRED_DELIVERY_STILL_NO_REPLY`;
- restart-sentinel validation: `PASS_RESTART_SENTINEL_BLOCKED_CLOSEOUT_STILL_SAFE`;
- evidence root: `sharedspace/runtime-kernel-validation/memory-ledger/m25h_delivery_contract_repair_final_proof_20260719T153336+1000`;
- evidence manifest SHA: `06954e9e7a5ff9c389e7195903a6d91cb81871f42a18893d6fd9fa5a560fc945`;
- pushed commit: `6c62cf22dddbe828de523d3eb823908b5cb599b3`.

Observed facts:

- focused local handler repair/tests passed;
- offline exact-run probe produced the intended sanitized reply for the live runtime session-key shape;
- live cron proof still returned exact `NO_REPLY`, `delivered=false`, `deliveryStatus=not-delivered`;
- handler ended dormant/unarmed; M25E/M25G/M25H jobs absent/not runnable; each run count exactly 1; delivery and Telegram send count 0.

Interpretation: the remaining issue is not simply one handler predicate; it is the broader handler/runtime/cron/surface delivery contract boundary and result propagation model.

## Chunk 3 — Rearchitecture invariants

- Do not solve delivery by manual Telegram sends or by bypassing the boundary handler.
- `NO_REPLY` must be a typed terminal/silent policy, not an accidental masking value for delivery-required success.
- A delivery-required proof path must bind request -> job/run/session -> handler decision -> reply payload -> message_sending gate -> delivery runtime -> message_sent receipt -> closeout receipt.
- HOLD/ABORT paths must be typed no-delivery outcomes, not prose that accidentally renders or disappears.
- Exactly-one delivery and dedupe must be contract-level properties, not ad hoc cron behavior.
- Surface policy must narrow identity/privacy/rendering/delivery; it must not grant source authority or broaden runtime capabilities.
- All consequential claims still need canonical source readback; vector/session/summary/context bridge output is navigation only.

## Chunk 4 — Design notebook and rehydrator start

Started project notebook:

- `projects/durable-memory-architecture/DELIVERY_SURFACE_CONTRACT_REARCHITECTURE_IMPLEMENTATION_TROUBLESHOOTING_REPAIR_NOTEBOOK.md`

Started read-only rehydrator:

- `projects/durable-memory-architecture/scripts/delivery_surface_contract_rehydrate.py`

Generated output location:

- `state/durable-memory-architecture/delivery-surface-contract-rehydration/latest.json`
- `state/durable-memory-architecture/delivery-surface-contract-rehydration/latest.md`

Final generated hashes are intentionally not embedded here because this notebook is one of the rehydrator's input sources; embedding them would create self-referential packet drift. Record final run hashes in daily memory and/or closeout summaries instead.

Banana checkpoint: chunks persisted for compaction-gap recovery plus delivery-surface contract rearchitecture start.

## Chunk 5 — Banana Banana / Surface Response Target Resolver (SRTR)

Stick identified a missing generalized target-resolution layer: SSB currently defines whether a surface may deliver and how to render, but the architecture also needs a safe bounded contract for where the response goes.

New generalized delivery path:

```text
SanitizedPayloadEnvelope
-> Surface Service Broker policy decision
-> Surface Response Target Resolver (SRTR)
-> Surface Delivery Adapter
-> DeliveryResultEnvelope
```

SRTR distinguishes surface authorization, recipient/target authorization, payload authorization, delivery authorization, and completed delivery. It accepts symbolic aliases such as `owner-direct-primary`, resolves them only through a private runtime registry, and returns short-lived sanitized target grants/receipts without exposing provider-specific target IDs to jobs, fixtures, evidence, Context Bridge, reconstruction packets, UMC prose, or model-visible context.

M25J-R scope: repair the M25J security fixture that used a realistic provider-target pattern; replace it with an unmistakably synthetic forbidden marker; add `SurfaceResponseTargetRequest`, `SurfaceResponseTargetGrant`, and `SurfaceResponseTargetReceipt`; add fixtures/tests/gates/health checks; update rehydrator/notebooks/evidence; create one new local repair commit; no push and no live target resolution/delivery/runtime mutation.

Banana Banana checkpoint: SRTR chunks persisted for M25J-R security fixture redaction and target resolver contract extension.

## Chunk 6 — SRTR target registry contract boundaries

SRTR is design-only in M25J-R. A later private runtime registry may map `surface_id + target_alias` to provider-specific handles, but the registry is untracked, owner/operator managed, permission restricted, separate from model prompts and Context Bridge, versioned only by sanitized policy epoch/hash, and fail-closed if missing/ambiguous/expired/unauthorized.

Required aliases in fixtures are symbolic only: `owner-direct-primary`, `current-approved-session`, `operator-canary-target`. No heuristic recipient discovery and no “last chat” fallback. Health checks for M25J-R are fixture/design checks, not live registry reads.

Target gates added: valid unexpired target grant required; surface permission does not imply target permission; raw provider IDs absent from tracked artifacts; alias resolution only via private runtime registry in later milestones; cross-user/session/surface/stale replay denied; target resolution can narrow only; no fallback; grant/payload/result share idempotency key, surface, policy epoch and grant chain; max deliveries one; evidence uses keyed rotating non-correlatable aliases.
