# Stickbot-TARS generated audio audit

Generated: 2026-07-03T10:33:15.435Z
Schema: `stickbot.tars.generated-audio-audit.v1`
Classification: `STICKBOT_TARS_GENERATED_AUDIO_AUDIT_STAGE_PASS`
Manifest SHA256: `73a98f67341c07202db170903b140074c8e9139c321a6658bb76b4cf4b75a84f`

## Summary

- files scanned: 1
- staged for deletion: 0
- protected/skipped: 1
- total bytes: 95788
- staged bytes: 0
- blocked bytes: 95788
- min age minutes: 0

## Guardrails

- Stage/audit mode never deletes files.
- Delete mode requires `--delete --manifest <PASS manifest> --confirm-delete`.
- Candidates must be under allowlisted generated-audio roots.
- Git-tracked files, protected roots, executable source/script references, and open files are blocked.
- Runtime speaker reference, models, tools, certs, source, tests, and app dependencies are never scan roots.

## Scan roots

- `data/audio/input`
- `data/audio/normalized`
- `data/audio/output`
- `exports`
- `/home/stickai/stickbot-voice/output`

## Staged files

_None._

## Protected/skipped files

- `/home/stickai/stickbot-voice/output/m4-first-generation.wav` — REFERENCED_BY_EXECUTABLE_SOURCE
