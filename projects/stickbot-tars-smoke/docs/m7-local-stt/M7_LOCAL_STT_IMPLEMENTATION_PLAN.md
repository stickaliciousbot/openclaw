# M7 Local STT Implementation Plan

Status: `IN_PROGRESS_FIXTURE_CONTRACT_IMPLEMENTED_REAL_ENGINE_BLOCKED`

Generated: 2026-07-02 20:17 AEST / 2026-07-02T10:17:00Z

## Approval

Stick approved M7 on 2026-07-02 after M6 OpenClaw adapter fixture voice smoke was pushed.

## Discovery result

Local STT discovery command/session:

- `21ac704a` / `young-crustacean`

Findings:

- `ffmpeg`: missing.
- `ffprobe`: missing.
- `whisper-cli`: missing.
- `whisper-cpp`: missing.
- `whisper`: missing.
- `whisperx`: missing.
- `faster-whisper`: missing.
- Python packages in system Python: `faster_whisper`, `whisper`, `torch`, `torchaudio`, `soundfile` all missing.
- No local STT model directories found:
  - `/home/stickai/stickbot-voice/stt_models` missing.
  - `/home/stickai/.cache/whisper` missing.
  - `/home/stickai/.cache/huggingface` missing.

Conclusion: real local transcription is blocked until a local STT engine and model are acquired/installed in a separate approved milestone. No cloud STT or model download should occur inside M7 fixture work.

## M7 safe progress path

Implement the local STT adapter contract and `/api/stt` integration with fixture mode first:

- `STT_MODE=capture` — default current behavior: save audio locally and return 501 capture-only.
- `STT_MODE=fixture` — return configured `STT_FIXTURE_TEXT` without spawning or cloud calls.
- `STT_MODE=cli` — future local CLI engine mode with safe spawn and `{file}` placeholder.

This lets us validate browser/server STT plumbing, CSRF, upload limits, local capture, response shape, UI transcript insertion, and fail-closed adapter behavior before acquiring a real local engine.

## Explicit non-scope

M7 fixture contract does **not** include:

- cloud speech APIs;
- browser Web Speech API;
- OpenAI Whisper API;
- model download;
- package install;
- ffmpeg install;
- real whisper/faster-whisper transcription;
- Android;
- LAN/Tailscale exposure;
- Gateway/NOA mutation;
- persistent service install.

## Implementation files

- `src/stt-adapter.js` — safe STT adapter contract.
- `test/stt-adapter.test.mjs` — fixture/CLI parser/fail-closed tests.
- `server.js` — `/api/stt` now calls fixture/CLI STT modes or preserves capture-only behavior.
- `public/app.js` — mic upload fills the text box when a transcript is returned.
- `scripts/m7-sandboxed-stt-fixture-smoke.sh` — Node-only sandbox smoke for `/api/stt` fixture contract.
- `package.json` — adds `m7:smoke` and includes M7 checks.

## Pass gates for M7 fixture contract

M7 fixture contract can pass if:

1. Static checks pass.
2. Existing safety tests continue to pass.
3. STT adapter tests pass:
   - fixture mode no-spawn;
   - capture mode fails closed;
   - CLI mode requires `{file}`;
   - JSON/plain transcript parsing;
   - shell metacharacters in file path passed as argv with `shell:false`;
   - non-zero exit fails closed;
   - stdout limit fails closed.
4. Sandboxed `/api/stt` fixture smoke passes:
   - private namespace;
   - loopback enabled;
   - external network blocked/unavailable;
   - secret dirs hidden;
   - Node `/api/stt` returns HTTP 200 with transcript;
   - captured audio is stored under project-local sandbox data dir;
   - no cloud/browser speech API.

## Future real-STT milestone

A later approved milestone should choose and acquire one local engine path:

- install/provision `ffmpeg` for webm/opus normalization; and
- either `whisper.cpp` with a local `.bin`/`.gguf` model or `faster-whisper` with local model files.

That milestone must include model provenance, hashes, local-only/offline validation, and no cloud STT.
