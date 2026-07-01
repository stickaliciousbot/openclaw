import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import test from 'node:test';

import { evaluateStaleness, watchRunCloseout } from './work-closeout-watcher.ts';
import { replayLifecycleRun } from './work-ledger-replay.ts';
import { readLifecycleEvents, readRunSummary, writeRunSummary } from './work-ledger-store.ts';
import { readQueuedNotification } from './work-notification-outbox.ts';
import {
  abortRunWithCloseout,
  appendCorruptEventLine,
  assertNoStaleContinuation,
  injectRuntimeExceptionFailure,
  notificationDedupeKeyFor,
  queueTerminalNotificationOnce,
  recordNotificationTransportFailure,
  rejectInvalidTransitionAttempt,
  replayIgnoringCorruptEvents,
  supersedeRunWithReplacement
} from './work-failure-injection-harness.ts';

async function tempRoot() {
  return mkdtemp(join(tmpdir(), 'work-failure-injection-test-'));
}

function runRecord({ runId = 'work_m8_failure_case_alpha', status = 'RUNNING', milestoneStatus = 'RUNNING', updatedAt = '2026-07-01T00:00:00Z' } = {}) {
  return {
    schema_version: 'work_lifecycle.v1',
    run_id: runId,
    parent_run_id: null,
    user_turn_id: 'telegram:turn:sha256-redacted',
    surface: 'telegram_direct_sha256_redacted',
    chat_id: 'telegram:direct:sha256-redacted',
    actor: 'stickbot',
    title: 'M8 synthetic failure injection run',
    requested_by: 'operator',
    status,
    started_at: updatedAt,
    updated_at: updatedAt,
    ended_at: null,
    safety_boundary: {
      mode: 'repo_patch',
      allowed_mutations: ['local_fixture', 'synthetic_ledger', 'synthetic_outbox'],
      forbidden_mutations: ['runtime_hook_import', 'cli_registration', 'gateway_config', 'service_restart', 'telegram_send'],
      requires_operator_approval: ['commit', 'push'],
      secrets_redaction_required: true
    },
    ack: { required: true, delivered: true },
    milestones: [{
      milestone_id: 'M8',
      name: 'Failure Injection Harness',
      status: milestoneStatus,
      required: true,
      started_at: updatedAt,
      ended_at: null,
      hard_gates: [],
      artifacts: [],
      notification: { required: true, delivered: false, queued: false }
    }],
    failure: null,
    hold: null,
    abort: null,
    superseded_by: null
  };
}

function activeMilestone(run) {
  return run.milestones[0];
}

test('M8_G1/M8_G2 injected tool/runtime exception marks current milestone FAIL and queues terminal outbox', async () => {
  const root = await tempRoot();
  try {
    const run = runRecord();
    const result = await injectRuntimeExceptionFailure(root, run, new Error('synthetic tool failure'), {
      timestamp: '2026-07-01T00:01:00Z'
    });

    assert.equal(result.run.status, 'FAIL');
    assert.equal(activeMilestone(result.run).status, 'FAIL');
    assert.equal(activeMilestone(result.run).notification.queued, true);
    assert.equal(result.notification.notification.terminal_status, 'FAIL');
    assert.match(result.notification.notification.body, /FAIL/);

    const persisted = await readRunSummary(root, run.run_id);
    assert.equal(persisted.status, 'FAIL');
    const replay = await replayLifecycleRun(root, run.run_id);
    assert.equal(replay.status, 'FAIL');
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('M8_G1/M8_G2 stale RUNNING milestone is detected and transitions to HOLD with closeout notification', async () => {
  const root = await tempRoot();
  try {
    const run = runRecord({ runId: 'work_m8_failure_case_stale', updatedAt: '2026-07-01T00:00:00Z' });
    await writeRunSummary(root, run);
    const stale = evaluateStaleness({ runRecord: run, now: new Date('2026-07-01T00:10:00Z'), staleAfterMs: 1000 });
    assert.equal(stale.stale, true);
    assert.equal(stale.reason, 'STALE_RUNNING');

    const result = await watchRunCloseout(root, run.run_id, {
      now: new Date('2026-07-01T00:10:00Z'),
      timestamp: '2026-07-01T00:10:00Z',
      staleAfterMs: 1000,
      timeoutStatus: 'HOLD'
    });
    assert.equal(result.run.status, 'HOLD');
    assert.equal(result.notification.notification.terminal_status, 'HOLD');
    const persisted = await readRunSummary(root, run.run_id);
    assert.equal(persisted.status, 'HOLD');
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('M8_G3 notification transport failure persists outbox and records delivery failure', async () => {
  const root = await tempRoot();
  try {
    const run = runRecord({ runId: 'work_m8_failure_case_transport' });
    const fail = await injectRuntimeExceptionFailure(root, run, new Error('synthetic exception'), {
      timestamp: '2026-07-01T00:02:00Z'
    });
    const failed = await recordNotificationTransportFailure(root, {
      runId: fail.run.run_id,
      notificationId: fail.notification.notification.notification_id,
      error: new Error('synthetic transport unavailable'),
      timestamp: '2026-07-01T00:03:00Z'
    });

    assert.equal(failed.status, 'FAILED');
    assert.equal(failed.attempts.at(-1).status, 'FAILED');
    assert.match(failed.attempts.at(-1).error, /synthetic transport unavailable/);

    const readBack = await readQueuedNotification(root, fail.run.run_id, fail.notification.notification.notification_id);
    assert.equal(readBack.status, 'FAILED');
    const events = await readLifecycleEvents(root, fail.run.run_id);
    assert.equal(events.some((event) => event.type === 'NOTIFICATION_FAILED'), true);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('M8_G5 duplicate retry does not create duplicate terminal notification', async () => {
  const root = await tempRoot();
  try {
    const run = runRecord({ runId: 'work_m8_failure_case_dedupe', status: 'FAIL', milestoneStatus: 'FAIL' });
    const milestone = activeMilestone(run);
    const first = await queueTerminalNotificationOnce(root, {
      run,
      milestone,
      status: 'FAIL',
      now: new Date('2026-07-01T00:04:00Z')
    });
    const second = await queueTerminalNotificationOnce(root, {
      run,
      milestone,
      status: 'FAIL',
      now: new Date('2026-07-01T00:05:00Z')
    });

    assert.equal(first.duplicate, false);
    assert.equal(second.duplicate, true);
    assert.equal(second.notification.notification_id, first.notification.notification_id);
    assert.equal(second.notification.dedupe_key, notificationDedupeKeyFor(run, milestone, 'FAIL'));

    const events = await readLifecycleEvents(root, run.run_id);
    assert.equal(events.filter((event) => event.type === 'NOTIFICATION_QUEUED').length, 1);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('M8_G1/M8_G4 invalid transition attempt is rejected, recorded, and replay does not poison final state', async () => {
  const root = await tempRoot();
  try {
    const run = runRecord({ runId: 'work_m8_failure_case_invalid', status: 'PASS', milestoneStatus: 'PASS' });
    await writeRunSummary(root, run);
    const rejected = await rejectInvalidTransitionAttempt(root, run, {
      kind: 'run',
      fromState: 'PASS',
      toState: 'RUNNING',
      timestamp: '2026-07-01T00:06:00Z'
    });
    assert.equal(rejected.rejected, true);
    assert.equal(rejected.code, 'TERMINAL_STATE_IMMUTABLE');

    const events = await readLifecycleEvents(root, run.run_id);
    assert.equal(events.at(-1).type, 'RUN_SUMMARY_RECOMPUTED');
    assert.equal(events.at(-1).data.rejected, true);
    const persisted = await readRunSummary(root, run.run_id);
    assert.equal(persisted.status, 'PASS');
    const replay = await replayLifecycleRun(root, run.run_id);
    assert.equal(replay.status, null);
    assert.equal(replay.event_count, 1);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('M8_G3/M8_G4 partial corrupt write is quarantined or ignored without poisoning current state', async () => {
  const root = await tempRoot();
  try {
    const run = runRecord({ runId: 'work_m8_failure_case_corrupt' });
    const fail = await injectRuntimeExceptionFailure(root, run, new Error('synthetic exception'), {
      timestamp: '2026-07-01T00:07:00Z'
    });
    await appendCorruptEventLine(root, run.run_id);

    const recovered = await replayIgnoringCorruptEvents(root, run.run_id);
    assert.equal(recovered.run.status, 'FAIL');
    assert.equal(recovered.events.some((event) => event.type === 'RUN_TRANSITION' && event.to_state === 'FAIL'), true);
    assert.equal(recovered.quarantineFiles.length, 1);

    const persisted = await readRunSummary(root, run.run_id);
    assert.equal(persisted.status, fail.run.status);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('M8_G1/M8_G2 user abort marks run ABORT with closeout', async () => {
  const root = await tempRoot();
  try {
    const run = runRecord({ runId: 'work_m8_failure_case_abort' });
    const result = await abortRunWithCloseout(root, run, {
      reason: 'Operator requested synthetic abort',
      timestamp: '2026-07-01T00:08:00Z'
    });
    assert.equal(result.run.status, 'ABORT');
    assert.equal(activeMilestone(result.run).status, 'ABORT');
    assert.equal(result.run.abort.requested_by, 'operator');
    assert.equal(result.notification.notification.terminal_status, 'ABORT');

    const replay = await replayLifecycleRun(root, run.run_id);
    assert.equal(replay.status, 'ABORT');
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('M8_G1/M8_G2 superseded run links replacement and prevents stale continuation', async () => {
  const root = await tempRoot();
  try {
    const run = runRecord({ runId: 'work_m8_failure_case_superseded' });
    const result = await supersedeRunWithReplacement(root, run, 'work_m8_replacement_run', {
      timestamp: '2026-07-01T00:09:00Z'
    });
    assert.equal(result.run.status, 'SUPERSEDED');
    assert.equal(result.run.superseded_by, 'work_m8_replacement_run');
    assert.equal(activeMilestone(result.run).superseded_by, 'work_m8_replacement_run');
    assert.equal(result.notification.notification.terminal_status, 'SUPERSEDED');
    assert.throws(() => assertNoStaleContinuation(result.run, 'work_m8_replacement_run'), /Superseded run cannot continue/);

    const replay = await replayLifecycleRun(root, run.run_id);
    assert.equal(replay.status, 'SUPERSEDED');
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('M8_G6/M8_G7 focused artifacts stay redacted and sidecar-only', async () => {
  const artifactPaths = [
    'src/work-lifecycle/work-failure-injection-harness.ts',
    'src/work-lifecycle/work-failure-injection-harness.test.mjs',
    'state/work-lifecycle/runs/work_20260701T094400Z_lifecycle_ledger_m8.json',
    'state/work-lifecycle/events/work_20260701T094400Z_lifecycle_ledger_m8.jsonl',
    // M8_G9: evidence redaction scan covers status, gate results, and manifest.
    'sharedspace/runtime-kernel-validation/work-lifecycle/m8-failure-injection/status.json',
    'sharedspace/runtime-kernel-validation/work-lifecycle/m8-failure-injection/summary.json',
    'sharedspace/runtime-kernel-validation/work-lifecycle/m8-failure-injection/gate-results.json',
    'sharedspace/runtime-kernel-validation/work-lifecycle/m8-failure-injection/evidence_manifest.json'
  ];
  const ownerIdPattern = new RegExp(['849', '520', '3551'].join(''));
  const rawPrivatePatterns = [
    ownerIdPattern,
    /telegram:[^\s`"]*:[0-9]{6,}/,
    /(authorization|token|api[_-]?key|secret)\s*[:=]\s*[^\s,;}"`]+/i
  ];
  for (const artifactPath of artifactPaths) {
    const text = await readFile(artifactPath, 'utf8');
    for (const pattern of rawPrivatePatterns) {
      assert.doesNotMatch(text, pattern, `${artifactPath} failed redaction pattern ${pattern}`);
    }
  }

  const harnessSource = await readFile('src/work-lifecycle/work-failure-injection-harness.ts', 'utf8');
  assert.doesNotMatch(harnessSource, /gateway|telegram\.send|sessions_send|message\(/i);
  assert.doesNotMatch(harnessSource, /openclaw\.json|config\.patch|config\.apply|restart/i);
  assert.doesNotMatch(harnessSource, /\.\.\/cron|\.\.\/gateway|runtime\/|plugins\//i);

  const summary = JSON.parse(await readFile('sharedspace/runtime-kernel-validation/work-lifecycle/m8-failure-injection/summary.json', 'utf8'));
  assert.equal(summary.boundaryReadback.runtimeBehaviorChanged, false);
  assert.equal(summary.boundaryReadback.gatewayConfigChanged, false);
  assert.equal(summary.boundaryReadback.gatewayRestarted, false);
  assert.equal(summary.boundaryReadback.routesChanged, false);
  assert.equal(summary.boundaryReadback.providerAuthChanged, false);
  assert.equal(summary.boundaryReadback.memoryMutated, false);
  assert.equal(summary.boundaryReadback.runtimeHookImported, false);
  assert.equal(summary.boundaryReadback.cliRegistered, false);
  assert.equal(summary.boundaryReadback.telegramSentFromCode, false);
  assert.equal(summary.boundaryReadback.productionStateMutated, false);
  // M8_G10: PASS_PUSHED git preservation is distinct from runtime/production mutation.
  assert.equal(summary.boundaryReadback.committed, true);
  assert.equal(summary.boundaryReadback.pushed, true);
});
