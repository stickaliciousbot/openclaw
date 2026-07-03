import test from 'node:test';
import assert from 'node:assert/strict';
import { buildFinalSttControllerSummary, buildPartialSttControllerSummary, runSanitizedDuplexScenario, sanitizeDuplexEvent, transcriptEventFromText } from '../src/audio/duplex-event-ingress.js';

test('STICKBOT_TARS_M7N_PARTIAL_STT_CONTROLLER_INGRESS_PASS', () => {
  const summary = buildPartialSttControllerSummary({ turnId: 'turn-partial', partialText: 'partial local words', confidence: 0.42 });
  assert.equal(summary.state, 'listening');
  assert.equal(summary.boundaries.rawTranscriptDurableStorage, false);
  const partial = summary.events.find((event) => event.type === 'partial_transcript');
  assert.equal(partial.payload.charCount, 'partial local words'.length);
  assert.equal(partial.payload.durableRawTextStored, false);
  assert.equal(partial.payload.text, undefined);
  assert.equal(partial.payload.textSha256.length, 64);
});

test('STICKBOT_TARS_M7N_FINAL_STT_CONTROLLER_INGRESS_PASS', () => {
  const summary = buildFinalSttControllerSummary({ turnId: 'turn-final', finalText: 'final local words' });
  assert.equal(summary.state, 'thinking');
  assert.ok(summary.actions.some((action) => action.type === 'submit_final_transcript_to_turn_engine'));
  assert.equal(summary.events.find((event) => event.type === 'final_transcript').payload.text, undefined);
  assert.equal(summary.boundaries.cloudSpeechApiAllowed, false);
});

test('STICKBOT_TARS_M7N_SANITIZES_RAW_TRANSCRIPT_EVENTS_PASS', () => {
  const event = sanitizeDuplexEvent({ type: 'partial_transcript', payload: { text: 'do not store raw text', confidence: 0.8 } });
  assert.equal(event.payload.text, undefined);
  assert.equal(event.payload.textSha256.length, 64);
  assert.equal(event.payload.charCount, 'do not store raw text'.length);
  assert.equal(event.payload.durableRawTranscript, false);
  const direct = transcriptEventFromText('final_transcript', 'same rule');
  assert.equal(direct.payload.text, undefined);
});

test('STICKBOT_TARS_M7O_BARGE_IN_SCENARIO_INGRESS_PASS', () => {
  const summary = runSanitizedDuplexScenario([
    { type: 'listen_start' },
    { type: 'final_transcript', payload: { text: 'start the turn' } },
    { type: 'assistant_text_ready', payload: { canonicalTextSha256: 'a'.repeat(64) } },
    { type: 'audio_frame_ready', payload: { seq: 7, frameType: 'audio_chunk_ready' } },
    { type: 'barge_in', payload: { reason: 'mic_capture_started' } },
    { type: 'resume_listening' }
  ], { turnId: 'turn-barge' });
  assert.equal(summary.state, 'listening');
  assert.ok(summary.actions.some((action) => action.type === 'stop_audio_output'));
  assert.ok(summary.actions.some((action) => action.type === 'return_to_local_listening'));
  assert.equal(summary.events.find((event) => event.type === 'final_transcript').payload.text, undefined);
});
