import { TARS_XTTS_PARAMETER_BOUNDS } from '../voice/tars-prosody-matrix.js';
import { FACTORY_TARS_TUNING } from '../voice/tars-prosody-tuning.js';

const ROLE_DELTAS_TARS = Object.freeze({
  status: { temperature: -0.02, speed: 0.01 },
  blocker: { temperature: -0.06, topP: -0.04, speed: -0.01 },
  warning: { temperature: -0.08, topP: -0.05, lengthPenalty: 0.06, speed: 0.04 },
  instruction: { temperature: -0.03, lengthPenalty: 0.04, speed: 0.02 },
  evidence: { temperature: 0, speed: -0.01 },
  aside: { temperature: 0.04, topP: 0.03, speed: -0.02 },
  punchline: { temperature: 0.04, topP: 0.03, speed: -0.03 },
  confirmation: { temperature: -0.02, topP: -0.01, speed: 0 },
  uncertainty: { temperature: -0.02, topP: -0.02, speed: -0.02 },
  recovery: { temperature: -0.01, speed: -0.01 },
  question: { temperature: 0.01, topP: 0.01, speed: -0.01 },
  closeout: { temperature: -0.02, speed: 0.01 }
});

const ROLE_DELTAS_CASE = Object.freeze({
  status: { temperature: -0.04, topP: -0.02, speed: -0.01 },
  blocker: { temperature: -0.08, topP: -0.05, speed: -0.03 },
  warning: { temperature: -0.09, topP: -0.06, lengthPenalty: 0.06, speed: 0.02 },
  instruction: { temperature: -0.05, lengthPenalty: 0.04, speed: 0 },
  evidence: { temperature: -0.02, speed: -0.02 },
  aside: { temperature: 0.0, topP: -0.01, speed: -0.03 },
  punchline: { temperature: 0.0, topP: -0.01, speed: -0.03 },
  confirmation: { temperature: -0.04, topP: -0.02, speed: -0.02 },
  uncertainty: { temperature: -0.04, topP: -0.03, speed: -0.03 },
  recovery: { temperature: -0.03, speed: -0.02 },
  question: { temperature: -0.01, topP: -0.01, speed: -0.02 },
  closeout: { temperature: -0.04, speed: -0.01 }
});

const KEY_MAP = Object.freeze({
  temperature: 'temperature',
  topP: 'topP',
  topK: 'topK',
  repetitionPenalty: 'repetitionPenalty',
  lengthPenalty: 'lengthPenalty',
  speed: 'speed'
});

function round(value, decimals = 2) {
  return Number(value.toFixed(decimals));
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function addDelta(target, key, amount) {
  target[key] = round((target[key] || 0) + amount, key === 'topK' ? 0 : 3);
}

export function phraseRoleDeltas(role, voicePersona = 'TARS') {
  const table = voicePersona === 'CASE' ? ROLE_DELTAS_CASE : ROLE_DELTAS_TARS;
  return { ...(table[role] || table.evidence) };
}

export function sentenceFeatureDeltas(features = {}) {
  const d = {};
  if (features.technicalDensity > 0.18) {
    addDelta(d, 'temperature', -0.015);
    addDelta(d, 'topP', -0.015);
    addDelta(d, 'lengthPenalty', 0.015);
  }
  if (features.punctuationDensity > 0.55) addDelta(d, 'speed', -0.01);
  if (features.shortStatusSentence) addDelta(d, 'speed', 0.01);
  if (features.question) addDelta(d, 'temperature', 0.01);
  if (features.uncertainty) addDelta(d, 'topP', -0.02);
  return d;
}

export function userTuningDeltas(tuning = {}) {
  const safeTuning = tuning || {};
  const base = FACTORY_TARS_TUNING.parameters;
  const p = { ...base, ...(safeTuning.parameters || {}) };
  const rBase = FACTORY_TARS_TUNING.randomness;
  const r = { ...rBase, ...(safeTuning.randomness || {}) };
  return {
    temperature: round((r.global - rBase.global) * 0.18 + (p.verbalGait - base.verbalGait) * 0.04, 3),
    topP: round((r.global - rBase.global) * 0.06 - (r.threshold - rBase.threshold) * 0.03, 3),
    topK: Math.round((r.global - rBase.global) * 24 + (p.verbalGait - base.verbalGait) * 10),
    repetitionPenalty: round((p.clip - base.clip) * 1.0 + (p.compression - base.compression) * 0.6, 3),
    lengthPenalty: round((p.verbosity - base.verbosity) * 0.09, 3),
    speed: round((p.speed - base.speed) * 0.12, 3)
  };
}

export function combineDeltas(...parts) {
  const out = {};
  for (const part of parts) {
    for (const [key, value] of Object.entries(part || {})) {
      if (!Object.prototype.hasOwnProperty.call(KEY_MAP, key)) continue;
      addDelta(out, key, Number(value) || 0);
    }
  }
  return out;
}

export function resolveEffectiveXtts({ baseXtts = {}, phraseRole = 'evidence', features = {}, tuning = {}, voiceIdentity = {}, bounds = TARS_XTTS_PARAMETER_BOUNDS } = {}) {
  const role = phraseRoleDeltas(phraseRole, voiceIdentity.voicePersona || 'TARS');
  const feature = sentenceFeatureDeltas(features);
  const user = userTuningDeltas(tuning);
  const deltas = combineDeltas(role, feature, user);
  const effective = {};
  const clampEvents = [];
  for (const key of Object.keys(KEY_MAP)) {
    const bound = bounds[key] || TARS_XTTS_PARAMETER_BOUNDS[key];
    const base = Number(baseXtts[key] ?? bound.defaultAnchor);
    const raw = base + Number(deltas[key] || 0);
    const identityDelta = key === 'temperature'
      ? voiceIdentity.allowedTemperatureDelta
      : key === 'topP'
        ? voiceIdentity.allowedTopPDelta
        : key === 'speed'
          ? voiceIdentity.allowedSpeedDelta
          : null;
    const identityMin = identityDelta == null ? bound.safeMin : Math.max(bound.safeMin, base - identityDelta);
    const identityMax = identityDelta == null ? bound.safeMax : Math.min(bound.safeMax, base + identityDelta);
    const value = clamp(raw, identityMin, identityMax);
    if (value !== raw) clampEvents.push({ key, raw: round(raw, 3), clamped: round(value, key === 'topK' ? 0 : 3), min: identityMin, max: identityMax });
    effective[key] = key === 'topK' ? Math.round(value) : round(value, 2);
  }
  return { baseXtts: { ...baseXtts }, roleDeltas: role, featureDeltas: feature, userTuningDeltas: user, deltas, effectiveXtts: effective, clampEvents };
}

export function averageEffectiveXtts(chunks = []) {
  if (!chunks.length) return null;
  const keys = Object.keys(KEY_MAP);
  const out = {};
  for (const key of keys) {
    const total = chunks.reduce((sum, c) => sum + Number(c.effectiveXtts?.[key] ?? 0), 0);
    out[key] = key === 'topK' ? Math.round(total / chunks.length) : round(total / chunks.length, 2);
  }
  return out;
}
