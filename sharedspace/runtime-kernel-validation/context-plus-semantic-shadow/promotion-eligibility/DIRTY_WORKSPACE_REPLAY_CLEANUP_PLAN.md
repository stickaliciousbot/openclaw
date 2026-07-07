# Context+ Dirty-Workspace Replay Cleanup Plan

Generated: 2026-07-07 AEST

## Closeout classification

`HOLD_DIRTY_INVENTORY_TOO_BROAD`

The workspace is not replay-ready. A cleanup path is feasible, but the current dirty inventory is too broad to safely classify every untracked artifact for preservation/ignore/quarantine without a separate exhaustive manifest review and operator decisions. No cleanup has been performed.

## Boundary readback

No replay occurred. No comparator ran. No promotion occurred. No M6 proposal was prepared. No route/config/Gateway mutation occurred. No memory promotion occurred. No provider/model change occurred. No production apply occurred. No cache enablement occurred. No files were deleted, quarantined, staged, committed, or pushed by this planning step.

## Current dirty inventory summary

Read-only inventory basis: current `git status --porcelain=v1 -uall` / `git status --short --untracked-files=normal` observations during the clean-replay planning line.

Current pre-plan dirty summary:

Strict full inventory (`git status --porcelain=v1 -uall`):

- Total dirty status entries: `71156`
- Modified tracked entries: `24`
- Untracked files: `71132`
- Untracked entries under `sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility`: `6`

Earlier directory-collapsed view (`git status --short --untracked-files=normal`) showed `1520` total entries (`24` modified tracked, `1496` untracked entries/directories). The stricter `-uall` count is authoritative for replay readiness because every individual untracked file can affect the mutation sentinel unless cleaned, preserved, ignored by approved rule, or captured in an approved baseline.

This plan file itself will add one additional untracked replay-blocking path until separately preserved or removed by approval:

```text
?? sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/DIRTY_WORKSPACE_REPLAY_CLEANUP_PLAN.md
```

## Top-level dirty directories / roots observed

Observed top-level dirty roots include:

```text
sharedspace/                         50217 entries in strict -uall view
tooling/                             12843
.artifacts/                           5238
scripts/                               765
jdk11/                                 546
jdk17/                                 492
memory/                                305
services/                              183
projects/                              179
equipmentiq-fabric-dtb/                 78
.local-browser-libs/                    31
tax/                                    26
backups/                                21
projects (quoted path variants)          15
sharedspace (quoted path variants)       14
schemas/                                 8
skills/                                  6
hooks/                                   6
fabric-dtb-bootstrap/                    5
systemd/                                 4
specs/                                   4
.openclaw/                               4
tests/                                   3
config/                                  3
tools/                                   2
state/                                   2
outputs/                                 2
.trash/                                  2
tax receipts (quoted path variant)       2
AGENTS.md
HEARTBEAT.md
IDENTITY.md
SOUL.md
TOOLS.md
USER.md
equipmentiq-node-handoff.zip
equipmentiq-node-handoff/
fixtures/
goodmorning-openclaw.sh
jdk11.tar.gz
tmp_*
webworkspace-openclaw-xr-test-20260605/
webworkspace-openclaw-xr-test/
webworkspace/
```

All of these are replay-blocking unless the future replay is run from a separate clean worktree or a specific baseline snapshot is explicitly approved.

## Exact modified tracked replay-blocking paths

These tracked modifications are exact replay blockers:

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

Classification:

- `USER.md`: requires operator decision; root context file.
- `equipmentiq-fabric-dtb/...`: unrelated work-in-progress; requires project-specific preservation or separate worktree.
- `memory/...`: requires operator decision; memory artifacts may need preservation but must not be promoted/rewritten as part of replay cleanup.
- `sharedspace/context-bridge/events.jsonl`: requires operator decision; context-bridge state must not be silently rewritten.
- `sharedspace/runtime-kernel-validation/work-lifecycle*` and `state/work-lifecycle*`: unrelated work-in-progress / lifecycle evidence; requires preservation decision before cleanup.

## Exact untracked promotion-eligibility replay blockers observed

These untracked files under the Context+ promotion-eligibility area are exact replay blockers and must not be broadly committed under the replay cleanup line without separate approval:

```text
?? sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/ELIGIBILITY_INSPECTION.md
?? sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/FALSE_POSITIVE_BASELINE_COMPARISON.md
?? sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/FRESH_BASELINE_REPLAY_APPROVAL_REQUEST.md
?? sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/SAME_SUITE_COMPARATOR_PLAN.md
?? sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/m7_replay_input_manifest.jsonl
?? sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/m7_replay_input_manifest.summary.json
```

Classification:

- `FRESH_BASELINE_REPLAY_APPROVAL_REQUEST.md`: already useful planning evidence but not part of current approved commit set; needs preservation decision.
- `SAME_SUITE_COMPARATOR_PLAN.md`: comparator planning evidence; do not use as comparator approval; needs preservation decision.
- `ELIGIBILITY_INSPECTION.md`: eligibility planning evidence; needs preservation decision.
- `FALSE_POSITIVE_BASELINE_COMPARISON.md`: existing comparison artifact; needs preservation decision and must not imply comparator-ready state for failed replay.
- `m7_replay_input_manifest.jsonl` and `.summary.json`: replay manifest evidence; likely needs preservation, but only after manifest SHA/line-count validation and explicit approval.

## Already-preserved evidence

Already preserved in Git and not requiring cleanup action for replay readiness:

```text
commit 9c1e1f941383acd6d44451630ea4bb68074e3d1e
- MEMORY.md
- memory/2026-07-07.md
- memory/lessons-learned-context-plus-replay-mutation-sentinel-2026-07-07.md
- sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/MUTATION_SENTINEL_FAILURE_INVESTIGATION.md
- sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/investigate_mutation_sentinel_failure.py

commit f9a34caf124759ff7fc34e4424a4fe4f66b9cd90
- sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/CLEAN_WORKSPACE_REPLAY_READINESS_PLAN.md
```

## Classification categories and cleanup actions

### 1. Already-preserved evidence

Action: leave as tracked clean files. No cleanup needed.

Includes the two commits above.

### 2. Needs preservation

Candidate preservation set, pending explicit approval and file-specific readback:

```text
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/DIRTY_WORKSPACE_REPLAY_CLEANUP_PLAN.md
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/FRESH_BASELINE_REPLAY_APPROVAL_REQUEST.md
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/SAME_SUITE_COMPARATOR_PLAN.md
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/ELIGIBILITY_INSPECTION.md
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/FALSE_POSITIVE_BASELINE_COMPARISON.md
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/m7_replay_input_manifest.jsonl
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/m7_replay_input_manifest.summary.json
```

Required before preservation:

- exact staged-set approval per file/group;
- `git diff --check` for text artifacts;
- line count and SHA256 for JSONL manifest;
- explicit statement that preserving these files does not run comparator/replay or grant promotion/M6 authority.

### 3. Unrelated work-in-progress

Action: do not clean automatically. Either commit in their own project lanes, move to separate worktrees, or explicitly approve quarantine.

Likely includes:

```text
equipmentiq-fabric-dtb/
equipmentiq-node-handoff/
fabric-dtb-bootstrap/
projects/
sharedspace/runtime-kernel-validation/work-lifecycle*/
state/work-lifecycle*/
webworkspace*/
```

### 4. Generated/temp artifact

Action: candidate for ignore/quarantine/delete only with explicit approval; do not delete now.

Likely includes:

```text
.artifacts/
.local-browser-libs/
.trash/
backups/
jdk11.tar.gz
jdk11/
jdk17/
tmp_*
tooling/
tools/  # only if confirmed generated/local, otherwise operator decision
```

### 5. Safe to ignore via existing rules

Current status: none approved by this plan.

Possible future ignore candidates require separate review:

```text
.local-browser-libs/
.artifacts/
.tmp or tmp_* patterns
```

No `.gitignore` change is approved by this plan.

### 6. Requires operator decision

Action: Stick/operator must decide preserve, ignore, quarantine, delete, or move to separate worktree.

High-priority operator-decision paths:

```text
USER.md
AGENTS.md
HEARTBEAT.md
IDENTITY.md
SOUL.md
TOOLS.md
config/
.openclaw/
memory/
sharedspace/context-bridge/
state/
```

These are protected/adjoining surfaces. They must not be silently cleaned because they can contain operational state, private context, config-adjacent material, or memory continuity.

## Proposed replay-ready cleanup sequence

Preferred sequence, no deletion by default:

1. Preserve this cleanup plan in a single-file commit if approved.
2. Produce an exhaustive machine-readable dirty inventory artifact from `git status --porcelain=v1 -uall` with per-path classification.
3. Split cleanup into lanes:
   - Context+ promotion-eligibility evidence lane.
   - Memory/context/state preservation lane.
   - Work-lifecycle evidence lane.
   - EquipmentIQ/Fabric worktree lane.
   - Temp/generated artifact ignore/quarantine lane.
4. For each lane, request explicit staged-set approval.
5. Prefer separate clean worktree for replay instead of trying to clean the global workspace.
6. Before replay approval, require `git status --porcelain=v1 -uall` to be empty in the replay worktree, or require an explicitly approved dirty baseline snapshot.

## Proposed ignore/exclude set

No ignore/exclude is approved now.

Candidate ignore patterns for future review only:

```text
.local-browser-libs/
.artifacts/
.tmp/
tmp_*
*.pyc
__pycache__/
```

Important: mutation sentinel exclusions for a future replay should still exclude only the approved replay output directory. `.gitignore` hygiene is separate from sentinel exclusion and must not be used to hide unsafe replay mutations.

## Proposed quarantine/delete candidates

No quarantine/delete action is approved or performed.

Candidate quarantine/delete review buckets only:

```text
tmp_*
.local-browser-libs/
.artifacts/
.trash/
jdk11.tar.gz
jdk11/
jdk17/
webworkspace-openclaw-xr-test*/
```

Each requires separate approval. Prefer quarantine over delete if provenance is uncertain.

## Required operator approvals

Before any cleanup:

1. Approve preserving this cleanup plan, if desired.
2. Approve exhaustive inventory artifact generation.
3. Approve disposition of broad untracked promotion-eligibility files.
4. Approve memory/context/state preservation handling.
5. Approve EquipmentIQ/Fabric worktree handling.
6. Approve temp/generated ignore or quarantine policy.
7. Approve creation/use of a dedicated clean replay worktree.
8. Separately approve any future replay command after clean baseline proof.

## Replay-readiness gate

Replay remains blocked until one of these is true:

- Preferred: a dedicated replay worktree has empty `git status --porcelain=v1 -uall` before output directory creation.
- Fallback: Stick explicitly approves a dirty baseline snapshot and accepts that any outside-output delta still blocks comparator/promotion eligibility.

Decision from late-inventory review: do not clean the global workspace. Do not delete or quarantine files as part of replay readiness. Use a separate clean replay worktree for any future fresh baseline replay.

## Final status

- Cleanup plan: `HOLD_DIRTY_INVENTORY_TOO_BROAD`
- Workspace state: `NOT_REPLAY_READY`
- Replay: `BLOCKED_PENDING_CLEAN_WORKSPACE_OR_APPROVED_BASELINE`
- Comparator: `BLOCKED`
- Promotion: `BLOCKED`
- M6 proposal: `BLOCKED`
