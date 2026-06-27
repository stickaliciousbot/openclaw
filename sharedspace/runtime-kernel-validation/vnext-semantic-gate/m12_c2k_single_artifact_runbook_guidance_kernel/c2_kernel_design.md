# C2K Kernel Design

Status: `M12_C2K_SINGLE_ARTIFACT_RUNBOOK_GUIDANCE_KERNEL_PASS`

The C2K kernel is deterministic and fixture-scoped. It accepts exactly one approved, hash-pinned artifact handle plus one C2 case, compiles deterministic runbook sections/source rows, emits `GUIDANCE` or `HOLD`, and then runs a final source-authority guard.

Non-goals and hard boundaries:

- No C2 production route activation.
- No C3/C4 start.
- No production expansion.
- No cache enablement.
- No artifact-memory/global promotion.
- No Gateway/config/live-route/fallback/memory-route/runtime-authority mutation.
- No direct provider bypass.
- No provider/model calls for authoritative guidance.
