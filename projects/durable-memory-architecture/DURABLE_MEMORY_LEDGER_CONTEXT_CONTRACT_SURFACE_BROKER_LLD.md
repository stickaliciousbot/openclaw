# Durable Memory Ledger / Context / Contract / Surface Broker
## Low-Level Design and Systemic Implementation Plan

**Document status:** owner-ready implementation plan; design only; no runtime apply  
**Plan version:** `v1.0`  
**Initial milestone:** resume and close `M24 — Sanitized Presentation Default Switch Observation / Soak`  
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
| 1 | Resume M24; close/freeze Ledger v0.1 | observation only | natural existing announce only | terminal M24 evidence and frozen v0.1 |
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

# Milestone 1 — Resume M24 and freeze Memory Ledger v0.1

**Purpose:** complete the already-running M24 observation correctly and preserve the final Ledger v0.1 baseline before new architecture work.

**Entry state:** M24 `RUNNING`, T+2 reached, observer alive, sentinel and T+2 run history successful, no failed gates.

### Submilestone 1A — M24 semantic terminal

Continue observation through T+8, the natural boundary, T+24 and independent final readback. A presentation-soak PASS does not itself freeze Ledger schemas/contracts.

### Submilestone 1B — v0.1 freeze/preservation

Only after 1A has a durable PASS or explicit evidenced no-boundary HOLD: resolve canonical worktree/branch/head; require clean allowlisted Git state; build sanitized evidence, privacy scan, mutation sentinels, rollback proof and updated rehydrator; create the local terminal commit. No schema or runtime mutation occurs in the freeze.

### Tasks

1. Rehydrate from M24 canonical status, registry, run ledger, job definitions, and project rehydrator.
2. Verify observer PID/start-time anchor, registry ownership, harness health, sentinel durable history, and T+2 artifact.
3. Continue observation without manual production cron invocation or manual Telegram send.
4. Capture T+8.
5. Observe the natural 06:00 AEST production boundary.
6. Require exactly one expected sanitized announce and no duplicate/unexpected delivery for PASS.
7. Continue through T+24 and final independent readback.
8. Classify PASS, explicit no-boundary HOLD, or ABORT.
9. Generate sanitized closeout, hard gates, privacy scan, source map, mutation sentinels, evidence manifest, docs, milestones, troubleshooting update, and rehydrator.
10. Commit locally only after terminal classification; push only with separate authorization.

### M1 hard gates

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
- M1-G21 no M25/new architecture implementation started;
- M1-G22 final evidence manifest hashes all closeout artifacts;
- M1-G23 independent terminal readback agrees with semantic observer; missing/ambiguous sentinel or process-only exit classifies HOLD, never PASS;
- M1-G24 recurring sentinel removed only after durable terminal;
- M1-G25 Submilestone 1B verifies exact canonical worktree/branch/head, clean allowlisted Git state, evidence/rehydrator parity and local commit only after all applicable gates and terminal classification.

### M1 health checks

Observer process/registry; checkpoint freshness; cron sentinel history; production caller/run ledger; delivery count; protected hashes; rollback readback; privacy scan; Git allowlist; rehydrator strict run.

### M1 terminals

- `MEMORY_LEDGER_V0_1_M24_SANITIZED_PRESENTATION_DEFAULT_SWITCH_OBSERVATION_PASS_NO_AUTHORITY_PROMOTION`
- `MEMORY_LEDGER_V0_1_M24_HOLD_NO_SCHEDULED_PRESENTATION_BOUNDARY_OBSERVED`
- `MEMORY_LEDGER_V0_1_M24_ABORT_<FIRST_HARD_GATE_FAILURE>`

### M1 expected closeout artifacts

Under the M24 tracked evidence root: preflight/current-state, checkpoint summary, natural-boundary proof, delivery classification, mutation sentinels, privacy scan, hard gates, closeout JSON, summary Markdown, evidence manifest, rehydrator update, milestone/troubleshooting updates.

**Successor boundary:** stop and request owner authorization for Milestone 2.

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

The first milestone is **M24 resumption and Ledger v0.1 freeze**. Do not start Milestone 2 code or schema work while M24 is running. Continue the existing observer through T+8, the natural 06:00 AEST presentation boundary, T+24 and final readback; then close, document, rehydrate, commit locally, and stop for owner review.

The durable-memory design, this LLD, lessons learned, and hydration script preserve the work until that boundary closes.
