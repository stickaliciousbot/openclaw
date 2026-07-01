// OpenClaw Stickbot Work Lifecycle Ledger — M4 notification outbox
// Sidecar-only module. Do not import from runtime paths until later lifecycle milestones.

import { join } from 'node:path';

import { atomicWriteJson, createWorkLedgerPaths, ensureWorkLedgerDirs, readJsonFile } from './work-ledger-store.ts';

export class WorkNotificationOutboxError extends Error {
  constructor(code, message, details = {}) {
    super(message);
    this.name = 'WorkNotificationOutboxError';
    this.code = code;
    this.details = details;
  }
}

export function makeNotificationId({ runId, milestoneId, status, kind = 'TERMINAL' }) {
  if (!runId) throw new WorkNotificationOutboxError('RUN_ID_REQUIRED', 'runId is required for notification id');
  const parts = ['notif', runId, milestoneId ?? 'run', kind.toLowerCase(), String(status ?? 'unknown').toLowerCase()];
  return parts.join('_').replace(/[^a-zA-Z0-9_:-]/g, '_');
}

export function makeDedupeKey({ runId, milestoneId, status, surface, kind = 'TERMINAL' }) {
  return [runId, milestoneId ?? 'run', status ?? 'UNKNOWN', surface ?? 'unknown_surface', kind].join(':');
}

export async function queueNotification(rootDir, notification) {
  if (!notification?.run_id || !notification?.notification_id) {
    throw new WorkNotificationOutboxError('INVALID_NOTIFICATION', 'notification.run_id and notification.notification_id are required');
  }

  const paths = createWorkLedgerPaths(rootDir, notification.run_id);
  await ensureWorkLedgerDirs(rootDir);
  const outboxPath = join(paths.outboxDir, `${notification.notification_id}.json`);
  const persisted = {
    schema_version: 'work_lifecycle.notification.v1',
    status: 'QUEUED',
    created_at: new Date().toISOString(),
    attempts: [],
    ...notification
  };
  await atomicWriteJson(outboxPath, persisted);
  return { outboxPath, notification: persisted };
}

export async function readQueuedNotification(rootDir, runId, notificationId) {
  const paths = createWorkLedgerPaths(rootDir, runId);
  return readJsonFile(join(paths.outboxDir, `${notificationId}.json`));
}

export function markDeliveryAttempt(notification, attempt) {
  if (!notification || typeof notification !== 'object') {
    throw new WorkNotificationOutboxError('INVALID_NOTIFICATION', 'notification must be an object');
  }
  const attempts = Array.isArray(notification.attempts) ? notification.attempts : [];
  const status = attempt?.status ?? 'FAILED';
  return {
    ...notification,
    status,
    attempts: [...attempts, { timestamp: new Date().toISOString(), ...attempt, status }],
    delivered_at: status === 'DELIVERED' ? (attempt?.timestamp ?? new Date().toISOString()) : notification.delivered_at ?? null
  };
}
