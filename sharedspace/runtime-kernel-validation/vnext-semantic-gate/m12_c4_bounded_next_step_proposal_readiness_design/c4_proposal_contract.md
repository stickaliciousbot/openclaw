# C4 Proposal Contract

```json
{
  "assumptions": "explicitly listed, never hidden",
  "cited_source_refs": "approved SourceRows only",
  "conditional_fields": {
    "hold_reason": "required when status is HOLD or REJECT"
  },
  "disposition": "deterministic explanation for PROPOSAL/HOLD/REJECT",
  "non_execution_notice": "required: proposal only; no action authority; owner approval required before execution",
  "proposal_steps": "non-executing bounded next-step text only; cannot authorize or perform actions",
  "rationale": "must be derived from cited approved source refs",
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
  "schema": "stickbot.vnext_semantic_gate.m12_c4.proposal_contract.v1",
  "status": [
    "PROPOSAL",
    "HOLD",
    "REJECT"
  ],
  "uncertainties": "explicitly preserved; cannot be removed by renderer/model prose"
}
```
