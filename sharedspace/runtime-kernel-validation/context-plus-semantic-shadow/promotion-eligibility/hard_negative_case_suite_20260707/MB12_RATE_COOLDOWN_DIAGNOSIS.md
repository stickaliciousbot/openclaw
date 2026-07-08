# MB12 Rate/Cooldown Diagnosis

Classification: `HOLD_MB12_RESUME_PLAN_REQUIRED`

## Scope

Diagnosis only for preserved MB12 evidence.

Forbidden actions remained blocked during this diagnosis:

- MB12 resume: `NOT_RUN`
- MB13 start: `NOT_RUN`
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

## Preserved MB12 Evidence

- MB12 evidence commit: `ed11c1d1c2499b9f67e111ddd5034aadf2e8ea1e`
- MB12 evidence branch: `evidence/context-plus-hard-negative-micro-batch-12-20260708`
- MB12 output directory: `hard_negative_micro_batch_12_timeout_retry_20260708T1736AEST/`

## MB12 Summary Evidence

From `hard_negative_micro_batch_12_timeout_retry_20260708T1736AEST/summary.json`:

- Classification: `HOLD_MICRO_BATCH_12_INCOMPLETE`
- Stop reason: `rate_or_cooldown_signal`
- Approved case range: `hn-20260707-0184` → `hn-20260707-0188`
- Completed terminal case count: `1`
- All attempt count: `1`
- Completed case: `hn-20260707-0184`
- Remaining MB12 cases: `hn-20260707-0185` → `hn-20260707-0188`
- Provider report: `PASS_PROVIDER_CALL_BOUNDARY`
- Provider verified count: `1`
- Provider mismatch count: `0`
- Retry count: `0`
- Command failures: `PASS_NO_COMMAND_FAILURES`
- Mutation sentinel: `PASS_MUTATION_SENTINEL_OUTSIDE_OUTPUT_UNCHANGED`
- Comparator: `BLOCKED_NOT_RUN`
- Promotion: `BLOCKED_NOT_RUN`
- M6 proposal: `BLOCKED_NOT_RUN`
- Continue next batch: `false`

## Exact Rate/Cooldown Evidence

From `rate_limit_cooldown_report.json`:

- Classification: `HOLD_RATE_LIMIT_OR_COOLDOWN`
- `rate_limit_or_cooldown_event_count`: `1`
- Event case: `hn-20260707-0184`
- Attempt: `attempt-0001`
- `rate_or_cooldown_signal`: `true`
- Return code: `0`
- Timed out: `false`
- Command status: `PASS_COMMAND_OUTPUT_PARSE_READY`
- Provider: `token-broker-vmesh`
- Requested model: `token-broker-vmesh/auto`
- Provider boundary: `PASS_PROVIDER_VERIFIED`
- Stderr bytes: `0`
- Stdout bytes: `1326`

From `raw_calls/0001_hn-20260707-0184_attempt-0001/parse_result.json`:

- `stdout_json_parse_ok`: `true`
- stdout JSON keys: `attempts`, `capability`, `model`, `ok`, `outputs`, `provider`, `transport`
- `provider_raw_value`: `token-broker-vmesh`
- `provider_normalized`: `token-broker-vmesh`
- `provider_boundary_classification`: `PASS_PROVIDER_VERIFIED`
- `rate_or_cooldown_signal`: `true`
- `timed_out`: `false`
- `timeout_error`: `null`

From `raw_calls/0001_hn-20260707-0184_attempt-0001/child_stdout.raw`:

- Top-level JSON returned `ok: true`, `transport: gateway`, `provider: token-broker-vmesh`, `model: auto`.
- Output text asked for actual SHA fields and `visible_user_text`, then supplied an example Python SHA verifier.
- The output included this example hash string:

```text
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

## Diagnosis

The evidence does **not** prove an active hard provider rate limit, provider cooldown, transport timeout, quota exhaustion, or command failure.

The most likely source is a harness parser false positive:

- The MB12 wrapper computes `rate_or_cooldown_signal` by lowercasing combined stdout/stderr and checking whether any value in `H.RATE_NEEDLES` appears as a raw substring.
- `scripts/context_plus_hard_negative_evaluator.py` defines:

```python
RATE_NEEDLES = ["429", "rate limit", "ratelimit", "quota", "cooldown", "too many requests"]
```

- The raw output contains an example SHA-256 hash beginning `e3b0c44298...`.
- That hash contains the substring `429` across `...c44298...`.
- Because the detector treats bare `429` anywhere in successful model output as a rate/cooldown signal, the response was misclassified as rate/cooldown despite:
  - return code `0`,
  - JSON parse success,
  - provider verification,
  - zero stderr,
  - no timeout,
  - no command failure,
  - no explicit text such as `rate limit`, `quota`, `cooldown`, or `too many requests`.

Therefore MB12 stopped after 1/5 because of an over-broad parser classification, not proven provider throttling.

## Is a Timed Wait Sufficient?

No. A timed wait alone does not address the actual observed cause.

Since the source appears to be a parser false positive on the literal digits `429` inside a SHA example, waiting would not make the same detector safe. A later resume should first patch or override the rate/cooldown classifier so that:

- bare `429` is accepted only as a structured HTTP/status/error indicator, not as an arbitrary substring inside normal output;
- text needles such as `rate limit`, `ratelimit`, `quota`, `cooldown`, and `too many requests` remain detectable in stderr/stdout;
- the fixed classifier is validated against this exact `hn-20260707-0184` raw output as a regression fixture.

## Duplicate-Safe Resume Possibility

Duplicate-safe resume is possible later, but not automatically and not from the original five-case MB12 scope.

Safe later continuation would require a separate approved resume plan that:

1. Treats `hn-20260707-0184` as already attempted and preserved.
2. Selects exactly the remaining MB12 cases: `hn-20260707-0185` → `hn-20260707-0188`.
3. Uses a fresh output directory.
4. Verifies no prior attempts for `0185` → `0188` before any provider calls.
5. Re-verifies held exclusions for `hn-20260707-0145` and `hn-20260707-0153`.
6. Keeps MB13 blocked.
7. Keeps comparator, promotion, and M6 blocked.
8. Applies or embeds the corrected rate/cooldown classifier before live execution.
9. Requires separate owner approval before any Gateway/model/provider calls.

## Recommended Next Check / Wait

Recommended next action is **not** a timed cooldown wait. Recommended next check is a zero-provider-call harness diagnosis/patch plan:

- Patch candidate: replace bare substring `"429"` detection with a structured matcher such as HTTP status lines, JSON fields, stderr transport errors, or word-boundary/status-code contexts.
- Add fixture: run the classifier against MB12 `hn-20260707-0184` raw stdout/stderr and require `PASS_NO_RATE_LIMIT_OR_COOLDOWN` for that fixture.
- Then prepare a duplicate-safe MB12 remainder plan for `hn-20260707-0185` → `hn-20260707-0188`, subject to separate approval.

If Stick still wants a conservative operational pause before later live calls, a short manual wait/check window is acceptable, but the evidence here does not require a provider cooldown wait; it requires classifier repair.

## MB13 Boundary

MB13 remains blocked.

No evidence in this diagnosis authorizes MB13, comparator, promotion, or M6 proposal.

## Closeout

Final diagnosis classification: `HOLD_MB12_RESUME_PLAN_REQUIRED`.

Rationale: MB12 did not hit a proven active rate limit; it appears to have stopped due to a parser false positive on `429` inside an example SHA hash. Execution may be safely continued later only after a separate duplicate-safe remainder plan and classifier-fix validation, with separate approval before any provider calls.
