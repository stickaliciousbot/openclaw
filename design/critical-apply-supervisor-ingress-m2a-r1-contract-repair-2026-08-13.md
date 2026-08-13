# CAH-J1 M2A-R1 Supervisor / Ingress Contract Repair

**Date:** 2026-08-13  
**Status:** `PASS_CONSTRUCTION_HOLD_FOR_FRESH_INDEPENDENT_VERIFICATION` only when every local gate passes  
**Boundary:** design/evidence and disposable `/tmp` only. M2B, source/runtime implementation, install, Git mutation, Gateway/config/runtime/provider/network/production, cron/systemd, and external messaging remain forbidden.

## Authority and preservation

This repair is subordinate to the verified M0-R3 and M1 contracts. It preserves the original M2A candidate (manifest SHA-256 `3f026764d75c96acfca5317e9d9c67e48b140e2281ed563c9bff08f5f5e2f7e2`) and its independent HOLD (manifest SHA-256 `c014a7f7bb6c1b7bb06b29fc72b47c2134eda27e0dc97e50d6cac38c0bf9b538`) as immutable inputs. `IMMUTABLE-INPUT-SEALS.json` binds these plus M0-R3/M1 authorities.

## B01 — canonical adjacency

`SUPERVISOR-STATE-MACHINE.json` contains a single ordered `canonical_transitions` chain. Noncanonical receipt-preimage preparation is held separately in `artifact_preparations`; it has no canonical `from`/`to` state and is bound to the exact release journal head. The canonical projection directly contains `SCOPE_LEASE_RELEASE_RECORDED -> SUPERVISOR_CLOSED`. `validate_m2a_r1.py` derives the projection and rejects any intervening canonical event, wrong state adjacency, duplicate/missing transition, or promotion of preparation into the chain.

## B02 — unconditional N07 CAS sequence

`CHILD-LAUNCH-AND-RESULT-CONTRACT.json` freezes exact ordered N07 tokens: unconditional governing response/receipt byte capture in descriptor-bound CAS; reopen verification of exact CAS SHA-256, size, and path; canonical `CALL_OUTCOME_RECORDED` referencing that exact object; journal sync and reopen verification; only then AuthorityDB begin, exact bind/receipt, `COMMIT_FULL`, and reopen verification. Optional, skipped, fake, or reordered CAS is rejected.

## B03 — typed action/call semantics

`action_allowed` means only bounded non-provider child eligibility. It is false before exact active-scope and launch-intent barriers and false after result/execution/release. `provider_call_allowed` is distinct and always false throughout M2A. Legacy `call_allowed` is a strict false alias. Child launch never grants provider authority. A future provider gate (not active here) requires exact N05 canonical `CALL_START_COMMITTED`, N06 durable AuthorityDB consume, active fence/epoch, owner authority, and immutable request hashes.

## B04 — exact nonce identities

The ordered N01–N11 objects are frozen by complete equality of ID, order, semantic, and critical predicates. Prefix/length checks are insufficient and absent. Suffix, action, order, duplicate, and missing mutations are required rejection cases.

## B05 — crash vectors

Every canonical transition has exactly one `BEFORE_COMMIT` and one `AFTER_COMMIT` vector. Their observed states equal transition `from` and `to`, respectively; IDs follow `CV-<transition>-<side>`; recovery proof IDs are nonempty and transition/side-specific; bounded action and provider-call eligibility remain false until proof. Noncanonical preparation has separate `AV-*` artifact vectors and is excluded from canonical adjacency counts.

## B06 — executable content gates

The validator enforces strict schemas and content invariants: one active owner for overlapping scope, disjoint progress, exact 2/5/20 contention, stale epoch/fence rejection, no child registration/shared-path creation, ACK only after exact CAS+journal sync/reopen and required AuthorityDB bind, same-event/different-proposal HOLD/no execution, exact N04 with no bypass, notification/WitnessDB non-semantic, unknown outcome terminal/no retry or new call, strict ingress unknown-field/path rejection, exactly one scalar creator/writer for each mutable path, meaningful ACK vectors with explicit inputs/outcomes/barriers, non-authoritative runtime/shadow outputs, and exact transition-side coverage.

The repaired suite includes the prior 12 mutations, all 26 independent adversarial cases, additional B01–B05 mutations, and direct positive assertions. Failed attempts must be preserved; tests may not be weakened.

## Artifacts

- `COMPONENT-TRUST-BOUNDARIES.json`
- `INGRESS-ENVELOPE-CONTRACT.json`
- `SUPERVISOR-STATE-MACHINE.json`
- `INGRESS-IDEMPOTENCY-CONTRACT.json`
- `PATH-OWNERSHIP-MATRIX.json`
- `SUPERVISOR-CRASH-VECTORS.json`
- `CONCURRENCY-FENCING-VECTORS.json`
- `ACK-REPLAY-VECTORS.json`
- `CHILD-LAUNCH-AND-RESULT-CONTRACT.json`
- `RECOVERY-AUTHORITY-ORDER.json`
- `M2B-PROMOTION-GATES.json`
- `ZERO-EFFECT-CONTRACT.json`
- `IMMUTABLE-INPUT-SEALS.json`
- `ARTIFACT-SHA256.json`
- `validate_m2a_r1.py`
- `test_validate_m2a_r1.py`
- `independent_adversarial_r1.py`

## Terminal and handoff

No detached alert/check is created because the boundary forbids cron/systemd and external messages. Construction closes only as `PASS_CONSTRUCTION_HOLD_FOR_FRESH_INDEPENDENT_VERIFICATION`; an independent verifier must rehash governing inputs and the repaired manifest, execute the validator and all mutation/adversarial tests in disposable copies, rerun the exact privacy scanner SHA-256 `ce38bf7811561c096bfe72ef12fc799712986d77ff86cb62b8e099eedc481115`, verify original candidate/HOLD immutability and zero operational effect, and issue a fresh PASS or exact HOLD. M2B remains not started.
