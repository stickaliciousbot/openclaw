const STATUS_RE = /\b(PASS|FAIL|HOLD|ABORT|READY|BLOCKED|WARNING|WARN|ERROR|DENY|ALLOW)\b/g;
const NUMBER_RE = /(?<![A-Za-z])(?:\d+(?:\.\d+)?%?|[A-Fa-f0-9]{7,64})(?![A-Za-z])/g;
const WARNING_RE = /\b(risk|unsafe|blocked|failed|failure|leak|secret|token|permission|approval|mutation|rollback|restart|exposure|private|raw transcript)\b/gi;
const OPERATOR_RE = /\b(approve|deny|refresh|retry|stop|do not|don't|must|requires|operator|permission|instruction)\b/gi;
const MISSION_RE = /\b(milestone|gate|classification|validation|smoke|canary|runtime|loopback|local|LAN|HTTPS|XTTS|STT|TTS)\b/gi;

function collect(text, regex, kind, weight) {
  const out = [];
  for (const m of text.matchAll(regex)) {
    out.push({ kind, text: m[0], start: m.index, end: m.index + m[0].length, weight });
  }
  return out;
}

function overlap(a, b) {
  return a.start < b.end && b.start < a.end;
}

export function annotateTarsSalience(text, profile) {
  const weights = profile.salienceWeights;
  const candidates = [
    ...collect(text, STATUS_RE, 'status', weights.statusToken),
    ...collect(text, NUMBER_RE, 'number', weights.number),
    ...collect(text, WARNING_RE, 'warning', weights.warning),
    ...collect(text, OPERATOR_RE, 'operator_instruction', weights.operatorInstruction),
    ...collect(text, MISSION_RE, 'mission_state', weights.missionState)
  ].sort((a, b) => b.weight - a.weight || a.start - b.start || (b.end - b.start) - (a.end - a.start));

  const spans = [];
  for (const c of candidates) {
    if (spans.some((s) => overlap(s, c))) continue;
    spans.push(c);
  }
  return spans.sort((a, b) => a.start - b.start);
}

export function summarizeSalience(spans) {
  const counts = {};
  for (const s of spans) counts[s.kind] = (counts[s.kind] || 0) + 1;
  return counts;
}
