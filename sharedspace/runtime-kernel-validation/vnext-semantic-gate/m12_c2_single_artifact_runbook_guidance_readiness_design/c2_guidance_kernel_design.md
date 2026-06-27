# M12-C2 Guidance Kernel Design

C2 should use a deterministic guidance kernel as the authoritative path.

## Kernel stages

1. Validate ArtifactRef allowlist and SHA.
2. Load exactly one approved file.
3. Segment into deterministic sections using headings, anchors, or stable line ranges.
4. Extract candidate guidance units:
   - ordered steps,
   - bullet steps,
   - prerequisites,
   - warnings,
   - explicit next actions,
   - rollback/safety notes.
5. Classify each unit as required, conditional, warning, or informational.
6. Build source refs with quote hashes and section hashes.
7. Produce a draft envelope with status `GUIDANCE` or `HOLD`.
8. Run final deterministic guard:
   - one artifact only,
   - all steps cited,
   - no external action execution,
   - no code/config/routing/safety authority escalation,
   - no forbidden source use,
   - no cache/artifact-memory/runtime mutation.

## Deterministic-first decision

Readiness design recommendation: C2 can use the deterministic kernel alone for authoritative answers. Optional model prose may be added later only as non-authoritative phrasing assistance behind the final guard.

## No-apply state

This design creates no kernel production deployment, no runtime route, no config setting, no model call path, and no C2 production permission.
