# OpenClaw Stickbot Work Lifecycle Ledger — Design / Implementation / Troubleshooting Notebook

Status: M0 contract local PASS; HOLD before M1 pending selective GitHub preservation.
Created: 2026-07-01 AEST
Owner context: Stick / Stickbot

## Intake protocol

- Read Stick's design feedback in chunks until the word `banana` appears.
- Persist each chunk before synthesis so no design detail is lost across context windows.
- Treat Stick's feedback as strong recommendations, not immutable instructions; improve where useful and record any changes.
- Do not mutate GE2, vector graph memory, vNext Mesh, Gateway config, production runtime authority, or core delivery infrastructure during intake.
- If core runtime capability is missing, document the missing feature and design a temporary sidecar/broker for this milestone; defer proper core-system integration to a later vNext_2 upgrade.
- On each milestone PASS, push code/docs to GitHub before beginning the next milestone.

## Global artifacts required by Stick

Final deliverable must include an end-to-end design, implementation, troubleshooting, and repair guide detailed enough to rebuild from scratch if code is corrupted or lost. It should capture:

- design choices and philosophies;
- subsystem boundaries;
- implementation plan;
- validation gates;
- errors/bugs encountered;
- how errors were fixed;
- what core infrastructure was reused;
- what core infrastructure was missing;
- what temporary sidecars were introduced;
- what should later be promoted into vNext_2/core systems.

Errors/bugs must also be logged separately to lessons learned.

## Chunk 1 — 2026-07-01 14:38 AEST

### Stick's five operating requirements

1. Collaboration mode:
   - Treat Stick's feedback as recommendations.
   - Tweak/improve when I have better ideas.
   - Record all changes and deviations.

2. Documentation while building:
   - Continuously document and update docs during implementation.
   - Final artifact must be an end-to-end design/implementation/troubleshooting/repair guide.
   - Guide must be detailed enough to rebuild from scratch if code is corrupted/lost.
   - It should outline design choices, philosophies, errors made, and fixes.

3. Lessons learned:
   - Log errors or bugs found/made separately to lessons learned.

4. Robust delivery infrastructure integration:
   - Refresh understanding of GE2, vector graph memory, and vNext Mesh scalable system.
   - Alter plan to leverage these systems without mutating them.
   - If something is missing, note/document it and implement a temp sidecar to broker the missing function.
   - Sidecar must be properly smoked.
   - Missing function/use cases should be captured for a later vNext_2 core upgrade.
   - Separate concerns, enforce explicit boundaries, deliver the milestone.

5. GitHub fallback discipline:
   - On each milestone PASS, push code to GitHub repo before starting the next milestone.
   - Purpose: fallback and fast recovery if anything happens.

### Proposed system: OpenClaw Stickbot Work Lifecycle Ledger

#### Objective

Build an automatic, durable, user-visible work lifecycle mechanism for Stickbot/OpenClaw so every meaningful unit of work is acknowledged when it begins and closed with explicit terminal outcome:

- `PASS`
- `FAIL`
- `HOLD`
- `ABORT`
- `SUPERSEDED`

This must not depend on model memory/attention. It should be infrastructure-level behavior enforced by runtime hooks, durable state, transition guards, and notification closeout validation.

Design goal:

> No toolful, multi-step, long-running, production-affecting, or operator-requested task may silently start, silently stall, silently fail, or silently complete.

#### Core problem

Current state is a behavioral rule: acknowledge work and notify when done.

Problem: behavioral rule is fragile because it depends on model attention during:

- tool use;
- long process execution;
- event-heavy workflows;
- async completions;
- context switches/restarts.

Required shift:

```text
persona/instruction rule
→ runtime lifecycle mechanism + durable ledger + enforced notification closeout
```

#### Required user-visible states

Run states:

| State | Meaning |
| --- | --- |
| `ACK_PENDING` | Run accepted but start acknowledgement not yet delivered. |
| `RUNNING` | Work started and actively progressing. |
| `PASS` | Required gates passed and work completed successfully. |
| `FAIL` | Work completed/stopped because one or more hard gates failed. |
| `HOLD` | Cannot safely continue without user input, missing dependency, unavailable resource, or external blocker. |
| `ABORT` | Intentionally stopped by user request, policy boundary, timeout, cancellation, or runtime abort. |
| `SUPERSEDED` | Replaced by newer run; should no longer continue. |

Milestone states use the same terminal states, but a run can contain many milestones.

Allowed milestone transition graph:

```text
PENDING -> RUNNING -> PASS | FAIL | HOLD | ABORT | SUPERSEDED
```

### Initial Stickbot interpretation / improvements to consider later

- Add an explicit `PENDING` state for milestones and maybe runs before acceptance, but user-visible runs should enter `ACK_PENDING` immediately once accepted.
- Add `ACKED` as an event rather than a state, because a run can be `RUNNING` with `ackDelivered=true`.
- Add `STALE` or `WATCHDOG_ALERT` as derived health, not terminal state, to avoid state explosion.
- Treat notification delivery as a gate with its own evidence: `ackDelivery` and `terminalDelivery` should have message/channel/timestamp where available.
- A sidecar ledger can satisfy this without mutating core systems; later vNext_2 can absorb it into TaskFlow/runtime hooks.

## Chunk 2 — 2026-07-01 AEST through sentinel `banana`

Status: `BANANA_RECEIVED_INTAKE_COMPLETE`

Full chunk preserved verbatim-ish in separate artifact:

- `sharedspace/runtime-kernel-validation/work-lifecycle-ledger/intake-chunk-2-banana-20260701.md`

Key design requirements captured:

- No milestone may move from one terminal state to another without creating a new transition record.
- No required milestone may start until the prior required milestone has reached terminal state and terminal notification is delivered or durably queued.
- First-class runtime components:
  - `WorkLifecycleLedger`
  - `WorkNotifier`
  - `WorkCloseoutWatcher`
  - `WorkContext`
- Durable state root: `state/work-lifecycle/`.
- Validation mirror: `sharedspace/runtime-kernel-validation/work-lifecycle/<run_id>/`.
- Atomic writes: temp write, fsync, rename, append event, recompute summary.
- Notification delivery is state, not assumption.
- `FAIL`, `HOLD`, and `ABORT` terminal updates are never suppressed.
- GE2/vector graph memory/vNext Mesh are pattern/evidence surfaces only during sidecar milestones; no mutation until explicit later promotion.

## M0 — Contract and baseline

Status: `WORK_LIFECYCLE_M0_CONTRACT_LOCAL_PASS_REDACTION_REPAIRED_PUSH_PENDING`

M0 created contract-only artifacts with no runtime behavior change:

- `docs/work-lifecycle-ledger.md`
- `src/work-lifecycle/work-lifecycle.types.ts`
- `src/work-lifecycle/work-lifecycle.schema.ts`
- `state/work-lifecycle/runs/work_20260701T043800Z_lifecycle_ledger_m0.json`
- `state/work-lifecycle/events/work_20260701T043800Z_lifecycle_ledger_m0.jsonl`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m0-contract/gate-results.json`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m0-contract/summary.json`

M0 gates:

- `M0_G1` Contract names all states: PASS.
- `M0_G2` Contract defines transition graph: PASS.
- `M0_G3` Contract defines notification templates: PASS.
- `M0_G4` Contract defines safety boundary object: PASS.
- `M0_G5` No runtime behavior changed yet: PASS_WITH_SCOPE_NOTE.
- `M0_G6_REDACTION_READBACK` Sidecar state does not retain raw chat id: PASS_AFTER_REPAIR.
- `OWNER_GITHUB_PUSH_BEFORE_NEXT_MILESTONE`: PENDING.

Safety boundary held:

- No Gateway config mutation.
- No route/fallback/model mutation.
- No provider auth/secret mutation.
- No GE2 mutation.
- No vector graph memory mutation.
- No vNext Mesh mutation.
- No production apply or service restart.

### M0 bug/repair

Bug: initial sidecar run record stored raw Telegram chat id and a Telegram-shaped user turn id.

Repair:

- Replaced chat id with `telegram:direct:sha256-redacted` marker.
- Replaced user turn id with `telegram:turn:sha256-redacted` marker.
- Added append-only repair event `evt_20260701T045300Z_redaction_repair`.
- Updated gate/summary classification to include redaction repair.

Lesson:

- Lifecycle sidecar state should be treated as potentially exposed operator evidence. Redact direct identifiers in state samples and validation artifacts from the start; store reversible identifiers only behind approved runtime-private boundaries if later needed.

## Current hold before M1

M0 is locally complete but M1 must not start until selective GitHub preservation is done or Stick explicitly defers the GitHub-before-next-milestone rule.
