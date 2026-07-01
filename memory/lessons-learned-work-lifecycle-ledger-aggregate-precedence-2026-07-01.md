# Lesson Learned — Work Lifecycle Ledger aggregate precedence

Date: 2026-07-01 AEST
Classification: `WORK_LIFECYCLE_M2_AGGREGATE_PRECEDENCE_REPAIR_LESSON`

## What happened

During Work Lifecycle Ledger M2 focused validation, the first executed M2 validation failed:

- Validation command id: `90b6efbc-37e0-4086-8abc-a1ff44b02f92`
- Tests: 9
- Passed: 8
- Failed: 1

The failing case exposed an aggregate-status precedence bug in `deriveAggregateRunStatus()`.

If all required milestones were `PASS` but the run record still had status `RUNNING`, the aggregate logic returned `RUNNING` before checking the `all_required_milestones_passed` condition.

## Why it matters

The lifecycle ledger must derive truth from milestone state, not stale top-level run state. Otherwise a run could remain indefinitely `RUNNING` even after all required milestones passed, recreating the silent-closeout failure class this project is meant to eliminate.

## Repair

Changed `src/work-lifecycle/work-status-aggregate.ts` so the aggregate order is:

1. Run-level `ABORT` / abort record takes precedence.
2. Run-level `SUPERSEDED` / superseded link takes precedence.
3. Required milestone `ABORT` / `SUPERSEDED` / `FAIL` / `HOLD` take precedence.
4. `ACK_PENDING` stays `ACK_PENDING`.
5. All required milestones `PASS` derives `PASS`.
6. Only then does pending/running milestone or stale run `RUNNING` derive `RUNNING`.

After repair:

- Validation command id: `fa4ba2a4-a7bc-4c03-a51b-02673200e0df`
- Tests: 9
- Passed: 9
- Failed: 0
- `M2_REDACTION_SCAN_PASS`
- `M2_FOCUSED_VALIDATION_PASS_AFTER_REPAIR`

## Durable rule

Aggregate lifecycle status must prefer decisive terminal milestone evidence over stale parent run status. Parent run state is a cached summary, not the source of truth, until replay/aggregation recomputes it.

## Future implementation implication

M5 no-next-milestone guard and M6 watcher should call aggregate/replay before deciding whether work is still running. A stale top-level `RUNNING` must not override completed required milestones.
