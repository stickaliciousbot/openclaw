# Stickbot Memory Ledger v0.1 — Rehydration Packet

Generated: 2026-07-18T19:58:44.666Z

Status: PASS

Project root: `projects/stickbot-memory-ledger-v0`

Branch: `feature/stickbot-memory-ledger-v0-1`

## Immediate Resume

1. Read `docs/STICKBOT_MEMORY_LEDGER_V0_1_REVISED_IMPROVED_PLAN.md`.
2. Read `docs/MILESTONES.md`, `docs/PROJECT_REHYDRATOR.md`, `docs/REHYDRATOR_IMPROVEMENTS_NOTEBOOK.md`, `docs/TROUBLESHOOTING_REPAIR_AND_IMPLEMENTATION_GUIDE.md`, `docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5R_ACTIONS_LEDGER_REDACTION_PROVENANCE.md`, and `docs/M25D_BOUNDARY_HANDLER_ARMING_PLAN_NO_APPLY.md`. For older implementation slice docs not present in this evidence branch, use the branch/worktree recovery section instead of broad filesystem searches.
3. Preserve hard boundaries: no Gateway/model/provider/runtime memory-route mutation and no `MEMORY.md` writes in v0.1.
4. Treat the production recall path as operator-only and explicit-flag/confirmation/scope gated for exactly `system:memory-ledger`, `project:openclaw-runtime`, and `project:stickbot-tars`.
5. Current live state: M25D arming plan READY/no-apply. M25B-R hash provenance and scoped preservation push PASS; installed boundary-handler runtime hash `98a174e1767221f355d7a28364f738c2918eab320ed5373f9851d31da33b4347` is provenance-proven. M25C pushed blocked because the handler was enabled/hash-proven but unarmed; no retry scheduled/run and no delivery/send. M25D documented exact arming fields and future M25E plan without arming, scheduling, delivery, config mutation, Ledger/Context Bridge mutation, or authority promotion. M25E/M26 not started.
6. Scoped preservation push rule: if global tracked dirt is unrelated/pre-existing, do not treat it as clean; require explicit owner approval for scoped committed-head push, verify empty index/no rebase/no merge and committed diff scope, then push without staging/commit/amend/force.
7. If the current checkout is not the Ledger branch, use the branch/worktree recovery section below before broad filesystem searches.
8. Update this rehydrator and docs before every milestone closeout.
9. For M20R details, read `docs/M20R_DETERMINISTIC_OBSERVER_RECOVERY.md`.

## Current Milestone

M25D boundary-handler arming plan READY/no-apply; installed M25B handler remains enabled, hash-proven, and unarmed; exact installed-handler arming fields and future M25E one-shot arming/disarm proof plan documented; terminal M25D_BOUNDARY_HANDLER_ARMING_PLAN_READY_NO_APPLY; no plugin arming, no retry scheduling/run, no delivery/send, no Gateway/plugin config mutation, no Ledger/Context Bridge mutation, no authority promotion; M25E/M26 not started

Previous milestone: M25C pushed blocked closeout at 3b36d0317b2b5d520be3b9c9de6e8c4eeab6d717: M25C_PUSHED_BLOCKED_SAFE_SINGLE_RETRY_SCHEDULING_NOT_ESTABLISHED because handler was enabled/hash-proven but unarmed. M25B-R hash provenance/preservation PASS at fd00fb76518d463d009b055918d88bcf75d50b27. CB-L5R actions ledger redaction/provenance repair PASS/no marker append; M20R deterministic observer recovery PASS

Next implementation slice: Recommended only, not started: M25E — Boundary Handler Armed One-Shot Retry Controlled Execution. Requires separate owner approval allowing bounded plugin config arming/disarming, exactly one one-shot retry schedule/run, immediate disarm/removal, and sanitized evidence. Do not start M25E/M26 automatically; do not mutate routes/model/provider/fallback/memory routes, Ledger, or Context Bridge

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
- `docs/TROUBLESHOOTING_REPAIR_AND_IMPLEMENTATION_GUIDE.md` — 40896 bytes — sha256:6f741c3a3ed956e34557ee3d4b02844a0548c6ad75be2ff5936485f61f468a9b
- `docs/PROJECT_REHYDRATOR.md` — 18851 bytes — sha256:9a60d555c7b568f49a57886c436c0685a13d8c9330f002019ce853435d1526ed
- `docs/REHYDRATOR_IMPROVEMENTS_NOTEBOOK.md` — 5645 bytes — sha256:e30c2fb18e1c4698625a9dc2a8e92005600c2ce4f7c4d5a057bb21044deba000
- `docs/MILESTONES.md` — 56916 bytes — sha256:97a4cfa5711bffdbe4fe7b6348aeb87d7628e79012ff03836f7619d42f58d609
- `docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5R_ACTIONS_LEDGER_REDACTION_PROVENANCE.md` — 3901 bytes — sha256:6c89634f755fe63010d6d32c09f67b42ea704b23c21c8fdd4a7dfa262c9fb889
- `docs/M25D_BOUNDARY_HANDLER_ARMING_PLAN_NO_APPLY.md` — 17158 bytes — sha256:8490856ae60c3a9660d900bfb07736257cad78cbde28f9b985a3f74a1912ddde
- `artifacts/memory-ledger/m25d-boundary-handler-arming-plan/status.json` — 1111 bytes — sha256:238dcf95b642c95b7161bcce8d1573d320584ab864805cba14dc7b85b95d7751
- `artifacts/memory-ledger/m25d-boundary-handler-arming-plan/summary.json` — 2085 bytes — sha256:4eaff179551ad33a9b46f38d2254cee9cdc57e827c203440c6cf400099846243
- `scripts/stickbot-memory-ledger-rehydrate.mjs` — 12287 bytes — sha256:f7748a89355e3967e2adc57210ce4a8a77936d29c4c3f4eb56405c36c9def6a3
- `scripts/context_bridge_actions_l5r_redact_provenance.py` — 19834 bytes — sha256:cf54ad020136a9dd412e45b5027ba2572e95718bc0f04a93e869e35189725cfe

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
