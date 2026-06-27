# C3 Conflict Policy

C3 conflict handling is deterministic and non-reconciliatory.

Rules:

1. Normalize only approved primitive comparison forms: exact strings, booleans, numbers with declared units, enums, timestamp fields, and explicit source-ref lists.
2. Compare each canonical field id independently.
3. If values match after approved normalization, add an agreement point.
4. If values differ, are missing on one side, or require interpretation beyond approved rules, add a conflict point.
5. If any conflict point exists, status is `CONFLICT` unless a fail-closed guard requires `HOLD` or `REJECT`.
6. No artifact wins by default. C3 does not choose an authoritative winner.
7. No remediation, next-step proposal, merge plan, or operational recommendation may be drafted; that is C4-or-later scope.

Allowed disposition language is limited to explaining the bounded consistency/conflict result and citing source refs.
