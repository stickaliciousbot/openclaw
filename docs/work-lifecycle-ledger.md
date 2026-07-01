# OpenClaw Stickbot Work Lifecycle Ledger

Status: M0 contract draft  
Created: 2026-07-01 AEST  
Scope: lifecycle contract only; no runtime behavior changed in M0.

## 1. Objective

Build an automatic, durable, user-visible work lifecycle mechanism for Stickbot/OpenClaw so every meaningful unit of work is acknowledged when it begins and closed with an explicit terminal outcome:

- `PASS`
- `FAIL`
- `HOLD`
- `ABORT`
- `SUPERSEDED`

This must not depend on the model remembering to send updates. It must become infrastructure-level behavior enforced by runtime hooks, durable state, transition guards, and notification closeout validation.

Final invariant:

> If Stickbot starts meaningful work, the runtime owns the lifecycle. If the runtime owns the lifecycle, the ledger records it. If the ledger records a terminal transition, the notifier must attempt delivery. If delivery fails, the failure itself becomes visible state.

## 2. Non-goals and boundaries for M0

M0 is contract and baseline only.

M0 must not:

- mutate OpenClaw Gateway config;
- change model routes/defaults/fallbacks;
- mutate provider auth or secrets;
- mutate GE2, vector graph memory, vNext Mesh, TaskFlow, cron, or production runtime authority;
- install packages;
- apply to production;
- restart services.

M0 may:

- add design docs;
- add TypeScript contract/schema files not imported by runtime;
- add validation artifacts under `sharedspace/runtime-kernel-validation/work-lifecycle/`;
- add sidecar state samples under `state/work-lifecycle/`.

## 3. Lifecycle-managed work

Lifecycle-managed requests include:

- tool use;
- file edits;
- repo patches;
- long-running checks;
- TaskFlow/cron/watchers;
- production or service-affecting work;
- multi-step investigations;
- any request where Stick expects progress and closeout.

Trivial direct answers may create a lightweight ledger record, but do not require noisy visible acknowledgement.

## 4. Run states

| State | Meaning |
| --- | --- |
| `ACK_PENDING` | Run accepted but start acknowledgement has not yet been delivered or durably queued. |
| `RUNNING` | Work started and actively progressing. |
| `PASS` | Required gates passed and work completed successfully. |
| `FAIL` | Work completed or stopped because one or more hard gates failed. |
| `HOLD` | Cannot safely continue without user input, missing dependency, unavailable resource, or external blocker. |
| `ABORT` | Intentionally stopped by user request, policy boundary, timeout, cancellation, or runtime abort. |
| `SUPERSEDED` | Replaced by newer run and should no longer continue. |

`PENDING` is allowed for milestones before they begin. User-visible accepted runs should start as `ACK_PENDING`.

## 5. Milestone states and transition graph

Milestone states:

- `PENDING`
- `RUNNING`
- `PASS`
- `FAIL`
- `HOLD`
- `ABORT`
- `SUPERSEDED`

Allowed transition graph:

```text
PENDING -> RUNNING -> PASS | FAIL | HOLD | ABORT | SUPERSEDED
```

Rules:

- Terminal states are immutable.
- No milestone may move from one terminal state to another without creating a new transition record linked to the prior milestone.
- No required milestone may start until the prior required milestone has:
  - reached terminal state; and
  - had terminal notification delivered or durably queued.

## 6. Components

### 6.1 `WorkLifecycleLedger`

Responsibilities:

- Create durable run record when work begins.
- Create milestone records for major work phases.
- Enforce valid state transitions.
- Persist append-only lifecycle events.
- Derive aggregate run state.
- Trigger notification outbox entries.
- Validate closeout delivery.
- Prevent silent continuation after unclosed milestones.

### 6.2 `WorkNotifier`

Responsibilities:

- Send user-visible acknowledgement and terminal updates.
- Render standard templates.
- Redact secrets.
- Deduplicate repeated notices.
- Persist delivery attempts.
- Retry failed delivery.
- Mark notification delivery state.

### 6.3 `WorkCloseoutWatcher`

Responsibilities:

- Scan for stale `RUNNING` or `ACK_PENDING` work.
- Detect missing closeout.
- Detect notification delivery failure.
- Mark work `HOLD`, `FAIL`, or `ABORT` based on configured rule.
- Emit recovery notification if possible.
- Produce evidence artifacts for validation.

### 6.4 `WorkContext`

Responsibilities:

- Carry `run_id`, `milestone_id`, `user_turn_id`, `surface`, and `safety_boundary` through tool calls.
- Prevent tool runners, TaskFlow, cron jobs, or async callbacks from losing lifecycle state.
- Allow nested work without duplicate top-level notifications.

## 7. Durable state layout

Recommended root:

```text
state/work-lifecycle/
```

Structure:

```text
state/work-lifecycle/
  runs/<run_id>.json
  events/<run_id>.jsonl
  notifications/<run_id>.jsonl
  outbox/<notification_id>.json
  locks/<run_id>.lock
  indexes/active-runs.json
  indexes/by-user-turn.json
  indexes/by-surface.json
```

Validation mirror:

```text
sharedspace/runtime-kernel-validation/work-lifecycle/<run_id>/
  summary.json
  status.json
  events.jsonl
  notification-delivery.jsonl
  gate-results.json
```

Atomicity rules:

1. Write temp file.
2. `fsync`.
3. Rename into place.
4. Append event to JSONL.
5. Recompute run summary.

No in-memory-only lifecycle state is acceptable for work that uses tools, modifies files, calls external services, or runs longer than a trivial response.

## 8. Safety boundary

Every run must carry a safety boundary.

Minimum fields:

```json
{
  "mode": "read_only | repo_patch | local_runtime | production_apply | watcher",
  "allowed_mutations": [],
  "forbidden_mutations": [],
  "requires_operator_approval": [],
  "rollback_required": true,
  "secrets_redaction_required": true
}
```

Hard gate:

- No notification may include secrets, tokens, auth material, raw private headers, or unredacted chat IDs.

## 9. Notification templates

### 9.1 Start acknowledgement

```text
RUNNING — <work title>
I’ve started work.
Scope:
• <short scope>
Safety boundary:
• Allowed: <allowed mutation classes>
• Not allowed without approval: <restricted mutation classes>
First checkpoint:
• <next milestone or validation target>
```

### 9.2 Terminal milestone update

```text
PASS — <milestone name>
Gates:
• <gate 1>: PASS
• <gate 2>: PASS
Artifacts:
• <path 1>
• <path 2>
Next:
• <next milestone>
Safety boundary:
• <unchanged / changed with reason>
```

### 9.3 Failure update

```text
FAIL — <milestone name>
Failed gates:
• <gate>: <reason>
Evidence:
• <artifact path>
• <log path>
Action taken:
• <rollback / no mutation / stopped before apply>
Next:
• <recommended next step>
Safety boundary:
• <what was protected>
```

### 9.4 Hold update

```text
HOLD — <milestone name>
Blocked on:
• <missing input/resource/approval/dependency>
Current state:
• <what completed>
• <what did not run>
Needed from operator:
• <specific ask>
Safety boundary:
• No further mutation will occur until resumed.
```

### 9.5 Abort update

```text
ABORT — <milestone name>
Reason:
• <user cancellation / timeout / policy boundary / superseded run / runtime stop>
State:
• <what was completed>
• <what was skipped>
Artifacts:
• <paths>
Safety boundary:
• <rollback/no mutation/remaining risk>
```

## 10. Hook map

### 10.1 Inbound message router

When Stickbot receives a lifecycle-managed request:

1. Classify whether lifecycle-managed.
2. Create `run_id`.
3. Persist run in `ACK_PENDING`.
4. Send acknowledgement or durable notification outbox record.
5. Transition to `RUNNING`.

### 10.2 Tool runner

Before first tool side effect:

```text
work_ack_delivered_or_durably_queued == true
```

For each tool phase:

1. Create/attach milestone.
2. Mark `RUNNING`.
3. On success, mark `PASS` if gates pass.
4. On exception, mark `FAIL` or `ABORT`.
5. Emit terminal notification.

### 10.3 Reply dispatcher

Before final response:

```text
no_required_milestone_left_unclosed == true
```

If final response is generated while required milestone is still `RUNNING`, dispatcher must either close it or mark run `HOLD` with `INCOMPLETE_CLOSEOUT`.

### 10.4 TaskFlow / cron / watcher

Long jobs get:

- `run_id`
- `watcher_id`
- `heartbeat_path`
- `expected_closeout_path`
- `notification_outbox_path`

Watcher emits `RUNNING` heartbeat, then `PASS`/`FAIL`/`HOLD`/`ABORT` independent of model memory.

### 10.5 Error boundary

Unhandled exception behavior:

1. Mark current milestone `FAIL`.
2. Mark run `FAIL`.
3. Write evidence.
4. Attempt notification.
5. If notification fails, spool outbox and mark `CLOSEOUT_NOT_DELIVERED`.

## 11. GE2 / vector graph memory / vNext Mesh boundary

Use existing robust delivery infrastructure as **pattern and evidence surfaces**, not mutation targets during M0-M8.

Rules:

- Do not mutate GE2 registry, command surfaces, or plugin lifecycle while implementing sidecar ledger.
- Do not promote memory/vector graph artifacts as a side effect.
- Do not mutate vNext Mesh route authority, cache, fallback chain, or semantic gate authority.
- If a core capability is missing, implement a temporary sidecar and document the gap for a later vNext_2 upgrade.

Potential later integrations after sidecar proof:

- GE2: native operator command/status surface for lifecycle inspection.
- Vector graph memory: durable retrieval of prior lifecycle incidents and recurring failure classes, read-only at first.
- vNext Mesh: bounded lifecycle status Q&A / proposal drafting using approved lifecycle artifacts, not action authority.
- TaskFlow: durable orchestration binding for long-running lifecycle-managed jobs.

## 12. Anti-spam and event torrent control

Ledger records everything. Notifier surfaces only:

- start acknowledgement;
- required milestone terminal states;
- holds;
- aborts;
- final run closeout;
- long-running heartbeat summaries at configured intervals.

Terminal `FAIL`, `HOLD`, and `ABORT` are never suppressed.

Deduplication key:

```text
<run_id>:<milestone_id>:<status>:<surface>
```

Grouping allowed only if:

- same parent milestone;
- none failed;
- summary delivered before next required milestone starts;
- artifacts remain available.

## 13. Hard validation gates

### Group A — Ledger correctness

- `A1_SCHEMA_VALID`
- `A2_ATOMIC_WRITE`
- `A3_APPEND_ONLY_EVENTS`
- `A4_VALID_TRANSITIONS_ONLY`
- `A5_AGGREGATE_STATUS_CORRECT`
- `A6_IDEMPOTENT_REPLAY`

### Group B — Acknowledgement

- `B1_ACK_CREATED`
- `B2_ACK_BEFORE_TOOL_SIDE_EFFECT`
- `B3_ACK_TEMPLATE_VALID`
- `B4_ACK_DEDUPED`

### Group C — Terminal closeout

- `C1_TERMINAL_REQUIRED`
- `C2_TERMINAL_NOTIFICATION_REQUIRED`
- `C3_CLOSEOUT_DELIVERED`
- `C4_NO_NEXT_WITHOUT_CLOSEOUT`
- `C5_FAILURE_NOT_SUPPRESSED`

### Group D — Long-running work

- `D1_HEARTBEAT_WRITTEN`
- `D2_STALE_RUN_DETECTED`
- `D3_TIMEOUT_TO_HOLD_OR_ABORT`
- `D4_RESTART_SURVIVAL`
- `D5_WATCHER_CLOSEOUT`

### Group E — Notification reliability

- `E1_OUTBOX_PERSISTED`
- `E2_RETRY_SAFE`
- `E3_SURFACE_FAILURE_RECORDED`
- `E4_SECRET_REDACTION`
- `E5_OPERATOR_VISIBLE_FALLBACK`

### Group F — Regression protection

- `F1_EXISTING_TESTS_PASS`
- `F2_FOCUSED_TESTS_PASS`
- `F3_STATIC_CHECKS_PASS`
- `F4_NO_ROUTE_DRIFT`
- `F5_NO_MEMORY_PROMOTION`
- `F6_ROLLBACK_READY`

## 14. Milestones

Build order:

1. M0 Contract and baseline.
2. M1 Durable ledger store.
3. M2 FSM and status aggregation.
4. M3 Start acknowledgement hook.
5. M4 Terminal notification hook.
6. M5 No-next-milestone guard.
7. M6 Long-running runner and closeout watcher.
8. M7 CLI/UI status surface.
9. M8 Failure injection harness.
10. M9 Observe-only canary.
11. M10 Enforced canary.
12. M11 Production rollout.

Do not start with notification templates alone. That recreates the original failure mode: rule without enforcement.

## 15. Rollback design

Rollback disables enforcement without deleting evidence.

Observe-only rollback:

```json
{
  "work_lifecycle": {
    "enabled": true,
    "mode": "observe_only",
    "enforce_ack_before_tool": false,
    "enforce_closeout_before_next": false
  }
}
```

Emergency disable:

```json
{
  "work_lifecycle": { "enabled": false }
}
```

Preserve:

- `state/work-lifecycle/`
- `sharedspace/runtime-kernel-validation/work-lifecycle/`

## 16. Definition of done

Complete only when:

1. Toolful work automatically creates durable run.
2. Start acknowledgement is automatic, templated, and deduped.
3. Milestones have enforced finite-state transitions.
4. `PASS`, `FAIL`, `HOLD`, and `ABORT` terminal states generate notifications automatically.
5. Long-running jobs survive restart/context switch through heartbeat and watcher.
6. Notification delivery is tracked as state, not assumed.
7. Missing closeout becomes detectable failure condition.
8. CLI/UI can show active, failed, held, and unclosed work.
9. Existing OpenClaw route/model/memory authority is unchanged.
10. Regression and failure-injection tests pass.
11. Production rollout has rollback and closeout validation.
