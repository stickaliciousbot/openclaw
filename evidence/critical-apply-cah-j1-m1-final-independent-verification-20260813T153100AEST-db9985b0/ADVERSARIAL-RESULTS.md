# INDEPENDENT ADVERSARIAL RESULTS

`adversarial_verifier_tests.py` is independent verifier-authored code run only against the disposable candidate. Result: **19/19 PASS**.

Covered: ProgressDB same-count/head full-row tamper and transaction-ID mismatch; concurrent distinct event IDs and conflicting same-ID proposals; CAS shard symlink/non-directory, orphan/publish crash recovery, corrupt destination no-overwrite, append/truncate/metadata mutation; AuthorityDB identity/application/version/schema/pragmas, receipt tamper, busy failure, cross-epoch/stale fence, crash classifications, N04 journal-first refusal, N07 invalid-CAS-reference refusal, UNKNOWN_CONSUMED persistence after reopen, and 2/5/20 contention.

One harmless Python `ResourceWarning` identified an unclosed verifier-side mutation helper handle after an expected CAS hold. It did not touch candidate source or affect assertions/process state; classified verifier-test hygiene only, non-blocking.
