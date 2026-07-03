import test from 'node:test';
import assert from 'node:assert/strict';
import { loadTarsProsodyProfile } from '../src/voice/tars-prosody-profile.js';
import { buildTarsProsodyPlan, inspectNoSecretSpeech } from '../src/voice/tars-prosody-kernel.js';
import { reconstructChunks } from '../src/voice/tars-sentence-chunker.js';
import {
  defaultTarsTuningState,
  deriveAudibleXttsParamsFromTuning,
  deriveDeliveryFromTuning,
  sanitizeTarsTuning
} from '../src/voice/tars-prosody-tuning.js';
import {
  deriveMoodMatrixSelection,
  importProsodyMatrixJson,
  listTarsMoodPresets,
  publicProsodyMatrixSummary,
  sanitizeXttsParams
} from '../src/voice/tars-prosody-matrix.js';

test('TARS_PROSODY_PROFILE_LOAD_PASS', () => {
  const profile = loadTarsProsodyProfile();
  assert.equal(profile.id, 'tars-inspired-local-v1');
  assert.equal(profile.goal, 'voice_likeness_only_canonical_text_unchanged');
  assert.equal(profile.delivery.sentenceChunking, true);
  assert.equal(profile.engineHints.piperReference.inference.noiseScale, 0.667);
});

test('TARS_SENTENCE_CHUNKING_PASS and TARS_CANONICAL_TEXT_UNCHANGED_PASS', () => {
  const text = 'PASS. M7F prosody kernel loaded. No mutation. No rewrite.';
  const plan = buildTarsProsodyPlan(text, { maxChars: 24 });
  assert.ok(plan.chunkCount > 1);
  assert.equal(reconstructChunks(plan.chunks), text);
  assert.equal(plan.canonicalTextUnchanged, true);
});

test('TARS_STATUS_SALIENCE_PASS', () => {
  const text = 'PASS. No mutation. HOLD if token risk appears. 19890 remains HTTPS.';
  const plan = buildTarsProsodyPlan(text);
  assert.ok(plan.salienceSummary.status >= 2, JSON.stringify(plan.salienceSummary));
  assert.ok(plan.salienceSummary.number >= 1, JSON.stringify(plan.salienceSummary));
  assert.ok(plan.salienceSummary.warning >= 1, JSON.stringify(plan.salienceSummary));
});

test('TARS_NO_SECRET_SPEECH_PASS blocks secret-like text', () => {
  const safe = inspectNoSecretSpeech('PASS. No mutation. No send.');
  assert.equal(safe.ok, true);
  const unsafe = inspectNoSecretSpeech('Bearer sk-supersecretvalue123456789 should never be spoken.');
  assert.equal(unsafe.ok, false);
});

test('TARS_PROSODY_TUNING_SCHEMA_PASS exposes requested sliders', () => {
  const state = defaultTarsTuningState(new Date('2026-07-03T00:00:00Z'));
  for (const key of ['pitch', 'timbre', 'speed', 'compression', 'verbalGait', 'verbosity', 'clip']) {
    assert.equal(typeof state.active.parameters[key], 'number', key);
  }
  for (const key of ['global', 'threshold', 'pitch', 'timbre', 'speed', 'compression', 'verbalGait', 'verbosity', 'clip']) {
    assert.equal(typeof state.active.randomness[key], 'number', key);
  }
  assert.equal(state.active.boundaries.canonicalTextAuthoritative, true);
  assert.equal(state.active.boundaries.textRewriteAllowed, false);
});

test('TARS_PROSODY_TUNING_CLAMP_PASS keeps slider values bounded', () => {
  const tuning = sanitizeTarsTuning({
    parameters: { pitch: 2, timbre: -1, speed: 0.25, compression: '0.9' },
    randomness: { global: 3, threshold: -4, pitch: '0.5' }
  });
  assert.equal(tuning.parameters.pitch, 1);
  assert.equal(tuning.parameters.timbre, 0);
  assert.equal(tuning.parameters.speed, 0.25);
  assert.equal(tuning.parameters.compression, 0.9);
  assert.equal(tuning.randomness.global, 1);
  assert.equal(tuning.randomness.threshold, 0);
  assert.equal(tuning.randomness.pitch, 0.5);
});

test('TARS_PROSODY_TUNING_CANONICAL_TEXT_UNCHANGED_PASS', () => {
  const text = 'PASS. This is the exact canonical text.';
  const tuning = sanitizeTarsTuning({ parameters: { pitch: 0.8, speed: 0.7 }, randomness: { global: 0.2 } });
  const plan = buildTarsProsodyPlan(text, { tuning, maxChars: 16 });
  assert.equal(reconstructChunks(plan.chunks), text);
  assert.equal(plan.canonicalTextUnchanged, true);
  assert.equal(plan.tuning.boundaries.textRewriteAllowed, false);
  assert.equal(plan.delivery.textRewriteAllowed, false);
});

test('TARS_PROSODY_TUNING_DELIVERY_DERIVATION_PASS', () => {
  const profile = loadTarsProsodyProfile();
  const low = deriveDeliveryFromTuning(profile.delivery, sanitizeTarsTuning({ parameters: { pitch: 0, speed: 0 } }));
  const high = deriveDeliveryFromTuning(profile.delivery, sanitizeTarsTuning({ parameters: { pitch: 1, speed: 1 } }));
  assert.ok(low.pitchShiftSemitones < high.pitchShiftSemitones);
  assert.ok(low.normalRate < high.normalRate);
});

test('TARS_PROSODY_TUNING_AUDIBLE_XTTS_SLIDER_MAPPING_PASS', () => {
  const matrix = { temperature: 0.68, topP: 0.82, topK: 45, repetitionPenalty: 10, lengthPenalty: 1.03, speed: 0.98 };
  const low = deriveAudibleXttsParamsFromTuning(matrix, { speed: 0, compression: 0, verbosity: 0, clip: 0, verbalGait: 0 }, { global: 0, threshold: 1 });
  const high = deriveAudibleXttsParamsFromTuning(matrix, { speed: 1, compression: 1, verbosity: 1, clip: 1, verbalGait: 1 }, { global: 1, threshold: 0 });
  assert.ok(low.speed < high.speed);
  assert.ok(low.temperature < high.temperature);
  assert.ok(low.topP < high.topP);
  assert.ok(low.topK < high.topK);
  assert.ok(low.repetitionPenalty < high.repetitionPenalty);
  assert.ok(low.lengthPenalty < high.lengthPenalty);
  assert.deepEqual(Object.keys(high).sort(), ['lengthPenalty', 'repetitionPenalty', 'speed', 'temperature', 'topK', 'topP'].sort());
});

test('TARS_PROSODY_MATRIX_SCHEMA_PASS exposes local mood presets', () => {
  const matrix = publicProsodyMatrixSummary();
  assert.equal(matrix.schema, 'stickbot-tars-prosody-tuning-matrix/v0.1-derived-local');
  assert.equal(listTarsMoodPresets().length, 13);
  assert.ok(matrix.moodPrecedence.includes('urgent_alert'));
  assert.ok(matrix.moods.some((mood) => mood.id === 'baseline_deadpan'));
  assert.equal(matrix.bounds.temperature.safeMin, 0.5);
  assert.equal(matrix.textChunking.hardMaxCharsPerTtsRequest, 210);
});

test('TARS_PROSODY_MATRIX_XTTS_CLAMP_PASS keeps uploaded recommendations bounded', () => {
  const params = sanitizeXttsParams({ temperature: 99, top_p: -2, top_k: 999, repetition_penalty: 3, length_penalty: 9, speed: '0.5' });
  assert.equal(params.temperature, 0.78);
  assert.equal(params.topP, 0.7);
  assert.equal(params.topK, 60);
  assert.equal(params.repetitionPenalty, 9.8);
  assert.equal(params.lengthPenalty, 1.27);
  assert.equal(params.speed, 0.82);
});

test('TARS_PROSODY_MATRIX_MOOD_DELIVERY_PASS applies mood chunking without text rewrite', () => {
  const text = 'PASS. This mission brief should stay canonical while chunk delivery follows the local matrix recommendation. No mutation. No rewrite.';
  const tuning = sanitizeTarsTuning({ moodId: 'mission_brief' });
  const plan = buildTarsProsodyPlan(text, { tuning, maxChars: 220 });
  assert.equal(reconstructChunks(plan.chunks), text);
  assert.equal(plan.tuning.moodId, 'mission_brief');
  assert.equal(plan.delivery.moodId, 'mission_brief');
  assert.equal(plan.delivery.maxCharsPerChunk, 200);
  assert.equal(plan.delivery.baseXttsParams.temperature, 0.63);
  assert.ok(plan.delivery.xttsParams.temperature <= 0.63);
  assert.ok(plan.chunks.every((chunk) => chunk.text.length <= 200));
  assert.equal(plan.delivery.textRewriteAllowed, false);
});

test('TARS_PROSODY_MATRIX_UNKNOWN_MOOD_FALLBACK_PASS', () => {
  const selection = deriveMoodMatrixSelection({ moodId: 'try_to_be_a_space_opera' });
  assert.equal(selection.moodId, 'baseline_deadpan');
  assert.equal(selection.boundaries.textRewriteAllowed, false);
  assert.equal(selection.boundaries.cloudSpeechAllowed, false);
});

test('TARS_PROSODY_MATRIX_OVERRIDE_WIRING_PASS keeps applied JSON slider values', () => {
  const tuning = sanitizeTarsTuning({
    moodId: 'mission_brief',
    matrix: {
      xttsParams: { temperature: 0.7, topP: 0.9, topK: 60, repetitionPenalty: 11.2, lengthPenalty: 1.11, speed: 1.09 },
      delivery: { maxCharsPerChunk: 123, sentencePauseMs: 410, commaPauseMs: 140, lineBreakPauseMs: 470 }
    }
  });
  assert.equal(tuning.matrix.moodId, 'mission_brief');
  assert.equal(tuning.matrix.xttsParams.temperature, 0.7);
  assert.equal(tuning.matrix.xttsParams.topP, 0.89);
  assert.equal(tuning.matrix.xttsParams.topK, 60);
  assert.equal(tuning.matrix.delivery.maxCharsPerChunk, 123);
  assert.equal(tuning.matrix.delivery.sentencePauseMs, 410);
  const text = 'Calibrated response uses applied matrix override values while preserving text.';
  const plan = buildTarsProsodyPlan(text, { tuning, maxChars: 220 });
  assert.equal(plan.delivery.baseXttsParams.temperature, 0.7);
  assert.equal(plan.delivery.baseXttsParams.speed, 1.09);
  assert.ok(plan.delivery.xttsParams.temperature <= 0.7);
  assert.ok(plan.delivery.xttsParams.speed <= 1.09);
  assert.equal(plan.delivery.maxCharsPerChunk, 123);
  assert.equal(plan.prosodySheet[0].xttsParams.temperature, 0.7);
  assert.equal(plan.prosodySheet[0].delivery.maxCharsPerChunk, 123);
  assert.ok(plan.chunks.every((chunk) => chunk.text.length <= 123));
  assert.equal(reconstructChunks(plan.chunks), text);
});

test('TARS_PROSODY_MATRIX_JSON_IMPORT_PASS sanitizes uploaded local matrix', () => {
  const matrix = importProsodyMatrixJson({
    schema: 'stickbot-tars-prosody-tuning-matrix/v0.1',
    mood_precedence: ['laser_mode', 'baseline_deadpan'],
    moods: [
      {
        id: 'laser mode!!!',
        label: 'Laser Mode',
        purpose: 'Test custom uploaded expression.',
        selection_thresholds: { priority: 99 },
        expression_token: '🎯',
        xtts_params: { temperature: { recommended: 999 }, top_p: { recommended: -1 }, top_k: { recommended: 70 }, speed: { recommended: 2 } },
        delivery: { max_chars_per_chunk: 999, sentence_pause_ms: 999, comma_pause_ms: 1, line_break_pause_ms: 250 },
        evaluation_thresholds: { min_intelligibility_score: 0.91 }
      }
    ]
  }, new Date('2026-07-03T00:00:00Z'));
  assert.ok(matrix.moods.some((mood) => mood.id === 'laser_mode'));
  assert.ok(matrix.moods.some((mood) => mood.id === 'baseline_deadpan'));
  const selection = deriveMoodMatrixSelection({ moodId: 'laser_mode' }, matrix);
  assert.equal(selection.expressionToken, '🎯');
  assert.equal(selection.xttsParams.temperature, 0.78);
  assert.equal(selection.xttsParams.topP, 0.7);
  assert.equal(selection.delivery.maxCharsPerChunk, 210);
  assert.equal(selection.delivery.sentencePauseMs, 560);
  assert.equal(selection.boundaries.importedJsonIsInstructionAuthority, false);
});

test('TARS_PROSODY_MATRIX_V2_TARS_CASE_IMPORT_PASS preserves v2 persona defaults', () => {
  const matrix = importProsodyMatrixJson({
    schema: 'stickbot-tars-case-prosody-tuning-matrix/v2.0',
    global_parameter_bounds: {
      temperature: { safe_min: 0.5, safe_max: 0.78, default_anchor: 0.62 },
      top_p: { safe_min: 0.7, safe_max: 0.89, default_anchor: 0.8 },
      top_k: { safe_min: 25, safe_max: 60, default_anchor: 40 },
      repetition_penalty: { safe_min: 9.8, safe_max: 12.5, default_anchor: 10.8 },
      length_penalty: { safe_min: 0.92, safe_max: 1.27, default_anchor: 1.1 },
      speed: { safe_min: 0.82, safe_max: 1.13, default_anchor: 0.99 }
    },
    global_text_chunking: { hard_max_chars_per_tts_request: 210, recommended_default_max_chars_per_chunk: 160, min_pause_ms: 45, max_pause_ms: 560 },
    mood_precedence: ['tars_urgent_alert_v2', 'case_rescue_urgent_v2', 'tars_baseline_deadpan_v2'],
    moods: [
      {
        id: 'tars_baseline_deadpan_v2',
        label: 'TARS baseline deadpan / crew-normal',
        voice_persona: 'TARS',
        purpose: 'Default Stickbot voice for normal responses.',
        selection_thresholds: { priority: 50, fallback_default: true },
        xtts_params: { temperature: { recommended: 0.64 }, top_p: { recommended: 0.8 }, top_k: { recommended: 42 }, repetition_penalty: { recommended: 10.4 }, length_penalty: { recommended: 1.06 }, speed: { recommended: 0.98 } },
        delivery: { max_chars_per_chunk: 165, sentence_pause_ms: 250, comma_pause_ms: 95, line_break_pause_ms: 340 },
        evaluation_thresholds: { min_tars_or_case_likeness_score: 0.74 }
      },
      {
        id: 'case_rescue_urgent_v2',
        label: 'CASE rescue urgent / controlled acceleration',
        voice_persona: 'CASE',
        purpose: 'CASE-style urgent assistance.',
        selection_thresholds: { priority: 98 },
        xtts_params: { temperature: { recommended: 0.53 }, top_p: { recommended: 0.73 }, top_k: { recommended: 30 }, repetition_penalty: { recommended: 11.4 }, length_penalty: { recommended: 1.2 }, speed: { recommended: 1.09 } },
        delivery: { max_chars_per_chunk: 120, sentence_pause_ms: 135, comma_pause_ms: 45, line_break_pause_ms: 195 },
        evaluation_thresholds: { min_tars_or_case_likeness_score: 0.74 }
      }
    ]
  }, new Date('2026-07-03T00:00:00Z'));
  assert.equal(matrix.defaultMoodId, 'tars_baseline_deadpan_v2');
  assert.equal(matrix.moods.length, 2);
  assert.equal(matrix.bounds.topK.safeMin, 25);
  const caseSelection = deriveMoodMatrixSelection({ moodId: 'case_rescue_urgent_v2' }, matrix);
  assert.equal(caseSelection.voicePersona, 'CASE');
  assert.equal(caseSelection.xttsParams.temperature, 0.53);
  assert.equal(caseSelection.delivery.maxCharsPerChunk, 120);
  assert.equal(caseSelection.evaluationThresholds.minTarsOrCaseLikenessScore, 0.74);
});

test('TARS_PROSODY_SHEET_MUSIC_PASS attaches per-chunk cues without rewrite', () => {
  const text = 'PASS. Validation gate is green. HOLD if a secret token appears. We can investigate the log next.';
  const tuning = sanitizeTarsTuning({ moodId: 'mission_brief' });
  const plan = buildTarsProsodyPlan(text, { tuning, maxChars: 32 });
  assert.equal(reconstructChunks(plan.chunks), text);
  assert.equal(plan.prosodySheet.length, plan.chunks.length);
  assert.ok(plan.prosodySheet.every((entry) => entry.moodId === 'mission_brief'));
  assert.ok(plan.prosodySheet.some((entry) => entry.phraseRole === 'status' || entry.phraseRole === 'closeout'));
  assert.ok(plan.prosodySheet.some((entry) => entry.phraseRole === 'blocker'));
  assert.ok(plan.prosodySheet.every((entry) => entry.canonicalTextUnchanged));
  assert.ok(plan.prosodySheet.every((entry) => entry.textRewriteAllowed === false));
});
