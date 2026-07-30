# Critical Apply Harness v2 Adoption Review

Date: 2026-07-30
Status: SOURCE/DOCS REVIEW — no production mutation authorised

## Intake verification

Stick provided three v2 artifact checksums:

- `critical-apply-observation-harness-architecture-v2.0-2026-07-30.md` — expected `1fecc6b04d6fce0baffcb86ea1bfd7ea5da559e83c14032d4eb95792d6f5ec3b`
- `CRITICAL_APPLY_OBSERVER_LOW_LEVEL_DESIGN_AND_BUILD_PLAN_v2.0_20260730.md` — expected `66243ebdf5baf3ccccbf864faa83ad26872906de5a1d1b95aef6e155025b3f6b`
- `CRITICAL_APPLY_HARNESS_V2_REVIEW_AND_STRENGTHENING_SUMMARY_20260730.md` — expected `13b641a6503b134216f9c94dadc2f2b72d4f551268085e8a3ac32eff50aa868c`

Received and verified:

- Architecture v2.0 matched `1fecc6b04d6fce0baffcb86ea1bfd7ea5da559e83c14032d4eb95792d6f5ec3b` and is stored at `critical-apply-observation-harness-architecture-v2.0-2026-07-30.md`.
- Low-level design v2.0 matched `66243ebdf5baf3ccccbf864faa83ad26872906de5a1d1b95aef6e155025b3f6b`.
- Review/strengthening summary matched `13b641a6503b134216f9c94dadc2f2b72d4f551268085e8a3ac32eff50aa868c`.

The prior architecture-v2 HOLD is cleared.

## Review result

The v2 docs materially supersede the initial scaffold. The original branch remains useful as a source/docs foundation, but M0/M1 must be reframed around the v2 contract before any production-critical work resumes.

Key v2 adoption decisions:

1. Production requires HRL-3: a pre-existing supervisor-managed observer service with startup reconciliation. `nohup`, `setsid`, background shells, or raw detached subprocesses are not sufficient.
2. Mutation child release requires durable `apply-intent`, `apply-spawned-blocked`, final precondition revalidation, atomic approval consumption, and durable `apply-release` before the child can `execve`.
3. Restore point freshness is checked at mutation release; after release the bound artifact remains transaction-eligible if seal/integrity and release-time eligibility verify.
4. Exit code is not system truth. Terminal derivation must use the full execution/package/substrate/guard/recovery state vector.
5. Filesystem reconstruction with atomic rename is the primary recovery path when npm/global substrate is broken or unknown; npm reinstall is not the default repair for npm damage.
6. Evidence requires crash-consistent atomic JSON, hash-chain journal, projections derived from journal, non-circular manifest, and terminal seal.
7. Package apply, Gateway restart, and functional smoke remain separate transactions and approvals; no authority inheritance.
8. M6B service bootstrap is a separate milestone before any production OpenClaw package mutation can be governed by the service.

## Scaffold adjustments made

- Added v2 phase, terminal, execution, official package, substrate, guard, and recovery enums to `scripts/critical_apply_contracts.py` while retaining v1 skeleton compatibility.
- Tightened generated transaction IDs to use 128-bit random suffixes.
- Added HRL-3/ad-hoc-detach-forbidden metadata to the skeleton approval boundary.
- Copied verified architecture v2.0, v2 low-level design, review summary, and checksum list into the project folder.
- Updated project/hydrator docs to mark v2 as the governing contract direction and architecture-v2 as verified.

## Non-authority statement

This pass performed source/docs/test updates only. It did not deploy, install, activate a service, restart/reload Gateway, mutate cron, call providers/delivery, mutate protected memory, mutate OpenClaw package files, or perform recovery.

## Current next action

Continue M0-v2 only:

- finalize strict schemas/enums;
- write transition and terminal derivation tables;
- add v2 state-machine tests;
- keep production mutation blocked.

Expected safe terminal after completion of that later M0-v2 gate:

`M0_PASS_CRITICAL_APPLY_V2_CONTRACT_FINALIZED_NO_MUTATION`
