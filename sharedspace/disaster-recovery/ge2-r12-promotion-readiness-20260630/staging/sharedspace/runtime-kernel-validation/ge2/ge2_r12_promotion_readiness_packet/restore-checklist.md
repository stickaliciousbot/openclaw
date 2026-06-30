# GE2 R12 restore / rollback checklist

Do not run this checklist unless a rollback condition is met and Stick explicitly authorizes recovery.

Rollback conditions:
- /ge2 absent or duplicated in commands.list.
- fake /ge2 command appears.
- existing commands pair/dreaming/phone/voice missing.
- Gateway health red or admin/connectivity fails.
- GE2 native help/status/run/artifact proof regresses.

Recovery steps:
1. Capture current Gateway status and PID.
2. Preserve current ledgers/artifacts under state/ge2-native.
3. Review reverser: sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/reverser_ge2_r7_lifecycle_20260630T0812Z.mjs
4. If authorized, run the reverser.
5. Restart Gateway only under the health-based gate.
6. Verify new PID/health/connectivity/admin/listener.
7. Verify commands.list: /ge2 count exactly 1, fake absent, pair/dreaming/phone/voice preserved.
8. Verify /ge2 help and /ge2 status before any run.

No cron closeout apply is authorized by this checklist.
