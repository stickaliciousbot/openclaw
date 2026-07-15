# M3N Context Overflow Compaction Method Analysis

Status: `PASS_M3N_CONTEXT_OVERFLOW_SAFE_COMPACTION_METHOD_IDENTIFIED`

## Selected method

`runtime_sessions_compact_with_pre_backup` — `SAFE_WITH_APPROVAL`

Exact runtime compaction call identified from the local daily compaction script:

```sh
openclaw gateway call sessions.compact --json --timeout 600000 --params '{"key":"agent:main:telegram:direct:8495203551"}'
```

This is selected only with explicit operator approval and only after a pre-compaction backup/snapshot.

## Why not use the existing daily wrapper?

`/home/stickai/.openclaw/workspace/scripts/daily_memory_drift_reconcile_then_compact.sh` is not selected because it also:

- runs drift reconciliation;
- writes `state/daily-post-drift-compaction/...` artifacts;
- appends to today's daily memory file.

That violates the current phase boundary: no durable memory mutation and no unrelated repair work.

## Rejected / deferred methods

- Manual transcript trim: `UNKNOWN_DO_NOT_USE` — risks JSONL/session corruption and evidence loss.
- Snapshot + bounded truncation: `UNKNOWN_DO_NOT_USE` — bypasses runtime invariants.
- Summary artifact + active-context reset: `UNKNOWN_DO_NOT_USE` — reset semantics not proven for Telegram direct production path.
- New Telegram owner session: `UNSAFE_PRODUCTION_AUTHORITY_MUTATION` — changes production response-path continuity.
- Rehydrator handoff: useful later, but not a proven compaction mechanism.

## Selected approval status

`HOLD_M3N_CONTEXT_OVERFLOW_COMPACTION_AWAITING_OPERATOR_APPROVAL`

No compaction has been executed.
