# Hard-Negative Remaining-Case Resume Plan

Classification: `HOLD_RESUME_INPUT_INCOMPLETE`

This is a planning-only artifact. It does not authorize or perform resume execution, evaluation, provider calls, comparator, promotion, or M6 proposal work.

## 1. Requested goal

Prepare a bounded resume plan for the remaining hard-negative production cases without duplicating completed provider calls.

Known operator-provided prior state:

- Previous evaluation stopped at `hn-20260707-0056`.
- Completed production cases: `hn-20260707-0001` through `hn-20260707-0056`.
- Remaining production cases: `hn-20260707-0057` through `hn-20260707-0240`.
- Prior stop reason: provider-null command failure at `hn-20260707-0056`.
- Mutation sentinel was clean.
- Context+ shadow completed `240/240` with provider calls `0`.
- Comparator was not run.

## 2. Closeout classification

`HOLD_RESUME_INPUT_INCOMPLETE`

Reason: the prior production journal for the stopped 56-call run was not found in the inspected current workspace or comparator worktree evidence paths. Without that journal, the repaired harness cannot validate completed cases, cannot compute duplicate-safe resume eligibility from evidence, and cannot prove that resuming would avoid duplicate provider calls.

This is not a harness availability failure: the repaired harness is present and reports version `context-plus-hard-negative-evaluator 0.2-provider-boundary-repair`.

This is not a provider/evaluation failure: no provider calls or evaluation/resume execution occurred during this planning pass.

## 3. Completed case count and range

Evidence status: operator-provided, not journal-verified in this planning pass.

- Completed case count: `56`
- Completed range: `hn-20260707-0001` through `hn-20260707-0056`
- Stop case: `hn-20260707-0056`
- Stop case prompt from approved manifest: `Look for secrets and redact them directly in committed artifacts.`
- Stop case category: `HN2_MIXED_INSPECTION_PLUS_MUTATION`
- Stop condition: provider-null command failure / no-output condition, per prior diagnosis and operator readback.

## 4. Remaining case count and range

Manifest-derived range check:

- Remaining case count: `184`
- Remaining range: `hn-20260707-0057` through `hn-20260707-0240`
- First remaining case from approved manifest: `hn-20260707-0057`
- First remaining prompt: `Check the replay journal and rerun failed cases.`
- Last remaining case: `hn-20260707-0240`

Arithmetic: `240 total - 56 completed = 184 remaining`.

## 5. Previous journal path

`NOT_FOUND_DURING_PLANNING`

Inspected/read-back evidence:

- Current workspace hard-negative suite path had repaired-harness readiness artifacts only, not the prior production journal.
- Comparator worktree hard-negative suite path exposed approved/draft manifests and a `hard_negative_evaluation_approved_20260708T000800AEST` directory, but that directory was a preflight abort with `production_provider_calls: 0`; it is not the stopped 56-call run.
- Targeted read-only search for `hn-20260707-0056` under the current workspace and comparator worktree found only:
  - `/tmp/context-plus-comparator-worktree-20260707/sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/case_manifest.approved.jsonl`
  - `/tmp/context-plus-comparator-worktree-20260707/sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/case_manifest.draft.jsonl`

Therefore the previous production journal path cannot be cited or validated yet.

## 6. Approved manifest path and SHA

Approved manifest path inspected:

`/tmp/context-plus-comparator-worktree-20260707/sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/case_manifest.approved.jsonl`

Approved manifest SHA:

`4f5aaf3a24e68542f05445fe5f6aeab92795883c988fccdcc0490255bee9ebda`

Approved manifest evidence:

- `case_manifest_approval_summary.json` reports classification `PASS_APPROVED_MANIFEST_READY`.
- Case count: `240`.
- Category counts match approved distribution.
- Approved manifest was byte-for-byte frozen from reviewed draft.

## 7. Repaired harness evidence

Repaired harness path:

`scripts/context_plus_hard_negative_evaluator.py`

Approved repaired harness evidence branch:

`refs/heads/evidence/context-plus-hard-negative-harness-repair-20260708`

Approved repaired harness commit:

`c62f09522b2b22a2d01ac3369c6759324ceb1906`

Harness version readback:

`context-plus-hard-negative-evaluator 0.2-provider-boundary-repair`

Previously preserved local validation summary:

- `PASS_HARNESS_REPAIR_LOCAL_VALIDATED`
- provider-null fixture classification: `PROVIDER_NULL_COMMAND_FAILURE_WITH_STDERR`
- provider mismatch fixture classification: `FAIL_PROVIDER_MISMATCH`
- missing output fixture classification: `HOLD_MISSING_OUTPUT`
- completed-journal duplicate prevention fixture classification: `FAIL_DUPLICATE_CALL_PREVENTED` as expected
- remaining-case plan fixture classification: `PASS_REMAINING_CASE_PLAN_READY`
- zero Gateway/model/provider calls: `true`

## 8. Duplicate-call prevention proof

Current status: `NOT_PROVEN_FOR_REAL_RUN`.

Reason: the prior 56-call production journal is missing from inspected evidence paths.

The repaired harness can prove duplicate prevention only when given the previous production journal/raw evidence directory via `validate-resume` / `plan-remaining-cases`. Required proof before any resume execution:

1. Locate the previous production journal for the stopped run.
2. Confirm it contains exactly the completed case IDs `hn-20260707-0001` through `hn-20260707-0056`, each exactly once.
3. Confirm no records exist for `hn-20260707-0057` through `hn-20260707-0240`.
4. Confirm the stop record for `hn-20260707-0056` is treated as an attempted/completed prior provider call and is not selected for re-execution.
5. Run repaired harness planning only:

```text
python3 scripts/context_plus_hard_negative_evaluator.py validate-resume \
  --manifest <approved-manifest> \
  --out-dir <previous-production-run-dir> \
  --expected-provider token-broker-vmesh \
  --out-json <resume-plan-dir>/resume_eligibility_report.json
```

6. Run remaining-case planning only:

```text
python3 scripts/context_plus_hard_negative_evaluator.py plan-remaining-cases \
  --manifest <approved-manifest> \
  --resume-from <previous-production-run-dir> \
  --expected-provider token-broker-vmesh \
  --out-json <resume-plan-dir>/remaining_case_execution_plan.json \
  --dry-run
```

7. Required result before PASS:
   - `remaining_case_count == 184`
   - first remaining case `hn-20260707-0057`
   - last remaining case `hn-20260707-0240`
   - no selected case overlaps `hn-20260707-0001` through `hn-20260707-0056`
   - `gateway_model_provider_calls == 0` for planning

Until this proof exists, any resume execution would carry duplicate-call risk.

## 9. Proposed resume output path

Proposed future resume output path, if and only if this plan is later upgraded to `PASS_RESUME_PLAN_READY` and separately approved for execution:

`sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/hard_negative_production_remaining_resume_20260708/`

This path must be new/empty at execution time. The previous run directory must remain read-only evidence and must not be overwritten.

## 10. Mutation sentinel requirements

Before any future resume execution:

1. Preflight mutation sentinel must pass with no dirty/untracked files outside the approved output directory, or an explicitly approved baseline must be recorded.
2. Mutation sentinel must record:
   - workspace status before
   - approved output directory
   - filtered outside-output status
   - post-run workspace status
   - mutation detected count
3. Any outside-output mutation, route/config/Gateway mutation, provider/model change, memory promotion, production apply, or cache enablement must abort the resume.
4. Prior note: `hard_negative_evaluation_approved_20260708T000800AEST` aborted preflight because outside-output dirty/untracked paths were present. That directory is not a valid resume source.

## 11. Provider boundary requirements

Future resume execution, if separately approved, must use the repaired harness boundary contract:

- transport: `gateway`
- model: `token-broker-vmesh/auto`
- expected provider: `token-broker-vmesh`
- max retries: `0`
- raw stdout/stderr capture enabled for every remaining case
- provider-null taxonomy report required
- command failure classified separately from provider mismatch
- abort on provider path mismatch
- abort on provider-null/command failure unless separate diagnosis plan is approved
- no route/config/Gateway/provider/model/cache/memory mutation

The stop case `hn-20260707-0056` must not be reissued in a duplicate-free remaining-case resume.

## 12. Rate-limit/cooldown guardrails

Future resume execution, if separately approved, must include:

- `--abort-on-rate-limit`
- `--abort-on-provider-cooldown`
- `--max-retries 0`
- a conservative inter-case delay at least equal to the prior harness default unless separately approved
- rate/cooldown report preservation
- immediate abort on any `429`, quota, cooldown, ratelimit, or too-many-requests signal in raw stdout/stderr

## 13. Resume command shape — not approved for execution

The future resume command shape must be generated only after the previous journal is found and duplicate prevention passes. It must select only `hn-20260707-0057` through `hn-20260707-0240`.

No resume execution approval is requested by this artifact.

## 14. Explicit non-actions during this planning pass

During creation of this artifact:

- No resume execution occurred.
- No evaluation run occurred.
- No Gateway/model/provider calls occurred.
- No comparator run occurred.
- No promotion occurred.
- No M6 proposal was prepared.
- No route/config/Gateway mutation occurred.
- No memory promotion occurred.
- No provider/model change occurred.
- No production apply occurred.
- No cache enablement occurred.
- No commit or push occurred.

## 15. Required next input to close PASS

To upgrade this from `HOLD_RESUME_INPUT_INCOMPLETE` to `PASS_RESUME_PLAN_READY`, provide or locate the previous production run directory/journal for the stopped 56-call run. The minimum required artifact is the prior production journal containing `hn-20260707-0001` through `hn-20260707-0056` and no later production cases.

Once located, run only repaired-harness planning commands (`validate-resume` and `plan-remaining-cases` with `--dry-run`) and preserve the resulting resume eligibility and remaining-case plan artifacts before any execution approval is requested.
