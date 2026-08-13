# CAH-J1-M0 AuthorityDB Fencing Protocol

**Contract:** `critical_apply.authoritydb_fencing_protocol.v1`  
**Status:** `FROZEN_FOR_M0_B1_B2_S4`  
**Scope:** offline contract only; no provider, Terra, runtime, Gateway, configuration, install, Git, or production action

## 1. Authority boundary

The canonical journal is the **sole semantic and transaction-fact authority**. AuthorityDB is authoritative only for facts that must survive and exclude across transactions:

- current ownership of a shared production mutation scope;
- monotonically fenced scope generations;
- reservation, consumption, unknown consumption, outcome recording, and retirement of one-call/approval nonces.

AuthorityDB never records or decides semantic `PASS`, `HOLD`, or `FAIL`. Its state cannot manufacture a journal event, terminal result, provider outcome, or production-effect claim. ProgressDB is never consulted for authority. A protected action requires both (a) the exact committed journal barrier and (b) the matching live AuthorityDB fenced state described below.

## 2. Mandatory startup ordering — epoch before row

The only permitted startup order is:

1. verify the frozen transaction contract and transaction root;
2. acquire and retain the transaction `journal/LOCK` descriptor;
3. recover and verify the canonical journal prefix;
4. create or recover a supervisor epoch and commit `SUPERVISOR_STARTED` or `SUPERVISOR_RECOVERED` to the journal;
5. only then open an AuthorityDB mutation transaction and create a row that binds that epoch;
6. reserve, journal, and activate cross-transaction authority;
7. open worker ingress and arm the independent checker/watcher;
8. commit the protected-action barrier;
9. begin the protected action only after all barrier predicates verify.

Acquiring a scope lease before step 4 is forbidden. An AuthorityDB mutation whose `supervisor_epoch` is absent from the verified canonical journal is rejected. Recovery creates a new epoch only after lock exclusivity and journal recovery; it never silently reuses a dead epoch.

## 3. Fencing-token allocation

Each normalized `scope_hash` has a persistent counter. Allocation occurs under one `BEGIN IMMEDIATE` transaction:

```text
read scope_counter
next = scope_counter + 1
persist next
insert scope lease history row with fencing_token = next
append authority receipt row
COMMIT with synchronous=FULL
```

Rules:

- `fencing_token` is an unsigned 64-bit positive integer, monotonically increasing per `scope_hash`.
- Counters and released lease rows are never deleted or reset during ordinary operation.
- `UNIQUE(scope_hash, fencing_token)` and a unique-current-scope constraint prevent collisions.
- Every protected-action journal barrier carries `scope_hash`, `fencing_token`, `transaction_id`, `supervisor_epoch`, and the exact AuthorityDB receipt SHA-256.
- Immediately before spawn/send/mutation, the supervisor re-reads AuthorityDB and rejects a row unless all bound fields and the latest receipt hash match the barrier.
- A worker never receives unfenced mutation authority. A stale epoch or lower token cannot authorize an action, even if it retains old journal bytes or a process handle.
- After database recovery/restore, no token is issued until reconciliation computes a high-water mark from the preserved DB/WAL and all journal-bound receipts. The next token is strictly greater. If that cannot be proven, authority service stays `HOLD`.

## 4. Authority receipt

Every AuthorityDB state transition atomically appends an immutable receipt to `authority_receipts` and updates the current row. The receipt contains:

```text
schema
receipt_id
record_kind                 # SCOPE_LEASE or NONCE
record_key_sha256
transition_ordinal
previous_receipt_sha256
from_state
to_state
transaction_id
origin_supervisor_epoch
supervisor_epoch
scope_hash or nonce_sha256
fencing_token               # required for scope; authority-generation token for nonce
journal_sequence            # null only in a pending-before-journal state
journal_event_sha256        # null only in a pending-before-journal state
contract_sha256
request_sha256              # nonce only
db_generation_uuid
created_at_utc              # reporting only
authority_receipt_sha256
```

`authority_receipt_sha256` is SHA-256 over RFC-8785-compatible canonical JSON of every receipt field except itself. The receipt chain is append-only. An update that does not advance `transition_ordinal` by one or whose previous hash does not match fails closed.

## 5. Scope-lease state machine

Frozen states:

```text
RESERVED_PENDING_JOURNAL
  -> JOURNAL_COMMITTED
  -> ACTIVE
  -> RELEASE_PENDING
  -> RELEASED
```

No transition may be skipped in the logical receipt chain, although `JOURNAL_COMMITTED -> ACTIVE` may occur in the same `BEGIN IMMEDIATE` database transaction with two receipts.

### 5.1 Reserve → journal → activate

1. **Reserve in AuthorityDB** — allocate the next fence and commit `RESERVED_PENDING_JOURNAL`; journal references are null. The row grants no action.
2. **Commit canonical reservation event** — commit and sync `SCOPE_LEASE_RESERVATION_COMMITTED`, binding the pending receipt hash and all identity/fence fields.
3. **Bind journal in AuthorityDB** — verify the event from journal bytes, transition to `JOURNAL_COMMITTED`, and store its sequence/hash.
4. **Activate in AuthorityDB** — transition to `ACTIVE`, retaining the exact journal binding, and commit the active receipt.
5. **Commit acquisition record** — commit and sync `SCOPE_LEASE_ACQUIRED`, binding the active receipt hash.

A protected action is permitted only when:

```text
AuthorityDB state == ACTIVE
AND AuthorityDB latest receipt == journal SCOPE_LEASE_ACQUIRED receipt
AND reservation event and acquisition event verify in the canonical hash chain
AND transaction_id, contract, epoch, scope, token all match
AND no SCOPE_LEASE_RELEASE_INTENT exists for that token
AND transaction lock and process identity still verify
```

Thus an orphan pending row cannot become active silently, and an `ACTIVE` row lacking its exact acquisition event cannot authorize an action.

### 5.2 Release intent → journal → release

The only clean release order is:

1. commit and sync canonical `SCOPE_LEASE_RELEASE_INTENT`, binding the active receipt;
2. permanently close the protected-action gate for that scope/token;
3. under `BEGIN IMMEDIATE`, transition `ACTIVE -> RELEASE_PENDING`, binding the release-intent sequence/hash;
4. transition `RELEASE_PENDING -> RELEASED`, preserving fence history, and commit the released receipt;
5. commit and sync `SCOPE_LEASE_RELEASE_RECORDED`, binding the released receipt;
6. include the release result in the completion receipt; only then commit `SUPERVISOR_CLOSED` and release the transaction lock.

Once release intent is committed, no protected action is allowed even if AuthorityDB still says `ACTIVE`. If the AuthorityDB release cannot be proven, closeout is lease-release `HOLD`; it never claims clean closure.

## 6. Cross-store recovery matrix — scope lease

| Canonical journal | AuthorityDB | Classification | Deterministic recovery | Action allowed? |
|---|---|---|---|---|
| No reservation event | No row | `NOT_RESERVED` | reserve only under current valid epoch | No |
| No reservation event | `RESERVED_PENDING_JOURNAL` | `ORPHAN_PENDING` | same transaction/epoch may commit the exact reservation event if contract and receipt verify; otherwise transition through release/retirement policy and HOLD | No |
| Reservation event present | Row absent | `AUTHORITY_STORE_LOSS_OR_ROLLBACK` | preserve stores; recover verified AuthorityDB backup/WAL and reconcile; never recreate grant from journal alone | No |
| Reservation event present | `RESERVED_PENDING_JOURNAL` | `BIND_PENDING` | bind exact event, advance to `JOURNAL_COMMITTED`, then activate | No |
| Reservation event present | `JOURNAL_COMMITTED` | `ACTIVATION_PENDING` | activate only if current epoch/lock and exact receipt/event verify | No |
| Reservation event present; no acquisition event | `ACTIVE` | `ACTIVE_UNACKNOWLEDGED` | commit exact acquisition event from verified active receipt or release/HOLD; never act first | No |
| Acquisition event present | `ACTIVE` with exact binding | `ACTIVE_PROVEN` | normal operation | Yes, until release intent |
| Acquisition event present | absent/mismatched/non-active row | `AUTHORITY_INTEGRITY_HOLD` | preserve and reconcile; do not repair by inference | No |
| Release intent absent | `RELEASE_PENDING` or `RELEASED` | `DB_AHEAD_OF_JOURNAL` | integrity HOLD; no reactivation; reconcile receipts | No |
| Release intent present | `ACTIVE` | `RELEASE_DB_PENDING` | no action; perform exact release transitions | No |
| Release intent present | `RELEASE_PENDING` | `RELEASE_IN_PROGRESS` | complete release under same intent binding | No |
| Release intent present; no release-recorded event | `RELEASED` | `RELEASE_ACK_PENDING` | commit exact `SCOPE_LEASE_RELEASE_RECORDED` | No |
| Release-recorded event present | exact `RELEASED` row | `RELEASE_COMPLETE` | closeout may report clean release | No |
| Release-recorded event present | absent/mismatched row | `AUTHORITY_INTEGRITY_HOLD` | preserve and reconcile; no reuse | No |

Recovery may complete an idempotent cross-store transition only from the exact immutable receipt/event pair. It may never infer authority from timestamps, PID existence, ProgressDB, checkpoint, projections, or a worker claim.

## 7. At-most-once nonce/call protocol

The normative machine is `NONCE-AT-MOST-ONCE-STATE-MACHINE.json`. Frozen states are:

```text
RESERVED_PENDING_JOURNAL
COMMITTED_NOT_USED
CALL_START_COMMITTED
OUTCOME_RECORDED
RETIRED
UNKNOWN_CONSUMED
```

### 7.1 Reservation

- Reserve the unique `nonce_sha256` in AuthorityDB under `BEGIN IMMEDIATE` as `RESERVED_PENDING_JOURNAL`, binding transaction, origin/current epoch, authority ID, contract, exact canonical request digest, and authority-generation fencing token.
- Commit/sync `CALL_AUTHORITY_RESERVED` in the canonical journal, binding the pending receipt.
- Transition to `COMMITTED_NOT_USED`, binding that event, then commit/sync `CALL_AUTHORITY_RESERVATION_RECORDED` with the committed receipt.
- Duplicate nonce insertion or any request/authority mismatch fails closed.

### 7.2 Call-start barrier

Before any provider/protected-call bytes are sent or call-capable child is spawned:

1. commit/sync canonical `CALL_START_COMMITTED`, binding nonce, request digest, endpoint/operation identity, exact authority receipt, current epoch, and scope fence;
2. transition AuthorityDB to `CALL_START_COMMITTED`, binding the journal sequence/hash;
3. commit/sync `AUTHORITY_NONCE_CONSUMED`, binding the consumed receipt;
4. re-read and verify both stores and the process/scope fence;
5. invoke at most once.

No call starts after step 1 but before steps 2–4. The durable call-start event is the semantic execution barrier; AuthorityDB makes consumption durable across transactions.

### 7.3 Safe resume before call start

A crash in `RESERVED_PENDING_JOURNAL` or `COMMITTED_NOT_USED` does **not** automatically authorize a call. Resume to call start is allowed only if all are true:

- journal proves no `CALL_START_COMMITTED` and no attempt/outcome event for the nonce;
- AuthorityDB is exactly `COMMITTED_NOT_USED` with matching request/authority hashes;
- the frozen transaction contract says `safe_resume_before_call_start=true` for this exact operation;
- owner authority remains valid and unexpired;
- a new recovered supervisor epoch holds the transaction lock and any required active scope fence;
- canonical `SUPERVISOR_RECOVERED` and `CALL_SAFE_RESUME_AUTHORIZED` are committed;
- the nonce row is rebound to the recovered epoch through a new chained AuthorityDB receipt.

Otherwise retire without use, terminalise `HOLD`, and require new owner authority/new nonce.

### 7.4 Outcome and ambiguity

- A verified response/outcome becomes semantic evidence only when captured as required and committed/synced as `CALL_OUTCOME_RECORDED` in the canonical journal.
- AuthorityDB then transitions to `OUTCOME_RECORDED`, binding that event. Later semantic validation may HOLD, but consumption remains durable.
- If recovery finds `CALL_START_COMMITTED` without a canonical outcome, it transitions AuthorityDB to `UNKNOWN_CONSUMED` and commits/syncs `CALL_OUTCOME_UNKNOWN` binding that receipt.
- Crash after bytes may have been sent but before response, response received but not journaled, transport timeout after send, connection reset after send, or uncertain SQLite/call coordination all default to `UNKNOWN_CONSUMED`.
- `UNKNOWN_CONSUMED` is terminal for that nonce and **non-retryable**. Automatic retry, transport retry, replay, and reuse are forbidden. Any later attempt requires explicit new owner authority, a new nonce, and a new call-start barrier.
- An exception is permitted only when the frozen contract proves the exact external operation idempotent and supplies an externally enforced idempotency key plus a read-only reconciliation method. The default contract contains no such exception; merely using HTTP retries or a client idempotency claim is insufficient.

### 7.5 Retirement

- `OUTCOME_RECORDED -> RETIRED` occurs under `BEGIN IMMEDIATE`; `NONCE_RETIRED` is then committed/synced binding the retired receipt.
- `COMMITTED_NOT_USED -> RETIRED` is allowed only for explicit abandonment before call start and is journaled as no-call retirement.
- `RESERVED_PENDING_JOURNAL -> RETIRED` is allowed only to quarantine/abandon an orphan reservation; it never authorizes a call.
- `CALL_START_COMMITTED` cannot transition directly to `RETIRED`; it must become `OUTCOME_RECORDED` or `UNKNOWN_CONSUMED`.
- `UNKNOWN_CONSUMED` cannot transition to any reusable state and is treated as permanently consumed.

## 8. SQLite/WAL authority rules

The normative requirements are in `SQLITE-AUTHORITY-STORAGE-CONTRACT.json`. In summary:

- AuthorityDB and WitnessDB live on a proven local Linux filesystem, never `/mnt/c`;
- WAL is permitted only with `synchronous=FULL`, bounded busy timeout, asserted schema/application/user versions, parent-directory durability, and a frozen full backup/recovery procedure;
- every lease/nonce mutation uses `BEGIN IMMEDIATE`;
- `SQLITE_BUSY`, `SQLITE_FULL`, `SQLITE_IOERR*`, `SQLITE_CORRUPT`, `SQLITE_NOTADB`, and uncertain COMMIT are fail-closed;
- a live backup uses SQLite Online Backup API or an atomic paused snapshot including main DB, `-wal`, and `-shm`; copying only the main DB is forbidden;
- restore never automatically revives authority. It enters reconciliation HOLD, fences all scopes above proven high-water marks, and treats uncertain nonces as consumed.

## 9. Required event vocabulary

This contract adds/freezes these authority events without changing journal ownership:

```text
SCOPE_LEASE_RESERVATION_COMMITTED
SCOPE_LEASE_ACQUIRED
SCOPE_LEASE_RELEASE_INTENT
SCOPE_LEASE_RELEASE_RECORDED
CALL_AUTHORITY_RESERVED
CALL_AUTHORITY_RESERVATION_RECORDED
CALL_SAFE_RESUME_AUTHORIZED
CALL_START_COMMITTED
AUTHORITY_NONCE_CONSUMED
CALL_OUTCOME_RECORDED
CALL_OUTCOME_UNKNOWN
NONCE_RETIRED
AUTHORITY_RECOVERY_HOLD
```

Only the supervisor commits these events. AuthorityDB supplies fenced cross-transaction receipts; it does not commit journal events.

## 10. Hard invariants and acceptance

1. Supervisor epoch exists in the verified journal before any row binds it.
2. No protected action starts without exact journal barrier ACK plus exact active/consumed AuthorityDB receipt.
3. An orphan pending row is never active.
4. An active row without its bound acquisition event is never actionable.
5. Release intent immediately and permanently closes the protected-action gate for that token.
6. Fencing tokens strictly increase and stale tokens are rejected.
7. A nonce has one canonical request digest and at most one call start.
8. Call-start-without-journaled-outcome recovers to `UNKNOWN_CONSUMED`.
9. `UNKNOWN_CONSUMED` is never automatically retried or reused.
10. Nonce consumption survives later semantic HOLD/FAIL and database restart.
11. SQLite ambiguity never grants authority.
12. Journal remains the sole semantic authority; AuthorityDB remains cross-transaction authority only.

The exhaustive vectors in `AUTHORITY-CRASH-VECTORS.json` are mandatory M1 fixtures. Any unclassified cross-store combination or unrecognized state fails closed with `AUTHORITY_INTEGRITY_HOLD`.