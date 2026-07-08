# MB14 Rate/Cooldown Parser Repair Implementation

## Classification

`PASS_PARSER_REPAIR_IMPLEMENTED_VALIDATED`

## Scope

Implemented and locally validated the source-aware rate/cooldown parser repair only.

No MB14 resume, MB15 start, Gateway/model/provider calls, comparator, promotion, M6 proposal, route/config/Gateway mutation, memory promotion, provider/model change, production apply, cache enablement, commit, or push occurred.

## Files Changed

- `scripts/context_plus_hard_negative_evaluator.py`
- `sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/rate_cooldown_parser_repair_mb14_validation_20260708/fixture_selftest/rate_cooldown_fixture_selftest_summary.json`
- `sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/rate_cooldown_parser_repair_mb14_validation_20260708/validation_summary.json`
- `sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/MB14_RATE_COOLDOWN_PARSER_REPAIR_IMPLEMENTATION.md`

## Parser Behavior Before

`rate_or_cooldown_signal(...)` scanned combined stdout/stderr text directly. When stdout was a valid JSON payload, generated model answer text inside `outputs[].text` was still present in the raw stdout string. Therefore a generated answer phrase such as:

```text
safe_next=retry after tool path check.
```

triggered `retry_after_phrase` and caused `HOLD_RATE_LIMIT_OR_COOLDOWN`, even though provider/system metadata was clean.

## Parser Behavior After

The parser is now source-aware:

- `stderr` is scanned as provider/system/transport text.
- if stdout parses as a structured JSON payload, only provider/system surfaces are scanned:
  - top-level status fields: `status`, `status_code`, `code`, `http_status`
  - top-level provider/system text fields: `message`, `error`, `detail`, `reason`
  - provider attempt metadata under `attempts[]`
- generated model content keys are skipped while scanning attempt metadata:
  - `output`, `outputs`, `text`, `content`, `message_text`, `mediaUrl`
- generated answer text under `outputs[].text` does not trigger cooldown by itself.
- if stdout is not structured JSON, raw stdout remains conservatively scanned as transport/error text.

Real provider/system cooldown signals still trigger, including HTTP/status `429`, retry-after/header-like text, quota, rate-limit, cooldown, too-many-requests, top-level payload metadata, and attempt metadata.

## Fixtures / Tests Added or Updated

Updated `rate-cooldown-fixture-selftest` with fixtures for:

- generated `outputs[].text` containing `safe_next=retry after tool path check.` must **not** trigger cooldown.
- top-level payload message containing `retry after` must trigger cooldown.
- attempt metadata with `status_code: 429` and `error: too many requests` must trigger cooldown.

Existing fixtures retained:

- SHA/hash containing `429` does not trigger.
- hash-like token containing `429` does not trigger.
- embedded numeric `1429` does not trigger.
- `HTTP 429 Too Many Requests` triggers.
- structured `status_code: 429` triggers.
- provider rate-limit text triggers.
- too-many-requests text triggers.
- quota text triggers.
- cooldown text triggers.
- header-style `Retry-After` triggers.
- saved MB12 `hn-20260707-0184` output remains no-rate/cooldown.

## Validation Commands Run

```sh
python3 -m py_compile scripts/context_plus_hard_negative_evaluator.py
python3 scripts/context_plus_hard_negative_evaluator.py rate-cooldown-fixture-selftest \
  --out-dir sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/rate_cooldown_parser_repair_mb14_validation_20260708/fixture_selftest \
  --fixture-source sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/hard_negative_micro_batch_12_timeout_retry_20260708T1736AEST/raw_calls/0001_hn-20260707-0184_attempt-0001
```

Additional validation summary was written to:

`sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/rate_cooldown_parser_repair_mb14_validation_20260708/validation_summary.json`

## Validation Results

- Fixture self-test classification: `PASS_RATE_COOLDOWN_FIXTURES_VALIDATED`
- Parser repair validation classification: `PASS_PARSER_REPAIR_VALIDATION`
- Passed fixtures: `14`
- Failed fixtures: `0`
- Missing required checks: `[]`
- Failed required checks: `[]`
- Provider calls: `0`
- Gateway/model calls: `0`
- Mutation performed: `false`

Required checks passed:

- `generated_outputs_retry_after_no_trigger`
- `payload_retry_after_message_trigger`
- `attempt_metadata_cooldown_trigger`
- `http_429_trigger`
- `json_status_429_trigger`
- `rate_limit_text_trigger`
- `quota_exceeded_text_trigger`
- `cooldown_text_trigger`
- `retry_after_header_trigger`
- `mb12_hn0184_saved_output_no_rate_cooldown`

## Safety / Boundary State

- Provider calls: `0`
- Gateway/model calls: `0`
- MB14 resume: `BLOCKED_PENDING_REPAIR_PRESERVATION`
- MB15: `BLOCKED`
- Comparator: `BLOCKED`
- Promotion: `BLOCKED`
- M6 proposal: `BLOCKED`
- Route/config/Gateway mutation: unchanged / not run
- Memory promotion: unchanged / not run
- Provider/model change: unchanged / not run
- Production apply: unchanged / not run
- Cache enablement: unchanged / not run

## Next Step

Stop here and request read-only scoped preservation review for the implementation evidence only. Do not resume MB14 or start MB15 until repair evidence is preserved and a duplicate-safe MB14 resume plan is separately approved.
