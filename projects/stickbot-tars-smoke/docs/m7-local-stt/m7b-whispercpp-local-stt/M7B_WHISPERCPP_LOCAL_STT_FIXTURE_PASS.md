# M7B whisper.cpp Local STT Fixture — PASS

Status: `STICKBOT_TARS_M7B_WHISPERCPP_LOCAL_STT_FIXTURE_PASS`

Generated: 2026-07-02 22:05 AEST / 2026-07-02T12:05:00Z

## Summary

M7B acquired pinned local whisper.cpp assets, ran local STT through the existing `/api/stt` contract, and passed the sandboxed fixture gate with FFmpeg normalization enabled.

No OpenClaw/Gateway/NOA mutation occurred. No cloud STT or browser Web Speech API was used. No raw transcript, model, binary, audio, cache, venv, or runtime artifact is committed.

## Preflight

Command/session:

- `540f891f-aff6-4ff9-8dc9-88e9c91131f7` / `swift-slug`

Findings:

- Branch: `feature/stickbot-tars-m25-hardening-repair`.
- Head at preflight: `67d1155dddba50c26e691eb329ea9949432dbf26`.
- Build tools present: `git`, `make`, `gcc`, `g++`, `cc`, `c++`, `curl`, `sha256sum`, `python3`.
- `cmake` missing, so M7B avoided local source build/apt mutation and used pinned release binary.
- M7A FFmpeg static binary present.
- No existing whisper.cpp tools/models found before acquisition.
- Upstream tag chosen: `v1.9.1`, commit `f049fff95a089aa9969deb009cdd4892b3e74916`.

## Acquisition

Command/session:

- `73997222-455b-46d3-b2f4-1b5fc4042b02` / `grand-pine`

Static checks before acquisition:

- `npm run check`: `39/39 PASS`.

whisper.cpp release:

- Repo: `https://github.com/ggml-org/whisper.cpp`
- Tag: `v1.9.1`
- Commit: `f049fff95a089aa9969deb009cdd4892b3e74916`
- Asset: `whisper-bin-ubuntu-x64.tar.gz`
- URL: `https://github.com/ggml-org/whisper.cpp/releases/download/v1.9.1/whisper-bin-ubuntu-x64.tar.gz`
- Expected release asset digest from GitHub API: `sha256:f3bf3b4369a99b54665b0f19b88483b30de27f25963b0414235dea03198515c5`
- Downloaded tarball SHA256: `f3bf3b4369a99b54665b0f19b88483b30de27f25963b0414235dea03198515c5`
- Local extract path: `/home/stickai/stickbot-voice/tools/whisper.cpp/v1.9.1-ubuntu-x64/extract/whisper-bin-ubuntu-x64/`

Selected binary:

- Binary: `/home/stickai/stickbot-voice/tools/whisper.cpp/v1.9.1-ubuntu-x64/extract/whisper-bin-ubuntu-x64/whisper-cli`
- SHA256: `427dfb509f2c04d0f01c101978b5666102c6f7e3abf2a236452db5939f5b533a`

Model:

- Model: `ggml-base.en.bin`
- Source: `https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin`
- Local path: `/home/stickai/stickbot-voice/stt_models/whisper.cpp/ggml-base.en.bin`
- SHA256: `a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002`
- Bytes: `147964211`

## R1/R2 repairs

### R1 fail-closed

R1 selected deprecated `main`, which exits non-zero and asks callers to use `whisper-cli`.

- Result: `/api/stt` returned HTTP 500.
- Classification: `STT_EXIT_NONZERO`.
- Repair: select `whisper-cli` and block deprecated `main` in the smoke script.

### R2 partial pass / normalization gate failure

R2 used `whisper-cli` and proved local transcription worked:

- `/api/stt`: HTTP 200.
- Transcript chars: `42`.
- Transcript SHA256: `3e1f84be507525854b4acd7d9074dd1c7c55478130609fab0d509f97b6420075`.
- No raw transcript committed.

But `STT_NORMALIZE_AUDIO=1` parsed false because the runtime boolean parser only accepts literal `true`.

- Result: `normalizedLocal:false`.
- Repair: use `STT_NORMALIZE_AUDIO=true` and add a hard smoke assertion that `normalizedLocal` must be true.

## R3 pass

Command/session:

- `aecf89d6-537b-42f9-9076-72381acde0c6` / `nova-bison`

Markers:

- `M7B_WHISPERCPP_LOCAL_STT_SMOKE_COMPLETE`
- `STICKBOT_TARS_M7B_WHISPERCPP_LOCAL_STT_SMOKE_PASS_R3`

Result:

```json
{
  "classification": "STICKBOT_TARS_M7B_WHISPERCPP_LOCAL_STT_FIXTURE_PASS",
  "whisperBinSha256": "427dfb509f2c04d0f01c101978b5666102c6f7e3abf2a236452db5939f5b533a",
  "whisperModelSha256": "a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002",
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
  "transcriptChars": 42,
  "transcriptSha256": "3e1f84be507525854b4acd7d9074dd1c7c55478130609fab0d509f97b6420075",
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
- Node workspace pointed at `/tmp/tars-m7b-boundary/workspace`.
- Raw transcript written only under `/tmp/tars-m7b-boundary/traces/transcript.txt` and not copied into durable evidence.

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

`STICKBOT_TARS_M7B_WHISPERCPP_LOCAL_STT_FIXTURE_PASS`

Next possible target:

`M7C_SMALL_EN_USABLE_DEMO_NOT_STARTED_REQUIRES_SEPARATE_APPROVAL`
