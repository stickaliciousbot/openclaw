// OpenClaw Stickbot Work Lifecycle Ledger — M2 finite-state transition guard
// Sidecar-only module. Do not import from runtime paths until later lifecycle milestones.

export class WorkLifecycleFsmError extends Error {
  constructor(code, message, details = {}) {
    super(message);
    this.name = 'WorkLifecycleFsmError';
    this.code = code;
    this.details = details;
  }
}

export const WORK_RUN_STATES = Object.freeze([
  'ACK_PENDING',
  'RUNNING',
  'PASS',
  'FAIL',
  'HOLD',
  'ABORT',
  'SUPERSEDED'
]);

export const WORK_MILESTONE_STATES = Object.freeze([
  'PENDING',
  'RUNNING',
  'PASS',
  'FAIL',
  'HOLD',
  'ABORT',
  'SUPERSEDED'
]);

export const WORK_TERMINAL_STATES = Object.freeze(['PASS', 'FAIL', 'HOLD', 'ABORT', 'SUPERSEDED']);

export const WORK_RUN_TRANSITIONS = Object.freeze({
  ACK_PENDING: Object.freeze(['RUNNING', 'HOLD', 'ABORT', 'SUPERSEDED']),
  RUNNING: Object.freeze(['PASS', 'FAIL', 'HOLD', 'ABORT', 'SUPERSEDED']),
  PASS: Object.freeze([]),
  FAIL: Object.freeze([]),
  HOLD: Object.freeze(['RUNNING', 'ABORT', 'SUPERSEDED']),
  ABORT: Object.freeze([]),
  SUPERSEDED: Object.freeze([])
});

export const WORK_MILESTONE_TRANSITIONS = Object.freeze({
  PENDING: Object.freeze(['RUNNING', 'ABORT', 'SUPERSEDED']),
  RUNNING: Object.freeze(['PASS', 'FAIL', 'HOLD', 'ABORT', 'SUPERSEDED']),
  PASS: Object.freeze([]),
  FAIL: Object.freeze([]),
  HOLD: Object.freeze(['RUNNING', 'ABORT', 'SUPERSEDED']),
  ABORT: Object.freeze([]),
  SUPERSEDED: Object.freeze([])
});

export function isWorkTerminalState(state) {
  return WORK_TERMINAL_STATES.includes(state);
}

function assertKnownState(kind, state, allowed) {
  if (!allowed.includes(state)) {
    throw new WorkLifecycleFsmError('UNKNOWN_STATE', `Unknown ${kind} state ${String(state)}`, { kind, state });
  }
}

export function assertValidRunTransition(fromState, toState, options = {}) {
  assertKnownState('run', fromState, WORK_RUN_STATES);
  assertKnownState('run', toState, WORK_RUN_STATES);

  const allowed = WORK_RUN_TRANSITIONS[fromState] ?? [];
  if (!allowed.includes(toState)) {
    const code = isWorkTerminalState(fromState) ? 'TERMINAL_STATE_IMMUTABLE' : 'INVALID_RUN_TRANSITION';
    throw new WorkLifecycleFsmError(code, `Invalid run transition ${fromState} -> ${toState}`, {
      fromState,
      toState,
      allowed
    });
  }

  if (toState === 'SUPERSEDED' && !options.supersededBy) {
    throw new WorkLifecycleFsmError('SUPERSEDED_REQUIRES_REPLACEMENT', 'SUPERSEDED run transition requires supersededBy', {
      fromState,
      toState
    });
  }

  return true;
}

export function assertValidMilestoneTransition(fromState, toState, options = {}) {
  assertKnownState('milestone', fromState, WORK_MILESTONE_STATES);
  assertKnownState('milestone', toState, WORK_MILESTONE_STATES);

  const allowed = WORK_MILESTONE_TRANSITIONS[fromState] ?? [];
  if (!allowed.includes(toState)) {
    const code = isWorkTerminalState(fromState) ? 'TERMINAL_STATE_IMMUTABLE' : 'INVALID_MILESTONE_TRANSITION';
    throw new WorkLifecycleFsmError(code, `Invalid milestone transition ${fromState} -> ${toState}`, {
      fromState,
      toState,
      allowed
    });
  }

  if (toState === 'SUPERSEDED' && !options.supersededBy) {
    throw new WorkLifecycleFsmError('SUPERSEDED_REQUIRES_REPLACEMENT', 'SUPERSEDED milestone transition requires supersededBy', {
      fromState,
      toState
    });
  }

  return true;
}

export function transitionRun(runRecord, toState, options = {}) {
  if (!runRecord || typeof runRecord !== 'object') {
    throw new WorkLifecycleFsmError('INVALID_RUN_RECORD', 'runRecord must be an object');
  }
  assertValidRunTransition(runRecord.status, toState, options);

  return {
    ...runRecord,
    status: toState,
    updated_at: options.timestamp ?? runRecord.updated_at,
    ended_at: isWorkTerminalState(toState) ? (options.timestamp ?? runRecord.ended_at ?? null) : runRecord.ended_at,
    superseded_by: toState === 'SUPERSEDED' ? options.supersededBy : runRecord.superseded_by
  };
}

export function transitionMilestone(milestone, toState, options = {}) {
  if (!milestone || typeof milestone !== 'object') {
    throw new WorkLifecycleFsmError('INVALID_MILESTONE_RECORD', 'milestone must be an object');
  }
  assertValidMilestoneTransition(milestone.status, toState, options);

  return {
    ...milestone,
    status: toState,
    started_at: milestone.started_at ?? (toState === 'RUNNING' ? (options.timestamp ?? null) : milestone.started_at),
    ended_at: isWorkTerminalState(toState) ? (options.timestamp ?? milestone.ended_at ?? null) : milestone.ended_at,
    superseded_by: toState === 'SUPERSEDED' ? options.supersededBy : milestone.superseded_by
  };
}
