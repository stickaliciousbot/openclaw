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

## R2 — end-trim truncation fix

Stick reported that M5.6 sounded much better, but the browser output was only about `0:02` and cut off mid-sentence.

Root cause:

```text
silenceremove ... stop_periods=1 ...
```

The end-trim side of `silenceremove` can interpret a normal phrase pause as end-of-audio and truncate the mastered chunk/final output.

Fix:

- keep conservative leading-silence trim,
- remove end/tail silence trim entirely,
- set `trimLeadingSilenceOnly: true`,
- set `trimEndingSilence: false`,
- add a regression gate that the M5.6 filter must not contain `stop_periods=`.

Validation after fix:

```text
npm run check -> 82/82 PASS
targeted tars-dsp-stream-duplex tests -> 8/8 PASS
```

Live smoke after refreshed server:

```json
{
  "ok": true,
  "audioUrl": "/audio/54ac75b8-7852-4401-b5cf-d2bd995a5867.wav",
  "masteringEnabled": true,
  "outputFormat": {
    "codec": "pcm_s16le",
    "sampleRate": 48000,
    "channels": 1,
    "bitRate": 768000
  },
  "frameCount": 3,
  "masteredFrames": 3,
  "firstMaster": "54ac75b8-7852-4401-b5cf-d2bd995a5867-chunk-001.dsp.master.wav"
}
```

Final playback WAV duration proof:

```json
{
  "file": "54ac75b8-7852-4401-b5cf-d2bd995a5867.wav",
  "codec": "pcm_s16le",
  "sampleRate": 48000,
  "channels": 1,
  "bitRate": 768000,
  "durationSeconds": 4.255
}
```

## R3 — tail guard for final syllable clipping

Stick then confirmed sentence timing was much better but the last syllable still clipped slightly:

> it replayed 99.8% of it and only clipped the last syllable from the entire sentence.

Fix:

- Add a conservative 320 ms `apad` tail guard after mastering.
- Keep improved voice-body EQ/compression.
- Keep end/tail trimming disabled.
- Add regression assertion for `apad=pad_dur=0.320`.

Validation:

```text
npm run check -> 82/82 PASS
targeted tars-dsp-stream-duplex tests -> 8/8 PASS
```

Live smoke after refreshed server:

```json
{
  "ok": true,
  "audioUrl": "/audio/dff8aa9d-e95a-4910-8419-962bae538516.wav",
  "masteringEnabled": true,
  "outputFormat": {
    "codec": "pcm_s16le",
    "sampleRate": 48000,
    "channels": 1,
    "bitRate": 768000
  },
  "frameCount": 3,
  "masteredFrames": 3,
  "firstMaster": "dff8aa9d-e95a-4910-8419-962bae538516-chunk-001.dsp.master.wav"
}
```

Tail-guard final playback WAV duration proof:

```json
{
  "file": "dff8aa9d-e95a-4910-8419-962bae538516.wav",
  "codec": "pcm_s16le",
  "sampleRate": 48000,
  "channels": 1,
  "bitRate": 768000,
  "durationSeconds": 5.035
}
```

## R4 — terminal TTS tail hint + longer output drain PASS

Stick confirmed the M5.6 sound was great and barge-in still worked, but R3 still cut the very last syllable in half abruptly.

Diagnosis:

- R3 silence padding helped playback drain, but cannot recover a terminal phoneme if XTTS itself stops the final waveform too abruptly.
- The fix should preserve the M5.6 voice body and barge-in behavior.

Fix:

- Increase post-mastering `apad` tail guard from 320 ms to 900 ms.
- Apply a TTS-only terminal render hint on the final chunk by appending an ellipsis to the text sent to XTTS.
- Preserve canonical text and canonical text hash; the render hint is tracked separately as `renderTextSha256` / `terminalTailHintApplied`.
- Keep public summaries free of raw chunk text.

R4 live verification:

```json
{
  "ok": true,
  "audioUrl": "/audio/3a5664c9-c6ae-44a4-9a48-20cbabc8f8eb.wav",
  "hasPad900": true,
  "hasTerminalTailHint": true,
  "frameCount": 3,
  "chunkCount": 3,
  "textRewriteAllowed": false
}
```

Human confirmation:

```text
The sentence finished perfectly.
```

Barge-in confirmation:

```text
Stick also retested that barge-in still works.
```

R4 classification:

```text
STICKBOT_TARS_M56_R4_TERMINAL_TAIL_DRAIN_LIVE_PASS
```
