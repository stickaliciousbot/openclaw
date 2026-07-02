import crypto from 'node:crypto';

export class CsrfError extends Error {
  constructor(message) {
    super(message);
    this.name = 'CsrfError';
    this.statusCode = 403;
    this.publicMessage = 'csrf rejected';
    this.classification = 'CSRF_REJECTED';
  }
}

export function createSessionStore() {
  return new Map();
}

export function parseCookies(header = '') {
  const out = new Map();
  for (const part of String(header).split(';')) {
    const i = part.indexOf('=');
    if (i === -1) continue;
    out.set(part.slice(0, i).trim(), decodeURIComponent(part.slice(i + 1).trim()));
  }
  return out;
}

export function createCsrfSession(store, res) {
  const sessionId = crypto.randomUUID();
  const csrfToken = crypto.randomBytes(32).toString('hex');
  store.set(sessionId, { csrfToken, createdAt: Date.now() });
  res.setHeader('set-cookie', `tars_session=${encodeURIComponent(sessionId)}; Path=/; SameSite=Strict`);
  return { sessionId, csrfToken };
}

export function assertCsrf(req, store) {
  const cookies = parseCookies(req.headers?.cookie || '');
  const sessionId = cookies.get('tars_session');
  const supplied = req.headers?.['x-csrf-token'];
  if (!sessionId || !supplied) throw new CsrfError('missing csrf token');
  const record = store.get(sessionId);
  if (!record || record.csrfToken !== supplied) throw new CsrfError('bad csrf token');
  return true;
}
