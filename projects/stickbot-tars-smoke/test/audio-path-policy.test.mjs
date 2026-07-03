import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { resolveAudioOutputPath, audioUrlForFile } from '../safety/audio-path-policy.js';

const UUID = '123e4567-e89b-12d3-a456-426614174000.wav';
const UUID_CHUNK = '123e4567-e89b-12d3-a456-426614174000-chunk-001.wav';
const UUID_CHUNK_DSP = '123e4567-e89b-12d3-a456-426614174000-chunk-001.dsp.wav';
const UUID_MASTER = '123e4567-e89b-12d3-a456-426614174000.master.wav';
const UUID_CHUNK_MASTER = '123e4567-e89b-12d3-a456-426614174000-chunk-001.dsp.master.wav';

test('UUID .wav is accepted when file exists in controlled output dir', async () => {
  const dir = await mkdtemp(path.join(os.tmpdir(), 'tars-audio-'));
  await writeFile(path.join(dir, UUID), 'wav');
  const resolved = resolveAudioOutputPath(dir, UUID);
  assert.equal(resolved.name, UUID);
  assert.equal(resolved.full, path.join(dir, UUID));
  assert.equal(audioUrlForFile(UUID), `/audio/${UUID}`);
});

test('generated UUID chunk .wav files are accepted for streaming playback smoke', async () => {
  const dir = await mkdtemp(path.join(os.tmpdir(), 'tars-audio-'));
  await writeFile(path.join(dir, UUID_CHUNK), 'wav');
  await writeFile(path.join(dir, UUID_CHUNK_DSP), 'wav');
  await writeFile(path.join(dir, UUID_MASTER), 'wav');
  await writeFile(path.join(dir, UUID_CHUNK_MASTER), 'wav');
  assert.equal(resolveAudioOutputPath(dir, UUID_CHUNK).name, UUID_CHUNK);
  assert.equal(resolveAudioOutputPath(dir, UUID_CHUNK_DSP).name, UUID_CHUNK_DSP);
  assert.equal(resolveAudioOutputPath(dir, UUID_MASTER).name, UUID_MASTER);
  assert.equal(resolveAudioOutputPath(dir, UUID_CHUNK_MASTER).name, UUID_CHUNK_MASTER);
  assert.equal(audioUrlForFile(UUID_CHUNK), `/audio/${UUID_CHUNK}`);
  assert.equal(audioUrlForFile(UUID_CHUNK_MASTER), `/audio/${UUID_CHUNK_MASTER}`);
});

test('path traversal is rejected', () => {
  assert.throws(() => resolveAudioOutputPath('/tmp/audio', '../secret.wav'));
  assert.throws(() => resolveAudioOutputPath('/tmp/audio', '..%2Fsecret.wav'));
  assert.throws(() => resolveAudioOutputPath('/tmp/audio', 'nested/file.wav'));
  assert.throws(() => resolveAudioOutputPath('/tmp/audio', '/tmp/evil.wav'));
});

test('non-UUID audio and alternate extensions are rejected', () => {
  assert.throws(() => resolveAudioOutputPath('/tmp/audio', 'not-a-uuid.wav'));
  assert.throws(() => resolveAudioOutputPath('/tmp/audio', '123e4567-e89b-12d3-a456-426614174000-chunk-1.wav'));
  assert.throws(() => resolveAudioOutputPath('/tmp/audio', '123e4567-e89b-12d3-a456-426614174000-chunk-001.tmp.wav'));
  assert.throws(() => resolveAudioOutputPath('/tmp/audio', '123e4567-e89b-12d3-a456-426614174000.mp3'));
  assert.throws(() => resolveAudioOutputPath('/tmp/audio', '123e4567-e89b-12d3-a456-426614174000.wav.bak'));
});
