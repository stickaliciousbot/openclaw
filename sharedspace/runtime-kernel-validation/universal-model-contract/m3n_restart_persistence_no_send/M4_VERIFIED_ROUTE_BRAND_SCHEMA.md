# M4 VerifiedRoute Brand Schema

Status: PASS_M4_VERIFIED_ROUTE_BRAND_DEFINED

## Required fields

- `verified_route_version`
- `route_id`
- `turn_id`
- `session_id`
- `channel`
- `owner_scope`
- `provider`
- `model`
- `fallback_chain`
- `capability_manifest_ref`
- `contract_version`
- `contract_envelope_ref`
- `authority_mode`
- `created_by`
- `created_at`
- `verification_reason`
- `signature_or_brand_token`
- `non_forgeable_brand`
- `source`
- `no_apply`
- `production_enforcement`

## Invariants

- created_only_by_route_verifier_broker_code: PASS
- raw_object_literals_cannot_satisfy_brand: PASS
- brand_not_serializable_as_trusted_authority: PASS
- deserialized_route_requires_reverify: PASS
- session_channel_pins_are_route_intent_not_authority: PASS
- fallback_routes_preserve_contract_version_and_authority_mode: PASS

## Authority note

The JSON representation is evidence only. Runtime trust requires the private module symbol brand; raw object literals and deserialized JSON are rejected until route intent is reverified.
