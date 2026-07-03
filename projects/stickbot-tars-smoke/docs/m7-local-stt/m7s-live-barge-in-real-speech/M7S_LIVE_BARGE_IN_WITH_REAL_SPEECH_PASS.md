# M7S — Live Barge-In With Real Speech PASS

Date: 2026-07-03
Classification: `STICKBOT_TARS_M7S_LIVE_BARGE_IN_WITH_REAL_SPEECH_PASS`

## Objective

Prove that Stickbot-TARS can be interrupted by a real spoken user utterance during live browser audio playback, while preserving local-only speech boundaries.

M7P/M7O already proved mic-start barge-in mechanics and playback stop coverage. M7S raises the gate to human live speech during playback, with browser-visible local partial STT evidence.

## Evidence

Stick performed the live browser test at:

```text
https://192.168.1.107:19890/
```

Stick confirmed:

```text
that worked. screenshot attached
```

Screenshot readback showed:

```text
Partial STT: Stick butt, I'm so sorry to interrupt you.
seq 0; local whisper slice; privacy guard: raw transcript durable storage is off.

Duplex: barge-in smoke listening
Privacy guard: raw mic transcript is not durably stored (off).

Mic: recording with local partial STT slices... tap the mic button again to stop and transcribe

Playback: stopped
M7O barge-in: mic capture started

Streaming transport: 3 chunk frames preloaded
M7R browser_preload_queue_then_serial_playback; target first audio 1200ms; final WAV remains fallback.
```

The interrupted assistant response was a live TARS voice turn:

```text
Echo smoke response: Okay, Stickbot, we're about to test M7S and I'm going to interrupt you. I don't mean to be rude.
```

Visible voice/streaming evidence:

```text
Voice score: mood TARS mission brief / marine commander, base temp 0.58, effective temp 0.58, top_p 0.77, XTTS speed 1.02, chunk 175
Streaming frames: 3 / target streaming_full_duplex_mesh
```

## Pass criteria

- [x] Live browser audio playback active before interruption.
- [x] Real spoken user interruption captured by browser mic.
- [x] Playback stopped on mic capture.
- [x] Duplex controller reported barge-in/listening state.
- [x] Partial local STT slice appeared from local whisper.
- [x] Raw mic transcript durable storage remained off.
- [x] Browser Web Speech API was not used.
- [x] Cloud speech API was not used.
- [x] Streaming transport remained M7R low-latency queue mode.
- [x] No OpenClaw/Gateway/NOA/provider routing mutation.
- [x] Port `8787` untouched.

## Boundaries

```json
{
  "localOnly": true,
  "rawTranscriptDurableStorage": false,
  "browserWebSpeechApi": false,
  "cloudSpeechApi": false,
  "openClawProductionMutation": false,
  "gatewayConfigMutation": false,
  "port8787Touched": false
}
```

## Result

```text
STICKBOT_TARS_M7S_LIVE_BARGE_IN_WITH_REAL_SPEECH_PASS
```

Next recommended milestones:

```text
LIVE_PROSODY_MOOD_SCORE_AND_EMOTIONAL_SHEET_MUSIC
AUDIO_FIRST_MULTIPLEXED_PRODUCTION_STREAMING_ARCHITECTURE
```
