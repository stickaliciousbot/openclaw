# M6 OpenClaw Adapter Fixture Voice Smoke — PASS

Status: `STICKBOT_TARS_M6_OPENCLAW_ADAPTER_FIXTURE_VOICE_PASS_READY_FOR_M7_PLANNING_ONLY`

Generated: 2026-07-02 20:03 AEST / 2026-07-02T10:03:00Z

## Summary

M6 successfully wired the Node app through a safe OpenClaw adapter surface and proved Node → OpenClaw adapter → local XTTS voice generation inside the accepted sandbox boundary.

The M6 smoke used a fixture OpenClaw CLI inside the sandbox. This intentionally avoided live provider calls, production Gateway calls, and real session/tool/memory context while the TARS `.pth` model was loaded.

## Result

Source evidence:

- `projects/stickbot-tars-smoke/docs/m6-openclaw-adapter/result.json`
- `projects/stickbot-tars-smoke/docs/m6-openclaw-adapter/node-openclaw-voice-smoke.json`
- `projects/stickbot-tars-smoke/docs/m6-openclaw-adapter/xtts-ready.json`

Result summary:

```json
{
  "classification": "STICKBOT_TARS_M6_OPENCLAW_ADAPTER_FIXTURE_VOICE_PASS",
  "adapterMode": "infer",
  "adapterSurface": "openclaw infer model run --prompt {prompt} --json",
  "liveProviderCalled": false,
  "gatewayCalled": false,
  "fixtureOpenClawCli": true,
  "xttsServerReady": true,
  "nodeOpenClawVoicePass": true,
  "networkBlockedOrUnavailable": true,
  "secretDirsHidden": true,
  "modelReadOnly": true,
  "speakerReadOnly": true,
  "host": "127.0.0.1",
  "nodePort": 18788,
  "xttsPort": 18020,
  "audioSha256": "fc7da588940bbe2238dcc91b9dc5156d36cbcaafcc49bbf606ebbdc3427ce5d0",
  "finishedAt": "2026-07-02T10:01:25Z"
}
```

Node `/api/chat` result:

```json
{
  "nodeStatus": 200,
  "body": {
    "id": "f640fa4b-115d-4063-9ea8-511d998d1592",
    "text": "OpenClaw adapter fixture response: M6 OpenClaw adapter fixture voice smoke",
    "audioUrl": "/audio/f640fa4b-115d-4063-9ea8-511d998d1592.wav",
    "audioError": null,
    "logs": {
      "dailyWritten": true,
      "eventWritten": true
    }
  }
}
```

Generated WAV evidence:

- SHA256: `fc7da588940bbe2238dcc91b9dc5156d36cbcaafcc49bbf606ebbdc3427ce5d0`
- Bytes: `111148`
- Type: `RIFF (little-endian) data, WAVE audio, Microsoft PCM, 16 bit, mono 24000 Hz`
- Sandbox path: `/tmp/tars-m6-boundary/app/data/audio/output/f640fa4b-115d-4063-9ea8-511d998d1592.wav`
- Audio file is excluded from git.

## Static validation

- Command/session: `718a054e` / `glow-ocean`
- Tests: 27/27 PASS
- Marker: `STICKBOT_TARS_M6_STATIC_CHECK_PASS`

## Adapter implementation

Implemented files:

- `src/openclaw-adapter.js`
- `test/openclaw-adapter.test.mjs`
- `scripts/m6-sandboxed-openclaw-adapter-smoke.sh`

Adapter safety gates:

- `spawn(file,args,{shell:false})`; no shell interpolation.
- `{prompt}` placeholder required in configured args.
- bounded args count.
- bounded stdout/stderr.
- timeout with process kill.
- whitelisted environment only.
- non-zero exit fails closed.
- JSON output must contain extractable text for `infer`/`agent` modes.
- shell-metacharacter prompt test verifies prompt is passed as argv, not executed.

Supported modes:

- `echo` — local echo mode.
- `infer` — default M6 adapter surface: `openclaw infer model run --prompt {prompt} --json`.
- `agent` — explicit future mode: `openclaw agent --message {prompt} --json`.
- `cli` — legacy explicit stdout CLI mode.

## Boundary evidence

Command/session:

- approval id: `9932f947-07b8-4d46-b5ef-46dddbf90485`
- session: `fresh-daisy`
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
- Node app ran from copied sandbox app directory under `/tmp/tars-m6-boundary/app`.
- Node `WORKSPACE_DIR` pointed at `/tmp/tars-m6-boundary/workspace`, not the real OpenClaw workspace.

## Boundaries preserved

- No live provider call.
- No production Gateway call.
- No Gateway config/routing/default/fallback mutation.
- No Gateway restart.
- No NOA touch.
- No STT touch.
- No Android touch.
- No persistent service install.
- No LAN/Tailscale exposure.
- No bind to `8787`.
- No browser Web Speech API.
- No model/audio/cache/venv committed.

## Final M6 classification

`STICKBOT_TARS_M6_OPENCLAW_ADAPTER_FIXTURE_VOICE_PASS_READY_FOR_M7_PLANNING_ONLY`

Live provider/Gateway smoke, STT, Android, persistent service install, and host-PC Tailscale proxy/user-testing exposure are **not started** and require separate approval.
