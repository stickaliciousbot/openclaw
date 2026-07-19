# Durable Memory Architecture — Compaction-Gap Recovery Proposal

Status: **design proposal only; not implemented; not an authoritative fact source**
Scope: deterministic recovery of facts and source paths after conversation compaction without promoting lossy summaries to authority.

## 1. Core decision

Compaction must preserve **retrieval coordinates**, not attempt to preserve every fact.

A compaction summary is a T3/T4 navigation aid. It may point to stable entity IDs, claim IDs, source IDs, paths, versions, and unresolved questions, but it must never become the authority for consequential facts. The full transcript remains evidence-of-conversation, not automatically evidence-of-truth.

Vector retrieval is a candidate generator. A typed graph resolves identity and constraints. The canonical source supplies the answer.

## 2. Failure this design prevents

The Altoura pricing miss followed this chain:

1. the canonical document existed under `projects/`, outside the default memory corpus;
2. a condensed MEMORY.md entry ranked weakly;
3. session history was not indexed by the live memory-search configuration;
4. compaction removed the attachment body from active context;
5. retrieval did not deterministically follow the persisted source pointer;
6. an adjacent SKU/user-count interpretation was used instead of validating the licensing unit.

This is not solved by a larger summary or by indiscriminately indexing the workspace.

## 3. Layered model

### L0 — Canonical sources

Original files, owner-approved records, vendor documents, contracts, configuration, and other authoritative artifacts. Each source remains in its native location.

No generated summary may silently replace L0.

### L1 — Source Registry

A compact allowlisted registry containing one record per approved source:

- `source_id` — stable opaque ID;
- canonical path or URI;
- source type and domain;
- authority tier (T0-T4);
- privacy/access class;
- owner or custodian;
- content hash and version;
- effective/expiry dates;
- supersedes/superseded-by edges;
- permitted claim types, extraction, and answer domains;
- aliases and entity IDs represented;
- explicit readback method (file span, database query, API operation, etc.);
- last verification result and timestamp.

The registry stores pointers and metadata, not an uncontrolled copy of every source. Missing, moved, hash-mismatched, expired, or inaccessible sources fail closed for consequential answers.

### L2 — Entity and relationship graph

Stable entities and typed edges:

- organizations, people, products, SKUs, plans, documents, projects, decisions, systems;
- aliases, former names, abbreviations, and lexical variants;
- negative alias/non-equivalence edges so similar products cannot be silently merged;
- `HAS_SKU`, `PRICED_BY`, `APPLIES_TO`, `REQUIRES`, `EXCLUDES`, `NOT_EQUIVALENT_TO`, `SUPERSEDES`, `SUPPORTED_BY_SOURCE`, `CONTRADICTS`, `MENTIONED_IN`, `OWNED_BY`;
- unit ontology: named user, concurrent user, shared device, site, tenant, transaction, hour, month, year;
- temporal validity and jurisdiction/currency qualifiers.

The graph resolves identity and constraint shape. It does not turn inferred edges into authoritative facts.

### L3 — Atomic claim index

One independently verifiable claim per record:

- `claim_id`;
- subject/entity ID;
- predicate;
- typed value/object;
- unit, currency, interval, jurisdiction, scope, and other qualifiers;
- valid-from/valid-to and recorded-at;
- exact source ID, version/hash, and source span/anchor;
- extraction method;
- authority tier;
- confidence in extraction, distinct from source authority;
- status: active, disputed, superseded, withdrawn, unverified;
- contradiction and supersession edges.

Example:

- entity: `altoura.frontline_procedures`
- predicate: `annual_price`
- value: `7800`
- currency: `USD`
- pricing unit: `shared_device`
- user entitlement: `unlimited_users`
- source: canonical Altoura pricing document plus exact section anchor

Price, unit, entitlement, applicability, and source are separate typed fields rather than one dense prose bullet.

### L4 — Search indexes

Two candidate indexes serve different purposes:

1. lexical/FTS for exact names, SKUs, IDs, paths, currencies, and quoted wording;
2. vectors for paraphrases, aliases, related concepts, and candidate expansion.

The indexes may include:

- registry cards;
- atomic claim cards;
- allowlisted sanitized source excerpts;
- owner-direct session history as a lower-authority discovery corpus, if separately approved.

Search scores never confer authority. A high-scoring claim still requires source and constraint validation.

### L5 — Retrieval orchestrator

Deterministic pipeline:

1. classify the request by domain, consequence, and required freshness;
2. resolve entities/SKUs and aliases;
3. infer the required answer dimensions (price, unit, currency, period, jurisdiction, date, etc.);
4. query exact registry/graph records first;
5. use FTS/vector search to expand candidates;
6. rank candidates using identity, authority, freshness, and constraint compatibility—not similarity alone;
7. resolve the canonical source;
8. read the source and verify its hash/version and cited span;
9. validate units, applicability, temporal state, and contradictions;
10. answer with the source reference and material qualifiers, or abstain/ask for the one missing input.

### L5A — Forward Context Reconstruction Graph

The graph can borrow the useful behavior of forward attention without depending on opaque, transient transformer attention tensors.

Every durable object receives a stable identifier suited to its lifecycle:

- stable `entity_guid` for an organization, person, product, project, or system;
- immutable/versioned `claim_guid` for each atomic claim;
- stable `source_guid` plus content-addressed `span_id` for an exact source passage;
- ordered `event_guid` for decisions, observations, and conversation events;
- deterministic `edge_id` derived from source GUID, relation type, target GUID, and qualifier set.

GUIDs preserve identity across compaction and file renames; hashes and versions detect changed content. A GUID alone must never imply that content is current or authoritative.

The graph contains bidirectional typed edges, including forward context edges such as:

- `DEPENDS_ON`, `PRODUCED_BY`, `ELABORATED_IN`, `NEXT_DECISION`, `SUPERSEDED_BY`, `RESOLVED_BY`, `REQUIRES_DIMENSION`;
- reverse/provenance edges such as `SUPPORTS`, `DERIVED_FROM`, `MENTIONED_BY`, `CONTRADICTED_BY`;
- negative edges such as `NOT_EQUIVALENT_TO` and `DOES_NOT_APPLY_TO`.

Multi-party facts should use event/context-frame nodes or hyperedges with named roles rather than collapsing the relationship into ambiguous pairwise links.

For each query, the retriever creates a sparse, ephemeral **attention vector over GUIDs**. It starts with exact and semantic seed nodes, then propagates attention through permitted edges:

```text
a[t+1](v) = normalize(
  query_relevance(q, v)
  + sum(a[t](u) * typed_edge_prior(u -> v))
  + authority_and_freshness(v)
  + missing_slot_coverage(v)
  - privacy_staleness_contradiction_and_redundancy_penalties(v)
)
```

This is query-conditioned graph traversal, not a stored model belief. The attention vector is a retrieval plan and carries no authority.

Traversal uses a bounded beam and a query coverage frame. For a pricing query, required slots might be product/SKU, price, pricing unit, currency, term, effective date, applicability, and authoritative source. Expansion stops when:

1. all required slots are covered by compatible candidates;
2. each consequential claim resolves to a valid canonical source span;
3. contradiction and privacy gates pass; or
4. the budget is exhausted, producing an omission ledger and fail-closed clarification.

The selected subgraph becomes a **Context Reconstruction Packet** containing:

- the query frame and resolved entities;
- ranked GUID paths and why each hop was selected;
- exact source/version/span pointers;
- relevant event ordering and task state;
- contradictions, rejected alternatives, and missing slots;
- a coverage score and omission ledger.

Only verified source spans and non-authoritative navigation metadata enter the final model context. The traversal trace is replayable, so a wrong answer can be audited back through every GUID and edge.

This reconstructs **query-sufficient context**, not every historical token. When exact wording or complete conversational history matters, the graph must resolve the relevant transcript/event GUIDs and fetch those original spans rather than regenerate them.

### L6 — Consequential-answer gate

For commercial/pricing, contracts, configuration, security, permissions, routing, medical/legal/financial implications, and other selected domains:

- source readback is mandatory;
- summaries and session recollections cannot satisfy the gate;
- unit mismatches fail closed;
- unresolved contradictions block a definitive answer;
- stale or unavailable sources are disclosed;
- calculations must bind each operand to a verified unit and source.

For pricing specifically, always resolve:

- exact product/SKU;
- licensing metric;
- quantity-bearing object;
- currency;
- billing period;
- geography/jurisdiction;
- effective date/version;
- included entitlements and exclusions.

A user-count question for a device-priced SKU must not multiply by users.

## 4. Compaction handoff

Before or during compaction, produce a bounded **Continuity Manifest** containing only retrieval coordinates and unresolved state:

- active entity IDs;
- claim IDs referenced in the conversation;
- canonical source IDs and versions;
- open decisions/questions;
- current task/milestone IDs;
- contradictions or missing dimensions;
- privacy/access labels;
- a checksum over the manifest.

The manifest must not synthesize new facts or promote claims. Its job is to tell the next context what to resolve.

The compacted prose summary may reference these IDs, but source and claim data are rehydrated from L1-L3. If the manifest is missing or invalid, the system falls back to entity/source discovery rather than trusting the prose summary.

Current read-only/no-recall-time-write boundaries mean this should first run as an offline/shadow compaction artifact. Automatic generation or injection requires a later, separately approved canary.

## 5. Indexing policy

Do not set `extraPaths` to the entire workspace.

Recommended pattern:

- keep canonical files in place;
- maintain an allowlisted source registry;
- index compact registry and claim cards by default;
- index only approved sanitized source directories/excerpts;
- use source IDs to fetch canonical documents on demand;
- treat session history as discovery evidence only unless a referenced source independently verifies a claim.

This limits privacy leakage, prompt-injection exposure, stale duplicates, and semantic noise.

The live system currently indexes only `MEMORY.md` and `memory/*.md`; no `extraPaths` or session source is configured. The active-memory plugin is also not enabled. These are observable coverage gaps, but turning them on broadly would not create the required authority or provenance semantics.

## 6. Prompt-injection and privacy boundaries

Every source ingestion/readback path must apply:

- source allowlisting and access checks;
- redaction policy before any derived searchable card is emitted;
- schema validation;
- extraction coverage mapping and omission ledger;
- prompt-injection classification (document instructions are data, not commands);
- secret/private-data scanning;
- mutation sentinels;
- no automatic authority promotion;
- no recall-time writes in the read-only phase.

Private/raw canonical sources may be resolved and read only within their authorized context. Search cards should expose the minimum needed for discovery.

## 7. Contradiction, freshness, and supersession

Never overwrite a conflicting claim in place.

- retain each claim with its source/version;
- create explicit `CONTRADICTS` or `SUPERSEDES` edges;
- compute a current-view projection only after authority, effective date, scope, and source freshness checks;
- report disagreement when no deterministic winner exists;
- invalidate derived answers when a source hash/version changes;
- re-extract asynchronously, never during answer-time read-only recall.

Confidence measures extraction quality; authority comes from source policy. A confident extraction from a low-authority source remains low authority.

## 8. Minimal safe implementation sequence

### Phase A — Specification and fixtures (no runtime mutation)

- define source, entity, claim, relation, continuity-manifest, and retrieval-trace schemas;
- encode authority tiers and domain gates;
- build compaction-gap regression fixtures;
- create privacy and injection negative tests.

### Phase B — Read-only registry and resolver

- create a manually allowlisted registry;
- implement `resolve_source(source_id)` with path, hash, version, and access checks;
- emit bounded retrieval traces;
- no vector changes, prompt injection, automatic recall, or writes.

### Phase C — Atomic claims and graph

- extract selected domains into atomic claim records;
- validate source spans and units;
- add alias, supersession, and contradiction handling;
- start with Altoura as a fixture, not a special-case implementation.

### Phase D — Hybrid retrieval shadow mode

- compare graph/FTS/vector candidates against current memory search;
- perform authoritative readback but do not alter live answers;
- measure source hit rate, entity resolution, unit correctness, abstention, and leakage.

### Phase E — Commercial/pricing gate canary

- for owner-approved commercial questions, require source readback and unit validation;
- no automatic source mutation or authority promotion;
- immediate rollback to current behavior plus explicit uncertainty if the gate fails operationally.

### Phase F — Expand by domain

Only after domain-specific fixtures pass, extend to decisions, contacts/CRM, projects, configuration, and other consequential classes.

## 9. Required invariants

1. Lossy summaries never become authoritative.
2. Vector similarity never grants authority.
3. Every consequential claim resolves to a versioned canonical source and span.
4. Entity resolution precedes arithmetic or policy conclusions.
5. Units and applicability are typed and validated.
6. Contradictions are retained and surfaced, not silently merged.
7. Source/hash drift invalidates cached claims.
8. Missing source, missing unit, or unresolved contradiction causes abstention/clarification.
9. Retrieval is read-only; no answer-time memory mutation.
10. Derived indexes are rebuildable from source registry plus approved canonical sources.
11. Compaction manifests preserve coordinates, not synthetic facts.
12. Privacy/access checks apply before retrieval content enters model context.

## 10. Regression suite

At minimum:

- Altoura Procedures after active context and attachment body are absent;
- device-priced SKU with a user-count question;
- adjacent SKU with similar wording but different unit;
- exact alias/SKU and paraphrased query;
- source moved with registry pointer update;
- source hash changed without re-extraction;
- old and new price documents with supersession;
- two authoritative sources with unresolved disagreement;
- incorrect compaction summary but correct canonical source;
- session-only recollection with no canonical source;
- unavailable/private source;
- malicious instructions inside a source document;
- vector index stale while source/graph is current;
- canonical source absent but a dense memory bullet exists;
- arithmetic requiring two differently scoped operands.

Success requires correct source resolution, correct qualifiers, correct answer or correct abstention, and zero authority promotion/leakage.

## 11. Recommendation

Build the registry/resolver and typed claim graph first. Add vectors only as a discovery accelerator around them. Do not begin by widening `extraPaths`, enabling all session indexing, or injecting active-memory output into prompts. Those may improve recall volume while preserving the exact failure mode: a plausible but unverified answer.
