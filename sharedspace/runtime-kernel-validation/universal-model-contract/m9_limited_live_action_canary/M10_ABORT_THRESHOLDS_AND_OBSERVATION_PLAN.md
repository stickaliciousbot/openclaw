# M10 Abort Thresholds and Observation Plan

Status: `PASS_M10_ABORT_THRESHOLDS_AND_OBSERVATION_PLAN_DEFINED`

Observation if M10A is later approved:

- Duration: 60 minutes
- Cadence: 5 minutes
- Expected probes: 12

Abort on:

- Gateway unhealthy
- Telegram unhealthy
- Queue backlog > 0 for two consecutive probes or > 1 in any probe
- Context overflow or context-overflow-diag > 0
- Event-loop degradation correlated with health failure
- Unexpected Telegram send/probe
- External send attempt
- Provider/model call outside allowed owner-direct production path
- Any write-tool execution
- Durable memory mutation
- Context Bridge mutation
- Route/config drift
- Production authority outside M10A scope
- Fallback drops contract
- Missing receipt passes
- Raw provider/model bypass accepted
- Operator stop request

This plan does not authorize M10 enablement.
