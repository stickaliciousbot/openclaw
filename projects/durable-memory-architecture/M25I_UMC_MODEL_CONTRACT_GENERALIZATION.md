# M25I UMC Model Contract Generalization

UMC generalizes from model routing and tool supervision into receipt-bound postconditions.

## Extensions

ContractEnvelope adds `required_services`, `required_delivery`, `required_source_readback`, `receipt_requirements`, `surface_policy_epoch`, `quiet_allowed`, `success_prose_claims_allowed`, and `terminal_outcome`.

## Prose-success prevention

The model cannot claim source checked, graph reconstructed, tool/service used, message delivered, Ledger complete, or postcondition met unless a matching receipt is attached and passes schema/hash/session/surface/policy verification. Without receipt, render HOLD/REJECT/failure prose only.

## Quiet compatibility

Existing `NO_REPLY` remains valid for genuine quiet-success watchers only when `deliveryRequired=false` and the job envelope explicitly permits quiet terminal closeout. Delivery-required jobs cannot normalize missing payload into `NO_REPLY`; that becomes `DELIVERY_REQUIRED_PAYLOAD_MISSING`.
