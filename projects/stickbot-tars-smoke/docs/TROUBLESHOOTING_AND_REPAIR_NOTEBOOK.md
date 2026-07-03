# Stickbot-TARS Troubleshooting and Repair Notebook

Last updated: 2026-07-02 20:03 AEST / 2026-07-02T10:03:00Z

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
- Result fields: `modelLoaded:true`, `wavGenerated:true`, `torchVersion:2.8.0+cpu`, `transformersVersion:4.57.6`, `torchaudioVersion:2.8.0+cpu`, `cudaAvailable:false`, `outputBytes:95788`, `sampleRate:24000`.
- Boundary remained intact: network blocked, secret dirs hidden, model/speaker read-only, output writable.

## Current M4 classification

`STICKBOT_TARS_M4_SANDBOXED_XTTS_LOCAL_LOAD_PASS_READY_FOR_M5_PLANNING_ONLY`

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
- XTTS server process stayed alive and eventually logged `STICKBOT_TARS_M5_XTTS_SERVER_MODEL_LOADED` and `STICKBOT_TARS_M5_XTTS_SERVER_LISTENING`.
- Readiness polling timed out because `curl http://127.0.0.1:18020/ready` could not connect.
- Root cause: private `unshare -n` network namespace did not have loopback (`lo`) brought up.
- Secondary bug: cleanup trap referenced unset `node_pid` when Node had not started.

Repair:

- Updated `scripts/m5-sandboxed-node-voice-smoke.sh` to bring loopback up using `ip link set lo up` or `ifconfig lo up`.
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

## M6 OpenClaw adapter notes

### Static validation passed

Command/session:

- `718a054e` / `glow-ocean`

Result:

- Existing + adapter tests: 27/27 PASS.
- Marker: `STICKBOT_TARS_M6_STATIC_CHECK_PASS`.
- Adapter tests covered echo no-spawn behavior, default `infer` and `agent` command shapes, required `{prompt}` placeholder, JSON text extraction, shell-metacharacter prompt passed as argv with `shell:false`, non-zero exit fail-closed behavior, and stdout limit fail-closed behavior.

### M6 sandboxed OpenClaw adapter fixture smoke passed

Command/session:

- `9932f947` / `fresh-daisy`

Result:

- Classification: `STICKBOT_TARS_M6_OPENCLAW_ADAPTER_FIXTURE_VOICE_PASS`.
- Adapter mode: `infer`.
- Adapter surface: `openclaw infer model run --prompt {prompt} --json`.
- Fixture OpenClaw CLI used: true.
- Live provider called: false.
- Gateway called: false.
- Node `/api/chat`: HTTP 200, text `OpenClaw adapter fixture response: M6 OpenClaw adapter fixture voice smoke`, audio URL `/audio/f640fa4b-115d-4063-9ea8-511d998d1592.wav`, `audioError:null`.
- Generated WAV SHA256 `fc7da588940bbe2238dcc91b9dc5156d36cbcaafcc49bbf606ebbdc3427ce5d0`, bytes `111148`, mono 24 kHz PCM WAV.
- Boundary remained intact: loopback enabled, external network blocked/unavailable, model/speaker read-only, secret dirs hidden, Node workspace sandboxed.

## Current M6 classification

`STICKBOT_TARS_M6_OPENCLAW_ADAPTER_FIXTURE_VOICE_PASS_READY_FOR_M7_PLANNING_ONLY`

## M7 local STT notes

### Real STT engine discovery blocked

Command/session:

- `21ac704a` / `young-crustacean`

Finding:

- `ffmpeg` / `ffprobe` missing.
- `whisper-cli`, `whisper-cpp`, `whisper`, `whisperx`, `faster-whisper` missing.
- System Python packages missing: `faster_whisper`, `whisper`, `torch`, `torchaudio`, `soundfile`.
- No local STT model dirs found under `/home/stickai/stickbot-voice/stt_models`, `~/.cache/whisper`, or `~/.cache/huggingface`.

Decision:

- Do not attempt real transcription in M7.
- Do not install/download models or call cloud STT.
- Implement fixture STT contract and leave real engine acquisition as separate approved milestone.

### M7 fixture contract passed

Static command/session:

- `0e287a97` / `salty-atlas`
- Tests: 34/34 PASS.
- Marker: `STICKBOT_TARS_M7_STATIC_CHECK_PASS`.

Smoke command/session:

- `3291be75` / `quick-reef`

Result:

- Classification: `STICKBOT_TARS_M7_LOCAL_STT_FIXTURE_CONTRACT_PASS_REAL_ENGINE_BLOCKED`.
- `/api/stt`: HTTP 200.
- Transcript: `M7 fixture transcript`.
- `cloudSpeechApi:false`.
- `browserWebSpeechApi:false`.
- Captured audio SHA256 `2976da01e205a110c9fa41d47659e238a5c6d3c3f3137582f2949853faa201dd`, bytes `3244`, mono 16 kHz PCM WAV.
- Boundary remained intact: private namespace, loopback enabled, external network blocked/unavailable, secret dirs hidden.

## Current M7 classification

`STICKBOT_TARS_M7_LOCAL_STT_FIXTURE_CONTRACT_PASS_REAL_ENGINE_BLOCKED_READY_FOR_STT_ENGINE_ACQUISITION`

## M7A local audio normalization notes

### Apt install blocked by runtime privilege shape

After repairing the normalizer test harness, `npm run check` passed `39/39` in session `faint-basil`, but the same command stopped at FFmpeg apt install because Telegram exec had no TTY/elevated sudo authority:

- `sudo: a terminal is required to read the password`
- elevated exec unavailable from Telegram runtime.

Resolution: use WSL-native user-space static FFmpeg fallback, not OpenClaw/Gateway mutation.

### Static FFmpeg fallback passed

Command/session:

- `02aed404-7c9e-417b-b309-13de64bde293` / `glow-valley`

Source:

- John Van Sickle `ffmpeg-release-amd64-static.tar.xz`.
- GPLv3 static build; private/dev validation only, not future distributable default.

Hashes:

- Download tarball SHA256: `abda8d77ce8309141f83ab8edf0596834087c52467f6badf376a6a2a4c87cf67`.
- Upstream MD5: `7fa72b652e19bf84c9461e332ea1cdf3`, checked OK.
- FFmpeg SHA256: `e7e7fb30477f717e6f55f9180a70386c62677ef8a4d4d1a5d948f4098aa3eb99`.
- FFprobe SHA256: `4f231a1960d83e403d08f7971e271707bec278a9ae18e21b8b5b03186668450d`.

Smoke result:

- Marker: `STICKBOT_TARS_M7A_STATIC_FFMPEG_ACQUIRE_AND_NORMALIZE_PASS`.
- Classification: `STICKBOT_TARS_M7A_LOCAL_AUDIO_NORMALIZATION_PROVENANCE_PASS`.
- Normalized fixture WAV SHA256: `38e3b264d99a035f168d6913520d2541a943c6a931e3f896882daf756b66fb7f`.
- Probe: `pcm_s16le`, 16000 Hz, mono.
- Network blocked/unavailable, secret dirs hidden, no cloud STT, no browser Web Speech API, no OpenClaw mutation.

## M7B whisper.cpp local STT notes

M7B completed as `STICKBOT_TARS_M7B_WHISPERCPP_LOCAL_STT_FIXTURE_PASS`.

Preflight:

- `cmake` missing, so avoided build/apt mutation and used pinned release binary.
- whisper.cpp tag: `v1.9.1`, commit `f049fff95a089aa9969deb009cdd4892b3e74916`.

Acquisition:

- Release asset SHA256 matched expected GitHub API digest: `f3bf3b4369a99b54665b0f19b88483b30de27f25963b0414235dea03198515c5`.
- Selected binary: `whisper-cli`, SHA256 `427dfb509f2c04d0f01c101978b5666102c6f7e3abf2a236452db5939f5b533a`.
- Model: `ggml-base.en.bin`, SHA256 `a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002`, bytes `147964211`.

Repairs:

- R1 failed safely because the harness selected deprecated `main`; `/api/stt` fail-closed with `STT_EXIT_NONZERO`. Repair: select `whisper-cli` and block `main`.
- R2 proved local transcription worked but failed normalization gate because `STT_NORMALIZE_AUDIO=1` parsed false. Repair: use `STT_NORMALIZE_AUDIO=true` and assert `normalizedLocal:true`.
- R3 passed: HTTP 200, `sttMode:cli`, `normalizedLocal:true`, transcript chars `42`, transcript SHA256 only preserved, raw transcript trace-only under `/tmp`, no durable raw transcript.

Boundary:

- No network required during transcription.
- Network blocked/unavailable in sandbox.
- Secret dirs hidden.
- No cloud STT.
- No browser Web Speech API.
- No OpenClaw/Gateway/NOA mutation.

## M7C small.en usable demo notes

M7C completed as `STICKBOT_TARS_M7C_SMALL_EN_USABLE_DEMO_PASS`.

Run:

- `655d2910-b2b9-42e5-834a-d05c23e9a508` / `tide-mist`.
- Static checks: `39/39 PASS`.
- Marker: `STICKBOT_TARS_M7C_SMALL_EN_USABLE_DEMO_SMOKE_PASS`.

Model:

- `ggml-small.en.bin`.
- SHA256: `c6138d6d58ecc8322097e0f987c32f1be8bb0a18532a3f88f734d1bbf9c41e5d`.
- Bytes: `487614201`.
- Path: `/home/stickai/stickbot-voice/stt_models/whisper.cpp/ggml-small.en.bin`.
- Excluded from git.

Smoke:

- `/api/stt`: HTTP 200.
- `sttMode:cli`.
- `normalizedLocal:true`.
- Transcript chars: `45`.
- Transcript SHA256 only: `44b7adbb95a5d4d7129029ad17b4b2cc1bc3429e1b9057f3ad3640ef234a2fac`.
- Raw transcript trace-only under `/tmp`.
- No network required during transcription; network blocked/unavailable in sandbox.
- No cloud STT, no browser Web Speech API, no OpenClaw/Gateway/NOA mutation.

## M7D LAN/loopback repair notes

### Issue: Windows localhost worked but Windows LAN IP did not

Context:

- M7D real mic demo was approved after M7C.
- Node was running inside WSL2 on Susie-Dell-Inspiron.
- Windows host Wi-Fi IP: `192.168.1.107`.
- WSL internal IP: `172.24.168.46`.
- Port: `19890`.

Symptoms:

- `http://localhost:19890/` worked from the Windows host.
- `http://192.168.1.107:19890/` did not work from LAN.

Root cause:

- Windows localhost forwarding into WSL does not automatically mean Windows is listening on the Wi-Fi/LAN interface.
- Binding Node to `0.0.0.0` inside WSL is necessary but not sufficient for same-LAN devices.
- Windows required explicit portproxy/firewall exposure from Windows LAN IP/port to WSL IP/port.

Related harness repairs:

- M7D harness supports explicit LAN mode with `VOICE_DEMO_ALLOW_LAN=true`.
- Default remains loopback-only.
- `0.0.0.0` requires explicit LAN allow.
- Port `8787` remains blocked.
- LAN browser Origin is accepted only when `allowLan=true` and Host/Origin match.
- Validation included local health and LAN-shaped Origin+CSRF mutating POST, not just listener presence.

Validation before Windows host exposure:

- `npm run check`: PASS, 41/41 tests after Origin policy repair.
- `STICKBOT_TARS_M7D_LAN_READINESS_VALIDATION_PASS`.
- `HEALTH_OK host=0.0.0.0 port=19890`.
- `SESSION_CSRF_OK`.
- `LAN_ORIGIN_MUTATING_POST_OK`.
- `STICKBOT_TARS_M7D_LIVE_SERVER_HEALTH_PASS`.
- Listener: `0.0.0.0:19890`, Node PID `568896`.

Operator-applied Windows host repair:

```powershell
netsh interface portproxy add v4tov4 listenaddress=192.168.1.107 listenport=19890 connectaddress=172.24.168.46 connectport=19890
New-NetFirewallRule -DisplayName "Stickbot TARS M7D 19890" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 19890
```

Result:

- Stick reported the PowerShell exposure advice worked.

Durable repair rule:

Every loopback/LAN browser demo must identify runtime location, discover all relevant addresses, bind with explicit LAN allow, verify local health, verify representative browser POST path, and configure/verify host-network forwarding/firewall when runtime is WSL2 or otherwise behind NAT. Do not tell Stick to retry a LAN URL until these gates pass.

M7D real mic final PASS remains pending actual microphone interaction and privacy-safe transcript confirmation. M8, live provider/Gateway smoke, Android, persistent service install, and broader host-PC Tailscale proxy/user-testing exposure are not started and require separate approval.
