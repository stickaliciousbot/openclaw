# M3 Source Build Path Candidate Map

Status: `PASS_M3_SOURCE_BUILD_PATH_CANDIDATES_MAPPED`

## Selected path

`/home/stickai/.openclaw/worktrees/umc-m3g-observe-only-hook-source-20260711`

Classification: `SOURCE_BUILD_PATH_READY`

Why selected:

- OpenClaw package version is `2026.5.7`, matching installed runtime version.
- Clean git status before M3 source apply.
- `pnpm-lock.yaml` and `node_modules` are present.
- Existing M2 queued route-admission source hook exists in `src/auto-reply/reply/followup-runner.ts`.
- Known M2 terms present in source:
  - `resolveUmcV1DefaultRouteFromConfig`
  - `isUmcV1QueuedOwnerScope`
  - `applyUmcV1QueuedRouteAdmission`
  - `umcV1QueuedRouteIntent`

## Other candidates

### `/home/stickai/.openclaw/workspace/tmp/openclaw-2026-5-7-closeout-backport`

Classification: `SOURCE_BUILD_PATH_DIRTY_REQUIRES_CLEAN_WORKTREE`

- Version: `openclaw@2026.5.7`
- Branch: `closeout-delivery-2026-5-7-backport`
- Head: `9338825836c9989062dfcf7e6231fc5b56bf44a5`
- Dirty with many unrelated closeout/backport changes.
- Not selected directly to avoid overwriting or mixing unrelated changes.

### `/home/stickai/.openclaw/workspace/tmp/openclaw-source-start-ack-backport-2026-5-7`

Classification: `SOURCE_BUILD_PATH_VERSION_MISMATCH`

- Version: `openclaw@2026.6.10`
- Not selected because installed runtime is `2026.5.7`.

### `/home/stickai/.openclaw/worktrees/umc-m3-envelope-supervision-source-build-20260716`

Classification: `SOURCE_BUILD_PATH_UNUSABLE`

- Clean linked worktree from base `9338825836c9989062dfcf7e6231fc5b56bf44a5`.
- Not selected because this baseline source lacks the active M2 queued route-admission source hook that exists in the M3G source branch and installed runtime.

### `/home/stickai/.openclaw/workspace`

Classification: `SOURCE_BUILD_PATH_UNUSABLE`

- Global workspace, not OpenClaw package source root.
- Broad unrelated dirty state.

## Decision

Use the existing clean M3G source worktree and apply the validated M3 envelope supervision source there. This preserves the M2 hook source and avoids direct installed-dist patching.
