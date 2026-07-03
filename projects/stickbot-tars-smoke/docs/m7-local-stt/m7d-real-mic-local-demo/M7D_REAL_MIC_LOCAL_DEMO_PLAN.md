# M7D Real Mic Local Demo Plan

Status: `READYNESS_HARNESS_IN_PROGRESS_HUMAN_MIC_REQUIRED`

Generated: 2026-07-02 22:35 AEST / 2026-07-02T12:35:00Z

## Target classifications

Readiness target:

`STICKBOT_TARS_M7D_REAL_MIC_LOCAL_DEMO_READY_HUMAN_ACTION_REQUIRED`

Final human-confirmed target:

`STICKBOT_TARS_M7D_REAL_MIC_LOCAL_DEMO_PASS`

## Why this is human-gated

M7D moves from fixture audio to a real microphone. The assistant can prepare and validate the local demo harness, but it cannot honestly produce a real-mic PASS without Stick opening the local page, granting microphone access, recording a short phrase, and confirming the visible transcript.

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

Real mic privacy policy:

- Browser records via `MediaRecorder` only.
- Audio is posted to local `/api/stt`.
- STT uses local FFmpeg + local whisper.cpp `ggml-small.en.bin`.
- Raw transcript is browser-visible and may exist in tmp runtime files only.
- Durable evidence should record PASS/FAIL, transcript length/hash if needed, and operator confirmation, but not raw transcript text.

## Harness

Script:

- `scripts/m7d-local-real-mic-demo.sh`

Default local URL:

- `http://127.0.0.1:19890/`

Runtime defaults:

- `HOST=127.0.0.1`
- `PORT=19890`
- `WORKSPACE_DIR=/tmp/tars-m7d-workspace`
- `STT_MODE=cli`
- `STT_NORMALIZE_AUDIO=true`
- `OPENCLAW_MODE=echo`
- `WHISPER_BIN=/home/stickai/stickbot-voice/tools/whisper.cpp/v1.9.1-ubuntu-x64/extract/whisper-bin-ubuntu-x64/whisper-cli`
- `WHISPER_MODEL=/home/stickai/stickbot-voice/stt_models/whisper.cpp/ggml-small.en.bin`
- `FFMPEG_BIN=/home/stickai/stickbot-voice/tools/ffmpeg-static/johnvansickle-ffmpeg-release-amd64-static/extract/ffmpeg`

Loopback-only rules:

- Non-loopback `HOST` is blocked.
- Port `8787` is blocked.
- No LAN/Tailscale exposure in M7D readiness.

## Operator procedure

1. Start the script from the project root:

   ```sh
   npm run m7d:demo
   ```

2. Open the URL on the same host:

   ```text
   http://127.0.0.1:19890/
   ```

3. Click **Hold / stop mic capture**.
4. Grant microphone permission if the browser asks.
5. Say a short non-sensitive phrase.
6. Click **Hold / stop mic capture** again to stop.
7. Confirm whether a transcript appears in the page.
8. Do not paste raw transcript into durable docs/memory unless explicitly needed; prefer confirming length/hash/semantic OK.

## Readiness pass gates

Readiness can pass if:

- script syntax passes;
- `npm run check` passes;
- local assets exist and hashes are recorded;
- script blocks `/mnt/c`, non-loopback host, and port `8787`;
- no OpenClaw/Gateway/NOA mutation is performed;
- docs and operator procedure are present.

## Final real-mic pass gates

Final M7D PASS requires a human action:

- demo server started loopback-only;
- real browser microphone permission granted intentionally;
- real mic audio submitted through `/api/stt`;
- `/api/stt` returns HTTP 200;
- `normalizedLocal:true`;
- transcript visible to operator;
- no cloud STT / browser Web Speech API;
- no raw transcript committed to git/durable memory.
