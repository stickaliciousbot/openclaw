// OpenClaw Stickbot Work Lifecycle Ledger — M6 closeout watcher sidecar
// Sidecar-only module. Do not import from runtime paths until later lifecycle milestones.

import { readdir } from 'node:fs/promises';
import { join } from 'node:path';

import { appendLifecycleEvent, readRunSummary, writeRunSummary } from './work-ledger-store.ts';
import { terminalStatusRequiresNotification, queueTerminalNotification } from './work-notifier.ts';
import { readWorkHeartbeat } from './work-heartbeat.ts';

export class WorkCloseoutWatcherError extends Error {
  constructor(code, message, details = {}) {
    super(message);
    this.name = 'WorkCloseoutWatcherError';
    this.code = code;
    this.details = details;
  }
}

export function isActiveRunStatus(status) {
  return status === 'ACK_PENDING' || status === 'RUNNING';
}

export function terminalNoticeMissing(runRecord) {
  const milestones = Array.isArray(runRecord?.milestones) ? runRecord.milestones : [];
  return milestones.some((milestone) => {
    if (!terminalStatusRequiresNotification(milestone.status)) return false;
    const notification = milestone.notification ?? {};
    return notification.required !== false && notification.delivered !== true && notification.queued !== true;
  });
}

export function evaluateStaleness({ runRecord, heartbeat = null, now = new Date(), staleAfterMs = 15 * 60 * 1000 }) {
  if (!runRecord?.run_id) {
    throw new WorkCloseoutWatcherError('RUN_RECORD_REQUIRED', 'runRecord.run_id is required');
  }
  const nowMs = new Date(now).getTime();
  const heartbeatAt = heartbeat?.heartbeat_at ? new Date(heartbeat.heartbeat_at).getTime() : NaN;
  const updatedAt = runRecord.updated_at ? new Date(runRecord.updated_at).getTime() : NaN;
  const basisMs = Number.isFinite(heartbeatAt) ? heartbeatAt : updatedAt;
  const effectiveStaleAfterMs = heartbeat?.stale_after_ms ?? staleAfterMs;
  const ageMs = Number.isFinite(basisMs) ? nowMs - basisMs : Number.POSITIVE_INFINITY;

  if (isActiveRunStatus(runRecord.status) && ageMs > effectiveStaleAfterMs) {
    return {
      stale: true,
      reason: runRecord.status === 'ACK_PENDING' ? 'STALE_ACK_PENDING' : 'STALE_RUNNING',
      age_ms: ageMs,
      stale_after_ms: effectiveStaleAfterMs
    };
  }

  if (terminalNoticeMissing(runRecord)) {
    return {
      stale: true,
      reason: 'TERMINAL_NOTICE_MISSING',
      age_ms: ageMs,
      stale_after_ms: effectiveStaleAfterMs
    };
  }

  return {
    stale: false,
    reason: 'FRESH_OR_TERMINAL_CLOSED',
    age_ms: ageMs,
    stale_after_ms: effectiveStaleAfterMs
  };
}

export function markStaleRun(runRecord, staleness, options = {}) {
  const timestamp = options.timestamp ?? new Date().toISOString();
  const status = options.timeoutStatus ?? (staleness.reason === 'STALE_ACK_PENDING' ? 'ABORT' : 'HOLD');
  if (!['HOLD', 'ABORT'].includes(status)) {
    throw new WorkCloseoutWatcherError('INVALID_TIMEOUT_STATUS', 'timeoutStatus must be HOLD or ABORT', { status });
  }

  const base = {
    ...runRecord,
    status,
    updated_at: timestamp,
    ended_at: status === 'ABORT' ? timestamp : runRecord.ended_at ?? null
  };

  if (status === 'ABORT') {
    return {
      ...base,
      abort: {
        code: staleness.reason,
        reason: `Watcher aborted stale run: ${staleness.reason}`,
        requested_by: 'watcher'
      }
    };
  }

  return {
    ...base,
    hold: {
      code: staleness.reason,
      reason: `Watcher held stale run: ${staleness.reason}`,
      needed_from_operator: options.neededFromOperator ?? 'Inspect stale work, close out, or resume explicitly.',
      blocker_artifacts: options.blockerArtifacts ?? []
    }
  };
}

export async function watchRunCloseout(rootDir, runId, options = {}) {
  const runRecord = await readRunSummary(rootDir, runId);
  let heartbeat = null;
  try {
    heartbeat = await readWorkHeartbeat(rootDir, runId);
  } catch (error) {
    if (error?.details?.causeCode !== 'ENOENT' && error?.code !== 'READ_JSON_FAILED') throw error;
  }

  const staleness = evaluateStaleness({
    runRecord,
    heartbeat,
    now: options.now ?? new Date(),
    staleAfterMs: options.staleAfterMs
  });

  if (!staleness.stale) {
    return { action: 'NOOP', run: runRecord, staleness, notification: null };
  }

  const heldOrAborted = markStaleRun(runRecord, staleness, {
    timestamp: options.timestamp ?? (options.now ? new Date(options.now).toISOString() : new Date().toISOString()),
    timeoutStatus: options.timeoutStatus,
    neededFromOperator: options.neededFromOperator,
    blockerArtifacts: options.blockerArtifacts
  });
  await writeRunSummary(rootDir, heldOrAborted);

  const activeMilestone = Array.isArray(heldOrAborted.milestones)
    ? heldOrAborted.milestones.find((milestone) => milestone.status === 'RUNNING' || milestone.status === 'PENDING' || milestone.status === 'HOLD') ?? heldOrAborted.milestones.at(-1)
    : null;

  const notification = await queueTerminalNotification(rootDir, {
    run: heldOrAborted,
    milestone: activeMilestone ? { ...activeMilestone, status: heldOrAborted.status } : null,
    status: heldOrAborted.status,
    hold: heldOrAborted.hold,
    abort: heldOrAborted.abort,
    next: heldOrAborted.hold?.needed_from_operator ?? heldOrAborted.abort?.reason,
    now: options.now ? new Date(options.now) : new Date()
  });

  await appendLifecycleEvent(rootDir, {
    schema_version: 'work_lifecycle.v1',
    event_id: options.eventId ?? `evt_${runId}_watcher_${heldOrAborted.status.toLowerCase()}`,
    run_id: runId,
    milestone_id: activeMilestone?.milestone_id ?? null,
    type: 'WATCHER_ALERT',
    timestamp: options.timestamp ?? (options.now ? new Date(options.now).toISOString() : new Date().toISOString()),
    notification_id: notification.notification.notification_id,
    actor: 'work-closeout-watcher',
    summary: `Watcher marked stale run ${heldOrAborted.status}: ${staleness.reason}`
  });

  return { action: heldOrAborted.status, run: heldOrAborted, staleness, notification };
}

export async function listRunIds(rootDir) {
  const dir = join(rootDir, 'runs');
  try {
    const entries = await readdir(dir);
    return entries.filter((entry) => entry.endsWith('.json')).map((entry) => entry.slice(0, -'.json'.length));
  } catch (error) {
    if (error?.code === 'ENOENT') return [];
    throw error;
  }
}

export async function watchAllActiveRuns(rootDir, options = {}) {
  const runIds = await listRunIds(rootDir);
  const results = [];
  for (const runId of runIds) {
    const result = await watchRunCloseout(rootDir, runId, options);
    if (result.action !== 'NOOP') results.push(result);
  }
  return results;
}
