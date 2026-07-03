# Audio-First Multiplexed Runtime Harness — Local Live PASS

Date: 2026-07-03
Classification: `STICKBOT_TARS_AUDIO_FIRST_MULTIPLEXED_RUNTIME_HARNESS_LIVE_PASS`

## Objective

Wire the audio-first multiplex production contract into a deterministic local runtime harness and prove one assistant turn emits all production lanes end-to-end:

- canonical text lane,
- audio PCM stream lane,
- prosody metadata lane,
- control events lane,
- audit trace lane.

The harness must also prove that barge-in cancels audio while preserving the canonical text hash.

## Implementation

Added:

```text
src/audio/production-multiplex-runtime-harness.js
```

The harness performs:

1. Builds a canonical TARS prosody plan from assistant text.
2. Refuses secret-like assistant text before audio rendering.
3. Synthesizes deterministic local audio frame artifacts.
4. Builds the existing realtime frame manifest.
5. Builds the five-lane production multiplex contract.
6. Simulates lifecycle events, including barge-in.
7. Returns a public summary with hashes, counts, lane metadata, and event effects only.

No raw assistant text is included in the public runtime summary.

## Runtime proof classification

```text
STICKBOT_TARS_AUDIO_FIRST_MULTIPLEXED_RUNTIME_HARNESS_LIVE_PASS
```

## Barge-in proof

The runtime harness emits a `barge_in` event whose effects include:

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

## Focused validation

Command:

```text
node --check src/audio/production-multiplex-runtime-harness.js
node --test test/tars-dsp-stream-duplex.test.mjs
```

Result:

```text
14/14 PASS
```

Full project gate:

```text
npm run check
```

Result:

```text
92/92 PASS
```

Rehydrator:

```text
sourceCount: 57
missingSources: []
```

New deterministic tests:

```text
STICKBOT_TARS_AUDIO_FIRST_MULTIPLEXED_RUNTIME_HARNESS_LIVE_PASS
STICKBOT_TARS_AUDIO_FIRST_RUNTIME_HARNESS_SECRET_TEXT_FAILS_CLOSED_PASS
```

## Boundaries

```json
{
  "localOnly": true,
  "audioFirst": true,
  "canonicalTextAuthoritative": true,
  "textRewriteAllowed": false,
  "rawTranscriptDurableStorage": false,
  "cloudSpeechApiAllowed": false,
  "browserWebSpeechApiAllowed": false,
  "gatewayMutationAllowed": false,
  "openClawRoutingMutationAllowed": false,
  "port8787Touched": false
}
```

## Result

```text
STICKBOT_TARS_AUDIO_FIRST_MULTIPLEXED_RUNTIME_HARNESS_LIVE_PASS
```

## Next recommended milestone

```text
AUDIO_FIRST_MULTIPLEXED_BROWSER_LIVE_CONTRACT_PROOF
```

That next milestone should expose/read back this runtime harness through the local browser/API harness and prove the five-lane contract appears on a real local turn without mutating OpenClaw/Gateway routing.
