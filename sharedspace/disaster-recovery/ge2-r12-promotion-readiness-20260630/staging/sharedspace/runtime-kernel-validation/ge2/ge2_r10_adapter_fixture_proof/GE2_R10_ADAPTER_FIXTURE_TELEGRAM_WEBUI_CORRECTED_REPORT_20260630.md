# GE2-R10 Adapter Fixture Telegram/WebUI Corrected Report

Final classification: `GE2_R10_ADAPTER_FIXTURE_TELEGRAM_WEBUI_PASS_P3_PENDING`

Proof level: **P2 adapter fixture only**  
No P3 claim: **true**

## Correction note

The raw R10 report emitted `GE2_R10_ADAPTER_FIXTURE_PARITY_FAIL_P2_BLOCKED`, but both per-surface adapter fixtures passed.

The raw parity failure came from an extra assumed `webchat_both` `commands.list` visibility gate. `webchat_text` showed `/ge2` present exactly once and existing commands preserved, and the actual WebUI P2 fixture executed through `commands-handlers.runtime-DlESKC_s.js` `handlePluginCommand`. Therefore `webchat_both` is not a valid blocker for this P2 adapter execution proof.

No adapter fixture run was rerun for this correction.

## Telegram adapter fixture — PASS

Adapter path:

- exported `createTelegramBot` from `bot-Ds7bwqAK.js`
- synthetic grammy update through `bot.handleUpdate`
- fake Telegram API transport captured sends; no external Telegram network used
- native command path: `registerTelegramNativeCommands` builds `commandBody`, loads Telegram native runtime, calls `matchPluginCommand()`, then `executePluginCommand()`

Commands proven:

1. `/ge2 help`
2. `/ge2 status`
3. `/ge2 run r10-telegram-adapter-fixture-smoke`
4. `/ge2 status ge2-20260630093527-d6193cf1`
5. `/ge2 artifacts ge2-20260630093527-d6193cf1`

Run ID: `ge2-20260630093527-d6193cf1`

Status: `completed`  
Milestones: `7`  
Artifacts: `1`  
Errors: `0`

Artifact:

`/home/stickai/.openclaw/workspace/state/ge2-native/artifacts/ge2-20260630093527-d6193cf1/run-summary.json`

SHA256 reported/computed:

`5a07d2983bd65fbee07a605ae4eb76214ee86bf69c98abed17e32e78f93e7d5c`

Hash match: yes

Hard gates:

- fixture entered Telegram adapter/native command path: yes
- matched native `/ge2`: yes
- pluginId `ge2-native`: yes
- `continueAgent:false`: yes
- no model/chat fallthrough: yes
- native GE2 responses: yes
- durable ledger entry: yes
- milestones emitted: yes
- artifact exists: yes
- artifact SHA matches: yes
- status retrieves exact run_id: yes
- artifacts retrieves exact run_id: yes
- bounded/compressed responses: yes

## WebUI adapter fixture — PASS

Adapter path:

- `commands-handlers.runtime-DlESKC_s.js`
- `loadCommandHandlers()[0]` / `handlePluginCommand`
- WebUI-shaped command params with `channel:'webchat'`
- code path: `allowTextCommands -> matchPluginCommand(commandBodyNormalized,{channel:'webchat'}) -> executePluginCommand() -> shouldContinue=false`

Commands proven:

1. `/ge2 help`
2. `/ge2 status`
3. `/ge2 run r10-webui-adapter-fixture-smoke`
4. `/ge2 status ge2-20260630093530-398319fe`
5. `/ge2 artifacts ge2-20260630093530-398319fe`

Run ID: `ge2-20260630093530-398319fe`

Status: `completed`  
Milestones: `7`  
Artifacts: `1`  
Errors: `0`

Artifact:

`/home/stickai/.openclaw/workspace/state/ge2-native/artifacts/ge2-20260630093530-398319fe/run-summary.json`

SHA256 reported/computed:

`273a92f7f6a29e15617b39b6bcdb6c22f0b5cfab4b84703dbafb73494ffc92f2`

Hash match: yes

Hard gates:

- fixture entered WebUI adapter/native command path: yes
- matched native `/ge2`: yes
- pluginId `ge2-native`: yes
- `continueAgent:false`: yes
- no model/chat fallthrough: yes
- native GE2 responses: yes
- durable ledger entry: yes
- milestones emitted: yes
- artifact exists: yes
- artifact SHA matches: yes
- status retrieves exact run_id: yes
- artifacts retrieves exact run_id: yes
- bounded/compressed responses: yes

## Cross-surface parity

- both surfaces passed: yes
- distinct run IDs: yes
- distinct artifacts: yes
- both artifact hashes match: yes
- default `commands.list` `/ge2` count: 1
- Telegram text `commands.list` `/ge2` count: 1
- WebUI text `commands.list` `/ge2` count: 1
- fake command absent: yes
- existing commands preserved on default/Telegram/WebUI text surfaces: yes
- Gateway health green: yes

Note: `webchat_both` `commands.list` returned 0 for plugin text commands and is excluded as an invalid P2 visibility blocker. The actual WebUI command-handler path passed.

## Safety

- production touched: no
- GE2 runtime state touched: yes, intentionally by R10 fixture runs
- Gateway restarted: no
- rollback performed: no
- cron closeout apply retried: no
- promoted: no
- external Telegram network used: no
- real inbound Gateway path: no

## Next

`GE2_R11_REAL_INBOUND_GATEWAY_PATH_PENDING`

P3 remains pending and must not be claimed from this R10 result.

## Artifacts

Raw report:

`sharedspace/runtime-kernel-validation/ge2/ge2_r10_adapter_fixture_proof/GE2_R10_ADAPTER_FIXTURE_TELEGRAM_WEBUI_REPORT_20260630.json`

Corrected JSON:

`sharedspace/runtime-kernel-validation/ge2/ge2_r10_adapter_fixture_proof/GE2_R10_ADAPTER_FIXTURE_TELEGRAM_WEBUI_CORRECTED_REPORT_20260630.json`
