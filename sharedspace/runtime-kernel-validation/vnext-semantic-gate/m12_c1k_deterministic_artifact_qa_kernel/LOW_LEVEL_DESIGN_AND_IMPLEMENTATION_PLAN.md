# M12-C1K Deterministic Artifact Q&A Kernel — Low-Level Design & Implementation Plan Goal

Generated: 2026-06-27 AEST
Owner lane: Stickbot / OpenClaw runtime-kernel validation
Status: DRAFT_READY_FOR_REVIEW
Mutation posture: NO_APPLY / NO_PRODUCTION_MUTATION / NO_MEMORY_PROMOTION

## 1. Goal

Build a deterministic artifact-bound Q&A kernel that can answer bounded owner/operator questions from explicitly selected validation artifacts without using hidden session context, hot memory, model recall, or unverified summaries as authority.

The kernel exists to make artifact status questions repeatable, auditable, and source-visible after the M12-C1 source-authority failure and M12-C1R isolation repair.

Success means: given the same question, same source allowlist, same artifact snapshot, and same kernel version, the system produces the same answer classification, citations, abstentions, and evidence ledger.

## 2. Problem Statement

M12-C1 showed that an artifact status Q&A path can fail if it lets non-authoritative context, summaries, or implicit memory answer in place of canonical artifacts. C1K hardens that path by creating a narrow deterministic kernel with explicit source selection, evidence extraction, citation requirements, abstention semantics, and reproducible output.

## 3. Non-Goals

- No Gateway config mutation.
- No model route/default/fallback mutation.
- No artifact-memory promotion.
- No cache/hydration/context-bridge authority promotion.
- No direct provider bypass.
- No broad natural-language assistant answer mode.
- No rewriting historical artifacts.
- No using T3/T4 lossy summaries as authoritative evidence.

## 4. Authority Model

### 4.1 Inputs

The kernel accepts only:

1. `question_text` — the bounded owner/operator question.
2. `source_allowlist` — exact artifact files or manifest entries allowed for this question.
3. `artifact_snapshot_id` — immutable identifier for the artifact set under review.
4. `kernel_policy_version` — deterministic ruleset version.
5. `expected_question_class` — one of the supported bounded classes.

### 4.2 Authoritative Sources

Allowed authority levels:

- T0 `raw_source`
- T1 `redacted_raw`
- T2 `extractive_semantic`

Explicitly non-authoritative for final claims:

- T3 `bounded_abstraction`
- T4 `lossy_summary`
- live chat context
- hot context
- memory recall
- model prior knowledge
- unpinned web results
- comments not tied to SourceRef IDs

### 4.3 SourceRef Requirement

Every factual claim in a non-abstain answer must map to at least one SourceRef:

```text
SourceRef := artifact_snapshot_id + relative_path + line_range_or_json_pointer + sha256_if_available
```

If a claim lacks SourceRef coverage, the kernel must either remove it or classify the answer as `ABSTAIN_INSUFFICIENT_SOURCE_COVERAGE`.

## 5. Supported Question Classes

C1K supports only deterministic artifact Q&A classes:

1. `STATUS_LOOKUP`
   - Example: “Did M12-C1R pass?”
   - Output: status, artifact path, source refs, first blocking failure if any.

2. `GATE_RESULT_LOOKUP`
   - Example: “Which gates failed?”
   - Output: gate table/list from authoritative gate result artifacts only.

3. `ARTIFACT_LOCATION_LOOKUP`
   - Example: “Where is the evidence manifest?”
   - Output: path(s), manifest pointers, existence/readability evidence.

4. `SAFETY_POSTURE_LOOKUP`
   - Example: “Was production mutated?”
   - Output: bounded mutation/cache/provider/memory/scope posture from source refs.

5. `NEXT_STEP_READINESS_LOOKUP`
   - Example: “May M12-C1 full readiness rerun start?”
   - Output: readiness decision only if explicit source says so; otherwise abstain.

Unsupported questions must return `ABSTAIN_UNSUPPORTED_QUESTION_CLASS`.

## 6. Deterministic Pipeline

### Stage 0 — Request Normalize

- Trim whitespace.
- Preserve exact original question.
- Derive normalized question for class matching.
- Reject multi-question bundles unless each question can be split deterministically.

Output: `request_normalization.json`

### Stage 1 — Question Classify

- Match against supported question-class rules.
- Require either exact operator-provided expected class or deterministic classifier agreement.
- If ambiguous, abstain with `ABSTAIN_AMBIGUOUS_QUESTION_CLASS`.

Output: `question_classification.json`

### Stage 2 — Source Allowlist Resolve

- Resolve only files/manifests listed in `source_allowlist`.
- Reject symlinks, missing files, unreadable files, path traversal, hidden context, or unlisted siblings.
- Record file metadata and digest when available.

Output: `source_resolution_ledger.json`

### Stage 3 — Evidence Extract

- Extract only spans/JSON pointers relevant to the question class.
- Preserve exact text snippets or JSON values.
- Do not paraphrase at this stage.
- Assign SourceRef IDs.

Output: `evidence_extract.jsonl`

### Stage 4 — Coverage Map

- Map each required answer field to one or more SourceRefs.
- Mark required fields as `covered`, `contradicted`, or `missing`.
- Contradictions force `ABSTAIN_CONFLICTING_SOURCES` unless class policy defines a tie-breaker.

Output: `coverage_map.json`

### Stage 5 — Decision/Answer Compose

- Compose from covered fields only.
- Include answer classification.
- Include citations beside claims.
- No uncited summary sentences.
- If any required field is missing, use the class-specific abstention.

Output: `answer.json`

### Stage 6 — Self-Check

Hard checks:

- No unsupported source authority.
- No uncited factual claims.
- No hidden-context fields.
- No cache/hydration/memory dependency.
- Output schema valid.
- Re-run determinism fixture matches expected output.

Output: `self_check.json`

### Stage 7 — Evidence Manifest

Create a run manifest containing:

- kernel version
- artifact snapshot ID
- question text
- source allowlist
- outputs from stages 0–6
- final classification
- failed gates if any
- no-mutation readback

Output: `evidence_manifest.json`

## 7. Output Schema

```json
{
  "kernel": "m12_c1k_deterministic_artifact_qa_kernel",
  "kernel_policy_version": "m12-c1k.v1",
  "artifact_snapshot_id": "string",
  "question_text": "string",
  "question_class": "STATUS_LOOKUP | GATE_RESULT_LOOKUP | ARTIFACT_LOCATION_LOOKUP | SAFETY_POSTURE_LOOKUP | NEXT_STEP_READINESS_LOOKUP",
  "classification": "ANSWERED | ABSTAIN_UNSUPPORTED_QUESTION_CLASS | ABSTAIN_AMBIGUOUS_QUESTION_CLASS | ABSTAIN_INSUFFICIENT_SOURCE_COVERAGE | ABSTAIN_CONFLICTING_SOURCES | DENY_SOURCE_AUTHORITY_FAILURE | DENY_SCHEMA_FAILURE",
  "answer": {
    "summary": "string or null",
    "fields": {}
  },
  "citations": [
    {
      "source_ref_id": "string",
      "path": "string",
      "range": "line range or json pointer",
      "sha256": "string or null"
    }
  ],
  "abstention_reason": "string or null",
  "safety_readback": {
    "production_mutated": false,
    "gateway_config_mutated": false,
    "model_route_mutated": false,
    "artifact_memory_promoted": false,
    "cache_or_hydration_used_as_authority": false,
    "direct_provider_bypass": false
  }
}
```

## 8. Hard Pass Gates

C1K passes only if all gates pass:

1. `G_SOURCE_ALLOWLIST_ONLY`
2. `G_NO_HIDDEN_CONTEXT_AUTHORITY`
3. `G_SOURCE_REF_COVERAGE`
4. `G_SCHEMA_VALID`
5. `G_ABSTAIN_ON_MISSING_OR_CONFLICTING_EVIDENCE`
6. `G_DETERMINISTIC_REPLAY`
7. `G_NO_PRODUCTION_MUTATION`
8. `G_NO_ARTIFACT_MEMORY_PROMOTION`
9. `G_NO_DIRECT_PROVIDER_BYPASS`
10. `G_NO_CACHE_OR_HYDRATION_AUTHORITY`

Any failed hard gate yields `DENY_HOLD_C1K_KERNEL_UNSAFE` and blocks downstream artifact Q&A readiness use.

## 9. Implementation Plan

### Step 1 — Create kernel policy file

Create `kernel_policy.m12-c1k.v1.json` defining:

- supported question classes
- required fields per class
- allowed authority levels
- abstention codes
- hard pass gates
- output schema pointer

### Step 2 — Create source resolver

Implement a small deterministic resolver that:

- accepts an explicit allowlist
- refuses traversal/symlink expansion
- records digest/readability
- emits `source_resolution_ledger.json`

### Step 3 — Create class-specific extractors

Implement extractors for:

- manifest status fields
- gate results
- artifact path pointers
- safety readback fields
- explicit readiness decisions

No free-form semantic inference in v1.

### Step 4 — Create coverage mapper

Implement required-field coverage checks and contradiction detection.

### Step 5 — Create answer composer

Compose strict JSON answer output only from covered fields.

### Step 6 — Create deterministic fixtures

Fixtures should include:

- passing status lookup
- missing source coverage abstain
- conflicting source abstain
- unsupported question class abstain
- safety posture lookup
- readiness lookup with missing explicit permission

### Step 7 — Validate against C1/C1R artifacts

Run C1K in read-only mode against:

- M12-C1 abort package
- M12-C1 owner abort condition addendum
- M12-C1R source authority isolation repair package

Expected result: C1 questions must not be answered from summaries alone; C1R status may be answered only from explicit authoritative artifacts.

### Step 8 — Freeze C1K evidence package

Write final artifacts under a dedicated run directory and record:

- manifest
- policy file
- fixture outputs
- gate results
- final classification
- no-mutation readback

## 10. First Owner-Facing Goal Statement

M12-C1K should prove that Stickbot can answer artifact-status questions from frozen validation artifacts with deterministic citations and abstain whenever source authority is missing, conflicting, or outside the allowlist.

It is not a smarter summarizer. It is a safety kernel for artifact Q&A.

## 11. Initial Recommendation

Proceed with C1K as a no-apply design-and-fixture milestone first. Do not connect it to live owner/operator Q&A until deterministic replay and source-ref coverage fixtures pass.

Recommended next classification if accepted:

`M12_C1K_LLD_IMPLEMENTATION_PLAN_READY_NO_APPLY`
