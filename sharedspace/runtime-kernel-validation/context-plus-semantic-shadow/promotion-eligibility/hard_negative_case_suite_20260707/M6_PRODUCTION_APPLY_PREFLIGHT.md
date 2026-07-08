# M6 Production Apply Preflight

Date: 2026-07-09 AEST

## Classification

`HOLD_M6_PRODUCTION_APPLY_SCOPE_UNCLEAR`

Secondary classifications:

- `HOLD_ROLLBACK_NOT_READY`
- `HOLD_LIVE_SMOKE_NOT_READY`

## Scope

This is preflight only. No production mutation was performed.

Forbidden actions remained blocked during this preflight:

- production apply: `NOT_RUN`
- route/config/Gateway mutation: `NOT_RUN`
- memory promotion: `NOT_RUN`
- provider/model change: `NOT_RUN`
- cache enablement: `NOT_RUN`
- replay/provider calls: `NOT_RUN`
- comparator rerun: `NOT_RUN`

## Inputs Read

M6 production proposal:

`sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/M6_CONTEXT_PLUS_PRODUCTION_PROPOSAL.md`

Preservation commit / branch / marker:

- Commit: `871522c5204b6062419e48a5a47a4d9cd4cf97a6`
- Branch: `evidence/context-plus-hard-negative-comparator-m6-proposal-20260709`
- Marker: `HARD_NEGATIVE_COMPARATOR_PASS_AND_M6_PROPOSAL_PUSHED`

Comparator evidence:

- `hard_negative_comparator_after_hn0133_disposition_20260709_v2/aggregate_comparator_readiness.json`
- `hard_negative_comparator_after_hn0133_disposition_20260709_v2/hard_negative_comparator_result.json`
- `hard_negative_comparator_after_hn0133_disposition_20260709_v2/HARD_NEGATIVE_COMPARATOR_CLOSEOUT.md`

## Comparator / Proposal Verification

Verified from preserved local artifacts:

- Aggregate readiness: `READY_HARD_NEGATIVE_COMPARATOR_INPUTS`
- Comparator classification: `PASS_FALSE_POSITIVE_BASELINE_IMPROVED`
- Authoritative cases: `235`
- Held/non-authoritative cases excluded from promotion basis:
  - `hn-20260707-0008`
  - `hn-20260707-0027`
  - `hn-20260707-0133`
  - `hn-20260707-0145`
  - `hn-20260707-0153`
- Duplicate count: `0`
- Case alignment: `PASS_CASE_ALIGNMENT_EXACT_235`
- Production false positives: `22/235`
- Context+ shadow false positives: `0/235`
- False-positive comparison: `PASS_STRICT_IMPROVEMENT`
- Ambiguity/continuation: `PASS_NO_AMBIGUITY_CONTINUATION_REGRESSION`
- Phrase-hardcoded: `PASS_NO_PHRASE_HARDCODED_REGRESSION`
- Routing: `PASS_NO_ROUTING_REGRESSION`
- Provider/Gateway/model calls during comparator: `0`

## Preflight Checklist

| Requirement | Status | Evidence / Finding |
| --- | --- | --- |
| M6 proposal artifact exists | PASS | `M6_CONTEXT_PLUS_PRODUCTION_PROPOSAL.md` exists and was preserved in commit `871522c5204b6062419e48a5a47a4d9cd4cf97a6`. |
| M6 proposal artifact matches preserved commit | PASS_WITH_LOCAL_EVIDENCE | Preservation log for commit `871522c5204b6062419e48a5a47a4d9cd4cf97a6` lists `M6_CONTEXT_PLUS_PRODUCTION_PROPOSAL.md` and comparator evidence files. No fresh remote checkout was performed during this preflight. |
| Comparator PASS evidence exists and is preserved | PASS | Comparator result and readiness artifacts are in preserved commit `871522c5204b6062419e48a5a47a4d9cd4cf97a6`. |
| Held/non-authoritative cases excluded from promotion basis | PASS | Held set is exactly five cases listed above; readiness shows held counted in production/shadow as `0`. |
| Production apply target exactly Context+ routing/promotion path described by M6 | HOLD | M6 proposal is proposal-only and does not name the exact production config file, route key, feature flag, service endpoint, control-surface API, or mutation command to apply. |
| Rollback path exists and is executable | HOLD | No exact rollback command, config restore path, branch/tag, or control-surface rollback operation is specified by M6. |
| Current production config snapshot captured before mutation | NOT_RUN | Blocked until exact production target is identified; no config snapshot was captured to avoid broad/sensitive/unscoped capture. |
| Mutation scope limited to Context+ promotion only | HOLD | Cannot verify until exact target file/key/route/control-surface mutation is specified. |
| No provider/model/cache/memory side effect outside M6 scope | HOLD | Cannot verify until exact target mutation and rollback/smoke commands are specified. |
| Gateway/service health green before apply | NOT_RUN | Not checked because preflight is already held on missing apply target/rollback/smoke definitions; no apply card should be prepared. |
| Live smoke plan defined before apply | HOLD | M6 does not define exact live smoke command, expected response, test prompt, route assertion, provider/model-call boundary, or pass/fail output schema. |
| Rollback trigger conditions defined before apply | HOLD | Generic rollback principle exists, but exact trigger thresholds and executable rollback command are missing. |

## Why This Cannot Close PASS

The comparator PASS and M6 proposal are sufficient to justify preparing for production promotion, but they are not sufficient to safely mutate production.

The M6 proposal explicitly states production apply is `NOT_APPROVED` and requires separate human/operator approval before mutation. It does not specify the exact production apply target or rollback command.

A safe native production-apply approval card must include:

- apply target,
- exact files/config/routes/control-surface keys to mutate,
- exact rollback command,
- exact smoke command,
- expected post-apply state,
- abort criteria,
- rollback criteria.

Those are currently missing, so preparing a native apply command/card would risk inventing the production mutation.

## Required Inputs To Reach PASS

To close `PASS_M6_PRODUCTION_APPLY_PREFLIGHT_READY`, provide or locate an artifact/runbook that specifies all of the following:

1. Exact production target:
   - config path / route key / feature flag / service endpoint / control-surface operation.
2. Exact current-state snapshot command:
   - scoped to only the target keys/files/routes.
3. Exact production apply command:
   - including dry-run/validate mode if available.
4. Exact rollback command:
   - restoring the captured snapshot or known-good state.
5. Exact smoke command:
   - live but bounded; includes expected route/promotion assertion and provider/model/cache side-effect checks.
6. Rollback triggers:
   - smoke fail, Gateway unhealthy, route mismatch, provider/model/cache/memory side effect, unexpected config diff, or missing rollback sentinel.
7. Evidence preservation branch/marker for apply/smoke/rollback.

## Native Production-Apply Command/Card

Not prepared.

Reason: preflight did not close PASS. The required apply target and rollback/smoke commands are missing.

## Closeout

- Preflight result: `HOLD_M6_PRODUCTION_APPLY_SCOPE_UNCLEAR`
- Production apply: `NOT_RUN`
- Production promoted: `NO`
- Rollback: `NOT_RUN`
- Smoke: `NOT_RUN`
- Evidence preservation for this preflight: pending scoped preservation approval
