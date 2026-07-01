// OpenClaw Stickbot Work Lifecycle Ledger — M0 contract types
// Contract-only artifact. This file must not be imported by runtime paths until a later milestone.

export const WORK_LIFECYCLE_SCHEMA_VERSION = 'work_lifecycle.v1' as const;

export type WorkRunState =
  | 'ACK_PENDING'
  | 'RUNNING'
  | 'PASS'
  | 'FAIL'
  | 'HOLD'
  | 'ABORT'
  | 'SUPERSEDED';

export type WorkMilestoneState =
  | 'PENDING'
  | 'RUNNING'
  | 'PASS'
  | 'FAIL'
  | 'HOLD'
  | 'ABORT'
  | 'SUPERSEDED';

export type WorkTerminalState = Extract<WorkRunState, 'PASS' | 'FAIL' | 'HOLD' | 'ABORT' | 'SUPERSEDED'>;

export type WorkSafetyBoundaryMode =
  | 'read_only'
  | 'repo_patch'
  | 'local_runtime'
  | 'production_apply'
  | 'watcher';

export interface WorkSafetyBoundary {
  mode: WorkSafetyBoundaryMode;
  allowed_mutations: string[];
  forbidden_mutations: string[];
  requires_operator_approval: string[];
  rollback_required?: boolean;
  secrets_redaction_required: boolean;
}

export interface WorkNotificationState {
  required: boolean;
  delivered: boolean;
  delivered_at?: string | null;
  notification_id?: string | null;
  queued?: boolean;
  closeout_not_delivered?: boolean;
}

export interface WorkGateResult {
  name: string;
  status: 'PASS' | 'FAIL' | 'HOLD' | 'SKIP';
  reason?: string;
  evidence?: string[];
}

export interface WorkMilestoneRecord {
  milestone_id: string;
  name: string;
  status: WorkMilestoneState;
  required: boolean;
  started_at?: string | null;
  ended_at?: string | null;
  hard_gates: WorkGateResult[];
  artifacts: string[];
  notification: WorkNotificationState;
  superseded_by?: string | null;
}

export interface WorkFailureRecord {
  code: string;
  reason: string;
  failed_gate?: string;
  evidence?: string[];
}

export interface WorkHoldRecord {
  code: string;
  reason: string;
  needed_from_operator?: string;
  blocker_artifacts?: string[];
}

export interface WorkAbortRecord {
  code: string;
  reason: string;
  requested_by?: 'operator' | 'runtime' | 'policy' | 'watcher';
}

export interface WorkRunRecord {
  schema_version: typeof WORK_LIFECYCLE_SCHEMA_VERSION;
  run_id: string;
  parent_run_id: string | null;
  user_turn_id: string | null;
  surface: string;
  chat_id: string;
  actor: 'stickbot' | string;
  title: string;
  requested_by: 'operator' | 'runtime' | string;
  status: WorkRunState;
  started_at: string;
  updated_at: string;
  ended_at: string | null;
  safety_boundary: WorkSafetyBoundary;
  ack: WorkNotificationState;
  milestones: WorkMilestoneRecord[];
  failure: WorkFailureRecord | null;
  hold: WorkHoldRecord | null;
  abort: WorkAbortRecord | null;
  superseded_by: string | null;
}

export type WorkLifecycleEventType =
  | 'RUN_CREATED'
  | 'ACK_QUEUED'
  | 'ACK_DELIVERED'
  | 'RUN_TRANSITION'
  | 'MILESTONE_CREATED'
  | 'MILESTONE_TRANSITION'
  | 'NOTIFICATION_QUEUED'
  | 'NOTIFICATION_DELIVERED'
  | 'NOTIFICATION_FAILED'
  | 'HEARTBEAT'
  | 'WATCHER_ALERT'
  | 'RUN_SUMMARY_RECOMPUTED';

export interface WorkLifecycleEvent {
  schema_version: typeof WORK_LIFECYCLE_SCHEMA_VERSION;
  event_id: string;
  run_id: string;
  milestone_id?: string | null;
  type: WorkLifecycleEventType;
  timestamp: string;
  from_state?: WorkRunState | WorkMilestoneState | null;
  to_state?: WorkRunState | WorkMilestoneState | null;
  notification_id?: string | null;
  actor: 'stickbot' | 'runtime' | 'watcher' | 'operator' | string;
  summary: string;
  data?: Record<string, unknown>;
}

export const WORK_MILESTONE_TRANSITIONS: Record<WorkMilestoneState, WorkMilestoneState[]> = {
  PENDING: ['RUNNING'],
  RUNNING: ['PASS', 'FAIL', 'HOLD', 'ABORT', 'SUPERSEDED'],
  PASS: [],
  FAIL: [],
  HOLD: [],
  ABORT: [],
  SUPERSEDED: []
};

export const WORK_RUN_TERMINAL_STATES: readonly WorkTerminalState[] = [
  'PASS',
  'FAIL',
  'HOLD',
  'ABORT',
  'SUPERSEDED'
] as const;
