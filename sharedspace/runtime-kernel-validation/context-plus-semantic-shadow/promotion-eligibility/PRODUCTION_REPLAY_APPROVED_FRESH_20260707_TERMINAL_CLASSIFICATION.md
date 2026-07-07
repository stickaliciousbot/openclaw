# Context+ Fresh Same-Suite Production Replay — Terminal Classification

Date: 2026-07-07 AEST
Run ID: `production_replay_approved_fresh_20260707`

## Classification

```text
FAIL_REPLAY_UNSAFE
```

The replay completed all 440 requested cases, but the run is **not comparator-ready** and **not promotion-eligible** because the replay's mutation/workspace sentinel detected workspace changes outside the approved output directory while the replay was running.

## Evidence

Replay output directory:

```text
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/production_replay_approved_fresh_20260707/
```

Terminal process result:

```text
session=briny-cedar
exit_code=2
completed_cases=440
expected_cases=440
gateway_model_provider_calls=440
classification=FAIL_REPLAY_UNSAFE
hard_abort.reason=workspace_status_changed_outside_output_dir
```

Replay summary:

```text
replay_summary.json: FAIL_REPLAY_UNSAFE
mutation_sentinel_report.json: FAIL_MUTATION_SENTINEL
provider_model_call_count_report.json: PASS_PROVIDER_CALL_BOUNDARY
rate_limit_cooldown_report.json: PASS_NO_RATE_LIMIT_OR_COOLDOWN
same_suite_comparator_ready_status.json: HOLD_SAME_SUITE_COMPARATOR_NOT_READY
```

Provider/call boundary did pass:

```text
actual_calls=440
expected_calls=440
expected_provider=token-broker-vmesh
requested_model=token-broker-vmesh/auto
fallback_attempt_count=0
provider_mismatch_count=0
```

Last journal record was `m7-live-0440`; journal records show provider `token-broker-vmesh`, requested model `token-broker-vmesh/auto`, fallback false, mutation_detected 0, output present true on per-case records.

## Decision

Do **not** run the same-suite comparator from this replay output.

Do **not** promote.

Do **not** prepare an M6 proposal from this run.

This replay may be retained as preserved failed/unsafe evidence. A valid comparator-ready replay would require a fresh approved run with a clean workspace sentinel boundary and no outside-output workspace changes during execution.

## Safety boundary readback

- No promotion performed.
- No comparator run performed.
- No M6 proposal prepared.
- No route/config/Gateway/model/provider/fallback/cache/memory-route mutation performed by the replay classification.
