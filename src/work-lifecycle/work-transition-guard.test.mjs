import assert from 'node:assert/strict';
import { mkdtemp, rm } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import test from 'node:test';

import { evaluateNextMilestoneGuard, guardNextMilestoneStart, terminalNoticeSatisfied } from './work-transition-guard.ts';
import { readLifecycleEvents } from './work-ledger-store.ts';

async function tempRoot() {
  return mkdtemp(join(tmpdir(), 'work-transition-guard-test-'));
}

function runWith(milestones) {
  return {
    schema_version: 'work_lifecycle.v1',
    run_id: 'work_20260701T000000Z_guard',
    surface: 'telegram_direct',
    title: 'Guard test',
    status: 'RUNNING',
    updated_at: '2026-07-01T00:00:00Z',
    safety_boundary: { forbidden_mutations: ['runtime_hook_import', 'telegram_send'] },
    hold: null,
    milestones
  };
}

function milestone(id, status, notification = {}) {
  return {
    milestone_id: id,
    name: id,
    status,
    required: true,
    artifacts: [],
    hard_gates: [],
    notification: { required: true, delivered: false, queued: false, ...notification }
  };
}

test('M5_G1 required milestone cannot start if prior required milestone is RUNNING', () => {
  const result = evaluateNextMilestoneGuard(runWith([milestone('M4', 'RUNNING'), milestone('M5', 'PENDING')]), 'M5');
  assert.equal(result.allowed, false);
  assert.equal(result.reason, 'PRIOR_REQUIRED_MILESTONE_NOT_TERMINAL');
  assert.equal(result.prior_milestone_id, 'M4');
});

test('M5_G2 required milestone cannot start if prior terminal notice was neither delivered nor queued', () => {
  const result = evaluateNextMilestoneGuard(runWith([milestone('M4', 'PASS'), milestone('M5', 'PENDING')]), 'M5');
  assert.equal(result.allowed, false);
  assert.equal(result.reason, 'PRIOR_REQUIRED_MILESTONE_NOTICE_NOT_DELIVERED_OR_QUEUED');
});

test('guard allows next milestone when prior required milestone is terminal and delivered or queued', () => {
  assert.equal(terminalNoticeSatisfied(milestone('M4', 'PASS', { delivered: true })), true);
  assert.equal(terminalNoticeSatisfied(milestone('M4', 'PASS', { queued: true })), true);
  const delivered = evaluateNextMilestoneGuard(runWith([milestone('M4', 'PASS', { delivered: true }), milestone('M5', 'PENDING')]), 'M5');
  assert.equal(delivered.allowed, true);
  const queued = evaluateNextMilestoneGuard(runWith([milestone('M4', 'PASS', { queued: true }), milestone('M5', 'PENDING')]), 'M5');
  assert.equal(queued.allowed, true);
});

test('M5_G3 guard failure marks run HOLD with INCOMPLETE_CLOSEOUT', async () => {
  const root = await tempRoot();
  try {
    const result = await guardNextMilestoneStart(root, runWith([milestone('M4', 'RUNNING'), milestone('M5', 'PENDING')]), 'M5', {
      now: new Date('2026-07-01T00:00:00Z'),
      timestamp: '2026-07-01T00:00:00Z'
    });
    assert.equal(result.allowed, false);
    assert.equal(result.run.status, 'HOLD');
    assert.equal(result.run.hold.code, 'INCOMPLETE_CLOSEOUT');
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('M5_G4 guard failure emits HOLD notification', async () => {
  const root = await tempRoot();
  try {
    const result = await guardNextMilestoneStart(root, runWith([milestone('M4', 'PASS'), milestone('M5', 'PENDING')]), 'M5', {
      now: new Date('2026-07-01T00:00:00Z'),
      timestamp: '2026-07-01T00:00:00Z'
    });
    assert.equal(result.allowed, false);
    assert.equal(result.notification.notification.terminal_status, 'HOLD');
    assert.match(result.notification.notification.body, /HOLD — Start M5/);
    const events = await readLifecycleEvents(root, 'work_20260701T000000Z_guard');
    assert.equal(events.at(-1).type, 'NOTIFICATION_QUEUED');
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
