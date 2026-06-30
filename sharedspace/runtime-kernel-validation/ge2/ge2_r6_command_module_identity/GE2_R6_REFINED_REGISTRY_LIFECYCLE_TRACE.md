# GE2-R6 Refined Registry Lifecycle Trace

Classification: `GE2_R6_REFINED_COMMAND_PATH_IMPORTED_PATCHED_CHUNK_BUT_REGISTRY_LIFECYCLE_EXCLUDES_GE2`

Mutation: **false**

## Correction

The earlier preliminary note that commands.list did not point to the patched chunk was too broad because it selected an agents CLI string candidate. The actual Gateway RPC server-methods chunk does import the patched commands-D2qp4St4.js.

## Actual commands.list path

- File: `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/server-methods-Dw6hzI_j.js`
- Imports patched chunk: **true**
- Patched chunk SHA: `660af5de5094031703c6f62260cb118643043275999bb68ff53e806796e250eb`
- R5 marker present: **true**

## Telegram/native matching path

- Telegram bot registers native plugin commands from `pluginCatalog.commands`.
- Handler calls `nativeCommandRuntime.matchPluginCommand(commandBody)`.
- `bot-native-commands.runtime-OmS7iYqz.js` imports `./commands-D2qp4St4.js`.

## Diagnosis

The actual Gateway RPC commands.list path imports the patched command chunk, and Telegram native command runtime also imports the patched command chunk for matching/execution. Because live commands.list still omits /ge2 after PID turnover, the R5 top-level pluginCommands.set(/ge2) is not durable through plugin registry lifecycle: it is likely cleared/rebuilt by loader registry activation, or Telegram native command catalog is snapshotted before that ad-hoc registration. The next confirmed patch target should be the plugin loader/registry activation path that builds registry.commands and pluginCommands, not another arbitrary command file and not plugin-manager bridges.

## Hard stop

No rollback, no live `/ge2` smoke, no cron closeout apply, no plugin-manager bridge patch, and no production mutation were performed.
