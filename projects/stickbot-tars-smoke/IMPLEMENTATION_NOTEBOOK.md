# Stickbot-TARS Implementation Notebook

Last updated: 2026-07-03 21:15 AEST / 2026-07-03T11:15:00Z

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

### M7T — live prosody mood score and emotional sheet music

Status: `STICKBOT_TARS_M7T_LIVE_PROSODY_MOOD_SCORE_AND_EMOTIONAL_SHEET_MUSIC_PASS`

Summary:

- Added deterministic live prosody cue layer in `src/prosody/live-prosody-cue-layer.js`.
- The cue layer derives mood score, dominant cue, cue sequence, per-chunk cue glyphs, dynamic marks, contour, tempo, emotional color, intensity, rest glyphs, pause duration, and text hashes from the existing canonical prosody score.
- Integrated public cue metadata into `buildTarsProsodyPlan()` and the browser UI live voice line.
- Preserved canonical text boundaries: canonical text hash unchanged, `textRewriteAllowed: false`, public cue layer exposes `textSha256` only and no raw chunk text.
- Updated rehydrator/status/closeout docs so future sessions know M7T is current and next milestone is `AUDIO_FIRST_MULTIPLEXED_PRODUCTION_STREAMING_ARCHITECTURE`.

Validation:

- Focused syntax and prosody tests: `9/9 PASS`.
- Full `npm run check`: `PASS`.
- Live health/capability boundary remained local: HTTPS `19890`, STT mode `cli`, XTTS loopback ready, browser Web Speech API false, cloud speech API false.

Artifacts:

- `docs/m7-local-stt/m7t-live-prosody-mood-score/M7T_LIVE_PROSODY_MOOD_SCORE_AND_EMOTIONAL_SHEET_MUSIC_PASS.md`
- `src/prosody/live-prosody-cue-layer.js`
- `state/status.json` (`m7t`)

Next:

- `AUDIO_FIRST_MULTIPLEXED_PRODUCTION_STREAMING_ARCHITECTURE`

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

M7C outcome:

- Final classification: `STICKBOT_TARS_M7C_SMALL_EN_USABLE_DEMO_PASS`.
- Approval/run `655d2910` / `tide-mist` created M7C smoke harness, updated `package.json`, ran static checks (`39/39 PASS`), downloaded `ggml-small.en.bin`, and passed the local small.en STT smoke.
- Model: `/home/stickai/stickbot-voice/stt_models/whisper.cpp/ggml-small.en.bin`, SHA256 `c6138d6d58ecc8322097e0f987c32f1be8bb0a18532a3f88f734d1bbf9c41e5d`, bytes `487614201`, excluded from git.
- Reused M7B `whisper-cli` SHA256 `427dfb509f2c04d0f01c101978b5666102c6f7e3abf2a236452db5939f5b533a`.
- Smoke passed: `/api/stt` HTTP 200, `sttMode:cli`, `normalizedLocal:true`, transcript chars `45`, transcript SHA256 `44b7adbb95a5d4d7129029ad17b4b2cc1bc3429e1b9057f3ad3640ef234a2fac`, normalized audio SHA256 `2cdd6e22cbf67805f03d275881955edfa7cd8deada3b818e7fff827010fab4ad`, probe `pcm_s16le` 16000 Hz mono.
- Boundary preserved: network blocked/unavailable during transcription, secret dirs hidden, no cloud STT, no browser Web Speech API, no OpenClaw/Gateway/NOA mutation, no raw transcript committed; raw transcript existed only under `/tmp` trace.
- Evidence: `docs/m7-local-stt/m7c-small-en-usable-demo/M7C_SMALL_EN_USABLE_DEMO_PASS.md` and `docs/m7-local-stt/m7c-small-en-usable-demo/evidence_manifest.json`.

Next possible target: `M7D_REAL_MIC_LOCAL_DEMO_NOT_STARTED_REQUIRES_SEPARATE_APPROVAL`.

## M7D — real mic HTTPS LAN demo

Status: `STICKBOT_TARS_M7D_HTTPS_LAN_REAL_MIC_STT_ECHO_PASS_OPTIONAL_XTTS_OUTPUT_BLOCKED`

Summary:

- Implemented `scripts/m7d-local-real-mic-demo.sh`, browser mic capture, local FFmpeg normalization, and local whisper.cpp `ggml-small.en.bin` STT behind the existing Node demo.
- Runtime location was WSL2 on Susie-Dell-Inspiron, not Windows-native Node. Windows Wi-Fi IP `192.168.1.107`; WSL IP `172.24.168.46`; Tailscale IP `100.119.233.106`.
- Windows `localhost:19890` working did not prove LAN reachability. Stick fixed LAN exposure with Windows `netsh interface portproxy` from `192.168.1.107:19890` to `172.24.168.46:19890` plus an inbound firewall rule.
- HTTPS LAN path `https://192.168.1.107:19890/` was operator-confirmed: mic capture/STT worked, transcript appeared, and echo send worked.
- Durable evidence intentionally preserves semantic confirmation only, not raw transcript.
- Plain HTTP LAN may load the page but is not a trustworthy mic origin; HTTPS/cert flow is the working LAN mic path.
- Added `/api/capabilities` so TARS voice output is disabled unless XTTS `/ready` is reachable.
- Closeout artifacts:
  - `docs/m7-local-stt/m7d-real-mic-local-demo/M7D_REAL_MIC_LOCAL_DEMO_PLAN.md`
  - `docs/m7-local-stt/m7d-real-mic-local-demo/M7D_REAL_MIC_LOCALHOST_DEMO_PASS.md`
  - `docs/m7-local-stt/m7d-real-mic-local-demo/M7D_HTTPS_LAN_REAL_MIC_STT_ECHO_PASS.md`
  - `docs/LOOPBACK_LAN_EXPOSURE_NOTEBOOK.md`

Boundaries held: no cloud STT, no browser Web Speech API, no OpenClaw/Gateway/NOA mutation, no `8787`, no raw transcript durable storage.

## M7E — HTTPS LAN TARS voice output

Status: `STICKBOT_TARS_M7E_HTTPS_LAN_TARS_VOICE_OUTPUT_PASS`

Summary:

- Started local XTTS backend loopback-only at `http://127.0.0.1:8020` behind the already-working HTTPS LAN Node frontend on port `19890`.
- XTTS was started via `scripts/m7e-start-xtts-loopback.sh` in a mount-isolated boundary with model/speaker read-only and `.openclaw`, `.ssh`, `.codex`, `.config` hidden.
- Approved run `15cc2145-71e1-4036-ad32-39b1866ebed1` / `sharp-mist` passed with marker `STICKBOT_TARS_M7E_HTTPS_LAN_TARS_VOICE_OUTPUT_SMOKE_PASS`.
- `/api/capabilities` reported `voice.enabled:true`, `reason:"xtts_ready"`, `detail:200`.
- HTTPS LAN-shaped `/api/chat` with `voice:true` returned `audioError:null` and `/audio/5a18bf48-d136-4cac-9656-fe03ebac82e3.wav`.
- Generated WAV SHA256 `2e8556b9bac193ce5efde9bbc5ba2553d52c7428473aee18dcb1c8eb568218f0`, bytes `73260`, type `RIFF WAVE audio, Microsoft PCM, 16 bit, mono 24000 Hz`.
- Closeout artifact: `docs/m7-local-stt/m7e-https-lan-xtts-voice-output/M7E_HTTPS_LAN_TARS_VOICE_OUTPUT_PASS.md`.

Boundary held: no cloud STT, no browser Web Speech API, no provider API, no OpenClaw/Gateway production mutation, no Gateway restart, no NOA touch, no `8787`, no generated audio committed.

## M7F — TARS-inspired prosody kernel

Status: `STICKBOT_TARS_M7F_PROSODY_KERNEL_LOCAL_CHECK_PASS`

Stick approved starting a prosody kernel on 2026-07-03 and clarified the governing boundary: capture voice likeness only, do not alter what Stickbot says.

Scope:

- Add local delivery metadata layer for TARS-inspired cadence/salience.
- Preserve canonical assistant text byte-for-byte.
- Add sentence chunking that reconstructs exactly to canonical text.
- Add salience annotation for status/risk/number/operator/mission-state spans.
- Add no-secret-speech guard before synthesis.
- Return public `voicePlan` summary from `/api/chat` when voice synthesis succeeds.
- Do not import external TARS-AI code/binaries in this milestone.

Reference findings from TARS-AI docs/source:

- v3 release notes mention TTS/STT refactor, Silero VAD, and sentence-level TTS chunk streaming.
- v3 config points to `faster-whisper` for STT and `piper` for TTS.
- v3 Piper TARS ONNX config reports sample rate `22050` and inference defaults `noise_scale:0.667`, `length_scale:1`, `noise_w:0.8`.

Implementation files:

- `src/voice/tars-prosody-profile.js`
- `src/voice/tars-salience-annotator.js`
- `src/voice/tars-sentence-chunker.js`
- `src/voice/tars-prosody-kernel.js`
- `test/tars-prosody-kernel.test.mjs`
- `docs/m7-local-stt/m7f-prosody-kernel/M7F_PROSODY_KERNEL_IMPLEMENTATION_PLAN.md`

Integration:

- `server.js` now builds a prosody plan before XTTS synthesis.
- The current XTTS call still receives canonical assistant text unchanged.
- If secret-like text is detected, synthesis is refused with `TARS_NO_SECRET_SPEECH_FAIL`.

Validation:

- Approved command/run: `7ca280ac-99a1-4363-8a82-baedadfea7c1` / `wild-kelp`.
- Result: exit `0`, tests `46/46 PASS`, status JSON parse PASS.
- Terminal marker: `STICKBOT_TARS_M7F_PROSODY_KERNEL_LOCAL_CHECK_PASS`.

Validated gates:

- `TARS_PROSODY_PROFILE_LOAD_PASS`
- `TARS_SENTENCE_CHUNKING_PASS`
- `TARS_STATUS_SALIENCE_PASS`
- `TARS_NO_SECRET_SPEECH_PASS`
- `TARS_CANONICAL_TEXT_UNCHANGED_PASS`

Closeout artifact:

- `docs/m7-local-stt/m7f-prosody-kernel/M7F_PROSODY_KERNEL_LOCAL_CHECK_PASS.md`

M7F local check is PASS. Future work requires separate approval: chunked synthesis/playback queue, FFmpeg rate/pitch/loudness post-processing, Faster-Whisper benchmark, Piper low-latency lane, live OpenClaw/Gateway/provider path, Android/phone packaging, persistent service install, or broader user-testing exposure.

## M7G — Local/private TARS prosody tuning console

Status: `STICKBOT_TARS_M7G_PROSODY_TUNING_CONSOLE_LOCAL_CHECK_PASS`

Implementation:

- Added `src/voice/tars-prosody-tuning.js` for local tuning state, slider sanitization/clamping, baseline/factory/active profile handling, and delivery metadata derivation.
- Added UI/API controls for pitch, timbre, speed, compression, verbal gait, verbosity, clip guard, global randomness, randomness threshold, and per-parameter randomness co-sliders.
- Added baseline actions: apply, establish baseline, restore baseline, and reset to factory default.
- Updated `server.js`, `public/index.html`, `public/app.js`, `src/voice/tars-prosody-kernel.js`, tests, and package check script.

Boundary:

- Canonical assistant text remains authoritative and unchanged.
- Tuning is delivery metadata only.
- XTTS still receives canonical text directly; audio post-processing/application is deferred to M7H/M7I.

Validation:

- `npm run check` PASS.
- Node tests: `50/50 PASS` at initial M7G closeout.

Closeout artifact:

- `docs/m7-local-stt/m7g-prosody-tuning-console/M7G_PROSODY_TUNING_CONSOLE_LOCAL_CHECK_PASS.md`

## M7G-R1 — Local prosody mood/preset matrix integration

Status: `STICKBOT_TARS_M7G_PROSODY_TUNING_MATRIX_LOCAL_CHECK_PASS`

Input:

- Stick supplied `stickbot_tars_prosody_tuning_matrix_v0_1.json` as local testing recommendations.
- Treated as reference data only, not prompt authority.

Implementation:

- Added `src/voice/tars-prosody-matrix.js` with 13 local mood presets, XTTS safe bounds, chunking recommendations, acceptance thresholds, and unknown-mood fallback to `baseline_deadpan`.
- Added mood preset selector to the tuning console.
- Extended active tuning summaries and public voice plans with mood id/label, chunking metadata, pause metadata, and XTTS recommendation metadata.
- Mood matrix can cap chunk size and affect delivery metadata. It cannot rewrite assistant text.

Validation:

- `npm run check` PASS.
- Node tests: `54/54 PASS`.
- New gates: `TARS_PROSODY_MATRIX_SCHEMA_PASS`, `TARS_PROSODY_MATRIX_XTTS_CLAMP_PASS`, `TARS_PROSODY_MATRIX_MOOD_DELIVERY_PASS`, `TARS_PROSODY_MATRIX_UNKNOWN_MOOD_FALLBACK_PASS`.

Next:

- `M7H_FFMPEG_AUDIO_POLISH_FROM_TUNING_STATE` should apply pitch/rate/loudness/compression/clip guard in the audio pipeline while preserving canonical text and local-only boundaries.

## M7G-R2 — JSON matrix controls and prosody sheet-music planning

Status: `STICKBOT_TARS_M7G_PROSODY_JSON_MATRIX_AND_SHEET_MUSIC_LOCAL_CHECK_PASS`

Implementation:

- Dashboard can now read the active prosody JSON matrix, upload a new JSON matrix, and reset to the built-in default JSON.
- Uploaded matrices are sanitized and persisted at `state/prosody-matrix.json` only when a user uploads one.
- Mood dropdown is dynamic from the active matrix, including expressive emoji-style tokens.
- Voice plans now include a per-chunk `prosodySheet`: chunk hash/range, selected mood, expression token, intensity, cues, XTTS recommendation parameters, delivery timing, and no-rewrite flags.
- Current speech path still sends canonical assistant text to XTTS as one request; the sheet is the control score for M7H/M7I chunked synthesis and live prosody application.

New endpoints:

- `GET /api/prosody/matrix`
- `POST /api/prosody/matrix`
- `POST /api/prosody/matrix/reset`

Validation:

- `npm run check` PASS.
- Node tests: `56/56 PASS`.
- New gates: `TARS_PROSODY_MATRIX_JSON_IMPORT_PASS`, `TARS_PROSODY_SHEET_MUSIC_PASS`.

## M7R — low-latency streaming transport / live repair trail

Status: `STICKBOT_TARS_M7R_LOW_LATENCY_STREAMING_TRANSPORT_LIVE_PASS`

Commit: `0b1366791`

Implementation:

- Added explicit low-latency transport metadata to realtime frame manifests:
  - schema `stickbot.tars.low-latency-transport.v1`
  - classification `STICKBOT_TARS_M7R_LOW_LATENCY_STREAMING_TRANSPORT_READY`
  - mode `browser_preload_queue_then_serial_playback`
  - queue-depth target `2`
  - first-audio target `1200ms`
  - inter-chunk-gap target `120ms`
- Updated browser playback to build a preloaded serial audio queue and display `STICKBOT_TARS_M7R_LOW_LATENCY_CLIENT_TELEMETRY` with first-play / max-gap / played-count data.
- Preserved final WAV fallback, M7Q partial local STT, and M7O barge-in semantics.
- Boundaries unchanged: local-only, no cloud STT, no browser Web Speech API, no OpenClaw/Gateway/NOA/provider mutation, no port `8787`.

Validation before live repair:

- Focused gate: `node --check src/audio/streaming-frame-interface.js`, `node --check public/app.js`, `node --test test/tars-dsp-stream-duplex.test.mjs` → `9/9 PASS`.
- Full gate: `npm run check` → `85/85 PASS`.
- Rehydrator: `47` sources, `missingSources: []`.

Live repair findings captured during M7R browser test:

1. **Foreground demo timeout can kill the server.**
   - Symptom: approved `scripts/m7d-local-real-mic-demo.sh` printed READY, then the exec wrapper timed out and `19890` went down.
   - Cause: the demo script intentionally runs foreground until Ctrl-C; bounded exec timeout terminated it.
   - Repair: use a managed/background process for live testing or a detached command that preserves the exact script environment. Verify with loopback + LAN `/health` after the wrapper exits.

2. **Detached restart must preserve the script-generated STT args.**
   - Symptom: browser partial/final STT showed `STT args must include a {file} placeholder`; audio was saved locally but local whisper was not invoked.
   - Cause: manual detached `node server.js` restart set `STT_BIN`/model paths but omitted `STT_ARGS_JSON` with the `{file}` placeholder. The harness normally generates this JSON.
   - Repair: restart Node with `STT_ARGS_JSON=["-m","/home/stickai/stickbot-voice/stt_models/whisper.cpp/ggml-small.en.bin","-f","{file}","-nt","-np","-l","en"]` or use the script path that generates it. Validation: real partial STT smoke returned `STICKBOT_TARS_M7Q_TRUE_PARTIAL_LOCAL_STT_LOOP_PASS`, `sttMode:cli`, `normalizedLocal:true`, `error:null`.

3. **Stuck browser Send is not the same as backend down.**
   - Symptom: browser remained on `Sending...` for several minutes with no voice output.
   - Evidence: backend health and XTTS `/ready` were green; one turn produced only `chunk-001.wav` and no final WAV; XTTS log showed `BrokenPipeError` during `/tts_to_audio/` after the client side abandoned the request.
   - Repair: do not stack repeated browser sends; run a bounded backend voice smoke. If backend smoke passes, instruct Stick to open a fresh/hard-refreshed tab rather than waiting on the stale request. If it fails, restart XTTS/Node cleanly.
   - Validation: bounded backend voice smoke completed in ~20 seconds, produced final WAV, and returned `STICKBOT_TARS_M7R_LOW_LATENCY_STREAMING_TRANSPORT_READY`.

Live PASS confirmation:

- Stick confirmed: “partial STT works, reconstruction works, send works, audio generation works, barge in works.”
- Stick provided strict telemetry readback/screenshots:
  - `Streaming telemetry: first play 267ms; max gap 255ms; played 2/2`
  - `STICKBOT_TARS_M7R_LOW_LATENCY_CLIENT_TELEMETRY; local-only, no transcript/audio cloud path.`
  - `Streaming transport: 2 chunk frames preloaded`
- Final classification: `STICKBOT_TARS_M7R_LOW_LATENCY_STREAMING_TRANSPORT_LIVE_PASS`.

Follow-up hardening remains recommended:

- If Send hangs again, patch UI/backend timeout/fail-fast recovery instead of accepting indefinite `Sending...`.

## 2026-07-03 — M7S live barge-in with real speech PASS

Status: `STICKBOT_TARS_M7S_LIVE_BARGE_IN_WITH_REAL_SPEECH_PASS`

Objective:

- Prove live spoken user interruption while TARS audio is playing, not only deterministic mic-start barge-in mechanics.

Preflight:

- Live server health passed on `https://127.0.0.1:19890/health`.
- Capabilities passed: `sttMode:cli`, voice enabled, partial local STT loop enabled, browser Web Speech API false, cloud speech API false.
- XTTS ready on `http://127.0.0.1:8020`, model loaded.

Live evidence from Stick screenshot/readback:

- Stick confirmed: “that worked. screenshot attached”.
- Partial STT: `Stick butt, I'm so sorry to interrupt you.`
- Partial STT metadata: `seq 0; local whisper slice; privacy guard: raw transcript durable storage is off.`
- Duplex state: `barge-in smoke listening`; privacy guard off.
- Mic state: `recording with local partial STT slices... tap the mic button again to stop and transcribe`.
- Playback stopped with reason: `M7O barge-in: mic capture started`.
- Streaming transport: `3 chunk frames preloaded`; mode `M7R browser_preload_queue_then_serial_playback`.
- Interrupted assistant text: `Echo smoke response: Okay, Stickbot, we're about to test M7S and I'm going to interrupt you. I don't mean to be rude.`
- Voice score: mood `TARS mission brief / marine commander`; streaming frames `3 / target streaming_full_duplex_mesh`.

Boundaries preserved:

- local-only true;
- raw transcript durable storage false;
- browser Web Speech API false;
- cloud speech API false;
- OpenClaw/Gateway/NOA/provider routing unchanged;
- port `8787` untouched.

Next recommended milestone:

- `LIVE_PROSODY_MOOD_SCORE_AND_EMOTIONAL_SHEET_MUSIC`.
