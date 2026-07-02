export class LimitError extends Error {
  constructor(message, { statusCode = 413, classification = 'LIMIT_EXCEEDED' } = {}) {
    super(message);
    this.name = 'LimitError';
    this.statusCode = statusCode;
    this.classification = classification;
    this.publicMessage = message;
  }
}

export function assertTextWithinLimit(text, maxTextChars) {
  if (typeof text !== 'string' || text.length === 0) {
    const e = new LimitError('text required', { statusCode: 400, classification: 'TEXT_REQUIRED' });
    throw e;
  }
  if (text.length > maxTextChars) {
    throw new LimitError('text body too large', { classification: 'TEXT_BODY_LIMIT_EXCEEDED' });
  }
}

export async function readLimitedBody(req, maxBytes, label = 'request') {
  const chunks = [];
  let size = 0;
  const declared = Number(req.headers?.['content-length'] || 0);
  if (declared > maxBytes) {
    throw new LimitError(`${label} body too large`, { classification: `${label.toUpperCase()}_LIMIT_EXCEEDED` });
  }
  for await (const chunk of req) {
    size += chunk.length;
    if (size > maxBytes) {
      throw new LimitError(`${label} body too large`, { classification: `${label.toUpperCase()}_LIMIT_EXCEEDED` });
    }
    chunks.push(chunk);
  }
  return Buffer.concat(chunks);
}

export async function readJsonBody(req, maxBytes) {
  const buf = await readLimitedBody(req, maxBytes, 'json');
  try {
    return JSON.parse(buf.toString('utf8') || '{}');
  } catch {
    const e = new LimitError('invalid json', { statusCode: 400, classification: 'INVALID_JSON' });
    throw e;
  }
}

export async function readAudioUploadBody(req, maxBytes) {
  return readLimitedBody(req, maxBytes, 'audio');
}
