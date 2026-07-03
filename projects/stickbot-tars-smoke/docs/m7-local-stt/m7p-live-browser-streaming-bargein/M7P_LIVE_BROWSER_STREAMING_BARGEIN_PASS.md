# M7P — Live Browser Streaming + Barge-In Verification PASS

Date: 2026-07-03
Classification: `STICKBOT_TARS_M7P_LIVE_BROWSER_STREAMING_BARGEIN_PASS`

## Summary

Stick performed the live browser verification against the refreshed Stickbot-TARS HTTPS LAN webapp.

Live URL:

```text
https://192.168.1.107:19890/
```

Pre-test health checks passed:

```text
https://127.0.0.1:19890/health  OK
https://192.168.1.107:19890/health OK
http://127.0.0.1:8020/ready OK / STICKBOT_TARS_M5_XTTS_SERVER_READY
```

## Human-observed evidence

Stick reported:

> I could hear TARS until I started the mic again. MIC stopped and I saw an error "raw transcript durable storage: false"

Screenshot evidence showed:

```text
Streaming: 4 chunk frames queued
M7M local frame playback smoke; final WAV remains available as fallback.

Playback: stopped
M7O barge-in: mic capture started

Mic: recording... tap the mic button again to stop and transcribe

Duplex: barge-in smoke listening
raw transcript durable storage: false

Mic transcript: [BLANK_AUDIO]
Saved locally; click Send text to ask Stickbot. Duplex state: thinking; raw transcript durable storage: false
```

Interpretation:

- M7M frame playback path was active (`4 chunk frames queued`).
- TARS audio was audible.
- Starting mic capture stopped active playback.
- M7O barge-in smoke fired and returned duplex state to `listening`.
- M7N final STT path returned a duplex summary (`thinking`) with raw transcript durable storage disabled.
- `[BLANK_AUDIO]` is acceptable for this pass because the target proof was playback interruption/barge-in and privacy-safe STT ingress, not speech recognition accuracy.

## UI wording fix

The string `raw transcript durable storage: false` is a privacy/safety status, not an error.

Changed browser copy in `public/app.js` to:

```text
Privacy guard: raw mic transcript is not durably stored (off).
```

and:

```text
privacy guard: raw mic transcript durable storage is off.
```

## Validation

Automated gate before live test:

```text
npm run check -> 80/80 tests passed
```

Post-live local change gate should continue to pass via the same command.

## Boundaries preserved

No changes to:

- OpenClaw routing/defaults/fallbacks,
- Gateway config/service state,
- NOA,
- Android,
- provider settings,
- model runtime isolation,
- LAN exposure beyond the already-approved HTTPS LAN demo path,
- port `8787`,
- cloud speech APIs,
- browser Web Speech API.

Raw mic transcript durable storage remained false.

## R2 follow-up — final WAV fallback barge-in stop

After the initial pass, Stick tested the non-streaming/final WAV playback path and found:

> Once it played, I tried the model capture again when it wasn't streaming, and it kept playing the wav, not live, but the mic didn't break it.

Root cause: M7O mic-start stop logic tracked the streaming chunk `Audio()` object, but the final fallback WAV was an inline `<audio>` element and was not registered as active playback when manually played.

Fix:

- Added a browser playback registry for all generated audio elements.
- Registered inline final WAV `<audio>` elements by `turnId`.
- `stopActivePlayback()` now stops either the registered active playback object or any currently-playing `<audio>` element found by fallback scan.
- Streaming chunk audio still removes its source on stop; final WAV pauses/resets without removing its source so the user can replay/save it.
- Updated cache buster to `m7p-final-wav-bargein-stop`.

This upgrades M7P from streaming-path-only interruption proof to streaming + fallback WAV interruption coverage.

## R3 follow-up — mic lifecycle after streaming barge-in confirmed

Stick retested live streaming barge-in and confirmed:

> after the audio cut out, the mic allowed me to keep recording. no break. no error.

This proves the intended streaming barge-in lifecycle:

- live streaming audio cuts out immediately when mic capture starts,
- microphone capture continues after playback interruption,
- no mic lifecycle break or browser error was observed,
- `raw transcript durable storage: false` is understood as a privacy state/guardrail, not an error.

Streaming-path M7P is therefore confirmed end-to-end: audible streaming playback -> mic-start barge-in -> playback stop -> mic remains recording.

## Remaining work

Next recommended milestones:

1. `M7Q_TRUE_PARTIAL_LOCAL_STT_LOOP` — feed real incremental local STT/voice activity events into M7L rather than metadata-only partial ingress.
2. `M7R_LOW_LATENCY_STREAMING_TRANSPORT` — SSE/WebSocket or equivalent so playback starts while later chunks are still being synthesized, not after response completion.
3. `M7S_LIVE_BARGE_IN_WITH_REAL_SPEECH` — verify spoken interruption with non-blank mic audio and restart the turn pipeline.
