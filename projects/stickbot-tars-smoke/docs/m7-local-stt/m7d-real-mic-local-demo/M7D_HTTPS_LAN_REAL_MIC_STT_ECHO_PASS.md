# M7D HTTPS LAN Real Mic STT + Echo PASS

Classification: `STICKBOT_TARS_M7D_HTTPS_LAN_REAL_MIC_STT_ECHO_PASS_OPTIONAL_XTTS_OUTPUT_BLOCKED`

Date: 2026-07-02 23:35 AEST / 2026-07-02T13:35:00Z

## Result

Stick confirmed the HTTPS LAN browser path works:

- URL: `https://192.168.1.107:19890/`
- real browser microphone capture worked over LAN;
- local FFmpeg + whisper.cpp STT produced a transcript in the page;
- `Send text` echo path worked;
- no browser Web Speech API;
- no cloud STT;
- no OpenClaw/Gateway/NOA mutation;
- raw transcript not preserved in durable docs/memory.

This upgrades the prior localhost-only M7D pass to HTTPS LAN pass for real-mic STT + echo.

## Remaining blocker

TARS voice output remains intentionally disabled because the local XTTS backend is not running:

- `/api/capabilities`: `voice.enabled:false`
- reason: `xtts_not_ready`

A future voice-output milestone should start/health-check local XTTS and only enable the UI checkbox when XTTS `/ready` is green.

## Related artifacts

- `M7D_REAL_MIC_LOCALHOST_DEMO_PASS.md` — original localhost pass, updated with HTTPS LAN confirmation.
- `docs/LOOPBACK_LAN_EXPOSURE_NOTEBOOK.md` — loopback/LAN/HTTPS procedure.
- `scripts/m7d-generate-local-https-cert.sh` — local CA + IP-SAN certificate helper.
