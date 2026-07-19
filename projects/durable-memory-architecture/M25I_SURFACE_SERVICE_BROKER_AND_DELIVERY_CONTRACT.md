# M25I Surface Service Broker and Delivery Contract

SSB controls least-privilege identity, privacy, rendering, delivery, and dedupe for each surface. It narrows grants only.

## SurfacePolicy fields

surface_id, identity_scope, session_scope, allowed_privacy_classes, denied_privacy_classes, permitted_services, permitted_tools, render_profile, delivery_profile, external_send_approval, group_private_memory_default_deny, evidence_policy, idempotency_namespace, cross_surface_replay_denial, policy_epoch, expiry.

## Delivery-required pipeline

DeliveryRequiredJobEnvelope -> UMC postcondition -> RSB grant -> BoundaryDecisionEnvelope -> SanitizedPayloadEnvelope -> SSB render/delivery policy -> Delivery Adapter -> DeliveryResultEnvelope -> UMC verification.

## `NO_REPLY` rule

`NO_REPLY` is permitted only for `deliveryRequired=false`. A delivery-required job must produce one explicit outcome from the delivery outcome table in the LLD.

## Dedupe

Idempotency key binds job/run/session/surface/payload hash/policy epoch. Duplicate key after delivered receipt yields `DUPLICATE_DELIVERY_SUPPRESSED`; it must not attempt a second send.
