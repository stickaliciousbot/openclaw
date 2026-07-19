# M25J Contract Schema Skeleton Implementation Prompt

Start only after explicit owner authorization. Do not start from M25I-A closeout alone.

## Objective

Implement draft/inert schema/type skeletons and validation fixtures for the M25I delivery/context/broker contracts. No runtime apply, no Gateway reload/restart, no Telegram, no jobs, no handler arming, no Ledger/Context Bridge/model-route mutation.

## Required terminal

`M25J_CONTRACT_SCHEMA_SKELETON_TESTS_PASS_NO_LIVE_DELIVERY`

## File allowlist

Use `projects/durable-memory-architecture/M25J_FILE_ALLOWLIST_AND_TEST_MATRIX.json`.

## Schemas to skeleton

- SourceRecord
- SourceResolutionResult
- EntityRecord
- ClaimRecord
- RelationRecord
- ContradictionRecord
- SupersessionRecord
- ContextReconstructionRequest
- ContextReconstructionPacket
- ContextReconstructionReceipt
- ServiceDefinition
- ServiceHealth
- ServiceGrantRequest
- ServiceAuthorityGrant
- ServiceInvocation
- ServiceReceipt
- ServiceDenial
- ServicePostconditionEvidence
- UMC ContractEnvelope extensions
- SurfacePolicy
- DeliveryRequiredJobEnvelope
- BoundaryDecisionEnvelope
- SanitizedPayloadEnvelope
- DeliveryResultEnvelope
- ContextBridgeProjectionRecord

## Required validation

- JSON parse and canonical serialization fixtures.
- Unknown major fails closed.
- Extension policy fixtures.
- Request/grant/session/surface/policy epoch receipt binding fixtures.
- Delivery-required bare `NO_REPLY` negative fixture.
- Privacy/raw scan PASS.
- Evidence manifest with no unresolved UNKNOWN.

Stop after M25J; do not start M25K.

## M25J-R SRTR extension

M25J now includes the Surface Response Target Resolver contract skeleton: `SurfaceResponseTargetRequest`, `SurfaceResponseTargetGrant`, and `SurfaceResponseTargetReceipt`. Security fixtures must use visibly synthetic forbidden markers such as `<RAW_TELEGRAM_TARGET_ID_FORBIDDEN>` rather than realistic provider identifiers. M25J-R remains offline/no-live-delivery and must not implement a target registry, invoke adapters, mutate runtime config, create jobs, or start M25K.
