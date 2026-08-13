# DIRECT SOURCE FINDINGS

Direct review of the exact four implementation modules and three focused tests against all frozen M0-R3 contracts found no blocker and no constant-only proof without a source gate.

- Journal/idempotency: verified journal committed bytes are sole authority for original ACK/idempotency; same-ID conflict raises HOLD; append/head operate under lock with file and parent durability; ProgressDB is disposable and full row/content parity is validated, including transaction identity.
- CAS: source is retained descriptor-bound; source identity/type/nlink/symlink and mutation checks are enforced; publication is no-overwrite/dedupe with directory durability, reopen/rehash, and journal sync before ACK; orphan publication is recoverable, while referenced missing/corrupt bytes are fatal; ownership modes are restrictive.
- AuthorityDB: filesystem and SQLite identity, application_id, user_version, schema hash, pragmas, WAL durability, and receipt chains are verified; epochs are journal-proven; fencing is monotonic; lease/release states are exact and journal-gated; semantic outcomes are absent from DB authority.
- N01-N11: source gates implement exact sequencing. N04 safe resume refuses without journal-first recovered-epoch authorization. N07 requires response bytes in CAS plus a verified journal event referring to the CAS object before DB outcome. UNKNOWN_CONSUMED is terminal/non-retryable, including after reopen.
- Busy/contention paths fail closed and serialize correctly at 2/5/20 workers.
