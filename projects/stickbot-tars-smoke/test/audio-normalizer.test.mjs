import test from 'node:test';
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { buildFfmpegNormalizeCommand, normalizeAudio } from '../src/audio-normalizer.js';

function cfg(overrides = {}) {
  return {
    workspace: process.cwd(),
    ffmpegBin: '/usr/bin/ffmpeg',
    audioNormalizeTimeoutMs: 5000,
    audioNormalizeMaxStderrBytes: 64 * 1024,
    ...overrides
  };
}

function fakeChild({ code = 0, stdout = '', stderr = '' } = {}) {
  const child = new EventEmitter();
  child.stdout = new EventEmitter();
  child.stderr = new EventEmitter();
  child.kill = () => { child.killed = true; };
  queueMicrotask(() => {
    if (stdout) child.stdout.emit('data', Buffer.from(stdout));
    if (stderr) child.stderr.emit('data', Buffer.from(stderr));
    child.emit('close', code);
  });
  return child;
}

test('ffmpeg normalize command is fixed and bounded', () => {
  const cmd = buildFfmpegNormalizeCommand(cfg(), '/tmp/input.webm', '/tmp/output.wav');
  assert.equal(cmd.file, '/usr/bin/ffmpeg');
  assert.deepEqual(cmd.args, [
    '-nostdin', '-hide_banner', '-loglevel', 'error', '-y', '-i', '/tmp/input.webm',
    '-ac', '1', '-ar', '16000', '-f', 'wav', '/tmp/output.wav'
  ]);
});

test('/mnt/c paths are blocked for binary, input, and output', () => {
  assert.throws(() => buildFfmpegNormalizeCommand(cfg({ ffmpegBin: '/mnt/c/ffmpeg.exe' }), '/tmp/in.webm', '/tmp/out.wav'), /not \/mnt\/c/);
  assert.throws(() => buildFfmpegNormalizeCommand(cfg(), '/mnt/c/in.webm', '/tmp/out.wav'), /not \/mnt\/c/);
  assert.throws(() => buildFfmpegNormalizeCommand(cfg(), '/tmp/in.webm', '/mnt/c/out.wav'), /not \/mnt\/c/);
});

test('normalizer spawns with shell=false and returns normalized metadata', async () => {
  let seen;
  const result = await normalizeAudio('/tmp/in;echo-nope.webm', '/tmp/out.wav', cfg(), {
    spawnImpl(file, args, opts) {
      seen = { file, args, opts };
      return fakeChild({ code: 0 });
    }
  });
  assert.equal(seen.file, '/usr/bin/ffmpeg');
  assert.equal(seen.opts.shell, false);
  assert.ok(seen.args.includes('/tmp/in;echo-nope.webm'));
  assert.equal(result.outputPath, '/tmp/out.wav');
  assert.equal(result.sampleRate, 16000);
});

test('normalizer fails closed on non-zero exit', async () => {
  await assert.rejects(
    () => normalizeAudio('/tmp/in.webm', '/tmp/out.wav', cfg(), {
      spawnImpl() { return fakeChild({ code: 7, stderr: 'bad media' }); }
    }),
    /ffmpeg exited 7/
  );
});

test('normalizer stderr limit fails closed', async () => {
  await assert.rejects(
    () => normalizeAudio('/tmp/in.webm', '/tmp/out.wav', cfg({ audioNormalizeMaxStderrBytes: 8 }), {
      spawnImpl() { return fakeChild({ code: 0, stderr: 'x'.repeat(32) }); }
    }),
    /exceeded/
  );
});
