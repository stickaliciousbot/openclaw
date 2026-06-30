# GE2-R7 Loader Lifecycle Exact Target and Repair Plan

Generated: 2026-06-30T08:05:00Z

Classification: `GE2_R7_SOURCE_SNAPSHOT_REPAIR_PLAN_TARGET_PROVEN_NO_PRODUCTION_MUTATION`

Production mutation performed: **no**  
Gateway restart performed: **no**  
Live `/ge2` smoke performed: **no**  
Cron closeout apply performed: **no**

## R6 carry-forward

R6 branch C stands: `GE2_R6_COMMAND_REGISTRY_CACHE_IDENTIFIED_NO_MUTATION`.

The live process imports the patched command chunk, but `/ge2` remains absent from `commands.list`, because the R5 top-level `pluginCommands.set("/ge2", ...)` registration is cleared/rebuilt during plugin registry startup lifecycle.

## Snapshot status

Preimage snapshots already captured:

| Label | Source | Snapshot | SHA256 |
|---|---|---|---|
| types | `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/types-CdFhLeaX.js` | `snapshots_20260630T0800Z/types-CdFhLeaX.js` | `864d569218baa6a23bfaa48547947e503ea2343929e5f78171af4e031dad202f` |
| loader | `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/loader-Bfm_uDYG.js` | `snapshots_20260630T0800Z/loader-Bfm_uDYG.js` | `ff2d89b04d1d5f7fb727f586a78fe92e0b52ffbe43a484551475cf140b53feb0` |
| serverMethods | `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/server-methods-Dw6hzI_j.js` | `snapshots_20260630T0800Z/server-methods-Dw6hzI_j.js` | `638aa2dbf4cc7a9758b0d3f5679ec745e329e0f8f164408731a2107357993986` |
| commands | `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/commands-D2qp4St4.js` | `snapshots_20260630T0800Z/commands-D2qp4St4.js` | `660af5de5094031703c6f62260cb118643043275999bb68ff53e806796e250eb` |

Manifest: `sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/r7_source_snapshot_manifest_20260630.json`

## Required inspection findings

### 1. `types-CdFhLeaX.js`

Role: registry storage/API.

Findings:

- Owns shared state key `openclaw.pluginCommandsState`.
- `pluginCommands` is a proxy over `getState$1().pluginCommands`, a process/global `Map`.
- `clearPluginCommands()` calls `pluginCommands.clear()`.
- `restorePluginCommands(commands)` calls `pluginCommands.clear()` and then sets `/${name}` for each command.
- `listRegisteredPluginCommands()` returns `Array.from(pluginCommands.values())`.
- Expected command visibility fields include at least:
  - `name`
  - `description`
  - `acceptsArgs`
  - optional `nativeName` / `nativeNames`
  - optional `channels` / `channelIds`
  - not hidden/internal/private/visible false/exposeInCommandsList false

Patch recommendation: **do not patch first**. This is lower-level shared storage and patching it would broaden registry semantics globally.

### 2. `loader-Bfm_uDYG.js`

Role: plugin lifecycle/cache/activation.

Findings:

- Imports command registry APIs from `types-CdFhLeaX.js`:
  - `pluginCommands`
  - `clearPluginCommandsForPlugin`
  - `clearPluginCommands`
  - `restorePluginCommands`
  - `listRegisteredPluginCommands`
  - `registerPluginCommand`
  - `validatePluginCommandDefinition`
- `clearActivatedPluginRuntimeState()` calls `clearPluginCommands()`.
- `loadOpenClawPlugins()` calls `clearActivatedPluginRuntimeState()` when `shouldActivate` is true.
- Cache restore path calls `restorePluginCommands(cached.state.commands ?? [])` before `activatePluginRegistry(...)`.
- Normal load path caches `commands: listRegisteredPluginCommands()` and then activates registry via `activatePluginRegistry(registry, ...)`.
- Durable command records are created by `registerCommand(record, command)`, which:
  - validates reserved ownership
  - uses `registerPluginCommand(...)` for active side effects
  - appends `record.commands.push(name)`
  - appends `registry.commands.push({ pluginId, pluginName, command, source, rootDir })`

Patch recommendation: **yes, lifecycle target**. This is the proven place where command state is cleared/restored and where durable commands enter both `pluginCommands` and `registry.commands`.

### 3. `server-methods-Dw6hzI_j.js`

Role: `commands.list` RPC handler/formatter.

Findings:

- Exact handler: `commandsHandlers["commands.list"]`.
- Calls `buildCommandsListResult(...)`.
- `buildCommandsListResult(...)` builds native/skill commands, then appends `buildPluginCommandEntries(...)`.
- `buildPluginCommandEntries(...)` uses:
  - `listPluginCommands()` from `commands-D2qp4St4.js`
  - `getPluginCommandSpecs(provider, { config })`
  - `collectActiveRegistryPluginCommandEntries(...)`
- `collectActiveRegistryPluginCommandEntries(...)` reads `getActivePluginRegistry()?.commands` and applies visibility/provider filters.

Patch recommendation: **no**. It already consumes the correct registry and patched command chunk. Hardcoding `/ge2` here would bypass registry lifecycle and violate the R7 principles.

### 4. `commands-D2qp4St4.js`

Role: slash matcher/native handler and plugin command list helpers.

Findings:

- Contains R5 GE2 native handler patch.
- `ensureNativeGe2CommandRegistered()` currently performs top-level `pluginCommands.set("/ge2", ...)`.
- `listPluginCommands()` maps `listEffectivePluginCommands()` to descriptors for `commands.list`.
- `matchPluginCommand()` uses `pluginCommands.get(...)` and `listEffectivePluginCommands()`.
- `listEffectivePluginCommands()` bridges `getActivePluginRegistry()?.commands` into matcher candidates.
- The R5 descriptor is local to `pluginCommands` at module import time; it is not durable in `registry.commands` and is cleared by loader lifecycle.

Patch recommendation: **no additional matcher-only patch** as the first move. R5 local behavior is valid; missing visibility is lifecycle registration.

## Target-selection table

| Candidate file | Role | Needs patch? | Why / why not |
|---|---|---|---|
| `types-CdFhLeaX.js` | Registry storage/API | no | Confirms shared state and clear/restore mechanics, but patching storage API would be a broad registry rewrite. |
| `loader-Bfm_uDYG.js` | Lifecycle clear/restore/register/cache/activate | yes | Proven lifecycle target. It clears R5 top-level registration and owns durable registration into both `pluginCommands` and `registry.commands`. |
| `server-methods-Dw6hzI_j.js` | `commands.list` handler | no | Already reads `listPluginCommands()` and active `registry.commands`; hardcoding here would bypass registry. |
| `commands-D2qp4St4.js` | Slash matcher/native handler | no for first patch | Existing R5 handler works locally and live paths import it. Missing issue is not matcher code; it is lifecycle registration. |

## Proven final patch target

Primary target file:

`/home/stickai/.npm-global/lib/node_modules/openclaw/dist/loader-Bfm_uDYG.js`

Target functions/regions:

1. `clearActivatedPluginRuntimeState()` — proves why R5 top-level state is cleared.
2. `loadOpenClawPlugins()` cache restore path — after `restorePluginCommands(cached.state.commands ?? [])` and before `activatePluginRegistry(...)`.
3. `loadOpenClawPlugins()` normal path — after plugin registrations and before `setCachedPluginRegistry(...)` / `activatePluginRegistry(...)`.
4. `registerCommand(record, command)` is the model for durable registration, but R7 should avoid broad changes inside the generic API if a small GE2 seeding helper can call existing APIs.

Supporting target file if needed:

`/home/stickai/.npm-global/lib/node_modules/openclaw/dist/commands-D2qp4St4.js`

Only needed if the loader patch needs a reusable exported GE2 command-definition factory rather than duplicating the already-present R5 handler in loader. If used, snapshot already exists.

## Proposed R7 patch shape

Preferred lifecycle-correct shape:

1. Add a small GE2 seed helper in `loader-Bfm_uDYG.js` near loader lifecycle helpers.
2. The helper should create one GE2 command definition with:
   - `name: "ge2"`
   - `nativeName: "ge2"`
   - `nativeNames: { default: "ge2", telegram: "ge2" }`
   - `description: "Run and inspect native GE2 durable command-surface operations."`
   - `acceptsArgs: true`
   - `requireAuth: true`
   - no hidden/private/internal/no-list flags
   - handler backed by existing GE2 runtime (`ge2_command_router.mjs` + `ge2_dispatcher.mjs`)
3. Seed via existing registry semantics, not `server-methods`:
   - ensure `pluginCommands` has `/ge2`, and
   - ensure `registry.commands` has one GE2 entry before cache/activation.
4. Call helper in both lifecycle branches:
   - cached restore path, after `restorePluginCommands(...)` and before `activatePluginRegistry(...)`
   - normal load path, after plugin registration loop and before `setCachedPluginRegistry(...)` / `activatePluginRegistry(...)`
5. Guard idempotently:
   - do not add duplicate `/ge2` into `pluginCommands`
   - do not add duplicate `registry.commands` entry if command name `ge2` already exists
6. Preserve existing commands and filters.

## Why not patch `server-methods`

`server-methods` is already reading both command sources. A patch there would be a hardcoded display shim and could make `/ge2` appear without making native matching durable. That violates R7’s no-hardcoded-commands-list requirement.

## Why not patch only `commands-D2qp4St4.js`

A lazy `ensureNativeGe2CommandRegistered()` before every list/match call could make the symptom disappear, but it would not register GE2 into the loader-owned lifecycle/cache that backs `registry.commands`. R7’s requirement is lifecycle registration, so the durable target is loader.

## Rollback/reverser plan

No rollback is needed for this source/snapshot plan because production was not mutated.

For the future R7 production patch:

- use `snapshots_20260630T0800Z/loader-Bfm_uDYG.js` as loader preimage.
- if `commands-D2qp4St4.js` is also changed, use `snapshots_20260630T0800Z/commands-D2qp4St4.js` as command preimage.
- write a manifest before mutation with source path, snapshot path, old SHA, new SHA, and patch markers.
- write a reverser script that restores the exact snapshot bytes atomically.

Rollback triggers for R7 apply:

- Gateway health/admin fails.
- existing commands `pair`, `dreaming`, `phone`, or `voice` disappear.
- fake command appears.
- `/ge2` remains absent after the confirmed lifecycle target patch.
- command matching degrades.
- `/ge2 help` or `/ge2 status` falls through to model/chat after visibility gate passes.

## R7 pass gate after future mutation

- Gateway health/admin PASS.
- `commands.list` shows `/ge2` for default, telegram/both, and telegram/text.
- `pair`, `dreaming`, `phone`, `voice` preserved.
- fake command absent.
- only after `/ge2` visibility: live `/ge2 help` returns native GE2 response.
- live `/ge2 status` returns native GE2 response.
- no model/chat fallthrough.
- artifact manifest and reverser validate.

## Current stop point

Stop before production mutation.

The final patch target is proven and snapshotted as `loader-Bfm_uDYG.js`; exact future patch should be limited to lifecycle seeding and guarded against duplicates.
