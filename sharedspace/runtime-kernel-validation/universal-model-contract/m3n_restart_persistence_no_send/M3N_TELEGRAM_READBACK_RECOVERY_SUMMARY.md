# M3N Telegram Readback Recovery Restart Summary

Final status: `FAIL_M3N_TELEGRAM_READBACK_RECOVERY_STABILITY`

## Results

- Preflight: `PASS_M3N_TELEGRAM_READBACK_RECOVERY_RESTART_PREFLIGHT`
- Restart: `PASS_M3N_TELEGRAM_READBACK_RECOVERY_RESTART_COMPLETED`
- Restart reason: `M3N Telegram readback recovery after cron liveness stabilization no-send`
- Pre-restart Gateway PID: `122580`
- Post-restart Gateway PID: `122580`
- Post-restart health: `PASS_M3N_TELEGRAM_READBACK_RECOVERY_POST_RESTART_HEALTH`
- Readback no-send verification: `PASS_M3N_TELEGRAM_READBACK_RECOVERY_NO_SEND_VERIFIED`
- Stability watch: `FAIL_M3N_TELEGRAM_READBACK_RECOVERY_STABILITY`
- Disabled cron: `b29e6275-9bad-4622-8a56-041e5a2dc864` enabled=`False`

## Failure reason

The restart completed and Telegram readback recovered using `channels.status probe=false`, but the bounded stability phase failed fast because post-restart logs contained context-overflow diagnostics for the active Telegram owner session. Phase E requires `context overflow 0`.

## Safety counters

- Telegram tool send/probe count: 0
- External send count: 0
- Provider/model shadow call count: 0
- Route/config mutation count: 0
- Memory mutation count: 0
- Context Bridge mutation count: 0
- Production authority change count: 0
- Cron re-enable count: 0
- N2/N3 retry run: false
- Persistence verification started: false
- M3O/M4/enforcement started: false

## Recommendation

`REPAIR_CONTEXT_OVERFLOW_BEFORE_APPROVE_M3N_N2_N3_RETRY_AFTER_TELEGRAM_READBACK_RECOVERY`

Do not approve or run N2/N3 until the active Telegram owner session context-overflow condition is repaired/compacted and readback stability can be re-run cleanly.
