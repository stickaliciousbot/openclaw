function pauseFor(segment, profile) {
  const trimmed = segment.trimEnd();
  if (/\b(WARNING|WARN|FAIL|ABORT|HOLD|ERROR)\b[:.]?$/i.test(trimmed)) return profile.pausesMs.warningAfterLabel;
  if (/\b(PASS|READY)\b[:.]?$/i.test(trimmed)) return profile.pausesMs.status;
  if (/[,:;]$/.test(trimmed)) return profile.pausesMs.comma;
  if (/[.!?]$/.test(trimmed)) return profile.pausesMs.period;
  return profile.pausesMs.comma;
}

function shouldBreakAt(text, i) {
  const c = text[i];
  if (!/[.!?;:]/.test(c)) return false;
  const next = text[i + 1] || '';
  return !next || /\s/.test(next);
}

export function chunkTarsSentences(text, profile, { maxChars = 220 } = {}) {
  const chunks = [];
  let start = 0;
  let lastBreak = -1;

  for (let i = 0; i < text.length; i += 1) {
    if (shouldBreakAt(text, i)) lastBreak = i + 1;
    const tooLong = i - start + 1 >= maxChars;
    if ((lastBreak > start && (tooLong || /[.!?;:]$/.test(text.slice(start, lastBreak).trimEnd()))) || tooLong) {
      const end = lastBreak > start ? lastBreak : i + 1;
      const segment = text.slice(start, end);
      chunks.push({ index: chunks.length, start, end, text: segment, pauseAfterMs: pauseFor(segment, profile) });
      start = end;
      lastBreak = -1;
    }
  }

  if (start < text.length) {
    const segment = text.slice(start);
    chunks.push({ index: chunks.length, start, end: text.length, text: segment, pauseAfterMs: pauseFor(segment, profile) });
  }

  if (!chunks.length && text === '') return [];
  return chunks;
}

export function reconstructChunks(chunks) {
  if (!chunks.length) return '';
  return chunks.map((c) => c.text).join('');
}
