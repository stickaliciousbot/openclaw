# M10A Package Drift Source Repair

Status: `PASS_M10A_PACKAGE_DRIFT_SOURCE_REPAIRED_NO_APPLY`

Repair: scoped M10A overlay/install guard. The repaired plan validates the candidate overlay SHA, allows only `dist/auto-reply/reply/umc-m10a-owner-telegram-direct-control-path.js`, rejects overlays containing M8 or any preserved M2-M9 runtime artifact, verifies preserved installed SHA values before and after copy, and remains no-apply until operator approval.

Expected M8 preserved SHA256: `27116a4374b699b7e98bc8ec9be98f3584bc14a8ca740d0723316deaa66088db`

No preserved M8 expectation change was made. No install, Gateway restart, runtime mutation, or M10A enablement was performed.
