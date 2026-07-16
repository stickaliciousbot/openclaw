# M10A Explicit Abort Thresholds

Status: `PASS_M10A_EXPLICIT_ABORT_THRESHOLDS_DEFINED`

Abort thresholds are defined for Gateway/Telegram health, queue backlog, context overflow and diagnostics, event-loop/health correlation, missing M10A readback, scope expansion, Web UI/LAN/browser inclusion, unexpected Telegram/external/provider/write/memory/Context Bridge/config mutations, production authority drift, broad enforcement, fallback contract drops, missing receipt acceptance, raw provider/model bypass, and operator stop.

Default action: disable M10A via exact off-switch; if disable/readback fails, execute rollback and hold. The exact registered disable/rollback commands are not yet proven, so production approval remains blocked until command-surface repair.
