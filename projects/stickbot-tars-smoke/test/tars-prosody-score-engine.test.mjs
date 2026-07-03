import test from 'node:test';
import assert from 'node:assert/strict';
import { buildTarsProsodyPlan } from '../src/voice/tars-prosody-kernel.js';
import { buildProsodyScore } from '../src/prosody/prosody-score-engine.js';
import { loadTarsProsodyProfile } from '../src/voice/tars-prosody-profile.js';
import { sanitizeTarsTuning } from '../src/voice/tars-prosody-tuning.js';
import { importProsodyMatrixJson } from '../src/voice/tars-prosody-matrix.js';
import { buildLiveProsodyCueLayer, publicLiveProsodyCueLayer } from '../src/prosody/live-prosody-cue-layer.js';

const profile = loadTarsProsodyProfile();

test('STICKBOT_TARS_M55_MOOD_BASE_XTTS_VALUES_CHANGE_PASS', () => {
  const mission = buildProsodyScore('Proceeding with docking sequence.', { profile, tuning: sanitizeTarsTuning({ moodId: 'mission_brief' }) });
  const dry = buildProsodyScore('Proceeding with docking sequence.', { profile, tuning: sanitizeTarsTuning({ moodId: 'dry_wit' }) });
  assert.equal(mission.baseXtts.temperature, 0.63);
  assert.equal(mission.baseXtts.topP, 0.8);
  assert.equal(dry.baseXtts.temperature, 0.74);
  assert.notDeepEqual(mission.baseXtts, dry.baseXtts);
});

test('STICKBOT_TARS_M55_BLOCKER_PHRASE_SCORE_APPLIED_PASS', () => {
  const score = buildProsodyScore('One problem. The Fabric SQL gate is BLOCKED pending MFA reauth.', { profile, tuning: sanitizeTarsTuning({ moodId: 'mission_brief' }), maxChars: 60 });
  const blocker = score.chunks.find((chunk) => chunk.phraseRole === 'blocker');
  assert.ok(blocker, JSON.stringify(score.chunks.map((c) => [c.text, c.phraseRole])));
  assert.ok(blocker.effectiveXtts.temperature < blocker.baseXtts.temperature, JSON.stringify(blocker));
  assert.ok(blocker.effectiveXtts.topP < blocker.baseXtts.topP, JSON.stringify(blocker));
  assert.ok(blocker.effectivePauses.postPauseMs >= 250, JSON.stringify(blocker.effectivePauses));
});

test('STICKBOT_TARS_M55_DRY_ASIDE_PAUSE_AND_EXPRESSIVENESS_PASS', () => {
  const score = buildProsodyScore('Naturally, the robot waits before pretending to be impressed.', { profile, tuning: sanitizeTarsTuning({ moodId: 'dry_wit' }) });
  const aside = score.chunks[0];
  assert.equal(aside.phraseRole, 'aside');
  assert.ok(aside.effectivePauses.prePauseMs >= 100, JSON.stringify(aside.effectivePauses));
  assert.ok(aside.effectivePauses.postPauseMs >= 300, JSON.stringify(aside.effectivePauses));
  assert.ok(aside.effectiveXtts.temperature >= aside.baseXtts.temperature, JSON.stringify(aside));
});

test('STICKBOT_TARS_M55_URGENT_STOP_CLIPPED_TIMING_PASS', () => {
  const score = buildProsodyScore('STOP. Do not delete the gateway config.', { profile, tuning: sanitizeTarsTuning({ moodId: 'urgent_alert' }) });
  const warning = score.chunks[0];
  assert.equal(warning.phraseRole, 'warning');
  assert.ok(warning.effectiveXtts.temperature < warning.baseXtts.temperature, JSON.stringify(warning));
  assert.ok(warning.effectiveXtts.speed > warning.baseXtts.speed, JSON.stringify(warning));
  assert.ok(warning.effectivePauses.postPauseMs <= 160, JSON.stringify(warning.effectivePauses));
});

test('STICKBOT_TARS_M55_VALUES_CLAMP_WITHIN_IDENTITY_SAFE_BOUNDS_PASS', () => {
  const tuning = sanitizeTarsTuning({ moodId: 'dry_wit', parameters: { speed: 1, verbalGait: 1, clip: 1 }, randomness: { global: 1, threshold: 0 } });
  const score = buildProsodyScore('Naturally, this needs enthusiasm without sounding like a cartoon robot.', { profile, tuning });
  const chunk = score.chunks[0];
  assert.ok(chunk.effectiveXtts.temperature <= chunk.baseXtts.temperature + 0.08, JSON.stringify(chunk));
  assert.ok(chunk.effectiveXtts.topP <= chunk.baseXtts.topP + 0.06, JSON.stringify(chunk));
  assert.ok(chunk.effectiveXtts.speed <= chunk.baseXtts.speed + 0.08, JSON.stringify(chunk));
});

test('STICKBOT_TARS_M55_UI_DATA_MODEL_BASE_EFFECTIVE_DELTA_SEPARATED_PASS', () => {
  const plan = buildTarsProsodyPlan('PASS. M7H score engine loaded.', { tuning: sanitizeTarsTuning({ moodId: 'mission_brief' }), maxChars: 32 });
  assert.ok(plan.delivery.baseXttsParams);
  assert.ok(plan.delivery.xttsParams);
  assert.ok(plan.prosodyScore.chunks[0].baseXtts);
  assert.ok(plan.prosodyScore.chunks[0].deltas);
  assert.ok(plan.prosodyScore.chunks[0].effectiveXtts);
  assert.equal(plan.prosodyScore.chunks[0].text, undefined, 'public score summary must not expose raw chunk text');
  assert.equal(plan.prosodyScore.chunks[0].textSha256.length, 64);
});

test('STICKBOT_TARS_LIVE_PROSODY_MOOD_SCORE_AND_EMOTIONAL_SHEET_MUSIC_PASS', () => {
  const text = 'PASS. Proceed with the validation gate. STOP if the protected fixture is touched.';
  const score = buildProsodyScore(text, { profile, tuning: sanitizeTarsTuning({ moodId: 'mission_brief' }), maxChars: 42 });
  const layer = buildLiveProsodyCueLayer(score);
  const pub = publicLiveProsodyCueLayer(layer);
  assert.equal(layer.classification, 'STICKBOT_TARS_LIVE_PROSODY_MOOD_SCORE_AND_EMOTIONAL_SHEET_MUSIC_READY');
  assert.equal(layer.canonicalTextSha256, score.canonicalTextSha256);
  assert.equal(layer.canonicalTextUnchanged, true);
  assert.equal(layer.textRewriteAllowed, false);
  assert.equal(layer.boundaries.exposesRawText, false);
  assert.equal(layer.boundaries.deliveryMetadataOnly, true);
  assert.equal(pub.emotionalSheetMusic.length, score.chunks.length);
  assert.ok(pub.moodScore.cueSequence.includes('/'), JSON.stringify(pub.moodScore));
  assert.ok(pub.emotionalSheetMusic.some((cue) => cue.phraseRole === 'warning'), JSON.stringify(pub.emotionalSheetMusic));
  assert.ok(pub.emotionalSheetMusic.every((cue) => cue.text === undefined), 'public cue layer must not expose raw chunk text');
  assert.ok(pub.emotionalSheetMusic.every((cue) => cue.textSha256?.length === 64), JSON.stringify(pub.emotionalSheetMusic));
});

test('STICKBOT_TARS_LIVE_PROSODY_PLAN_SURFACES_CUE_LAYER_PASS', () => {
  const plan = buildTarsProsodyPlan('HOLD. I need evidence before we continue.', { tuning: sanitizeTarsTuning({ moodId: 'mission_brief' }), maxChars: 48 });
  assert.equal(plan.liveProsodyCueLayer.classification, 'STICKBOT_TARS_LIVE_PROSODY_MOOD_SCORE_AND_EMOTIONAL_SHEET_MUSIC_READY');
  assert.equal(plan.liveProsodyCueLayer.canonicalTextSha256, plan.canonicalTextSha256);
  assert.equal(plan.liveProsodyCueLayer.textRewriteAllowed, false);
  assert.equal(plan.liveProsodyCueLayer.boundaries.deliveryMetadataOnly, true);
  assert.ok(plan.liveProsodyCueLayer.moodScore.averageIntensity > 0, JSON.stringify(plan.liveProsodyCueLayer.moodScore));
  assert.equal(plan.chunks.map((chunk) => chunk.text).join(''), 'HOLD. I need evidence before we continue.');
});

test('STICKBOT_TARS_M55_TARS_AND_CASE_SAME_TEXT_RESOLVE_DIFFERENTLY_PASS', () => {
  const matrix = importProsodyMatrixJson({
    schema: 'stickbot-tars-case-prosody-tuning-matrix/v2.0',
    mood_precedence: ['tars_mission_brief_v2', 'case_mission_ops_reserved_v2'],
    moods: [
      {
        id: 'tars_mission_brief_v2',
        label: 'TARS mission brief',
        voice_persona: 'TARS',
        selection_thresholds: { priority: 70, fallback_default: true },
        xtts_params: { temperature: { recommended: 0.63 }, top_p: { recommended: 0.8 }, top_k: { recommended: 42 }, repetition_penalty: { recommended: 10.5 }, length_penalty: { recommended: 1.08 }, speed: { recommended: 1.03 } },
        delivery: { max_chars_per_chunk: 180, sentence_pause_ms: 190, comma_pause_ms: 70, line_break_pause_ms: 260 }
      },
      {
        id: 'case_mission_ops_reserved_v2',
        label: 'CASE mission ops reserved',
        voice_persona: 'CASE',
        selection_thresholds: { priority: 70 },
        xtts_params: { temperature: { recommended: 0.59 }, top_p: { recommended: 0.78 }, top_k: { recommended: 38 }, repetition_penalty: { recommended: 10.8 }, length_penalty: { recommended: 1.1 }, speed: { recommended: 0.99 } },
        delivery: { max_chars_per_chunk: 170, sentence_pause_ms: 250, comma_pause_ms: 100, line_break_pause_ms: 340 }
      }
    ]
  });
  const text = 'Proceeding with docking sequence.';
  const tars = buildProsodyScore(text, { profile, tuning: { moodId: 'tars_mission_brief_v2' }, matrixState: matrix });
  const kase = buildProsodyScore(text, { profile, tuning: { moodId: 'case_mission_ops_reserved_v2' }, matrixState: matrix });
  assert.equal(tars.voicePersona, 'TARS');
  assert.equal(kase.voicePersona, 'CASE');
  assert.notDeepEqual(tars.utteranceXttsParams, kase.utteranceXttsParams);
  assert.ok(kase.chunks[0].effectivePauses.postPauseMs > tars.chunks[0].effectivePauses.postPauseMs);
});
