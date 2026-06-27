# C1K manifest SHA transition note — M12-C1K-D

Status: PASS
Created UTC: 2026-06-27T03:38:30Z

## What changed

The earlier expected C1K `evidence_manifest.json` SHA was:

`50527805a332a4ebecb8737bdb82354d9503edca2986b71fba536c20c0e27e75`

During preparation for C1R16, the C1K evidence-generating test was accidentally rerun in-place. That regenerated the C1K evidence packet and changed `evidence_manifest.json` to the now accepted SHA:

`097c0819182001fcf0c0497c7c072be12a8c51f948d2d8f52a39c2ceaf7f28dd`

## Why C1K remains PASS

The regenerated C1K packet still reports `M12_C1K_DETERMINISTIC_ARTIFACT_QA_KERNEL_PASS`, `70/70` tests, `0` provider/model calls, no production expansion, cache disabled, artifact-memory promotion false, runtime authority mutation false, and rollback ready true.

Read-only validation now re-runs C1K kernel checks in memory and confirms the frozen disk artifacts match the accepted SHA without rewriting `status.json`, `kernel_test_report.json`, or `evidence_manifest.json`.

## Why C1R16 blocked correctly

C1R16 was authorized to consume C1K read-only at the prior expected SHA. Because the C1K generating script had changed the evidence SHA before C1R16 replay, the prerequisite no longer held. C1R16 therefore correctly failed closed / BLOCKED instead of consuming a drifted artifact.

## What prevents recurrence

- `scripts/test_m12_c1_artifact_qa_kernel.py` now defaults to read-only validation.
- Artifact regeneration requires explicit `--write-artifacts`.
- `scripts/m12_c1k_read_only_guard.py` is the required C1R16 preflight/consumption guard.
- The guard verifies the accepted C1K SHA and proves no C1K artifact hash changes during validation.
- C1R16 must consume C1K through the read-only guard, not by running the evidence-generating path.
