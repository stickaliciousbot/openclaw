# Lessons learned — Stickbot-TARS M7R live transport repair

Date: 2026-07-03 AEST

## Trigger

During M7R live browser validation, Stick reported three valuable live failures:

1. Send stuck on `Sending...` with no voice output.
2. Partial/final STT error: `STT args must include a {file} placeholder`.
3. Live demo server readiness messages appeared successful, but bounded foreground execution later killed the process.

These are repair-data assets. Preserve them in implementation notebook, troubleshooting notebook, rehydrator, and memory before declaring M7R live PASS.

## Durable lessons

### 1. Foreground demo READY is not durable server readiness

`scripts/m7d-local-real-mic-demo.sh` runs the live server in the foreground until Ctrl-C. If it is launched under a bounded exec, it can print READY and then be killed by the wrapper timeout.

Rule:

- For live browser testing, either keep the process in an explicit managed background session or launch detached with the exact same environment.
- After the wrapper returns, always re-verify:
  - `https://127.0.0.1:19890/health`
  - `https://192.168.1.107:19890/health`
  - app cache-buster/version
  - `/api/capabilities`

### 2. Never manually reconstruct the STT environment from memory

The M7D/M7Q script generates a required `STT_ARGS_JSON` template for whisper.cpp. `src/stt-adapter.js` intentionally fails closed unless args include `{file}`.

Required arg shape:

```json
["-m", "/home/stickai/stickbot-voice/stt_models/whisper.cpp/ggml-small.en.bin", "-f", "{file}", "-nt", "-np", "-l", "en"]
```

Rule:

- Prefer the script path that generates `STT_ARGS_JSON`.
- If restarting `node server.js` manually, copy the full environment, including `STT_ARGS_JSON`, not just `STT_BIN`/model paths.
- Validate with a real partial STT POST before telling Stick the mic path is fixed.

### 3. A stuck browser Send can be a stale in-flight request, not total backend failure

Observed evidence:

- Browser stayed on `Sending...` for several minutes.
- Backend `/health` and XTTS `/ready` remained green.
- Output directory showed only a first chunk for the stuck turn and no final WAV.
- XTTS log showed `BrokenPipeError` while writing `/tts_to_audio/` response.

Rule:

- Do not tell Stick to keep pressing Send; that can stack jobs.
- Run a bounded backend voice smoke.
- If it passes, the backend is ready and the stale browser request should be abandoned with a fresh/hard-refreshed tab.
- If it fails, restart XTTS/Node cleanly and validate again.

### 4. Add fail-fast UI/back-end hardening before live PASS if hangs repeat

M7R should not accept indefinite `Sending...` as normal behavior.

Recommended follow-up:

- Add browser-side timeout around `/api/chat` with a visible failure/retry state.
- Add server-side turn timing telemetry for chunk generation and final stitch.
- Keep timing logs privacy-safe: hashes/counts/classifications/timing only, no durable raw transcript storage.

## Live functional confirmation

After the STT args repair and backend voice smoke, Stick confirmed the browser flow:

```text
partial STT works, reconstruction works, send works, audio generation works, barge in works.
```

Treat that as `STICKBOT_TARS_M7R_LOW_LATENCY_STREAMING_TRANSPORT_LIVE_FUNCTIONAL_PASS_TELEMETRY_READBACK_PENDING`. Strict final M7R timing PASS still wants a readback/screenshot of the `Streaming telemetry` line with first-play and max-gap values.

## Canonical project notes updated

- `projects/stickbot-tars-smoke/IMPLEMENTATION_NOTEBOOK.md`
- `projects/stickbot-tars-smoke/docs/TROUBLESHOOTING_AND_REPAIR_NOTEBOOK.md`
- `projects/stickbot-tars-smoke/scripts/stickbot-tars-rehydrate.mjs`
- rehydration packet should include this lesson file and the implementation notebook.
