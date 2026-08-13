# CAH-J1 M2A-R2 Exact Supervisor / Ingress Contract Repair

**Date:** 2026-08-13  
**Status:** construction may close only as `PASS_CONSTRUCTION_HOLD_FOR_FRESH_INDEPENDENT_VERIFICATION` after zero local unsafe accepts/blockers.  
**Boundary:** design/evidence plus disposable `/tmp` only. M2B, source/runtime implementation, Git stage/commit/push/index/config/ref mutation, install, Gateway/config/runtime/provider/network/production, cron/systemd, and external action remain forbidden.

## Immutable authority and preservation

This R2 construction is subordinate to M0-R3 and M1 and preserves the original candidate, original independent HOLD, R1 repair candidate, and fresh R1 independent HOLD. `IMMUTABLE-INPUT-SEALS.json` names and hashes the actual authority files; the validator rehashes those files and validates every supported governing manifest entry. The authoritative R1 independent manifest SHA-256 is `019f34f1b8f4e64b191457f283e66eb0e0a010f33b6841851b8be204970a6f6b` and the R1 repair manifest SHA-256 is `62b2357a1e15bf165ef80bcc1129da31719bae28f1f7ddea39af26c1fd027b4e`.

## B01 — exact closeout and separated lifecycle

The canonical event/transition/state chain has exactly T00–T22 and ends at `SUPERVISOR_CLOSED`. `COMPLETION_RECEIPT_PUBLISHED` and `TRANSACTION_LOCK_RELEASED` are absent from the canonical projection and are represented only by LO01/LO02 in `ARTIFACT-LIFECYCLE-CONTRACT.json`. Both operations are `canonical=false`, `semantic_authority=false`, and may mutate none of semantic, terminal-decision, or closeout heads. Each requires the immutable exact `closeout_head == sha256(SUPERVISOR_CLOSED event bytes)`. LO02 additionally requires the verified LO01 publication receipt. AP01 remains a noncanonical side condition bound to the exact release head and required before T22; it introduces no canonical state.

## B02 — typed proof registry and crash recovery

`RECOVERY-PROOF-REGISTRY.json` is the canonical typed registry. Every T00–T22 `BEFORE_COMMIT` and `AFTER_COMMIT` vector resolves to exactly one unique transition/side proof. AP01 and LO01/LO02 use a separate typed artifact/lifecycle proof collection. Every proof has only the exact typed fields: `id`, `transition_id`, `side`, `observed_state`, `required_journal_events`, `required_journal_hashes`, `required_cas_refs`, `required_authoritydb_state`, `required_authoritydb_receipt`, `required_authoritydb_fence`, `required_authoritydb_epoch`, `prohibited_actions`, `terminal_on_ambiguity`, and `recovery_classification`. Content is phase- and side-specific; cross-side reuse, unresolved/extra proof IDs, permissive action/provider gates, and ambiguity retry are rejected.

## B03 — strict schemas, inventory, seals, and cross-artifact equality

`STRICT-SCHEMA-REGISTRY.json` defines exact allowed/required keys, types, array lengths, and per-index nested schemas for every governing JSON object. Fixed artifact schemas and frozen artifact digests reject prefix spoofing, unknown/missing keys, shape/type/value drift, extra or missing identities, and nested extension attacks. The validator freezes components/roles, mutable paths/owners, transitions/states, nonce objects, concurrency and ACK vectors, artifact/lifecycle operations, proof IDs, ingress fields, and immutable input seals.

Cross-artifact gates require exact state/child action semantics; exact inactive future provider gates; child/concurrency epoch/fence fields on every mutation/result; child/idempotency/ACK result order; transition authority component roles; trusted path inventory and scalar creator/writer roles; exact same/overlap/disjoint scopes; exact lifecycle prerequisites/order/head immutability; and exact proof vector resolution. `DESIGN-CONTRACT.json` binds this design's SHA-256 plus the exact required statement set and canonical statement digest; filename presence is not authority. `ARTIFACT-SHA256.json` seals every contract, schema/proof artifact, validator, all test suites, the exact R1 independent test source snapshot, design snapshot, and bounded privacy scanner.

## Ingress, nonce, ACK, and effect boundary

Ingress accepts only the exact declared fields, rejects unknown fields and untrusted paths, and derives no semantic authority from transport. N01–N11 identities, order, predicates, and unconditional N07 descriptor-CAS/journal/AuthorityDB sequence remain exact. ACK occurs only after exact CAS capture/reopen, canonical journal sync/reopen, and required AuthorityDB bind/reopen. Provider and legacy call gates remain false throughout M2A. Runtime/production/shadow authority remains false and M2B is not started.

## Required executable evidence and handoff

The local suite executes the prior 55 construction mutations, prior 26 adversarial cases, all 56 byte-for-byte R1 independent mutation bodies with an R2 path/import/direct-check adaptation, and at least 18 new R2 schema/seal/proof/lifecycle combination attacks. Every unsafe fixture must reject. The exact bounded privacy scanner SHA-256 `ce38bf7811561c096bfe72ef12fc799712986d77ff86cb62b8e099eedc481115`, input rehash, repository parity, zero-effect receipt, process-leak check, and evidence manifest are mandatory. Failed attempts are retained. Local success is still a construction HOLD for a fresh independent verifier; M2B remains not started.

## Machine-bound required statements

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

`COMPONENT-TRUST-BOUNDARIES.json`, `INGRESS-ENVELOPE-CONTRACT.json`, `SUPERVISOR-STATE-MACHINE.json`, `INGRESS-IDEMPOTENCY-CONTRACT.json`, `PATH-OWNERSHIP-MATRIX.json`, `SUPERVISOR-CRASH-VECTORS.json`, `CONCURRENCY-FENCING-VECTORS.json`, `ACK-REPLAY-VECTORS.json`, `CHILD-LAUNCH-AND-RESULT-CONTRACT.json`, `RECOVERY-AUTHORITY-ORDER.json`, `M2B-PROMOTION-GATES.json`, `ZERO-EFFECT-CONTRACT.json`, `IMMUTABLE-INPUT-SEALS.json`, `ARTIFACT-LIFECYCLE-CONTRACT.json`, `RECOVERY-PROOF-REGISTRY.json`, `STRICT-SCHEMA-REGISTRY.json`, `DESIGN-CONTRACT.json`, `ARTIFACT-SHA256.json`, `validate_m2a_r2.py`, `test_validate_m2a_r2.py`, `independent_adversarial_r2.py`, `independent_adversarial_tests_r2.py`, and `combination_attacks_r2.py`.
