# CAH-J1 M1 Offline Core — Construction Closeout

**Status:** `PASS_CONSTRUCTION_HOLD_FOR_INDEPENDENT_VERIFICATION`

Implemented at exact base `b48fbacb12f07de334a0195e13992ce7237db910` in the isolated detached worktree only.

## Delivered

- Canonical journal idempotency with explicit `event_id` / `proposal_sha256`, verified-journal-only reconstruction, stable replay ACKs, conflict HOLD, post-sync crash recovery, and disposable atomic-rebuild ProgressDB.
- Descriptor-bound CAS with registered root/source descriptors, safe `dir_fd` traversal plus `O_NOFOLLOW`, identity/nlink checks, one-fd hash+copy, durable same-filesystem no-overwrite publication, dedupe, reopen/rehash, referenced-object integrity checks, and journal-before-ACK binding.
- Distinct AuthorityDB with authority-grade SQLite setup/assertions, immutable hash-chained receipts/history, journal-proven supervisor epochs, monotonically fenced scope leases, N01–N11 nonce ordering, journal/DB dual gates, UNKNOWN_CONSUMED terminal handling, and no semantic outcome columns.
- Offline table-driven crash/integrity/concurrency coverage, including 2/5/20-process cases.

## Gates

- Changed-module `py_compile`: PASS
- New focused tests: 48/48 PASS
- Required/relevant predecessor tests: 201/201 PASS
- Total: 249/249 PASS
- `git diff --check`: PASS
- Bounded privacy/key/network scan: PASS, zero matches
- Zero-effects gate: PASS

Failed attempts and their source-level corrections are retained in `TEST-RESULTS.json`; validators were not weakened.

## Exact changed paths

1. `scripts/critical_apply_journal.py`
2. `scripts/critical_apply_progress.py`
3. `scripts/critical_apply_cas.py`
4. `scripts/critical_apply_authority_db.py`
5. `scripts/tests/test_critical_apply_journal_idempotency.py`
6. `scripts/tests/test_critical_apply_cas.py`
7. `scripts/tests/test_critical_apply_authority_db.py`

Source manifest hash: `610bd31940cb86b4eaa2199eea8aad007f0e5ff15495249578c6befb3fcc8e43`

No independent verification is claimed. The next gate is independent read-only verification against the frozen M0 contracts and this evidence set.
