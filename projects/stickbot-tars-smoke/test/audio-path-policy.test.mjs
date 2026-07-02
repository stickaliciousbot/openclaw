import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { resolveAudioOutputPath, audioUrlForFile } from '../safety/audio-path-policy.js';

const UUID = '123e4567-e89b-12d3-a456-426614174000.wav';

test('UUID .wav is accepted when file exists in controlled output dir', async () => {
  const dir = await mkdtemp(path.join(os.tmpdir(), 'tars-audio-'));
  await writeFile(path.join(dir, UUID), 'wav');
  const resolved = resolveAudioOutputPath(dir, UUID);
  assert.equal(resolved.name, UUID);
  assert.equal(resolved.full, path.join(dir, UUID));
  assert.equal(audioUrlForFile(UUID), `/audio/${UUID}`);
});

test('path traversal is rejected', () => {
  assert.throws(() => resolveAudioOutputPath('/tmp/audio', '../secret.wav'));
  assert.throws(() => resolveAudioOutputPath('/tmp/audio', '..%2Fsecret.wav'));
  assert.throws(() => resolveAudioOutputPath('/tmp/audio', 'nested/file.wav'));
  assert.throws(() => resolveAudioOutputPath('/tmp/audio', '/tmp/evil.wav'));
});

test('non-UUID audio and alternate extensions are rejected', () => {
  assert.throws(() => resolveAudioOutputPath('/tmp/audio', 'not-a-uuid.wav'));
  assert.throws(() => resolveAudioOutputPath('/tmp/audio', '123e4567-e89b-12d3-a456-426614174000.mp3'));
  assert.throws(() => resolveAudioOutputPath('/tmp/audio', '123e4567-e89b-12d3-a456-426614174000.wav.bak'));
});
