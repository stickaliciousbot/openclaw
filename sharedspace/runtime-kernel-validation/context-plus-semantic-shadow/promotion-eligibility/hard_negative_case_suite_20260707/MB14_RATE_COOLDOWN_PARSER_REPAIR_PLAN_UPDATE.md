# MB14 Rate/Cooldown Parser Repair Plan Update

## Classification

`PASS_REPAIR_PLAN_UPDATE_READY`

## Source Diagnosis

- Diagnosis artifact: `MB14_RATE_COOLDOWN_DIAGNOSIS.md`
- Diagnosis preservation: `PASS_PUSHED`
- Commit: `ddcb575762d59bbff279537bb98694171c3402fa`
- Branch: `evidence/context-plus-hard-negative-mb14-rate-cooldown-diagnosis-20260708`
- Diagnosis classification: `HOLD_PARSER_REPAIR_REQUIRED`
- Trigger case: `hn-20260707-0196`
- False-positive source: generated `outputs[].text` contained `retry after` while provider/system metadata was clean.

## Scope

Plan update only. No code changes, MB14 resume, MB15 start, Gateway/model/provider calls, comparator, promotion, M6 proposal, route/config/Gateway mutation, memory promotion, provider/model change, production apply, cache enablement, commit, or push occurred while writing this plan update.

## Problem Statement

The prior parser repair correctly stopped matching bare `429` inside hash-like output, but the active detector still scans the full combined stdout/stderr text, including generated model answer text under `outputs[].text`.

In MB14 case `hn-20260707-0196`, the provider call completed successfully:

- `returncode`: `0`
- `timed_out`: `false`
- `provider`: `token-broker-vmesh`
- `provider_boundary_classification`: `PASS_PROVIDER_VERIFIED`
- `stderr`: empty
- top-level payload metadata: `ok: true`, `transport: gateway`, `provider: token-broker-vmesh`, `model: auto`

The only cooldown-like phrase was inside generated answer text:

```text
safe_next=retry after tool path check.
```

That generated text is not a provider/system throttle signal. Treating it as a rate/cooldown signal caused MB14 to hold after `3/5` cases.

## Required Parser Rule Change

Cooldown detection must distinguish provider/system/transport signals from generated model content.

### Must Ignore Unless Paired With Structured Provider/System Metadata

The detector must not classify text inside generated output fields as rate/cooldown by itself, including:

- `outputs[].text`
- assistant/model answer text extracted from `outputs`
- user-facing safe-next/degraded-reason prose
- answer text containing phrases such as `retry after`, `try again in`, `cooldown`, `quota`, or `rate limit`, unless a provider/system signal is also present

Required fixture:

```text
safe_next=retry after tool path check.
```

Expected: `rate_or_cooldown_signal == false` when this appears only inside generated `outputs[].text` and provider/system metadata is clean.

### Must Still Trigger For Real Provider/System Cooldown Signals

The detector must continue to trigger on explicit provider/system/transport evidence, including:

- stderr containing rate-limit/cooldown text
- HTTP status text such as `HTTP 429 Too Many Requests`
- header-style `Retry-After: <seconds>`
- structured payload fields such as `status`, `status_code`, `code`, `http_status` equal to `429`
- top-level or provider-attempt metadata fields such as `message`, `error`, `detail`, `reason` containing `rate limit`, `too many requests`, `quota exceeded`, `cooldown`, or `retry after`
- provider attempt/error metadata that records throttle/cooldown, if present in `attempts[]` or equivalent runtime metadata

## Proposed Implementation Shape

Replace full-payload text scanning with source-aware extraction.

Suggested function shape:

```python
def rate_or_cooldown_signal(stdout_text: str, stderr_text: str = "", payload: Any | None = None) -> tuple[bool, list[str]]:
    reasons = []

    # 1. Always inspect stderr / transport text.
    reasons += scan_rate_text(stderr_text, source="stderr")
    reasons += scan_status_429(stderr_text, source="stderr")

    # 2. Inspect top-level structured provider/system fields only.
    if isinstance(payload, dict):
        reasons += scan_status_fields(payload, source="payload")
        reasons += scan_text_fields(payload, keys=("message", "error", "detail", "reason"), source="payload")
        reasons += scan_attempt_metadata(payload.get("attempts"), source="attempts")

    # 3. Do NOT scan generated answer text from outputs[].text unless step 1 or 2
    # already found provider/system evidence.
    return bool(reasons), sorted(set(reasons))
```

Important: the implementation should avoid accidental scanning of `json.dumps(payload)` or raw stdout when payload is valid JSON, because that reintroduces generated-answer false positives.

If stdout is not valid JSON, the detector may conservatively scan raw stdout as transport/error text only when command status indicates command/provider failure or missing structured payload. Successful valid JSON with `outputs[].text` must use source-aware scanning.

## Fixture Requirements

Add zero-provider-call fixtures to `rate-cooldown-fixture-selftest`.

### New Must-Not-Trigger Fixture

1. Generated answer text containing retry-after phrase only:

Payload:

```json
{
  "ok": true,
  "transport": "gateway",
  "provider": "token-broker-vmesh",
  "model": "auto",
  "attempts": [],
  "outputs": [
    {
      "text": "I couldn’t complete the requested internal path cleanly, so I did not guess. degraded_reason=stale_ack_instead_of_answer; safe_next=retry after tool path check.",
      "mediaUrl": null
    }
  ]
}
```

Expected:

- `rate_or_cooldown_signal == false`
- no `retry_after_phrase` reason

### Existing Must-Not-Trigger Fixtures To Keep

- SHA/hash containing `429`
- hash-like / token-like alphanumeric text containing `429`
- ordinary prose containing a number with embedded `429`

### Must-Trigger Fixtures To Keep/Add

- `HTTP 429 Too Many Requests`
- structured `{"status_code": 429, "message": "Too Many Requests"}`
- top-level `{"error": "rate limit exceeded"}`
- stderr `Retry-After: 120`
- attempt metadata containing `rate limit`, `too many requests`, `quota exceeded`, `cooldown`, or structured `429`

## Validation Requirements

Before any MB14 resume is considered, run and preserve zero-provider-call validation:

```sh
python3 -m py_compile scripts/context_plus_hard_negative_evaluator.py
python3 scripts/context_plus_hard_negative_evaluator.py rate-cooldown-fixture-selftest \
  --fixture-source sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/hard_negative_micro_batch_12_timeout_retry_20260708T1736AEST/raw_calls/0001_hn-20260707-0184_attempt-0001 \
  --no-provider-calls
```

The self-test must report:

- generated `outputs[].text` retry-after fixture: `false`
- hash `429` fixtures: `false`
- real provider/system cooldown fixtures: `true`
- `gateway_model_provider_calls`: `0`
- `mutation_performed`: `false`

## MB14 Resume Policy After Repair

MB14 resume remains blocked until all are true:

1. Parser repair is implemented.
2. Parser repair validation passes with zero provider calls.
3. Parser repair evidence is selectively preserved.
4. A duplicate-safe MB14 resume plan is written and approved.

A later MB14 resume plan, if approved, must only target unattempted cases:

- `hn-20260707-0197`
- `hn-20260707-0198`

It must not rerun provider-verified cases:

- `hn-20260707-0194`
- `hn-20260707-0195`
- `hn-20260707-0196`

## Continuing Blocks

- MB14 resume: `BLOCKED_PENDING_PARSER_REPAIR`
- MB15: `BLOCKED`
- Comparator: `BLOCKED`
- Promotion: `BLOCKED`
- M6 proposal: `BLOCKED`
- Gateway/model/provider calls: `BLOCKED`
- Route/config/Gateway mutation: `BLOCKED`
- Memory promotion: `BLOCKED`
- Provider/model change: `BLOCKED`
- Production apply/cache enablement: `BLOCKED`
