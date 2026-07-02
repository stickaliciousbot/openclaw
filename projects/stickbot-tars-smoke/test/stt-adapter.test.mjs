import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, writeFile, chmod } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { buildSttCommand, parseSttOutput, transcribeAudio } from '../src/stt-adapter.js';

function cfg(overrides = {}) {
  return {
    workspace: process.cwd(),
    sttMode: 'fixture',
    sttBin: 'whisper-cli',
    sttArgsJson: '',
    sttFixtureText: 'fixture transcript',
    sttTimeoutMs: 5000,
    sttMaxStdoutBytes: 64 * 1024,
    ...overrides
  };
}

async function fakeCli(script) {
  const dir = await mkdtemp(path.join(os.tmpdir(), 'tars-stt-fake-'));
  const file = path.join(dir, 'fake-stt.mjs');
  await writeFile(file, script, 'utf8');
  await chmod(file, 0o700);
  return file;
}

test('fixture mode returns configured transcript without spawning', async () => {
  const transcript = await transcribeAudio('/tmp/audio.wav', cfg(), {
    spawnImpl() { throw new Error('should not spawn'); }
  });
  assert.equal(transcript, 'fixture transcript');
});

test('capture mode fails closed so caller can return capture-only response', async () => {
  await assert.rejects(() => transcribeAudio('/tmp/audio.wav', cfg({ sttMode: 'capture' })), /captured only/);
});

test('cli args require file placeholder', () => {
  assert.throws(() => buildSttCommand(cfg({ sttMode: 'cli', sttArgsJson: '["--json"]' }), '/tmp/a.wav'), /placeholder/);
});

test('STT output parser accepts JSON and plain text', () => {
  assert.equal(parseSttOutput('{"text":"hello"}'), 'hello');
  assert.equal(parseSttOutput('{"segments":[{"text":"hello"},{"text":"world"}]}'), 'hello world');
  assert.equal(parseSttOutput('plain transcript'), 'plain transcript');
});

test('cli mode passes file path as argv with shell=false', async () => {
  const file = await fakeCli(`#!/usr/bin/env node
const i = process.argv.indexOf('--file');
console.log(JSON.stringify({ transcript: process.argv[i + 1] }));
`);
  const audioPath = '/tmp/audio; echo SHOULD_NOT_EXECUTE.wav';
  const transcript = await transcribeAudio(audioPath, cfg({
    sttMode: 'cli',
    sttBin: process.execPath,
    sttArgsJson: JSON.stringify([file, '--file', '{file}', '--json'])
  }));
  assert.equal(transcript, audioPath);
});

test('non-zero STT exits fail closed', async () => {
  const file = await fakeCli(`#!/usr/bin/env node
console.error('stt boom');
process.exit(9);
`);
  await assert.rejects(
    () => transcribeAudio('/tmp/a.wav', cfg({ sttMode: 'cli', sttBin: process.execPath, sttArgsJson: JSON.stringify([file, '{file}']) })),
    /STT CLI exited 9/
  );
});

test('STT stdout limit fails closed', async () => {
  const file = await fakeCli(`#!/usr/bin/env node
console.log('x'.repeat(2048));
`);
  await assert.rejects(
    () => transcribeAudio('/tmp/a.wav', cfg({
      sttMode: 'cli',
      sttBin: process.execPath,
      sttArgsJson: JSON.stringify([file, '{file}']),
      sttMaxStdoutBytes: 128
    })),
    /exceeded/
  );
});
