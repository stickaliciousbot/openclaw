# M10A Control Path Staged Install Rollback Summary

Status: `HOLD_M10A_INSTALL_ROLLED_BACK_PRESERVATION_DRIFT_REPAIR_REQUIRED`

Rollback was approved and completed before Gateway restart or activation.

## Trigger

The approved M10A tarball installed successfully and the M10A dist hash matched, but validation detected unexpected drift in the preserved M8 runtime artifact before Gateway restart:

- File: `dist/auto-reply/reply/umc-m8-owner-contract-lane.js`
- Expected SHA256: `27116a4374b699b7e98bc8ec9be98f3584bc14a8ca740d0723316deaa66088db`
- Actual after install: `753fade05d957fb295dcf33a7beaec7a89d6b977e750c937e26a9cd7ad18b0ef`

## Rollback

Trusted backup restored from:

`/home/stickai/.openclaw/backups/openclaw-m10a-control-path-install-20260716T111530Z/openclaw-installed-package`

Failed post-install tree quarantined at:

`/home/stickai/.openclaw/backups/openclaw-m10a-control-path-install-20260716T111530Z/failed-installed-package-postinstall-20260716T112500Z`

## Verified after rollback

- M8 dist SHA256 restored: `27116a4374b699b7e98bc8ec9be98f3584bc14a8ca740d0723316deaa66088db`
- M10A installed dist absent after rollback.
- Gateway restart count: `0`
- Gateway activation count: `0`
- Gateway remains running on PID `1285995` and connectivity/admin probe is OK.
- M10A enabled: `false`
- Production authority changed: `false`
- Broad enforcement enabled: `false`
- Telegram send/probe count: `0`
- External send count: `0`
- Provider/model live call count: `0`
- Write tool execution count: `0`
- Durable memory mutation count: `0`
- Context Bridge mutation count: `0`

Next phase: `REPAIR_M10A_PACKAGE_PRESERVATION_DRIFT_SOURCE_READY_NO_APPLY`.
