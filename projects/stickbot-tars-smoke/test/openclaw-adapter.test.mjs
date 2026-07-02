import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, writeFile, chmod } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { askOpenClaw, buildOpenClawCommand, parseOpenClawJsonOutput } from '../src/openclaw-adapter.js';

function cfg(overrides = {}) {
  return {
    workspace: process.cwd(),
    openclawMode: 'infer',
    openclawBin: 'openclaw',
    openclawArgsJson: '',
    openclawTimeoutMs: 5000,
    openclawMaxStdoutBytes: 64 * 1024,
    ...overrides
  };
}

async function fakeCli(script) {
  const dir = await mkdtemp(path.join(os.tmpdir(), 'tars-openclaw-fake-'));
  const file = path.join(dir, 'fake-openclaw.mjs');
  await writeFile(file, script, 'utf8');
  await chmod(file, 0o700);
  return file;
}

test('echo mode stays local and does not spawn', async () => {
  const text = await askOpenClaw('hello', cfg({ openclawMode: 'echo' }), {
    spawnImpl() { throw new Error('should not spawn'); }
  });
  assert.equal(text, 'Echo smoke response: hello');
});

test('infer mode default command uses infer model run json shape', () => {
  const command = buildOpenClawCommand(cfg({ openclawMode: 'infer' }), 'hi');
  assert.deepEqual(command.args, ['infer', 'model', 'run', '--prompt', 'hi', '--json']);
});

test('agent mode default command uses agent json shape', () => {
  const command = buildOpenClawCommand(cfg({ openclawMode: 'agent' }), 'hi');
  assert.deepEqual(command.args, ['agent', '--message', 'hi', '--json']);
});

test('prompt placeholder is required so prompts are not appended ambiguously', () => {
  assert.throws(
    () => buildOpenClawCommand(cfg({ openclawArgsJson: '["infer","model","run","--json"]' }), 'hi'),
    /placeholder/
  );
});

test('infer JSON output extracts common text shapes', () => {
  assert.equal(parseOpenClawJsonOutput('{"text":"ok"}'), 'ok');
  assert.equal(parseOpenClawJsonOutput('{"result":{"output":"nested ok"}}'), 'nested ok');
  assert.equal(parseOpenClawJsonOutput('{"choices":[{"message":{"content":"choice ok"}}]}'), 'choice ok');
});

test('infer mode executes with shell=false and passes shell metacharacters as argv', async () => {
  const file = await fakeCli(`#!/usr/bin/env node
const i = process.argv.indexOf('--prompt');
console.log(JSON.stringify({ text: process.argv[i + 1] }));
`);
  const prompt = 'hello; echo SHOULD_NOT_EXECUTE';
  const text = await askOpenClaw(prompt, cfg({
    openclawBin: process.execPath,
    openclawArgsJson: JSON.stringify([file, 'infer', 'model', 'run', '--prompt', '{prompt}', '--json'])
  }));
  assert.equal(text, prompt);
});

test('non-zero CLI exits fail closed', async () => {
  const file = await fakeCli(`#!/usr/bin/env node
console.error('boom');
process.exit(7);
`);
  await assert.rejects(
    () => askOpenClaw('hi', cfg({ openclawBin: process.execPath, openclawArgsJson: JSON.stringify([file, '{prompt}']) })),
    /OpenClaw CLI exited 7/
  );
});

test('stdout limit fails closed', async () => {
  const file = await fakeCli(`#!/usr/bin/env node
console.log('x'.repeat(2048));
`);
  await assert.rejects(
    () => askOpenClaw('hi', cfg({
      openclawBin: process.execPath,
      openclawArgsJson: JSON.stringify([file, '{prompt}']),
      openclawMaxStdoutBytes: 128
    })),
    /exceeded/
  );
});
