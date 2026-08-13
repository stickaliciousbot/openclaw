# Critical Apply Supervisor-Owned Event Journal

## Owner Revision — M0 Freeze Adjudication

**Date:** 2026-08-13  
**Owner-authored candidate:** `critical-apply-supervisor-owned-event-journal-owner-revision-2026-08-13.md`  
**Candidate SHA-256:** `6d80167ba92e1a68c9d17d6027135b289f88c6b9f3d6fd9e24ea86aedab459af`  
**Status:** `PASS_AS_OWNER_AUTHORED_M0_INPUT_HOLD_FOR_SIX_PROTOCOL_CONTRACT_CORRECTIONS_BEFORE_FREEZE`  
**Scope:** design review only; no implementation, provider call, Gateway/config/runtime change, or production mutation

---

## 1. Adjudication

The owner revision is accepted as the governing **input to M0 architecture freeze**.

It successfully resolves the major weaknesses in the earlier draft:

- the canonical journal remains the sole transaction-fact authority;
- CAS owns immutable governing evidence bytes;
- ProgressDB is explicitly rebuildable and non-authoritative;
- WitnessDB independently witnesses history without replacing semantics;
- AuthorityDB governs only cross-transaction leases and nonce consumption;
- terminal reduction precedes terminal decision;
- owned-process cleanup precedes PASS sealing;
- proposer and committer identities are distinct;
- terminal conflicts are integrity failures, not severity-precedence choices;
- semantic paths are immutable and cannot be inferred from command text;
- WSL filesystem and Unix-socket path constraints are explicit;
- notification remains orthogonal to semantic result;
- same-UID prevention versus detection is honestly separated.

This is now a coherent transaction-system architecture rather than merely an improved observer.

It should **not yet be labelled the frozen v1 contract**. The six BLOCKER contracts below must be resolved and represented in schemas, state transitions, fixtures, and health gates during M0.

---

## 2. BLOCKER contracts required before M0 freeze

### B1 — AuthorityDB ↔ canonical journal crash consistency

**Affected sections:** 11, 15–16, 30, 61, 76, 79.

AuthorityDB and the canonical journal govern different facts, but protected execution depends on both. The revision does not yet specify deterministic recovery for crashes between their commits.

Examples:

- scope lease row created, journal lease event absent;
- journal authority event committed, AuthorityDB row still pending;
- nonce reserved in AuthorityDB, journal barrier absent;
- release recorded in one store but not the other.

There is also an ordering mismatch: section 30 acquires the cross-transaction lease before creating the supervisor epoch, while the section 11 row requires `supervisor_epoch`.

**Required frozen correction:**

Create/recover the supervisor epoch before any AuthorityDB row that binds it. Define AuthorityDB records as fenced state machines, for example:

```text
RESERVED_PENDING_JOURNAL
  -> JOURNAL_COMMITTED
  -> ACTIVE / CONSUMED
  -> RELEASE_PENDING
  -> RELEASED
```

Every state-changing row must bind:

```text
transaction_id
supervisor_epoch
fencing_token
journal_sequence (nullable only while pending)
journal_event_sha256 (nullable only while pending)
authority_receipt_sha256
```

Recovery must classify every journal/AuthorityDB combination. An orphan pending row cannot silently become active, and an ACTIVE row without its bound journal event cannot authorize a protected action.

**Required fixture:** kill at every boundary of reserve → journal commit → activate and release intent → journal commit → release.

---

### B2 — Complete at-most-once nonce/call protocol

**Affected sections:** 11, 16–17, 42, 53, 66, invariant 28.

A unique nonce row prevents duplicate insertion but does not alone prove safe behavior across reservation, call start, unknown outcome, recovery, and retirement.

**Required frozen nonce states:**

```text
RESERVED_PENDING_JOURNAL
COMMITTED_NOT_USED
CALL_START_COMMITTED
OUTCOME_RECORDED
RETIRED
UNKNOWN_CONSUMED
```

**Required policy:**

- No provider/protected call before `CALL_START_COMMITTED` is durably acknowledged.
- Crash after reservation but before call start does not automatically authorize a call; resume requires an explicit frozen safe-resume rule.
- Crash after call-start commit without a recorded outcome yields `UNKNOWN_CONSUMED` by default.
- `UNKNOWN_CONSUMED` is non-retryable without new owner authority and a new nonce.
- Retrying transport after an ambiguous external attempt is forbidden unless the exact contract expressly proves that the external operation is idempotent.
- Nonce retirement and one-call authority consumption remain durable even when semantic validation later HOLDs.

**Required fixture:** exhaustive crash matrix around each state transition, including call attempted/no response and response received/not journaled.

---

### B3 — Canonical terminal input-freeze event

**Affected sections:** 30–31, 38, 53, invariants 10–12.

“Freeze preterminal head” must be a committed event, not an in-memory supervisor condition.

**Required frozen correction:**

Make `TERMINAL_REDUCTION_PREPARED` mandatory and canonical. It must bind:

```text
semantic_input_closed = true
freeze_sequence
freeze_event_sha256
contract_sha256
reducer_sha256
allowed_post_freeze_event_types
```

The reducer evaluates the semantic prefix ending at this fence. After the fence, semantic evidence proposals are rejected. Only explicitly enumerated closeout events may follow.

A crash during reduction recovers from the committed fence and re-runs the same reducer against the same prefix.

---

### B4 — Name and bind three distinct journal heads

**Affected sections:** 31, 43–44, 77, invariant 30.

The design currently refers to “canonical journal head” even though terminal decision, seal, notification, witness, lease release, and closeout occur at different sequences.

**Required frozen vocabulary:**

1. `semantic_reduction_head` — the committed input-freeze event/head consumed by the reducer.
2. `terminal_decision_head` — the canonical `TERMINAL_DECISION` event that binds the reduction result.
3. `closeout_head` — the final canonical event written before the transaction becomes closed.

**Binding rules:**

- `REDUCTION.json` binds `semantic_reduction_head`.
- `TERMINAL_DECISION` binds the reduction and its antecedent head.
- `MANIFEST.json` and `TERMINAL-SEAL.json` bind `terminal_decision_head` and semantic result.
- `COMPLETION-RECEIPT.json` binds `closeout_head`, terminal seal, notification outcome, lease-release outcome, and provider/production effects.
- Later closeout events cannot rewrite the sealed semantic result.

---

### B5 — Journal-derived event idempotency, never ProgressDB authority

**Affected sections:** 17, 22–23, 61, 66.

ProgressDB may cache event IDs, but it cannot decide whether a proposal was already committed.

**Required frozen correction:**

Before accepting event proposals, `JournalWriter` reconstructs or verifies its canonical idempotency map from the journal:

```text
(transaction_id, event_id) -> proposal_sha256, sequence, event_sha256, ACK
```

ProgressDB may accelerate lookup only after proving its indexed head equals the verified journal head. A missing, stale, deleted, or corrupt ProgressDB falls back to journal-derived state before accepting proposals.

**Required fixture:** delete/corrupt ProgressDB after an event was ACKed, retry the same event, and prove the original ACK is returned without a duplicate append.

---

### B6 — Descriptor-bound, crash-durable CAS publication

**Affected sections:** 24–25, 50, 67.

Path validation followed by a path-based copy leaves a TOCTOU window. CAS publication also needs exact durability ordering before journal acknowledgement.

**Required frozen correction:**

- open the registered artifact relative to a verified directory descriptor using `openat`/equivalent and `O_NOFOLLOW`;
- `fstat` before and after hashing/copying;
- bind device, inode, owner, mode, size, and hard-link policy;
- hash bytes from the opened descriptor, not by reopening the path;
- write a same-filesystem temporary CAS object;
- `fdatasync` the object;
- atomically publish via link/rename without overwrite;
- `fsync` affected parent directories;
- reopen and rehash the published object;
- append and sync the journal event;
- only then ACK.

Orphan CAS objects after a crash are allowed and can be garbage-collected only by a future separately proven policy. A journal-referenced object must always survive recovery.

**Required fixture:** source replacement/mutation during capture plus kill at every object-publication boundary.

---

## 3. SHOULD-FIX contracts before implementation

These should be frozen in M0 as well, but they do not alter the core authority model.

### S1 — Lease release and supervisor close ordering

The current lifecycle closes the supervisor before releasing leases/lock, while closeout requires reporting release.

Recommended order:

```text
semantic seal
notification terminal outcome
independent terminal witness
SCOPE_LEASE_RELEASE_INTENT committed
AuthorityDB release recorded
SCOPE_LEASE_RELEASE_RECORDED committed
COMPLETION_RECEIPT prepared
SUPERVISOR_CLOSED committed
transaction lock released
```

No protected action is allowed after release intent. If AuthorityDB release fails, closeout reports a lease-release HOLD and does not claim clean closure.

### S2 — WitnessDB assurance grade

For version 1, freeze an explicit claim such as:

```text
WITNESS_GRADE_1_SAME_HOST_SAME_UID_INDEPENDENT_PROCESS_DETECTION
```

This detects accidental/out-of-contract truncation but is not hostile same-UID tamper-proof. Stronger claims require separate UID, append-only privileged service, remote host, or comparable isolation.

### S3 — Late notification receipt behavior

Supervisor waits to a bounded notification deadline and commits one of:

```text
DELIVERED_CONFIRMED
DELIVERY_FAILED
DELIVERY_UNKNOWN
```

before close. A later delivery receipt is notification-plane evidence only or a new follow-up transaction; it cannot append to the closed canonical journal or rewrite semantics.

### S4 — Authority-grade SQLite/WAL contract

AuthorityDB and WitnessDB need stronger storage rules than rebuildable ProgressDB:

- Linux filesystem with proven semantics; not `/mnt/c`;
- `journal_mode=WAL` only if the frozen recovery/backup procedure includes `-wal` and `-shm`;
- `synchronous=FULL` or a documented, tested equivalent;
- `BEGIN IMMEDIATE` for lease/nonce mutations;
- bounded busy timeout and fail-closed contention handling;
- schema/user-version checks;
- integrity check and recovery policy;
- parent-directory durability for DB creation;
- backup/checkpoint rules that never copy only the main DB while live WAL contains authority rows.

---

## 4. Required M0 deltas

M0 should add the following concrete deliverables to the owner revision’s section 71:

1. `AUTHORITYDB-FENCING-PROTOCOL.md`
2. `NONCE-AT-MOST-ONCE-STATE-MACHINE.json`
3. `TERMINAL-HEADS-AND-FENCE-CONTRACT.json`
4. `EVENT-IDEMPOTENCY-CONTRACT.json`
5. `CAS-CAPTURE-DURABILITY-CONTRACT.json`
6. `SQLITE-AUTHORITY-STORAGE-CONTRACT.json`
7. `WITNESS-ASSURANCE-GRADE.json`
8. crash-boundary test vectors covering all cross-store state transitions
9. a revised lifecycle transition table proving cleanup, sealing, notification, lease release, closure, and lock release ordering

M0 PASS requires independent verification that these additions do not create a second semantic authority.

---

## 5. Verification of owner-authored candidate

The inbound revision was preserved byte-for-byte at:

`/home/stickai/.openclaw/workspace/design/critical-apply-supervisor-owned-event-journal-owner-revision-2026-08-13.md`

Verification:

- inbound SHA-256: `6d80167ba92e1a68c9d17d6027135b289f88c6b9f3d6fd9e24ea86aedab459af`
- preserved SHA-256: `6d80167ba92e1a68c9d17d6027135b289f88c6b9f3d6fd9e24ea86aedab459af`
- byte comparison: exact
- bytes: `55,288`
- lines: `2,990`
- bounded privacy scan: `R6_R6_PHASE_A_BOUNDED_PRIVACY_SCAN_PASS`
- blocking privacy findings: `0`
- privacy issues: `0`
- scanner SHA-256: `ce38bf7811561c096bfe72ef12fc799712986d77ff86cb62b8e099eedc481115`
- privacy receipt SHA-256: `5c50398324a002c910270de7953ad5b6035ecffd7ec74ab3f7ca321bb494119a`

---

## 6. Recommended next milestone

Proceed to:

```text
CAH-J1-M0_ARCHITECTURE_AUTHORITY_AND_EVENT_CONTRACT_FREEZE
```

with the owner revision as immutable source input and this adjudication as the required correction ledger.

M0 remains:

```text
PREP_ONLY
zero provider/model calls
zero production mutation
zero Gateway/config/runtime mutation
zero consumed production authority
```

### M0 PASS criteria

- all six BLOCKER contracts resolved;
- all four SHOULD-FIX contracts frozen;
- schemas and transition tables internally consistent;
- crash matrices complete;
- no second semantic authority introduced;
- exact owner-authored input hash preserved;
- bounded privacy scan PASS;
- independent verification PASS.

Expected terminal:

```text
PASS_CAH_J1_M0_SUPERVISOR_EVENT_JOURNAL_ARCHITECTURE_AUTHORITY_STORAGE_SECURITY_AND_CRASH_CONSISTENCY_CONTRACTS_FROZEN_NO_PRODUCTION_EFFECT
```

Until then:

```text
HOLD_FOR_CAH_J1_M0_SIX_PROTOCOL_CONTRACT_CORRECTIONS
```
