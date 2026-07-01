// OpenClaw Stickbot Work Lifecycle Ledger — M0 schema contract
// Contract-only artifact. No runtime behavior should import this before implementation milestones.

export const workLifecycleRunSchema = {
  $id: 'https://openclaw.local/schemas/work_lifecycle.v1.run.json',
  type: 'object',
  required: [
    'schema_version',
    'run_id',
    'parent_run_id',
    'user_turn_id',
    'surface',
    'chat_id',
    'actor',
    'title',
    'requested_by',
    'status',
    'started_at',
    'updated_at',
    'ended_at',
    'safety_boundary',
    'ack',
    'milestones',
    'failure',
    'hold',
    'abort',
    'superseded_by'
  ],
  additionalProperties: false,
  properties: {
    schema_version: { const: 'work_lifecycle.v1' },
    run_id: { type: 'string', pattern: '^work_[0-9TZ]+_[a-zA-Z0-9]+$' },
    parent_run_id: { anyOf: [{ type: 'string' }, { type: 'null' }] },
    user_turn_id: { anyOf: [{ type: 'string' }, { type: 'null' }] },
    surface: { type: 'string' },
    chat_id: { type: 'string' },
    actor: { type: 'string' },
    title: { type: 'string' },
    requested_by: { type: 'string' },
    status: { enum: ['ACK_PENDING', 'RUNNING', 'PASS', 'FAIL', 'HOLD', 'ABORT', 'SUPERSEDED'] },
    started_at: { type: 'string', format: 'date-time' },
    updated_at: { type: 'string', format: 'date-time' },
    ended_at: { anyOf: [{ type: 'string', format: 'date-time' }, { type: 'null' }] },
    safety_boundary: { $ref: '#/$defs/safetyBoundary' },
    ack: { $ref: '#/$defs/notificationState' },
    milestones: { type: 'array', items: { $ref: '#/$defs/milestone' } },
    failure: { anyOf: [{ $ref: '#/$defs/failure' }, { type: 'null' }] },
    hold: { anyOf: [{ $ref: '#/$defs/hold' }, { type: 'null' }] },
    abort: { anyOf: [{ $ref: '#/$defs/abort' }, { type: 'null' }] },
    superseded_by: { anyOf: [{ type: 'string' }, { type: 'null' }] }
  },
  $defs: {
    safetyBoundary: {
      type: 'object',
      required: [
        'mode',
        'allowed_mutations',
        'forbidden_mutations',
        'requires_operator_approval',
        'secrets_redaction_required'
      ],
      additionalProperties: false,
      properties: {
        mode: { enum: ['read_only', 'repo_patch', 'local_runtime', 'production_apply', 'watcher'] },
        allowed_mutations: { type: 'array', items: { type: 'string' } },
        forbidden_mutations: { type: 'array', items: { type: 'string' } },
        requires_operator_approval: { type: 'array', items: { type: 'string' } },
        rollback_required: { type: 'boolean' },
        secrets_redaction_required: { type: 'boolean' }
      }
    },
    notificationState: {
      type: 'object',
      required: ['required', 'delivered'],
      additionalProperties: false,
      properties: {
        required: { type: 'boolean' },
        delivered: { type: 'boolean' },
        delivered_at: { anyOf: [{ type: 'string', format: 'date-time' }, { type: 'null' }] },
        notification_id: { anyOf: [{ type: 'string' }, { type: 'null' }] },
        queued: { type: 'boolean' },
        closeout_not_delivered: { type: 'boolean' }
      }
    },
    gateResult: {
      type: 'object',
      required: ['name', 'status'],
      additionalProperties: false,
      properties: {
        name: { type: 'string' },
        status: { enum: ['PASS', 'FAIL', 'HOLD', 'SKIP'] },
        reason: { type: 'string' },
        evidence: { type: 'array', items: { type: 'string' } }
      }
    },
    milestone: {
      type: 'object',
      required: [
        'milestone_id',
        'name',
        'status',
        'required',
        'hard_gates',
        'artifacts',
        'notification'
      ],
      additionalProperties: false,
      properties: {
        milestone_id: { type: 'string' },
        name: { type: 'string' },
        status: { enum: ['PENDING', 'RUNNING', 'PASS', 'FAIL', 'HOLD', 'ABORT', 'SUPERSEDED'] },
        required: { type: 'boolean' },
        started_at: { anyOf: [{ type: 'string', format: 'date-time' }, { type: 'null' }] },
        ended_at: { anyOf: [{ type: 'string', format: 'date-time' }, { type: 'null' }] },
        hard_gates: { type: 'array', items: { $ref: '#/$defs/gateResult' } },
        artifacts: { type: 'array', items: { type: 'string' } },
        notification: { $ref: '#/$defs/notificationState' },
        superseded_by: { anyOf: [{ type: 'string' }, { type: 'null' }] }
      }
    },
    failure: {
      type: 'object',
      required: ['code', 'reason'],
      additionalProperties: false,
      properties: {
        code: { type: 'string' },
        reason: { type: 'string' },
        failed_gate: { type: 'string' },
        evidence: { type: 'array', items: { type: 'string' } }
      }
    },
    hold: {
      type: 'object',
      required: ['code', 'reason'],
      additionalProperties: false,
      properties: {
        code: { type: 'string' },
        reason: { type: 'string' },
        needed_from_operator: { type: 'string' },
        blocker_artifacts: { type: 'array', items: { type: 'string' } }
      }
    },
    abort: {
      type: 'object',
      required: ['code', 'reason'],
      additionalProperties: false,
      properties: {
        code: { type: 'string' },
        reason: { type: 'string' },
        requested_by: { enum: ['operator', 'runtime', 'policy', 'watcher'] }
      }
    }
  }
} as const;

export const workLifecycleEventSchema = {
  $id: 'https://openclaw.local/schemas/work_lifecycle.v1.event.json',
  type: 'object',
  required: ['schema_version', 'event_id', 'run_id', 'type', 'timestamp', 'actor', 'summary'],
  additionalProperties: false,
  properties: {
    schema_version: { const: 'work_lifecycle.v1' },
    event_id: { type: 'string' },
    run_id: { type: 'string' },
    milestone_id: { anyOf: [{ type: 'string' }, { type: 'null' }] },
    type: {
      enum: [
        'RUN_CREATED',
        'ACK_QUEUED',
        'ACK_DELIVERED',
        'RUN_TRANSITION',
        'MILESTONE_CREATED',
        'MILESTONE_TRANSITION',
        'NOTIFICATION_QUEUED',
        'NOTIFICATION_DELIVERED',
        'NOTIFICATION_FAILED',
        'HEARTBEAT',
        'WATCHER_ALERT',
        'RUN_SUMMARY_RECOMPUTED'
      ]
    },
    timestamp: { type: 'string', format: 'date-time' },
    from_state: { anyOf: [{ type: 'string' }, { type: 'null' }] },
    to_state: { anyOf: [{ type: 'string' }, { type: 'null' }] },
    notification_id: { anyOf: [{ type: 'string' }, { type: 'null' }] },
    actor: { type: 'string' },
    summary: { type: 'string' },
    data: { type: 'object' }
  }
} as const;
