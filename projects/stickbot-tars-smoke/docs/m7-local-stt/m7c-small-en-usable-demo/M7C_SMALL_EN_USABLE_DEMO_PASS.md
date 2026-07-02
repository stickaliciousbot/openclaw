# M7C small.en Usable Local Demo — PASS

Status: `STICKBOT_TARS_M7C_SMALL_EN_USABLE_DEMO_PASS`

Generated: 2026-07-02 22:22 AEST / 2026-07-02T12:22:00Z

## Summary

M7C acquired the larger local Whisper `ggml-small.en.bin` model and passed the usable-demo local STT gate through the existing `/api/stt` contract.

The run reused the proven M7A FFmpeg normalization and M7B whisper.cpp `whisper-cli` binary. No OpenClaw/Gateway/NOA mutation occurred. No cloud STT or browser Web Speech API was used. No raw transcript, model, binary, audio, cache, venv, or runtime artifact is committed.

## Inputs

Existing M7B engine:

- whisper.cpp tag: `v1.9.1`
- Binary: `/home/stickai/stickbot-voice/tools/whisper.cpp/v1.9.1-ubuntu-x64/extract/whisper-bin-ubuntu-x64/whisper-cli`
- Binary SHA256: `427dfb509f2c04d0f01c101978b5666102c6f7e3abf2a236452db5939f5b533a`

Existing M7A normalizer:

- FFmpeg: `/home/stickai/stickbot-voice/tools/ffmpeg-static/johnvansickle-ffmpeg-release-amd64-static/extract/ffmpeg`
- FFprobe: `/home/stickai/stickbot-voice/tools/ffmpeg-static/johnvansickle-ffmpeg-release-amd64-static/extract/ffprobe`

M7C model:

- Model: `ggml-small.en.bin`
- Source: `https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin`
- Local path: `/home/stickai/stickbot-voice/stt_models/whisper.cpp/ggml-small.en.bin`
- SHA256: `c6138d6d58ecc8322097e0f987c32f1be8bb0a18532a3f88f734d1bbf9c41e5d`
- Bytes: `487614201`
- Commit policy: excluded from git.

## Validation

Command/session:

- `655d2910-b2b9-42e5-834a-d05c23e9a508` / `tide-mist`

Static checks:

- `npm run check`: `39/39 PASS`.

Smoke markers:

- `M7C_SMALL_EN_USABLE_DEMO_SMOKE_COMPLETE`
- `STICKBOT_TARS_M7C_SMALL_EN_USABLE_DEMO_SMOKE_PASS`

Result:

```json
{
  "classification": "STICKBOT_TARS_M7C_SMALL_EN_USABLE_DEMO_PASS",
  "whisperBinSha256": "427dfb509f2c04d0f01c101978b5666102c6f7e3abf2a236452db5939f5b533a",
  "whisperModelSha256": "c6138d6d58ecc8322097e0f987c32f1be8bb0a18532a3f88f734d1bbf9c41e5d",
  "fixtureInputSha256": "9a1f332a74f2625c4f18e246b738eee29aede9c89362b5a407e6033b7135fc84",
  "normalizedAudioSha256": "2cdd6e22cbf67805f03d275881955edfa7cd8deada3b818e7fff827010fab4ad",
  "normalizedProbe": {
    "codec_name": "pcm_s16le",
    "sample_rate": "16000",
    "channels": 1
  },
  "nodeStatus": 200,
  "sttMode": "cli",
  "normalizedLocal": true,
  "transcriptChars": 45,
  "transcriptSha256": "44b7adbb95a5d4d7129029ad17b4b2cc1bc3429e1b9057f3ad3640ef234a2fac",
  "rawTranscriptPolicy": "trace_only_not_committed",
  "networkRequiredDuringTranscription": false,
  "networkBlockedOrUnavailable": true,
  "secretDirsHidden": true,
  "cloudSpeechApiCalled": false,
  "browserWebSpeechApi": false,
  "openClawMutation": false
}
```

Evidence files:

- `result.json`
- `stt-response-summary.json`
- `whisper-help.txt`
- `whisper-bin.sha256`
- `whisper-model.sha256`
- `fixture-input.sha256`
- `normalized-audio.sha256`
- `normalized-audio.stat`
- `normalized-audio.file`
- `normalized-audio-ffprobe.json`

## Boundary evidence

- Private namespace: `unshare -Urnm`.
- Loopback enabled inside namespace.
- External network probe failed DNS resolution and was classified as blocked/unavailable before transcription.
- Secret dirs hidden with empty bind mounts:
  - `/home/stickai/.openclaw`
  - `/home/stickai/.ssh`
  - `/home/stickai/.codex`
  - `/home/stickai/.config`
- Raw transcript existed only under `/tmp` trace and was not copied into durable evidence.

## Boundaries preserved

- No OpenClaw mutation.
- No Gateway config/routing/default/fallback mutation.
- No Gateway restart.
- No NOA mutation.
- No cloud STT.
- No browser Web Speech API.
- No Android/LAN/Tailscale exposure.
- No persistent service install.
- No `/mnt/c` model/audio/runtime paths.
- No raw transcript in durable memory/docs/git.
- No model/binary/audio/cache/venv/runtime artifact committed.

## Final classification

`STICKBOT_TARS_M7C_SMALL_EN_USABLE_DEMO_PASS`

Next possible target:

`M7D_REAL_MIC_LOCAL_DEMO_NOT_STARTED_REQUIRES_SEPARATE_APPROVAL`
