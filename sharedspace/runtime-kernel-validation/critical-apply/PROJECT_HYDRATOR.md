# Critical Apply Harness Project Hydrator

Use this after context reset to restore project state.

## Project status

Active project: Critical Apply Harness for OpenClaw/Stickbot.

Universal Runtime Kernel work is paused. Critical Apply Harness is the active build track.

Current branch:

`feature/critical-apply-harness-observer-20260730`

Latest pushed baseline before v2 adoption: `a0e1be27ebaaa17a9329385b3ca3a70057822b66`.

Latest pushed v2 adoption commit before this rehydration closeout update: `aa3da4efc8a2166fd4847185d07e4155d14523bd`.

## Safety rules to load first

1. Read `AGENTS.md` Execution Governance critical apply hard rule.
2. Read `MEMORY.md` top entries for:
   - Critical apply global rule — no foreground apply processes.
   - Critical Apply Harness branch/scaffold.
   - OpenClaw global npm mixed-generation incident + prevention rule.
3. Read project docs listed below.

## Governing v2 posture

Stick supplied strengthened v2 materials on 2026-07-30. The v2 contract supersedes the initial M0/M1 scaffold for production readiness.

Verified v2 artifacts received:

- `sharedspace/runtime-kernel-validation/critical-apply/CRITICAL_APPLY_OBSERVER_LOW_LEVEL_DESIGN_AND_BUILD_PLAN_V2_20260730.md` — SHA256 `66243ebdf5baf3ccccbf864faa83ad26872906de5a1d1b95aef6e155025b3f6b`
- `sharedspace/runtime-kernel-validation/critical-apply/CRITICAL_APPLY_HARNESS_V2_REVIEW_AND_STRENGTHENING_SUMMARY_20260730.md` — SHA256 `13b641a6503b134216f9c94dadc2f2b72d4f551268085e8a3ac32eff50aa868c`
- `sharedspace/runtime-kernel-validation/critical-apply/CRITICAL_APPLY_HARNESS_V2_SHA256SUMS_20260730.txt`

HOLD artifact:

- `critical-apply-observation-harness-architecture-v2.0-2026-07-30.md` is referenced by checksum `1fecc6b04d6fce0baffcb86ea1bfd7ea5da559e83c14032d4eb95792d6f5ec3b`, but the file itself was not visible in inbound media during the v2 adoption pass. Do not claim architecture-v2 equivalence until received and verified.

## Canonical docs

Read these first:

- `sharedspace/runtime-kernel-validation/critical-apply/CRITICAL_APPLY_V2_ADOPTION_REVIEW_20260730.md`
- `sharedspace/runtime-kernel-validation/critical-apply/CRITICAL_APPLY_OBSERVER_LOW_LEVEL_DESIGN_AND_BUILD_PLAN_V2_20260730.md`
- `sharedspace/runtime-kernel-validation/critical-apply/CRITICAL_APPLY_HARNESS_V2_REVIEW_AND_STRENGTHENING_SUMMARY_20260730.md`
- `sharedspace/runtime-kernel-validation/critical-apply/CRITICAL_APPLY_HARNESS_V2_SHA256SUMS_20260730.txt`
- `sharedspace/runtime-kernel-validation/critical-apply/CRITICAL_APPLY_REHYDRATION_CLOSEOUT_20260730T1705AEST.md`

Initial scaffold docs retained for lineage:

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

M0-v2 adoption scaffold:

- v2 phase/terminal/state-vector enums added while retaining v1 skeleton compatibility;
- transaction ID random suffix tightened to 128 bits;
- approval boundary records HRL-3 requirement and ad-hoc-detach prohibition;
- OpenClaw npm package classifiers remain read-only by default;
- runner supports `prepare`, `status`, `final-report`, `validate`;
- runner `execute` intentionally refuses mutation and writes `execute-refusal.json`;
- no HRL-3 daemon/service exists yet;
- no production apply/restart/smoke path is enabled.

## Next milestone

M0-v2 — Strict Contract Finalization.

Pass criteria:

- architecture v2.0 file received and checksum-verified;
- strict schemas/enums validate;
- transition table and terminal derivation table exist;
- authority envelope and one-time consumption model are specified;
- HRL-3 service topology and bootstrap boundary are represented;
- no foreground/ad hoc detached critical apply path exists;
- docs and implementation skeleton pass local tests;
- no production mutation.

Expected terminal:

`M0_PASS_CRITICAL_APPLY_V2_CONTRACT_FINALIZED_NO_MUTATION`

## Absolute prohibitions until gates pass

- No npm install.
- No package root mutation.
- No service activation/bootstrap unless a later bootstrap milestone is explicitly approved.
- No Gateway restart/reload.
- No cron mutation/calls.
- No provider/Gmail/Telegram/delivery smoke.
- No foreground critical apply.
- No ad hoc detached critical apply.
- No production mutation before M0-v2 through M10 pass and Stick approves the exact later transaction.

## Rehydration checklist

1. `git status --short --branch`
2. Confirm branch `feature/critical-apply-harness-observer-20260730`.
3. Read this hydrator.
4. Read the v2 adoption review and verified v2 low-level design.
5. Read `CRITICAL_APPLY_REHYDRATION_CLOSEOUT_20260730T1705AEST.md` for the latest closeout status.
6. Check whether architecture v2.0 was received; verify SHA before using it.
7. Run tests only if continuing implementation:
   - `python3 -m unittest scripts/test_critical_apply_runner.py scripts/test_openclaw_npm_package_plugin.py`
8. Continue at M0-v2; do not skip to bootstrap/live apply.
