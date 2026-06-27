# C4 Deterministic Kernel Design

A deterministic C4 proposal skeleton/kernel is required before any C4 exercise, canary, or production use.

Kernel responsibilities:

1. Validate the case manifest and source allowlist.
2. Compile approved C1/C2/C3/artifact SourceRows.
3. Classify request as PROPOSAL, HOLD, or REJECT.
4. Generate deterministic proposal skeleton fields.
5. Enforce source citations and source-count limits.
6. Preserve assumptions, uncertainty, conflicts, and prerequisites.
7. Enforce non-execution policy.
8. Reject/HOLD execution, mutation, external action, arbitrary path, unapproved memory/context/daily-memory, provider-authority, and prompt-injection control attempts.
9. Permit optional model prose only after deterministic contract validation, and only as non-authoritative rendering.
10. Emit audit counters, source authority report, fail-closed report, model prose boundary report, mutation sentinel report, and rollback readback.

C4K must be implemented and tested before readiness exercise/canary/production.
