# Work Lifecycle Ledger Intake — Chunk 2 through `banana`

Captured: 2026-07-01 AEST
Status: `BANANA_RECEIVED_INTAKE_COMPLETE`

## Transition and sequencing rules

- No milestone may move from one terminal state to another without creating a new transition record.
- No required milestone may start until the prior required milestone has either:
  - reached a terminal state; and
  - had its terminal notification delivered or durably queued.

## 4. Architecture

### New component: `WorkLifecycleLedger`

Responsibilities:

- Create a durable run record when work begins.
- Create milestone records for major work phases.
- Enforce valid state transitions.
- Persist append-only lifecycle events.
- Derive aggregate run state.
- Trigger notification outbox entries.
- Validate closeout delivery.
- Prevent silent continuation after unclosed milestones.

### New component: `WorkNotifier`

Responsibilities:

- Send user-visible acknowledgement and terminal updates.
- Render standard templates.
- Redact secrets.
- Deduplicate repeated notices.
- Persist delivery attempts.
- Retry failed delivery.
- Mark notification delivery state.

### New component: `WorkCloseoutWatcher`

Responsibilities:

- Scan for stale `RUNNING` or `ACK_PENDING` work.
- Detect missing closeout.
- Detect notification delivery failure.
- Mark work `HOLD`, `FAIL`, or `ABORT` based on configured rule.
- Emit recovery notification if possible.
- Produce evidence artifacts for validation.

### New component: `WorkContext`

Responsibilities:

- Carry `run_id`, `milestone_id`, `user_turn_id`, `surface`, and `safety_boundary` through tool calls.
- Prevent tool runners, TaskFlow, cron jobs, or async callbacks from losing lifecycle state.
- Allow nested work without creating duplicate top-level notifications.

## 5. Durable State Layout

Recommended state root:

```text
state/work-lifecycle/
```

Recommended structure:

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

For OpenClaw validation-style artifacts, mirror summarized evidence into:

```text
sharedspace/runtime-kernel-validation/work-lifecycle/<run_id>/
  summary.json
  status.json
  events.jsonl
  notification-delivery.jsonl
  gate-results.json
```

### Atomicity rules

All writes must be atomic:

1. Write temp file.
2. `fsync`.
3. Rename into place.
4. Append event to JSONL.
5. Recompute run summary.

No in-memory-only lifecycle state is acceptable for work that uses tools, modifies files, calls external services, or runs longer than a trivial response.

## 6. Run Schema

Example schema instance:

```json
{
  "schema_version": "work_lifecycle.v1",
  "run_id": "work_20260701T142233Z_7f3a91",
  "parent_run_id": null,
  "user_turn_id": "turn_abc123",
  "surface": "telegram_direct",
  "chat_id": "redacted_or_hashed",
  "actor": "stickbot",
  "title": "Patch Stickbot acknowledgement mechanism",
  "requested_by": "operator",
  "status": "RUNNING",
  "started_at": "2026-07-01T14:22:33Z",
  "updated_at": "2026-07-01T14:24:10Z",
  "ended_at": null,
  "safety_boundary": {
    "mode": "repo_patch",
    "allowed_mutations": ["working_tree", "tests", "docs"],
    "forbidden_mutations": ["production_gateway_config", "secrets", "provider_auth", "memory_promotion"],
    "requires_operator_approval": ["production_apply", "service_restart", "network_exposure_change"]
  },
  "ack": {
    "required": true,
    "delivered": true,
    "delivered_at": "2026-07-01T14:22:35Z",
    "notification_id": "notif_001"
  },
  "milestones": [
    {
      "milestone_id": "M0",
      "name": "Create lifecycle ledger contract",
      "status": "PASS",
      "started_at": "2026-07-01T14:22:36Z",
      "ended_at": "2026-07-01T14:25:00Z",
      "hard_gates": [
        { "name": "schema_valid", "status": "PASS" }
      ],
      "artifacts": ["state/work-lifecycle/runs/work_20260701T142233Z_7f3a91.json"],
      "notification": { "required": true, "delivered": true }
    }
  ],
  "failure": null,
  "hold": null,
  "abort": null,
  "superseded_by": null
}
```

## 7. Notification Templates

### Start acknowledgement

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

### Terminal milestone update

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

### Failure update

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

### Hold update

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

### Abort update

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

## 8. Hook Points

### 8.1 Inbound message router

When Stickbot receives a user request:

1. Classify whether it is lifecycle-managed.
2. Create `run_id`.
3. Persist run in `ACK_PENDING`.
4. Send acknowledgement if required.
5. Transition to `RUNNING`.

Lifecycle-managed requests include:

- tool use;
- file edits;
- repo patches;
- long-running checks;
- TaskFlow/cron/watchers;
- production or service-affecting work;
- multi-step investigations;
- any request where the user expects progress and closeout.

Trivial direct answers may still create a lightweight ledger record, but do not need noisy visible acknowledgement.

### 8.2 Tool runner

Before first tool call:

Hard gate:

```text
work_ack_delivered_or_durably_queued == true
```

For each tool phase:

1. Create or attach to a milestone.
2. Mark `RUNNING`.
3. On tool success, mark milestone `PASS` if gates pass.
4. On exception, mark `FAIL` or `ABORT`.
5. Emit terminal notification.

### 8.3 Reply dispatcher

The reply dispatcher must check:

```text
no_required_milestone_left_unclosed == true
```

Before final response.

If final response is generated while a required milestone is still `RUNNING`, the dispatcher must either:

- close it properly; or
- mark the run `HOLD` with reason `INCOMPLETE_CLOSEOUT`.

### 8.4 TaskFlow / cron / watcher

Long jobs must not rely on chat context.

Each durable job gets:

```text
run_id
watcher_id
heartbeat_path
expected_closeout_path
notification_outbox_path
```

Watcher emits:

- `RUNNING` heartbeat;
- `PASS` if success gates pass;
- `FAIL` if gates fail;
- `HOLD` if external dependency blocks progress;
- `ABORT` if timeout, cancellation, or supersession occurs.

### 8.5 Error boundary

Every top-level runtime error must be caught by lifecycle-aware boundary.

Unhandled exception behavior:

1. Mark current milestone `FAIL`.
2. Mark run `FAIL`.
3. Write evidence.
4. Attempt notification.
5. If notification fails, spool outbox and mark `CLOSEOUT_NOT_DELIVERED`.

## 9. Anti-Spam and Event Torrent Control

Ledger records everything; notifier surfaces only:

- start acknowledgement;
- required milestone terminal states;
- holds;
- aborts;
- final run closeout;
- long-running heartbeat summaries at configured intervals.

Hard rule:

- Terminal `FAIL`, `HOLD`, and `ABORT` are never suppressed.

Deduplication key:

```text
<run_id>:<milestone_id>:<status>:<surface>
```

Notification grouping is allowed only if:

- grouped milestones belong to same parent milestone;
- none failed;
- summary delivered before next required milestone starts;
- artifact paths remain available.

## 10. Safety Boundary Readback

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

Examples:

### Read-only investigation

```json
{
  "mode": "read_only",
  "allowed_mutations": ["logs_read", "status_read"],
  "forbidden_mutations": ["file_write", "service_restart", "production_apply"],
  "requires_operator_approval": ["any_mutation"]
}
```

### Repo patch

```json
{
  "mode": "repo_patch",
  "allowed_mutations": ["working_tree", "tests", "local_artifacts"],
  "forbidden_mutations": ["production_gateway_config", "secrets", "provider_auth"],
  "requires_operator_approval": ["push", "production_apply", "service_restart"]
}
```

### Production apply

```json
{
  "mode": "production_apply",
  "allowed_mutations": ["approved_patch", "approved_restart"],
  "forbidden_mutations": ["secret_exposure", "unapproved_route_change"],
  "requires_operator_approval": ["apply", "promotion"],
  "rollback_required": true
}
```

Hard gate:

- No notification may include secrets, tokens, auth material, raw private headers, or unredacted chat IDs.

## 11. Hard Validation Gates

### Gate group A — Ledger correctness

| Gate | Requirement |
| --- | --- |
| `A1_SCHEMA_VALID` | Every run and event validates against schema. |
| `A2_ATOMIC_WRITE` | Simulated crash cannot leave partial JSON as current state. |
| `A3_APPEND_ONLY_EVENTS` | All transitions are represented in JSONL event history. |
| `A4_VALID_TRANSITIONS_ONLY` | Invalid transitions are rejected. |
| `A5_AGGREGATE_STATUS_CORRECT` | Run state correctly derives from milestone states. |
| `A6_IDEMPOTENT_REPLAY` | Replaying event log reconstructs same run summary. |

### Gate group B — Acknowledgement

| Gate | Requirement |
| --- | --- |
| `B1_ACK_CREATED` | Lifecycle-managed work creates `ACK_PENDING`. |
| `B2_ACK_BEFORE_TOOL_SIDE_EFFECT` | First tool side effect cannot occur before acknowledgement is delivered or durably queued. |
| `B3_ACK_TEMPLATE_VALID` | Ack includes scope, first checkpoint, and safety boundary. |
| `B4_ACK_DEDUPED` | Retries do not send duplicate start notices. |

### Gate group C — Terminal closeout

| Gate | Requirement |
| --- | --- |
| `C1_TERMINAL_REQUIRED` | Every required milestone reaches terminal state. |
| `C2_TERMINAL_NOTIFICATION_REQUIRED` | Terminal milestone creates notification outbox entry. |
| `C3_CLOSEOUT_DELIVERED` | Final terminal run notice is delivered or explicitly marked `CLOSEOUT_NOT_DELIVERED`. |
| `C4_NO_NEXT_WITHOUT_CLOSEOUT` | Next required milestone cannot start before prior closeout is delivered or queued. |
| `C5_FAILURE_NOT_SUPPRESSED` | `FAIL`, `HOLD`, and `ABORT` always surface. |

### Gate group D — Long-running work

| Gate | Requirement |
| --- | --- |
| `D1_HEARTBEAT_WRITTEN` | Long jobs write heartbeat. |
| `D2_STALE_RUN_DETECTED` | Watcher detects stale `RUNNING` jobs. |
| `D3_TIMEOUT_TO_HOLD_OR_ABORT` | Timed-out jobs become `HOLD` or `ABORT`, not silent. |
| `D4_RESTART_SURVIVAL` | Runtime restart does not lose active work state. |
| `D5_WATCHER_CLOSEOUT` | Watcher emits terminal notification independent of model memory. |

### Gate group E — Notification reliability

| Gate | Requirement |
| --- | --- |
| `E1_OUTBOX_PERSISTED` | Notification intent persists before delivery attempt. |
| `E2_RETRY_SAFE` | Delivery retry is idempotent. |
| `E3_SURFACE_FAILURE_RECORDED` | Telegram/UI delivery failure is recorded. |
| `E4_SECRET_REDACTION` | Notifications pass redaction tests. |
| `E5_OPERATOR_VISIBLE_FALLBACK` | Failed delivery is visible via CLI/UI status command. |

### Gate group F — Regression protection

| Gate | Requirement |
| --- | --- |
| `F1_EXISTING_TESTS_PASS` | Existing test suite remains green. |
| `F2_FOCUSED_TESTS_PASS` | New lifecycle tests pass. |
| `F3_STATIC_CHECKS_PASS` | Typecheck/lint/diff checks pass. |
| `F4_NO_ROUTE_DRIFT` | Gateway/default/fallback/model routes unchanged unless explicitly approved. |
| `F5_NO_MEMORY_PROMOTION` | No memory or semantic artifact promotion happens as a side effect. |
| `F6_ROLLBACK_READY` | Rollback path exists before production apply. |

## 12. Implementation Milestones

### M0 — Contract and Baseline

Goal: Define lifecycle contract, schemas, state locations, and hook map before changing runtime behavior.

Deliverables:

- `docs/work-lifecycle-ledger.md`
- `src/work-lifecycle/work-lifecycle.types.ts`
- `src/work-lifecycle/work-lifecycle.schema.ts`

Hard gates:

- `M0_G1` Contract names all states: `ACK_PENDING`, `RUNNING`, `PASS`, `FAIL`, `HOLD`, `ABORT`, `SUPERSEDED`.
- `M0_G2` Contract defines transition graph.
- `M0_G3` Contract defines notification templates.
- `M0_G4` Contract defines safety boundary object.
- `M0_G5` No runtime behavior changed yet.

Evidence:

- `sharedspace/runtime-kernel-validation/work-lifecycle/m0-contract/summary.json`

### M1 — Durable Ledger Store

Goal: Implement append-only event store and atomic run summary writer.

Deliverables:

- `src/work-lifecycle/work-ledger-store.ts`
- `src/work-lifecycle/work-ledger-replay.ts`
- `src/work-lifecycle/work-ledger-lock.ts`

Hard gates:

- `M1_G1` Atomic write test passes.
- `M1_G2` Event replay reconstructs summary.
- `M1_G3` Corrupt partial write is ignored or quarantined.
- `M1_G4` Concurrent writes are serialized by lock.
- `M1_G5` Schema validation rejects malformed records.

Focused tests:

- `corepack pnpm exec vitest run src/work-lifecycle/work-ledger-store.test.ts`
- `corepack pnpm exec vitest run src/work-lifecycle/work-ledger-replay.test.ts`

### M2 — FSM and Status Aggregation

Goal: Implement legal transition enforcement and aggregate run state derivation.

Deliverables:

- `src/work-lifecycle/work-fsm.ts`
- `src/work-lifecycle/work-status-aggregate.ts`

Hard gates:

- `M2_G1` Invalid transitions rejected.
- `M2_G2` Terminal states immutable.
- `M2_G3` `RUNNING` + failed required milestone derives `FAIL`.
- `M2_G4` `HOLD` milestone derives `HOLD` unless superseded or aborted.
- `M2_G5` `SUPERSEDED` links to replacement run.

Focused tests:

- `corepack pnpm exec vitest run src/work-lifecycle/work-fsm.test.ts`
- `corepack pnpm exec vitest run src/work-lifecycle/work-status-aggregate.test.ts`

### M3 — Start Acknowledgement Hook

Goal: Automatically acknowledge lifecycle-managed work before meaningful tool-side effects.

Likely hook areas, adapted to actual repo names:

- `src/auto-reply/`
- `src/reply/`
- `src/tools/`
- `src/gateway/`
- `src/taskflow/`

Deliverables:

- `src/work-lifecycle/work-context.ts`
- `src/work-lifecycle/work-start-hook.ts`
- `src/work-lifecycle/work-classifier.ts`

Hard gates:

- `M3_G1` Toolful user turn creates run in `ACK_PENDING`.
- `M3_G2` Ack notification is created before first tool side effect.
- `M3_G3` Ack includes scope, safety boundary, and first checkpoint.
- `M3_G4` Duplicate tool-start progress is not emitted.
- `M3_G5` If ack cannot be sent, notification is durably queued.

Focused tests:

- `corepack pnpm exec vitest run src/work-lifecycle/work-start-hook.test.ts`
- `corepack pnpm exec vitest run src/auto-reply/reply/dispatch-from-config.test.ts`

### M4 — Terminal Notification Hook

Goal: Every terminal milestone emits an automatic user-visible closeout.

Deliverables:

- `src/work-lifecycle/work-notifier.ts`
- `src/work-lifecycle/work-notification-template.ts`
- `src/work-lifecycle/work-notification-outbox.ts`

Hard gates:

- `M4_G1` `PASS` milestone creates terminal notification.
- `M4_G2` `FAIL` milestone creates terminal notification.
- `M4_G3` `HOLD` milestone creates terminal notification.
- `M4_G4` `ABORT` milestone creates terminal notification.
- `M4_G5` Notification includes gates, blockers, artifacts, next step, and safety boundary.
- `M4_G6` Notification redaction test passes.

Focused tests:

- `corepack pnpm exec vitest run src/work-lifecycle/work-notifier.test.ts`
- `corepack pnpm exec vitest run src/work-lifecycle/work-notification-template.test.ts`

### M5 — No-Next-Milestone Guard

Goal: Prevent silent continuation when prior milestone is unclosed.

Deliverable:

- `src/work-lifecycle/work-transition-guard.ts`

Hard gates:

- `M5_G1` Required milestone cannot start if prior required milestone is `RUNNING`.
- `M5_G2` Required milestone cannot start if prior terminal notice was neither delivered nor queued.
- `M5_G3` Guard failure marks run `HOLD` with `INCOMPLETE_CLOSEOUT`.
- `M5_G4` Guard failure emits `HOLD` notification.

Focused test:

- `corepack pnpm exec vitest run src/work-lifecycle/work-transition-guard.test.ts`

### M6 — Long-Running Runner and Closeout Watcher

Goal: Make long jobs survive context switches, restarts, and model distraction.

Deliverables:

- `src/work-lifecycle/work-closeout-watcher.ts`
- `src/work-lifecycle/work-heartbeat.ts`
- `scripts/work-lifecycle-closeout-check.ts`

Hard gates:

- `M6_G1` Long job writes heartbeat.
- `M6_G2` Watcher detects stale `ACK_PENDING`.
- `M6_G3` Watcher detects stale `RUNNING`.
- `M6_G4` Watcher marks stale work `HOLD` or `ABORT`.
- `M6_G5` Watcher emits notification independently of model.
- `M6_G6` Restart test preserves active run and emits closeout.

Focused test:

- `corepack pnpm exec vitest run src/work-lifecycle/work-closeout-watcher.test.ts`

### M7 — CLI / UI Status Surface

Goal: Give operator direct way to inspect work state even if chat delivery fails.

Proposed commands:

- `openclaw work status`
- `openclaw work status --run <run_id>`
- `openclaw work active`
- `openclaw work closeout-check`
- `openclaw work replay --run <run_id>`

Deliverables:

- `src/cli/work-status.ts`
- `src/cli/work-active.ts`
- `src/cli/work-closeout-check.ts`

Hard gates:

- `M7_G1` Active runs visible from CLI.
- `M7_G2` Failed notification delivery visible from CLI.
- `M7_G3` Replay command validates event log.
- `M7_G4` CLI does not expose secrets.

### M8 — Failure Injection Harness

Goal: Prove the mechanism works under bad conditions.

Failure cases:

- tool throws exception;
- process exits mid-run;
- notification transport unavailable;
- duplicate notification retry;
- stale `RUNNING` milestone;
- invalid transition attempt;
- event log partial write;
- user aborts run;
- newer run supersedes old run.

Deliverables:

- `scripts/work-lifecycle-failure-injection.ts`
- `src/work-lifecycle/work-lifecycle.fixture.test.ts`

Hard gates:

- `M8_G1` Every injected failure produces terminal state.
- `M8_G2` `FAIL`/`HOLD`/`ABORT` are not suppressed.
- `M8_G3` Notification outbox survives restart.
- `M8_G4` Event replay matches final summary.
- `M8_G5` No duplicate terminal notifications.

### M9 — Observe-Only Canary

Goal: Run lifecycle ledger in observe-only mode without blocking existing behavior.

Config:

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

Duration:

- Minimum: 2 hours or 25 lifecycle-managed turns, whichever gives better coverage.

Hard gates:

- `M9_G1` 100% of toolful turns create run records.
- `M9_G2` 100% of terminal outcomes are classified.
- `M9_G3` Missing closeouts are detected.
- `M9_G4` No user-facing duplicate storm.
- `M9_G5` No Gateway route drift.
- `M9_G6` No production mutation.

Pass condition:

- Observe-only canary may pass with detected gaps only if all gaps are recorded and no runtime regression occurs.

### M10 — Enforced Canary

Goal: Turn on hard enforcement for acknowledgement and terminal closeout.

Config:

```json
{
  "work_lifecycle": {
    "enabled": true,
    "mode": "enforced",
    "enforce_ack_before_tool": true,
    "enforce_closeout_before_next": true
  }
}
```

Hard gates:

- `M10_G1` Toolful work blocked until ack delivered or queued.
- `M10_G2` Next required milestone blocked until prior closeout delivered or queued.
- `M10_G3` Long-running stale work transitions to `HOLD`/`ABORT`.
- `M10_G4` `FAIL`/`HOLD`/`ABORT` messages delivered in Telegram direct chat.
- `M10_G5` Existing focused reply dispatch tests still pass.
- `M10_G6` No direct-provider, route, fallback, memory, or Gateway authority drift.

Minimum validation:

- `git diff --check`
- `corepack pnpm install --frozen-lockfile`
- `corepack pnpm exec tsc --noEmit`
- `corepack pnpm exec vitest run src/work-lifecycle`
- `corepack pnpm exec vitest run src/auto-reply/reply/dispatch-from-config.test.ts`

### M11 — Production Rollout

Goal: Enable enforced lifecycle closeout for Stickbot production paths.

Required before apply:

- rollback package exists;
- config diff reviewed;
- state root writable;
- notification surface tested;
- closeout watcher active;
- operator status command available.

Hard gates:

- `M11_G1` Pre-apply smoke PASS.
- `M11_G2` Rollback ready PASS.
- `M11_G3` Config mutation limited to `work_lifecycle` settings.
- `M11_G4` Gateway restart healthy.
- `M11_G5` Telegram direct-chat ack smoke PASS.
- `M11_G6` PASS closeout smoke PASS.
- `M11_G7` FAIL closeout smoke PASS.
- `M11_G8` HOLD closeout smoke PASS.
- `M11_G9` ABORT closeout smoke PASS.

Rollback trigger:

- `ACK_NOT_DELIVERED_AND_NOT_QUEUED`
- `CLOSEOUT_NOT_DELIVERED`
- `DUPLICATE_NOTIFICATION_STORM`
- `TOOL_RUN_BLOCKED_FALSE_POSITIVE`
- `GATEWAY_HEALTH_RED`
- `TELEGRAM_DIRECT_SESSION_BROKEN`
- `STATE_CORRUPTION`
- `SECRET_REDACTION_FAILURE`

## 13. Rollback Design

Rollback must disable enforcement without deleting ledger evidence.

Recommended rollback config:

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

Rollback must preserve:

- `state/work-lifecycle/`
- `sharedspace/runtime-kernel-validation/work-lifecycle/`

Do not delete evidence during rollback.

## 14. Definition of Done

Mechanism complete only when:

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

## 15. Recommended Build Order

Build sequence:

1. M0 Contract
2. M1 Durable ledger
3. M2 FSM
4. M3 Start ack hook
5. M4 Terminal notifier
6. M5 No-next guard
7. M6 Watcher/heartbeat
8. M7 CLI/UI status
9. M8 Failure injection
10. M9 Observe-only canary
11. M10 Enforced canary
12. M11 Production rollout

Do not start with notification template alone. That would recreate original problem: a rule without enforcement.

Core mechanism is ledger plus transition guard. Notifications are side effects of state transitions, not behavior model remembers.

## 16. Key Design Principle

Final invariant:

> If Stickbot starts meaningful work, the runtime owns the lifecycle. If the runtime owns the lifecycle, the ledger records it. If the ledger records a terminal transition, the notifier must attempt delivery. If delivery fails, the failure itself becomes visible state.

That is the difference between advice and infrastructure.

## Sentinel

`banana`

## Immediate directive after sentinel

Stick asked: revise or begin implementing.
