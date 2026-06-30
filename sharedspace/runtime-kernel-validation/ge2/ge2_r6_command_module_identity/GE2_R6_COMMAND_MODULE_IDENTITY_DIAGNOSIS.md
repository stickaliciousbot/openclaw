# GE2-R6 Command Module Identity Diagnosis — 2026-06-30

Classification: `GE2_R6_COMMAND_MODULE_IDENTITY_DIAGNOSIS_ONLY`

Mutation: **false**

## Trace table

| Question | Result | Evidence |
|---|---|---|
| Current OpenClaw version | captured | OpenClaw 2026.5.7 (9338825) |
| Gateway PID/health/admin | PASS | pid=303370; connectivityOk=true; adminCapable=true |
| Live commands.list baseline | R5_BLOCK_REPRODUCED | default:count=60,ge2=false,fake=false,plugins=pair/dreaming/phone/voice; telegram_both:count=60,ge2=false,fake=false,plugins=pair/dreaming/phone/voice; telegram_text:count=60,ge2=false,fake=false,plugins=pair/dreaming/phone/voice |
| Patched chunk on disk | ON_DISK_PATCH_PRESENT | /home/stickai/.npm-global/lib/node_modules/openclaw/dist/commands-D2qp4St4.js; sha=660af5de5094031703c6f62260cb118643043275999bb68ff53e806796e250eb; expected=660af5de5094031703c6f62260cb118643043275999bb68ff53e806796e250eb |
| commands.list serving chunk | CANDIDATE_FOUND | agents-DuBZxb_5.js; symbols=commands.list |
| commands.list imports patched command chunk | NO_STATIC_IMPORT_EDGE_TO_PATCHED_CHUNK | ./agents.commands.add-C-_oLjHs.js->agents.commands.add-C-_oLjHs.js sha=5085c80a1c304c7b846f0bd4986dff5903eec9ec00d0aed818911380afb13288 patched=false; ./registry-BkuUNjzB.js->registry-BkuUNjzB.js sha=708c24a767e2e012a220f88eeefcb9cee9fe84f8f7a7ffc3bb2c019c163ab78c patched=false |
| Command matcher chunk candidates | CANDIDATES_FOUND | bot-Ds7bwqAK.js:matchPluginCommand/executePluginCommand/maybeResolveTextAlias/normalizeCommandBody/pair/voice; bot-native-commands.runtime-OmS7iYqz.js:matchPluginCommand/executePluginCommand; command-status-builders-B_8xsDoR.js:listPluginCommands/pluginCommands; commands-D2qp4St4.js[R5]:GE2_R5_NATIVE_COMMAND_SURFACE_START/ensureNativeGe2CommandRegistered/matchPluginCommand/executePluginCommand/listPluginCommands/listEffectivePluginCommands/pluginCommands; commands-handlers.runtime-DlESKC_s.js:matchPluginCommand/executePluginCommand/resolveTextCommand/normalizeCommandBody/pair/voice; loader-Bfm_uDYG.js:pluginCommands/clearPluginCommands/restorePluginCommands/registerCommand/pair/dreaming/voice; server-methods-Dw6hzI_j.js:listPluginCommands/commands.list/buildCommandsListResult/buildPluginCommandEntries/pair/dreaming/voice; types-CdFhLeaX.js:pluginCommands/pluginCommands.clear/clearPluginCommands/restorePluginCommands |
| Registry cache/reset candidates | CACHE_OR_RESET_PATHS_FOUND | loader-Bfm_uDYG.js:pluginCommands/clearPluginCommands/restorePluginCommands/registerCommand/pair/dreaming/voice; types-CdFhLeaX.js:pluginCommands/pluginCommands.clear/clearPluginCommands/restorePluginCommands |
| Plugin manager GE2 state | GE2_PLUGIN_MANAGER_LOADED | status=loaded; commands=["ge2"]; source=/home/stickai/.openclaw/extensions/ge2-command/index.mjs |

## Preliminary conclusion

commands.list static import edge does not point to patched chunk; locate alternate imported command chunk before any patch.

## Hard stop

No rollback, no live `/ge2` smoke, no cron closeout apply, and no production patch were performed.
