# M3N N3 failure rehydration

Status: `PASS_M3N_N3_FAILURE_REHYDRATED`

- N0 preflight: `PASS_M3N_RESTART_PERSISTENCE_PREFLIGHT`
- N1 baseline: `PASS_M3N_PRE_RESTART_BASELINE_CAPTURED`
- N2 Gateway restart: `PASS_M3N_GATEWAY_RESTART_COMPLETED`
- N3 post-restart health: `FAIL_M3N_POST_RESTART_HEALTH`
- Gateway current readback: up / RPC OK / PID 122580
- Queue depth: 0
- Safety counters: zero
- Locked: M3N persistence verification, M3O, M4, enforcement.
