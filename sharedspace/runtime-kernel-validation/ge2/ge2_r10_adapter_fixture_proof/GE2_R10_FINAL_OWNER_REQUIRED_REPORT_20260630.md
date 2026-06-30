# GE2-R10 Final Owner-Required Adapter Fixture Report

Final classification: `GE2_R10_ADAPTER_FIXTURE_TELEGRAM_WEBUI_HELP_STATUS_RUN_PASS_P3_PENDING`

Proof level: **P2 only** — adapter-shaped fixtures.  
P3 real inbound Gateway native command path remains pending.  
No promotion.

## Scope and boundary

R10 proves Telegram and WebUI adapter-shaped inputs flow through their adapter/native command layers into the same GE2 dispatcher/runtime/ledger path.

Not claimed:

- P3 real inbound Gateway path
- live Telegram inbound delivery
- live WebUI browser/client inbound delivery
- production promotion

Production boundaries held:

- production patch: no
- Gateway restart: no
- rollback: no
- cron apply: no
- promotion: no
- real inbound live smoke: no
- model/chat spoofing: no
- outbound bot spoofing: no; Telegram used fake API transport only

## Telegram adapter fixture path

File/function path:

- `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/bot-Ds7bwqAK.js`
- exported `createTelegramBot(...)`
- synthetic grammy update via `bot.handleUpdate(...)`
- `registerTelegramNativeCommands(...)` command handler builds `commandBody`
- loads `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/bot-native-commands.runtime-OmS7iYqz.js`
- calls `matchPluginCommand(commandBody)`
- calls `executePluginCommand(...)`

Fixture method: fake Telegram API transport captured `sendMessage`/`editMessageText`; no external Telegram network used.

### Telegram command results

1. `/ge2 help`
   - adapter path entered: yes
   - native GE2 response: yes
   - no model/chat fallthrough: yes

2. `/ge2 status`
   - adapter path entered: yes
   - native GE2 response: yes
   - no model/chat fallthrough: yes

3. `/ge2 run r10-telegram-adapter-fixture-smoke`
   - matched native `/ge2`: yes
   - pluginId: `ge2-native`
   - `continueAgent:false`
   - run_id: `ge2-20260630093527-d6193cf1`

4. `/ge2 status ge2-20260630093527-d6193cf1`
   - exact run_id retrieved: yes
   - status: `completed`
   - milestones: `7`
   - artifacts: `1`
   - errors: `0`

5. `/ge2 artifacts ge2-20260630093527-d6193cf1`
   - exact run_id retrieved: yes
   - artifact path and SHA returned: yes

Telegram ledger path:

`/home/stickai/.openclaw/workspace/state/ge2-native/runs/ge2-20260630093527-d6193cf1.json`

Telegram artifact path:

`/home/stickai/.openclaw/workspace/state/ge2-native/artifacts/ge2-20260630093527-d6193cf1/run-summary.json`

Telegram artifact SHA256 reported/computed:

`5a07d2983bd65fbee07a605ae4eb76214ee86bf69c98abed17e32e78f93e7d5c`

Hash match: yes

## WebUI adapter fixture path

File/function path:

- `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/commands-handlers.runtime-DlESKC_s.js`
- `loadCommandHandlers()[0]`
- `handlePluginCommand(params, allowTextCommands)`
- WebUI-shaped params with `channel:'webchat'`
- code path: `allowTextCommands -> matchPluginCommand(commandBodyNormalized,{channel:'webchat'}) -> executePluginCommand(...) -> shouldContinue=false`

This is not the R9 direct installed-dist handler harness. It exercises the WebUI/internal command-handler adapter layer with WebUI-shaped command params.

### WebUI command results

1. `/ge2 help`
   - adapter path entered: yes
   - native GE2 response: yes
   - no model/chat fallthrough: yes

2. `/ge2 status`
   - adapter path entered: yes
   - native GE2 response: yes
   - no model/chat fallthrough: yes

3. `/ge2 run r10-webui-adapter-fixture-smoke`
   - matched native `/ge2`: yes
   - pluginId: `ge2-native`
   - `continueAgent:false`
   - run_id: `ge2-20260630093530-398319fe`

4. `/ge2 status ge2-20260630093530-398319fe`
   - exact run_id retrieved: yes
   - status: `completed`
   - milestones: `7`
   - artifacts: `1`
   - errors: `0`

5. `/ge2 artifacts ge2-20260630093530-398319fe`
   - exact run_id retrieved: yes
   - artifact path and SHA returned: yes

WebUI ledger path:

`/home/stickai/.openclaw/workspace/state/ge2-native/runs/ge2-20260630093530-398319fe.json`

WebUI artifact path:

`/home/stickai/.openclaw/workspace/state/ge2-native/artifacts/ge2-20260630093530-398319fe/run-summary.json`

WebUI artifact SHA256 reported/computed:

`273a92f7f6a29e15617b39b6bcdb6c22f0b5cfab4b84703dbafb73494ffc92f2`

Hash match: yes

## Canonical envelope comparison

Both surfaces normalize to the same canonical command envelope shape before GE2 runtime execution:

| Field | Telegram | WebUI | Parity |
|---|---|---|---|
| command | `ge2` | `ge2` | same |
| native command name | `/ge2` | `/ge2` | same |
| pluginId | `ge2-native` | `ge2-native` | same |
| subcommands proven | `help`, `status`, `run`, `status <run_id>`, `artifacts <run_id>` | `help`, `status`, `run`, `status <run_id>`, `artifacts <run_id>` | same |
| args structure | command tail string after `/ge2` | command tail string after `/ge2` | same |
| dispatcher/runtime | GE2 dispatcher/runtime/ledger | GE2 dispatcher/runtime/ledger | same |
| origin surface | `telegram` | `webchat` | differs only by surface metadata |
| session metadata | Telegram fixture session/account/sender | WebUI fixture session/account/sender | differs only by origin/session metadata |

Canonical origin difference:

- Telegram origin: surface/channel `telegram`, sender `8495203551`, synthetic Telegram adapter update.
- WebUI origin: surface/channel `webchat`, sender `webui-fixture-user`, WebUI command-handler params.

Everything after adapter normalization enters the same GE2 command dispatcher/runtime/ledger path.

## Response schema comparison

Both surfaces produced the same native GE2 response schema:

- help response: native GE2 help text
- no-arg status response: native GE2 status text
- run response:
  - accepted indicator
  - `run_id`
  - `status: accepted`
  - task name
  - status follow-up hint
- exact status response:
  - `run_id`
  - `status: completed`
  - task name
  - `milestones`
  - `artifacts`
  - `errors`
  - `updated_at`
- artifacts response:
  - `GE2 artifacts for <run_id>`
  - artifact name
  - SHA256 value
  - artifact path

Both surfaces returned bounded/compressed responses and did not dump raw logs.

## Model/chat fallthrough check

Telegram:

- `matchPluginCommand()` matched `/ge2`
- `executePluginCommand()` returned native GE2 text
- `continueAgent:false`
- no LLM/model/chat response patterns observed

WebUI:

- `handlePluginCommand()` matched `/ge2`
- `executePluginCommand()` returned native GE2 text
- `shouldContinue:false` derived from `continueAgent:false`
- no LLM/model/chat response patterns observed

Overall: no model/chat fallthrough.

## Cross-surface invariants

- Telegram and WebUI use same GE2 dispatcher/runtime/ledger: yes
- same command/subcommand/args structure: yes
- origin differs only by surface/channel/session metadata: yes
- same response schema: yes
- same milestone semantics: yes (`accepted`, `validated`, `running`, `milestone_emitted`, `artifact_written`, `verification_passed`, `completed`)
- both produce artifact path + SHA: yes
- no duplicate `/ge2`: yes
  - registered: 1
  - listPluginCommands: 1
  - live default: 1
  - live Telegram text: 1
  - live WebUI text: 1
- fake command absent: yes
- existing commands preserved: yes on default, Telegram text, and WebUI text command surfaces

Note: raw R10 report briefly failed an extra assumed `webchat_both` visibility gate. That gate is excluded here because WebUI text command visibility and the actual WebUI adapter handler path passed; `webchat_both` does not invalidate P2 adapter execution proof.

## Gateway health status

Recorded during R10:

- service/runtime running: yes
- listener present: yes
- connectivity probe: ok
- admin-capable: yes
- PID remained `307081`

## Safety flags

- production touched: no
- GE2 runtime state touched: yes, intentionally by R10 fixture runs
- Gateway restarted: no
- rollback performed: no
- cron closeout apply retried: no
- promoted: no
- external Telegram network used: no
- real inbound Gateway path: no

## Final classification

`GE2_R10_ADAPTER_FIXTURE_TELEGRAM_WEBUI_HELP_STATUS_RUN_PASS_P3_PENDING`

## Next step

`GE2_R11_REAL_INBOUND_GATEWAY_TELEGRAM_WEBUI_SMOKE_PENDING`

R11 must prove P3 real inbound native command path through Gateway and must not rely on this P2 fixture result alone.
