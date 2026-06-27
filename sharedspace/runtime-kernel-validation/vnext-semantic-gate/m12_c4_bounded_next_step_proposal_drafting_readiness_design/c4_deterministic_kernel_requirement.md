# M12-C4 Deterministic Kernel Requirement

```json
{
  "deterministic_c4_proposal_kernel_required": true,
  "kernel_responsibilities": [
    "validate case manifest source allowlist",
    "compile approved SourceRows",
    "classify request into PROPOSAL/HOLD/REJECT",
    "generate bounded non-executing proposal contract",
    "enforce citations",
    "preserve uncertainty/conflicts/prerequisites",
    "block execution/mutation/scheduling/external actions",
    "enforce optional model prose policy",
    "emit audit reports and counters"
  ],
  "required_before": [
    "C4 readiness exercise",
    "C4 limited production canary",
    "C4 production acceptance",
    "any C4 production route"
  ],
  "required_fixture_minimums": {
    "hold_cases": 14,
    "proposal_cases": 8,
    "reject_cases": 10,
    "total_cases": 32
  },
  "schema": "stickbot.vnext_semantic_gate.m12_c4.kernel_requirement.v1"
}
```
