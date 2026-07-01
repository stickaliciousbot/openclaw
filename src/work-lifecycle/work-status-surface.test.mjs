import assert from 'node:assert/strict';
import { mkdtemp, rm } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import test from 'node:test';

import { appendLifecycleEvent, atomicWriteJson, createWorkLedgerPaths, writeRunSummary } from './work-ledger-store.ts';
import {
  assertStatusRedacted,
  getWorkRunStatus,
  listActiveWorkRuns,
  listFailedNotificationDeliveries,
  renderWorkStatusText,
  replayWorkRunStatus
} from './work-status-surface.ts';

async function tempRoot() {
  return mkdtemp(join(tmpdir(), 'work-status-surface-test-'));
}

function runRecord({ runId = 'work_20260701T000000Z_status', status = 'RUNNING', title = 'Status test run' } = {}) {
  return {
    schema_version: 'work_lifecycle.v1',
    run_id: runId,
    parent_run_id: null,
    user_turn_id: 'telegram:turn:sha256-redacted',
    surface: 'telegram_direct',
    chat_id: 'telegram:direct:sha256-redacted',
    title,
    status,
    started_at: '2026-07-01T00:00:00Z',
    updated_at: '2026-07-01T00:01:00Z',
    ended_at: status === 'PASS' ? '2026-07-01T00:02:00Z' : null,
    milestones: [{ milestone_id: 'M7', status, required: true }],
    hold: status === 'HOLD' ? { code: 'TEST_HOLD', reason: 'Waiting for approval' } : null,
    failure: null,
    abort: null
  };
}

test('M7_G1 active runs visible from status surface', async () => {
  const root = await tempRoot();
  try {
    await writeRunSummary(root, runRecord({ runId: 'work_active', status: 'RUNNING' }));
    await writeRunSummary(root, runRecord({ runId: 'work_done', status: 'PASS' }));
    const active = await listActiveWorkRuns(root);
    assert.deepEqual(active.map((run) => run.run_id), ['work_active']);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('M7_G2 failed notification delivery visible from status surface', async () => {
  const root = await tempRoot();
  try {
    const paths = createWorkLedgerPaths(root, 'work_notify');
    await atomicWriteJson(join(paths.outboxDir, 'notif_failed.json'), {
      notification_id: 'notif_failed',
      run_id: 'work_notify',
      kind: 'TERMINAL',
      status: 'FAILED',
      surface: 'telegram_direct',
      attempts: [{ status: 'FAILED', error: 'telegram:direct:123456789 failed', timestamp: '2026-07-01T00:00:00Z' }]
    });
    const failed = await listFailedNotificationDeliveries(root);
    assert.equal(failed.length, 1);
    assert.equal(failed[0].notification_id, 'notif_failed');
    assert.doesNotMatch(JSON.stringify(failed), /123456789/);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('M7_G3 replay command validates event log', async () => {
  const root = await tempRoot();
  try {
    const runId = 'work_replay';
    await appendLifecycleEvent(root, { schema_version: 'work_lifecycle.v1', event_id: 'evt1', run_id: runId, type: 'RUN_CREATED', timestamp: '2026-07-01T00:00:00Z' });
    await appendLifecycleEvent(root, { schema_version: 'work_lifecycle.v1', event_id: 'evt2', run_id: runId, type: 'RUN_TRANSITION', from_state: 'RUNNING', to_state: 'PASS', timestamp: '2026-07-01T00:01:00Z' });
    const replay = await replayWorkRunStatus(root, runId);
    assert.equal(replay.run_id, runId);
    assert.equal(replay.status, 'PASS');
    assert.equal(replay.event_count, 2);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('M7_G4 status output does not expose raw identifiers or secrets', async () => {
  const root = await tempRoot();
  try {
    await writeRunSummary(root, runRecord({ title: 'raw 123456789 token=secretvalue', status: 'HOLD' }));
    const status = await getWorkRunStatus(root, 'work_20260701T000000Z_status');
    const rendered = renderWorkStatusText(status);
    assert.doesNotMatch(rendered, /123456789/);
    assert.doesNotMatch(rendered, /secretvalue/);
    assert.equal(assertStatusRedacted(rendered), true);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
