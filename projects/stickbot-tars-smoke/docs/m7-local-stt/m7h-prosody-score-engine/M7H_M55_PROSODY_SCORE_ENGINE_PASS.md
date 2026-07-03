# M7H / M55 Prosody Score Engine — PASS

Date: 2026-07-03
Classification: `STICKBOT_TARS_M55_PROSODY_SCORE_ENGINE_PASS`
Parent milestone: M7H, local prosody/voice polish path

## Summary

Implemented a local Stickbot-TARS Prosody Score Engine that treats speech as a score instead of a flat preset.

Architecture:

```text
canonical assistant text
  -> mood profile loader
  -> sentence analyzer
  -> phrase role classifier
  -> chunk planner
  -> XTTS param resolver
  -> pause score resolver
  -> per-chunk prosody score
  -> utterance-level effective XTTS envelope for current single-request XTTS path
```

This is a direct extension of the existing M7G prosody sheet/music path. It does not rewrite canonical assistant text and does not mutate OpenClaw/Gateway/NOA/provider/runtime configuration.

## Implemented modules

```text
src/prosody/mood-profile-loader.js
src/prosody/sentence-analyzer.js
src/prosody/phrase-role-classifier.js
src/prosody/chunk-planner.js
src/prosody/xtts-param-resolver.js
src/prosody/pause-score-resolver.js
src/prosody/prosody-score-engine.js
src/prosody/prosody-trace-writer.js
```

## Behavior

The engine now separates:

- preset base XTTS values,
- active base XTTS values,
- phrase-role deltas,
- sentence-feature deltas,
- user tuning deltas,
- identity-safe clamp events,
- final effective XTTS values per chunk,
- effective pause/rest values per chunk.

Current XTTS runtime remains a single request path for safety, so M7H computes an utterance-level effective XTTS envelope from the per-chunk score and sends that to XTTS. Full chunk-by-chunk synthesis/stitching remains M7I.

## UI/API exposure

The chat response `voicePlan` now exposes:

- `delivery.baseXttsParams`,
- `delivery.presetBaseXttsParams`,
- `delivery.xttsParams` as the utterance-level effective XTTS params,
- `prosodyScore.chunks[*].baseXtts`,
- `prosodyScore.chunks[*].deltas`,
- `prosodyScore.chunks[*].effectiveXtts`,
- `prosodyScore.chunks[*].effectivePauses`.

The UI now displays base/effective/delta information for the selected first chunk in addition to the current voice summary.

Durable/public traces use text hashes rather than raw chunk text.

## Pass gates

Validated by `npm run check`:

```text
66/66 tests passed
```

New gates include:

```text
STICKBOT_TARS_M55_MOOD_BASE_XTTS_VALUES_CHANGE_PASS
STICKBOT_TARS_M55_BLOCKER_PHRASE_SCORE_APPLIED_PASS
STICKBOT_TARS_M55_DRY_ASIDE_PAUSE_AND_EXPRESSIVENESS_PASS
STICKBOT_TARS_M55_URGENT_STOP_CLIPPED_TIMING_PASS
STICKBOT_TARS_M55_VALUES_CLAMP_WITHIN_IDENTITY_SAFE_BOUNDS_PASS
STICKBOT_TARS_M55_UI_DATA_MODEL_BASE_EFFECTIVE_DELTA_SEPARATED_PASS
STICKBOT_TARS_M55_TARS_AND_CASE_SAME_TEXT_RESOLVE_DIFFERENTLY_PASS
```

Regression gates preserved:

- canonical text unchanged,
- no secret-like speech synthesis,
- mood delivery still applies chunking,
- uploaded JSON matrix remains local reference data only,
- TARS/CASE v2 import preserved,
- local-only/no cloud speech/no browser Web Speech API boundaries preserved.

## Boundaries

No changes to:

- OpenClaw routing/defaults/fallbacks,
- Gateway config/service state,
- NOA,
- STT,
- Android,
- provider settings,
- model files,
- XTTS runtime isolation,
- LAN exposure.

## Remaining M7H/M7I work

M7H still has a later audio-DSP polish lane available: FFmpeg/local pitch/rate/loudness/compression/clip guard on generated WAVs.

M7I remains the chunk conductor milestone:

```text
per-chunk XTTS synthesis
  -> rests/pause insertion
  -> local WAV stitching
  -> per-chunk artifact hashes
  -> playback/trace/rating loop
```
