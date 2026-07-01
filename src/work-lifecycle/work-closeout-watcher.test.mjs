import assert from 'node:assert/strict';
import { mkdtemp, rm } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import test from 'node:test';

import { writeRunSummary, readRunSummary, readLifecycleEvents } from './work-ledger-store.ts';
import { writeWorkHeartbeat, readWorkHeartbeat } from './work-heartbeat.ts';
import { evaluateStaleness, watchRunCloseout, watchAllActiveRuns } from './work-closeout-watcher.ts';

async function tempRoot() {
  return mkdtemp(join(tmpdir(), 'work-closeout-watcher-test-'));
}

function runRecord({ runId = 'work_20260701T000000Z_watch', status = 'RUNNING', updatedAt = '2026-07-01T00:00:00Z', milestoneStatus = 'RUNNING', notification = { required: true, delivered: false, queued: false } } = {}) {
  return {
    schema_version: 'work_lifecycle.v1',
    run_id: runId,
    surface: 'telegram_direct',
    title: 'Watcher test run',
    status,
    started_at: updatedAt,
    updated_at: updatedAt,
    ended_at: null,
    safety_boundary: { forbidden_mutations: ['runtime_hook_import', 'telegram_send'] },
    ack: { required: true, delivered: true },
    milestones: [{
      milestone_id: 'M6',
      name: 'M6 watcher',
      status: milestoneStatus,
      required: true,
      artifacts: [],
      hard_gates: [],
      notification
    }],
    failure: null,
    hold: null,
    abort: null,
    superseded_by: null
  };
}

test('M6_G1 long job writes heartbeat', async () => {
  const root = await tempRoot();
  try {
    const run = runRecord();
    await writeRunSummary(root, run);
    const heartbeat = await writeWorkHeartbeat(root, run, { timestamp: '2026-07-01T00:01:00Z', staleAfterMs: 1000 });
    assert.equal(heartbeat.run_id, run.run_id);
    assert.equal(heartbeat.status, 'RUNNING');
    const readBack = await readWorkHeartbeat(root, run.run_id);
    assert.equal(readBack.heartbeat_at, '2026-07-01T00:01:00Z');
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('M6_G2 watcher detects stale ACK_PENDING', () => {
  const stale = evaluateStaleness({
    runRecord: runRecord({ status: 'ACK_PENDING', updatedAt: '2026-07-01T00:00:00Z' }),
    now: new Date('2026-07-01T00:10:00Z'),
    staleAfterMs: 1000
  });
  assert.equal(stale.stale, true);
  assert.equal(stale.reason, 'STALE_ACK_PENDING');
});

test('M6_G3 watcher detects stale RUNNING and marks HOLD', async () => {
  const root = await tempRoot();
  try {
    const run = runRecord({ updatedAt: '2026-07-01T00:00:00Z' });
    await writeRunSummary(root, run);
    const result = await watchRunCloseout(root, run.run_id, {
      now: new Date('2026-07-01T00:10:00Z'),
      timestamp: '2026-07-01T00:10:00Z',
      staleAfterMs: 1000,
      timeoutStatus: 'HOLD'
    });
    assert.equal(result.action, 'HOLD');
    assert.equal(result.run.status, 'HOLD');
    assert.equal(result.run.hold.code, 'STALE_RUNNING');
    const persisted = await readRunSummary(root, run.run_id);
    assert.equal(persisted.status, 'HOLD');
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('M6_G4 watcher emits notification independently of model', async () => {
  const root = await tempRoot();
  try {
    const run = runRecord({ updatedAt: '2026-07-01T00:00:00Z' });
    await writeRunSummary(root, run);
    const result = await watchRunCloseout(root, run.run_id, {
      now: new Date('2026-07-01T00:10:00Z'),
      timestamp: '2026-07-01T00:10:00Z',
      staleAfterMs: 1000
    });
    assert.equal(result.notification.notification.terminal_status, 'HOLD');
    assert.match(result.notification.notification.body, /Watcher held stale run/);
    const events = await readLifecycleEvents(root, run.run_id);
    assert.equal(events.at(-1).type, 'WATCHER_ALERT');
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('M6_G5 restart-style scan reads persisted active run and emits closeout', async () => {
  const root = await tempRoot();
  try {
    const run = runRecord({ runId: 'work_20260701T000000Z_restart', updatedAt: '2026-07-01T00:00:00Z' });
    await writeRunSummary(root, run);
    // Simulate a fresh process by only using persisted root state through watchAllActiveRuns.
    const results = await watchAllActiveRuns(root, {
      now: new Date('2026-07-01T00:10:00Z'),
      timestamp: '2026-07-01T00:10:00Z',
      staleAfterMs: 1000
    });
    assert.equal(results.length, 1);
    assert.equal(results[0].run.run_id, run.run_id);
    assert.equal(results[0].action, 'HOLD');
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('terminal milestone missing notice is detected', () => {
  const stale = evaluateStaleness({
    runRecord: runRecord({ status: 'PASS', milestoneStatus: 'PASS', notification: { required: true, delivered: false, queued: false } }),
    now: new Date('2026-07-01T00:01:00Z'),
    staleAfterMs: 999999
  });
  assert.equal(stale.stale, true);
  assert.equal(stale.reason, 'TERMINAL_NOTICE_MISSING');
});
