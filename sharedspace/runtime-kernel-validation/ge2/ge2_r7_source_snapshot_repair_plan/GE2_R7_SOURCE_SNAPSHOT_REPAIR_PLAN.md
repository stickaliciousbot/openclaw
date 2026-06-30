# GE2-R7 Source/Snapshot Repair Plan — 2026-06-30

Classification: `GE2_R7_SOURCE_SNAPSHOT_REPAIR_PLAN_NO_PRODUCTION_MUTATION`

Production mutation: **false**
Gateway restart: **false**
Live /ge2 smoke: **false**

## Snapshots

- types: /home/stickai/.npm-global/lib/node_modules/openclaw/dist/types-CdFhLeaX.js -> /home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/snapshots_20260630T0800Z/types-CdFhLeaX.js (864d569218baa6a23bfaa48547947e503ea2343929e5f78171af4e031dad202f)
- loader: /home/stickai/.npm-global/lib/node_modules/openclaw/dist/loader-Bfm_uDYG.js -> /home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/snapshots_20260630T0800Z/loader-Bfm_uDYG.js (ff2d89b04d1d5f7fb727f586a78fe92e0b52ffbe43a484551475cf140b53feb0)
- serverMethods: /home/stickai/.npm-global/lib/node_modules/openclaw/dist/server-methods-Dw6hzI_j.js -> /home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/snapshots_20260630T0800Z/server-methods-Dw6hzI_j.js (638aa2dbf4cc7a9758b0d3f5679ec745e329e0f8f164408731a2107357993986)
- commands: /home/stickai/.npm-global/lib/node_modules/openclaw/dist/commands-D2qp4St4.js -> /home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/snapshots_20260630T0800Z/commands-D2qp4St4.js (660af5de5094031703c6f62260cb118643043275999bb68ff53e806796e250eb)

## Target-selection table

| Candidate file | Role | Needs patch? | Why / why not |
|---|---|---|---|
| /home/stickai/.npm-global/lib/node_modules/openclaw/dist/types-CdFhLeaX.js | Registry storage/API: owns pluginCommands state, clear/restore/listRegistered APIs. | no for first R7 patch | It is lower-level shared state. Patching storage would broaden behavior globally. It confirms lifecycle cache/reset source but not the minimal durable GE2 registration site. |
| /home/stickai/.npm-global/lib/node_modules/openclaw/dist/loader-Bfm_uDYG.js | Plugin lifecycle: clears/restores/registers plugin commands, pushes registry.commands, sets active registry. | likely yes after exact call-order proof | This is where durable command records like pair/dreaming/phone/voice enter registry.commands and pluginCommands. R5 top-level registration is lost because this lifecycle rebuilds registry state. |
| /home/stickai/.npm-global/lib/node_modules/openclaw/dist/server-methods-Dw6hzI_j.js | RPC commands.list handler and formatter. | no | It already imports the patched command chunk and lists plugin commands. Hardcoding GE2 here would violate design and duplicate descriptors on list calls. |
| /home/stickai/.npm-global/lib/node_modules/openclaw/dist/commands-D2qp4St4.js | Slash matcher/native command execution and plugin command list helpers; contains R5 GE2 handler patch. | no additional patch until loader lifecycle target proven | Local matching/handler works. Live imports it. Missing visibility is lifecycle/cache exclusion, not command handler absence. |

## Recommendation

Prefer durable registration through existing registerCommand lifecycle using a GE2 command definition so both pluginCommands and registry.commands/pluginCatalog.commands include ge2. Do not hardcode in server-methods and do not duplicate descriptors per commands.list call.

Exact final mutation target is not yet authorized as a single file/function; one more pre-patch call-order trace inside `loader-Bfm_uDYG.js` is required before production mutation.
