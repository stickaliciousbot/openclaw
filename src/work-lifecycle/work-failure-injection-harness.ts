// OpenClaw Stickbot Work Lifecycle Ledger — M8 failure injection harness
// Sidecar-only test harness. Do not import from runtime paths until later lifecycle milestones.

import { appendFile, readdir } from 'node:fs/promises';
import { join } from 'node:path';

import { assertValidMilestoneTransition, assertValidRunTransition, isWorkTerminalState, transitionMilestone, transitionRun } from './work-fsm.ts';
import { appendLifecycleEvent, atomicWriteJson, createWorkLedgerPaths, readLifecycleEvents, readRunSummary, writeRunSummary } from './work-ledger-store.ts';
import { makeDedupeKey, makeNotificationId, markDeliveryAttempt, readQueuedNotification } from './work-notification-outbox.ts';
import { queueTerminalNotification } from './work-notifier.ts';

export class WorkFailureInjectionHarnessError extends Error {
  constructor(code, message, details = {}) {
    super(message);
    this.name = 'WorkFailureInjectionHarnessError';
    this.code = code;
    this.details = details;
  }
}

function isoNow(options = {}) {
  return options.timestamp ?? options.now?.toISOString?.() ?? new Date().toISOString();
}

function activeMilestone(runRecord) {
  const milestones = Array.isArray(runRecord?.milestones) ? runRecord.milestones : [];
  return milestones.find((milestone) => !isWorkTerminalState(milestone.status)) ?? milestones.at(-1) ?? null;
}

function withMilestone(runRecord, milestone) {
  const milestones = Array.isArray(runRecord?.milestones) ? runRecord.milestones : [];
  return {
    ...runRecord,
    milestones: milestones.map((item) => (item.milestone_id === milestone?.milestone_id ? milestone : item))
  };
}

function markMilestoneNotificationQueued(milestone, notification) {
  if (!milestone) return null;
  return {
    ...milestone,
    notification: {
      required: true,
      delivered: false,
      ...(milestone.notification ?? {}),
      queued: true,
      notification_id: notification?.notification_id ?? milestone.notification?.notification_id ?? null
    }
  };
}

async function appendTransitionEvents(rootDir, { runId, milestoneId, fromRunState, toRunState, fromMilestoneState, toMilestoneState, timestamp, actor = 'failure-injection-harness', summary }) {
  if (fromRunState && toRunState) {
    await appendLifecycleEvent(rootDir, {
      schema_version: 'work_lifecycle.v1',
      event_id: `evt_${runId}_${toRunState.toLowerCase()}_${Date.parse(timestamp)}`,
      run_id: runId,
      type: 'RUN_TRANSITION',
      timestamp,
      from_state: fromRunState,
      to_state: toRunState,
      actor,
      summary
    });
  }
  if (milestoneId && fromMilestoneState && toMilestoneState) {
    await appendLifecycleEvent(rootDir, {
      schema_version: 'work_lifecycle.v1',
      event_id: `evt_${runId}_${milestoneId}_${toMilestoneState.toLowerCase()}_${Date.parse(timestamp)}`,
      run_id: runId,
      milestone_id: milestoneId,
      type: 'MILESTONE_TRANSITION',
      timestamp,
      from_state: fromMilestoneState,
      to_state: toMilestoneState,
      actor,
      summary
    });
  }
}

export async function queueTerminalNotificationOnce(rootDir, { run, milestone = null, status = null, gates = [], artifacts = [], next = null, failure = null, hold = null, abort = null, now = new Date() }) {
  const finalStatus = status ?? milestone?.status ?? run?.status;
  const notificationId = makeNotificationId({
    runId: run?.run_id,
    milestoneId: milestone?.milestone_id,
    status: finalStatus,
    kind: 'TERMINAL'
  });

  try {
    const existing = await readQueuedNotification(rootDir, run.run_id, notificationId);
    return {
      duplicate: true,
      outboxPath: join(createWorkLedgerPaths(rootDir, run.run_id).outboxDir, `${notificationId}.json`),
      notification: existing
    };
  } catch (error) {
    if (error?.details?.causeCode !== 'ENOENT') throw error;
  }

  const queued = await queueTerminalNotification(rootDir, { run, milestone, status: finalStatus, gates, artifacts, next, failure, hold, abort, now });
  return { duplicate: false, ...queued };
}

export async function injectRuntimeExceptionFailure(rootDir, runRecord, error, options = {}) {
  const timestamp = isoNow(options);
  const milestone = activeMilestone(runRecord);
  const failedMilestone = milestone
    ? transitionMilestone(milestone, 'FAIL', { timestamp })
    : null;
  const failedRunBase = transitionRun(runRecord, 'FAIL', { timestamp });
  const failedRun = {
    ...withMilestone(failedRunBase, failedMilestone),
    failure: {
      code: options.code ?? 'INJECTED_RUNTIME_EXCEPTION',
      reason: error?.message ?? String(error ?? 'Injected runtime exception'),
      evidence: options.evidence ?? []
    }
  };
  await writeRunSummary(rootDir, failedRun);
  const notification = await queueTerminalNotificationOnce(rootDir, {
    run: failedRun,
    milestone: failedMilestone,
    status: 'FAIL',
    failure: { action_taken: 'Marked current milestone FAIL from injected tool/runtime exception.' },
    now: new Date(timestamp)
  });
  const notificationMilestone = markMilestoneNotificationQueued(failedMilestone, notification.notification);
  const finalRun = withMilestone(failedRun, notificationMilestone);
  await writeRunSummary(rootDir, finalRun);
  await appendTransitionEvents(rootDir, {
    runId: finalRun.run_id,
    milestoneId: milestone?.milestone_id ?? null,
    fromRunState: runRecord.status,
    toRunState: 'FAIL',
    fromMilestoneState: milestone?.status,
    toMilestoneState: failedMilestone?.status,
    timestamp,
    summary: 'Injected runtime exception marked work FAIL and queued terminal notification.'
  });
  return { run: finalRun, notification };
}

export async function recordNotificationTransportFailure(rootDir, { runId, notificationId, error, timestamp = new Date().toISOString() }) {
  const paths = createWorkLedgerPaths(rootDir, runId);
  const notification = await readQueuedNotification(rootDir, runId, notificationId);
  const failed = markDeliveryAttempt(notification, {
    status: 'FAILED',
    timestamp,
    transport: 'synthetic_transport',
    error: error?.message ?? String(error ?? 'Injected notification transport failure')
  });
  await atomicWriteJson(join(paths.outboxDir, `${notificationId}.json`), failed);
  await appendLifecycleEvent(rootDir, {
    schema_version: 'work_lifecycle.v1',
    event_id: `evt_${notificationId}_delivery_failed_${Date.parse(timestamp)}`,
    run_id: runId,
    milestone_id: notification.milestone_id ?? null,
    type: 'NOTIFICATION_FAILED',
    timestamp,
    notification_id: notificationId,
    actor: 'failure-injection-harness',
    summary: 'Injected notification transport failure persisted to outbox.'
  });
  return failed;
}

export async function rejectInvalidTransitionAttempt(rootDir, runRecord, { kind = 'run', fromState, toState, timestamp = new Date().toISOString() }) {
  try {
    if (kind === 'milestone') assertValidMilestoneTransition(fromState, toState);
    else assertValidRunTransition(fromState, toState);
  } catch (error) {
    await appendLifecycleEvent(rootDir, {
      schema_version: 'work_lifecycle.v1',
      event_id: `evt_${runRecord.run_id}_invalid_transition_${Date.parse(timestamp)}`,
      run_id: runRecord.run_id,
      type: 'RUN_SUMMARY_RECOMPUTED',
      timestamp,
      actor: 'failure-injection-harness',
      summary: `Rejected invalid ${kind} transition ${fromState} -> ${toState}.`,
      data: {
        rejected: true,
        kind,
        from_state: fromState,
        to_state: toState,
        code: error?.code ?? 'INVALID_TRANSITION'
      }
    });
    return { rejected: true, code: error?.code ?? 'INVALID_TRANSITION', message: error?.message };
  }
  throw new WorkFailureInjectionHarnessError('TRANSITION_WAS_VALID', `Expected invalid ${kind} transition ${fromState} -> ${toState}`);
}

export async function appendCorruptEventLine(rootDir, runId, line = '{"schema_version":"work_lifecycle.v1",') {
  const paths = createWorkLedgerPaths(rootDir, runId);
  await appendFile(paths.eventPath, `${line}\n`, 'utf8');
  return paths.eventPath;
}

export async function replayIgnoringCorruptEvents(rootDir, runId) {
  const events = await readLifecycleEvents(rootDir, runId, { quarantineCorrupt: true });
  const paths = createWorkLedgerPaths(rootDir, runId);
  const eventEntries = await readdir(join(rootDir, 'events')).catch(() => []);
  const quarantineFiles = eventEntries.filter((entry) => entry.startsWith(`${runId}.jsonl.corrupt-`));
  const run = await readRunSummary(rootDir, runId);
  return { events, run, quarantineFiles, eventPath: paths.eventPath };
}

export async function abortRunWithCloseout(rootDir, runRecord, { reason = 'Operator requested abort', timestamp = new Date().toISOString() } = {}) {
  const milestone = activeMilestone(runRecord);
  const abortedMilestone = milestone ? transitionMilestone(milestone, 'ABORT', { timestamp }) : null;
  const abortedRunBase = transitionRun(runRecord, 'ABORT', { timestamp });
  const abortedRun = {
    ...withMilestone(abortedRunBase, abortedMilestone),
    abort: {
      code: 'USER_ABORT',
      reason,
      requested_by: 'operator'
    }
  };
  await writeRunSummary(rootDir, abortedRun);
  const notification = await queueTerminalNotificationOnce(rootDir, {
    run: abortedRun,
    milestone: abortedMilestone,
    status: 'ABORT',
    abort: abortedRun.abort,
    now: new Date(timestamp)
  });
  const finalRun = withMilestone(abortedRun, markMilestoneNotificationQueued(abortedMilestone, notification.notification));
  await writeRunSummary(rootDir, finalRun);
  await appendTransitionEvents(rootDir, {
    runId: finalRun.run_id,
    milestoneId: milestone?.milestone_id ?? null,
    fromRunState: runRecord.status,
    toRunState: 'ABORT',
    fromMilestoneState: milestone?.status,
    toMilestoneState: abortedMilestone?.status,
    timestamp,
    actor: 'operator',
    summary: 'User abort marked run ABORT and queued closeout notification.'
  });
  return { run: finalRun, notification };
}

export async function supersedeRunWithReplacement(rootDir, runRecord, replacementRunId, { timestamp = new Date().toISOString() } = {}) {
  if (!replacementRunId || replacementRunId === runRecord?.run_id) {
    throw new WorkFailureInjectionHarnessError('REPLACEMENT_RUN_REQUIRED', 'A distinct replacement run id is required');
  }
  const milestone = activeMilestone(runRecord);
  const supersededMilestone = milestone ? transitionMilestone(milestone, 'SUPERSEDED', { timestamp, supersededBy: replacementRunId }) : null;
  const supersededRunBase = transitionRun(runRecord, 'SUPERSEDED', { timestamp, supersededBy: replacementRunId });
  const supersededRun = withMilestone(supersededRunBase, supersededMilestone);
  await writeRunSummary(rootDir, supersededRun);
  const notification = await queueTerminalNotificationOnce(rootDir, {
    run: supersededRun,
    milestone: supersededMilestone,
    status: 'SUPERSEDED',
    next: `Continue in replacement run ${replacementRunId}`,
    now: new Date(timestamp)
  });
  const finalRun = withMilestone(supersededRun, markMilestoneNotificationQueued(supersededMilestone, notification.notification));
  await writeRunSummary(rootDir, finalRun);
  await appendTransitionEvents(rootDir, {
    runId: finalRun.run_id,
    milestoneId: milestone?.milestone_id ?? null,
    fromRunState: runRecord.status,
    toRunState: 'SUPERSEDED',
    fromMilestoneState: milestone?.status,
    toMilestoneState: supersededMilestone?.status,
    timestamp,
    summary: `Superseded run linked to replacement ${replacementRunId}; stale continuation must stop.`
  });
  return { run: finalRun, notification };
}

export function assertNoStaleContinuation(runRecord, expectedReplacementRunId = null) {
  if (runRecord?.status !== 'SUPERSEDED') return true;
  if (expectedReplacementRunId && runRecord.superseded_by !== expectedReplacementRunId) {
    throw new WorkFailureInjectionHarnessError('SUPERSEDED_REPLACEMENT_MISMATCH', 'Superseded run replacement id mismatch', {
      expectedReplacementRunId,
      actualReplacementRunId: runRecord.superseded_by
    });
  }
  throw new WorkFailureInjectionHarnessError('STALE_CONTINUATION_BLOCKED', 'Superseded run cannot continue; use replacement run', {
    replacementRunId: runRecord.superseded_by ?? null
  });
}

export function notificationDedupeKeyFor(run, milestone, status) {
  return makeDedupeKey({
    runId: run?.run_id,
    milestoneId: milestone?.milestone_id,
    status,
    surface: run?.surface,
    kind: 'TERMINAL'
  });
}
