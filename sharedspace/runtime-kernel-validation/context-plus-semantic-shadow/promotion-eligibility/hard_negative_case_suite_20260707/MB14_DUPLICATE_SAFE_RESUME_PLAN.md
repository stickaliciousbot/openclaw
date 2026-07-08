# MB14 Duplicate-Safe Resume Plan

## Classification

`PASS_MB14_RESUME_PLAN_READY`

## Scope

Plan only. No MB14 resume execution, MB15 start, Gateway/model/provider calls, comparator, promotion, M6 proposal, route/config/Gateway mutation, memory promotion, provider/model change, production apply, cache enablement, commit, or push was performed while creating this plan.

## Inputs / Evidence Read

- MB14 summary:
  - `sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/hard_negative_micro_batch_14_after_parser_repair_20260708T1833AEST/summary.json`
- MB14 duplicate-call prevention report:
  - `sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/hard_negative_micro_batch_14_after_parser_repair_20260708T1833AEST/duplicate_call_prevention_report.json`
- Parser repair implementation closeout:
  - `sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/MB14_RATE_COOLDOWN_PARSER_REPAIR_IMPLEMENTATION.md`
- Parser repair validation summary:
  - `sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/rate_cooldown_parser_repair_mb14_validation_20260708/validation_summary.json`
- Active branch ref readback:
  - `.git/refs/heads/feature/stickbot-tars-m25-hardening-repair`

## Known MB14 State

- MB14 original range:
  - `hn-20260707-0194`
  - `hn-20260707-0195`
  - `hn-20260707-0196`
  - `hn-20260707-0197`
  - `hn-20260707-0198`
- MB14 summary classification before parser repair preservation:
  - `HOLD_MICRO_BATCH_14_INCOMPLETE`
- MB14 prior stop reason:
  - `rate_or_cooldown_signal`
- Provider boundary:
  - `PASS_PROVIDER_CALL_BOUNDARY`
- Provider verified count:
  - `3`
- Gateway/model/provider calls in original MB14 run:
  - `3`
- Mutation sentinel:
  - `PASS_MUTATION_SENTINEL_OUTSIDE_OUTPUT_UNCHANGED`
- Duplicate prevention classification in original MB14 run:
  - `PASS_DUPLICATE_CALL_PREVENTION_BOUNDARY`

## Attempted / Terminal Case Set

The duplicate-call prevention report lists the attempted MB14 case IDs as:

```json
[
  "hn-20260707-0194",
  "hn-20260707-0195",
  "hn-20260707-0196"
]
```

The MB14 summary confirms:

- `all_attempt_count`: `3`
- `terminal_case_count`: `3`
- `provider_verified_count`: `3`

Therefore the attempted/terminal MB14 set is exactly:

```text
A = {hn-20260707-0194, hn-20260707-0195, hn-20260707-0196}
```

These cases are forbidden for the future resume and must not be selected or rerun.

## Resume Case Set

The future resume set is exactly:

```text
R = {hn-20260707-0197, hn-20260707-0198}
```

Resume count:

```text
|R| = 2
```

No other case IDs are eligible for this MB14 resume.

## Duplicate-Safety Proof

Attempted/terminal set:

```text
A = {hn-20260707-0194, hn-20260707-0195, hn-20260707-0196}
```

Planned resume set:

```text
R = {hn-20260707-0197, hn-20260707-0198}
```

Intersection:

```text
A ∩ R = ∅
```

Explicit non-rerun guarantee:

- `hn-20260707-0194` is in `A`, not in `R`; it must not be rerun.
- `hn-20260707-0195` is in `A`, not in `R`; it must not be rerun.
- `hn-20260707-0196` is in `A`, not in `R`; it must not be rerun.

If any future execution plan includes `hn-20260707-0194`, `hn-20260707-0195`, or `hn-20260707-0196`, classify the plan as:

`FAIL_DUPLICATE_CALL_RISK`

If any future execution plan selects anything other than exactly `hn-20260707-0197` and `hn-20260707-0198`, classify the plan as:

`FAIL_MB14_RESUME_PLAN_UNSAFE`

## Parser Repair Availability Proof

Parser repair implementation evidence was preserved and pushed before this plan:

- Parser repair commit:
  - `9b4395897c6f6aa549ee7190004c088ee966f5cd`
- Evidence branch:
  - `evidence/context-plus-hard-negative-mb14-parser-repair-implementation-20260708`
- Marker:
  - `MB14_RATE_COOLDOWN_PARSER_REPAIR_IMPLEMENTATION_PUSHED`
- Implementation classification:
  - `PASS_PARSER_REPAIR_IMPLEMENTED_VALIDATED`
- Validation classification:
  - `PASS_PARSER_REPAIR_VALIDATION`
- Fixtures passed:
  - `14`
- Fixtures failed:
  - `0`
- Provider calls during repair validation:
  - `0`
- Gateway/model calls during repair validation:
  - `0`

Active branch ref readback:

```text
.git/refs/heads/feature/stickbot-tars-m25-hardening-repair = 9b4395897c6f6aa549ee7190004c088ee966f5cd
```

Therefore the repaired parser commit is present and active in the current working branch state used for this plan.

If the active commit does not contain `9b4395897c6f6aa549ee7190004c088ee966f5cd`, or if the source-aware parser fixtures are unavailable, future execution must classify as:

`HOLD_REPAIRED_HARNESS_NOT_AVAILABLE`

## Future Output Directory Guard

Future resume output directory reserved for a later separately approved execution:

```text
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/hard_negative_micro_batch_14_resume_after_parser_repair_20260708T1905AEST/
```

Creation-time readback for this plan returned ENOENT for that path, proving it does not currently exist. Non-existent is acceptable as new/empty for a future resume output target.

Future execution must abort before any provider call unless this output path is still new/empty. If the directory exists and contains any files, classify as:

`FAIL_MB14_RESUME_PLAN_UNSAFE`

## Future Execution Selection Requirements

A later separately approved MB14 resume may only run if all of the following are true immediately before the first provider call:

1. Parser repair commit `9b4395897c6f6aa549ee7190004c088ee966f5cd` is present and active.
2. Source-aware parser fixture evidence is readable and still passes in preserved evidence:
   - generated `outputs[].text` retry-after no-trigger fixture passed
   - real provider/system signal fixtures still trigger
3. Attempted set remains exactly:
   - `{hn-20260707-0194, hn-20260707-0195, hn-20260707-0196}`
4. Resume set is exactly:
   - `{hn-20260707-0197, hn-20260707-0198}`
5. `A ∩ R = ∅`
6. Future output directory is new/empty.
7. No comparator, promotion, M6 proposal, MB15 start, route/config/Gateway mutation, memory promotion, provider/model change, production apply, or cache enablement is included in the execution command.

## Later Resume Command Shape — Not Approved Here

The following is a shape constraint only, not approval to run:

```text
run MB14 resume with exactly hn-20260707-0197 and hn-20260707-0198, writing to the reserved new/empty output directory, with duplicate-call prevention enabled, parser repair commit active, and abort-on-mutation / provider-boundary / rate-cooldown guards enabled.
```

This plan does not authorize provider calls. A separate owner approval is required before any execution.

## Closeout Classification Rules

Use these classifications for future plan/execution gate results:

- `PASS_MB14_RESUME_PLAN_READY`
  - attempted set verified as exactly `{0194, 0195, 0196}`
  - resume set exactly `{0197, 0198}`
  - attempted/resume intersection empty
  - parser repair commit present and active
  - future output directory new/empty
  - MB15/comparator/promotion/M6 remain blocked
- `HOLD_MB14_ATTEMPTED_CASES_NOT_VERIFIED`
  - attempted/terminal set cannot be proven from preserved evidence
- `HOLD_REPAIRED_HARNESS_NOT_AVAILABLE`
  - parser repair commit/evidence is not active or cannot be verified
- `FAIL_DUPLICATE_CALL_RISK`
  - future plan includes `0194`, `0195`, or `0196`, or any previously attempted terminal case
- `FAIL_MB14_RESUME_PLAN_UNSAFE`
  - resume set differs from exactly `{0197, 0198}`
  - output directory is not new/empty
  - future command includes forbidden actions or side effects

## Boundary Readback

- MB14 resume execution: `BLOCKED_NOT_RUN`
- MB15: `BLOCKED`
- Comparator: `BLOCKED`
- Promotion: `BLOCKED`
- M6 proposal: `BLOCKED`
- Gateway/model/provider calls while creating this plan: `0`
- Route/config/Gateway mutation: `not run`
- Memory promotion: `not run`
- Provider/model change: `not run`
- Production apply: `not run`
- Cache enablement: `not run`
- Commit/push: `not run`

## Next Step

Stop here and request read-only scoped preservation review for this plan artifact only. Do not execute the MB14 resume, do not start MB15, and do not run comparator/promotion/M6.
