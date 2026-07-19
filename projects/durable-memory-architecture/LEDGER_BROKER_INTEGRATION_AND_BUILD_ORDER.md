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
