# MB12 Duplicate-Safe Resume Plan

Classification: `PASS_MB12_RESUME_PLAN_READY`

## Scope

Plan only. This artifact defines a future duplicate-safe resume for the remaining MB12 cases after the rate/cooldown parser false-positive repair.

Forbidden actions remained blocked while writing this plan:

- MB12 resume execution: `NOT_RUN`
- MB13 start: `NOT_RUN`
- Live evaluation: `NOT_RUN`
- Gateway/model/provider calls: `NOT_RUN`
- Comparator: `BLOCKED_NOT_RUN`
- Promotion: `BLOCKED_NOT_RUN`
- M6 proposal: `BLOCKED_NOT_RUN`
- Route/config/Gateway mutation: `NOT_RUN`
- Memory promotion: `NOT_RUN`
- Provider/model change: `NOT_RUN`
- Production apply: `NOT_RUN`
- Cache enablement: `NOT_RUN`
- Commit/push: `NOT_RUN`

## Completed MB12 Case Verification

Completed case: `hn-20260707-0184`

Evidence path:

`sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/hard_negative_micro_batch_12_timeout_retry_20260708T1736AEST/`

Evidence files checked:

- `summary.json`
- `terminal_production_routing_journal.v2.jsonl`
- `raw_calls/0001_hn-20260707-0184_attempt-0001/parse_result.json`
- `duplicate_call_prevention_report.json`

Observed completion facts:

- MB12 classification: `HOLD_MICRO_BATCH_12_INCOMPLETE`
- Stop reason: `rate_or_cooldown_signal`
- Terminal case count: `1`
- All attempt count: `1`
- Completed terminal case: `hn-20260707-0184`
- Attempt: `hard-negative-micro-batch-12-timeout-retry-20260708T1736AEST:0001:hn-20260707-0184:attempt-0001`
- Return code: `0`
- Timed out: `false`
- Timeout error: `null`
- JSON parse: `true`
- Output present: `true`
- Provider: `token-broker-vmesh`
- Requested model: `token-broker-vmesh/auto`
- Provider boundary: `PASS_PROVIDER_VERIFIED`
- Provider mismatch count: `0`
- Command status: `PASS_COMMAND_OUTPUT_PARSE_READY`
- Stderr bytes: `0`
- Mutation performed: `false`
- Mutation sentinel: `PASS_MUTATION_SENTINEL_OUTSIDE_OUTPUT_UNCHANGED`
- Comparator/promotion/M6: `BLOCKED_NOT_RUN`

Note: preserved MB12 evidence records `rate_or_cooldown_signal: true` for `0184`; later diagnosis proved this was likely a parser false positive from bare `429` inside SHA/hash-like text, not a real provider rate limit.

## Remaining MB12 Case Range / Count

Original approved MB12 range: `hn-20260707-0184` → `hn-20260707-0188`.

Completed set:

- `hn-20260707-0184`

Resume candidate set:

- `hn-20260707-0185`
- `hn-20260707-0186`
- `hn-20260707-0187`
- `hn-20260707-0188`

Remaining range/count: `hn-20260707-0185` → `hn-20260707-0188`, exactly `4` cases.

## Duplicate-Call Prevention Proof

Static set proof:

```text
completed = {hn-20260707-0184}
resume_candidates = {hn-20260707-0185, hn-20260707-0186, hn-20260707-0187, hn-20260707-0188}
intersection = {}
```

Therefore the proposed resume candidate set does not duplicate the completed MB12 case.

Execution-time duplicate guard required before any provider call:

1. Build the selected case list from explicit literal IDs only: `0185`, `0186`, `0187`, `0188`.
2. Hard abort if `hn-20260707-0184` appears in the selected list.
3. Hard abort if `hn-20260707-0145` or `hn-20260707-0153` appears in the selected list.
4. Hard abort if selected count is not exactly `4`.
5. Hard abort if selected range is not exactly `hn-20260707-0185` → `hn-20260707-0188`.
6. Scan existing preserved production routing journals/raw attempt directories for any prior successful or attempted calls for `0185` → `0188`; hard abort if any are found unless explicitly approved as already-attempted HOLD evidence.
7. Use a fresh output directory and hard abort if it already exists and is non-empty.

## Repaired Harness Readback

Rate/cooldown parser repair: `PASS_PUSHED`

- Commit: `9453c1dd78bbe39cc9754aea88445e097f0afdda`
- Branch: `evidence/context-plus-rate-cooldown-parser-repair-20260708`
- Preserved repaired file: `scripts/context_plus_hard_negative_evaluator.py`
- Readiness evidence: `rate_cooldown_parser_repair_readiness_20260708/`
- Validation: `17 passed / 0 failed`
- Gateway/model/provider calls during validation: `0`

Required repaired-parser expectations for future resume:

- MB12 `hn-20260707-0184` saved output fixture must continue to classify as no rate/cooldown.
- SHA/hash text containing `429` must not trigger.
- Real HTTP/status `429` must trigger.
- `rate limit`, `ratelimit`, `too many requests`, `quota`, `cooldown`, and `retry after` text must trigger.
- Any future rate/cooldown HOLD must include detector reasons for audit.

## Proposed Resume Output Path

Proposed fresh output directory for a future approved execution:

`sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/hard_negative_micro_batch_12_remainder_after_parser_repair_20260708T1810AEST/`

Before any execution, preflight must verify this directory is absent or empty. If it exists and is non-empty, abort or choose a new owner-approved fresh directory.

## Mutation Sentinel Plan

Future resume execution must:

1. Capture pre-state before any provider calls.
2. Filter out only the approved fresh output directory.
3. Run only the approved four-case MB12 remainder.
4. Capture post-state after execution.
5. Classify as PASS only if filtered outside-output state is unchanged.
6. Classify as `FAIL_MICRO_BATCH_12_REMAINDER_UNSAFE` or equivalent if any route/config/Gateway/memory/provider/model/cache/production mutation is detected outside the approved output directory.

Required mutation boundary:

- Route/config/Gateway mutation: forbidden
- Memory promotion: forbidden
- Provider/model change: forbidden
- Production apply: forbidden
- Cache enablement: forbidden
- Comparator/promotion/M6: forbidden

## Provider Boundary Plan

Future resume execution must use:

- Expected provider: `token-broker-vmesh`
- Requested model: `token-broker-vmesh/auto`
- Gateway/model/provider calls allowed only for `hn-20260707-0185` → `hn-20260707-0188`
- No fallback/model override
- No cases outside the four-case remainder

Provider gates:

- `PASS_PROVIDER_CALL_BOUNDARY` required.
- Provider verified count must equal completed terminal count.
- Provider mismatch count must be `0`.
- Command failures must be `PASS_NO_COMMAND_FAILURES`, except approved retryable transport timeouts under the existing timeout-retry policy.
- `provider=null` must not be treated as provider mismatch unless raw stdout/stderr prove a successful response from the wrong provider; command/transport failures remain HOLD.

## Retry / Timeout / Rate-Cooldown Plan

Keep existing retry constraints:

- Max one retry per case.
- Retry allowed only for:
  - `GatewayTransportError: gateway timeout after 120000ms`
  - `TOKEN_SOLVER_V4_UPSTREAM_TIMEOUT`
  - `provider=null` only when raw stdout/stderr prove command/transport failure
- Preserve first attempt and retry attempt evidence.
- Use the existing 180-second cooldown before a retry when the timeout-retry policy applies.

Rate/cooldown after parser repair:

- Real rate/cooldown signals still stop the batch as HOLD.
- Hash-like text containing `429` must not stop the batch.
- If `rate_or_cooldown_signal` fires, closeout must include detector reasons and raw stdout/stderr evidence.

## Required Future Approval

Exact approval needed before any future MB12 resume execution:

```text
Approve MB12 remainder execution only:
- Cases: hn-20260707-0185 → hn-20260707-0188
- Batch size: 4
- Fresh output directory: hard_negative_micro_batch_12_remainder_after_parser_repair_20260708T1810AEST/
- Expected provider: token-broker-vmesh
- Requested model: token-broker-vmesh/auto
- Use parser repair commit 9453c1dd78bbe39cc9754aea88445e097f0afdda
- Do not run hn-20260707-0184
- Do not run held cases hn-20260707-0145 or hn-20260707-0153
- Do not start MB13
- Do not run comparator, promotion, or M6 proposal
- Preserve evidence after closeout before any further continuation
```

## Closeout Criteria for Future Execution

Potential future execution classifications:

- `PASS_MICRO_BATCH_12_REMAINDER_READY`: all four remaining cases complete, provider/mutation/rate gates pass, no duplicate calls.
- `HOLD_MICRO_BATCH_12_REMAINDER_RETRY_EXHAUSTED`: retryable timeout repeats after one retry.
- `HOLD_MICRO_BATCH_12_REMAINDER_INCOMPLETE`: partial/rate-limited/transport-held execution.
- `FAIL_MICRO_BATCH_12_REMAINDER_UNSAFE`: duplicate-call/provider/fallback/mutation boundary fails.
- `ABORT`: any hard abort fires before or during execution.

## MB13 / Comparator / Promotion Boundary

MB13 remains blocked.

This plan does not authorize:

- MB12 resume execution
- MB13
- Live evaluation
- Comparator
- Promotion
- M6 proposal

## Closeout

Final plan classification: `PASS_MB12_RESUME_PLAN_READY`.

Rationale: `hn-20260707-0184` completion is verified from preserved MB12 evidence; the proposed future resume set is exactly `hn-20260707-0185` → `hn-20260707-0188`; the completed set and resume set are disjoint; parser repair is pushed and locally validated; provider, mutation, duplicate, and rate/cooldown boundaries are concrete.

No provider calls, live evaluation, MB12 resume execution, MB13 start, comparator, promotion, or M6 proposal occurred while preparing this plan.
