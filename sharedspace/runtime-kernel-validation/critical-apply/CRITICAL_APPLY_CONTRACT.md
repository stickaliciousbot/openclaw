# Critical Apply Contract

Status: M0 contract draft

## Contract summary

Critical production apply/deploy/install/recovery/runtime mutation is forbidden as a foreground chat/session process. The only acceptable path is a durable observer transaction with verified restore point, receipts, postcheck, and observer-owned recovery.

## Production mutation boundary

No production mutation is authorized by this contract until milestones M0–M9 pass and Stick approves an exact M10 transaction boundary.

## Required receipts

Every transaction must be rehydratable from files alone:

- `transaction.json`
- `scope.json`
- `approval-boundary.json`
- `restore-point.json`
- `precheck.json`
- `apply-start.json` if child started
- `heartbeat.jsonl`
- `apply-exit.json` if child exited/was killed
- `postcheck.json`
- `recovery-decision.json`
- `recovery-action.json` if recovery ran
- `final-report.json`
- `hard-gates.json`
- `evidence-manifest.json`
- `evidence-manifest.sha256`

## Restore point contract

Before any critical apply, a restore point newer than 3600 seconds must exist or be created and verified. If the restore point is absent, stale, invalid, or outside mutation authority, apply is blocked.

## Observer recovery contract

After apply failure, the observer must classify npm/package base health. If the official package root is missing, empty, or incomplete and a verified fresh restore point exists, observer-owned recovery restores/reinstalls only from that restore point. Hidden `.openclaw-*` staging directories are never moved/deleted until process references prove inactive.

## Separation contract

Package apply, Gateway restart, and functional smoke are separate transactions. Package apply cannot restart Gateway. Gateway restart cannot run functional smoke. Functional smoke requires separate explicit approval.

## Current implementation level

M0/M1 skeleton exists:

- `scripts/critical_apply_contracts.py`
- `scripts/critical_apply_observer_runner.py`
- `scripts/critical_apply_plugins/openclaw_npm_package.py`

The runner currently supports `prepare`, `status`, `final-report`, `validate`, and an intentional `execute` refusal. This is deliberate until the later gates pass.
