# Stickbot-TARS production voice stream architecture

Date: 2026-07-03
Status: design note captured during M5.6 R4 live browser validation

## Key clarification

The current browser smoke stack is a proving harness, not the final production shape.

In production, Stickbot-TARS should not be framed as:

```text
record Stick -> transcribe Stick -> convert Stick's words into TARS voice
```

The target is:

```text
assistant response generation -> live TARS audio stream
                          \-> parallel canonical text channel
```

The audio stream is the primary real-time output. The text channel exists for chat surfaces, memory, search, audit, and accessibility.

## Multiplexed output model

A production turn should produce at least two coordinated channels:

1. **Audio channel**
   - streams generated WAV/PCM frames directly,
   - carries prosody/mood/sheet-music timing,
   - owns playback lifecycle,
   - handles interruption/break-in/barge-in,
   - may be cancelled mid-stream without invalidating the canonical text record.

2. **Text channel**
   - records canonical assistant text,
   - feeds chat surfaces and memories,
   - remains authoritative for meaning/audit,
   - does not need to handle audio break-in itself.

The channels should share a turn id and provenance, but audio interruption should not require mutating or deleting the canonical text channel.

## Audio-first artifact direction

The ideal path is not “generate all text, then render a final WAV.” It should support direct audio artifacts/streams:

- chunked PCM/WAV frames,
- sequence metadata,
- audio hashes/provenance,
- prosody cues,
- cancellation/interruption markers,
- final optional stitch/export for replay only.

Text may still be generated in parallel for capture, but the audio stream should be able to progress as soon as safe response/prosody units are available.

## Live prosody drive requirement

Before closing Stickbot-TARS as done, test Stickbot's ability to live-drive prosody:

- create its own mood score,
- create “emotional sheet music” for the response,
- use prosody emojis/cues as expressive markup where useful,
- keep canonical text unchanged,
- prove the mood/sheet-music layer changes delivery rather than rewriting meaning.

Stick's current subjective preference: the most TARS-like voice setting is the mission brief / marine commander direction. Keep experimenting with prosody emojis and live mood scoring, but treat that preset family as the strongest TARS baseline so far.

## Break-in ownership

Break-in belongs to the live audio channel.

If the user interrupts:

- stop/cancel active audio frames,
- record an interruption marker,
- return to listening,
- keep the canonical text channel intact unless a higher-level turn policy decides to supersede it.

## Current browser-smoke relationship

M5.6/M7 browser work remains useful because it proves:

- local XTTS rendering,
- prosody/chunking,
- DSP/mastering,
- streaming playback mechanics,
- browser/device drain behavior,
- barge-in lifecycle,
- privacy boundaries.

But production should evolve toward audio-first multiplexed streaming rather than browser final-WAV playback as the primary architecture.

## Contract layer added — 2026-07-03

Milestone classification:

```text
STICKBOT_TARS_AUDIO_FIRST_MULTIPLEXED_PRODUCTION_STREAMING_ARCHITECTURE_LOCAL_CONTRACT_PASS
```

The production-facing contract now lives at:

```text
src/audio/production-multiplex-contract.js
```

It defines five lanes for each turn:

1. `canonical_text` — authoritative text/hash lane for meaning, audit, memory, search, chat, and accessibility.
2. `audio_pcm_stream` — primary realtime output lane for direct WAV/PCM frames, cancellable by barge-in.
3. `prosody_metadata` — mood score, emotional sheet music, and cue glyphs; delivery metadata only.
4. `control_events` — turn lifecycle and barge-in policy.
5. `audit_trace` — hashes, provenance, and interruption markers without raw transcript storage.

Hard invariants:

```json
{
  "canonicalTextHashSharedByAllLanes": true,
  "audioLaneOwnsBargeIn": true,
  "audioCancellationPreservesTextLane": true,
  "prosodyMetadataCannotRewriteText": true,
  "auditUsesHashesNotRawText": true
}
```

The runtime harness milestone now lives at:

```text
src/audio/production-multiplex-runtime-harness.js
```

It reached:

```text
STICKBOT_TARS_AUDIO_FIRST_MULTIPLEXED_RUNTIME_HARNESS_LIVE_PASS
```

The harness emits a complete local turn across all lanes and proves barge-in cancels audio while preserving the canonical text lane. Next proof should expose/read back this contract through the local browser/API harness without mutating OpenClaw/Gateway routing.
