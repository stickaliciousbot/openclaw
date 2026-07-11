# M3H Build Command Discovery — blocked

Status: `BLOCKED_M3H_BUILD_COMMAND_UNAVAILABLE`
Generated: `2026-07-11T22:38:30Z`

## Source state

- Source worktree: `/home/stickai/.openclaw/worktrees/umc-m3g-observe-only-hook-source-20260711`
- Source branch: `evidence/umc-m3g-observe-only-hook-source-20260711`
- Source HEAD: `8da099e99e94e3feb4532769112075bdca5aedba`
- Source remote: `fork/evidence/umc-m3g-observe-only-hook-source-20260711` @ `8da099e99e94e3feb4532769112075bdca5aedba`

## Candidate build command

Candidate: `node scripts/tsdown-build.mjs`

Reason: package `build` runs `node scripts/build-all.mjs`; the artifact-generating runtime chunk step inside that profile is `node scripts/tsdown-build.mjs`, which writes repo-local `dist` / `dist-runtime` output and is the narrowest candidate for M3H artifact parity.

## Blocker

The source checkout is clean but not build-ready locally:

- `packageManager`: `pnpm@10.33.2+sha512...`
- `pnpm --version`: command not found
- `corepack --version`: `0.34.6`
- `node_modules`: absent
- `node_modules/.bin/tsdown`: absent
- `dist`: absent
- `dist-runtime`: absent

Using corepack to activate pnpm and then installing dependencies would download/mutate dependency state. M3H did not authorize dependency installation, and the prompt says to prefer a blocked result with exact missing dependency evidence over unsafe install if dependencies are missing.

## Decision

No safe build command was executed. M3H stops at `BLOCKED_M3H_BUILD_COMMAND_UNAVAILABLE`.

## Safety counters

- Installed runtime hash before/after: `6567099cf446f8675a00dd6a800b786013d0effbaae5c1b633d528272c0ab014` / `6567099cf446f8675a00dd6a800b786013d0effbaae5c1b633d528272c0ab014`
- Installed dist mutation count: `0`
- Production install/apply count: `0`
- Gateway restart count: `0`
- Provider/model live execution count: `0`
- Telegram send count: `0`
- External-send count: `0`
- Real write tool count outside evidence artifacts/build outputs: `0`
- Production runtime/config mutation count: `0`
- Memory mutation count: `0`
- Context Bridge mutation count: `0`
