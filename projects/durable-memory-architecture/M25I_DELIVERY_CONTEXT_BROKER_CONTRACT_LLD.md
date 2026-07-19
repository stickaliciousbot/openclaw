# M25I Delivery Context Broker Contract LLD

Status: design baseline; no runtime apply. Terminal target: `M25I_A_ARCHITECTURE_BASELINE_IMPLEMENTATION_READINESS_PASS_NO_APPLY`.

## Scope and non-goals

M25I-A freezes an architecture baseline after the M25H pushed BLOCKED closeout. It does not start M25J/M26, does not arm the boundary handler, does not create or run jobs, does not send Telegram, and does not mutate Ledger, Context Bridge, Gateway config, model/provider/fallback/memory routes, runtime reconstruction, RSB, or SSB.

## Design authority inputs

- Owner supplied LLD copied unchanged to `projects/durable-memory-architecture/DURABLE_MEMORY_LEDGER_CONTEXT_CONTRACT_SURFACE_BROKER_LLD.md`; SHA-256 `edd7284f2f591517b3536300ba476ab9b06abd0d01a02ec3b1500cc748f66de1`.
- Compaction-gap hydration strict status PASS with seven bounded sources and zero warnings/errors at baseline.
- M25H accepted-pushed state represented by branch `evidence/umc-m3n-post-restart-health-failclosed-20260713` at `6c62cf22dddbe828de523d3eb823908b5cb599b3` with terminal `M25H_PUSHED_BLOCKED_REPAIRED_DELIVERY_STILL_NO_REPLY`.

## Responsibility boundaries

| Component | Responsibility | Authority/input | Output | Failure | Health | Rollback | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Memory Ledger | Durable, scoped, hashed continuity and source-reference spine | Canonical owner-approved source refs and Ledger records | Ledger record/manifest/status receipts | fail closed to read-only v0.1 baseline; no recall-time write | ledger integrity/no-write/hash-stability check | feature flag/sidecar disabled; v0.1 frozen read-only | source refs, hashes, record manifests, mutation sentinels |
| Source Registry | Maps stable source GUIDs to canonical source versions/spans/hash/privacy/readback policy | Owner-approved source manifests and exact source readback | SourceResolutionResult with version/span/hash | unresolvable or stale source => HOLD/deny | registry integrity/source resolution smoke | use prior accepted manifest | resolution manifests and pre/post source hashes |
| Forward Context Reconstruction Graph | Rebuildable projection of entities/claims/relations for query planning | Registry/Ledger/source claim cards | query paths, watermarks, coverage/omission ledger | stale/unavailable graph degrades to source registry direct lookup or HOLD | graph parity/watermark/stale check | discard/rebuild projection | projection receipt and graph build manifest |
| FTS/vector indexes | Candidate discovery accelerators | Sanitized excerpts/claim cards | ranked candidates only | index stale => discovery disabled; never truth authority | index freshness/parity smoke | drop/rebuild index | candidate list with authority=false |
| Context Reconstruction Service | Read-only request-to-packet service with exact source verification | RSB grant + request + Registry/Ledger/source readback | ContextReconstructionPacket and Receipt | missing coverage/contradiction => HOLD or degraded packet | reconstruction smoke/receipt/no-write | disable service route | request/packet/receipt/source hashes |
| Runtime Service Broker | Capability grants, budgets, service invocation, health, cancellation, receipts | UMC/SSB grant request, service definitions, health | grant/denial/invocation/receipt/postcondition evidence | deny wrong scope/expired grant/unhealthy service | live/readiness/grant roundtrip/timeout cancel | unregister/disable route | grant and receipt chain |
| UMC | Turn envelope, postconditions, receipt verification, prose-success prevention | job/turn envelope, receipts, service grants, boundary/delivery outcomes | verified closeout terminal or HOLD/ABORT | receipt missing/mismatch => HOLD/REJECT prose success | fixtures: required actions, postconditions, HOLD rendering | accepted current baseline adapter | ContractEnvelope and postcondition receipts |
| Surface Service Broker | Identity/session/privacy/render/delivery policy intersection | identity/session/surface policy, RSB grant, sanitized payload | SurfacePolicy, render profile, delivery decision/result binding | wrong surface/session/policy epoch => deny | policy intersection/render/dedupe/cross-surface denial | previous accepted surface path | surface policy and delivery receipts |
| Delivery Adapter | Actual external delivery attempt after SSB+boundary allow | SanitizedPayloadEnvelope + DeliveryRequiredJobEnvelope + boundary allow | DeliveryResultEnvelope | failure captured, never prose success without receipt | adapter dry-run/canary/result health | off-switch and pending-send check | message result metadata, dedupe key, adapter response class |
| Context Bridge | Sanitized operational projection only | sanitized terminal categories/counts/keyed aliases | projection records, no raw packets | projection missing => dashboard stale, not source loss | projection sanitizer and parity check | existing sanitized presentation only | projection diff and privacy scan |
| Hydrator/Rehydrator | Bounded non-authoritative resume/navigation packets | allowlisted docs/evidence manifests | bounded md/json packets with source inventory | strict status FAIL/HOLD; never authority | strict source hash/private scan | delete/regenerate packet | source inventory and mutation checks |
| Boundary Handler | Final in-process gate for delivery-required proof payloads | job/run/session envelope, prepared payload, SSB policy, boundary contract | BoundaryDecisionEnvelope and message gate receipt | hold/reject => no delivery; missing correlation => HOLD | dormant/unarmed check; exact-scope fixture | armed=false; config disabled | decision receipts and disarm proof |

## Forbidden responsibility summary

- Memory Ledger and Source Registry must not render/send surface prose or become recall-time writers.
- Graph/FTS/vector must not decide truth or authority.
- Context Reconstruction Service must not write Ledger/Bridge or bypass RSB grants.
- RSB must not broaden surface disclosure or create source authority.
- UMC must not trust model prose for source/tool/delivery/postcondition success without receipts.
- SSB must narrow only; it must not grant source authority or broaden runtime capabilities.
- Delivery Adapter must not render private material or send without boundary+SSB allow.
- Context Bridge must not receive raw packets, raw identifiers, or authority promotion.
- Hydrators must not inject prompts, start work, or update canonical state.
- Boundary Handler must not remain armed outside exact proof windows.

## Authority hierarchy

1. owner-approved canonical source or authoritative live record
2. source registry exact version/span/hash
3. Ledger atomic source-reference/claim/event record
4. graph/reconstruction projection
5. FTS/vector candidate
6. session memory, compacted summary, model prose or hot context

No lower tier may promote itself. Graph, vector, summary, hot context and model prose are navigation only until exact source readback and receipt verification succeed.

## Contract schemas

### 1. SourceRecord

- **schema_id:** `stickbot.m25i.sourcerecord.v1`
- **semantic version:** `1.0.0-draft`; unknown major fails closed; unknown minor ignored only when extension policy allows.
- **canonical serialization:** UTF-8 JSON, sorted keys, no insignificant whitespace for hash preimage.
- **contract hash:** `sha256(canonical_schema_json)`; computed in M25J, not embedded here as self-reference.
- **required fields:** `schema_id`, `schema_version`, `request_id` or component-native ID, `policy_epoch`, `created_utc`, `source_refs`, `authority_tier`, `privacy_class`, `surface_scope`, `session_scope`, `idempotency_key` when effectful, `receipt_binding` when a receipt.
- **optional fields:** `extensions`, `diagnostics`, `redactions`, `budget`, `watermark`, `parent_receipt_id`, `human_note`.
- **extension policy:** `x_*` namespaced extensions allowed for same major only; mandatory unknown extension is a hard failure.
- **binding/replay:** receipts bind exact request/grant/session/surface/policy epoch and canonical payload hash; stale epoch, duplicate idempotency key, forged parent, or cross-surface replay denies.

### 2. SourceResolutionResult

- **schema_id:** `stickbot.m25i.sourceresolutionresult.v1`
- **semantic version:** `1.0.0-draft`; unknown major fails closed; unknown minor ignored only when extension policy allows.
- **canonical serialization:** UTF-8 JSON, sorted keys, no insignificant whitespace for hash preimage.
- **contract hash:** `sha256(canonical_schema_json)`; computed in M25J, not embedded here as self-reference.
- **required fields:** `schema_id`, `schema_version`, `request_id` or component-native ID, `policy_epoch`, `created_utc`, `source_refs`, `authority_tier`, `privacy_class`, `surface_scope`, `session_scope`, `idempotency_key` when effectful, `receipt_binding` when a receipt.
- **optional fields:** `extensions`, `diagnostics`, `redactions`, `budget`, `watermark`, `parent_receipt_id`, `human_note`.
- **extension policy:** `x_*` namespaced extensions allowed for same major only; mandatory unknown extension is a hard failure.
- **binding/replay:** receipts bind exact request/grant/session/surface/policy epoch and canonical payload hash; stale epoch, duplicate idempotency key, forged parent, or cross-surface replay denies.

### 3. EntityRecord

- **schema_id:** `stickbot.m25i.entityrecord.v1`
- **semantic version:** `1.0.0-draft`; unknown major fails closed; unknown minor ignored only when extension policy allows.
- **canonical serialization:** UTF-8 JSON, sorted keys, no insignificant whitespace for hash preimage.
- **contract hash:** `sha256(canonical_schema_json)`; computed in M25J, not embedded here as self-reference.
- **required fields:** `schema_id`, `schema_version`, `request_id` or component-native ID, `policy_epoch`, `created_utc`, `source_refs`, `authority_tier`, `privacy_class`, `surface_scope`, `session_scope`, `idempotency_key` when effectful, `receipt_binding` when a receipt.
- **optional fields:** `extensions`, `diagnostics`, `redactions`, `budget`, `watermark`, `parent_receipt_id`, `human_note`.
- **extension policy:** `x_*` namespaced extensions allowed for same major only; mandatory unknown extension is a hard failure.
- **binding/replay:** receipts bind exact request/grant/session/surface/policy epoch and canonical payload hash; stale epoch, duplicate idempotency key, forged parent, or cross-surface replay denies.

### 4. ClaimRecord

- **schema_id:** `stickbot.m25i.claimrecord.v1`
- **semantic version:** `1.0.0-draft`; unknown major fails closed; unknown minor ignored only when extension policy allows.
- **canonical serialization:** UTF-8 JSON, sorted keys, no insignificant whitespace for hash preimage.
- **contract hash:** `sha256(canonical_schema_json)`; computed in M25J, not embedded here as self-reference.
- **required fields:** `schema_id`, `schema_version`, `request_id` or component-native ID, `policy_epoch`, `created_utc`, `source_refs`, `authority_tier`, `privacy_class`, `surface_scope`, `session_scope`, `idempotency_key` when effectful, `receipt_binding` when a receipt.
- **optional fields:** `extensions`, `diagnostics`, `redactions`, `budget`, `watermark`, `parent_receipt_id`, `human_note`.
- **extension policy:** `x_*` namespaced extensions allowed for same major only; mandatory unknown extension is a hard failure.
- **binding/replay:** receipts bind exact request/grant/session/surface/policy epoch and canonical payload hash; stale epoch, duplicate idempotency key, forged parent, or cross-surface replay denies.

### 5. RelationRecord

- **schema_id:** `stickbot.m25i.relationrecord.v1`
- **semantic version:** `1.0.0-draft`; unknown major fails closed; unknown minor ignored only when extension policy allows.
- **canonical serialization:** UTF-8 JSON, sorted keys, no insignificant whitespace for hash preimage.
- **contract hash:** `sha256(canonical_schema_json)`; computed in M25J, not embedded here as self-reference.
- **required fields:** `schema_id`, `schema_version`, `request_id` or component-native ID, `policy_epoch`, `created_utc`, `source_refs`, `authority_tier`, `privacy_class`, `surface_scope`, `session_scope`, `idempotency_key` when effectful, `receipt_binding` when a receipt.
- **optional fields:** `extensions`, `diagnostics`, `redactions`, `budget`, `watermark`, `parent_receipt_id`, `human_note`.
- **extension policy:** `x_*` namespaced extensions allowed for same major only; mandatory unknown extension is a hard failure.
- **binding/replay:** receipts bind exact request/grant/session/surface/policy epoch and canonical payload hash; stale epoch, duplicate idempotency key, forged parent, or cross-surface replay denies.

### 6. ContradictionRecord

- **schema_id:** `stickbot.m25i.contradictionrecord.v1`
- **semantic version:** `1.0.0-draft`; unknown major fails closed; unknown minor ignored only when extension policy allows.
- **canonical serialization:** UTF-8 JSON, sorted keys, no insignificant whitespace for hash preimage.
- **contract hash:** `sha256(canonical_schema_json)`; computed in M25J, not embedded here as self-reference.
- **required fields:** `schema_id`, `schema_version`, `request_id` or component-native ID, `policy_epoch`, `created_utc`, `source_refs`, `authority_tier`, `privacy_class`, `surface_scope`, `session_scope`, `idempotency_key` when effectful, `receipt_binding` when a receipt.
- **optional fields:** `extensions`, `diagnostics`, `redactions`, `budget`, `watermark`, `parent_receipt_id`, `human_note`.
- **extension policy:** `x_*` namespaced extensions allowed for same major only; mandatory unknown extension is a hard failure.
- **binding/replay:** receipts bind exact request/grant/session/surface/policy epoch and canonical payload hash; stale epoch, duplicate idempotency key, forged parent, or cross-surface replay denies.

### 7. SupersessionRecord

- **schema_id:** `stickbot.m25i.supersessionrecord.v1`
- **semantic version:** `1.0.0-draft`; unknown major fails closed; unknown minor ignored only when extension policy allows.
- **canonical serialization:** UTF-8 JSON, sorted keys, no insignificant whitespace for hash preimage.
- **contract hash:** `sha256(canonical_schema_json)`; computed in M25J, not embedded here as self-reference.
- **required fields:** `schema_id`, `schema_version`, `request_id` or component-native ID, `policy_epoch`, `created_utc`, `source_refs`, `authority_tier`, `privacy_class`, `surface_scope`, `session_scope`, `idempotency_key` when effectful, `receipt_binding` when a receipt.
- **optional fields:** `extensions`, `diagnostics`, `redactions`, `budget`, `watermark`, `parent_receipt_id`, `human_note`.
- **extension policy:** `x_*` namespaced extensions allowed for same major only; mandatory unknown extension is a hard failure.
- **binding/replay:** receipts bind exact request/grant/session/surface/policy epoch and canonical payload hash; stale epoch, duplicate idempotency key, forged parent, or cross-surface replay denies.

### 8. ContextReconstructionRequest

- **schema_id:** `stickbot.m25i.contextreconstructionrequest.v1`
- **semantic version:** `1.0.0-draft`; unknown major fails closed; unknown minor ignored only when extension policy allows.
- **canonical serialization:** UTF-8 JSON, sorted keys, no insignificant whitespace for hash preimage.
- **contract hash:** `sha256(canonical_schema_json)`; computed in M25J, not embedded here as self-reference.
- **required fields:** `schema_id`, `schema_version`, `request_id` or component-native ID, `policy_epoch`, `created_utc`, `source_refs`, `authority_tier`, `privacy_class`, `surface_scope`, `session_scope`, `idempotency_key` when effectful, `receipt_binding` when a receipt.
- **optional fields:** `extensions`, `diagnostics`, `redactions`, `budget`, `watermark`, `parent_receipt_id`, `human_note`.
- **extension policy:** `x_*` namespaced extensions allowed for same major only; mandatory unknown extension is a hard failure.
- **binding/replay:** receipts bind exact request/grant/session/surface/policy epoch and canonical payload hash; stale epoch, duplicate idempotency key, forged parent, or cross-surface replay denies.

### 9. ContextReconstructionPacket

- **schema_id:** `stickbot.m25i.contextreconstructionpacket.v1`
- **semantic version:** `1.0.0-draft`; unknown major fails closed; unknown minor ignored only when extension policy allows.
- **canonical serialization:** UTF-8 JSON, sorted keys, no insignificant whitespace for hash preimage.
- **contract hash:** `sha256(canonical_schema_json)`; computed in M25J, not embedded here as self-reference.
- **required fields:** `schema_id`, `schema_version`, `request_id` or component-native ID, `policy_epoch`, `created_utc`, `source_refs`, `authority_tier`, `privacy_class`, `surface_scope`, `session_scope`, `idempotency_key` when effectful, `receipt_binding` when a receipt.
- **optional fields:** `extensions`, `diagnostics`, `redactions`, `budget`, `watermark`, `parent_receipt_id`, `human_note`.
- **extension policy:** `x_*` namespaced extensions allowed for same major only; mandatory unknown extension is a hard failure.
- **binding/replay:** receipts bind exact request/grant/session/surface/policy epoch and canonical payload hash; stale epoch, duplicate idempotency key, forged parent, or cross-surface replay denies.

### 10. ContextReconstructionReceipt

- **schema_id:** `stickbot.m25i.contextreconstructionreceipt.v1`
- **semantic version:** `1.0.0-draft`; unknown major fails closed; unknown minor ignored only when extension policy allows.
- **canonical serialization:** UTF-8 JSON, sorted keys, no insignificant whitespace for hash preimage.
- **contract hash:** `sha256(canonical_schema_json)`; computed in M25J, not embedded here as self-reference.
- **required fields:** `schema_id`, `schema_version`, `request_id` or component-native ID, `policy_epoch`, `created_utc`, `source_refs`, `authority_tier`, `privacy_class`, `surface_scope`, `session_scope`, `idempotency_key` when effectful, `receipt_binding` when a receipt.
- **optional fields:** `extensions`, `diagnostics`, `redactions`, `budget`, `watermark`, `parent_receipt_id`, `human_note`.
- **extension policy:** `x_*` namespaced extensions allowed for same major only; mandatory unknown extension is a hard failure.
- **binding/replay:** receipts bind exact request/grant/session/surface/policy epoch and canonical payload hash; stale epoch, duplicate idempotency key, forged parent, or cross-surface replay denies.

### 11. ServiceDefinition

- **schema_id:** `stickbot.m25i.servicedefinition.v1`
- **semantic version:** `1.0.0-draft`; unknown major fails closed; unknown minor ignored only when extension policy allows.
- **canonical serialization:** UTF-8 JSON, sorted keys, no insignificant whitespace for hash preimage.
- **contract hash:** `sha256(canonical_schema_json)`; computed in M25J, not embedded here as self-reference.
- **required fields:** `schema_id`, `schema_version`, `request_id` or component-native ID, `policy_epoch`, `created_utc`, `source_refs`, `authority_tier`, `privacy_class`, `surface_scope`, `session_scope`, `idempotency_key` when effectful, `receipt_binding` when a receipt.
- **optional fields:** `extensions`, `diagnostics`, `redactions`, `budget`, `watermark`, `parent_receipt_id`, `human_note`.
- **extension policy:** `x_*` namespaced extensions allowed for same major only; mandatory unknown extension is a hard failure.
- **binding/replay:** receipts bind exact request/grant/session/surface/policy epoch and canonical payload hash; stale epoch, duplicate idempotency key, forged parent, or cross-surface replay denies.

### 12. ServiceHealth

- **schema_id:** `stickbot.m25i.servicehealth.v1`
- **semantic version:** `1.0.0-draft`; unknown major fails closed; unknown minor ignored only when extension policy allows.
- **canonical serialization:** UTF-8 JSON, sorted keys, no insignificant whitespace for hash preimage.
- **contract hash:** `sha256(canonical_schema_json)`; computed in M25J, not embedded here as self-reference.
- **required fields:** `schema_id`, `schema_version`, `request_id` or component-native ID, `policy_epoch`, `created_utc`, `source_refs`, `authority_tier`, `privacy_class`, `surface_scope`, `session_scope`, `idempotency_key` when effectful, `receipt_binding` when a receipt.
- **optional fields:** `extensions`, `diagnostics`, `redactions`, `budget`, `watermark`, `parent_receipt_id`, `human_note`.
- **extension policy:** `x_*` namespaced extensions allowed for same major only; mandatory unknown extension is a hard failure.
- **binding/replay:** receipts bind exact request/grant/session/surface/policy epoch and canonical payload hash; stale epoch, duplicate idempotency key, forged parent, or cross-surface replay denies.

### 13. ServiceGrantRequest

- **schema_id:** `stickbot.m25i.servicegrantrequest.v1`
- **semantic version:** `1.0.0-draft`; unknown major fails closed; unknown minor ignored only when extension policy allows.
- **canonical serialization:** UTF-8 JSON, sorted keys, no insignificant whitespace for hash preimage.
- **contract hash:** `sha256(canonical_schema_json)`; computed in M25J, not embedded here as self-reference.
- **required fields:** `schema_id`, `schema_version`, `request_id` or component-native ID, `policy_epoch`, `created_utc`, `source_refs`, `authority_tier`, `privacy_class`, `surface_scope`, `session_scope`, `idempotency_key` when effectful, `receipt_binding` when a receipt.
- **optional fields:** `extensions`, `diagnostics`, `redactions`, `budget`, `watermark`, `parent_receipt_id`, `human_note`.
- **extension policy:** `x_*` namespaced extensions allowed for same major only; mandatory unknown extension is a hard failure.
- **binding/replay:** receipts bind exact request/grant/session/surface/policy epoch and canonical payload hash; stale epoch, duplicate idempotency key, forged parent, or cross-surface replay denies.

### 14. ServiceAuthorityGrant

- **schema_id:** `stickbot.m25i.serviceauthoritygrant.v1`
- **semantic version:** `1.0.0-draft`; unknown major fails closed; unknown minor ignored only when extension policy allows.
- **canonical serialization:** UTF-8 JSON, sorted keys, no insignificant whitespace for hash preimage.
- **contract hash:** `sha256(canonical_schema_json)`; computed in M25J, not embedded here as self-reference.
- **required fields:** `schema_id`, `schema_version`, `request_id` or component-native ID, `policy_epoch`, `created_utc`, `source_refs`, `authority_tier`, `privacy_class`, `surface_scope`, `session_scope`, `idempotency_key` when effectful, `receipt_binding` when a receipt.
- **optional fields:** `extensions`, `diagnostics`, `redactions`, `budget`, `watermark`, `parent_receipt_id`, `human_note`.
- **extension policy:** `x_*` namespaced extensions allowed for same major only; mandatory unknown extension is a hard failure.
- **binding/replay:** receipts bind exact request/grant/session/surface/policy epoch and canonical payload hash; stale epoch, duplicate idempotency key, forged parent, or cross-surface replay denies.

### 15. ServiceInvocation

- **schema_id:** `stickbot.m25i.serviceinvocation.v1`
- **semantic version:** `1.0.0-draft`; unknown major fails closed; unknown minor ignored only when extension policy allows.
- **canonical serialization:** UTF-8 JSON, sorted keys, no insignificant whitespace for hash preimage.
- **contract hash:** `sha256(canonical_schema_json)`; computed in M25J, not embedded here as self-reference.
- **required fields:** `schema_id`, `schema_version`, `request_id` or component-native ID, `policy_epoch`, `created_utc`, `source_refs`, `authority_tier`, `privacy_class`, `surface_scope`, `session_scope`, `idempotency_key` when effectful, `receipt_binding` when a receipt.
- **optional fields:** `extensions`, `diagnostics`, `redactions`, `budget`, `watermark`, `parent_receipt_id`, `human_note`.
- **extension policy:** `x_*` namespaced extensions allowed for same major only; mandatory unknown extension is a hard failure.
- **binding/replay:** receipts bind exact request/grant/session/surface/policy epoch and canonical payload hash; stale epoch, duplicate idempotency key, forged parent, or cross-surface replay denies.

### 16. ServiceReceipt

- **schema_id:** `stickbot.m25i.servicereceipt.v1`
- **semantic version:** `1.0.0-draft`; unknown major fails closed; unknown minor ignored only when extension policy allows.
- **canonical serialization:** UTF-8 JSON, sorted keys, no insignificant whitespace for hash preimage.
- **contract hash:** `sha256(canonical_schema_json)`; computed in M25J, not embedded here as self-reference.
- **required fields:** `schema_id`, `schema_version`, `request_id` or component-native ID, `policy_epoch`, `created_utc`, `source_refs`, `authority_tier`, `privacy_class`, `surface_scope`, `session_scope`, `idempotency_key` when effectful, `receipt_binding` when a receipt.
- **optional fields:** `extensions`, `diagnostics`, `redactions`, `budget`, `watermark`, `parent_receipt_id`, `human_note`.
- **extension policy:** `x_*` namespaced extensions allowed for same major only; mandatory unknown extension is a hard failure.
- **binding/replay:** receipts bind exact request/grant/session/surface/policy epoch and canonical payload hash; stale epoch, duplicate idempotency key, forged parent, or cross-surface replay denies.

### 17. ServiceDenial

- **schema_id:** `stickbot.m25i.servicedenial.v1`
- **semantic version:** `1.0.0-draft`; unknown major fails closed; unknown minor ignored only when extension policy allows.
- **canonical serialization:** UTF-8 JSON, sorted keys, no insignificant whitespace for hash preimage.
- **contract hash:** `sha256(canonical_schema_json)`; computed in M25J, not embedded here as self-reference.
- **required fields:** `schema_id`, `schema_version`, `request_id` or component-native ID, `policy_epoch`, `created_utc`, `source_refs`, `authority_tier`, `privacy_class`, `surface_scope`, `session_scope`, `idempotency_key` when effectful, `receipt_binding` when a receipt.
- **optional fields:** `extensions`, `diagnostics`, `redactions`, `budget`, `watermark`, `parent_receipt_id`, `human_note`.
- **extension policy:** `x_*` namespaced extensions allowed for same major only; mandatory unknown extension is a hard failure.
- **binding/replay:** receipts bind exact request/grant/session/surface/policy epoch and canonical payload hash; stale epoch, duplicate idempotency key, forged parent, or cross-surface replay denies.

### 18. ServicePostconditionEvidence

- **schema_id:** `stickbot.m25i.servicepostconditionevidence.v1`
- **semantic version:** `1.0.0-draft`; unknown major fails closed; unknown minor ignored only when extension policy allows.
- **canonical serialization:** UTF-8 JSON, sorted keys, no insignificant whitespace for hash preimage.
- **contract hash:** `sha256(canonical_schema_json)`; computed in M25J, not embedded here as self-reference.
- **required fields:** `schema_id`, `schema_version`, `request_id` or component-native ID, `policy_epoch`, `created_utc`, `source_refs`, `authority_tier`, `privacy_class`, `surface_scope`, `session_scope`, `idempotency_key` when effectful, `receipt_binding` when a receipt.
- **optional fields:** `extensions`, `diagnostics`, `redactions`, `budget`, `watermark`, `parent_receipt_id`, `human_note`.
- **extension policy:** `x_*` namespaced extensions allowed for same major only; mandatory unknown extension is a hard failure.
- **binding/replay:** receipts bind exact request/grant/session/surface/policy epoch and canonical payload hash; stale epoch, duplicate idempotency key, forged parent, or cross-surface replay denies.

### 19. UMC ContractEnvelope extensions

- **schema_id:** `stickbot.m25i.umc_contractenvelope_extensions.v1`
- **semantic version:** `1.0.0-draft`; unknown major fails closed; unknown minor ignored only when extension policy allows.
- **canonical serialization:** UTF-8 JSON, sorted keys, no insignificant whitespace for hash preimage.
- **contract hash:** `sha256(canonical_schema_json)`; computed in M25J, not embedded here as self-reference.
- **required fields:** `schema_id`, `schema_version`, `request_id` or component-native ID, `policy_epoch`, `created_utc`, `source_refs`, `authority_tier`, `privacy_class`, `surface_scope`, `session_scope`, `idempotency_key` when effectful, `receipt_binding` when a receipt.
- **optional fields:** `extensions`, `diagnostics`, `redactions`, `budget`, `watermark`, `parent_receipt_id`, `human_note`.
- **extension policy:** `x_*` namespaced extensions allowed for same major only; mandatory unknown extension is a hard failure.
- **binding/replay:** receipts bind exact request/grant/session/surface/policy epoch and canonical payload hash; stale epoch, duplicate idempotency key, forged parent, or cross-surface replay denies.

### 20. SurfacePolicy

- **schema_id:** `stickbot.m25i.surfacepolicy.v1`
- **semantic version:** `1.0.0-draft`; unknown major fails closed; unknown minor ignored only when extension policy allows.
- **canonical serialization:** UTF-8 JSON, sorted keys, no insignificant whitespace for hash preimage.
- **contract hash:** `sha256(canonical_schema_json)`; computed in M25J, not embedded here as self-reference.
- **required fields:** `schema_id`, `schema_version`, `request_id` or component-native ID, `policy_epoch`, `created_utc`, `source_refs`, `authority_tier`, `privacy_class`, `surface_scope`, `session_scope`, `idempotency_key` when effectful, `receipt_binding` when a receipt.
- **optional fields:** `extensions`, `diagnostics`, `redactions`, `budget`, `watermark`, `parent_receipt_id`, `human_note`.
- **extension policy:** `x_*` namespaced extensions allowed for same major only; mandatory unknown extension is a hard failure.
- **binding/replay:** receipts bind exact request/grant/session/surface/policy epoch and canonical payload hash; stale epoch, duplicate idempotency key, forged parent, or cross-surface replay denies.

### 21. DeliveryRequiredJobEnvelope

- **schema_id:** `stickbot.m25i.deliveryrequiredjobenvelope.v1`
- **semantic version:** `1.0.0-draft`; unknown major fails closed; unknown minor ignored only when extension policy allows.
- **canonical serialization:** UTF-8 JSON, sorted keys, no insignificant whitespace for hash preimage.
- **contract hash:** `sha256(canonical_schema_json)`; computed in M25J, not embedded here as self-reference.
- **required fields:** `schema_id`, `schema_version`, `request_id` or component-native ID, `policy_epoch`, `created_utc`, `source_refs`, `authority_tier`, `privacy_class`, `surface_scope`, `session_scope`, `idempotency_key` when effectful, `receipt_binding` when a receipt.
- **optional fields:** `extensions`, `diagnostics`, `redactions`, `budget`, `watermark`, `parent_receipt_id`, `human_note`.
- **extension policy:** `x_*` namespaced extensions allowed for same major only; mandatory unknown extension is a hard failure.
- **binding/replay:** receipts bind exact request/grant/session/surface/policy epoch and canonical payload hash; stale epoch, duplicate idempotency key, forged parent, or cross-surface replay denies.

### 22. BoundaryDecisionEnvelope

- **schema_id:** `stickbot.m25i.boundarydecisionenvelope.v1`
- **semantic version:** `1.0.0-draft`; unknown major fails closed; unknown minor ignored only when extension policy allows.
- **canonical serialization:** UTF-8 JSON, sorted keys, no insignificant whitespace for hash preimage.
- **contract hash:** `sha256(canonical_schema_json)`; computed in M25J, not embedded here as self-reference.
- **required fields:** `schema_id`, `schema_version`, `request_id` or component-native ID, `policy_epoch`, `created_utc`, `source_refs`, `authority_tier`, `privacy_class`, `surface_scope`, `session_scope`, `idempotency_key` when effectful, `receipt_binding` when a receipt.
- **optional fields:** `extensions`, `diagnostics`, `redactions`, `budget`, `watermark`, `parent_receipt_id`, `human_note`.
- **extension policy:** `x_*` namespaced extensions allowed for same major only; mandatory unknown extension is a hard failure.
- **binding/replay:** receipts bind exact request/grant/session/surface/policy epoch and canonical payload hash; stale epoch, duplicate idempotency key, forged parent, or cross-surface replay denies.

### 23. SanitizedPayloadEnvelope

- **schema_id:** `stickbot.m25i.sanitizedpayloadenvelope.v1`
- **semantic version:** `1.0.0-draft`; unknown major fails closed; unknown minor ignored only when extension policy allows.
- **canonical serialization:** UTF-8 JSON, sorted keys, no insignificant whitespace for hash preimage.
- **contract hash:** `sha256(canonical_schema_json)`; computed in M25J, not embedded here as self-reference.
- **required fields:** `schema_id`, `schema_version`, `request_id` or component-native ID, `policy_epoch`, `created_utc`, `source_refs`, `authority_tier`, `privacy_class`, `surface_scope`, `session_scope`, `idempotency_key` when effectful, `receipt_binding` when a receipt.
- **optional fields:** `extensions`, `diagnostics`, `redactions`, `budget`, `watermark`, `parent_receipt_id`, `human_note`.
- **extension policy:** `x_*` namespaced extensions allowed for same major only; mandatory unknown extension is a hard failure.
- **binding/replay:** receipts bind exact request/grant/session/surface/policy epoch and canonical payload hash; stale epoch, duplicate idempotency key, forged parent, or cross-surface replay denies.

### 24. DeliveryResultEnvelope

- **schema_id:** `stickbot.m25i.deliveryresultenvelope.v1`
- **semantic version:** `1.0.0-draft`; unknown major fails closed; unknown minor ignored only when extension policy allows.
- **canonical serialization:** UTF-8 JSON, sorted keys, no insignificant whitespace for hash preimage.
- **contract hash:** `sha256(canonical_schema_json)`; computed in M25J, not embedded here as self-reference.
- **required fields:** `schema_id`, `schema_version`, `request_id` or component-native ID, `policy_epoch`, `created_utc`, `source_refs`, `authority_tier`, `privacy_class`, `surface_scope`, `session_scope`, `idempotency_key` when effectful, `receipt_binding` when a receipt.
- **optional fields:** `extensions`, `diagnostics`, `redactions`, `budget`, `watermark`, `parent_receipt_id`, `human_note`.
- **extension policy:** `x_*` namespaced extensions allowed for same major only; mandatory unknown extension is a hard failure.
- **binding/replay:** receipts bind exact request/grant/session/surface/policy epoch and canonical payload hash; stale epoch, duplicate idempotency key, forged parent, or cross-surface replay denies.

### 25. ContextBridgeProjectionRecord

- **schema_id:** `stickbot.m25i.contextbridgeprojectionrecord.v1`
- **semantic version:** `1.0.0-draft`; unknown major fails closed; unknown minor ignored only when extension policy allows.
- **canonical serialization:** UTF-8 JSON, sorted keys, no insignificant whitespace for hash preimage.
- **contract hash:** `sha256(canonical_schema_json)`; computed in M25J, not embedded here as self-reference.
- **required fields:** `schema_id`, `schema_version`, `request_id` or component-native ID, `policy_epoch`, `created_utc`, `source_refs`, `authority_tier`, `privacy_class`, `surface_scope`, `session_scope`, `idempotency_key` when effectful, `receipt_binding` when a receipt.
- **optional fields:** `extensions`, `diagnostics`, `redactions`, `budget`, `watermark`, `parent_receipt_id`, `human_note`.
- **extension policy:** `x_*` namespaced extensions allowed for same major only; mandatory unknown extension is a hard failure.
- **binding/replay:** receipts bind exact request/grant/session/surface/policy epoch and canonical payload hash; stale epoch, duplicate idempotency key, forged parent, or cross-surface replay denies.


## Delivery semantics

`NO_REPLY` is valid only when `deliveryRequired=false`. Delivery-required work must end in one explicit outcome:

| Outcome | UMC terminal | Runtime behavior | Surface behavior | Delivery attempt | Evidence/receipt | User-facing prose |
| --- | --- | --- | --- | --- | --- | --- |
| DELIVERY_REQUIRED_PAYLOAD_READY | UMC pending delivery | runtime carries explicit payload; not terminal alone | surface renders only after policy allow | no adapter attempt yet | payload artifact + hash + anchor | allowed only as internal/sanitized preview |
| BOUNDARY_ALLOWED_PAYLOAD_DELIVERED | UMC success if delivery receipt valid | runtime terminal delivered | surface displays sent result | exactly one adapter attempt success | boundary allow + payload + result + dedupe receipt | allowed |
| BOUNDARY_ALLOWED_PAYLOAD_DELIVERY_FAILED | UMC fail/hold requiring owner review | runtime terminal failed | surface may report failure if safe | attempted once and failed | adapter error class + no duplicate proof | allowed only failure prose |
| BOUNDARY_HOLD_NO_DELIVERY | UMC HOLD | runtime no send, explicit hold payload to evidence | no user prose unless current surface is closeout channel and safe | no attempt | hold reason + receipt | safe hold prose only |
| BOUNDARY_REJECT_NO_DELIVERY | UMC REJECT/ABORT | runtime no send | no deliverable payload | no attempt | reject reason + policy receipt | safe reject prose only |
| DELIVERY_REQUIRED_PAYLOAD_MISSING | UMC ABORT | runtime forbids bare NO_REPLY | no payload | no attempt | missing payload receipt | safe failure prose only |
| ANCHOR_MISSING_NO_DELIVERY | UMC HOLD/ABORT | runtime forbids delivery | no payload | no attempt | anchor parser evidence | safe failure prose only |
| DUPLICATE_DELIVERY_SUPPRESSED | UMC success/degraded depending prior receipt | runtime suppresses duplicate | surface no duplicate | no second attempt | idempotency proof + prior result | safe duplicate-suppressed prose only |

## UMC prose-success prevention

Machine enforcement must reject claims that a source was checked, graph reconstructed, service/tool used, message delivered, Ledger completed, or postcondition met unless the turn carries a matching valid receipt bound to the exact request/grant/payload/session/surface/policy epoch. The model may draft prose, but closeout permission is computed from receipts. Missing receipt yields HOLD/REJECT prose, never success prose.

## Surface least privilege

Every surface grant includes identity scope, session scope, privacy classes, permitted services/tools, render profile, delivery profile, external-send approval state, duplicate-suppression keyspace, evidence policy, and cross-surface replay denial. Owner-direct private context is denied in group/shared surfaces by default. SSB may narrow grants only and cannot promote authority.

## Current delivery-contract conflict

M25H proved handler-side local repair but live cron still normalized to `NO_REPLY` and `delivered=false`. Therefore the unresolved architecture dependency is not a single session-key predicate: it is the job/run/session -> boundary decision -> reply payload -> delivery runtime -> result receipt propagation contract. M25I resolves this at design level only.
