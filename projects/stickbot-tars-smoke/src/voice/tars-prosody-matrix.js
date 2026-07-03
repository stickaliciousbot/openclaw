import { mkdir, readFile, writeFile, rm } from 'node:fs/promises';
import path from 'node:path';

export const TARS_PROSODY_MATRIX_SCHEMA = 'stickbot-tars-prosody-tuning-matrix/v0.1-derived-local';
export const TARS_PROSODY_MATRIX_STATE_VERSION = 1;

export const TARS_XTTS_PARAMETER_BOUNDS = Object.freeze({
  temperature: Object.freeze({ safeMin: 0.5, safeMax: 0.78, defaultAnchor: 0.62 }),
  topP: Object.freeze({ safeMin: 0.7, safeMax: 0.89, defaultAnchor: 0.8 }),
  topK: Object.freeze({ safeMin: 25, safeMax: 60, defaultAnchor: 40 }),
  repetitionPenalty: Object.freeze({ safeMin: 9.8, safeMax: 12.5, defaultAnchor: 10.8 }),
  lengthPenalty: Object.freeze({ safeMin: 0.92, safeMax: 1.27, defaultAnchor: 1.1 }),
  speed: Object.freeze({ safeMin: 0.82, safeMax: 1.13, defaultAnchor: 0.99 })
});

export const TARS_TEXT_CHUNKING_BOUNDS = Object.freeze({
  hardMaxCharsPerTtsRequest: 210,
  recommendedDefaultMaxCharsPerChunk: 160,
  minPauseMs: 45,
  maxPauseMs: 560,
  rule: 'short_declarative_sentence_chunks_preferred'
});

export const TARS_MOOD_PRECEDENCE = Object.freeze([
  'urgent_alert',
  'fail_closed',
  'confidential_low',
  'skeptical_challenge',
  'reassuring_calm',
  'mission_brief',
  'celebratory_green',
  'curious_diagnostic',
  'dry_wit',
  'confused_recovering',
  'playful_banter',
  'baseline_deadpan',
  'low_power_tired'
]);

const EXPRESSION_TOKENS = Object.freeze({
  tars_baseline_deadpan_v2: '😐',
  case_baseline_reserved_v2: '⬛',
  tars_humor_75_dry_wit_v2: '😏',
  tars_honesty_95_direct_v2: '🎚️',
  tars_mission_brief_v2: '🛰️',
  case_mission_ops_reserved_v2: '◼️',
  tars_urgent_alert_v2: '🚨',
  case_rescue_urgent_v2: '⛑️',
  tars_fail_closed_v2: '⛔',
  tars_confidential_low_v2: '🔒',
  case_reassuring_calm_v2: '🫳',
  tars_curious_diagnostic_v2: '🔍',
  tars_skeptical_challenge_v2: '🤨',
  tars_celebratory_green_v2: '🟢',
  tars_emotional_restraint_v2: '⚫',
  tars_low_power_tired_v2: '🔋',
  tars_confused_recovering_v2: '❓',
  case_quiet_confirmation_v2: '✓',
  urgent_alert: '🚨',
  fail_closed: '⛔',
  confidential_low: '🔒',
  skeptical_challenge: '🤨',
  reassuring_calm: '🫳',
  mission_brief: '🛰️',
  celebratory_green: '🟢',
  curious_diagnostic: '🔍',
  dry_wit: '😏',
  confused_recovering: '❓',
  playful_banter: '🙂',
  baseline_deadpan: '😐',
  low_power_tired: '🔋'
});

const DEFAULT_MOOD_PRESETS = Object.freeze([
  preset('baseline_deadpan', 'Baseline deadpan TARS', 50, 'Default factual voice with no strong emotion signal.', [0.68, 0.82, 45, 10.0, 1.03, 0.98], [180, 230, 90, 320], [0.92, 0.76, 0.14, 0.18]),
  preset('dry_wit', 'Dry wit / sarcastic aside', 60, 'Brief low-risk comic aside; never mock distress.', [0.74, 0.87, 55, 10.2, 1.05, 1.01], [160, 260, 110, 380], [0.90, 0.82, 0.16, 0.22]),
  preset('mission_brief', 'Mission brief / operator mode', 70, 'Procedural work, validation gates, commands, and closeout summaries.', [0.63, 0.80, 42, 10.5, 1.08, 1.03], [200, 190, 70, 260], [0.94, 0.72, 0.12, 0.15]),
  preset('reassuring_calm', 'Reassuring calm', 80, 'Frustration, uncertainty, hardware/network failures, and recovery work.', [0.64, 0.81, 42, 10.0, 0.98, 0.94], [180, 310, 120, 420], [0.93, 0.68, 0.13, 0.12]),
  preset('curious_diagnostic', 'Curious diagnostic', 65, 'Investigative troubleshooting and root-cause analysis.', [0.70, 0.84, 50, 10.0, 1.01, 0.99], [190, 240, 100, 340], [0.92, 0.74, 0.15, 0.18]),
  preset('urgent_alert', 'Urgent alert', 100, 'High-priority safety, security, destructive action, or stop-condition warning.', [0.58, 0.78, 35, 10.8, 1.12, 1.07], [140, 160, 55, 220], [0.96, 0.64, 0.10, 0.10]),
  preset('fail_closed', 'Fail-closed blocker', 95, 'Gate failure, unsafe config, missing evidence, or no-go milestone state.', [0.57, 0.77, 35, 11.0, 1.14, 0.99], [150, 210, 80, 300], [0.96, 0.70, 0.10, 0.08]),
  preset('playful_banter', 'Playful banter', 55, 'Low-risk casual warmth or celebratory riffing.', [0.80, 0.91, 65, 9.8, 0.98, 1.04], [160, 220, 95, 300], [0.90, 0.76, 0.18, 0.25]),
  preset('celebratory_green', 'Celebratory green / pass closeout', 75, 'Milestone PASS, green validation, or preserved artifact closeout.', [0.73, 0.87, 55, 10.0, 1.02, 1.03], [170, 210, 85, 290], [0.92, 0.78, 0.15, 0.20]),
  preset('skeptical_challenge', 'Skeptical challenge', 85, 'Evidence-light shortcut or unsafe assumption challenge.', [0.66, 0.82, 45, 10.4, 1.09, 0.97], [155, 290, 115, 380], [0.93, 0.80, 0.14, 0.16]),
  preset('confidential_low', 'Confidential / low voice', 90, 'Secret-adjacent, private, or local-only boundary checks.', [0.61, 0.80, 40, 10.5, 1.03, 0.92], [150, 330, 130, 440], [0.94, 0.70, 0.12, 0.10]),
  preset('low_power_tired', 'Low-power tired / drained system', 35, 'Rare comic flavor for harmless status moments only.', [0.69, 0.84, 48, 10.2, 0.96, 0.89], [135, 380, 150, 500], [0.88, 0.74, 0.20, 0.24]),
  preset('confused_recovering', 'Confused but recovering', 58, 'Minor mismatch, self-correction, or unknown state acknowledgment.', [0.72, 0.86, 55, 10.0, 1.00, 0.96], [150, 300, 125, 400], [0.91, 0.72, 0.16, 0.20])
]);

function preset(id, label, priority, purpose, xtts, delivery, evals) {
  return Object.freeze({
    id,
    label,
    priority,
    purpose,
    expressionToken: EXPRESSION_TOKENS[id] || '🎚️',
    xttsParams: Object.freeze({
      temperature: xtts[0],
      topP: xtts[1],
      topK: xtts[2],
      repetitionPenalty: xtts[3],
      lengthPenalty: xtts[4],
      speed: xtts[5]
    }),
    delivery: Object.freeze({
      maxCharsPerChunk: delivery[0],
      splitSentences: true,
      sentencePauseMs: delivery[1],
      commaPauseMs: delivery[2],
      lineBreakPauseMs: delivery[3]
    }),
    evaluationThresholds: Object.freeze({
      minIntelligibilityScore: evals[0],
      minTarsLikenessScore: evals[1],
      maxArtifactScore: evals[2],
      maxOveractingScore: evals[3]
    })
  });
}

function clone(obj) {
  return JSON.parse(JSON.stringify(obj));
}

function finite(value, fallback) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function clamp(value, min, max, fallback) {
  return Math.min(max, Math.max(min, finite(value, fallback)));
}

function recommended(value) {
  return value && typeof value === 'object' && !Array.isArray(value) ? value.recommended : value;
}

function safeId(raw, fallback = 'baseline_deadpan') {
  const s = String(raw || '').trim().toLowerCase().replace(/[^a-z0-9_-]+/g, '_').replace(/^_+|_+$/g, '');
  return s ? s.slice(0, 80) : fallback;
}

function safeText(raw, fallback, max = 240) {
  const s = String(raw || '').replace(/\s+/g, ' ').trim();
  return (s || fallback).slice(0, max);
}

function normalizeXttsBounds(raw = {}, fallback = TARS_XTTS_PARAMETER_BOUNDS) {
  const normalize = (name, key = name) => Object.freeze({
    safeMin: finite(raw[key]?.safe_min ?? raw[key]?.safeMin, fallback[name].safeMin),
    safeMax: finite(raw[key]?.safe_max ?? raw[key]?.safeMax, fallback[name].safeMax),
    defaultAnchor: finite(raw[key]?.default_anchor ?? raw[key]?.defaultAnchor, fallback[name].defaultAnchor)
  });
  return {
    temperature: normalize('temperature'),
    topP: normalize('topP', 'top_p'),
    topK: normalize('topK', 'top_k'),
    repetitionPenalty: normalize('repetitionPenalty', 'repetition_penalty'),
    lengthPenalty: normalize('lengthPenalty', 'length_penalty'),
    speed: normalize('speed')
  };
}

function normalizeTextChunking(raw = {}, fallback = TARS_TEXT_CHUNKING_BOUNDS) {
  return {
    hardMaxCharsPerTtsRequest: Math.round(clamp(raw.hard_max_chars_per_tts_request ?? raw.hardMaxCharsPerTtsRequest, 80, 500, fallback.hardMaxCharsPerTtsRequest)),
    recommendedDefaultMaxCharsPerChunk: Math.round(clamp(raw.recommended_default_max_chars_per_chunk ?? raw.recommendedDefaultMaxCharsPerChunk, 60, 360, fallback.recommendedDefaultMaxCharsPerChunk)),
    minPauseMs: Math.round(clamp(raw.min_pause_ms ?? raw.minPauseMs, 0, 1000, fallback.minPauseMs)),
    maxPauseMs: Math.round(clamp(raw.max_pause_ms ?? raw.maxPauseMs, 50, 1200, fallback.maxPauseMs)),
    rule: safeText(raw.chunking_rule || raw.rule, fallback.rule, 180)
  };
}

function sanitizeDelivery(raw = {}, fallback = {}, textChunking = TARS_TEXT_CHUNKING_BOUNDS) {
  return {
    maxCharsPerChunk: Math.round(clamp(
      raw.maxCharsPerChunk ?? raw.max_chars_per_chunk,
      60,
      textChunking.hardMaxCharsPerTtsRequest,
      fallback.maxCharsPerChunk || textChunking.recommendedDefaultMaxCharsPerChunk
    )),
    splitSentences: Boolean(raw.splitSentences ?? raw.split_sentences ?? fallback.splitSentences ?? true),
    sentencePauseMs: Math.round(clamp(raw.sentencePauseMs ?? raw.sentence_pause_ms, textChunking.minPauseMs, textChunking.maxPauseMs, fallback.sentencePauseMs || 230)),
    commaPauseMs: Math.round(clamp(raw.commaPauseMs ?? raw.comma_pause_ms, textChunking.minPauseMs, textChunking.maxPauseMs, fallback.commaPauseMs || 90)),
    lineBreakPauseMs: Math.round(clamp(raw.lineBreakPauseMs ?? raw.line_break_pause_ms, textChunking.minPauseMs, textChunking.maxPauseMs, fallback.lineBreakPauseMs || 320))
  };
}

function sanitizeEvaluationThresholds(raw = {}, fallback = {}) {
  const tarsOrCase = raw.minTarsOrCaseLikenessScore ?? raw.min_tars_or_case_likeness_score ?? raw.minTarsLikenessScore ?? raw.min_tars_likeness_score;
  return {
    minIntelligibilityScore: clamp(raw.minIntelligibilityScore ?? raw.min_intelligibility_score, 0, 1, fallback.minIntelligibilityScore || 0.9),
    minTarsLikenessScore: clamp(tarsOrCase, 0, 1, fallback.minTarsLikenessScore || fallback.minTarsOrCaseLikenessScore || 0.7),
    minTarsOrCaseLikenessScore: clamp(tarsOrCase, 0, 1, fallback.minTarsOrCaseLikenessScore || fallback.minTarsLikenessScore || 0.7),
    maxArtifactScore: clamp(raw.maxArtifactScore ?? raw.max_artifact_score, 0, 1, fallback.maxArtifactScore || 0.18),
    maxOveractingScore: clamp(raw.maxOveractingScore ?? raw.max_overacting_score, 0, 1, fallback.maxOveractingScore || 0.22)
  };
}

function defaultMatrixState(now = new Date()) {
  return {
    schemaVersion: TARS_PROSODY_MATRIX_STATE_VERSION,
    schema: TARS_PROSODY_MATRIX_SCHEMA,
    sourceSchema: 'built_in_default_from_stickbot_tars_prosody_tuning_matrix_v0_1',
    source: 'built_in_default_json',
    updatedAt: now.toISOString(),
    defaultMoodId: 'baseline_deadpan',
    moodPrecedence: [...TARS_MOOD_PRECEDENCE],
    moods: clone(DEFAULT_MOOD_PRESETS),
    bounds: clone(TARS_XTTS_PARAMETER_BOUNDS),
    textChunking: clone(TARS_TEXT_CHUNKING_BOUNDS),
    acceptanceThresholds: defaultAcceptanceThresholds(),
    boundaries: defaultBoundaries()
  };
}

function defaultAcceptanceThresholds() {
  return {
    minIntelligibilityScore: 0.9,
    minTarsLikenessScore: 0.7,
    maxArtifactScore: 0.18,
    maxOveractingScore: 0.22,
    maxUnintendedEmotionScore: 0.2,
    rejectIfAny: [
      'unintelligible_output',
      'unexpected_language_switch',
      'long_silence_or_loop',
      'voice_identity_collapse',
      'unsafe_text_read_aloud'
    ]
  };
}

function defaultBoundaries() {
  return {
    canonicalTextAuthoritative: true,
    textRewriteAllowed: false,
    localOnly: true,
    cloudSpeechAllowed: false,
    browserWebSpeechApiAllowed: false,
    importedJsonIsInstructionAuthority: false
  };
}

function normalizeMood(raw = {}, fallback = getTarsMoodPreset('baseline_deadpan'), bounds = TARS_XTTS_PARAMETER_BOUNDS, textChunking = TARS_TEXT_CHUNKING_BOUNDS) {
  const xtts = raw.xttsParams || raw.xtts_params || {};
  const delivery = raw.delivery || {};
  const evals = raw.evaluationThresholds || raw.evaluation_thresholds || {};
  const id = safeId(raw.id, fallback.id);
  return {
    id,
    label: safeText(raw.label, fallback.label, 120),
    priority: Math.round(clamp(raw.priority ?? raw.selection_thresholds?.priority, 0, 100, fallback.priority || 50)),
    purpose: safeText(raw.purpose, fallback.purpose, 300),
    voicePersona: safeText(raw.voicePersona ?? raw.voice_persona, fallback.voicePersona || 'TARS', 24),
    expressionToken: safeText(raw.expressionToken || raw.expression_token, EXPRESSION_TOKENS[id] || fallback.expressionToken || '🎚️', 8),
    xttsParams: sanitizeXttsParams(xtts, fallback, bounds),
    delivery: sanitizeDelivery(delivery, fallback.delivery, textChunking),
    evaluationThresholds: sanitizeEvaluationThresholds(evals, fallback.evaluationThresholds)
  };
}

export function importProsodyMatrixJson(input = {}, now = new Date()) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) {
    const e = new Error('TARS_PROSODY_MATRIX_IMPORT_FAIL: JSON root must be an object');
    e.classification = 'TARS_PROSODY_MATRIX_IMPORT_FAIL';
    e.statusCode = 400;
    throw e;
  }
  const defaults = defaultMatrixState(now);
  const bounds = normalizeXttsBounds(input.global_parameter_bounds || input.bounds || {}, defaults.bounds);
  const textChunking = normalizeTextChunking(input.global_text_chunking || input.textChunking || input.text_chunking || {}, defaults.textChunking);
  const rawMoods = Array.isArray(input.moods) ? input.moods : [];
  if (!rawMoods.length) {
    const e = new Error('TARS_PROSODY_MATRIX_IMPORT_FAIL: JSON must contain a moods array');
    e.classification = 'TARS_PROSODY_MATRIX_IMPORT_FAIL';
    e.statusCode = 400;
    throw e;
  }
  if (rawMoods.length > 40) {
    const e = new Error('TARS_PROSODY_MATRIX_IMPORT_FAIL: too many moods; max 40');
    e.classification = 'TARS_PROSODY_MATRIX_IMPORT_FAIL';
    e.statusCode = 400;
    throw e;
  }

  const fallbackById = new Map(defaults.moods.map((mood) => [mood.id, mood]));
  const explicitFallbackId = rawMoods.map((mood) => safeId(mood?.id, '')).find((id, index) => id && rawMoods[index]?.selection_thresholds?.fallback_default === true);
  const seen = new Set();
  const moods = [];
  for (const raw of rawMoods) {
    const id = safeId(raw.id, '');
    if (!id || seen.has(id)) continue;
    seen.add(id);
    moods.push(normalizeMood(raw, fallbackById.get(id) || defaults.moods.find((mood) => mood.id === 'baseline_deadpan'), bounds, textChunking));
  }
  if (!explicitFallbackId && !moods.some((mood) => mood.id === 'baseline_deadpan')) {
    moods.push(defaults.moods.find((mood) => mood.id === 'baseline_deadpan'));
  }

  const precedence = Array.isArray(input.mood_precedence)
    ? input.mood_precedence.map((id) => safeId(id, '')).filter((id) => id && moods.some((mood) => mood.id === id))
    : defaults.moodPrecedence.filter((id) => moods.some((mood) => mood.id === id));
  for (const mood of moods) if (!precedence.includes(mood.id)) precedence.push(mood.id);

  return {
    schemaVersion: TARS_PROSODY_MATRIX_STATE_VERSION,
    schema: TARS_PROSODY_MATRIX_SCHEMA,
    sourceSchema: safeText(input.schema, 'uploaded_json', 120),
    source: 'uploaded_json_sanitized_local_reference',
    updatedAt: now.toISOString(),
    defaultMoodId: explicitFallbackId && moods.some((mood) => mood.id === explicitFallbackId)
      ? explicitFallbackId
      : (moods.some((mood) => mood.id === 'baseline_deadpan') ? 'baseline_deadpan' : moods[0].id),
    moodPrecedence: precedence,
    moods,
    bounds: clone(bounds),
    textChunking: clone(textChunking),
    acceptanceThresholds: defaultAcceptanceThresholds(),
    boundaries: defaultBoundaries()
  };
}

function matrixStateOrDefault(matrixState) {
  if (!matrixState || !Array.isArray(matrixState.moods) || !matrixState.moods.length) return defaultMatrixState();
  return matrixState;
}

export function prosodyMatrixStatePath(workspace) {
  return path.join(workspace, 'projects', 'stickbot-tars-smoke', 'state', 'prosody-matrix.json');
}

export async function loadTarsProsodyMatrixState(workspace) {
  const file = prosodyMatrixStatePath(workspace);
  try {
    const raw = JSON.parse(await readFile(file, 'utf8'));
    if (!raw || !Array.isArray(raw.moods)) return defaultMatrixState();
    return { ...defaultMatrixState(), ...raw, boundaries: defaultBoundaries() };
  } catch (e) {
    if (e.code !== 'ENOENT') throw e;
    return defaultMatrixState();
  }
}

export async function saveTarsProsodyMatrixState(workspace, state) {
  const file = prosodyMatrixStatePath(workspace);
  await mkdir(path.dirname(file), { recursive: true });
  await writeFile(file, `${JSON.stringify(state, null, 2)}\n`, 'utf8');
  return state;
}

export async function uploadTarsProsodyMatrixJson(workspace, input, now = new Date()) {
  const state = importProsodyMatrixJson(input.matrix || input, now);
  return saveTarsProsodyMatrixState(workspace, state);
}

export async function resetTarsProsodyMatrixJson(workspace) {
  const file = prosodyMatrixStatePath(workspace);
  await rm(file, { force: true });
  return defaultMatrixState();
}

export function listTarsMoodPresets(matrixState = null) {
  return clone(matrixStateOrDefault(matrixState).moods);
}

export function getTarsMoodPreset(id = 'baseline_deadpan', matrixState = null) {
  const state = matrixStateOrDefault(matrixState);
  const requested = safeId(id, state.defaultMoodId || 'baseline_deadpan');
  const hit = state.moods.find((mood) => mood.id === requested)
    || state.moods.find((mood) => mood.id === state.defaultMoodId)
    || state.moods.find((mood) => mood.id === 'baseline_deadpan')
    || state.moods[0];
  return clone(hit);
}

export function sanitizeXttsParams(params = {}, fallbackPreset = getTarsMoodPreset('baseline_deadpan'), bounds = TARS_XTTS_PARAMETER_BOUNDS) {
  const base = fallbackPreset.xttsParams || getTarsMoodPreset('baseline_deadpan').xttsParams;
  return {
    temperature: clamp(recommended(params.temperature), bounds.temperature.safeMin, bounds.temperature.safeMax, base.temperature),
    topP: clamp(recommended(params.topP ?? params.top_p), bounds.topP.safeMin, bounds.topP.safeMax, base.topP),
    topK: Math.round(clamp(recommended(params.topK ?? params.top_k), bounds.topK.safeMin, bounds.topK.safeMax, base.topK)),
    repetitionPenalty: clamp(recommended(params.repetitionPenalty ?? params.repetition_penalty), bounds.repetitionPenalty.safeMin, bounds.repetitionPenalty.safeMax, base.repetitionPenalty),
    lengthPenalty: clamp(recommended(params.lengthPenalty ?? params.length_penalty), bounds.lengthPenalty.safeMin, bounds.lengthPenalty.safeMax, base.lengthPenalty),
    speed: clamp(recommended(params.speed), bounds.speed.safeMin, bounds.speed.safeMax, base.speed)
  };
}

export function deriveMoodMatrixSelection(input = {}, matrixState = null) {
  const state = matrixStateOrDefault(matrixState);
  const preset = getTarsMoodPreset(input.moodId || input.id || matrixStateOrDefault(matrixState).defaultMoodId || 'baseline_deadpan', matrixState);
  return {
    schema: TARS_PROSODY_MATRIX_SCHEMA,
    moodId: preset.id,
    label: preset.label,
    priority: preset.priority,
    purpose: preset.purpose,
    voicePersona: preset.voicePersona || 'TARS',
    expressionToken: preset.expressionToken,
    source: state.source,
    xttsParams: sanitizeXttsParams(input.xttsParams || input.xtts || {}, preset, state.bounds || TARS_XTTS_PARAMETER_BOUNDS),
    recommendedXttsParams: preset.xttsParams,
    delivery: sanitizeDelivery(input.delivery || {}, preset.delivery, state.textChunking || TARS_TEXT_CHUNKING_BOUNDS),
    recommendedDelivery: preset.delivery,
    evaluationThresholds: preset.evaluationThresholds,
    boundaries: defaultBoundaries()
  };
}

export function publicProsodyMatrixSummary(matrixState = null) {
  const state = matrixStateOrDefault(matrixState);
  return {
    schema: state.schema || TARS_PROSODY_MATRIX_SCHEMA,
    schemaVersion: state.schemaVersion || TARS_PROSODY_MATRIX_STATE_VERSION,
    sourceSchema: state.sourceSchema,
    source: state.source,
    updatedAt: state.updatedAt,
    defaultMoodId: state.defaultMoodId,
    bounds: state.bounds || clone(TARS_XTTS_PARAMETER_BOUNDS),
    textChunking: state.textChunking || clone(TARS_TEXT_CHUNKING_BOUNDS),
    moodPrecedence: [...(state.moodPrecedence || TARS_MOOD_PRECEDENCE)],
    moods: listTarsMoodPresets(state),
    acceptanceThresholds: state.acceptanceThresholds || defaultAcceptanceThresholds(),
    boundaries: defaultBoundaries(),
    controls: {
      importJson: true,
      exportJson: true,
      resetToDefaultJson: true,
      dynamicMoodSwitching: true,
      prosodySheetMusic: true
    }
  };
}
