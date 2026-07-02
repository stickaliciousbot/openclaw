# M5 Local Serverization / Node Voice Integration — PASS

Status: `STICKBOT_TARS_M5_LOCAL_SERVERIZATION_NODE_VOICE_PASS_READY_FOR_M6_PLANNING_ONLY`

Generated: 2026-07-02 19:39 AEST / 2026-07-02T09:39:00Z

## Summary

M5 successfully serverized the local TARS XTTS path and proved Node echo-mode voice integration inside the accepted sandbox boundary.

The smoke started:

1. a minimal local XTTS HTTP server exposing `GET /health`, `GET /ready`, and `POST /tts_to_audio/`;
2. the Node `stickbot-tars-smoke` app in `OPENCLAW_MODE=echo`;
3. a CSRF/session-backed `/api/chat` turn that returned text and a generated WAV URL.

This was local-only validation. It did **not** start a persistent service, expose LAN/Tailscale, mutate Gateway/OpenClaw production config, touch NOA, wire STT, touch Android, or call providers.

## Result

Source evidence:

- `projects/stickbot-tars-smoke/docs/m5-local-serverization/result.json`
- `projects/stickbot-tars-smoke/docs/m5-local-serverization/node-voice-smoke.json`
- `projects/stickbot-tars-smoke/docs/m5-local-serverization/xtts-ready.json`

Result summary:

```json
{
  "classification": "STICKBOT_TARS_M5_LOCAL_SERVERIZATION_NODE_VOICE_PASS",
  "xttsServerReady": true,
  "nodeEchoVoicePass": true,
  "networkBlockedOrUnavailable": true,
  "secretDirsHidden": true,
  "modelReadOnly": true,
  "speakerReadOnly": true,
  "openclawMode": "echo",
  "host": "127.0.0.1",
  "nodePort": 18788,
  "xttsPort": 18020,
  "audioSha256": "1daf103c5e9de8dbeef2a373638b843ff8e01429b415c6ae279853c9908712ec",
  "finishedAt": "2026-07-02T09:37:25Z"
}
```

Node `/api/chat` result:

```json
{
  "nodeStatus": 200,
  "body": {
    "id": "41712ff0-d842-4e12-9228-5fe33536f2a2",
    "text": "Echo smoke response: M5 local voice echo smoke",
    "audioUrl": "/audio/41712ff0-d842-4e12-9228-5fe33536f2a2.wav",
    "audioError": null,
    "logs": {
      "dailyWritten": true,
      "eventWritten": true
    }
  }
}
```

XTTS `/ready` result:

```json
{
  "ok": true,
  "classification": "STICKBOT_TARS_M5_XTTS_SERVER_READY",
  "modelLoaded": true,
  "modelLoadedAt": "2026-07-02T09:36:59Z"
}
```

Generated WAV evidence:

- SHA256: `1daf103c5e9de8dbeef2a373638b843ff8e01429b415c6ae279853c9908712ec`
- Bytes: `142380`
- Type: `RIFF (little-endian) data, WAVE audio, Microsoft PCM, 16 bit, mono 24000 Hz`
- Sandbox path: `/tmp/tars-m5-boundary/app/data/audio/output/41712ff0-d842-4e12-9228-5fe33536f2a2.wav`
- Audio file is excluded from git.

## Boundary evidence

Command/session:

- approval id: `655a4a74-5e73-4c3c-94ab-2b36b3ebda8c`
- session: `vivid-cove`
- exit code: `0`

Boundary checks:

- Private user/mount/network namespace via `unshare -Urnm`.
- Loopback brought up inside private namespace.
- External network probe to `https://huggingface.co` failed DNS resolution, classified as `NETWORK_BLOCKED_OR_UNAVAILABLE`.
- Model mounted read-only from `/home/stickai/stickbot-voice/xtts_models/tars`.
- Speaker directory mounted read-only from `/home/stickai/stickbot-voice/speakers`.
- Secret/runtime dirs hidden with empty bind mounts:
  - `/home/stickai/.openclaw`
  - `/home/stickai/.ssh`
  - `/home/stickai/.codex`
  - `/home/stickai/.config`
- Node app ran from a copied sandbox app directory under `/tmp/tars-m5-boundary/app`.
- Node `WORKSPACE_DIR` pointed at `/tmp/tars-m5-boundary/workspace`, not the real OpenClaw workspace.

## Static validation

Before R2 smoke:

- Command/session `f9412916` / `sharp-crest` passed.
- Existing tests: 19/19 PASS.
- Marker: `STICKBOT_TARS_M5_R2_STATIC_CHECK_PASS`.

Earlier static validation:

- Command/session `0e9bda9a` / `calm-ocean` passed.
- Existing tests: 19/19 PASS.
- Marker: `STICKBOT_TARS_M5_STATIC_CHECK_PASS`.

## R1 failure and repair

R1 command/session `b01b48c0` / `dawn-ember` failed safely:

- XTTS model loaded and server listened.
- `/ready` polling timed out because loopback was down in the private network namespace.
- Cleanup also referenced unset `node_pid` when Node had not started.

Repair:

- Bring `lo` up inside the namespace using `ip link set lo up` or `ifconfig lo up`.
- Initialize `xtts_pid`/`node_pid` and make cleanup tolerate processes that never started.
- R2 static checks and sandbox smoke passed after this repair.

## Boundaries preserved

- No OpenClaw production config mutation.
- No Gateway config/routing/default/fallback mutation.
- No Gateway restart.
- No NOA touch.
- No STT touch.
- No Android touch.
- No persistent XTTS service install/start.
- No LAN/Tailscale exposure yet.
- No bind to `8787`.
- No provider/API calls.
- No browser Web Speech API.
- No model/audio/cache/venv committed.

## Future LAN/Tailscale note

Stick clarified that before user testing, the app should be reachable from phone and laptop browsers via the host PC's Tailscale connection/proxy. That is not part of M5 and remains a later approved milestone.

## Final M5 classification

`STICKBOT_TARS_M5_LOCAL_SERVERIZATION_NODE_VOICE_PASS_READY_FOR_M6_PLANNING_ONLY`

M6/OpenClaw adapter, STT, Android, LAN/Tailscale exposure, and persistent service install are **not started** and require separate approval.
