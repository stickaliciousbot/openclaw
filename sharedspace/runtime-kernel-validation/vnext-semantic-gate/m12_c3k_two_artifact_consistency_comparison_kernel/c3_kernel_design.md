# M12-C3K Kernel Design

C3K implements deterministic two-artifact consistency comparison for exactly two approved artifacts. It compiles approved SourceRows for Artifact A and Artifact B, validates immutable approval handles, compares only bounded fields/sections, and emits `CONSISTENT`, `CONFLICT`, `HOLD`, or guard `REJECT` envelopes.

No C3 production route is activated by this packet. C4 remains blocked until separate owner approval.
