# C3 Abort Gates

Abort or mark BLOCKED if any gate trips:

1. C3 cannot be separated from C4 proposal drafting.
2. Comparison requires more than two artifacts.
3. Artifact precedence/staleness cannot be made deterministic.
4. Conflict handling cannot be made deterministic.
5. Production expansion would be required.
6. Mutation sentinels trip.
7. Rollback readiness cannot be verified.
8. C1 frozen production boundary is not preserved.
9. C2 frozen production boundary is not preserved.
10. Cache, semantic cache, artifact-memory, or global Semantic Gate promotion is required or observed.
11. Runtime/Gateway/config/live-route/fallback/memory-route authority mutation is required or observed.
12. Direct provider bypass or model-owned authoritative comparison is required or observed.
13. Arbitrary paths, memory/context-bridge/daily-memory, external actions, or unapproved artifacts are accepted as authority.
14. C3 production route activation occurs.
15. C4 starts without separate owner approval.
