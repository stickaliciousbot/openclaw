# M7Q — True Partial Local STT Loop LIVE PASS

Date: 2026-07-03
Classification: `STICKBOT_TARS_M7Q_TRUE_PARTIAL_LOCAL_STT_LOOP_LIVE_PASS`

## Purpose

Move beyond deterministic partial-text ingress by wiring browser mic slices into the local STT path:

```text
browser MediaRecorder slices
  -> POST /api/stt/partial-audio
  -> local file save
  -> optional local FFmpeg normalization
  -> local whisper.cpp transcript
  -> sanitized partial duplex controller summary
```

This is still local-only and does not use browser Web Speech API or cloud STT.

## Implementation

Added:

```text
src/audio/partial-stt-loop.js
```

New server endpoint:

```text
POST /api/stt/partial-audio?turnId=<id>&seq=<n>
```

Behavior:

- accepts browser audio slice uploads,
- saves audio locally under the existing controlled input directory,
- normalizes with local FFmpeg when `STT_NORMALIZE_AUDIO=true`,
- transcribes with configured local STT when `STT_MODE=cli`,
- returns a browser-visible partial transcript for UX,
- returns a sanitized duplex summary where raw transcript text is replaced by hash/count,
- tolerates empty partial STT output as `NO_TRANSCRIPT` rather than failing the whole recording loop.

Browser changes:

- `MediaRecorder.start(2500)` enables periodic slice events,
- each partial upload sends the accumulated recording-so-far rather than a standalone WebM fragment, because individual WebM timeslices are not always independently decodable,
- final stop path still submits the full recording to `/api/stt`,
- partial transcripts are displayed as provisional local STT slices and do not overwrite the final input text.

## Privacy and safety boundaries

Preserved:

- local-only STT path,
- no cloud speech API,
- no browser Web Speech API,
- no durable raw transcript storage,
- no OpenClaw/Gateway/NOA/provider/routing/default mutation,
- no port `8787`,
- canonical text remains authoritative.

The HTTP response may include browser-visible `partialTranscript` so the UI can show what local STT heard, but durable controller summaries use `textSha256`/`charCount` and do not store raw transcript text.

## Gates

Added/updated gates:

```text
STICKBOT_TARS_M7Q_TRUE_PARTIAL_LOCAL_STT_LOOP_RESPONSE_PASS
STICKBOT_TARS_M7Q_EMPTY_PARTIAL_LOCAL_STT_LOOP_NO_TRANSCRIPT_PASS
```

Validation:

```text
targeted node --check + node --test test/tars-stream-duplex-ingress.test.mjs -> 6/6 PASS
npm run check -> 84/84 PASS
```

## Live status

The HTTPS LAN demo was restarted through the STT-aware local path. Readiness checks:

```json
{
  "healthLoopback": true,
  "healthLan": true,
  "capabilities": {
    "sttMode": "cli",
    "partialLocalSttLoop": true,
    "voiceReady": true
  }
}
```

Server-side endpoint smokes:

```json
{
  "partialAudio": {
    "classification": "STICKBOT_TARS_M7Q_TRUE_PARTIAL_LOCAL_STT_LOOP_PASS",
    "sttMode": "cli",
    "normalizedLocal": true,
    "transcriptPresent": true,
    "rawTranscriptDurableStorage": false,
    "browserWebSpeechApi": false,
    "cloudSpeechApi": false,
    "duplexState": "listening"
  },
  "finalStt": {
    "sttMode": "cli",
    "normalizedLocal": true,
    "transcriptPresent": true,
    "rawTranscriptDurableStorage": false,
    "browserWebSpeechApi": false,
    "cloudSpeechApi": false,
    "duplexState": "thinking"
  }
}
```

Human browser evidence from Stick:

```text
PASSED ✅
```

Screenshot evidence showed:

- `Partial STT` seq `0` through `5` progressively expanding the transcript,
- final `Mic transcript` filled the input text,
- duplex state `thinking`,
- each partial line marked `local whisper slice`,
- privacy guard displayed as `raw mic transcript durable storage is off`.

Final classification:

```text
STICKBOT_TARS_M7Q_TRUE_PARTIAL_LOCAL_STT_LOOP_LIVE_PASS
```
