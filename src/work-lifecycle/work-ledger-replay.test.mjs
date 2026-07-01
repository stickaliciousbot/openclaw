import assert from 'node:assert/strict';
import { mkdtemp, rm } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import test from 'node:test';

import { appendLifecycleEvent } from './work-ledger-store.ts';
import { replayLifecycleEvents, replayLifecycleRun } from './work-ledger-replay.ts';

async function tempRoot() {
  return mkdtemp(join(tmpdir(), 'work-ledger-replay-test-'));
}

test('replayLifecycleEvents reconstructs run and milestone status', () => {
  const events = [
    { schema_version: 'work_lifecycle.v1', event_id: 'evt1', run_id: 'work_20260701T000000Z_replay', type: 'RUN_CREATED', timestamp: '2026-07-01T00:00:00Z' },
    { schema_version: 'work_lifecycle.v1', event_id: 'evt2', run_id: 'work_20260701T000000Z_replay', type: 'ACK_DELIVERED', timestamp: '2026-07-01T00:00:01Z', notification_id: 'notif_ack' },
    { schema_version: 'work_lifecycle.v1', event_id: 'evt3', run_id: 'work_20260701T000000Z_replay', milestone_id: 'M1', type: 'MILESTONE_TRANSITION', from_state: 'PENDING', to_state: 'RUNNING', timestamp: '2026-07-01T00:00:02Z' },
    { schema_version: 'work_lifecycle.v1', event_id: 'evt4', run_id: 'work_20260701T000000Z_replay', milestone_id: 'M1', type: 'MILESTONE_TRANSITION', from_state: 'RUNNING', to_state: 'PASS', timestamp: '2026-07-01T00:00:03Z', notification_id: 'notif_m1_pass' },
    { schema_version: 'work_lifecycle.v1', event_id: 'evt5', run_id: 'work_20260701T000000Z_replay', type: 'RUN_TRANSITION', from_state: 'RUNNING', to_state: 'PASS', timestamp: '2026-07-01T00:00:04Z' }
  ];

  const summary = replayLifecycleEvents(events);
  assert.equal(summary.run_id, 'work_20260701T000000Z_replay');
  assert.equal(summary.status, 'PASS');
  assert.equal(summary.ack.delivered, true);
  assert.equal(summary.ack.notification_id, 'notif_ack');
  assert.equal(summary.milestones.M1.status, 'PASS');
  assert.equal(summary.milestones.M1.notification_id, 'notif_m1_pass');
  assert.equal(summary.event_count, 5);
});

test('replayLifecycleEvents rejects mixed run ids', () => {
  assert.throws(
    () => replayLifecycleEvents([
      { run_id: 'work_20260701T000000Z_a', type: 'RUN_CREATED' },
      { run_id: 'work_20260701T000000Z_b', type: 'RUN_CREATED' }
    ]),
    /multiple run ids/
  );
});

test('replayLifecycleRun reads JSONL event log from store', async () => {
  const root = await tempRoot();
  try {
    const runId = 'work_20260701T000000Z_replay_store';
    await appendLifecycleEvent(root, { schema_version: 'work_lifecycle.v1', event_id: 'evt1', run_id: runId, type: 'RUN_CREATED' });
    await appendLifecycleEvent(root, { schema_version: 'work_lifecycle.v1', event_id: 'evt2', run_id: runId, type: 'RUN_TRANSITION', to_state: 'HOLD' });
    const summary = await replayLifecycleRun(root, runId);
    assert.equal(summary.status, 'HOLD');
    assert.equal(summary.event_count, 2);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
