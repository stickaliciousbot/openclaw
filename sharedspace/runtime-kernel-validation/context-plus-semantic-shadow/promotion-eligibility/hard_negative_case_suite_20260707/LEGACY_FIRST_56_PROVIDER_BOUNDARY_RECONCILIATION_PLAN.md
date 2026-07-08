# Legacy First-56 Provider-Boundary Reconciliation Plan

Classification: `HOLD_FIRST_56_RAW_EVIDENCE_INCOMPLETE`

## Scope and Non-Actions

- Scope: read-only plan for reconciling the legacy first 56-case production fragment against the repaired provider-boundary schema.
- Cases covered: `hn-20260707-0001` → `hn-20260707-0056`.
- Comparator was not run.
- No provider calls occurred.
- No live replay occurred.
- Promotion and M6 remain blocked.
- No post-0240 case execution, route/config/Gateway mutation, memory promotion, provider/model change, production apply, cache enablement, commit, or push occurred.

## Evidence Location

- Exact first-56 evidence path selected: `/tmp/context-plus-hard-negative-eval-clean-worktree-de5800b1/sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/hard_negative_evaluation_clean_worktree_20260708T001800AEST/production_routing`
- Exact journal path selected: `/tmp/context-plus-hard-negative-eval-clean-worktree-de5800b1/sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/hard_negative_evaluation_clean_worktree_20260708T001800AEST/production_routing/production_routing_journal.jsonl`
- Journal SHA256: `8ebcceaf8d651929158eb430587963f1407ea5929b7401469bb6226e3d7e0446`
- Workspace duplicate-safe authority path: `sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/hard_negative_remaining_resume_20260708T083500AEST/preflight/legacy_attempted_authority_56`; exists `True`
- Original clean-worktree production path: `/tmp/context-plus-hard-negative-eval-clean-worktree-de5800b1/sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/hard_negative_evaluation_clean_worktree_20260708T001800AEST/production_routing`; exists `True`

## Available Files

- `/tmp/context-plus-hard-negative-eval-clean-worktree-de5800b1/sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/hard_negative_evaluation_clean_worktree_20260708T001800AEST/closeout_summary.json`; sha256 `a342638428afd9d4f42158477d1bc543721435e2785980b36e354a77a92ff249`
- `/tmp/context-plus-hard-negative-eval-clean-worktree-de5800b1/sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/hard_negative_evaluation_clean_worktree_20260708T001800AEST/production_routing/production_provider_model_call_count_report.json`; sha256 `319cdb60e816ade8baf9a2bcd912e6d2092bb2061bb69bf046c22944f5c8cfc9`
- `/tmp/context-plus-hard-negative-eval-clean-worktree-de5800b1/sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/hard_negative_evaluation_clean_worktree_20260708T001800AEST/production_routing/rate_limit_cooldown_report.json`; sha256 `c1446f4cd2ad723bd0f2da3c42a167d52bf437fb491031bda71aad3e7a063034`
- `/tmp/context-plus-hard-negative-eval-clean-worktree-de5800b1/sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/hard_negative_evaluation_clean_worktree_20260708T001800AEST/production_routing/summary.json`; sha256 `b610cad5941799b8bb52e06ce50013b268d4de3945d87f4d732967add3c045b1`

## Journal Coverage and Duplicate Authority

- Journal row count: `56`
- Cases covered exactly `0001` → `0056`: `true`
- Duplicate case IDs in first-56 journal: `[]`
- Duplicate-safe authority remains valid for selection/exclusion: `true` if the journal SHA/range/count remains unchanged; it does not by itself prove repaired-schema provider verification.

## Raw Evidence Availability

- Raw stdout availability count: `0/56`
- Raw stderr availability count: `0/56`
- Raw stdout+stderr availability count: `0/56`
- Raw calls directory: `/tmp/context-plus-hard-negative-eval-clean-worktree-de5800b1/sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/hard_negative_evaluation_clean_worktree_20260708T001800AEST/production_routing/raw_calls`; exists `False`; directory count `0`

## Provider Metadata Availability

- Provider metadata availability count: `55/56`
- Provider verified/reconstructable count from journal provider field: `55/56`
- Provider missing/null case IDs: `['hn-20260707-0056']`
- Provider mismatch records: `[]`
- Repaired-schema field presence counts: `{"attempt_id": 0, "output_present": 56, "provider_boundary_classification": 0, "provider_path_verified_gateway_token_broker": 56, "raw_stderr_path": 0, "raw_stdout_path": 0, "returncode": 56, "stderr_sha256": 0, "stdout_sha256": 0}`

## Repaired Parser / Schema Readback

- `raw_capture`: `true`
- `provider_verified_class`: `true`
- `command_failure_hold`: `true`
- `provider_missing_hold`: `true`
- `rate_cooldown_source_aware_hint`: `true`
- Repaired taxonomy requirement: command failures/provider-null metadata must be classified as provider-unverified HOLD, not as a provider mismatch.

## Reconstruction Decision

- Repaired-schema provider-boundary fields can be reconstructed read-only for all 56 cases: `false`
- Fragment can be normalized without re-running provider calls: `false`
- Missing/unreconstructable case IDs: `['hn-20260707-0001', 'hn-20260707-0002', 'hn-20260707-0003', 'hn-20260707-0004', 'hn-20260707-0005', 'hn-20260707-0006', 'hn-20260707-0007', 'hn-20260707-0008', 'hn-20260707-0009', 'hn-20260707-0010', 'hn-20260707-0011', 'hn-20260707-0012', 'hn-20260707-0013', 'hn-20260707-0014', 'hn-20260707-0015', 'hn-20260707-0016', 'hn-20260707-0017', 'hn-20260707-0018', 'hn-20260707-0019', 'hn-20260707-0020', 'hn-20260707-0021', 'hn-20260707-0022', 'hn-20260707-0023', 'hn-20260707-0024', 'hn-20260707-0025', 'hn-20260707-0026', 'hn-20260707-0027', 'hn-20260707-0028', 'hn-20260707-0029', 'hn-20260707-0030', 'hn-20260707-0031', 'hn-20260707-0032', 'hn-20260707-0033', 'hn-20260707-0034', 'hn-20260707-0035', 'hn-20260707-0036', 'hn-20260707-0037', 'hn-20260707-0038', 'hn-20260707-0039', 'hn-20260707-0040', 'hn-20260707-0041', 'hn-20260707-0042', 'hn-20260707-0043', 'hn-20260707-0044', 'hn-20260707-0045', 'hn-20260707-0046', 'hn-20260707-0047', 'hn-20260707-0048', 'hn-20260707-0049', 'hn-20260707-0050', 'hn-20260707-0051', 'hn-20260707-0052', 'hn-20260707-0053', 'hn-20260707-0054', 'hn-20260707-0055', 'hn-20260707-0056']`
- Cases requiring HOLD instead of reconstruction: `['hn-20260707-0001', 'hn-20260707-0002', 'hn-20260707-0003', 'hn-20260707-0004', 'hn-20260707-0005', 'hn-20260707-0006', 'hn-20260707-0007', 'hn-20260707-0008', 'hn-20260707-0009', 'hn-20260707-0010', 'hn-20260707-0011', 'hn-20260707-0012', 'hn-20260707-0013', 'hn-20260707-0014', 'hn-20260707-0015', 'hn-20260707-0016', 'hn-20260707-0017', 'hn-20260707-0018', 'hn-20260707-0019', 'hn-20260707-0020', 'hn-20260707-0021', 'hn-20260707-0022', 'hn-20260707-0023', 'hn-20260707-0024', 'hn-20260707-0025', 'hn-20260707-0026', 'hn-20260707-0027', 'hn-20260707-0028', 'hn-20260707-0029', 'hn-20260707-0030', 'hn-20260707-0031', 'hn-20260707-0032', 'hn-20260707-0033', 'hn-20260707-0034', 'hn-20260707-0035', 'hn-20260707-0036', 'hn-20260707-0037', 'hn-20260707-0038', 'hn-20260707-0039', 'hn-20260707-0040', 'hn-20260707-0041', 'hn-20260707-0042', 'hn-20260707-0043', 'hn-20260707-0044', 'hn-20260707-0045', 'hn-20260707-0046', 'hn-20260707-0047', 'hn-20260707-0048', 'hn-20260707-0049', 'hn-20260707-0050', 'hn-20260707-0051', 'hn-20260707-0052', 'hn-20260707-0053', 'hn-20260707-0054', 'hn-20260707-0055', 'hn-20260707-0056']`
- Local-only normalization required/possible: `false`
- Live replay required later: `true`
- Live replay reason: first-56 preserved evidence lacks complete raw stdout/stderr and/or provider metadata needed to reconstruct repaired-schema provider-boundary evidence for every case. Any live replay would duplicate or replace legacy provider-call evidence and therefore requires separate explicit approval/disposition.

## Boundary Reconciliation Outlook

- Mutation boundary for first 56 can be reconciled read-only from available summaries/status: `needs_local_summary_review`
- Rate/cooldown boundary for first 56 can be reconciled read-only from available summaries/status: `true`
- Fallback/model boundary for first 56: requires local journal/schema review; no live calls are needed for planning, but repaired-schema normalization cannot assert full provider-boundary PASS unless raw/provider metadata is complete.
- Comparator readiness after proposed plan: `NOT_READY_WITHOUT_SEPARATE_LIVE_REPLAY_OR_DISPOSITION_APPROVAL`

## Proposed Next Step

1. Preserve this plan.
2. Decide separately whether to authorize a live replay/disposition for the first-56 blocker; do not normalize as PASS from incomplete evidence.
3. Comparator remains blocked until first-56 provider-boundary reconciliation is complete or explicitly dispositioned.

## Closeout

- Closeout classification: `HOLD_FIRST_56_RAW_EVIDENCE_INCOMPLETE`
- Exact first-56 evidence path: `/tmp/context-plus-hard-negative-eval-clean-worktree-de5800b1/sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/hard_negative_evaluation_clean_worktree_20260708T001800AEST/production_routing`
- Cases covered: `hn-20260707-0001` → `hn-20260707-0056`
- Raw stdout/stderr availability count: `0/56`
- Provider metadata availability count: `55/56`
- Provider verified/reconstructable count: `55/56`
- Missing/unreconstructable case IDs: `['hn-20260707-0001', 'hn-20260707-0002', 'hn-20260707-0003', 'hn-20260707-0004', 'hn-20260707-0005', 'hn-20260707-0006', 'hn-20260707-0007', 'hn-20260707-0008', 'hn-20260707-0009', 'hn-20260707-0010', 'hn-20260707-0011', 'hn-20260707-0012', 'hn-20260707-0013', 'hn-20260707-0014', 'hn-20260707-0015', 'hn-20260707-0016', 'hn-20260707-0017', 'hn-20260707-0018', 'hn-20260707-0019', 'hn-20260707-0020', 'hn-20260707-0021', 'hn-20260707-0022', 'hn-20260707-0023', 'hn-20260707-0024', 'hn-20260707-0025', 'hn-20260707-0026', 'hn-20260707-0027', 'hn-20260707-0028', 'hn-20260707-0029', 'hn-20260707-0030', 'hn-20260707-0031', 'hn-20260707-0032', 'hn-20260707-0033', 'hn-20260707-0034', 'hn-20260707-0035', 'hn-20260707-0036', 'hn-20260707-0037', 'hn-20260707-0038', 'hn-20260707-0039', 'hn-20260707-0040', 'hn-20260707-0041', 'hn-20260707-0042', 'hn-20260707-0043', 'hn-20260707-0044', 'hn-20260707-0045', 'hn-20260707-0046', 'hn-20260707-0047', 'hn-20260707-0048', 'hn-20260707-0049', 'hn-20260707-0050', 'hn-20260707-0051', 'hn-20260707-0052', 'hn-20260707-0053', 'hn-20260707-0054', 'hn-20260707-0055', 'hn-20260707-0056']`
- Local-only normalization possible: `false`
- Live replay required: `true`
- Comparator readiness after proposed plan: `NOT_READY_WITHOUT_SEPARATE_LIVE_REPLAY_OR_DISPOSITION_APPROVAL`
- Comparator was not run.
- No provider calls occurred.
- Promotion and M6 remain blocked.
