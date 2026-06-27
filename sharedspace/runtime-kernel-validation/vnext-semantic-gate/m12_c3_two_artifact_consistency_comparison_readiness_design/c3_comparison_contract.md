# C3 Comparison Output Contract

Every C3 comparison result must use this envelope:

```json
{
  "status": "CONSISTENT | CONFLICT | HOLD | REJECT",
  "artifact_a_ref": "string|null",
  "artifact_b_ref": "string|null",
  "compared_fields": ["canonical.field.id"],
  "agreement_points": [
    {
      "field": "canonical.field.id",
      "artifact_a_value": "source-backed value",
      "artifact_b_value": "source-backed value",
      "source_refs": ["artifact_a:...", "artifact_b:..."]
    }
  ],
  "conflict_points": [
    {
      "field": "canonical.field.id",
      "artifact_a_value": "source-backed value",
      "artifact_b_value": "source-backed value",
      "source_refs": ["artifact_a:...", "artifact_b:..."],
      "conflict_type": "value_mismatch | missing_in_a | missing_in_b | semantic_incompatibility"
    }
  ],
  "cited_source_refs": ["artifact_a:...", "artifact_b:..."],
  "disposition": "bounded comparison disposition",
  "hold_reason": "required when status is HOLD or REJECT"
}
```

Status semantics:

- `CONSISTENT`: all compared fields agree or are directly compatible under approved deterministic normalization rules.
- `CONFLICT`: one or more compared fields disagree, are missing on one side, or are semantically incompatible.
- `HOLD`: fail-closed because inputs or requested comparison cannot be safely resolved inside C3 scope.
- `REJECT`: guard rejection for requests outside C3 scope or attempting authority bypass/mutation.

No output may invent missing values or reconcile conflicts without direct source-row support from both artifacts.
