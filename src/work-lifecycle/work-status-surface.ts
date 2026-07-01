// OpenClaw Stickbot Work Lifecycle Ledger — M7 operator status surface
// Sidecar-only module. Do not import from runtime paths until later lifecycle milestones.

import { readdir, readFile } from 'node:fs/promises';
import { join } from 'node:path';

import { isWorkTerminalState } from './work-fsm.ts';
import { replayLifecycleRun } from './work-ledger-replay.ts';

const RAW_PRIVATE_PATTERNS = Object.freeze([
  /\b\d{9,}\b/g,
  /telegram:[^\s`"]*:[0-9]{6,}/gi,
  /(authorization|token|api[_-]?key|secret)\s*[:=]\s*[^\s,;"}]+/gi
]);

export class WorkStatusSurfaceError extends Error {
  constructor(code, message, details = {}) {
    super(message);
    this.name = 'WorkStatusSurfaceError';
    this.code = code;
    this.details = details;
  }
}

export function redactStatusValue(value) {
  let text = typeof value === 'string' ? value : JSON.stringify(value);
  for (const pattern of RAW_PRIVATE_PATTERNS) {
    text = text.replace(pattern, (match) => {
      if (/^(authorization|token|api[_-]?key|secret)/i.test(match)) return 'redacted-secret';
      if (/telegram:/i.test(match)) return 'telegram:sha256-redacted';
      return 'sha256-redacted';
    });
  }
  return text;
}

export function assertStatusRedacted(value) {
  const text = typeof value === 'string' ? value : JSON.stringify(value);
  const failures = [];
  for (const pattern of RAW_PRIVATE_PATTERNS) {
    pattern.lastIndex = 0;
    if (pattern.test(text)) failures.push(pattern.toString());
  }
  if (failures.length > 0) {
    throw new WorkStatusSurfaceError('STATUS_REDACTION_FAILED', 'Status output contains raw private identifier or secret-like content', { failures });
  }
  return true;
}

export async function loadRunSummaries(rootDir) {
  const dir = join(rootDir, 'runs');
  let entries;
  try {
    entries = await readdir(dir);
  } catch (error) {
    if (error?.code === 'ENOENT') return [];
    throw error;
  }

  const summaries = [];
  for (const entry of entries.filter((item) => item.endsWith('.json')).sort()) {
    const path = join(dir, entry);
    try {
      const run = JSON.parse(await readFile(path, 'utf8'));
      summaries.push({ path, run });
    } catch (error) {
      summaries.push({ path, corrupt: true, error: error?.message });
    }
  }
  return summaries;
}

export function isActiveRun(run) {
  return run?.status === 'ACK_PENDING' || run?.status === 'RUNNING' || run?.status === 'HOLD';
}

export async function listActiveWorkRuns(rootDir) {
  const summaries = await loadRunSummaries(rootDir);
  return summaries
    .filter((entry) => entry.run && isActiveRun(entry.run))
    .map((entry) => sanitizeRunSummary(entry.run, entry.path));
}

export async function getWorkRunStatus(rootDir, runId) {
  if (!runId) throw new WorkStatusSurfaceError('RUN_ID_REQUIRED', 'runId is required');
  const summaries = await loadRunSummaries(rootDir);
  const match = summaries.find((entry) => entry.run?.run_id === runId || entry.path.endsWith(`${runId}.json`));
  if (!match?.run) {
    throw new WorkStatusSurfaceError('RUN_NOT_FOUND', `Run not found: ${runId}`, { runId });
  }
  return sanitizeRunSummary(match.run, match.path);
}

export async function listFailedNotificationDeliveries(rootDir) {
  const dir = join(rootDir, 'outbox');
  let entries;
  try {
    entries = await readdir(dir);
  } catch (error) {
    if (error?.code === 'ENOENT') return [];
    throw error;
  }

  const failed = [];
  for (const entry of entries.filter((item) => item.endsWith('.json')).sort()) {
    const path = join(dir, entry);
    try {
      const notification = JSON.parse(await readFile(path, 'utf8'));
      const attempts = Array.isArray(notification.attempts) ? notification.attempts : [];
      const failedAttempt = attempts.some((attempt) => attempt.status === 'FAILED') || notification.status === 'FAILED' || notification.closeout_not_delivered === true;
      if (failedAttempt) {
        failed.push(sanitizeNotificationSummary(notification, path));
      }
    } catch (error) {
      failed.push({ path, corrupt: true, error: redactStatusValue(error?.message ?? 'unknown error') });
    }
  }
  return failed;
}

export async function replayWorkRunStatus(rootDir, runId) {
  const replay = await replayLifecycleRun(rootDir, runId, { quarantineCorrupt: false });
  const redacted = JSON.parse(redactStatusValue(replay));
  assertStatusRedacted(redacted);
  return redacted;
}

export function renderWorkStatusText(payload) {
  const redacted = redactStatusValue(payload);
  assertStatusRedacted(redacted);
  return redacted;
}

function sanitizeRunSummary(run, path) {
  const milestones = Array.isArray(run.milestones) ? run.milestones : [];
  const activeMilestone = milestones.find((milestone) => !isWorkTerminalState(milestone.status)) ?? milestones.at(-1) ?? null;
  const summary = {
    path,
    run_id: run.run_id,
    parent_run_id: run.parent_run_id ?? null,
    title: run.title,
    status: run.status,
    active_milestone_id: activeMilestone?.milestone_id ?? null,
    active_milestone_status: activeMilestone?.status ?? null,
    started_at: run.started_at ?? null,
    updated_at: run.updated_at ?? null,
    ended_at: run.ended_at ?? null,
    hold: run.hold ? { code: run.hold.code, reason: run.hold.reason } : null,
    failure: run.failure ? { code: run.failure.code, reason: run.failure.reason } : null,
    abort: run.abort ? { code: run.abort.code, reason: run.abort.reason } : null
  };
  const redacted = JSON.parse(redactStatusValue(summary));
  assertStatusRedacted(redacted);
  return redacted;
}

function sanitizeNotificationSummary(notification, path) {
  const summary = {
    path,
    notification_id: notification.notification_id,
    run_id: notification.run_id,
    milestone_id: notification.milestone_id ?? null,
    kind: notification.kind,
    status: notification.status,
    terminal_status: notification.terminal_status ?? null,
    surface: notification.surface,
    attempts: Array.isArray(notification.attempts)
      ? notification.attempts.map((attempt) => ({ status: attempt.status, error: attempt.error ?? null, timestamp: attempt.timestamp ?? null }))
      : []
  };
  const redacted = JSON.parse(redactStatusValue(summary));
  assertStatusRedacted(redacted);
  return redacted;
}
