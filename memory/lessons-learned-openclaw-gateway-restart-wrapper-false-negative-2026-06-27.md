# Lesson Learned — OpenClaw Gateway Restart Wrapper False-Negative After Lifecycle Visibility Patch Rollback

Date: 2026-06-27 AEST

## Summary

During the lifecycle visibility patch production apply/rollback, `openclaw gateway restart` returned exit code `1` with no stdout/stderr, but the Gateway operationally restarted onto a new PID and became healthy. This caused a false production-apply failure signal and contributed to rollback/mixed-runtime confusion.

## Final Recovery State

| Area | Status |
| --- | --- |
| Mixed runtime cleanup | PASS |
| Gateway operational health | PASS |
| Runtime after rollback | `OpenClaw 2026.5.7 (eeef486)` |
| Lifecycle visibility patch installed | NO |
| Failed patched install preserved | YES |
| Backup preserved | YES |
| Remaining blocker | restart wrapper returns code `1` despite successful operational restart |

Preserved artifacts:

- Failed patched install: `/home/stickai/.npm-global/lib/node_modules/openclaw.failed-lifecycle-visibility-20260626T2117Z`
- Rollback backup: `/home/stickai/.openclaw/workspace/backups/openclaw-global-lifecycle-visibility-20260626T210158Z.tar.gz`
- Staged patched tarball: `/tmp/openclaw-lifecycle-visibility-pack/openclaw-2026.5.7.tgz`
- Temp staged install: `/tmp/openclaw-lifecycle-visibility-prefix`

## Evidence

- Pre-restart disk runtime was restored: `OpenClaw 2026.5.7 (eeef486)`.
- Installed production dist had no lifecycle completion marker (`maybeSendSourceVisibleCompletionAcknowledgement`) and no run-lifecycle terminal marker (`onRunLifecycleTerminal`).
- Failed patched install and backup remained present.
- `openclaw gateway restart` returned code `1` with no stdout/stderr.
- `openclaw gateway status` after restart showed:
  - runtime running
  - new PID `707840`
  - connectivity probe OK
  - admin-capable
- `systemctl --user show openclaw-gateway.service` showed:
  - `ActiveState=active`
  - `SubState=running`
  - `Result=success`
  - `ExecMainStatus=0`
  - `ExecMainStartTimestamp=Sat 2026-06-27 09:24:29 AEST`
- Gateway log showed the failure mechanism pattern:
  - `signal SIGTERM received`
  - `received SIGTERM; restarting`
  - `draining 2 active task(s) and 1 active embedded run(s) before restart with timeout 300000ms`
  - `still draining 2 active task(s) and 1 active embedded run(s) before restart` at roughly the 30s boundary
  - subsequent fresh Gateway startup and `gateway ready`
- Systemd unit showed:
  - `TimeoutStopSec=30`
  - `TimeoutStartSec=30`
- This creates a mismatch: OpenClaw intends to drain active work for up to 300s, while systemd gives the process only 30s to stop during restart.

## Diagnosis

Root cause class: **restart wrapper false-negative caused by systemd stop timeout vs Gateway active-work drain mismatch**.

The CLI/service restart wrapper treats `systemctl --user restart openclaw-gateway.service` returning nonzero as restart failure. But operational evidence showed systemd still brought the Gateway back up successfully afterward. The likely reason for the nonzero command result is that systemd's `TimeoutStopSec=30` expires while OpenClaw is intentionally draining active background tasks/embedded runs for `300000ms`.

This is not evidence that the lifecycle visibility patch package failed to boot. The preserved patched package and temp-prefix install both started successfully as `OpenClaw 2026.5.7 (5c3a327)`.

## Avoid Repeating the Mistake

For production applies/restarts, do not use `openclaw gateway restart` exit code alone as the rollback trigger while this bug exists.

Use a health-based operational restart gate:

1. Capture old Gateway PID.
2. Run restart command.
3. Capture restart command exit code/stdout/stderr.
4. Capture new Gateway PID.
5. Verify Gateway health/connectivity/admin-capable.
6. Check logs for fatal startup/runtime import errors.
7. Roll back only if new-PID, health/connectivity/admin, or fatal-log gates fail — not merely because the wrapper returned nonzero.

If rollback changes installed bundle files while a Gateway process may still be running from the previous bundle, perform/verify a controlled restart from the rollback disk state; otherwise lazy dynamic imports can fail against mismatched chunk names.

## Next Fix Direction

Treat this as a separate operational reliability bug in the CLI/service layer. Candidate fixes to evaluate before the second lifecycle patch apply:

- Make `openclaw gateway restart` report scheduled/deferred restart when active work is draining instead of returning silent code `1`.
- Align systemd `TimeoutStopSec` with Gateway's restart drain budget, or make the CLI use a restart intent path that does not rely solely on `systemctl restart` stop completion semantics.
- Improve restart command stdout/stderr/status reporting to include drain blockers, systemd timeout results, old/new PID, and health-gate outcome.
- Add an apply-run gate helper that validates operational success by PID + health + logs rather than wrapper exit code alone.

## Second Apply Constraint

Do not reapply the lifecycle visibility patch until either:

1. the restart wrapper issue is fixed/classified, or
2. Stick explicitly approves a second apply using the health-based restart gate above.
