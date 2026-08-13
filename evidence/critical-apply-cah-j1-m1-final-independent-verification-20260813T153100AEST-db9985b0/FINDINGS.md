# FINDINGS

## Blockers

None.

## Non-blocking observations

- `OBS-R1-01` — **HARNESS_TIMEOUT**: journal 2/5/20 contention uses a fixed 20-second queue timeout. It timed out under verifier filesystem load, including resumed attempts. The exact unchanged test passed in the prior verifier's isolated retry (56.805s total); independent same-ID/distinct-ID adversarial contention passed; the clean predecessor concurrency aggregate passed; final scoped process scan is empty. This is not a candidate contract failure.
- `OBS-R1-02` — **HARNESS_WARNING**: verifier CAS append-mutation helper emitted one unclosed-handle `ResourceWarning` after the required HOLD. Assertions, candidate state, cleanup, and leak closeout were unaffected.
- `OBS-R1-03` — **BASELINE_STATE**: repository already had an index lock and broad dirty baseline. The verifier did not remove or mutate the lock. Immutable HEAD/tree, empty index diff, tracked-status hash, patch hash, seven source hashes, and evidence manifests are the controlling sentinels.
- `OBS-R1-04` — **NON-ACCEPTANCE INVOCATION**: an initial resumed predecessor invocation overlapped a still-running approval-triggered command and emitted transient process-leak errors before termination. It had no terminal result and was not used. The exact aggregate rerun alone passed 142/142.

No candidate remediation is required for M1 offline core.
