# Lifecycle Visibility Patch — Recovery State Baseline

Timestamp: 2026-06-27 AEST

## Current Recovery State

| Area | Status |
| --- | --- |
| Mixed runtime cleanup | PASS |
| Gateway operational health | PASS |
| Runtime after rollback | OpenClaw 2026.5.7 (eeef486) |
| Lifecycle visibility patch installed | NO |
| Failed patched install preserved | YES |
| Backup preserved | YES |
| Remaining blocker | `openclaw gateway restart` returns code 1 with no output despite successful operational restart |

## Key Finding

`openclaw gateway restart` is currently unreliable as a production apply gate. It returned exit code 1 with no stdout/stderr, but Gateway restarted onto a new PID and became healthy. Future production applies must not use restart wrapper exit code alone as the rollback trigger.

## Required Future Restart Gate

For lifecycle visibility patch reapply or similar production mutations, use a health-based restart validation gate:

1. Capture old Gateway PID.
2. Run restart command.
3. Capture restart command exit code/stdout/stderr.
4. Capture new Gateway PID.
5. Verify Gateway health/connectivity/admin-capable.
6. Check relevant logs for fatal/runtime import errors.
7. Roll back only if new-PID, health, connectivity/admin, or fatal-log gates fail — not merely because wrapper exit code is nonzero.

## Current Recommendation

Do not reapply lifecycle visibility patch yet. Keep production restored. Keep staged patched tarball ready. First diagnose/classify why `openclaw gateway restart` exits 1 while succeeding operationally.

## Preserved Artifacts

- Failed patched install: `/home/stickai/.npm-global/lib/node_modules/openclaw.failed-lifecycle-visibility-20260626T2117Z`
- Rollback backup: `/home/stickai/.openclaw/workspace/backups/openclaw-global-lifecycle-visibility-20260626T210158Z.tar.gz`
- Staged patched tarball: `/tmp/openclaw-lifecycle-visibility-pack/openclaw-2026.5.7.tgz`
- Temp staged install: `/tmp/openclaw-lifecycle-visibility-prefix`

## Bug Class

Separate operational reliability bug: restart command completion reporting false-negative / silent failure. This is the CLI/service-layer analogue of the broader completion visibility class.
