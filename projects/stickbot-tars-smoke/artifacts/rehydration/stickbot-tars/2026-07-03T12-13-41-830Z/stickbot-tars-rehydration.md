# Stickbot-TARS deterministic rehydration packet

Generated: 2026-07-03T12:13:41.830Z
Mode: offline-with-local-git-status

## Thesis

A local-only TARS-like voice/audio stack for Stickbot: browser text+mic UI, local whisper.cpp STT, local XTTS voice generation, deterministic prosody/chunking, DSP/mastering, streaming-frame playback, and barge-in control without mutating OpenClaw production routing.

## Current project state

- Project root: `projects/stickbot-tars-smoke`
- Runtime root: `/home/stickai/stickbot-voice`
- Git branch: `feature/stickbot-tars-m25-hardening-repair`
- Remote: `https://github.com/stickaliciousbot/webworkspace.git`
- LAN URL: `https://192.168.1.107:19890/`
- XTTS URL: `http://127.0.0.1:8020`
- Latest classification: `STICKBOT_TARS_AUDIO_FIRST_MULTIPLEXED_PRODUCTION_STREAMING_ARCHITECTURE_LOCAL_CONTRACT_PASS`
- Live browser milestone: `STICKBOT_TARS_M7P_LIVE_BROWSER_STREAMING_BARGEIN_PASS`

## Guardrails

- Do not mutate OpenClaw Gateway config, production routing/default/fallbacks, NOA, Android, or provider settings for this project unless Stick explicitly authorizes it.
- Do not use port 8787; it is reserved for NOA bridge work.
- Do not use cloud STT by default and do not use browser Web Speech API.
- Do not durably store raw mic transcripts; public/controller summaries use hashes/counts where possible.
- Do not store runtime/model/audio/venv/cache artifacts under /mnt/c paths.
- Do not commit generated audio, model files, venvs, caches, private keys, cert private keys, or runtime output directories.
- Canonical assistant text is authoritative; prosody, DSP, mastering, mood, and audio polish must not rewrite response text.
- TARS voice/branding remains private-demo-only until rights/branding review.

## Resume commands

```bash
npm run rehydrate:tars
npm run rehydrate:tars -- --status
npm run check
npm run m7e:xtts:start
HOST=0.0.0.0 PORT=19890 VOICE_DEMO_ALLOW_LAN=true VOICE_DEMO_HTTPS=true VOICE_DEMO_HTTPS_KEY=/home/stickai/stickbot-voice/certs/m7d-https/stickbot-tars-m7d-server.key.pem VOICE_DEMO_HTTPS_CERT=/home/stickai/stickbot-voice/certs/m7d-https/stickbot-tars-m7d-server.cert.pem LOG_DIR=/tmp/tars-live-demo bash scripts/m7d-local-real-mic-demo.sh
curl -k -fsS https://127.0.0.1:19890/health
curl -k -fsS https://192.168.1.107:19890/health
curl -fsS http://127.0.0.1:8020/ready
```

Browser URL for Stick: `https://192.168.1.107:19890/`

## Proven milestones

- M3 model acquired/provenance recorded, no load
- M4 sandboxed XTTS local load
- M5 local serverization node voice pass
- M6 OpenClaw adapter fixture voice pass
- M7D HTTPS LAN real mic STT + echo pass
- M7E audible HTTPS LAN TARS voice output pass
- M7F prosody kernel local check pass
- M7G tuning console + JSON/matrix controls + audible XTTS slider mapping pass
- M7H/M55 prosody score engine pass
- M7I chunk conductor local pass
- M7J/K/L DSP + streaming frame + duplex controller local pass
- M7M/N/O streaming playback hooks + partial ingress + barge-in local pass
- M7P live browser streaming + barge-in pass
- M5.6 voice body/mastering postprocess pass with R2 tail-trim fix, R3 tail guard, and R4 terminal tail/drain live PASS
- M7Q true partial local STT loop live pass: browser mic partials seq 0-5, final transcript, local whisper slices, privacy guard off
- M7R low-latency streaming transport live pass: partial STT, reconstruction, Send, audio generation, barge-in, and strict telemetry readback confirmed
- Generated audio auditor added: deterministic stage manifest plus explicit guarded delete mode for generated/captured speech-session audio cleanup
- M7S live barge-in with real speech pass: live spoken interruption stopped active TARS playback, triggered duplex barge-in/listening, and produced local partial STT with privacy guard off
- M7T live prosody mood score / emotional sheet music pass: deterministic delivery-metadata cue layer emits mood score, cue glyphs, intensity, contour, rests, and text hashes without rewriting canonical assistant text
- Audio-first multiplexed production streaming architecture local contract pass: five-lane turn contract defines canonical text, audio PCM stream, prosody metadata, control events, and audit trace; barge-in cancels audio without mutating canonical text

## Next recommended milestones

- AUDIO_FIRST_MULTIPLEXED_RUNTIME_HARNESS_LIVE_PASS
- AUTOMATIC_OPERATIONAL_REHYDRATOR_MESH_AFTER_STICKBOT_TARS

## Live readiness note

- Status: `STICKBOT_TARS_AUDIO_FIRST_MULTIPLEXED_PRODUCTION_STREAMING_ARCHITECTURE_LOCAL_CONTRACT_PASS`
- Needs human ear: Audio-first production contract is complete. Next milestone is a local runtime harness/live proof across all multiplex lanes.

## Runtime/local path inventory

| Label | Path | Exists | Bytes | SHA256 prefix |
|---|---|---:|---:|---|
| runtimeRoot | `/home/stickai/stickbot-voice` | yes | 4096 |  |
| tarsModelPath | `/home/stickai/stickbot-voice/xtts_models/tars` | yes | 4096 |  |
| referenceWav | `/home/stickai/stickbot-voice/speakers/reference.wav` | yes | 986156 | `b2935696d607` |
| whisperBin | `/home/stickai/stickbot-voice/tools/whisper.cpp/v1.9.1-ubuntu-x64/extract/whisper-bin-ubuntu-x64/whisper-cli` | yes | 976312 | `427dfb509f2c` |
| whisperModel | `/home/stickai/stickbot-voice/stt_models/whisper.cpp/ggml-small.en.bin` | yes | 487614201 |  |
| ffmpegBin | `/home/stickai/stickbot-voice/tools/ffmpeg-static/johnvansickle-ffmpeg-release-amd64-static/extract/ffmpeg` | yes | 79826272 |  |
| ffprobeBin | `/home/stickai/stickbot-voice/tools/ffmpeg-static/johnvansickle-ffmpeg-release-amd64-static/extract/ffprobe` | yes | 79665792 |  |
| httpsCertDir | `/home/stickai/stickbot-voice/certs/m7d-https` | yes | 4096 |  |

## Curated source inventory

| Kind | Path | Exists | Lines | SHA256 prefix |
|---|---|---:|---:|---|
| repo | `projects/stickbot-tars-smoke/README.md` | yes | 618 | `ac0e6e3e925d` |
| repo | `projects/stickbot-tars-smoke/IMPLEMENTATION_NOTEBOOK.md` | yes | 678 | `3457b6b1e3d2` |
| repo | `projects/stickbot-tars-smoke/package.json` | yes | 29 | `7a241a40315f` |
| repo | `projects/stickbot-tars-smoke/server.js` | yes | 453 | `86f7af8adae4` |
| repo | `projects/stickbot-tars-smoke/scripts/stickbot-tars-rehydrate.mjs` | yes | 362 | `56006bda47c1` |
| repo | `projects/stickbot-tars-smoke/scripts/generated-audio-auditor.mjs` | yes | 599 | `e80c74f1de0d` |
| repo | `projects/stickbot-tars-smoke/src/config.js` | yes | 83 | `970254a02b80` |
| repo | `projects/stickbot-tars-smoke/src/stt-adapter.js` | yes | 147 | `cc078e89d94e` |
| repo | `projects/stickbot-tars-smoke/src/audio-normalizer.js` | yes | 118 | `673cab9a8d77` |
| repo | `projects/stickbot-tars-smoke/src/audio/dsp-polish-stage.js` | yes | 224 | `c320a9bd73e0` |
| repo | `projects/stickbot-tars-smoke/src/audio/voice-body-mastering-stage.js` | yes | 247 | `1bb386869e41` |
| repo | `projects/stickbot-tars-smoke/src/audio/audio-performance-pipeline.js` | yes | 96 | `785996ff3669` |
| repo | `projects/stickbot-tars-smoke/src/audio/streaming-frame-interface.js` | yes | 200 | `e6127d877103` |
| repo | `projects/stickbot-tars-smoke/src/audio/full-duplex-turn-controller.js` | yes | 179 | `c41382400e9f` |
| repo | `projects/stickbot-tars-smoke/src/audio/production-multiplex-contract.js` | yes | 235 | `cfcb5a936bb4` |
| repo | `projects/stickbot-tars-smoke/src/audio/duplex-event-ingress.js` | yes | 64 | `163cb8843857` |
| repo | `projects/stickbot-tars-smoke/src/audio/partial-stt-loop.js` | yes | 57 | `a15d1a2a2578` |
| repo | `projects/stickbot-tars-smoke/src/audio/wav-stitcher.js` | yes | 122 | `b3dab5a33b94` |
| repo | `projects/stickbot-tars-smoke/src/audio/xtts-chunk-conductor.js` | yes | 276 | `87a522eba3fd` |
| repo | `projects/stickbot-tars-smoke/src/prosody/prosody-score-engine.js` | yes | 154 | `98e488709d90` |
| repo | `projects/stickbot-tars-smoke/src/prosody/live-prosody-cue-layer.js` | yes | 138 | `e3b179e75513` |
| repo | `projects/stickbot-tars-smoke/src/voice/tars-prosody-kernel.js` | yes | 198 | `240115a067c0` |
| repo | `projects/stickbot-tars-smoke/src/voice/tars-prosody-matrix.js` | yes | 434 | `ad30c2f89559` |
| repo | `projects/stickbot-tars-smoke/public/app.js` | yes | 720 | `6b94863c8291` |
| repo | `projects/stickbot-tars-smoke/public/index.html` | yes | 75 | `83f03bb7e75c` |
| repo | `projects/stickbot-tars-smoke/safety/audio-path-policy.js` | yes | 44 | `2c6f52fd7c2a` |
| repo | `projects/stickbot-tars-smoke/safety/network-policy.js` | yes | 65 | `48c836a3a29a` |
| repo | `projects/stickbot-tars-smoke/scripts/m7d-local-real-mic-demo.sh` | yes | 99 | `352b645ea0bd` |
| repo | `projects/stickbot-tars-smoke/scripts/m7e-start-xtts-loopback.sh` | yes | 64 | `e578525e0ef4` |
| repo | `projects/stickbot-tars-smoke/scripts/xtts-local-server.py` | yes | 262 | `909cdeb470af` |
| repo | `projects/stickbot-tars-smoke/state/status.json` | yes | 1636 | `77aaf6eb7564` |
| doc | `projects/stickbot-tars-smoke/docs/STICKBOT_TARS_REHYDRATION.md` | yes | 71 | `a39245cbc82f` |
| doc | `projects/stickbot-tars-smoke/docs/PRODUCTION_VOICE_STREAM_ARCHITECTURE.md` | yes | 129 | `caab67bfd1d6` |
| doc | `projects/stickbot-tars-smoke/docs/audio-first-multiplexed-production-streaming/AUDIO_FIRST_MULTIPLEXED_PRODUCTION_STREAMING_ARCHITECTURE_LOCAL_CONTRACT_PASS.md` | yes | 165 | `ce1e0b2c5b6f` |
| doc | `projects/stickbot-tars-smoke/docs/LOW_LEVEL_DESIGN_AND_IMPLEMENTATION_PLAN.md` | yes | 1045 | `b5a906560671` |
| doc | `projects/stickbot-tars-smoke/docs/LOOPBACK_LAN_EXPOSURE_NOTEBOOK.md` | yes | 166 | `e161d380d315` |
| doc | `projects/stickbot-tars-smoke/docs/TROUBLESHOOTING_AND_REPAIR_NOTEBOOK.md` | yes | 665 | `b8481b1d573c` |
| doc | `projects/stickbot-tars-smoke/docs/m3-model-provenance/M3_MODEL_ACQUIRED_HASHED_PROVENANCE_RECORDED_NO_LOAD.md` | yes | 47 | `466ea14bf8e1` |
| doc | `projects/stickbot-tars-smoke/docs/m5-local-serverization/M5_LOCAL_SERVERIZATION_NODE_VOICE_PASS.md` | yes | 159 | `59d47b22daf4` |
| doc | `projects/stickbot-tars-smoke/docs/m6-openclaw-adapter/M6_OPENCLAW_ADAPTER_FIXTURE_VOICE_PASS.md` | yes | 147 | `5da254bc043e` |
| doc | `projects/stickbot-tars-smoke/docs/m7-local-stt/m7d-real-mic-local-demo/M7D_HTTPS_LAN_REAL_MIC_STT_ECHO_PASS.md` | yes | 36 | `fd106485939a` |
| doc | `projects/stickbot-tars-smoke/docs/m7-local-stt/m7e-https-lan-xtts-voice-output/M7E_HTTPS_LAN_TARS_VOICE_OUTPUT_PASS.md` | yes | 125 | `ab549333abd2` |
| doc | `projects/stickbot-tars-smoke/docs/m7-local-stt/m7h-prosody-score-engine/M7H_M55_PROSODY_SCORE_ENGINE_PASS.md` | yes | 127 | `dd2c30b933bb` |
| doc | `projects/stickbot-tars-smoke/docs/m7-local-stt/m7i-chunk-conductor/M7I_CHUNK_CONDUCTOR_LOCAL_PASS.md` | yes | 166 | `80bd0b6661fc` |
| doc | `projects/stickbot-tars-smoke/docs/m7-local-stt/m7jkl-dsp-stream-duplex/M7JKL_DSP_STREAM_DUPLEX_LOCAL_PASS.md` | yes | 200 | `d12eb4ed1ed5` |
| doc | `projects/stickbot-tars-smoke/docs/m7-local-stt/m7mno-streaming-partial-bargein/M7MNO_STREAMING_PARTIAL_BARGEIN_LOCAL_PASS.md` | yes | 134 | `48460f9e72c3` |
| doc | `projects/stickbot-tars-smoke/docs/m7-local-stt/m7p-live-browser-streaming-bargein/M7P_LIVE_BROWSER_STREAMING_BARGEIN_PASS.md` | yes | 162 | `806fa4ff39e4` |
| doc | `projects/stickbot-tars-smoke/docs/m7-local-stt/m56-voice-body-mastering/M56_VOICE_BODY_POSTPROCESS_PASS.md` | yes | 309 | `98dbb6a8e585` |
| doc | `projects/stickbot-tars-smoke/docs/m7-local-stt/m7q-true-partial-local-stt-loop/M7Q_TRUE_PARTIAL_LOCAL_STT_LOOP_LIVE_PASS.md` | yes | 143 | `b7dd1b851f79` |
| doc | `projects/stickbot-tars-smoke/docs/m7-local-stt/m7r-low-latency-streaming-transport/M7R_LOW_LATENCY_STREAMING_TRANSPORT_LIVE_PASS.md` | yes | 134 | `dd7f787421e3` |
| doc | `projects/stickbot-tars-smoke/docs/m7-local-stt/m7s-live-barge-in-real-speech/M7S_LIVE_BARGE_IN_WITH_REAL_SPEECH_PASS.md` | yes | 97 | `9d94e1b3c9a9` |
| doc | `projects/stickbot-tars-smoke/docs/m7-local-stt/m7t-live-prosody-mood-score/M7T_LIVE_PROSODY_MOOD_SCORE_AND_EMOTIONAL_SHEET_MUSIC_PASS.md` | yes | 194 | `c5b4b0afb2fb` |
| memory | `memory/2026-07-03.md` | yes | 455 | `edcccd3f1037` |
| memory | `memory/lessons-learned-stickbot-tars-live-dashboard-refresh-2026-07-03.md` | yes | 70 | `bc743eedea7c` |
| memory | `memory/lessons-learned-stickbot-tars-m7r-live-transport-repair-2026-07-03.md` | yes | 95 | `5bd77b56222f` |

All curated sources were found.

## Latest local generated-artifact pointers

Generated audio is local/runtime evidence only and should not be committed. Latest pointers:

- `projects/stickbot-tars-smoke/data/audio/output/b956ec02-c17c-4253-816f-848599069056.wav` (854958 bytes, 2026-07-03T10:41:01.757Z)
- `projects/stickbot-tars-smoke/data/audio/output/b956ec02-c17c-4253-816f-848599069056-stitch/silence-002-230ms.wav` (22158 bytes, 2026-07-03T10:41:01.697Z)
- `projects/stickbot-tars-smoke/data/audio/output/b956ec02-c17c-4253-816f-848599069056-stitch/silence-001-245ms.wav` (23598 bytes, 2026-07-03T10:41:01.685Z)
- `projects/stickbot-tars-smoke/data/audio/output/b956ec02-c17c-4253-816f-848599069056-chunk-003.dsp.master.wav` (198410 bytes, 2026-07-03T10:41:01.673Z)
- `projects/stickbot-tars-smoke/data/audio/output/b956ec02-c17c-4253-816f-848599069056-chunk-002.dsp.master.wav` (407554 bytes, 2026-07-03T10:41:01.625Z)
- `projects/stickbot-tars-smoke/data/audio/output/b956ec02-c17c-4253-816f-848599069056-chunk-001.dsp.master.wav` (203550 bytes, 2026-07-03T10:41:01.485Z)
- `projects/stickbot-tars-smoke/data/audio/output/b956ec02-c17c-4253-816f-848599069056-chunk-003.dsp.wav` (67378 bytes, 2026-07-03T10:41:01.437Z)
- `projects/stickbot-tars-smoke/data/audio/output/b956ec02-c17c-4253-816f-848599069056-chunk-002.dsp.wav` (172090 bytes, 2026-07-03T10:41:01.365Z)

Latest mastered chunks:

- `projects/stickbot-tars-smoke/data/audio/output/b956ec02-c17c-4253-816f-848599069056-chunk-003.dsp.master.wav` (198410 bytes, 2026-07-03T10:41:01.673Z)
- `projects/stickbot-tars-smoke/data/audio/output/b956ec02-c17c-4253-816f-848599069056-chunk-002.dsp.master.wav` (407554 bytes, 2026-07-03T10:41:01.625Z)
- `projects/stickbot-tars-smoke/data/audio/output/b956ec02-c17c-4253-816f-848599069056-chunk-001.dsp.master.wav` (203550 bytes, 2026-07-03T10:41:01.485Z)


## Rehydration instruction

For future sessions: run `npm run rehydrate:tars -- --status`, read `artifacts/rehydration/stickbot-tars/latest.md`, then open only the listed source files needed for the immediate task. This packet restores project/goals/locations/procedures; it is not a substitute for running `npm run check` or the relevant live browser/audio smoke before claiming readiness.
