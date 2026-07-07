# Context+ Clean-Workspace Replay Readiness Plan

Generated: 2026-07-07 AEST

## Closeout classification

`PASS_CLEAN_REPLAY_PLAN_READY`

This is a readiness plan only. It does not approve, start, resume, retry, or simulate a replay. It does not run the same-suite comparator, promote anything, or prepare an M6 proposal.

## Current state readback

Prior replay:

- Replay: `production_replay_approved_fresh_20260707`
- Terminal classification: `FAIL_REPLAY_UNSAFE / HOLD_NOT_PROMOTION_ELIGIBLE`
- Mutation investigation: `HOLD_CONCURRENT_WORKSPACE_NOISE`
- Provider/case boundary: `440/440` cases and `440/440` provider calls
- Mutation sentinel: `FAIL_MUTATION_SENTINEL`
- Comparator readiness: `HOLD_SAME_SUITE_COMPARATOR_NOT_READY`

Preserved evidence:

- Mutation investigation artifact + helper are already preserved in commit `9c1e1f941` (`Document Context+ replay sentinel lessons`).
- Do not commit the broad untracked promotion-eligibility files as part of this line.

## Current dirty/untracked inventory summary

Read-only inventory command used:

```sh
git status --short --untracked-files=normal
```

Summary from current workspace:

- Total status entries: `1520`
- Tracked modified entries: `24`
- Untracked entries/directories: `1496`
- Untracked entries currently under `sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility`: `6`

Current tracked modified entries observed:

```text
 M USER.md
 M equipmentiq-fabric-dtb/docs/FAILURES_AND_FIXES_LEDGER.md
 M memory/2026-06-27.md
 M memory/2026-06-28.md
 M memory/2026-06-30.md
 M memory/2026-07-01.md
 M memory/2026-07-02.md
 M memory/lessons-learned-ge2-native-command-surface-promotion-2026-06-30.md
 M memory/lessons-learned-stickbot-tars-voice-demo-2026-07-02.md
 M sharedspace/context-bridge/events.jsonl
 M sharedspace/runtime-kernel-validation/work-lifecycle-ledger/OPENCLAW_STICKBOT_WORK_LIFECYCLE_LEDGER_DESIGN_NOTEBOOK.md
 M sharedspace/runtime-kernel-validation/work-lifecycle/m10-enforced-canary/evidence_manifest.json
 M sharedspace/runtime-kernel-validation/work-lifecycle/m10-enforced-canary/gate-results.json
 M sharedspace/runtime-kernel-validation/work-lifecycle/m10-enforced-canary/status.json
 M sharedspace/runtime-kernel-validation/work-lifecycle/m10-enforced-canary/summary.json
 M sharedspace/runtime-kernel-validation/work-lifecycle/m8-failure-injection/evidence_manifest.json
 M sharedspace/runtime-kernel-validation/work-lifecycle/m8-failure-injection/gate-results.json
 M sharedspace/runtime-kernel-validation/work-lifecycle/m8-failure-injection/summary.json
 M sharedspace/runtime-kernel-validation/work-lifecycle/m9-observe-only-canary/evidence_manifest.json
 M sharedspace/runtime-kernel-validation/work-lifecycle/m9-observe-only-canary/gate-results.json
 M sharedspace/runtime-kernel-validation/work-lifecycle/m9-observe-only-canary/status.json
 M sharedspace/runtime-kernel-validation/work-lifecycle/m9-observe-only-canary/summary.json
 M state/work-lifecycle/events/work_20260701T114900Z_lifecycle_ledger_m10.jsonl
 M state/work-lifecycle/runs/work_20260701T114900Z_lifecycle_ledger_m10.json
```

Current untracked promotion-eligibility entries observed:

```text
?? sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/ELIGIBILITY_INSPECTION.md
?? sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/FALSE_POSITIVE_BASELINE_COMPARISON.md
?? sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/FRESH_BASELINE_REPLAY_APPROVAL_REQUEST.md
?? sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/SAME_SUITE_COMPARATOR_PLAN.md
?? sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/m7_replay_input_manifest.jsonl
?? sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/m7_replay_input_manifest.summary.json
```

Current workspace status also contains broad untracked directories/files under root, `memory/`, `projects/`, `scripts/`, `sharedspace/`, `state/`, `tests/`, `tools/`, `skills/`, temp files, local caches, and project artifacts. These are not listed exhaustively in this plan because the replay precondition is zero outside-output status entries, not manual allowlisting of the current dirt.

## Replay readiness verdict for current workspace

The current workspace is **not replay-ready**.

A future 440-case replay must not run from this workspace while these dirty/untracked entries remain visible to `git status` unless Stick explicitly approves a baseline snapshot policy. The preferred path is a dedicated clean worktree.

## Clean baseline requirements

Preferred safe baseline:

1. Use a dedicated clean worktree/checkout at the intended commit, preferably including commit `9c1e1f941` or a later commit that preserves the investigation artifacts.
2. Before creating the replay output directory, require:

   ```sh
   git diff --quiet
   git diff --cached --quiet
   test -z "$(git status --short --untracked-files=all)"
   ```

3. Record immutable baseline evidence:
   - `git rev-parse HEAD`
   - `git branch --show-current`
   - `git status --porcelain=v1 -uall` must be empty
   - SHA256 of the exact replay manifest
   - exact approved output directory
4. Only after the empty baseline is captured, create the fresh replay output directory.
5. During and after replay, the mutation sentinel may filter only the approved replay output directory. Any other status entry is a hard abort.

Fallback baseline, only with explicit approval:

- If Stick approves a non-clean baseline, write a `baseline_snapshot.json` with the exact dirty status list and SHA256 before replay.
- This mode is inferior and should be treated as `HOLD_BASELINED_DIRTY_WORKSPACE`, not clean replay, unless every outside-output delta is proven unchanged against the approved baseline.
- Broad untracked promotion-eligibility files must not be implicitly accepted; they need explicit preserve/ignore/quarantine decisions.

## What must be committed, ignored, quarantined, or excluded before replay

### Must be clean before replay

The following must be absent from `git status --short --untracked-files=all` before replay, unless explicitly included in an approved dirty baseline:

- `USER.md`
- `memory/`
- `MEMORY.md`
- `sharedspace/context-bridge/`
- `state/`
- `sharedspace/runtime-kernel-validation/work-lifecycle/`
- `sharedspace/runtime-kernel-validation/work-lifecycle-ledger/`
- `equipmentiq-fabric-dtb/`
- `projects/`
- `scripts/`
- `tests/`
- `tools/`
- `skills/`
- `config/`
- `.openclaw/`
- `.artifacts/`
- `.local-browser-libs/`
- `.trash/`
- `backups/`
- `tmp_*`
- any root-level untracked or modified file
- any untracked file under `sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/` except the approved future replay output directory after it is created

### Must not be committed as part of this line without separate approval

Do not commit these broad existing untracked promotion-eligibility files under the replay-readiness line:

```text
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/ELIGIBILITY_INSPECTION.md
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/FALSE_POSITIVE_BASELINE_COMPARISON.md
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/FRESH_BASELINE_REPLAY_APPROVAL_REQUEST.md
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/SAME_SUITE_COMPARATOR_PLAN.md
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/m7_replay_input_manifest.jsonl
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/m7_replay_input_manifest.summary.json
```

### Commit / ignore / quarantine decision rules

- Commit only scoped, reviewed evidence that belongs to the current approved line.
- Ignore only stable local/generated directories with explicit owner approval and a reviewed `.gitignore` change.
- Quarantine only with explicit owner approval; do not delete or move evidence silently.
- Do not use broad sentinel exclusions to hide dirty workspace. If it affects `git status`, it must be clean, approved-baselined, or aborting.

## Exact files/dirs excluded from the future mutation sentinel

For a clean replay, the only allowed sentinel exclusion is the approved fresh replay output directory:

```text
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/fresh_same_suite_production_replay_clean_YYYYMMDDTHHMMSSZ/
```

Everything else remains in-scope for mutation detection.

No exclusion is allowed for:

- `MEMORY.md`
- `memory/`
- root context files such as `USER.md`, `AGENTS.md`, `SOUL.md`, `IDENTITY.md`, `TOOLS.md`, `HEARTBEAT.md`
- `sharedspace/context-bridge/`
- `state/`
- `config/`
- `.openclaw/`
- provider/model/Gateway/route/cache files
- broad project roots such as `projects/`, `scripts/`, `sharedspace/`, `equipmentiq-fabric-dtb/`

## Proposed fresh replay output path

Use a new, never-reused run root:

```text
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/fresh_same_suite_production_replay_clean_YYYYMMDDTHHMMSSZ/
```

Example shape, not approved for execution:

```text
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/fresh_same_suite_production_replay_clean_20260707T093000Z/
```

Required files, all inside that output path:

```text
run_config.json
baseline_snapshot.json
case_manifest.copy.jsonl
mutation_sentinel_before.json
production_replay_journal.jsonl
production_replay_checkpoints.jsonl
provider_model_call_count_report.json
rate_limit_cooldown_report.json
mutation_sentinel_after.json
mutation_sentinel_report.json
same_suite_comparator_ready_status.json
replay_summary.json
status.json
```

## Mutation sentinel precheck

Before any future replay approval can be requested, run a read-only precheck that reports:

1. exact `HEAD` commit;
2. exact branch/worktree path;
3. exact manifest path and SHA256;
4. exact proposed output directory;
5. `git status --porcelain=v1 -uall` before output directory creation;
6. classification: `PASS_CLEAN_BASELINE_READY` only if status is empty;
7. if not empty, classification: `HOLD_DIRTY_WORKSPACE_BASELINE_REQUIRED` with exact dirty entries.

Replay start gate:

- If clean baseline: continue only after explicit replay approval.
- If dirty baseline: stop unless Stick explicitly approves using that dirty baseline; even then, any changed outside-output delta must hard-abort and remain non-promotion-eligible until separately investigated.

Replay terminal gate:

- Compare before/after filtered workspace status by exact line and by path.
- Added, removed, or changed status outside the approved output directory => `FAIL_MUTATION_SENTINEL` and `HOLD_NOT_PROMOTION_ELIGIBLE`.
- A passing provider boundary must never override a failed mutation sentinel.

## Rate-limit/cooldown guardrails for future replay

A future replay approval package must require:

```text
max_cases=440
expected_provider=token-broker-vmesh
requested_model=token-broker-vmesh/auto
transport=gateway
max_retries=0
min_delay_ms>=2000
chunk_size=25
checkpoint_every=25
abort_on_rate_limit=true
abort_on_provider_cooldown=true
abort_on_provider_path_mismatch=true
abort_on_mutation=true
require_mutation_sentinel=true
read_only=true
no_route_config_gateway_memory_cache_mutation=true
fallback_model_provider_retries=false
direct_provider_bypass=false
```

If any 429/cooldown/provider mismatch/fallback/direct-bypass/mutation event occurs, stop and classify HOLD/FAIL; do not retry into a burst.

## Approval gates for any future replay

A future replay requires separate explicit approval for each of these, in order:

1. **Plan acknowledgement**: this plan accepted as bounded readiness design only.
2. **Workspace baseline approval**: clean status proof, or explicit dirty baseline approval if Stick chooses the inferior path.
3. **Replay command approval**: exact command, exact manifest SHA, exact output directory, exact model/provider path, expected 440 provider calls, rate guardrails.
4. **Post-run evidence preservation approval**: preserve terminal replay evidence only.
5. **Comparator approval**: separate and only if replay terminal state is comparator-ready. This plan does not grant it.
6. **Promotion/M6 proposal approval**: separate and only after comparator and promotion-readiness evidence exist. This plan does not grant it.

## Forbidden actions readback

No comparator run occurred. No replay rerun occurred. No promotion occurred. No M6 proposal was prepared. No route/config/Gateway mutation occurred. No memory promotion occurred. No provider/model change occurred. No production apply occurred. No cache enablement occurred. No files were deleted or quarantined.

## Next safe step

The next safe step is a read-only preservation review of this plan artifact, or a separate owner-approved cleanup/baseline plan. It is not a replay run.
