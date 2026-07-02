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

M6 preservation:

- Commit `d1297b5ca81c7f952eb07a99fe92e1d2b7b37511` pushed and remote head verified.
- Marker: `STICKBOT_TARS_M6_EVIDENCE_PUSH_PASS`.

## M7 — local STT adapter contract

Status: `STICKBOT_TARS_M7_LOCAL_STT_FIXTURE_CONTRACT_PASS_REAL_ENGINE_BLOCKED_READY_FOR_STT_ENGINE_ACQUISITION`

Approval:

- Stick approved M7 on 2026-07-02.

Discovery:

- Command/session `21ac704a` / `young-crustacean` completed.
- `ffmpeg`, `ffprobe`, `whisper-cli`, `whisper-cpp`, `whisper`, `whisperx`, `faster-whisper`: missing.
- System Python packages `faster_whisper`, `whisper`, `torch`, `torchaudio`, `soundfile`: missing.
- No local STT model dirs found under `/home/stickai/stickbot-voice/stt_models`, `~/.cache/whisper`, or `~/.cache/huggingface`.

Decision:

- Real local transcription is blocked until a local STT engine/model is acquired in a separate approved milestone.
- Safe M7 progress path is STT adapter contract + fixture `/api/stt` integration only; no cloud STT, no model download, no installs.

Implementation files:

- `src/stt-adapter.js`
- `test/stt-adapter.test.mjs`
- `scripts/m7-sandboxed-stt-fixture-smoke.sh`
- `docs/m7-local-stt/M7_LOCAL_STT_IMPLEMENTATION_PLAN.md`
- updates to `server.js`, `src/config.js`, `public/app.js`, and `package.json`.

Static validation:

- Command/session `0e287a97` / `salty-atlas` passed.
- Tests: 34/34 PASS.
- Marker: `STICKBOT_TARS_M7_STATIC_CHECK_PASS`.

M7 fixture smoke validation:

- Command/session `3291be75` / `quick-reef` passed.
- Marker: `STICKBOT_TARS_M7_SANDBOXED_STT_FIXTURE_SMOKE_COMMAND_PASS`.
- Result classification: `STICKBOT_TARS_M7_LOCAL_STT_FIXTURE_CONTRACT_PASS_REAL_ENGINE_BLOCKED`.
- `/api/stt`: HTTP 200; `sttMode:fixture`; transcript `M7 fixture transcript`; `cloudSpeechApi:false`; `browserWebSpeechApi:false`.
- Captured audio SHA256: `2976da01e205a110c9fa41d47659e238a5c6d3c3f3137582f2949853faa201dd`.
- Captured audio bytes: `3244`, mono 16 kHz PCM WAV.
- Boundary remained intact: network blocked/unavailable, secret dirs hidden, sandbox workspace.

Closeout artifacts:

- `docs/m7-local-stt/M7_LOCAL_STT_FIXTURE_CONTRACT_PASS.md`
- `docs/m7-local-stt/evidence_manifest.json`
- `docs/m7-local-stt/result.json`
- `docs/m7-local-stt/stt-fixture-smoke.json`
- `docs/m7-local-stt/captured-audio.sha256`
- `docs/m7-local-stt/captured-audio.stat`
- `docs/m7-local-stt/captured-audio.file`

Next required milestone for real transcription:

## M7A/M7B — local STT engine path

Stick approved the stack direction on 2026-07-02:

- M7A target: `STICKBOT_TARS_M7A_LOCAL_AUDIO_NORMALIZATION_PROVENANCE_PASS`.
- M7B target: `STICKBOT_TARS_M7B_WHISPERCPP_LOCAL_STT_FIXTURE_PASS`.
- Primary engine: `whisper.cpp`.
- Smoke model: `ggml-base.en.bin`.
- Usable local demo model: `ggml-small.en.bin`.
- Normalizer: WSL-local `ffmpeg` with version/hash/provenance recorded.
- Optional later: `faster-whisper` if CUDA is healthy; `sherpa-onnx` for Android/native; Ollama only for transcript cleanup/intent routing, not primary STT.
- Community Ollama Whisper models rejected as core substrate for now due weaker provenance and less standard audio-ingestion contract.

Hard boundary: no OpenClaw mutation, no Gateway/NOA mutation/restart, no cloud STT, no browser Web Speech API, no Android/LAN/Tailscale exposure, no persistent service install, no `/mnt/c` model/audio/runtime paths, no audio/model/cache/venv artifacts committed.

Plan artifact: `docs/m7-local-stt/M7A_M7B_LOCAL_STT_ENGINE_PLAN.md`.

M7A outcome:

- Final classification: `STICKBOT_TARS_M7A_LOCAL_AUDIO_NORMALIZATION_PROVENANCE_PASS`.
- Preflight `4e509d14` / `nova-ocean`: no ffmpeg/ffprobe and no apt ffmpeg package found.
- First bundle `fb637f42` stopped before install because one new normalizer test failed; failure was a test-harness ordering bug, not normalizer behavior.
- Repaired test harness; session `faint-basil` then showed `39/39` tests PASS before stopping at sudo TTY/elevated restriction.
- Elevated apt unavailable from Telegram runtime, so approved fallback used: John Van Sickle static FFmpeg release amd64 under `/home/stickai/stickbot-voice/tools/ffmpeg-static/...`.
- Static source posture: GPLv3 static build, acceptable for private/dev validation only, not future distributable default.
- Download tarball SHA256: `abda8d77ce8309141f83ab8edf0596834087c52467f6badf376a6a2a4c87cf67`; upstream MD5 `7fa72b652e19bf84c9461e332ea1cdf3` checked OK.
- FFmpeg SHA256: `e7e7fb30477f717e6f55f9180a70386c62677ef8a4d4d1a5d948f4098aa3eb99`.
- FFprobe SHA256: `4f231a1960d83e403d08f7971e271707bec278a9ae18e21b8b5b03186668450d`.
- M7A smoke `02aed404` / `glow-valley` passed with marker `STICKBOT_TARS_M7A_STATIC_FFMPEG_ACQUIRE_AND_NORMALIZE_PASS`.
- Normalized fixture WAV: SHA256 `38e3b264d99a035f168d6913520d2541a943c6a931e3f896882daf756b66fb7f`, 32078 bytes, `pcm_s16le`, 16000 Hz, 1 channel.
- Boundary preserved: network blocked/unavailable during sandbox smoke, secret dirs hidden, no cloud STT, no browser Web Speech API, no OpenClaw mutation.
- Evidence: `docs/m7-local-stt/m7a-audio-normalization/M7A_LOCAL_AUDIO_NORMALIZATION_PROVENANCE_PASS.md` and `docs/m7-local-stt/m7a-audio-normalization/evidence_manifest.json`.

M7B outcome:

- Final classification: `STICKBOT_TARS_M7B_WHISPERCPP_LOCAL_STT_FIXTURE_PASS`.
- Preflight `540f891f` / `swift-slug`: branch/head clean at `67d1155dddba50c26e691eb329ea9949432dbf26`; `cmake` missing; `make/gcc/g++/curl/python3` present; M7A FFmpeg present; no whisper tools/models existed.
- Acquisition/static validation `73997222` / `grand-pine`: `npm run check` passed `39/39`; whisper.cpp `v1.9.1` Ubuntu x64 release asset hash matched expected GitHub API digest `f3bf3b4369a99b54665b0f19b88483b30de27f25963b0414235dea03198515c5`; `ggml-base.en.bin` model acquired.
- Selected binary: `/home/stickai/stickbot-voice/tools/whisper.cpp/v1.9.1-ubuntu-x64/extract/whisper-bin-ubuntu-x64/whisper-cli`, SHA256 `427dfb509f2c04d0f01c101978b5666102c6f7e3abf2a236452db5939f5b533a`.
- Model: `/home/stickai/stickbot-voice/stt_models/whisper.cpp/ggml-base.en.bin`, SHA256 `a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002`, bytes `147964211`.
- R1 failed safely because deprecated `main` was selected and exited nonzero; repaired by using `whisper-cli` and blocking `main` in the smoke script.
- R2 proved local transcription worked, but normalization was not applied because `STT_NORMALIZE_AUDIO=1` parsed false; repaired to `STT_NORMALIZE_AUDIO=true` and added a hard assertion that `normalizedLocal` is true.
- R3 smoke `aecf89d6` / `nova-bison` passed with marker `STICKBOT_TARS_M7B_WHISPERCPP_LOCAL_STT_SMOKE_PASS_R3`: `/api/stt` HTTP 200, `sttMode:cli`, `normalizedLocal:true`, transcript chars `42`, transcript SHA256 `3e1f84be507525854b4acd7d9074dd1c7c55478130609fab0d509f97b6420075`, normalized WAV SHA256 `2cdd6e22cbf67805f03d275881955edfa7cd8deada3b818e7fff827010fab4ad`, probe `pcm_s16le` 16000 Hz mono.
- Boundary preserved: network blocked/unavailable during transcription, secret dirs hidden, no cloud STT, no browser Web Speech API, no OpenClaw/Gateway/NOA mutation, no raw transcript committed; raw transcript existed only under `/tmp` trace.
- Evidence: `docs/m7-local-stt/m7b-whispercpp-local-stt/M7B_WHISPERCPP_LOCAL_STT_FIXTURE_PASS.md` and `docs/m7-local-stt/m7b-whispercpp-local-stt/evidence_manifest.json`.

Next possible target: `M7C_SMALL_EN_USABLE_DEMO_NOT_STARTED_REQUIRES_SEPARATE_APPROVAL`.
