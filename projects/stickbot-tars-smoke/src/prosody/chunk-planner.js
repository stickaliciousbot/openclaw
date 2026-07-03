import { chunkTarsSentences, reconstructChunks } from '../voice/tars-sentence-chunker.js';

export function planProsodyChunks(text, profile, { maxChars = 220 } = {}) {
  const chunks = chunkTarsSentences(String(text ?? ''), profile, { maxChars });
  if (reconstructChunks(chunks) !== String(text ?? '')) {
    const e = new Error('PROSODY_SCORE_CHUNK_TEXT_CHANGED');
    e.classification = 'PROSODY_SCORE_CHUNK_TEXT_CHANGED';
    throw e;
  }
  return chunks;
}
