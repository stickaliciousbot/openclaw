# Stickbot-TARS M3 Model Acquisition / Hash / Provenance Closeout

Generated: 2026-07-02T17:41:54+10:00

## Classification

`STICKBOT_TARS_M3_MODEL_ACQUIRED_HASHED_PROVENANCE_RECORDED_NO_LOAD_PASS`

## Scope

M3 downloaded and hashed the pinned TARS model artifacts only. No model load, no XTTS server start, no STT, no Android, no Gateway/OpenClaw/NOA production mutation.

## Source

- Model: `Pyrater/TARS`
- Source: https://huggingface.co/Pyrater/TARS
- Revision: `7a1517d76eb0db89828b1c812682fa75125e5de7`
- Declared license: MIT
- Voice/branding status: private demo only until separate rights/branding review.

## WSL-native paths

- Runtime root: `/home/stickai/stickbot-voice`
- Model root: `/home/stickai/stickbot-voice/xtts_models/tars`
- Speaker root: `/home/stickai/stickbot-voice/speakers`
- Output root: `/home/stickai/stickbot-voice/output`

None of these paths are under `/mnt/c`.

## Files acquired

- `config.json`
- `vocab.json`
- `model.pth`
- `speakers_xtts.pth`
- `reference.wav`
- Runtime copy: `speakers/reference.wav`

## Evidence

- Manifest: `projects/stickbot-tars-smoke/docs/m3-model-provenance/tars-model-provenance-manifest.json`
- SHA256 list: `projects/stickbot-tars-smoke/docs/m3-model-provenance/sha256sum.txt`

## Stop condition

M4 is not started. The downloaded `.pth` file remains untrusted until loaded only inside the constrained M4 runtime boundary.
