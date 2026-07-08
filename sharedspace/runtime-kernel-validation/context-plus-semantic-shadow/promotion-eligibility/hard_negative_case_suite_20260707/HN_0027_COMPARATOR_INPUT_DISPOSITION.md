# HN-0027 Comparator-Input Disposition

Classification: `PASS_HN_0027_COMPARATOR_INPUT_HELD_DISPOSITION_READY`

## Scope and Non-Actions

This artifact gives an explicit comparator-input disposition for `hn-20260707-0027` after the repaired-schema first56 `0009→0056` replay held provider-unverified after the approved retry.

No replay, normalization, comparator execution, Gateway/model/provider calls, promotion, M6 proposal, post-0056 execution, post-0240 execution, route/config/Gateway mutation, memory promotion, provider/model change, production apply, or cache enablement occurred while creating this disposition.

## Evidence Inputs

- First56 `0009→0056` replay evidence: `PASS_PUSHED`
- First56 `0009→0056` replay evidence commit: `80e6c340a36a9d6dbc00aadd610498565b207894`
- First56 `0009→0056` replay evidence branch: `evidence/context-plus-hard-negative-first56-0009-0056-replay-20260708`
- First56 `0009→0056` replay evidence marker: `FIRST56_0009_0056_REPAIRED_SCHEMA_REPLAY_EVIDENCE_PUSHED`
- Aggregate readiness after first56 replay commit: `4d154ad745aa9a5706e11348d315e2b7c6f272fe`

## Comparator-Input Disposition

- Case ID: `hn-20260707-0027`
- Disposition: `HELD_RETRY_EXHAUSTED_PROVIDER_UNVERIFIED`
- Comparator-input treatment: `HELD_NON_AUTHORITATIVE_CASE`
- Reason: `provider-unverified after retry`
- Replay classification: `HOLD_FIRST56_0009_0056_REPLAY_RETRY_EXHAUSTED`
- Provider mismatch: `0`
- Rate/cooldown: `PASS_NO_RATE_LIMIT_OR_COOLDOWN`
- Duplicate prevention: `PASS_DUPLICATE_CALL_PREVENTION_READY`
- Fallback/model boundary: `PASS_NO_FALLBACK_OR_MODEL_OVERRIDE`
- Mutation sentinel: `PASS_MUTATION_SENTINEL_OUTSIDE_OUTPUT_UNCHANGED`

`hn-20260707-0027` may be represented in aggregate readiness as a held/retry-exhausted provider-unverified case. It must not be counted as a completed provider-verified comparator-authoritative case.

## Authority Rules

- The legacy first-56 fragment remains `non-authoritative / not superseded`.
- The partial repaired replay remains `partial HOLD / not complete comparator authority`.
- Comparator input must not count legacy first-56 evidence and repaired replay evidence together for the same case.
- `hn-20260707-0027` may be counted only in a held/disposition ledger, not in provider-verified completion counts.
- Cases after `hn-20260707-0027` in the first-56 range remain unresolved unless separately replayed or explicitly dispositioned.

## Closeout

- Closeout classification: `PASS_HN_0027_COMPARATOR_INPUT_HELD_DISPOSITION_READY`
- Blocking case dispositioned as held: `hn-20260707-0027`
- Treatment: `HELD_NON_AUTHORITATIVE_CASE`
- Reason: `provider-unverified after retry`
- Comparator-authoritative completion for HN-0027: `false`
- Held/disposition ledger eligibility: `true`
- Replay evidence commit: `80e6c340a36a9d6dbc00aadd610498565b207894`
- Legacy first-56 comparator authority: `non-authoritative / not superseded`
- Comparator readiness impact: HN-0027 is no longer the active replay blocker, but first-56 cases `hn-20260707-0028` → `hn-20260707-0056` remain unresolved under repaired-schema comparator authority.
- Comparator: `BLOCKED_NOT_RUN`
- Promotion: `BLOCKED`
- M6 proposal: `BLOCKED`
