# Stickbot-TARS Local Voice Project

Stickbot-TARS is a local-first voice/audio proving ground for giving Stickbot a TARS-like browser voice loop without mutating OpenClaw production routing.

The project currently includes:

- browser text + microphone UI,
- local whisper.cpp speech-to-text (STT),
- local XTTS voice generation using the private-demo TARS voice model,
- deterministic prosody scoring and mood/tuning controls,
- chunked synthesis,
- DSP polish and voice-body mastering,
- realtime streaming-frame playback,
- low-latency browser transport telemetry,
- full-duplex / barge-in control,
- deterministic rehydration packets for future sessions.

Latest confirmed milestone at the time of this README:

```text
STICKBOT_TARS_M7R_LOW_LATENCY_STREAMING_TRANSPORT_LIVE_PASS
```

Next milestone:

```text
M7S_LIVE_BARGE_IN_WITH_REAL_SPEECH
```

---

## Quick start for future Stickbot sessions

From the project root:

```bash
cd /home/stickai/.openclaw/workspace/projects/stickbot-tars-smoke
npm run rehydrate:tars -- --status
```

Then read:

```text
artifacts/rehydration/stickbot-tars/latest.md
```

The rehydration packet is the fastest way to recover the live project state, paths, guardrails, milestone chain, source inventory, and next actions after context compaction.

---

## Project locations

### Repository project root

```text
/home/stickai/.openclaw/workspace/projects/stickbot-tars-smoke
```

Workspace-relative path:

```text
projects/stickbot-tars-smoke
```

### Runtime root

```text
/home/stickai/stickbot-voice
```

This is where local runtime-heavy assets live: XTTS model files, speaker reference audio, STT models/tools, FFmpeg binaries, generated audio, HTTPS certificates, and virtual environments.

### Git branch / remote

```text
branch: feature/stickbot-tars-m25-hardening-repair
remote: https://github.com/stickaliciousbot/webworkspace.git
```

---

## Live demo URLs

Browser URL for Stick:

```text
https://192.168.1.107:19890/
```

Loopback URL:

```text
https://127.0.0.1:19890/
```

XTTS loopback:

```text
http://127.0.0.1:8020
```

Health checks:

```bash
curl -k -fsS https://127.0.0.1:19890/health
curl -k -fsS https://192.168.1.107:19890/health
curl -fsS http://127.0.0.1:8020/ready
```

The current browser build should serve:

```text
/app.js?v=m7r-low-latency-transport
```

---

## Core guardrails

These are project invariants unless Stick explicitly approves a boundary change:

- Do **not** mutate OpenClaw Gateway config, production routing, defaults, fallbacks, NOA, Android, or provider settings.
- Do **not** use port `8787`; it is reserved for NOA bridge work.
- Do **not** use cloud STT by default.
- Do **not** use browser Web Speech API.
- Do **not** durably store raw mic transcripts; public/controller summaries should use hashes/counts where possible.
- Do **not** put runtime/model/audio/venv/cache assets under `/mnt/c`.
- Do **not** commit generated audio, model files, virtualenvs, caches, private keys, certificate private keys, or runtime output directories.
- Canonical assistant text is authoritative; prosody, DSP, mastering, mood, and audio polish must not rewrite response text.
- TARS voice/branding remains private-demo-only until rights/branding review.

---

## What the system does

### Browser UI

Files:

```text
public/index.html
public/app.js
```

The browser UI provides:

- text input,
- optional TARS voice generation,
- microphone capture using `MediaRecorder`,
- local partial STT display,
- final STT transcript reconstruction,
- prosody/mood/tuning controls,
- streaming chunk playback,
- playback telemetry,
- barge-in by starting mic capture while audio is playing.

### Local STT

Main files:

```text
src/stt-adapter.js
src/audio-normalizer.js
src/audio/partial-stt-loop.js
```

Runtime resources:

```text
whisper binary: /home/stickai/stickbot-voice/tools/whisper.cpp/v1.9.1-ubuntu-x64/extract/whisper-bin-ubuntu-x64/whisper-cli
whisper model:  /home/stickai/stickbot-voice/stt_models/whisper.cpp/ggml-small.en.bin
ffmpeg:         /home/stickai/stickbot-voice/tools/ffmpeg-static/johnvansickle-ffmpeg-release-amd64-static/extract/ffmpeg
ffprobe:        /home/stickai/stickbot-voice/tools/ffmpeg-static/johnvansickle-ffmpeg-release-amd64-static/extract/ffprobe
```

Critical live STT environment detail:

```json
["-m", "/home/stickai/stickbot-voice/stt_models/whisper.cpp/ggml-small.en.bin", "-f", "{file}", "-nt", "-np", "-l", "en"]
```

`STT_ARGS_JSON` must contain `{file}`. If it is missing, STT fails closed with:

```text
STT args must include a {file} placeholder
```

Do not manually reconstruct the STT environment from memory. Prefer the demo script or copy the full known-good environment.

### Local XTTS voice generation

Main files:

```text
scripts/xtts-local-server.py
scripts/m7e-start-xtts-loopback.sh
server.js
```

Runtime resources:

```text
model:     /home/stickai/stickbot-voice/xtts_models/tars
speaker:   /home/stickai/stickbot-voice/speakers/reference.wav
XTTS URL:  http://127.0.0.1:8020
```

The browser/node app talks to the local XTTS loopback server. XTTS must stay loopback-only behind the Node/browser demo.

### Prosody, chunking, DSP, mastering

Important modules:

```text
src/voice/tars-prosody-kernel.js
src/voice/tars-prosody-matrix.js
src/prosody/prosody-score-engine.js
src/audio/xtts-chunk-conductor.js
src/audio/dsp-polish-stage.js
src/audio/voice-body-mastering-stage.js
src/audio/wav-stitcher.js
```

Current audio path:

1. canonical assistant text is scored into chunks,
2. chunks receive prosody/mood/XTTS metadata,
3. each chunk is synthesized locally,
4. DSP polish is applied,
5. voice-body mastering is applied,
6. chunks are stitched to a final WAV,
7. realtime frame manifest exposes chunk frames for browser streaming,
8. browser plays the low-latency queue and retains final WAV as fallback.

### Streaming transport and barge-in

Important modules:

```text
src/audio/streaming-frame-interface.js
src/audio/full-duplex-turn-controller.js
src/audio/duplex-event-ingress.js
public/app.js
```

M7R live PASS evidence:

```text
Streaming telemetry: first play 267ms; max gap 255ms; played 2/2
STICKBOT_TARS_M7R_LOW_LATENCY_CLIENT_TELEMETRY; local-only, no transcript/audio cloud path.
```

The browser uses:

```text
browser_preload_queue_then_serial_playback
```

Barge-in works by stopping active playback when mic capture starts, then returning the duplex state to local listening.

---

## Rehydrator: where it is and how to use it

### Script path

Local path:

```text
/home/stickai/.openclaw/workspace/projects/stickbot-tars-smoke/scripts/stickbot-tars-rehydrate.mjs
```

Workspace-relative path:

```text
projects/stickbot-tars-smoke/scripts/stickbot-tars-rehydrate.mjs
```

GitHub link:

```text
https://github.com/stickaliciousbot/webworkspace/blob/feature/stickbot-tars-m25-hardening-repair/projects/stickbot-tars-smoke/scripts/stickbot-tars-rehydrate.mjs
```

### NPM command

From this project root:

```bash
npm run rehydrate:tars
```

With local git status:

```bash
npm run rehydrate:tars -- --status
```

Markdown to stdout only:

```bash
npm run rehydrate:tars -- --md --stdout-only
```

JSON to stdout only:

```bash
npm run rehydrate:tars -- --json --stdout-only
```

### Rehydrator outputs

Latest stable outputs:

```text
artifacts/rehydration/stickbot-tars/latest.md
artifacts/rehydration/stickbot-tars/latest.json
```

Timestamped packet outputs:

```text
artifacts/rehydration/stickbot-tars/<timestamp>/stickbot-tars-rehydration.md
artifacts/rehydration/stickbot-tars/<timestamp>/stickbot-tars-rehydration.json
```

### What the rehydrator captures

The deterministic rehydrator records:

- project thesis,
- current classification,
- next recommended milestones,
- branch and remote,
- LAN/loopback/XTTS URLs,
- local runtime paths,
- model/reference/STT/FFmpeg/certificate pointers,
- guardrails,
- proven milestone chain,
- resume commands,
- health-check commands,
- curated source inventory with line counts and SHA256 prefixes,
- runtime path inventory,
- generated-audio pointers for local evidence,
- optional git status when `--status` is used.

It does **not** store credentials or commit generated audio.

### Rehydration rule

At the start of any future Stickbot-TARS work:

1. Run:

   ```bash
   npm run rehydrate:tars -- --status
   ```

2. Read:

   ```text
   artifacts/rehydration/stickbot-tars/latest.md
   ```

3. Open only the source files needed for the immediate task.
4. Run the smallest meaningful validation gate before claiming readiness.

The rehydrator restores context. It does **not** prove the live server is currently ready. Live readiness still requires health checks and feature-specific browser/API proof.

---

## Common commands

### Full validation

```bash
npm run check
```

Latest known full gate after M7R:

```text
85/85 PASS
```

### Generated audio auditor

Audit/stage generated and captured speech-session audio artifacts without deleting anything:

```bash
npm run audit:generated-audio
```

The auditor writes deterministic manifests to:

```text
artifacts/generated-audio-audits/latest.md
artifacts/generated-audio-audits/latest.json
artifacts/generated-audio-audits/<timestamp>/stage-manifest.md
artifacts/generated-audio-audits/<timestamp>/stage-manifest.json
```

Delete mode is intentionally gated and must be requested explicitly:

```bash
npm run audit:generated-audio -- --delete --manifest artifacts/generated-audio-audits/latest.json --confirm-delete
```

Safety gates:

- default mode never deletes files,
- delete mode requires a prior PASS manifest and `--confirm-delete`,
- every file is rechecked by path, size, mtime, SHA256, allowlisted root, and open-process state before unlink,
- git-tracked files are blocked,
- executable dependency references in `server.js`, `package.json`, `public/`, `src/`, `safety/`, and `scripts/` are blocked,
- protected runtime roots such as speaker reference, models, tools, certs, source, tests, and app code are never scan roots,
- docs/evidence references do not make generated audio a live app dependency.

Current no-delete audit gate after script-fixture dependency correction:

```text
STICKBOT_TARS_GENERATED_AUDIO_AUDIT_STAGE_PASS
files scanned: 483
staged for deletion: 482
protected/skipped: 1
staged bytes: 68075006
protected bytes: 95788
protected file: /home/stickai/stickbot-voice/output/m4-first-generation.wav
reason: REFERENCED_BY_EXECUTABLE_SOURCE via M7B/M7C smoke script defaults
```

### Start XTTS loopback

```bash
npm run m7e:xtts:start
```

### Start HTTPS LAN demo

Prefer the script path because it generates the correct STT args:

```bash
HOST=0.0.0.0 \
PORT=19890 \
VOICE_DEMO_ALLOW_LAN=true \
VOICE_DEMO_HTTPS=true \
VOICE_DEMO_HTTPS_KEY=/home/stickai/stickbot-voice/certs/m7d-https/stickbot-tars-m7d-server.key.pem \
VOICE_DEMO_HTTPS_CERT=/home/stickai/stickbot-voice/certs/m7d-https/stickbot-tars-m7d-server.cert.pem \
LOG_DIR=/tmp/tars-live-demo \
bash scripts/m7d-local-real-mic-demo.sh
```

Important: this script runs foreground until Ctrl-C. If run under a bounded exec wrapper, the wrapper can kill the server after timeout. For live testing, keep it in a managed process/session and verify health after the wrapper returns.

### Health checks

```bash
curl -k -fsS https://127.0.0.1:19890/health
curl -k -fsS https://192.168.1.107:19890/health
curl -fsS http://127.0.0.1:8020/ready
```

### Capabilities check

```bash
curl -k -fsS https://127.0.0.1:19890/api/capabilities
```

Expected live capabilities include:

```json
{
  "sttMode": "cli",
  "voice": { "enabled": true },
  "boundaries": {
    "browserWebSpeechApi": false,
    "cloudSpeechApi": false,
    "partialLocalSttLoop": true
  }
}
```

---

## Documentation map

### Core notebooks

```text
IMPLEMENTATION_NOTEBOOK.md
docs/TROUBLESHOOTING_AND_REPAIR_NOTEBOOK.md
docs/LOW_LEVEL_DESIGN_AND_IMPLEMENTATION_PLAN.md
docs/LOOPBACK_LAN_EXPOSURE_NOTEBOOK.md
docs/STICKBOT_TARS_REHYDRATION.md
docs/PRODUCTION_VOICE_STREAM_ARCHITECTURE.md
```

### Current milestone closeouts

```text
docs/m7-local-stt/m56-voice-body-mastering/M56_VOICE_BODY_POSTPROCESS_PASS.md
docs/m7-local-stt/m7q-true-partial-local-stt-loop/M7Q_TRUE_PARTIAL_LOCAL_STT_LOOP_LIVE_PASS.md
docs/m7-local-stt/m7r-low-latency-streaming-transport/M7R_LOW_LATENCY_STREAMING_TRANSPORT_LIVE_PASS.md
```

### Repair lessons

```text
memory/lessons-learned-stickbot-tars-live-dashboard-refresh-2026-07-03.md
memory/lessons-learned-stickbot-tars-m7r-live-transport-repair-2026-07-03.md
```

---

## Proven milestone chain

Current proven chain:

- M3 — model acquired / provenance recorded / no load
- M4 — sandboxed XTTS local load
- M5 — local serverization Node voice pass
- M6 — OpenClaw adapter fixture voice pass
- M7D — HTTPS LAN real mic STT + echo pass
- M7E — audible HTTPS LAN TARS voice output pass
- M7F — prosody kernel local check pass
- M7G — tuning console + JSON/matrix controls + audible XTTS slider mapping pass
- M7H/M55 — prosody score engine pass
- M7I — chunk conductor local pass
- M7J/K/L — DSP + streaming frame + duplex controller local pass
- M7M/N/O — streaming playback hooks + partial ingress + barge-in local pass
- M7P — live browser streaming + barge-in pass
- M5.6 — voice-body/mastering postprocess pass with R2/R3/R4 tail fixes
- M7Q — true partial local STT loop live pass
- M7R — low-latency streaming transport live pass

---

## Known live repair lessons

### PASS_BUILD is not PASS_LIVE

A green `npm run check` does not mean the currently-running browser demo loaded the new code. Always verify the specific endpoint/UI against the live URL.

### Foreground demo READY is not durable readiness

The live demo script can print READY and then be killed by a bounded exec timeout. Always re-check `/health` after the command wrapper returns.

### Preserve `STT_ARGS_JSON`

If restarting `node server.js` manually, include `STT_ARGS_JSON` with `{file}`. Missing this breaks partial and final STT even though audio capture itself works.

### A stuck browser Send can be stale-request failure

If the browser stays on `Sending...`:

1. Do not stack more Send clicks.
2. Check backend `/health` and XTTS `/ready`.
3. Inspect whether only `chunk-001.wav` exists with no final WAV.
4. Check XTTS logs for `BrokenPipeError`.
5. Run a bounded backend voice smoke.
6. If backend passes, use a fresh/hard-refreshed browser tab.
7. If hangs repeat, implement fail-fast UI/backend timeout and recovery.

---

## Git / artifact policy

Commit:

- source code,
- tests,
- docs,
- status JSON when intentionally force-added,
- rehydration packets,
- lessons-learned files when they are durable project knowledge.

Do not commit:

- generated audio,
- `exports/`,
- model files,
- virtual environments,
- caches,
- private keys,
- certificate private keys,
- raw transcript artifacts.

Daily memory is usually local/untracked unless explicitly intended for repo preservation.

---

## Next work

Recommended next milestones:

```text
M7S_LIVE_BARGE_IN_WITH_REAL_SPEECH
LIVE_PROSODY_MOOD_SCORE_AND_EMOTIONAL_SHEET_MUSIC
AUDIO_FIRST_MULTIPLEXED_PRODUCTION_STREAMING_ARCHITECTURE
```

Before closing Stickbot-TARS as done, also prove live-driven prosody: Stickbot should create its own mood score / emotional sheet music / prosody emoji cues while preserving canonical text.

Production direction is audio-first and multiplexed:

- stream generated WAV/PCM frames directly as the live output,
- keep canonical text in a parallel channel for chat, memory, audit, search, and accessibility,
- let break-in/barge-in belong to the audio channel,
- preserve canonical text even when audio is interrupted or superseded.
