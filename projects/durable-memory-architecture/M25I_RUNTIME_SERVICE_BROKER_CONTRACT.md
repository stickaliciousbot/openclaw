# M25I Runtime Service Broker Contract

RSB is the runtime capability and receipt control plane. It does not own source truth or surface disclosure.

## Contract objects

- ServiceDefinition: service_id, version, health endpoint, accepted request schema, grant requirements, budgets, cancellation support, receipt schema.
- ServiceHealth: GREEN/YELLOW/RED, version, contract hash compatibility, dependency watermarks.
- ServiceGrantRequest: requested service/action, surface/session/identity scope, privacy class, budget, policy epoch, postcondition.
- ServiceAuthorityGrant: grant_id, expiry, scope, allowed actions, budget, denial reasons if absent.
- ServiceInvocation: grant_id/request_id/service_id/canonical payload hash.
- ServiceReceipt/Denial/PostconditionEvidence: exact binding of invocation to result, timeout/cancel/error, no-write sentinel and source readback.

## Enforcement

Wrong scope, stale policy epoch, expired grant, forged receipt, bypassed service, budget overrun, or unhealthy required dependency denies. Shadow milestones observe and count bypass first; enforcement occurs only after schemas, shadow broker, receipt verification, and surface migration.
