# M11B Schema/Hook Readiness — Work Lifecycle Ledger Production Rollout

Status: `PASS_LOCAL_VALIDATED`
Closeout: `PASS_LOCAL_VALIDATED`
Preservation: `HOLD_BEFORE_SELECTIVE_COMMIT_PUSH`
Prepared at: 2026-07-01T12:21:30Z
M11 lifecycle state: `NOT_STARTED`
M11 apply approval: `NOT_READY`
M12 lifecycle state: `NOT_STARTED`

## Scope

M11B creates readiness only. It does not start M11 production apply, does not enable enforcement, does not change live Gateway behavior, and does not start M12.

## Current schema lookup result

First-class Gateway schema lookups performed during M11B:

| Path | Result |
| --- | --- |
| `work_lifecycle` | `config schema path not found` |
| `agents.defaults.hooks` | `config schema path not found` |
| `hooks` | schema-backed root exists |
| `hooks.internal` | schema-backed internal hook runtime settings exist |
| `hooks.internal.entries` | schema-backed internal hook entries object exists |
| `hooks.internal.entries.*` | schema-backed wildcard entry object exists with child `enabled` plus extensible fields |

## Does a schema-backed `work_lifecycle` config path exist?

No.

`work_lifecycle` is not a root Gateway config schema path, so M11 cannot be `CONFIG_FLAG_READY` using the originally proposed root path.

## Exact proposed config path, if available

The exact schema-backed Gateway location available for a future bounded internal hook is:

```json5
{
  hooks: {
    internal: {
      enabled: true,
      entries: {
        "work-lifecycle-production-canary": {
          enabled: true,
          mode: "enforce_canary",
          scope: "production_canary",
          canaryOwner: "stickbot",
          productionPromotion: false,
          requireTerminalCloseout: true,
          requireDeliveryState: true,
          suppressFailHoldAbort: false,
          allowRuntimeSend: false
        }
      }
    }
  }
}
```

This is a future proposal only. M11B did not write this config and did not enable it.

## Exact bounded runtime hook point, if needed

Implemented local readiness scaffold:

- config/schema helper: `src/work-lifecycle/work-runtime-hook-config.ts`
- bounded canary adapter: `src/work-lifecycle/work-runtime-canary-hook.ts`
- focused test/evidence generator: `src/work-lifecycle/work-runtime-canary-hook.test.mjs`

Future live runtime import point still needs separate M11 production-apply approval. The intended boundary is the accepted-work / before-next-milestone / before-terminal-closeout decision point for a production canary lane only, not global runtime execution.

No live runtime path imports these files in M11B.

## Exact files that changed

M11B implementation/readiness files:

- `src/work-lifecycle/work-runtime-hook-config.ts`
- `src/work-lifecycle/work-runtime-canary-hook.ts`
- `src/work-lifecycle/work-runtime-canary-hook.test.mjs`

M11B evidence files:

- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/M11B_SCHEMA_HOOK_READINESS.md`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11b-status.json`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11b-summary.json`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11b-gate-results.json`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11b-evidence_manifest.json`

M11B sidecar state files:

- `state/work-lifecycle/runs/work_20260701T122100Z_lifecycle_ledger_m11b.json`
- `state/work-lifecycle/events/work_20260701T122100Z_lifecycle_ledger_m11b.jsonl`

## Implementation type

`schema+hook`

Details:

- Schema-backed Gateway root for original `work_lifecycle.*`: unavailable.
- Schema-backed generic internal hook surface: available at `hooks.internal.entries.*`.
- Project-local Work Lifecycle config schema/helper added for the exact canary entry shape.
- Project-local bounded runtime canary adapter added but not imported by live runtime.

## Disabled-by-default safety model

Default behavior with `{}` config:

```json
{
  "action": "NOOP",
  "enforcementActive": false,
  "allowed": true,
  "reason": "WORK_LIFECYCLE_INTERNAL_HOOK_DISABLED_BY_DEFAULT",
  "mutation": false,
  "externalSend": false,
  "productionPromotion": false
}
```

Additional safety properties:

- Both `hooks.internal.enabled === true` and `hooks.internal.entries.work-lifecycle-production-canary.enabled === true` are required before enforcement can activate.
- Out-of-scope events return `NOOP`.
- Scope must be exactly `production_canary`.
- Owner must be exactly `stickbot`.
- `productionPromotion` must remain `false`.
- `allowRuntimeSend` must remain `false`.
- `suppressFailHoldAbort` must remain `false`.
- Adapter returns decisions only; it does not mutate Gateway/config/state, send Telegram, call providers, restart services, or promote runtime behavior.

## How M11 canary would later enable enforcement

Later M11 canary, after separate approval only, would need to:

1. Preserve current head and rollback package.
2. Import `src/work-lifecycle/work-runtime-canary-hook.ts` into a reviewed bounded production-canary decision point.
3. Write only the approved `hooks.internal.*` config entry or equivalent approved activation surface.
4. Keep `productionPromotion: false` and `allowRuntimeSend: false`.
5. Run post-apply smoke proving:
   - missing closeout is held;
   - valid closeout is allowed;
   - terminal delivery state cannot be assumed;
   - FAIL/HOLD/ABORT are not suppressed;
   - no provider/auth/route/memory/Telegram/service mutation occurred.

M11B did not perform any of those apply steps.

## Rollback implications

M11B rollback is ordinary repo/workspace rollback only because there was no production apply and no live config mutation.

If M11B files are not preserved, rollback is simply to discard these files:

```sh
git checkout -- \
  src/work-lifecycle/work-runtime-hook-config.ts \
  src/work-lifecycle/work-runtime-canary-hook.ts \
  src/work-lifecycle/work-runtime-canary-hook.test.mjs \
  sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/M11B_SCHEMA_HOOK_READINESS.md \
  sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11b-status.json \
  sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11b-summary.json \
  sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11b-gate-results.json \
  sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11b-evidence_manifest.json \
  state/work-lifecycle/runs/work_20260701T122100Z_lifecycle_ledger_m11b.json \
  state/work-lifecycle/events/work_20260701T122100Z_lifecycle_ledger_m11b.jsonl
```

Do not restart services for M11B rollback.

## Validation commands

Focused validation executed:

```sh
node --experimental-strip-types --test src/work-lifecycle/work-runtime-canary-hook.test.mjs
```

Result:

```text
1..1
# tests 1
# pass 1
# fail 0
```

Recommended readback validation:

```sh
set -euo pipefail

node --experimental-strip-types --test src/work-lifecycle/work-runtime-canary-hook.test.mjs

grep -RIn 'M11B_SCHEMA_OR_HOOK_SCAFFOLD_VALIDATION_PASS\|M11B_DISABLED_BY_DEFAULT_PASS\|M11B_NO_LIVE_ENFORCEMENT_WITHOUT_FLAG_PASS\|M11B_REDACTION_SCAN_PASS\|M11B_BOUNDARY_CHECK_FILES_SCOPED' \
  sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11b-gate-results.json \
  sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11b-summary.json \
  state/work-lifecycle/runs/work_20260701T122100Z_lifecycle_ledger_m11b.json

printf 'M11B_READBACK_VALIDATION_PASS\n'
```

## Redaction scan

M11B test includes a bounded redaction sentinel check across generated M11B evidence/state artifacts for raw Telegram id/token/API-key-shaped strings. Result:

`M11B_REDACTION_SCAN_PASS`

The artifacts use redacted markers only:

- `telegram:direct:sha256-redacted`
- `telegram:turn:sha256-redacted`

## Boundary check

`M11B_BOUNDARY_CHECK_FILES_SCOPED`: `PASS`

Boundary readback:

- production apply: false
- production promotion: false
- production mutation: false
- live Gateway behavior changed: false
- config mutation: false
- route/provider/auth/memory mutation: false
- service restart: false
- Telegram send from code/runtime: false
- provider/message API call: false
- CLI registration change: false
- M11 production apply approval requested: false
- M12 started: false

## Required gates

| Gate | Status |
| --- | --- |
| `M11B_SCHEMA_OR_HOOK_SCAFFOLD_VALIDATION_PASS` | `PASS` |
| `M11B_DISABLED_BY_DEFAULT_PASS` | `PASS` |
| `M11B_NO_LIVE_ENFORCEMENT_WITHOUT_FLAG_PASS` | `PASS` |
| `M11B_REDACTION_SCAN_PASS` | `PASS` |
| `M11B_BOUNDARY_CHECK_FILES_SCOPED` | `PASS` |

## Remaining blockers

Before M11 production canary apply can be requested:

1. Identify and review the exact live runtime import point for accepted-work / next-milestone / terminal-closeout decisions.
2. Prepare a concrete M11 apply command limited to that import point and the approved `hooks.internal.*` entry.
3. Prepare a concrete rollback package and rollback command for the selected import path.
4. Confirm whether the live import/config activation requires Gateway restart; if yes, request separate restart approval and health gates.
5. Prepare post-apply smoke commands against the real canary lane.
6. Keep real Telegram/runtime sends separately approved; default delivery remains durable state only.

## Recommendation

`BOUNDED_HOOK_READY`

Rationale:

- `CONFIG_FLAG_READY` is not valid because `work_lifecycle` is not a Gateway schema path.
- `HOLD_DESIGN_REQUIRED` is no longer necessary for local readiness because a schema-backed generic internal hook surface exists and a disabled-by-default bounded adapter now validates locally.
- M11 production apply is still `NOT_READY` until a live runtime import point and rollback/apply/smoke package are separately reviewed and approved.

## Closeout

M11B closeout: `PASS_LOCAL_VALIDATED`

Preservation status: `HOLD_BEFORE_SELECTIVE_COMMIT_PUSH`

No production apply, no enforcement enablement, no live Gateway behavior change, no config mutation, no restart, no Telegram send, no provider/message API call, no CLI registration, no production promotion, no M12 start.
