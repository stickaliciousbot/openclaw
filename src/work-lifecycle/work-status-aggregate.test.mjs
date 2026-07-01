import assert from 'node:assert/strict';
import test from 'node:test';

import { applyAggregateStatus, deriveAggregateRunStatus } from './work-status-aggregate.ts';

function runWithMilestones(status, milestones, extras = {}) {
  return {
    schema_version: 'work_lifecycle.v1',
    run_id: 'work_20260701T000000Z_aggregate',
    status,
    updated_at: '2026-07-01T00:00:00Z',
    ended_at: null,
    milestones,
    failure: null,
    hold: null,
    abort: null,
    superseded_by: null,
    ...extras
  };
}

test('M2_G3 RUNNING run with failed required milestone derives FAIL', () => {
  const derived = deriveAggregateRunStatus(runWithMilestones('RUNNING', [
    { milestone_id: 'M1', required: true, status: 'PASS' },
    { milestone_id: 'M2', required: true, status: 'FAIL' }
  ]));
  assert.equal(derived.status, 'FAIL');
  assert.equal(derived.reason, 'required_milestone_failed');
  assert.equal(derived.decisive_milestone_id, 'M2');
});

test('M2_G4 HOLD milestone derives HOLD unless run is superseded or aborted', () => {
  const held = deriveAggregateRunStatus(runWithMilestones('RUNNING', [
    { milestone_id: 'M1', required: true, status: 'HOLD' }
  ]));
  assert.equal(held.status, 'HOLD');
  assert.equal(held.reason, 'required_milestone_held');

  const aborted = deriveAggregateRunStatus(runWithMilestones('ABORT', [
    { milestone_id: 'M1', required: true, status: 'HOLD' }
  ], { abort: { code: 'USER_ABORT', reason: 'operator stopped run' } }));
  assert.equal(aborted.status, 'ABORT');

  const superseded = deriveAggregateRunStatus(runWithMilestones('SUPERSEDED', [
    { milestone_id: 'M1', required: true, status: 'HOLD' }
  ], { superseded_by: 'work_replacement' }));
  assert.equal(superseded.status, 'SUPERSEDED');
});

test('M2_G5 SUPERSEDED links to replacement run and applies aggregate status', () => {
  const run = runWithMilestones('SUPERSEDED', [
    { milestone_id: 'M1', required: true, status: 'PASS' }
  ], { superseded_by: 'work_20260701T010000Z_replacement' });
  const applied = applyAggregateStatus(run, { timestamp: '2026-07-01T01:00:00Z' });
  assert.equal(applied.status, 'SUPERSEDED');
  assert.equal(applied.superseded_by, 'work_20260701T010000Z_replacement');
  assert.equal(applied.aggregate.reason, 'run_superseded_takes_precedence');
  assert.equal(applied.ended_at, '2026-07-01T01:00:00Z');
});

test('all required milestones passed derives PASS', () => {
  const derived = deriveAggregateRunStatus(runWithMilestones('RUNNING', [
    { milestone_id: 'M1', required: true, status: 'PASS' },
    { milestone_id: 'optional', required: false, status: 'FAIL' }
  ]));
  assert.equal(derived.status, 'PASS');
  assert.equal(derived.reason, 'all_required_milestones_passed');
});

test('pending or running required milestones derive RUNNING', () => {
  const derived = deriveAggregateRunStatus(runWithMilestones('RUNNING', [
    { milestone_id: 'M1', required: true, status: 'PASS' },
    { milestone_id: 'M2', required: true, status: 'PENDING' }
  ]));
  assert.equal(derived.status, 'RUNNING');
  assert.equal(derived.reason, 'required_milestone_incomplete');
  assert.equal(derived.decisive_milestone_id, 'M2');
});
