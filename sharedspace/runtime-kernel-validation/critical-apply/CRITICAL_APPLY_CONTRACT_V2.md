# Critical Apply Observation Harness v2 — Strict M0 Contract

Status: M0 machine-validatable contract artifact. No production mutation or mutation-capable runner is implemented or authorised.

## Governing authorities

Normative:

1. `critical-apply-observation-harness-architecture-v2.0-2026-07-30.md` SHA-256 `1fecc6b04d6fce0baffcb86ea1bfd7ea5da559e83c14032d4eb95792d6f5ec3b`
2. `CRITICAL_APPLY_OBSERVER_LOW_LEVEL_DESIGN_AND_BUILD_PLAN_V2_20260730.md` SHA-256 `66243ebdf5baf3ccccbf864faa83ad26872906de5a1d1b95aef6e155025b3f6b`

Explanatory only:

- `CRITICAL_APPLY_HARNESS_V2_REVIEW_AND_STRENGTHENING_SUMMARY_20260730.md` SHA-256 `13b641a6503b134216f9c94dadc2f2b72d4f551268085e8a3ac32eff50aa868c`

## Code authority

The machine contract is `scripts/critical_apply_contracts.py`. It defines:

- exact v2 phase enum: 23 values;
- exact v2 terminal enum: 17 values;
- state-vector enums and typed records;
- process, filesystem, generation, surface, surface-set, authority, and approval records;
- strict JSON parser/canonical JSON SHA-256;
- phase-transition table and validator;
- terminal-derivation table and pure derivation function;
- authority-envelope validation and approval one-time-consumption rules;
- restore-point release-time freshness semantics;
- fixture-only surface profiles for package apply, package-only recovery, Gateway restart, functional smoke, guarded cron update, protected-memory writer state, and model-route apply.

The module imports no `subprocess`, performs no `os.system`, uses no shell execution, and contains no npm/OpenClaw CLI/Gateway/cron/provider/delivery mutation path.

## Phase contract

The exact v2 phases are:

```text
CREATED
PREPARING
RESTORE_POINT_READY
PRECHECK_PASS
PLAN_SEALED
AWAITING_APPROVAL
APPROVAL_RECORDED
COMMIT_LOCKS_ACQUIRED
COMMIT_REVALIDATING
COMMIT_VALIDATED
APPLY_INTENT_DURABLE
APPLY_CHILD_SPAWNED_BLOCKED
MUTATION_RELEASED
APPLY_RUNNING
APPLY_EXIT_OBSERVED
APPLY_EXIT_UNKNOWN
POSTCHECK_RUNNING
RECOVERY_DECIDING
RECOVERY_INTENT_DURABLE
RECOVERY_RUNNING
POST_RECOVERY_CHECK
FINALIZING
TERMINAL
```

Every legal transition is enumerated by `transition_table()`. All unlisted transitions fail closed. The table records for each phase: allowed predecessor phases, allowed successor phases, required receipts, permitted actor, lock requirements, approval state requirement, primary/recovery mutation possibility flags, terminal derivations, and prohibited-transition rule.

Hard transition invariants:

- `MUTATION_RELEASED` is impossible without durable blocked-child identity, commit revalidation, release-time restore validity, and atomic approval consumption.
- No second primary mutation may follow consumed approval.
- Recovery cannot run before `RECOVERY_INTENT_DURABLE`.
- Terminal PASS requires a valid terminal seal.
- Plugins cannot bypass the core transition table.

## Terminal contract

The exact v2 terminals are:

```text
CANCELLED_NO_APPROVAL
APPROVAL_EXPIRED_REPREPARE_REQUIRED
APPROVED_NOT_STARTED
PRECONDITION_DRIFT_BLOCKED
APPLY_STATE_UNKNOWN_OPERATOR_REQUIRED
FAIL_SAFE_NO_MUTATION
APPLY_EFFECTIVE_EXIT_NONZERO_HOLD
PASS_PACKAGE_INSTALLED_HOLD_FOR_SEPARATE_RESTART
FAIL_MUTATION_PARTIAL_RECOVERY_REQUIRED
RECOVERY_PASS_HOLD_FOR_SEPARATE_RESTART
RECOVERY_PASS_WITH_GUARD_WARNING_OPERATOR_HOLD
RECOVERY_BLOCKED_STATE_UNKNOWN
ROLLBACK_FAIL_OPERATOR_REQUIRED
EVIDENCE_TAMPERED_OR_INCOMPLETE_HOLD
PASS_CONTROLLED_GATEWAY_RESTART
PASS_FUNCTIONAL_SMOKE
FUNCTIONAL_SMOKE_FAIL_NO_PACKAGE_RECOVERY
```

Terminal classification is the pure core function `derive_terminal(StateVector)`. Inputs include transaction type, execution state, official target/package state, package-manager substrate state, running/staging generation states, guard state, recovery state, evidence integrity, authority validity, applicable policy, restart/smoke authority flags, and equality/mutation-evidence proofs.

Rules:

- Plugins may contribute observed facts only; they may not assert PASS.
- Unknown/conflicting/tampered evidence never maps to PASS.
- `FAIL_SAFE_NO_MUTATION` requires exact pre-state equality for every declared write-set surface and no unresolved mutation evidence.
- Nonzero exit with official target exactly candidate maps to `APPLY_EFFECTIVE_EXIT_NONZERO_HOLD`, not automatic rollback.

## State-vector contracts

The exact execution, official package, substrate, guard, and recovery enums are implemented as requested. Additional M0 records cover:

- running generation identity;
- hidden/staging generation identity;
- process identity requiring PID + start ticks + boot ID + cgroup + executable realpath + command digest;
- filesystem identity;
- mount identity;
- boot identity via process/restore evidence records;
- evidence integrity state;
- authority validity state.

PID-only process identity is invalid.

## Surface-set contract

Each transaction declares:

- `read_set`
- `write_set`
- `recovery_write_set`
- `guard_set`
- `forbidden_set`

Rules implemented:

- surfaces require canonical identifier and type;
- primary mutation may touch only `write_set`;
- automatic recovery may touch only `recovery_write_set`;
- guard surfaces are read-only except signed field-level allowed drift;
- forbidden surfaces cannot overlap mutation-capable sets;
- ambiguous assignments fail closed;
- wildcard paths require bounded expansion;
- symlink and mount crossing policy must be explicit;
- recovery authority is separate from restore existence;
- package apply, restart, and functional smoke are separate profiles.

Fixture profiles exist under `scripts/tests/fixtures/critical_apply/contracts/` and are generated/validated by `fixture_surface_profiles()`.

## Authority-envelope contract

Schema: `critical_apply.authority_envelope.v2`.

The envelope binds transaction ID, campaign ID, owner, approval mechanism, one-time nonce, issuance and expiry, transaction-spec SHA-256, runner bundle SHA-256, contract bundle SHA-256, plugin bundle SHA-256, interpreter identity SHA-256, supervisor-unit SHA-256, candidate authority SHA-256, exact argv/exec-spec SHA-256, environment-policy SHA-256, restore-point ID, restore manifest SHA-256, restore method, pre-state fingerprint SHA-256, surface-set digest, resource/timeout/network/recovery policy hashes, maximum primary mutations, maximum automatic recoveries, restart-authorised flag, and functional-smoke-authorised flag.

Approval binds the canonical authority-envelope hash. Consumption is one-time and atomic by contract. Drift of candidate, argv, environment, runner, contract, plugin, interpreter, supervisor, restore point, restore manifest, pre-state, guard state, executable path, host/boot/mount/filesystem identity, resource policy, network policy, timeout policy, or recovery policy invalidates approval and requires reprepare/reapproval.

## Restore-point semantics

M0 defines but does not implement restore:

- freshness is evaluated at `MUTATION_RELEASE`;
- max age is 3,600 seconds unless stricter transaction policy applies;
- fresh at prepare but stale at release blocks;
- approval delay cannot substitute a newer restore point;
- new restore point requires new authority envelope and approval;
- valid at release remains eligible for that transaction’s recovery after one hour if immutable artifact and seal verify;
- clock rollback, negative age, missing monotonic evidence, substitution, corrupt manifest, or unsafe path blocks;
- restore point is evidence, not recovery authority;
- recovery authority is separately present in the authority envelope;
- recovery count is at most one and idempotency-keyed;
- unknown recovery commit state requires inspection, not blind retry.

## Prepare / approve / commit

M0 formally defines the three boundaries:

- Prepare: classify scope, inspect candidate/pre-state, generate guard sentinels, build/seal plan; release preparation locks before approval wait.
- Approve: bind sealed authority envelope; approval is not a shell command.
- Commit: acquire ordered locks, verify unconsumed approval, revalidate bound identities, block on drift, record commit validation, later create blocked child, record full child identity, consume approval atomically, release mutation only after durable receipts.

M0 does not implement child gate or locks.

## Strict schema and canonicalisation

Implemented rules:

- duplicate JSON keys reject;
- unknown fields reject under authority schema;
- missing fields reject;
- NaN/Infinity reject;
- uppercase/malformed SHA-256 reject;
- UTC RFC3339 timestamps required;
- wall and monotonic time distinguished for restore freshness;
- deterministic canonical JSON and SHA-256;
- list ordering preserved;
- realpath/symlink policy represented in surfaces;
- path traversal rejects;
- transaction ID requires >=128-bit suffix;
- machine-readable error codes.

## A1–A4 gates

- `A1_PASS_NO_FOREGROUND_OR_GENERIC_CRITICAL_MUTATION_PATH`
- `A2_PASS_STRICT_SCHEMA_AND_CANONICAL_HASH`
- `A3_PASS_STATE_MACHINE_TOTALITY`
- `A4_PASS_AUTHORITY_BINDING_ONE_TIME_CONSUMPTION`

M0 PASS requires all four gates, static checks, tests, privacy scan, production absence proof, manifest validation, and one scoped local commit. M1 remains blocked.
