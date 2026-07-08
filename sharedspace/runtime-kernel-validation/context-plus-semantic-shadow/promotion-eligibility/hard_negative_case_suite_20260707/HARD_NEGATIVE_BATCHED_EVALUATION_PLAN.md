# Hard-Negative Batched Evaluation Plan

Classification: `PASS_BATCHED_EVALUATION_PLAN_READY`

## Scope

Plan only. No new evaluation execution, resume execution, tail continuation, Gateway/model/provider calls, comparator, promotion, M6 proposal, route/config/Gateway mutation, memory promotion, provider/model change, production apply, cache enablement, commit, or push occurred while preparing this plan.

This plan is not approval to execute. It is the concrete safer execution method to review and preserve before any new provider calls.

## Objective

Evaluate the 240-case hard-negative production suite without ad hoc resume/tail commands.

The output of this plan, if later executed successfully, is **only** clean hard-negative production evidence ready for same-suite comparison. It is not promotion by itself.

## Promotion gate

Only `PASS_FALSE_POSITIVE_BASELINE_IMPROVED` can lead to promotion eligibility.

Comparator outcomes must be interpreted as:

- `PASS_FALSE_POSITIVE_BASELINE_IMPROVED` → may proceed to promotion eligibility artifact review
- `HOLD_EQUAL_ZERO_ZERO` → no promotion
- `FAIL_FALSE_POSITIVE_NOT_IMPROVED` → no promotion
- `FAIL_REGRESSION_FOUND` → no promotion

M6 proposal remains blocked unless promotion eligibility is proven and separately approved.

## Batch size

Default batch size: `20` cases.

Total suite: `240` cases.

Total batches: `12`.

Rationale:

- localizes Gateway timeout failures
- avoids one-case churn
- provides frequent checkpoints
- prevents ad hoc range/tail chasing

Batch size may be increased to `40` only after at least two 20-case batches pass cleanly and Stick explicitly approves the change.

## Batch ranges

1. `batch_001`: `hn-20260707-0001` → `hn-20260707-0020`
2. `batch_002`: `hn-20260707-0021` → `hn-20260707-0040`
3. `batch_003`: `hn-20260707-0041` → `hn-20260707-0060`
4. `batch_004`: `hn-20260707-0061` → `hn-20260707-0080`
5. `batch_005`: `hn-20260707-0081` → `hn-20260707-0100`
6. `batch_006`: `hn-20260707-0101` → `hn-20260707-0120`
7. `batch_007`: `hn-20260707-0121` → `hn-20260707-0140`
8. `batch_008`: `hn-20260707-0141` → `hn-20260707-0160`
9. `batch_009`: `hn-20260707-0161` → `hn-20260707-0180`
10. `batch_010`: `hn-20260707-0181` → `hn-20260707-0200`
11. `batch_011`: `hn-20260707-0201` → `hn-20260707-0220`
12. `batch_012`: `hn-20260707-0221` → `hn-20260707-0240`

## Harness inspection evidence

Approved async inspection `fdd2aee2` completed with exit code `0` and confirmed relevant harness behavior:

- `validate_manifest(... strict_approved_shape=True)` default at line `114`; strict approved-shape enforcement occurs around line `144`.
- `cmd_run_production_routing` starts at line `445`.
- non-resume selection uses `result.records[:args.max_cases]` at line `452`.
- `--remaining-only` selection uses remaining manifest records then `[:args.max_cases]` at line `463`.
- `run_config.json` records `max_cases`, `remaining_only`, `resume_from`, model/provider boundary, and no-mutation flags at line `468`.
- fixture/selftest path shows `validate_manifest(... strict_approved_shape=False)` usage at line `607`, supporting the plan’s need for generated batch manifests to bypass the full 240-case shape check intentionally.

## Batch manifest generation method

Generate one JSONL manifest per batch from the approved 240-case manifest by filtering exact `case_id` suffix ranges.

Rules:

- Source manifest SHA must equal `4f5aaf3a24e68542f05445fe5f6aeab92795883c988fccdcc0490255bee9ebda`.
- Each batch manifest must contain exactly 20 records.
- Batch manifest case IDs must be contiguous and match the batch range.
- Each record must preserve the original fields unchanged.
- Batch manifest SHA is recorded in `batch_manifest.summary.json`.
- Harness invocation for generated batch manifests must use `--allow-fixture-manifest` because each batch manifest intentionally does not have the approved 240-case shape.

## Output directory structure

Run root:

`hard_negative_batched_evaluation_<timestamp>/`

Top-level:

- `run_config.json`
- `batch_ledger.jsonl`
- `batch_manifest_index.json`
- `combined_summary.json` only after all batches pass
- `combined_production_journal.v2.jsonl` only after all batches pass
- `combined_provider_boundary_report.json` only after all batches pass
- `combined_mutation_sentinel_report.json` only after all batches pass
- `FINALIZATION_READINESS.md` only after all batches pass

Per batch:

`batch_001/`

Required files:

- `batch_manifest.jsonl`
- `batch_manifest.summary.json`
- `run_config.json`
- `mutation_sentinel_before.git_status_short.txt`
- `case_selection_plan.json`
- `duplicate_call_prevention_report.json`
- `production_routing_journal.v2.jsonl`
- `production_provider_model_call_count_report.json`
- `provider_null_taxonomy_report.json`
- `command_failure_report.json`
- `rate_limit_cooldown_report.json`
- `mutation_sentinel_report.json`
- `summary.json`
- `batch_closeout.json`
- `raw_calls/<case_attempt>/child_stdout.raw`
- `raw_calls/<case_attempt>/child_stderr.raw`
- `raw_calls/<case_attempt>/parse_result.json`

## Per-batch execution protocol

For each batch:

1. Verify source manifest SHA.
2. Generate batch manifest.
3. Verify batch range/count exactly.
4. Verify output directory is new/empty.
5. Verify no prior batch ledger overlap.
6. Capture mutation sentinel pre-state.
7. Run only that batch.
8. Capture raw stdout/stderr and parse reports for every attempt.
9. Write provider boundary report.
10. Write provider-null taxonomy report.
11. Write command failure report.
12. Write rate-limit/cooldown report.
13. Capture mutation sentinel post-state and compare outside approved output dir.
14. Write terminal `batch_closeout.json`.
15. Continue to next batch only if closeout is `PASS_BATCH_READY_FOR_MERGE`.

## Per-batch provider boundary checks

Pass only if:

- expected provider is `token-broker-vmesh`
- requested model is `token-broker-vmesh/auto`
- provider verified count equals batch case count
- provider mismatch count is `0`
- command failure count is `0`
- timeout count is `0`
- missing provider metadata count is `0`
- raw stdout/stderr artifacts exist for every attempted case

Provider mismatch is hard fail.

Provider-null/command failure/timeout is HOLD unless proven provider mismatch.

## Per-batch mutation sentinel

For every batch:

- Capture `git status --short` before.
- Capture `git status --short` after.
- Filter out approved batch output dir only.
- If any outside-output delta is introduced by the batch, close `FAIL_BATCH_MUTATION_SENTINEL`.

Existing unrelated workspace dirt may be recorded, but the before/after filtered outside-output set must remain equal.

## Per-batch rate-limit/cooldown checks

Close `HOLD_RATE_LIMIT_OR_COOLDOWN` if any case emits rate/cooldown signals such as:

- `429`
- `rate limit`
- `ratelimit`
- `quota`
- `cooldown`
- `too many requests`

Do not continue to next batch after a rate/cooldown HOLD.

## Per-batch closeout classifications

- `PASS_BATCH_READY_FOR_MERGE`
- `HOLD_GATEWAY_TRANSPORT_TIMEOUT`
- `HOLD_RATE_LIMIT_OR_COOLDOWN`
- `HOLD_PROVIDER_NULL_TRANSPORT_OR_COMMAND_FAILURE`
- `HOLD_BATCH_INCOMPLETE`
- `FAIL_BATCH_PROVIDER_MISMATCH`
- `FAIL_BATCH_DUPLICATE_CALL_BOUNDARY`
- `FAIL_BATCH_MUTATION_SENTINEL`
- `ABORT_BATCH_FORBIDDEN_ACTION_ATTEMPTED`

## Retry policy

Default: `0` retries.

Retry behavior is not automatically approved by this plan.

If Stick approves retry policy later:

- allow exactly `1` retry only for Gateway/transport timeout
- preserve first failed raw attempt
- write retry attempt under same case lineage as `attempt-0002`
- never retry provider mismatch
- never retry duplicate-call failure
- never retry mutation sentinel failure
- never retry route/config/provider/model/cache mutation
- never retry comparator/promotion/M6 attempts

If retry policy is not approved, any Gateway timeout closes the batch as `HOLD_GATEWAY_TRANSPORT_TIMEOUT`.

## Timeout policy

Do not blindly increase timeouts.

Default starting timeout should remain explicit in run config. If changing timeout:

- document old/new timeout
- explain why batching alone is insufficient
- require explicit owner approval
- preserve timeout failure evidence

The observed tail failure was `GatewayTransportError: gateway timeout after 120000ms`, so timeout changes are a design decision, not an automatic fix.

## Abort criteria

Abort immediately if any of these occur:

- case outside current batch is selected
- batch count is not exactly 20
- duplicate-call prevention fails
- provider mismatch
- fallback/model override
- mutation sentinel failure outside approved output
- route/config/Gateway/memory/provider/model/cache mutation detected
- comparator run attempted
- promotion attempted
- M6 proposal attempted
- output dir is not new/empty
- batch manifest does not match source manifest records exactly

## Merge / finalization step

Only after all 12 batches close `PASS_BATCH_READY_FOR_MERGE`:

1. Concatenate batch production journals in batch order.
2. Verify combined case count is `240 / 240`.
3. Verify case IDs exactly `hn-20260707-0001` → `hn-20260707-0240`.
4. Verify no duplicates.
5. Verify combined provider boundary clean.
6. Verify combined mutation sentinel clean.
7. Verify rate-limit/cooldown events `0`.
8. Write `PASS_HARD_NEGATIVE_PRODUCTION_EVIDENCE_READY_FOR_COMPARATOR` or HOLD/FAIL equivalent.

## Comparator gating

Comparator remains blocked until combined production evidence is clean.

Do not run comparator unless:

- all batches pass
- combined production journal is complete
- Context+ shadow/offline hard-negative journal is present/approved
- provider/mutation/rate/duplicate gates are clean
- separate comparator approval is given

## Preservation requirements

Preserve after each terminal batch:

- batch manifest
- raw attempts
- reports
- closeout
- batch ledger update

Preserve after plan/diagnosis before any new execution:

- `GATEWAY_EVAL_TRANSPORT_RELIABILITY_DIAGNOSIS.md`
- `HARD_NEGATIVE_BATCHED_EVALUATION_PLAN.md`
- execution freeze artifact if present

## Closeout

Classification: `PASS_BATCHED_EVALUATION_PLAN_READY`

This means the protocol is concrete enough for review/preservation. It does **not** authorize execution.

No live evaluation approval should be requested until this plan and the transport diagnosis are preserved and Stick explicitly reopens execution under the batched protocol.
