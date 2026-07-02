# M7 Local STT Fixture Contract — PASS / Real Engine Blocked

Status: `STICKBOT_TARS_M7_LOCAL_STT_FIXTURE_CONTRACT_PASS_REAL_ENGINE_BLOCKED_READY_FOR_STT_ENGINE_ACQUISITION`

Generated: 2026-07-02 20:22 AEST / 2026-07-02T10:22:00Z

## Summary

M7 implemented and validated the local STT adapter contract and `/api/stt` fixture path.

Real local transcription remains blocked because no local STT engine, ffmpeg, or STT model is present. No cloud STT, browser Web Speech API, package install, or model download was used.

## Discovery result

Command/session:

- `21ac704a` / `young-crustacean`

Findings:

- `ffmpeg`: missing.
- `ffprobe`: missing.
- `whisper-cli`: missing.
- `whisper-cpp`: missing.
- `whisper`: missing.
- `whisperx`: missing.
- `faster-whisper`: missing.
- System Python packages missing: `faster_whisper`, `whisper`, `torch`, `torchaudio`, `soundfile`.
- No local STT model directories found under:
  - `/home/stickai/stickbot-voice/stt_models`
  - `/home/stickai/.cache/whisper`
  - `/home/stickai/.cache/huggingface`

Conclusion:

`REAL_STT_ENGINE_BLOCKED_MISSING_LOCAL_ENGINE_MODEL_AND_FFMPEG`

## Static validation

Command/session:

- `0e287a97` / `salty-atlas`

Result:

- Tests: 34/34 PASS.
- Marker: `STICKBOT_TARS_M7_STATIC_CHECK_PASS`.

M7 added STT tests for:

- fixture mode no-spawn behavior;
- capture mode fail-closed behavior;
- CLI mode requiring `{file}` placeholder;
- JSON/plain transcript parsing;
- file paths with shell metacharacters passed as argv with `shell:false`;
- non-zero STT CLI exit fail-closed behavior;
- stdout limit fail-closed behavior.

## Fixture smoke result

Command/session:

- `3291be75` / `quick-reef`

Source evidence:

- `projects/stickbot-tars-smoke/docs/m7-local-stt/result.json`
- `projects/stickbot-tars-smoke/docs/m7-local-stt/stt-fixture-smoke.json`

Result summary:

```json
{
  "classification": "STICKBOT_TARS_M7_LOCAL_STT_FIXTURE_CONTRACT_PASS_REAL_ENGINE_BLOCKED",
  "sttMode": "fixture",
  "fixtureTranscript": "M7 fixture transcript",
  "realSttEngineAvailable": false,
  "ffmpegAvailable": false,
  "cloudSpeechApiCalled": false,
  "browserWebSpeechApi": false,
  "nodeSttStatus": 200,
  "networkBlockedOrUnavailable": true,
  "secretDirsHidden": true,
  "capturedAudioSha256": "2976da01e205a110c9fa41d47659e238a5c6d3c3f3137582f2949853faa201dd",
  "finishedAt": "2026-07-02T10:20:39Z"
}
```

Node `/api/stt` response:

```json
{
  "nodeStatus": 200,
  "body": {
    "id": "2812d254-740c-455c-a65f-cdf88521a57d",
    "savedLocal": true,
    "sttMode": "fixture",
    "transcript": "M7 fixture transcript",
    "maxAudioDurationSeconds": 60,
    "boundaries": {
      "browserWebSpeechApi": false,
      "cloudSpeechApi": false
    }
  }
}
```

Captured fixture audio evidence:

- SHA256: `2976da01e205a110c9fa41d47659e238a5c6d3c3f3137582f2949853faa201dd`
- Bytes: `3244`
- Type: `RIFF (little-endian) data, WAVE audio, Microsoft PCM, 16 bit, mono 16000 Hz`
- Sandbox path: `/tmp/tars-m7-boundary/app/data/audio/input/2812d254-740c-455c-a65f-cdf88521a57d-input.bin`
- Audio file is excluded from git.

## Boundary evidence

- Private user/mount/network namespace via `unshare -Urnm`.
- Loopback brought up inside private namespace.
- External network probe to `https://huggingface.co` failed DNS resolution, classified as `NETWORK_BLOCKED_OR_UNAVAILABLE`.
- Secret/runtime dirs hidden with empty bind mounts:
  - `/home/stickai/.openclaw`
  - `/home/stickai/.ssh`
  - `/home/stickai/.codex`
  - `/home/stickai/.config`
- Node app ran from copied sandbox app directory under `/tmp/tars-m7-boundary/app`.
- Node `WORKSPACE_DIR` pointed at `/tmp/tars-m7-boundary/workspace`, not the real OpenClaw workspace.

## Boundaries preserved

- No cloud speech API.
- No browser Web Speech API.
- No OpenAI Whisper API.
- No model download.
- No package install.
- No ffmpeg install.
- No real STT engine run.
- No Gateway config/routing/default/fallback mutation.
- No Gateway restart.
- No NOA touch.
- No Android touch.
- No LAN/Tailscale exposure.
- No persistent service install.
- No model/audio/cache/venv committed.

## Final M7 classification

`STICKBOT_TARS_M7_LOCAL_STT_FIXTURE_CONTRACT_PASS_REAL_ENGINE_BLOCKED_READY_FOR_STT_ENGINE_ACQUISITION`

Next required milestone for real transcription: approved local STT engine acquisition/provenance/install, including ffmpeg or equivalent audio normalization, local model hashes, and offline/local validation.
