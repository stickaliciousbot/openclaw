# M7F Prosody Kernel Implementation Plan

Classification target: `STICKBOT_TARS_M7F_PROSODY_KERNEL_PASS`

## Scope

Build a local TARS-inspired prosody kernel on top of the existing M7E voice output path.

Hard boundary from Stick: **capture voice likeness only, not alter what Stickbot says.**

Therefore the M7F kernel is non-authoritative delivery metadata only:

- canonical assistant text remains byte-for-byte authoritative;
- sentence chunking must reconstruct exactly to canonical text;
- salience tags identify delivery emphasis spans without rewriting words;
- secret-like text must not be synthesized;
- TTS receives the canonical text unless a later milestone explicitly approves chunk streaming/playback queue changes.

## Reference findings

From `https://docs-tars-ai.vercel.app/releases` and public GitHub refs:

- TARS-AI v3 added TTS/STT refactor, Silero VAD, and sentence-level TTS chunk streaming.
- TARS-AI v3 config defaults STT processor to `faster-whisper`, TTS option to `piper`, and VAD method to `rms` with `silero` as another option.
- TARS-AI v3 includes a Piper TARS voice artifact `src/tts/TARS.onnx` and config `src/tts/TARS.onnx.json`.
- Piper voice config reports sample rate `22050` and inference defaults:
  - `noise_scale: 0.667`
  - `length_scale: 1`
  - `noise_w: 0.8`

These are reference signals only; no external code or binary is imported in M7F.

## Implemented modules

- `src/voice/tars-prosody-profile.js`
- `src/voice/tars-salience-annotator.js`
- `src/voice/tars-sentence-chunker.js`
- `src/voice/tars-prosody-kernel.js`

## Initial gates

- `TARS_PROSODY_PROFILE_LOAD_PASS`
- `TARS_SENTENCE_CHUNKING_PASS`
- `TARS_STATUS_SALIENCE_PASS`
- `TARS_NO_SECRET_SPEECH_PASS`
- `TARS_CANONICAL_TEXT_UNCHANGED_PASS`

## Integration

`server.js` now builds a prosody plan before XTTS synthesis. The plan:

- hashes canonical assistant text;
- verifies chunk reconstruction equals canonical text;
- annotates status/risk/number/operator/mission-state salience;
- blocks synthesis for secret-like text;
- returns a public summary in `/api/chat` as `voicePlan` when voice synthesis succeeds.

No text rewriting is performed.

## Out of scope

- no Gateway/OpenClaw/NOA mutation;
- no production route/default/fallback change;
- no persistent service install;
- no Piper model acquisition/load;
- no Faster-Whisper benchmark;
- no raw transcript durable storage;
- no exact clone or personality change.
