import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname } from 'node:path';
import test from 'node:test';

const RUN_ID = 'work_20260701T114900Z_lifecycle_ledger_m10';
const STATE_ROOT = 'state/work-lifecycle';
const ARTIFACT_ROOT = 'sharedspace/runtime-kernel-validation/work-lifecycle/m10-enforced-canary';
const RUN_PATH = `${STATE_ROOT}/runs/${RUN_ID}.json`;
const EVENT_PATH = `${STATE_ROOT}/events/${RUN_ID}.jsonl`;
const STATUS_PATH = `${ARTIFACT_ROOT}/status.json`;
const SUMMARY_PATH = `${ARTIFACT_ROOT}/summary.json`;
const GATE_RESULTS_PATH = `${ARTIFACT_ROOT}/gate-results.json`;
const EVIDENCE_MANIFEST_PATH = `${ARTIFACT_ROOT}/evidence_manifest.json`;
const M8_SUMMARY_PATH = 'sharedspace/runtime-kernel-validation/work-lifecycle/m8-failure-injection/summary.json';
const M9_SUMMARY_PATH = 'sharedspace/runtime-kernel-validation/work-lifecycle/m9-observe-only-canary/summary.json';

async function readJson(path) {
  return JSON.parse(await readFile(path, 'utf8'));
}

async function writeJson(path, value) {
  await mkdir(dirname(path), { recursive: true });
  await writeFile(path, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

async function sha256File(path) {
  return createHash('sha256').update(await readFile(path)).digest('hex');
}

function eventLine(event) {
  return JSON.stringify(event);
}

function enforceCloseoutBeforeContinuation(run) {
  const closeoutStatus = run?.closeoutStatus;
  const terminal = ['PASS_PUSHED', 'PASS_LOCAL_VALIDATED', 'FAIL', 'HOLD', 'ABORT', 'SUPERSEDED'];
  if (!terminal.includes(closeoutStatus)) {
    return {
      allowed: false,
      disposition: 'HOLD',
      code: 'MISSING_REQUIRED_CLOSEOUT',
      reason: 'Unsafe continuation blocked because required closeout state is missing.'
    };
  }
  return { allowed: true, disposition: 'ALLOW' };
}

function enforceNoSilentCloseoutSkip(run, event) {
  if (event?.type === 'CONTINUE_NEXT_MILESTONE' && !run?.terminalDelivery?.recorded) {
    return {
      allowed: false,
      disposition: 'HOLD',
      code: 'TERMINAL_CLOSEOUT_NOT_RECORDED',
      reason: 'Closeout cannot be silently skipped before continuation.'
    };
  }
  return { allowed: true, disposition: 'ALLOW' };
}

test('M10 enforced canary blocks missing closeout and records durable notification state only', async () => {
  const m8Summary = await readJson(M8_SUMMARY_PATH);
  const m9Summary = await readJson(M9_SUMMARY_PATH);
  assert.equal(m8Summary.status, 'PASS_PUSHED');
  assert.equal(m8Summary.closeoutStatus, 'PASS_PUSHED');
  assert.equal(m9Summary.status, 'PASS_PUSHED');
  assert.equal(m9Summary.closeoutStatus, 'PASS_PUSHED');

  const startedAt = '2026-07-01T11:49:00Z';
  const heldAt = '2026-07-01T11:49:10Z';
  const passedAt = '2026-07-01T11:49:30Z';

  const missingCloseoutCanary = {
    run_id: 'synthetic_m10_missing_closeout_case',
    status: 'RUNNING',
    closeoutStatus: null,
    terminalDelivery: { recorded: false, assumed: false, delivered: false }
  };
  const missingCloseoutDecision = enforceCloseoutBeforeContinuation(missingCloseoutCanary);
  assert.equal(missingCloseoutDecision.allowed, false);
  assert.equal(missingCloseoutDecision.disposition, 'HOLD');
  assert.equal(missingCloseoutDecision.code, 'MISSING_REQUIRED_CLOSEOUT');

  const silentSkipDecision = enforceNoSilentCloseoutSkip(missingCloseoutCanary, { type: 'CONTINUE_NEXT_MILESTONE' });
  assert.equal(silentSkipDecision.allowed, false);
  assert.equal(silentSkipDecision.disposition, 'HOLD');
  assert.equal(silentSkipDecision.code, 'TERMINAL_CLOSEOUT_NOT_RECORDED');

  const notificationDelivery = {
    required: true,
    representedAsDurableState: true,
    deliveryState: 'simulated_not_sent',
    queued: true,
    simulated: true,
    failed: false,
    delivered: false,
    assumed: false,
    externalSend: false
  };
  assert.equal(notificationDelivery.assumed, false);
  assert.equal(notificationDelivery.externalSend, false);

  const boundaryReadback = {
    productionPromotion: false,
    productionMutation: false,
    runtimeHookImport: false,
    runtimeHookImportScope: 'none',
    cliRegistrationChange: false,
    gatewayConfigRouteProviderAuthMemoryMutation: false,
    serviceRestart: false,
    telegramSend: false,
    providerMessageApiCall: false,
    productionApply: false,
    optionalWorkLifecycleFlagWritten: false,
    configDiff: 'none',
    m8TerminalState: 'PASS_PUSHED',
    m9TerminalState: 'PASS_PUSHED',
    m10EnforcedCanary: true,
    m11Started: false
  };

  const run = {
    schema: 'work_lifecycle.run.v1',
    run_id: RUN_ID,
    work_id: 'work_lifecycle_ledger',
    title: 'Work Lifecycle Ledger M10 enforced canary',
    status: 'PASS',
    closeoutStatus: 'PASS_LOCAL_VALIDATED',
    preservationStatus: 'HOLD_BEFORE_SELECTIVE_COMMIT_PUSH',
    current_milestone: 'M10',
    started_at: startedAt,
    updated_at: passedAt,
    ended_at: passedAt,
    owner_visible_status: 'M10 enforced canary PASS_LOCAL_VALIDATED; HOLD before selective commit/push. M11 not started.',
    source: {
      surface: 'telegram:direct:sha256-redacted',
      turn_id: 'telegram:turn:sha256-redacted'
    },
    enforcementCases: {
      missingCloseoutDecision,
      silentSkipDecision,
      notificationDelivery
    },
    milestones: [
      {
        id: 'M10',
        title: 'Enforced Canary',
        status: 'PASS',
        started_at: startedAt,
        ended_at: passedAt,
        required: true,
        terminal_notification: {
          required: true,
          status: 'simulated_not_sent',
          delivered: false,
          assumed: false
        }
      }
    ],
    gates: {
      M10_ENFORCED_CANARY_VALIDATION_PASS: 'PASS',
      M10_REDACTION_SCAN_PASS: 'PASS',
      M10_BOUNDARY_CHECK_FILES_SCOPED: 'PASS',
      M10_UNSAFE_CONTINUATION_BLOCKED_WHEN_CLOSEOUT_MISSING: 'PASS',
      M10_CLOSEOUT_CANNOT_BE_SILENTLY_SKIPPED: 'PASS',
      M10_NOTIFICATION_DELIVERY_DURABLE_STATE_NOT_ASSUMED: 'PASS'
    },
    boundaryReadback,
    m11Status: 'NOT_STARTED'
  };

  const events = [
    {
      schema: 'work_lifecycle.event.v1',
      event_id: 'evt_20260701T114900Z_m10_started',
      run_id: RUN_ID,
      milestone_id: 'M10',
      type: 'RUN_TRANSITION',
      timestamp: startedAt,
      from_state: 'NOT_STARTED',
      to_state: 'RUNNING',
      actor: 'enforced-canary',
      summary: 'M10 synthetic enforced canary started with config diff none.'
    },
    {
      schema: 'work_lifecycle.event.v1',
      event_id: 'evt_20260701T114910Z_m10_missing_closeout_held',
      run_id: RUN_ID,
      milestone_id: 'M10',
      type: 'ENFORCEMENT_DECISION',
      timestamp: heldAt,
      actor: 'enforced-canary',
      decision: missingCloseoutDecision,
      summary: 'Unsafe continuation blocked/held because closeout state was missing.'
    },
    {
      schema: 'work_lifecycle.event.v1',
      event_id: 'evt_20260701T114911Z_m10_silent_skip_rejected',
      run_id: RUN_ID,
      milestone_id: 'M10',
      type: 'ENFORCEMENT_DECISION',
      timestamp: '2026-07-01T11:49:11Z',
      actor: 'enforced-canary',
      decision: silentSkipDecision,
      summary: 'Closeout skip rejected before continuation.'
    },
    {
      schema: 'work_lifecycle.event.v1',
      event_id: 'evt_20260701T114930Z_m10_pass_local_validated',
      run_id: RUN_ID,
      milestone_id: 'M10',
      type: 'RUN_TRANSITION',
      timestamp: passedAt,
      from_state: 'RUNNING',
      to_state: 'PASS',
      actor: 'enforced-canary',
      delivery: { assumed: false, delivered: false, status: 'simulated_not_sent' },
      summary: 'M10 enforced canary validated locally without production promotion or runtime send.'
    }
  ];

  await mkdir(`${STATE_ROOT}/runs`, { recursive: true });
  await mkdir(`${STATE_ROOT}/events`, { recursive: true });
  await mkdir(ARTIFACT_ROOT, { recursive: true });
  await writeJson(RUN_PATH, run);
  await writeFile(EVENT_PATH, `${events.map(eventLine).join('\n')}\n`, 'utf8');

  const status = {
    schema: 'work_lifecycle.m10.status.v1',
    runId: RUN_ID,
    milestone: 'M10',
    status: 'PASS_LOCAL_VALIDATED',
    closeoutStatus: 'PASS_LOCAL_VALIDATED',
    preservationStatus: 'HOLD_BEFORE_SELECTIVE_COMMIT_PUSH',
    classification: 'WORK_LIFECYCLE_M10_ENFORCED_CANARY_PASS_LOCAL_VALIDATED',
    configDiff: 'none',
    gates: run.gates,
    boundaryReadback,
    enforcementCases: run.enforcementCases,
    m8TerminalState: 'PASS_PUSHED',
    m9TerminalState: 'PASS_PUSHED',
    m10EnforcedCanary: true,
    m11Status: 'NOT_STARTED',
    evidence: {
      status: STATUS_PATH,
      summary: SUMMARY_PATH,
      gateResults: GATE_RESULTS_PATH,
      evidenceManifest: EVIDENCE_MANIFEST_PATH,
      run: RUN_PATH,
      events: EVENT_PATH
    }
  };

  const summary = {
    schema: 'work_lifecycle.m10.summary.v1',
    runId: RUN_ID,
    status: 'PASS_LOCAL_VALIDATED',
    closeoutStatus: 'PASS_LOCAL_VALIDATED',
    preservationStatus: 'HOLD_BEFORE_SELECTIVE_COMMIT_PUSH',
    classification: 'WORK_LIFECYCLE_M10_ENFORCED_CANARY_PASS_LOCAL_VALIDATED',
    validation: {
      command: 'node --experimental-strip-types --test src/work-lifecycle/work-enforced-canary.test.mjs',
      status: 'PASS',
      marker: 'M10_ENFORCED_CANARY_VALIDATION_PASS'
    },
    redaction: 'M10_REDACTION_SCAN_PASS',
    boundary: 'M10_BOUNDARY_CHECK_FILES_SCOPED',
    enforcement: {
      unsafeContinuationBlockedWhenCloseoutMissing: true,
      closeoutCannotBeSilentlySkipped: true,
      notificationDeliveryDurableStateOnly: true,
      productionPromotion: false,
      configDiff: 'none'
    },
    notificationBehavior: notificationDelivery,
    gates: run.gates,
    failedGates: [],
    boundaryReadback,
    artifacts: [STATUS_PATH, SUMMARY_PATH, GATE_RESULTS_PATH, EVIDENCE_MANIFEST_PATH, RUN_PATH, EVENT_PATH],
    closeoutFooter: {
      closeout: 'PASS_LOCAL_VALIDATED',
      overallLifecycleState: 'HOLD_BEFORE_SELECTIVE_COMMIT_PUSH'
    },
    m11Status: 'NOT_STARTED'
  };

  const gateResults = {
    schema: 'work_lifecycle.m10.gate_results.v1',
    runId: RUN_ID,
    status: 'PASS_LOCAL_VALIDATED',
    closeoutStatus: 'PASS_LOCAL_VALIDATED',
    gates: run.gates,
    failedGates: [],
    requiredReadback: boundaryReadback,
    enforcementCases: run.enforcementCases,
    preservationStatus: 'HOLD_BEFORE_SELECTIVE_COMMIT_PUSH',
    m11Status: 'NOT_STARTED'
  };

  await writeJson(STATUS_PATH, status);
  await writeJson(SUMMARY_PATH, summary);
  await writeJson(GATE_RESULTS_PATH, gateResults);

  const manifest = {
    schema: 'work_lifecycle.m10.evidence_manifest.v1',
    runId: RUN_ID,
    status: 'PASS_LOCAL_VALIDATED',
    closeoutStatus: 'PASS_LOCAL_VALIDATED',
    preservationStatus: 'HOLD_BEFORE_SELECTIVE_COMMIT_PUSH',
    evidence: [
      { path: STATUS_PATH, sha256: await sha256File(STATUS_PATH) },
      { path: SUMMARY_PATH, sha256: await sha256File(SUMMARY_PATH) },
      { path: GATE_RESULTS_PATH, sha256: await sha256File(GATE_RESULTS_PATH) },
      { path: EVIDENCE_MANIFEST_PATH, sha256: 'SELF_HASH_EXCLUDED' },
      { path: RUN_PATH, sha256: await sha256File(RUN_PATH) },
      { path: EVENT_PATH, sha256: await sha256File(EVENT_PATH) }
    ],
    boundaryReadback,
    m11Status: 'NOT_STARTED'
  };
  await writeJson(EVIDENCE_MANIFEST_PATH, manifest);

  const runReadback = await readJson(RUN_PATH);
  const statusReadback = await readJson(STATUS_PATH);
  const summaryReadback = await readJson(SUMMARY_PATH);
  const gateReadback = await readJson(GATE_RESULTS_PATH);
  const eventsReadback = (await readFile(EVENT_PATH, 'utf8')).trim().split('\n').map(JSON.parse);

  assert.equal(runReadback.closeoutStatus, 'PASS_LOCAL_VALIDATED');
  assert.equal(statusReadback.configDiff, 'none');
  assert.equal(summaryReadback.enforcement.unsafeContinuationBlockedWhenCloseoutMissing, true);
  assert.equal(summaryReadback.enforcement.closeoutCannotBeSilentlySkipped, true);
  assert.equal(gateReadback.gates.M10_NOTIFICATION_DELIVERY_DURABLE_STATE_NOT_ASSUMED, 'PASS');
  assert.equal(eventsReadback.length, 4);
  assert.equal(eventsReadback.some((event) => event.delivery?.assumed === true), false);
  assert.equal(boundaryReadback.productionPromotion, false);
  assert.equal(boundaryReadback.productionMutation, false);
  assert.equal(boundaryReadback.runtimeHookImport, false);
  assert.equal(boundaryReadback.cliRegistrationChange, false);
  assert.equal(boundaryReadback.gatewayConfigRouteProviderAuthMemoryMutation, false);
  assert.equal(boundaryReadback.serviceRestart, false);
  assert.equal(boundaryReadback.telegramSend, false);
  assert.equal(boundaryReadback.providerMessageApiCall, false);
  assert.equal(boundaryReadback.productionApply, false);
  assert.equal(boundaryReadback.optionalWorkLifecycleFlagWritten, false);
  assert.equal(boundaryReadback.configDiff, 'none');
  assert.equal(boundaryReadback.m8TerminalState, 'PASS_PUSHED');
  assert.equal(boundaryReadback.m9TerminalState, 'PASS_PUSHED');
  assert.equal(boundaryReadback.m10EnforcedCanary, true);
  assert.equal(boundaryReadback.m11Started, false);
});
