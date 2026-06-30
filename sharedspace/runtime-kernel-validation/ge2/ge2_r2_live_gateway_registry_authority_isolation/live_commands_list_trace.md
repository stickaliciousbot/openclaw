# Live commands.list trace

Generated: 2026-06-30T06:00:12.400Z

Authoritative RPC path identified:

1. Gateway WS handles method `commands.list` (confirmed by /tmp/openclaw log entries `gateway/ws ⇄ res ✓ commands.list`).
2. `server-methods-Dw6hzI_j.js` imports `listPluginCommands` as `r` and `getPluginCommandSpecs` as `a` from `commands-D2qp4St4.js`.
3. `commandsHandlers["commands.list"]` calls `buildCommandsListResult()`.
4. `buildCommandsListResult()` appends `buildPluginCommandEntries()`.
5. `buildPluginCommandEntries()` calls `listPluginCommands()`.
6. `listPluginCommands()` returns `Array.from(pluginCommands.values())`.
7. `pluginCommands` is imported from `types-CdFhLeaX.js` export `A`, backed by Symbol.for("openclaw.pluginCommandsState") in that module realm.

Observed live RPC plugin entries: pair, dreaming, phone, voice. /ge2 present: false.
