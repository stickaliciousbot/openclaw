# Lessons Learned — Stickbot-TARS Voice Demo Hardening / M3 / M4

Date: 2026-07-02 AEST

## Durable rule: notebooks are gates, not afterthoughts

For Stickbot-TARS, every milestone needs synchronized documentation before final closeout:

- project implementation notebook
- troubleshooting/repair notebook
- project-local status/closeout artifacts
- long-term lessons for major bugs/repairs

If a milestone changes dependencies, isolation, security posture, model files, route boundaries, or runtime assumptions, update the notebooks before declaring PASS.

## M2.5 hardening lesson

Fail-closed before M3 was correct. The pre-hardening scaffold had missing gates:

- config fail-closed
- unsafe LAN/non-loopback refusal
- UUID-only audio route
- separate audio limits
- Origin/CSRF checks

Repairing these before model acquisition/load prevented the voice-demo path from becoming a localhost/LAN footgun.

## M3 model provenance lesson

M3 must remain provenance-only:

- download exact pinned revision
- hash every expected file
- record license/voice-rights caveat
- store under WSL-native path
- do not load `.pth`

Hashing proves artifact consistency only; it does not make `.pth` safe.

## M4 isolation lesson

Do not load `.pth` in the main `stickai` context just because it is convenient.

Findings:

- Docker/Podman/bwrap/firejail were unavailable.
- Dedicated low-privilege Unix user was preferred but blocked from Telegram because sudo needed TTY/password.
- Plain `unshare -Urn` was insufficient because it still saw `/home/stickai/.openclaw`.
- `unshare -Urnm` with private mount namespace and explicit empty bind mounts over `/home/stickai/.openclaw`, `.ssh`, `.codex`, `.config` was acceptable for this local M4 attempt because it hid secrets, blocked network, mounted model/speaker read-only, and left only output writable.

Durable rule: network isolation alone is not enough; verify filesystem/secret isolation too.

## M4 dependency lessons

### `xtts-api-server` install path

`xtts-api-server==0.9.0` pulled `pyaudio`, which failed because Python dev headers / `Python.h` were missing. Avoid this path unless system dependencies are explicitly approved or a wheel-compatible environment is prepared.

### Coqui direct path

`coqui-tts==0.27.5` installed, but dependency compatibility required manual fixes:

1. Initial install lacked Torch/Torchaudio.
2. CPU Torch/Torchaudio 2.12 installed, but `transformers==5.12.1` broke XTTS import because `isin_mps_friendly` was missing.
3. Pinning `transformers>=4.57,<5` to `4.57.6` restored the expected symbol.
4. PyTorch >=2.9 triggered Coqui's `torchcodec` audio IO requirement.
5. Installing `torchcodec==0.14.0` failed at native library load with missing `libnvrtc.so.13` / TorchCodec compatibility issues in the CPU stack.
6. CPU Torch/Torchaudio `2.8.0+cpu` installed successfully and restored `TTS_import=ok`, avoiding the PyTorch >=2.9 TorchCodec requirement. R4 sandbox load is pending after this repair.

Durable rule: for Coqui/XTTS, pin a known-compatible set instead of accepting latest major versions. Do not rely on open-ended `transformers` or latest Torch in this environment.

## Safety posture to preserve

- No model load unless secret dirs are hidden and network is blocked.
- No OpenClaw/Gateway/NOA config/routing/provider mutation for voice demo milestones.
- No model binaries in git.
- No generated audio/traces/venv/cache/node_modules in git.
- No browser/provider direct calls.
- No browser Web Speech API.
- No `/mnt/c` runtime/model/audio/traces.
- TARS never binds `8787`.

## Current classification reminder

M4 passed after Torch/Torchaudio `2.8.0+cpu` repair. R4 sandboxed first-load/generation loaded the local TARS XTTS model and generated a 95,788-byte, 24 kHz WAV inside the accepted no-network, secret-hidden, read-only-model boundary. Generated WAV SHA256: `9a1f332a74f2625c4f18e246b738eee29aede9c89362b5a407e6033b7135fc84`. Classification: `STICKBOT_TARS_M4_SANDBOXED_XTTS_LOCAL_LOAD_PASS_READY_FOR_M5_PLANNING_ONLY`.

Do not start M5/integration/serverization without separate owner approval and a fresh threat model.
