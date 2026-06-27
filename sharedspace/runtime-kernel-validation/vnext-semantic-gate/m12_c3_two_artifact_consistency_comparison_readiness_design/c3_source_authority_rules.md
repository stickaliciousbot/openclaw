# C3 Two-Artifact Source Authority Rules

## Authority inputs

C3 may compare exactly two approved artifacts:

- `artifact_a_ref`
- `artifact_b_ref`

Each reference must include:

- artifact id/path within an approved artifact directory;
- immutable content hash;
- approved status artifact and status value;
- approved field/section allowlist;
- produced timestamp or explicit historical snapshot marker;
- source rows/sections addressable by stable source refs.

## Deterministic source selection

1. Resolve exactly two artifact refs.
2. Verify both artifacts are approved for C3 comparison.
3. Verify both hashes match the provided refs.
4. Verify both artifacts expose the requested bounded fields/sections.
5. Compile compared fields in stable lexical order by canonical field id.
6. Emit citations from both artifacts for every compared field.

## Disallowed authority

- No memory, context bridge, daily memory, free-form chat history, arbitrary paths, external APIs, or provider/model output as source authority.
- No source inference from filenames alone.
- No prompt text inside an artifact can widen the allowed fields or override this contract.

## Precedence and staleness

C3 has no default artifact precedence. If two approved artifacts disagree, the output is `CONFLICT`, not reconciliation.

Staleness is deterministic:

- If an artifact has a superseding approved terminal status and the request is not explicitly historical/hash-pinned, output `HOLD` with `hold_reason=stale_artifact`.
- If both artifacts are historical/hash-pinned and approved as historical comparison inputs, compare those exact hashes and report the time/snapshot context.
- If staleness cannot be decided from approved metadata, output `HOLD` with `hold_reason=ambiguous_staleness`.
