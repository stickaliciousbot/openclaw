// OpenClaw Stickbot Work Lifecycle Ledger — M1 event replay
// Sidecar-only module. Do not import from runtime paths until later lifecycle milestones.

import { readLifecycleEvents } from './work-ledger-store.ts';

export class WorkLedgerReplayError extends Error {
  constructor(code, message, details = {}) {
    super(message);
    this.name = 'WorkLedgerReplayError';
    this.code = code;
    this.details = details;
  }
}

export function replayLifecycleEvents(events) {
  if (!Array.isArray(events)) {
    throw new WorkLedgerReplayError('INVALID_EVENTS', 'events must be an array');
  }

  const summary = {
    schema_version: 'work_lifecycle.replay.v1',
    run_id: null,
    status: null,
    ack: {
      queued: false,
      delivered: false
    },
    milestones: {},
    notifications: {},
    event_count: 0,
    last_event_id: null,
    last_timestamp: null,
    corrupt: false
  };

  for (const event of events) {
    if (!event?.run_id || !event?.type) {
      throw new WorkLedgerReplayError('INVALID_EVENT', 'event.run_id and event.type are required', { event });
    }
    if (summary.run_id && summary.run_id !== event.run_id) {
      throw new WorkLedgerReplayError('RUN_ID_MISMATCH', 'event stream contains multiple run ids', {
        expected: summary.run_id,
        actual: event.run_id
      });
    }

    summary.run_id = event.run_id;
    summary.event_count += 1;
    summary.last_event_id = event.event_id ?? null;
    summary.last_timestamp = event.timestamp ?? null;

    switch (event.type) {
      case 'RUN_CREATED':
        summary.status = event.to_state ?? 'ACK_PENDING';
        break;
      case 'ACK_QUEUED':
        summary.ack.queued = true;
        break;
      case 'ACK_DELIVERED':
        summary.ack.delivered = true;
        summary.ack.notification_id = event.notification_id ?? summary.ack.notification_id;
        break;
      case 'RUN_TRANSITION':
        summary.status = event.to_state ?? summary.status;
        break;
      case 'MILESTONE_CREATED':
      case 'MILESTONE_TRANSITION': {
        const id = event.milestone_id;
        if (!id) {
          throw new WorkLedgerReplayError('MISSING_MILESTONE_ID', `${event.type} requires milestone_id`, { event });
        }
        summary.milestones[id] = {
          ...(summary.milestones[id] ?? {}),
          milestone_id: id,
          status: event.to_state ?? summary.milestones[id]?.status ?? 'PENDING',
          last_event_id: event.event_id ?? null,
          last_timestamp: event.timestamp ?? null,
          notification_id: event.notification_id ?? summary.milestones[id]?.notification_id
        };
        break;
      }
      case 'NOTIFICATION_QUEUED':
      case 'NOTIFICATION_DELIVERED':
      case 'NOTIFICATION_FAILED': {
        const id = event.notification_id;
        if (id) {
          summary.notifications[id] = {
            notification_id: id,
            status: event.type.replace('NOTIFICATION_', ''),
            last_event_id: event.event_id ?? null,
            last_timestamp: event.timestamp ?? null
          };
        }
        break;
      }
      case 'HEARTBEAT':
      case 'WATCHER_ALERT':
      case 'RUN_SUMMARY_RECOMPUTED':
        break;
      default:
        throw new WorkLedgerReplayError('UNKNOWN_EVENT_TYPE', `Unknown event type ${event.type}`, { event });
    }
  }

  return summary;
}

export async function replayLifecycleRun(rootDir, runId, options = {}) {
  const events = await readLifecycleEvents(rootDir, runId, options);
  return replayLifecycleEvents(events);
}
