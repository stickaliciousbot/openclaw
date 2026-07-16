# M10A Control Path Staged Install and Validation Summary

Status: `FAIL_M10A_CONTROL_PATH_STAGED_INSTALL_FAILED`

The approved tarball SHA256 was verified and `npm install -g --ignore-scripts` completed, but the preservation gate failed before Gateway restart/activation.

Failure:

- Expected M8 dist SHA256: `27116a4374b699b7e98bc8ec9be98f3584bc14a8ca740d0723316deaa66088db`
- Actual M8 dist SHA256 after install: `753fade05d957fb295dcf33a7beaec7a89d6b977e750c937e26a9cd7ad18b0ef`

Because the approval boundary allowed adding the M10A control path only, the install was stopped before Gateway restart. The post-install disk tree was quarantined and the trusted backup was restored.

Rollback result: `PASS_M10A_STAGED_INSTALL_ROLLBACK_DISK_RESTORE`

Post-rollback:

- Gateway stayed running on PID `1285995`; no restart was run.
- Gateway health: OK/admin-capable.
- Telegram health: `ON/OK`.
- M8 dist hash restored to `27116a4374b699b7e98bc8ec9be98f3584bc14a8ca740d0723316deaa66088db`.
- M10A installed dist is absent after rollback.
- M10A remains disabled; production authority unchanged; broad enforcement false.

Next phase: `REPAIR_M10A_SCOPED_PACKAGE_TO_PRESERVE_M8_OR_EXPLICITLY_REBASE_APPROVAL_BOUNDARY`.
