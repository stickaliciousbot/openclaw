# M11A Pre-Apply Classification — Work Lifecycle Ledger Production Rollout

Status: `HOLD_SCHEMA_OR_HOOK_UNAVAILABLE`
Prepared at: 2026-07-01T12:08:00Z
M11 lifecycle state: `NOT_STARTED`
M11 apply approval: `NOT_READY`
Overall lifecycle state: `READY_FOR_M11_PRE_APPLY_CLASSIFICATION`

## Classification summary

`applyMode`: `HOLD_SCHEMA_OR_HOOK_UNAVAILABLE`

M11 is not ready for production apply approval.

Reason:

- Gateway config schema lookup for `work_lifecycle` returned `config schema path not found`.
- Existing Work Lifecycle implementation modules are explicitly sidecar-only and warn not to import runtime paths until later milestones.
- No current verified live runtime hook point or schema-backed Gateway config path exists for `work_lifecycle.enforcement.*`.
- Applying production enforcement now would require broader design/integration work beyond M11 approval-request scope.

## Exact config diff

Current executable config diff: none.

```diff
(no config diff)
```

The previously proposed M11 path remains proposal-only and is not executable yet:

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

Classification: `HOLD_SCHEMA_OR_HOOK_UNAVAILABLE` because this path is not present in Gateway config schema and has not been proven as a project-local production runtime config path.

## Exact file-change list

Production apply file changes approved by this classification: none.

Expected file changes for this M11A classification package only:

- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/PRE_APPLY_CLASSIFICATION.md`
- `state/work-lifecycle/runs/work_20260701T120800Z_lifecycle_ledger_m11a.json`
- `state/work-lifecycle/events/work_20260701T120800Z_lifecycle_ledger_m11a.jsonl`

Files that would likely need future design/integration before M11 can become apply-ready:

- Gateway config schema/source for a supported `work_lifecycle.enforcement.*` path, or a project-local equivalent.
- A bounded runtime integration/hook file that imports existing sidecar modules safely into the approved production canary lane.
- Focused tests for that integration.
- Rollback package generated from the exact selected integration mode.

No provider/auth/route/memory/Telegram/systemd/service/CLI files are approved to change.

## Runtime hook requirement

Current classification: `BOUNDED_RUNTIME_HOOK_REQUIRED_BUT_UNAVAILABLE`

Existing sidecar modules:

- `src/work-lifecycle/work-start-hook.ts`
- `src/work-lifecycle/work-closeout-watcher.ts`
- `src/work-lifecycle/work-transition-guard.ts`
- `src/work-lifecycle/work-status-aggregate.ts`

These are useful implementation components, but they are marked sidecar-only and are not proven to be live runtime integration points.

M11 cannot proceed until a bounded production canary hook/integration path is designed, reviewed, validated, and separately approved.

## Service restart requirement

Current executable restart requirement: none.

M11A does not approve or require a service restart.

Future M11 production apply restart impact: not finalized. If a future bounded runtime hook or Gateway config path requires Gateway restart, M11 must HOLD and request separate restart approval with exact command/tool, rollback, and health checks.

## Notification / delivery behavior

Current executable behavior: state-only.

- No Telegram send from code/runtime.
- No provider/message API call.
- Delivery must remain durable state: queued/simulated/failed/not sent unless a separate real-delivery approval is granted.
- `FAIL`, `HOLD`, and `ABORT` closeouts must not be suppressed.

Future M11 closeout-delivery validation must remain state-first. Any real user notification requires separate approval naming delivery mechanism and message text.

## Rollback package path

Finalized rollback package path for this HOLD classification:

- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/rollback/m11a-hold-schema-or-hook-unavailable/`

Because no production apply is performed in M11A, rollback is a no-op verification package rather than a state restoration package.

## Rollback command

Concrete rollback command for M11A HOLD/no-apply state:

```sh
set -euo pipefail

# M11A performed no production apply and no runtime/config/service mutation.
# Rollback is therefore verification-only.

test ! -e sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/APPLIED

grep -RIn '"m11Status": "NOT_STARTED"\|M11 lifecycle state: `NOT_STARTED`' \
 sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout \
 state/work-lifecycle/runs/work_20260701T120800Z_lifecycle_ledger_m11a.json

printf 'M11A_ROLLBACK_NOOP_VERIFIED\n'
```

## Pre-apply validation commands

Concrete M11A pre-apply classification validation command:

```sh
set -euo pipefail

# Verify prerequisites remain pushed.
grep -RIn '"closeoutStatus": "PASS_PUSHED"' \
 sharedspace/runtime-kernel-validation/work-lifecycle/m10-enforced-canary/summary.json \
 sharedspace/runtime-kernel-validation/work-lifecycle/m9-observe-only-canary/summary.json \
 sharedspace/runtime-kernel-validation/work-lifecycle/m8-failure-injection/summary.json

# Verify current enforced canary still passes.
node --experimental-strip-types --test src/work-lifecycle/work-enforced-canary.test.mjs

# Verify M11A classification is HOLD, not apply-ready.
grep -RIn 'HOLD_SCHEMA_OR_HOOK_UNAVAILABLE' \
 sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/PRE_APPLY_CLASSIFICATION.md

# Verify no production apply marker exists.
test ! -e sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/APPLIED

# Secret sentinel scan must use the owner-approved literal expression at execution time.
# The literal expression is intentionally not stored here because this artifact may be scanned.

git diff --check

printf 'M11A_PRE_APPLY_CLASSIFICATION_VALIDATION_PASS\n'
```

## Apply command

Concrete M11A apply command:

```sh
set -euo pipefail
printf 'M11_APPLY_NOT_READY_HOLD_SCHEMA_OR_HOOK_UNAVAILABLE\n'
exit 2
```

No production apply command is available or approved in this classification.

## Post-apply smoke commands

Concrete M11A post-apply smoke command:

```sh
set -euo pipefail

# No production apply occurred. Smoke verifies no apply marker and prerequisites unchanged.
test ! -e sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/APPLIED

grep -RIn '"closeoutStatus": "PASS_PUSHED"' \
 sharedspace/runtime-kernel-validation/work-lifecycle/m10-enforced-canary/summary.json \
 sharedspace/runtime-kernel-validation/work-lifecycle/m9-observe-only-canary/summary.json \
 sharedspace/runtime-kernel-validation/work-lifecycle/m8-failure-injection/summary.json

printf 'M11A_NO_APPLY_SMOKE_PASS\n'
```

## Closeout-delivery validation command

Concrete M11A closeout-delivery validation command:

```sh
set -euo pipefail

grep -RIn '"closeoutStatus": "HOLD_SCHEMA_OR_HOOK_UNAVAILABLE"\|HOLD_SCHEMA_OR_HOOK_UNAVAILABLE' \
 sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/PRE_APPLY_CLASSIFICATION.md \
 state/work-lifecycle/runs/work_20260701T120800Z_lifecycle_ledger_m11a.json \
 state/work-lifecycle/events/work_20260701T120800Z_lifecycle_ledger_m11a.jsonl

printf 'M11A_CLOSEOUT_DELIVERY_STATE_VALIDATED_NO_RUNTIME_SEND\n'
```

Delivery behavior: state-only; no Telegram send from code/runtime.

## Hard abort triggers

M11A / future M11 must abort if any occur:

- Any Gateway/config/route/provider/auth/memory mutation before schema/source proof and separate approval.
- Service restart.
- Telegram send from code/runtime.
- Provider/message API call.
- Production apply/promotion.
- Runtime hook import into live path without bounded hook approval.
- CLI registration.
- Secret/redaction scan hit.
- M8, M9, or M10 not `PASS_PUSHED`.
- M12 starts.
- Scope cannot be proven production-canary-only.

## Expected evidence paths

M11A evidence paths:

- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/APPROVAL_REQUEST.md`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/PRE_APPLY_CLASSIFICATION.md`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/rollback/m11a-hold-schema-or-hook-unavailable/`
- `state/work-lifecycle/runs/work_20260701T120800Z_lifecycle_ledger_m11a.json`
- `state/work-lifecycle/events/work_20260701T120800Z_lifecycle_ledger_m11a.jsonl`

Future apply-ready M11 evidence paths remain pending until a supported schema/hook path exists.

## Safety-boundary readback

- `firstProductionAffectingMilestone`: true for M11, but M11A did not apply.
- `m11ApplyApproval`: `NOT_READY`
- `applyMode`: `HOLD_SCHEMA_OR_HOOK_UNAVAILABLE`
- `productionApply`: false
- `productionPromotion`: false
- `productionMutation`: false
- `configDiff`: none
- `configDiffLimitedToWorkLifecycleEnforcement`: false because no supported path exists yet
- `runtimeHookImport`: false
- `cliRegistrationChange`: false
- `gatewayRoutesMutation`: false
- `providerMutation`: false
- `authMutation`: false
- `memoryMutation`: false
- `serviceRestart`: false
- `telegramSendFromCodeRuntime`: false
- `providerMessageApiCall`: false
- `rollbackPackageReady`: true for no-op HOLD rollback
- `m8TerminalState`: `PASS_PUSHED`
- `m9TerminalState`: `PASS_PUSHED`
- `m10TerminalState`: `PASS_PUSHED`
- `m11Status`: `NOT_STARTED`
- `m12Started`: false

## Reason M11 is not ready for apply approval

M11 is not ready for apply approval because the production enforcement path is not executable yet:

1. The proposed `work_lifecycle.enforcement.*` config path is not present in Gateway schema.
2. Existing Work Lifecycle implementation is sidecar-only and not wired into a live runtime hook.
3. Runtime hook mode cannot be safely selected as `CONFIG_FLAG_ONLY` or `BOUNDED_RUNTIME_HOOK` without additional source/schema work.
4. Restart impact cannot be finalized until the integration path exists.
5. Production canary boundary cannot be proven executable without that integration path.

Terminal closeout: `HOLD_SCHEMA_OR_HOOK_UNAVAILABLE`.
