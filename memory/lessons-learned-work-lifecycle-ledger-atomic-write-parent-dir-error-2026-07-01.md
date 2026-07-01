# Lesson Learned — Work Lifecycle Ledger atomic write parent-dir failure

Date: 2026-07-01 AEST
Classification: `WORK_LIFECYCLE_M1_ATOMIC_WRITE_REPAIR_LESSON`

## What happened

During Work Lifecycle Ledger M1 focused validation, the first test run failed:

- Validation command id: `cc27e1c5-4bfa-4f72-a771-6b4cdd1e75aa`
- Tests: 10
- Passed: 9
- Failed: 1
- Failing area: `src/work-lifecycle/work-ledger-store.test.mjs`, atomic write failure-path test.

The test exposed that `atomicWriteJson()` created parent directories before entering its try/catch. If parent directory creation failed, the function emitted a raw filesystem error instead of the intended `WorkLedgerStoreError('ATOMIC_WRITE_FAILED')` envelope.

## Why it matters

The Work Lifecycle Ledger must produce deterministic, classified failure states. Raw filesystem errors escaping before classification would make recovery, watcher logic, and operator evidence less reliable.

## Repair

Moved parent directory creation into the atomic write try/catch block in:

- `src/work-lifecycle/work-ledger-store.ts`

After repair, validation passed:

- Validation command id: `93350b61-17ca-43e7-a14b-42189e4fb645`
- Tests: 10
- Passed: 10
- Failed: 0
- `M1_REDACTION_SCAN_PASS`
- `M1_FOCUSED_VALIDATION_PASS_AFTER_REPAIR`

## Durable rule

For lifecycle infrastructure, no setup step in a classified operation should sit outside the classification/error-envelope boundary unless intentionally allowed and documented. Parent-dir creation, temp file creation, fsync, rename, event append, lock acquisition, and summary recompute should each either succeed or emit a lifecycle-specific error code.

## Future implementation implication

M2/M6 should preserve classified error envelopes when adding FSM/guards/watchers. Failure injection in M8 should include parent directory conflicts, read-only directory, partial temp file, corrupt JSONL, and lock conflict cases.
