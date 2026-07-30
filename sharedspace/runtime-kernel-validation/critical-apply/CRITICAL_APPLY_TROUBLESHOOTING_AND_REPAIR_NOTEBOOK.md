# Critical Apply Harness — Troubleshooting and Repair Notebook

## Current status

Project branch: `feature/critical-apply-harness-observer-20260730`

Implementation level: M0/M1 skeleton. No production apply path is enabled.

## Safety posture

- No foreground critical apply processes.
- `execute` currently writes `execute-refusal.json` and does not mutate production.
- OpenClaw npm plugin classifier functions are read-only by default.
- Production package apply is blocked until M0–M9 gates pass.

## Known design risks and mitigations

### Risk: runner becomes another foreground wrapper

Mitigation: runner must run detached/durable in later milestones. Chat may request status only. `execute` cannot depend on chat stdout for correctness.

### Risk: restore point stale or incomplete

Mitigation: restore point gate requires age <= 3600 seconds, manifest, boundary, path-safety, and verify drill. Stale restore point must terminal `ROLLBACK_FAIL_OPERATOR_REQUIRED` if needed.

### Risk: hidden `.openclaw-*` directory is live generation

Mitigation: staging inspector checks `/proc/<pid>/maps`, `/proc/<pid>/fd`, `/proc/<pid>/cwd`, `/proc/<pid>/exe`, and cmdline. Live-referenced staging is `LIVE_REFERENCED_LEAVE_UNTOUCHED`.

### Risk: jobs-state observational drift blocks safe work

Mitigation: strict `jobs.json`; semantic protected-writer state; exact protected run logs; volatile scheduler timestamps only under signed policy.

### Risk: apply succeeds but package is incoherent

Mitigation: observer postcheck classifies `NPM_BASE_MISSING`, `NPM_BASE_EMPTY`, `NPM_BASE_INCOMPLETE`, `NPM_BASE_COHERENT`, or `NPM_BASE_UNKNOWN`; failure can invoke restore from fresh restore point.

### Risk: restart health false failure

Mitigation: restart is separate later transaction with bounded readiness polling. WebSocket 101 + HTTP warning should classify warning, not trigger package reinstall by default.

## Recovery rules during harness development

1. If tests fail, fix tests/code only; do not touch production package/Gateway.
2. If git working tree contains unrelated dirty files, stage only critical-apply paths.
3. If runner `execute` is accidentally invoked in current milestone, expected behavior is refusal with no mutation.
4. If any approval card appears during docs/tests, treat it as stale unless explicitly approved as a new governing transaction.

## Immediate next milestone

M0 — Contract finalization.

Pass criteria:

- `CRITICAL_APPLY_CONTRACT.md` present.
- contract schemas validate.
- state machine totality documented.
- no foreground critical apply path remains.
- no production mutation.

Expected terminal:

`M0_PASS_CRITICAL_APPLY_CONTRACT_FINALIZED_NO_MUTATION`
