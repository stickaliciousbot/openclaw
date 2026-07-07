# Duplicate-Safe Remaining-Case Resume Plan

Classification: `PASS_DUPLICATE_SAFE_RESUME_PLAN_READY`

## 1. Scope

Duplicate-safe remaining-case resume planning only. This artifact does not authorize or perform resume execution, evaluation rerun, Gateway/model/provider calls, comparator, promotion, or M6 proposal work.

## 2. Located 56-call journal authority

- Located journal path: `/tmp/context-plus-hard-negative-eval-clean-worktree-de5800b1/sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/hard_negative_evaluation_clean_worktree_20260708T001800AEST/production_routing/production_routing_journal.jsonl`
- Located journal SHA256: `8ebcceaf8d651929158eb430587963f1407ea5929b7401469bb6226e3d7e0446`
- Expected journal SHA256: `8ebcceaf8d651929158eb430587963f1407ea5929b7401469bb6226e3d7e0446`
- SHA matches expected: `True`
- Completed case count: `56`
- Completed case range: `hn-20260707-0001` → `hn-20260707-0056`
- Completed IDs exactly expected `hn-20260707-0001` through `hn-20260707-0056`: `True`
- Duplicate completed case IDs: `[]`

Stop record verification:

- Stop case: `hn-20260707-0056`
- Stop returncode: `1`
- Stop provider: `None`
- Stop expected_provider: `token-broker-vmesh`
- Stop output_present: `False`
- Stop gateway_model_provider_calls: `56`

## 3. Approved manifest authority

- Approved manifest path: `/tmp/context-plus-comparator-worktree-20260707/sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/case_manifest.approved.jsonl`
- Approved manifest SHA256: `4f5aaf3a24e68542f05445fe5f6aeab92795883c988fccdcc0490255bee9ebda`
- Expected approved manifest SHA256: `4f5aaf3a24e68542f05445fe5f6aeab92795883c988fccdcc0490255bee9ebda`
- SHA matches expected: `True`
- Manifest case count: `240`
- Manifest first case: `hn-20260707-0001`
- Manifest last case: `hn-20260707-0240`

## 4. Remaining case set

- Remaining case count: `184`
- Remaining range: `hn-20260707-0057` → `hn-20260707-0240`
- Remaining IDs exactly expected `hn-20260707-0057` through `hn-20260707-0240`: `True`
- Completed/remaining overlap: `[]`

The resume selection must include only these 184 case IDs and must exclude all 56 already-attempted/completed case IDs.

## 5. Duplicate-call prevention proof

Duplicate-call prevention status: `PASS`

Proof points:

1. Located journal SHA matches the previously preserved locator SHA: `True`.
2. Located journal has exactly 56 JSONL records: `True`.
3. Located journal case IDs exactly match `hn-20260707-0001` through `hn-20260707-0056`: `True`.
4. Approved manifest has exactly 240 cases: `True`.
5. Derived remaining set has exactly 184 cases: `True`.
6. Derived remaining set exactly matches `hn-20260707-0057` through `hn-20260707-0240`: `True`.
7. Completed/remaining overlap is empty: `True`.
8. Completed duplicate case IDs are empty: `True`.

Because the old journal is v1 and lacks repaired raw per-case stdout/stderr capture, it should be treated as completed/attempted authority for duplicate prevention, not as repaired-schema completed-valid evidence. The future resume command must use an explicit remaining-case selection file or harness mode that refuses to select any case already present in the 56-call journal.

## 6. Repaired harness availability and support

- Repaired harness path: `scripts/context_plus_hard_negative_evaluator.py`
- Harness version readback: `context-plus-hard-negative-evaluator 0.2-provider-boundary-repair`
- Required remaining/resume flags present in help: `True`
- Evidence branch: `refs/heads/evidence/context-plus-hard-negative-harness-repair-20260708`
- Evidence commit: `c62f09522b2b22a2d01ac3369c6759324ceb1906`

Required harness capabilities verified from help text:

- `--remaining-only`
- `--resume-from`
- `--dry-run`
- `--execute-approved`
- `--abort-on-provider-path-mismatch`
- `--abort-on-rate-limit`
- `--abort-on-provider-cooldown`
- `--no-route-config-gateway-memory-cache-mutation`

## 7. Proposed resume output path

Proposed future resume output directory:

`sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/hard_negative_remaining_resume_20260708TBD/`

Requirements:

- Must be new/empty before execution.
- Must contain only resumed 184-case evidence.
- Must not overwrite or mutate the located 56-call source journal.
- Must preserve `run_config.json`, case selection plan, duplicate-call prevention report, raw stdout/stderr per resumed case, provider-null taxonomy report, provider boundary report, rate-limit/cooldown report, mutation sentinel report, summary, and journal.

## 8. Proposed final merged output path

Proposed merged output directory after resume completes and before any comparator:

`sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/hard_negative_combined_56_plus_184_20260708TBD/`

Merge/finalization plan:

1. Copy or reference the immutable located 56-call journal with SHA `8ebcceaf8d651929158eb430587963f1407ea5929b7401469bb6226e3d7e0446`.
2. Copy or reference the 184-case resumed production journal from the proposed resume output directory.
3. Verify resumed journal contains exactly `hn-20260707-0057` through `hn-20260707-0240` and no duplicate case IDs.
4. Concatenate/merge into a 240-case production journal in manifest order only after both halves validate.
5. Verify merged production journal has exactly 240 records and case IDs `hn-20260707-0001` through `hn-20260707-0240` exactly once.
6. Preserve merged provider boundary, rate-limit/cooldown, mutation sentinel, and summary reports.
7. Only after preservation and separate approval may comparator be considered.

## 9. Mutation sentinel plan

Future resume execution must require:

- Clean preflight mutation sentinel or explicitly approved baseline.
- Approved output directory limited to the resume output path.
- No dirty/untracked outside-output mutation during execution.
- Abort on mutation sentinel failure.
- Preserve before/after workspace status, filtered outside-output status, mutation detected count, and sentinel classification.
- No route/config/Gateway mutation, memory promotion, provider/model change, production apply, or cache enablement.

## 10. Provider boundary plan

Future resume execution must require:

- transport: `gateway`
- model: `token-broker-vmesh/auto`
- expected provider: `token-broker-vmesh`
- `--max-retries 0`
- `--abort-on-provider-path-mismatch`
- raw stdout/stderr capture for every resumed case
- command failure classified separately from provider mismatch
- provider-null taxonomy report preserved
- stop/abort on provider mismatch, provider-null command failure, missing provider metadata, command failure, timeout, or missing output unless a separate diagnosis plan is approved.

## 11. Rate-limit/cooldown plan

Future resume execution must require:

- `--abort-on-rate-limit`
- `--abort-on-provider-cooldown`
- `--max-retries 0`
- conservative inter-case delay, at least prior harness default unless separately approved
- preserve rate-limit/cooldown report
- abort on any `429`, quota, cooldown, ratelimit, or too-many-requests signal in raw stdout/stderr.

## 12. Exact approval needed for future resume execution

A future resume execution approval must name all of the following exactly:

- Located 56-call journal path: `/tmp/context-plus-hard-negative-eval-clean-worktree-de5800b1/sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/hard_negative_evaluation_clean_worktree_20260708T001800AEST/production_routing/production_routing_journal.jsonl`
- Located 56-call journal SHA256: `8ebcceaf8d651929158eb430587963f1407ea5929b7401469bb6226e3d7e0446`
- Approved manifest path: `/tmp/context-plus-comparator-worktree-20260707/sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/case_manifest.approved.jsonl`
- Approved manifest SHA256: `4f5aaf3a24e68542f05445fe5f6aeab92795883c988fccdcc0490255bee9ebda`
- Completed case exclusion range: `hn-20260707-0001` through `hn-20260707-0056`
- Remaining execution range: `hn-20260707-0057` through `hn-20260707-0240`
- Expected remaining case count: `184`
- Repaired harness commit: `c62f09522b2b22a2d01ac3369c6759324ceb1906`
- Resume output directory: `sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/hard_negative_remaining_resume_20260708TBD/`
- Provider boundary flags, mutation sentinel flags, and rate-limit/cooldown flags
- Explicit statement that duplicate provider calls for cases `0001` through `0056` are forbidden.

No resume execution approval is requested by this plan.

## 13. Explicit non-actions during this planning pass

During creation of this plan:

- No resume execution occurred.
- No evaluation rerun occurred.
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

## 14. Closeout

`PASS_DUPLICATE_SAFE_RESUME_PLAN_READY`

The remaining 184-case resume is concrete and duplicate-safe as a plan: the completed 56-case journal is verified by path/SHA/count/range, the remaining 184-case set is derived exactly from the approved 240-case manifest, completed/remaining overlap is empty, and the repaired harness supports remaining-case execution guardrails. Resume execution remains not approved until this plan is preserved and a separate exact execution approval is granted.
