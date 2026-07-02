# M7A/M7B Local STT Engine Plan

Status: `M7A_PASS_M7B_NOT_STARTED`

Generated: 2026-07-02 20:35 AEST / 2026-07-02T10:35:00Z

## Hard boundary

No OpenClaw mutation:

- no OpenClaw production routing/config/default/fallback mutation;
- no Gateway config mutation;
- no Gateway restart;
- no NOA mutation;
- no provider/model API call for STT;
- no cloud STT;
- no browser Web Speech API;
- no Android/LAN/Tailscale exposure;
- no persistent service install unless separately approved.

TARS local runtime constraints remain active:

- Use WSL-native paths only.
- Do not use `/mnt/c` for model files, venvs, `node_modules`, generated/uploaded audio, or traces.
- Keep default host `127.0.0.1`.
- Do not bind `8787`.
- Do not load `.pth` model files in production OpenClaw/Gateway process.
- Do not mount OpenClaw/Codex/Gmail/Telegram/secrets into STT/XTTS runtime.
- Transcript goes to local trace/project response only, not raw durable memory.

## Approved stack direction

Primary local STT substrate:

- Engine: `whisper.cpp`
- Smoke model: `ggml-base.en.bin`
- Usable demo model: `ggml-small.en.bin`
- Normalizer: WSL-local `ffmpeg`

Rejected as primary STT substrate for this track:

- community Ollama Whisper models — weaker provenance and less standard audio-ingestion contract than `whisper.cpp` / `faster-whisper`.

Optional later lanes:

- `faster-whisper` + CTranslate2 if Alienware GPU/CUDA health is confirmed.
- `sherpa-onnx` for future embedded/mobile/native direction.
- Ollama only after transcript exists, for cleanup/intent routing, not primary STT.

## M7A — local audio normalization acquisition gate

Final classification:

`STICKBOT_TARS_M7A_LOCAL_AUDIO_NORMALIZATION_PROVENANCE_PASS`

Purpose:

Browser/mobile microphone formats should normalize through a tightly bounded local command:

```sh
ffmpeg -nostdin -hide_banner -loglevel error \
  -i input.webm \
  -ac 1 -ar 16000 -f wav output.wav
```

M7A pass gates:

1. FFmpeg binary path is WSL-native and not under `/mnt/c`. PASS.
2. `ffmpeg -version` captured. PASS.
3. License/config posture captured from FFmpeg version output. PASS.
4. If a downloaded static binary is used, SHA256 is captured. PASS.
5. If Ubuntu apt package is used for private/dev WSL, package version/status is captured. N/A; apt was unavailable from Telegram runtime due sudo TTY/elevated restrictions.
6. Converts fixture browser-style audio to mono 16 kHz WAV/PCM. PASS.
7. Output WAV is non-empty. PASS.
8. Output audio remains ignored/excluded from git. PASS.
9. No audio/model/cache/venv/runtime artifacts committed. PASS.
10. No OpenClaw/Gateway/NOA mutation. PASS.

M7A evidence:

- Closeout: `m7a-audio-normalization/M7A_LOCAL_AUDIO_NORMALIZATION_PROVENANCE_PASS.md`
- Manifest: `m7a-audio-normalization/evidence_manifest.json`
- FFmpeg: John Van Sickle `7.0.2-static`, GPLv3 private/dev validation posture.
- FFmpeg SHA256: `e7e7fb30477f717e6f55f9180a70386c62677ef8a4d4d1a5d948f4098aa3eb99`.
- FFprobe SHA256: `4f231a1960d83e403d08f7971e271707bec278a9ae18e21b8b5b03186668450d`.
- Normalized fixture WAV SHA256: `38e3b264d99a035f168d6913520d2541a943c6a931e3f896882daf756b66fb7f`, 16000 Hz mono PCM.

Preferred M7A install/source policy:

- Private/dev WSL: Ubuntu `apt install ffmpeg` is acceptable if version/config/package status is recorded.
- Product/distribution later: use stricter FFmpeg LGPL/GPL posture, source/build/license preservation, and preferably LGPL-only static builds where appropriate.

## M7B — whisper.cpp acquisition / STT gate

Target classification:

`STICKBOT_TARS_M7B_WHISPERCPP_LOCAL_STT_FIXTURE_PASS`

M7B pass gates:

1. `whisper.cpp` source/release is pinned.
2. Binary version/hash captured.
3. Model file hash captured.
4. Model path is WSL-native and not under `/mnt/c`.
5. Smoke starts with `ggml-base.en.bin`; usable local demo may use `ggml-small.en.bin`.
6. Fixture WAV transcribes locally.
7. No network is required during transcription.
8. Timeout/body/audio limits still pass.
9. Transcript goes to local trace/response only, not raw durable memory.
10. `/api/stt` contract remains explicit and fail-closed.
11. No OpenClaw/Gateway/NOA mutation.
12. No audio/model/cache/venv/runtime artifacts committed.

## Adapter implications

Existing M7 adapter contract remains the boundary:

- `STT_MODE=capture`: default fail-closed capture-only when no engine is configured.
- `STT_MODE=fixture`: UI/server contract testing only.
- `STT_MODE=cli`: local real-engine path, with:
  - `spawn(file,args,{shell:false})`;
  - required `{file}` placeholder;
  - bounded stdout/stderr;
  - timeout/kill;
  - JSON/plain text transcript parser;
  - non-zero exit fail-closed.

M7A should add a separate bounded normalizer step before STT, without weakening the adapter contract.
