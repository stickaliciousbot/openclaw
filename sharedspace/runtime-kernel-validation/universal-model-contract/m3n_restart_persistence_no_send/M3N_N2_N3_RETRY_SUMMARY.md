# M3N N2/N3 Retry After Context-Overflow Repair

Final status: `PASS_M3N_N2_N3_RETRY_AFTER_CONTEXT_OVERFLOW_REPAIRED`

- Preflight: `PASS_M3N_N2_N3_RETRY_PREFLIGHT_AFTER_CONTEXT_REPAIR`
- Gateway restart: `PASS_M3N_N2_RETRY_GATEWAY_RESTART_COMPLETED`
- Restart reason: `M3N N2/N3 retry after context-overflow repair no-send`
- Pre-restart PID: `716259`
- Post-restart PID: `795787`
- Restart mode: `full process restart (supervisor restart)` (tool reported `SIGUSR1`)
- N3 health (raw): `FAIL_M3N_N3_RETRY_POST_RESTART_HEALTH`
- N3 health (classified): `PASS_M3N_N3_RETRY_POST_RESTART_HEALTH_CLASSIFIED`
- Health false-positive classification: `PASS_M3N_N3_RETRY_HEALTH_CONTEXT_OVERFLOW_CLASSIFIED_FALSE_POSITIVE`
- Stability: `PASS_M3N_N3_RETRY_STABILITY_CONFIRMED`
- Disabled cron: `context-plus-semantic-shadow-pass-watch` / `b29e6275-9bad-4622-8a56-041e5a2dc864` enabled=`False`
- Telegram readback: `channels.status probe=false`, account_ok=`True`, account_count=`1`
- Context overflow: `0` (1 raw hit classified as false positive)
- Context-overflow-diag: `0`
- Telegram repair-lane send/probe count: `0`
- Ambient global Telegram delivery count: `0`
- External send count: `0`
- Provider/model shadow call count: `0`
- Route/config mutation count: `0`
- Durable memory mutation count: `0`
- Context Bridge mutation count: `0`
- Production authority change count: `0`
- Persistence verification started: `false`
- M3O/M4/enforcement started: `false`

Exact next phase: `M3N_POST_RESTART_PERSISTENCE_VERIFICATION`
