# Context+ Clean Replay Worktree Plan

Generated: 2026-07-07 AEST

## Closeout classification

`PASS_CLEAN_WORKTREE_PLAN_READY`

This is a plan only. It does not create a worktree, run replay, run comparator, promote anything, or prepare an M6 proposal.

## Current branch/head inspected

Read-only inspection result:

```text
branch: feature/stickbot-tars-m25-hardening-repair
head: a652c65bef224f34f7b488f39de19e00f4455009
remote: origin https://github.com/stickaliciousbot/webworkspace.git
head decoration: HEAD -> feature/stickbot-tars-m25-hardening-repair, origin/feature/stickbot-tars-m25-hardening-repair
head subject: docs(context-plus): preserve dirty workspace replay cleanup plan
```

## Proposed base commit

Use the current pushed branch head as the clean worktree base:

```text
a652c65bef224f34f7b488f39de19e00f4455009
```

Reason:

- It includes the preserved mutation-sentinel investigation evidence.
- It includes the clean-workspace replay readiness plan.
- It includes the dirty-workspace replay cleanup plan.
- It is pushed to `origin/feature/stickbot-tars-m25-hardening-repair`.
- It does not require cleaning the current global workspace.

If branch head advances before execution, rerun this plan's branch/head readback and decide whether to use the newer head or pin to this commit.

## Proposed clean worktree path

Future approved worktree path:

```text
/tmp/context-plus-clean-replay-worktree-a652c65be
```

Preferred future command shape, not approved by this plan:

```sh
git fetch origin feature/stickbot-tars-m25-hardening-repair

git worktree add \
  --detach \
  /tmp/context-plus-clean-replay-worktree-a652c65be \
  a652c65bef224f34f7b488f39de19e00f4455009
```

Alternative future preservation branch shape, if evidence should be committed directly from the worktree:

```sh
git worktree add \
  -b context-plus/fresh-replay-clean-YYYYMMDDTHHMMSSZ \
  /tmp/context-plus-clean-replay-worktree-a652c65be \
  a652c65bef224f34f7b488f39de19e00f4455009
```

This plan recommends the branch worktree form if replay evidence is expected to be committed/pushed without touching the dirty global workspace.

## Required artifacts available from the clean base

Tracked artifacts confirmed available from current branch/head:

```text
scripts/context_plus_semantic_shadow_same_suite_comparator.py
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/m7_replay_input_manifest.readiness.jsonl
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/m7_replay_input_manifest.readiness.summary.json
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/MUTATION_SENTINEL_FAILURE_INVESTIGATION.md
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/CLEAN_WORKSPACE_REPLAY_READINESS_PLAN.md
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/DIRTY_WORKSPACE_REPLAY_CLEANUP_PLAN.md
```

The earlier untracked non-readiness manifest artifacts in the dirty global workspace are **not** required for the future clean worktree replay and must not be copied into the worktree unless separately approved and validated:

```text
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/m7_replay_input_manifest.jsonl
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/m7_replay_input_manifest.summary.json
```

Preferred input manifest for any future replay approval:

```text
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/m7_replay_input_manifest.readiness.jsonl
```

Expected manifest SHA256:

```text
0c28b5f5080838ee80e77ee47845e108685019ad613401385d4796e3615b8188
```

## Artifact sync rule

Do not copy broad artifacts from the dirty global workspace into the clean worktree.

Allowed artifact availability methods, in order of preference:

1. Check out tracked artifacts from `a652c65bef224f34f7b488f39de19e00f4455009`.
2. If a required artifact is missing, stop with `HOLD_ARTIFACT_SYNC_UNCLEAR` and preserve/commit that artifact separately from the dirty workspace before creating or using the replay worktree.
3. Do not use untracked dirty-workspace artifacts as replay input unless a separate approval validates exact path, SHA256, provenance, and copy target.

## Clean-state verification commands

After future worktree creation, before creating any replay output directory, run from the clean worktree:

```sh
set -euo pipefail

git rev-parse HEAD
git branch --show-current || true
git status --porcelain=v1 -uall
git diff --quiet
git diff --cached --quiet
test -z "$(git status --porcelain=v1 -uall)"

sha256sum \
  sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/m7_replay_input_manifest.readiness.jsonl

python3 scripts/context_plus_semantic_shadow_same_suite_comparator.py --help >/tmp/context-plus-comparator-help.txt
```

Required result:

- `HEAD` equals `a652c65bef224f34f7b488f39de19e00f4455009`, or a separately approved newer base.
- `git status --porcelain=v1 -uall` is empty before the replay output directory is created.
- Manifest SHA matches `0c28b5f5080838ee80e77ee47845e108685019ad613401385d4796e3615b8188`.
- Comparator script help works without Gateway/model/provider calls.

If any condition fails, stop before replay approval.

## Replay output directory inside clean worktree

Future replay output directory shape:

```text
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/fresh_same_suite_production_replay_clean_YYYYMMDDTHHMMSSZ/
```

Example only, not approved for execution:

```text
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/fresh_same_suite_production_replay_clean_20260707T100000Z/
```

The output directory must be created only after the clean baseline proof is captured.

Expected terminal files, all inside that output directory:

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

## Mutation sentinel rules

Before replay:

- Capture `baseline_snapshot.json` before output directory creation.
- Baseline must show empty `git status --porcelain=v1 -uall`.
- Record `HEAD`, branch/worktree path, manifest path, manifest SHA, and approved output directory.

During replay:

- The only permitted sentinel exclusion is the approved fresh replay output directory.
- No exclusions for memory, context bridge, state, config, `.openclaw`, provider/model/Gateway/route/cache, scripts, tests, tools, projects, or root files.

After replay:

- Compare before/after filtered workspace status by exact line and by path.
- Any added, removed, or changed status entry outside the approved output directory => `FAIL_MUTATION_SENTINEL` and `HOLD_NOT_PROMOTION_ELIGIBLE`.
- Provider/case success never overrides a failed mutation sentinel.

## Replay command shape

Future command shape only; not approved by this plan:

```sh
python3 scripts/context_plus_semantic_shadow_same_suite_comparator.py \
  run-production-replay \
  --execute-approved \
  --manifest sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/m7_replay_input_manifest.readiness.jsonl \
  --manifest-sha256 0c28b5f5080838ee80e77ee47845e108685019ad613401385d4796e3615b8188 \
  --out-dir sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/fresh_same_suite_production_replay_clean_YYYYMMDDTHHMMSSZ \
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
  --no-route-config-gateway-memory-cache-mutation
```

Required guardrails:

```text
expected cases: 440
expected provider calls: 440
fallback retries: 0
max retries: 0
min delay: >=2000ms
rate-limit/cooldown abort: true
provider path mismatch abort: true
mutation abort: true
direct provider bypass: false
route/config/Gateway/memory/cache mutation: false
```

## Approval gates

Separate explicit approvals are required, in this order:

1. Preserve this clean replay worktree plan, if desired.
2. Create the clean worktree / replay branch.
3. Run clean-state precheck in the worktree.
4. Approve the exact 440-case replay command with output dir, manifest SHA, model/provider path, and expected provider-call count.
5. Preserve terminal replay evidence only.
6. Consider same-suite comparator only if replay terminal state is comparator-ready. This plan does not approve comparator.
7. Consider promotion/M6 proposal only after separate comparator/promotion-readiness evidence. This plan does not approve promotion or M6 proposal.

## Evidence preservation path

Preferred evidence preservation path:

1. Use a dedicated replay evidence branch worktree:

   ```text
   context-plus/fresh-replay-clean-YYYYMMDDTHHMMSSZ
   ```

2. Commit only the approved replay output directory and any explicit terminal closeout artifact from within the clean worktree branch.
3. Push the evidence branch to origin.
4. Do not copy replay evidence into the dirty global workspace.
5. If evidence must land on `feature/stickbot-tars-m25-hardening-repair`, use a separate reviewed merge/cherry-pick after evidence preservation and staged-file review.

Fallback evidence preservation path:

- If a detached worktree is used, tar the approved output directory and produce SHA256/manifest, then request explicit approval before copying or committing into any branch.

## Failure/HOLD conditions

- `HOLD_WORKTREE_BASE_UNCLEAR`: branch/head changed and no approved base is selected.
- `HOLD_ARTIFACT_SYNC_UNCLEAR`: required manifest/script/artifacts are missing from the clean base.
- `HOLD_CLEAN_BASELINE_NOT_PROVEN`: clean precheck has any status output.
- `FAIL_UNSAFE_WORKTREE_PLAN`: plan would require copying dirty artifacts, deleting/quarantining files, or mutating runtime/provider/config/cache.

## Final status

- Clean replay worktree plan: `PASS_CLEAN_WORKTREE_PLAN_READY`
- Workspace state: `GLOBAL_WORKSPACE_NOT_REPLAY_READY`
- Future replay: `BLOCKED_PENDING_CLEAN_WORKTREE_CREATION_AND_APPROVAL`
- Comparator: `BLOCKED`
- Promotion: `BLOCKED`
- M6 proposal: `BLOCKED`

## Boundary readback

No worktree was created. No replay occurred. No comparator ran. No promotion occurred. No M6 proposal was prepared. No route/config/Gateway mutation occurred. No memory promotion occurred. No provider/model change occurred. No production apply occurred. No cache enablement occurred. No files were deleted or quarantined. No commit or push occurred.
