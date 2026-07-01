# M11 Production Rollout — Approval Request Only

Status: `APPROVAL_REQUEST_PREPARED_NOT_EXECUTED`
Prepared at: 2026-07-01T11:55:00Z
Prerequisite closeout: M10 `PASS_PUSHED`
Overall lifecycle state: `READY_FOR_M11_APPROVAL`
M11 lifecycle state: `NOT_STARTED`

## Explicit production-impact statement

M11 is the first production-affecting milestone for the Work Lifecycle Ledger line.

M11 must not execute without separate approval after this artifact is reviewed. This artifact is not approval to apply, restart, send Telegram, mutate Gateway/config/routes/providers/auth/memory, import runtime hooks, register CLI commands, or promote any behavior.

## Exact production rollout scope

Proposed M11 scope, pending separate approval:

1. Enable Work Lifecycle Ledger enforcement for a bounded production canary lane only.
2. Enforce lifecycle start/closeout state for real operator-visible work accepted by Stickbot in the approved canary lane.
3. Ensure required terminal outcomes cannot be silently skipped.
4. Ensure delivery state is recorded durably and never assumed.
5. Ensure `FAIL`, `HOLD`, and `ABORT` closeouts are never suppressed.
6. Emit production rollout evidence under `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/`.
7. Preserve rollback package before any apply.
8. Perform post-apply smoke only after the approved apply step.

Out of scope without separate approval:

- Broad/global rollout beyond the bounded M11 canary lane.
- Provider/model/auth/route/memory changes unrelated to Work Lifecycle Ledger enforcement.
- M12 or later promotion work.
- Any user-facing Telegram send from implementation code/runtime beyond the explicitly approved closeout-delivery validation path.
- Any production apply not listed in this request.

## Exact config diff / enforcement flag path

Default config diff before M11 approval: none.

Required proposed enforcement flag path for M11 review:

```yaml
work_lifecycle:
  enforcement:
    enabled: true
    scope: "production_canary"
    canary_owner: "stickbot"
    production_promotion: false
    require_terminal_closeout: true
    require_delivery_state: true
    suppress_fail_hold_abort: false
```

Important: this path is proposed for approval review. Before M11 apply, the executor must prove the path is supported by Gateway config schema or project-local runtime source. If it is not supported exactly, M11 must HOLD and request a narrower schema-backed approval. Do not invent or apply an unverified Gateway config field.

Allowed config mutation, if separately approved:

- Only the `work_lifecycle.enforcement.*` path above.

Forbidden config mutation:

- Gateway routes.
- Provider config.
- Auth/secret profiles.
- Memory routing or memory stores.
- Model/fallback routing.
- Telegram provider config.
- Any unrelated Gateway/runtime/service config.

## Runtime hooks or CLI registration required?

Runtime hook import: expected to be required only if M11 production enforcement cannot operate through an already-present work-lifecycle hook point.

CLI registration: not expected and not approved by default.

Before apply, M11 must classify one of these exact modes:

1. `CONFIG_FLAG_ONLY`: no new runtime hook import, no CLI registration.
2. `BOUNDED_RUNTIME_HOOK`: imports an already-reviewed Work Lifecycle hook only for the approved canary lane.
3. `HOLD_SCHEMA_OR_HOOK_UNAVAILABLE`: no apply; request a narrower approval.

Any CLI registration change requires separate approval and is not included in this request.

## Exact files expected to change

Expected production rollout code/config files, subject to pre-apply source/schema proof:

- Work Lifecycle Ledger enforcement/runtime integration file, if required by mode.
- Work Lifecycle Ledger test file(s) for production canary enforcement.
- Gateway config or project-local config artifact only at `work_lifecycle.enforcement.*`, if schema/source-proven and separately approved.
- Evidence files under `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/`.
- Sidecar state under `state/work-lifecycle/` for the M11 run.

Files that must not change during M11 without separate approval:

- Provider/auth/secret files.
- Route/model/fallback config.
- Memory store/config files.
- Telegram provider config.
- CLI registration files.
- Systemd/service files.
- M8/M9/M10 evidence except read-only prerequisite checks.

## Exact services that would be restarted, if any

Default service restart: none.

If Gateway config/runtime hook activation requires a Gateway restart, M11 must HOLD before restart and request explicit restart approval with:

- pre-restart status;
- exact restart command/tool;
- rollback path;
- post-restart health checks;
- owner-visible closeout plan.

No service restart is approved by this artifact.

## Telegram / user-notification behavior

- Implementation code/runtime must not call Telegram directly.
- Delivery state must be durable and explicit: queued, simulated, sent by approved OpenClaw delivery surface, failed, or not sent.
- No Telegram send from code/runtime is approved by this artifact.
- If closeout-delivery validation requires an actual Telegram notification, M11 must request a separate explicit approval naming the delivery mechanism and message text.
- `FAIL`, `HOLD`, and `ABORT` terminal states must not be suppressed.

## Rollback package/path and rollback command

Rollback package path to prepare before any apply:

- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/rollback/`

Rollback package must contain:

- pre-apply config snapshot or config diff inverse;
- pre-apply git head;
- list of files changed by M11;
- any sidecar state quarantine instructions;
- post-rollback validation command output.

Rollback command placeholder pending exact apply mode:

```sh
set -euo pipefail
# If config flag applied: restore pre-apply config snapshot using the approved Gateway/config tool path.
# If code/hook applied: revert only the approved M11 commit or restore pre-apply artifact snapshot.
# Do not restart services unless separately approved.
printf 'M11_ROLLBACK_READY_OR_COMPLETED\n'
```

M11 must not apply unless a concrete rollback command is finalized for the selected apply mode.

## Pre-apply validation commands

Required before any production-affecting apply approval:

```sh
set -euo pipefail

# Verify prerequisites.
grep -RIn '"closeoutStatus": "PASS_PUSHED"' \
 sharedspace/runtime-kernel-validation/work-lifecycle/m10-enforced-canary/summary.json \
 sharedspace/runtime-kernel-validation/work-lifecycle/m9-observe-only-canary/summary.json \
 sharedspace/runtime-kernel-validation/work-lifecycle/m8-failure-injection/summary.json

# Verify focused tests.
node --experimental-strip-types --test src/work-lifecycle/work-enforced-canary.test.mjs

# Verify no secret sentinels in M11 files.
grep -RIn --exclude-dir=.git --exclude='*.lock' --exclude='package-lock.json' \
 -E '<OWNER_APPROVED_SECRET_SENTINEL_PATTERN>' \
 src/work-lifecycle \
 sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout \
 state/work-lifecycle \
 && { echo 'M11_REDACTION_SCAN_FAIL'; exit 1; } || true

git diff --check
printf 'M11_PRE_APPLY_VALIDATION_PASS\n'
```

The literal secret-sentinel expression is intentionally represented as `<OWNER_APPROVED_SECRET_SENTINEL_PATTERN>` here so this approval artifact does not self-match scans that include its own directory. The actual execution approval must provide or reuse the owner-approved literal scan expression.

## Apply command

No apply command is approved by this artifact.

Apply command template, only after separate approval and only after exact mode is selected:

```sh
set -euo pipefail
# 1. Reconfirm branch/head and clean staged scope.
# 2. Apply only the approved M11 work_lifecycle enforcement flag/path and/or bounded hook change.
# 3. Do not mutate routes/providers/auth/memory/Telegram/service config.
# 4. Do not restart services unless separately approved.
printf 'M11_APPLY_COMPLETE_PENDING_SMOKE\n'
```

## Post-apply smoke commands

Required after any approved M11 apply:

```sh
set -euo pipefail

# Verify Gateway/service health only if apply touched a live runtime surface.
# Verify lifecycle enforcement blocks missing closeout.
# Verify lifecycle enforcement permits valid closeout path.
# Verify FAIL/HOLD/ABORT are not suppressed.
# Verify delivery state is explicit and not assumed.
# Verify no route/provider/auth/memory mutation occurred.
printf 'M11_POST_APPLY_SMOKE_PASS\n'
```

Exact smoke commands must be finalized after the selected apply mode is known.

## Closeout-delivery validation

M11 must validate closeout delivery as state first:

- closeout event appended;
- terminal outcome recorded;
- delivery status explicit;
- delivery not assumed;
- failed delivery remains visible and does not suppress `FAIL`, `HOLD`, or `ABORT`.

If owner approves real notification delivery, validation must also record:

- channel;
- target class redacted;
- message id or redacted delivery id;
- timestamp;
- delivery status;
- failure handling.

No actual Telegram send is approved by this artifact.

## Hard abort triggers

Abort M11 immediately if any occur:

- Gateway route/provider/auth/memory mutation outside approved `work_lifecycle.enforcement.*` path.
- Secret/redaction scan hit.
- Service restart attempted without separate approval.
- Telegram send from code/runtime without separate approval.
- Provider/message API call from implementation code.
- Production promotion beyond bounded M11 canary lane.
- Runtime hook import outside approved canary/hook path.
- CLI registration change.
- M8, M9, or M10 not `PASS_PUSHED`.
- Rollback package missing or incomplete before apply.
- Scope cannot be proven production-canary-only.
- M12 or promotion work starts.

## Expected evidence paths

- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/APPROVAL_REQUEST.md`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/pre-apply-validation.json`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/status.json`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/summary.json`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/gate-results.json`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/evidence_manifest.json`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/rollback/`
- `state/work-lifecycle/runs/<m11-run-id>.json`
- `state/work-lifecycle/events/<m11-run-id>.jsonl`

## Safety-boundary readback required

M11 may pass only if all read back exactly:

- `firstProductionAffectingMilestone`: true
- `productionPromotion`: false
- `productionCanaryOnly`: true
- `configDiffLimitedToWorkLifecycleEnforcement`: true or `configDiff`: `none`
- `runtimeHookImport`: false unless separately approved and bounded
- `cliRegistrationChange`: false
- `gatewayRoutesMutation`: false
- `providerMutation`: false
- `authMutation`: false
- `memoryMutation`: false
- `serviceRestart`: false unless separately approved and evidenced
- `telegramSendFromCodeRuntime`: false
- `providerMessageApiCall`: false
- `productionApplyApprovedSeparately`: true before apply
- `rollbackPackageReady`: true before apply
- `m8TerminalState`: `PASS_PUSHED`
- `m9TerminalState`: `PASS_PUSHED`
- `m10TerminalState`: `PASS_PUSHED`
- `m12Started`: false

## Terminal states

- `HOLD_APPROVAL_REQUIRED`: this artifact is prepared but M11 execution is not approved.
- `PASS_LOCAL_VALIDATED`: pre-apply validation passes but production apply not yet performed.
- `HOLD_BEFORE_PRODUCTION_APPLY`: pre-apply ready, waiting for explicit apply approval.
- `PASS_APPLIED`: approved apply and post-apply smoke pass, but not yet selectively preserved.
- `HOLD_BEFORE_SELECTIVE_COMMIT_PUSH`: evidence exists but not preserved.
- `PASS_PUSHED`: only after separate selective commit/push approval.
- `FAIL`: validation/smoke/boundary gate fails.
- `ABORT`: hard abort trigger fires.
- `HOLD_APPROVAL_TRANSPORT_BLOCKED`: approval/execution blocked by approval transport.

## Current execution readback

- M11 started: no.
- M11 production apply executed: no.
- Runtime/config/service mutation: no.
- Service restarted: no.
- Telegram sent from code/runtime: no.
- Provider/message API call: no.
- Commit/push: no.
- M12/promotion work started: no.
