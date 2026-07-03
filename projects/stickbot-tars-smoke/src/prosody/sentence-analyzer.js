const PASS_RE = /\b(PASS|READY|GREEN|COMPLETE|COMPLETED|VALIDATED|SUCCESS)\b/i;
const FAIL_RE = /\b(FAIL|FAILED|FAILURE|RED|BROKEN|ERROR)\b/i;
const BLOCK_RE = /\b(BLOCKED|HOLD|NO-GO|MISSING|MFA|AUTH|UNSAFE|CANNOT|CAN'T|NOT READY)\b/i;
const WARN_RE = /\b(WARNING|WARN|URGENT|STOP|ABORT|DANGER|DESTRUCTIVE|SECURITY)\b/i;
const INSTRUCT_RE = /\b(run|open|click|select|paste|type|check|verify|rerun|use|start|stop|approve|login|reauth|authenticate)\b/i;
const EVIDENCE_RE = /\b(evidence|artifact|hash|sha256|query|sql|dom\.|dbo\.|log|trace|count|rows|validated|classification)\b/i;
const ASIDE_RE = /\b(joke|humor|obviously|classic|naturally|because of course|dry|tars)\b|[()—]/i;
const UNCERTAIN_RE = /\b(maybe|probably|likely|unclear|unknown|not sure|appears|seems)\b/i;
const RECOVERY_RE = /\b(recover|repair|restore|retry|fallback|caught|fix)\b/i;
const CLOSEOUT_RE = /\b(closeout|summary|final|done|complete|handoff)\b/i;

function words(text) {
  return String(text || '').trim().split(/\s+/).filter(Boolean);
}

export function analyzeSentenceFeatures(text = '') {
  const s = String(text || '');
  const wordList = words(s);
  const punctuation = (s.match(/[.,;:!?—()]/g) || []).length;
  const technicalTokens = (s.match(/\b[A-Z0-9_/-]{3,}\b|\b\w+\.\w+\b|`[^`]+`/g) || []).length;
  const features = {
    lengthChars: s.length,
    wordCount: wordList.length,
    shortStatusSentence: wordList.length > 0 && wordList.length <= 6 && (PASS_RE.test(s) || FAIL_RE.test(s) || BLOCK_RE.test(s)),
    passMarker: PASS_RE.test(s),
    failMarker: FAIL_RE.test(s),
    warningMarker: WARN_RE.test(s),
    blockerMarker: BLOCK_RE.test(s),
    instruction: INSTRUCT_RE.test(s),
    diagnosticEvidence: EVIDENCE_RE.test(s),
    question: /\?\s*$/.test(s) || /^\s*(can|could|should|what|why|how|when|where|is|are|do|does)\b/i.test(s),
    humorDryAside: ASIDE_RE.test(s),
    uncertainty: UNCERTAIN_RE.test(s),
    recovery: RECOVERY_RE.test(s),
    closeout: CLOSEOUT_RE.test(s) || PASS_RE.test(s),
    technicalDensity: wordList.length ? Math.min(1, technicalTokens / Math.max(1, wordList.length)) : 0,
    punctuationDensity: s.length ? Math.min(1, punctuation / Math.max(1, s.length / 24)) : 0,
    hasComma: /,/.test(s),
    hasSemicolon: /;/.test(s),
    hasColon: /:/.test(s),
    hasLineBreak: /\n/.test(s),
    endsHard: /[.!?]\s*$/.test(s),
    rawPunctuationCount: punctuation,
    rawTechnicalTokenCount: technicalTokens
  };
  return features;
}
