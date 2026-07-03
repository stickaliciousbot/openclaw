import crypto from 'node:crypto';
import { loadTarsProsodyProfile } from '../voice/tars-prosody-profile.js';
import { loadMoodProfile } from './mood-profile-loader.js';
import { analyzeSentenceFeatures } from './sentence-analyzer.js';
import { classifyPhraseRole, roleDeliveryLabel } from './phrase-role-classifier.js';
import { planProsodyChunks } from './chunk-planner.js';
import { averageEffectiveXtts, resolveEffectiveXtts } from './xtts-param-resolver.js';
import { resolvePauseScore } from './pause-score-resolver.js';

function sha256(text) {
  return crypto.createHash('sha256').update(String(text ?? '')).digest('hex');
}

function idFor(index) {
  return `c${String(index + 1).padStart(3, '0')}`;
}

export function buildProsodyScore(text, {
  profile = loadTarsProsodyProfile(),
  tuning = null,
  matrixState = null,
  turnId = null,
  maxChars = 220,
  now = new Date()
} = {}) {
  const canonicalText = String(text ?? '');
  const moodProfile = loadMoodProfile({ moodId: tuning?.moodId || 'baseline_deadpan', matrixState, tuning });
  const chunkMax = Math.min(maxChars, moodProfile.baseDelivery.maxCharsPerChunk || maxChars);
  const chunks = planProsodyChunks(canonicalText, profile, { maxChars: chunkMax });
  const scoredChunks = chunks.map((chunk) => {
    const features = analyzeSentenceFeatures(chunk.text);
    const phraseRole = classifyPhraseRole(features, chunk.text);
    const xtts = resolveEffectiveXtts({
      baseXtts: moodProfile.baseXtts,
      phraseRole,
      features,
      tuning,
      voiceIdentity: moodProfile.voiceIdentity,
      bounds: matrixState?.bounds
    });
    const pauses = resolvePauseScore({
      text: chunk.text,
      phraseRole,
      features,
      baseDelivery: moodProfile.baseDelivery,
      voiceIdentity: moodProfile.voiceIdentity
    });
    return {
      chunkId: idFor(chunk.index),
      chunkIndex: chunk.index,
      start: chunk.start,
      end: chunk.end,
      text: chunk.text,
      textSha256: sha256(chunk.text),
      phraseRole,
      deliveryLabel: roleDeliveryLabel(phraseRole),
      features,
      baseXtts: xtts.baseXtts,
      presetBaseXtts: moodProfile.presetBaseXtts,
      roleDeltas: xtts.roleDeltas,
      featureDeltas: xtts.featureDeltas,
      userTuningDeltas: xtts.userTuningDeltas,
      deltas: xtts.deltas,
      effectiveXtts: xtts.effectiveXtts,
      baseDelivery: moodProfile.baseDelivery,
      effectivePauses: pauses,
      pauseAfterMs: pauses.postPauseMs,
      clampEvents: xtts.clampEvents,
      generationArtifact: null,
      canonicalTextUnchanged: true,
      textRewriteAllowed: false
    };
  });

  return {
    schema: 'stickbot.tars.prosody-score.v1',
    classification: 'STICKBOT_TARS_M55_PROSODY_SCORE_ENGINE_PLAN',
    generatedAt: now.toISOString(),
    turnId,
    moodId: moodProfile.moodId,
    moodLabel: moodProfile.label,
    expressionToken: moodProfile.expressionToken,
    voicePersona: moodProfile.voicePersona,
    voiceIdentity: moodProfile.voiceIdentity,
    style: moodProfile.style,
    canonicalTextSha256: sha256(canonicalText),
    canonicalTextUnchanged: true,
    textRewriteAllowed: false,
    chunkCount: scoredChunks.length,
    baseXtts: moodProfile.baseXtts,
    presetBaseXtts: moodProfile.presetBaseXtts,
    baseDelivery: moodProfile.baseDelivery,
    presetBaseDelivery: moodProfile.presetBaseDelivery,
    utteranceXttsParams: averageEffectiveXtts(scoredChunks) || moodProfile.baseXtts,
    chunks: scoredChunks,
    boundaries: {
      canonicalTextAuthoritative: true,
      textRewriteAllowed: false,
      localOnly: true,
      cloudSpeechAllowed: false,
      browserWebSpeechApiAllowed: false,
      gatewayMutationAllowed: false,
      openClawRoutingMutationAllowed: false
    }
  };
}

export function publicProsodyScoreSummary(score = {}) {
  return {
    schema: score.schema,
    classification: score.classification,
    generatedAt: score.generatedAt,
    turnId: score.turnId || null,
    moodId: score.moodId,
    moodLabel: score.moodLabel,
    expressionToken: score.expressionToken,
    voicePersona: score.voicePersona,
    chunkCount: score.chunkCount,
    canonicalTextSha256: score.canonicalTextSha256,
    canonicalTextUnchanged: score.canonicalTextUnchanged,
    textRewriteAllowed: score.textRewriteAllowed,
    baseXtts: score.baseXtts,
    presetBaseXtts: score.presetBaseXtts,
    baseDelivery: score.baseDelivery,
    presetBaseDelivery: score.presetBaseDelivery,
    utteranceXttsParams: score.utteranceXttsParams,
    chunks: (score.chunks || []).map((chunk) => ({
      chunkId: chunk.chunkId,
      chunkIndex: chunk.chunkIndex,
      start: chunk.start,
      end: chunk.end,
      textSha256: chunk.textSha256,
      phraseRole: chunk.phraseRole,
      deliveryLabel: chunk.deliveryLabel,
      features: chunk.features,
      baseXtts: chunk.baseXtts,
      presetBaseXtts: chunk.presetBaseXtts,
      roleDeltas: chunk.roleDeltas,
      featureDeltas: chunk.featureDeltas,
      userTuningDeltas: chunk.userTuningDeltas,
      deltas: chunk.deltas,
      effectiveXtts: chunk.effectiveXtts,
      baseDelivery: chunk.baseDelivery,
      effectivePauses: chunk.effectivePauses,
      pauseAfterMs: chunk.pauseAfterMs,
      clampEvents: chunk.clampEvents,
      generationArtifact: chunk.generationArtifact,
      canonicalTextUnchanged: chunk.canonicalTextUnchanged,
      textRewriteAllowed: chunk.textRewriteAllowed
    })),
    boundaries: score.boundaries
  };
}
