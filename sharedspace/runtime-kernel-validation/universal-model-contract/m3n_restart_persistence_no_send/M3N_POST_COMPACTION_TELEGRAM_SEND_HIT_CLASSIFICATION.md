# M3N Post-Compaction Telegram Send Hit Classification

Status: `PASS_M3N_POST_COMPACTION_SEND_HITS_CLASSIFIED_AMBIENT_FALSE_POSITIVE`

The two send hits are formally classified as `AMBIENT_OWNER_CHAT_DELIVERY_GLOBAL_LOG_FALSE_POSITIVE`.

| Timestamp | Chat | Message | Classification | Counts as repair lane send/probe? | Counts as message-tool send? | Counts as UMC shadow send? |
|---|---:|---:|---|---|---|---|
| 2026-07-15T10:26:21.396Z | 8495203551 | 38510 | AMBIENT_OWNER_CHAT_DELIVERY_GLOBAL_LOG_FALSE_POSITIVE | no | no | no |
| 2026-07-15T10:26:22.366Z | 8495203551 | 38511 | AMBIENT_OWNER_CHAT_DELIVERY_GLOBAL_LOG_FALSE_POSITIVE | no | no | no |

Basis: the entries came from the global `channels/telegram` sendMessage log while the repair lane was isolated. They match normal owner-chat replies and no `probe=true`, message-tool send, UMC shadow-caused send, external send, route/config mutation, memory mutation, Context Bridge mutation, or production authority mutation was present.
