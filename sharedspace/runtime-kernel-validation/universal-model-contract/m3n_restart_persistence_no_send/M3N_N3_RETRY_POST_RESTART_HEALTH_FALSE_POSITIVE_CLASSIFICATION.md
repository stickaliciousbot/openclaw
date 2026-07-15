# M3N N3 Post-Restart Health — Context Overflow False Positive Classification

Status: `PASS_M3N_N3_RETRY_HEALTH_CONTEXT_OVERFLOW_CLASSIFIED_FALSE_POSITIVE`

The 1 `context_overflow` hit in the N3 post-restart health scan is classified as `LOG_SCANNER_REGEX_FALSE_POSITIVE_SESSION_TRANSCRIPT_TEXT`.

## Evidence

- Context-overflow-diag count: `0`
- The over-broad regex matches the literal word "context_overflow" in session transcript summary text loaded during the pre-restart window.
- No context-overflow-diag entries exist in the post-restart log window.
- The restart completed successfully: full process restart, gateway ready at 21:12:04 AEST, Telegram started at 21:12:07 AEST.
- This is the same false-positive class as the ambient Telegram send hits classified earlier.

## Restart mode note

The `gateway.restart` tool reported SIGUSR1, but the log shows "restart mode: full process restart (supervisor restart)" with clean shutdown and reload. PID changed from 716259.
