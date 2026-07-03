# Stickbot-TARS M2.5 hardening closeout

Classification: `STICKBOT_TARS_M25_HARDENING_CLOSEOUT_BLOCKED_FAIL_CLOSED`

Timestamp: 2026-07-02T02:35:51.888Z

## Commands / evidence

- Path verification: `pwd`, `realpath`, `stat` for project/docs/server/package/path-policy files.
- Runtime root readback: `/home/stickai/stickbot-voice` and `/home/stickai/stickbot-voice/xtts_models/tars` are WSL-native planned paths and currently missing.
- Available check: `npm run check` PASS.
- Static M2.5 gate scan written to `m25-hardening-closeout.json`.

## Gate results

- FAIL — `configFailClosedImplemented`
- PASS — `loopbackDefaultExists`
- FAIL — `unsafeLanRefusesStartup`
- PASS — `audioPathTraversalBlocked`
- FAIL — `uuidOnlyAudioRoute`
- PASS — `requestBodyLimitExists`
- FAIL — `separateAudioLimitExists`
- FAIL — `originHostCsrfChecksExist`
- PASS — `noBrowserWebSpeechApi`
- PASS — `noProviderDirectInBrowser`
- PASS — `gitignoreAudioGeneratedTraces`
- PASS — `gitignoreVenvModelsRuntime`
- PASS — `routeDefaultFallbackMutationSentinelsPlanned`
- PASS — `noOpenClawProductionMutationInCode`
- PASS — `noMntCInProjectPolicy`

## Failed/incomplete gates

- `configFailClosedImplemented`
- `unsafeLanRefusesStartup`
- `uuidOnlyAudioRoute`
- `separateAudioLimitExists`
- `originHostCsrfChecksExist`

## Evidence hashes

- /home/stickai/.openclaw/workspace/projects/stickbot-tars-smoke/server.js — sha256 `0415564e15257f2292f9c8f7dc879f53f9335b3d516b07117224394a06806579`
- /home/stickai/.openclaw/workspace/projects/stickbot-tars-smoke/public/app.js — sha256 `b8dffc801aaa9fb12f80c47138a9c9a3b7dce7bbc2007312059ed86a74bedca6`
- /home/stickai/.openclaw/workspace/projects/stickbot-tars-smoke/.gitignore — sha256 `5ab2fc03809ab4c7e06a2480687a5bee98b32bbe885a8289e7c166c6e1cb6212`
- /home/stickai/.openclaw/workspace/projects/stickbot-tars-smoke/package.json — sha256 `516fb48d5e91cb4ad72d513331ff4d8b2f882e8e9f897327a313461838a60690`
- /home/stickai/.openclaw/workspace/projects/stickbot-tars-smoke/docs/IMPLEMENTATION_PLAN.md — sha256 `5bd488b68efdad11e601212e939fca4ec8a8bbae7d4176e2d6e9e4ead6bb08e9`
- /home/stickai/.openclaw/workspace/projects/stickbot-tars-smoke/docs/LOW_LEVEL_DESIGN_AND_IMPLEMENTATION_PLAN.md — sha256 `56ff1f782b038d709f6fe43d5c00c8247aae4c0da3509f160272e8261e7169a5`

## Closeout

M2.5 hardening gates are incomplete; do not proceed to M3 model acquisition/load.

No OpenClaw production routing/config/default/fallback mutation, Gateway mutation/restart, model load, provider call, Android/STT jump, LAN exposure, or service exposure was performed.
