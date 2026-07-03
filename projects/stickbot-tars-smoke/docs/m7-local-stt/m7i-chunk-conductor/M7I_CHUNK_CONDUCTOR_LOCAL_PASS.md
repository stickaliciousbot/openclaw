# M7I Chunk Conductor — Local PASS

Date: 2026-07-03
Classification: `STICKBOT_TARS_M7I_CHUNK_CONDUCTOR_LOCAL_PASS`

## Summary

M7I turns the M7H/M55 prosody score into a real audio performance pipeline.

Instead of sending the whole assistant reply to XTTS with one averaged envelope, the runtime now:

```text
canonical assistant text
  -> M7H/M55 prosody score
  -> per-chunk XTTS synthesis frames
  -> local WAV chunk artifacts
  -> local render/stitch stage with computed pauses/rests
  -> one playable WAV response
  -> public trace / audio-performance summary
```

The implementation intentionally carves native seams for later DSP, realtime effects, and streaming full-duplex operation. DSP and streaming are not bolted on after the fact; they are represented as reserved pipeline stages with stable frame schemas.

## New modules

```text
src/audio/audio-performance-pipeline.js
src/audio/wav-stitcher.js
src/audio/xtts-chunk-conductor.js
```

### `audio-performance-pipeline.js`

Defines the local audio mesh contract:

- canonical text stage,
- prosody score stage,
- chunk synthesis frame stage,
- DSP reserved stage,
- render stage,
- realtime/streaming reserved stage.

Reserved future schemas:

```text
stickbot.tars.audio-dsp-frame.v1
stickbot.tars.realtime-audio-frame.v1
```

Target future mode:

```text
streaming_full_duplex_mesh
```

### `wav-stitcher.js`

Local FFmpeg-backed WAV renderer:

- shell-free `spawn`,
- WSL-native path guard,
- `/mnt/c` blocked,
- computed silence/rest WAVs between chunks,
- concat render to one WAV,
- single-chunk copy fast path.

### `xtts-chunk-conductor.js`

Converts a raw internal prosody score into audio chunk artifacts:

- fails closed if canonical text/hash boundaries are violated,
- calls XTTS once per scored chunk using that chunk's effective XTTS params,
- writes chunk WAV artifacts locally,
- stitches final WAV locally,
- exposes redacted public summaries using text hashes, not raw chunk text.

## Server integration

`server.js` now uses the chunk conductor inside `synthesize()`:

- loads active tuning/matrix state,
- builds the TARS prosody plan,
- checks no-secret speech gate,
- uses raw internal `prosodyScoreRaw` for synthesis,
- synthesizes chunks through local XTTS loopback,
- stitches final WAV,
- attaches `voicePlan.audioPerformance` to the API response.

The public `voicePlan.prosodyScore` remains redacted; raw chunk text is only used inside the local synthesis path.

## Future mesh hooks

M7I reserves native insertion points for later work:

1. **DSP polish stage**
   - loudness normalize,
   - clip guard,
   - compression,
   - rate/pitch polish.

2. **Realtime effects stage**
   - operate per chunk/frame before final stitch,
   - can stream frames incrementally rather than waiting for final WAV.

3. **Full duplex streaming stage**
   - same chunk-frame contract can become streaming frames,
   - planned path: STT partials -> turn controller -> prosody score deltas -> chunk synth frames -> audio output frames.

## Validation

Command:

```text
npm run check
```

Result:

```text
69/69 tests passed
```

New gates:

```text
STICKBOT_TARS_M7I_CHUNK_SYNTH_USES_PER_CHUNK_EFFECTIVE_XTTS_PASS
STICKBOT_TARS_M7I_CONDUCTOR_STITCHES_AND_EXPOSES_PUBLIC_MESH_SUMMARY_PASS
STICKBOT_TARS_M7I_CANONICAL_BOUNDARY_FAILS_CLOSED_PASS
```

Regression gates preserved:

- M7H/M55 score engine gates,
- M7G prosody tuning/matrix gates,
- canonical text unchanged,
- no secret-like speech synthesis,
- config/network fail-closed boundaries,
- STT local/capture boundaries.

## Boundaries preserved

No changes to:

- OpenClaw routing/defaults/fallbacks,
- Gateway config/service state,
- NOA,
- Android,
- provider settings,
- model runtime isolation,
- LAN exposure,
- port `8787`,
- cloud speech APIs,
- browser Web Speech API.

Canonical assistant text remains authoritative. No speakability rewrite was introduced in M7I.

## Current limitation

This is still local sequential chunk synthesis. It is not yet realtime/full duplex.

Next recommended milestones:

1. `M7J_DSP_POLISH_STAGE_LOCAL_PASS` — implement the reserved DSP frame stage.
2. `M7K_STREAMING_FRAME_INTERFACE_PASS` — emit/consume chunk frames incrementally for streaming playback.
3. `M7L_FULL_DUPLEX_TURN_CONTROLLER_PASS` — coordinate partial STT, interruption/barge-in, and realtime output.
