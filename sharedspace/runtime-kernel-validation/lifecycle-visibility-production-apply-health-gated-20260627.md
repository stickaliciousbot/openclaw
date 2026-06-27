# Lifecycle Visibility Patch — Production Apply with Health-Based Restart Gate

Timestamp: 2026-06-27 AEST

## Result

| Area | Status |
| --- | --- |
| Production apply | PASS |
| Installed runtime | `OpenClaw 2026.5.7 (5c3a327)` |
| Restart wrapper exit | code `1`, no stdout/stderr — known false-negative class |
| Health-based restart gate | PASS |
| Old Gateway PID | `707840` |
| New Gateway PID | `717046` |
| Gateway status | running / active |
| Connectivity probe | OK |
| Admin-capable | YES |
| Fatal/missing-module log gate since latest restart | PASS (`bad_hits=0`) |
| Patched lifecycle markers present | YES |
| Rollback performed | NO |
| Backup preserved | YES |
| Failed prior patched install preserved | YES |

## Applied Artifact

- Validated tarball: `/tmp/openclaw-lifecycle-visibility-pack/openclaw-2026.5.7.tgz`
- Install command: `npm install -g --prefix /home/stickai/.npm-global /tmp/openclaw-lifecycle-visibility-pack/openclaw-2026.5.7.tgz`
- Fresh rollback backup: `/home/stickai/.openclaw/workspace/backups/openclaw-global-lifecycle-visibility-reapply-20260627T011619Z.tar.gz`
- Prior rollback backup still preserved: `/home/stickai/.openclaw/workspace/backups/openclaw-global-lifecycle-visibility-20260626T210158Z.tar.gz`
- Prior failed patched install still preserved: `/home/stickai/.npm-global/lib/node_modules/openclaw.failed-lifecycle-visibility-20260626T2117Z`

## Pre-Restart Installed Marker Verification

- CLI after install before restart: `OpenClaw 2026.5.7 (5c3a327)`
- Required chunks present:
  - `dist/dispatch-CQKtelZr.js`
  - `dist/agent-runner.runtime-BVgetsv5.js`
  - `dist/channel-0qcWkTpz.js`
  - `dist/send-BHK9WeqL.js`
- Required markers present:
  - `maybeSendSourceVisibleStartAcknowledgement` in `dist/dispatch-CQKtelZr.js`
  - `maybeSendSourceVisibleCompletionAcknowledgement` in `dist/dispatch-CQKtelZr.js`
  - `onRunLifecycleTerminal` in `dist/agent-runner.runtime-BVgetsv5.js` and `dist/dispatch-CQKtelZr.js`

## Restart Gate Evidence

- Old PID before restart: `707840`
- `openclaw gateway restart` returned code `1` with no stdout/stderr.
- Health gate did not use exit code alone.
- New PID observed: `717046`
- `openclaw gateway status` showed runtime running, connectivity probe OK, admin-capable.
- `systemctl --user show openclaw-gateway.service` showed `ActiveState=active`, `SubState=running`, `ExecMainStatus=0`, `Result=success`, start timestamp `Sat 2026-06-27 11:19:48 AEST`.
- Recent fatal/missing-module scan since latest restart: `bad_hits=0`.

## Smoke

- Harmless direct Telegram-session tool-backed smoke executed via `openclaw --version` after health gate.
- Tool result: `OpenClaw 2026.5.7 (5c3a327)`.
- Recent fatal/missing-module log gate after smoke remained PASS (`bad_hits=0`).

## Remaining Known Issue

`openclaw gateway restart` still returns a false-negative exit code under active-work drain/systemd timeout conditions. Keep using health/new-PID/log/marker gates until the restart wrapper/service-timeout behavior is fixed separately.
