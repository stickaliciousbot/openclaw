# M7E HTTPS LAN TARS Voice Output PASS

Classification: `STICKBOT_TARS_M7E_HTTPS_LAN_TARS_VOICE_OUTPUT_PASS`

Date: 2026-07-02 23:46 AEST / 2026-07-02T13:46:00Z

## Summary

M7E passed: the HTTPS LAN Stickbot-TARS demo can now generate TARS voice output when the local XTTS backend is running and ready.

This extends the M7D HTTPS LAN real-mic STT + echo pass with optional TARS voice output.

## Validation run

Approval/run:

- `15cc2145-71e1-4036-ad32-39b1866ebed1` / `sharp-mist`

Terminal marker:

- `STICKBOT_TARS_M7E_HTTPS_LAN_TARS_VOICE_OUTPUT_SMOKE_PASS`

Validation gates:

- `npm run check`: PASS
- XTTS loopback backend started inside mount-isolated boundary.
- XTTS `/ready`: PASS
- Frontend `/api/capabilities`: PASS, `voice.enabled:true`, `reason:"xtts_ready"`
- HTTPS LAN-shaped browser session/CSRF: PASS
- HTTPS LAN-shaped `/api/chat` with `voice:true`: PASS
- Generated WAV fetched successfully: PASS

## Runtime shape

Frontend:

- URL: `https://192.168.1.107:19890/`
- Bind: `0.0.0.0:19890`
- Protocol: HTTPS
- OpenClaw mode: `echo`
- STT mode: `cli`

XTTS backend:

- URL: `http://127.0.0.1:8020`
- Bind: loopback-only
- Model loaded: true
- Model loaded at: `2026-07-02T13:46:25Z`

Boundary:

- XTTS model/speaker bind-mounted read-only.
- Secret dirs hidden in XTTS boundary: `.openclaw`, `.ssh`, `.codex`, `.config`.
- No Gateway/OpenClaw production/NOA mutation.
- Port `8787` untouched.

## Evidence

Frontend capabilities:

```json
{
  "ok": true,
  "openclawMode": "echo",
  "sttMode": "cli",
  "voice": {
    "enabled": true,
    "xttsUrl": "http://127.0.0.1:8020",
    "reason": "xtts_ready",
    "detail": 200
  },
  "boundaries": {
    "browserWebSpeechApi": false,
    "cloudSpeechApi": false
  }
}
```

Chat voice result:

```json
{
  "id": "5a18bf48-d136-4cac-9656-fe03ebac82e3",
  "text": "Echo smoke response: M7E local TARS voice output smoke",
  "audioUrl": "/audio/5a18bf48-d136-4cac-9656-fe03ebac82e3.wav",
  "audioError": null
}
```

Generated WAV:

- SHA256: `2e8556b9bac193ce5efde9bbc5ba2553d52c7428473aee18dcb1c8eb568218f0`
- Bytes: `73260`
- Type: `RIFF WAVE audio, Microsoft PCM, 16 bit, mono 24000 Hz`
- Runtime proof copy: `/tmp/tars-m7e-xtts-loopback-logs/generated.wav`
- Commit policy: generated WAV excluded from git.

## Boundaries preserved

- no cloud STT;
- no browser Web Speech API;
- no provider call;
- no live OpenClaw/Gateway route mutation;
- no Gateway restart;
- no NOA touch;
- no raw mic transcript preserved;
- no model/audio/cache/venv artifacts committed;
- XTTS backend loopback-only behind HTTPS Node frontend.

## Operator instruction

Refresh `https://192.168.1.107:19890/`. The `generate TARS voice` checkbox should now be enabled because `/api/capabilities` reports `xtts_ready`.

## Next state

M7E is complete.

Future work requires separate approval:

- polished final UX (timer/pulse indicator);
- live OpenClaw provider/Gateway smoke;
- Android/phone packaging;
- persistent service install;
- broader user-testing exposure.
