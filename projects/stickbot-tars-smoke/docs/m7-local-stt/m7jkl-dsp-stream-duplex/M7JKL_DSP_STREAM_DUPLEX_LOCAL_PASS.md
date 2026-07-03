# M7J / M7K / M7L — DSP, Streaming Frames, Full-Duplex Controller Local PASS

Date: 2026-07-03
Classification: `STICKBOT_TARS_M7JKL_DSP_STREAM_DUPLEX_LOCAL_PASS`

## Summary

Implemented the next M7x tranche after M7I:

- **M7J** — local DSP polish stage.
- **M7K** — streaming/realtime frame interface.
- **M7L** — deterministic full-duplex turn controller skeleton with barge-in/interruption semantics.

These are intentionally built as native stages in the same audio-performance mesh rather than bolted on after chunk rendering.

## New modules

```text
src/audio/dsp-polish-stage.js
src/audio/streaming-frame-interface.js
src/audio/full-duplex-turn-controller.js
```

## M7J — DSP polish stage

`src/audio/dsp-polish-stage.js` defines:

- DSP frame schema: `stickbot.tars.audio-dsp-frame.v1`
- deterministic prosody-to-DSP profile derivation,
- safe FFmpeg filter graph builder,
- local FFmpeg frame polish helper,
- chunk artifact polishing stage,
- public redacted DSP summary.

Current DSP profile is deliberately subtle:

- compressor,
- limiter,
- loudness normalization,
- bounded `atempo` from effective XTTS speed.

Boundaries:

- shell-free FFmpeg spawn,
- WSL-native path guard,
- `/mnt/c` blocked,
- no text rewrite,
- no voice identity rewrite,
- local only.

## M7K — streaming frame interface

`src/audio/streaming-frame-interface.js` defines:

- realtime frame schema: `stickbot.tars.realtime-audio-frame.v1`
- frame manifest schema: `stickbot.tars.realtime-frame-manifest.v1`
- frame iterator for future incremental playback.

Frame types currently emitted:

```text
turn_start
audio_chunk_ready
pause
turn_end
```

Each frame carries only redacted/audio-safe metadata:

- chunk id,
- text hash,
- phrase role,
- effective XTTS,
- audio hash/basename,
- pause timing,
- DSP profile summary when present.

Target remains:

```text
streaming_full_duplex_mesh
```

## M7L — full-duplex turn controller

`src/audio/full-duplex-turn-controller.js` defines a deterministic local state machine:

```text
idle -> listening -> thinking -> speaking -> interrupted -> listening
                                      -> complete
                                      -> failed
```

Supported events:

- `listen_start`
- `partial_transcript`
- `final_transcript`
- `assistant_text_ready`
- `audio_frame_ready`
- `barge_in`
- `resume_listening`
- `turn_complete`
- `error`

Barge-in behavior:

- stop active audio output,
- return to local listening,
- do not durably store raw transcript,
- keep safe text fallback available.

Invalid/out-of-order events are ignored safely rather than driving speculative state transitions.

## Integration

`xtts-chunk-conductor.js` now supports native DSP and realtime stages:

```text
prosody score
  -> chunk XTTS artifacts
  -> optional DSP chunk artifacts
  -> WAV stitch/render
  -> realtime frame manifest
  -> audio-performance pipeline summary
```

`server.js` passes `polishChunkArtifacts` as the DSP processor, so live local synthesis now routes through the M7J stage before stitching.

The public API summary includes:

- `voicePlan.audioPerformance.dspStage`
- `voicePlan.audioPerformance.realtime`
- `voicePlan.audioPerformance.pipeline.stages.dsp`
- `voicePlan.audioPerformance.pipeline.stages.realtime`

Raw chunk text remains internal to local synthesis; public artifacts use `textSha256`.

## Validation

Command:

```text
npm run check
```

Result:

```text
75/75 tests passed
```

New gates:

```text
STICKBOT_TARS_M7J_DSP_PROFILE_AND_FILTER_GRAPH_PASS
STICKBOT_TARS_M7J_DSP_STAGE_PROCESSES_CHUNK_ARTIFACTS_PASS
STICKBOT_TARS_M7K_STREAMING_FRAME_INTERFACE_PASS
STICKBOT_TARS_M7L_FULL_DUPLEX_TURN_CONTROLLER_BARGE_IN_PASS
STICKBOT_TARS_M7L_INVALID_EVENT_FAILS_SAFE_BY_IGNORING_PASS
STICKBOT_TARS_M7JKL_PIPELINE_INTEGRATION_SUMMARY_PASS
```

Regression gates preserved:

- M7I chunk conductor gates,
- M7H/M55 score engine gates,
- M7G prosody tuning/matrix gates,
- canonical text unchanged,
- no secret-like speech synthesis,
- network/config fail-closed rules,
- local STT/capture boundaries.

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

Raw transcript durable storage remains false in the full-duplex controller.

## Remaining work

This is still local deterministic infrastructure, not full live duplex audio UX.

Next practical milestones:

1. `M7M_LIVE_STREAMING_PLAYBACK_SMOKE` — browser/client consumes realtime frames and begins playback before final WAV completes.
2. `M7N_PARTIAL_STT_TO_TURN_CONTROLLER` — local partial STT events feed M7L without raw transcript durable storage.
3. `M7O_BARGE_IN_LIVE_AUDIO_STOP_SMOKE` — real mic barge-in interrupts current local playback and returns to listening.
