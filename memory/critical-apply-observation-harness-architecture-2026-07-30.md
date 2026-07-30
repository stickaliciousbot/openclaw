# Critical Apply Observation Harness Architecture — No Foreground Apply Processes (2026-07-30)

## Global rule
No critical production APPLY/deploy/install/recovery mutation may be governed by a foreground chat/session process. Foreground turns may prepare evidence, explain, and request authorization, but the mutation itself must run under a durable observation-harness transaction with independent receipts and recovery semantics.

## Problem statement
Foreground apply processes are brittle because the same chat/control-plane path is responsible for approval, execution, observation, and closeout. If that path wedges, compacts, restarts, or loses output, the operator is blind exactly when the system is mutating production. This failure mode caused or amplified multiple incidents, including the MEM-CRON U3 INSTALL-R1 APPLY / OpenClaw npm mixed-generation recovery.

## Definitions

- **Critical apply:** any mutation to OpenClaw runtime/package/config/Gateway/service lifecycle/cron/protected-memory/model routing/provider delivery, or any operation whose failure can wedge replies or require recovery.
- **Foreground process:** an exec/tool command whose mutation safety depends on the current chat turn staying alive and receiving stdout/stderr/completion in-order.
- **Observation-harness apply:** a detached, receipt-driven transaction supervised by a durable observer that can classify state after session loss.
- **Restore point:** a verified package/config/runtime rollback snapshot created within the last 60 minutes, with manifest, size/hash, path-safety, ownership, and restore command authority.

## Hard prohibition
For critical apply:

- Do not run mutation commands directly as foreground exec.
- Do not use a native approval card whose approved command is itself the only observer.
- Do not combine install/apply and restart in one command.
- Do not proceed if the observer cannot independently classify failure and recovery state.
- Do not proceed without a fresh restore point or a successful restore-point creation.

## Required high-level state machine

```text
INIT
  -> ACQUIRE_MAINTENANCE_LOCK
  -> CLASSIFY_TARGET_AND_SCOPE
  -> VERIFY_OR_CREATE_FRESH_RESTORE_POINT
  -> PRECHECK_CURRENT_STATE
  -> PREPARE_TRANSACTION_DIR
  -> ARM_OBSERVER
  -> OWNER_AUTHORIZATION_BOUNDARY
  -> EXECUTE_APPLY_UNDER_OBSERVER
  -> OBSERVE_EXIT_AND_POSTCHECK
  -> IF_PASS: FINALIZE_PASS
  -> IF_FAIL: AUTO_RECOVERY_DECISION
  -> IF_RECOVERY_NEEDED: RESTORE_OR_REINSTALL_FROM_RESTORE_POINT
  -> POST_RECOVERY_REPORT
  -> HOLD_FOR_SEPARATE_RESTART_OR_SMOKE_IF_NEEDED
```

## Restore-point gate
Before any critical apply, the runner must check for a restore point newer than 60 minutes.

Fresh restore point requirements:

1. Created under an evidence directory with monotonic phase name.
2. Contains exact package/config/runtime state needed for rollback.
3. Includes manifest with SHA-256 and byte counts.
4. Includes path-safety inspection: no unexpected symlinks, ownership sane, same filesystem for atomic moves where needed.
5. Includes restore command authority and restore boundary: what it may and may not mutate.
6. Includes current service/process identity and package-root identity.
7. Includes protected cron/memory sentinels if those surfaces are in or adjacent to scope.

If no fresh restore point exists, the critical apply runner creates one first. If restore-point creation fails or cannot be verified, apply is blocked.

## Observer Level resiliency requirements
Critical apply observer must be able to recover from chat/session death and classify the transaction without relying on live stdout.

Minimum observer receipts:

- `transaction.json`: stable transaction id, scope, target, operator approval id/phrase, command hash, phase.
- `restore-point.json`: selected/created restore point metadata.
- `precheck.json`: current state sentinels before mutation.
- `apply-start.json`: written immediately before mutation with child PID/process group, command argv, cwd, env allowlist, start time.
- `heartbeat.jsonl`: periodic phase/liveness receipts.
- `apply-exit.json`: exit code/signal/timing/stdout-stderr artifact refs.
- `postcheck.json`: package/config/service/scheduler/memory integrity after mutation.
- `recovery-decision.json`: PASS/FAIL/HOLD/ROLLBACK_REQUIRED decision with reason.
- `recovery-action.json`: if automatic recovery is allowed/needed.
- `final-report.json`: terminal classification and next boundary.

Required classifications:

- `NO_APPROVAL`
- `APPROVED_NOT_STARTED`
- `STARTED_NO_EXIT`
- `EXITED_UNVERIFIED`
- `PASS`
- `FAIL_SAFE_NO_MUTATION`
- `FAIL_MUTATION_PARTIAL`
- `ROLLBACK_REQUIRED`
- `ROLLBACK_PASS`
- `ROLLBACK_FAIL_OPERATOR_REQUIRED`
- `RECOVERED_WITH_WARNING`
- `HOLD_FOR_SEPARATE_RESTART`

## npm/OpenClaw package critical apply policy
For OpenClaw npm/global package applies, the observer must additionally inspect npm base after any failed apply.

### Before apply

- Confirm package authority: exact path, SHA-256, version, source commit.
- Confirm rollback/restore authority fresh within 60 minutes or create it.
- Inspect package root: `package.json`, `openclaw.mjs`, `dist/index.js`, `dist/extensions/speech-core/runtime-api.js`, build info.
- Inspect npm sibling staging directories: `openclaw`, `.openclaw-*`.
- Inspect live process references before touching hidden directories:
  - `/proc/<pid>/maps`
  - `/proc/<pid>/fd`
  - `/proc/<pid>/cwd`
  - `/proc/<pid>/exe`
  - cmdline
  - systemd cgroup
- Acquire maintenance lock to prevent concurrent npm/recovery/restart/update.

### Apply execution

- Run only via observer harness.
- Command must be argv-array exact, not shell-concatenated.
- Write `apply-start.json` before exec.
- Capture stdout/stderr to files, not only chat output.
- Preserve npm logs if generated.

### Automatic recovery on apply failure

If apply fails, observer immediately checks npm base:

1. Is official package root missing/empty/incomplete?
2. Are critical files missing: `package.json`, `openclaw.mjs`, `dist/index.js`, speech runtime?
3. Did npm leave hidden `.openclaw-*` dirs?
4. Are hidden dirs live-referenced by any Gateway/process?
5. Does Gateway still run from old generation?
6. Is restore point complete and newer than 60 minutes?

Recovery decision matrix:

| Condition | Action |
|---|---|
| Apply failed before mutation and official root intact | `FAIL_SAFE_NO_MUTATION`; no restore. |
| Official root missing/empty/incomplete and restore point fresh | Restore/reinstall from restore point under observer. |
| Official root missing/empty/incomplete, hidden live generation referenced | Do not touch hidden dir; preserve official incomplete root if present; restore official path from restore point; no restart until verified. |
| Hidden staging dir inactive but blocks npm rename | Preserve/quarantine inactive staging dir, then retry restore/install only from verified restore point. |
| Restore point absent/stale/invalid | `ROLLBACK_FAIL_OPERATOR_REQUIRED`; stop, no restart. |
| Package restored but HTTP/control surface warning remains | `RECOVERED_WITH_WARNING`; no further package repair/restart unless separate report says so. |

Automatic recovery must only mutate surfaces included in the restore boundary. It must not mutate cron/protected memory/provider/config/routes unless those were explicitly part of the critical apply scope and restore authority.

## Restart boundary
Critical apply may not automatically restart Gateway unless the specific transaction explicitly includes restart authority. Default is:

- apply/install only;
- verify package/config coherence;
- final state `HOLD_FOR_SEPARATE_RESTART` if restart is needed.

Restart, if authorized, is a second critical apply transaction with its own restore point, observer, bounded readiness polling, and final report.

## Functional smoke boundary
Telegram/provider/Gmail/delivery smokes are not part of package repair by default. They require separate explicit authorization and should be a third transaction after package and service readiness pass.

## Restore-script extraction note
The inbound recovery script `recover_openclaw_cli_gateway_speech_surface---bdfc3ad2-6f75-49d6-a6e1-4dd4acbb508c.sh` (SHA-256 `282b52ac57dc96d89ac7b3661a1cbf63fd1d8d55c19570449bd0d79da972baf8`) was inspected read-only. Reusable logic and code extraction targets are recorded in `memory/critical-apply-restore-script-repurpose-notes-2026-07-30.md`.

Most important extraction decision: the observer must not merely run npm and return an exit code. The observer owns npm/package health classification after success or failure, including official package root missing/empty/incomplete detection, `.openclaw-*` process-reference inspection, and restore/reinstall invocation from the verified fresh restore point when authorized.

## Implementation recommendation
Create a reusable runner, tentatively:

- `scripts/critical_apply_observer_runner.py`

Core interfaces:

```bash
critical_apply_observer_runner.py prepare \
  --name <critical-apply-name> \
  --scope <json> \
  --restore-policy max-age=3600,create-if-missing \
  --precheck <script-or-plugin> \
  --apply-argv-json <argv.json> \
  --postcheck <script-or-plugin> \
  --recovery-policy <json>

critical_apply_observer_runner.py execute --transaction <id>
critical_apply_observer_runner.py status --transaction <id>
critical_apply_observer_runner.py recover --transaction <id>
critical_apply_observer_runner.py final-report --transaction <id>
```

OpenClaw npm package plugin:

- `scripts/critical_apply_plugins/openclaw_npm_package.py`

Plugin responsibilities:

- create/verify restore point;
- inspect npm package root and staging dirs;
- verify package authority;
- verify package coherence;
- decide restore/reinstall behavior after failure;
- never delete hidden staging directories automatically.

## Global memory rule
If a future task says “apply”, “deploy”, “install”, “repair”, “restart”, “roll back”, “activate”, “migrate”, “mutate runtime”, or “critical apply”, first classify whether it is critical. If critical, use this architecture. If no critical apply runner exists yet, stop at architecture/prep and do not improvise a foreground mutation.
