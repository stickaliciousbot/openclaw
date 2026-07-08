# HN-0145 / HN-0153 Case-Hold Continuation Policy

Date: 2026-07-08 AEST

Closeout classification: `PASS_CASE_HOLD_CONTINUATION_POLICY_READY`

Execution gate: `HOLD_OPERATOR_APPROVAL_REQUIRED`

Micro-batch 5 gate: `BLOCKED_PENDING_CASE_HOLD_POLICY_UPDATE_PRESERVATION`

## Scope

Policy artifact only. This policy updates the previous HN-0145-only continuation policy after preserving the HN-0153 timeout diagnosis.

This policy does **not** authorize live evaluation, retry, Micro-batch 5 start, Gateway/model/provider calls, comparator, promotion, M6 proposal, route/config/Gateway mutation, memory promotion, provider/model change, production apply, cache enablement, commit, or push.

## Preserved diagnosis evidence

HN-0145:

- Artifact: `HN_0145_TIMEOUT_RETRY_EXHAUSTED_DIAGNOSIS.md`
- Diagnosis classification: `HOLD_CASE_TIMEOUT_RETRY_EXHAUSTED`
- Pushed branch: `evidence/context-plus-hard-negative-hn-0145-timeout-diagnosis-20260708`
- Pushed commit: `b4b1c72d33405dedcca87e5c7c73a340e090a65e`

HN-0153:

- Artifact: `HN_0153_TIMEOUT_RETRY_EXHAUSTED_DIAGNOSIS.md`
- Diagnosis classification: `HOLD_CASE_TIMEOUT_RETRY_EXHAUSTED`
- Secondary continuation gate: `HOLD_CASE_HOLD_POLICY_UPDATE_REQUIRED`
- Pushed branch: `evidence/context-plus-hard-negative-hn-0153-timeout-diagnosis-20260708`
- Pushed commit: `d63f22dd13f52f44a2108495173f60dbdc7a76b9`

## Current lineage state

Micro-batch 1:

- Range: `hn-20260707-0134` -> `hn-20260707-0138`
- Classification: `PASS_MICRO_BATCH_1_READY`
- Pushed branch: `evidence/context-plus-hard-negative-micro-batch-1-20260708`
- Pushed commit: `eff29e0b82030f206a65ec86f27489d70894f1a6`

Micro-batch 2:

- Range: `hn-20260707-0139` -> `hn-20260707-0143`
- Classification: `PASS_MICRO_BATCH_2_READY`
- Pushed branch: `evidence/context-plus-hard-negative-micro-batch-2-20260708`
- Pushed commit: `17c8f93c86fa5721f9ef63c3a74706d4739fc648`

Micro-batch 3:

- Approved range: `hn-20260707-0144` -> `hn-20260707-0148`
- Pushed branch: `evidence/context-plus-hard-negative-micro-batch-3-20260708`
- Pushed commit: `be09877f07811fee1253a8374d4b41cb3908f6c2`
- Classification: `HOLD_MICRO_BATCH_3_RETRY_EXHAUSTED`
- Held case: `hn-20260707-0145`
- Stop reason: retry exhausted on `HOLD_GATEWAY_CLIENT_TRANSPORT_TIMEOUT`
- Provider mismatch: `0`
- Rate/cooldown: `PASS_NO_RATE_LIMIT_OR_COOLDOWN`
- Mutation sentinel: `PASS_MUTATION_SENTINEL_OUTSIDE_OUTPUT_UNCHANGED`
- Comparator/promotion/M6: `BLOCKED_NOT_RUN`

Micro-batch 4:

- Approved range: `hn-20260707-0149` -> `hn-20260707-0153`
- Pushed branch: `evidence/context-plus-hard-negative-micro-batch-4-20260708`
- Pushed commit: `b8ae570df934b62cf5a74ae462daf32f07816487`
- Classification: `HOLD_MICRO_BATCH_4_RETRY_EXHAUSTED`
- Held case: `hn-20260707-0153`
- Stop reason: `retry_exhausted:HOLD_GATEWAY_CLIENT_TRANSPORT_TIMEOUT`
- Provider verified count: `4/5`
- Provider mismatch: `0`
- Retry count: `1`
- Rate/cooldown: `PASS_NO_RATE_LIMIT_OR_COOLDOWN`
- Mutation sentinel: `PASS_MUTATION_SENTINEL_OUTSIDE_OUTPUT_UNCHANGED`
- Comparator/promotion/M6: `BLOCKED_NOT_RUN`

## Held-case decisions

This policy marks the following cases as held for continuation planning:

- `hn-20260707-0145` -> `HOLD_CASE_TIMEOUT_RETRY_EXHAUSTED`
- `hn-20260707-0153` -> `HOLD_CASE_TIMEOUT_RETRY_EXHAUSTED`

Held-case rules:

1. Do not retry `hn-20260707-0145` under the current timeout/retry policy.
2. Do not retry `hn-20260707-0153` under the current timeout/retry policy.
3. Do not include either held case in any future live provider-call selection unless Stick separately approves a new diagnosis/remediation policy for that specific case.
4. Do not count either held case as provider-boundary PASS.
5. Do not treat either held case as comparator-ready or promotion evidence.
6. Represent both held cases in any future ledger as terminal HOLD, not as success and not as missing/unseen.
7. Preserve all first-attempt and retry evidence for both held cases; never overwrite it.

## Continuation principle

Continuation may be safe only if it is explicit that the suite has held cases. The continuation ledger must separate:

- provider-verified terminal PASS cases;
- terminal held cases;
- unattempted cases;
- retry-exhausted cases;
- future attempts.

Partial/held evidence is not promotion evidence.

Comparator remains blocked unless and until a later approved comparator policy explicitly defines how held cases are treated. Under the current strict promotion rule, held hard-negative cases block promotion readiness.

## Micro-batch 5 gate

Micro-batch 5 is currently:

`BLOCKED_PENDING_CASE_HOLD_POLICY_UPDATE_PRESERVATION`

Micro-batch 5 must not start until all of the following are true:

1. This updated policy is reviewed and preserved.
2. The preserved policy explicitly lists both held cases: `hn-20260707-0145` and `hn-20260707-0153`.
3. A separate execution approval is given after policy preservation.
4. The selected live range is explicitly approved and duplicate-safe.
5. The live selection excludes both held cases unless Stick separately approves a new remediation/retry policy.
6. Comparator, promotion, and M6 proposal remain blocked.

This policy does not define or approve the Micro-batch 5 case range.

## Required preflight for any future continuation

Before any future live execution after this policy, require all of the following:

1. Verify Micro-batch 1 `PASS_PUSHED` evidence is present at commit `eff29e0b82030f206a65ec86f27489d70894f1a6`.
2. Verify Micro-batch 2 `PASS_PUSHED` evidence is present at commit `17c8f93c86fa5721f9ef63c3a74706d4739fc648`.
3. Verify Micro-batch 3 HOLD evidence is present at commit `be09877f07811fee1253a8374d4b41cb3908f6c2`.
4. Verify Micro-batch 4 HOLD evidence is present at commit `b8ae570df934b62cf5a74ae462daf32f07816487`.
5. Verify HN-0145 diagnosis evidence is present at commit `b4b1c72d33405dedcca87e5c7c73a340e090a65e`.
6. Verify HN-0153 diagnosis evidence is present at commit `d63f22dd13f52f44a2108495173f60dbdc7a76b9`.
7. Verify `hn-20260707-0145` is excluded from the live selection and recorded as `HOLD_CASE_TIMEOUT_RETRY_EXHAUSTED`.
8. Verify `hn-20260707-0153` is excluded from the live selection and recorded as `HOLD_CASE_TIMEOUT_RETRY_EXHAUSTED`.
9. Verify no selected case has provider-verified terminal evidence in this lineage.
10. Verify selected case count and range exactly match the separately approved continuation request.
11. Verify requested model is `token-broker-vmesh/auto`.
12. Verify expected provider is `token-broker-vmesh`.
13. Verify output directory is new/empty.
14. Verify mutation sentinel pre-state.
15. Verify rate-limit/cooldown guardrails.
16. Verify comparator, promotion, and M6 proposal remain blocked.

## Hard aborts for future continuation

Abort any future continuation if:

- `hn-20260707-0145` is selected for live retry without separate explicit approval;
- `hn-20260707-0153` is selected for live retry without separate explicit approval;
- any selected case falls outside the separately approved continuation range;
- duplicate-prevention fails;
- provider mismatch appears;
- fallback/model override appears;
- rate-limit/cooldown unsafe signal appears;
- mutation sentinel changes outside approved output;
- route/config/Gateway/memory/provider/model/cache mutation appears;
- Micro-batch 5 starts before this updated policy is preserved;
- Micro-batch 5 starts without separate execution approval;
- comparator runs;
- promotion is attempted;
- M6 proposal is prepared.

## Comparator / promotion / M6 gating

Comparator remains blocked.

Promotion remains blocked.

M6 proposal remains blocked.

A held case means the full 240-case hard-negative production evidence is not cleanly complete. No promotion eligibility can be inferred from Micro-batch 1, Micro-batch 2, Micro-batch 3, Micro-batch 4, either held-case diagnosis, or this policy.

Only a later separately approved policy may define whether held-case comparator treatment is allowed. Even then, current standing rule remains: only `PASS_FALSE_POSITIVE_BASELINE_IMPROVED` can lead to promotion eligibility.

## Policy closeout

This policy is ready for review but does not authorize execution.

Closeout classification:

`PASS_CASE_HOLD_CONTINUATION_POLICY_READY`

Execution gate:

`HOLD_OPERATOR_APPROVAL_REQUIRED`

Micro-batch 5 gate:

`BLOCKED_PENDING_CASE_HOLD_POLICY_UPDATE_PRESERVATION`
