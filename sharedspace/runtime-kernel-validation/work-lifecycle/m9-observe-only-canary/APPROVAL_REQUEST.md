# M9 Observe-Only Canary — Approval Request Only

Status: `APPROVAL_REQUEST_PREPARED_NOT_EXECUTED`
Prepared at: 2026-07-01T11:17:00Z
Prerequisite closeout: M8 `PASS_PUSHED`
Overall lifecycle state: `READY_FOR_M9_APPROVAL`
M9 lifecycle state: `NOT_STARTED`

## Approval requested

Approve M9 observe-only canary execution only after reviewing this scope.

## Exact scope

Allowed:

1. Create synthetic sidecar-only M9 canary state under `state/work-lifecycle/` for a new M9 run id.
2. Write validation mirror artifacts under `sharedspace/runtime-kernel-validation/work-lifecycle/m9-observe-only-canary/`.
3. Exercise observe-only lifecycle recording paths against synthetic/test data only.
4. Verify ACK/terminal closeout transitions are durably recorded without assuming delivery.
5. Verify watcher/readback behavior without importing runtime hooks or registering CLI commands.
6. Produce terminal M9 evidence summary and boundary readback.

Forbidden:

- Production mutation.
- Runtime hook import.
- CLI registration change.
- Gateway/config/route/provider/auth/memory mutation.
- Service restart.
- Telegram send from code/runtime.
- Production apply.
- Any M10 or promotion work.

## Config diff

Expected config diff: none.

No Gateway config, route, provider, auth, memory, service, systemd, runtime authority, or Telegram delivery configuration may change during M9.

## Rollback path

Because M9 is observe-only and sidecar/test-scoped, rollback is file-only:

1. Stop immediately if any boundary check reports mutation outside the allowed scope.
2. Do not restart Gateway or services.
3. Preserve failure evidence under `sharedspace/runtime-kernel-validation/work-lifecycle/m9-observe-only-canary/`.
4. If cleanup is required, move synthetic M9 sidecar state to a quarantine path under `state/work-lifecycle/quarantine/`; do not delete evidence.
5. Mark M9 `FAIL` or `HOLD` with explicit closeout and failed gate.
6. Leave M8 `PASS_PUSHED` unchanged.

## Validation command

After approval, expected focused validation command:

```sh
set -euo pipefail
node --experimental-strip-types --test src/work-lifecycle/work-observe-only-canary.test.mjs
printf 'M9_OBSERVE_ONLY_CANARY_VALIDATION_PASS\n'
```

If the M9 test file does not yet exist, M9 implementation must first create it within the allowed sidecar/test scope and then run the same focused validation shape.

## Expected evidence paths

- `sharedspace/runtime-kernel-validation/work-lifecycle/m9-observe-only-canary/status.json`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m9-observe-only-canary/summary.json`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m9-observe-only-canary/gate-results.json`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m9-observe-only-canary/evidence_manifest.json`
- `state/work-lifecycle/runs/<m9-run-id>.json`
- `state/work-lifecycle/events/<m9-run-id>.jsonl`

## Explicit boundary readback required

M9 may pass only if all read back exactly:

- `productionMutation`: false
- `runtimeHookImport`: false
- `cliRegistrationChange`: false
- `gatewayConfigRouteProviderAuthMemoryMutation`: false
- `serviceRestart`: false
- `telegramSend`: false
- `productionApply`: false
- `m8TerminalState`: `PASS_PUSHED`
- `m9ObserveOnly`: true

## Terminal states

- If all gates pass and evidence is written: M9 may close `PASS` or `PASS_PUSHED` only after any required preservation step is separately approved.
- If validation fails: M9 closes `FAIL` with failed gate.
- If approval/config/boundary is missing: M9 remains `HOLD`.

## Current execution readback

- M9 started: no.
- M9 canary executed: no.
- Runtime hook imported: no.
- CLI registered: no.
- Gateway/config/route/provider/auth/memory mutated: no.
- Service restarted: no.
- Telegram sent from code/runtime: no.
- Production apply: no.
