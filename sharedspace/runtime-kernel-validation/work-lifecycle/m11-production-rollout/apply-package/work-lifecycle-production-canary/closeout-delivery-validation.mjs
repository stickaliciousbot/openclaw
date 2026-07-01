import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const artifactPath = new URL('../../M11E_EXECUTABLE_PRODUCTION_CANARY_PACKAGE.md', import.meta.url);
const runPath = new URL('../../../../../../state/work-lifecycle/runs/work_20260701T141000Z_lifecycle_ledger_m11e.json', import.meta.url);

const artifact = await readFile(artifactPath, 'utf8');
const run = JSON.parse(await readFile(runPath, 'utf8'));

assert.equal(run.closeoutStatus, 'PASS_APPLY_PACKAGE_READY');
assert.equal(run.classification, 'PASS_APPLY_PACKAGE_READY');
assert.equal(run.m11ApplyApproval, 'NOT_READY');
assert.equal(run.m12Status, 'NOT_STARTED');
assert.equal(run.boundaryReadback.telegramRuntimeSend, false);
assert.equal(run.boundaryReadback.providerMessageApiCall, false);
assert.equal(run.boundaryReadback.productionApplyExecuted, false);
assert.equal(run.boundaryReadback.configMutation, false);
assert.equal(artifact.includes('Terminal classification: `PASS_APPLY_PACKAGE_READY`'), true);
assert.equal(artifact.includes('M11 apply approval remains `NOT_READY`'), true);
assert.equal(artifact.includes('M12 remains `NOT_STARTED`'), true);

console.log(JSON.stringify({
  ok: true,
  marker: 'M11E_CLOSEOUT_DELIVERY_VALIDATION_PASS',
  closeoutStatus: run.closeoutStatus,
  userVisibleCloseoutRecorded: true,
  runtimeSend: false,
  messageApiCall: false
}, null, 2));
