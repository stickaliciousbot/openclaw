# M3N post-restart liveness repair policy

Status: `PASS_M3N_POST_RESTART_LIVENESS_REPAIR_READY`

The health gate remains fail-closed. A bounded post-restart stabilization window may distinguish transient reconnect delay from persistent Telegram plugin instability, but `Telegram readback OK` is not sufficient if fresh liveness warnings persist. No Telegram probes, config mutation, repeated restarts, or health-gate weakening are allowed.
