# M5.6 — TARS Voice Body / Mastering Postprocess PASS

Date: 2026-07-03
Classification: `STICKBOT_TARS_M56_VOICE_BODY_POSTPROCESS_PASS`

## Why

Before moving deeper into partial STT/full-duplex milestones, Stick recommended confirming the generated WAV format and adding a light local post-processing stage for TARS voice body rather than chasing heavy pitch changes.

Target format expectation:

```text
codec: pcm_s16le or pcm_s24le
sample_rate: 24000 internally
channels: 1
bit_rate: ~384 kbps for 16-bit mono 24 kHz, or ~576 kbps for 24-bit mono 24 kHz
```

Current code path before M5.6 already forced internal DSP/stitch output to:

```text
pcm_s16le / 24000 Hz / mono / ~384 kbps
```

One-off `ffprobe`/ad-hoc Python probes were approval-gated, so this milestone adds durable code/test gates instead of relying on a transient shell probe.

## Implementation

Added local module:

```text
src/audio/voice-body-mastering-stage.js
```

The stage runs after M7J DSP and before M7K realtime frames / final stitch, so browser playback uses the mastered artifacts rather than leaving the stage unused.

Processing chain:

```text
XTTS raw mono chunk WAV
  -> M7J DSP light polish chunk WAV
  -> M5.6 voice-body mastered chunk WAV
  -> streaming frame playback + final stitched playback WAV
```

Filter family:

```text
silence trim
highpass ~60 Hz
low-mid body boost around 170 Hz
upper-body support around 320 Hz
presence restraint around 3.2 kHz
compression
loudness normalization
mono 48 kHz browser playback WAV
```

Default output target:

```json
{
  "codec": "pcm_s16le",
  "sampleRate": 48000,
  "channels": 1,
  "bitRate": 768000
}
```

This keeps the canonical generated artifacts mono and makes stereo/widening a later optional browser-only enhancement.

## Important integration details

- Raw XTTS chunk artifacts are preserved.
- DSP intermediates are preserved.
- Mastered chunk files are generated as `.master.wav`.
- Realtime frames now include a `mastering` payload.
- Browser frame playback now prefers `mastering.outputFileBasename`, then DSP, then raw file basename.
- Final stitched WAV uses the mastered chunk sequence and mono 48 kHz output.
- `safety/audio-path-policy.js` now narrowly allows UUID `.master.wav` and generated UUID chunk `.master.wav` names only.

## Gates

Added/updated gates:

```text
STICKBOT_TARS_M56_VOICE_BODY_PROFILE_AND_FILTER_PASS
STICKBOT_TARS_M56_VOICE_BODY_STAGE_PRESERVES_RAW_AND_MASTERS_PASS
STICKBOT_TARS_M7K_STREAMING_FRAME_INTERFACE_PASS includes mastering payload
STICKBOT_TARS_M7JKL_PIPELINE_INTEGRATION_SUMMARY_PASS includes mastering stage
```

Validation:

```text
npm run check -> 82/82 PASS
```

## Boundaries

Preserved:

- canonical assistant text authoritative,
- no text rewrite,
- no voice identity rewrite,
- local-only FFmpeg processing,
- no cloud STT,
- no browser Web Speech API,
- no OpenClaw/Gateway/NOA routing/default/provider mutation,
- no port `8787`,
- no generated audio committed.

## Live smoke

Refreshed HTTPS LAN demo server loaded M5.6 successfully.

LAN checks:

```text
https://192.168.1.107:19890/health -> OK
index.html -> app.js?v=m56-voice-body-mastering
```

Live `/api/chat` smoke text:

```text
PASS. Keep the voice heavy, clean, and local.
```

Result summary:

```json
{
  "ok": true,
  "audioUrl": "/audio/f470fbd4-4015-4368-aab3-53d25d0701f1.wav",
  "masteringEnabled": true,
  "outputFormat": {
    "codec": "pcm_s16le",
    "sampleRate": 48000,
    "channels": 1,
    "bitRate": 768000
  },
  "frameCount": 3,
  "masteredFrames": 3,
  "firstMaster": "f470fbd4-4015-4368-aab3-53d25d0701f1-chunk-001.dsp.master.wav"
}
```

Human A/B listening remains the next subjective quality check: confirm heavier/cleaner TARS body without muddy low-mid buildup.
