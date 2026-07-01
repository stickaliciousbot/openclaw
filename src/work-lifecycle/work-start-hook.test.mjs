import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import test from 'node:test';

import { classifyWorkRequest } from './work-classifier.ts';
import { createWorkContext } from './work-context.ts';
import { createStartAcknowledgement, renderStartAcknowledgement, runAfterStartAcknowledgement } from './work-start-hook.ts';
import { readJsonFile, readLifecycleEvents } from './work-ledger-store.ts';

async function tempRoot() {
  return mkdtemp(join(tmpdir(), 'work-start-hook-test-'));
}

test('M3_G1 toolful user turn creates ACK_PENDING run', async () => {
  const root = await tempRoot();
  try {
    const result = await createStartAcknowledgement(root, {
      text: 'implement M3 start acknowledgement hook',
      usesTools: true,
      surface: 'telegram_direct',
      chat_id: 'telegram:raw-chat',
      message_id: 'telegram:raw-message'
    }, { runId: 'work_20260701T000000Z_m3ack', now: new Date('2026-07-01T00:00:00Z') });

    assert.equal(result.lifecycle_managed, true);
    assert.equal(result.run.status, 'ACK_PENDING');
    assert.equal(result.run.ack.queued, true);
    assert.equal(result.run.chat_id, 'telegram:direct:sha256-redacted');
    assert.equal(result.run.user_turn_id, 'telegram:turn:sha256-redacted');
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('M3_G2 side effect runs only after ack is queued', async () => {
  const root = await tempRoot();
  try {
    const marker = join(root, 'marker.txt');
    let observedAckReady = false;
    const result = await runAfterStartAcknowledgement(root, {
      text: 'run focused validation',
      usesTools: true,
      surface: 'telegram_direct',
      chat_id: 'telegram:raw-chat'
    }, async ({ ackReady }) => {
      observedAckReady = ackReady;
      return 'side-effect-ok';
    }, { runId: 'work_20260701T000000Z_m3sideeffect', now: new Date('2026-07-01T00:00:00Z'), sideEffectMarkerPath: marker });

    assert.equal(observedAckReady, true);
    assert.equal(result.result, 'side-effect-ok');
    assert.equal(await readFile(marker, 'utf8'), 'ackReady:true\n');
    const events = await readLifecycleEvents(root, 'work_20260701T000000Z_m3sideeffect');
    assert.equal(events[0].type, 'RUN_CREATED');
    assert.equal(events[1].type, 'ACK_QUEUED');
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('M3_G3 ack template includes scope, safety boundary, and first checkpoint', () => {
  const classification = classifyWorkRequest({ text: 'validate work lifecycle hook', usesTools: true, first_checkpoint: 'M3 focused validation' });
  const context = createWorkContext({ surface: 'telegram_direct', chat_id: 'telegram:raw-chat' }, { runId: 'work_20260701T000000Z_template', now: new Date('2026-07-01T00:00:00Z') });
  const body = renderStartAcknowledgement({ classification, context });
  assert.match(body, /Scope:/);
  assert.match(body, /Safety boundary:/);
  assert.match(body, /First checkpoint:/);
  assert.match(body, /M3 focused validation/);
});

test('M3_G4 duplicate start ack is deduped by stable notification id/key', async () => {
  const root = await tempRoot();
  try {
    const request = { text: 'implement repeatable hook', usesTools: true, surface: 'telegram_direct' };
    const options = { runId: 'work_20260701T000000Z_dedupe', notificationId: 'notif_static_ack', now: new Date('2026-07-01T00:00:00Z') };
    const first = await createStartAcknowledgement(root, request, options);
    const second = await createStartAcknowledgement(root, request, options);
    assert.equal(first.acknowledgement.dedupe_key, second.acknowledgement.dedupe_key);
    const outbox = await readJsonFile(first.outboxPath);
    assert.equal(outbox.notification_id, 'notif_static_ack');
    assert.equal(outbox.dedupe_key, 'work_20260701T000000Z_dedupe:ACK_PENDING:START_ACK:telegram_direct');
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('M3_G5 if ack cannot be delivered it is durably queued', async () => {
  const root = await tempRoot();
  try {
    const result = await createStartAcknowledgement(root, {
      text: 'patch files',
      usesTools: true,
      surface: 'telegram_direct'
    }, { runId: 'work_20260701T000000Z_queued', now: new Date('2026-07-01T00:00:00Z') });
    const outbox = await readJsonFile(result.outboxPath);
    assert.equal(outbox.status, 'QUEUED');
    assert.equal(result.run.ack.delivered, false);
    assert.equal(result.run.ack.queued, true);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('non-tool trivial request is not lifecycle managed', async () => {
  const root = await tempRoot();
  try {
    const result = await createStartAcknowledgement(root, { text: 'hello there', noLifecycle: true });
    assert.equal(result.lifecycle_managed, false);
    assert.equal(result.run, null);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
