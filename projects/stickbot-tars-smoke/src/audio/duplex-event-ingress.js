import crypto from 'node:crypto';
import { publicFullDuplexControllerSummary, runFullDuplexScenario } from './full-duplex-turn-controller.js';

function sha256(text) {
  return crypto.createHash('sha256').update(String(text ?? '')).digest('hex');
}

function boundedCount(n, fallback = 0) {
  const x = Number(n);
  if (!Number.isFinite(x) || x < 0) return fallback;
  return Math.min(100000, Math.floor(x));
}

export function transcriptEventFromText(type, text, { confidence = null } = {}) {
  const s = String(text ?? '');
  return {
    type,
    payload: {
      textSha256: sha256(s),
      charCount: s.length,
      confidence,
      durableRawTranscript: false
    }
  };
}

export function sanitizeDuplexEvent(input = {}) {
  const type = String(input.type || '');
  const payload = input.payload || {};
  if (type === 'partial_transcript' || type === 'final_transcript') {
    if (typeof payload.text === 'string') return transcriptEventFromText(type, payload.text, { confidence: payload.confidence ?? null });
    return {
      type,
      payload: {
        textSha256: /^[a-f0-9]{64}$/i.test(String(payload.textSha256 || '')) ? String(payload.textSha256) : null,
        charCount: boundedCount(payload.charCount),
        confidence: payload.confidence ?? null,
        durableRawTranscript: false
      }
    };
  }
  return { type, payload: { ...payload } };
}

export function buildPartialSttControllerSummary({ turnId, partialText = '', confidence = null } = {}) {
  const controller = runFullDuplexScenario([
    { type: 'listen_start' },
    transcriptEventFromText('partial_transcript', partialText, { confidence })
  ], { turnId });
  return publicFullDuplexControllerSummary(controller);
}

export function buildFinalSttControllerSummary({ turnId, finalText = '', confidence = null } = {}) {
  const controller = runFullDuplexScenario([
    { type: 'listen_start' },
    transcriptEventFromText('final_transcript', finalText, { confidence })
  ], { turnId });
  return publicFullDuplexControllerSummary(controller);
}

export function runSanitizedDuplexScenario(events = [], { turnId } = {}) {
  return publicFullDuplexControllerSummary(runFullDuplexScenario(events.map(sanitizeDuplexEvent), { turnId }));
}
