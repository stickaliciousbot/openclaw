#!/usr/bin/env node
// OpenClaw Stickbot Work Lifecycle Ledger — M7 status surface script
// Sidecar-only script. It reads state/work-lifecycle when explicitly invoked.

import { resolve } from 'node:path';

import {
  getWorkRunStatus,
  listActiveWorkRuns,
  listFailedNotificationDeliveries,
  replayWorkRunStatus,
  renderWorkStatusText
} from '../src/work-lifecycle/work-status-surface.ts';

const args = process.argv.slice(2);
const command = args[0] ?? 'active';
const rootFlag = args.find((arg) => arg.startsWith('--root='));
const runFlag = args.find((arg) => arg.startsWith('--run='));
const rootDir = resolve(rootFlag ? rootFlag.split('=')[1] : 'state/work-lifecycle');
const runId = runFlag?.split('=')[1] ?? args[1];

let payload;
if (command === 'active') {
  payload = { schema_version: 'work_lifecycle.status.active.v1', rootDir, runs: await listActiveWorkRuns(rootDir) };
} else if (command === 'status') {
  payload = { schema_version: 'work_lifecycle.status.run.v1', rootDir, run: await getWorkRunStatus(rootDir, runId) };
} else if (command === 'failed-notifications') {
  payload = { schema_version: 'work_lifecycle.status.failed_notifications.v1', rootDir, notifications: await listFailedNotificationDeliveries(rootDir) };
} else if (command === 'replay') {
  payload = { schema_version: 'work_lifecycle.status.replay.v1', rootDir, replay: await replayWorkRunStatus(rootDir, runId) };
} else {
  throw new Error(`Unknown command ${command}; expected active|status|failed-notifications|replay`);
}

console.log(renderWorkStatusText(payload));
