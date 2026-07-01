// OpenClaw Stickbot Work Lifecycle Ledger — M4 terminal notifier sidecar
// Sidecar-only module. Do not import from runtime paths until later lifecycle milestones.

import { appendLifecycleEvent } from './work-ledger-store.ts';
import { makeDedupeKey, makeNotificationId, queueNotification } from './work-notification-outbox.ts';
import { renderTerminalNotification } from './work-notification-template.ts';

export class WorkNotifierError extends Error {
  constructor(code, message, details = {}) {
    super(message);
    this.name = 'WorkNotifierError';
    this.code = code;
    this.details = details;
  }
}

export function terminalStatusRequiresNotification(status) {
  return ['PASS', 'FAIL', 'HOLD', 'ABORT', 'SUPERSEDED'].includes(status);
}

export async function queueTerminalNotification(rootDir, { run, milestone = null, status = null, gates = [], artifacts = [], next = null, failure = null, hold = null, abort = null, now = new Date() }) {
  const finalStatus = status ?? milestone?.status ?? run?.status;
  if (!terminalStatusRequiresNotification(finalStatus)) {
    throw new WorkNotifierError('NON_TERMINAL_STATUS', `Terminal notification requires terminal status, got ${finalStatus}`, {
      status: finalStatus
    });
  }
  if (!run?.run_id) {
    throw new WorkNotifierError('RUN_REQUIRED', 'run.run_id is required');
  }

  const notificationId = makeNotificationId({
    runId: run.run_id,
    milestoneId: milestone?.milestone_id,
    status: finalStatus,
    kind: 'TERMINAL'
  });
  const dedupeKey = makeDedupeKey({
    runId: run.run_id,
    milestoneId: milestone?.milestone_id,
    status: finalStatus,
    surface: run.surface,
    kind: 'TERMINAL'
  });
  const body = renderTerminalNotification({ run, milestone, status: finalStatus, gates, artifacts, next, failure, hold, abort });

  const queued = await queueNotification(rootDir, {
    notification_id: notificationId,
    run_id: run.run_id,
    milestone_id: milestone?.milestone_id ?? null,
    kind: 'TERMINAL',
    terminal_status: finalStatus,
    surface: run.surface ?? 'unknown_surface',
    dedupe_key: dedupeKey,
    created_at: now.toISOString(),
    body
  });

  await appendLifecycleEvent(rootDir, {
    schema_version: 'work_lifecycle.v1',
    event_id: `evt_${notificationId}_queued`,
    run_id: run.run_id,
    milestone_id: milestone?.milestone_id ?? null,
    type: 'NOTIFICATION_QUEUED',
    timestamp: now.toISOString(),
    notification_id: notificationId,
    actor: 'runtime',
    summary: `${finalStatus} terminal notification queued.`
  });

  return queued;
}

export async function requireTerminalNotification(rootDir, args) {
  const queued = await queueTerminalNotification(rootDir, args);
  if (!queued?.notification?.notification_id) {
    throw new WorkNotifierError('TERMINAL_NOTIFICATION_NOT_QUEUED', 'Terminal notification was not queued');
  }
  return queued;
}
