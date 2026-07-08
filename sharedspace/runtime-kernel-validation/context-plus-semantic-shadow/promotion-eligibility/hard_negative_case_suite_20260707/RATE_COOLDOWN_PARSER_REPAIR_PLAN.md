# Rate/Cooldown Parser Repair Plan

Classification: `PASS_REPAIR_PLAN_READY`

## Scope

Plan only. This artifact designs the minimal safe parser repair needed after MB12 stopped on a likely false positive rate/cooldown signal.

Forbidden actions remained blocked while writing this plan:

- Code changes: `NOT_RUN`
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

## Current Parser Behavior

Current shared evaluator logic in `scripts/context_plus_hard_negative_evaluator.py` defines:

```python
RATE_NEEDLES = ["429", "rate limit", "ratelimit", "quota", "cooldown", "too many requests"]
```

The production-routing attempt parser then builds a lowercased combined stdout/stderr string and performs raw substring matching:

```python
combined = (stdout_text + "\n" + stderr_text).lower()
rate = any(n in combined for n in RATE_NEEDLES)
```

The MB12 wrapper copied the same behavior:

```python
rate = any(n in combined for n in H.RATE_NEEDLES)
```

The wrapper then stops the micro-batch immediately when the flag is true:

```python
if rec1.get('rate_or_cooldown_signal'):
    terminal.append(rec1)
    append_jsonl(terminal_journal, rec1)
    close_class = 'HOLD_MICRO_BATCH_12_INCOMPLETE'
    stop_reason = 'rate_or_cooldown_signal'
    break
```

## False-Positive Example

MB12 case `hn-20260707-0184` completed successfully:

- Provider: `token-broker-vmesh`
- Requested model: `token-broker-vmesh/auto`
- Return code: `0`
- JSON parse: OK
- Stderr: empty
- Timeout: none
- Command failure: none
- Provider boundary: `PASS_PROVIDER_VERIFIED`

The response included an example SHA-256 hash:

```text
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

That string contains the digit sequence `429` inside hash-like text (`...c44298...`). Because the parser treats bare `"429"` anywhere in model output as a rate/cooldown signal, MB12 stopped after `1/5` cases despite no real rate-limit evidence.

## Proposed Parser Rule

Replace raw substring matching with a small structured detector function, for example:

```python
def rate_or_cooldown_signal(stdout_text: str, stderr_text: str, payload: object | None = None) -> tuple[bool, list[str]]:
    combined = f"{stdout_text}\n{stderr_text}"
    lower = combined.lower()
    reasons = []

    # Strong textual signals. Keep substring or regex matching for actual words/phrases.
    text_patterns = [
        ("rate_limit_phrase", r"\brate[- ]?limit(?:ed|ing)?\b"),
        ("ratelimit_phrase", r"\bratelimit(?:ed|ing)?\b"),
        ("too_many_requests_phrase", r"\btoo many requests\b"),
        ("quota_phrase", r"\bquota\b.*\b(exceeded|exhausted|limit|reached)\b|\b(exceeded|exhausted|reached)\b.*\bquota\b"),
        ("cooldown_phrase", r"\bcool[- ]?down\b|\btry again in\b|\bretry after\b"),
    ]

    # Structured 429 only, never arbitrary substring inside alphanumeric/hash text.
    status_429_patterns = [
        ("http_status_429", r"\bhttp(?:/\d(?:\.\d)?)?\s+429\b"),
        ("status_code_429", r"\bstatus(?:_code| code)?\s*[:=]\s*429\b"),
        ("error_code_429", r"\b(?:error|code|status)\s*[:=]\s*429\b"),
        ("json_status_429", r"[\"'](?:status|status_code|code|http_status)[\"']\s*:\s*429\b"),
        ("standalone_429_with_context", r"\b429\b[^\n]{0,80}\b(too many requests|rate[- ]?limit|quota|cool[- ]?down)\b"),
    ]
```

Implementation details:

1. Remove bare `"429"` from `RATE_NEEDLES`, or stop using `RATE_NEEDLES` for numeric status detection.
2. Add `rate_or_cooldown_signal(...)` returning both boolean and reason list.
3. Treat `429` as rate/cooldown only when it is a standalone status/code token with nearby rate-limit semantics or a structured status field.
4. Continue detecting strong text signals: `rate limit`, `ratelimit`, `too many requests`, `quota exceeded`, `cooldown`, `retry after`, and similar.
5. Store reasons in parse/evidence output, e.g. `rate_or_cooldown_reasons`, so future HOLDs can be audited precisely.
6. Keep the conservative stop behavior: if the corrected detector returns true, micro-batches still stop rather than continuing through a real rate boundary.

## Retry / Rate-Limit Classification Implications

The repair does not loosen retry policy. It only improves signal precision.

- Real rate-limit/cooldown signals remain `HOLD_RATE_LIMIT_OR_COOLDOWN` and should stop the batch.
- Bare hash-like text containing `429` becomes `PASS_NO_RATE_LIMIT_OR_COOLDOWN` if no other real signal exists.
- Retryable transport failures remain governed by the existing retry policy:
  - `GatewayTransportError: gateway timeout after 120000ms`
  - `TOKEN_SOLVER_V4_UPSTREAM_TIMEOUT`
  - `provider=null` only when raw stdout/stderr prove command/transport failure
- A real rate-limit/cooldown signal should not be retried as a transport retry; it should remain a HOLD until a separate wait/check plan or operator approval.
- The batch closeout should include the detector reason list so future diagnosis can distinguish hard provider rate limits from parser false positives.

## Fixture Test Cases

Add zero-provider-call fixture tests for the detector.

### Must Not Trigger

1. SHA/hash containing `429`:

```text
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

Expected: `rate_or_cooldown_signal == false`.

2. Hash-like / token-like alphanumeric text containing `429`:

```text
sha256: aa429bbccddeeff00112233445566778899aabbccddeeff0011223344556677
```

Expected: `rate_or_cooldown_signal == false`.

3. Ordinary prose containing a number with `429` embedded:

```text
The artifact id is build-1429-final and the command completed successfully.
```

Expected: `rate_or_cooldown_signal == false`.

### Must Trigger

4. HTTP 429 status:

```text
HTTP 429 Too Many Requests
```

Expected: `rate_or_cooldown_signal == true`, reason includes `http_status_429` or equivalent.

5. Structured status code:

```json
{"status_code": 429, "message": "Too Many Requests"}
```

Expected: `rate_or_cooldown_signal == true`, reason includes structured `429` detection.

6. “rate limit” text:

```text
Provider returned rate limit exceeded. Retry later.
```

Expected: `rate_or_cooldown_signal == true`.

7. “too many requests” text:

```text
Too many requests; please retry after 60 seconds.
```

Expected: `rate_or_cooldown_signal == true`.

8. “quota exceeded” text:

```text
Quota exceeded for this provider.
```

Expected: `rate_or_cooldown_signal == true`.

9. Cooldown text:

```text
Provider cooldown active; try again in 180 seconds.
```

Expected: `rate_or_cooldown_signal == true`.

10. Retry-after header style:

```text
HTTP/1.1 429 Too Many Requests
Retry-After: 120
```

Expected: `rate_or_cooldown_signal == true`.

## Validation Commands

After implementation, run only zero-provider-call validations first:

```sh
python3 -m py_compile scripts/context_plus_hard_negative_evaluator.py
```

Add a local fixture/self-test mode or a tiny deterministic test script that imports the detector and runs the fixture list above without Gateway/model/provider calls, for example:

```sh
python3 scripts/context_plus_hard_negative_evaluator.py rate-cooldown-fixture-selftest \
  --fixture-source sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/hard_negative_micro_batch_12_timeout_retry_20260708T1736AEST/raw_calls/0001_hn-20260707-0184_attempt-0001 \
  --no-provider-calls
```

If no CLI subcommand is added, use an explicit local Python fixture runner committed with the repair evidence, e.g.:

```sh
python3 /tmp/context_plus_rate_cooldown_fixture_selftest.py
```

Required self-test assertions:

- MB12 `hn-20260707-0184` raw stdout/stderr reclassifies as `PASS_NO_RATE_LIMIT_OR_COOLDOWN`.
- SHA/hash containing `429` does not trigger.
- HTTP 429 triggers.
- `rate limit` triggers.
- `too many requests` triggers.
- `quota exceeded` triggers.
- cooldown/retry-after text triggers.
- The self-test reports zero Gateway/model/provider calls.

Then run bounded artifact checks only:

```sh
git diff --check -- scripts/context_plus_hard_negative_evaluator.py
```

If wrapper scripts are regenerated for later MB12 remainder execution, they must use the repaired detector; do not patch only a one-off wrapper while leaving shared harness behavior unsafe.

## Pass / Hold / Fail Criteria

### PASS_REPAIR_VALIDATED

All of the following are true:

- Parser repair is implemented in shared harness code, not only in a one-off MB12 wrapper.
- Fixture self-test passes all must-trigger and must-not-trigger cases.
- MB12 `hn-20260707-0184` preserved raw output reclassifies as no rate/cooldown.
- Real HTTP 429 / rate-limit / quota / cooldown examples still trigger.
- `py_compile` and `git diff --check` pass.
- No Gateway/model/provider calls occur during validation.
- No comparator, promotion, M6, MB12 resume, or MB13 start occurs.

### HOLD_REPAIR_SCOPE_UNCLEAR

Use this if:

- Detector ownership between shared harness and generated wrappers is unclear.
- Additional call sites use `RATE_NEEDLES` and cannot be audited safely.
- Existing evidence is insufficient to prove the false positive source.
- A repair would need broader evaluator restructuring than this plan covers.

### FAIL_REPAIR_PLAN_UNSAFE

Use this if:

- The proposed repair suppresses real rate-limit/cooldown text.
- Bare `429` remains matched inside arbitrary alphanumeric/hash strings.
- Validation requires live provider calls.
- The repair path couples parser repair to MB12 resume, MB13, comparator, promotion, or M6.

## MB12 / MB13 Continuation Boundary

This plan does not authorize continuation.

Before any MB12 remainder execution:

1. Preserve this plan.
2. Review and approve implementation of parser repair.
3. Validate parser repair using zero-provider-call fixtures.
4. Preserve repair evidence.
5. Prepare a separate duplicate-safe MB12 remainder plan selecting only `hn-20260707-0185` → `hn-20260707-0188` in a fresh output directory.
6. Obtain separate approval before any Gateway/model/provider calls.

MB13 remains blocked until MB12 remainder policy is resolved and separately approved.

## Closeout

Final plan classification: `PASS_REPAIR_PLAN_READY`.

No provider calls, evaluation runs, comparator, promotion, M6 proposal, MB12 resume, MB13 start, route/config/Gateway mutation, memory promotion, provider/model change, production apply, cache enablement, or commit/push occurred while preparing this plan.
