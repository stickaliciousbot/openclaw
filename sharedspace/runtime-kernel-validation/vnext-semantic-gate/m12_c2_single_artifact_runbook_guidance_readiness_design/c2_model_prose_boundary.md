# M12-C2 Model Prose Boundary

C2 may support either deterministic guidance only or deterministic guidance plus optional model prose. This packet recommends deterministic guidance as the authoritative path and treats model prose as optional, non-authoritative, and disabled by default for readiness.

If optional model prose is later tested:

- The model receives only deterministic extracted snippets from the single approved artifact, not arbitrary files or memory.
- The model may rephrase but not add steps, prerequisites, warnings, citations, or applicability labels.
- The model may not select sources.
- The model may not resolve ambiguity.
- The model may not perform external actions.
- The final deterministic guard must compare prose against the deterministic envelope and reject additions or contradictions.
- Provider/model calls must be counted and reported separately; no direct provider bypass is allowed.

Authoritative source selection and citations remain deterministic. Final guard remains authoritative.
