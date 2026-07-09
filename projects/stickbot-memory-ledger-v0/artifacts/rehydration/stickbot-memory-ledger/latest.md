# Stickbot Memory Ledger v0.1 — Rehydration Packet

Generated: 2026-07-09T09:44:51.742Z

Status: WARN_MISSING_SOURCES

Project root: `projects/stickbot-memory-ledger-v0`

Branch: `feature/stickbot-memory-ledger-v0-1`

## Immediate Resume

1. Read `docs/STICKBOT_MEMORY_LEDGER_V0_1_REVISED_IMPROVED_PLAN.md`.
2. Read `docs/MILESTONES.md`, `docs/M10_READ_ONLY_OPENCLAW_ADAPTER_CANARY_APPROVAL.md`, `docs/M11_PRODUCTION_READINESS_AND_RUNTIME_ENABLEMENT_PLAN.md`, `docs/M12_TINY_PRODUCTION_READONLY_CANARY.md`, `docs/M13_CONTROLLED_PRODUCTION_INTEGRATION_PLAN.md`, `docs/M14_OPERATOR_ONLY_PRODUCTION_READONLY_RECALL.md`, `docs/M15_OPENCLAW_RUNTIME_OPERATOR_READONLY_RECALL.md`, `docs/M16_OPERATOR_RECALL_HARDENING_AND_REPEATABILITY.md`, `docs/M17_STICKBOT_TARS_OPERATOR_READONLY_RECALL.md`, `docs/M18_PRODUCTION_RELEASE_CANDIDATE_CUTOVER_READINESS.md`, `docs/M19_CONTROLLED_PRODUCTION_ENABLEMENT.md`, `docs/M20R_DETERMINISTIC_OBSERVER_RECOVERY.md`, `docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L0_L1_READONLY_AUDIT.md`, `docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L2_AUTHORITY_MATRIX.md`, `docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L3_SHADOW_PROJECTION.md`, `docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L4_SANITIZER_CANARY.md`, and `docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5R_ACTIONS_LEDGER_REDACTION_PROVENANCE.md`.
3. Preserve hard boundaries: no Gateway/model/provider/runtime memory-route mutation and no `MEMORY.md` writes in v0.1.
4. Treat the production recall path as operator-only and explicit-flag/confirmation/scope gated for exactly `system:memory-ledger`, `project:openclaw-runtime`, and `project:stickbot-tars`.
5. Current live state: CB-L5 marker append is blocked/not performed while CB-L5R actions ledger redaction/provenance repair is in progress; CB-L4 PASS/repaired/pushed, CB-L3 PASS/repaired/pushed, CB-L2 PASS/repaired/pushed, CB-L1 PASS/pushed, M20R PASS, no authority promotion; CB-L6/M21/M22 not started. Original M20 remains HOLD because detached observer sessions did not execute required checks.
6. If the current checkout is not the Ledger branch, use the branch/worktree recovery section below before broad filesystem searches.
7. Update this rehydrator and docs before every milestone closeout.
8. For M20R details, read `docs/M20R_DETERMINISTIC_OBSERVER_RECOVERY.md`.

## Current Milestone

CB-L5R actions ledger redaction/provenance repair in progress; CB-L5 marker append blocked and not performed; CB-L4 pushed PASS; no authority promotion; CB-L6/M21/M22 not started

Previous milestone: CB-L4 sanitizer canary PASS and pushed; CB-L3 shadow projection PASS and pushed; CB-L2 authority matrix PASS and pushed; CB-L1 read-only audit PASS and pushed; M20R deterministic observer recovery PASS; M20 detached observer HOLD; M19 controlled production enablement PASS

Next implementation slice: Finish CB-L5R actions ledger redaction/provenance repair only; do not append CB-L5 marker or start CB-L6/M21/M22 without separate owner approval

## Active Observation / Detached Observer

- Milestone: M20R
- Status: MEMORY_LEDGER_V0_1_M20R_DETERMINISTIC_OBSERVER_RECOVERY_PASS_NO_AUTHORITY_PROMOTION
- Started: 2026-07-06T17:49:33+10:00
- Final eligibility: 2026-07-07T17:49:33+10:00
- Session target: session:m20-post-production-observation
- Current gate: CB-L5R
- Detached observer: yes — Original M20 detached observer did not execute required checks; M20R used deterministic harness and child observer artifacts instead.
- Checkpoints: T+2h 8980885e-fc62-44e7-897f-ccc84e2f673c; T+8h 4334fb16-e319-4ef2-a804-bb83c1eef22b; T+24h final 72b92d09-602f-4649-9bd8-df7b91d3d4ce
- Guard: No runtime mutation
- Guard: No recall memory write
- Guard: No recall authority leak
- Guard: Operator surface must remain inert
- Guard: Do not start M21/M22 without separate owner approval

## Branch / Worktree Recovery

If this packet is needed while the active checkout is a different project branch, do **not** infer that Ledger files are missing. Use the Ledger branch/worktree directly.

Preferred worktree: `/tmp/stickbot-memory-ledger-v0-worktree`

Branch: `feature/stickbot-memory-ledger-v0-1`

Read latest packet without switching branches:

```bash
git show feature/stickbot-memory-ledger-v0-1:projects/stickbot-memory-ledger-v0/artifacts/rehydration/stickbot-memory-ledger/latest.md
```

Bounded discovery order:

- `git worktree list`
- `git branch --all --list '*memory-ledger*'`
- `git ls-tree -r --name-only feature/stickbot-memory-ledger-v0-1 projects/stickbot-memory-ledger-v0`

## No-Apply Boundaries

- No Gateway config mutation
- No model/provider route mutation
- No production memory-route mutation
- No MEMORY.md writes in v0.1
- No Nuzo code/package/schema/test/plugin reuse
- No hidden inferred writes

## Source Inventory

- `docs/STICKBOT_MEMORY_LEDGER_V0_1_REVISED_IMPROVED_PLAN.md` — 35416 bytes — sha256:97862604efb7a507e80e77d178e300bca994bb8a2a671c87b031f034a1548931
- `docs/TROUBLESHOOTING_REPAIR_AND_IMPLEMENTATION_GUIDE.md` — 40257 bytes — sha256:69eb46d4507a5cd833c29a1121b62753ff000b58ba3228c7fa2b04be21f0b1b2
- `docs/PROJECT_REHYDRATOR.md` — 18170 bytes — sha256:18ddc848255a3ad7f5c154baefe561c55f272da7ef4527231084a26f66abe458
- `docs/MILESTONES.md` — 55924 bytes — sha256:f4946c6ba6218b7710c73182015fd1974c5967236f64c8aaf8caedbf874c3eef
- `docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5R_ACTIONS_LEDGER_REDACTION_PROVENANCE.md` — 3901 bytes — sha256:6c89634f755fe63010d6d32c09f67b42ea704b23c21c8fdd4a7dfa262c9fb889
- `scripts/stickbot-memory-ledger-rehydrate.mjs` — 13313 bytes — sha256:4e05ab659cc9c5b3860ea1e73dc52b58a8da953857f4b1dbcab63b9cc2bbd48c
- `scripts/context_bridge_actions_l5r_redact_provenance.py` — 19834 bytes — sha256:cf54ad020136a9dd412e45b5027ba2572e95718bc0f04a93e869e35189725cfe

Missing sources:
- `README.md`
- `pyproject.toml`
- `docs/REHYDRATOR_IMPROVEMENTS_NOTEBOOK.md`
- `docs/CLEAN_ROOM_NOTES.md`
- `docs/M10_READ_ONLY_OPENCLAW_ADAPTER_CANARY_APPROVAL.md`
- `docs/M11_PRODUCTION_READINESS_AND_RUNTIME_ENABLEMENT_PLAN.md`
- `docs/M12_TINY_PRODUCTION_READONLY_CANARY.md`
- `docs/M13_CONTROLLED_PRODUCTION_INTEGRATION_PLAN.md`
- `docs/M14_OPERATOR_ONLY_PRODUCTION_READONLY_RECALL.md`
- `docs/M15_OPENCLAW_RUNTIME_OPERATOR_READONLY_RECALL.md`
- `docs/M16_OPERATOR_RECALL_HARDENING_AND_REPEATABILITY.md`
- `docs/M17_STICKBOT_TARS_OPERATOR_READONLY_RECALL.md`
- `docs/M18_PRODUCTION_RELEASE_CANDIDATE_CUTOVER_READINESS.md`
- `docs/M19_CONTROLLED_PRODUCTION_ENABLEMENT.md`
- `docs/M20R_DETERMINISTIC_OBSERVER_RECOVERY.md`
- `docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L0_L1_READONLY_AUDIT.md`
- `docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L2_AUTHORITY_MATRIX.md`
- `docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L3_SHADOW_PROJECTION.md`
- `docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L4_SANITIZER_CANARY.md`
- `scripts/stickbot-memory-ledger-cli.py`
- `scripts/stickbot-memory-ledger-m12-canary.py`
- `scripts/stickbot-memory-ledger-operator-recall.py`
- `scripts/stickbot-memory-ledger-m16-repeatability.py`
- `scripts/context_bridge_ledger_l0_l1_readonly_audit.py`
- `scripts/context_bridge_ledger_l2_authority_matrix.py`
- `scripts/context_bridge_ledger_l3_shadow_projection.py`
- `scripts/context_bridge_ledger_l4_sanitizer_canary.py`
- `src/stickbot_memory_ledger/__init__.py`
- `src/stickbot_memory_ledger/constants.py`
- `src/stickbot_memory_ledger/util.py`
- `src/stickbot_memory_ledger/redaction.py`
- `src/stickbot_memory_ledger/store.py`
- `src/stickbot_memory_ledger/cli.py`
- `src/stickbot_memory_ledger/openclaw_readonly_adapter.py`
- `test/test_first_slice.py`

## LLD Headings

- # Stickbot Memory Ledger v0.1 — Revised Improved Low-Level Design and Implementation Plan
- ## 0. Executive Decision
- ## 1. Design Basis
- ### 1.1 Stickbot goals retained
- ### 1.2 Nuzo-inspired concepts retained, without code reuse
- ### 1.3 Stickbot-specific additions
- ## 2. Non-Negotiable Constraints
- ### 2.1 Clean-room implementation constraints
- ### 2.2 Runtime safety constraints
- ### 2.3 Data safety constraints
- ## 3. Revised Architecture
- ## 4. Storage Design v0.1
- ### 4.1 Canonical store
- ### 4.2 Git ignore requirements
- ### 4.3 Permissions
- ## 5. Revised Schema
- ### 5.1 `store_meta`
- ### 5.2 `schema_migrations`
- ### 5.3 `memory_records`
- ### 5.4 `memory_events`
- ### 5.5 `memory_record_edges`
- ### 5.6 `capture_drafts`
- ### 5.7 `source_refs`
- ### 5.8 `projection_runs`
- ### 5.9 `health_runs`
- ## 6. Scope and Authorization Model
- ### 6.1 Scope syntax
- ### 6.2 Scope is not authorization
- ### 6.3 Scope resolution rules
- ## 7. Trust, Authority, and Sensitivity
- ### 7.1 Trust levels
- ### 7.2 Authority classes
- ### 7.3 Sensitivity classes
- ## 8. Capture and Update Flow
- ### 8.1 Explicit remember
- ### 8.2 Explicit update
- ### 8.3 Forget / archive
- ### 8.4 Operator artifact promotion
- ### 8.5 Daily memory reconciliation
- ## 9. Relationship Evidence Contract

## Milestone Headings

- # Stickbot Memory Ledger v0.1 — Milestones and Gate Ledger
- ## Milestone Status Summary
- ## M0 — Revised Design Closeout
- ## M0R — Docs, Repair Guide, Rehydrator, GitHub Preservation
- ## M1 — Store Bootstrap
- ## M2 — Lifecycle + Event Integrity
- ## M3 — Policy + Capture Evidence
- ## M4 — Redaction Gate
- ## M5 — Recall Boundary
- ## M6 — Doctor + Export/Import DR
- ## M7 — Generated Projection
- ## M8 — Reconcile
- ## M9 — Limited Internal Adoption
- ## M10 — Optional Read-Only OpenClaw Adapter Canary
- ## M11 — Production Readiness and Runtime Enablement Plan
- ## M12 — Tiny Production Read-Only Canary
- ## M13 — Controlled Production Integration Plan
- ## M14 — Operator-Only Production Read-Only Recall Integration
- ## M15 — OpenClaw Runtime Operator-Only Read-Only Recall
- ## M16 — Operator Recall Hardening and Repeatability
- ## M17 — Stickbot-TARS Operator-Only Read-Only Recall
- ## M18 — Production Release Candidate / Cutover Readiness
- ## M19 — Controlled Production Enablement
- ## M20 — 24h Post-Production Observation / Soak
- ## M20R — Deterministic Observer Recovery / Redo
- ## CB-L0/CB-L1 — Context Bridge ↔ Mesh ↔ Ledger Read-Only Reconciliation
- ## CB-L2 — Context Bridge ↔ Mesh ↔ Ledger Authority Classification + Drift Matrix
- ## CB-L3 — Context Bridge ↔ Mesh ↔ Ledger Shadow User-Facing Projection
- ## CB-L5 / CB-L5R — Context Bridge Actions Provenance Boundary
- ## CB-L4 — Context Bridge ↔ Mesh ↔ Ledger Presentation Sanitizer Canary
- ## Closeout Record Template

## Troubleshooting Guide Headings

- # Stickbot Memory Ledger v0.1 — Troubleshooting, Repair, and Detailed Implementation Guide
- ## 1. Purpose
- ## 2. Golden Rules
- ## 3. File and Directory Map
- ## 4. Build Order
- ### Slice A — M1/M2/M4/M5-partial
- ### Slice B — M3
- ### Slice C — M6/M7/M8
- ### Slice D — M9/M10
- ## 5. Health Checks to Keep Green
- ## 6. Common Failure Modes and Repairs
- ### 6.1 Schema migration failed
- ### 6.2 Redaction failure
- ### 6.3 Event hash chain broken
- ### 6.3a Record hash/content integrity broken
- ### 6.4 Recall boundary failure
- ### 6.4a M10 read-only adapter canary failure
- ### 6.5 Clean-room failure
- ### 6.6 Git safety failure
- ### 6.7 Mutation sentinel failure
- ### 6.8 Capture suggestion false positive
- ### 6.9 Generated projection failure
- ### 6.10 Reconcile failure or unexpected warning
- ### 6.11 Limited adoption rollback
- ## 7. Detailed Implementation Guidance
- ### 7.1 IDs
- ### 7.2 Event hash
- ### 7.3 Record hash
- ### 7.4 Redaction scanner
- ### 7.5 Transactions
- ### 7.6 Recall renderer
- ### 7.7 Import quarantine
- ## 8. M15 OpenClaw Runtime Operator Recall Recovery
- ## 9. M16 Operator Repeatability Recovery
- ## 10. M17 Stickbot-TARS Operator Recall Recovery
- ## 11. M18 Production Release-Candidate / Cutover Readiness Recovery
- ## 12. M19 Controlled Production Enablement Recovery
- ## 13. M20 / M20R Detached Observer Recovery
- ## 14. Context Bridge ↔ Mesh ↔ Ledger CB-L0/CB-L1 Read-Only Audit Recovery
- ## 15. Context Bridge ↔ Mesh ↔ Ledger CB-L2 Authority Matrix Recovery

## Validation Commands

```bash
node projects/stickbot-memory-ledger-v0/scripts/stickbot-memory-ledger-rehydrate.mjs --status
node --check projects/stickbot-memory-ledger-v0/scripts/stickbot-memory-ledger-rehydrate.mjs
git diff --check -- projects/stickbot-memory-ledger-v0
```
