import test from 'node:test';
import assert from 'node:assert/strict';
import { loadConfig } from '../src/config.js';

function base(overrides = {}) {
  return {
    HOST: '127.0.0.1',
    PORT: '18788',
    XTTS_URL: 'http://127.0.0.1:8020',
    ...overrides
  };
}

function classificationFor(env) {
  try {
    loadConfig(env);
    return null;
  } catch (e) {
    return e.classification;
  }
}

test('defaults are loopback-only and accepted', () => {
  const cfg = loadConfig(base());
  assert.equal(cfg.host, '127.0.0.1');
  assert.equal(cfg.port, 18788);
  assert.equal(cfg.allowLan, false);
});

test('HOST=0.0.0.0 without explicit LAN allow fails closed', () => {
  assert.equal(classificationFor(base({ HOST: '0.0.0.0' })), 'BLOCKED_UNSAFE_CONFIG');
});

test('non-loopback HOST without explicit LAN allow fails closed', () => {
  assert.equal(classificationFor(base({ HOST: '192.168.1.50' })), 'BLOCKED_NON_LOOPBACK_HOST');
});

test('reserved port 8787 fails closed', () => {
  assert.equal(classificationFor(base({ PORT: '8787' })), 'BLOCKED_RESERVED_PORT');
});

test('non-loopback XTTS_URL without explicit remote allow fails closed', () => {
  assert.equal(classificationFor(base({ XTTS_URL: 'http://192.168.1.50:8020' })), 'BLOCKED_NON_LOOPBACK_XTTS');
});

test('explicit LAN/remote opt-in permits non-loopback validation only', () => {
  const cfg = loadConfig(base({ HOST: '192.168.1.50', XTTS_URL: 'http://192.168.1.51:8020', VOICE_DEMO_ALLOW_LAN: 'true' }));
  assert.equal(cfg.allowLan, true);
});

test('HTTPS mode requires explicit existing key/cert paths', () => {
  assert.equal(classificationFor(base({ VOICE_DEMO_HTTPS: 'true' })), 'BLOCKED_HTTPS_CERT_MISSING');
});

test('HTTPS key/cert paths reject /mnt/c', () => {
  assert.equal(classificationFor(base({
    VOICE_DEMO_HTTPS: 'true',
    VOICE_DEMO_HTTPS_KEY: '/mnt/c/tmp/key.pem',
    VOICE_DEMO_HTTPS_CERT: '/tmp/cert.pem'
  })), 'BLOCKED_MNT_C_PATH');
});
