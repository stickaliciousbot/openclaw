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

## Surface Response Target Resolver

Delivery-required pipeline becomes:

```text
DeliveryRequiredJobEnvelope -> UMC postcondition -> RSB grant -> BoundaryDecisionEnvelope -> SanitizedPayloadEnvelope -> SSB policy -> Surface Response Target Resolver -> Delivery Adapter -> DeliveryResultEnvelope -> UMC verification
```

SRTR distinguishes surface authorization from target authorization. It accepts symbolic aliases (`owner-direct-primary`, `current-approved-session`, `operator-canary-target`), verifies identity/session/surface/capability/approval/expiry/intent, and returns a short-lived target grant plus sanitized resolution receipt. It never generates content, broadens SSB permission, chooses fallback recipients, persists raw provider IDs in tracked artifacts, sends messages, or lets the model choose arbitrary addresses.

Additional SurfacePolicy fields: permitted target aliases/classes, target-resolution policy, target-grant requirement, expiry limits, delivery capability limits, no-fallback policy, and target evidence/redaction policy. A permitted delivery surface does not authorize every target on that surface.
