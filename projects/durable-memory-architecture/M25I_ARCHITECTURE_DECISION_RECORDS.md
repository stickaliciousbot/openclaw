# M25I Architecture Decision Records

## ADR-01 Canonical authority

Decision: Ledger/source registry remain canonical continuity and source-reference layers; graph/indexes are projections. Consequence: graph/vector/session/model prose cannot promote authority.

## ADR-02 Delivery contract ownership

Decision: split ownership. UMC declares delivery postcondition; job envelope declares delivery intent; boundary handler validates; SSB authorizes render/delivery policy; delivery adapter sends; UMC verifies delivery receipt. Consequence: no single cron/runtime prose path can silently erase required delivery.

## ADR-03 Boundary decision transport

Decision: use explicit durable runtime-local envelope/receipt artifacts in addition to in-process hook return. Do not rely only on in-memory `message_sent` observations. Consequence: M25L/M25M must persist sanitized boundary/payload receipts outside raw private logs.

## ADR-04 Quiet task compatibility

Decision: preserve `NO_REPLY` for genuine quiet-success watchers with `deliveryRequired=false`; delivery-required jobs treat bare `NO_REPLY` as `DELIVERY_REQUIRED_PAYLOAD_MISSING`. Consequence: old quiet jobs remain compatible while proof/closeout jobs cannot disappear silently.

## ADR-05 Receipt persistence

Decision: process-memory only is allowed for transient hook correlation; runtime-local ephemeral receipts for job/run/session binding; sanitized tracked evidence for milestone closeout; canonical Ledger/source state only after explicit authority approval. Consequence: no raw packets or raw surface identifiers in tracked evidence.

## ADR-06 Broker enforcement sequence

Decision: schemas first, shadow broker, receipt verification, enforcement, surface migration. Consequence: direct service calls become prohibited only after receipts and parity prove no hidden breakage.

## ADR-07 Context Bridge projection

Decision: Context Bridge receives sanitized terminal categories/counts/keyed aliases only; no raw packet or cross-log-correlatable hashes. Consequence: it remains operational projection, never authority.

## ADR-08 Schema migration

Decision: Ledger v0.1 remains frozen and compatible while v0.2 records are prototyped in disposable sidecar storage. Consequence: migration cannot rewrite historical evidence or current Ledger records.
