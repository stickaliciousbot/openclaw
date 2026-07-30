# Critical Apply Observation Harness v2 — M2 One-Time Authority and Commit Fencing

Status: M2 implementation artifact. Fixture-only; no production mutation authority.

## Scope

M2 adds held kernel-lock primitives, canonical lock ordering, fixture-only lock roots, transaction fencing generations/tokens, prepare/approve/commit separation, synthetic approval receipts, atomic one-time approval consumption, commit revalidation, drift invalidation, stale-holder classification, conflict-set evaluation, synthetic release fixtures, and release-time restore freshness evaluation.

M2 does not implement an observer daemon, systemd service, blocked-child launcher, production worker, command runner, npm install, restore creation, restore/recovery, OpenClaw package classifier, Gateway lifecycle action, cron call, provider/delivery call, production lock acquisition, real owner approval consumption, or M3.

## Lock API inventory

- `critical_apply_locks.KernelLock.acquire(...)`
- `KernelLock.release()`
- `LockSet.assert_live()`
- `LockSet.release()`
- `acquire_lockset(...)`
- `issue_fencing(...)`
- `validate_fencing_current(...)`
- `classify_stale_holder(...)`

A JSON receipt is never accepted as a live lock capability. `KernelLock` and `LockSet` reject pickling/serialization as authority.

## Canonical lock order

0. `global:critical-apply`
1. `package-manager:global-prefix`
2. `surface:*` locks in canonical lexicographic order
3. `transaction:journal`

Release is reverse order. M2 has no reentrant mode. Prepare releases locks before `AWAITING_APPROVAL`.

## Contract surface identities

Fixture-only canonical identities include global critical apply, npm/global prefix, OpenClaw official package root, npm executable link, npm metadata, Gateway lifecycle, Gateway config/routes, strict cron definitions, scheduler state, protected writer state, protected memory, Runtime Kernel, Ledger, Context Bridge, model routing, provider/delivery surface, and transaction journal.

## Fencing

On global acquisition, a root-local fencing generation is atomically incremented and a 256-bit token is created. Durable receipts record only the token SHA-256. Old tokens, wrong transaction tokens, wrong-root tokens, released tokens, and stale generations fail closed. This is not a lease and has no wall-clock lock break.

## Prepare / approve / commit split

Prepare validates fixture transaction shape, canonicalises surface sets, seals authority, journals `PLAN_SEALED`, then releases mutation locks before `AWAITING_APPROVAL`.

Approve records immutable synthetic `critical_apply.approval_receipt.v2` receipts and journals `APPROVAL_RECORDED`. Only `allow-once` is accepted. `allow-always`, wrong nonce, wrong owner, wrong envelope/spec/campaign/transaction, expired or ill-ordered times all fail.

Commit reacquires locks, verifies live fencing, verifies approval is present/unexpired/unconsumed, evaluates conflict and restore freshness, records per-field commit revalidation, and stops at `COMMIT_VALIDATED`. M2 does not create `APPLY_INTENT_DURABLE`, `APPLY_CHILD_SPAWNED_BLOCKED`, `MUTATION_RELEASED`, or `APPLY_RUNNING` for milestone execution.

## Atomic approval consumption

`receipts/approval-consumed.json` uses M1 immutable create/no-replace semantics. It binds transaction, campaign, approval-receipt SHA, authority-envelope SHA, nonce, commit-revalidation SHA, fencing generation/token SHA, lock-set digest, actor identity, boot/time, primary mutation ordinal `1`, and maximum primary mutations `1`.

Concurrent fixture consumers produce exactly one live consumed-approval capability; losing consumers classify `APPROVAL_ALREADY_CONSUMED` or blocked. Unknown or conflicting crash states never convert to PASS.

## Drift invalidation

The drift matrix covers transaction spec, authority envelope, contract/runner/plugin/interpreter/supervisor bundles, candidate identity/version/source, executable/argv/env/cwd/uid/gid, npm prefix, restore identity/manifest/method/freshness, pre-state, strict guard, scheduler semantics, surface set, resource/timeout/network/recovery policy, host/boot/mount, lock set, fencing generation, conflict set, approval expiry/nonce/owner, restart/smoke flags, and maximum mutation count.

Only exact field-level policy sealed before approval may allow non-authority drift. Immutable candidate/code/restore/approval/lock/mutation-boundary fields do not accept drift.

## C1 release-time restore freshness

M2 implements fixture-only freshness evaluation. It does not create, archive, verify, reconstruct, or restore a package root. Freshness passes only when release age is `< 3600` seconds, identity and manifest match, integrity and authority binding pass, boot/monotonic/clock policies pass, and no substitution occurs. Exactly `3600` seconds blocks. Same-transaction recovery after one hour is eligible only when release-time eligibility was durably recorded and restore identity/manifest/integrity remain valid.

## Gates

- `M2_G1_PASS_KERNEL_LOCK_ORDER_AND_EXCLUSION`
- `M2_G2_PASS_TRANSACTION_FENCING_AND_STALE_WORKER_REJECTION`
- `M2_G3_PASS_PREPARE_APPROVE_COMMIT_REVALIDATION`
- `M2_G4_PASS_ATOMIC_ONE_TIME_APPROVAL_CONSUMPTION`
- `A4_PASS_AUTHORITY_BINDING_ONE_TIME_CONSUMPTION`
- `C1_PASS_RELEASE_TIME_RESTORE_FRESHNESS`
