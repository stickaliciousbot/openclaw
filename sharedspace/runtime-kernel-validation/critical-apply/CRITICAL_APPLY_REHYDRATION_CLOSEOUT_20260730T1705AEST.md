# Critical Apply Harness Rehydration Closeout — 2026-07-30 17:05 AEST

Status: SOURCE/DOCS/HYDRATOR UPDATE — no production mutation authorised

## GitHub branch

- Branch: `feature/critical-apply-harness-observer-20260730`
- Latest pushed v2 adoption commit before this closeout update: `aa3da4efc8a2166fd4847185d07e4155d14523bd`

## New documentation incorporated

Verified and committed v2 docs already present in the project workspace:

- `CRITICAL_APPLY_OBSERVER_LOW_LEVEL_DESIGN_AND_BUILD_PLAN_V2_20260730.md`
  - SHA256 `66243ebdf5baf3ccccbf864faa83ad26872906de5a1d1b95aef6e155025b3f6b`
- `CRITICAL_APPLY_HARNESS_V2_REVIEW_AND_STRENGTHENING_SUMMARY_20260730.md`
  - SHA256 `13b641a6503b134216f9c94dadc2f2b72d4f551268085e8a3ac32eff50aa868c`
- `CRITICAL_APPLY_HARNESS_V2_SHA256SUMS_20260730.txt`
- `CRITICAL_APPLY_V2_ADOPTION_REVIEW_20260730.md`
- `M0_V2_ADOPTION_VALIDATION.json`

## Current HOLD

The checksum list references:

- `critical-apply-observation-harness-architecture-v2.0-2026-07-30.md`
- expected SHA256 `1fecc6b04d6fce0baffcb86ea1bfd7ea5da559e83c14032d4eb95792d6f5ec3b`

The actual file was not visible in inbound media/project tree during the v2 adoption pass. Continue to classify this as `ARCHITECTURE_V2_FILE_HOLD_CHECKSUM_ONLY` until the exact file is received and verified.

## Rehydrator state

Use:

- `PROJECT_HYDRATOR.md`
- `project_hydrator.latest.json`

Both now identify v2 as the governing contract posture and preserve the architecture-v2 HOLD.

## Implementation state

M0-v2 adoption scaffold only:

- v2 phase/terminal/state-vector enums are present;
- transaction IDs use 128-bit random suffixes;
- approval boundary records HRL-3 requirement and ad-hoc-detach prohibition;
- runner `execute` intentionally refuses mutation;
- no HRL-3 daemon/service exists yet;
- no package/restart/smoke transaction is enabled.

## Safety confirmation

This closeout updates source/docs/hydrator and memories only. It did not perform deploy, install, service activation, Gateway restart/reload, cron mutation/call, provider/delivery action, OpenClaw package mutation, protected-memory mutation, or functional smoke.

## Next safe action

Receive and verify the missing architecture v2.0 file, then continue M0-v2 strict contract closure only.

Expected future M0-v2 terminal:

`M0_PASS_CRITICAL_APPLY_V2_CONTRACT_FINALIZED_NO_MUTATION`
