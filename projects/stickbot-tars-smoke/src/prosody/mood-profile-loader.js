import { deriveMoodMatrixSelection } from '../voice/tars-prosody-matrix.js';

function clone(obj) {
  return JSON.parse(JSON.stringify(obj || {}));
}

export const DEFAULT_TARS_VOICE_IDENTITY = Object.freeze({
  id: 'tars_primary',
  voicePersona: 'TARS',
  identityLockStrength: 0.85,
  allowedSpeedDelta: 0.08,
  allowedTemperatureDelta: 0.08,
  allowedTopPDelta: 0.06,
  allowedPauseDeltaMs: 160,
  forbiddenStyles: Object.freeze([
    'cheerful_assistant',
    'cartoon_robot',
    'dramatic_trailer',
    'warm_therapist',
    'radio_announcer'
  ])
});

export const DEFAULT_CASE_VOICE_IDENTITY = Object.freeze({
  ...DEFAULT_TARS_VOICE_IDENTITY,
  id: 'case_secondary',
  voicePersona: 'CASE',
  identityLockStrength: 0.9,
  allowedSpeedDelta: 0.06,
  allowedTemperatureDelta: 0.06,
  allowedTopPDelta: 0.05,
  allowedPauseDeltaMs: 210
});

export function loadMoodProfile({ moodId = 'baseline_deadpan', matrixState = null, tuning = null } = {}) {
  const selection = deriveMoodMatrixSelection({ moodId }, matrixState);
  const voicePersona = selection.voicePersona || (String(selection.moodId || '').startsWith('case_') ? 'CASE' : 'TARS');
  const identity = voicePersona === 'CASE' ? DEFAULT_CASE_VOICE_IDENTITY : DEFAULT_TARS_VOICE_IDENTITY;
  const activeMatrix = tuning?.matrix?.moodId === selection.moodId ? tuning.matrix : selection;
  return {
    moodId: selection.moodId,
    label: selection.label,
    expressionToken: selection.expressionToken,
    voicePersona,
    voiceIdentity: { ...identity, voicePersona },
    baseXtts: clone(activeMatrix.xttsParams || selection.xttsParams),
    presetBaseXtts: clone(selection.recommendedXttsParams || selection.xttsParams),
    baseDelivery: clone(activeMatrix.delivery || selection.delivery),
    presetBaseDelivery: clone(selection.recommendedDelivery || selection.delivery),
    evaluationThresholds: clone(selection.evaluationThresholds),
    style: {
      tempo: selection.moodId?.includes('mission') ? 'brisk_controlled' : 'restrained',
      articulation: voicePersona === 'CASE' ? 'reserved' : 'clipped',
      emotionalRange: 'low',
      witAllowed: /wit|banter|humor/i.test(selection.moodId || '')
    },
    boundaries: clone(selection.boundaries)
  };
}
