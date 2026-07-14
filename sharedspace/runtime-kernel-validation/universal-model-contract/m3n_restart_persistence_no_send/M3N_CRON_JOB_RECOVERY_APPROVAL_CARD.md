# M3N cron job recovery approval card

Status: `HOLD_M3N_CRON_JOB_RECOVERY_AWAITING_OPERATOR_APPROVAL`

Selected job/timer/service: `context-plus-semantic-shadow-pass-watch`

Exact tool call: `{"action": "update", "jobId": "b29e6275-9bad-4622-8a56-041e5a2dc864", "patch": {"enabled": false}}`

Rollback/re-enable: `{"action": "update", "jobId": "b29e6275-9bad-4622-8a56-041e5a2dc864", "patch": {"enabled": true}}`

Expected effect: Stop the every-5-minute shadow watcher from launching isolated agent/model work while M3N Telegram liveness recovery is validated.

Approval text required: `APPROVE_M3N_CRON_JOB_RECOVERY_ACTION: cron.update jobId=b29e6275-9bad-4622-8a56-041e5a2dc864 patch.enabled=false`

No Telegram send/probe is authorized. No Gateway restart is included. No route/fallback/config/memory/Context Bridge mutation is authorized.

Next phase: `APPROVE_M3N_CRON_JOB_RECOVERY_ACTION`
