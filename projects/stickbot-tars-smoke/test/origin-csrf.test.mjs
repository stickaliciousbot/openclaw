import test from 'node:test';
import assert from 'node:assert/strict';
import { assertPostOriginAllowed } from '../safety/origin-policy.js';
import { createSessionStore, createCsrfSession, assertCsrf } from '../safety/csrf.js';

const config = { port: 18788, allowLan: false };

function req({ method = 'POST', origin, host = '127.0.0.1:18788', cookie, csrf } = {}) {
  const headers = {};
  headers.host = host;
  if (origin !== undefined) headers.origin = origin;
  if (cookie !== undefined) headers.cookie = cookie;
  if (csrf !== undefined) headers['x-csrf-token'] = csrf;
  return { method, headers };
}

test('allowed loopback Origin accepted', () => {
  assert.doesNotThrow(() => assertPostOriginAllowed(req({ origin: 'http://127.0.0.1:18788' }), config));
  assert.doesNotThrow(() => assertPostOriginAllowed(req({ origin: 'http://localhost:18788' }), config));
});

test('unexpected Origin rejected', () => {
  assert.throws(() => assertPostOriginAllowed(req({ origin: 'http://evil.example' }), config), /Unexpected Origin/);
  assert.throws(() => assertPostOriginAllowed(req({ origin: 'http://192.168.1.5:18788' }), config), /Unexpected Origin/);
});

test('LAN Origin accepted only with explicit allowLan and same host/port', () => {
  const lanConfig = { port: 18788, allowLan: true };
  assert.doesNotThrow(() => assertPostOriginAllowed(req({
    origin: 'http://192.168.1.107:18788',
    host: '192.168.1.107:18788'
  }), lanConfig));
  assert.throws(() => assertPostOriginAllowed(req({
    origin: 'http://192.168.1.108:18788',
    host: '192.168.1.107:18788'
  }), lanConfig), /Unexpected Origin/);
  assert.throws(() => assertPostOriginAllowed(req({
    origin: 'http://192.168.1.107:18789',
    host: '192.168.1.107:18788'
  }), lanConfig), /Unexpected Origin/);
});

test('local CLI/no-Origin allowance is documented but still requires CSRF', () => {
  assert.doesNotThrow(() => assertPostOriginAllowed(req({ origin: undefined }), config));
});

test('missing CSRF rejected', () => {
  const store = createSessionStore();
  assert.throws(() => assertCsrf(req(), store), /missing csrf token/);
});

test('bad CSRF rejected', () => {
  const store = createSessionStore();
  const res = { headers: {}, setHeader(k, v) { this.headers[k] = v; } };
  const { sessionId } = createCsrfSession(store, res);
  assert.throws(() => assertCsrf(req({ cookie: `tars_session=${sessionId}`, csrf: 'bad' }), store), /bad csrf token/);
});

test('valid CSRF accepted', () => {
  const store = createSessionStore();
  const res = { headers: {}, setHeader(k, v) { this.headers[k] = v; } };
  const { sessionId, csrfToken } = createCsrfSession(store, res);
  assert.doesNotThrow(() => assertCsrf(req({ cookie: `tars_session=${sessionId}`, csrf: csrfToken }), store));
});
