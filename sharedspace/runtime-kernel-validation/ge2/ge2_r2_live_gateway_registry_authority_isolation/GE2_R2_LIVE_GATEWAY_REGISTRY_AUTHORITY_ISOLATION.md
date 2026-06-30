# GE2-R2 Live Gateway Registry Authority Isolation

Generated: 2026-06-30T06:00:12.400Z

Final classification: **GE2_R2_LIVE_GATEWAY_REGISTRY_AUTHORITY_ISOLATION_PASS_NO_APPLY**

## Exact loss point

Hook registrar writes /ge2 into a registrar-local command registry visible to hook-side dynamic imports of types-CdFhLeaX.js/commands-D2qp4St4.js, but live Gateway RPC commands.list reads a different authoritative pluginCommands registry that lacks /ge2. The loss occurs at registry object/module-realm boundary before command-list filtering, not in auth/scope filtering.

## Restart/reload

R2 did **not** require or perform a Gateway restart/reload. It used the existing live Gateway PID 285000.

## GE2-R3 recommendation

GE2-R3 should be: **packaging/bundle singleton repair**. A narrow registry bridge repair is acceptable only if it targets the exact authoritative RPC command-list registry and preserves auth/visibility.

Do **not** start GE2-R3 automatically.
