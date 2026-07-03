import crypto from 'node:crypto';
import { loadTarsProsodyProfile } from './tars-prosody-profile.js';
import { annotateTarsSalience, summarizeSalience } from './tars-salience-annotator.js';
import { chunkTarsSentences, reconstructChunks } from './tars-sentence-chunker.js';
import { deriveDeliveryFromTuning, sanitizeTarsTuning } from './tars-prosody-tuning.js';
import { deriveMoodMatrixSelection } from './tars-prosody-matrix.js';
import { buildProsodyScore, publicProsodyScoreSummary } from '../prosody/prosody-score-engine.js';
import { buildLiveProsodyCueLayer, publicLiveProsodyCueLayer } from '../prosody/live-prosody-cue-layer.js';

const SECRET_PATTERNS = [
  /\bBearer\s+[A-Za-z0-9._~+/=-]{16,}\b/i,
  /\bsk-[A-Za-z0-9_-]{16,}\b/,
  /\b(?:api[_-]?key|token|secret|password)\s*[:=]\s*[^\s]{8,}/i,
  /-----BEGIN [A-Z ]*PRIVATE KEY-----/
];

function sha256(text) {
  return crypto.createHash('sha256').update(text).digest('hex');
}

export function assertCanonicalTextUnchanged(text, chunks) {
  const reconstructed = reconstructChunks(chunks);
  if (reconstructed !== text) {
    const e = new Error('TARS prosody chunk reconstruction changed canonical text.');
    e.classification = 'TARS_CANONICAL_TEXT_CHANGED_FAIL';
    e.expectedSha256 = sha256(text);
    e.actualSha256 = sha256(reconstructed);
    throw e;
  }
  return true;
}

export function inspectNoSecretSpeech(text) {
  const hits = [];
  for (const pattern of SECRET_PATTERNS) {
    const m = text.match(pattern);
    if (m) hits.push({ kind: 'secret_like_pattern', start: m.index ?? 0, end: (m.index ?? 0) + m[0].length });
  }
  return { ok: hits.length === 0, hits };
}

function scoreChunkMood(text, activeMoodId = 'baseline_deadpan') {
  const s = String(text || '');
  const cues = [];
  const hit = (id, pattern, cue, intensity = 0.7) => {
    if (pattern.test(s)) cues.push({ moodId: id, cue, intensity });
  };
  hit('urgent_alert', /\b(STOP|ABORT|URGENT|DANGER|DESTRUCTIVE|SECURITY|EXPOSURE)\b/i, 'urgent_or_safety_language', 0.95);
  hit('fail_closed', /\b(FAIL|FAILED|BLOCKED|HOLD|NO-GO|MISSING EVIDENCE|UNSAFE)\b/i, 'fail_closed_or_blocker_language', 0.9);
  hit('confidential_low', /\b(secret|private|credential|token|password|redact|raw transcript)\b/i, 'privacy_or_secret_adjacent_language', 0.85);
  hit('skeptical_challenge', /\b(assumption|shortcut|unverified|evidence gap|not enough evidence|risky)\b/i, 'skeptical_evidence_language', 0.75);
  hit('reassuring_calm', /\b(frustrating|stress|stuck|recovery|we caught|calm|safe path)\b/i, 'reassurance_or_recovery_language', 0.68);
  hit('mission_brief', /\b(step|plan|validation|gate|command|milestone|classification|artifact|next)\b/i, 'operator_or_mission_language', 0.65);
  hit('celebratory_green', /\b(PASS|READY|green|success|validated|well done|nice)\b/i, 'success_or_pass_language', 0.72);
  hit('curious_diagnostic', /\b(why|unknown|diagnostic|investigate|root cause|log|trace|probe)\b/i, 'diagnostic_language', 0.62);
  hit('dry_wit', /\b(humor|joke|classic|naturally|obviously)\b/i, 'dry_wit_language', 0.55);
  hit('confused_recovering', /\b(correction|actually|wait|mismatch|recovering|unclear)\b/i, 'correction_or_ambiguity_language', 0.58);
  if (!cues.length) return { moodId: activeMoodId || 'baseline_deadpan', intensity: 0.35, cues: ['active_or_baseline_fallback'] };
  cues.sort((a, b) => b.intensity - a.intensity);
  return { moodId: cues[0].moodId, intensity: cues[0].intensity, cues: cues.map((c) => c.cue) };
}

export function buildTarsProsodySheet(chunks, { activeMoodId = 'baseline_deadpan', activeMatrix = null, matrixState = null } = {}) {
  return chunks.map((chunk) => {
    const scored = scoreChunkMood(chunk.text, activeMoodId);
    const selection = activeMatrix?.moodId === scored.moodId
      ? activeMatrix
      : deriveMoodMatrixSelection({ moodId: scored.moodId }, matrixState);
    return {
      chunkIndex: chunk.index,
      start: chunk.start,
      end: chunk.end,
      textSha256: sha256(chunk.text),
      moodId: selection.moodId,
      moodLabel: selection.label,
      expressionToken: selection.expressionToken,
      intensity: Number(scored.intensity.toFixed(2)),
      cues: scored.cues,
      xttsParams: selection.xttsParams,
      delivery: selection.delivery,
      pauseAfterMs: chunk.pauseAfterMs,
      canonicalTextUnchanged: true,
      textRewriteAllowed: false
    };
  });
}

export function buildTarsProsodyPlan(text, { profile = loadTarsProsodyProfile(), tuning = null, matrixState = null, maxChars = 220 } = {}) {
  const canonicalText = String(text ?? '');
  const activeTuning = tuning
    ? (tuning.matrix?.moodId ? { ...sanitizeTarsTuning(tuning), moodId: tuning.moodId, matrix: tuning.matrix } : sanitizeTarsTuning(tuning))
    : null;
  const matrixMaxChars = activeTuning?.matrix?.delivery?.maxCharsPerChunk;
  const effectiveMaxChars = matrixMaxChars ? Math.min(maxChars, matrixMaxChars) : maxChars;
  const chunks = chunkTarsSentences(canonicalText, profile, { maxChars: effectiveMaxChars });
  assertCanonicalTextUnchanged(canonicalText, chunks);
  const salience = annotateTarsSalience(canonicalText, profile);
  const noSecretSpeech = inspectNoSecretSpeech(canonicalText);
  const canonicalTextSha256 = sha256(canonicalText);
  const delivery = activeTuning ? deriveDeliveryFromTuning(profile.delivery, activeTuning) : profile.delivery;
  const prosodyScore = buildProsodyScore(canonicalText, {
    profile,
    tuning: activeTuning,
    matrixState,
    maxChars: effectiveMaxChars
  });
  const scoredDelivery = {
    ...delivery,
    baseXttsParams: prosodyScore.baseXtts,
    presetBaseXttsParams: prosodyScore.presetBaseXtts,
    xttsParams: prosodyScore.utteranceXttsParams,
    scoreEngineClassification: prosodyScore.classification
  };
  const activeSheetMatrix = activeTuning?.matrix
    ? { ...activeTuning.matrix, xttsParams: scoredDelivery.xttsParams }
    : null;
  const legacySheet = buildTarsProsodySheet(chunks, {
    activeMoodId: activeTuning?.moodId || 'baseline_deadpan',
    activeMatrix: activeSheetMatrix,
    matrixState
  });
  const liveProsodyCueLayer = buildLiveProsodyCueLayer(prosodyScore);
  const prosodySheet = prosodyScore.chunks.map((entry, index) => ({
    ...(legacySheet[index] || {}),
    chunkIndex: entry.chunkIndex,
    start: entry.start,
    end: entry.end,
    textSha256: entry.textSha256,
    moodId: prosodyScore.moodId,
    moodLabel: prosodyScore.moodLabel,
    expressionToken: prosodyScore.expressionToken,
    phraseRole: entry.phraseRole,
    deliveryLabel: entry.deliveryLabel,
    baseXtts: entry.baseXtts,
    presetBaseXtts: entry.presetBaseXtts,
    roleDeltas: entry.roleDeltas,
    featureDeltas: entry.featureDeltas,
    userTuningDeltas: entry.userTuningDeltas,
    deltas: entry.deltas,
    effectiveXtts: entry.effectiveXtts,
    xttsParams: entry.effectiveXtts,
    baseDelivery: entry.baseDelivery,
    effectivePauses: entry.effectivePauses,
    pauseAfterMs: entry.pauseAfterMs,
    clampEvents: entry.clampEvents,
    canonicalTextUnchanged: true,
    textRewriteAllowed: false
  }));
  return {
    classification: 'TARS_PROSODY_KERNEL_PLAN_V1',
    profileId: profile.id,
    goal: profile.goal,
    canonicalTextSha256,
    canonicalTextUnchanged: true,
    noSecretSpeech: noSecretSpeech.ok,
    secretHitCount: noSecretSpeech.hits.length,
    chunkCount: chunks.length,
    salienceCount: salience.length,
    salienceSummary: summarizeSalience(salience),
    delivery: scoredDelivery,
    prosodySheet,
    liveProsodyCueLayer: publicLiveProsodyCueLayer(liveProsodyCueLayer),
    liveProsodyCueLayerRaw: liveProsodyCueLayer,
    prosodyScore: publicProsodyScoreSummary(prosodyScore),
    prosodyScoreRaw: prosodyScore,
    tuning: activeTuning ? {
      id: activeTuning.id,
      label: activeTuning.label,
      moodId: activeTuning.moodId,
      matrix: activeTuning.matrix,
      parameters: activeTuning.parameters,
      randomness: activeTuning.randomness,
      boundaries: activeTuning.boundaries
    } : null,
    chunks,
    salience
  };
}

export function publicProsodyPlanSummary(plan) {
  return {
    classification: plan.classification,
    profileId: plan.profileId,
    goal: plan.goal,
    canonicalTextSha256: plan.canonicalTextSha256,
    canonicalTextUnchanged: plan.canonicalTextUnchanged,
    noSecretSpeech: plan.noSecretSpeech,
    chunkCount: plan.chunkCount,
    salienceCount: plan.salienceCount,
    salienceSummary: plan.salienceSummary,
    delivery: plan.delivery,
    prosodySheet: plan.prosodySheet,
    liveProsodyCueLayer: plan.liveProsodyCueLayer,
    prosodyScore: plan.prosodyScore,
    tuning: plan.tuning
  };
}
