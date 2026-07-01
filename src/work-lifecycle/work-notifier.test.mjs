import assert from 'node:assert/strict';
import { mkdtemp, rm } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import test from 'node:test';

import { readQueuedNotification } from './work-notification-outbox.ts';
import { assertNotificationRedacted, renderTerminalNotification } from './work-notification-template.ts';
import { queueTerminalNotification, terminalStatusRequiresNotification } from './work-notifier.ts';
import { readLifecycleEvents } from './work-ledger-store.ts';

async function tempRoot() {
  return mkdtemp(join(tmpdir(), 'work-notifier-test-'));
}

function baseRun(status = 'RUNNING') {
  return {
    schema_version: 'work_lifecycle.v1',
    run_id: 'work_20260701T000000Z_notifier',
    surface: 'telegram_direct',
    title: 'Notifier test run',
    status,
    safety_boundary: {
      forbidden_mutations: ['gateway_restart', 'provider_auth', 'telegram_send']
    },
    hold: null,
    abort: null,
    superseded_by: null
  };
}

function milestone(status) {
  return {
    milestone_id: `M_${status}`,
    name: `${status} milestone`,
    status,
    hard_gates: [
      { name: 'gate_one', status: status === 'FAIL' ? 'FAIL' : 'PASS', reason: status === 'FAIL' ? 'expected failure' : undefined }
    ],
    artifacts: ['sharedspace/runtime-kernel-validation/work-lifecycle/example.json']
  };
}

test('M4_G1 PASS milestone creates terminal notification', async () => {
  const root = await tempRoot();
  try {
    const queued = await queueTerminalNotification(root, { run: baseRun(), milestone: milestone('PASS'), next: 'M5 guard' });
    assert.equal(queued.notification.terminal_status, 'PASS');
    assert.match(queued.notification.body, /PASS — PASS milestone/);
    assert.match(queued.notification.body, /Gates:/);
    const readBack = await readQueuedNotification(root, baseRun().run_id, queued.notification.notification_id);
    assert.equal(readBack.status, 'QUEUED');
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('M4_G2 FAIL milestone creates terminal notification', async () => {
  const root = await tempRoot();
  try {
    const queued = await queueTerminalNotification(root, { run: baseRun(), milestone: milestone('FAIL'), failure: { action_taken: 'Stopped before apply' } });
    assert.equal(queued.notification.terminal_status, 'FAIL');
    assert.match(queued.notification.body, /Failed gates:/);
    assert.match(queued.notification.body, /Stopped before apply/);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('M4_G3 HOLD milestone creates terminal notification', async () => {
  const root = await tempRoot();
  try {
    const run = { ...baseRun('HOLD'), hold: { reason: 'Needs approval', needed_from_operator: 'Approve validation' } };
    const queued = await queueTerminalNotification(root, { run, milestone: milestone('HOLD') });
    assert.equal(queued.notification.terminal_status, 'HOLD');
    assert.match(queued.notification.body, /Blocked on:/);
    assert.match(queued.notification.body, /Approve validation/);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('M4_G4 ABORT milestone creates terminal notification', async () => {
  const root = await tempRoot();
  try {
    const run = { ...baseRun('ABORT'), abort: { reason: 'Operator stopped run' } };
    const queued = await queueTerminalNotification(root, { run, milestone: milestone('ABORT') });
    assert.equal(queued.notification.terminal_status, 'ABORT');
    assert.match(queued.notification.body, /Reason:/);
    assert.match(queued.notification.body, /Operator stopped run/);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('M4_G5 notification includes gates artifacts next step and safety boundary', () => {
  const body = renderTerminalNotification({
    run: baseRun(),
    milestone: milestone('PASS'),
    next: 'Run M5 no-next guard validation'
  });
  assert.match(body, /gate_one: PASS/);
  assert.match(body, /sharedspace\/runtime-kernel-validation\/work-lifecycle\/example.json/);
  assert.match(body, /Run M5 no-next guard validation/);
  assert.match(body, /Safety boundary:/);
});

test('M4_G6 notification redaction test passes', () => {
  const redacted = renderTerminalNotification({
    run: { ...baseRun(), title: 'raw 123456789 token=secretvalue' },
    milestone: { ...milestone('FAIL'), name: 'telegram:direct:123456789 failed' },
    status: 'FAIL'
  });
  assert.doesNotMatch(redacted, /123456789/);
  assert.doesNotMatch(redacted, /secretvalue/);
  assert.equal(assertNotificationRedacted(redacted), true);
});

test('terminal notifications append NOTIFICATION_QUEUED event and reject non-terminal status', async () => {
  const root = await tempRoot();
  try {
    assert.equal(terminalStatusRequiresNotification('RUNNING'), false);
    await assert.rejects(() => queueTerminalNotification(root, { run: baseRun(), milestone: milestone('RUNNING') }), /Terminal notification requires terminal status/);
    const queued = await queueTerminalNotification(root, { run: baseRun(), milestone: milestone('SUPERSEDED') });
    const events = await readLifecycleEvents(root, baseRun().run_id);
    assert.equal(events.at(-1).type, 'NOTIFICATION_QUEUED');
    assert.equal(events.at(-1).notification_id, queued.notification.notification_id);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
