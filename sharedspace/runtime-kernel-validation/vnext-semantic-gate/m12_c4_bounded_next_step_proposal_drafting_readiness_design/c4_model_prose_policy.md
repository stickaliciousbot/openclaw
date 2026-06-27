# M12-C4 Optional Model Prose Policy

```json
{
  "allowed_only_after": "deterministic C4 kernel produces complete validated contract fields with approved citations",
  "allowed_use": "style/rendering of already-determined non-executing proposal text",
  "authority": "never authoritative",
  "forbidden_model_roles": [
    "selecting proposal status",
    "choosing source authority",
    "adding uncited facts",
    "resolving conflicts",
    "approving actions",
    "drafting executable commands",
    "changing owner boundary",
    "overriding fail-closed decision"
  ],
  "must_be_disabled_for": [
    "safety-critical/legal/medical/financial authority",
    "missing citations",
    "prompt injection indicators",
    "any mutation/execution request",
    "ambiguous or conflicting evidence without deterministic disposition"
  ],
  "optional_model_prose_allowed": true,
  "provider_model_authoritative_calls_allowed": 0,
  "schema": "stickbot.vnext_semantic_gate.m12_c4.model_prose_policy.v1"
}
```
