# Stickbot-TARS Lessons Learned

Last updated: 2026-07-02 18:31 AEST / 2026-07-02T08:31:00Z

## Documentation is part of the gate

Milestone PASS requires notebook updates, not just a working command:

- `IMPLEMENTATION_NOTEBOOK.md`
- `docs/TROUBLESHOOTING_AND_REPAIR_NOTEBOOK.md`
- `docs/LESSONS_LEARNED.md`
- milestone status/closeout evidence

This keeps cold-resume safe and avoids rediscovering dependency/sandbox failures.

## M2.5: fail closed before model work

Hardening the Node demo before model acquisition was correct. Required gates included fail-closed config, loopback-by-default, reserved port refusal for `8787`, UUID-only audio paths, split upload limits, Origin checks, and CSRF/session nonce checks.

## M3: model provenance is not model safety

Hashing pinned model files gives provenance and repeatability only. `.pth` remains pickle-based and must not be loaded in the production OpenClaw/Gateway process or in a context that can see secrets.

## M4: isolation must include filesystem secrecy

Network isolation alone was insufficient. Plain `unshare -Urn` still exposed `/home/stickai/.openclaw`. The accepted no-root fallback was `unshare -Urnm` with model/speaker read-only mounts, output writable mount, network namespace, and empty bind mounts over `.openclaw`, `.ssh`, `.codex`, and `.config`.

A dedicated low-privilege user/container is still preferable later, but was blocked from Telegram context by sudo TTY/password requirements.

## M4: pin the XTTS dependency stack

Open-ended latest packages caused cascading failures:

- `xtts-api-server` pulled `pyaudio`, which needed `Python.h`.
- `transformers==5.12.1` broke Coqui XTTS imports.
- `torch==2.12.1+cpu` triggered Coqui's TorchCodec requirement.
- `torchcodec==0.14.0` failed native loading with the current CPU stack.

Known passing local M4 stack:

- `coqui-tts==0.27.5`
- `torch==2.8.0+cpu`
- `torchaudio==2.8.0+cpu`
- `transformers==4.57.6`
- CPU-only, `cuda_available False`

## Current state after M4

M4 passed: local TARS XTTS model load and first WAV generation succeeded inside the no-network, secret-hidden, read-only-model boundary.

Do not proceed beyond M5 local-loopback serverization into LAN/mobile user testing without a separate owner approval and a fresh threat model.

## M5: private network namespaces need loopback enabled

The first M5 serverization smoke failed safely because the private `unshare -n` network namespace had external network isolation but loopback was down. XTTS loaded and listened, yet Node/curl could not reach `127.0.0.1:18020/ready`.

Durable rule: for local multi-process sandbox smokes, explicitly bring `lo` up inside the namespace, then verify both external network is blocked and local loopback works. Also initialize cleanup PIDs so early-stage failures do not mask the real failure classification.

## M5 passing local serverization stack

M5 local serverization passed with:

- minimal loopback XTTS HTTP server (`GET /health`, `GET /ready`, `POST /tts_to_audio/`);
- Node echo app in `OPENCLAW_MODE=echo`;
- private `unshare -Urnm` boundary;
- loopback enabled inside namespace;
- model/speaker read-only;
- secret dirs hidden;
- external network blocked/unavailable.

Generated Node voice smoke WAV SHA256: `1daf103c5e9de8dbeef2a373638b843ff8e01429b415c6ae279853c9908712ec`.

## Future LAN/mobile demo access

Stick clarified on 2026-07-02 that before user testing, the TARS web app needs to be reachable from phone and laptop browsers. Preferred future path is host-PC proxy through the host PC's Tailscale connection/IP; the app does not need to run directly on a Tailscale-native host and can remain local/WSL-bound.

Do not blur this into M5. Treat it as a separate LAN/Tailscale milestone:

- explicit approval before starting;
- safe non-`8787` port;
- host-PC Tailscale proxy/reverse-proxy or restrictive portproxy plan;
- raw LAN exposure only as fallback;
- Origin/Host allowlist for phone/laptop URLs;
- CSRF still required;
- no wildcard CORS;
- XTTS kept loopback/private behind Node unless separately approved;
- phone and laptop browser validation before user testing.

## M6: adapter fixture before live provider/Gateway smoke

M6 proved the Node OpenClaw adapter path with a fixture CLI inside the sandbox before any live provider/Gateway call. This was the right safety sequence because the TARS `.pth` was loaded in the same boundary.

Durable adapter rules:

- Discover actual CLI shape from local docs/help before coding.
- Default raw inference shape is `openclaw infer model run --prompt {prompt} --json`.
- Full agent/session shape is `openclaw agent --message {prompt} --json` and should be explicit opt-in.
- Use `spawn(file,args,{shell:false})`, never shell interpolation.
- Require `{prompt}` placeholder to avoid ambiguous prompt concatenation.
- Bound stdout/stderr and enforce timeout/kill.
- Parse JSON and fail closed if no text is extractable.
- First adapter smoke can use a fixture CLI to prove process/JSON/prompt/voice wiring without provider or Gateway side effects.

M6 fixture result: Node `/api/chat` returned OpenClaw adapter fixture text and generated WAV SHA256 `fc7da588940bbe2238dcc91b9dc5156d36cbcaafcc49bbf606ebbdc3427ce5d0` inside the no-network, secret-hidden, read-only-model boundary. Live provider/Gateway smoke remains a separate approval gate.

## M7: STT contract before engine acquisition

M7 discovery found no local STT stack: no `ffmpeg`/`ffprobe`, no whisper/faster-whisper binaries/packages, and no local STT model directories. The correct response was not to install/download or call cloud STT inside the milestone; it was to implement the `/api/stt` adapter contract and fixture mode first.

Durable STT rules:

- Browser Web Speech API remains forbidden.
- Cloud STT APIs remain forbidden unless separately approved.
- Real transcription requires a later local engine/model acquisition milestone with provenance/hashes/offline validation.
- `STT_MODE=capture` should remain default when no engine is configured.
- `STT_MODE=fixture` is valid for UI/server contract testing only.
- `STT_MODE=cli` must use `spawn(file,args,{shell:false})`, require `{file}`, bound stdout/stderr, timeout/kill, and fail closed.

M7 fixture result: Node `/api/stt` returned HTTP 200 with transcript `M7 fixture transcript`, captured local audio SHA256 `2976da01e205a110c9fa41d47659e238a5c6d3c3f3137582f2949853faa201dd`, and preserved no-network/secret-hidden boundaries. Real STT remains blocked on local engine/model/ffmpeg acquisition.

## M7A: FFmpeg normalization as its own gate

M7A proved that local audio normalization should be separated from real STT. The normalizer contract now uses a fixed FFmpeg command, WSL-native path checks, `/mnt/c` rejection, `shell:false`, stderr/stdout bounds, timeout/kill, and fail-closed non-zero handling.

Runtime privilege lesson: apt install from Telegram may fail even after approval because sudo needs a TTY/password and elevated exec may be disabled for that provider. Do not mutate OpenClaw/Gateway to work around this. Use an approved user-space WSL-native fallback when suitable.

M7A fallback result: John Van Sickle static FFmpeg `7.0.2-static` was acquired under `/home/stickai/stickbot-voice/tools/ffmpeg-static`, with tarball SHA256 `abda8d77ce8309141f83ab8edf0596834087c52467f6badf376a6a2a4c87cf67`, FFmpeg SHA256 `e7e7fb30477f717e6f55f9180a70386c62677ef8a4d4d1a5d948f4098aa3eb99`, FFprobe SHA256 `4f231a1960d83e403d08f7971e271707bec278a9ae18e21b8b5b03186668450d`. License posture is GPLv3 private/dev validation only, not future distributable default. Sandboxed normalization converted fixture WebM/Opus into mono 16 kHz PCM WAV SHA256 `38e3b264d99a035f168d6913520d2541a943c6a931e3f896882daf756b66fb7f`, preserving no-network/secret-hidden/no-cloud/no-WebSpeech/no-OpenClaw-mutation boundaries.

## M7B: whisper.cpp local STT real fixture

M7B proved the primary STT substrate decision: pinned whisper.cpp release binary + `ggml-base.en.bin` can transcribe locally through `/api/stt` with FFmpeg normalization and no network during transcription.

Lessons:

- Prefer `whisper-cli`; deprecated `main` exits nonzero in `v1.9.1` and should be blocked by smoke gates.
- Boolean env flags in this project only accept literal `true`; `1` is false. Smoke scripts must use `STT_NORMALIZE_AUDIO=true` and assert `normalizedLocal:true`.
- Raw transcripts are privacy-sensitive runtime traces; preserve length/hash only in durable docs/memory.
- Missing `cmake` does not block the first proof if an official pinned release binary with digest is available.

M7B result: whisper.cpp `v1.9.1` release asset SHA256 `f3bf3b4369a99b54665b0f19b88483b30de27f25963b0414235dea03198515c5`, `whisper-cli` SHA256 `427dfb509f2c04d0f01c101978b5666102c6f7e3abf2a236452db5939f5b533a`, `ggml-base.en.bin` SHA256 `a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002`; R3 `/api/stt` HTTP 200 with `normalizedLocal:true`, transcript chars `42`, transcript SHA256 `3e1f84be507525854b4acd7d9074dd1c7c55478130609fab0d509f97b6420075`, no cloud/WebSpeech/OpenClaw mutation.

## M7C: small.en usable local demo

M7C upgraded only the model, not the STT authority boundary. Reusing the same M7A/M7B harness with `ggml-small.en.bin` proved a more usable local demo path while preserving the same local-only constraints.

M7C result: `ggml-small.en.bin` SHA256 `c6138d6d58ecc8322097e0f987c32f1be8bb0a18532a3f88f734d1bbf9c41e5d`, bytes `487614201`; `/api/stt` HTTP 200, `normalizedLocal:true`, transcript chars `45`, transcript SHA256 `44b7adbb95a5d4d7129029ad17b4b2cc1bc3429e1b9057f3ad3640ef234a2fac`, no network required during transcription, network blocked/unavailable in sandbox, secret dirs hidden, no cloud/WebSpeech/OpenClaw mutation. Raw transcript remains trace-only and must not be copied into durable docs/memory.
