# M5 Local Serverization Implementation Plan

Status: `IN_PROGRESS`

Generated: 2026-07-02 19:05 AEST / 2026-07-02T09:05:00Z

## Approval

Stick approved M5/integration/serverization at 2026-07-02 18:59 AEST.

## Scope

M5 means local-only serverization and echo-mode integration:

1. Add a minimal loopback XTTS HTTP server that exposes the endpoint already expected by the Node smoke app:
   - `GET /health`
   - `GET /ready`
   - `POST /tts_to_audio/`
2. Run XTTS and Node echo app together in one sandbox smoke.
3. Prove Node `/api/chat` can receive text, use `OPENCLAW_MODE=echo`, call the local XTTS server, save a generated WAV, and return an `audioUrl`.
4. Preserve evidence and notebooks.

## Explicit non-scope

M5 does **not** include:

- OpenClaw production adapter.
- Gateway config/routing/default/fallback mutation.
- Gateway restart.
- NOA adapter or NOA service changes.
- STT wiring.
- Android/LAN/mobile exposure.
- XTTS systemd service install.
- LAN bind or portproxy.
- Use of port `8787`.
- Browser Web Speech API.
- Provider/API calls.

## Future user-testing LAN gate

Stick clarified that before user testing, the web app must be reachable from a phone and laptop on the LAN, similar to prior Douglas Bagmaker / local demo accessibility expectations. This is **not part of M5** and should be handled as a separate approved milestone after local loopback M5 passes.

Future LAN/mobile gate requirements:

1. Keep M5 loopback-only until the LAN milestone is explicitly started.
2. Choose a stable non-conflicting app port, not `8787`.
3. Preferred future reachability path: host-PC proxy over Tailscale.
   - Stick clarified the app does **not** need to run on a Tailscale host directly.
   - The app can remain local/WSL-bound; the host PC should proxy/expose the app through the host PC's Tailscale connection/IP.
   - Treat raw LAN exposure as fallback, not the default.
   - Possible implementation lanes to evaluate later: Windows host reverse proxy bound only to the Tailscale interface/IP, or Windows `netsh interface portproxy` from the host Tailscale IP/port to the WSL app port with a matching restrictive firewall rule.
   - Previous physical-phone testing had a successful Tailscale reachability pattern for LAR.
4. Bind only after explicit opt-in:
   - `VOICE_DEMO_ALLOW_LAN=true`
   - `HOST=0.0.0.0` or a specific LAN IP only for the browser-facing Node app.
   - Keep XTTS itself loopback/private behind Node unless a separate threat model approves otherwise.
5. Add LAN-specific security gates before exposing:
   - Origin/Host allowlist for phone/laptop URLs.
   - CSRF/session nonce still required for POSTs.
   - no wildcard CORS.
   - no browser-visible tokens, secret paths, model paths, or traces.
   - audio route remains UUID-only.
   - upload/body limits remain enforced.
6. Verify from both target classes before user testing:
   - phone browser health/session/UI load;
   - laptop browser health/session/UI load;
   - one text-to-voice turn from each if approved;
   - generated audio playback works;
   - no direct provider calls / no browser Web Speech API.
7. Record portproxy/firewall/URL evidence and rollback instructions.

## Safety boundary

The M5 smoke must run in the same class of boundary accepted during M4:

- `unshare -Urnm` private user/mount/network namespace.
- Model mounted read-only.
- Speaker directory mounted read-only.
- Output writable only where explicitly needed.
- Network blocked/unavailable.
- Empty bind mounts hiding:
  - `/home/stickai/.openclaw`
  - `/home/stickai/.ssh`
  - `/home/stickai/.codex`
  - `/home/stickai/.config`
- Node app copied to `/tmp/tars-m5-boundary/app` so the real `.openclaw` tree can remain hidden.
- Node `WORKSPACE_DIR` points to `/tmp/tars-m5-boundary/workspace`, not the real workspace, during sandbox smoke.

## Implementation files

- `scripts/xtts-local-server.py` — minimal loopback XTTS HTTP server.
- `scripts/m5-sandboxed-node-voice-smoke.sh` — starts XTTS + Node echo app inside the boundary and writes evidence under `docs/m5-local-serverization/`.
- `package.json` script `m5:smoke` — runs the sandbox smoke.
- `package.json` `check` now syntax-checks the M5 shell/Python scripts.

## Pass gates

M5 can be classified PASS only if all gates pass:

1. Static checks pass:
   - Node syntax checks.
   - existing blocker tests.
   - `bash -n scripts/m5-sandboxed-node-voice-smoke.sh`.
   - `python3 -m py_compile scripts/xtts-local-server.py`.
2. XTTS server startup refuses unsafe config by design:
   - loopback default;
   - reserved `8787` refused;
   - `/mnt/c` model/speaker path refused;
   - model artifact presence checked.
3. Sandbox smoke passes:
   - XTTS `/ready` returns ready after model load;
   - Node `/health` passes;
   - Node `/api/session` CSRF flow works;
   - Node `/api/chat` echo mode returns `audioUrl`;
   - generated app audio file exists and hashes;
   - network probe is blocked/unavailable;
   - secret dirs hidden;
   - model/speaker read-only;
   - no real OpenClaw/Gateway/NOA/STT/Android touched.
4. Evidence is written under `docs/m5-local-serverization/`.
5. Implementation notebook, troubleshooting/repair notebook, lessons learned, and `state/status.json` are updated.

## Current state

Implementation files have been written. Validation is pending native approval for shell execution.
