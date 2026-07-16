# M10 Rollback / Off-Switch Plan

Status: `BLOCKED_M10_ROLLBACK_OFF_SWITCH_INCOMPLETE`

Known rollback assets:

- M8 R3 rollback tarball: `/home/stickai/.openclaw/workspace/tmp/umc-m8-r3-package/openclaw-2026.5.7.tgz`
- SHA256: `1f6bd7fed192b1413f6320a69ca56cc528e807c81c2dae36473e14bc9ddbc9a0`
- Current installed backup: `/home/stickai/.openclaw/backups/openclaw-m8-r3-authority-mode-install-20260716T0707Z/scoped-installed-files`

Proposed off-switch only:

- `state/umc-v1/m10a-owner-telegram-direct-enforcement/control.json enabled=false`

Blocking gap:

No installed runtime-backed M10A control reader/flag has been proven, so the off-switch cannot yet be treated as exact.
