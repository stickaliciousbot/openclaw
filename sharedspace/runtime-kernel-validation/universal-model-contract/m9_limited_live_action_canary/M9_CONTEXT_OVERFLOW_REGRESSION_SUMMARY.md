# M9 Context Overflow Regression Rehydration

Status: `PASS_M9_CONTEXT_OVERFLOW_REGRESSION_REHYDRATED`

- Canary execution: `PASS_M9_LIMITED_LIVE_ACTION_CANARY_LOCAL_ARTIFACT_WRITE`
- Target SHA: `1908d9158dc06e6c7127b86cde923361c3f86a13ba084c4f03746d4af49ff0cf`
- Duplicate write count: `0`
- Probes 1-5: PASS
- Probe 6: `FAIL_M9_POST_CANARY_OBSERVATION_REGRESSION` only on `context_overflow_count, context_overflow_diag_count`
- Send/provider/mutation/authority counters: clean
- M10 started: false
