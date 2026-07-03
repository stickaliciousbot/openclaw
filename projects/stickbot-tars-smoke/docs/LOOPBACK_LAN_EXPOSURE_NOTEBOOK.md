# Loopback / LAN Exposure Notebook

Created: 2026-07-02 23:18 AEST / 2026-07-02T13:18:00Z

## Why this exists

Stick reminded me during M7D that a WSL-hosted Node app being reachable from the Windows host via `localhost` is not the same as being reachable from another device on the LAN.

This notebook captures the proven procedure from the Douglas Bagmaker / EquipmentIQ demo and the M7D repair so future local browser demos do not stall on the same loopback/NAT mistake.

## Proven prior procedure: Douglas Bagmaker / EquipmentIQ

The Douglas Bagmaker digital twin Node app was made available by:

1. running the Node service with host/bind address `0.0.0.0`;
2. validating local health first;
3. then using the Windows host LAN IP for browser access.

Recorded proof from memory:

- local health: `http://127.0.0.1:8790/health` returned HTTP 200;
- service reported `host: 0.0.0.0` and requested port `8790`;
- LAN URL: `http://192.168.1.107:8790/`.

## WSL2-specific rule

When Node runs inside WSL2:

- `http://localhost:<port>/` working on Windows only proves Windows-to-WSL localhost forwarding.
- It does **not** prove the Windows LAN IP is listening on that port.
- LAN devices may fail to reach `http://<windows-lan-ip>:<port>/` until Windows port forwarding/firewall is configured.

For M7D on Susie-Dell-Inspiron:

- Node ran inside WSL.
- WSL internal IP was `172.24.168.46`.
- Windows Wi-Fi LAN IP was `192.168.1.107`.
- Tailscale IP was `100.119.233.106`.
- `http://localhost:19890/` worked on Windows.
- `http://192.168.1.107:19890/` did not work until Stick ran a Windows PowerShell portproxy/firewall exposure.

## Required procedure for every future loopback/LAN demo

Do all of this before telling Stick to retry from phone/laptop/LAN:

1. **Identify runtime location**
   - Is Node running in Windows native, WSL2, Alienware, another node, Docker, or a remote host?
   - State this explicitly.

2. **Identify the relevant addresses**
   - Loopback URL: `http://127.0.0.1:<port>/` or `http://localhost:<port>/`.
   - WSL IP if applicable.
   - Windows host LAN IP if applicable.
   - Tailscale IP if intentionally approved.
   - Remote host IP if not local.

3. **Bind safely**
   - Default must stay loopback-only.
   - LAN bind must require an explicit allow flag, e.g. `VOICE_DEMO_ALLOW_LAN=true`.
   - Never bind reserved ports such as `8787`.
   - Keep backend/model services loopback/private behind the frontend Node process unless separately approved.

4. **Verify service health locally**
   - Run `GET /health` from the same runtime namespace.
   - Require HTTP 200 and expected host/port in the response.
   - Do not ask Stick to retry until health is green.

5. **Verify browser mutation path, not just health**
   - For browser apps with CSRF/origin checks, verify `GET /api/session` and at least one mutating POST using the intended Host/Origin shape.
   - Health alone is insufficient; LAR taught that health posts can pass while the real payload path fails.

6. **Instrument Windows host exposure when runtime is WSL2**
   - If Windows `localhost` works but LAN IP does not, configure Windows forwarding/firewall from an elevated Windows PowerShell session.
   - Template:

```powershell
netsh interface portproxy add v4tov4 listenaddress=<windows-lan-ip> listenport=<port> connectaddress=<wsl-ip> connectport=<port>
New-NetFirewallRule -DisplayName "<meaningful name> <port>" -Direction Inbound -Action Allow -Protocol TCP -LocalPort <port>
```

   - For M7D this was:

```powershell
netsh interface portproxy add v4tov4 listenaddress=192.168.1.107 listenport=19890 connectaddress=172.24.168.46 connectport=19890
New-NetFirewallRule -DisplayName "Stickbot TARS M7D 19890" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 19890
```

7. **Only then give the retry URL**
   - Windows host first: `http://localhost:<port>/`.
   - LAN device second: `http://<windows-lan-ip>:<port>/`.
   - Tailscale only if explicitly approved: `http://<tailscale-ip>:<port>/`.

8. **Document the result**
   - Record runtime host, bind address, port, health result, POST-path result, portproxy/firewall status, and final reachable URL.
   - If real user/mic data is involved, preserve only privacy-safe evidence such as transcript length/hash or semantic confirmation, not raw transcript.

## M7D repair summary

M7D initially failed because I treated `0.0.0.0` in WSL as enough for LAN reachability. It was not.

Repairs made/required:

- M7D harness supports explicit LAN mode instead of rejecting all non-loopback binds.
- `VOICE_DEMO_ALLOW_LAN=true` is passed through to Node.
- LAN browser Origin is accepted only when `allowLan=true` and Host/Origin match.
- Validation proved local health and LAN-shaped Origin+CSRF mutating POST.
- Windows host exposure still required PowerShell `netsh interface portproxy` + firewall because Node was running inside WSL2.

## Browser microphone secure-origin rule

M7D proved another important distinction:

- `http://localhost:19890/` on the Windows host can access microphone permission because browsers treat `localhost` as a secure/trustworthy origin exception.
- `http://192.168.1.107:19890/` can load over LAN after portproxy/firewall repair, but browser microphone permission may still be blocked because plain HTTP on a LAN IP is not a secure origin.
- If the LAN page does not ask for mic permission, do not assume Stick blocked it. Treat it as browser policy until proven otherwise.

Before final/user testing, LAN/phone microphone capture needs a secure-origin plan, for example:

1. HTTPS on the host/LAN URL with a trusted/dev-installed certificate; or
2. a Tailscale HTTPS/Funnel/Serve-style secure endpoint if approved; or
3. Windows-host local browser via `http://localhost:<port>/` for local-only validation.

Plain `http://<lan-ip>:<port>/` is acceptable for page reachability/server POST tests, but not sufficient proof for real browser microphone capture.

## M7D UX blocker

Stick confirmed localhost voice capture works, but the current control is clunky:

- button wording/action is effectively “press once to start, press again to stop/send”;
- there is no visible active recording state;
- there is no clear indication that mic permission/capture activated.

Basic repair applied after operator feedback:

- button label now changes to “Recording… tap to stop/send”;
- button enters a disabled “Processing mic capture...” state while STT is running;
- insecure-origin microphone failures now show a LAN/HTTPS-oriented error message.

Before final M7D/user testing, improve this further:

- visual red/pulsing indicator or timer;
- clearer separate “start recording” / “stop and transcribe” affordance;
- final mobile/phone secure-origin UX.

## TTS voice-output rule

M7D also showed that STT capture and TTS playback must be gated separately.

- The M7D demo ran with `OPENCLAW_MODE=echo` and no XTTS backend at `127.0.0.1:8020`.
- With `generate TARS voice` checked, `/api/chat` returned text but voice synthesis failed with a fetch error.
- That is not an STT failure; it is missing XTTS backend readiness.

Repair applied:

- default `generate TARS voice` checkbox is now unchecked;
- UI labels voice generation as requiring a local XTTS backend.

Future rule:

- Do not default voice output on unless XTTS `/ready` is health-checked and green.
- If a milestone is STT-only, keep TTS disabled by default and make the UI explicit.

## General rule

Every loopback/LAN demo must include runtime-location identification, address discovery, explicit bind/allow flag, local health check, real POST-path check, host-network forwarding instrumentation where needed, and browser secure-origin checks for mic/camera APIs before user retry. Never conflate “works on localhost” with “available on LAN,” and never conflate “page loads on LAN” with “mic/camera APIs are permitted on LAN.”
