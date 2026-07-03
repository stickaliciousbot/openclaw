import crypto from 'node:crypto';
import { buildPartialSttControllerSummary } from './duplex-event-ingress.js';

export const PARTIAL_STT_LOOP_SCHEMA = 'stickbot.tars.partial-stt-loop.v1';

function sha256Text(value) {
  return crypto.createHash('sha256').update(String(value ?? '')).digest('hex');
}

function boundedSeq(value) {
  const n = Number(value);
  if (!Number.isInteger(n) || n < 0) return 0;
  return Math.min(9999, n);
}

export function buildPartialLocalSttLoopResponse({
  id,
  seq = 0,
  transcript = '',
  savedLocal = true,
  normalizedLocal = false,
  sttMode = 'cli',
  confidence = null,
  noTranscript = false,
  error = null
} = {}) {
  const text = String(transcript || '').trim();
  const turnId = id || crypto.randomUUID();
  const transcriptPresent = Boolean(text);
  return {
    schema: PARTIAL_STT_LOOP_SCHEMA,
    id: turnId,
    seq: boundedSeq(seq),
    classification: transcriptPresent
      ? 'STICKBOT_TARS_M7Q_TRUE_PARTIAL_LOCAL_STT_LOOP_PASS'
      : 'STICKBOT_TARS_M7Q_TRUE_PARTIAL_LOCAL_STT_LOOP_NO_TRANSCRIPT',
    savedLocal: Boolean(savedLocal),
    normalizedLocal: Boolean(normalizedLocal),
    sttMode,
    partialTranscript: text || null,
    partialTranscriptSha256: transcriptPresent ? sha256Text(text) : null,
    charCount: text.length,
    noTranscript: Boolean(noTranscript || !transcriptPresent),
    error: error ? String(error) : null,
    duplex: buildPartialSttControllerSummary({ turnId, partialText: text, confidence }),
    boundaries: {
      localOnly: true,
      rawTranscriptDurableStorage: false,
      browserWebSpeechApi: false,
      cloudSpeechApi: false,
      openClawProductionMutation: false,
      gatewayConfigMutation: false,
      textRewriteAllowed: false
    }
  };
}
