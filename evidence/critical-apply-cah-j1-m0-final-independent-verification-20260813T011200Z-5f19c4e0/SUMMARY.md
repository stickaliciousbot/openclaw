# CAH-J1-M0 Final Independent Verification

**Status:** `HOLD`

**Terminal:** `HOLD_CAH_J1_M0_FOR_POST_FREEZE_VOCABULARY_CLOSEOUT_HEAD_PUBLICATION_AND_EXHAUSTIVE_CRASH_MATRIX_CORRECTIONS_NO_PRODUCTION_EFFECT`

Identity and mechanical checks passed:

- expected candidate manifest SHA-256 exact;
- expected privacy receipt SHA-256 exact;
- governing owner revision and adjudication hashes exact;
- all 24 manifest-listed artifacts match SHA-256 and byte size;
- all 22 JSON files parse;
- candidate validator returned PASS, exit 0;
- privacy receipt reports zero blocking findings;
- no candidate or production mutation occurred.

Substantive architecture review found three blocking defects:

1. The terminal fence's post-freeze allowlist includes owned-child reconciliation and cleanup even though lifecycle and PASS readiness require both before the fence, while the same contract rejects post-fence semantic evidence.
2. `COMPLETION-RECEIPT.json` is required to bind `closeout_head = SUPERVISOR_CLOSED`, but lifecycle prepares the receipt before that event and freezes no future-hash/publication/recovery protocol across the boundary.
3. Mandatory crash matrices are not exhaustive for several frozen nonce transitions and CAS publication boundaries.

No second semantic authority was found. The journal remains sole semantic/transaction-fact authority; AuthorityDB, WitnessDB, and ProgressDB remain correctly partitioned. Core UNKNOWN_CONSUMED/no-retry, journal-derived idempotency, descriptor-bound CAS, SQLite/WAL, detect-only same-UID witness, immutable semantic-path registration, single nonce-ledger creator, and stale-projection subordination contracts are otherwise present.

See `FINDINGS.json` for exact evidence and required corrections.
