import assert from 'node:assert/strict';
import test from 'node:test';

import {
  assertValidMilestoneTransition,
  assertValidRunTransition,
  transitionMilestone,
  transitionRun
} from './work-fsm.ts';

test('M2_G1 invalid transitions are rejected', () => {
  assert.throws(() => assertValidMilestoneTransition('PENDING', 'PASS'), /Invalid milestone transition/);
  assert.throws(() => assertValidRunTransition('ACK_PENDING', 'PASS'), /Invalid run transition/);
  assert.equal(assertValidMilestoneTransition('PENDING', 'RUNNING'), true);
});

test('M2_G2 terminal milestone states are immutable', () => {
  assert.throws(() => assertValidMilestoneTransition('PASS', 'RUNNING'), /Invalid milestone transition PASS -> RUNNING/);
  assert.throws(() => assertValidMilestoneTransition('FAIL', 'HOLD'), /Invalid milestone transition FAIL -> HOLD/);
});

test('SUPERSEDED transitions require replacement run id', () => {
  assert.throws(() => assertValidRunTransition('RUNNING', 'SUPERSEDED'), /requires supersededBy/);
  assert.equal(assertValidRunTransition('RUNNING', 'SUPERSEDED', { supersededBy: 'work_replacement' }), true);
  assert.throws(() => assertValidMilestoneTransition('RUNNING', 'SUPERSEDED'), /requires supersededBy/);
});

test('transition helpers clone records and stamp terminal metadata', () => {
  const milestone = { milestone_id: 'M2', status: 'RUNNING', required: true };
  const transitioned = transitionMilestone(milestone, 'PASS', { timestamp: '2026-07-01T05:55:00Z' });
  assert.notEqual(transitioned, milestone);
  assert.equal(transitioned.status, 'PASS');
  assert.equal(transitioned.ended_at, '2026-07-01T05:55:00Z');

  const run = { run_id: 'work_test', status: 'RUNNING', updated_at: 'old', ended_at: null, superseded_by: null };
  const aborted = transitionRun(run, 'ABORT', { timestamp: '2026-07-01T05:56:00Z' });
  assert.equal(aborted.status, 'ABORT');
  assert.equal(aborted.ended_at, '2026-07-01T05:56:00Z');
});
