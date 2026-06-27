# M12-C2 Output Contract

C2 outputs exactly one guarded envelope.

```json
{
  "status": "GUIDANCE|HOLD",
  "guidance_steps": [
    {
      "step_id": "string",
      "text": "string",
      "source_ref_ids": ["string"],
      "source_section_ids": ["string"],
      "applicability": "required|conditional|warning|informational",
      "confidence": "high|medium|low"
    }
  ],
  "cited_source_refs": [
    {
      "source_ref_id": "string",
      "artifact_id": "string",
      "path": "string",
      "sha256": "string",
      "section_id": "string",
      "quote_hash": "string"
    }
  ],
  "source_sections": [
    {
      "section_id": "string",
      "heading": "string",
      "line_range": "start-end",
      "section_hash": "string"
    }
  ],
  "confidence": "high|medium|low",
  "applicability": "direct|conditional|insufficient",
  "disposition": "single_artifact_guidance|fail_closed_hold",
  "hold_reason": "string|null"
}
```

Rules:

- `GUIDANCE` requires at least one deterministic cited source ref and all guidance steps must be fully supported by cited sections from the same approved artifact.
- `HOLD` requires empty `guidance_steps` and a specific `hold_reason`.
- The envelope must not include external actions, config edits, routing changes, or uncited next-step recommendations.
- The guard rejects any claim that cannot be traced to deterministic section extraction.
