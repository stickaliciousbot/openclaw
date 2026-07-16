# M10A Command Surface Repair Plan

Status: `HOLD_M10A_COMMAND_SURFACE_REPAIR_REQUIRED`

The installed M10A module has the right helper semantics but lacks a proven registered/persistent operator command surface.

Required repair:

- Add exact control command surface for enable, disable/off-switch, status/readback, verify-disabled, verify-enabled-scope, rollback-if-disable-fails, start-observation, and operator-stop.
- Preserve the exact scope: owner Telegram direct, owner chat `8495203551`, agent `main`.
- Persist/read only the approved M10A control artifact/flag.
- Reject Web UI, LAN/browser, wrong owner/channel/agent, production authority, broad enforcement, external sends, provider expansion, write tools, durable memory mutation, and Context Bridge mutation.
- Add fixtures for command registration, dry-run, persistent read/write round trip, fail-closed rollback, observation plan, and no-side-effect counters.

Next phase: `IMPLEMENT_M10A_COMMAND_SURFACE_SOURCE_READY_NO_APPLY`.
