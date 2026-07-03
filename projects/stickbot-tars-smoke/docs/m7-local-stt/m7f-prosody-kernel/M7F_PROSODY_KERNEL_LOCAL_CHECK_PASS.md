# M7F Prosody Kernel Local Check PASS

Classification: `STICKBOT_TARS_M7F_PROSODY_KERNEL_LOCAL_CHECK_PASS`

Date: 2026-07-03 00:08 AEST / 2026-07-02T14:08:00Z

## Summary

M7F local validation passed. The initial TARS-inspired prosody kernel is implemented as a non-authoritative delivery metadata layer over the existing M7E voice path.

Hard boundary from Stick is preserved:

> Voice likeness only; do not alter what Stickbot says.

The canonical assistant text remains authoritative. The M7F layer can produce chunk/pause/salience metadata and a public voice plan summary, but it does not rewrite the text passed to XTTS.

## Validation

Approved command:

- Gateway id: `7ca280ac-99a1-4363-8a82-baedadfea7c1`
- Session: `wild-kelp`

Command:

```sh
npm run check && python3 -m json.tool state/status.json >/tmp/stickbot-tars-m7f-status-json-check.out && echo STICKBOT_TARS_M7F_PROSODY_KERNEL_LOCAL_CHECK_PASS
```

Result:

- exit code: `0`
- Node test suite: `46/46` passed
- status JSON parse: PASS
- terminal marker: `STICKBOT_TARS_M7F_PROSODY_KERNEL_LOCAL_CHECK_PASS`

New gates covered by tests:

- `TARS_PROSODY_PROFILE_LOAD_PASS`
- `TARS_SENTENCE_CHUNKING_PASS`
- `TARS_STATUS_SALIENCE_PASS`
- `TARS_NO_SECRET_SPEECH_PASS`
- `TARS_CANONICAL_TEXT_UNCHANGED_PASS`

## Implemented files

- `src/voice/tars-prosody-profile.js`
- `src/voice/tars-salience-annotator.js`
- `src/voice/tars-sentence-chunker.js`
- `src/voice/tars-prosody-kernel.js`
- `test/tars-prosody-kernel.test.mjs`
- `docs/m7-local-stt/m7f-prosody-kernel/M7F_PROSODY_KERNEL_IMPLEMENTATION_PLAN.md`

## Runtime integration

`server.js` now builds a prosody plan before XTTS synthesis. It:

- hashes canonical assistant text;
- verifies chunk reconstruction exactly matches canonical text;
- annotates status/risk/number/operator/mission-state salience spans;
- blocks synthesis for secret-like text;
- returns public `voicePlan` summary in `/api/chat` when voice synthesis succeeds.

The current XTTS request still sends the canonical assistant text unchanged.

## Reference findings

From TARS-AI docs/source inspection:

- v3 release notes mention TTS/STT refactor, Silero VAD, and sentence-level TTS chunk streaming.
- v3 config points to `faster-whisper` for STT and `piper` for TTS.
- Piper TARS ONNX config reports sample rate `22050` and inference defaults:
  - `noise_scale: 0.667`
  - `length_scale: 1`
  - `noise_w: 0.8`

No external code or binary was imported for M7F.

## Boundaries preserved

- no canonical text rewrite;
- no cloud STT;
- no browser Web Speech API;
- no provider API call;
- no OpenClaw/Gateway production mutation;
- no Gateway restart;
- no NOA touch;
- no `8787`;
- no model/audio/cache/venv artifact committed by this milestone;
- no raw sensitive transcript storage.

## Next options

Future work requires separate approval:

- make XTTS actually synthesize sentence chunks and queue playback;
- add FFmpeg post-processing for rate/pitch/loudness/EQ;
- benchmark Faster-Whisper;
- evaluate Piper TARS ONNX as a low-latency local voice lane;
- run live OpenClaw/Gateway/provider path;
- Android/phone packaging or persistent service install.
