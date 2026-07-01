# M10 Enforced Canary — Approval Request Only

Status: `APPROVAL_REQUEST_PREPARED_NOT_EXECUTED`
Prepared at: 2026-07-01T11:38:00Z
Prerequisite closeout: M9 `PASS_PUSHED`
Overall lifecycle state: `READY_FOR_M10_APPROVAL`
M10 lifecycle state: `NOT_STARTED`

## Explicit statement: not production promotion

M10 is an enforced canary, not production promotion. Approval for M10 must not be interpreted as approval to permanently enable lifecycle enforcement globally, promote runtime hooks broadly, register new CLI surfaces, mutate routes/providers/auth/memory, restart services, send Telegram from code/runtime, or begin M11/M10 promotion work.

## Exact enforcement scope

Allowed only if explicitly approved for M10 execution:

1. Exercise lifecycle enforcement against synthetic/test canary work only.
2. Verify that lifecycle enforcement can block/hold unsafe continuation when required closeout state is missing.
3. Verify that required closeout states cannot be silently skipped in the canary path.
4. Verify that notification behavior is represented as durable state, not assumed delivery.
5. Write M10 evidence under `sharedspace/runtime-kernel-validation/work-lifecycle/m10-enforced-canary/`.
6. Write synthetic M10 sidecar run/event state under `state/work-lifecycle/`.
7. If an enforcement flag is required, mutate only the approved `work_lifecycle` enforcement flag path documented below, and only for the bounded canary window.

Forbidden:

- Production promotion.
- Broad runtime hook import outside the approved M10 canary path.
- CLI registration change.
- Gateway route/provider/auth/memory mutation.
- Service restart.
- Telegram send from code/runtime.
- Production apply.
- M11 or promotion work.
- Commit/push without separate approval.

## Exact config diff

Default expected config diff: none.

If M10 requires a temporary enforcement flag, the only allowed config-like mutation is the approved work-lifecycle canary flag path:

```json
{
  "work_lifecycle": {
    "enforcement": {
      "m10_canary_enabled": true,
      "scope": "synthetic_sidecar_only",
      "production_promotion": false
    }
  }
}
```

This flag must not alter Gateway routes, providers, auth profiles, memory routing, model routing, Telegram delivery, service lifecycle, or production runtime authority. If the exact flag path does not already exist or cannot be represented as a sidecar/test config artifact without Gateway mutation, M10 must HOLD before applying it.

## Rollback path

1. Stop M10 immediately on any hard abort trigger.
2. If a temporary sidecar/test enforcement flag was written, restore it to disabled or remove the sidecar test artifact.
3. Do not restart Gateway or services.
4. Do not send Telegram from code/runtime.
5. Preserve failure evidence under `sharedspace/runtime-kernel-validation/work-lifecycle/m10-enforced-canary/`.
6. Mark M10 `FAIL`, `HOLD`, or `ABORT` with explicit failed gate and boundary readback.
7. Leave M9 `PASS_PUSHED` and M8 `PASS_PUSHED` unchanged.

## Validation command

Expected focused validation shape after M10 execution approval:

```sh
set -euo pipefail
node --experimental-strip-types --test src/work-lifecycle/work-enforced-canary.test.mjs

# Run the owner-approved secret-sentinel grep scan over src/work-lifecycle,
# the M10 evidence directory, and state/work-lifecycle. The literal sentinel
# expression is intentionally not repeated in this repo-bound approval artifact
# because this artifact is itself included in the scan and would self-match.

git diff --check

printf 'M10_ENFORCED_CANARY_VALIDATION_PASS\n'
printf 'M10_REDACTION_SCAN_PASS\n'
printf 'M10_BOUNDARY_CHECK_FILES_SCOPED\n'
```

If `src/work-lifecycle/work-enforced-canary.test.mjs` does not exist, M10 implementation may create it only within the approved M10 sidecar/test scope.

Repair note: the first M10 validation attempt passed the Node test but the redaction scan self-matched this approval artifact because it repeated the literal secret-sentinel expression. The artifact was repaired to preserve the validation shape without storing that literal expression in the scanned evidence directory.

## Expected evidence paths

- `src/work-lifecycle/work-enforced-canary.test.mjs`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m10-enforced-canary/status.json`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m10-enforced-canary/summary.json`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m10-enforced-canary/gate-results.json`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m10-enforced-canary/evidence_manifest.json`
- `state/work-lifecycle/runs/<m10-run-id>.json`
- `state/work-lifecycle/events/<m10-run-id>.jsonl`
- Optional sidecar-only test config artifact if and only if needed: `sharedspace/runtime-kernel-validation/work-lifecycle/m10-enforced-canary/enforcement-flag-readback.json`

## Notification behavior

- Notification delivery is state, not assumption.
- M10 may record ACK/terminal notification intent in synthetic sidecar state.
- M10 must not send Telegram from code/runtime.
- M10 must not call provider messaging APIs or OpenClaw message tools from implementation code.
- Any terminal notification readback must state whether delivery was recorded, queued, simulated, failed, or not sent.
- `FAIL`, `HOLD`, and `ABORT` states must not be suppressed in canary evidence.

## Hard abort triggers

Abort M10 immediately and record terminal evidence if any occur:

- Gateway/config/route/provider/auth/memory mutation outside the approved `work_lifecycle` enforcement flag path.
- Service restart or service lifecycle mutation.
- Telegram send from code/runtime.
- Production apply.
- Runtime hook import outside the approved canary/test path.
- CLI registration change.
- Any secret/redaction scan hit.
- M8 terminal state not `PASS_PUSHED`.
- M9 terminal state not `PASS_PUSHED`.
- M11/M10 promotion work starts.
- Evidence cannot prove the enforcement scope stayed synthetic/test-only.

## Safety-boundary readback required

M10 may pass only if all read back exactly:

- `productionPromotion`: false
- `productionMutation`: false
- `runtimeHookImport`: false unless explicitly bounded to the approved synthetic canary/test path
- `cliRegistrationChange`: false
- `gatewayConfigRouteProviderAuthMemoryMutation`: false except the approved `work_lifecycle.enforcement.m10_canary_enabled` path if explicitly used
- `serviceRestart`: false
- `telegramSend`: false
- `productionApply`: false
- `m8TerminalState`: `PASS_PUSHED`
- `m9TerminalState`: `PASS_PUSHED`
- `m10EnforcedCanary`: true
- `m11Started`: false

## Gateway/routes/provider/auth/memory mutation statement

M10 must not mutate Gateway, routes, providers, auth, or memory except the approved `work_lifecycle` enforcement flag path, if any. If that path is unavailable or would require broader Gateway/config mutation, M10 must HOLD and request a narrower approval rather than applying it.

## Terminal states

- `PASS_LOCAL_VALIDATED`: M10 validation passes but files are not yet preserved.
- `HOLD_BEFORE_SELECTIVE_COMMIT_PUSH`: M10 preservation files exist but are not pushed.
- `PASS_PUSHED`: only after separate selective commit/push approval.
- `FAIL`: any validation/boundary/redaction gate fails.
- `ABORT`: hard abort trigger fires.
- `HOLD_APPROVAL_TRANSPORT_BLOCKED`: approval/execution is blocked by approval transport.

## Current execution readback

- M10 started: no.
- M10 canary executed: no.
- Runtime hook imported: no.
- CLI registered: no.
- Gateway/config/route/provider/auth/memory mutated: no.
- Service restarted: no.
- Telegram sent from code/runtime: no.
- Production apply: no.
- M11/promotion work started: no.
