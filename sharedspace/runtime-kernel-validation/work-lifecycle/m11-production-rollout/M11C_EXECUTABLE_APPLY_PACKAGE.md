# M11C Executable Production-Canary Apply Package — Work Lifecycle Ledger

Status: `HOLD_LIVE_HOOK_INSERTION_UNSAFE`
Prepared at: 2026-07-01T12:55:00Z
M11 readiness preservation: `PASS_PUSHED`
M11A: `HOLD_SCHEMA_OR_HOOK_UNAVAILABLE`
M11B: `PASS_LOCAL_VALIDATED` / `BOUNDED_HOOK_READY`
M11 apply approval: `NOT_READY`
M12: `NOT_STARTED`

## Executive classification

Terminal classification: `HOLD_LIVE_HOOK_INSERTION_UNSAFE`

M11C does **not** request M11 production apply approval.

Reason: M11B proved a disabled-by-default bounded adapter and a schema-backed generic hook-config surface, but M11C has not verified an exact live Gateway source insertion point where the adapter can be imported without changing live behavior or broadening scope. An executable production-canary package must not guess the runtime insertion path.

## Current baseline

- Branch: `stickbot/v3-selected-model-persona-injection`
- Preserved M11 readiness head: `a16b94a60a9be7ea0df3c0b09bd18c29f00e6756`
- Push range already preserved: `23b9635afbab91510f5b70187ca87d96b20116bb..a16b94a60a9be7ea0df3c0b09bd18c29f00e6756`
- Post-push local drift note: delayed inspection found `m11b-evidence_manifest.json` modified after push because the M11B test regenerated the manifest without `M11B_SCHEMA_HOOK_READINESS.md`; repaired locally by adding `READINESS_PATH` to the test's `evidencePaths` and rerunning the focused test. That follow-up repair is not part of the preserved M11 readiness commit yet.

## Current schema/config support

Known schema/config result from M11A/M11B evidence:

| Path | Result |
| --- | --- |
| `work_lifecycle` | `config schema path not found` |
| `agents.defaults.hooks` | `config schema path not found` |
| `hooks` | schema-backed root exists |
| `hooks.internal` | schema-backed internal hook runtime settings exist |
| `hooks.internal.entries` | schema-backed internal hook entries object exists |
| `hooks.internal.entries.*` | schema-backed wildcard entry object exists with child `enabled` plus extensible fields |

Conclusion: `CONFIG_FLAG_ONLY` remains unavailable for the original `work_lifecycle.enforcement.*` path.

## Exact live integration point

Verified exact live integration point: **none yet**.

Candidate semantic decision points remain:

1. accepted-work / request acceptance boundary;
2. before-next-milestone transition boundary;
3. before-terminal-closeout boundary.

However, M11C has not identified a concrete Gateway runtime file/function that can be changed with all of the following guarantees:

- disabled by default;
- gated to `hooks.internal.entries.work-lifecycle-production-canary` only;
- canary scoped to Stickbot production canary only;
- no Telegram/runtime send;
- no provider/message API call;
- no CLI registration;
- no route/provider/auth/memory mutation;
- no production promotion;
- no enforcement unless explicitly enabled later;
- no Gateway behavior change while disabled.

Because the exact live file/function is not verified, this package cannot be `PASS_APPLY_PACKAGE_READY`.

## Exact proposed file changes

M11C evidence-only file changes:

- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/M11C_EXECUTABLE_APPLY_PACKAGE.md`
- `state/work-lifecycle/runs/work_20260701T125500Z_lifecycle_ledger_m11c.json`
- `state/work-lifecycle/events/work_20260701T125500Z_lifecycle_ledger_m11c.jsonl`

Local M11B drift already present before M11C:

- `src/work-lifecycle/work-runtime-canary-hook.test.mjs`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11b-evidence_manifest.json`

Future production-canary apply file changes: **not finalized** because the exact live insertion point is not verified.

Expected future apply files, once verified separately:

- one exact Gateway runtime integration file: `TBD_BY_SOURCE_INSPECTION`;
- possibly one focused runtime integration test file: `TBD_BY_SOURCE_INSPECTION`;
- existing bounded adapter files already preserved in M11 readiness evidence: `src/work-lifecycle/work-runtime-canary-hook.ts` and `src/work-lifecycle/work-runtime-hook-config.ts`.

## Exact config diff

M11C config diff: none.

```diff
(no config diff)
```

Future candidate activation diff, **not approved and not ready**, would target the schema-backed hook surface only after the live insertion point is verified:

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

This candidate config is not an apply command and must not be written during M11C.

## Can integration remain disabled by default?

Design intent: yes.

Verified local adapter behavior from M11B:

- empty config returns `NOOP`;
- `hooks.internal.enabled=false` returns `NOOP` even when the entry is enabled;
- out-of-scope events return `NOOP`;
- enforcement decisions return decision objects only and do not mutate Gateway/config/state or send messages.

Unverified live-runtime property: whether importing/calling the adapter at the target Gateway insertion point creates any observable behavior change while disabled.

This unverified property is the reason for `HOLD_LIVE_HOOK_INSERTION_UNSAFE`.

## Rollback command

Concrete rollback command for M11C HOLD/no-apply state:

```sh
set -euo pipefail

# M11C performed no production apply, no config mutation, no live runtime import, and no service restart.
# Rollback is verification-only for the M11C evidence package.

test ! -e sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/M11C_APPLIED

grep -RIn 'HOLD_LIVE_HOOK_INSERTION_UNSAFE' \
  sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/M11C_EXECUTABLE_APPLY_PACKAGE.md \
  state/work-lifecycle/runs/work_20260701T125500Z_lifecycle_ledger_m11c.json \
  state/work-lifecycle/events/work_20260701T125500Z_lifecycle_ledger_m11c.jsonl

printf 'M11C_ROLLBACK_NOOP_VERIFIED\n'
```

Concrete production-apply rollback command: **not ready**, because the exact live integration file is unknown.

Rollback blocker classification: not `HOLD_ROLLBACK_NOT_READY` as the primary terminal class only because the earlier safety blocker is stricter: no verified live hook insertion point.

## Pre-apply validation command

Concrete M11C pre-apply validation command for the HOLD package:

```sh
set -euo pipefail

# Verify M8/M9/M10 prerequisites stayed preserved.
grep -RIn '"closeoutStatus": "PASS_PUSHED"' \
  sharedspace/runtime-kernel-validation/work-lifecycle/m8-failure-injection/summary.json \
  sharedspace/runtime-kernel-validation/work-lifecycle/m9-observe-only-canary/summary.json \
  sharedspace/runtime-kernel-validation/work-lifecycle/m10-enforced-canary/summary.json

# Verify M11 readiness preservation marker exists.
grep -RIn 'M11_PRODUCTION_ROLLOUT_READINESS_EVIDENCE_PRESERVATION\|M11 readiness preservation: `PASS_PUSHED`' \
  sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/M11C_EXECUTABLE_APPLY_PACKAGE.md \
  memory/2026-07-01.md

# Verify M11B adapter remains disabled-by-default locally.
node --experimental-strip-types --test src/work-lifecycle/work-runtime-canary-hook.test.mjs

# Verify M11C is HOLD, not apply-ready.
grep -RIn 'HOLD_LIVE_HOOK_INSERTION_UNSAFE' \
  sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/M11C_EXECUTABLE_APPLY_PACKAGE.md

# Verify no M11C apply marker exists.
test ! -e sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/M11C_APPLIED

git diff --check

printf 'M11C_PRE_APPLY_HOLD_VALIDATION_PASS\n'
```

## Apply command

Concrete M11C apply command:

```sh
set -euo pipefail
printf 'M11C_APPLY_NOT_READY_HOLD_LIVE_HOOK_INSERTION_UNSAFE\n'
exit 2
```

There is no concrete production apply command yet. This fails closed by design.

## Post-apply smoke command

Concrete M11C post-apply smoke command for HOLD/no-apply state:

```sh
set -euo pipefail

test ! -e sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/M11C_APPLIED

grep -RIn 'HOLD_LIVE_HOOK_INSERTION_UNSAFE' \
  sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/M11C_EXECUTABLE_APPLY_PACKAGE.md

node --experimental-strip-types --test src/work-lifecycle/work-runtime-canary-hook.test.mjs

printf 'M11C_NO_APPLY_SMOKE_PASS\n'
```

Future production smoke command remains blocked until the exact live insertion point is verified.

## Closeout-delivery validation command

Concrete M11C closeout-delivery validation command:

```sh
set -euo pipefail

grep -RIn '"closeoutStatus": "HOLD_LIVE_HOOK_INSERTION_UNSAFE"\|HOLD_LIVE_HOOK_INSERTION_UNSAFE' \
  sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/M11C_EXECUTABLE_APPLY_PACKAGE.md \
  state/work-lifecycle/runs/work_20260701T125500Z_lifecycle_ledger_m11c.json \
  state/work-lifecycle/events/work_20260701T125500Z_lifecycle_ledger_m11c.jsonl

printf 'M11C_CLOSEOUT_DELIVERY_STATE_VALIDATED_NO_RUNTIME_SEND\n'
```

Delivery behavior: state-only; no Telegram/runtime send.

## Redaction scan

Required redaction scan for M11C artifacts:

```sh
set -euo pipefail

python3 - <<'PY'
from pathlib import Path
paths = [
  'sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/M11C_EXECUTABLE_APPLY_PACKAGE.md',
  'state/work-lifecycle/runs/work_20260701T125500Z_lifecycle_ledger_m11c.json',
  'state/work-lifecycle/events/work_20260701T125500Z_lifecycle_ledger_m11c.jsonl',
]
for path in paths:
    text = Path(path).read_text(errors='ignore')
    for term in ['botToken', 'Authorization: Bearer', 'apiKey', 'OPENAI_API_KEY']:
        if term in text:
            raise SystemExit(f'M11C_REDACTION_SCAN_FAIL {path} {term}')
print('M11C_REDACTION_SCAN_PASS')
PY
```

## Boundary check

M11C boundary readback:

- production apply: false
- enforcement enablement: false
- live Gateway behavior change: false
- config mutation: false
- route/provider/auth/memory mutation: false
- service restart: false
- Telegram/runtime send: false
- provider/message API call: false
- CLI registration: false
- production promotion: false
- M11 apply approval request: false
- M12 start: false

## Remaining blockers

1. Verify exact Gateway runtime source insertion point by local source inspection.
2. Prove disabled import/call has no observable live behavior change when `hooks.internal` or the work-lifecycle entry is disabled.
3. Produce exact future apply file list with no `TBD_BY_SOURCE_INSPECTION` entries.
4. Produce exact production rollback command for the verified live integration file.
5. Produce exact production post-apply smoke commands against a real bounded canary lane.
6. Preserve or explicitly fold the local M11B manifest-generator repair before any apply-readiness commit/push.
7. Confirm whether the eventual live integration requires Gateway restart; if yes, request separate restart approval with health-based gates.

## Delayed source-search result

A delayed approved source-search command completed after M11C closeout with exit code `2`.

Observed output was partial and included only config/install-related hits such as:

- `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/plugins-install-command-BX6Dvw3G.js:... hooks: result.hooks`
- `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/config-IDJLYZjb.js:... manual:hooks:...`
- `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/installs-2yUCxgqb.js:... hooks: {`

Interpretation:

- The command likely failed because the packaged install has `dist/` but no readable `src/` tree at `/home/stickai/.npm-global/lib/node_modules/openclaw/src`.
- The partial hits do not identify an accepted-work, before-next-milestone, or before-terminal-closeout live Gateway runtime insertion point.
- Therefore this delayed evidence does not change the M11C terminal classification.

## Terminal closeout

M11C terminal classification: `HOLD_LIVE_HOOK_INSERTION_UNSAFE`

M11 production apply approval remains: `NOT_READY`

M12 remains: `NOT_STARTED`

No production apply, enforcement enablement, live Gateway behavior change, config mutation, service restart, Telegram/runtime send, provider/message API call, CLI registration, production promotion, M12 start, or M11 apply request occurred.
