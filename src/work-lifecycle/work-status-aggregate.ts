// OpenClaw Stickbot Work Lifecycle Ledger — M2 aggregate run-status derivation
// Sidecar-only module. Do not import from runtime paths until later lifecycle milestones.

import { isWorkTerminalState } from './work-fsm.ts';

export class WorkStatusAggregateError extends Error {
  constructor(code, message, details = {}) {
    super(message);
    this.name = 'WorkStatusAggregateError';
    this.code = code;
    this.details = details;
  }
}

export function requiredMilestones(runRecord) {
  if (!runRecord || typeof runRecord !== 'object') {
    throw new WorkStatusAggregateError('INVALID_RUN_RECORD', 'runRecord must be an object');
  }
  if (!Array.isArray(runRecord.milestones)) {
    return [];
  }
  return runRecord.milestones.filter((milestone) => milestone?.required !== false);
}

export function deriveAggregateRunStatus(runRecord) {
  const milestones = requiredMilestones(runRecord);

  if (runRecord.status === 'ABORT' || runRecord.abort) {
    return aggregate('ABORT', 'run_abort_takes_precedence', runRecord, milestones);
  }

  if (runRecord.status === 'SUPERSEDED' || runRecord.superseded_by) {
    return aggregate('SUPERSEDED', 'run_superseded_takes_precedence', runRecord, milestones);
  }

  const abortedMilestone = milestones.find((milestone) => milestone.status === 'ABORT');
  if (abortedMilestone) {
    return aggregate('ABORT', 'required_milestone_aborted', runRecord, milestones, abortedMilestone);
  }

  const supersededMilestone = milestones.find((milestone) => milestone.status === 'SUPERSEDED');
  if (supersededMilestone) {
    return aggregate('SUPERSEDED', 'required_milestone_superseded', runRecord, milestones, supersededMilestone);
  }

  const failedMilestone = milestones.find((milestone) => milestone.status === 'FAIL');
  if (failedMilestone) {
    return aggregate('FAIL', 'required_milestone_failed', runRecord, milestones, failedMilestone);
  }

  const heldMilestone = milestones.find((milestone) => milestone.status === 'HOLD');
  if (heldMilestone) {
    return aggregate('HOLD', 'required_milestone_held', runRecord, milestones, heldMilestone);
  }

  const runningMilestone = milestones.find((milestone) => milestone.status === 'RUNNING' || milestone.status === 'PENDING');
  if (runRecord.status === 'ACK_PENDING') {
    return aggregate('ACK_PENDING', 'run_ack_pending', runRecord, milestones, runningMilestone ?? null);
  }

  if (milestones.length > 0 && milestones.every((milestone) => milestone.status === 'PASS')) {
    return aggregate('PASS', 'all_required_milestones_passed', runRecord, milestones);
  }

  if (runningMilestone || runRecord.status === 'RUNNING') {
    return aggregate('RUNNING', 'required_milestone_incomplete', runRecord, milestones, runningMilestone ?? null);
  }

  if (isWorkTerminalState(runRecord.status)) {
    return aggregate(runRecord.status, 'run_status_terminal_without_required_milestone_override', runRecord, milestones);
  }

  return aggregate('RUNNING', 'default_running_no_required_milestones', runRecord, milestones);
}

function aggregate(status, reason, runRecord, milestones, decisiveMilestone = null) {
  return {
    schema_version: 'work_lifecycle.aggregate.v1',
    run_id: runRecord.run_id ?? null,
    status,
    reason,
    decisive_milestone_id: decisiveMilestone?.milestone_id ?? null,
    required_milestone_count: milestones.length,
    required_terminal_count: milestones.filter((milestone) => isWorkTerminalState(milestone.status)).length,
    required_pass_count: milestones.filter((milestone) => milestone.status === 'PASS').length,
    required_fail_count: milestones.filter((milestone) => milestone.status === 'FAIL').length,
    required_hold_count: milestones.filter((milestone) => milestone.status === 'HOLD').length,
    required_abort_count: milestones.filter((milestone) => milestone.status === 'ABORT').length,
    required_superseded_count: milestones.filter((milestone) => milestone.status === 'SUPERSEDED').length
  };
}

export function applyAggregateStatus(runRecord, options = {}) {
  const derived = deriveAggregateRunStatus(runRecord);
  return {
    ...runRecord,
    status: derived.status,
    updated_at: options.timestamp ?? runRecord.updated_at,
    ended_at: isWorkTerminalState(derived.status) ? (options.timestamp ?? runRecord.ended_at ?? null) : runRecord.ended_at,
    aggregate: derived
  };
}
