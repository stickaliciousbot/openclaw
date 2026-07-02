# M6 OpenClaw Adapter Implementation Plan

Status: `IN_PROGRESS_IMPLEMENTED_STATIC_VALIDATION_PENDING`

Generated: 2026-07-02 19:55 AEST / 2026-07-02T09:55:00Z

## Approval

Stick approved M6 on 2026-07-02 after M5 local serverization evidence was pushed.

## Scope

M6 wires the Node app to a safe OpenClaw adapter surface.

Implemented adapter modes:

- `OPENCLAW_MODE=echo` — existing local echo path.
- `OPENCLAW_MODE=infer` — default safe OpenClaw raw model CLI shape: `openclaw infer model run --prompt {prompt} --json`.
- `OPENCLAW_MODE=agent` — supported command shape: `openclaw agent --message {prompt} --json`, available for later use but not the default M6 smoke.
- `OPENCLAW_MODE=cli` — legacy stdout mode for explicit operator-provided commands.

M6 validation uses a fixture OpenClaw CLI inside the sandbox. This proves the Node adapter, JSON parsing, safe process spawning, prompt passing, and TTS voice path without making provider calls or requiring production Gateway/session state while the XTTS model is loaded.

## Explicit non-scope

M6 does **not** include:

- live provider inference call;
- production Gateway mutation;
- Gateway restart;
- runtime routing/default/fallback mutation;
- NOA adapter;
- STT;
- Android;
- persistent XTTS/Node service install;
- host-PC Tailscale proxy/user-testing exposure;
- Telegram/runtime sends.

A live OpenClaw/Gateway/provider smoke can be a later explicit gate if Stick wants it.

## Discovery evidence

CLI/docs discovery found:

- `openclaw agent --message <text> --json` is the full agent/session surface.
- `openclaw infer model run --prompt "..." --json` is the canonical headless/raw model inference surface.
- Docs state `infer model run --prompt` is the narrowest CLI smoke for model/provider/auth health, while `openclaw agent` is for full agent context/tools/memory/session transcript.

M6 therefore implements `infer` as the default adapter surface and leaves `agent` as explicit opt-in.

## Implementation files

- `src/openclaw-adapter.js` — spawn-based safe adapter.
- `server.js` — uses `askOpenClaw(text, config)` instead of inline CLI code.
- `src/config.js` — adds timeout/stdout-limit fields and mode-specific default args.
- `test/openclaw-adapter.test.mjs` — adapter safety and JSON parsing tests.
- `scripts/m6-sandboxed-openclaw-adapter-smoke.sh` — local XTTS + Node + fixture OpenClaw adapter smoke.
- `package.json` — adds `m6:smoke` and includes M6 checks.

## Adapter safety gates

- `spawn(file,args,{shell:false})`; no shell interpolation.
- `{prompt}` placeholder required in configured args.
- bounded args count.
- bounded stdout/stderr.
- timeout with process kill.
- whitelisted environment only.
- non-zero exit fails closed.
- JSON output must contain extractable text for `infer`/`agent` modes.
- prompt with shell metacharacters is passed as argv and tested not to execute.

## Planned validation gates

1. Static checks:
   - syntax checks;
   - existing hardening tests;
   - adapter tests;
   - M5/M6 shell syntax checks;
   - Python compile check.
2. M6 sandbox smoke:
   - local XTTS `/ready` true;
   - Node app runs with `OPENCLAW_MODE=infer`;
   - fixture CLI receives prompt via argv and returns JSON;
   - Node `/api/chat` returns fixture OpenClaw text;
   - voice audio URL returned;
   - generated WAV hash/file type captured;
   - no live provider/Gateway calls;
   - external network blocked/unavailable;
   - secret dirs hidden;
   - model/speaker read-only.
3. Update closeout/status/notebooks/lessons.
4. Guarded commit/push of M6 code+evidence only.

## Current state

Implementation files have been written. Static validation is pending native approval.
