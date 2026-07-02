# Stickbot-TARS Troubleshooting and Repair Notebook

Last updated: 2026-07-02 18:18 AEST / 2026-07-02T08:18:00Z

## Purpose

Track every meaningful failure, root cause, repair, and validation result for Stickbot-TARS so future work can resume without re-discovering the same issues.

## Repair protocol

For each issue:

1. Record failing command/session id if available.
2. Classify whether model load occurred.
3. Record boundary status: network, secret visibility, model read/write status, output status.
4. Record root cause.
5. Record repair action.
6. Record validation result before proceeding.

## M2.5 repairs

### Issue: pre-hardening scaffold was unsafe for M3

Classification before repair:

`STICKBOT_TARS_M25_HARDENING_CLOSEOUT_BLOCKED_FAIL_CLOSED`

Failed gates:

- `configFailClosedImplemented`
- `unsafeLanRefusesStartup`
- `uuidOnlyAudioRoute`
- `separateAudioLimitExists`
- `originHostCsrfChecksExist`

Repair:

- Added `src/config.js` fail-closed startup validation.
- Added `safety/network-policy.js`.
- Added `safety/audio-path-policy.js`.
- Added `safety/limits.js`.
- Added `safety/origin-policy.js`.
- Added `safety/csrf.js`.
- Updated `server.js`, `public/app.js`, `.gitignore`, `package.json`.
- Added tests for all blocker gates.

Validation:

- `npm run check`: PASS.
- `node --test test/*.test.mjs`: PASS, 19/19.
- Unsafe startup tests: PASS.
- Guarded local echo smoke on `127.0.0.1:19888`: PASS.
- `git diff --check`: PASS.
- no `/mnt/c` in runtime repair files: PASS.
- production sentinel stat-only readback: PASS.

Commit:

`5c29204016bebd11da4ffa6dc20bb99aba9676a4`

## M3 repairs / notes

### Issue: approval-card/runtime friction during preflight and download

Status: operational friction only.

Resolution:

- Continued through native approvals.
- Kept M3 strictly to download/hash/provenance/no-load.

Validation:

- All expected files present.
- Model stored under WSL-native `/home/stickai/stickbot-voice`.
- SHA256 manifest written.
- No model load.
- No OpenClaw/Gateway mutation.

Commit:

`0fa3b732e70d403a4b0597c225a41d2f6043e452`

## M4 sandbox and runtime repairs

### Issue: no Docker/Podman/bwrap/firejail available

Finding:

- `docker`, `podman`, `bwrap`, `firejail` unavailable.
- `unshare` available.

Decision:

- Do not use the main `stickai` context directly for `.pth` load.
- Try a stronger `unshare -Urnm` private mount+network namespace boundary.

### Issue: plain `unshare -Urn` still sees secrets

Finding:

- `unshare -Urn` blocked/isolated network enough for DNS test, but still saw `/home/stickai/.openclaw`.

Resolution:

- Rejected plain `unshare` as insufficient.
- Accepted only `unshare -Urnm` with private mount namespace and empty bind mounts over secret dirs.

### Issue: dedicated low-privilege Unix user not creatable from Telegram context

Command/session:

- `e3c2cbbd` / `brisk-shoal`

Failure:

- `sudo: a terminal is required to read the password`.

Resolution:

- No model load attempted.
- Use `unshare -Urnm` fallback boundary instead.
- Still prefer real dedicated user/container later if operator shell/elevated context is available.

### Boundary probe: `unshare -Urnm`

Command/session:

- `b287b42a` / `brisk-cove`

Result:

- Model bind mount read-only: PASS.
- Speaker bind mount read-only: PASS.
- Output writable: PASS.
- Secret dirs hidden inside namespace: PASS.
- DNS/network blocked: PASS.
- Host secret dirs still present outside namespace: PASS.

Decision:

- M4 first load may proceed inside this boundary.

### Issue: `xtts-api-server` dependency install failed on `pyaudio`

Command/session:

- `854ac5d4` / `tender-daisy`

Failure:

- `pyaudio==0.2.14` failed to build due missing `Python.h`.
- `xtts-api-server==0.9.0` depends on `pyaudio`.

Model load occurred: no.

Resolution:

- Avoid `xtts-api-server` for M4 first load.
- Use direct Coqui XTTS Python path first.

### Issue: Coqui installed without Torch

Command/session:

- `7eab79aa` / `glow-slug`

Finding:

- `coqui-tts==0.27.5` installed.
- `TTS` present.
- `torch` missing.
- `torchaudio` missing.

Resolution:

- Install CPU Torch/Torchaudio into the TARS venv only.

### Issue: Transformers 5.x incompatible with Coqui XTTS import

Command/session:

- First load attempt `ac38812a` / `quiet-pine`
- Inspection `604ec3c5` / `briny-summit`

Failure:

- `ImportError: cannot import name 'isin_mps_friendly' from transformers.pytorch_utils`.
- Installed `transformers==5.12.1` lacked the symbol.

Boundary status:

- Network blocked.
- Secrets hidden.
- Model not loaded.
- WAV not generated.

Resolution:

- Pin `transformers>=4.57,<5`.
- Installed `transformers==4.57.6`.
- Verified `isin_mps_friendly` exists.

### Issue: PyTorch >=2.9 path requires TorchCodec

Command/session:

- Second load attempt `76d57e74` / `delta-bloom`

Failure:

- Coqui import raised: `From Pytorch 2.9, the torchcodec library is required for audio IO`.

Boundary status:

- Network blocked.
- Secrets hidden.
- Model not loaded.
- WAV not generated.

Resolution:

- Installed `coqui-tts[codec]` / `torchcodec==0.14.0`.

### Issue: TorchCodec native load failure with Torch 2.12 CPU stack

Command/session:

- Third load attempt `355676ea` / `nova-breeze`

Failure:

- `RuntimeError: Could not load libtorchcodec`.
- Native load complained about missing `libnvrtc.so.13` and Torch/TorchCodec compatibility.

Boundary status:

- Network blocked.
- Secrets hidden.
- Model not loaded.
- WAV not generated.

Repair:

- Command/session `95b9eeff` / `oceanic-zephyr` downgraded CPU Torch/Torchaudio successfully:
  - `torch 2.8.0+cpu`
  - `torchaudio 2.8.0+cpu`
  - `cuda_available False`
  - `TTS_import=ok`

Validation:

- R4 sandboxed first-load/generation command `76573901` passed inside the same `unshare -Urnm` boundary.
- Result fields:
  - `classification`: `STICKBOT_TARS_M4_SANDBOXED_XTTS_LOCAL_LOAD_PASS`
  - `modelLoaded`: `true`
  - `wavGenerated`: `true`
  - `torchVersion`: `2.8.0+cpu`
  - `transformersVersion`: `4.57.6`
  - `torchaudioVersion`: `2.8.0+cpu`
  - `cudaAvailable`: `false`
  - `outputBytes`: `95788`
  - `sampleRate`: `24000`
- Boundary remained intact: network blocked, secret dirs hidden, model/speaker read-only, output writable.

## Current M4 classification

`STICKBOT_TARS_M4_SANDBOXED_XTTS_LOCAL_LOAD_PASS_READY_FOR_M5_PLANNING_ONLY`

M5/integration/serverization was later approved by Stick for local-only serverization.

## M5 local serverization notes

### Static validation passed

Command/session:

- `0e9bda9a` / `calm-ocean`

Result:

- Existing blocker tests: 19/19 PASS.
- New M5 shell launcher syntax check: PASS via `bash -n`.
- New M5 Python XTTS local server compile check: PASS via `python3 -m py_compile`.
- Marker: `STICKBOT_TARS_M5_STATIC_CHECK_PASS`.

### M5 sandbox smoke R1 failed safely: loopback down in private netns

Command/session:

- `b01b48c0` / `dawn-ember`

Result:

- Boundary setup succeeded: model/speaker mounted read-only, secret dirs hidden, external network probe blocked/unavailable.
- XTTS server process stayed alive and eventually logged:
  - `STICKBOT_TARS_M5_XTTS_SERVER_MODEL_LOADED`
  - `STICKBOT_TARS_M5_XTTS_SERVER_LISTENING`
- Readiness polling still timed out because `curl http://127.0.0.1:18020/ready` could not connect.
- Root cause: the private `unshare -n` network namespace did not have loopback (`lo`) brought up, so local loopback services were unreachable even though external network remained isolated.
- Secondary bug: cleanup trap referenced unset `node_pid` when Node had not started, masking the intended `XTTS_READY_TIMEOUT` exit.

Repair:

- Updated `scripts/m5-sandboxed-node-voice-smoke.sh` to bring loopback up inside the private namespace using `ip link set lo up` or `ifconfig lo up`.
- Initialized `xtts_pid` and `node_pid` and made cleanup tolerate processes that never started.

R2 validation:

- Static recheck command/session `f9412916` / `sharp-crest` passed: existing tests 19/19, marker `STICKBOT_TARS_M5_R2_STATIC_CHECK_PASS`.
- Sandbox smoke R2 command/session `655a4a74` / `vivid-cove` passed.
- XTTS `/ready`: `ok:true`, classification `STICKBOT_TARS_M5_XTTS_SERVER_READY`, model loaded at `2026-07-02T09:36:59Z`.
- Node `/api/chat`: HTTP 200, returned `audioUrl` `/audio/41712ff0-d842-4e12-9228-5fe33536f2a2.wav`, `audioError:null`, and logged daily/event records inside the sandbox workspace.
- Generated WAV SHA256 `1daf103c5e9de8dbeef2a373638b843ff8e01429b415c6ae279853c9908712ec`, bytes `142380`, mono 24 kHz PCM WAV.
- Boundary remained intact: loopback enabled inside namespace, external network blocked/unavailable, model/speaker read-only, secret dirs hidden, Node workspace sandboxed.

## Current M5 classification

`STICKBOT_TARS_M5_LOCAL_SERVERIZATION_NODE_VOICE_PASS_READY_FOR_M6_PLANNING_ONLY`

M6/OpenClaw adapter, STT, Android, persistent service install, and host-PC Tailscale proxy/user-testing exposure are not started and require separate approval.
