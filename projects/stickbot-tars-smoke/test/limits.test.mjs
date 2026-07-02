import test from 'node:test';
import assert from 'node:assert/strict';
import { Readable } from 'node:stream';
import { assertTextWithinLimit, readAudioUploadBody, readJsonBody } from '../safety/limits.js';

function reqFrom(buffer, headers = {}) {
  const r = Readable.from([buffer]);
  r.headers = headers;
  return r;
}

test('text body over-limit rejected independently', () => {
  assert.doesNotThrow(() => assertTextWithinLimit('ok', 2));
  assert.throws(() => assertTextWithinLimit('too long', 3), /text body too large/);
});

test('json byte limit rejected independently', async () => {
  await assert.rejects(() => readJsonBody(reqFrom(Buffer.from('{"x":"abcdef"}')), 6), /json body too large/);
});

test('audio upload byte limit rejected independently', async () => {
  await assert.rejects(() => readAudioUploadBody(reqFrom(Buffer.alloc(10), { 'content-length': '10' }), 4), /audio body too large/);
});

test('audio upload within limit accepted', async () => {
  const buf = await readAudioUploadBody(reqFrom(Buffer.alloc(4), { 'content-length': '4' }), 4);
  assert.equal(buf.length, 4);
});
