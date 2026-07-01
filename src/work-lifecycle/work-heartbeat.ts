// OpenClaw Stickbot Work Lifecycle Ledger — M6 heartbeat sidecar
// Sidecar-only module. Do not import from runtime paths until later lifecycle milestones.

import { mkdir } from 'node:fs/promises';
import { join } from 'node:path';

import { appendLifecycleEvent, atomicWriteJson, createWorkLedgerPaths, readJsonFile } from './work-ledger-store.ts';

export class WorkHeartbeatError extends Error {
  constructor(code, message, details = {}) {
    super(message);
    this.name = 'WorkHeartbeatError';
    this.code = code;
    this.details = details;
  }
}

export function heartbeatPath(rootDir, runId) {
  return join(rootDir, 'heartbeats', `${runId}.json`);
}

export async function writeWorkHeartbeat(rootDir, runRecord, options = {}) {
  if (!runRecord?.run_id) {
    throw new WorkHeartbeatError('RUN_ID_REQUIRED', 'runRecord.run_id is required');
  }
  const timestamp = options.timestamp ?? new Date().toISOString();
  await mkdir(join(rootDir, 'heartbeats'), { recursive: true });

  const heartbeat = {
    schema_version: 'work_lifecycle.heartbeat.v1',
    run_id: runRecord.run_id,
    status: runRecord.status,
    milestone_id: options.milestoneId ?? currentMilestoneId(runRecord),
    heartbeat_at: timestamp,
    stale_after_ms: options.staleAfterMs ?? 15 * 60 * 1000,
    expected_closeout_path: createWorkLedgerPaths(rootDir, runRecord.run_id).runPath,
    notification_outbox_root: join(rootDir, 'outbox'),
    watcher_id: options.watcherId ?? 'work-closeout-watcher'
  };

  await atomicWriteJson(heartbeatPath(rootDir, runRecord.run_id), heartbeat);
  await appendLifecycleEvent(rootDir, {
    schema_version: 'work_lifecycle.v1',
    event_id: options.eventId ?? `evt_${runRecord.run_id}_heartbeat_${timestamp.replace(/[^0-9A-Za-z]/g, '')}`,
    run_id: runRecord.run_id,
    milestone_id: heartbeat.milestone_id,
    type: 'HEARTBEAT',
    timestamp,
    actor: heartbeat.watcher_id,
    summary: `Heartbeat written for ${runRecord.status} run.`
  });

  return heartbeat;
}

export async function readWorkHeartbeat(rootDir, runId) {
  return readJsonFile(heartbeatPath(rootDir, runId));
}

export function currentMilestoneId(runRecord) {
  const milestones = Array.isArray(runRecord?.milestones) ? runRecord.milestones : [];
  const active = milestones.find((milestone) => milestone.status === 'RUNNING' || milestone.status === 'HOLD' || milestone.status === 'PENDING');
  return active?.milestone_id ?? milestones.at(-1)?.milestone_id ?? null;
}
