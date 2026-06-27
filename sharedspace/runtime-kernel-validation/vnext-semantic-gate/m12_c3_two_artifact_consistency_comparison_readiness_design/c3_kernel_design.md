# C3K Deterministic Comparison Kernel Design

A C3K deterministic comparison kernel is required before any C3 readiness exercise or C3 production canary.

C3K responsibilities:

1. Accept exactly two `ArtifactRef` inputs.
2. Verify approval status, immutable hashes, and source allowlists.
3. Reject/HOLD more-than-two, missing, stale, ambiguous, or unapproved artifacts.
4. Compile bounded fields/sections into canonical comparison rows.
5. Apply deterministic normalization only for approved field types.
6. Emit the C3 comparison envelope with `CONSISTENT`, `CONFLICT`, `HOLD`, or guard `REJECT`.
7. Emit explicit source refs from both artifacts.
8. Enforce no C4 proposal drafting and no reconciliation except direct source-row-supported equivalence.
9. Count provider/model calls and direct bypass; both must remain zero for authoritative comparison.
10. Emit mutation/cache/artifact-memory/runtime-authority sentinels.

C3K is not implemented by this readiness design packet. This packet authorizes design only and recommends a separate owner-approved C3K implementation packet as the next step.
