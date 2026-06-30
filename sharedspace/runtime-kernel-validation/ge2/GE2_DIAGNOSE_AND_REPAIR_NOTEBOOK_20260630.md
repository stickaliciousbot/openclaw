# GE2 Diagnose and Repair Notebook — 2026-06-30

Final status update: this is now a historical R5-era ledger. Use `sharedspace/runtime-kernel-validation/ge2/GE2_IMPLEMENTATION_DIAGNOSE_AND_REPAIR_NOTEBOOK_20260630.md` for the cleaned-up from-scratch implementation/diagnose/repair notebook. Final amended classification: `GE2_NATIVE_COMMAND_SURFACE_PROMOTED_PUSH_BLOCKED_HANDOFF_PRESERVED`.

Historical status at time of this notebook snapshot: **R5 HOLD — patch installed and locally validated; awaiting Gateway PID turnover**

Historical classification: `GE2_R5_HOLD_PATCH_APPLIED_LOCAL_PASS_AWAITING_GATEWAY_PID_TURNOVER`

This notebook is the concrete GE2 repair ledger for the current production install. It supersedes generic plugin-visibility attempts as the working operator notebook for `/ge2` native command surface repair.

---

## 0. Non-negotiable operating rules

- Do **not** retry cron closeout apply from this notebook.
- Do **not** claim GE2 PASS until live Gateway RPC `commands.list` exposes `/ge2` after a PID turnover.
- Do **not** treat local import tests as production surface proof.
- Do **not** create placeholder GE2 success.
- Do **not** hardcode `/ge2` into only `commands.list`; `/ge2` must dispatch through the GE2 router/dispatcher/runtime.
- Preserve auth: `/ge2` command handler is registered with `requireAuth:true`.
- Preserve unrelated plugin commands: `pair`, `dreaming`, `phone`, `voice` must remain visible.
- Preserve fake-negative: fake command must remain absent.
- Snapshot before mutation; rollback path must remain single-command.

---

## 1. Current known state

### Gateway

- Last live Gateway PID checked: `300576`
- Gateway health: connectivity OK, admin-capable
- Important blocker: PID has **not** turned over since R5 patch was installed, so live Gateway is still serving the old process image.

Evidence:

- `ge2_r5_native_command_surface/gateway_status_after_async_completion_20260630.txt`
- `ge2_r5_native_command_surface/restart_hold_20260630T0726Z.json`

### Installed OpenClaw runtime

- Runtime install root: `/home/stickai/.npm-global/lib/node_modules/openclaw`
- Gateway command: `/usr/bin/node /home/stickai/.npm-global/lib/node_modules/openclaw/dist/index.js gateway --port 18789`
- Gateway log: `/tmp/openclaw/openclaw-2026-06-30.log`

### GE2 native kit

Async approved file listing confirmed these files exist:

- `ge2-native-runtime/examples/channel_command_mapping.json`
- `ge2-native-runtime/examples/demo_run.mjs`
- `ge2-native-runtime/examples/ge2_run_request.json`
- `ge2-native-runtime/src/ge2_artifacts.mjs`
- `ge2-native-runtime/src/ge2_command_router.mjs`
- `ge2-native-runtime/src/ge2_dispatcher.mjs`
- `ge2-native-runtime/src/ge2_ledger.mjs`
- `ge2-native-runtime/src/ge2_milestones.mjs`
- `ge2-native-runtime/src/ge2_runtime.mjs`
- `ge2-native-runtime/src/ge2_snapshot.mjs`

Evidence file:

- `ge2_r5_native_command_surface/ge2_kit_file_listing_from_async_406ce933_20260630.txt`

---

## 2. Failure chain diagnosis

### R0 / R1 finding

The GE2 hook/plugin could load and report registration success, and plugin-manager views eventually showed:

- plugin: `ge2-command`
- status: `loaded`
- commands: `["ge2"]`

But live public command surfaces still omitted `/ge2`.

### R2 finding

The public RPC command list is built through:

- `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/server-methods-Dw6hzI_j.js`
- `commandsHandlers["commands.list"]`
- `buildCommandsListResult()`
- `buildPluginCommandEntries()`
- `listPluginCommands()` from `commands-D2qp4St4.js`

The loss point was not user auth or command-list filtering. The loss point was a registry/module-realm boundary: the hook-side registrar could see `/ge2`, while the public RPC path read another registry.

### R3 finding

Singleton/effective-registry bridging was insufficient. After restart, Gateway remained healthy but public `commands.list` still returned:

- count: `60`
- `ge2Present:false`
- `fakePresent:false`
- plugin commands: `pair,dreaming,phone,voice`

Classification: `GE2_R3_BLOCKED_LIVE_COMMANDS_LIST_OMITS_GE2_AFTER_SINGLETON_AND_EFFECTIVE_REGISTRY_BRIDGE`

### R4 finding

R4 patched the public RPC builder to merge validated active plugin registry commands into `buildPluginCommandEntries()`.

Patch target:

- `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/server-methods-Dw6hzI_j.js`

Patch markers present:

- `collectActiveRegistryPluginCommandEntries`
- bridge call in `buildPluginCommandEntries()`
- hidden/internal/private/no-list filters

After Gateway restart to PID `300576`, live `commands.list` still omitted `/ge2` on all surfaces:

- default: count `60`, `ge2Present:false`, `fakePresent:false`, plugins `pair,dreaming,phone,voice`
- telegram/both: count `60`, `ge2Present:false`, `fakePresent:false`, plugins `pair,dreaming,phone,voice`
- telegram/text: count `60`, `ge2Present:false`, `fakePresent:false`, plugins `pair,dreaming,phone,voice`

Classification: `GE2_R4_BLOCKED_AUTHORITATIVE_BUILDER_BRIDGE_DID_NOT_EXPOSE_GE2`

Evidence:

- `ge2_r4_authoritative_rpc_command_list_builder_bridge/final_blocked_summary.json`
- `ge2_r4_authoritative_rpc_command_list_builder_bridge/GE2_R4_FINAL_BLOCKED.md`

### R5 diagnosis shift

The attached native command surface spec made the correct target explicit: `/ge2` should not depend on the fragile hook/plugin command visibility path. It should be a direct native command surface backed by the existing deterministic GE2 router/dispatcher/runtime.

Therefore R5 shifted from “make plugin manager command visible” to “register a direct native `/ge2` command handler in the authoritative plugin command map used by both command listing and command matching.”

---

## 3. R5 repair installed

### Patch target

Only one installed bundle file was mutated:

```text
/home/stickai/.npm-global/lib/node_modules/openclaw/dist/commands-D2qp4St4.js
```

### Snapshot and rollback

Manifest:

```text
sharedspace/runtime-kernel-validation/ge2/ge2_r5_native_command_surface/install_manifest_20260630T0715Z.json
```

Reverser:

```text
sharedspace/runtime-kernel-validation/ge2/ge2_r5_native_command_surface/reverser_20260630T0715Z.mjs
```

Backup:

```text
sharedspace/runtime-kernel-validation/ge2/ge2_r5_native_command_surface/snapshots_20260630T0715Z/commands-D2qp4St4.js.pre-ge2-r5
```

Hashes:

- before: `fad314e2005e0481f724afe5c0dbabb3888d6756bd0812324862ae9a96a10b5b`
- after: `660af5de5094031703c6f62260cb118643043275999bb68ff53e806796e250eb`

Patch markers:

- `GE2_R5_NATIVE_COMMAND_SURFACE_START:true`
- `GE2_R5_NATIVE_COMMAND_SURFACE_END:true`
- `ensureNativeGe2CommandRegistered:true`
- `Ge2Dispatcher:true`
- `noPlaceholderSuccess:true`

### What the patch does

At module load, R5 registers `/ge2` directly into the authoritative `pluginCommands` map if it is not already present.

Registered command shape:

- `name: "ge2"`
- `nativeName: "ge2"`
- `nativeNames: { default: "ge2", telegram: "ge2" }`
- `description: "Run and inspect native GE2 durable command-surface operations."`
- `acceptsArgs: true`
- `requireAuth: true`
- `pluginId: "ge2-native"`
- `pluginName: "GE2 Native Command Surface"`
- `ownership: "reserved"`
- `handler: handleNativeGe2Command`

The handler dynamically imports:

- `file:///home/stickai/.openclaw/workspace/ge2-native-runtime/src/ge2_command_router.mjs`
- `file:///home/stickai/.openclaw/workspace/ge2-native-runtime/src/ge2_dispatcher.mjs`

State and artifacts go to:

- state: `/home/stickai/.openclaw/workspace/state/ge2-native`
- artifacts: `/home/stickai/.openclaw/workspace/state/ge2-native/artifacts`

Supported commands:

- `/ge2 help`
- `/ge2 status`
- `/ge2 status <run_id>`
- `/ge2 run <task>`
- `/ge2 artifacts <run_id>`
- `/ge2 cancel <run_id>`

---

## 4. Local validation already passed

### Import / match validation

Evidence:

```text
sharedspace/runtime-kernel-validation/ge2/ge2_r5_native_command_surface/local_import_validation_20260630.json
```

Result:

- module import succeeded
- exported command list had `/ge2`
- `matchPluginCommand('/ge2 status', { channel:'telegram' })` matched
- match args: `status`
- command auth preserved: `requireAuth:true`

### Handler validation

Evidence:

```text
sharedspace/runtime-kernel-validation/ge2/ge2_r5_native_command_surface/local_handler_validation_20260630.json
```

Result:

- `/ge2 help` returned canonical help text
- `/ge2 status` returned deterministic `RUN_NOT_FOUND` before any run
- `/ge2 run r5-local-validation` returned a run id
- run id: `ge2-20260630072413-c1e88e51`
- `/ge2 status ge2-20260630072413-c1e88e51` returned:
  - status: `completed`
  - milestones: `7`
  - artifacts: `1`
  - errors: `0`
- `/ge2 artifacts ge2-20260630072413-c1e88e51` returned artifact:
  - `run-summary.json`
  - sha256: `bf07cd46c95908385c988ce8fc788ebc3ceddbb619fcedd7645c2b5e5030f4ce`
  - path: `/home/stickai/.openclaw/workspace/state/ge2-native/artifacts/ge2-20260630072413-c1e88e51/run-summary.json`

Local conclusion: the installed file contains a working `/ge2` command handler, and the handler dispatches through the GE2 runtime. This is not yet live production proof because Gateway PID has not turned over.

---

## 5. Live validation remains blocked by PID turnover

Restart was requested after R5 install, but live Gateway remained on old PID `300576`.

Live command matrix after install, before PID turnover:

Evidence:

```text
sharedspace/runtime-kernel-validation/ge2/ge2_r5_native_command_surface/commands_list_r5_summary.json
```

Results:

- default: count `60`, `ge2Present:false`, `fakePresent:false`, pluginNames `pair,dreaming,phone,voice`
- telegram/both: count `60`, `ge2Present:false`, `fakePresent:false`, pluginNames `pair,dreaming,phone,voice`
- telegram/text: count `60`, `ge2Present:false`, `fakePresent:false`, pluginNames `pair,dreaming,phone,voice`

Interpretation:

- This is consistent with old-process behavior.
- It is not proof the patch failed.
- It is not a rollback trigger because the running Gateway remains healthy and the old command surface is intact.

---

## 6. Resume procedure after restart/PID turnover

Run these checks only after a restart sentinel or explicit sign that Gateway may have turned over.

### Step 1 — verify PID and health

```bash
openclaw gateway status | tee sharedspace/runtime-kernel-validation/ge2/ge2_r5_native_command_surface/gateway_status_resume_$(date -u +%Y%m%dT%H%M%SZ).txt
```

PASS conditions:

- PID is not `300576`
- connectivity probe OK
- admin-capable

If PID is still `300576`, remain HOLD. Do not claim PASS.

### Step 2 — live command-list matrix

```bash
node sharedspace/runtime-kernel-validation/ge2/ge2_r5_native_command_surface/live_commands_list_check_20260630.mjs
```

PASS conditions for each surface:

- default: `/ge2` present
- telegram/both: `/ge2` present
- telegram/text: `/ge2` present or, if only native/both surface lists it, document exact surface semantics and verify Telegram command handling directly
- fake command absent
- `pair,dreaming,phone,voice` preserved

If `/ge2` is absent after PID turnover, R5 is BLOCKED and the next target is import/chunk identity: prove whether the live process loaded patched `commands-D2qp4St4.js` SHA `660af5...` or another chunk.

### Step 3 — live direct command smoke

Use the smallest safe command first:

```text
/ge2 help
```

Expected:

```text
GE2 native commands:
/ge2 run <task>
/ge2 status
/ge2 status <run_id>
/ge2 artifacts <run_id>
/ge2 cancel <run_id>
/ge2 help
```

Then:

```text
/ge2 status
```

Expected:

- Either latest run status if ledger exists, or deterministic `RUN_NOT_FOUND` if no run exists.
- No model-mediated response.
- No generic assistant answer.

Then a bounded run:

```text
/ge2 run r5-live-smoke
```

Expected:

- run id returned
- run record persisted under `state/ge2-native/runs/`
- milestones persisted
- artifact written and hashed

Then:

```text
/ge2 status <run_id>
/ge2 artifacts <run_id>
```

Expected:

- status includes completed/failed/cancelled terminal state
- artifacts include file path and sha256

### Step 4 — final artifact write

If all live checks pass, write:

- `ge2_r5_native_command_surface/final_pass_summary.json`
- `ge2_r5_native_command_surface/GE2_R5_FINAL_PASS.md`
- `ge2_r5_native_command_surface/final_file_manifest_20260630.json`

Classification:

```text
GE2_R5_NATIVE_COMMAND_SURFACE_PASS_LIVE_COMMANDS_LIST_AND_DISPATCH_VALIDATED
```

If command list passes but dispatch fails, classification should be:

```text
GE2_R5_BLOCKED_COMMAND_VISIBLE_DISPATCH_FAILED
```

If PID turns over but `/ge2` remains absent, classification should be:

```text
GE2_R5_BLOCKED_PATCH_NOT_LOADED_OR_ALTERNATE_COMMAND_CHUNK
```

---

## 7. Rollback procedure

Rollback is available but should not be used merely because the old PID has not turned over.

Rollback trigger conditions:

- Gateway fails health/admin after loading patched file
- command matching crashes Gateway
- `/ge2` degrades unrelated command surfaces
- hidden/fake/internal command exposure appears
- existing plugin commands disappear unexpectedly after PID turnover

Rollback command:

```bash
node sharedspace/runtime-kernel-validation/ge2/ge2_r5_native_command_surface/reverser_20260630T0715Z.mjs
```

After rollback:

1. restart Gateway or wait for PID turnover if restart is already pending
2. verify health/admin
3. verify `commands.list` returns old known-safe state:
   - count about `60`
   - `/ge2` absent
   - fake absent
   - `pair,dreaming,phone,voice` present

Rollback classification:

```text
GE2_R5_ROLLED_BACK_<REASON>
```

---

## 8. Specific next diagnostic if R5 blocks after PID turnover

If PID changes and `/ge2` is still absent:

1. Prove loaded module identity for the live Gateway process.
2. Specifically verify whether live process imported:
   - `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/commands-D2qp4St4.js`
   - SHA `660af5de5094031703c6f62260cb118643043275999bb68ff53e806796e250eb`
3. If not, locate the alternate command chunk actually imported by Gateway.
4. Patch only that alternate chunk with snapshot/reverser.
5. Do not return to plugin-manager bridges unless the live command matcher itself demonstrably reads plugin manager registry entries.

Do **not** broad-grep the whole workspace. Use targeted installed `dist/` chunk identity checks and exact known symbols:

- `matchPluginCommand`
- `executePluginCommand`
- `listPluginCommands`
- `getChatCommands`
- `commands.list`
- `buildPluginCommandEntries`

---

## 9. Artifact index

### R4 final blocked

- `sharedspace/runtime-kernel-validation/ge2/ge2_r4_authoritative_rpc_command_list_builder_bridge/final_blocked_summary.json`
- `sharedspace/runtime-kernel-validation/ge2/ge2_r4_authoritative_rpc_command_list_builder_bridge/GE2_R4_FINAL_BLOCKED.md`
- `sharedspace/runtime-kernel-validation/ge2/ge2_r4_authoritative_rpc_command_list_builder_bridge/final_file_manifest_20260630.json`

### R5 install and validation

- `sharedspace/runtime-kernel-validation/ge2/ge2_r5_native_command_surface/install_ge2_native_surface_20260630.mjs`
- `sharedspace/runtime-kernel-validation/ge2/ge2_r5_native_command_surface/install_manifest_20260630T0715Z.json`
- `sharedspace/runtime-kernel-validation/ge2/ge2_r5_native_command_surface/reverser_20260630T0715Z.mjs`
- `sharedspace/runtime-kernel-validation/ge2/ge2_r5_native_command_surface/local_import_validation_20260630.json`
- `sharedspace/runtime-kernel-validation/ge2/ge2_r5_native_command_surface/local_handler_validation_20260630.json`
- `sharedspace/runtime-kernel-validation/ge2/ge2_r5_native_command_surface/commands_list_r5_summary.json`
- `sharedspace/runtime-kernel-validation/ge2/ge2_r5_native_command_surface/restart_hold_20260630T0726Z.json`
- `sharedspace/runtime-kernel-validation/ge2/ge2_r5_native_command_surface/ge2_kit_file_listing_from_async_406ce933_20260630.txt`

### Runtime files

- `ge2-native-runtime/src/ge2_command_router.mjs`
- `ge2-native-runtime/src/ge2_dispatcher.mjs`
- `ge2-native-runtime/src/ge2_runtime.mjs`
- `ge2-native-runtime/src/ge2_ledger.mjs`
- `ge2-native-runtime/src/ge2_artifacts.mjs`
- `ge2-native-runtime/src/ge2_milestones.mjs`
- `ge2-native-runtime/src/ge2_snapshot.mjs`

---

## 10. Current close-loop statement

GE2 is not fixed live yet. The specific native repair is installed and locally proven. The only accepted current state is:

```text
GE2_R5_HOLD_PATCH_APPLIED_LOCAL_PASS_AWAITING_GATEWAY_PID_TURNOVER
```

The next operator action is to wait for or trigger a legitimate Gateway PID turnover, then run the R5 live validation gates. No cron closeout retry is authorized by this notebook.
