# CAH-J1-M0 Integrated Contract Freeze

Status candidate: `PASS_CAH_J1_M0_SUPERVISOR_EVENT_JOURNAL_ARCHITECTURE_AUTHORITY_STORAGE_SECURITY_AND_CRASH_CONSISTENCY_CONTRACTS_FROZEN_NO_PRODUCTION_EFFECT`

This package freezes the architecture contracts required by the owner revision and M0 adjudication. It does not implement, install, activate, or exercise a production supervisor.

Resolved contracts:

- B1 AuthorityDB ↔ journal fencing and crash recovery.
- B2 at-most-once nonce/call protocol including `UNKNOWN_CONSUMED` and no automatic retry.
- B3 mandatory canonical `TERMINAL_REDUCTION_PREPARED` fence.
- B4 distinct `semantic_reduction_head`, `terminal_decision_head`, and `closeout_head`.
- B5 journal-derived event idempotency independent of ProgressDB.
- B6 descriptor-bound, crash-durable CAS publication.
- S1 lease release / close ordering.
- S2 Witness Grade 1 same-host, same-UID independent-process detection.
- S3 bounded notification closeout and immutable late-receipt behavior.
- S4 authority-grade SQLite/WAL durability, backup, and recovery.

Additional frozen repairs:

- immutable semantic-path registration shared by supervisor, reducer, checker, watcher, and projection writer;
- canonical semantic terminal outranks mutable `RUNNING`, `STALE`, PID, registry, and notification projections;
- `nonce-ledger/` has exactly one directory creator (`supervisor_materializer`); the runner requires the registered existing directory and never creates it;
- v1 same-UID security claim is detect-only, not hostile tamper prevention;
- canonical append-only journal remains the sole semantic and transaction-fact authority.

Construction gates: integrated validator PASS (16/16 required files), bounded privacy scan PASS, zero provider/Terra/runtime/Gateway/config/Git/install/deploy/production effects. Independent verification remains required before M0 is considered closed.
