# Context+ Same-Suite Comparator Script Readiness

Generated: 2026-07-07 AEST
Mode: fresh readiness check after comparator preservation
Classification: `PASS_COMPARATOR_SCRIPT_READY`

## Executive decision

`PASS_COMPARATOR_SCRIPT_READY`

The comparator script exists, is preserved in Git, exposes the required subcommands and safety flags, can read/build the 440-case M7 manifest in dry-run mode with the required SHA, and can validate the future replay boundary in dry-run mode without Gateway/model/provider calls.

Do **not** run production replay yet. This readiness check only clears the comparator-script blocker. Fresh production replay still requires separate explicit approval.

## Preservation proof

- Branch: `feature/stickbot-tars-m25-hardening-repair`
- Preserved commit: `44f2c99e80757e9063e05ea44654149c702cce54`
- Push result from approved preservation command: `HEAD -> feature/stickbot-tars-m25-hardening-repair`
- Preservation marker: `COMPARATOR_SCRIPT_PRESERVATION_COMMIT_PUSH_COMPLETE`

Preserved files:

- `scripts/context_plus_semantic_shadow_same_suite_comparator.py`
- `sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/COMPARATOR_SCRIPT_CREATION_READINESS.md`
- `sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/m7_replay_input_manifest.validation.jsonl`
- `sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/m7_replay_input_manifest.validation.summary.json`

## Script path

`scripts/context_plus_semantic_shadow_same_suite_comparator.py`

## Script existence

Exists.

## Supported subcommands

Fresh help validation passed for:

- `build-case-manifest`
- `run-production-replay`
- `compare`
- `write-report`

Late async confirmation: the originally approved chained fresh-help command also completed with code 0 and marker `FRESH_HELP_OK`. The command was not re-run after async completion.

## Supported required flags

### `build-case-manifest`

Fresh help validation passed for:

- `--source`
- `--output`
- `--summary-output`
- `--dry-run`

### `run-production-replay`

Fresh help validation passed for:

- `--manifest`
- `--manifest-sha256`
- `--out-dir`
- `--transport {gateway}`
- `--model`
- `--expected-provider`
- `--max-cases`
- `--chunk-size`
- `--checkpoint-every`
- `--min-delay-ms`
- `--max-retries`
- `--abort-on-rate-limit`
- `--abort-on-provider-cooldown`
- `--abort-on-provider-path-mismatch`
- `--abort-on-mutation`
- `--require-mutation-sentinel`
- `--read-only`
- `--no-route-config-gateway-memory-cache-mutation`
- `--dry-run`
- `--execute-approved`

Safety: without `--execute-approved`, `run-production-replay` performs boundary validation only and writes `replay_not_executed.json`. In this script version, even `--execute-approved` fails closed pending separate live-replay implementation review.

### `compare`

Fresh help validation passed for:

- `--manifest`
- `--shadow-journal`
- `--production-results`
- `--provider-path-report`
- `--mutation-sentinel-report`
- `--out-json`
- `--out-md`
- `--equal-zero-zero-is-hold`
- `--require-strict-improvement`
- `--require-no-critical-category-worse`

Safety: compare operates over existing files only. Equal `0% vs 0%` classifies `HOLD_EQUAL_ZERO_ZERO` when `--equal-zero-zero-is-hold` is supplied.

### `write-report`

Fresh help validation passed for:

- `--comparison-json`
- `--out-md`

Safety: writes Markdown from existing comparison JSON only.

## Manifest read validation result

Fresh manifest dry-run command:

```bash
python3 scripts/context_plus_semantic_shadow_same_suite_comparator.py build-case-manifest \
  --source sharedspace/runtime-kernel-validation/vnext-semantic-gate/context_plus_preselector_m6_fresh_trace_shadow_run_20260622/m7_shadow_observation_20260622/context_plus_preselector_m7_shadow_observation_journal.jsonl \
  --output sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/m7_replay_input_manifest.readiness.jsonl \
  --summary-output sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/m7_replay_input_manifest.readiness.summary.json \
  --dry-run
```

Result: PASS.

Summary:

- Classification: `PASS_MANIFEST_DRY_RUN_VALIDATED`
- Status: `M7_CASE_MANIFEST_READY_WITH_FINDINGS`
- Case count: 440
- Unique visible prompt hashes: 10
- Duplicate visible prompt hash count: 430
- Missing required field findings: 0
- Source journal SHA256: `4a7df21a9178427b53fd0f4289cddc76e761e7ea3c8d2870560e0c119d37add0`
- Readiness manifest SHA256: `0c28b5f5080838ee80e77ee47845e108685019ad613401385d4796e3615b8188`
- Gateway/model/provider calls: 0
- Mutation performed: false

## Replay boundary dry-run validation

Fresh replay boundary dry-run command used `--dry-run` and intentionally omitted `--execute-approved`:

```bash
python3 scripts/context_plus_semantic_shadow_same_suite_comparator.py run-production-replay \
  --manifest sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/m7_replay_input_manifest.readiness.jsonl \
  --manifest-sha256 0c28b5f5080838ee80e77ee47845e108685019ad613401385d4796e3615b8188 \
  --out-dir sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/replay_boundary_readiness_dry_run \
  --transport gateway \
  --model token-broker-vmesh/auto \
  --expected-provider token-broker-vmesh \
  --max-cases 440 \
  --chunk-size 25 \
  --checkpoint-every 25 \
  --min-delay-ms 2000 \
  --max-retries 0 \
  --abort-on-rate-limit \
  --abort-on-provider-cooldown \
  --abort-on-provider-path-mismatch \
  --abort-on-mutation \
  --require-mutation-sentinel \
  --read-only \
  --no-route-config-gateway-memory-cache-mutation \
  --dry-run
```

Result: PASS boundary validation; replay not executed.

Dry-run output:

- Classification: `HOLD_FRESH_BASELINE_REPLAY_REQUIRED`
- Mode: `dry_run_boundary_validation`
- Transport: `gateway`
- Model: `token-broker-vmesh/auto`
- Expected provider: `token-broker-vmesh`
- Case count: 440
- Manifest SHA256: `0c28b5f5080838ee80e77ee47845e108685019ad613401385d4796e3615b8188`
- Max retries: 0
- Abort on rate limit: true
- Abort on provider cooldown: true
- Abort on provider path mismatch: true
- Abort on mutation: true
- Require mutation sentinel: true
- Read only: true
- No route/config/Gateway/memory/cache mutation: true
- Gateway/model/provider calls: 0
- Mutation performed: false

## Source safety scan

Command:

```bash
grep -nE 'subprocess|requests|urllib|httpx|curl|openclaw|infer|gateway\.|browser\.|message\.|cron\.' scripts/context_plus_semantic_shadow_same_suite_comparator.py || true
```

Result: no output.

Interpretation: no obvious shell/network/OpenClaw-provider execution path is present in the comparator script source.

## Diff check

Command:

```bash
git diff --check
```

Result: PASS; no output.

## Is replay command safe to approve next?

Comparator-script blocker: cleared.

Replay command approval is now technically reviewable from the comparator-script-readiness perspective, but replay is **not** approved and was **not** requested here. Fresh production replay still requires separate explicit approval, and the current script intentionally fails closed for live replay execution pending separate live-replay implementation review.

## Classification rationale

`PASS_COMPARATOR_SCRIPT_READY` is the correct classification because:

- Script exists at the required path.
- Script was preserved and pushed.
- All required subcommands exist.
- Required manifest/replay/compare/report flags are present.
- Manifest read/build dry-run succeeded for 440 cases.
- Manifest SHA matches the required SHA: `0c28b5f5080838ee80e77ee47845e108685019ad613401385d4796e3615b8188`.
- Replay boundary dry-run validates provider/Gateway boundary without executing replay.
- Dry-run and readiness commands made zero Gateway/model/provider calls.
- No unsafe provider-call path was detected in source scan.

## Explicit no-call / no-mutation statement

No production replay occurred. No Gateway/model/provider calls occurred. No promotion occurred. No route/config/Gateway mutation occurred. No memory promotion occurred. No provider/model change occurred. No production apply occurred. No cache enablement occurred. No M6 proposal mutation occurred. No fabricated PASS evidence was created.
