export const PHRASE_ROLES = Object.freeze([
  'status',
  'instruction',
  'warning',
  'blocker',
  'evidence',
  'aside',
  'punchline',
  'confirmation',
  'uncertainty',
  'recovery',
  'question',
  'closeout'
]);

export function classifyPhraseRole(features = {}, text = '') {
  const s = String(text || '');
  if (features.warningMarker && /\b(STOP|ABORT|URGENT|DANGER|DESTRUCTIVE)\b/i.test(s)) return 'warning';
  if (features.blockerMarker || features.failMarker) return 'blocker';
  if (features.passMarker && features.shortStatusSentence) return 'status';
  if (features.question) return 'question';
  if (features.instruction) return 'instruction';
  if (features.diagnosticEvidence || features.technicalDensity > 0.18) return 'evidence';
  if (features.humorDryAside && /[.!?)]\s*$/.test(s)) return 'aside';
  if (features.uncertainty) return 'uncertainty';
  if (features.recovery) return 'recovery';
  if (features.closeout) return 'closeout';
  if (/\b(yes|confirmed|correct|done|okay|ok)\b[.!]?$/i.test(s.trim())) return 'confirmation';
  return 'evidence';
}

export function roleDeliveryLabel(role) {
  return {
    status: 'flat_positive',
    instruction: 'brisk_precise',
    warning: 'clipped_command',
    blocker: 'firm_deadpan',
    evidence: 'measured_analysis',
    aside: 'delayed_deadpan',
    punchline: 'delayed_deadpan',
    confirmation: 'quiet_confirmation',
    uncertainty: 'careful_uncertain',
    recovery: 'calm_recovery',
    question: 'measured_question',
    closeout: 'flat_closeout'
  }[role] || 'measured_analysis';
}
