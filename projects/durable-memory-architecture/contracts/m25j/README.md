# M25J Contract Schema Skeletons

Terminal target: `M25J_CONTRACT_SCHEMA_SKELETON_TESTS_PASS_NO_LIVE_DELIVERY`.

Canonical schema root selected exactly once: `projects/durable-memory-architecture/contracts/m25j/`.

This is an inert/offline contract package only. It defines schemas, deterministic canonicalization, validation commands, sanitized fixtures, and tests. It does not integrate with Gateway, plugins, cron, Telegram delivery, Ledger, Context Bridge, runtime Service Broker enforcement, UMC live enforcement, Surface Service Broker routing, M25K, or M26.

Canonicalization is a JCS-compatible bounded subset: UTF-8 JSON, sorted object keys, compact separators, duplicate-key rejection, non-finite/floating-point rejection for exact number handling, and SHA-256 lowercase hex. `contractHash` is excluded only from its own preimage for object hash verification.
