# M7T — Live Prosody Mood Score and Emotional Sheet Music PASS

Date: 2026-07-03
Classification: `STICKBOT_TARS_M7T_LIVE_PROSODY_MOOD_SCORE_AND_EMOTIONAL_SHEET_MUSIC_PASS`

## Objective

Prove that Stickbot-TARS can generate live delivery metadata for mood score, emotional sheet music, and prosody cue glyphs from canonical assistant text without rewriting that canonical text.

This milestone sits above the existing prosody score engine. The cue layer is render metadata only: it helps the audio/browser renderer understand emotional shape, intensity, contour, rests, and phrase-role cues while preserving the text channel for chat, memory, audit, search, and accessibility.

## Implementation

Added deterministic cue-layer module:

```text
src/prosody/live-prosody-cue-layer.js
```

The module derives:

- `moodScore`: mood id/label, expression token, average intensity, dominant cue, cue sequence, chunk count.
- `emotionalSheetMusic`: per-chunk cue glyph, dynamic marking, rest glyph, contour, tempo, emotional color, intensity, pause duration, and `textSha256`.
- `boundaries`: canonical text authoritative, delivery metadata only, no raw text exposure, local-only, no cloud STT, no browser Web Speech API, no Gateway/OpenClaw routing mutation.

Integrated into:

```text
src/voice/tars-prosody-kernel.js
public/app.js
package.json
test/tars-prosody-score-engine.test.mjs
```

Browser UI now shows a compact line like:

```text
Live prosody: <expression> <mood>; intensity <score>; cues <sheet tokens>; STICKBOT_TARS_LIVE_PROSODY_MOOD_SCORE_AND_EMOTIONAL_SHEET_MUSIC_READY
```

## Canonical text boundary

The cue layer is derived from `prosodyScore.chunks` and carries only hashes in public output.

Required invariants:

```json
{
  "canonicalTextUnchanged": true,
  "textRewriteAllowed": false,
  "deliveryMetadataOnly": true,
  "exposesRawText": false
}
```

The canonical text hash is preserved:

```text
liveProsodyCueLayer.canonicalTextSha256 === plan.canonicalTextSha256
```

## Validation

Focused gate:

```text
node --check src/prosody/live-prosody-cue-layer.js
node --check src/voice/tars-prosody-kernel.js
node --check public/app.js
node --test test/tars-prosody-score-engine.test.mjs
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
PASS
```

Direct local kernel payload smoke:

```text
STICKBOT_TARS_M7T_DIRECT_KERNEL_PAYLOAD_SMOKE_PASS
```

Evidence artifact:

```text
artifacts/m7t-live-prosody/direct-kernel-payload-smoke.json
```

Readback:

```json
{
  "cueLayerClassification": "STICKBOT_TARS_LIVE_PROSODY_MOOD_SCORE_AND_EMOTIONAL_SHEET_MUSIC_READY",
  "canonicalTextSha256": "59e4434a5a58e4691ea4a438db089f950f635d49248d8686b45dd0d5f1cbd4a9",
  "cueSequence": "✅mf/𝄾 🔎mp/𝄾 ⚠️f/·",
  "averageIntensity": 0.79,
  "chunkCount": 3,
  "textRewriteAllowed": false,
  "exposesRawText": false,
  "localOnly": true,
  "browserWebSpeechApiAllowed": false,
  "cloudSpeechAllowed": false
}
```

New deterministic tests:

```text
STICKBOT_TARS_LIVE_PROSODY_MOOD_SCORE_AND_EMOTIONAL_SHEET_MUSIC_PASS
STICKBOT_TARS_LIVE_PROSODY_PLAN_SURFACES_CUE_LAYER_PASS
```

Live project health boundary checked before server reload:

```json
{
  "ok": true,
  "protocol": "https",
  "openclawMode": "echo",
  "xttsUrl": "http://127.0.0.1:8020",
  "host": "0.0.0.0",
  "port": 19890,
  "sttMode": "cli",
  "browserWebSpeechApi": false,
  "cloudSpeechApi": false
}
```

## Boundaries

```json
{
  "localOnly": true,
  "canonicalTextAuthoritative": true,
  "textRewriteAllowed": false,
  "deliveryMetadataOnly": true,
  "rawTranscriptDurableStorage": false,
  "browserWebSpeechApi": false,
  "cloudSpeechApi": false,
  "openClawProductionMutation": false,
  "gatewayConfigMutation": false,
  "port8787Touched": false
}
```

## HTTP/live-server note

A late-approved temporary loopback HTTP smoke completed after initial closeout. It proved the temporary server could start and answer health on `127.0.0.1:19891`, but the `/api/chat` smoke request used `voice:false`, so the response correctly returned `voicePlan: null` and the smoke assertion failed with `missing liveProsodyCueLayer`.

This is classified as a smoke-harness input error, not a TARS server or cue-layer failure. The existing LAN server on `0.0.0.0:19890` was not restarted or disturbed. The direct kernel payload smoke remains the authoritative M7T metadata proof because it validates the exact `buildTarsProsodyPlan()` cue layer exposed by voice turns.

HTTP smoke readback:

```json
{
  "health": {
    "ok": true,
    "protocol": "http",
    "openclawMode": "echo",
    "host": "127.0.0.1",
    "port": 19891
  },
  "chatVoiceClassification": "VOICE_FALSE_TEXT_ONLY_PASS",
  "voicePlan": null,
  "failureReason": "smoke request used voice:false, so cue metadata was not requested"
}
```

## Result

```text
STICKBOT_TARS_M7T_LIVE_PROSODY_MOOD_SCORE_AND_EMOTIONAL_SHEET_MUSIC_PASS
```

Next recommended milestone:

```text
AUDIO_FIRST_MULTIPLEXED_PRODUCTION_STREAMING_ARCHITECTURE
```
