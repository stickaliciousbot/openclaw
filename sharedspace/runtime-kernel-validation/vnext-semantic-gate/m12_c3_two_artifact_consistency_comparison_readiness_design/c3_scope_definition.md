# M12-C3 Scope Definition — Two-Artifact Consistency Comparison

M12-C3 is a **no-apply readiness design** for deterministic two-artifact consistency comparison.

Allowed candidate scope:

- M12-C3 only.
- Exactly two approved artifacts: `artifact_a` and `artifact_b`.
- Each artifact must be identified by immutable artifact reference, approved status reference, and hash.
- Deterministic comparison of bounded fields/sections only.
- Outputs are limited to `CONSISTENT`, `CONFLICT`, `HOLD`, or guard `REJECT`.
- Source refs from both artifacts must be explicit in every non-HOLD comparison result.
- Reconciliation is forbidden unless the approved source rows themselves directly support the reconciliation.
- Model prose, if ever added in a later design, is non-authoritative and cannot select sources, resolve conflicts, or alter disposition.

C3 readiness design does not activate production routing and does not mutate runtime authority.
