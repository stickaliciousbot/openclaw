# M7B whisper.cpp Local STT Implementation Plan

Status: `IN_PROGRESS_ACQUISITION_PENDING`

Generated: 2026-07-02 21:55 AEST / 2026-07-02T11:55:00Z

## Target classification

`STICKBOT_TARS_M7B_WHISPERCPP_LOCAL_STT_FIXTURE_PASS`

## Hard boundary

No OpenClaw mutation:

- no OpenClaw production routing/config/default/fallback mutation;
- no Gateway config mutation;
- no Gateway restart;
- no NOA mutation;
- no cloud STT;
- no browser Web Speech API;
- no Android/LAN/Tailscale exposure;
- no persistent service install;
- no `/mnt/c` model/audio/runtime paths;
- no audio/model/cache/binary artifacts committed.

Raw transcript policy:

- Raw transcript may exist only in `/tmp` trace during smoke.
- Durable evidence may include transcript length and SHA256 only.
- Raw transcript must not be written into memory files, closeout docs, manifests, or git.

## Preflight result

Command/session:

- `540f891f-aff6-4ff9-8dc9-88e9c91131f7` / `swift-slug`

Findings:

- Branch: `feature/stickbot-tars-m25-hardening-repair`.
- Head: `67d1155dddba50c26e691eb329ea9949432dbf26`.
- `git`, `make`, `gcc`, `g++`, `cc`, `c++`, `curl`, `sha256sum`, `python3`: present.
- `cmake`: missing.
- M7A FFmpeg static binary present.
- No existing whisper.cpp tools/models found.
- Latest observed upstream tags include `v1.9.1` at commit `f049fff95a089aa9969deb009cdd4892b3e74916`.

Decision:

- Avoid apt/cmake due previous Telegram runtime elevated/sudo restriction.
- Use pinned official GitHub release binary for Ubuntu x64.
- Use base.en model for first smoke.

## Pinned acquisition inputs

whisper.cpp:

- Repo: `https://github.com/ggml-org/whisper.cpp`
- Tag: `v1.9.1`
- Commit: `f049fff95a089aa9969deb009cdd4892b3e74916`
- Release asset: `whisper-bin-ubuntu-x64.tar.gz`
- Release asset URL: `https://github.com/ggml-org/whisper.cpp/releases/download/v1.9.1/whisper-bin-ubuntu-x64.tar.gz`
- Published asset digest from GitHub API: `sha256:f3bf3b4369a99b54665b0f19b88483b30de27f25963b0414235dea03198515c5`

Model:

- Smoke model: `ggml-base.en.bin`
- Source: `https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin`
- Model SHA256 will be captured after download.
- Model will live under `/home/stickai/stickbot-voice/stt_models/whisper.cpp/`, not git and not `/mnt/c`.

## Smoke gate

Script:

- `scripts/m7b-sandboxed-whispercpp-stt-smoke.sh`

Expected behavior:

1. Use M7A FFmpeg to normalize fixture speech WAV into mono 16 kHz PCM.
2. Start Node server in private sandbox namespace.
3. Hide secret dirs with empty bind mounts.
4. Block/unavailable external network inside namespace.
5. POST fixture audio to `/api/stt` with:
   - `STT_MODE=cli`
   - `STT_NORMALIZE_AUDIO=1`
   - local `WHISPER_BIN`
   - local `WHISPER_MODEL`
6. Verify HTTP 200 and non-empty transcript.
7. Write raw transcript only to `/tmp` trace.
8. Commit only metadata: transcript length/hash, binary/model hashes, normalized audio hash/probe, boundaries.

## Current non-scope

- `ggml-small.en.bin` usable demo model acquisition.
- CUDA/faster-whisper.
- Android/sherpa-onnx.
- Ollama transcript cleanup/intent routing.
- Live provider/Gateway smoke.
