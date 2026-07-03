import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { deriveMoodMatrixSelection, loadTarsProsodyMatrixState, publicProsodyMatrixSummary } from './tars-prosody-matrix.js';

export const TARS_TUNING_SCHEMA_VERSION = 1;

export const FACTORY_TARS_TUNING = Object.freeze({
  schemaVersion: TARS_TUNING_SCHEMA_VERSION,
  id: 'tars-tuning-factory-v1',
  label: 'Factory TARS private-demo baseline',
  parameters: Object.freeze({
    pitch: 0.50,
    timbre: 0.50,
    speed: 0.46,
    compression: 0.42,
    verbalGait: 0.58,
    verbosity: 0.48,
    clip: 0.18
  }),
  randomness: Object.freeze({
    global: 0.12,
    threshold: 0.74,
    pitch: 0.08,
    timbre: 0.06,
    speed: 0.05,
    compression: 0.04,
    verbalGait: 0.08,
    verbosity: 0.02,
    clip: 0.01
  }),
  moodId: 'baseline_deadpan',
  boundaries: Object.freeze({
    canonicalTextAuthoritative: true,
    textRewriteAllowed: false,
    deliveryMetadataOnly: true
  })
});

const PARAMETER_KEYS = Object.freeze(Object.keys(FACTORY_TARS_TUNING.parameters));
const RANDOMNESS_KEYS = Object.freeze(Object.keys(FACTORY_TARS_TUNING.randomness));

function clone(obj) {
  return JSON.parse(JSON.stringify(obj));
}

function finiteNumber(value, fallback) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function clamp01(value, fallback) {
  return Math.min(1, Math.max(0, finiteNumber(value, fallback)));
}

function clampRange(value, min, max, fallback) {
  return Math.min(max, Math.max(min, finiteNumber(value, fallback)));
}

function round(value, decimals = 2) {
  return Number(value.toFixed(decimals));
}

export function deriveAudibleXttsParamsFromTuning(matrixXtts = {}, parameters = {}, randomness = {}) {
  const base = FACTORY_TARS_TUNING.parameters;
  const baseRandom = FACTORY_TARS_TUNING.randomness;
  const p = { ...base, ...(parameters || {}) };
  const r = { ...baseRandom, ...(randomness || {}) };
  const globalDelta = r.global - baseRandom.global;
  const thresholdDelta = r.threshold - baseRandom.threshold;
  const speedFromSlider = (matrixXtts.speed ?? 0.98) + (p.speed - base.speed) * 0.24;
  return {
    temperature: round(clampRange((matrixXtts.temperature ?? 0.68) + globalDelta * 0.35 + (p.verbalGait - base.verbalGait) * 0.08, 0.55, 0.9, 0.68), 2),
    topP: round(clampRange((matrixXtts.topP ?? 0.82) + globalDelta * 0.12 - thresholdDelta * 0.04, 0.75, 0.95, 0.82), 2),
    topK: Math.round(clampRange((matrixXtts.topK ?? 45) + globalDelta * 45 + (p.verbalGait - base.verbalGait) * 18, 35, 80, 45)),
    repetitionPenalty: round(clampRange((matrixXtts.repetitionPenalty ?? 10) + (p.clip - base.clip) * 2.0 + (p.compression - base.compression) * 1.2, 8, 12, 10), 2),
    lengthPenalty: round(clampRange((matrixXtts.lengthPenalty ?? 1.03) + (p.verbosity - base.verbosity) * 0.18, 0.9, 1.15, 1.03), 2),
    speed: round(clampRange(speedFromSlider, 0.88, 1.12, matrixXtts.speed ?? 0.98), 2)
  };
}

function normalizeTuning(input = {}, fallback = FACTORY_TARS_TUNING, matrixState = null) {
  const base = fallback || FACTORY_TARS_TUNING;
  const rawParameters = input.parameters || input;
  const rawRandomness = input.randomness || {};
  const rawMoodId = input.moodId || input.matrix?.moodId || input.mood?.moodId || base.moodId || 'baseline_deadpan';
  const parameters = {};
  const randomness = {};
  for (const key of PARAMETER_KEYS) {
    parameters[key] = clamp01(rawParameters[key], base.parameters[key]);
  }
  for (const key of RANDOMNESS_KEYS) {
    randomness[key] = clamp01(rawRandomness[key], base.randomness[key]);
  }
  return {
    schemaVersion: TARS_TUNING_SCHEMA_VERSION,
    id: typeof input.id === 'string' && input.id.trim() ? input.id.trim().slice(0, 80) : base.id,
    label: typeof input.label === 'string' && input.label.trim() ? input.label.trim().slice(0, 120) : base.label,
    parameters,
    randomness,
    moodId: deriveMoodMatrixSelection({ moodId: rawMoodId }, matrixState).moodId,
    matrix: deriveMoodMatrixSelection({
      moodId: rawMoodId,
      xttsParams: input.xttsParams || input.matrix?.xttsParams || input.mood?.xttsParams || {},
      delivery: input.delivery || input.matrix?.delivery || input.mood?.delivery || {}
    }, matrixState),
    boundaries: clone(FACTORY_TARS_TUNING.boundaries),
    updatedAt: typeof input.updatedAt === 'string' ? input.updatedAt : undefined
  };
}

export function sanitizeTarsTuning(input = {}) {
  return normalizeTuning(input, FACTORY_TARS_TUNING);
}

export function defaultTarsTuningState(now = new Date()) {
  const factory = sanitizeTarsTuning(FACTORY_TARS_TUNING);
  const stamped = { ...factory, updatedAt: now.toISOString() };
  return {
    schemaVersion: TARS_TUNING_SCHEMA_VERSION,
    factory,
    baseline: { ...stamped, id: 'tars-tuning-baseline-v1', label: 'User baseline' },
    active: { ...stamped, id: 'tars-tuning-active-v1', label: 'Active tuning' }
  };
}

export function tuningStatePath(workspace) {
  return path.join(workspace, 'projects', 'stickbot-tars-smoke', 'state', 'prosody-tuning.json');
}

export async function loadTarsTuningState(workspace) {
  const file = tuningStatePath(workspace);
  const matrixState = await loadTarsProsodyMatrixState(workspace);
  try {
    const raw = JSON.parse(await readFile(file, 'utf8'));
    const state = defaultTarsTuningState();
    return {
      schemaVersion: TARS_TUNING_SCHEMA_VERSION,
      factory: normalizeTuning(state.factory, FACTORY_TARS_TUNING, matrixState),
      baseline: normalizeTuning(raw.baseline || state.baseline, state.baseline, matrixState),
      active: normalizeTuning(raw.active || state.active, state.active, matrixState),
      matrixState
    };
  } catch (e) {
    if (e.code !== 'ENOENT') throw e;
    const state = defaultTarsTuningState();
    return {
      ...state,
      factory: normalizeTuning(state.factory, FACTORY_TARS_TUNING, matrixState),
      baseline: normalizeTuning(state.baseline, state.baseline, matrixState),
      active: normalizeTuning(state.active, state.active, matrixState),
      matrixState
    };
  }
}

export async function saveTarsTuningState(workspace, state) {
  const file = tuningStatePath(workspace);
  const persisted = {
    schemaVersion: state.schemaVersion,
    factory: state.factory,
    baseline: state.baseline,
    active: state.active
  };
  await mkdir(path.dirname(file), { recursive: true });
  await writeFile(file, `${JSON.stringify(persisted, null, 2)}\n`, 'utf8');
  return state;
}

export async function updateActiveTarsTuning(workspace, patch = {}, now = new Date()) {
  const state = await loadTarsTuningState(workspace);
  const nextMoodId = patch.moodId || patch.matrix?.moodId || state.active.moodId;
  const moodChanged = nextMoodId !== state.active.moodId;
  const merged = {
    ...state.active,
    ...patch,
    parameters: { ...state.active.parameters, ...(patch.parameters || {}) },
    randomness: { ...state.active.randomness, ...(patch.randomness || {}) },
    moodId: nextMoodId,
    matrix: patch.matrix || (moodChanged ? undefined : state.active.matrix),
    id: 'tars-tuning-active-v1',
    label: patch.label || state.active.label,
    updatedAt: now.toISOString()
  };
  state.active = normalizeTuning(merged, state.active, state.matrixState);
  state.active.updatedAt = now.toISOString();
  return saveTarsTuningState(workspace, state);
}

export async function resetActiveTarsTuning(workspace, now = new Date()) {
  const state = await loadTarsTuningState(workspace);
  state.active = normalizeTuning({
    ...state.factory,
    id: 'tars-tuning-active-v1',
    label: 'Active tuning',
    updatedAt: now.toISOString()
  }, state.factory, state.matrixState);
  state.active.updatedAt = now.toISOString();
  return saveTarsTuningState(workspace, state);
}

export async function establishTarsTuningBaseline(workspace, now = new Date()) {
  const state = await loadTarsTuningState(workspace);
  state.baseline = normalizeTuning({
    ...state.active,
    id: 'tars-tuning-baseline-v1',
    label: 'User baseline',
    updatedAt: now.toISOString()
  }, state.active, state.matrixState);
  state.baseline.updatedAt = now.toISOString();
  return saveTarsTuningState(workspace, state);
}

export async function restoreTarsTuningBaseline(workspace, now = new Date()) {
  const state = await loadTarsTuningState(workspace);
  state.active = normalizeTuning({
    ...state.baseline,
    id: 'tars-tuning-active-v1',
    label: 'Active tuning',
    updatedAt: now.toISOString()
  }, state.baseline, state.matrixState);
  state.active.updatedAt = now.toISOString();
  return saveTarsTuningState(workspace, state);
}

export function deriveDeliveryFromTuning(profileDelivery, tuning = FACTORY_TARS_TUNING) {
  const active = tuning?.matrix?.moodId
    ? { ...sanitizeTarsTuning(tuning), moodId: tuning.moodId, matrix: tuning.matrix }
    : sanitizeTarsTuning(tuning);
  const p = active.parameters;
  const r = active.randomness;
  const speedScale = 0.78 + (p.speed * 0.54);
  const pitchShiftSemitones = -7 + (p.pitch * 8);
  return {
    ...profileDelivery,
    normalRate: Number((profileDelivery.normalRate * speedScale).toFixed(3)),
    statusRate: Number((profileDelivery.statusRate * speedScale).toFixed(3)),
    warningRate: Number((profileDelivery.warningRate * (0.84 + p.verbalGait * 0.34)).toFixed(3)),
    pitchShiftSemitones: Number(pitchShiftSemitones.toFixed(2)),
    pitchVariance: Number((0.02 + r.pitch * 0.42 + r.global * 0.18).toFixed(3)),
    energy: Number((0.35 + p.compression * 0.45).toFixed(3)),
    breathiness: Number((0.02 + p.timbre * 0.14).toFixed(3)),
    expressiveness: Number((0.08 + p.verbalGait * 0.30 + r.global * 0.12).toFixed(3)),
    compression: Number(p.compression.toFixed(3)),
    timbre: Number(p.timbre.toFixed(3)),
    verbalGait: Number(p.verbalGait.toFixed(3)),
    verbosity: Number(p.verbosity.toFixed(3)),
    clipGuard: Number(p.clip.toFixed(3)),
    randomness: clone(active.randomness),
    moodId: active.moodId,
    moodLabel: active.matrix.label,
    xttsParams: deriveAudibleXttsParamsFromTuning(active.matrix.xttsParams, p, r),
    recommendedXttsParams: clone(active.matrix.recommendedXttsParams),
    maxCharsPerChunk: active.matrix.delivery.maxCharsPerChunk,
    sentencePauseMs: active.matrix.delivery.sentencePauseMs,
    commaPauseMs: active.matrix.delivery.commaPauseMs,
    lineBreakPauseMs: active.matrix.delivery.lineBreakPauseMs,
    splitSentences: active.matrix.delivery.splitSentences,
    tuningId: active.id,
    tuningUpdatedAt: active.updatedAt || null,
    textRewriteAllowed: false
  };
}

export function publicTuningSummary(state) {
  const matrix = publicProsodyMatrixSummary(state.matrixState);
  return {
    schemaVersion: TARS_TUNING_SCHEMA_VERSION,
    factory: state.factory,
    baseline: state.baseline,
    active: state.active,
    controls: {
      parameters: PARAMETER_KEYS,
      randomness: RANDOMNESS_KEYS,
      range: { min: 0, max: 1, step: 0.01 },
      moodPresets: matrix.moods.map((mood) => ({
        id: mood.id,
        label: mood.label,
        priority: mood.priority,
        purpose: mood.purpose,
        expressionToken: mood.expressionToken
      })),
      resetToFactory: true,
      establishBaseline: true,
      restoreBaseline: true
    },
    matrix,
    boundaries: clone(FACTORY_TARS_TUNING.boundaries)
  };
}
