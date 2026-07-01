// OpenClaw Stickbot Work Lifecycle Ledger — M5 no-next-milestone guard
// Sidecar-only module. Do not import from runtime paths until later lifecycle milestones.

import { isWorkTerminalState } from './work-fsm.ts';
import { queueTerminalNotification } from './work-notifier.ts';

export class WorkTransitionGuardError extends Error {
  constructor(code, message, details = {}) {
    super(message);
    this.name = 'WorkTransitionGuardError';
    this.code = code;
    this.details = details;
  }
}

export function terminalNoticeSatisfied(milestone) {
  const notification = milestone?.notification ?? {};
  return notification.delivered === true || notification.queued === true;
}

export function findPriorRequiredMilestone(runRecord, nextMilestoneId) {
  const milestones = Array.isArray(runRecord?.milestones) ? runRecord.milestones : [];
  const nextIndex = milestones.findIndex((milestone) => milestone?.milestone_id === nextMilestoneId);
  const searchEnd = nextIndex >= 0 ? nextIndex : milestones.length;
  for (let index = searchEnd - 1; index >= 0; index -= 1) {
    const milestone = milestones[index];
    if (milestone?.required !== false) return milestone;
  }
  return null;
}

export function evaluateNextMilestoneGuard(runRecord, nextMilestoneId) {
  if (!runRecord || typeof runRecord !== 'object') {
    throw new WorkTransitionGuardError('INVALID_RUN_RECORD', 'runRecord must be an object');
  }
  if (!nextMilestoneId) {
    throw new WorkTransitionGuardError('NEXT_MILESTONE_ID_REQUIRED', 'nextMilestoneId is required');
  }

  const prior = findPriorRequiredMilestone(runRecord, nextMilestoneId);
  if (!prior) {
    return { allowed: true, reason: 'no_prior_required_milestone', prior_milestone_id: null };
  }

  if (!isWorkTerminalState(prior.status)) {
    return {
      allowed: false,
      reason: 'PRIOR_REQUIRED_MILESTONE_NOT_TERMINAL',
      prior_milestone_id: prior.milestone_id,
      prior_status: prior.status
    };
  }

  if (!terminalNoticeSatisfied(prior)) {
    return {
      allowed: false,
      reason: 'PRIOR_REQUIRED_MILESTONE_NOTICE_NOT_DELIVERED_OR_QUEUED',
      prior_milestone_id: prior.milestone_id,
      prior_status: prior.status
    };
  }

  return {
    allowed: true,
    reason: 'prior_required_milestone_closed_and_notified',
    prior_milestone_id: prior.milestone_id,
    prior_status: prior.status
  };
}

export function markRunHoldForIncompleteCloseout(runRecord, guardResult, options = {}) {
  const timestamp = options.timestamp ?? new Date().toISOString();
  const reason = guardResult?.reason ?? 'INCOMPLETE_CLOSEOUT';
  return {
    ...runRecord,
    status: 'HOLD',
    updated_at: timestamp,
    hold: {
      code: 'INCOMPLETE_CLOSEOUT',
      reason: `Cannot start next required milestone: ${reason}`,
      needed_from_operator: options.neededFromOperator ?? 'Close or queue the prior milestone terminal notification, then retry.',
      blocker_artifacts: options.blockerArtifacts ?? []
    }
  };
}

export async function guardNextMilestoneStart(rootDir, runRecord, nextMilestoneId, options = {}) {
  const result = evaluateNextMilestoneGuard(runRecord, nextMilestoneId);
  if (result.allowed) {
    return { allowed: true, run: runRecord, guard: result, notification: null };
  }

  const heldRun = markRunHoldForIncompleteCloseout(runRecord, result, options);
  const notification = await queueTerminalNotification(rootDir, {
    run: heldRun,
    milestone: {
      milestone_id: nextMilestoneId,
      name: options.milestoneName ?? `Start ${nextMilestoneId}`,
      status: 'HOLD',
      artifacts: options.artifacts ?? [],
      hard_gates: [{ name: 'no_next_without_closeout', status: 'HOLD', reason: result.reason }]
    },
    status: 'HOLD',
    hold: heldRun.hold,
    next: heldRun.hold.needed_from_operator,
    now: options.now ?? new Date()
  });

  return { allowed: false, run: heldRun, guard: result, notification };
}
