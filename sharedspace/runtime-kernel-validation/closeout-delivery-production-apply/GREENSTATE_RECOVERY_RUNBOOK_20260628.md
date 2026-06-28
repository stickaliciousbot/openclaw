# Greenstate recovery runbook — closeout-delivery production state (2026-06-28)

## Target greenstate

Recover to the live + memory state after the `openclaw@2026.5.7` closeout-delivery backport production confirmation.

Final classification preserved:

`CLOSEOUT_DELIVERY_CONTRACT_PRODUCTION_HEALTH_PASS_TELEGRAM_APPEND_GAP`

Target properties:

- OpenClaw runtime: `OpenClaw 2026.5.7 (5c3a327)`
- Installed package version: `openclaw@2026.5.7`
- Patch-only artifact installed, not `2026.6.10`
- Gateway health: running, connectivity probe OK, admin-capable
- Production artifact SHA: `9ffa4cafda8b1185b09cebb7905a063c3851d8f83d74abfee9017dcf18a1e616`
- Memory/context/docs contain the append-gap classification
- Rollback remains not performed unless Gateway health fails
- Next engineering scope remains limited to direct-chat closeout append/session routing

## Primary recovery artifact

One disaster-recovery tarball is produced under:

`sharedspace/disaster-recovery/`

Expected naming pattern:

`stickbot-greenstate-closeout-20260628T*.tar.gz`

The tarball contains:

- `payload/artifacts/openclaw-2026.5.7.tgz` — validated production-compatible closeout-delivery artifact
- `payload/workspace-overlay/` — memory, context bridge, evidence, lessons, docs, scripts, and DR manifests needed to restore this greenstate
- `payload/systemd-user/` — user-systemd watchdog files relevant to current live recovery posture, when present
- `payload/manifests/` — file manifests, checksums, runtime health proof, and Git metadata
- `recover.sh` — copy of `scripts/recover_closeout_delivery_greenstate_20260628.sh`

## Recovery command

From a machine with Node/npm, Git, and user-systemd available:

```sh
cd /home/stickai/.openclaw/workspace
bash scripts/recover_closeout_delivery_greenstate_20260628.sh \
  sharedspace/disaster-recovery/stickbot-greenstate-closeout-<RUN_ID>.tar.gz
```

The script:

1. verifies the bundled OpenClaw artifact SHA,
2. fetches/pulls GitHub branch `stickbot/v3-selected-model-persona-injection` when possible,
3. overlays the greenstate memory/context/docs/scripts,
4. restores current user-systemd watchdog files when present,
5. installs the bundled `openclaw@2026.5.7` closeout-delivery artifact,
6. restarts Gateway unless `SKIP_GATEWAY_RESTART=1`,
7. verifies Gateway status, connectivity, and admin capability,
8. writes a restore report under `sharedspace/disaster-recovery/restore-reports/`.

## Safety notes

- The recovery script intentionally uses health gates, not restart exit code alone.
- The known `openclaw gateway restart` code `1` false-negative class is tolerated only if PID/status/connectivity/admin/log/marker gates pass.
- The script does not restore secrets or provider credentials from the DR tarball.
- The script does not apply a `2026.6.10` upgrade.
- The script does not declare the Telegram closeout append contract fixed; it restores the exact known greenstate, including the append-gap classification.

## Current evidence

- Production evidence note: `sharedspace/runtime-kernel-validation/closeout-delivery-production-apply/CLOSEOUT_DELIVERY_CONTRACT_PRODUCTION_HEALTH_PASS_TELEGRAM_APPEND_GAP_20260628.md`
- Durable lesson: `memory/lessons-learned-closeout-delivery-telegram-append-gap-2026-06-28.md`
- Recovery script: `scripts/recover_closeout_delivery_greenstate_20260628.sh`
