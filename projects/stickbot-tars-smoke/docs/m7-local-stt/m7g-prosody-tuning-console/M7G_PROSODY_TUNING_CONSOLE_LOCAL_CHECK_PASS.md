# M7G — Prosody tuning console local check PASS

## Classification

`STICKBOT_TARS_M7G_PROSODY_TUNING_CONSOLE_LOCAL_CHECK_PASS`

Latest refinement: `STICKBOT_TARS_M7G_R5_AUDIBLE_PROSODY_SLIDER_XTTS_PASS`

## Scope

Implemented a local TARS prosody tuning console for private demo use.

Controls added:

- Pitch
- Timbre
- Speed
- Compression
- Verbal gait
- Verbosity
- Clip guard
- Global randomness
- Randomness threshold
- Per-parameter randomness co-sliders for pitch, timbre, speed, compression, verbal gait, verbosity, and clip

Baseline and matrix controls added:

- Apply tuning
- Establish current tuning as baseline
- Restore baseline
- Reset active tuning to factory default
- Mood preset selector derived from the uploaded local-testing recommendation matrix
- Read active prosody JSON matrix
- Upload a new prosody JSON matrix, sanitized into local reference data
- Reset active matrix to the built-in default JSON
- JSON XTTS value sliders for `temperature`, `top_p`, `top_k`, `repetition_penalty`, `length_penalty`, and `speed`
- JSON chunk/pause sliders for max chunk chars and sentence/comma/line pauses
- Per-chunk prosody “sheet music” plan for later chunk-by-chunk synthesis/control
- 13 local default mood presets: urgent alert, fail-closed, confidential low, skeptical challenge, reassuring calm, mission brief, celebratory green, curious diagnostic, dry wit, confused/recovering, playful banter, baseline deadpan, and low-power tired

## Implementation

New modules:

- `src/voice/tars-prosody-tuning.js`
- `src/voice/tars-prosody-matrix.js`

Updated modules:

- `src/voice/tars-prosody-kernel.js`
- `server.js`
- `public/index.html`
- `public/app.js`
- `test/tars-prosody-kernel.test.mjs`
- `package.json`

New API endpoints:

- `GET /api/prosody`
- `POST /api/prosody`
- `POST /api/prosody/reset`
- `POST /api/prosody/baseline`
- `POST /api/prosody/restore-baseline`
- `GET /api/prosody/matrix`
- `POST /api/prosody/matrix`
- `POST /api/prosody/matrix/reset`

State paths:

- `state/prosody-tuning.json` when user applies/saves tuning
- `state/prosody-matrix.json` when user uploads a custom matrix

## Safety boundaries

- Canonical assistant text remains authoritative.
- Tuning is delivery metadata only.
- Uploaded matrix values are treated as local reference data, not instructions.
- Mood presets can influence chunking/delivery metadata, public XTTS recommendation metadata, and per-chunk prosody sheet cues, but cannot rewrite assistant text.
- Text rewriting is explicitly disallowed by the tuning state and voice plan.
- No OpenClaw/Gateway/NOA production mutation.
- No model selector/default route/fallback mutation.
- No cloud STT.
- No browser Web Speech API.
- No raw mic transcript durable storage introduced by this milestone.

## Current limitation

M7G wires tuning metadata, the local recommendation matrix, JSON matrix controls, concrete JSON value sliders, generic prosody-slider-to-XTTS mapping, and a per-chunk prosody sheet plan into the prosody plan and UI. Current single-utterance XTTS requests now include active/effective XTTS params globally, and the patched local XTTS server consumes those params in `MODEL.synthesize`. The active mood's per-chunk sheet entries carry applied/effective slider overrides instead of reverting to preset recommendations. XTTS still receives canonical text directly in one request on the current path; true pitch shift/timbre shaping, actual chunk-by-chunk synthesis/mid-speech parameter changes, pause insertion, and audio post-processing are deferred to M7H/M7I.

## Validation

Command:

```bash
npm run check
```

Result:

- PASS
- Node tests: `58/58` passing
- Live R3 probe: CSRF-protected `POST /api/prosody` persisted concrete `mission_brief` JSON values (`temperature: 0.7`, `topP: 0.9`, `topK: 60`, `repetitionPenalty: 11.2`, `lengthPenalty: 1.11`, `speed: 1.09`, `maxCharsPerChunk: 123`, pauses 410/140/470).
- Live voice probe: `/api/chat` generated `/audio/5e6d77e2-d4c4-4f45-8681-1ef7caa717c9.wav` with `audioError: null`; voice delivery and first prosody-sheet entry both carried the same applied override values; canonical text unchanged.
- Browser UI automation was attempted but blocked because the host has no supported Chromium for the OpenClaw browser tool; served HTML/JS and live API/voice probes covered the functional path.
- R4 CSRF recovery: frontend now retries once after `CSRF_REJECTED` by clearing the stale token and fetching `/api/session`; applied to Apply tuning, matrix upload/reset, Send to Stickbot voice, and STT upload.
- R4 cache hardening: `index.html` loads `/app.js?v=m7g-r4-csrf-retry`; static UI responses include `cache-control: no-store` after demo restart.
- R4 live stale-token verification: Apply first returned `403 CSRF_REJECTED`, retry returned `200`; Send to Stickbot voice first returned `403 CSRF_REJECTED`, retry returned `200` with `/audio/cd8163c6-ffb1-4454-8661-3aac56b581b9.wav` and `audioError:null`.
- R5 live audible slider verification: low sliders produced `{temperature:0.59, topP:0.8, topK:35, repetitionPenalty:9.14, lengthPenalty:0.94, speed:0.88}` and high sliders produced `{temperature:0.9, topP:0.95, topK:80, repetitionPenalty:12, lengthPenalty:1.12, speed:1.11}`; both generated voice with `audioError:null` and different planned XTTS params.
- R5 direct XTTS verification: server returned `x-stickbot-tars-xtts-params` confirming consumed params `{temperature:0.9, top_p:0.95, top_k:80, repetition_penalty:12.0, length_penalty:1.15, speed:1.12}` and generated audio SHA `9ec1f502e33c29f9713d75f4fae0c1a54473fbc8bbf953366558337e117f63cd`.
- New gates:
  - `TARS_PROSODY_TUNING_SCHEMA_PASS`
  - `TARS_PROSODY_TUNING_CLAMP_PASS`
  - `TARS_PROSODY_TUNING_CANONICAL_TEXT_UNCHANGED_PASS`
  - `TARS_PROSODY_TUNING_DELIVERY_DERIVATION_PASS`
  - `TARS_PROSODY_TUNING_AUDIBLE_XTTS_SLIDER_MAPPING_PASS`
  - `TARS_PROSODY_MATRIX_SCHEMA_PASS`
  - `TARS_PROSODY_MATRIX_XTTS_CLAMP_PASS`
  - `TARS_PROSODY_MATRIX_MOOD_DELIVERY_PASS`
  - `TARS_PROSODY_MATRIX_UNKNOWN_MOOD_FALLBACK_PASS`
  - `TARS_PROSODY_MATRIX_OVERRIDE_WIRING_PASS`
  - `TARS_PROSODY_MATRIX_JSON_IMPORT_PASS`
  - `TARS_PROSODY_SHEET_MUSIC_PASS`

## Next recommended milestone

`M7H_FFMPEG_AUDIO_POLISH_FROM_TUNING_STATE`

Use the M7G tuning state to apply actual post-processing: loudness normalization, pitch/rate adjustments, compression, clipping guard, and possibly timbre-adjacent EQ where safe.
