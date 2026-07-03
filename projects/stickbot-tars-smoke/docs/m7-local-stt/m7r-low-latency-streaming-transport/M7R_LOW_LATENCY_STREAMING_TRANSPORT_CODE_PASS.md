# M7R — Low-Latency Streaming Transport CODE PASS

Date: 2026-07-03
Classification: `STICKBOT_TARS_M7R_LOW_LATENCY_STREAMING_TRANSPORT_CODE_PASS_LIVE_TIMING_PENDING`

## Scope

M7R adds an explicit low-latency transport contract to the existing realtime frame manifest and updates the browser playback path to use a preloaded serial queue with client-side timing telemetry.

This is a transport/timing milestone. It does **not** change canonical text, STT authority, OpenClaw routing, Gateway config, NOA, provider settings, or the local-only/privacy boundary.

## Implemented

- Added `LOW_LATENCY_TRANSPORT_SCHEMA` and `buildLowLatencyTransportPlan()` in `src/audio/streaming-frame-interface.js`.
- Realtime manifests now include `transport`:
  - schema: `stickbot.tars.low-latency-transport.v1`
  - classification: `STICKBOT_TARS_M7R_LOW_LATENCY_STREAMING_TRANSPORT_READY`
  - mode: `browser_preload_queue_then_serial_playback`
  - queue target: `2`
  - first-audio target: `1200ms`
  - inter-chunk gap target: `120ms`
  - telemetry contract for first-play and gap timing.
- Browser streaming path now:
  - builds an audio queue from realtime chunk frames,
  - preloads the first queue-depth frames eagerly,
  - serially plays queued frames,
  - records client telemetry:
    - `queueBuiltMs`
    - `firstFrameCanPlayMs`
    - `firstAudioPlayMs`
    - `maxInterChunkGapMs`
    - `playedFrameCount`
    - `cancelled`
  - displays `STICKBOT_TARS_M7R_LOW_LATENCY_CLIENT_TELEMETRY` in the live UI.
- Updated static cache buster to `/app.js?v=m7r-low-latency-transport`.

## Validation

Focused gate:

```text
node --check src/audio/streaming-frame-interface.js
node --check public/app.js
node --test test/tars-dsp-stream-duplex.test.mjs
```

Result:

```text
9/9 PASS
```

Full project gate:

```text
npm run check
```

Result:

```text
85/85 PASS
```

New/updated gates:

- `STICKBOT_TARS_M7K_STREAMING_FRAME_INTERFACE_PASS` now verifies embedded M7R transport plan.
- `STICKBOT_TARS_M7R_LOW_LATENCY_STREAMING_TRANSPORT_CONTRACT_PASS` verifies queue/depth/target/telemetry/boundary contract.

## Live status

Code/local gate is complete. Live browser timing proof is pending.

Pending live evidence for full M7R pass:

- refreshed browser serves `/app.js?v=m7r-low-latency-transport`,
- voice turn shows `Streaming transport` line,
- voice turn shows `Streaming telemetry` line,
- first-play and max-gap values appear,
- audio still plays in order,
- M7Q mic partials still work,
- barge-in still stops active TARS playback,
- boundaries remain local-only/no-cloud/no-Web-Speech/no-routing-mutation.

Pending classification:

```text
STICKBOT_TARS_M7R_LOW_LATENCY_STREAMING_TRANSPORT_LIVE_PASS
```

## Boundaries

```json
{
  "localOnly": true,
  "canonicalTextAuthoritative": true,
  "textRewriteAllowed": false,
  "rawTranscriptDurableStorage": false,
  "browserWebSpeechApi": false,
  "cloudSpeechApi": false,
  "gatewayMutationAllowed": false,
  "openClawRoutingMutationAllowed": false,
  "port8787Touched": false
}
```
