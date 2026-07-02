import path from 'node:path';

export class AudioPathPolicyError extends Error {
  constructor(message) {
    super(message);
    this.name = 'AudioPathPolicyError';
    this.statusCode = 400;
    this.publicMessage = 'invalid audio file';
  }
}

export const UUID_WAV_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\.wav$/i;

export function normalizeAudioFileParam(raw) {
  if (typeof raw !== 'string' || raw.length === 0) throw new AudioPathPolicyError('missing audio file');
  let decoded;
  try {
    decoded = decodeURIComponent(raw);
  } catch {
    throw new AudioPathPolicyError('bad audio file encoding');
  }
  if (decoded !== raw && /[/\\]/.test(decoded)) throw new AudioPathPolicyError('encoded traversal is not allowed');
  if (/[/\\]/.test(raw) || /[/\\]/.test(decoded)) throw new AudioPathPolicyError('nested audio paths are not allowed');
  if (decoded.includes('..') || path.isAbsolute(decoded)) throw new AudioPathPolicyError('audio traversal is not allowed');
  if (!UUID_WAV_RE.test(decoded)) throw new AudioPathPolicyError('audio file must be a UUID .wav');
  return decoded;
}

export function resolveAudioOutputPath(outputDir, rawFile) {
  const name = normalizeAudioFileParam(rawFile);
  const base = path.resolve(outputDir);
  const full = path.resolve(base, name);
  if (full !== path.join(base, name) || !full.startsWith(base + path.sep)) {
    throw new AudioPathPolicyError('audio path escaped output directory');
  }
  return { name, full };
}

export function audioUrlForFile(name) {
  const safe = normalizeAudioFileParam(name);
  return `/audio/${encodeURIComponent(safe)}`;
}
