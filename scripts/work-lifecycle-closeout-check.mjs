#!/usr/bin/env node
// OpenClaw Stickbot Work Lifecycle Ledger — M6 closeout watcher check script
// Sidecar-only script. It reads/writes state/work-lifecycle only when explicitly invoked.

import { resolve } from 'node:path';

import { watchAllActiveRuns } from '../src/work-lifecycle/work-closeout-watcher.ts';

const rootDir = resolve(process.argv[2] ?? 'state/work-lifecycle');
const staleAfterArg = process.argv.find((arg) => arg.startsWith('--stale-after-ms='));
const timeoutStatusArg = process.argv.find((arg) => arg.startsWith('--timeout-status='));

const options = {
  staleAfterMs: staleAfterArg ? Number(staleAfterArg.split('=')[1]) : undefined,
  timeoutStatus: timeoutStatusArg ? timeoutStatusArg.split('=')[1] : undefined
};

const results = await watchAllActiveRuns(rootDir, options);
const summary = {
  schema_version: 'work_lifecycle.closeout_check.v1',
  rootDir,
  checked_at: new Date().toISOString(),
  changed_count: results.length,
  changed_runs: results.map((result) => ({
    run_id: result.run.run_id,
    action: result.action,
    reason: result.staleness.reason,
    notification_id: result.notification?.notification?.notification_id ?? null
  }))
};

console.log(JSON.stringify(summary, null, 2));
