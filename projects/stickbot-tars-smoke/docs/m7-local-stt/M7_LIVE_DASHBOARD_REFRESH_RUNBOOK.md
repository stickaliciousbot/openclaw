# M7 live dashboard refresh runbook

## Classification

`STICKBOT_TARS_LIVE_DASHBOARD_REFRESH_RUNBOOK`

## Why this exists

During M7G-R2, the local workspace code passed validation but the HTTPS LAN demo still served the old Node process. The live test URL was reachable, voice/STT were available, but the new JSON matrix endpoint returned `not found`.

Durable rule: **PASS_BUILD is not PASS_LIVE.**

## Known live demo shape

- Browser URL for Stick: `https://192.168.1.107:19890/`
- WSL runtime IP observed: `172.24.168.46`
- Windows LAN IP observed: `192.168.1.107`
- Node demo bind: `0.0.0.0:19890`
- XTTS loopback: `127.0.0.1:8020`
- HTTPS cert/key root: `/home/stickai/stickbot-voice/certs/m7d-https`
- Demo workspace: `/tmp/tars-m7d-live-https-demo-workspace`
- Demo logs: `/tmp/tars-m7d-live-https-demo-logs`
- STT: `cli`, normalized with local FFmpeg
- OpenClaw mode for this demo: `echo`

## Do not touch

- Do not restart OpenClaw Gateway.
- Do not touch NOA.
- Do not touch port `8787`.
- Do not mutate model selector/default/fallback config.
- Do not move runtime/model/audio/venv/cache paths under `/mnt/c`.
- Do not store raw mic transcripts durably beyond the existing local demo policy.

## Push-live steps after dashboard/server code changes

1. Run build/test validation:

   ```bash
   npm run check
   ```

2. Check the current live process:

   ```bash
   ss -ltnp | grep -E ':(19890|8020) '
   curl -sk https://127.0.0.1:19890/health
   curl -sk https://127.0.0.1:19890/api/capabilities
   ```

3. Probe the feature-specific endpoint. For M7G-R2:

   ```bash
   curl -sk https://127.0.0.1:19890/api/prosody/matrix
   ```

   Expected: matrix JSON. If the response is `{ "error": "not found" }`, the live Node process is stale.

4. Restart only the demo Node process, preserving XTTS. Use the same HTTPS LAN launch shape:

   ```bash
   HOST=0.0.0.0 \
   PORT=19890 \
   VOICE_DEMO_ALLOW_LAN=true \
   VOICE_DEMO_HTTPS=true \
   VOICE_DEMO_HTTPS_KEY=/home/stickai/stickbot-voice/certs/m7d-https/stickbot-tars-m7d-server.key.pem \
   VOICE_DEMO_HTTPS_CERT=/home/stickai/stickbot-voice/certs/m7d-https/stickbot-tars-m7d-server.cert.pem \
   WORKSPACE_DIR_DEMO=/tmp/tars-m7d-live-https-demo-workspace \
   LOG_DIR=/tmp/tars-m7d-live-https-demo-logs \
   XTTS_URL=http://127.0.0.1:8020 \
   npm run m7d:demo:https
   ```

5. Re-probe before telling Stick it is ready:

   ```bash
   curl -sk https://127.0.0.1:19890/health
   curl -sk https://127.0.0.1:19890/api/capabilities
   curl -sk https://127.0.0.1:19890/api/prosody/matrix
   ```

6. Browser/UI verification:

   - Page loads on `https://192.168.1.107:19890/`.
   - Voice availability says local XTTS backend ready.
   - JSON matrix controls are visible:
     - Read active JSON
     - Upload JSON
     - Reset default JSON
   - Mood dropdown is populated from the active matrix.
   - A chat response includes voice-plan/prosody-sheet metadata.

## M7G-R2 live state after approved refresh

- Classification: `STICKBOT_TARS_M7G_R2_LIVE_DASHBOARD_AVAILABLE_PASS`.
- Build validation: PASS (`56/56` tests).
- `state/status.json`: parse PASS.
- Live voice/STT demo: available.
- New JSON/mood/sheet-music dashboard: available at `https://192.168.1.107:19890/`.
- Live `/health`: PASS.
- Live `/api/capabilities`: PASS, `voice.enabled:true`, `sttMode:cli`, `prosodyTuning.enabled:true`.
- Live `/api/prosody/matrix`: PASS, returns built-in default JSON instead of `not found`.
- Served HTML contains JSON matrix controls: Read active JSON, Upload JSON, Reset default JSON, and mood selector.
- Served JS contains `/api/prosody/matrix`, `/api/prosody/matrix/reset`, and `prosodySheet` rendering.
- XTTS remained preserved on `127.0.0.1:8020`.
- A duplicate launch attempt logged `EADDRINUSE` because the refreshed process was already bound to `19890`; this was not a live failure.
