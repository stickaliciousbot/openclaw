# Lessons learned — Closeout UNKNOWN explicit status contract (2026-07-10)

## Classification

`CLOSEOUT_UNKNOWN_EXPLICIT_STATUS_CONTRACT_REPAIR`

## What happened

Multiple closeout surfaces could show or preserve `Closeout: UNKNOWN` even when the underlying run had an explicit substantive terminal such as `PASS_FINAL_ROLLOUT_CLOSEOUT_READY` or a repaired canonical JSON closeout of `PASS`.

Observed cases:

- Work Lifecycle M13: artifact body/status indicated `PASS_FINAL_ROLLOUT_CLOSEOUT_READY`, but visible footer said `Closeout: UNKNOWN`; root cause was missing explicit `closeoutStatus` for summary/footer readers.
- Ledger v0.1 CB-L2/CB-L3/CB-L4: substantive evidence was green, but closeout presentation/metadata was missing or ambiguous and got classified as `HOLD_CB_L*_CLOSEOUT_STATUS_UNKNOWN_NEEDS_REPAIR`.
- Ledger v0.1 closeout gates used weak checks such as `closeout_status != "UNKNOWN"`; missing fields (`None`) incorrectly passed that test.

## Root cause

Closeout projectors/readers were using status-like fields inconsistently:

- Some artifacts had `status` or `terminal_status` but no explicit `closeoutStatus` / `closeout_status`.
- Some readers defaulted absent/ambiguous closeout metadata to `UNKNOWN` instead of deriving from canonical terminal evidence or failing closed.
- Some gates only checked “not UNKNOWN,” which allowed missing closeout metadata to pass.

## Durable rule

For every closeout artifact, projector, footer, readback, or watcher:

1. Require an explicit closeout field: `closeoutStatus` or `closeout_status`.
2. Valid closeout values must come from a closed enum such as `PASS`, `FAIL`, `ABORT`, `HOLD`, `BLOCKED`, `WARN`, `PASS_PUSHED`, `DRY_RUN_PASS`, or a project-defined explicit terminal closeout classification.
3. Missing/empty/null closeout fields must fail closed as `HOLD_CLOSEOUT_STATUS_MISSING_NEEDS_REPAIR`; they must not be treated as “not UNKNOWN.”
4. `status` / `terminal_status` may be used as input to derive a closeout, but the derived value must be materialized into the explicit closeout field before PASS/readback/push.
5. Projectors and visible footers must prefer explicit closeout fields over generic status, and must not emit `Closeout: UNKNOWN` when canonical JSON has an explicit PASS/FAIL/ABORT/HOLD closeout.
6. Regression tests must include missing-closeout metadata, explicit UNKNOWN, and terminal-status-only cases.

## Ledger v0.1 repair applied

- Patched CB-L2/CB-L3/CB-L4 gates to require explicit closeout statuses from `{PASS, FAIL, ABORT, HOLD, DRY_RUN_PASS}`.
- Generalized `context_bridge_closeout_readback.py` to audit CB-L2, CB-L3, CB-L4, CB-L7, and all available milestone profiles.
- Added regression coverage proving missing `closeout_status` is not explicit and must fail.
- Validation after repair: current canonical UNKNOWN count `0`, unresolved UNKNOWN marker count `0`, resolved historical UNKNOWN count `3`.

## Safety boundary

This lesson is documentation/readback/gate hardening. It does not authorize Gateway/runtime/model/provider/fallback/memory-route mutation, authority promotion, or production closeout projector apply without separate owner approval.
