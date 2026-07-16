# M9 Context Overflow Compaction Plan

Status: `HOLD_M9_CONTEXT_OVERFLOW_COMPACTION_PLAN_READY`

This is approval-card prep only. It does not compact anything.

Required approval text: `APPROVE_M9_CONTEXT_OVERFLOW_OWNER_SESSION_COMPACTION`

Target session: `agent:main:telegram:direct:8495203551`
Observed messages: `503`

Boundaries: no canary rerun, no live sends/probes, no provider calls, no config/route/memory/Context Bridge mutation, no production authority, no broad enforcement, no M10 enablement.

Recommended next after approval and compaction: rerun a repaired/idle M9 context-overflow recheck before M10 prep.
