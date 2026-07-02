# M4 Sandboxed XTTS Local Load — PASS

Status: `STICKBOT_TARS_M4_SANDBOXED_XTTS_LOCAL_LOAD_PASS`

Generated: 2026-07-02 18:31 AEST / 2026-07-02T08:31:00Z

## Summary

M4 successfully loaded the pinned local `Pyrater/TARS` XTTS model and generated the first local WAV inside the accepted `unshare -Urnm` sandbox boundary.

This was a local CPU-only validation. It did **not** start an XTTS server and did **not** integrate with OpenClaw, Gateway, NOA, STT, Android, Telegram, or production routing.

## Result

Source evidence: `projects/stickbot-tars-smoke/docs/m4-sandboxed-load/result.json`

```json
{
  "classification": "STICKBOT_TARS_M4_SANDBOXED_XTTS_LOCAL_LOAD_PASS",
  "modelLoaded": true,
  "wavGenerated": true,
  "networkExpectedBlocked": true,
  "startedAt": "2026-07-02T08:24:37Z",
  "torchVersion": "2.8.0+cpu",
  "transformersVersion": "4.57.6",
  "torchaudioVersion": "2.8.0+cpu",
  "cudaAvailable": false,
  "outputPath": "/tmp/tars-m4-boundary/output/m4-first-generation.wav",
  "outputBytes": 95788,
  "sampleRate": 24000,
  "finishedAt": "2026-07-02T08:30:46Z"
}
```

Generated WAV host path:

`/home/stickai/stickbot-voice/output/m4-first-generation.wav`

Generated WAV size:

`95,788 bytes`

Generated WAV SHA256:

`9a1f332a74f2625c4f18e246b738eee29aede9c89362b5a407e6033b7135fc84`

File type verification:

`RIFF (little-endian) data, WAVE audio, Microsoft PCM, 16 bit, mono 24000 Hz`

The audio file itself is intentionally excluded from git.

## Sandbox boundary evidence

Command/session:

- approval id: `76573901-c5d3-490a-b475-cdc8c86c6ba2`
- session: `good-lobster`
- exit code: `0`

Boundary checks from log:

- Private user/mount/network namespace via `unshare -Urnm`.
- Model bind-mounted from `/home/stickai/stickbot-voice/xtts_models/tars` to `/tmp/tars-m4-boundary/model` and remounted read-only.
- Speaker directory bind-mounted read-only.
- Output directory bind-mounted writable.
- Secret/runtime dirs hidden with empty bind mounts:
  - `/home/stickai/.openclaw`
  - `/home/stickai/.ssh`
  - `/home/stickai/.codex`
  - `/home/stickai/.config`
- Network probe: `curl` to `https://huggingface.co` failed with DNS resolution error, classified as `NETWORK_BLOCKED_OR_UNAVAILABLE`.
- CUDA unavailable: `false`.

## Dependency state at PASS

- Python: `/home/stickai/stickbot-voice/venv-coqui`
- `coqui-tts==0.27.5`
- `torch==2.8.0+cpu`
- `torchaudio==2.8.0+cpu`
- `transformers==4.57.6`
- `torchcodec==0.14.0` remains installed from the previous repair attempt, but the PASS path used Torch 2.8 to avoid the PyTorch >=2.9 TorchCodec hard requirement.

## Prior blocked attempts resolved

1. Transformers 5.x failed before model load: missing `isin_mps_friendly`.
   - Repair: pin `transformers>=4.57,<5`, resolved to `4.57.6`.
2. Torch 2.12 required TorchCodec.
   - Repair attempt: installed `coqui-tts[codec]` / `torchcodec==0.14.0`.
3. TorchCodec native load failed with Torch 2.12 CPU stack due missing `libnvrtc.so.13` / compatibility.
   - Final repair: downgrade Torch/Torchaudio to `2.8.0+cpu`, verified `TTS_import=ok`.

## Boundaries preserved

- No OpenClaw production config mutation.
- No Gateway restart/config mutation.
- No NOA touch.
- No STT touch.
- No Android touch.
- No browser provider call.
- No Web Speech API.
- No XTTS server start.
- No LAN exposure.
- No bind to `8787`.
- No `/mnt/c` model/runtime/audio path.
- No model/audio/cache/venv committed.

## Final M4 classification

`STICKBOT_TARS_M4_SANDBOXED_XTTS_LOCAL_LOAD_PASS_READY_FOR_M5_PLANNING_ONLY`

M5/integration is **not started** and requires separate approval.
