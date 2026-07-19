# Durable Memory Architecture — Compaction-Gap Hydration Packet

Generated: `2026-07-19T06:46:14.432702Z`
Status: **PASS**
Authority: **non-authoritative navigation only**

## Mandatory interpretation

This packet restores retrieval coordinates, design decisions, and build ordering. It does not prove mutable production state and does not authorize implementation. Verify the current Ledger terminal and canonical sources before acting.

## Resume order

1. Read the live M24 and later M25/terminal Ledger state first
2. Read the Ledger project rehydrator and verify it against canonical artifacts
3. Read the systemic LLD and seven-milestone implementation plan
4. Read the integration/build-order design, proposal, and systemic lesson
5. Do not implement Milestone 2 after M24 alone; require Ledger M25 final-completion/freeze PASS and new milestone authorization

## Preserved boundaries

- Finish the currently authorized Memory Ledger work before implementation or surface expansion
- Verify mutable Ledger and runtime state from canonical sources before acting
- No automatic prompt injection or hot-context insertion
- No recall-time memory writes or authority promotion
- No Gateway, model, provider, route, Telegram, Context Bridge, or Ledger mutation
- No implementation milestone or UMC surface expansion is started by this script

## Current Ledger snapshot

Tracked rehydrator summary (may lag uncommitted observation state):

```json
{
  "acceptedBaselineHead": "65d34a6095e4f81f2139c91d80abce3308a9b756",
  "branch": "evidence/stickbot-memory-ledger-v0-1-m23b-sanitized-presentation-default-switch-20260717",
  "currentCloseoutStatus": "PASS",
  "currentGateResult": "25/25 PASS",
  "currentMilestone": "M23B",
  "currentTerminal": "MEMORY_LEDGER_V0_1_M23B_SANITIZED_PRESENTATION_DEFAULT_SWITCH_PASS_ROLLBACK_READY_NO_AUTHORITY_PROMOTION",
  "gitBoundary": "M23B local no-push branch; commit only after all 25 gates PASS; do not push until owner asks",
  "invariants": [
    "Sanitized mode is persisted only in the proven daily caller",
    "M23B verification Telegram sends remain zero",
    "Legacy rollback and sanitized restoration are proven",
    "No Context Bridge or Ledger mutation",
    "No Gateway/model/provider/fallback/Telegram/memory-route mutation",
    "No authority promotion or automatic recall",
    "No recall-time memory write",
    "No raw/private artifact commit",
    "No M24 start",
    "No push without separate owner authorization"
  ],
  "nextBoundary": "M24 \u2014 Sanitized Presentation Default Switch Observation / Soak is PROPOSED_NOT_STARTED and requires separate owner authorization",
  "preferredWorktree": "/tmp/context-bridge-ledger-v0-1-completion-20260717",
  "project": "stickbot-memory-ledger-v0.1",
  "schema": "stickbot.memory_ledger.rehydrator.v8.m23b",
  "status": "PASS"
}
```

Latest bounded M24 runtime observation snapshot, when available:

```json
{
  "boundary_observed": true,
  "checkpoint": "t24h",
  "closeout_status": "ABORT",
  "failed_gates": [
    "MEMORY_LEDGER_V0_1_M24_ABORT_SANITIZED_DEFAULT_NOT_USED"
  ],
  "schema": "stickbot.memory_ledger.m24.status.v1",
  "status": "ABORT",
  "terminal_status": "MEMORY_LEDGER_V0_1_M24_ABORT_SANITIZED_DEFAULT_NOT_USED",
  "updated_utc": "2026-07-18T09:26:03Z"
}
```

## How the capabilities fit together

- **Ledger:** durable, scoped, hashed write model and continuity spine.
- **Source registry:** authority and canonical readback resolver.
- **Knowledge graph:** rebuildable relationship/provenance read model.
- **Vector/FTS:** disposable candidate discovery accelerators.
- **Runtime Service Broker:** scoped capability grants and service receipts.
- **UMC:** turn-level contract, supervision, postcondition proof, and closeout.
- **Surface Service Broker:** channel privacy/capability/rendering boundary.
- **Context Bridge:** sanitized operational projection, never raw memory authority.

## Systemic LLD and seven-milestone implementation plan

# Durable Memory Ledger / Context / Contract / Surface Broker
## Low-Level Design and Systemic Implementation Plan

**Document status:** owner-ready implementation plan; design only; no runtime apply
**Plan version:** `v1.1` — M25 final Ledger completion/freeze boundary
**Initial milestone:** close `M24 — Sanitized Presentation Default Switch Observation / Soak`, then complete `M25 — Memory Ledger v0.1 Final Completion / Freeze`
**Overall authority boundary:** no milestone starts its successor automatically; each production mutation or surface expansion requires explicit owner authorization.

---

## 0. Executive decision

Build one coherent system, but keep its responsibilities separated:

- **Memory Ledger:** durable, scoped, hashed write model and continuity spine.
- **Canonical sources/source registry:** authority and deterministic readback.
- **Knowledge graph:** rebuildable relationship/provenance read projection.
- **FTS/vector indexes:** disposable candidate-discovery accelerators.
- **Context reconstruction engine:** query-conditioned GUID traversal, coverage, source verification, and omission reporting.
- **Runtime Service Broker (RSB):** scoped service grants, budgets, health, cancellation, and deterministic receipts.
- **Universal Model Contract (UMC):** turn envelope, authority, supervision, postconditions, and prose-success prevention.
- **Surface Service Broker (SSB):** channel/session capability, privacy, approval, rendering, delivery, and deduplication boundary.
- **Context Bridge:** sanitized operational projection only.
- **Hydrator:** deterministic operator/developer resume packet; never authority or automatic prompt injection.

The system is built in seven ordered milestones. Core rule: **contract design together, durable core before runtime integration, Runtime Broker before Surface Broker expansion**.

### Roadmap summary

| Milestone | Scope | Production mutation | User-visible change | Success boundary |
|---|---|---:|---:|---|
| 1 | Resume/close M24, then complete Ledger M25 final closure/freeze | M24 observation; M25 closure/evidence only | natural existing M24 announce only | M24 PASS followed by M25 PASS and frozen v0.1 |
| 2 | Contract/schema/threat-model alignment | none | none | accepted contracts, fixtures and rollback design |
| 3 | Offline registry/resolver and Ledger v0.2 draft | disposable/offline only until separately approved | none | authoritative source core and migration candidate |
| 4 | Graph/vector forward-context reconstruction | shadow only | none | replayable source-verified packets and safe degradation |
| 5 | Minimal read-only Runtime Service Broker | bounded loopback integration | none | grant/receipt/postcondition path proven |
| 6 | Owner-direct commercial/pricing UMC canary | narrow feature-gated apply | eligible owner-direct answers only | bounded live PASS and rollback proof |
| 7 | Surface Service Broker and one-cell expansions | one separately approved cell at a time | one reviewed surface/domain at a time | reusable broker plus bounded accepted cells |

---

## 1. Current entry state

At plan creation:

- Commit vocabulary is explicit: M23A binding-base commit is `65d34a6095e4f81f2139c91d80abce3308a9b756`; M23B production-switch subject/accepted branch head is `43a739a8a2b5bf9aab74623ceeafd1becff26a77`; the M24 branch started from that M23B head and its current M24 files remain uncommitted until terminal classification.
- M24 observation began `2026-07-17 19:25:56 AEST` and remains observation-only.
- Current bounded status: `RUNNING`, checkpoint `t2h`, scheduled boundary not yet observed, failed gates `[]`.
- Observer PID `1927859` remained alive at the latest registry readback; harness state `running`.
- The recurring early-abort sentinel `81fa4fcc-69c1-4d2f-8cd7-0dde73807a26` has durable successful run history; T+2 readback completed successfully; the separate final independent readback job is `0b988a5e-214f-4fce-9e75-203520460f0d`.
- Before any action, resolve the active branch/worktree and canonical evidence root from the observer registry and Git readback; `/tmp/...` hydration pointers are evidence coordinates, not an assumption that every temporary path is still canonical.
- Expected natural production boundary: `2026-07-18 06:00 AEST`.
- Expected T+24 completion: `2026-07-18 19:25:56 AEST`; final independent readback approximately `19:28:56 AEST`.
- Protected M24 baseline hashes:
  - Context Bridge events: `4d3966717a5cfe92ba7ae6cc179aea45a7e46a7a453ce1d986a984c82a7549e5`
  - Context Bridge actions: `a7b0d3d4bd1a9c8bb0da20a1f92cc248f3f37dbf551c66a361330076777bba63`
  - Ledger: `f50ff3836724358d2ef99d92d7c32c2c07651138a749e2a03ce5c03c512807f6`
  - OpenClaw config: `a4f0aac75704eb7d171e528c0486fd8baa95260450d38653aea5ba3226e2d859`
  - presentation binding: `26e9004dc83a61604ddd18a3e46cc9a47d441e9074f55ba2d0b9a7db8599207d`
- Future UMC surface expansion remains paused after narrow M10A owner-direct enforcement; expansion must use the proposed RSB/SSB rather than one-off surface patches.

This document does not alter that state.

---

## 2. System architecture

```text
Client / channel / agent surface
            |
            v
+---------------------------+
| Surface Service Broker    |
| identity, privacy, UX,    |
| approvals, render/delivery|
+---------------------------+
            |
            v
+---------------------------+
| Universal Model Contract  |
| ContractEnvelope          |
| required actions/services |
| postconditions/closeout   |
+---------------------------+
            |
            v
+---------------------------+
| Runtime Service Broker    |
| service registry          |
| scoped grants/budgets     |
| timeout/cancel/receipts   |
+---------------------------+
            |
            v
+-----------------------------------------------+
| Read-only Context Reconstruction Service      |
| query frame -> entities -> graph/vector       |
| -> source resolution -> verification          |
| -> packet + deterministic receipt             |
+-----------------------------------------------+
       |            |             |
       v            v             v
 Source Registry  Graph View   FTS/Vector Index
       |            ^             ^
       v            |             |
 Canonical Sources  +---- derived from ----+
       ^                                  |
       +---------- Memory Ledger ---------+
             durable write model

Context Bridge <- sanitized status/receipt hashes only
Hydrator       <- bounded docs + Ledger terminal/readback only
```

### 2.1 Authority order

1. Owner-approved canonical source or authoritative live record.
2. Versioned source-registry metadata and exact source span/hash.
3. Ledger atomic claim/event/source-reference record, non-authoritative unless its source policy explicitly permits the claim type.
4. Graph projection and retrieval packet, rebuildable/non-authoritative.
5. FTS/vector candidate score, discovery only.
6. Session recollection, compacted summary, model prose, or hot context, navigation only.

No lower tier may silently promote itself.

### 2.2 Storage and write boundaries

- Freeze Ledger v0.1 before schema extension.
- Develop new record types in an untracked/test sidecar first.
- A later owner-approved Ledger v0.2 migration may add immutable/versioned records:
  - `source_record`
  - `entity_record`
  - `claim_record`
  - `relation_record`
  - `contradiction_record`
  - `supersession_record`
  - `continuity_manifest_record`
- Runtime query/recall remains read-only.
- Graph/index projections are rebuilt asynchronously from approved records; never written during answer generation.
- Canonical source content remains in its approved native store; registry/Ledger store pointers, hashes, spans, and policy metadata rather than uncontrolled copies.

### 2.3 Identity model

- `entity_guid`: stable across aliases and file moves.
- `source_guid`: stable logical source identity.
- `source_version_id`: immutable version/hash identity.
- `span_id`: content-addressed exact source passage.
- `claim_guid`: immutable/versioned atomic claim.
- `event_guid`: ordered observation/decision/conversation event.
- `edge_id`: deterministic hash of source GUID, relation type, target GUID, and qualifiers.
- `request_id`, `grant_id`, `packet_id`, `receipt_id`: unique runtime contract identifiers.

A GUID proves identity only; authority, freshness, and access are separate gates.

---

## 3. Low-level components

### 3.1 Source Registry and Resolver

**Inputs**

- manually approved source registrations;
- canonical path/URI/query method;
- authority, privacy, scope, and permitted claim types;
- hash/version/effective/expiry metadata;
- aliases/entity GUIDs;
- exact readback method.

**Outputs**

```text
SourceResolutionResult
- source_guid
- source_version_id
- resolved_location
- content_hash
- access_decision
- authority_tier
- freshness_state
- permitted_claim_types
- supersession_state
- exact_span_handles
- terminal: PASS | HOLD_SOURCE_* | FAIL_SOURCE_*
```

**Hard behavior**

- path traversal, symlink escape, inaccessible source, hash mismatch, expiry, unsupported type, or denied privacy scope fails closed;
- source content is treated as data, never instructions;
- moved sources require registry update and versioned audit, never heuristic path substitution for consequential answers.

**Registry administration**

- writes are operator/ingestion-only through a typed change request, never from recall;
- every add/update/revoke binds approver/authority scope, old/new record hashes, source readback proof, effective time, reason, and rollback record;
- changes receive a monotonically increasing registry epoch and immutable audit entry;
- revocation immediately prevents new grants/authoritative packets; active packets tied to the prior epoch are quarantined or re-resolved;
- rollback restores the prior accepted manifest/epoch without deleting the superseded audit trail.

### 3.2 Ledger Record Service

**Write path**

- operator/ingestion-only;
- explicit scope and confirmation;
- schema validation and idempotency key;
- append/version, never in-place historical rewrite;
- source reference and evidence hash required;
- contradiction/supersession represented explicitly;
- privacy scan before tracked evidence.

**Read path**

- read-only connection/query;
- allowed scopes and result limits;
- no usage metadata or query-time memory writes;
- mutation sentinel around every canary/soak.

### 3.3 Graph Projector

Builds a reproducible read projection from accepted registry/Ledger records.

**Node classes**

- entity, source, source version/span, claim, event, decision, task, surface, service, contract.

**Edge classes**

- `HAS_SKU`, `PRICED_BY`, `APPLIES_TO`, `REQUIRES`, `EXCLUDES`, `DEPENDS_ON`, `PRODUCED_BY`, `ELABORATED_IN`, `NEXT_DECISION`, `RESOLVED_BY`, `SUPPORTED_BY_SOURCE`, `DERIVED_FROM`, `MENTIONED_BY`, `SUPERSEDES`, `CONTRADICTS`, `NOT_EQUIVALENT_TO`, `DOES_NOT_APPLY_TO`.

**Projection receipt**

- input Ledger watermark/hash;
- registry hash;
- node/edge counts;
- rejected records and reasons;
- contradiction count;
- output projection hash;
- deterministic replay result.

**Edge-prior governance**

- no opaque model attention tensors or learned weights are persisted as memory;
- edge-type priors live in a versioned, reviewable policy file with author/reason/hash;
- query-conditioned weights are ephemeral and reproducible from the query frame, graph version and policy hash;
- every prior change must pass golden traversal, contradiction, privacy and rollback fixtures before promotion.

### 3.4 FTS/Vector Indexer

- indexes registry cards, atomic claim cards, aliases, and allowlisted sanitized excerpts;
- never indexes the entire workspace by default;
- local embeddings are the default; remote embedding/index providers are prohibited unless separately approved with privacy, retention and egress evidence;
- records embedding provider/model/dimension/config hash and source watermark;
- rebuilds rather than patching unknown/stale index state;
- supports FTS exact IDs/paths/SKUs plus vector paraphrase expansion;
- index score never enters authority calculation except as candidate relevance.

### 3.5 Context Reconstruction Engine

**Pipeline**

```text
classify query/risk
-> create required-slot frame
-> exact entity/alias resolution
-> graph seeds
-> FTS/vector expansion
-> sparse query-conditioned GUID attention traversal
-> coverage/contradiction/privacy checks
-> canonical source readback
-> source-span/hash verification
-> ContextReconstructionPacket + Receipt
```

**Required packet fields**

- query classification and consequence level;
- resolved and rejected entities/SKUs;
- required slots and coverage;
- ranked GUID paths with reasons;
- candidate atomic claims;
- exact source/version/span pointers;
- verified excerpts within privacy/token bounds;
- contradictions/supersession/freshness;
- rejected alternatives;
- omission ledger;
- authority labels;
- packet hash.

**Stop conditions**

- PASS only when required slots and authoritative source conditions are satisfied;
- HOLD on missing source/unit/permission/freshness or unresolved contradiction;
- FAIL on integrity, service, schema, or privacy breach;
- bounded hop, time, token, and source-open budgets.

### 3.6 Runtime Service Broker

**Responsibilities**

- canonical service registry snapshot;
- health/readiness and contract-hash discovery;
- per-turn scoped grant issuance with short TTL, policy epoch and revocation semantics;
- authenticated local service identity and grant integrity (Unix socket or loopback plus a non-exported capability credential/MAC);
- surface/session/privacy policy intersection;
- time/token/hop/source budgets;
- cancellation/deadline propagation;
- idempotent invocation and exactly-once logical receipt acceptance;
- source-version binding through response assembly to prevent verification/use time-of-check-time-of-use drift;
- bypass detection;
- no-write and mutation evidence.

**Core types**

```text
ServiceDefinition
ServiceHealth
ServiceGrantRequest
ServiceAuthorityGrant
ServiceInvocation
ServiceReceipt
ServicePostconditionEvidence
ServiceDenial
```

No model/provider directly calls the reconstruction service without an RSB grant once enforcement is enabled.

### 3.7 UMC Adapter

Adds to `ContractEnvelope`:

- `required_services`;
- `required_context_slots`;
- `consequential_answer_policy`;
- `required_source_authority`;
- `required_postconditions`;
- `allowed_surface_disclosure`.

The postcondition verifier rejects claims such as “I checked the source” unless a valid RSB `ContextReconstructionReceipt` proves source readback and required gates.

### 3.8 Surface Service Broker

**Surface policy record**

```text
SurfacePolicy
- surface_id/type
- identity/session scope
- allowed memory domains
- allowed privacy classes
- permitted service capabilities
- approval requirements
- render/redaction profile
- delivery/deduplication contract
- max context/excerpt budget
- external-send policy
- audit/evidence policy
```

SSB may narrow access, never broaden source authority or RSB grants.

### 3.9 Context Bridge Projection

Context Bridge remains a sanitized operational projection, never the canonical memory store or an authority/control plane. Packet/receipt identifiers exposed there must be Bridge-specific keyed/HMAC aliases with rotation policy, not raw hashes that permit cross-log correlation.

Permitted later:

- service health color/status;
- milestone state;
- sanitized counts;
- packet/receipt hashes;
- latest successful watermark and freshness;
- HOLD/FAIL category without raw source content.

Forbidden:

- raw reconstruction packets;
- source excerpts;
- private entity/query content;
- auth/session identifiers in tracked evidence;
- authority promotion or write control.

### 3.10 Hydrator

The existing `compaction_gap_rehydrate.py` remains an operator/developer tool. It reads allowlisted design and Ledger status sources, validates hashes and forbidden content, emits bounded non-authoritative packets, and never becomes automatic prompt injection.

### 3.11 Deterministic commercial calculation service

Commercial arithmetic is a pure typed subcomponent, not free-form model math:

- inputs: verified `claim_guid` values plus typed `Money(currency, decimal_amount)`, `PriceUnit`, `Term`, `QuantityObject`, quantity, jurisdiction/effective date and applicability;
- decimal arithmetic only—never binary floating point;
- formula and operands are explicit and replayable;
- output receipt binds input claim/source versions, formula version, result and rounding policy;
- it is invokable only after source, unit and applicability gates pass;
- missing device count or a user/device mismatch returns `HOLD_REQUIRED_UNIT_MISSING` or clarification, not arithmetic.

### 3.12 Ephemeral packet retention

- default: raw reconstruction packets remain process-memory only;
- explicit diagnostics may materialize packets only under untracked state with mode `0600`, bounded owner access, TTL no greater than 24 hours, and no durable raw-query log;
- encrypt at rest where the host capability is available; otherwise do not persist packets requiring that protection;
- privacy-scan failure quarantines the packet from rendering/evidence and triggers RED health;
- diagnostic packets are removed at terminal closeout or TTL expiry under the approved ephemeral-state policy; failures to remove/quarantine are evidence and block clean closeout;
- tracked artifacts retain only permitted counts, terminal categories and keyed/non-correlatable aliases.

---

## 4. Runtime contracts

### 4.1 ContextReconstructionRequest

```json
{
  "schema": "stickbot.context_reconstruction.request.v1",
  "request_id": "uuid",
  "idempotency_key": "surface+session+contract scoped opaque id",
  "contract_envelope_id": "uuid",
  "contract_schema": "major.minor+canonical-hash",
  "surface_scope": "owner-direct|web-owner|group|...",
  "session_scope_hash": "non-reversible scoped hash",
  "query": "bounded text",
  "candidate_entity_guids": [],
  "required_slots": [],
  "allowed_source_domains": [],
  "allowed_privacy_classes": [],
  "freshness_requirement": "current|effective_at|historical",
  "consequential_policy": "authoritative_source_required|discovery_only",
  "budgets": {"max_hops": 4, "max_sources": 8, "max_excerpt_tokens": 4000, "deadline_ms": 5000},
  "deadline": {"monotonic_budget_ms": 5000, "wall_clock_observed_at": "timestamp"}
}
```

Budgets are initial bounded defaults and must be benchmarked before production acceptance.

### 4.2 ContextReconstructionReceipt

```json
{
  "schema": "stickbot.context_reconstruction.receipt.v1",
  "receipt_id": "uuid",
  "request_id": "uuid",
  "idempotency_key": "same scoped opaque id",
  "grant_id": "uuid",
  "surface_scope": "bound surface",
  "session_scope_hash": "bound session hash",
  "policy_epoch": "version/hash",
  "issued_at": "timestamp",
  "expires_at": "timestamp",
  "terminal": "PASS|HOLD|FAIL",
  "service_version": "content hash/version",
  "policy_decision": "allow|deny|hold",
  "packet_hash": "sha256|null",
  "source_versions_verified": [],
  "required_slots": [],
  "covered_slots": [],
  "missing_slots": [],
  "contradictions": [],
  "gates": [],
  "postconditions": [],
  "no_write_proof": {},
  "duration_ms": 0,
  "error_code": null
}
```

Receipts contain hashes/metadata; raw private excerpts remain in the bounded packet and are not placed in tracked evidence.

### 4.3 Canonicalization, negotiation and replay

- schemas use explicit IDs/major-minor versions and JSON Canonicalization Scheme (RFC 8785) plus SHA-256 for contract hashes;
- unknown major versions and unknown fields fail closed unless that exact schema explicitly permits extension fields;
- negotiation selects only an allowlisted compatible version and records the chosen hash in grant and receipt;
- one scoped idempotency key binds request -> grant -> packet -> receipt -> render/delivery receipt;
- cancellation or deadline expiry moves later packets/receipts into a non-renderable quarantine state;
- replay across a different surface, session, policy epoch, service instance or contract hash is denied;
- monotonic time controls deadlines; wall-clock time is evidence/context only and cannot extend an expired monotonic budget.

### 4.4 User-facing HOLD/clarification contract

UMC renders a typed HOLD without pretending success:

- concise statement that a definitive answer cannot yet be verified;
- missing/ambiguous slots and the minimum clarification/source needed;
- safe facts that were independently verified, each still bound to source receipts;
- no internal paths, private metadata or fabricated estimate;
- machine terminal and receipt alias remain separate from user prose.

### 4.5 Terminal codes

**PASS**

- `PASS_CONTEXT_RECONSTRUCTED_SOURCE_VERIFIED`
- `PASS_DISCOVERY_ONLY_CANDIDATES_RETURNED`

**HOLD**

- `HOLD_SOURCE_NOT_REGISTERED`
- `HOLD_SOURCE_UNAVAILABLE`
- `HOLD_SOURCE_STALE_OR_HASH_MISMATCH`
- `HOLD_ENTITY_AMBIGUOUS`
- `HOLD_REQUIRED_UNIT_MISSING`
- `HOLD_REQUIRED_SLOT_UNCOVERED`
- `HOLD_CONTRADICTION_UNRESOLVED`
- `HOLD_PRIVACY_SCOPE_DENIED`
- `HOLD_SERVICE_UNAVAILABLE`
- `HOLD_APPROVAL_REQUIRED`

**FAIL**

- `FAIL_SCHEMA_INVALID`
- `FAIL_SOURCE_INTEGRITY`
- `FAIL_PRIVACY_LEAK_DETECTED`
- `FAIL_RECALL_WRITE_DETECTED`
- `FAIL_AUTHORITY_BYPASS_DETECTED`
- `FAIL_DUPLICATE_OR_FORGED_RECEIPT`
- `FAIL_POSTCONDITION_UNVERIFIED`

---

## 5. Global hard gates

These apply to every milestone where relevant.

| Gate | Requirement | Failure disposition |
|---|---|---|
| HG-01 Authority | No summary, model prose, graph score, vector score, or session recollection becomes authority | ABORT affected apply/canary |
| HG-02 Source | Consequential claim resolves to approved source/version/span and claim type; the same source version remains bound through response assembly | HOLD answer/re-resolve; block promotion |
| HG-03 Read-only recall | Before/after Ledger, registry, source, graph, index and config mutation sentinels unchanged during query | ABORT and disable route |
| HG-04 Privacy | Zero secrets/private raw data in tracked evidence, logs, Bridge projection or unauthorized surface output | ABORT; quarantine evidence |
| HG-05 Injection | Retrieved content cannot alter tool/service/routing/policy instructions | FAIL fixture/turn; block promotion |
| HG-06 Unit/applicability | Required units, quantity-bearing object, date, jurisdiction and scope validated | HOLD; no arithmetic/definitive answer |
| HG-07 Contradiction | Conflicting active claims retained and resolved by policy or surfaced | HOLD; no arbitrary selection |
| HG-08 Freshness | Registry/source/graph/index watermarks compatible; stale projections detected | HOLD/degrade to source-only |
| HG-09 Broker bypass | Once broker enforcement is enabled, direct service invocation count is zero | ABORT and off-switch |
| HG-10 Receipt integrity | Request/grant/packet/receipt hashes and IDs bind exactly; duplicates/forgeries rejected | ABORT affected path |
| HG-11 UMC prose-success | UMC cannot claim source/tool/delivery success without verified receipt/postcondition | HOLD/FAIL turn; block promotion |
| HG-12 Surface least privilege | SSB policy intersection only narrows access; no cross-session/group leakage | ABORT surface canary |
| HG-13 Delivery | Exactly one expected response/delivery; duplicate or unexpected sends zero | ABORT surface canary |
| HG-14 Rollback | Tested off-switch and exact pre-state readback exist before apply | BLOCKED; do not apply |
| HG-15 Health | Required liveness/readiness/dependency checks green before and during apply/soak | HOLD or rollback per severity |
| HG-16 Evidence | Required artifacts, hashes, gates, source map, privacy scan, and terminal status complete | No PASS/commit/push |
| HG-17 Git safety | Only allowlisted sanitized files staged; dirty/untracked private state and state/DB/WAL/SHM/secrets/telemetry/pycache block commit | ABORT commit |
| HG-18 Hydration | Hydrator strict validation and compact-gap resume fixture pass | No milestone closeout |
| HG-19 Observer | Any soak has deterministic detached owner, registry, PID/PGID/SID proof, checkpoint history and independent terminal sentinel | BLOCKED; no soak start |
| HG-20 No silent successor | Completing a milestone never starts the next one without owner authorization | Stop at boundary |

---

## 6. Health model

### 6.1 Health states

- **GREEN:** service works, dependencies current, policy/hash contracts match, no mutation/privacy/authority alerts.
- **YELLOW:** optional accelerator unavailable or stale; deterministic safe degradation works (for example graph/vector -> registry/source-only). No consequential PASS may rely on the failed component.
- **RED:** source/receipt integrity, privacy, write, authority, broker bypass, duplicate delivery, or required dependency failure. Fail closed and disable affected route.

### 6.2 Required health checks

| Check | Method | Green condition | Red trigger |
|---|---|---|---|
| HC-01 Ledger integrity | read-only open + schema/version + integrity check + before/after hash | readable, expected version, unchanged | mutation/corruption/version mismatch |
| HC-02 Registry integrity | schema, path policy, record hashes, duplicate GUID scan | all records valid; duplicate IDs zero | invalid record, path escape, secret |
| HC-03 Source resolution | exact fixture reads and hash/span verification | required sources resolve exactly | hash/span/access mismatch |
| HC-04 Graph parity | compare Ledger/registry watermark and projection receipt | deterministic hash/count parity | missing accepted records or unexplained edges |
| HC-05 Index freshness | embedding config/dimension and source watermark | compatible/current or explicitly degraded | incompatible dimension/silent stale use |
| HC-06 Reconstruction smoke | exact, paraphrase, contradiction, stale and unit fixtures | expected PASS/HOLD/FAIL exactly | any false authoritative PASS |
| HC-07 RSB liveness | local `/health/live` or equivalent function probe | process/responding | no response/crash |
| HC-08 RSB readiness | contract hash, service registry, dependencies, policy snapshot | exact accepted hashes and dependencies | mismatch/bypass/no off-switch |
| HC-09 Receipt round-trip | mock request -> grant -> receipt -> verifier | IDs/hashes/postconditions exact | forged/duplicate/unbound receipt accepted |
| HC-10 UMC vertical smoke | action/service-required fixture | deterministic terminal; no prose success | unsupported success claim |
| HC-11 SSB policy | matrix and cross-surface negative fixtures | least-privilege intersection | privacy/scope widening |
| HC-12 Delivery/dedupe | no-send first; later one bounded live response | expected count exactly | duplicate/unexpected send |
| HC-13 Privacy/injection | secret, PII, document-instruction fixtures | zero leak; instructions treated as data | any leak/policy override |
| HC-14 No-write sentinel | hashes/row counts/config/routes before/after | unchanged during recall | any recall-time write/mutation |
| HC-15 Context Bridge projection | schema + redaction + count/hash-only fields | sanitized/non-authoritative | raw packet/excerpt/private ID |
| HC-16 Hydration | strict check-only + generated packet replay | complete, bounded, source hashes valid | missing required source or unsafe content |

### 6.3 Initial performance objectives

These are acceptance targets to validate and may only be relaxed through an explicit documented decision:

- registry exact resolution p95 <= 100 ms local;
- graph/FTS candidate retrieval p95 <= 500 ms local;
- bounded reconstruction without remote source p95 <= 2 s;
- deadline exhaustion always returns deterministic HOLD, never partial authoritative PASS;
- service crash/restart never loses canonical data because indexes/graphs are rebuildable;
- zero privacy, write, authority, bypass, receipt-integrity, or duplicate-delivery events.

### 6.4 Soak/checkpoint requirements

- No rapid polling loops.
- Short local canaries: T+0, T+15m, T+30m, T+60m as appropriate.
- Production-facing canaries: minimum T+0/T+2/T+8/T+24 plus natural production boundary when schedule-driven.
- Independent sentinel checks early abort at a bounded cadence.
- Long observers must have a dedicated registry and terminal wake/cron independent from the primary process.
- Every checkpoint stores bounded hashes, counts, booleans, terminal categories, and omissions—not raw private packets.

---

## 7. Milestone plan

# Milestone 1 — Resume M24, then complete Ledger M25 final closure/freeze

**Purpose:** complete the already-running M24 observation correctly, then run a separate final Ledger M25 milestone that formally completes and freezes Memory Ledger v0.1 before any new architecture work.

**Entry state:** M24 `RUNNING`, T+2 reached, observer alive, sentinel and T+2 run history successful, no failed gates. M25 is not started.

### Submilestone 1A — M24 semantic terminal

Continue observation through T+8, the natural boundary, T+24 and independent final readback. M24 must close PASS. Its presentation-soak PASS does not itself freeze Ledger schemas/contracts and does not unlock Milestone 2.

### Submilestone 1B — Ledger M25 final completion/freeze

Only after M24 has a durable PASS and its sanitized closeout/local commit are verified: issue a separate owner-visible M25 STARTED notice with pass criteria and expected artifacts; resolve canonical worktree/branch/head; reconcile the full v0.1 milestone/terminal history; require clean allowlisted Git state; build final sanitized evidence, privacy scan, mutation sentinels, freeze declaration, rollback/readback proof and updated rehydrator; create the M25 terminal commit. M25 is closure/freeze only—no new feature, schema, runtime, route, memory-authority or surface mutation.

M24 HOLD/ABORT blocks M25. M25 HOLD/ABORT blocks all new-LLD implementation.

### Tasks

1. Rehydrate from M24 canonical status, registry, run ledger, job definitions, and project rehydrator.
2. Verify observer PID/start-time anchor, registry ownership, harness health, sentinel durable history, and T+2 artifact.
3. Continue observation without manual production cron invocation or manual Telegram send.
4. Capture T+8.
5. Observe the natural 06:00 AEST production boundary.
6. Require exactly one expected sanitized announce and no duplicate/unexpected delivery for PASS.
7. Continue through T+24 and final independent readback.
8. Classify PASS, explicit no-boundary HOLD, or ABORT.
9. Generate the sanitized M24 closeout, hard gates, privacy scan, source map, mutation sentinels, evidence manifest, docs, milestones, troubleshooting update, and rehydrator.
10. Commit M24 locally only after terminal classification; push only with separate authorization.
11. If and only if M24 closes PASS, send the separate Ledger M25 STARTED notice with its pass criteria and expected closeout artifacts.
12. Execute M25 final terminal convergence/freeze: reconcile v0.1 history, declare frozen contracts/schema/authority boundaries, verify canonical Git/evidence state, regenerate final rehydration, and produce M25 closeout artifacts.
13. Commit M25 locally only after every M25 gate passes; record the owner-selected preservation disposition (`pushed` or explicitly `local-only`).

### M1A / M24 hard gates

- M1-G01 observer identity/anchor/PID/PGID/SID valid and no duplicate owner;
- M1-G02 T+0/T+2/T+8/T+24 artifacts plus the separate final sentinel/readback are parse-valid and time-ordered;
- M1-G03 recurring sentinel history exists with no missed early-abort condition;
- M1-G04 production caller remains the same proven caller and schedule;
- M1-G05 selector remains caller-local explicit `sanitized`;
- M1-G06 binding hash exact and `--no-send` preserved;
- M1-G07 caller tools remain `read`, `write`, `exec`; no `message` tool;
- M1-G08 production cron was not manually run;
- M1-G09 manual Telegram verification sends zero;
- M1-G10 natural boundary classified from production run ledger;
- M1-G11 exactly one expected sanitized announce with accepted presentation semantics for PASS; duplicates, unexpected sends or unsanitized output zero;
- M1-G12 protected events/actions/Ledger/config hashes unchanged;
- M1-G13 no model/provider/fallback/route/Gateway mutation;
- M1-G14 no authority/automatic recall/hot-context/recall-write mutation;
- M1-G15 rollback remains exact and available;
- M1-G16 observer terminal is not `UNKNOWN` or merely process-exited;
- M1-G17 private/raw/credential scan clean;
- M1-G18 state/DB/WAL/SHM/telemetry/pycache excluded from Git;
- M1-G19 M24 docs and rehydrator agree with terminal;
- M1-G20 original M20 remains historical HOLD;
- M1-G21 no M25 starts before M24 PASS and no new-architecture implementation starts;
- M1-G22 final evidence manifest hashes all closeout artifacts;
- M1-G23 independent terminal readback agrees with semantic observer; missing/ambiguous sentinel or process-only exit classifies HOLD, never PASS;
- M1-G24 recurring sentinel removed only after durable terminal;
- M1-G25 M24 verifies exact canonical worktree/branch/head, clean allowlisted Git state, evidence/rehydrator parity and local commit only after all applicable gates and terminal classification.

### M1B / Ledger M25 hard gates

- M25-G01 accepted M24 terminal is exact PASS, not HOLD/ABORT/process exit;
- M25-G02 M24 closeout commit, evidence manifest, privacy scan, mutation sentinels and rehydrator all agree;
- M25-G03 canonical active worktree, branch, subject commit, branch head and upstream disposition are explicit;
- M25-G04 original M20 HOLD and all later recovery/terminal semantics remain historically accurate;
- M25-G05 M21–M24 accepted terminals, commits, manifests and preservation states reconcile without contradiction;
- M25-G06 Ledger v0.1 schema/contracts/authority/read-only boundaries are declared frozen and content-hashed;
- M25-G07 protected Context Bridge events/actions, Ledger, OpenClaw config, binding and production caller state match the accepted post-M24 baseline;
- M25-G08 no feature, schema, runtime, route, model/provider/fallback, Telegram, memory-authority, recall-write or surface mutation;
- M25-G09 final rollback/readback and no-send safety posture remain documented and usable;
- M25-G10 final rehydrator is complete, internally consistent and resolves M25 as the terminal Ledger v0.1 milestone;
- M25-G11 private/raw/credential scan and Git allowlist are clean; state/DB/WAL/SHM/telemetry/pycache remain untracked;
- M25-G12 final evidence manifest hashes every M25 closeout artifact;
- M25-G13 worktree is clean after the allowlisted terminal commit;
- M25-G14 preservation disposition is explicit: exact remote alignment if separately authorized, otherwise an explicit accepted local-only boundary; no implicit push;
- M25-G15 Milestone 2 remains not started until M25 PASS is owner-visible and durable.

### M1 health checks

M24 observer process/registry; checkpoint freshness; cron sentinel history; production caller/run ledger; delivery count; protected hashes; rollback readback; privacy scan; Git allowlist; M24 rehydrator strict run; then M25 canonical-history reconciliation, frozen-contract hash check, protected-state parity, final rehydrator, final Git/evidence consistency and preservation readback.

### M1 terminals

- `MEMORY_LEDGER_V0_1_M24_SANITIZED_PRESENTATION_DEFAULT_SWITCH_OBSERVATION_PASS_NO_AUTHORITY_PROMOTION`
- `MEMORY_LEDGER_V0_1_M24_HOLD_NO_SCHEDULED_PRESENTATION_BOUNDARY_OBSERVED`
- `MEMORY_LEDGER_V0_1_M24_ABORT_<FIRST_HARD_GATE_FAILURE>`
- `MEMORY_LEDGER_V0_1_M25_FINAL_COMPLETION_FREEZE_PASS_NO_AUTHORITY_PROMOTION`
- `MEMORY_LEDGER_V0_1_M25_HOLD_FINAL_COMPLETION_GATES_INCOMPLETE`
- `MEMORY_LEDGER_V0_1_M25_ABORT_<FIRST_HARD_GATE_FAILURE>`

### M1 expected closeout artifacts

Under the M24 tracked evidence root: preflight/current-state, checkpoint summary, natural-boundary proof, delivery classification, mutation sentinels, privacy scan, hard gates, closeout JSON, summary Markdown, evidence manifest, rehydrator update, milestone/troubleshooting updates.

Under the M25 final-completion evidence root: preflight/canonical-history reconciliation, branch/head/preservation map, frozen-contract/schema/authority declaration, protected-state parity, mutation sentinels, rollback/readback proof, privacy/Git scan, hard gates, terminal closeout JSON, owner-ready summary, evidence manifest, and final Ledger v0.1 rehydrator.

**Successor boundary:** only M25 PASS formally completes Ledger v0.1. Then stop and request owner authorization for Milestone 2.

---

# Milestone 2 — Contract alignment and threat model, no runtime integration

**Purpose:** freeze interfaces before building code so durable memory, Ledger, RSB, UMC and SSB share one contract vocabulary.

### Tasks

1. Freeze Ledger v0.1 compatibility contract and migration policy.
2. Define JSON Schemas for source, entity, claim, relation, contradiction, supersession, continuity manifest, reconstruction request/packet/receipt, service grant, surface policy, and sanitized Bridge projection.
3. Define authority matrix by claim type/domain.
4. Define privacy classes and surface-disclosure matrix.
5. Define unit/applicability ontology and consequential-answer policies.
6. Define UMC envelope/postcondition additions.
7. Define RSB service/grant/receipt/bypass contract.
8. Define SSB capability/privacy/render/delivery contract.
9. Complete threat model: prompt injection, source poisoning, alias overmerge, stale projection, receipt forgery/replay, cross-session leakage, direct service bypass, duplicate delivery, recall-write loops.
10. Create fixture corpus and rollback/compatibility plan.

### M2 hard gates

- all schemas parse and validate positive fixtures;
- every schema has negative/malformed/unknown-field tests;
- v0.1 readers remain compatible or fail closed on v0.2 draft records;
- authority and privacy matrices cover every field and surface;
- no free-form model prose controls authority/grants/terminal state;
- receipt IDs/hashes bind request, grant, packet, service version and postconditions;
- exact denial/HOLD/FAIL terminal codes defined;
- source content classified as data, not instruction;
- no production config/runtime/schema/data mutation;
- no route/surface/model/fallback expansion;
- rollback and migration-reversal strategy documented;
- fixture corpus includes Altoura, contradiction, stale source, private source, malicious source instructions, missing unit, ambiguous entity, duplicate receipt and cross-surface leakage;
- hydrator includes the accepted schemas/design source map.

### M2 health checks

Schema compiler/validator; fixture coverage report; contract hash generation; threat-model coverage; privacy-field inventory; v0.1 compatibility replay; hydrator strict pass.

### M2 terminal

`DURABLE_MEMORY_SYSTEM_M2_CONTRACT_ALIGNMENT_PASS_NO_RUNTIME_INTEGRATION`

**Successor boundary:** owner review/authorization before Milestone 3.

---

# Milestone 3 — Offline source registry, Ledger v0.2 draft and durable-memory core

**Purpose:** implement the authoritative source-resolution and atomic-record foundation without live recall or prompt integration.

### Submilestone 3A — Sidecar/offline core

- local allowlisted registry;
- safe path/URI/query resolver;
- GUID/version/span rules;
- atomic claim/entity/relation records;
- contradiction/supersession engine;
- unit/applicability validation;
- bounded extraction with coverage/omission ledger;
- Altoura fixtures as a general regression class;
- no live Ledger mutation.

### Submilestone 3B — Ledger v0.2 migration candidate

- migration preview against a disposable v0.1 copy;
- exact backup/hash and rollback proof;
- append-only/versioned record admission;
- old-reader fail-closed/compatibility proof;
- deterministic export/rebuild;
- owner approval package before any production Ledger schema/data change.

### M3 hard gates

- registry allowlist and path-containment tests pass;
- canonical source hash/span verification is deterministic;
- claim records cannot exist without valid source reference unless explicitly `unverified` and barred from consequential answers;
- duplicate GUID and alias-overmerge fixtures rejected;
- negative alias (`NOT_EQUIVALENT_TO`) fixtures pass;
- price/unit/currency/term/applicability stored as typed fields;
- contradictions retained, never overwritten;
- source update invalidates stale claim projection;
- prompt-injection fixtures cannot alter extraction policy;
- secrets/private raw content absent from tracked artifacts;
- source registry and Ledger stores unchanged during query tests;
- sidecar DB/state untracked;
- migration preview and rollback on disposable copy pass before any owner approval package;
- Altoura compaction-gap fixture answers Procedures correctly and never multiplies by user count;
- missing device count produces correct explanation/HOLD, not fabricated arithmetic;
- no runtime, config, memory-search, active-memory, Context Bridge or surface mutation.

### M3 health checks

Registry integrity; source resolver exact-read smoke; SQLite/schema integrity on disposable stores; deterministic export hash; mutation sentinels; extraction coverage; contradiction/supersession fixture; privacy/injection scan; hydration packet.

### M3 terminal

`DURABLE_MEMORY_SYSTEM_M3_OFFLINE_CORE_PASS_NO_RUNTIME_INTEGRATION`

**Successor boundary:** owner authorization before graph/vector shadow work.

---

# Milestone 4 — Graph/vector forward-context reconstruction in shadow mode

**Purpose:** reconstruct query-sufficient context using graph attention and candidate indexes while remaining invisible to live answers.

### Tasks

1. Build deterministic graph projector and receipts.
2. Build FTS exact lookup and vector candidate index from approved cards/excerpts only.
3. Implement query frame and required-slot classifier.
4. Implement entity/alias/negative-alias resolver.
5. Implement bounded sparse attention propagation across typed GUID edges.
6. Implement coverage, contradiction, freshness, privacy and omission gates.
7. Implement canonical source readback after candidate traversal.
8. Produce replayable reconstruction packet/receipt.
9. Run shadow comparisons against current memory search and compaction-gap fixtures.
10. Add safe degradation: vector unavailable -> graph/FTS/source; graph stale -> registry/source; source unavailable -> HOLD.

### M4 hard gates

- graph projection deterministic from the same inputs;
- unexplained node/edge count delta zero;
- vector index watermark/config/dimension recorded and checked;
- vector-only authoritative answer path impossible;
- all consequential PASS packets include verified source/version/span;
- query-sufficient coverage calculated; omissions explicit;
- exact historical wording fetches original transcript/source spans rather than regeneration;
- stale graph/vector fixtures degrade safely;
- ambiguous entity and unresolved contradiction never produce arbitrary PASS;
- privacy-denied source never appears in packet/excerpt;
- no live prompt injection, answer modification, memory write or service route;
- authority violations, privacy leaks and recall writes all zero;
- Altoura and all negative fixtures pass from compacted/no-active-context state;
- initial local performance objectives met or explicit HOLD with optimization plan;
- shadow observer and independent terminal sentinel satisfy HG-19.

### M4 health checks

Graph parity/watermark; index dimension/freshness; reconstruction fixture smoke; fallback/degradation smoke; source/hash verification; no-write and privacy sentinels; p50/p95 latency; packet/receipt replay; hydrator.

### M4 terminal

`DURABLE_MEMORY_SYSTEM_M4_SHADOW_RECONSTRUCTION_PASS_NO_PROMPT_INJECTION`

**Successor boundary:** owner authorization before RSB integration.

---

# Milestone 5 — Minimal read-only Runtime Service Broker path

**Purpose:** prove a complete runtime-owned service contract without changing user-visible answers or adding surfaces.

### Tasks

1. Implement canonical local service registry and version/contract hashes.
2. Implement grant request/policy intersection and scoped authority grants.
3. Implement timeout/cancellation/budget enforcement.
4. Register one service: read-only Context Reconstruction.
5. Implement invocation/receipt binding and exactly-once logical receipt acceptance.
6. Implement direct-bypass detection.
7. Add UMC service-required fields and postcondition verifier in mock/no-render mode.
8. Execute vertical path:

```text
ContractEnvelope
-> RSB grant
-> reconstruction invocation
-> packet/receipt
-> UMC postcondition verifier
-> shadow response assembler
-> terminal UMC receipt
```

9. Add off-switch and route/readback proof.
10. Run local soak with independent observer.

### M5 hard gates

- no service call without accepted authenticated grant and service identity;
- denied/expired/revoked/wrong-policy-epoch/wrong-surface/wrong-scope grants fail closed;
- capability credentials remain outside tracked config/evidence and are revocable;
- repeated invocation with the same idempotency key cannot produce multiple logical receipts or writes;
- direct-bypass accepted count zero;
- duplicate/forged/replayed/cross-surface/late receipts rejected;
- timeout/cancel returns deterministic HOLD/FAIL and no late authoritative result;
- service unavailability degrades to explicit HOLD, never model guess;
- UMC prose-success impossible without receipt/postcondition;
- read-only and no-write sentinels unchanged;
- service binds loopback only; no LAN/Tailscale exposure;
- no new Telegram/Web/group/XR surface;
- no external send and no live answer modification;
- off-switch restores exact pre-integration state;
- health/readiness/contract hashes green through soak;
- zero privacy, authority, bypass, write, duplicate-receipt and route mutation events.

### M5 health checks

RSB live/ready; service registry/contract hash; reconstruction dependency health; grant/deny smoke; timeout/cancel; receipt verifier; UMC mock vertical smoke; off-switch readback; loopback bind check; mutation/privacy sentinels; soak checkpoints.

### M5 terminal

`DURABLE_MEMORY_SYSTEM_M5_RUNTIME_SERVICE_BROKER_READONLY_PASS_NO_SURFACE_EXPANSION`

**Successor boundary:** separate owner approval package for Milestone 6.

---

# Milestone 6 — Narrow owner-direct commercial/pricing UMC canary

**Purpose:** use the existing narrow owner-direct UMC surface to prove authoritative source reconstruction on eligible commercial/pricing turns.

### Pre-apply package

- exact code/config/mutation set and hashes;
- accepted M5 receipts/contracts;
- owner-direct scope only;
- eligible intent definition;
- fallback/HOLD behavior;
- off-switch and rollback command/readback;
- no-send fixture results;
- expected live observations and delivery boundary;
- explicit exclusions: group, Web/LAN, Gmail/Drive/Calendar, voice/XR, general-user traffic, memory writes, route/model/fallback expansion.

### Canary phases

M6 uses only the already-accepted owner-direct UMC/Telegram scope policy. It must not create an `SSB-equivalent` reusable shim or a bypass around the future SSB; the future M7 kernel will replace this narrow policy adapter. If the RSB receipt cannot be exposed through that accepted narrow path without adding reusable surface-policy code, M6 must HOLD and the plan must be explicitly rebaselined to build M7A kernel/no-new-surface first.

1. owner-direct shadow classification, no answer change;
2. owner-direct no-send response comparison;
3. explicit approved limited live enablement;
4. bounded eligible turns/fixtures;
5. T+0/T+2/T+8/T+24 observation with natural owner traffic where possible;
6. rollback/readback exercise if required by package;
7. terminal classification and preservation.

### M6 hard gates

- exact owner-direct scope and eligible commercial/pricing intents only;
- authoritative source readback required for every definitive commercial claim;
- product/SKU, unit, currency, term, quantity type, geography/effective date and applicability validated;
- vector/session/summary-only answer path impossible;
- missing source/unit/device count/contradiction produces HOLD/clarification;
- no recall-time writes or authority promotion;
- no unexpected tool/service grants;
- no direct service bypass;
- exactly one normal response delivery per turn; duplicate/unexpected sends zero;
- no Telegram health regression, reset, unresponsive event or manual Gateway recovery during clean PASS window;
- no broad UMC authority or surface expansion;
- off-switch verified before apply and remains available;
- privacy/redaction policy satisfied in rendered answer and evidence;
- observation health/checkpoint history complete;
- at least one eligible natural owner-direct turn is required for production PASS; if none occurs, terminal is `HOLD_NO_ELIGIBLE_OWNER_DIRECT_TRAFFIC` even if fixture/no-send validation passes;
- all tracked evidence sanitized and manifest-hashed.

### M6 health checks

Telegram/Gateway existing health; UMC enforcement readback; SSB-equivalent owner-direct policy shim readback; RSB live/ready; reconstruction smoke; service/UMC receipts; delivery dedupe; source/unit fixture; no-write/privacy/route sentinels; observer health.

### M6 terminal

`DURABLE_MEMORY_SYSTEM_M6_OWNER_DIRECT_COMMERCIAL_CANARY_PASS_NO_AUTHORITY_PROMOTION`

Any privacy, write, authority, bypass or duplicate-delivery event requires immediate disable and ABORT.

**Successor boundary:** owner review before building/expanding SSB.

---

# Milestone 7 — Surface Service Broker and bounded surface/domain expansion

**Purpose:** replace one-off surface integrations with a reusable least-privilege broker and expand one reviewed cell at a time.

### Submilestone 7A — SSB kernel, no new surface

- surface registry and policy schema;
- identity/session scope adapter;
- privacy/capability intersection;
- approval requirements;
- render/redaction profiles;
- delivery/deduplication receipts;
- RSB/UMC integration;
- no-send/mock fixtures.

### Submilestone 7B — Existing owner-direct path through SSB

- route the already-proven owner-direct commercial path through SSB;
- prove semantic/output parity, no duplicate send, exact rollback;
- no new surface yet.

### Submilestone 7C+ — One surface/domain cell per milestone

Candidate order, each separately authorized:

1. owner-authenticated Web UI, loopback only;
2. owner-authenticated LAN/Tailscale only after explicit exposure plan and host/network verification;
3. additional read-only business domains such as opportunities/CRM/project decisions;
4. voice/XR presentation only after privacy/rendering and stale-command lifecycle gates;
5. groups/shared surfaces last, with deny-by-default private-memory policy;
6. external-write services only under separate stronger approval, postcondition and delivery contracts.

### M7 hard gates

- every surface has explicit identity/session/privacy/capability policy;
- policy intersection can only narrow RSB grants;
- cross-surface, cross-user, cross-session and group leakage fixtures all deny;
- no private memory in groups/shared surfaces by default;
- render/redaction/delivery receipt exactly bound to UMC terminal receipt;
- duplicate delivery zero;
- surface unavailable cannot cause bypass to a broader surface;
- loopback is default; non-loopback bind requires explicit owner approval, host location/address map, firewall/forwarding proof, local health then representative authenticated POST/mutation proof;
- each surface/domain cell has separate apply, off-switch, rollback, observer and terminal;
- Context Bridge receives only sanitized status/receipt hashes;
- no broad authority promotion from one accepted cell;
- production expansion matrix and evidence remain comprehensible and reversible.

### M7 health checks

SSB live/ready/policy hash; identity/session scope; privacy matrix; RSB dependency; UMC receipt binding; render/redaction golden tests; delivery/dedupe; cross-surface negative fixtures; network exposure checks when applicable; no-write/privacy/authority sentinels; per-cell soak.

### M7 terminal

For the kernel:

`DURABLE_MEMORY_SYSTEM_M7A_SURFACE_SERVICE_BROKER_KERNEL_PASS_NO_NEW_SURFACE`

For each accepted cell:

`DURABLE_MEMORY_SYSTEM_M7_CELL_<SURFACE>_<DOMAIN>_PASS_BOUNDED_SCOPE`

Overall v1 only after all owner-selected cells close:

`DURABLE_MEMORY_LEDGER_CONTEXT_CONTRACT_SURFACE_BROKER_V1_PASS_BOUNDED_PRODUCTION`

---

## 8. Test strategy

### 8.1 Unit

- schema, GUID, hash/span, path policy, unit ontology, alias/negative-alias, contradiction/supersession, budget and terminal-code logic.

### 8.2 Contract

- request/grant/invocation/packet/receipt/UMC/SSB schema and hash binding;
- version mismatch and unknown-field handling;
- v0.1/v0.2 compatibility.

### 8.3 Retrieval regression

- Altoura Procedures from compacted/no-active-context state;
- adjacent Remote Expert SKU;
- user-count vs shared-device pricing;
- exact and paraphrased aliases;
- moved source, changed hash, superseded price;
- conflicting authoritative sources;
- wrong compacted summary but correct source;
- session-only unsupported recollection;
- unavailable/private source;
- malicious source instructions;
- stale vector/graph;
- multi-operand arithmetic with mismatched units.

### 8.4 Broker/UMC

- grant allow/deny/expiry/scope;
- direct bypass;
- timeout/cancel and late receipt;
- duplicate/forged/replayed receipt;
- unavailable dependency;
- prose-success attempts without evidence;
- off-switch and rollback.

### 8.5 Surface/privacy

- owner direct, owner Web, group/shared, wrong account/session;
- redaction and excerpt budgets;
- duplicate delivery/dedupe key;
- fallback route widening attempts;
- surface-to-surface replay;
- private-memory denial in group.

### 8.6 Property/fuzz/chaos

- malformed graphs and cyclic edges;
- random alias collisions;
- source/graph/index watermark skew;
- source changes after verification but before response assembly;
- grant revocation/policy-epoch change during invocation;
- service crash between grant and receipt;
- network timeout and partial packet;
- disk read-only/full for derived stores;
- clock skew around effective dates and grant expiry.

---

## 9. Evidence and repository contract

### 9.1 Tracked

- design/LLD/schema documents;
- source code and tests;
- sanitized fixture corpus;
- hard-gate results;
- mutation sentinel summaries;
- privacy scan summaries;
- bounded closeout JSON/Markdown;
- evidence manifest with SHA-256;
- rehydrator/hydrator updates;
- rollback/runbook documentation.

### 9.2 Never tracked

- production Ledger DB/WAL/SHM;
- raw registry/graph/index state;
- raw reconstruction packets/excerpts;
- raw session/chat/account identifiers;
- credentials, tokens, auth headers;
- telemetry/log dumps containing private queries;
- raw query text in durable service logs by default; use bounded hashes/categories/latencies and opt-in untracked diagnostics only;
- observer state, PIDs, temporary files;
- pycache/pyc;
- unrelated runtime configuration snapshots.

### 9.3 Standard milestone artifacts

```text
<Milestone>_PREFLIGHT.json
<Milestone>_SOURCE_MAP.json
<Milestone>_CONTRACTS.json
<Milestone>_HEALTH.json
<Milestone>_MUTATION_SENTINELS.json
<Milestone>_PRIVACY_SCAN.json
<Milestone>_HARD_GATES.json
<Milestone>_ROLLBACK_PROOF.json
<Milestone>_CLOSEOUT.json
<Milestone>_SUMMARY.md
<Milestone>_EVIDENCE_MANIFEST.json
```

Each closeout identifies subject commit, branch, worktree, current authority, applied mutations, terminal status, next boundary, and whether push occurred.

---

## 10. Rollback matrix

| Component | Off-switch/rollback | Safe degraded state |
|---|---|---|
| Source registry | disable new registry version; restore prior signed/hash manifest | explicit source-unavailable HOLD |
| Ledger v0.2 | restore exact v0.1 snapshot or disable v0.2 readers; no destructive down-migration | v0.1 operator-only read-only recall |
| Graph projector | discard projection and rebuild | registry/source-only lookup |
| Vector index | disable/discard index | FTS/graph/source-only lookup |
| Reconstruction engine | disable service route | current explicit memory/source lookup with uncertainty |
| RSB | disable service registration/enforcement patch and verify direct path policy | pre-M5 runtime; no reconstruction service |
| UMC adapter | revert service-required envelope fields/feature gate | accepted M10A/current UMC baseline |
| SSB | disable one surface/domain cell or entire SSB route | previous accepted surface route |
| Context Bridge projection | disable projection | existing sanitized Bridge presentation |

Rollback never rewrites historical evidence or treats a failed milestone as PASS.

---

## 11. Milestone operating protocol

For every milestone:

1. Send owner-visible **STARTED** notice with scope, boundaries, pass criteria, expected artifacts, and abort triggers.
2. Rehydrate canonical state before mutation.
3. Snapshot/hash protected state.
4. Run preflight and negative fixtures.
5. Apply only the approved mutation set.
6. Read back actual state; never trust command success alone.
7. Run health/postcondition checks.
8. For long work, launch deterministic observer plus independent checkpoint/final sentinel.
9. On first hard-gate failure: stop, preserve evidence, restore exact pre-state when safe, verify rollback, classify HOLD/FAIL/ABORT.
10. Send immediate owner-visible terminal closeout.
11. Update docs, memory, lessons learned and hydrator.
12. Commit only sanitized allowlisted artifacts after terminal; push only with explicit authorization.
13. Do not auto-start the next milestone.

---

## 12. Recommended immediate action

The first milestone is **M24 resumption/terminal PASS followed by Ledger M25 final completion/freeze PASS**. Do not start Milestone 2 code or schema work after M24 alone. Continue the existing observer through T+8, the natural 06:00 AEST presentation boundary, T+24 and final readback; close and preserve M24; then run the separate closure-only M25 milestone with its own STARTED notice, gates, evidence and terminal.

Only M25 PASS formally finishes Ledger v0.1 and creates the clean handoff to the new LLD. The durable-memory design, this LLD, lessons learned, and hydration script preserve the work until that boundary closes.

## Integration and recommended build order

# Durable Memory ↔ Ledger ↔ UMC/Broker Integration and Build Order

Status: **design recommendation only; no runtime integration authorized**
Immediate boundary: finish the currently authorized Memory Ledger M24 observation with PASS, then complete a separate Ledger M25 final-completion/freeze PASS before starting an implementation milestone for this architecture or expanding UMC surfaces.

## 1. The capabilities fit together, but they have different jobs

### Memory Ledger — durable write model and continuity spine

Ledger provides scoped, hashed, versioned records and source references. It proves what was recorded, where it came from, what scope it belongs to, and whether it changed.

Ledger should remain:

- local-first and inspectable;
- non-authoritative by default;
- operator-controlled for writes and promotion;
- read-only during recall;
- free of automatic prompt injection and recall-time writes.

The durable-memory architecture can extend the Ledger data model only after v0.1 is formally frozen by M25 PASS, and must not mutate the active v0.1 schema during M24 or closure-only M25. A later version can add source, entity, atomic-claim, relation, supersession, contradiction, and continuity-manifest record types.

### Source registry — authority resolver

The source registry maps stable source GUIDs to canonical files/records, versions, hashes, privacy classes, permitted claim types, and exact readback methods.

It answers: **Where must this claim be verified?**

Registry metadata may be represented as Ledger records later, but the canonical source remains outside the registry.

### Knowledge graph — derived read model

The graph projects Ledger/source-registry records into entities, atomic claims, typed relationships, negative relationships, event ordering, and provenance paths.

It answers: **What is related, what is missing, and which path should retrieval follow?**

The graph is rebuildable and non-authoritative. It must never become the only copy of a claim or source pointer.

### Vector/FTS indexes — disposable discovery accelerators

Lexical and vector indexes generate candidate nodes and sources. They can be rebuilt from approved registry/claim cards and sanitized excerpts.

They answer: **What might be relevant?**

They cannot answer: **What is true?**

### Runtime Service Broker — capability and authority control plane

The Runtime Service Broker should expose memory/source reconstruction as a typed, read-only runtime service. It owns:

- service discovery and health;
- scoped capability grants;
- privacy/surface policy;
- time, hop, and token budgets;
- cancellation and timeout behavior;
- deterministic service receipts;
- denial/fail-closed results;
- postcondition evidence.

It answers: **May this turn use this service, with what scope and limits, and what happened?**

### Universal Model Contract — turn-level execution contract

UMC wraps the turn with a contract envelope, canonical tool/service authority, proposed action supervision, receipts, postcondition verification, and deterministic closeout semantics.

For memory retrieval, UMC should receive a typed `ContextReconstructionReceipt`; it should not trust free-form model claims that memory was searched or a source was verified.

It answers: **What did this turn require, what was authorized, what evidence was produced, and may the response claim success?**

### Surface Service Broker — channel-specific boundary

The Surface Service Broker maps Telegram, Web, group, voice, XR, or future clients to surface capabilities and privacy rules. It controls:

- identity/session scope;
- allowed memory domains;
- whether retrieved private material may be rendered;
- approval UX;
- delivery formatting, deduplication, and receipts;
- surface-specific redaction and response limits.

It answers: **What may be requested and shown on this surface?**

It should call the Runtime Service Broker rather than implementing memory retrieval independently.

### Context Bridge — operational projection

Context Bridge remains a sanitized operational dashboard/projection of milestones, actions, and status. It may display bounded service state or receipt hashes later, but must not become the raw memory store or receive raw reconstruction packets.

It answers: **What is active and what operational state should the operator see?**

## 2. Recommended service contract

A future read-only memory service boundary should look approximately like:

```text
ContextReconstructionRequest
- request_id
- surface/session scope
- query
- resolved or candidate entity GUIDs
- required context slots
- allowed source domains/privacy classes
- freshness requirement
- hop/token/time budgets
- consequential-answer policy

ContextReconstructionPacket
- resolved entities
- ranked GUID paths
- atomic claim candidates
- exact source/version/span pointers
- verified source excerpts
- contradictions and rejected alternatives
- missing slots and omission ledger
- authority/freshness/privacy labels
- coverage score

ContextReconstructionReceipt
- request_id
- policy decision
- service/version/hash
- sources opened and hashes verified
- graph paths traversed
- gates passed/failed
- postcondition evidence
- terminal status: PASS | HOLD | FAIL
- no-write sentinel result
```

The packet is data for response construction. The receipt is runtime proof. Neither automatically writes memory or promotes authority.

## 3. Why durable memory is a good first broker service

After Ledger v0.1 is complete, read-only context reconstruction is a strong first Runtime Service Broker integration because it:

- exercises capability grants without external sends;
- has deterministic source/hash postconditions;
- can run in shadow mode;
- naturally produces PASS/HOLD receipts;
- tests privacy, surface scope, and cancellation;
- exposes prose-success failures cleanly;
- can be rolled back by disabling one service route;
- does not require broad model or surface promotion.

It is safer than using an external-write tool as the broker’s first new service.

## 4. Recommended build order

### Stage 0 — Close M24, then finish/freeze Ledger v0.1 at M25

1. Complete M24 through its natural boundary and T+24 terminal classification.
2. Generate the sanitized M24 closeout, gates, privacy scan, manifest, rehydrator update, and local terminal commit.
3. Require M24 PASS; M24 HOLD/ABORT blocks M25 and all new-LLD work.
4. Start a separate closure-only Ledger M25 milestone with its own STARTED notice, gates, health checks and artifacts.
5. Reconcile the complete v0.1 history, protected state, branch/head/preservation map, contracts, authority boundaries, rollback/read-only posture and final rehydrator.
6. Close M25 PASS and freeze the accepted v0.1 schemas/contracts; no feature/runtime/schema/route/surface mutation is permitted in M25.
7. Push M24/M25 only if separately authorized, or explicitly record the accepted local-only preservation boundary.

Do not start durable-memory runtime integration, contract-alignment implementation or new UMC surface expansion before M25 PASS.

### Stage 1 — Contract alignment, no runtime integration

Define together:

- source/entity/claim/relation/continuity schemas;
- `ContextReconstructionRequest/Packet/Receipt`;
- authority, privacy, freshness, contradiction, and unit gates;
- Runtime Service Broker service/grant/receipt contracts;
- UMC envelope fields for service-required turns;
- Surface Service Broker privacy/capability matrix;
- mutation and no-write sentinels.

This avoids building a memory engine that later requires a one-off broker adapter.

### Stage 2 — Offline durable-memory core

Implement outside the live runtime:

1. allowlisted source registry and deterministic resolver;
2. atomic claim/entity/unit schemas;
3. GUID and source-span identity rules;
4. contradiction/supersession/freshness checks;
5. compaction-gap fixtures, beginning with Altoura;
6. hydration and reconstruction packets;
7. privacy/injection scans.

No prompt injection, automatic recall, config mutation, or surface exposure.

### Stage 3 — Graph/vector reconstruction in shadow mode

Build:

- graph projection from registry/claim records;
- lexical/vector candidate indexes;
- query-conditioned GUID attention traversal;
- coverage and omission ledger;
- deterministic source readback;
- replayable retrieval traces.

Compare results with current memory search, but do not change live answers.

### Stage 4 — Minimal Runtime Service Broker path

Implement one complete no-send path:

```text
UMC ContractEnvelope
-> Runtime Service Broker grant
-> read-only Context Reconstruction service
-> ContextReconstructionReceipt
-> UMC postcondition verifier
-> response assembler in shadow/no-render mode
```

Start with mock fixtures, then local canonical files. Require no-write proof and deterministic HOLD when source/unit/authority is missing.

### Stage 5 — Owner-direct commercial/pricing canary

Use the already-narrow owner-direct UMC surface only after Stage 4 passes:

- authoritative-source readback required;
- no external sends beyond the normal response boundary;
- no group/Web/XR expansion;
- no memory writes;
- immediate off-switch;
- bounded observation and rollback.

### Stage 6 — Surface Service Broker and domain expansion

After the memory service and Runtime Service Broker are proven:

1. introduce the Surface Service Broker capability/privacy matrix;
2. expand one surface or domain at a time;
3. add CRM/opportunities, projects/decisions, configuration, and other consequential domains only with fixtures;
4. keep external-write services behind separate grants and stronger approvals.

## 5. Dependency summary

```text
M24 PASS
        |
        v
Ledger M25 final completion/freeze PASS
        |
        v
Frozen source/authority/read-only contracts
        |
        +-----------------------------+
        |                             |
        v                             v
Durable-memory core          Broker/UMC contract schemas
        |                             |
        +-------------+---------------+
                      v
           Read-only Runtime Service Broker canary
                      |
                      v
             Owner-direct UMC integration
                      |
                      v
             Surface Service Broker expansion
```

The core and broker schemas can be designed together after Ledger freezes. The core implementation should precede live broker integration. Runtime broker integration should precede broad surface expansion.

## 6. Non-negotiable boundaries

- Ledger/registry/source records are the durable write model; graph/vector indexes are rebuildable projections.
- No model prose, compacted summary, vector score, or graph traversal grants authority.
- No recall-time writes or automatic authority promotion.
- No raw reconstruction packet in Context Bridge or tracked evidence.
- UMC must verify service receipts before claiming source verification.
- Surface policy can narrow access but cannot broaden source authority.
- Every consequential claim must resolve to a canonical, versioned source span.
- Missing source, unit, permission, freshness, or contradiction resolution produces HOLD/clarification.
- New surfaces are never implemented as one-off memory patches; they pass through the Surface and Runtime Service Brokers.

## 7. Immediate recommendation

Finish M24 PASS, then formally finish/freeze Ledger v0.1 through a separate M25 PASS. Preserve this architecture through the standalone hydration script and proposal. Only after M25 terminal PASS, begin the **design-only contract-alignment milestone**, then build the offline source registry/resolver and Altoura compaction fixture. Treat the read-only context reconstruction service as the first low-risk service used to prove the Runtime Service Broker before any broad UMC surface expansion.

## Draft compaction-gap recovery proposal

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

## Systemic lesson learned

# Lessons learned — Durable Memory / Ledger / Contract / Surface Broker systemic build order

Date: 2026-07-17

## Core lesson

Do not build durable memory, graph retrieval, runtime contracts, and new surfaces as separate one-off patches. They form one system, but each component must retain a narrow responsibility and authority boundary.

## Durable separation of concerns

- **Ledger is the durable write model and continuity spine.** It stores scoped, hashed, versioned records and source references; it is non-authoritative by default and read-only during recall.
- **The source registry resolves authority.** It maps stable source GUIDs to canonical locations, versions, hashes, privacy classes, permitted claim types, and exact readback methods.
- **The graph is a rebuildable read projection.** It organizes entities, claims, provenance, contradiction, supersession and forward context paths; it is not the canonical store.
- **FTS/vector indexes are disposable discovery accelerators.** Similarity generates candidates and never grants authority.
- **The Runtime Service Broker controls capability use.** It issues scoped grants, applies budgets, enforces timeout/cancellation, blocks bypass, and emits deterministic receipts.
- **UMC controls turn truthfulness.** It prevents the model from claiming source/tool/delivery success without verified receipts and postconditions.
- **The Surface Service Broker controls channel disclosure and delivery.** It applies identity/session, privacy, approval, render/redaction, and deduplication policy; it may narrow but never widen runtime grants or source authority.
- **Context Bridge remains a sanitized operational projection.** Never store raw reconstruction packets or private excerpts there.

## Ordering rule

Build in this order:

1. close M24 PASS, then run a separate Ledger M25 final-completion/freeze PASS;
2. align data/service/UMC/surface contracts without runtime mutation;
3. build the source registry, deterministic resolver and atomic record core offline;
4. build graph/vector reconstruction in shadow mode;
5. prove one complete read-only Runtime Service Broker path;
6. run a narrow owner-direct commercial/pricing canary;
7. build the Surface Service Broker and expand one surface/domain cell at a time.

Contract design can be coordinated across components after the Ledger freeze, but implementation remains **core before runtime integration, Runtime Broker before Surface Broker expansion**.

## Why M24 then M25 come first

M24 is already running and establishes the terminal production-presentation/continuity observation baseline. Starting new Ledger schemas, runtime hydration, memory routes, UMC surfaces or broker code before M24 closes would contaminate its observation invariants and make the final classification ambiguous.

M24 PASS is necessary but no longer the formal Ledger finish line. After M24 is preserved, run a separate closure-only M25 with its own STARTED notice, gates, evidence, rehydrator and terminal. M25 reconciles the full v0.1 history, declares the schema/contracts/authority boundaries frozen, records the preservation disposition, and closes PASS without new feature/runtime/schema/route/surface mutation. Only M25 PASS creates the clean handoff to the new LLD.

## Best first broker capability

Read-only context reconstruction is a safer first RSB service than an external-write tool because it can run no-send/shadow, has deterministic source/hash postconditions, naturally returns PASS/HOLD, exercises privacy and cancellation, and can be disabled by removing one service route. It must retain no-write and no-authority-promotion proof.

## Health and evidence are part of the architecture

A milestone is not complete because code exists. Require:

- liveness, readiness, dependency and contract-hash checks;
- source/registry/Ledger/graph/index freshness and parity;
- read-only mutation sentinels;
- privacy/injection scans;
- receipt and bypass tests;
- rollback/off-switch proof;
- deterministic long-observer ownership and independent terminal sentinels for soaks;
- sanitized evidence manifests and hydrator updates;
- explicit owner-visible STARTED and PASS/HOLD/FAIL/ABORT closeouts.

## Authority rule

Compaction summaries, model prose, graph paths, vector scores and session recollections are navigation aids. Every consequential claim must resolve to a permitted, current, canonical source version/span. Missing source, unit, permission, freshness, or contradiction resolution produces HOLD/clarification rather than a plausible guess.

## Surface expansion rule

Never add future Telegram/Web/group/voice/XR/business-domain memory behavior as a direct patch. Route it through SSB -> UMC -> RSB -> typed service. Expand one reviewed surface/domain matrix cell at a time with its own apply, off-switch, rollback, observer, evidence, and terminal.

## Ledger project rehydrator snapshot

# Stickbot Memory Ledger v0.1 — Project Rehydrator

**Status:** `MEMORY_LEDGER_V0_1_M23B_SANITIZED_PRESENTATION_DEFAULT_SWITCH_PASS_ROLLBACK_READY_NO_AUTHORITY_PROMOTION`

**Branch:** `evidence/stickbot-memory-ledger-v0-1-m23b-sanitized-presentation-default-switch-20260717`

**Accepted baseline:** `65d34a6095e4f81f2139c91d80abce3308a9b756`

**Project root:** `projects/stickbot-memory-ledger-v0/`

## Immediate resume

1. Work only in `/tmp/context-bridge-ledger-v0-1-completion-20260717`.
2. Read, in order:
   - `docs/M23B_SANITIZED_PRESENTATION_DEFAULT_SWITCH_CONTROLLED_ENABLEMENT.md`
   - `artifacts/memory-ledger/m23b-sanitized-presentation-default-switch/M23B_CLOSEOUT.json`
   - `docs/M23A_PRODUCTION_PRESENTATION_CALLER_BINDING_NO_DEFAULT_SWITCH.md`
   - `docs/M22_SANITIZED_PRESENTATION_DEFAULT_SWITCH_RELEASE_CANDIDATE.md`
   - `docs/MILESTONES.md`
   - `docs/TROUBLESHOOTING_REPAIR_AND_IMPLEMENTATION_GUIDE.md`
   - `artifacts/m23b_sanitized_presentation_default_switch_prompt_intake/NOTEBOOK.md`
3. Generate/read the executable packet:

   ```bash
   node projects/stickbot-memory-ledger-v0/scripts/stickbot-memory-ledger-rehydrate.mjs --status
   ```

4. Read `artifacts/rehydration/stickbot-memory-ledger/latest.md`.

## Preserved history

- M19 controlled operator-only read-only recall: PASS.
- Original M20 detached observer: `HOLD`; never upgrade it to PASS.
- M20R deterministic recovery: PASS.
- M21 steady-state/readiness: PASS and remotely preserved.
- Context Bridge CB-L0–CB-L13P: complete and remotely preserved.
- M22 sanitized presentation release candidate: PASS and remotely preserved.
- M23 caller-not-proven investigation: BLOCKED, no accepted switch closeout.
- M23A production caller binding/no default switch: 20/20 PASS and remotely preserved at `65d34a6095e4f81f2139c91d80abce3308a9b756`.

## M23B — controlled production default switch

`MEMORY_LEDGER_V0_1_M23B_SANITIZED_PRESENTATION_DEFAULT_SWITCH_PASS_ROLLBACK_READY_NO_AUTHORITY_PROMOTION`

- M23B_G1–M23B_G25 PASS.
- Final presentation mode: explicit `sanitized`.
- Scope: proven daily Context Bridge reconcile caller only.
- Binding: deployed exact copy of `scripts/context_bridge_presentation_binding.py`.
- Selector persistence: inside the proven caller command only.
- Existing cron announce is the sole delivery boundary; the binding is no-send and the caller does not have the message tool.
- Live rollback sequence: sanitized readback -> legacy readback -> exact legacy no-send invocation -> sanitized restore/readback.
- No M23B cron run or Telegram verification send.
- No Context Bridge events/actions, Ledger, OpenClaw config, model/provider/fallback/Telegram/memory-route, authority, automatic-recall, or recall-time-write mutation.
- No Gateway restart.
- Local commit only; no push without separate owner authorization.

Evidence:

`artifacts/memory-ledger/m23b-sanitized-presentation-default-switch/`

Runtime-local evidence remains untracked:

`state/stickbot-memory-ledger/m23b-sanitized-presentation-default-switch/`

## Production caller contract

- Job: daily Context Bridge reconcile caller.
- Schedule: daily 06:00 Australia/Sydney.
- Session target: isolated.
- Model: `openai-codex/gpt-5.5`; no fallbacks.
- Tools: `read`, `write`, `exec`.
- Final command uses `CONTEXT_BRIDGE_LEDGER_PRESENTATION_MODE=sanitized` and mandatory `--no-send`.
- Final response must equal binding stdout.
- Delivery remains existing cron announce.

## Protected state

- Events: `4d3966717a5cfe92ba7ae6cc179aea45a7e46a7a453ce1d986a984c82a7549e5`.
- Actions: `a7b0d3d4bd1a9c8bb0da20a1f92cc248f3f37dbf551c66a361330076777bba63`.
- Ledger: `f50ff3836724358d2ef99d92d7c32c2c07651138a749e2a03ce5c03c512807f6`, 19 records / 20 events.
- OpenClaw config: `a4f0aac75704eb7d171e528c0486fd8baa95260450d38653aea5ba3226e2d859`.

All matched before/after M23B.

## Immediate rollback

Change only the caller-local literal from:

```text
CONTEXT_BRIDGE_LEDGER_PRESENTATION_MODE=sanitized
```

to:

```text
CONTEXT_BRIDGE_LEDGER_PRESENTATION_MODE=legacy
```

Read back the caller and run the deployed binding with explicit legacy plus `--no-send`. Leave legacy selected if any check fails. No Gateway restart is required. Missing/unknown selector values still fail safely to legacy.

## Current boundary

Exactly one next target is proposed:

`M24 — Sanitized Presentation Default Switch Observation / Soak`

Status: `PROPOSED_NOT_STARTED`.

M24 must not begin without separate owner authorization.

## Validation before M23B local commit

```bash
python3 projects/stickbot-memory-ledger-v0/test/test_context_bridge_presentation_binding.py
node projects/stickbot-memory-ledger-v0/scripts/stickbot-memory-ledger-rehydrate.mjs --status
node --check projects/stickbot-memory-ledger-v0/scripts/stickbot-memory-ledger-rehydrate.mjs
git diff --check -- .
git status --short --branch
```

Also require current caller sanitized readback, source/deployed binding hash parity, rollback proof, final sanitized no-send/private scan, unchanged latest cron run, protected-state parity, JSON/manifest validation, committed private/raw scan, explicit non-UNKNOWN closeout, and 25/25 gates.

Never stage `state/`, DB/WAL/SHM, raw Bridge/recall/memory dumps, credentials, telemetry, pycache/pyc, temporary files, raw cron/runtime configuration, or unrelated changes.

## Source inventory

- `systemic_lld` — `/home/stickai/.openclaw/workspace/projects/durable-memory-architecture/DURABLE_MEMORY_LEDGER_CONTEXT_CONTRACT_SURFACE_BROKER_LLD_AND_IMPLEMENTATION_PLAN.md` — 58539 bytes — sha256:`beb248ec6efdbbe77915a5b1adfa3774661285c32796ff5c5c8acf1bfc7cee61` — design_only_non_authoritative
- `proposal` — `/home/stickai/.openclaw/workspace/projects/durable-memory-architecture/COMPACTION_GAP_RECOVERY_PROPOSAL.md` — 16299 bytes — sha256:`91d81c0b58addf99e7543007c43ce305df767ee948a4e3c23ca7ee5dca47cc43` — design_only_non_authoritative
- `integration_order` — `/home/stickai/.openclaw/workspace/projects/durable-memory-architecture/LEDGER_BROKER_INTEGRATION_AND_BUILD_ORDER.md` — 11935 bytes — sha256:`1c49f34526c9d360d441108257541c6ab8a96b86dd880018bd5ff6a7c8e2dc3d` — design_only_non_authoritative
- `systemic_lesson` — `/home/stickai/.openclaw/workspace/memory/lessons-learned-durable-memory-ledger-contract-surface-broker-systemic-build-order-2026-07-17.md` — 4873 bytes — sha256:`b7300eb8945b701ad10cea9bd89ed618058fa0d80465fcbc8d9a4be8119e7ca9` — lesson_non_authoritative_navigation
- `ledger_rehydrator` — `/tmp/context-bridge-ledger-v0-1-completion-20260717/projects/stickbot-memory-ledger-v0/docs/PROJECT_REHYDRATOR.md` — 5341 bytes — sha256:`6bfb5fdab48d2dd6d42fe82053549e8079fe6fc553404531182b7ef3ed42be80` — tracked_navigation_snapshot_verify_live_state
- `ledger_latest` — `/tmp/context-bridge-ledger-v0-1-completion-20260717/projects/stickbot-memory-ledger-v0/artifacts/rehydration/stickbot-memory-ledger/latest.json` — 27948 bytes — sha256:`5427f992e5db3a4de50d92b96b579396b32f524efb2e68cfee7145190ea54fa9` — tracked_navigation_snapshot_verify_live_state
- `m24_live_status` — `/tmp/context-bridge-ledger-v0-1-completion-20260717/state/stickbot-memory-ledger/m24-sanitized-presentation-default-switch-observation/m24-observation-20260717T1925AEST/status.json` — 367 bytes — sha256:`8d0712ad31602d363dfef4cb74bf4a52c2be6fe5ae781540cc788739f652c192` — runtime_observation_snapshot_not_terminal_authority

## Warnings

- None

## Errors

- None
