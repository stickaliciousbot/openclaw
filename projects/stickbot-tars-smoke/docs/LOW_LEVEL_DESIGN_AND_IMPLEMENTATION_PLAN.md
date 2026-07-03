# Stickbot-TARS Voice Demo — Low-Level Design and Implementation Plan

Status: draft v0.4 — tightened model isolation, path policy, provenance, and adapter security 2026-07-01 AEST
Owner context: Stick / Stickbot
Created: 2026-07-01 AEST
Scope: local-first Node voice demo, designed as a modular substrate for a larger Stickbot voice/multimodal mesh.

## 1. Executive goal

Build a safe, local-first Node demo where Stick can:

1. Type text or press a mic button.
2. Route the request into Stickbot/OpenClaw through a controlled server-side adapter.
3. Receive assistant text.
4. Generate a local TARS-style voice response using `Pyrater/TARS` via XTTS.
5. Play the response in browser/Android later.
6. Append durable turn logs into daily memory and Context Bridge so other chat surfaces can become aware of the voice interaction.

This is explicitly a testbed for a bigger solution, so the build must favor modular boundaries, observability, replaceable components, and safe routing over a one-off demo.

## 2. Non-goals / boundaries

- Do not use browser Web Speech API for STT; it can call cloud services.
- Do not call Google STT, OpenAI TTS, or external speech APIs in the demo path.
- Do not load `.pth` files unsandboxed on the production Gateway host.
- Do not expose TTS/OpenClaw endpoints to LAN/public until local-only gates pass.
- Do not make Android the owner of provider credentials or OpenClaw secrets.
- Do not hardcode TARS/Interstellar branding into a public-facing product.
- Do not mutate OpenClaw routing/config/service authority for the demo without explicit approval.

## 3. Current evidence baseline

Completed smoke evidence:

- Local host disk: `Susie-Dell-Inspiron`, `/dev/sdd`, 1007G total, 799G free.
- Alienware WSL disk: `/` 1007G total, 927G free. `/mnt/d` 126G free. `/mnt/c` avoid, only 8.5G free.
- Alienware WSL runtime gap: Python 3.10.12 present; `node`, `nvidia-smi`, and `nvcc` not visible.
- Node scaffold exists at `projects/stickbot-tars-smoke/`.
- Syntax gate passed: `node --check projects/stickbot-tars-smoke/server.js`.
- Echo-mode local smoke passed on `127.0.0.1:18788`.
- NOA assessment reviewed:
  - `state/noa-daily-restart/latest.json` run `noa-restart-20260701T014409Z` reports `PASS`, `healthGate: 1`, `probeGate: 1`.
  - Run log shows `8787`, `8790`, and `8795` health endpoints passed.
  - `noa-bridge.service` owns `8787`; the TARS demo must not bind that port.
  - Reason probe body still shows downstream provider/quota degradation: `REASONER_FAILED:429`, so NOA is liveness-green but semantic/provider-degraded.
  - Owner clarification: if the degradation is exhausted OpenAI API quota, it is acceptable/non-blocking; API quota is gone and the forward path is local TARS TTS if it works.
- Memory/context readback passed:
  - `memory/context-bridge-events/evt-20260701T010100Z-stickbot-tars-voice-smoke-482c732c-f7cd-4d71-bb46-4bc16151c78f.json`
  - boundaries show `externalCloudSpeechRecognition:false`, `browserWebSpeechApi:false`, `xttsExpectedLocalOnly:true`.

## 4. Architecture overview

### 4.1 Runtime lanes

```text
Browser / Android client
  ├─ text form
  ├─ mic capture button, MediaRecorder only
  └─ audio playback
        │
        ▼
Stickbot Voice Node Gateway / demo app
  ├─ HTTP UI/API
  ├─ local STT adapter, later
  ├─ Stickbot/OpenClaw adapter
  ├─ local XTTS adapter
  ├─ turn ledger
  ├─ memory writer
  ├─ context-bridge event writer
  └─ audit/trace writer
        │
        ├── OpenClaw Gateway / session adapter
        │     └─ text response
        │
        └── TARS XTTS service, local-only
              └─ WAV/stream response
```

### 4.2 Module boundaries

The Node app should be split into modules before feature growth:

```text
projects/stickbot-tars-smoke/
  server.js                         # thin HTTP/bootstrap entry
  src/
    config.js                       # env/config validation
    http/router.js                  # route registration
    adapters/
      openclaw-adapter.js           # OpenClaw bridge interface
      openclaw-echo-adapter.js      # safe test adapter
      openclaw-cli-adapter.js       # CLI adapter once confirmed
      openclaw-rpc-adapter.js       # later stable Gateway/RPC adapter
      xtts-adapter.js               # local XTTS HTTP adapter
      stt-placeholder-adapter.js    # saves audio only
      whisper-adapter.js            # later local STT
    ledgers/
      turn-ledger.js                # normalized turn schema
      memory-writer.js              # memory/YYYY-MM-DD.md append
      context-bridge-writer.js      # memory/context-bridge-events/*.json
      trace-writer.js               # JSONL operational traces
    safety/
      network-policy.js             # expected-local endpoints validation
      redaction.js                  # future PII/secrets scrub before logs
      limits.js                     # body/text/audio duration limits
    public/
      index.html
      app.js
    data/
      audio/                        # generated or captured audio, ignored later
      traces/                       # JSONL runtime traces
```

The current scaffold can be refactored into this shape in M2.

## 5. Integration surfaces

### 5.1 Client → Node API

Initial API:

- `GET /` — browser smoke UI.
- `GET /health` — service health and active adapter names.
- `POST /api/chat`
  - input: `{ text: string, voice?: boolean, source?: string }`
  - output: `{ id, text, audioUrl?, audioError?, logs, traceId }`
- `POST /api/stt`
  - input: `audio/webm` bytes from MediaRecorder.
  - current output: 501 + local saved file path.
  - future output: `{ transcript, confidence?, sttAdapter, traceId }`.
- `GET /audio/:file` — local generated audio file.

Future API:

- `POST /api/turn` — normalized multimodal turn: text, audioRef, channel, session, persona, routing hints.
- `GET /api/turn/:id` — inspect turn status/artifacts.
- `GET /api/events` — local SSE stream for browser status.

### 5.2 Node → OpenClaw

Adapter contract:

```ts
type OpenClawRequest = {
  turnId: string;
  userText: string;
  source: 'stickbot-tars-smoke' | 'android-voice' | string;
  sessionKey?: string;
  routeHints?: {
    agentId?: string;
    model?: string;
    safeMode?: boolean;
  };
};

type OpenClawResponse = {
  text: string;
  sessionKey?: string;
  routeTrace?: object;
  toolUseSummary?: object;
  safety?: object;
};
```

Initial adapters:

1. `echo` — deterministic local smoke; already validated.
2. `cli` — server-side OpenClaw command adapter once help/API is confirmed.
3. `rpc/http` — later preferred stable Gateway integration if documented.

Hard rule: Android/browser never calls model providers directly.

### 5.3 Node → XTTS

Adapter contract:

```ts
type TtsRequest = {
  turnId: string;
  text: string;
  speaker: string;
  language: 'en' | string;
};

type TtsResponse = {
  audioPath: string;
  audioUrl: string;
  durationMs?: number;
  modelId: 'Pyrater/TARS' | string;
  modelSha256?: Record<string,string>;
};
```

Initial XTTS endpoint:

```http
POST http://127.0.0.1:8020/tts_to_audio/
Content-Type: application/json

{ "text": "hello Stick", "speaker_wav": "reference.wav", "language": "en" }
```

Default TTS service must bind to `127.0.0.1` only until security gates pass.

### 5.4 Node → memory and Context Bridge

Every accepted turn should write:

1. Daily memory append:
   - path: `memory/YYYY-MM-DD.md`
   - compact human-readable summary.
2. Context Bridge event:
   - path: `memory/context-bridge-events/evt-...stickbot-tars...json`
   - machine-readable state.
3. Trace JSONL:
   - path: `projects/stickbot-tars-smoke/data/traces/YYYY-MM-DD.jsonl`
   - detailed operational span: request received, STT, OpenClaw, TTS, memory write, errors.

Context event schema baseline:

```json
{
  "id": "evt-...-stickbot-tars-voice-turn-<turnId>",
  "timestamp": "ISO-UTC",
  "localTime": "ISO-with-zone-if-available",
  "summary": "Voice turn logged...",
  "status": "OBSERVED|PASS|FAIL|BLOCKED",
  "classification": "STICKBOT_TARS_VOICE_TURN",
  "source": "stickbot-tars-smoke:text|mic|android",
  "turn": {
    "id": "uuid",
    "inputMode": "text|audio",
    "transcriptHash": "sha256 optional",
    "assistantTextHash": "sha256 optional"
  },
  "artifacts": {
    "inputAudioPath": null,
    "outputAudioPath": null,
    "tracePath": null
  },
  "routing": {
    "openclawAdapter": "echo|cli|rpc",
    "sessionKey": null,
    "routeMutation": false
  },
  "boundaries": {
    "externalCloudSpeechRecognition": false,
    "browserWebSpeechApi": false,
    "providerDirectFromClient": false,
    "xttsExpectedLocalOnly": true
  }
}
```

## 6. Safe mesh/routing substrate

The demo should introduce a small routing substrate rather than bolting routes directly into UI code.

### 6.1 Voice turn envelope

All requests become a `VoiceTurnEnvelope`:

```ts
type VoiceTurnEnvelope = {
  turnId: string;
  createdAt: string;
  actor: 'stick';
  surface: 'web-smoke' | 'android' | 'telegram-proxy' | string;
  input: {
    mode: 'text' | 'audio';
    text?: string;
    audioPath?: string;
    mimeType?: string;
  };
  route: {
    target: 'stickbot-main';
    adapter: 'echo' | 'openclaw-cli' | 'openclaw-rpc';
    sessionPolicy: 'voice-demo-session' | 'main-session' | 'isolated-session';
  };
  output: {
    text?: string;
    audioPath?: string;
    audioUrl?: string;
  };
  audit: {
    traceId: string;
    memoryWrite: boolean;
    contextBridgeWrite: boolean;
  };
};
```

### 6.2 Routing principles

- Route by envelope fields, not hardcoded UI assumptions.
- Keep `main-session` integration owner-gated; start with `voice-demo-session` or echo.
- Preserve close-loop status on every turn: accepted, transcribed, answered, voiced, logged.
- Never let voice demo mutate model routing/defaults/fallbacks.
- Do not bypass OpenClaw’s safe Gateway surface when invoking Stickbot.
- Keep future surfaces pluggable: web, Android, Telegram voice note, desktop push-to-talk.

### 6.3 NOA bridge assessment and directional signal

NOA bridge work is now reviewed enough to use as **pattern input**, not as a required runtime dependency for the first TARS demo.

Current NOA assessment:

- Liveness: recovered. Latest gate `noa-restart-20260701T014409Z` is `PASS` with `healthGate: 1` and `probeGate: 1`.
- Services: `8787` `noa-bridge-v1`, `8790` `noa-common-reasoner`, and `8795` `stickbot-unified-brain` all passed health in the recovery log.
- Ownership: `8787` belongs to `noa-bridge.service`; TARS must default to `18788` and avoid `8787`.
- Quality finding: reason probe text still reports downstream `REASONER_FAILED:429`. Owner clarified that if this is OpenAI API quota exhaustion, it is acceptable/non-blocking for TARS; do not chase API quota repair unless explicitly requested.
- Repair pattern: documented in `projects/noa-bridge-v1/NOA_TROUBLESHOOTING_AND_REPAIR_MANUAL.md`.

Reusable patterns:

- append-only event ledgers;
- clear bridge envelope schemas;
- route adapters as separate modules;
- health/probe gates before promotion;
- explicit service ownership for ports;
- no-silence / explicit status reporting;
- safe boundaries between live runtime and persisted memory/context.

Decision for TARS v0.2: **pattern-only reuse for now**. Do not copy NOA bridge code into TARS. Do not route TARS answers through NOA/unified-brain until it either avoids exhausted OpenAI API quota or Stick explicitly restores/reopens API quota and a separate adapter gate passes.

## 7. Low-level component design

### 7.1 `config.js`

Responsibilities:

- Parse env.
- Validate local-only defaults.
- Refuse unsafe configs by default.

Important env:

```bash
HOST=127.0.0.1
PORT=18788
OPENCLAW_MODE=echo|cli|rpc
OPENCLAW_ARGS_JSON='["agent","--message","{prompt}"]'
XTTS_URL=http://127.0.0.1:8020
XTTS_SPEAKER=reference.wav
XTTS_LANGUAGE=en
VOICE_DEMO_ALLOW_LAN=false
VOICE_DEMO_WRITE_MEMORY=true
VOICE_DEMO_WRITE_CONTEXT_BRIDGE=true
```

Fail-closed rules:

- If `XTTS_URL` is not loopback and `VOICE_DEMO_ALLOW_LAN!=true`, refuse to start.
- If `HOST=0.0.0.0` and `VOICE_DEMO_ALLOW_LAN!=true`, refuse to start.
- If `OPENCLAW_MODE=cli` without validated command template, refuse to start.

### 7.2 `openclaw-adapter`

Responsibilities:

- Convert `VoiceTurnEnvelope` to OpenClaw request.
- Preserve session policy.
- Return text and route trace.
- Bound timeout and error shape.

Hard validation:

- Echo adapter must be deterministic.
- CLI/RPC adapter must return exactly one assistant text response.
- Adapter errors must be logged and surfaced without losing the turn record.

### 7.3 `xtts-adapter`

Responsibilities:

- Check `/health` or `/docs` availability, if available.
- POST text to `/tts_to_audio/`.
- Store WAV under `data/audio/<turnId>.wav`.
- Return local URL.

Hard validation:

- Works with `voice:false` even if XTTS unavailable.
- Does not call external URLs.
- Fails closed if XTTS URL is non-local without explicit allow.

### 7.4 `stt-adapter`

Phase 1:

- Save `audio/webm` locally.
- Return 501 with explicit `LOCAL_STT_NOT_WIRED`.

Phase 2:

- Add local Whisper/faster-whisper adapter.
- Return transcript + confidence/metadata.
- Log STT model identity/hash.

Hard validation:

- Confirm no browser Web Speech API.
- Confirm no network call to external STT.
- Confirm max audio duration/size enforced.

### 7.5 `turn-ledger`

Responsibilities:

- Own canonical turn schema.
- Assign UUID.
- Hash large text/audio references.
- Emit state transitions:
  - `TURN_ACCEPTED`
  - `STT_CAPTURED`
  - `TRANSCRIPT_READY`
  - `OPENCLAW_RESPONSE_READY`
  - `TTS_AUDIO_READY`
  - `MEMORY_WRITTEN`
  - `CONTEXT_BRIDGE_WRITTEN`
  - `TURN_COMPLETE`
  - `TURN_FAILED`

### 7.6 `memory/context writers`

Responsibilities:

- Append daily memory concise summaries.
- Write context bridge JSON per turn.
- Avoid raw audio/transcript dumps into long-term memory.
- Store artifact paths, hashes, summaries.

Hard validation:

- A successful turn must create both daily memory and context event unless explicitly disabled.
- Readback must parse JSON and verify expected boundaries.

## 8. Milestones and hard pass gates

### M0 — Baseline preservation and current smoke

Status: mostly complete.

Deliverables:

- Scaffold exists.
- Echo-mode smoke passes.
- Memory/context logging proven.
- Implementation plan and LLD written.

Hard PASS gates:

- `node --check server.js` PASS.
- `/health` PASS on non-conflicting port.
- `/api/chat voice=false` PASS.
- Daily memory append present.
- Context bridge event JSON parse PASS.
- Boundaries show no cloud STT/WebSpeech.

Current classification target: `STICKBOT_TARS_M0_BASELINE_PASS`.

### M1 — Runtime host preparation

Deliverables:

- Decide runtime host: Alienware WSL `/home/stickai/stickbot-voice` preferred.
- Install Node on Alienware WSL if Node app runs there.
- Prepare Python venv for XTTS.
- Document GPU state.

Hard PASS gates:

- Alienware WSL path exists and has >20G free.
- Node version >=20 if Node app runs there.
- Python venv created.
- `pip freeze` captured.
- GPU gate either:
  - `GPU_READY`: `nvidia-smi` visible and PyTorch CUDA available; or
  - `CPU_ONLY_ACCEPTED`: explicit owner acceptance for slow validation.

Classification: `STICKBOT_TARS_M1_RUNTIME_HOST_READY` or `...CPU_ONLY_ACCEPTED`.

### M1.5 — NOA bridge pattern review

Status: **complete / pattern-only reuse** based on the 2026-07-01 NOA assessment and repair manual.

Deliverables:

- Locate NOA bridge files/notebooks/manuals.
- Extract reusable patterns only.
- Decide `reuse | adapt | no-reuse-pattern-only`.

Decision:

- `no-reuse-pattern-only` for the first TARS demo.
- Reuse architectural patterns, not code.
- Do not depend on NOA/unified-brain as answer source while provider quota/routing returns `REASONER_FAILED:429`, unless a later adapter proves it avoids exhausted OpenAI API quota.

Hard PASS gates:

- Files located or search documented as no-hit: PASS via `projects/noa-bridge-v1/NOA_TROUBLESHOOTING_AND_REPAIR_MANUAL.md` and NOA project files.
- No code copied without review: PASS.
- At least one explicit finding for routing/logging substrate: PASS — use health gates, envelopes, event ledgers, service ownership.
- No runtime mutation: PASS for documentation-only plan update.

Classification: `STICKBOT_TARS_M15_NOA_BRIDGE_PATTERN_REVIEW_PASS_PATTERN_ONLY`.

### M2 — Modular refactor

Deliverables:

- Split current `server.js` into `src/` modules.
- Add typed-ish schemas via JSDoc or lightweight validation.
- Add trace JSONL writer.

Hard PASS gates:

- `npm run check` PASS.
- Echo smoke PASS.
- Trace JSONL parse PASS.
- Memory/context readback PASS.
- No behavior regression from M0.

Classification: `STICKBOT_TARS_M2_MODULAR_NODE_SUBSTRATE_PASS`.

### M2.5 — Security and test harness

Deliverables:

- Unsafe-config tests.
- Path traversal tests for `/audio/:file` and artifact routes.
- CORS/origin/CSRF tests.
- Port conflict tests.
- JSON schema/body-limit parse tests.
- Audio upload size/duration rejection tests.
- Browser-visible redaction tests for provider keys, OpenClaw tokens, local secret paths, and raw traces.

Hard PASS gates:

- No wildcard CORS.
- Browser POSTs require a valid CSRF/session nonce or equivalent local UI guard.
- JSON body limits enforced.
- Audio byte/duration limits enforced.
- `/audio/:file` serves only UUID-named files from the controlled audio directory.
- Browser never receives provider keys, OpenClaw tokens, secret-bearing local file paths, or raw traces.

Classification: `STICKBOT_TARS_M25_SECURITY_TEST_HARNESS_PASS`.

### M3 — TARS model acquisition and safety scan

Deliverables:

- Download exact Hugging Face files:
  - `config.json`
  - `vocab.json`
  - `model.pth`
  - `speakers_xtts.pth`
  - `reference.wav`
- Store under WSL-native path.
- Record SHA256 manifest.

Hard PASS gates:

- All expected files present.
- SHA256 manifest written.
- File sizes match expected order of magnitude.
- No model load yet in this milestone.
- Download location is not `/mnt/c`.

Classification: `STICKBOT_TARS_M3_MODEL_ACQUIRED_HASHED_NO_LOAD_PASS`.

### M4 — Sandboxed XTTS load

Deliverables:

- Install `xtts-api-server` or minimal Coqui XTTS runtime in venv/container.
- Load model with outbound network blocked after dependencies are installed.
- Bind XTTS to `127.0.0.1` only.

Hard PASS gates:

- XTTS process starts with `--model-source local` and `--version tars`.
- No external network connection observed during first load/generation after block.
- First test generation produces WAV.
- Process logs captured.
- Failure does not affect Gateway/OpenClaw service.

Classification: `STICKBOT_TARS_M4_SANDBOXED_XTTS_LOCAL_LOAD_PASS`.

### M5 — Node ↔ XTTS voice integration

Deliverables:

- Configure `XTTS_URL`.
- `POST /api/chat` with `voice:true` returns `audioUrl`.
- Browser plays WAV.

Hard PASS gates:

- `/api/chat voice=false` still PASS.
- `/api/chat voice=true` returns WAV.
- WAV file exists and is non-empty.
- Audio endpoint returns `audio/wav`.
- Memory/context event includes output audio path.
- XTTS endpoint remains loopback unless explicitly allowed.

Classification: `STICKBOT_TARS_M5_TEXT_TO_TARS_VOICE_PASS`.

### M6 — OpenClaw adapter integration

Deliverables:

- Confirm stable OpenClaw invocation path: CLI or Gateway API/RPC.
- Replace echo with controlled OpenClaw adapter.
- Preserve route/session policy and logs.
- Add optional NOA health-awareness fields to traces, but do not route through NOA by default.

Hard PASS gates:

- One text turn reaches Stickbot/OpenClaw and returns assistant text.
- No direct provider call from browser/Android.
- No model route/default/fallback config mutation.
- Context event includes adapter, session policy, route mutation false.
- Error handling writes failed turn event if OpenClaw call fails.
- TARS remains on `18788` or another non-conflicting port; it must not bind `8787`.
- If any NOA/unified-brain adapter is evaluated, provider-quality status must be explicit; current `REASONER_FAILED:429` blocks using it as the primary answer source unless the adapter avoids exhausted OpenAI API quota.

Classification: `STICKBOT_TARS_M6_OPENCLAW_ADAPTER_PASS`.

### M7 — Local STT integration

Deliverables:

- Wire mic capture to local STT.
- Convert transcript into `/api/chat` turn.
- Add transcript confidence/metadata to trace.

Hard PASS gates:

- Mic capture does not use Web Speech API.
- Local STT returns transcript from sample audio.
- No outbound STT network calls.
- Audio size/duration limits enforced.
- Transcript turn reaches OpenClaw adapter and returns voice.

Classification: `STICKBOT_TARS_M7_LOCAL_STT_PASS`.

### M8 — Android-ready interface

Deliverables:

- Stabilize API contracts for Android client.
- Add auth token or local pairing guard if exposed beyond localhost.
- Add CORS/CSRF posture appropriate for LAN or local app.

Hard PASS gates:

- OpenAPI-ish contract documented.
- Android can use same `/api/turn` or `/api/chat` flow.
- No secrets in Android client.
- LAN exposure requires explicit allow + firewall notes.

Classification: `STICKBOT_TARS_M8_ANDROID_READY_API_PASS`.

### M9 — Mesh-aware promotion packet

Deliverables:

- Promote demo from smoke to reusable local substrate.
- Write docs, memory, context event, validation summary.

Hard PASS gates:

- All prior gates PASS or explicitly waived.
- DR/runbook exists.
- Known limitations documented.
- No unsafe external speech calls.
- Other chat surfaces have a context-bridge-visible summary.

Classification: `STICKBOT_TARS_M9_SUBSTRATE_PROMOTION_READY`.

## 9. Operational logging and observability

### Required per-turn trace fields

```json
{
  "traceId": "uuid",
  "turnId": "uuid",
  "timestamp": "ISO",
  "surface": "web-smoke",
  "inputMode": "text|audio",
  "stt": { "adapter": "placeholder|whisper", "status": "skipped|pass|fail" },
  "openclaw": { "adapter": "echo|cli|rpc", "status": "pass|fail", "latencyMs": 0 },
  "tts": { "adapter": "xtts", "status": "skipped|pass|fail", "latencyMs": 0, "audioPath": null },
  "memory": { "dailyPath": "memory/YYYY-MM-DD.md", "status": "pass|fail" },
  "contextBridge": { "eventPath": "memory/context-bridge-events/...json", "status": "pass|fail" },
  "boundaries": {
    "externalCloudSpeechRecognition": false,
    "providerDirectFromClient": false,
    "routeMutation": false
  }
}
```

### Log levels

- `INFO`: turn lifecycle.
- `WARN`: XTTS unavailable, STT unavailable, OpenClaw fallback to echo.
- `ERROR`: failed turn, failed memory/context write.
- `SECURITY`: non-loopback endpoint, unexpected external URL, oversized audio, unsafe config refusal.

## 10. Failure handling

- If STT fails: save audio artifact, return readable error, write failed event.
- If OpenClaw fails: do not synthesize; write failed event with adapter error summary.
- If XTTS fails: return text response and `audioError`; write event as `PASS_WITH_VOICE_FAILURE`.
- If memory write fails: return response but status `PASS_WITH_LOGGING_FAILURE`; write trace if possible.
- If context bridge write fails: do not claim cross-surface awareness.
- If port is occupied: fail with explicit `EADDRINUSE`, suggest free port; do not curl unknown service.

## 11. Security checklist

- [ ] Loopback-only by default.
- [ ] Explicit opt-in for LAN exposure.
- [ ] No browser Web Speech API.
- [ ] No Google STT.
- [ ] No provider keys in browser/Android.
- [ ] `.pth` model load only in sandbox/venv/container.
- [ ] SHA256 manifest for model files.
- [ ] Trace logs avoid full secrets and avoid raw long transcripts by default.
- [ ] Audio files stored under controlled app data dir.
- [ ] Path traversal blocked for audio retrieval.
- [ ] Max request body/audio duration enforced.

## 12. Immediate next implementation steps

1. M1 path/host/runtime verification first: lock Alienware vs Inspiron and canonical paths before Codex/refactor work.
2. M2 modular refactor.
3. M2.5 security/test harness: unsafe config tests, path traversal tests, CORS/origin/CSRF tests, port conflict tests, JSON schema/body-limit parse tests, audio limit tests, and browser redaction tests.
4. M3 model provenance/license/hash only; no model load.
5. M4 sandboxed XTTS load with low-privilege boundary, no secrets, read-only model mount, output-only audio dir, and blocked egress.
6. M5 voice with echo.
7. M6 OpenClaw adapter.
8. M7 local STT.
9. M8 Android/LAN gate.
10. M9 promotion packet only after cleanup/runbook and observer gates pass.

## 13. Acceptance bar for demo v1

Demo v1 is acceptable only when:

- Text request reaches Stickbot/OpenClaw through a safe adapter.
- Response text is shown in the UI.
- Response voice is generated locally by TARS XTTS.
- Mic path either works through local STT or is explicitly labelled as capture-only.
- Daily memory and Context Bridge both record the turn.
- Trace logs let us debug every stage.
- No external speech calls occur.
- No OpenClaw production routing/config mutation occurs.
- The design remains modular enough to replace browser UI with Android without rewriting the core voice substrate.

## 14. Hardening Addendum — Required Before M3/M4/M6

This addendum is a hard gate, not optional polish. The existing plan stays intact, but M3/M4/M6 cannot pass until the relevant hardening gates below are satisfied or explicitly waived by Stick with a recorded reason.

### 14.1 Untrusted model boundary

Treat all downloaded model artifacts, especially `.pth` files, as untrusted until loaded inside a constrained runtime. SHA256 proves consistency only; it does not prove safety.

Hard requirements before M4:

- Do not load model files in the production OpenClaw Gateway process.
- Do not load model files in a shell/session that has access to OpenClaw provider secrets, Codex secrets, SSH keys, Gmail credentials, Telegram tokens, or production runtime configuration.
- Do not load model files in any process that has access to OpenClaw secrets, `~/.openclaw`, `~/.ssh`, `~/.codex`, provider keys, project secret directories, Gateway config/state, or production Gateway files.
- Prefer a container, separate WSL distro, or dedicated low-privilege Linux user for XTTS.
- Use a low-privilege runtime boundary for first load/generation: dedicated Unix user, container, separate WSL distro, VM, or equivalent constrained process.
- Mount model files read-only during load/generation.
- Mount only a narrow output directory for generated audio.
- Provide an output-only audio directory with no write access back into model/source/config directories.
- Do not mount `~/.openclaw`, `~/.ssh`, `~/.codex`, project secret directories, or Gateway config into the XTTS runtime.
- Block outbound egress during model load and generation after dependencies/model files are already present.
- Block outbound network after dependency installation and before first model load/generation.
- Bind XTTS only to `127.0.0.1` unless a later LAN/mobile exposure gate explicitly approves otherwise.
- Record the exact boundary used: user/container/distro id, mounted paths, read/write permissions, egress-block method, process command, environment allowlist, package versions, model manifest, and first-generation logs.

M4 cannot pass if the model runtime can read production credentials or write outside its approved output/cache paths. M4 is not PASS unless the XTTS load is isolated from production OpenClaw state and the first generation succeeds without network egress.

### 14.2 Model provenance, license, and voice rights gate

M3 must be a provenance milestone, not just a download/hash milestone.

M3 must produce a provenance manifest before any model load.

Required manifest shape:

```json
{
  "modelName": "Pyrater/TARS or resolved model id",
  "source": "Hugging Face or local source",
  "revision": "commit sha / tag / exact snapshot",
  "downloadedAt": "ISO timestamp",
  "files": {
    "config.json": { "sha256": "...", "bytes": 0 },
    "vocab.json": { "sha256": "...", "bytes": 0 },
    "model.pth": { "sha256": "...", "bytes": 0 },
    "speakers_xtts.pth": { "sha256": "...", "bytes": 0 },
    "reference.wav": { "sha256": "...", "bytes": 0 }
  },
  "license": {
    "name": "resolved license name",
    "commercialUseAllowed": false,
    "notes": "demo/private-only unless separately cleared"
  },
  "voiceUse": {
    "publicProductSafe": false,
    "requiresBrandingRemoval": true,
    "requiresVoiceRightsReview": true
  }
}
```

Hard requirements before M3 PASS:

- Record source URL/repo, model filename list, download timestamp, and exact revision/commit/etag where available.
- Record license for every model/runtime component, including XTTS/Coqui-derived weights and server wrapper.
- Record allowed usage: private demo, internal testing, commercial use, redistribution, output restrictions, attribution, and model-card caveats.
- If the active model/license is non-commercial, classify the TARS demo as `PRIVATE_NONCOMMERCIAL_DEMO_ONLY` until replaced or legal review clears broader use.
- Store license/provenance in a local manifest adjacent to the SHA256 manifest.
- Do not public-brand, redistribute, or customer-demo the voice/model path until license status permits that use.
- If the model or generated output is non-commercial/demo-only, label the whole voice path as private demo only.
- Do not promote a non-commercial/demo-only voice path into an Altoura/customer/product surface.
- Track voice rights separately from model license: TARS/Interstellar-style voice use requires branding/removal and voice-rights review before any public/product/customer use.

M3 classification should become `STICKBOT_TARS_M3_MODEL_ACQUIRED_HASHED_PROVENANCE_RECORDED_NO_LOAD_PASS`.

### 14.3 Verified path and host policy

All implementation steps must use validated paths only.

Hard requirements:

- Use WSL-native project/runtime paths.
- Avoid `/mnt/c` for model files, venvs, node modules, generated audio, and traces.
- Do not invent Windows, WSL, or fake mounted drive paths.
- Before reading, writing, deleting, or moving files, commands must `pwd`, `realpath`, and `test -e` / `stat` the target.
- Codex must not create fake mount roots or translate paths into `C:\mnt\...`, `/mnt/c/mnt/...`, or other hybrid paths.
- Record the canonical project root and runtime root in `state/stickbot-tars-paths.json`; the initial artifact exists with status `PLANNED_UNVERIFIED` and must be verified before M1/M2 PASS.
- Record canonical paths for repo path, runtime root, model path, audio path, trace path, daily memory path, and Context Bridge events path.

M1/M2 are not PASS unless the runtime path, repo path, audio path, model path, and memory/context paths are all verified.

### 14.3A XTTS adapter discovery gate

Do not assume a specific XTTS API shape until the selected server/version is probed.

Hard requirements before Node depends on XTTS:

- Probe `GET /docs`, `GET /openapi.json`, or equivalent server metadata when available.
- Record the selected server package/version and launch flags.
- Store a sample request and response contract for the actual endpoint used.
- Run one known-good minimal local request outside the Node app first.
- Capture response content type, output path/bytes behavior, error shape, timeout behavior, and whether the API returns bytes, path, JSON, or stream.
- Keep a contract fixture under docs or test fixtures before wiring the Node adapter.

M5 cannot pass until the XTTS contract fixture exists and the Node adapter matches it.

### 14.4 OpenClaw adapter command discipline

The OpenClaw adapter is a privileged integration boundary. `OPENCLAW_ARGS_JSON` is a conceptual adapter template, not permission to use shell interpolation.

Hard requirements before M6 CLI adapter PASS:

- Prefer a documented Gateway/RPC adapter over CLI if available.
- Use `spawn(file, args, { shell: false })` or equivalent. Never use `exec`, shell strings, or `sh -c` for user-controlled prompt text.
- Use `shell: false`.
- Treat the executable name as a fixed allowlisted value, not user-configurable free text.
- Treat arguments as a fixed allowlisted template with explicit placeholders only.
- Pass prompt text through stdin or a temporary request file, not by interpolating untrusted text into a shell command.
- Enforce max prompt length.
- If a temp file is used, create it under a controlled private dir, set restrictive permissions, and delete it after completion.
- Whitelist environment variables; do not inherit secrets accidentally.
- Set timeout and max stdout/stderr capture sizes.
- Kill the full process tree on timeout/cancel.
- Capture stdout, stderr, exit code, signal, duration, bounded output summaries, and adapter classification.
- Confirm exactly one assistant response.
- Snapshot relevant OpenClaw routing/config state before and after the turn.
- Fail the gate if model route/default/fallback/config mutation is detected.
- Never allow arbitrary command templates from browser/Android/client input.

M6 cannot pass if prompt text can alter command structure. M6 is not PASS unless a failed OpenClaw call still writes a failed turn event and does not synthesize misleading voice output.

### 14.5 Localhost web security and future LAN gate

Loopback-only is necessary but not sufficient; malicious web pages can attempt localhost requests.

Hard requirements before M2.5/M5/M6 browser use beyond trivial smoke:

- Bind `127.0.0.1` by default.
- Disable wildcard CORS.
- Reject unexpected `Origin` and `Host` headers.
- Use same-origin checks for browser UI requests.
- Use a simple CSRF/session nonce or equivalent local UI guard for browser POST requests.
- Enforce JSON body limits.
- Enforce audio upload byte and duration limits.
- Add path traversal tests for `/audio/:file` and any artifact download route.
- Serve only UUID-named audio files from the controlled audio directory.
- Do not expose provider keys, OpenClaw tokens, file paths containing secrets, or raw traces to the browser.
- Set conservative response headers where practical.

Future LAN exposure requires a separate gate:

- Explicit `VOICE_DEMO_ALLOW_LAN=true`.
- Pairing token or local auth token.
- Firewall/portproxy notes.
- Android secret-free client validation.
- CORS restricted to expected origins.
- HTTPS or native Android mic path if browser mic capture is blocked on non-secure LAN origins.

M2.5 cannot pass if browser-visible endpoints leak secrets, serve arbitrary paths, accept cross-origin POSTs without a nonce, or expose wildcard CORS.

### 14.6 STT/audio conversion gate

Browser `MediaRecorder` commonly emits `audio/webm` with Opus. Local STT runtimes may need WAV/PCM or ffmpeg conversion.

The STT milestone must include audio format normalization.

Required path:

1. Browser captures with `MediaRecorder` only.
2. Server stores upload under controlled `data/audio/input/`.
3. Server verifies MIME type and size before conversion.
4. Server converts to normalized local audio before STT:
   - mono;
   - 16 kHz;
   - WAV/PCM;
   - bounded duration.
5. Local STT reads normalized audio.
6. Transcript, confidence, model identity, duration, and conversion metadata are written to trace.
7. Raw audio is not written into daily memory or Context Bridge.

Hard requirements before M7 PASS:

- Detect and record input MIME/container/codec where possible.
- Enforce max duration and max bytes before conversion.
- Normalize audio to STT-compatible format, initially mono 16 kHz PCM WAV unless the selected STT adapter requires otherwise.
- Use ffmpeg or equivalent with an allowlisted command shape; no shell interpolation.
- Record conversion command, input/output hashes, duration, sample rate, channel count, and byte size in trace logs.
- Optionally add VAD/trim later, but do not hide trimmed/discarded segments without trace metadata.
- Document Android browser/native differences, including MediaRecorder MIME support and secure-context requirements.
- Prove STT from both a saved fixture and a fresh browser-recorded sample.

M7 is not PASS unless STT works from a saved fixture and a fresh browser-recorded sample. M7 cannot pass if audio conversion is implicit or unbounded.

### 14.7 Queueing, readiness, and degraded modes

XTTS can be slow or unavailable; the voice substrate must not collapse the text path.

Required runtime behavior:

- Add bounded concurrency for TTS generation.
- Default to one TTS job at a time unless GPU validation proves safe parallelism.
- Add timeout per stage: STT, OpenClaw, TTS, memory write, and context write.
- Separate `/health` from `/ready`.
- `/health` reports process liveness and config.
- `/ready` reports adapter readiness and degraded dependencies.
- Return text even if TTS fails.
- Use explicit statuses:
  - `TURN_COMPLETE`
  - `TEXT_READY_VOICE_PENDING`
  - `PASS_WITH_VOICE_FAILURE`
  - `PASS_WITH_LOGGING_FAILURE`
  - `TURN_FAILED`
  - `BLOCKED_UNSAFE_CONFIG`
  - `STT_CAPTURE_ONLY`
  - `READY_TEXT_ONLY`
- Support cancellation/timeout and clean process/output cleanup.
- Expose readiness state in traces and UI so Stick can tell whether failure is STT, OpenClaw, XTTS, logging, or playback.

M5/M6 are not PASS unless voice failure leaves the text response intact and logs the degraded state.

### 14.8 Data retention and cleanup

Voice audio is more sensitive than ordinary logs.

Voice artifacts are local operational artifacts, not long-term memory.

Hard requirements:

- No raw audio in Context Bridge.
- No raw audio committed to git.
- Add `.gitignore` rules for generated audio, uploaded audio, traces if traces may contain sensitive text, venvs, downloaded models, and local manifests containing machine paths.
- Store raw/captured/generated audio only under controlled local app data dirs.
- Store only summaries and hashes in daily memory and Context Bridge.
- Do not store raw transcripts by default in long-term memory.
- Define retention windows for captured mic audio, generated TTS audio, traces, and temp conversion files.
- Add cleanup command/script: `scripts/cleanup-local-artifacts.sh`.
  - delete generated audio older than N days;
  - delete uploaded mic audio older than N days;
  - compact or archive traces older than N days.
- Daily memory should store compact summaries and artifact references only, not raw transcripts by default.
- If transcript hashes are used for sensitive phrases, prefer HMAC-SHA256 with a local secret over plain SHA256 to reduce offline guessing risk.
- Do not claim cross-surface awareness if Context Bridge write fails.
- Do not claim durable memory if daily memory write fails.

M9 is not PASS unless a cleanup/runbook path exists.

### 14.9 First-run TARS observer, quarantine, and 48-hour trust gate

The first TARS model load/generation is not trusted merely because it runs. It needs an observer that watches for suspicious behavior.

Required observer coverage for first load and first 48 hours of demo operation:

- Watch outbound network attempts. Any unexpected internet call during load/generation is suspicious.
- Watch file access/write attempts outside approved model, cache, temp, and output directories.
- Watch attempts to read secrets or sensitive paths, including `~/.ssh`, `~/.openclaw`, Codex config, provider key stores, Gateway config/state, and unrelated project files.
- Watch process spawning beyond the expected XTTS/runtime command tree.
- Watch unusual resource consumption: runaway CPU/GPU/RAM/disk, huge temp files, repeated crashes, or queue growth.
- Log observations to a local observer trace with timestamps, process ids, command line, network/file/process/resource events, and classification.

Quarantine rule:

- If suspicious behavior is detected, stop the XTTS process, block the model path from further loads, preserve logs/artifacts for review, and classify the model/runtime as `TARS_MODEL_QUARANTINED_PENDING_REVIEW`.
- Do not retry by relaxing boundaries.
- Do not copy quarantined artifacts into OpenClaw/Gateway directories.
- Do not treat generated output as safe evidence if the run is quarantined.

Trust promotion rule:

- If the model runs cleanly in the constrained demo boundary for 48 hours with no suspicious network, file, process, or resource behavior, it may be classified as `TARS_MODEL_DEMO_TRUSTED_48H_CLEAN` for that exact model revision/runtime/boundary only.
- Any model file, runtime version, launch flag, boundary, or host change resets the 48-hour trust clock.

M4 can pass for initial sandboxed generation before 48 hours, but M9 cannot pass until the observer/runbook path exists and either the 48-hour clean trust gate passes or the remaining trust limitation is explicitly documented.

### 14.10 Updated milestone dependencies

- M1 must lock host/path/runtime first: Alienware vs Inspiron, canonical paths, Node/Python/GPU state.
- M2.5 must pass before model acquisition/load work proceeds beyond planning.
- M3 now requires provenance/license manifest + SHA256 manifest + no model load.
- M4 now requires constrained model runtime + no-egress generation proof.
- M5 now requires XTTS API contract fixture + web security + retention gates for generated audio.
- M6 now requires command-injection-hardened adapter or RPC adapter with equivalent boundaries.
- M7 now requires bounded audio conversion/normalization + retention rules for captured audio.
- M8 now requires token pairing/secure-context notes for LAN/mobile use.
