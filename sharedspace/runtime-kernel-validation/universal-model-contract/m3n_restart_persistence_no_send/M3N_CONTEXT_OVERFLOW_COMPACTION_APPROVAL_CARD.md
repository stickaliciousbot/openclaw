# M3N Context Overflow Compaction Approval Card

Status: `HOLD_M3N_CONTEXT_OVERFLOW_COMPACTION_AWAITING_OPERATOR_APPROVAL`

Approval phrase: `APPROVE_M3N_CONTEXT_OVERFLOW_COMPACTION`

## Selected session

- Session key: `agent:main:telegram:direct:8495203551`
- Session id: `412b53c8-9047-4878-aeae-9040aaac5b05`
- Session path: `/home/stickai/.openclaw/agents/main/sessions/412b53c8-9047-4878-aeae-9040aaac5b05.jsonl`
- Trajectory: `/home/stickai/.openclaw/agents/main/sessions/412b53c8-9047-4878-aeae-9040aaac5b05.trajectory.jsonl`

## Selected method

Runtime-supported `sessions.compact` with explicit pre-compaction backup/snapshot.

## Exact command/tool call to approve

```sh
bash -lc 'set -euo pipefail; BACKUP=/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/universal-model-contract/m3n_restart_persistence_no_send/backups/m3n-context-overflow-precompact-20260715T083154Z; SESSION=/home/stickai/.openclaw/agents/main/sessions/412b53c8-9047-4878-aeae-9040aaac5b05; mkdir -p "$BACKUP"; cp -a "$SESSION.jsonl" "$BACKUP/"; cp -a "$SESSION.trajectory.jsonl" "$BACKUP/"; cp -a "$SESSION.trajectory-path.json" "$BACKUP/" 2>/dev/null || true; cp -a "$SESSION.jsonl.lock" "$BACKUP/" 2>/dev/null || true; cp -a /home/stickai/.openclaw/agents/main/sessions/412b53c8-9047-4878-aeae-9040aaac5b05.checkpoint.*.jsonl "$BACKUP/" 2>/dev/null || true; sha256sum "$BACKUP"/* > "$BACKUP/SHA256SUMS.txt"; openclaw gateway call sessions.compact --json --timeout 600000 --params '\''{"key":"agent:main:telegram:direct:8495203551"}'\'' | tee "$BACKUP/sessions.compact.result.json"'
```

Compaction tool call only:

```sh
openclaw gateway call sessions.compact --json --timeout 600000 --params '{"key":"agent:main:telegram:direct:8495203551"}'
```

## Backup/snapshot path

`/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/universal-model-contract/m3n_restart_persistence_no_send/backups/m3n-context-overflow-precompact-20260715T083154Z`

## Expected files modified

- The backup/snapshot directory above.
- `/home/stickai/.openclaw/agents/main/sessions/412b53c8-9047-4878-aeae-9040aaac5b05.jsonl`
- `/home/stickai/.openclaw/agents/main/sessions/412b53c8-9047-4878-aeae-9040aaac5b05.trajectory.jsonl`
- `/home/stickai/.openclaw/agents/main/sessions/412b53c8-9047-4878-aeae-9040aaac5b05.trajectory-path.json`
- Runtime checkpoint sidecars for this session, if created/updated by compaction.

## Expected files not modified

- `MEMORY.md`
- `memory/*.md`
- `sharedspace/context-bridge/events.jsonl`
- `sharedspace/context-bridge/actions.json`
- Gateway config / route / fallback / default model settings
- Cron enabled state for `b29e6275-9bad-4622-8a56-041e5a2dc864`
- Production authority controls

## Rollback/restore command

```sh
bash -lc 'set -euo pipefail; BACKUP=/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/universal-model-contract/m3n_restart_persistence_no_send/backups/m3n-context-overflow-precompact-20260715T083154Z; SESSION=/home/stickai/.openclaw/agents/main/sessions/412b53c8-9047-4878-aeae-9040aaac5b05; cp -a "$BACKUP/412b53c8-9047-4878-aeae-9040aaac5b05.jsonl" "$SESSION.jsonl"; cp -a "$BACKUP/412b53c8-9047-4878-aeae-9040aaac5b05.trajectory.jsonl" "$SESSION.trajectory.jsonl"; if [ -f "$BACKUP/412b53c8-9047-4878-aeae-9040aaac5b05.trajectory-path.json" ]; then cp -a "$BACKUP/412b53c8-9047-4878-aeae-9040aaac5b05.trajectory-path.json" "$SESSION.trajectory-path.json"; fi; sha256sum -c "$BACKUP/SHA256SUMS.txt" --ignore-missing'
```

## Post-compaction validation plan

1. Verify backup directory and `SHA256SUMS.txt` exist.
2. Verify Gateway RPC OK with `openclaw gateway status`; do not restart Gateway.
3. Verify Telegram readback only with `channels.status probe=false` if the approval includes Phase E readback.
4. Verify context-overflow/context-overflow-diag count is zero for the active owner session after compaction.
5. Verify cron `b29e6275-9bad-4622-8a56-041e5a2dc864` remains `enabled=false`.
6. Verify safety counters remain zero.
7. Write `M3N_CONTEXT_OVERFLOW_COMPACTION_EXECUTION_RESULT.json` before any stability watch.

## Explicit non-authorizations

- No Telegram send/probe is authorized.
- No Gateway restart is authorized.
- No route/fallback/config mutation is authorized.
- No durable memory mutation is authorized.
- No Context Bridge mutation is authorized.
- No production authority change is authorized.
- No cron re-enable is authorized.
- No N2/N3 retry is authorized.
- No persistence verification is authorized.
- No M3O/M4/enforcement is authorized.

Do not execute this card unless Stick explicitly approves it.
