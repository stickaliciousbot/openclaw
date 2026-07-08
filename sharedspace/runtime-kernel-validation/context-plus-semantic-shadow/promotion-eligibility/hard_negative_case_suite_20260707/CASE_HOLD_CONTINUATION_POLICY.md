# HN-0145 Case-Hold / Continuation Policy

Date: 2026-07-08 AEST

Closeout classification: `PASS_CASE_HOLD_CONTINUATION_POLICY_READY`

Execution gate: `HOLD_OPERATOR_APPROVAL_REQUIRED`

## Scope

Policy artifact only. This policy is prepared after preserving the HN-0145 timeout diagnosis.

Preserved diagnosis evidence:

- Artifact: `HN_0145_TIMEOUT_RETRY_EXHAUSTED_DIAGNOSIS.md`
- Diagnosis classification: `HOLD_CASE_TIMEOUT_RETRY_EXHAUSTED`
- Pushed branch: `evidence/context-plus-hard-negative-hn-0145-timeout-diagnosis-20260708`
- Pushed commit: `b4b1c72d33405dedcca87e5c7c73a340e090a65e`

No live evaluation, retry, Micro-batch 4 start, Gateway/model/provider call, comparator, promotion, M6 proposal, route/config/Gateway mutation, memory promotion, provider/model change, production apply, cache enablement, commit, or push occurred while preparing this policy.

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
- Completed terminal cases: `2`
- All attempts: `3`
- `hn-20260707-0144`: provider verified
- `hn-20260707-0145`: attempt 1 timeout + attempt 2 timeout after approved 180s cooldown
- `hn-20260707-0146` -> `hn-20260707-0148`: not attempted in Micro-batch 3

HN-0145 diagnosis:

- Classification: `HOLD_CASE_TIMEOUT_RETRY_EXHAUSTED`
- Timeout count: `3` preserved attempts across Batch 1 and Micro-batch 3
- Provider mismatch: `0`
- Rate/cooldown: `PASS`
- Mutation sentinel: `PASS`
- Gateway reached and active `model_call` stall observed
- Token-broker/token-solver completion not proven

## Held-case decision

This policy marks the following case as held for continuation planning:

- `hn-20260707-0145` -> `HOLD_CASE_TIMEOUT_RETRY_EXHAUSTED`

Held-case rules:

1. Do not retry `hn-20260707-0145` under the current timeout/retry policy.
2. Do not include `hn-20260707-0145` in any future live provider-call selection unless Stick separately approves a new diagnosis/remediation policy.
3. Do not count `hn-20260707-0145` as provider-boundary PASS.
4. Do not treat `hn-20260707-0145` as comparator-ready or promotion evidence.
5. Represent `hn-20260707-0145` in any future ledger as a terminal HOLD, not as success and not as missing/unseen.
6. Preserve all first-attempt and retry evidence for `hn-20260707-0145`; never overwrite it.

## Continuation principle

Continuation may be safe only if it is explicit that the suite has a held case. The continuation ledger must separate:

- provider-verified terminal PASS cases;
- held terminal cases;
- unattempted cases;
- retry-exhausted cases;
- future attempts.

Partial/held evidence is not promotion evidence.

Comparator remains blocked unless and until a later approved comparator policy explicitly defines how held cases are treated. Under the current strict promotion rule, a held hard-negative case blocks promotion readiness.

## Recommended next live-execution shape, if later approved

Because Micro-batch 3 stopped after `hn-20260707-0145`, cases `hn-20260707-0146` -> `hn-20260707-0148` remain unattempted in this lineage.

Do **not** start ordinary Micro-batch 4 (`hn-20260707-0149` -> `hn-20260707-0153`) while `0146` -> `0148` are unattempted unless a separate owner-approved skip policy explicitly allows that gap.

Recommended safe continuation shape:

`Micro-batch 3R / remainder-continuation` containing exactly:

- `hn-20260707-0146`
- `hn-20260707-0147`
- `hn-20260707-0148`
- `hn-20260707-0149`
- `hn-20260707-0150`

Rationale:

- excludes the held case `hn-20260707-0145`;
- does not duplicate `hn-20260707-0144` provider-verified evidence;
- fills the unattempted gap before advancing too far;
- preserves the 5-case micro-batch size;
- keeps continuation contiguous from the first unattempted case after the hold.

Alternative safe continuation shape, if Stick prefers strict original-batch boundaries:

`Micro-batch 3R / remainder-only` containing exactly:

- `hn-20260707-0146`
- `hn-20260707-0147`
- `hn-20260707-0148`

This breaks the 5-case micro-batch size and therefore requires explicit approval of a 3-case exception.

Recommendation: use the 5-case `0146` -> `0150` continuation shape only after this policy is approved and a separate execution approval is given.

## Required preflight for any future continuation

Before any future live execution after this policy, require all of the following:

1. Verify Micro-batch 1 `PASS_PUSHED` evidence is present at commit `eff29e0b82030f206a65ec86f27489d70894f1a6`.
2. Verify Micro-batch 2 `PASS_PUSHED` evidence is present at commit `17c8f93c86fa5721f9ef63c3a74706d4739fc648`.
3. Verify Micro-batch 3 HOLD evidence is present at commit `be09877f07811fee1253a8374d4b41cb3908f6c2`.
4. Verify HN-0145 diagnosis evidence is present at commit `b4b1c72d33405dedcca87e5c7c73a340e090a65e`.
5. Verify `hn-20260707-0145` is excluded from the live selection and recorded as `HOLD_CASE_TIMEOUT_RETRY_EXHAUSTED`.
6. Verify no selected case has provider-verified terminal evidence in this lineage.
7. Verify selected case count and range exactly match the separately approved continuation request.
8. Verify requested model is `token-broker-vmesh/auto`.
9. Verify expected provider is `token-broker-vmesh`.
10. Verify output directory is new/empty.
11. Verify mutation sentinel pre-state.
12. Verify rate-limit/cooldown guardrails.
13. Verify comparator, promotion, and M6 proposal remain blocked.

## Hard aborts for future continuation

Abort any future continuation if:

- `hn-20260707-0145` is selected for live retry without separate explicit approval;
- any selected case falls outside the separately approved continuation range;
- duplicate-prevention fails;
- provider mismatch appears;
- fallback/model override appears;
- rate-limit/cooldown unsafe signal appears;
- mutation sentinel changes outside approved output;
- route/config/Gateway/memory/provider/model/cache mutation appears;
- Micro-batch 4 starts without an approved gap/hold policy and an approved execution range;
- comparator runs;
- promotion is attempted;
- M6 proposal is prepared.

## Comparator / promotion / M6 gating

Comparator remains blocked.

Promotion remains blocked.

M6 proposal remains blocked.

A held case means the full 240-case hard-negative production evidence is not cleanly complete. No promotion eligibility can be inferred from Micro-batch 1, Micro-batch 2, Micro-batch 3, the HN-0145 diagnosis, or this policy.

Only a later separately approved policy may define whether held-case comparator treatment is allowed. Even then, current standing rule remains: only `PASS_FALSE_POSITIVE_BASELINE_IMPROVED` can lead to promotion eligibility.

## Policy closeout

This policy is ready for review but does not authorize execution.

Closeout classification:

`PASS_CASE_HOLD_CONTINUATION_POLICY_READY`

Execution gate:

`HOLD_OPERATOR_APPROVAL_REQUIRED`
