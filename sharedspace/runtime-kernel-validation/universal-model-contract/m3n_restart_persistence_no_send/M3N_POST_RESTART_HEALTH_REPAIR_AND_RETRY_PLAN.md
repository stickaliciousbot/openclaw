# M3N post-restart health repair and retry plan

Status: `PASS_M3N_POST_RESTART_HEALTH_REPAIR_AND_RETRY_PLAN_READY`

Do not weaken M3N gates. Repair scanner/log-window parity and add only justified bounded Telegram/liveness stabilization checks. Real Telegram/liveness instability must still fail closed. A fresh N2/N3 retry is required after repair; resume from N2/N3 only if N0/N1 stability is revalidated, otherwise restart from N0/N1. Any future Gateway restart requires explicit approval.

Suggested next milestone: `M3N_POST_RESTART_HEALTH_SCANNER_AND_LIVENESS_REPAIR_THEN_N2_N3_RETRY`.
