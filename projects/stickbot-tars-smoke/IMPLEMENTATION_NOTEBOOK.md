# Stickbot-TARS Implementation Notebook

Last updated: 2026-07-02 18:18 AEST / 2026-07-02T08:18:00Z

## Standing documentation rule

For every Stickbot-TARS milestone, keep these records current before final closeout:

1. `IMPLEMENTATION_NOTEBOOK.md` — what changed, milestone state, commits/artifacts.
2. `docs/TROUBLESHOOTING_AND_REPAIR_NOTEBOOK.md` — bugs, failed attempts, root cause, repair, validation.
3. `memory/lessons-learned-stickbot-tars-voice-demo-2026-07-02.md` — durable cross-session lessons worth remembering.
4. Project-local status/closeout JSON/Markdown under `projects/stickbot-tars-smoke/state/` and `projects/stickbot-tars-smoke/docs/`.

Do not treat a milestone as closed until the notebook/repair/lesson trail is accurate enough to resume from cold context.

## Boundaries that remain active

- No M4+ model load outside a constrained boundary.
- No OpenClaw/Gateway/NOA production config/routing/default/fallback mutation.
- No model binaries committed.
- No generated audio/traces/cache/venv/node_modules committed.
- No memory/context bridge source files staged unless separately approved.
- Do not use `/mnt/c` for runtime/model/audio/traces/venv/node_modules.
- Do not bind TARS to `8787`; NOA owns that port.
- Browser/Android must not call providers directly or use browser Web Speech API.

## Milestone ledger

### M2.5 — hardening repair

Status: `STICKBOT_TARS_M25_HARDENING_CLOSEOUT_PASS_READY_FOR_M3`

Branch: `feature/stickbot-tars-m25-hardening-repair`

Commit: `5c29204016bebd11da4ffa6dc20bb99aba9676a4`

Summary:

- Added fail-closed config validation.
- Enforced loopback-by-default / explicit LAN opt-in.
- Refused reserved port `8787`.
- Enforced UUID-only `/audio/:file` policy.
- Split JSON/text and audio upload limits.
- Added Origin + CSRF/session nonce protection.
- Added blocker tests.
- Validation passed: `npm run check`, 19/19 tests, guarded local echo smoke on `127.0.0.1:19888`, `git diff --check`, no `/mnt/c` in runtime repair files.

Artifacts:

- `docs/M25_HARDENING_CLOSEOUT.md`
- `docs/M25_REPAIR_PLAN.md`
- `docs/REPO_AUDIT_READ_ONLY_CLOSEOUT.md`
- `state/status.json`

### M3 — model acquisition, hash, provenance, no load

Status: `STICKBOT_TARS_M3_MODEL_ACQUIRED_HASHED_PROVENANCE_RECORDED_NO_LOAD_PASS`

Commit: `0fa3b732e70d403a4b0597c225a41d2f6043e452`

Summary:

- Downloaded pinned `Pyrater/TARS` model artifacts from Hugging Face revision `7a1517d76eb0db89828b1c812682fa75125e5de7`.
- Stored under WSL-native `/home/stickai/stickbot-voice` paths.
- Wrote SHA256 manifest and provenance closeout.
- No model load, no XTTS start, no M4 during M3.

Key files:

- Runtime model root: `/home/stickai/stickbot-voice/xtts_models/tars`
- Speaker root: `/home/stickai/stickbot-voice/speakers`
- Output root: `/home/stickai/stickbot-voice/output`
- Manifest: `docs/m3-model-provenance/tars-model-provenance-manifest.json`
- SHA list: `docs/m3-model-provenance/sha256sum.txt`
- Closeout: `docs/m3-model-provenance/M3_MODEL_ACQUIRED_HASHED_PROVENANCE_RECORDED_NO_LOAD.md`

Key hash:

- `model.pth` SHA256: `fbcbdae803777b0dea5c02b6309786b8dc06fde0120de8df4159151a11b51688`
- `model.pth` bytes: `1,863,948,438`

### M4 — sandboxed local XTTS load

Status: `STICKBOT_TARS_M4_SANDBOXED_XTTS_LOCAL_LOAD_PASS_READY_FOR_M5_PLANNING_ONLY`

M4 hard boundary decisions:

- Dedicated `stickbot-tars` Unix user would be preferred, but Telegram context cannot use elevated tool mode and `sudo` requires a TTY/password.
- Plain `unshare -Urn` was rejected because it still saw `/home/stickai/.openclaw`.
- Accepted fallback boundary is `unshare -Urnm` with explicit private mount namespace:
  - TARS model dir bind-mounted read-only.
  - Speaker dir bind-mounted read-only.
  - Output dir bind-mounted writable.
  - `/home/stickai/.openclaw`, `.ssh`, `.codex`, `.config` hidden via empty bind mounts.
  - Network namespace blocks DNS/network after dependency install.

M4 dependency progress:

- `xtts-api-server` install failed because dependency `pyaudio` needed Python dev headers (`Python.h`). No model load occurred.
- Switched to minimal direct Coqui path.
- `coqui-tts==0.27.5` installed into `/home/stickai/stickbot-voice/venv-coqui`.
- `torch==2.12.1+cpu`, `torchaudio==2.11.0+cpu` installed first.
- `transformers==5.12.1` broke XTTS import: missing `isin_mps_friendly`.
- Pinned `transformers>=4.57,<5`, resolved to `transformers==4.57.6`, which restored `isin_mps_friendly`.
- Coqui then required `torchcodec` for PyTorch >=2.9.
- Installed `torchcodec==0.14.0`, but it failed to load native `libtorchcodec_core*.so` with current Torch stack due missing `libnvrtc.so.13` / compatibility mismatch.
- Downgraded CPU Torch/Torchaudio to `2.8.0+cpu` to avoid the PyTorch >=2.9 torchcodec import path.
- Verification passed: `torch 2.8.0+cpu`, `torchaudio 2.8.0+cpu`, `cuda_available False`, `TTS_import=ok`.
- R4 sandboxed first-load/generation passed.
- Result: `modelLoaded=true`, `wavGenerated=true`, `outputBytes=95788`, `sampleRate=24000`, CPU-only.
- Closeout: `docs/m4-sandboxed-load/M4_SANDBOXED_XTTS_LOCAL_LOAD_PASS.md`.

M4 attempts so far:

1. `ac38812a` — blocked before model load: `ImportError isin_mps_friendly` with Transformers 5.x.
2. `76d57e74` — blocked before model load: Coqui requires `torchcodec` for PyTorch 2.12.
3. `355676ea` — blocked before model load: `torchcodec` native library failed to load due Torch/TorchCodec/libnvrtc compatibility.
4. `76573901` — PASS: model loaded and first WAV generated inside the accepted boundary.

Important: each failed attempt kept the no-network / secret-hidden / read-only-model boundary active. The first successful model load occurred only in R4 after dependency repair.

## M5 — local serverization / echo voice integration

Status: `STICKBOT_TARS_M5_LOCAL_SERVERIZATION_NODE_VOICE_PASS_READY_FOR_M6_PLANNING_ONLY`

Approval:

- Stick approved M5/integration/serverization on 2026-07-02.

Scope:

- Local-only serverization.
- Minimal loopback XTTS HTTP server with `GET /health`, `GET /ready`, and `POST /tts_to_audio/`.
- Node echo-mode integration smoke inside the accepted `unshare -Urnm` boundary.
- No OpenClaw/Gateway/NOA/STT/Android production mutation or integration.

Implementation files:

- `scripts/xtts-local-server.py`
- `scripts/m5-sandboxed-node-voice-smoke.sh`
- `docs/m5-local-serverization/M5_LOCAL_SERVERIZATION_IMPLEMENTATION_PLAN.md`
- `package.json` script `m5:smoke`

Static validation:

- Command/session `0e9bda9a` / `calm-ocean` passed.
- Existing Node tests: 19/19 PASS.
- Marker: `STICKBOT_TARS_M5_STATIC_CHECK_PASS`.
- R2 static recheck command/session `f9412916` / `sharp-crest` passed.
- Existing Node tests: 19/19 PASS.
- Marker: `STICKBOT_TARS_M5_R2_STATIC_CHECK_PASS`.

R1 safe failure and repair:

- R1 sandbox smoke command/session `b01b48c0` / `dawn-ember` failed safely.
- XTTS model loaded and server listened, but `/ready` polling timed out because loopback was down inside the private network namespace.
- Cleanup also referenced unset `node_pid` because Node had not started.
- Repair: bring `lo` up inside namespace and make cleanup tolerate unset PIDs.

M5 PASS validation:

- R2 sandbox smoke command/session `655a4a74` / `vivid-cove` passed.
- Marker: `STICKBOT_TARS_M5_R2_SANDBOXED_NODE_VOICE_SMOKE_COMMAND_PASS`.
- Result classification: `STICKBOT_TARS_M5_LOCAL_SERVERIZATION_NODE_VOICE_PASS`.
- XTTS `/ready`: `ok:true`, model loaded at `2026-07-02T09:36:59Z`.
- Node `/api/chat`: HTTP 200, text `Echo smoke response: M5 local voice echo smoke`, audio URL `/audio/41712ff0-d842-4e12-9228-5fe33536f2a2.wav`, no audio error.
- Generated WAV SHA256: `1daf103c5e9de8dbeef2a373638b843ff8e01429b415c6ae279853c9908712ec`.
- Generated WAV bytes: `142380`, mono 24 kHz PCM WAV.
- Boundary remained intact: network blocked/unavailable, secret dirs hidden, model/speaker read-only, loopback only, Node workspace sandboxed under `/tmp/tars-m5-boundary/workspace`.

Closeout artifacts:

- `docs/m5-local-serverization/M5_LOCAL_SERVERIZATION_NODE_VOICE_PASS.md`
- `docs/m5-local-serverization/evidence_manifest.json`
- `docs/m5-local-serverization/result.json`
- `docs/m5-local-serverization/node-voice-smoke.json`
- `docs/m5-local-serverization/xtts-ready.json`
- `docs/m5-local-serverization/generated-audio.sha256`
- `docs/m5-local-serverization/generated-audio.stat`
- `docs/m5-local-serverization/generated-audio.file`

Future user-testing LAN requirement:

Stick clarified that before user testing, the app must be reachable from phone and laptop browsers, similar to prior local demo/Douglas Bagmaker expectations. This is not part of M5 local-loopback PASS. Later preferred path is host-PC proxy over the host PC's Tailscale connection/IP: the app does not need to run on a Tailscale-native host and can remain local/WSL-bound. Add a later approved LAN/Tailscale milestone with explicit `VOICE_DEMO_ALLOW_LAN=true` only if needed, safe non-8787 port, restrictive host proxy/firewall evidence, Origin/Host allowlist, CSRF retained, no wildcard CORS, XTTS kept loopback behind Node, and phone+laptop browser validation before user testing.

## M6 — OpenClaw adapter

Status: `STICKBOT_TARS_M6_OPENCLAW_ADAPTER_FIXTURE_VOICE_PASS_READY_FOR_M7_PLANNING_ONLY`

Approval:

- Stick approved M6 on 2026-07-02.

Scope:

- Safe Node OpenClaw adapter only.
- Default raw inference surface: `openclaw infer model run --prompt {prompt} --json`.
- Explicit agent mode supported for later: `openclaw agent --message {prompt} --json`.
- M6 smoke uses a fixture OpenClaw CLI inside the sandbox to prove adapter/process/JSON/voice wiring without live provider/Gateway calls while the TARS model is loaded.

Implementation files:

- `src/openclaw-adapter.js`
- `test/openclaw-adapter.test.mjs`
- `scripts/m6-sandboxed-openclaw-adapter-smoke.sh`
- `docs/m6-openclaw-adapter/M6_OPENCLAW_ADAPTER_IMPLEMENTATION_PLAN.md`
- updates to `server.js`, `src/config.js`, and `package.json`.

Static validation:

- Command/session `718a054e` / `glow-ocean` passed.
- Tests: 27/27 PASS.
- Marker: `STICKBOT_TARS_M6_STATIC_CHECK_PASS`.

M6 PASS validation:

- Command/session `9932f947` / `fresh-daisy` passed.
- Marker: `STICKBOT_TARS_M6_SANDBOXED_OPENCLAW_ADAPTER_SMOKE_COMMAND_PASS`.
- Result classification: `STICKBOT_TARS_M6_OPENCLAW_ADAPTER_FIXTURE_VOICE_PASS`.
- Adapter mode: `infer`.
- Adapter surface: `openclaw infer model run --prompt {prompt} --json`.
- Fixture OpenClaw CLI used: true.
- Live provider called: false.
- Gateway called: false.
- Node `/api/chat`: HTTP 200; text `OpenClaw adapter fixture response: M6 OpenClaw adapter fixture voice smoke`; audio URL `/audio/f640fa4b-115d-4063-9ea8-511d998d1592.wav`; no audio error.
- Generated WAV SHA256: `fc7da588940bbe2238dcc91b9dc5156d36cbcaafcc49bbf606ebbdc3427ce5d0`.
- Generated WAV bytes: `111148`, mono 24 kHz PCM WAV.
- Boundary remained intact: network blocked/unavailable, secret dirs hidden, model/speaker read-only, loopback only, Node workspace sandboxed under `/tmp/tars-m6-boundary/workspace`.

Closeout artifacts:

- `docs/m6-openclaw-adapter/M6_OPENCLAW_ADAPTER_FIXTURE_VOICE_PASS.md`
- `docs/m6-openclaw-adapter/evidence_manifest.json`
- `docs/m6-openclaw-adapter/result.json`
- `docs/m6-openclaw-adapter/node-openclaw-voice-smoke.json`
- `docs/m6-openclaw-adapter/xtts-ready.json`
- `docs/m6-openclaw-adapter/generated-audio.sha256`
- `docs/m6-openclaw-adapter/generated-audio.stat`
- `docs/m6-openclaw-adapter/generated-audio.file`

Next action:

Run final validation and preserve M6 code/evidence with a guarded commit/push. M7, live provider/Gateway smoke, STT, Android, persistent service install, and Tailscale/user-testing exposure are not started and require separate approval.
