# Stickbot Memory Ledger v0.1 — Project Rehydrator

**Status:** `REHYDRATOR_READY_NO_APPLY`
**Branch:** `feature/stickbot-memory-ledger-v0-1`
**Project root:** `projects/stickbot-memory-ledger-v0/`

---

## 1. What This Project Is

Stickbot Memory Ledger v0.1 is a local-first structured canonical memory ledger for Stickbot. It adds IDs, revisions, scopes, event history, redaction gates, recall boundaries, and health checks underneath existing human-readable continuity files.

It does **not** replace:

- `MEMORY.md`;
- daily memory files;
- context bridge ledgers;
- project rehydrators;
- source-authority gates.

It makes them safer and more machine-verifiable.

---

## 2. Current Implementation Authority

Read this first:

```text
projects/stickbot-memory-ledger-v0/docs/STICKBOT_MEMORY_LEDGER_V0_1_REVISED_IMPROVED_PLAN.md
```

This supersedes the earlier v0 plan.

Key decisions:

- clean-room Stickbot-native implementation;
- SQLite + FTS canonical local store;
- event hash chain;
- record hashes;
- sensitivity classes;
- explicit scope allowlists for future runtime adapters;
- `MEMORY.md` writes forbidden until v1;
- OpenClaw integration delayed until M10 read-only canary;
- first slice is local CLI/store only.

---

## 3. Hard Boundaries to Preserve

Never do these in v0.1:

- mutate OpenClaw Gateway config;
- mutate model/provider/fallback routes;
- mutate production memory routes;
- install/import/vendor Nuzo code or packages;
- copy Nuzo schemas/tests/source/plugin artifacts;
- write production `MEMORY.md`;
- store raw chat/message/account IDs or tokens in Git-bound artifacts;
- persist inferred drafts silently;
- activate runtime adapter in production without a later explicit approval milestone.

Allowed bug-repair nuance:

- Public Nuzo code may be inspected for conceptual ideas if stuck, but final code/tests/schema must remain independently authored Stickbot code.

---

## 4. Key Files

```text
README.md
docs/STICKBOT_MEMORY_LEDGER_V0_1_REVISED_IMPROVED_PLAN.md
docs/TROUBLESHOOTING_REPAIR_AND_IMPLEMENTATION_GUIDE.md
docs/PROJECT_REHYDRATOR.md
docs/REHYDRATOR_IMPROVEMENTS_NOTEBOOK.md
docs/MILESTONES.md
docs/CLEAN_ROOM_NOTES.md
docs/M10_READ_ONLY_OPENCLAW_ADAPTER_CANARY_APPROVAL.md
docs/M11_PRODUCTION_READINESS_AND_RUNTIME_ENABLEMENT_PLAN.md
docs/M12_TINY_PRODUCTION_READONLY_CANARY.md
docs/M13_CONTROLLED_PRODUCTION_INTEGRATION_PLAN.md
docs/M14_OPERATOR_ONLY_PRODUCTION_READONLY_RECALL.md
docs/M15_OPENCLAW_RUNTIME_OPERATOR_READONLY_RECALL.md
docs/M16_OPERATOR_RECALL_HARDENING_AND_REPEATABILITY.md
docs/M17_STICKBOT_TARS_OPERATOR_READONLY_RECALL.md
docs/M18_PRODUCTION_RELEASE_CANDIDATE_CUTOVER_READINESS.md
docs/M19_CONTROLLED_PRODUCTION_ENABLEMENT.md
docs/M20R_DETERMINISTIC_OBSERVER_RECOVERY.md
docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L0_L1_READONLY_AUDIT.md
docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L2_AUTHORITY_MATRIX.md
docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L3_SHADOW_PROJECTION.md
docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L4_SANITIZER_CANARY.md
docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5R_ACTIONS_LEDGER_REDACTION_PROVENANCE.md
scripts/stickbot-memory-ledger-rehydrate.mjs
scripts/stickbot-memory-ledger-m12-canary.py
scripts/stickbot-memory-ledger-operator-recall.py
scripts/stickbot-memory-ledger-m16-repeatability.py
scripts/context_bridge_ledger_l0_l1_readonly_audit.py
scripts/context_bridge_ledger_l2_authority_matrix.py
scripts/context_bridge_ledger_l3_shadow_projection.py
scripts/context_bridge_ledger_l4_sanitizer_canary.py
scripts/context_bridge_actions_l5r_redact_provenance.py
artifacts/rehydration/stickbot-memory-ledger/latest.md
artifacts/rehydration/stickbot-memory-ledger/latest.json
```

Current implementation files:

```text
pyproject.toml
src/stickbot_memory_ledger/*.py
scripts/stickbot-memory-ledger-cli.py
test/test_first_slice.py
```

Future modules may be split under `src/stickbot_memory_ledger/` as the implementation grows.

---

## 5. Rehydrate Immediately

Preferred path when the Ledger worktree exists:

```bash
cd /tmp/stickbot-memory-ledger-v0-worktree
node projects/stickbot-memory-ledger-v0/scripts/stickbot-memory-ledger-rehydrate.mjs --status
```

Then read:

```text
projects/stickbot-memory-ledger-v0/artifacts/rehydration/stickbot-memory-ledger/latest.md
```

If the active checkout is another project branch, do **not** infer that Ledger files are missing. Use branch-aware recovery before broad filesystem scans:

```bash
git worktree list
git branch --all --list '*memory-ledger*'
git ls-tree -r --name-only feature/stickbot-memory-ledger-v0-1 projects/stickbot-memory-ledger-v0
git show feature/stickbot-memory-ledger-v0-1:projects/stickbot-memory-ledger-v0/artifacts/rehydration/stickbot-memory-ledger/latest.md
```

If the script fails, manually read:

1. this file;
2. `docs/REHYDRATOR_IMPROVEMENTS_NOTEBOOK.md`;
3. `docs/MILESTONES.md`;
4. `docs/TROUBLESHOOTING_REPAIR_AND_IMPLEMENTATION_GUIDE.md`;
5. `docs/STICKBOT_MEMORY_LEDGER_V0_1_REVISED_IMPROVED_PLAN.md`.

---

## 6. Current Milestone State

As of the M20R deterministic observer recovery closeout:

- M0 revised design: PASS/no-apply.
- M0R docs + rehydrator + GitHub preservation: PASS.
- M1 store bootstrap: PASS unit + CLI smoke.
- M2 lifecycle + event integrity: PASS unit + CLI smoke.
- M3 policy + capture evidence: PASS unit + CLI path.
- M4 redaction gate: PASS unit + CLI smoke.
- M5 recall boundary: PASS unit + CLI smoke.
- M6 doctor/export/import DR: PASS unit validated.
- M7 generated projection: PASS unit validated, no `MEMORY.md` write.
- M8 reconcile: PASS unit validated, no hidden write.
- M9 limited internal adoption: PASS unit validated, no runtime promotion.
- M10 optional read-only OpenClaw adapter canary: PASS unit validated, off by default, no runtime promotion.
- M11 production readiness/runtime enablement plan: READY/no-apply, no production enablement.
- M12 tiny read-only canary: PASS, local runtime-adjacent harness only, `system:memory-ledger`, 3 successful recalls, 1 denied-scope fail-closed check, rollback/off-by-default verified, no authority promotion.
- M13 controlled production integration plan: READY/no-apply; recommended operator-only CLI / local runtime-adjacent recall as the smallest safe next touchpoint.
- M14 operator-only production read-only recall: PASS; explicit local flag + `--confirm-readonly`; `system:memory-ledger` only; sanitized output by default; 3 successful recalls, denied-scope/missing-confirmation/missing-flag fail-closed checks; no writes or authority promotion.
- M15 OpenClaw runtime operator-only read-only recall: PASS; exactly one approved project scope added (`project:openclaw-runtime`); M15-A controlled source-ref-backed seed created 6 repo-sanitized project records; M15-B project recall succeeded 3 times, system recall still worked, denied second project/missing confirmation/missing flag failed closed, recall-time store hash unchanged, rollback proof passed.
- M16 operator recall hardening and repeatability: PASS; runbook and repeatability harness added; repeated recalls for both approved scopes succeeded; denied/missing-confirmation/missing-flag checks failed closed; store counts/hash unchanged; mutation sentinel clean; approval-gated verification handling documented.
- M17 Stickbot-TARS operator-only read-only recall: PASS; exactly one approved project scope added (`project:stickbot-tars`); M17-A controlled source-ref-backed seed created 7 repo/workspace-sanitized project records; operator recall succeeded for TARS while prior system/OpenClaw runtime recalls remained green; unapproved `project:equipmentiq`, missing confirmation, and missing flag paths failed closed; recall-time store hash/counts unchanged; no authority promotion.
- M18 production release-candidate/cutover readiness: PASS/no-apply; production enablement not performed; final M19 command contract, host/path preflight assumptions, go/no-go checklist, bounded production test plan, sanitized evidence plan, rollback plan, and approval-gated check handling documented.
- M19 controlled production enablement: PASS; canonical production store `state/stickbot-memory-ledger/v0/memory-ledger.sqlite` created/hydrated through confirmed seed paths; operator-only production read-only recall command verified for all three approved scopes; denied/missing-confirmation/missing-flag checks failed closed; recall-time counts/hash unchanged; no runtime mutation; no authority promotion; rollback/inert proof passed.
- M20 detached observer closeout: HOLD; the scheduled 24h detached cron/agent observer did not execute required M20 checks and must not be upgraded to PASS. Correct classification: `HOLD_M20_DETACHED_OBSERVER_DID_NOT_EXECUTE_CHECKS_NO_PASS_UPGRADE`.
- M20R deterministic observer recovery: PASS; deterministic harness launched, wrote required evidence, and child observer executed actual checks. Terminal status: `MEMORY_LEDGER_V0_1_M20R_DETERMINISTIC_OBSERVER_RECOVERY_PASS_NO_AUTHORITY_PROMOTION`.

Current live state:

```text
M20R — deterministic observer recovery PASS, no authority promotion; M21/M22 not started.
CB-L0/CB-L1 — Context Bridge ↔ Ledger read-only reconciliation PASS; no bridge/Ledger/runtime mutation.
CB-L2 — authority classification + drift matrix PASS with closeout metadata repaired to explicit PASS; read-only/no-apply.
CB-L3 — shadow user-facing projection PASS with closeout metadata repaired to explicit PASS; read-only/shadow-only; no production wiring.
CB-L4 — presentation sanitizer canary PASS with closeout metadata repaired to explicit PASS; test-harness-only; no production wiring; no mutation.
CB-L5 — append-only Ledger status marker blocked before append due to dirty/untracked live Context Bridge `actions.json` containing raw private identifier text; no marker append occurred.
CB-L5R — actions ledger redaction/provenance repair PASS; sanitized/tracked `actions.json`; no `events.jsonl` mutation; no marker append; CB-L6/M21/M22 not started.
```

M20R evidence root:

```text
sharedspace/runtime-kernel-validation/memory-ledger/m20r_deterministic_observer_recovery_20260709T1345AEST_r1/
```

M20R validation summary:

- recall success/fail-closed/error counts: `3 / 3 / 0`;
- store records/events unchanged: `19 / 20` before and after;
- store SHA unchanged: `f50ff3836724358d2ef99d92d7c32c2c07651138a749e2a03ce5c03c512807f6`;
- doctor status: `pass`;
- rehydrator status: `PASS`;
- mutation sentinel: `PASS_ALL_FALSE`;
- no runtime/Gateway/model/provider/fallback/Telegram/memory-route mutation;
- no recall-time memory writes;
- no authority promotion;
- no raw/private artifacts created or tracked.

CB-L0/CB-L1 closeout: `CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L1_READONLY_AUDIT_PASS_NO_MUTATION`; evidence root `state/context-bridge-ledger-audit/cb-l0-l1-20260709T1432AEST-final/`; 27/27 gates passed; bridge events/actions `113/43`; action counts `done=38`, `in_progress=5`; Ledger records/events `19/20`; recall authority `none`; raw runtime blob/presentation risk found and recorded as sanitized warning; no bridge/Ledger/runtime mutation; no authority promotion; preserved remote commit `b7140146a08693d7f3d43361123d0e5622c7ccb5`.

CB-L2 closeout repaired and pushed: `CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L2_CLOSEOUT_REPAIRED_PASS_NO_MUTATION`; substantive terminal remains `CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L2_AUTHORITY_MATRIX_PASS_NO_MUTATION`; final closeout status `PASS`; authority matrix hash `d4d619178b4fc5a408e353c024bcec1cee004f9e04627b829522ad3c3cf4b35c`; drift matrix hash `5d2d477c725c39efe6eec35491aa135fe644fd9d3acce4e75828d8fd005e0ed9`; pushed head `fcf63c161cfa7fd8632f830fee9b5299f5635336`; no Context Bridge/Ledger/runtime mutation; no authority promotion.

CB-L3 closeout repaired and pushed: `CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L3_CLOSEOUT_REPAIRED_PASS_NO_MUTATION`; substantive terminal remains `CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L3_SHADOW_PROJECTION_PASS_NO_MUTATION`; final closeout status `PASS`; projection hash `f36a08cd3995e269910856f219859f2edc92bf58d469ebb28766938cbc0ccd04`; sanitizer fixtures PASS; golden parity PASS; pushed head `0fbc7d2666a76384ebc63a867c749fdc66fd6193`; no Context Bridge/Ledger/runtime mutation; no authority promotion.

CB-L4 closeout repaired and pushed: `CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L4_CLOSEOUT_REPAIRED_PASS_NO_PRODUCTION_WIRING`; substantive terminal remains `CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L4_SANITIZER_CANARY_PASS_NO_PRODUCTION_WIRING`; final closeout status `PASS`; sanitizer hash `e95b5fea8464ad655a16c01e03d865e62e113e5574897cb11329c40ddac30f3f`; fixtures `10/10` PASS; deterministic repeat hash PASS; golden parity PASS; pushed head `3cf9ca4fb8420d88a196e3d04f948bd420617a0d`; no Context Bridge/Ledger/runtime mutation; no authority promotion.

CB-L5 append-only Ledger status marker attempted preflight and is blocked: `CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5_BLOCKED_DIRTY_LIVE_CONTEXT_BRIDGE_STATE`; reason: live `sharedspace/context-bridge/actions.json` was untracked and contained raw private identifier text; no marker append occurred.

CB-L5R completed PASS: `CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5R_ACTIONS_LEDGER_REDACTION_PROVENANCE_PASS_NO_MARKER_APPEND`; it sanitized/tracked `sharedspace/context-bridge/actions.json` using one deterministic placeholder, preserved action count/status counts (`43`; `done=38`, `in_progress=5`), did not edit/append `sharedspace/context-bridge/events.jsonl`, did not append the CB-L5 marker, and did not start CB-L6/M21/M22. Final allowed Ledger scopes remain `system:memory-ledger`, `project:openclaw-runtime`, and `project:stickbot-tars`.

---

## 7. First Implementation Slice

Implemented locally:

- SQLite store;
- migrations;
- FTS;
- create/update/archive/list/history;
- event hash chain;
- M3 read-only capture `suggest` path;
- exact duplicate, update candidate, related, independent, uncertain, hold, and policy-rejected suggestion classifications;
- bounded deterministic term/tag relationship evidence;
- redaction scanner;
- JSONL recall envelope;
- doctor checks H01/H03/H05/H12/H15/H16/H17/H18/H19;
- private export/import round trip;
- sanitized export with private content redaction and event payload exclusion;
- import conflict dry-run and confirmed conflict block;
- generated projection with manifest parity, redaction gate, state/output path generation, and no `MEMORY.md` write;
- reconcile with ledger/projection parity, daily-only/ledger-only warnings, contradiction failures, context bridge warn/fail distinction, and no hidden write;
- limited internal adoption for `system:memory-ledger` using explicit confirmed local seed records, useful recall/projection, DR, rollback, and no runtime promotion;
- M10 off-by-default read-only OpenClaw-facing adapter canary for bounded `system:memory-ledger` recall packets only, fail-closed policy violations, trust boundary preservation, source-ref retention, malicious-fixture-as-data behavior, and no runtime promotion;
- M11 no-apply production readiness plan covering runtime wiring map, future enablement mechanism, environment/config diff plan, observability, mutation sentinels, scope expansion, M12 success/abort criteria, rollback proof, and operator approval checklist;
- M12 tiny canary harness `scripts/stickbot-memory-ledger-m12-canary.py`, which uses a process-local flag map only, records sanitized counters only, verifies denied-scope fail-closed behavior, and proves no ledger writes by before/after store counts and SHA256;
- M13 controlled integration plan covering candidate touchpoints, recommended first touchpoint, M14 scope, production rollout ladder, guardrail matrix, observability/evidence plan, abort criteria, rollback plan, and owner approval checklist;
- M14 operator recall command `scripts/stickbot-memory-ledger-operator-recall.py`, which is operator-only, read-only, explicit-flag/confirmation/scope gated, sanitized by default, fail-closed on denied scope/missing confirmation/missing flag, and verifies store counts/hash unchanged;
- M15 `adopt-openclaw-runtime --confirm` seed path for exactly `project:openclaw-runtime`, using source refs from existing runtime-kernel validation summaries, and read-only operator recall for exactly `system:memory-ledger` plus `project:openclaw-runtime`;
- M16 repeatability harness `scripts/stickbot-memory-ledger-m16-repeatability.py`, which repeatedly exercises the operator path for exactly the two allowed scopes and fail-closed cases while verifying counts/hash/sentinel remain unchanged;
- mutation sentinel;
- clean-room dependency scanner.

Current closeout through M16:

```text
MEMORY_LEDGER_V0_1_M16_OPERATOR_RECALL_HARDENING_REPEATABILITY_PASS_NO_AUTHORITY_PROMOTION
```

---

## 8. Validation Before Any PASS Claim

Minimum for docs/rehydrator milestone:

```bash
node projects/stickbot-memory-ledger-v0/scripts/stickbot-memory-ledger-rehydrate.mjs --status
node --check projects/stickbot-memory-ledger-v0/scripts/stickbot-memory-ledger-rehydrate.mjs
git diff --check -- projects/stickbot-memory-ledger-v0
```

Minimum for current Python implementation slice:

```bash
cd projects/stickbot-memory-ledger-v0
python3 -m unittest discover -s test -v
python3 -m compileall -q src/stickbot_memory_ledger
./scripts/stickbot-memory-ledger-cli.py --store /tmp/memory-ledger.sqlite init
./scripts/stickbot-memory-ledger-cli.py --store /tmp/memory-ledger.sqlite suggest --scope project:memory-ledger --kind note --content "Capture policy evidence smoke" --tag capture
./scripts/stickbot-memory-ledger-cli.py --store /tmp/memory-ledger.sqlite doctor
```

---

## 9. GitHub / Branch Rule

Use branch:

```text
feature/stickbot-memory-ledger-v0-1
```

Commit only project files under:

```text
projects/stickbot-memory-ledger-v0/
```

Do not stage unrelated workspace files, private state, daily memory, TARS artifacts, or runtime output.

---

## 10. If Returning Much Later

1. Fetch branch from GitHub.
2. Read latest `PROJECT_REHYDRATOR.md`.
3. Run rehydrator script.
4. Read latest generated packet.
5. Check milestone file.
6. Run validation commands.
7. Continue from first incomplete milestone.
8. Send a START/PROGRESS/PASS/HOLD update; do not work silently.
