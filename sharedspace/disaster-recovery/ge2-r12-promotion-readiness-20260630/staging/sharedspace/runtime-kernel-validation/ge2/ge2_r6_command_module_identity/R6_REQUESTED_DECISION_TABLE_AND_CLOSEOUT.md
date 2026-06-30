# GE2-R6 Requested Decision Table and Closeout

Final classification: `GE2_R6_COMMAND_REGISTRY_CACHE_IDENTIFIED_NO_MUTATION`

Production touched: **no**

## Trace table

| Question | Result |
|---|---|
| Live Gateway PID | `303370` |
| `/ge2` visible in `commands.list` | no |
| Patched file exists | yes |
| Patched file SHA matches expected | yes — `660af5de5094031703c6f62260cb118643043275999bb68ff53e806796e250eb` |
| Live process imports patched file | yes |
| Actual `commands.list` handler file | `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/server-methods-Dw6hzI_j.js` |
| Actual command registry source file | `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/types-CdFhLeaX.js` plus loader lifecycle in `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/loader-Bfm_uDYG.js` |
| Actual slash-command matcher file | `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/commands-D2qp4St4.js`, imported through `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/bot-native-commands.runtime-OmS7iYqz.js` and Telegram dispatch in `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/bot-Ds7bwqAK.js` |
| Registry cached at startup | yes — in-memory `pluginCommands`/runtime registry state is built/restored during loader lifecycle |
| Alternate command chunk found | no — refined trace shows actual serving path imports the patched chunk |
| Safe patch target identified | not as a single final file yet; target class is loader/registry lifecycle that durably builds `registry.commands`/`pluginCommands` like `pair`, `dreaming`, `phone`, `voice` |
| Production mutation performed | no |

## Decision branch

Branch C applies:

`GE2_R6_COMMAND_REGISTRY_CACHE_IDENTIFIED_NO_MUTATION`

Reason: the live Gateway process imports the patched `commands-D2qp4St4.js`, but `/ge2` is still absent from live `commands.list`. Therefore the R5 top-level `pluginCommands.set("/ge2", ...)` is not durable through registry startup/loader lifecycle. The registry is cleared/restored/rebuilt or catalogued in a way that excludes the ad-hoc top-level registration.

## Required R6 output

- R6 diagnosis artifact path: `sharedspace/runtime-kernel-validation/ge2/ge2_r6_command_module_identity/final_diagnosis_summary.json`
- Trace table: this file, plus `GE2_R6_COMMAND_MODULE_IDENTITY_DIAGNOSIS.md` and `GE2_R6_REFINED_REGISTRY_LIFECYCLE_TRACE.md`
- Live serving file/path: `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/server-methods-Dw6hzI_j.js`
- Patch target recommendation: R7 should target the loader/registry lifecycle path that durably registers commands, not arbitrary command chunks and not plugin-manager bridges.
- Rollback recommendation: no rollback from R6. For R7, snapshot target files, write manifest/reverser, and rollback if Gateway health fails, existing commands disappear, fake appears, `/ge2` remains absent after confirmed target patch, or command matching degrades.
- Final classification: `GE2_R6_COMMAND_REGISTRY_CACHE_IDENTIFIED_NO_MUTATION`
- Production touched: no

## R7 repair plan requirements

- Snapshot target file(s) before mutation.
- Write manifest.
- Write reverser.
- Patch only the actual loader/registry lifecycle path once exact file/function is proven.
- Preserve existing commands: `pair`, `dreaming`, `phone`, `voice`.
- Keep fake command absent.
- Preserve local GE2 runtime behavior.
- Restart Gateway once.
- Health/admin gate.
- Live `commands.list` gate.
- Only if `/ge2` visible, run live `/ge2 help` smoke.
- Rollback if any hard rollback trigger fires.

## R7 pass gate

- Gateway health/admin PASS.
- `commands.list` shows `/ge2` for default and Telegram surfaces.
- Existing commands preserved.
- Fake command absent.
- `/ge2 help` returns native GE2 response.
- `/ge2 status` returns native GE2 response.
- No model/chat fallthrough.
- Artifacts written.
- Manifest/reverser validated.
