# M12-C2 Scope Definition — Single-Artifact Runbook Guidance

Status: `M12_C2_READINESS_DESIGN_PASS_NO_APPLY`

M12-C2 is a readiness-design candidate only. It is **not** C2 production and does not authorize any production expansion.

## Candidate scope

M12-C2 may answer guidance questions over exactly one approved artifact, where the question asks what the selected artifact says the operator should do next.

Allowed question classes:

- “What does this runbook/artifact say I should do next?”
- “What are the steps in this approved artifact?”
- “What prerequisites or warnings does this single artifact list?”
- “What section of this artifact supports the guidance?”

## Hard boundary

C2 must not:

- Compare two artifacts.
- Synthesize cross-artifact consistency.
- Draft multi-source next-step proposals.
- Perform external actions.
- Mutate runtime/config/route/fallback/memory/Gateway state.
- Use arbitrary paths.
- Use memory/context-bridge/daily-memory as production authority.
- Use C1K as mutable evidence.
- Enable cache or artifact-memory promotion.

## Single approved artifact definition

A single approved artifact is one immutable, hash-pinned file selected from an approved artifact packet or manifest. A directory, package, repo, memory file, live runtime state, session transcript, context bridge entry, or arbitrary filesystem path is not a single approved artifact for C2.

A valid C2 ArtifactRef must include:

- `artifact_id`
- `path` from a predefined allowlist or owner-approved artifact manifest
- `sha256`
- `approval_record` or source packet hash
- `artifact_class` such as `runbook`, `operator_review`, `status_review`, or `guidance_record`
- `max_section_scope` limiting extraction to sections inside that one file

Multiple files from one artifact packet are still multiple artifacts and must HOLD unless a separate owner-approved C2 packet explicitly expands the scope.
