# Audio-First Multiplexed Production Streaming Architecture — Local Contract PASS

Date: 2026-07-03
Classification: `STICKBOT_TARS_AUDIO_FIRST_MULTIPLEXED_PRODUCTION_STREAMING_ARCHITECTURE_LOCAL_CONTRACT_PASS`

## Objective

Define and validate the production-facing Stickbot-TARS turn contract that moves beyond browser smoke/demo shape toward audio-first, multiplexed streaming.

The key architecture rule is:

```text
canonical assistant text remains authoritative
live WAV/PCM audio frames are the primary real-time output
prosody/cue metadata drives delivery without rewriting text
barge-in cancels audio, not the canonical text record
```

## Implementation

Added:

```text
src/audio/production-multiplex-contract.js
```

The contract builds five coordinated lanes sharing a turn id and canonical text hash:

1. `canonical_text`
   - authoritative meaning/audit/search/accessibility lane
   - not interruptible by audio playback
   - not mutable by barge-in
2. `audio_pcm_stream`
   - primary realtime output lane
   - direct WAV/PCM frame target
   - interruptible/cancellable
   - optional final WAV remains replay/fallback only
3. `prosody_metadata`
   - mood score + emotional sheet music + cue glyphs
   - delivery metadata only
   - no text rewrite authority
4. `control_events`
   - turn lifecycle and barge-in policy
   - audio channel owns interruption
5. `audit_trace`
   - hashes, frame provenance, prosody hashes, interruption markers
   - no raw transcript text and no cloud audio path

## Contract classification

```text
STICKBOT_TARS_AUDIO_FIRST_MULTIPLEXED_PRODUCTION_STREAMING_ARCHITECTURE_READY
```

## Invariants

```json
{
  "canonicalTextHashSharedByAllLanes": true,
  "audioLaneOwnsBargeIn": true,
  "audioCancellationPreservesTextLane": true,
  "prosodyMetadataCannotRewriteText": true,
  "auditUsesHashesNotRawText": true
}
```

## Barge-in semantics

`reduceProductionMultiplexEvent(..., { type: "barge_in" })` emits effects:

```json
[
  {
    "lane": "audio_pcm_stream",
    "action": "cancel_active_audio_frames",
    "preserveCanonicalText": true
  },
  {
    "lane": "control_events",
    "action": "return_to_local_listening",
    "durableRawTranscript": false
  },
  {
    "lane": "audit_trace",
    "action": "record_interruption_marker",
    "rawTranscriptStored": false
  }
]
```

## Validation

Focused gate:

```text
node --check src/audio/production-multiplex-contract.js
node --test test/tars-dsp-stream-duplex.test.mjs
```

Result:

```text
12/12 PASS
```

Full project gate:

```text
npm run check
```

Result:

```text
90/90 PASS
```

Rehydrator:

```text
sourceCount: 55
missingSources: []
```

New deterministic tests:

```text
STICKBOT_TARS_AUDIO_FIRST_MULTIPLEXED_PRODUCTION_STREAMING_ARCHITECTURE_CONTRACT_PASS
STICKBOT_TARS_AUDIO_FIRST_BARGE_IN_CANCELS_AUDIO_NOT_TEXT_PASS
STICKBOT_TARS_AUDIO_FIRST_HASH_MISMATCH_FAILS_CLOSED_PASS
```

## Boundaries

```json
{
  "localOnly": true,
  "audioFirst": true,
  "canonicalTextAuthoritative": true,
  "textRewriteAllowed": false,
  "audioInterruptionMutatesText": false,
  "rawTranscriptDurableStorage": false,
  "rawAudioCloudUploadAllowed": false,
  "cloudSpeechApiAllowed": false,
  "browserWebSpeechApiAllowed": false,
  "gatewayMutationAllowed": false,
  "openClawRoutingMutationAllowed": false,
  "port8787Allowed": false
}
```

## Result

```text
STICKBOT_TARS_AUDIO_FIRST_MULTIPLEXED_PRODUCTION_STREAMING_ARCHITECTURE_LOCAL_CONTRACT_PASS
```

## Next recommended milestone

```text
AUDIO_FIRST_MULTIPLEXED_RUNTIME_HARNESS_LIVE_PASS
```

That next milestone should wire this contract into a local runtime harness and prove a full turn emits canonical text, prosody metadata, audio frames, and barge-in/cancel audit events through the same multiplexed contract.
