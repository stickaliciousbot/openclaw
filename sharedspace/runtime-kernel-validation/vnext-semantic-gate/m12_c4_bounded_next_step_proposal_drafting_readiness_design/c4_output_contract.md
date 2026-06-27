# M12-C4 Proposal Output Contract

```json
{
  "allowed_status": [
    "PROPOSAL",
    "HOLD",
    "REJECT"
  ],
  "cited_source_refs": "must cite approved SourceRows only",
  "conditional_fields": {
    "hold_reason": "required when status is HOLD or REJECT"
  },
  "disposition": "must explain why PROPOSAL/HOLD/REJECT was selected without creating authority beyond cited evidence",
  "non_execution_notice": "required exact semantic meaning: proposal only; no action authority; owner review required before execution",
  "proposal_steps": {
    "items": "non-executing bounded next-step text only",
    "must_not_contain": [
      "execute now",
      "schedule automatically",
      "mutate config",
      "approve production change",
      "external action command"
    ],
    "type": "array"
  },
  "required_fields": [
    "status",
    "proposal_steps",
    "rationale",
    "cited_source_refs",
    "assumptions",
    "uncertainties",
    "required_owner_review",
    "non_execution_notice",
    "disposition"
  ],
  "required_owner_review": true,
  "schema": "stickbot.vnext_semantic_gate.m12_c4.output_contract.v1"
}
```
