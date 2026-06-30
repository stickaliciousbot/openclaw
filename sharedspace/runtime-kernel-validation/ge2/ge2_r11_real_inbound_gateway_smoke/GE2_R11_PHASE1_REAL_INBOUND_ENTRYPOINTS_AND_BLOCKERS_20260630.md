# GE2 R11 Phase 1 / safe live-probe report

Final classification: `GE2_R11_REAL_INBOUND_BLOCKED_P2_PASS_ONLY`

Proof level: P3 attempted for safe WebUI/Gateway live RPC only; P3 **not passed**. P2 remains valid.

## Routes identified

### Telegram real inbound
- Ingress: Telegram Bot API update -> createTelegramBot/registerTelegramNativeCommands -> bot.handleUpdate in running Gateway
- Recognizer: matchPluginCommand(commandBody)
- Executor: executePluginCommand(...)
- Response delivery: Telegram reply/send path via deliverReplies/recordSentMessage
- Direct session key: `agent:main:telegram:direct:8495203551`
- Sent ledger: `/home/stickai/.openclaw/agents/main/sessions/sessions.json.telegram-sent-messages.json`
- P3 blocker: requires real operator-sent Telegram inbound /ge2 message; assistant must not spoof inbound or send outbound bot command as substitute

### WebUI/Gateway live inbound
- Ingress: Gateway RPC chat.send -> dispatchInboundMessage/get-reply command routing in running Gateway
- Required chat.send params: `sessionKey`, `message`, `idempotencyKey`
- Recognizer: commands-handlers.runtime handlePluginCommand / matchPluginCommand(commandBodyNormalized)
- Executor: executePluginCommand(...)
- Response delivery: chat transcript + nodeSendToSession live chat event
- P3 blocker: rendered browser WebUI unavailable on host; raw chat.send live RPC was accepted but /ge2 help returned authorization gate, not GE2 help

## Command visibility

- Telegram /ge2 count: 1
- Webchat /ge2 count: 1
- Telegram fake count: 0
- Webchat fake count: 0
- Existing command preservation (telegram): pair=present, dreaming=present, phone=present, voice=present
- Existing command preservation (webchat): pair=present, dreaming=present, phone=present, voice=present

## Safe live probes

- Browser WebUI: failed: No supported browser found (Chrome/Brave/Edge/Chromium)
- chat.send /ge2 help: accepted by chat.send, transcript response was authorization gate: ⚠️ This command requires authorization.
- Model/chat fallthrough: not observed; response provider/model gateway-injected with zero token usage
- Native GE2 execution: not proven because auth gate blocked before GE2 help response

## Boundary

- Production patch: no
- Gateway restart: no
- Rollback: no
- Cron apply: no
- Promotion: no

## SHA

JSON report SHA256: `ac21ae5f87d21741c8fd79acde914704c0ba48fa95d088a8479fe5427d8322d9`
