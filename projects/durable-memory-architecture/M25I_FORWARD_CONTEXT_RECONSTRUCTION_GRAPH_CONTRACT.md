# M25I Forward Context Reconstruction Graph Contract

The graph is always rebuildable and never canonical authority.

## Identity model

- `entity_guid`, `source_guid`, `source_version_id`, `span_id`, `claim_guid`, `relation_guid`, `contradiction_guid`, `supersession_guid`, `packet_id`, `receipt_id`.
- GUID identity proves only identity. Authority, freshness, privacy and access are separate receipt gates.

## Node classes

Entity, Alias, Source, SourceVersion, Span, Claim, Relation, Contradiction, Supersession, Event, Omission, PolicyEpoch, ReconstructionPacket.

## Edge classes

mentions, aliases, supports, contradicts, supersedes, derived_from, scoped_to, redacts, omitted_because, stale_against, verified_by, requested_by.

## Required behavior

- Inputs: source registry, Ledger source refs/claims, sanitized claim cards, approved source readback.
- Projection receipt: records source manifests, build hash, graph watermark, index watermark, discarded/private counts.
- Deterministic replay: sorted canonical inputs and deterministic IDs; replay hash must match or graph is YELLOW/RED.
- Query frame: request GUID, allowed source domains, required slots, budgets, privacy class, consequence class, policy epoch.
- Coverage: every required slot is filled, contradicted, omitted, or unavailable with reason.
- Traversal budgets: hop/time/token/node caps; exhausted budget produces omission ledger not hallucinated fill.
- Contradictions: emit ContradictionRecord candidates and require source readback before claims.
- Canonical readback: final packet includes exact source version/span/hash for every consequential claim.
- Bypass prevention: graph/vector candidates cannot enter prompt/context as authoritative unless source readback and RSB/UMC receipts bind them.
- Stale graph degradation: direct source registry readback if safe, otherwise HOLD.
