# M12-C2 Abort Gates

Abort any future C2 readiness/canary run if any of these occur:

- C2 production starts without explicit separate owner approval.
- C3 or C4 starts.
- Production expansion is applied.
- Cache or semantic cache is enabled.
- Artifact-memory or memory promotion occurs.
- Gateway/config/live-route/fallback/memory-route/runtime-authority mutates.
- Direct provider bypass is observed.
- Arbitrary path read is accepted as authority.
- Memory/context-bridge/daily-memory is used as production authority.
- More than one artifact is accepted for a C2 question.
- Cross-artifact synthesis or consistency checking occurs.
- External action is performed or recommended as an executed action.
- Code/config/routing/safety authority is asserted from a runbook guidance output.
- C1K frozen evidence changes or is regenerated.
- C1K `--write-artifacts` is invoked.
- M11 frozen baseline is not preserved.
- M12-C1 frozen accepted boundary is violated.
- Rollback readiness fails.
- Owner approval boundary is violated.
