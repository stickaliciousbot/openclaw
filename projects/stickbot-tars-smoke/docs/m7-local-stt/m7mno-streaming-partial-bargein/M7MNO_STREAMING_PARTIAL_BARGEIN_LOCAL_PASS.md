# M7M / M7N / M7O — Streaming Playback, Partial STT Ingress, Barge-In Smoke Local PASS

Date: 2026-07-03
Classification: `STICKBOT_TARS_M7MNO_STREAMING_PARTIAL_BARGEIN_LOCAL_PASS`

## Summary

Implemented the next live-facing layer on top of M7J/K/L:

- **M7M** — browser/client consumes realtime frame manifests and can play generated chunk audio in frame order with computed pauses.
- **M7N** — partial/final STT controller ingress with redacted transcript events and no raw transcript durable storage.
- **M7O** — barge-in smoke path: starting mic capture stops active playback and drives a deterministic duplex-controller interruption/resume scenario.

This remains local-first and deterministic. It does not introduce cloud STT, browser Web Speech API, Gateway/runtime mutation, provider routing changes, Android changes, or LAN exposure changes.

## M7M — streaming playback smoke

Changes:

- `public/app.js` now consumes `voicePlan.audioPerformance.realtime.frames`.
- `audio_chunk_ready` frames are mapped to generated chunk audio URLs.
- Browser playback plays chunk frames in order and waits each frame's computed pause duration.
- Final stitched WAV remains available as fallback.
- Audio route policy now admits only:
  - final UUID `.wav`,
  - generated UUID chunk `.wav`,
  - generated UUID chunk `.dsp.wav`.

Security/safety:

- No nested paths.
- No traversal.
- No arbitrary filenames.
- No non-WAV files.
- Chunk access remains limited to generated UUID chunk naming.

## M7N — partial/final STT controller ingress

New module:

```text
src/audio/duplex-event-ingress.js
```

New server endpoints:

```text
POST /api/stt/partial
POST /api/duplex/scenario
```

Behavior:

- Raw partial/final transcript text is converted to `textSha256` + `charCount` before controller summaries.
- Public duplex summaries do not expose raw transcript text.
- `/api/stt` final transcript responses now include a duplex controller summary.
- Durable raw transcript storage remains false.

## M7O — barge-in smoke

Browser behavior:

- If M7M chunk playback is active and the mic button is pressed, playback is stopped.
- UI sends a local `/api/duplex/scenario` smoke sequence:
  - listen start,
  - final transcript marker,
  - assistant text ready,
  - audio frame ready,
  - barge-in,
  - resume listening.
- The controller returns to `listening` with `stop_audio_output` and `return_to_local_listening` actions.

This is a smoke path for interruption semantics. It is not yet live partial STT or true low-latency duplex transport.

## Validation

Command:

```text
npm run check
```

Result:

```text
80/80 tests passed
```

New gates:

```text
generated UUID chunk .wav files are accepted for streaming playback smoke
STICKBOT_TARS_M7N_PARTIAL_STT_CONTROLLER_INGRESS_PASS
STICKBOT_TARS_M7N_FINAL_STT_CONTROLLER_INGRESS_PASS
STICKBOT_TARS_M7N_SANITIZES_RAW_TRANSCRIPT_EVENTS_PASS
STICKBOT_TARS_M7O_BARGE_IN_SCENARIO_INGRESS_PASS
```

Regression gates preserved:

- M7J/K/L DSP/stream/duplex gates,
- M7I chunk conductor gates,
- M7H/M55 score engine gates,
- M7G prosody tuning/matrix gates,
- config/network fail-closed rules,
- local STT/capture boundaries,
- no-secret speech synthesis,
- canonical text unchanged.

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

Raw transcript durable storage remains false for duplex-controller paths.

## Remaining work

Next practical milestones:

1. **M7P — live browser verification**: run the HTTPS local demo and verify chunk-frame playback + mic barge-in with human/browser evidence.
2. **M7Q — true partial local STT loop**: feed incremental local STT updates into M7L rather than metadata-only partial ingress.
3. **M7R — low-latency streaming transport**: SSE/WebSocket or equivalent frame transport so playback can begin while later chunks are still synthesizing.
