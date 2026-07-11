# M3H Build Artifact Parity Retry

Status: `PASS_M3H_BUILD_ARTIFACT_PARITY_NO_APPLY_RETRY`
Generated: `2026-07-11T23:22:14Z`

## Build

Executed from source worktree only:

```bash
env npm_execpath=/home/stickai/.cache/node/corepack/v1/pnpm/10.33.2/bin/pnpm.cjs node scripts/tsdown-build.mjs
```

The original direct candidate `node scripts/tsdown-build.mjs` failed before build with `spawn pnpm ENOENT` because the hydrated package manager was Corepack-managed and bare `pnpm` was not on PATH. The successful invocation used the same build wrapper with `npm_execpath` set to Corepack's cached `pnpm.cjs`; no global pnpm install was performed.

## Selected generated artifact

- Path: `dist/agent-runner.runtime-DT4NbowI.js`
- SHA256: `76d82c785f61d3e0af44db2d36fa3c555e4814d07b27df175bd346f859f2d847`
- Size: `210529` bytes
- Relation: generated replacement for installed `agent-runner.runtime-a09vVD0N.js`; chunk hash changed to `agent-runner.runtime-DT4NbowI.js`.
- Source map: not present.

## Parity

The generated artifact contains:

- `followup-runner`
- `createFollowupRunner`
- `runWithModelFallback`
- `runEmbeddedPiAgent`
- `maybeRunUmcV1ShadowObserveOnly`
- gating values `observe_no_send`, `fixture_only`, `no_send`, `mock_only`, `forbidden`

The compiled hook is disabled by default because `maybeRunUmcV1ShadowObserveOnly` returns `{ enabled: false }` unless `isUmcV1ShadowObserveOnlyEnabled(env = process.env)` sees all fixture env gates set to the no-send/mock/forbidden values. Receipt content records `sent: false`, provider execution count `0`, Telegram send count `0`, external send count `0`, and real write tool count `0`.

Placement evidence: hook marker at byte offset `137307`; later provider/model execution markers include `runWithModelFallback` at offsets `[147511]` and `runEmbeddedPiAgent` at offsets `[147985]`.

## Safety

Installed runtime hash before/after: `6567099cf446f8675a00dd6a800b786013d0effbaae5c1b633d528272c0ab014` / `6567099cf446f8675a00dd6a800b786013d0effbaae5c1b633d528272c0ab014`. Production install/apply, Gateway restart, provider/model live execution, Telegram sends, external sends, production runtime/config mutation, production memory mutation, and Context Bridge mutation remained `0`.
