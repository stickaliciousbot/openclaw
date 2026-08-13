# CAH-J1 M2A-R2-R1 Authority-Coherence and Proof-Semantic Repair

**Date:** 2026-08-13  
**Status:** construction may close only as `PASS_CONSTRUCTION_HOLD_FOR_FRESH_INDEPENDENT_VERIFICATION` after zero blockers and zero unsafe accepts.  
**Boundary:** design/evidence plus disposable `/tmp` only. The immutable R2 candidate is an input, not a mutation target. M2B, source/runtime implementation, Git stage/commit/push/index/config/ref mutation, install, Gateway/config/runtime/provider/network/production, cron/systemd, and external action remain forbidden.

## Immutable authority and R1 role coherence

This R2-R1 repair is subordinate to M0-R3 and M1 and preserves the original M2A candidate, original independent HOLD, R1 repair candidate, finalized R1 independent verification, and immutable R2 candidate. `IMMUTABLE-INPUT-SEALS.json` names and hashes the actual authority files; the validator live-rehashes those files and every supported governing manifest entry.

The sole authoritative finalized R1 independent manifest SHA-256 is `49ccef7181ff090c95267f8a5dcc3ccaaba88ce3bd42ade63cef13293e41d2d2`. The hash `019f34f1b8f4e64b191457f283e66eb0e0a010f33b6841851b8be204970a6f6b` is classified only as a superseded preliminary R1 independent manifest hash: it is non-authoritative, cannot bind immutable inputs, status, handoff, design authority, promotion, or any governing claim, and must never substitute for the finalized hash.

## Exact closeout and separated lifecycle

The canonical event/transition/state chain has exactly T00–T22 and ends at `SUPERVISOR_CLOSED`. `COMPLETION_RECEIPT_PUBLISHED` and `TRANSACTION_LOCK_RELEASED` are absent from the canonical projection and represented only by LO01/LO02 in `ARTIFACT-LIFECYCLE-CONTRACT.json`. Both operations are `canonical=false`, `semantic_authority=false`, and may mutate none of semantic, terminal-decision, or closeout heads. Each requires the immutable exact `closeout_head == sha256(SUPERVISOR_CLOSED event bytes)`. LO02 additionally requires the verified LO01 publication receipt. AP01 remains a noncanonical side condition bound to the exact release head and required before T22; it introduces no canonical state.

## Frozen phase- and side-specific recovery proofs

`RECOVERY-PROOF-SEMANTIC-INVENTORY.json` is the frozen expected semantic inventory and `RECOVERY-PROOF-REGISTRY.json` must equal it proof-for-proof. Every T00–T22 `BEFORE_COMMIT` and `AFTER_COMMIT` vector resolves to exactly one unique same-transition/same-side proof. AP01 and LO01/LO02 use six separate typed artifact/lifecycle proofs.

Each proof binds its exact observed phase, exact canonical predecessor or current journal event, and an explicitly labelled predecessor/current head. AuthorityDB epoch, state, receipt, and fence claims are transition-specific. Pre-initialization phases use the typed `NONE_NOT_INITIALIZED` sentinel and never claim a committed epoch or active fence. Reservation, journal binding, activation, release intent, released, release-recorded, and supervisor-closed phases use distinct exact AuthorityDB projections. Released and closed phases require retired or no-active fencing state. AuthorityDB receipts appear only as the exact latest semantically available receipt; otherwise the typed `NONE_NO_AUTHORITYDB_RECEIPT` sentinel is required.

CAS references are exact and transition-specific. Envelope capture, child-result capture, execution/evidence commit, terminal seal, completion-receipt preimage, publication, and lock-release lifecycle proofs distinguish absent-before from exact-after references. Empty CAS arrays are allowed only when the corresponding phase has no CAS object to prove. Lifecycle `required_journal_events` contains canonical events only. Noncanonical preparation/publication/release receipts are bound through exact typed AuthorityDB receipt or CAS-reference fields and never masquerade as canonical journal events.

The validator derives a frozen expected proof object for every transition/side and requires exact object equality in the semantic inventory, proof registry, and crash-vector mirror. Generic nonempty strings, cross-side reuse, role substitution, wrong predecessor/current heads, premature epoch/fence claims, active fences after release, missing exact CAS refs, noncanonical receipt publication in journal events, and contradictory proof prose reject.

## Strict schemas, inventory, seals, and cross-artifact equality

`STRICT-SCHEMA-REGISTRY.json` retains exact allowed/required keys, types, array lengths, and per-index nested schemas for every prior governing JSON object. The new semantic inventory is directly schema- and exact-content-validated by the validator. Fixed artifact digests reject shape/type/value drift, unknown/missing identities, and nested extension attacks.

`DESIGN-CONTRACT.json` binds this design's full SHA-256, the exact machine statement set below, and its canonical statement digest. The validator scans exact governing design claims, rejects contradictory prose, and cross-checks finalized/superseded hash roles against `IMMUTABLE-INPUT-SEALS.json`, status, handoff, and live authority-input rehash. `ARTIFACT-SHA256.json` seals every governing contract, proof inventory/registry, validator, suites, exact R1 independent source snapshot, design, and bounded privacy scanner.

## Ingress, nonce, ACK, and effect boundary

Ingress accepts only exact declared fields, rejects unknown fields and untrusted paths, and derives no semantic authority from transport. N01–N11 identities, order, predicates, and unconditional N07 descriptor-CAS/journal/AuthorityDB sequence remain exact. ACK occurs only after exact CAS capture/reopen, canonical journal sync/reopen, and required AuthorityDB bind/reopen. Provider and legacy call gates remain false throughout M2A. Runtime/production/shadow authority remains false and M2B is not started.

## Required executable evidence and handoff

The local suite ports all prior 155 mutation cases without changing their unsafe bodies, adds at least 30 semantic proof and manifest-role mutations spanning pre-root, pre-lease, reserved, bound, active, child/result, terminal, release, closed, artifact, and lifecycle phase families, and runs direct positive semantic assertions. Every unsafe fixture must reject. The exact bounded privacy scanner SHA-256 `ce38bf7811561c096bfe72ef12fc799712986d77ff86cb62b8e099eedc481115`, immutable-input live rehash, tracked parity, zero-effect receipt, process-leak check, and complete evidence manifest are mandatory. Failed attempts are retained. Local success remains a construction HOLD for a fresh independent verifier; no independent verifier is launched here and M2B remains false.

## Machine-bound required statements

- `FINAL_R1_INDEPENDENT_MANIFEST_SHA256=49ccef7181ff090c95267f8a5dcc3ccaaba88ce3bd42ade63cef13293e41d2d2`
- `SUPERSEDED_PRELIMINARY_R1_MANIFEST_SHA256=019f34f1b8f4e64b191457f283e66eb0e0a010f33b6841851b8be204970a6f6b`
- `SUPERSEDED_HASH_IS_AUTHORITY=false`
- `CANONICAL_FINAL_EVENT=SUPERVISOR_CLOSED`
- `CANONICAL_TRANSITION_COUNT=23`
- `COMPLETION_RECEIPT_PUBLICATION_CANONICAL=false`
- `TRANSACTION_LOCK_RELEASE_CANONICAL=false`
- `NONCANONICAL_OPERATIONS_MAY_MUTATE_SEMANTIC_HEAD=false`
- `NONCANONICAL_OPERATIONS_MAY_MUTATE_TERMINAL_DECISION_HEAD=false`
- `NONCANONICAL_OPERATIONS_MAY_MUTATE_CLOSEOUT_HEAD=false`
- `LOCK_RELEASE_REQUIRES_VERIFIED_PUBLICATION_RECEIPT=true`
- `CANONICAL_CRASH_VECTOR_COUNT=46`
- `ARTIFACT_PREPARATION_VECTOR_COUNT=2`
- `LIFECYCLE_VECTOR_COUNT=4`
- `TYPED_PROOF_COUNT=52`
- `PROVIDER_CALL_ALLOWED_IN_M2A=false`
- `M2B_STARTED=false`
- `TERMINAL=PASS_CONSTRUCTION_HOLD_FOR_FRESH_INDEPENDENT_VERIFICATION`

## Governing artifacts

`COMPONENT-TRUST-BOUNDARIES.json`, `INGRESS-ENVELOPE-CONTRACT.json`, `SUPERVISOR-STATE-MACHINE.json`, `INGRESS-IDEMPOTENCY-CONTRACT.json`, `PATH-OWNERSHIP-MATRIX.json`, `SUPERVISOR-CRASH-VECTORS.json`, `CONCURRENCY-FENCING-VECTORS.json`, `ACK-REPLAY-VECTORS.json`, `CHILD-LAUNCH-AND-RESULT-CONTRACT.json`, `RECOVERY-AUTHORITY-ORDER.json`, `M2B-PROMOTION-GATES.json`, `ZERO-EFFECT-CONTRACT.json`, `IMMUTABLE-INPUT-SEALS.json`, `ARTIFACT-LIFECYCLE-CONTRACT.json`, `RECOVERY-PROOF-SEMANTIC-INVENTORY.json`, `RECOVERY-PROOF-REGISTRY.json`, `STRICT-SCHEMA-REGISTRY.json`, `DESIGN-CONTRACT.json`, `ARTIFACT-SHA256.json`, `validate_m2a_r2.py`, `test_validate_m2a_r2.py`, `independent_adversarial_r2.py`, `independent_adversarial_tests_r2.py`, `independent_adversarial_tests_r1_exact_source.py`, `combination_attacks_r2.py`, and `semantic_proof_mutations_r2_r1.py`.
