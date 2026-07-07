# M20 Detached Observer Reconciliation — 2026-07-07

## Classification

`HOLD_M20_DETACHED_OBSERVER_DID_NOT_EXECUTE_CHECKS_NO_PASS_UPGRADE`

Do **not** upgrade to `MEMORY_LEDGER_V0_1_M20_24H_POST_PRODUCTION_OBSERVATION_PASS_NO_AUTHORITY_PROMOTION_WITH_REPORTING_FALSE_POSITIVE` from the available detached observer evidence.

## Scope

Project: Stickbot Memory Ledger v0.1

Milestone: M20 — 24h post-production observation / soak

Worktree: `/tmp/stickbot-memory-ledger-v0-worktree`

Expected session target: `session:m20-post-production-observation`

Checkpoint jobs:

- T+2h: `8980885e-fc62-44e7-897f-ccc84e2f673c`
- T+8h: `4334fb16-e319-4ef2-a804-bb83c1eef22b`
- T+24h final: `72b92d09-602f-4649-9bd8-df7b91d3d4ce`

## Evidence inspected

- Cron run ledger: `/home/stickai/.openclaw/cron/runs/72b92d09-602f-4649-9bd8-df7b91d3d4ce.jsonl`
- T+2h/T+8h detached session transcript: `/home/stickai/.openclaw/agents/main/sessions/62b1ae3c-d1ba-48ee-81ef-6d271f76cf88.jsonl`
- T+24h detached session transcript: `/home/stickai/.openclaw/agents/main/sessions/bf1655f2-555f-4a21-b671-368a1c8741af.jsonl`
- Ledger worktree docs/artifacts listing under `/tmp/stickbot-memory-ledger-v0-worktree/projects/stickbot-memory-ledger-v0`
- Rehydrator packet: `/tmp/stickbot-memory-ledger-v0-worktree/projects/stickbot-memory-ledger-v0/artifacts/rehydration/stickbot-memory-ledger/latest.json`

## Findings

1. The cron run ledger reports the T+24h job status as `ok` and Telegram delivery as delivered.
2. The cron delivery evidence gate classified the run as `CRON_REPORT_REQUIRED_CLOSEOUT_DELIVERY_FAILED` with failed gate `PAYLOAD_ANCHOR_NOT_OBSERVED`.
3. Source inspection showed that the closeout evidence gate adds `PAYLOAD_ANCHOR_NOT_OBSERVED` when `requiresCloseoutDelivery` is true and `payloadAnchorObserved !== true`.
4. The installed cron delivery trace path supplies `closeoutVisibleCount: 0` and does not provide `payloadAnchorObserved`, so the delivery classifier can false-positive even when a message was delivered.
5. However, the detached session transcripts show a stronger blocker: each M20 checkpoint/final prompt received only a generic project-ledger summary response. The transcripts do not show tool execution, operator recall checks, doctor output, rehydrator PASS output, store count/hash checks, mutation sentinel evidence, or a sanitized final M20 closeout document.
6. No final M20 document was found under the Ledger project `docs/` or `artifacts/` directories.
7. The latest rehydrator packet still says M20 is `OBSERVATION_ONLY_IN_PROGRESS_NOT_PASS`, so it is not final PASS evidence.

## Decision

This is **not** an M20 runtime safety failure from observed failing gates.

It is also **not** a valid M20 PASS.

The correct closeout state is:

```text
HOLD_M20_DETACHED_OBSERVER_DID_NOT_EXECUTE_CHECKS_NO_PASS_UPGRADE
```

## Safety boundary readback

- No M22 started.
- No promotion performed.
- No authority promotion claimed.
- No Gateway/runtime/model/provider/fallback/Telegram/memory-route mutation performed by this reconciliation.
- No commit/push performed.
- No raw memory DB/private content included in this artifact.

## Required recovery path

Run an explicit M20 recovery/final validation package if Stick approves it. That package should be classified as a recovery validation, not the original uninterrupted detached 24h observation, unless it can reconstruct the missing checkpoint evidence from another authoritative source.

Possible recovery terminal if checks pass:

```text
MEMORY_LEDGER_V0_1_M20_RECOVERY_FINAL_VALIDATION_PASS_NO_AUTHORITY_PROMOTION_ORIGINAL_DETACHED_OBSERVER_INVALID
```
