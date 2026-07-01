// OpenClaw Stickbot Work Lifecycle Ledger — M3 start acknowledgement sidecar hook
// Sidecar-only module. Do not import from runtime paths until later lifecycle milestones.

import { writeFile } from 'node:fs/promises';
import { join } from 'node:path';

import { classifyWorkRequest } from './work-classifier.ts';
import { createWorkContext } from './work-context.ts';
import { appendLifecycleEvent, atomicWriteJson, createWorkLedgerPaths, ensureWorkLedgerDirs, writeRunSummary } from './work-ledger-store.ts';

export class WorkStartHookError extends Error {
  constructor(code, message, details = {}) {
    super(message);
    this.name = 'WorkStartHookError';
    this.code = code;
    this.details = details;
  }
}

export function renderStartAcknowledgement({ classification, context }) {
  return [
    `RUNNING — ${classification.title}`,
    'I’ve started work.',
    'Scope:',
    `• ${classification.scope}`,
    'Safety boundary:',
    `• Allowed: ${context.safety_boundary.allowed_mutations.join(', ') || 'none'}`,
    `• Not allowed without approval: ${context.safety_boundary.requires_operator_approval.join(', ') || 'none'}`,
    'First checkpoint:',
    `• ${classification.first_checkpoint}`
  ].join('\n');
}

export async function createStartAcknowledgement(rootDir, request, options = {}) {
  const classification = classifyWorkRequest(request);
  if (!classification.lifecycle_managed) {
    return {
      lifecycle_managed: false,
      classification,
      context: null,
      run: null,
      acknowledgement: null
    };
  }

  const context = createWorkContext(request, options);
  const paths = createWorkLedgerPaths(rootDir, context.run_id);
  await ensureWorkLedgerDirs(rootDir);

  const acknowledgement = {
    schema_version: 'work_lifecycle.notification.v1',
    notification_id: options.notificationId ?? `notif_${context.run_id}_ack`,
    run_id: context.run_id,
    kind: 'START_ACK',
    surface: context.surface,
    status: 'QUEUED',
    dedupe_key: `${context.run_id}:ACK_PENDING:START_ACK:${context.surface}`,
    created_at: context.started_at,
    body: renderStartAcknowledgement({ classification, context })
  };

  const outboxPath = join(paths.outboxDir, `${acknowledgement.notification_id}.json`);
  await atomicWriteJson(outboxPath, acknowledgement);

  const run = {
    schema_version: 'work_lifecycle.v1',
    run_id: context.run_id,
    parent_run_id: context.parent_run_id,
    user_turn_id: context.user_turn_id,
    surface: context.surface,
    chat_id: context.chat_id,
    actor: context.actor,
    title: classification.title,
    requested_by: context.requested_by,
    status: 'ACK_PENDING',
    started_at: context.started_at,
    updated_at: context.started_at,
    ended_at: null,
    safety_boundary: context.safety_boundary,
    ack: {
      required: classification.acknowledgement_required,
      delivered: false,
      delivered_at: null,
      notification_id: acknowledgement.notification_id,
      queued: true
    },
    milestones: [],
    failure: null,
    hold: null,
    abort: null,
    superseded_by: null
  };

  await writeRunSummary(rootDir, run);
  await appendLifecycleEvent(rootDir, {
    schema_version: 'work_lifecycle.v1',
    event_id: options.eventId ?? `evt_${context.run_id}_created`,
    run_id: context.run_id,
    type: 'RUN_CREATED',
    timestamp: context.started_at,
    actor: 'runtime',
    to_state: 'ACK_PENDING',
    summary: 'Lifecycle-managed work created in ACK_PENDING and start acknowledgement queued before side effect.'
  });
  await appendLifecycleEvent(rootDir, {
    schema_version: 'work_lifecycle.v1',
    event_id: options.ackQueuedEventId ?? `evt_${context.run_id}_ack_queued`,
    run_id: context.run_id,
    type: 'ACK_QUEUED',
    timestamp: context.started_at,
    notification_id: acknowledgement.notification_id,
    actor: 'runtime',
    summary: 'Start acknowledgement durably queued before side effect.'
  });

  return {
    lifecycle_managed: true,
    classification,
    context,
    run,
    acknowledgement,
    outboxPath
  };
}

export async function runAfterStartAcknowledgement(rootDir, request, sideEffect, options = {}) {
  const start = await createStartAcknowledgement(rootDir, request, options);
  if (!start.lifecycle_managed) {
    return { start, result: await sideEffect({ start, ackReady: false }) };
  }
  if (!start.run?.ack?.queued && !start.run?.ack?.delivered) {
    throw new WorkStartHookError('ACK_NOT_READY', 'Acknowledgement must be delivered or queued before side effect', {
      run_id: start.context?.run_id
    });
  }

  const markerPath = options.sideEffectMarkerPath;
  if (markerPath) {
    await writeFile(markerPath, `ackReady:${start.run.ack.queued || start.run.ack.delivered}\n`, 'utf8');
  }
  const result = await sideEffect({ start, ackReady: true });
  return { start, result };
}
