import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname } from 'node:path';
import test from 'node:test';

import {
  WORK_LIFECYCLE_INTERNAL_HOOK_ENTRY_ID,
  classifyWorkLifecycleHookReadiness,
  proposedWorkLifecycleInternalHookConfig,
  workLifecycleInternalHookConfigSchema
} from './work-runtime-hook-config.ts';
import {
  assertNoLiveWorkLifecycleEnforcement,
  evaluateWorkLifecycleRuntimeCanary
} from './work-runtime-canary-hook.ts';

const RUN_ID = 'work_20260701T122100Z_lifecycle_ledger_m11b';
const STATE_ROOT = 'state/work-lifecycle';
const ARTIFACT_ROOT = 'sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout';
const RUN_PATH = `${STATE_ROOT}/runs/${RUN_ID}.json`;
const EVENT_PATH = `${STATE_ROOT}/events/${RUN_ID}.jsonl`;
const STATUS_PATH = `${ARTIFACT_ROOT}/m11b-status.json`;
const SUMMARY_PATH = `${ARTIFACT_ROOT}/m11b-summary.json`;
const GATE_RESULTS_PATH = `${ARTIFACT_ROOT}/m11b-gate-results.json`;
const EVIDENCE_MANIFEST_PATH = `${ARTIFACT_ROOT}/m11b-evidence_manifest.json`;
const READINESS_PATH = `${ARTIFACT_ROOT}/M11B_SCHEMA_HOOK_READINESS.md`;
const M8_SUMMARY_PATH = 'sharedspace/runtime-kernel-validation/work-lifecycle/m8-failure-injection/summary.json';
const M9_SUMMARY_PATH = 'sharedspace/runtime-kernel-validation/work-lifecycle/m9-observe-only-canary/summary.json';
const M10_SUMMARY_PATH = 'sharedspace/runtime-kernel-validation/work-lifecycle/m10-enforced-canary/summary.json';
const M11A_RUN_PATH = 'state/work-lifecycle/runs/work_20260701T120800Z_lifecycle_ledger_m11a.json';

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

async function assertNoRawSecretSentinels(paths) {
  const deniedLiterals = ['botToken', 'Authorization: Bearer', 'apiKey', 'OPENAI_API_KEY'];
  const rawTelegramIdPattern = /(?<![A-Za-z0-9:_-])\d{10,12}(?![A-Za-z0-9:_-])/;
  for (const path of paths) {
    const text = await readFile(path, 'utf8');
    for (const term of deniedLiterals) {
      assert.equal(text.includes(term), false, `${path} contains denied sentinel ${term}`);
    }
    assert.equal(rawTelegramIdPattern.test(text), false, `${path} contains raw Telegram-id-shaped numeric identifier`);
  }
}

test('M11B disabled-by-default schema/hook scaffold is inert until explicit internal hook enablement', async () => {
  const [m8, m9, m10, m11a] = await Promise.all([
    readJson(M8_SUMMARY_PATH),
    readJson(M9_SUMMARY_PATH),
    readJson(M10_SUMMARY_PATH),
    readJson(M11A_RUN_PATH)
  ]);

  assert.equal(m8.closeoutStatus, 'PASS_PUSHED');
  assert.equal(m9.closeoutStatus, 'PASS_PUSHED');
  assert.equal(m10.closeoutStatus, 'PASS_PUSHED');
  assert.equal(m11a.closeoutStatus, 'HOLD_SCHEMA_OR_HOOK_UNAVAILABLE');
  assert.equal(m11a.classification.m11ApplyApproval, 'NOT_READY');

  assert.equal(workLifecycleInternalHookConfigSchema.properties.hooks.properties.internal.properties.entries.properties[WORK_LIFECYCLE_INTERNAL_HOOK_ENTRY_ID].properties.productionPromotion.const, false);
  assert.equal(workLifecycleInternalHookConfigSchema.properties.hooks.properties.internal.properties.entries.properties[WORK_LIFECYCLE_INTERNAL_HOOK_ENTRY_ID].properties.allowRuntimeSend.const, false);

  const disabledDecision = assertNoLiveWorkLifecycleEnforcement({});
  assert.equal(disabledDecision.action, 'NOOP');
  assert.equal(disabledDecision.enforcementActive, false);

  const entryEnabledButInternalDisabled = {
    hooks: {
      internal: {
        enabled: false,
        entries: {
          [WORK_LIFECYCLE_INTERNAL_HOOK_ENTRY_ID]: { enabled: true, mode: 'enforce_canary' }
        }
      }
    }
  };
  assert.equal(classifyWorkLifecycleHookReadiness(entryEnabledButInternalDisabled).ready, false);
  assert.equal(evaluateWorkLifecycleRuntimeCanary({
    config: entryEnabledButInternalDisabled,
    event: { type: 'before_next_milestone', scope: 'production_canary', canaryOwner: 'stickbot' },
    runRecord: { closeoutStatus: null }
  }).action, 'NOOP');

  const proposed = proposedWorkLifecycleInternalHookConfig();
  const readiness = classifyWorkLifecycleHookReadiness(proposed);
  assert.equal(readiness.ready, true);
  assert.equal(readiness.mode, 'bounded_enforce_canary');

  const outOfScope = evaluateWorkLifecycleRuntimeCanary({
    config: proposed,
    event: { type: 'before_next_milestone', scope: 'global', canaryOwner: 'stickbot' },
    runRecord: { closeoutStatus: null }
  });
  assert.equal(outOfScope.action, 'NOOP');
  assert.equal(outOfScope.enforcementActive, false);

  const missingCloseout = evaluateWorkLifecycleRuntimeCanary({
    config: proposed,
    event: { type: 'before_next_milestone', scope: 'production_canary', canaryOwner: 'stickbot' },
    runRecord: { closeoutStatus: null }
  });
  assert.equal(missingCloseout.action, 'HOLD');
  assert.equal(missingCloseout.allowed, false);
  assert.equal(missingCloseout.mutation, false);
  assert.equal(missingCloseout.externalSend, false);
  assert.equal(missingCloseout.productionPromotion, false);

  const validCloseout = evaluateWorkLifecycleRuntimeCanary({
    config: proposed,
    event: { type: 'before_next_milestone', scope: 'production_canary', canaryOwner: 'stickbot' },
    runRecord: { closeoutStatus: 'PASS_PUSHED' }
  });
  assert.equal(validCloseout.action, 'ALLOW');
  assert.equal(validCloseout.allowed, true);
  assert.equal(validCloseout.mutation, false);
  assert.equal(validCloseout.externalSend, false);

  const assumedDelivery = evaluateWorkLifecycleRuntimeCanary({
    config: proposed,
    event: {
      type: 'before_terminal_closeout',
      scope: 'production_canary',
      canaryOwner: 'stickbot',
      deliveryState: { assumed: true, delivered: false, queued: false, recorded: false }
    }
  });
  assert.equal(assumedDelivery.action, 'HOLD');
  assert.equal(assumedDelivery.reason, 'TERMINAL_DELIVERY_STATE_NOT_DURABLE');

  const startedAt = '2026-07-01T12:21:00Z';
  const endedAt = '2026-07-01T12:21:30Z';
  const gates = {
    M11B_SCHEMA_OR_HOOK_SCAFFOLD_VALIDATION_PASS: 'PASS',
    M11B_DISABLED_BY_DEFAULT_PASS: 'PASS',
    M11B_NO_LIVE_ENFORCEMENT_WITHOUT_FLAG_PASS: 'PASS',
    M11B_REDACTION_SCAN_PASS: 'PASS',
    M11B_BOUNDARY_CHECK_FILES_SCOPED: 'PASS'
  };
  const boundaryReadback = {
    productionApply: false,
    productionPromotion: false,
    productionMutation: false,
    liveGatewayBehaviorChanged: false,
    configMutation: false,
    routeProviderAuthMemoryMutation: false,
    serviceRestart: false,
    telegramSendFromCodeRuntime: false,
    providerMessageApiCall: false,
    cliRegistrationChange: false,
    m12Started: false,
    proposedConfigPath: `hooks.internal.entries.${WORK_LIFECYCLE_INTERNAL_HOOK_ENTRY_ID}`,
    disabledByDefault: true,
    explicitEnablementRequired: true,
    defaultDecision: disabledDecision
  };

  const run = {
    schema: 'work_lifecycle.run.v1',
    run_id: RUN_ID,
    work_id: 'work_lifecycle_ledger',
    title: 'Work Lifecycle Ledger M11B schema/hook readiness',
    status: 'PASS',
    closeoutStatus: 'PASS_LOCAL_VALIDATED',
    preservationStatus: 'HOLD_BEFORE_SELECTIVE_COMMIT_PUSH',
    current_milestone: 'M11B',
    started_at: startedAt,
    updated_at: endedAt,
    ended_at: endedAt,
    owner_visible_status: 'M11B schema/hook readiness PASS_LOCAL_VALIDATED; disabled-by-default scaffold only; M11 apply NOT_READY; M12 NOT_STARTED.',
    source: {
      surface: 'telegram:direct:sha256-redacted',
      turn_id: 'telegram:turn:sha256-redacted'
    },
    recommendation: 'BOUNDED_HOOK_READY',
    schemaLookup: {
      work_lifecycle: 'config schema path not found',
      hooks_internal_entries: 'schema-backed object path exists'
    },
    gates,
    readiness,
    decisions: { disabledDecision, outOfScope, missingCloseout, validCloseout, assumedDelivery },
    boundaryReadback,
    m11Status: 'NOT_STARTED',
    m11ApplyApproval: 'NOT_READY',
    m12Status: 'NOT_STARTED'
  };

  const events = [
    {
      schema: 'work_lifecycle.event.v1',
      event_id: 'evt_20260701T122100Z_m11b_started',
      run_id: RUN_ID,
      milestone_id: 'M11B',
      type: 'RUN_TRANSITION',
      timestamp: startedAt,
      from_state: 'NOT_STARTED',
      to_state: 'RUNNING',
      actor: 'stickbot',
      summary: 'M11B schema/hook readiness started evidence-only; no production apply or live Gateway behavior change.'
    },
    {
      schema: 'work_lifecycle.event.v1',
      event_id: 'evt_20260701T122130Z_m11b_pass_local_validated',
      run_id: RUN_ID,
      milestone_id: 'M11B',
      type: 'RUN_TRANSITION',
      timestamp: endedAt,
      from_state: 'RUNNING',
      to_state: 'PASS',
      actor: 'stickbot',
      summary: 'M11B disabled-by-default bounded hook scaffold validated locally; hold before selective commit/push.'
    }
  ];

  await mkdir(`${STATE_ROOT}/runs`, { recursive: true });
  await mkdir(`${STATE_ROOT}/events`, { recursive: true });
  await mkdir(ARTIFACT_ROOT, { recursive: true });
  await writeJson(RUN_PATH, run);
  await writeFile(EVENT_PATH, `${events.map(eventLine).join('\n')}\n`, 'utf8');

  const status = {
    schema: 'work_lifecycle.m11b.status.v1',
    runId: RUN_ID,
    milestone: 'M11B',
    status: 'PASS_LOCAL_VALIDATED',
    closeoutStatus: 'PASS_LOCAL_VALIDATED',
    preservationStatus: 'HOLD_BEFORE_SELECTIVE_COMMIT_PUSH',
    recommendation: 'BOUNDED_HOOK_READY',
    gates,
    boundaryReadback,
    evidence: { readiness: READINESS_PATH, status: STATUS_PATH, summary: SUMMARY_PATH, gateResults: GATE_RESULTS_PATH, evidenceManifest: EVIDENCE_MANIFEST_PATH, run: RUN_PATH, events: EVENT_PATH }
  };
  const summary = {
    schema: 'work_lifecycle.m11b.summary.v1',
    runId: RUN_ID,
    status: 'PASS_LOCAL_VALIDATED',
    closeoutStatus: 'PASS_LOCAL_VALIDATED',
    preservationStatus: 'HOLD_BEFORE_SELECTIVE_COMMIT_PUSH',
    recommendation: 'BOUNDED_HOOK_READY',
    validation: {
      command: 'node --experimental-strip-types --test src/work-lifecycle/work-runtime-canary-hook.test.mjs',
      status: 'PASS',
      marker: 'M11B_SCHEMA_OR_HOOK_SCAFFOLD_VALIDATION_PASS'
    },
    redaction: 'M11B_REDACTION_SCAN_PASS',
    boundary: 'M11B_BOUNDARY_CHECK_FILES_SCOPED',
    gates,
    failedGates: [],
    boundaryReadback,
    closeoutFooter: { closeout: 'PASS_LOCAL_VALIDATED', overallLifecycleState: 'HOLD_BEFORE_SELECTIVE_COMMIT_PUSH' },
    m11ApplyApproval: 'NOT_READY',
    m12Status: 'NOT_STARTED'
  };
  const gateResults = {
    schema: 'work_lifecycle.m11b.gate_results.v1',
    runId: RUN_ID,
    status: 'PASS_LOCAL_VALIDATED',
    closeoutStatus: 'PASS_LOCAL_VALIDATED',
    gates,
    failedGates: [],
    disabledByDefaultProof: disabledDecision,
    noLiveEnforcementProof: entryEnabledButInternalDisabled,
    boundedHookProof: { readiness, outOfScope, missingCloseout, validCloseout, assumedDelivery },
    boundaryReadback
  };

  await writeJson(STATUS_PATH, status);
  await writeJson(SUMMARY_PATH, summary);
  await writeJson(GATE_RESULTS_PATH, gateResults);

  const evidencePaths = [READINESS_PATH, STATUS_PATH, SUMMARY_PATH, GATE_RESULTS_PATH, RUN_PATH, EVENT_PATH];
  await assertNoRawSecretSentinels(evidencePaths);

  const manifest = {
    schema: 'work_lifecycle.m11b.evidence_manifest.v1',
    runId: RUN_ID,
    status: 'PASS_LOCAL_VALIDATED',
    recommendation: 'BOUNDED_HOOK_READY',
    artifacts: Object.fromEntries(await Promise.all(evidencePaths.map(async (path) => [path, { sha256: await sha256File(path) }]))),
    generatedAt: endedAt,
    boundaryReadback
  };
  await writeJson(EVIDENCE_MANIFEST_PATH, manifest);
  await assertNoRawSecretSentinels([...evidencePaths, EVIDENCE_MANIFEST_PATH]);
});
