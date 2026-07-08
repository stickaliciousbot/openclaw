# Hard-Negative Batched Timeout / Retry Policy

Date: 2026-07-08 AEST

Closeout classification: `PASS_TIMEOUT_RETRY_POLICY_READY`

Execution gate: `HOLD_RETRY_POLICY_OPERATOR_APPROVAL_REQUIRED`

## Scope

Policy update only.

This artifact defines how future hard-negative production evaluation may safely handle Gateway/client timeouts and token-solver upstream timeouts without masking provider-boundary failures or duplicating calls.

No live execution occurred while writing this policy:

- No Batch 1 retry.
- No Batch 2 start.
- No hard-negative live evaluation.
- No Gateway/model/provider calls.
- No comparator run.
- No promotion.
- No M6 proposal.
- No route/config/Gateway mutation.
- No restart.
- No `doctor --repair`.
- No memory promotion.
- No provider/model change.
- No production apply.
- No cache enablement.
- No commit/push.

This policy is **not execution approval**. Future retry or micro-batch execution requires separate operator approval after this policy is reviewed and preserved.

## Diagnosis summary

Current diagnosis artifact:

`GATEWAY_HEALTH_TRANSPORT_DIAGNOSIS.md`

Current diagnosis classification:

`HOLD_GATEWAY_PROVIDER_STALL_CLIENT_TIMEOUT_PARTIAL`

Relevant findings:

- `hn-20260707-0134` reached Gateway and `token-broker-vmesh`; upstream `token-solver-v4` later timed out with `504 "TOKEN_SOLVER_V4_UPSTREAM_TIMEOUT"`.
- For `hn-20260707-0134`, the client websocket/CLI timeout fired first at `120000ms`, so raw per-case output showed provider-null/missing-output even though later Gateway embedded logs had provider-runtime timeout evidence.
- `hn-20260707-0145` reached Gateway and entered active `model_call`, then the client websocket/CLI timed out at `120000ms`; bounded logs did not prove token-broker/provider completion for that attempt.
- Gateway was not proven down; bounded logs showed Gateway continued answering other websocket requests around both failures.
- PATH drift is a background warning only, not proven causal.
- Transport failures are not provider mismatch evidence.
- Provider-null is not inherently retryable; it is retryable only when raw stdout/stderr prove a command/transport timeout failure and no provider output exists.

## Proposed batch size

Recovery batch size: `5` cases per batch until stable.

Rules:

1. Use 5-case micro-batches for any future hard-negative production execution until stability is re-established.
2. Do not return to 20-case batches until either:
   - three consecutive 5-case micro-batches close cleanly with provider boundary, mutation sentinel, duplicate guard, and rate/cooldown checks PASS; or
   - Stick explicitly approves a written return-to-20 rationale.
3. Do not increase above 20 cases in this evaluation lineage without separate explicit approval.
4. Batch 1 must not be retried wholesale. Existing provider-verified attempts remain attempted-authority.
5. Batch 2 remains blocked until Batch 1 is terminally resolved.

## Approved retryable errors

A case is retryable only if all duplicate-safety and preservation requirements pass, and only under one of these classifications:

1. `GatewayTransportError` with exact timeout signature:

```text
GatewayTransportError: gateway timeout after 120000ms
```

2. `TOKEN_SOLVER_V4_UPSTREAM_TIMEOUT`, including Gateway embedded/provider runtime evidence such as:

```text
504 "TOKEN_SOLVER_V4_UPSTREAM_TIMEOUT"
```

3. `provider=null` only when raw stdout/stderr prove command/transport failure, not fallback. Required proof:
   - raw stdout is empty or non-provider output;
   - raw stderr contains a recognized transport/upstream timeout signature;
   - parse result classifies the attempt as command/transport failure;
   - no provider-verified result exists for the same case attempt;
   - provider-null is not caused by fallback, model override, parse masking, missing capture, or harness bug.

Provider-null without preserved raw stdout/stderr proof remains `HOLD_PROVIDER_NULL_EVIDENCE_INCOMPLETE`, not retryable.

## Non-retryable errors

Never retry when any of these are present:

- provider mismatch;
- fallback execution or fallback/model override;
- mutation sentinel failure;
- rate-limit/cooldown unsafe signal;
- duplicate-call risk or duplicate-prevention uncertainty;
- selected case outside approved range;
- output directory not new/empty;
- missing first-attempt raw stdout/stderr/parse result;
- route/config/Gateway/memory/provider/model/cache mutation;
- comparator attempt;
- promotion attempt;
- M6 proposal attempt;
- production apply/cache enablement/provider/model change;
- any failure where retry would obscure whether the first attempt reached a provider.

Non-retryable closeouts must preserve evidence and stop the batch lineage until reviewed.

## Retry limit

Maximum retry limit: `1` retry per case.

Lineage:

- first attempt: `attempt-0001`
- only allowed retry: `attempt-0002`

No `attempt-0003` is allowed in this policy.

If `attempt-0002` also times out or returns the same upstream timeout class, close:

`HOLD_GATEWAY_TIMEOUT_RETRY_EXHAUSTED`

Do not attempt another retry, do not continue to the next case, and do not merge the batch as complete.

## Retry delay / cooldown

Before the single retry, enforce an explicit cooldown.

Minimum policy requirement:

- wait at least `180` seconds after the failed attempt is fully preserved; and
- verify there is no rate-limit/cooldown signal in raw stderr/stdout, parse result, rate-limit report, or Gateway/provider logs.

If any rate-limit/cooldown signal is present, do **not** retry. Close:

`HOLD_RATE_LIMIT_OR_COOLDOWN`

The retry cooldown is not approval to run health probes, provider calls, or extra diagnostics. It is only the minimum wait before an already-approved single retry.

## Client timeout vs upstream timeout classification

### Client websocket / CLI transport timeout

Classify as `HOLD_GATEWAY_CLIENT_TRANSPORT_TIMEOUT` when raw stderr contains:

```text
GatewayTransportError: gateway timeout after 120000ms
Gateway target: ws://127.0.0.1:18789
```

Characteristics:

- command exits non-zero;
- raw stdout is missing or non-provider output;
- provider field is null/missing in parse result;
- Gateway may still be alive and answering other websocket requests;
- provider reach may be unknown unless Gateway logs prove provider/backend evidence.

This is retryable once only if all retry preconditions pass.

### Upstream token-solver timeout

Classify as `HOLD_TOKEN_SOLVER_V4_UPSTREAM_TIMEOUT` when Gateway/provider logs show:

```text
504 "TOKEN_SOLVER_V4_UPSTREAM_TIMEOUT"
```

Characteristics:

- request reached Gateway;
- token-broker-vmesh/provider path is proven if `provider="token-broker-vmesh"` or equivalent appears in bounded logs;
- upstream `token-solver-v4` timeout is runtime/provider-path instability, not provider mismatch;
- raw case output may still be provider-null if the client timed out before Gateway returned the embedded error.

This is retryable once only if no provider-verified result exists for the case and duplicate-safety passes.

### Combined client-first/upstream-later timeout

Classify as `HOLD_CLIENT_TIMEOUT_MASKED_UPSTREAM_TIMEOUT` when the raw case attempt shows `GatewayTransportError ... 120000ms`, and later bounded Gateway logs show `TOKEN_SOLVER_V4_UPSTREAM_TIMEOUT` for the same run/case.

This is retryable once only if first-attempt evidence is preserved and no provider result was emitted to the harness.

## Provider-null handling

Provider-null taxonomy:

1. `PROVIDER_NULL_COMMAND_FAILURE_WITH_STDERR`
   - Retryable only if stderr proves approved transport/upstream timeout and all retry gates pass.
2. `PROVIDER_NULL_MISSING_EVIDENCE`
   - Not retryable. Close HOLD and preserve evidence.
3. `PROVIDER_NULL_PARSE_OR_CAPTURE_FAILURE`
   - Not retryable until harness/capture issue is diagnosed without live provider calls.
4. `PROVIDER_NULL_FALLBACK_OR_MODEL_OVERRIDE`
   - Non-retryable hard fail or HOLD depending on exact evidence; never merge as provider-boundary PASS.
5. `PROVIDER_NULL_PROVIDER_MISMATCH_MASKED`
   - Non-retryable fail; requires provider-boundary repair before any continuation.

Provider-null must never be treated as provider-boundary PASS. It is either a preserved HOLD/fail condition or a tightly scoped transport retry candidate.

## Per-case raw capture requirements

For every first attempt and retry attempt, preserve:

- `child_stdout.raw`
- `child_stderr.raw`
- `parse_result.json`
- command return code
- timeout flag and timeout layer if known
- requested model
- expected provider
- provider raw value and normalized value if present
- provider-boundary classification
- provider-null taxonomy classification
- rate-limit/cooldown signals
- Gateway target/config/bind from stderr when present
- Gateway runId/traceId if available from bounded logs
- attempt start/end timestamps
- attempt lineage (`attempt-0001`, `attempt-0002`)

Missing raw stdout/stderr for an attempted case is a hard HOLD and blocks retry until reviewed.

## Preservation requirements

Before retrying a case, preserve first-attempt evidence immutably:

- raw call directory for `attempt-0001`;
- parse result;
- provider-null taxonomy report;
- command failure report;
- rate-limit/cooldown report;
- duplicate-call prevention report;
- mutation sentinel state up to the failed attempt;
- batch closeout or interim retry-decision note.

After retrying, preserve retry evidence separately:

- raw call directory for `attempt-0002`;
- parse result;
- retry decision record linking to first attempt;
- updated provider/null/command/rate reports;
- terminal batch closeout.

Never overwrite first-attempt evidence. Retry evidence supplements, not replaces, first-attempt evidence.

## Duplicate-call safety

Before any retry:

1. Confirm the case has no provider-verified successful output in the active lineage.
2. Confirm retry count for that case is `0`.
3. Confirm the first attempt failed only with an approved retryable timeout class.
4. Confirm no previous retry attempt exists in any relevant output directory.
5. Confirm batch ledger marks the retry as `transport_retry`, not as a new ordinary case attempt.
6. Confirm all prior provider-verified cases are excluded from retry selection.

If duplicate-call safety cannot be proven, close:

`FAIL_BATCH_DUPLICATE_CALL_BOUNDARY`

or, if evidence is incomplete but no duplicate is proven:

`HOLD_DUPLICATE_CALL_RISK_UNRESOLVED`

## Hard abort rules

Abort immediately if any of the following occur:

- retry is attempted without explicit operator approval;
- retry count exceeds 1 for any case;
- Batch 1 is retried wholesale;
- Batch 2 starts before Batch 1 is terminally resolved;
- any case outside the approved micro-batch range is selected;
- any provider-verified case is selected for retry;
- provider mismatch appears;
- fallback/model override appears;
- mutation sentinel changes outside approved output;
- rate-limit/cooldown unsafe signal appears;
- duplicate-call risk appears;
- route/config/Gateway/memory/provider/model/cache mutation appears;
- Gateway restart/repair or `doctor --repair` is attempted during evaluation;
- comparator, promotion, or M6 is attempted;
- retry also times out.

Abort closeout classifications:

- `ABORT_BATCH_FORBIDDEN_ACTION_ATTEMPTED`
- `FAIL_BATCH_PROVIDER_MISMATCH`
- `FAIL_BATCH_MUTATION_SENTINEL`
- `FAIL_BATCH_DUPLICATE_CALL_BOUNDARY`
- `HOLD_GATEWAY_TIMEOUT_RETRY_EXHAUSTED`
- `HOLD_RATE_LIMIT_OR_COOLDOWN`

## Batch closeout policy

A 5-case micro-batch may close `PASS_BATCH_READY_FOR_MERGE` only if:

- all 5 cases have provider-boundary PASS;
- expected provider is `token-broker-vmesh` for every case;
- requested model is `token-broker-vmesh/auto` for every case;
- provider mismatch count is `0`;
- unresolved provider-null count is `0`;
- command failure count is `0` after any approved retry;
- timeout count is `0` after any approved retry;
- retry count per case is `0` or `1`, never higher;
- duplicate-call prevention PASS;
- mutation sentinel PASS;
- rate-limit/cooldown PASS;
- raw stdout/stderr/parse result exist for every attempt;
- retry lineage is preserved for every retried case.

If a retry succeeds, the batch closeout must still record that a transport retry occurred. A successful retry does not erase first-attempt instability evidence.

## Comparator gating

Comparator remains blocked until all `240` production hard-negative cases are complete and merged cleanly.

Comparator prerequisites:

- every case `hn-20260707-0001` → `hn-20260707-0240` has exactly one terminal provider-boundary result or an approved retry lineage ending in provider-boundary PASS;
- no unresolved HOLD batches remain;
- no provider mismatch;
- no duplicate-call unresolved risk;
- no mutation sentinel failure;
- no rate-limit/cooldown unsafe state;
- combined production journal is complete and deterministic;
- combined provider-boundary report is clean;
- combined mutation sentinel report is clean;
- combined evidence records retry lineage without overwriting first attempts.

Partial batches, partial retries, or equal-zero-zero findings are not comparator/promotion evidence.

## Promotion and M6 gates

Promotion remains blocked until comparator passes and all remaining gates close.

M6 proposal remains blocked until:

1. all 240 production hard-negative cases are complete and merged cleanly;
2. comparator is run under separate approval;
3. comparator returns an eligible improvement result, specifically `PASS_FALSE_POSITIVE_BASELINE_IMPROVED`;
4. mutation, provider-boundary, duplicate-call, and rate/cooldown gates are clean;
5. promotion eligibility artifact is reviewed and separately approved.

`HOLD_EQUAL_ZERO_ZERO`, `FAIL_FALSE_POSITIVE_NOT_IMPROVED`, `FAIL_REGRESSION_FOUND`, unresolved HOLDs, or transport instability block promotion and M6.

## Closeout decision

Selected closeout classification:

`PASS_TIMEOUT_RETRY_POLICY_READY`

Execution remains gated by:

`HOLD_RETRY_POLICY_OPERATOR_APPROVAL_REQUIRED`

Reason:

- The policy now defines 5-case micro-batches, one-retry maximum, retryable vs non-retryable timeout/provider-null classes, raw capture requirements, preservation rules, hard aborts, comparator gating, and promotion/M6 blocking.
- It does not authorize live retry or evaluation execution.
