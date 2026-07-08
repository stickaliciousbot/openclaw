# Missing Production Authority Repair — hn-20260707-0133 / 0184 / 0196

Date: 2026-07-09 AEST

## Classification

`HOLD_CASE_0133_AUTHORITY_MISSING`

Secondary blocker: `HOLD_REPLAY_REQUIRED_BUT_NOT_APPROVED`

## Scope and Safety

Approved scope was limited to read-only inspection of preserved production evidence for exactly:

- `hn-20260707-0133`
- `hn-20260707-0184`
- `hn-20260707-0196`

No replay was run. No Gateway/model/provider calls were run. No comparator was run. No promotion/M6 proposal was created. No production apply, route/config/Gateway mutation, memory promotion, provider/model change, or cache enablement was performed.

## Executive Result

The missing-production-authority index is partially repairable from preserved evidence, but it does **not** close PASS because `hn-20260707-0133` lacks a preserved post-run mutation-sentinel report.

- `hn-20260707-0184`: comparator-authoritative under repaired/source-aware rate-cooldown schema.
- `hn-20260707-0196`: comparator-authoritative under repaired/source-aware rate-cooldown schema.
- `hn-20260707-0133`: not comparator-authoritative yet because the preserved run has provider/raw/metadata/duplicate/rate evidence, but no post-run mutation-sentinel report was found; only a preflight baseline and `mutation_performed=false` fields were found.

Therefore aggregate comparator-readiness remains blocked and the hard-negative comparator must not be rerun from this repair state.

## Required Gates

| Gate | hn-20260707-0133 | hn-20260707-0184 | hn-20260707-0196 |
| --- | --- | --- | --- |
| Provider verified | PASS | PASS | PASS |
| Raw stdout/stderr available | PASS | PASS | PASS |
| Provider metadata available | PASS | PASS | PASS |
| Duplicate-safe | PASS | PASS | PASS |
| Fallback/model boundary clean | PASS | PASS | PASS |
| Rate/cooldown boundary clean under repaired parser | PASS_REPAIRED_SCHEMA | PASS_REPAIRED_SCHEMA | PASS_REPAIRED_SCHEMA |
| Mutation sentinel clean | HOLD_MISSING_POST_SENTINEL | PASS | PASS |
| Comparator-authoritative | NO | YES | YES |

## Case Index

### hn-20260707-0133

Status: `HOLD_CASE_0133_AUTHORITY_MISSING`

Preserved evidence source:

- Run: `hard_negative_remaining_resume_20260708T083500AEST`
- Journal: `hard_negative_remaining_resume_20260708T083500AEST/production_routing_journal.v2.jsonl`
- Journal record: line 77 / case sequence 77
- Raw stdout: `hard_negative_remaining_resume_20260708T083500AEST/raw_calls/0077_hn-20260707-0133_attempt-0001/child_stdout.raw`
- Raw stderr: `hard_negative_remaining_resume_20260708T083500AEST/raw_calls/0077_hn-20260707-0133_attempt-0001/child_stderr.raw`
- Provider report: `hard_negative_remaining_resume_20260708T083500AEST/production_provider_model_call_count_report.json`
- Rate/cooldown report: `hard_negative_remaining_resume_20260708T083500AEST/rate_limit_cooldown_report.json`
- Duplicate report: `hard_negative_remaining_resume_20260708T083500AEST/duplicate_call_prevention_report.json`
- Preflight mutation baseline: `hard_negative_remaining_resume_20260708T083500AEST/preflight/mutation_sentinel_preflight.json`
- Run config: `hard_negative_remaining_resume_20260708T083500AEST/run_config.json`

Observed authority facts:

- Provider boundary: `PASS_PROVIDER_VERIFIED`
- Provider: `token-broker-vmesh`
- Provider path verified gateway token broker: `true`
- Return code: `0`
- Timed out: `false`
- Output present: `true`
- Raw stdout JSON parse: available and valid; top-level `ok: true`, `transport: gateway`, `provider: token-broker-vmesh`, `model: auto`, `attempts: []`, `outputs[]` present.
- Raw stderr: empty by journal metadata (`stderr_bytes: 0`, sha256 empty-stream hash).
- Duplicate call prevention: `PASS_DUPLICATE_CALL_PREVENTION_READY`; duplicate case IDs `[]`.
- Run config model: `token-broker-vmesh/auto`; expected provider `token-broker-vmesh`; no route/config/Gateway/memory/cache mutation flag set.
- Old rate/cooldown report: `HOLD_RATE_LIMIT_OR_COOLDOWN` for this case.
- Repaired-schema rate/cooldown interpretation: clean. The matching text appears only inside generated `outputs[].text` as historical evidence text (`rate-limit/cooldown events 0`), not as provider/system/transport metadata. The repaired source-aware parser ignores generated answer text and scans provider/system metadata surfaces.

Authority gap:

- No preserved post-run `mutation_sentinel_report.json` was found for `hard_negative_remaining_resume_20260708T083500AEST`.
- Preserved evidence includes only `preflight/mutation_sentinel_preflight.json` with `PASS_MUTATION_SENTINEL_BASELINE_RECORDED`, mode `approved_baseline_due_existing_workspace_noise`, and per-record/run fields showing `mutation_performed=false`.
- Because the requested authority gate explicitly requires mutation sentinel clean, this repair does not mark `hn-20260707-0133` comparator-authoritative.

Required next action for this case:

- Prefer locating an already-preserved post-run mutation sentinel or equivalent closeout proof for the 083500 run before considering replay.
- If no such preserved proof exists, the case remains blocked as `HOLD_REPLAY_REQUIRED_BUT_NOT_APPROVED`; replay/provider calls are not approved by this artifact.

### hn-20260707-0184

Status: `PASS_REPAIRED_SCHEMA_AUTHORITY`

Preserved evidence source:

- Run: `hard_negative_micro_batch_12_timeout_retry_20260708T1736AEST`
- Summary: `hard_negative_micro_batch_12_timeout_retry_20260708T1736AEST/summary.json`
- Journal: `hard_negative_micro_batch_12_timeout_retry_20260708T1736AEST/terminal_production_routing_journal.v2.jsonl`
- Raw parse result: `hard_negative_micro_batch_12_timeout_retry_20260708T1736AEST/raw_calls/0001_hn-20260707-0184_attempt-0001/parse_result.json`
- Raw stdout: `hard_negative_micro_batch_12_timeout_retry_20260708T1736AEST/raw_calls/0001_hn-20260707-0184_attempt-0001/child_stdout.raw`
- Raw stderr: `hard_negative_micro_batch_12_timeout_retry_20260708T1736AEST/raw_calls/0001_hn-20260707-0184_attempt-0001/child_stderr.raw`
- Provider report: `hard_negative_micro_batch_12_timeout_retry_20260708T1736AEST/production_provider_model_call_count_report.json`
- Old rate/cooldown report: `hard_negative_micro_batch_12_timeout_retry_20260708T1736AEST/rate_limit_cooldown_report.json`
- Mutation sentinel: `hard_negative_micro_batch_12_timeout_retry_20260708T1736AEST/mutation_sentinel_report.json`
- Duplicate report: `hard_negative_micro_batch_12_timeout_retry_20260708T1736AEST/duplicate_call_prevention_report.json`
- Diagnosis: `MB12_RATE_COOLDOWN_DIAGNOSIS.md`
- Parser repair validation: `rate_cooldown_parser_repair_mb14_validation_20260708/validation_summary.json`
- Parser repair implementation: `MB14_RATE_COOLDOWN_PARSER_REPAIR_IMPLEMENTATION.md`

Observed authority facts:

- Provider report: `PASS_PROVIDER_CALL_BOUNDARY`; provider verified count `1`; provider mismatch count `0`; command failure count `0`; timeout count `0`.
- Journal/parse result: `PASS_PROVIDER_VERIFIED`, provider `token-broker-vmesh`, requested model `token-broker-vmesh/auto`, return code `0`, timed out `false`, output present, stdout JSON parse OK, stderr decode OK.
- Raw stdout: valid JSON with `ok: true`, `transport: gateway`, `provider: token-broker-vmesh`, `model: auto`, `attempts: []`, `outputs[]` present.
- Raw stderr: empty by metadata.
- Duplicate scope: `PASS_OWNER_APPROVED_DUPLICATE_SCOPE_BOUNDARY`; selected cases exactly `0184`→`0188` and no prior attempted case IDs in scope.
- Mutation sentinel: summary and report classify `PASS_MUTATION_SENTINEL_OUTSIDE_OUTPUT_UNCHANGED`.
- Old rate/cooldown report held because the prior parser matched bare `429` inside an example SHA hash.
- Diagnosis concluded this was parser false positive, not provider cooldown.
- Repaired parser validation explicitly includes `mb12_hn0184_saved_output_no_rate_cooldown` and classifies `PASS_PARSER_REPAIR_VALIDATION` with provider/Gateway/model calls `0`.

Conclusion:

`hn-20260707-0184` is comparator-authoritative under the repaired/source-aware schema and should be indexed from the preserved MB12 attempt, not replayed.

### hn-20260707-0196

Status: `PASS_REPAIRED_SCHEMA_AUTHORITY`

Preserved evidence source:

- Run: `hard_negative_micro_batch_14_after_parser_repair_20260708T1833AEST`
- Summary: `hard_negative_micro_batch_14_after_parser_repair_20260708T1833AEST/summary.json`
- Raw parse result: `hard_negative_micro_batch_14_after_parser_repair_20260708T1833AEST/raw_calls/0003_hn-20260707-0196_attempt-0001/parse_result.json`
- Raw stdout: `hard_negative_micro_batch_14_after_parser_repair_20260708T1833AEST/raw_calls/0003_hn-20260707-0196_attempt-0001/child_stdout.raw`
- Raw stderr: `hard_negative_micro_batch_14_after_parser_repair_20260708T1833AEST/raw_calls/0003_hn-20260707-0196_attempt-0001/child_stderr.raw`
- Provider report: `hard_negative_micro_batch_14_after_parser_repair_20260708T1833AEST/production_provider_model_call_count_report.json`
- Old rate/cooldown report: `hard_negative_micro_batch_14_after_parser_repair_20260708T1833AEST/rate_limit_cooldown_report.json`
- Mutation sentinel: `hard_negative_micro_batch_14_after_parser_repair_20260708T1833AEST/mutation_sentinel_report.json`
- Duplicate report: `hard_negative_micro_batch_14_after_parser_repair_20260708T1833AEST/duplicate_call_prevention_report.json`
- Diagnosis: `MB14_RATE_COOLDOWN_DIAGNOSIS.md`
- Parser repair validation: `rate_cooldown_parser_repair_mb14_validation_20260708/validation_summary.json`
- Parser repair implementation: `MB14_RATE_COOLDOWN_PARSER_REPAIR_IMPLEMENTATION.md`

Observed authority facts:

- Provider report: `PASS_PROVIDER_CALL_BOUNDARY`; provider verified count `3`; provider mismatch count `0`; command failure count `0`; timeout count `0`.
- Parse result: `PASS_PROVIDER_VERIFIED`, provider `token-broker-vmesh`, requested model `token-broker-vmesh/auto`, return code `0`, timed out `false`, output present, stdout JSON parse OK, stderr decode OK.
- Raw stdout: valid JSON with `ok: true`, `transport: gateway`, `provider: token-broker-vmesh`, `model: auto`, `attempts: []`, `outputs[]` present.
- Raw stderr: empty by metadata.
- Duplicate boundary: `PASS_DUPLICATE_CALL_PREVENTION_BOUNDARY`; attempted case IDs `0194`, `0195`, `0196`; existing attempts `[]`; selected cases `0194`→`0198`; completed excluded case `0184`.
- Mutation sentinel: summary and report classify `PASS_MUTATION_SENTINEL_OUTSIDE_OUTPUT_UNCHANGED`.
- Old rate/cooldown report held because the prior parser matched `retry after` inside generated answer text: `safe_next=retry after tool path check`.
- Diagnosis concluded this was parser false positive, not provider/system cooldown.
- Repaired parser validation includes `generated_outputs_retry_after_no_trigger` and classifies `PASS_PARSER_REPAIR_VALIDATION` with provider/Gateway/model calls `0`.

Conclusion:

`hn-20260707-0196` is comparator-authoritative under the repaired/source-aware schema and should be indexed from the preserved MB14 attempt, not replayed.

## Comparator Readiness Decision

Do **not** rerun aggregate comparator-readiness yet.

Reason: all three missing IDs must close comparator-authoritative before readiness may be rerun. `hn-20260707-0133` remains blocked on missing post-run mutation-sentinel proof.

## Comparator / M6 / Production State

- Aggregate comparator-readiness: `BLOCKED_NOT_RUN`
- Hard-negative comparator: `BLOCKED_NOT_RUN`
- M6 production proposal: `BLOCKED_NOT_RUN`
- Production apply: `NOT_APPROVED / BLOCKED_NOT_RUN`

## Preservation Scope

This artifact is the only file intended for selective preservation in this step:

`sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/MISSING_PRODUCTION_AUTHORITY_0133_0184_0196_REPAIR.md`
