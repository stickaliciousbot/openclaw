# AuthorityDB Fencing Protocol — CAH-J1-M0

**Schema:** `critical_apply.authoritydb_fencing_protocol.v1`  
**Status:** frozen offline contract  
**Semantic authority:** the canonical journal alone  
**AuthorityDB authority:** cross-transaction scope exclusion and durable nonce/call consumption only

## 1. Non-negotiable authority boundary

AuthorityDB never records or derives transaction PASS, HOLD, FAIL, or ABORT. A row may permit or deny a protected action, but it cannot establish that the action happened or alter the semantic result. Canonical transaction facts exist only after supervisor commit to the canonical journal and deterministic reduction.

A protected action is permitted only while all of these independently hold:

1. the transaction lock is held by the full current supervisor identity;
2. AuthorityDB has an eligible row for the exact scope/nonce, transaction, epoch, and fencing token;
3. the row is bound to the exact, verified canonical journal event required by this protocol;
4. the event commit was durably acknowledged;
5. no release intent, terminal input fence, expiry, integrity fault, or supervisor-generation mismatch forbids the action.

Absence or disagreement fails closed. Neither store repairs the other by assumption.

## 2. Identity and fencing

The supervisor creates and durably records a new `supervisor_epoch` **before** any AuthorityDB row can bind that epoch. Every authority mutation binds:

- `transaction_id`;
- `supervisor_epoch`;
- exact `scope_hash` or `nonce_sha256`;
- monotonically increasing integer `fencing_token` allocated under `BEGIN IMMEDIATE`;
- `boot_id`, PID, start ticks, and supervisor process-identity SHA-256;
- state;
- `journal_sequence` and `journal_event_sha256` (nullable only for a pending journal bind);
- `authority_receipt_sha256` over the canonicalized row receipt;
- row generation and UTC audit timestamp.

For a scope, every successful acquisition increments the durable fencing counter. Components reject a lower token even if an old process remains alive. Tokens are never reused or decremented.

## 3. Scope-lease state machine

Frozen states:

```text
ABSENT
  -> RESERVED_PENDING_JOURNAL
  -> JOURNAL_COMMITTED
  -> ACTIVE
  -> RELEASE_PENDING
  -> RELEASED
```

`RESERVED_PENDING_JOURNAL` has null journal bindings and authorizes nothing. `JOURNAL_COMMITTED` means the exact `SCOPE_LEASE_ACQUIRED` event is verified but activation is not complete; it authorizes nothing. `ACTIVE` requires the row and event bindings to agree and is the only scope state that may contribute to a protected-action gate. `RELEASE_PENDING` is entered only after a durably acknowledged `SCOPE_LEASE_RELEASE_INTENT`; it immediately and permanently forbids new protected actions. `RELEASED` is terminal for that acquisition generation.

No reverse transition is valid. Reacquisition creates a new generation and a greater fencing token.

## 4. Acquisition transaction

1. Verify contract, transaction root, filesystem, and transaction lock.
2. Create/recover and commit the supervisor epoch.
3. Under `BEGIN IMMEDIATE`, allocate the next scope fencing token and insert `RESERVED_PENDING_JOURNAL`; commit with SQLite FULL durability.
4. Commit and `fdatasync` canonical `SCOPE_LEASE_ACQUIRED`, binding the pending receipt hash, scope, epoch, and token; receive durable ACK.
5. Under `BEGIN IMMEDIATE`, verify both stores, bind the row to the exact event, transition through `JOURNAL_COMMITTED` to `ACTIVE`, and commit.
6. Read back the row and journal event. Only then may the scope side of a protected-action gate be true.

A crash at any step is recovered from the matrix below; no orphan pending row silently activates.

## 5. Release transaction and close ordering

1. After semantic seal, bounded notification terminal outcome, and independent terminal witness attempt, commit and ACK `SCOPE_LEASE_RELEASE_INTENT`.
2. The acknowledged intent is an irreversible execution fence: no new protected action is legal.
3. Under `BEGIN IMMEDIATE`, transition `ACTIVE` to `RELEASE_PENDING`, then record the release and transition to `RELEASED`; commit and read back.
4. Commit and ACK `SCOPE_LEASE_RELEASE_RECORDED` with the exact release receipt.
5. Prepare deterministic completion-receipt fields other than the not-yet-known closeout head.
6. Commit and ACK `SUPERVISOR_CLOSED`; this event is the `closeout_head` and is the final canonical event.
7. Materialize and durably publish `COMPLETION-RECEIPT.json` binding that closeout head, seal, notification outcome, lease-release outcome, and effects.
8. Release the transaction lock only after receipt readback. No journal append is permitted after `SUPERVISOR_CLOSED`.

If AuthorityDB release cannot be durably proven, do not commit clean `SUPERVISOR_CLOSED`; classify closeout HOLD and retain/recover under the frozen authority policy. A sealed semantic result remains unchanged.

## 6. Deterministic cross-store recovery matrix

| AuthorityDB observation | Canonical journal observation | Recovery/classification |
|---|---|---|
| no row | no acquisition event | clean absent; a new acquire may begin |
| `RESERVED_PENDING_JOURNAL` | no acquisition event | orphan pending; authorizes nothing; retire/release under recovery transaction, then reacquire with a new token |
| no row | valid acquisition event | integrity HOLD; reconstructing authority by journal alone is forbidden |
| pending row | matching acquisition event | bind event, enter `JOURNAL_COMMITTED`, then `ACTIVE` only after full verification and frozen safe-resume policy |
| pending row | conflicting acquisition event | integrity HOLD |
| `JOURNAL_COMMITTED` | matching acquisition event | finish activation after identity/token verification |
| `ACTIVE` | matching acquisition event | active only for matching live epoch and before release intent |
| `ACTIVE` | missing/conflicting acquisition event | integrity HOLD; authorizes nothing |
| `ACTIVE` | matching release intent | force `RELEASE_PENDING`; protected actions forbidden |
| `RELEASE_PENDING` | matching release intent, no release-recorded event | complete DB release, then commit release-recorded event |
| `RELEASED` | matching release intent, no release-recorded event | idempotently commit release-recorded event with existing receipt |
| `RELEASED` | matching release-recorded event | release complete |
| non-released row | release-recorded event | integrity HOLD; never infer DB release from journal alone |
| any row | wrong epoch/token/transaction | integrity HOLD; no action |

Recovery always acquires the transaction lock, verifies the canonical journal prefix and WitnessDB consistency, creates a new epoch where required, and records a canonical recovery event. An old token cannot regain authority.

## 7. Nonce integration

Nonce records use the separate frozen state machine in `NONCE-AT-MOST-ONCE-STATE-MACHINE.json`. Nonce-ledger schema creation, migration, fencing-counter allocation, and row mutation have one owner: `AuthorityService`. The canonical journal remains the sole record of transaction facts; AuthorityDB remains the durable at-most-once execution gate.

## 8. Invariants

- No AuthorityDB record exists before its bound supervisor epoch.
- Pending rows authorize no side effect.
- An `ACTIVE` scope without its exact journal binding authorizes no side effect.
- An acknowledged release intent permanently prevents further protected actions for that acquisition.
- A stale epoch or lower fencing token never authorizes action.
- AuthorityDB semantic-result columns are forbidden by schema.
- Recovery never converts uncertainty into PASS or implicit authority.
- All mismatch classes are fail-closed and fixture-covered.
