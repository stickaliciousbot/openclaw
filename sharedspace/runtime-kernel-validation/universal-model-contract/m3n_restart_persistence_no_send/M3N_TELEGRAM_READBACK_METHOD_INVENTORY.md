# M3N Telegram readback method inventory

Status: `PASS_M3N_TELEGRAM_READBACK_SAFE_METHOD_IDENTIFIED`

Selected safe method: `Gateway channels.status probe=false + current Telegram direct inbound/activity readback`.

Rejected: probe=true/getMe/getWebhookInfo as active provider probes; sendMessage/sendTyping as unsafe send/probe; sessions rows as not a channel health signal.
