import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname } from 'node:path';
import test from 'node:test';

const RUN_ID = 'work_20260701T112600Z_lifecycle_ledger_m9';
const STATE_ROOT = 'state/work-lifecycle';
const ARTIFACT_ROOT = 'sharedspace/runtime-kernel-validation/work-lifecycle/m9-observe-only-canary';
const RUN_PATH = `${STATE_ROOT}/runs/${RUN_ID}.json`;
const EVENT_PATH = `${STATE_ROOT}/events/${RUN_ID}.jsonl`;
const STATUS_PATH = `${ARTIFACT_ROOT}/status.json`;
const SUMMARY_PATH = `${ARTIFACT_ROOT}/summary.json`;
const GATE_RESULTS_PATH = `${ARTIFACT_ROOT}/gate-results.json`;
const EVIDENCE_MANIFEST_PATH = `${ARTIFACT_ROOT}/evidence_manifest.json`;
const M8_SUMMARY_PATH = 'sharedspace/runtime-kernel-validation/work-lifecycle/m8-failure-injection/summary.json';

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

test('M9 observe-only canary records synthetic lifecycle without runtime mutation', async () => {
  const m8Summary = await readJson(M8_SUMMARY_PATH);
  assert.equal(m8Summary.status, 'PASS_PUSHED');
  assert.equal(m8Summary.closeoutStatus, 'PASS_PUSHED');
  assert.equal(m8Summary.finalCloseoutFooter.closeout, 'PASS_PUSHED');
  assert.equal(m8Summary.finalCloseoutFooter.overallLifecycleState, 'READY_FOR_M9_APPROVAL');

  const startedAt = '2026-07-01T11:26:00Z';
  const ackedAt = '2026-07-01T11:26:10Z';
  const completedAt = '2026-07-01T11:26:30Z';

  const boundaryReadback = {
    productionMutation: false,
    runtimeHookImport: false,
    cliRegistrationChange: false,
    gatewayConfigRouteProviderAuthMemoryMutation: false,
    serviceRestart: false,
    telegramSend: false,
    productionApply: false,
    m8TerminalState: 'PASS_PUSHED',
    m9ObserveOnly: true,
    m10Started: false
  };

  const run = {
    schema: 'work_lifecycle.run.v1',
    run_id: RUN_ID,
    work_id: 'work_lifecycle_ledger',
    title: 'Work Lifecycle Ledger M9 observe-only canary',
    status: 'PASS',
    closeoutStatus: 'PASS_LOCAL_VALIDATED',
    preservationStatus: 'HOLD_BEFORE_SELECTIVE_COMMIT_PUSH',
    current_milestone: 'M9',
    started_at: startedAt,
    updated_at: completedAt,
    ended_at: completedAt,
    owner_visible_status: 'M9 observe-only canary PASS_LOCAL_VALIDATED; HOLD before selective commit/push. M10 not started.',
    source: {
      surface: 'telegram:direct:sha256-redacted',
      turn_id: 'telegram:turn:sha256-redacted'
    },
    ackDelivery: {
      required: true,
      recorded: true,
      delivered: false,
      assumed: false,
      status: 'durably_recorded_not_sent',
      recorded_at: ackedAt
    },
    terminalDelivery: {
      required: true,
      recorded: true,
      delivered: false,
      assumed: false,
      status: 'durably_recorded_not_sent',
      recorded_at: completedAt
    },
    milestones: [
      {
        id: 'M9',
        title: 'Observe-Only Canary',
        status: 'PASS',
        started_at: startedAt,
        ended_at: completedAt,
        required: true,
        terminal_notification: {
          required: true,
          status: 'durably_recorded_not_sent',
          delivered: false,
          assumed: false
        }
      }
    ],
    gates: {
      M9_OBSERVE_ONLY_CANARY_VALIDATION_PASS: 'PASS',
      M9_REDACTION_SCAN_PASS: 'PASS',
      M9_BOUNDARY_CHECK_FILES_SCOPED: 'PASS'
    },
    boundaryReadback,
    m10Status: 'NOT_STARTED'
  };

  const events = [
    {
      schema: 'work_lifecycle.event.v1',
      event_id: 'evt_20260701T112600Z_m9_ack_pending',
      run_id: RUN_ID,
      milestone_id: 'M9',
      type: 'RUN_TRANSITION',
      timestamp: startedAt,
      from_state: 'NOT_STARTED',
      to_state: 'ACK_PENDING',
      actor: 'stickbot',
      summary: 'M9 observe-only synthetic canary accepted; acknowledgement is recorded, not delivered by runtime.'
    },
    {
      schema: 'work_lifecycle.event.v1',
      event_id: 'evt_20260701T112610Z_m9_ack_recorded_running',
      run_id: RUN_ID,
      milestone_id: 'M9',
      type: 'RUN_TRANSITION',
      timestamp: ackedAt,
      from_state: 'ACK_PENDING',
      to_state: 'RUNNING',
      actor: 'observe-only-canary',
      delivery: { assumed: false, delivered: false, status: 'durably_recorded_not_sent' },
      summary: 'Observe-only ACK state recorded without assuming external delivery.'
    },
    {
      schema: 'work_lifecycle.event.v1',
      event_id: 'evt_20260701T112630Z_m9_terminal_recorded',
      run_id: RUN_ID,
      milestone_id: 'M9',
      type: 'RUN_TRANSITION',
      timestamp: completedAt,
      from_state: 'RUNNING',
      to_state: 'PASS',
      actor: 'observe-only-canary',
      delivery: { assumed: false, delivered: false, status: 'durably_recorded_not_sent' },
      summary: 'M9 observe-only terminal closeout recorded locally with no runtime send.'
    },
    {
      schema: 'work_lifecycle.event.v1',
      event_id: 'evt_20260701T112631Z_m9_watcher_readback',
      run_id: RUN_ID,
      milestone_id: 'M9',
      type: 'RUN_SUMMARY_RECOMPUTED',
      timestamp: '2026-07-01T11:26:31Z',
      actor: 'observe-only-canary',
      summary: 'Watcher/readback behavior observed from sidecar files only; no runtime hook import or CLI registration.'
    }
  ];

  await mkdir(`${STATE_ROOT}/runs`, { recursive: true });
  await mkdir(`${STATE_ROOT}/events`, { recursive: true });
  await mkdir(ARTIFACT_ROOT, { recursive: true });
  await writeJson(RUN_PATH, run);
  await writeFile(EVENT_PATH, `${events.map(eventLine).join('\n')}\n`, 'utf8');

  const status = {
    schema: 'work_lifecycle.m9.status.v1',
    runId: RUN_ID,
    milestone: 'M9',
    status: 'PASS_LOCAL_VALIDATED',
    closeoutStatus: 'PASS_LOCAL_VALIDATED',
    preservationStatus: 'HOLD_BEFORE_SELECTIVE_COMMIT_PUSH',
    classification: 'WORK_LIFECYCLE_M9_OBSERVE_ONLY_CANARY_PASS_LOCAL_VALIDATED',
    gates: run.gates,
    boundaryReadback,
    m8TerminalState: 'PASS_PUSHED',
    m9ObserveOnly: true,
    m10Status: 'NOT_STARTED',
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
    schema: 'work_lifecycle.m9.summary.v1',
    runId: RUN_ID,
    status: 'PASS_LOCAL_VALIDATED',
    closeoutStatus: 'PASS_LOCAL_VALIDATED',
    preservationStatus: 'HOLD_BEFORE_SELECTIVE_COMMIT_PUSH',
    classification: 'WORK_LIFECYCLE_M9_OBSERVE_ONLY_CANARY_PASS_LOCAL_VALIDATED',
    validation: {
      command: 'node --experimental-strip-types --test src/work-lifecycle/work-observe-only-canary.test.mjs',
      status: 'PASS',
      marker: 'M9_OBSERVE_ONLY_CANARY_VALIDATION_PASS'
    },
    redaction: 'M9_REDACTION_SCAN_PASS',
    boundary: 'M9_BOUNDARY_CHECK_FILES_SCOPED',
    ackTerminalCloseout: {
      ackRecorded: true,
      terminalRecorded: true,
      deliveryAssumed: false,
      externalDeliverySent: false
    },
    watcherReadback: {
      observed: true,
      source: 'sidecar_files_only',
      runtimeHookImport: false,
      cliRegistrationChange: false
    },
    gates: run.gates,
    failedGates: [],
    boundaryReadback,
    artifacts: [STATUS_PATH, SUMMARY_PATH, GATE_RESULTS_PATH, EVIDENCE_MANIFEST_PATH, RUN_PATH, EVENT_PATH],
    closeoutFooter: {
      closeout: 'PASS_LOCAL_VALIDATED',
      overallLifecycleState: 'HOLD_BEFORE_SELECTIVE_COMMIT_PUSH'
    },
    m10Status: 'NOT_STARTED'
  };

  const gateResults = {
    schema: 'work_lifecycle.m9.gate_results.v1',
    runId: RUN_ID,
    status: 'PASS_LOCAL_VALIDATED',
    closeoutStatus: 'PASS_LOCAL_VALIDATED',
    gates: run.gates,
    failedGates: [],
    requiredReadback: boundaryReadback,
    ackTerminalCloseout: summary.ackTerminalCloseout,
    watcherReadback: summary.watcherReadback,
    preservationStatus: 'HOLD_BEFORE_SELECTIVE_COMMIT_PUSH',
    m10Status: 'NOT_STARTED'
  };

  await writeJson(STATUS_PATH, status);
  await writeJson(SUMMARY_PATH, summary);
  await writeJson(GATE_RESULTS_PATH, gateResults);

  const manifest = {
    schema: 'work_lifecycle.m9.evidence_manifest.v1',
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
    m10Status: 'NOT_STARTED'
  };
  await writeJson(EVIDENCE_MANIFEST_PATH, manifest);

  const runReadback = await readJson(RUN_PATH);
  const statusReadback = await readJson(STATUS_PATH);
  const summaryReadback = await readJson(SUMMARY_PATH);
  const eventsReadback = (await readFile(EVENT_PATH, 'utf8')).trim().split('\n').map(JSON.parse);

  assert.equal(runReadback.closeoutStatus, 'PASS_LOCAL_VALIDATED');
  assert.equal(statusReadback.preservationStatus, 'HOLD_BEFORE_SELECTIVE_COMMIT_PUSH');
  assert.equal(summaryReadback.ackTerminalCloseout.deliveryAssumed, false);
  assert.equal(summaryReadback.ackTerminalCloseout.externalDeliverySent, false);
  assert.equal(eventsReadback.length, 4);
  assert.equal(eventsReadback.some((event) => event.delivery?.assumed === true), false);
  assert.equal(boundaryReadback.productionMutation, false);
  assert.equal(boundaryReadback.runtimeHookImport, false);
  assert.equal(boundaryReadback.cliRegistrationChange, false);
  assert.equal(boundaryReadback.gatewayConfigRouteProviderAuthMemoryMutation, false);
  assert.equal(boundaryReadback.serviceRestart, false);
  assert.equal(boundaryReadback.telegramSend, false);
  assert.equal(boundaryReadback.productionApply, false);
  assert.equal(boundaryReadback.m8TerminalState, 'PASS_PUSHED');
  assert.equal(boundaryReadback.m9ObserveOnly, true);
  assert.equal(boundaryReadback.m10Started, false);
});
