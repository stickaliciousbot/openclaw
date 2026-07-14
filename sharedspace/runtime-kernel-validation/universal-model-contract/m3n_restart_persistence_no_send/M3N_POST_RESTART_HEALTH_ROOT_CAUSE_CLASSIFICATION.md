# M3N post-restart health root-cause classification

Status: `PASS_M3N_POST_RESTART_HEALTH_ROOT_CAUSE_CLASSIFIED`

Primary classification: `POST_RESTART_TELEGRAM_PLUGIN_INSTABILITY`. Secondary: transient liveness/reconnect delay, too-short health window, and scanner false-positive scope. The failure was real plus scanner noise, not scanner-only. Gateway recovered without intervention; Telegram readback recovered enough to report OK, but fresh liveness instability remained. Gates must remain unchanged; repair scanner/log-window parity and add bounded stabilization checks only. Retry is not safe until that repair is preserved and any future restart is explicitly approved.
