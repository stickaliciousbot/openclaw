# M7C small.en Usable Local Demo Implementation Plan

Status: `IN_PROGRESS_MODEL_ACQUISITION_PENDING`

Generated: 2026-07-02 22:15 AEST / 2026-07-02T12:15:00Z

## Target classification

`STICKBOT_TARS_M7C_SMALL_EN_USABLE_DEMO_PASS`

## Purpose

M7B proved the local STT substrate with `ggml-base.en.bin`. M7C upgrades only the local Whisper model to `ggml-small.en.bin` for a more usable local demo while preserving the exact same local-only `/api/stt` contract and boundaries.

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

## Inputs

Existing M7B engine:

- whisper.cpp tag: `v1.9.1`
- selected binary: `/home/stickai/stickbot-voice/tools/whisper.cpp/v1.9.1-ubuntu-x64/extract/whisper-bin-ubuntu-x64/whisper-cli`
- binary SHA256: `427dfb509f2c04d0f01c101978b5666102c6f7e3abf2a236452db5939f5b533a`

Existing M7A normalizer:

- FFmpeg path: `/home/stickai/stickbot-voice/tools/ffmpeg-static/johnvansickle-ffmpeg-release-amd64-static/extract/ffmpeg`
- FFprobe path: `/home/stickai/stickbot-voice/tools/ffmpeg-static/johnvansickle-ffmpeg-release-amd64-static/extract/ffprobe`

M7C model:

- Model: `ggml-small.en.bin`
- Source: `https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin`
- Target local path: `/home/stickai/stickbot-voice/stt_models/whisper.cpp/ggml-small.en.bin`
- SHA256 and bytes captured after acquisition.

## Smoke gate

Script:

- `scripts/m7c-sandboxed-whispercpp-small-smoke.sh`

Expected behavior:

1. Use M7A FFmpeg to normalize fixture speech into mono 16 kHz PCM.
2. Use whisper.cpp `whisper-cli` with local `ggml-small.en.bin`.
3. Start Node server in private sandbox namespace.
4. Hide secret dirs with empty bind mounts.
5. Confirm external network is blocked/unavailable before transcription.
6. POST fixture audio to `/api/stt` with:
   - `STT_MODE=cli`
   - `STT_NORMALIZE_AUDIO=true`
   - local `WHISPER_BIN`
   - local `WHISPER_MODEL`
7. Verify HTTP 200, `normalizedLocal:true`, non-empty transcript.
8. Write raw transcript only to `/tmp` trace.
9. Commit only metadata: transcript length/hash, binary/model hashes, normalized audio hash/probe, boundaries.

## Current non-scope

- Medium/large/turbo models.
- CUDA/faster-whisper.
- Android/sherpa-onnx.
- Ollama transcript cleanup/intent routing.
- Live provider/Gateway smoke.
- LAN/Tailscale user testing.
