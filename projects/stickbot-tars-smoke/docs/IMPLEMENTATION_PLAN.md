# Stickbot TARS voice smoke implementation plan

## Goal

Build a local-first sample Node app where Stick can type or capture mic audio, send it to Stickbot/OpenClaw, receive text, synthesize a TARS-style voice using `Pyrater/TARS` through local XTTS, and log the turn into daily memory + context-bridge events so other chat surfaces can later see the continuity record.

## Current host finding

Local Gateway host check:

- Host: `Susie-Dell-Inspiron`.
- `/`, `/home`, and `/tmp` are on `/dev/sdd`: 1007G total, 158G used, **799G free**, 17% used.
- The disk command timed out while computing deeper directory sizes, but top-level capacity is sufficient for the Node smoke and could hold the model if needed. Still prefer Alienware for model runtime isolation.

Alienware WSL check:

- WSL root `/`: 1007G total, 927G free, 4% used.
- Windows `C:` mounted at `/mnt/c`: 459G total, 8.5G free, 99% used — do not place models/envs here.
- Windows `D:` mounted at `/mnt/d`: 932G total, 126G free, 87% used — usable but getting tight.
- `python3`: 3.10.12.
- `node`: not found in Alienware WSL.
- `nvidia-smi`: not found in Alienware WSL.
- `nvcc`: not found in Alienware WSL.

Implication: storage is fine under Alienware WSL `/home`, but GPU acceleration is not yet visible there. The first runtime lane can be CPU/slow validation, or we need a separate GPU visibility repair/install pass before fast XTTS.

## NOA assessment and implications — 2026-07-01

Latest NOA evidence reviewed before updating this plan:

- `state/noa-daily-restart/latest.json` reports run `noa-restart-20260701T014409Z`, status `PASS`, `healthGate: 1`, `probeGate: 1`.
- Run log `state/noa-daily-restart/noa-restart-20260701T014409Z.log` shows health passed for:
  - `8787` — `noa-bridge-v1`
  - `8790` — `noa-common-reasoner`
  - `8795` — `stickbot-unified-brain`
- Recovery runbook: `projects/noa-bridge-v1/NOA_TROUBLESHOOTING_AND_REPAIR_MANUAL.md`.
- Important finding: the reason probe gate returned `ok:true`, but answer text showed downstream provider quota degradation: `REASONER_FAILED:429`.
- Owner clarification: if this degradation is tied to exhausted OpenAI API quota, it is acceptable and should not become a repair chase. There is no API quota left, and the forward path is local TARS TTS if it works.

Implications for Stickbot-TARS:

1. Treat NOA as **liveness-recovered but semantically/provider-degraded**. If the degradation is OpenAI API quota related, it is expected/non-blocking for the local-first TARS path.
2. Borrow NOA patterns — health gates, envelopes, append-only context events, explicit service ownership — but do not make NOA/unified-brain the required answer source for the TARS demo yet.
3. Do not spend effort restoring OpenAI API quota for this demo unless Stick explicitly reopens that path; prioritize local TARS TTS and local/non-API routing.
4. Keep the TARS smoke port on `18788` or another non-conflicting port. Do **not** use `8787`; that belongs to `noa-bridge.service`.
5. Add a preflight gate before any OpenClaw/NOA-adjacent adapter work:
   - `state/noa-daily-restart/latest.json` status `PASS`
   - `scripts/noa_health_probe.sh` passes, if live execution is approved/available
   - no unresolved `EADDRINUSE :::8787`
   - provider-quality finding explicitly classified if reason probe still returns 429
6. TARS M6 should prefer the direct OpenClaw adapter path first. A NOA/unified-brain adapter is optional later only if it avoids exhausted API quota or quota is explicitly restored.

## Safety posture

- Do not load `*.pth` model files on the production Gateway host unsandboxed. PyTorch `.pth` is pickle-based and can execute code at load time.
- First load should happen in an isolated venv/container on Alienware WSL, with outbound network blocked after model/dependency download.
- Browser must not use Web Speech API because Chrome speech recognition can call Google. The smoke records audio with MediaRecorder and posts bytes locally.
- No API keys in browser or repo. OpenClaw access stays server-side.
- TARS/Interstellar voice should be private/local experimental only; do not public-brand or redistribute without legal review.

## TTS runtime

Recommended runtime: `daswer123/xtts-api-server` or a minimal direct Coqui XTTS wrapper.

TARS model layout expected by `xtts-api-server`:

```text
~/stickbot-voice/xtts_models/tars/
  config.json
  vocab.json
  model.pth
  speakers_xtts.pth        # keep if loader accepts it / for compatibility
~/stickbot-voice/speakers/
  reference.wav
~/stickbot-voice/output/
```

Launch candidate:

```bash
python -m xtts_api_server \
  --host 127.0.0.1 \
  --port 8020 \
  --device cpu \
  --model-folder ~/stickbot-voice/xtts_models \
  --speaker-folder ~/stickbot-voice/speakers \
  --output ~/stickbot-voice/output \
  --model-source local \
  --version tars \
  --lowvram
```

Switch to `--device cuda:0` only after WSL GPU visibility is fixed.

Use `/tts_to_audio/` with JSON:

```json
{ "text": "hello Stick", "speaker_wav": "reference.wav", "language": "en" }
```

## Node smoke

Scaffold lives in `projects/stickbot-tars-smoke/`.

Current behavior:

- `GET /` browser UI with text box, mic button, audio playback.
- `POST /api/chat` accepts `{text, voice}`.
- `POST /api/stt` stores mic capture locally and returns 501 until local STT is configured.
- `POST /api/chat` can run in:
  - `OPENCLAW_MODE=echo` default safe smoke.
  - `OPENCLAW_MODE=cli` with `OPENCLAW_ARGS_JSON` once CLI command shape is confirmed.
- XTTS call targets `XTTS_URL` default `http://127.0.0.1:8020`.
- Logs each text turn to:
  - `memory/YYYY-MM-DD.md`
  - `memory/context-bridge-events/evt-...-stickbot-tars-voice-smoke-<turn>.json`

## OpenClaw bridge options

Preferred first safe bridge: server-side CLI adapter using the supported OpenClaw command once confirmed by `openclaw agent --help`.

Better later bridge: first-class OpenClaw Gateway/API integration if documented/stable, avoiding chat-surface scraping.

Do not send from Android directly to provider APIs. The Node server should be the boundary that owns OpenClaw auth, logging, and TTS routing.

## STT path

Phase 1: text-only + mic capture saved locally.

Phase 2 options:

1. `whisper.cpp` local HTTP/CLI on Alienware or Gateway host.
2. `faster-whisper` local Python service on Alienware GPU.
3. Android on-device STT only if verified not to call cloud.

## Validation status

Completed:

1. Local disk check: PASS — local host has 799G free.
2. Alienware disk check: PASS — WSL `/` has 927G free; `/mnt/d` has 126G free; `/mnt/c` should be avoided.
3. Node smoke syntax check: PASS — `node --check projects/stickbot-tars-smoke/server.js`.
4. Echo-mode Node smoke: PASS on `127.0.0.1:18788` after avoiding occupied port `8788`.
5. Port ownership update after NOA assessment: reserve `8787` for `noa-bridge.service`; keep the TARS smoke on `18788` by default.
6. Memory/context-bridge readback: PASS — event `memory/context-bridge-events/evt-20260701T010100Z-stickbot-tars-voice-smoke-482c732c-f7cd-4d71-bb46-4bc16151c78f.json` recorded the turn and boundaries.

Pending / reordered next steps:

1. M1 path/host/runtime verification first. Lock Alienware vs Inspiron and canonical paths before Codex/refactor work.
2. M2 modular refactor.
3. M2.5 security/test harness: unsafe config tests, path traversal tests, CORS/origin/CSRF tests, port conflict tests, JSON schema/body-limit parse tests, audio upload limit tests, and browser redaction tests.
4. M3 model provenance/license/hash only. Record model source, revision, license, allowed usage, and SHA256 manifest. No model load.
5. M4 sandboxed load. Load/generate only inside the constrained low-privilege XTTS runtime with read-only model mount, output-only audio dir, no OpenClaw/Codex/SSH secrets, and blocked egress.
6. M5 voice with echo. Probe the actual XTTS API contract before Node depends on `/tts_to_audio/` or any endpoint; generate one WAV via verified local XTTS endpoint.
7. M6 OpenClaw adapter. Confirm stable OpenClaw CLI/API adapter; previous help probe timed out, so `OPENCLAW_MODE=cli` remains unvalidated.
8. M7 local STT. Wire whisper.cpp/faster-whisper only after ffmpeg/audio-normalization gate; current mic button only captures audio locally.
9. M8 Android/LAN gate with explicit `VOICE_DEMO_ALLOW_LAN=true`, token/pairing auth, firewall/portproxy notes, Android secret-free validation, restricted CORS, and HTTPS/native mic strategy.
10. Optional later: evaluate a NOA/unified-brain adapter only if it avoids exhausted OpenAI API quota or Stick explicitly restores/reopens API quota; current NOA state is process-liveness PASS with expected/non-blocking semantic/provider 429 degradation for the TARS-local path.

## Hardening addendum summary — required before M3/M4/M6

The LLD Section 14 is now a hard gate. Key additions:

- Model trust boundary: `.pth` files are untrusted; hashing is not safety. First model load/generation must run in a low-privilege boundary with no OpenClaw/provider/Codex/SSH/Gmail/Telegram secrets, no `~/.ssh`, no `~/.openclaw`, no `~/.codex`, no production Gateway config/runtime files, read-only model mount, narrow output-only audio dir, environment allowlist, package/version capture, first-generation logs, and blocked egress after dependency install.
- License/provenance/voice rights: M3 must produce a manifest with model name, source, revision, timestamp, file SHA256/bytes, license/commercial-use status, and voice-use flags. XTTS/Coqui-derived weights may be non-commercial; if so, the whole voice path is private-demo-only and must not be promoted into Altoura/customer/product surfaces without clearance.
- Verified path policy: use WSL-native paths, avoid `/mnt/c`, never invent fake Windows/WSL hybrid roots, verify targets with `pwd`/`realpath`/`test`/`stat` before file operations, and maintain `state/stickbot-tars-paths.json` before M1/M2 PASS.
- XTTS API discovery: probe `/docs`, `/openapi.json`, or equivalent and store a real request/response contract before depending on any endpoint.
- OpenClaw adapter hardening: prefer documented Gateway/RPC if available; if CLI is used, use `spawn(file,args,{shell:false})`, no shell interpolation, allowlisted executable/args, stdin/temp-file prompt passing, prompt length limit, env whitelist, timeout, process-tree kill, bounded stdout/stderr, exactly-one-response verification, before/after route/config snapshot, and failed-turn event without misleading voice synthesis.
- Mic/STT conversion: handle `audio/webm`/Opus from MediaRecorder with bounded ffmpeg normalization to mono 16 kHz PCM WAV or adapter-specific equivalent before local STT.
- Localhost web security: bind `127.0.0.1` by default, reject unexpected `Origin`/`Host`, no wildcard CORS, CSRF/session nonce for POSTs, JSON/audio limits, UUID-only `/audio/:file`, path traversal tests, no browser exposure of tokens/secret paths/raw traces, and secure-context/token-pairing notes before LAN/mobile.
- Retention/privacy: no raw audio in Context Bridge, no raw audio in git, `.gitignore` guardrails, retention windows, cleanup command `scripts/cleanup-local-artifacts.sh` for captured/generated audio/traces/temp files, HMAC hashes for sensitive transcripts where needed.
- Concurrency/readiness: add `/health` vs `/ready`, bounded XTTS queue/concurrency, cancellation/timeouts, and explicit degraded states such as `TURN_COMPLETE`, `TEXT_READY_VOICE_PENDING`, `PASS_WITH_VOICE_FAILURE`, `PASS_WITH_LOGGING_FAILURE`, `TURN_FAILED`, and `BLOCKED_UNSAFE_CONFIG`.
- TARS first-run observer: monitor first model load/generation and first 48 hours for unexpected internet calls, out-of-scope file access/writes, secret path reads, unexpected process spawning, runaway resources, and artifact creation. Quarantine on suspicious behavior. If clean for 48 hours in the same boundary/revision/runtime, classify that exact setup as demo-trusted.
