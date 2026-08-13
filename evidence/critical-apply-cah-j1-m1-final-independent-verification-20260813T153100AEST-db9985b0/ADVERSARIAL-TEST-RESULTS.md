# Independent Adversarial Test Results

- Disposition: **PASS**
- Tests: **19/19**
- Duration: **535.441 seconds**
- Execution provenance: completed in the prior independent verifier session before compaction; exact preserved candidate and test source remain bound by hash. Per resume instruction this successful suite was not rerun.
- Result reconstruction: `adversarial-verifier-preserved.log` records the transcript terminal and the 19 exact test names from the preserved verifier source.
- Coverage: ProgressDB full-row tamper and transaction mismatch rebuild; journal distinct/same-ID concurrency; CAS shard substitution, orphan recovery, corrupt-destination refusal, append/truncate/metadata mutation; AuthorityDB identity/pragmas, receipt tamper, busy fail-closed, epoch/fence refusal, crash classification, N04, N07 verified CAS reference, UNKNOWN_CONSUMED persistence, and 2/5/20 exactly-one-winner contention.
- N07 critical outcome: `test_N07_refuses_journal_record_without_valid_CAS_reference` passed. Direct review independently confirms `record_outcome()` requires `_verify_cas_outcome_event()`, while the supplied `ValidatedJournal` is only `ok` after `validate_payload_reference()` resolves the regular payload and verifies byte count plus SHA-256. A standalone `response_sha256` field is insufficient.
- Warning: the append mutator emitted a `ResourceWarning` for its deliberately short-lived unclosed file object. This is preserved as `HARNESS_WARNING`, not hidden. Fixture cleanup and resumed post-run leak checks determine effect status.
