# CAH-J1 M2A Supervisor / Ingress Architecture Freeze

**Date:** 2026-08-13

**Status:** `PASS_CONSTRUCTION_HOLD_FOR_INDEPENDENT_VERIFICATION` when local gates pass

**Boundary:** offline/shadow architecture and executable contract fixtures only; stop before M2B.

## 1. Authority and immutable inputs

This freeze is subordinate to the owner revision SHA-256 `6d80167ba92e1a68c9d17d6027135b289f88c6b9f3d6fd9e24ea86aedab459af`, M0 adjudication SHA-256 `1d2853fba832ebc243423c3c2dac00def80c3c2b56d892ee8c83aeff96c34427`, final M0-R3 contracts and independent evidence, and the permanently preserved M1 package with final `PASS_VERIFIED`. `IMMUTABLE-INPUT-SEALS.json` binds them. M2A creates no production authority.

## 2. Components and trust boundaries

`COMPONENT-TRUST-BOUNDARIES.json` freezes ingress adapters as untrusted translators; the supervisor as sole orchestration owner; journal core as sole semantic writer; descriptor CAS as immutable-byte owner; AuthorityDB as cross-transaction scope/fence/nonce authority only; ProgressDB as disposable projection; the child boundary as constrained and non-authoritative; reducer/checker as future boundaries; and notifications as non-authoritative projections. Journal semantics outrank every process or delivery observation.

## 3. Ingress acceptance and ACK/replay

`INGRESS-ENVELOPE-CONTRACT.json` requires transaction, request, contract, authority-reference, scope, provenance, idempotency, derived event ID, and payload CAS identities under strict versioned canonical JSON and bounded sizes. Paths and caller semantics convey no authority. `INGRESS-IDEMPOTENCY-CONTRACT.json` and `ACK-REPLAY-VECTORS.json` require CAS capture, canonical append/sync/reopen verification, and any required AuthorityDB bind before ACK. Exact duplicates return the original journal-derived ACK without append; a different proposal sharing event ID is an integrity HOLD. ProgressDB never decides.

## 4. Supervisor startup, recovery, and lifecycle

`SUPERVISOR-STATE-MACHINE.json` freezes one complete adjacency: supervisor creates and registers the run root; journal genesis and epoch precede AuthorityDB rows; scope reserve/bind/activate precedes launch intent and child start; result bytes enter CAS before canonical result acknowledgement; reconciliation and cleanup precede reduction; terminal, witness, release, direct closure, receipt, and lock release retain M0-R3 order. No child self-registration or shared-path creation is allowed.

`SUPERVISOR-CRASH-VECTORS.json` covers both sides of every transition. Every crash window is action/call closed until exact journal, epoch/fence, CAS, and relevant AuthorityDB proofs. `RECOVERY-AUTHORITY-ORDER.json` makes the semantic journal superior to PID, registry, status, ProgressDB, and notification. Unknown child/provider outcome fails closed and is never automatically retried.

## 5. Nonce, child, concurrency, and path ownership

`CHILD-LAUNCH-AND-RESULT-CONTRACT.json` integrates N01–N11. N04 remains safe-resume-before-call-start only under unchanged hashes, valid owner authority, active scope fence, and canonical authorization; otherwise retire and HOLD. N07 remains response capture, canonical synced outcome, then AuthorityDB binding and full commit. No weakened ordering is accepted.

`CONCURRENCY-FENCING-VECTORS.json` freezes 2-, 5-, and 20-client same-scope contention, overlapping-scope exclusion, disjoint scopes, stale epochs, and stale result fences. Exactly one active owner exists for overlapping scopes. The exact monotonic fence is passed to the child and checked for every mutation and result.

`PATH-OWNERSHIP-MATRIX.json` assigns one creator/writer per mutable shared path. The supervisor materializer alone creates the run root and `nonce-ledger/`; runner paths must already exist. Only CAS writes CAS, only journal writes canonical events, only AuthorityDB writes authority state, and ProgressDB is disposable.

## 6. Security and privacy

The v1 boundary detects but does not claim isolation from malicious same-UID peers. Every opened ancestor and leaf is checked without symlink following; mutable shared regular files require expected device/inode, owner, mode, link count one, and revalidation across open/write/rename to constrain symlink, hardlink, and TOCTOU substitution. Directory descriptors are pinned; writes use relative `openat`-style operations and atomic exclusive publication. Secrets are never embedded in journal/projection/notifications: only bounded fingerprints or CAS identities. Receipts are bounded and redact payload bytes.

## 7. Offline/shadow and promotion boundaries

`ZERO-EFFECT-CONTRACT.json` forbids commands, providers, network, production, Gateway/config/runtime, install, source implementation, Git stage/commit/push, cron/systemd, and external messages. Shadow outputs are non-authoritative. `M2B-PROMOTION-GATES.json` separates future M2B implementation gates from future M2C shadow gates; neither authorizes production. M2A stops before M2B.

## 8. Observer/check wiring and terminal artifacts

Construction records STARTED criteria, validator/test/privacy/diff receipts, immutable inputs, source hashes, zero effects, terminal status, and an evidence manifest. Independent alert/check wiring is not created here because cron/systemd and external messaging are forbidden; the main requester separately launches independent review. Construction may close only as `PASS_CONSTRUCTION_HOLD_FOR_INDEPENDENT_VERIFICATION`; final M2A PASS requires a fresh independent root that rehashes inputs/artifacts, executes validator and mutation tests, confirms privacy/zero effect, and writes `PASS_VERIFIED` or an exact HOLD.

## 9. Executable artifact index

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
- `validate_m2a_freeze.py`
- `test_validate_m2a_freeze.py`

The validator rejects hash/schema defects, incomplete adjacency, duplicate mutable ownership, non-unique vectors, permissive crash windows, authority reordering, N04/N07 weakening, ProgressDB authority, missing 20-way contention, runner creation of `nonce-ledger/`, runtime/production authority, threshold shortfalls, or missing design cross-references. Mutation tests preserve each expected rejection and must not weaken this gate.
