# First-56 Repaired-Schema Replay Closeout

Classification: `HOLD_FIRST_56_REPLAY_RETRY_EXHAUSTED`

## Summary

The narrow repaired-schema replay started correctly, passed the manifest/range preflight, and executed only the approved first-56 range until it held safely at `hn-20260707-0008`.

The run did not complete all 56 cases. It stopped after a command timeout on `hn-20260707-0008`:

- Command status: `HOLD_COMMAND_TIMEOUT_PROVIDER_UNVERIFIED`
- Provider null taxonomy: `PROVIDER_NULL_TIMEOUT`
- Return code: `null`
- stdout bytes: `0`
- stderr bytes: `0`

The approved one-retry policy could not be executed by the checked-in harness without modifying/wrapping the production run path, so the replay held safely rather than retrying.

## Boundary Readback

- Replay classification: `HOLD_FIRST_56_REPLAY_RETRY_EXHAUSTED`
- Cases executed: `hn-20260707-0001` → `hn-20260707-0008`
- Approved target cases: `hn-20260707-0001` → `hn-20260707-0056`
- Case count completed/attempted: `8/56`
- Gateway/model/provider calls: `8`
- Provider verified count: `7`
- Provider mismatch count: `0`
- Retries: `0`
- Raw stdout/stderr availability count: `8/8 attempted`
- Provider metadata availability count: `7/8 attempted`
- Provider missing/null case: `hn-20260707-0008`
- Duplicate prevention result: `PASS_DUPLICATE_CALL_PREVENTION_READY`
- Fallback/model boundary result: `PASS_NO_FALLBACK_OR_MODEL_OVERRIDE_FOR_COMPLETED_PROVIDER_VERIFIED_CASES`
- Rate/cooldown boundary result: `PASS_NO_RATE_LIMIT_OR_COOLDOWN`
- Mutation sentinel result: `PASS_MUTATION_PERFORMED_FALSE_IN_REPORTS`; standalone `mutation_sentinel_report.json` was not emitted before HOLD.
- Command failure result: `HOLD_COMMAND_FAILURE_OR_OUTPUT_CONTRACT_GAP`

## Comparator Authority

- Legacy first-56 comparator authority: `LEGACY_REMAINS_NON_COMPARATOR_AUTHORITY`
- Repaired replay comparator authority: `PARTIAL_HOLD_NOT_COMPARATOR_AUTHORITY`
- Legacy first-56 is not superseded because the repaired replay did not PASS all 56 cases.
- Aggregate comparator-readiness next step: `REQUIRED`, but it should report NOT_READY until first-56 replay/disposition is resolved.

## Explicit Non-Actions

- Comparator: `BLOCKED_NOT_RUN`
- Replay beyond `hn-20260707-0008`: `BLOCKED_NOT_RUN`
- Post-0056 execution: `BLOCKED_NOT_RUN`
- Post-0240 execution: `BLOCKED_NOT_RUN`
- Promotion: `BLOCKED`
- M6 proposal: `BLOCKED`
- Route/config/Gateway mutation: `BLOCKED_NOT_RUN`
- Memory promotion: `BLOCKED_NOT_RUN`
- Provider/model change: `BLOCKED_NOT_RUN`
- Production apply: `BLOCKED_NOT_RUN`
- Cache enablement: `BLOCKED_NOT_RUN`
