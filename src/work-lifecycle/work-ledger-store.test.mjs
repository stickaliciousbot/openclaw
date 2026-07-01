import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import test from 'node:test';

import {
  appendLifecycleEvent,
  atomicWriteJson,
  createWorkLedgerPaths,
  ensureWorkLedgerDirs,
  readJsonLines,
  readRunSummary,
  writeRunSummary
} from './work-ledger-store.ts';

async function tempRoot() {
  return mkdtemp(join(tmpdir(), 'work-ledger-store-test-'));
}

test('createWorkLedgerPaths returns expected sidecar layout', () => {
  const paths = createWorkLedgerPaths('/tmp/root', 'work_20260701T000000Z_test');
  assert.equal(paths.runPath, '/tmp/root/runs/work_20260701T000000Z_test.json');
  assert.equal(paths.eventPath, '/tmp/root/events/work_20260701T000000Z_test.jsonl');
  assert.equal(paths.lockPath, '/tmp/root/locks/work_20260701T000000Z_test.lock');
});

test('writeRunSummary atomically writes readable JSON summary', async () => {
  const root = await tempRoot();
  try {
    const run = {
      schema_version: 'work_lifecycle.v1',
      run_id: 'work_20260701T000000Z_store',
      status: 'RUNNING'
    };
    const path = await writeRunSummary(root, run);
    assert.equal(path, join(root, 'runs', `${run.run_id}.json`));
    assert.deepEqual(await readRunSummary(root, run.run_id), run);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('appendLifecycleEvent writes append-only JSONL events', async () => {
  const root = await tempRoot();
  try {
    const event1 = { schema_version: 'work_lifecycle.v1', event_id: 'evt1', run_id: 'work_20260701T000000Z_events', type: 'RUN_CREATED' };
    const event2 = { schema_version: 'work_lifecycle.v1', event_id: 'evt2', run_id: event1.run_id, type: 'ACK_DELIVERED' };
    const eventPath = await appendLifecycleEvent(root, event1);
    await appendLifecycleEvent(root, event2);
    assert.deepEqual(await readJsonLines(eventPath), [event1, event2]);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('readJsonLines rejects corrupt lines unless quarantine requested', async () => {
  const root = await tempRoot();
  try {
    await ensureWorkLedgerDirs(root);
    const path = join(root, 'events', 'work_20260701T000000Z_corrupt.jsonl');
    await writeFile(path, '{"ok":true}\nnot-json\n', 'utf8');
    await assert.rejects(() => readJsonLines(path), /Corrupt JSONL line 2/);
    assert.deepEqual(await readJsonLines(path, { quarantineCorrupt: true }), [{ ok: true }]);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('atomicWriteJson removes temporary file on write failure', async () => {
  const root = await tempRoot();
  try {
    const badPath = join(root, 'missing-parent-as-file', 'run.json');
    await writeFile(join(root, 'missing-parent-as-file'), 'not a directory', 'utf8');
    await assert.rejects(() => atomicWriteJson(badPath, { ok: true }), /Failed atomic JSON write/);
    const rootListing = await readFile(join(root, 'missing-parent-as-file'), 'utf8');
    assert.equal(rootListing, 'not a directory');
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
