# M3N cron job recovery decision

Status: `FAIL_M3N_CRON_JOB_RECOVERY_TELEGRAM_LIVENESS_NOT_FULLY_PROVEN`

Selected job `context-plus-semantic-shadow-pass-watch` was disabled by approved `cron.update`. The bounded watch found aggregate counts `{"context_overflow": 0, "event_loop_delay": 0, "gateway_timeout": 0, "getme_timeout": 0, "liveness_warning": 0, "selected_job_active_log_hits": 0, "telegram_send_log_hits_not_probe": 3}`.

N2/N3 retry can be requested: `False` because Telegram readback/account OK was not actively proven under the no-send/no-probe boundary.

Next phase: `RESCOPE_M3N_TELEGRAM_READBACK_NO_SEND_VERIFICATION_OR_RESTART_APPROVAL`.
