# M7D Real Mic Localhost Demo PASS

Classification: `STICKBOT_TARS_M7D_HTTPS_LAN_REAL_MIC_STT_ECHO_PASS_OPTIONAL_XTTS_OUTPUT_BLOCKED`

Date: 2026-07-02 23:27 AEST / 2026-07-02T13:27:00Z

## Summary

M7D passed first for the local Windows-host/WSL localhost path, then was upgraded to pass over the HTTPS LAN URL:

- Browser microphone capture worked from `http://localhost:19890/`.
- Capture used browser `MediaRecorder`, not browser Web Speech API.
- Audio posted to local `/api/stt`.
- Server used local FFmpeg normalization + local whisper.cpp `ggml-small.en.bin`.
- Transcript was inserted into the text box.
- `Send text` echo path worked after transcript insertion.
- TARS voice generation was capability-gated off because the local XTTS backend was not running.

No raw transcript is preserved in this closeout. Operator screenshot confirmed transcript/echo behavior; durable evidence records only semantic confirmation.

## Live server evidence

Validation and live restart:

- Approval/run: `95dcb06e-3a9c-4832-9746-2cef8bbd95fd` / `rapid-nudibranch`
- `npm run check`: PASS
- Tests: `40/40` pass
- Live Node PID after restart: `571853`
- Listener: `0.0.0.0:19890`
- `/health`: PASS with `ok:true`, `openclawMode:"echo"`, `host:"0.0.0.0"`, `port:19890`
- `/api/capabilities`: PASS with `voice.enabled:false`, `reason:"xtts_not_ready"`, `detail:"fetch failed"`
- Boundaries: `browserWebSpeechApi:false`, `cloudSpeechApi:false`

Earlier LAN readiness validation:

- `STICKBOT_TARS_M7D_LAN_READINESS_VALIDATION_PASS`
- `HEALTH_OK host=0.0.0.0 port=19890`
- `SESSION_CSRF_OK`
- `LAN_ORIGIN_MUTATING_POST_OK`
- `LAN_ALLOW=true`

## Operator confirmation

Stick confirmed:

- localhost voice capture works;
- visual indicators are good;
- echo worked;
- LAN page reached after Windows portproxy/firewall, but LAN microphone permission was blocked/not prompted;
- Stick did not block the LAN mic permission.

## HTTPS LAN confirmation

Stick confirmed `https://192.168.1.107:19890/` voice capture/STT works over LAN:

- browser microphone capture worked;
- transcript appeared in the page;
- `Send text` echo path worked;
- durable evidence does not preserve raw transcript text.

Screenshot showed Chrome still displaying `Not secure`, but the browser microphone capture path was operational after the HTTPS/cert/permission flow. Treat the LAN mic path as operator-confirmed for this local demo, while preserving the certificate/trust caveat for future devices.

## Known blockers carried forward

### Optional XTTS voice-output blocker

M7D is an STT/real-mic milestone. TARS voice output is separate.

The live M7D server ran in `OPENCLAW_MODE=echo` and did not start local XTTS at `127.0.0.1:8020`; therefore voice output was disabled by `/api/capabilities`.

Before a final demo that includes TARS voice output:

- start local XTTS backend;
- verify XTTS `/ready`;
- keep UI voice checkbox disabled until `/api/capabilities` reports ready;
- avoid showing `voice fetch failed` as a user-facing false failure.

### UX polish blocker

Basic UX repair is complete:

- mic button now indicates recording;
- mic button indicates processing during STT;
- voice checkbox is disabled while XTTS is unavailable;
- LAN/insecure-origin microphone errors are clearer.

Before final/user testing, add:

- timer or pulse recording indicator;
- clearer separate start/stop affordance;
- secure-origin guidance for LAN/phone.

## Boundary readback

Preserved:

- no browser Web Speech API;
- no cloud STT;
- no OpenClaw/Gateway/NOA production mutation;
- no Gateway restart;
- no model/audio/raw transcript committed;
- port `8787` untouched;
- local STT used whisper.cpp small.en model;
- raw transcript not preserved in durable docs/memory.

## Artifacts

- `scripts/m7d-local-real-mic-demo.sh`
- `public/index.html`
- `public/app.js`
- `server.js`
- `docs/m7-local-stt/m7d-real-mic-local-demo/M7D_REAL_MIC_LOCAL_DEMO_PLAN.md`
- `docs/m7-local-stt/m7d-real-mic-local-demo/M7D_REAL_MIC_LOCALHOST_DEMO_PASS.md`
- `docs/LOOPBACK_LAN_EXPOSURE_NOTEBOOK.md`

## Next state

M7D local real-mic localhost path is complete.

Next work requires separate approval:

- secure-origin LAN/phone mic milestone;
- optional XTTS voice-output milestone;
- M8 / live provider / Gateway / Android / persistent service / broader user-testing exposure.
