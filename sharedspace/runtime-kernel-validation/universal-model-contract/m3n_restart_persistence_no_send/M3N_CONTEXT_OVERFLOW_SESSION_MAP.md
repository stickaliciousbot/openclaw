# M3N Context Overflow Session Map

Status: `PASS_M3N_CONTEXT_OVERFLOW_SESSION_IDENTIFIED`

## Selected overflow source

- Classification: `ACTIVE_TELEGRAM_OWNER_SESSION_OVERFLOW_SOURCE`
- Session key: `agent:main:telegram:direct:8495203551`
- Session id: `412b53c8-9047-4878-aeae-9040aaac5b05`
- Channel: Telegram direct
- Owner/user scope: `8495203551`
- Agent: `main`
- Model/lane: `openai-codex/gpt-5.5`
- Context token cap/estimate: `272000`
- Total tokens reported by session listing: `83149`
- Transcript: `/home/stickai/.openclaw/agents/main/sessions/412b53c8-9047-4878-aeae-9040aaac5b05.jsonl`
- Transcript size observed: `1027727` bytes
- Trajectory: `/home/stickai/.openclaw/agents/main/sessions/412b53c8-9047-4878-aeae-9040aaac5b05.trajectory.jsonl`
- Active Telegram owner session: yes

## Evidence

The post-restart log diagnostic named the same session key and transcript path:

- `sessionKey=agent:main:telegram:direct:8495203551`
- `sessionFile=/home/stickai/.openclaw/agents/main/sessions/412b53c8-9047-4878-aeae-9040aaac5b05.jsonl`
- `provider=openai-codex/gpt-5.5`
- `diagId=ovf-mrls5zsl-U1yPmA`

Targeted transcript checks found:

- `M3N` hits: `135`
- `APPROVE_M3N|M3N_TELEGRAM|context-overflow` hits: `83`

So it contains current M3N evidence/approval content.

## Existing adjacent state

- Runtime-created checkpoint near overflow window: `/home/stickai/.openclaw/agents/main/sessions/412b53c8-9047-4878-aeae-9040aaac5b05.checkpoint.d80d6f4a-4db9-4ec1-83a3-4a6cd7ab5ba8.jsonl`
- Older checkpoint: `/home/stickai/.openclaw/agents/main/sessions/412b53c8-9047-4878-aeae-9040aaac5b05.checkpoint.1d39c519-1bbf-442b-9bb0-b9d844f2eed1.jsonl`
- Live lock file exists.

## Safety classification

- Safe to compact without approval: no
- Safe to compact with exact approval: yes, if using runtime-supported compaction and explicit backup/rollback
- Compaction would affect production response path: yes
- Compaction would mutate durable memory: no
- Compaction would mutate Context Bridge: no

Other recent sessions were classified `UNRELATED_SESSION` because the overflow diagnostic pointed exactly to the Telegram owner direct session.
