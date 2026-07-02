# Lessons Learned — Stickbot-TARS Voice Demo Hardening / M3 / M4

Date: 2026-07-02 AEST

## Durable rule: notebooks are gates, not afterthoughts

For Stickbot-TARS, every milestone needs synchronized documentation before final closeout:

- project implementation notebook
- troubleshooting/repair notebook
- project-local status/closeout artifacts
- long-term lessons for major bugs/repairs

If a milestone changes dependencies, isolation, security posture, model files, route boundaries, or runtime assumptions, update the notebooks before declaring PASS.

## M2.5 hardening lesson

Fail-closed before M3 was correct. The pre-hardening scaffold had missing gates:

- config fail-closed
- unsafe LAN/non-loopback refusal
- UUID-only audio route
- separate audio limits
- Origin/CSRF checks

Repairing these before model acquisition/load prevented the voice-demo path from becoming a localhost/LAN footgun.

## M3 model provenance lesson

M3 must remain provenance-only:

- download exact pinned revision
- hash every expected file
- record license/voice-rights caveat
- store under WSL-native path
- do not load `.pth`

Hashing proves artifact consistency only; it does not make `.pth` safe.

## M4 isolation lesson

Do not load `.pth` in the main `stickai` context just because it is convenient.

Findings:

- Docker/Podman/bwrap/firejail were unavailable.
- Dedicated low-privilege Unix user was preferred but blocked from Telegram because sudo needed TTY/password.
- Plain `unshare -Urn` was insufficient because it still saw `/home/stickai/.openclaw`.
- `unshare -Urnm` with private mount namespace and explicit empty bind mounts over `/home/stickai/.openclaw`, `.ssh`, `.codex`, `.config` was acceptable for this local M4 attempt because it hid secrets, blocked network, mounted model/speaker read-only, and left only output writable.

Durable rule: network isolation alone is not enough; verify filesystem/secret isolation too.

## M4 dependency lessons

### `xtts-api-server` install path

`xtts-api-server==0.9.0` pulled `pyaudio`, which failed because Python dev headers / `Python.h` were missing. Avoid this path unless system dependencies are explicitly approved or a wheel-compatible environment is prepared.

### Coqui direct path

`coqui-tts==0.27.5` installed, but dependency compatibility required manual fixes:

1. Initial install lacked Torch/Torchaudio.
2. CPU Torch/Torchaudio 2.12 installed, but `transformers==5.12.1` broke XTTS import because `isin_mps_friendly` was missing.
3. Pinning `transformers>=4.57,<5` to `4.57.6` restored the expected symbol.
4. PyTorch >=2.9 triggered Coqui's `torchcodec` audio IO requirement.
5. Installing `torchcodec==0.14.0` failed at native library load with missing `libnvrtc.so.13` / TorchCodec compatibility issues in the CPU stack.
6. CPU Torch/Torchaudio `2.8.0+cpu` installed successfully and restored `TTS_import=ok`, avoiding the PyTorch >=2.9 TorchCodec requirement. R4 sandbox load is pending after this repair.

Durable rule: for Coqui/XTTS, pin a known-compatible set instead of accepting latest major versions. Do not rely on open-ended `transformers` or latest Torch in this environment.

## Safety posture to preserve

- No model load unless secret dirs are hidden and network is blocked.
- No OpenClaw/Gateway/NOA config/routing/provider mutation for voice demo milestones.
- No model binaries in git.
- No generated audio/traces/venv/cache/node_modules in git.
- No browser/provider direct calls.
- No browser Web Speech API.
- No `/mnt/c` runtime/model/audio/traces.
- TARS never binds `8787`.

## Current classification reminder

M4 passed after Torch/Torchaudio `2.8.0+cpu` repair. R4 sandboxed first-load/generation loaded the local TARS XTTS model and generated a 95,788-byte, 24 kHz WAV inside the accepted no-network, secret-hidden, read-only-model boundary. Generated WAV SHA256: `9a1f332a74f2625c4f18e246b738eee29aede9c89362b5a407e6033b7135fc84`. Classification: `STICKBOT_TARS_M4_SANDBOXED_XTTS_LOCAL_LOAD_PASS_READY_FOR_M5_PLANNING_ONLY`.

M5 was later approved and passed as local-only serverization / Node echo voice integration. R1 failed safely because loopback was down inside the private `unshare -n` namespace; repair was to bring `lo` up inside the namespace and make cleanup tolerate unset PIDs. R2 passed: local XTTS `/ready`, Node `/api/chat` HTTP 200, audio URL returned, generated WAV SHA256 `1daf103c5e9de8dbeef2a373638b843ff8e01429b415c6ae279853c9908712ec`, no Gateway/OpenClaw/NOA/STT/Android/LAN mutation. Classification: `STICKBOT_TARS_M5_LOCAL_SERVERIZATION_NODE_VOICE_PASS_READY_FOR_M6_PLANNING_ONLY`.

M6 was later approved and passed as a fixture-backed OpenClaw adapter voice smoke. Implemented safe adapter modes for `infer` (`openclaw infer model run --prompt {prompt} --json`) and explicit future `agent` (`openclaw agent --message {prompt} --json`), with `spawn(...,{shell:false})`, required `{prompt}` placeholder, bounded stdout/stderr, timeout/kill, JSON text extraction, and fail-closed tests. M6 sandbox smoke used a fake OpenClaw CLI, not live provider/Gateway, while the TARS model was loaded; Node `/api/chat` returned `OpenClaw adapter fixture response: M6 OpenClaw adapter fixture voice smoke`, generated WAV SHA256 `fc7da588940bbe2238dcc91b9dc5156d36cbcaafcc49bbf606ebbdc3427ce5d0`, and preserved the no-network, secret-hidden, read-only-model boundary. Classification: `STICKBOT_TARS_M6_OPENCLAW_ADAPTER_FIXTURE_VOICE_PASS_READY_FOR_M7_PLANNING_ONLY`.

M7 was later approved and passed as a local STT fixture-contract milestone, while real STT remained blocked. Discovery found no `ffmpeg`/`ffprobe`, no whisper/faster-whisper binaries/packages, no local STT model dirs. Implemented `STT_MODE=capture` default, `STT_MODE=fixture`, and future `STT_MODE=cli` with safe spawn/`{file}`/bounds/fail-closed tests. Static tests 34/34 passed; sandbox `/api/stt` fixture smoke returned HTTP 200 transcript `M7 fixture transcript`, captured local audio SHA256 `2976da01e205a110c9fa41d47659e238a5c6d3c3f3137582f2949853faa201dd`, no cloud STT, no browser Web Speech API. Classification: `STICKBOT_TARS_M7_LOCAL_STT_FIXTURE_CONTRACT_PASS_REAL_ENGINE_BLOCKED_READY_FOR_STT_ENGINE_ACQUISITION`.

M7A was then approved/pursued as local audio normalization acquisition. Preflight confirmed no `ffmpeg`/`ffprobe`; apt install could not run from Telegram due sudo TTY/elevated restrictions after tests passed 39/39, so used approved WSL-native user-space static FFmpeg fallback. John Van Sickle `ffmpeg-release-amd64-static.tar.xz` acquired under `/home/stickai/stickbot-voice/tools/ffmpeg-static`; tarball SHA256 `abda8d77ce8309141f83ab8edf0596834087c52467f6badf376a6a2a4c87cf67`, upstream MD5 `7fa72b652e19bf84c9461e332ea1cdf3` OK, FFmpeg SHA256 `e7e7fb30477f717e6f55f9180a70386c62677ef8a4d4d1a5d948f4098aa3eb99`, FFprobe SHA256 `4f231a1960d83e403d08f7971e271707bec278a9ae18e21b8b5b03186668450d`; static build is GPLv3 private/dev validation only, not future distributable default. M7A sandbox smoke converted fixture WebM/Opus to mono 16 kHz PCM WAV SHA256 `38e3b264d99a035f168d6913520d2541a943c6a931e3f896882daf756b66fb7f`, no network/secret/cloud/WebSpeech/OpenClaw mutation. Classification: `STICKBOT_TARS_M7A_LOCAL_AUDIO_NORMALIZATION_PROVENANCE_PASS`.

M7B then passed as the first real local STT fixture. Preflight found `cmake` missing but make/gcc/g++/curl/python3 available, so used pinned official whisper.cpp `v1.9.1` Ubuntu x64 release binary instead of source build/apt. Release asset SHA256 matched GitHub API digest `f3bf3b4369a99b54665b0f19b88483b30de27f25963b0414235dea03198515c5`; selected `whisper-cli` SHA256 `427dfb509f2c04d0f01c101978b5666102c6f7e3abf2a236452db5939f5b533a`; acquired `ggml-base.en.bin` SHA256 `a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002` bytes `147964211`. R1 failed safely by selecting deprecated `main`; repaired to block `main` and use `whisper-cli`. R2 proved local transcription but failed normalization because `STT_NORMALIZE_AUDIO=1` parsed false; repaired to `STT_NORMALIZE_AUDIO=true` and hard assert `normalizedLocal:true`. R3 passed: `/api/stt` HTTP 200, `sttMode:cli`, `normalizedLocal:true`, transcript chars `42`, transcript SHA256 `3e1f84be507525854b4acd7d9074dd1c7c55478130609fab0d509f97b6420075`, normalized audio SHA256 `2cdd6e22cbf67805f03d275881955edfa7cd8deada3b818e7fff827010fab4ad`, network blocked/unavailable during transcription, secret dirs hidden, no cloud/WebSpeech/OpenClaw/Gateway/NOA mutation. Classification: `STICKBOT_TARS_M7B_WHISPERCPP_LOCAL_STT_FIXTURE_PASS`.

Do not start M7C small.en usable demo, M8, live provider/Gateway smoke, Android, persistent service install, or host-PC Tailscale proxy/user-testing exposure without separate owner approval and a fresh threat model.
