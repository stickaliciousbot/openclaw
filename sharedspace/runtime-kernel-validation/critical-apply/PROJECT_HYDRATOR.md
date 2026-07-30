# Critical Apply Harness Project Hydrator

Use this after context reset to restore project state.

## Project status

Active project: Critical Apply Harness for OpenClaw/Stickbot.

Universal Runtime Kernel work is paused. Critical Apply Harness is the active build track.

Current branch:

`feature/critical-apply-harness-observer-20260730`

## Safety rules to load first

1. Read `AGENTS.md` Execution Governance critical apply hard rule.
2. Read `MEMORY.md` top entries for:
   - Critical apply global rule — no foreground apply processes.
   - OpenClaw global npm mixed-generation incident + prevention rule.
3. Read project docs listed below.

## Canonical docs

- `sharedspace/runtime-kernel-validation/critical-apply/CRITICAL_APPLY_OBSERVER_LOW_LEVEL_DESIGN_AND_BUILD_PLAN_20260730.md`
- `sharedspace/runtime-kernel-validation/critical-apply/CRITICAL_APPLY_OBSERVATION_HARNESS_ARCHITECTURE_20260730.md`
- `sharedspace/runtime-kernel-validation/critical-apply/CRITICAL_APPLY_CONTRACT.md`
- `sharedspace/runtime-kernel-validation/critical-apply/CRITICAL_APPLY_TROUBLESHOOTING_AND_REPAIR_NOTEBOOK.md`
- `sharedspace/runtime-kernel-validation/critical-apply/CRITICAL_APPLY_RESTORE_SCRIPT_REPURPOSE_NOTES_20260730.md`

## Implementation files

- `scripts/critical_apply_contracts.py`
- `scripts/critical_apply_observer_runner.py`
- `scripts/critical_apply_plugins/__init__.py`
- `scripts/critical_apply_plugins/openclaw_npm_package.py`
- `scripts/test_critical_apply_runner.py`
- `scripts/test_openclaw_npm_package_plugin.py`

## Current implementation level

M0/M1 skeleton:

- contract primitives/enums/validators exist;
- OpenClaw npm package read-only classifiers exist;
- runner supports `prepare`, `status`, `final-report`, `validate`;
- runner `execute` intentionally refuses mutation and writes `execute-refusal.json`;
- no production apply/restart/smoke path is enabled.

## Next milestone

M0 — Critical Apply Contract Finalization.

Pass criteria:

- contract schemas validate;
- state machine totality proven/documented;
- no foreground critical apply path exists;
- docs and implementation skeleton pass local tests;
- no production mutation.

Expected terminal:

`M0_PASS_CRITICAL_APPLY_CONTRACT_FINALIZED_NO_MUTATION`

## Absolute prohibitions until gates pass

- No npm install.
- No package root mutation.
- No Gateway restart/reload.
- No cron mutation/calls.
- No provider/Gmail/Telegram/delivery smoke.
- No foreground critical apply.
- No production mutation before M0–M9 pass.

## Rehydration checklist

1. `git status --short --branch`
2. Confirm branch `feature/critical-apply-harness-observer-20260730`.
3. Read this hydrator.
4. Read low-level design and contract.
5. Run tests only if asked or continuing implementation:
   - `python3 -m unittest scripts/test_critical_apply_runner.py scripts/test_openclaw_npm_package_plugin.py`
6. Continue at M0/M1; do not skip to live apply.
