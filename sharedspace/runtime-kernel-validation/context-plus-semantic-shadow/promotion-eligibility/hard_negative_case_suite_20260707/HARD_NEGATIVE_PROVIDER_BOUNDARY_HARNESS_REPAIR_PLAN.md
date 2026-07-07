# Hard-Negative Provider Boundary Harness Repair Plan

Classification: `PASS_REPAIR_PLAN_READY`

Scope: minimal harness repair plan only. This document does not authorize, perform, resume, or rerun any hard-negative evaluation.

## 1. Exact failure summary

- Stop case: `hn-20260707-0056`.
- Observed classification before this plan: `HOLD_PROVIDER_NULL_EVIDENCE_INCOMPLETE`.
- Observed child command result preserved in existing journal/diagnosis:
  - `returncode`: `1`
  - `provider`: `null`
  - `provider_path_verified_gateway_token_broker`: `false`
  - `output_present`: `false`
  - output excerpt: empty
  - provider/model call count at stop: `56`
- Raw per-case child `stdout` and `stderr` were not persisted.
- The existing harness captured the subprocess output in memory, parsed `proc.stdout`, wrote only summary fields/excerpts to the journal, and classified `provider != expected_provider` as a provider boundary failure even when the command itself failed.
- Exact root cause cannot be proven from preserved evidence. Plausible causes include command/Gateway/CLI failure, timeout-like wrapper behavior, empty stdout, invalid JSON, missing provider metadata, prompt rejection, or parser/schema edge case.
- Because provider calls may already have been made for cases up to and including `hn-20260707-0056`, the harness must not resume or rerun from existing evidence without duplicate-call prevention.

## 2. Evidence gaps

Required evidence that is missing from the failed attempt:

1. Exact raw child `stdout` bytes for `hn-20260707-0056`.
2. Exact raw child `stderr` bytes for `hn-20260707-0056`.
3. Raw output SHA-256 hashes and byte counts.
4. Parse-stage evidence: whether stdout was empty, invalid JSON, valid JSON missing provider, or valid JSON with non-matching provider.
5. Command-failure evidence separated from provider mismatch evidence.
6. Attempt lifecycle evidence proving whether a case was only selected, command-started, command-returned, parsed, provider-verified, and scored.
7. Resume eligibility evidence proving which case IDs are safe to skip, which are safe to execute as remaining cases, and which are blocked because a provider call may already have occurred.
8. Duplicate-call refusal evidence.

## 3. Minimal raw stdout/stderr capture design

Repair the production-routing path only. Do not alter comparator semantics except to consume the repaired journal/report fields.

For every case attempt, create a per-attempt directory before invoking the child command:

```text
<out_dir>/raw_calls/<seq>_<case_id>_<attempt_id>/
  attempt_started.json
  child_stdout.raw
  child_stderr.raw
  child_outputs.sha256.json
  parse_result.json
  attempt_completed.json
```

Required behavior:

1. `attempt_started.json` is written atomically before the child command starts.
2. `attempt_id` is deterministic within the run, e.g. `<run_id>:<seq>:<case_id>:attempt-0001`, and included in every journal row.
3. Store raw `stdout` and `stderr` exactly as received from the child process, as bytes if possible; text decoding is a derived parse step, not the primary evidence.
4. Immediately write `child_outputs.sha256.json` with:
   - `stdout_sha256`
   - `stderr_sha256`
   - `stdout_bytes`
   - `stderr_bytes`
   - `stdout_present`
   - `stderr_present`
5. `parse_result.json` records the parse decision without destroying raw evidence:
   - `stdout_text_decode_ok`
   - `stdout_json_parse_ok`
   - `stdout_json_top_level_type`
   - `stdout_json_keys` when object
   - `provider_field_present`
   - `provider_raw_value`
   - `provider_normalized`
   - `output_text_present`
   - `parse_error_type` / `parse_error_excerpt`
6. The production journal row includes raw file paths and hashes, not only excerpts.
7. Excerpts may remain bounded/redacted for human reports, but raw local files are the authority for diagnosis.
8. If writing raw capture fails, abort before any further provider call and classify `FAIL_RAW_CAPTURE_UNAVAILABLE`.

## 4. Command-failure vs provider-mismatch classification design

Provider comparison must occur only after the child command is proven successful enough to support provider metadata.

Required precedence order for each case:

1. **Harness/local setup failure**
   - Example: cannot create attempt directory, cannot write raw capture, manifest mismatch.
   - Classification: `FAIL_HARNESS_LOCAL_EVIDENCE_CAPTURE_FAILURE`.
   - Provider comparison: not attempted.

2. **Child command timeout**
   - Example: `subprocess.TimeoutExpired`.
   - Classification: `HOLD_COMMAND_TIMEOUT_PROVIDER_UNVERIFIED`.
   - Provider comparison: not attempted.

3. **Child command failure**
   - Condition: `returncode != 0`.
   - Classification: `HOLD_COMMAND_FAILURE_PROVIDER_UNVERIFIED`.
   - Provider comparison: not attempted, even if stdout contains partial JSON.

4. **Child command success but stdout empty**
   - Condition: `returncode == 0`, stdout byte count `0`.
   - Classification: `HOLD_EMPTY_STDOUT_PROVIDER_UNVERIFIED`.
   - Provider comparison: not attempted.

5. **Child command success but stdout invalid JSON**
   - Condition: `returncode == 0`, stdout non-empty, JSON parse fails.
   - Classification: `HOLD_INVALID_JSON_PROVIDER_UNVERIFIED`.
   - Provider comparison: not attempted.

6. **Child command success, valid JSON, provider missing/null**
   - Classification: `HOLD_PROVIDER_METADATA_MISSING_PROVIDER_UNVERIFIED`.
   - Provider comparison: not a mismatch.

7. **Child command success, valid JSON, provider present and different**
   - Classification: `FAIL_PROVIDER_MISMATCH`.
   - Provider comparison: valid.

8. **Child command success, valid JSON, expected provider present**
   - Classification: `PASS_PROVIDER_VERIFIED`.
   - Scoring may proceed.

Suite-level provider boundary report must count these separately:

- `command_failure_count`
- `timeout_count`
- `empty_stdout_count`
- `invalid_json_count`
- `provider_metadata_missing_count`
- `provider_mismatch_count`
- `provider_verified_count`

`FAIL_PROVIDER_CALL_BOUNDARY` is reserved for proven provider mismatch or proven provider-boundary bypass. Command failures and provider-null metadata gaps are `HOLD_*`, not `FAIL_PROVIDER_MISMATCH`.

## 5. Provider-null classification taxonomy

Use these provider-null classes in `provider_null_taxonomy_report.json`:

| Class | Required condition | Boundary meaning | Default action |
|---|---|---|---|
| `PROVIDER_NULL_COMMAND_FAILURE_EMPTY_STDOUT` | `returncode != 0`, stdout empty | Provider path unverified; not mismatch | HOLD, stop |
| `PROVIDER_NULL_COMMAND_FAILURE_WITH_STDERR` | `returncode != 0`, stderr non-empty | Command failed; stderr is diagnostic authority | HOLD, stop |
| `PROVIDER_NULL_COMMAND_FAILURE_WITH_STDOUT_NONJSON` | `returncode != 0`, stdout non-empty but non-JSON | Command failed before reliable provider parse | HOLD, stop |
| `PROVIDER_NULL_TIMEOUT` | timeout raised | Unknown command/provider state | HOLD, stop |
| `PROVIDER_NULL_SUCCESS_EMPTY_STDOUT` | `returncode == 0`, stdout empty | Wrapper/output contract failure | HOLD, stop |
| `PROVIDER_NULL_SUCCESS_INVALID_JSON` | `returncode == 0`, stdout invalid JSON | Output contract failure | HOLD, stop |
| `PROVIDER_NULL_SUCCESS_JSON_MISSING_PROVIDER` | valid JSON object but no provider key | Metadata schema failure | HOLD, stop |
| `PROVIDER_NULL_SUCCESS_JSON_PROVIDER_NULL` | provider key exists but value null/empty | Metadata schema failure | HOLD, stop |
| `PROVIDER_NULL_RATE_OR_COOLDOWN_SIGNAL` | raw stdout/stderr contains rate/cooldown/quota markers | Provider availability boundary, not mismatch | HOLD, stop |
| `PROVIDER_NULL_LOCAL_PARSE_SCHEMA_GAP` | raw JSON contains provider only in an unsupported nested location | Harness parser gap | HOLD, repair parser before eval |
| `PROVIDER_NULL_UNKNOWN` | none of the above can be proven | Evidence incomplete | HOLD, no resume/rerun without approval |

## 6. Safe resume design

Safe resume must be based on a completed-journal validation pass, not on `max_cases`, line count, or provider call count alone.

Add a zero-provider-call subcommand or mode:

```text
validate-resume --manifest <manifest> --out-dir <existing_run_dir> --expected-provider token-broker-vmesh --out-json resume_eligibility_report.json
```

A case is `completed_valid` only if all are true:

1. Case ID exists exactly once in the manifest and exactly once in the production journal.
2. `visible_user_text_sha256` matches the manifest.
3. `attempt_started.json`, raw stdout, raw stderr, hash file, parse result, and completed row all exist.
4. Raw file hashes match the journal and hash report.
5. `returncode == 0`.
6. JSON parse succeeded.
7. `provider == expected_provider`.
8. `provider_path_verified_gateway_token_broker == true`.
9. Output text was present and scored.
10. No rate/cooldown marker was detected.
11. `mutation_performed == false`.

A case is `attempted_blocked` if `attempt_started.json` exists but the case is not `completed_valid`. This includes `hn-20260707-0056` in any repaired import of the failed run unless raw evidence proves otherwise.

Resume rules:

- Default: refuse resume if any `attempted_blocked` case exists before the requested resume boundary.
- Do not re-execute `completed_valid` cases.
- Do not re-execute `attempted_blocked` cases by default, because a provider call may already have occurred.
- If a previous run lacks raw capture, classify all previously executed/attempted cases as `legacy_attempt_without_raw_capture`; they are not resume-safe for duplicate-free execution.
- Existing `hn-20260707-0056` remains a barrier for full comparable evaluation unless explicitly handled under a separate owner-approved rerun/fresh-run decision.

## 7. Duplicate-call prevention design

Before any future provider call, the harness must build a duplicate-prevention ledger:

```text
<out_dir>/duplicate_call_prevention_report.json
```

Required checks:

1. Manifest hash matches the approved hash.
2. Output directory is either new or explicitly opened in `--remaining-only` mode.
3. For every selected case, no prior `attempt_started.json` exists in this run directory.
4. For every selected case, no prior journal row exists in this run directory.
5. For remaining-case mode, selected case IDs must be exactly the computed `remaining_unattempted_case_ids` from `resume_eligibility_report.json`.
6. If any case has `attempt_started` without `completed_valid`, the harness must not silently retry it.
7. Any mode that would intentionally duplicate prior provider calls must require a separate explicit flag and a separate owner approval artifact naming:
   - old run ID
   - old attempted case IDs
   - duplicate case IDs
   - reason duplication is accepted
   - new run ID/output dir

No such duplicate approval is granted by this repair plan.

## 8. Remaining-case execution design

Add a future execution mode only after local repair validation passes:

```text
run-production-routing --remaining-only --resume-from <existing_run_dir> --out-dir <new_or_same_run_dir> ...
```

Remaining-case selection:

1. Run `validate-resume` first.
2. Compute:
   - `completed_valid_case_ids`
   - `attempted_blocked_case_ids`
   - `remaining_unattempted_case_ids`
3. Refuse by default if `attempted_blocked_case_ids` is non-empty and the requested output is a full comparable evaluation.
4. If allowed to continue with non-comparable remaining-only evidence, execute only `remaining_unattempted_case_ids`, never `completed_valid` or `attempted_blocked`.
5. Write `remaining_case_execution_plan.json` before execution with exact case IDs and hashes.
6. Abort before first provider call if selected case IDs differ from the plan.
7. Final summary must clearly classify whether evidence is full comparable, partial non-comparable, or blocked.

For the current failed attempt, a duplicate-free remaining-only run could at most gather evidence for cases that have no prior attempt. It would not repair the missing evidence for `hn-20260707-0056` and therefore would not by itself produce a complete comparable 240-case evaluation.

## 9. Fresh-rerun fallback design

Fresh rerun is not authorized by this plan.

Future fresh-rerun safeguards, if separately approved:

1. Refuse to use the old output directory.
2. Require a new `run_id` and new output directory.
3. Require an owner approval artifact explicitly acknowledging that any repeated case IDs from the aborted run are duplicate provider calls.
4. Require the repaired harness local validation report to pass before approval can be used.
5. Require `--fresh-rerun-approved` plus `--execute-approved`; either flag alone is insufficient.
6. Write `fresh_rerun_safety_readback.json` before first provider call, including:
   - prior run ID/path
   - prior attempted case IDs
   - duplicate case count
   - new run ID/path
   - approval artifact path/hash
   - no route/config/Gateway/model/provider/cache/memory mutation flags
7. Abort if approval artifact does not exactly match selected duplicate case IDs.
8. Abort if any route/config/Gateway/model/provider/cache/memory mutation is detected.

## 10. Required validation tests

All repair-validation tests must be local/offline and must make zero Gateway/model/provider calls.

Required tests:

1. Python compile/import test for the repaired harness.
2. CLI help test for all new/changed subcommands.
3. Manifest validation fixture test.
4. Raw capture fixture test using a fake child command that returns `0` with valid provider JSON.
5. Command failure fixture: fake child returns `1`, empty stdout, diagnostic stderr; expected classification `HOLD_COMMAND_FAILURE_PROVIDER_UNVERIFIED` and provider mismatch count `0`.
6. Invalid JSON fixture: fake child returns `0`, stdout non-JSON; expected `HOLD_INVALID_JSON_PROVIDER_UNVERIFIED`.
7. Missing provider fixture: fake child returns `0`, valid JSON without provider; expected `HOLD_PROVIDER_METADATA_MISSING_PROVIDER_UNVERIFIED`.
8. Provider mismatch fixture: fake child returns `0`, valid JSON with wrong provider; expected `FAIL_PROVIDER_MISMATCH`.
9. Provider verified fixture: fake child returns `0`, valid JSON with `token-broker-vmesh`; expected `PASS_PROVIDER_VERIFIED`.
10. Timeout fixture: fake child simulates timeout; expected `HOLD_COMMAND_TIMEOUT_PROVIDER_UNVERIFIED`.
11. Resume validation fixture with:
    - completed-valid cases
    - duplicate journal row
    - missing raw stdout
    - hash mismatch
    - attempted-started without completion
12. Duplicate prevention fixture proving the harness refuses to select already attempted case IDs.
13. Remaining-only fixture proving selected cases equal `remaining_unattempted_case_ids` exactly.
14. Fresh-rerun safeguard fixture proving rerun is refused without explicit duplicate approval artifact.
15. Zero-provider-call sentinel proving validation tests do not invoke `openclaw infer model run`.

## 11. Required evidence outputs

The repaired harness must produce these outputs before any future evaluation result can be trusted:

```text
run_config.json
manifest_validation_report.json
case_selection_plan.json
raw_calls/<seq>_<case_id>_<attempt_id>/attempt_started.json
raw_calls/<seq>_<case_id>_<attempt_id>/child_stdout.raw
raw_calls/<seq>_<case_id>_<attempt_id>/child_stderr.raw
raw_calls/<seq>_<case_id>_<attempt_id>/child_outputs.sha256.json
raw_calls/<seq>_<case_id>_<attempt_id>/parse_result.json
raw_calls/<seq>_<case_id>_<attempt_id>/attempt_completed.json
production_routing_journal.v2.jsonl
production_provider_model_call_count_report.json
provider_null_taxonomy_report.json
command_failure_report.json
rate_limit_cooldown_report.json
resume_eligibility_report.json
duplicate_call_prevention_report.json
remaining_case_execution_plan.json  # when applicable
fresh_rerun_safety_readback.json    # only when separately approved
mutation_sentinel_report.json
summary.json
```

Minimum required journal v2 fields per row:

- `schema`
- `run_id`
- `attempt_id`
- `case_id`
- `case_sequence`
- `visible_user_text_sha256`
- `raw_stdout_path`
- `raw_stderr_path`
- `stdout_sha256`
- `stderr_sha256`
- `stdout_bytes`
- `stderr_bytes`
- `returncode`
- `command_status_classification`
- `provider_null_classification`
- `provider`
- `expected_provider`
- `provider_boundary_classification`
- `provider_path_verified_gateway_token_broker`
- `output_present`
- `false_positive`
- `false_positive_reasons`
- `gateway_model_provider_calls`
- `mutation_performed`

## 12. Pass/Hold/Fail criteria for repaired harness

### Harness repair local validation

- `PASS_HARNESS_REPAIR_LOCAL_VALIDATED` only if:
  - all offline fixture tests pass;
  - raw stdout/stderr capture is proven for every fixture attempt;
  - command failure and provider mismatch are classified separately;
  - provider-null taxonomy report is generated;
  - resume validation identifies completed, blocked, and remaining cases correctly;
  - duplicate-call prevention refuses duplicate selected cases;
  - fresh rerun is refused without explicit duplicate approval;
  - zero Gateway/model/provider calls are made during repair validation;
  - no route/config/Gateway/model/provider/cache/memory mutation occurs.

- `HOLD_HARNESS_REPAIR_VALIDATION_INCOMPLETE` if:
  - any fixture/evidence output is missing;
  - resume eligibility cannot be proven;
  - provider-null classification is ambiguous;
  - old legacy evidence without raw capture is needed for a full result.

- `FAIL_HARNESS_REPAIR_UNSAFE` if:
  - validation invokes real provider/model/Gateway calls;
  - the harness can rerun an attempted case without explicit duplicate approval;
  - command failure is still counted as provider mismatch;
  - raw capture can fail silently;
  - any route/config/Gateway/model/provider/cache/memory mutation occurs.

### Future hard-negative evaluation eligibility

A future evaluation attempt remains blocked until repaired-harness local validation passes and a separate owner approval explicitly authorizes the exact execution mode.

- Full comparable evaluation requires every manifest case to have `completed_valid` evidence under the repaired schema.
- Existing legacy records without raw capture may inform diagnosis, but cannot be upgraded into repaired-schema completed-valid evidence.
- The current `hn-20260707-0056` failure remains `HOLD_PROVIDER_NULL_EVIDENCE_INCOMPLETE` unless a separately approved future action gathers new evidence under the repaired harness.

## 13. Explicit non-actions during this plan

During creation of this repair plan:

- No evaluation run occurred.
- No resume execution occurred.
- No fresh rerun occurred.
- No replay occurred.
- No Gateway/model/provider call occurred.
- No comparator run occurred.
- No promotion occurred.
- No M6 proposal was prepared.
- No route/config/Gateway mutation occurred.
- No provider/model change occurred.
- No production apply occurred.
- No cache enablement occurred.
- No harness code was modified.
- No commit or push occurred.
- No memory promotion occurred.

## 14. Closeout

`PASS_REPAIR_PLAN_READY`

The minimal repair is concrete and bounded: preserve raw per-case child outputs before parsing, separate command failure from provider mismatch, classify provider-null causes explicitly, validate resume from completed evidence only, prevent duplicate calls by default, support remaining-case execution without reattempting prior cases, and require separate explicit approval for any fresh rerun that duplicates prior provider calls.
