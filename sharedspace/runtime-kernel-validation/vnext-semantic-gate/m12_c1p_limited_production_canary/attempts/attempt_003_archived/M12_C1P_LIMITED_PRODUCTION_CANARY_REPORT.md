# M12-C1P Limited Production Canary

Final status: `M12_C1P_LIMITED_PRODUCTION_CANARY_ABORT`

## Scope

M12-C1 only: bounded artifact status Q&A. Stop bound was 25 production C1 requests or 2 active hours, whichever came first.

## Result

- Production C1 requests: `1/25`
- ANSWER requests: `1`
- fail-closed HOLD requests: `0`
- Material regressions: `1`
- Missing-output regressions: `0`
- Direct provider bypass: `0`
- Provider/model calls: `0`
- Mutation detected: `0`
- Failed gates: `['first_request_failure:m12_c1p_prod_001', 'production_c1_request_count_25', 'all_requests_pass', 'answer_hold_distribution_expected', 'material_regressions_zero', 'required_files_present']`
- Stop reason: `abort_gate_or_interruption`

## Boundary

- M12-C1 limited production canary executed: `true`
- C2/C3/C4 started: `false`
- Cache enabled: `false`
- Artifact-memory promotion: `false`
- Global Semantic Gate promotion: `false`
- Gateway/config/live-route/fallback/memory-route/runtime authority mutation: `false`
- C1K consumed read-only only: `true`
- C1K frozen SHA unchanged: `097c0819182001fcf0c0497c7c072be12a8c51f948d2d8f52a39c2ceaf7f28dd`

## Artifacts

- `status.json`
- `summary.json`
- `production_request_journal.jsonl`
- `production_request_journal.sqlite3`
- `deterministic_kernel_result_log.json`
- `provider_path_report.json`
- `mutation_sentinel_report.json`
- `rollback_readiness.json`
