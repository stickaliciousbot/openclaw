# Stickbot Memory Ledger v0.1 — Milestones and Gate Ledger

**Branch:** `feature/stickbot-memory-ledger-v0-1`
**Project root:** `projects/stickbot-memory-ledger-v0/`

---

## Milestone Status Summary

| Milestone | Status | Notes |
|---|---|---|
| M0 | `DESIGN_REVISED_READY_FOR_OWNER_REVIEW_NO_APPLY` | Revised v0.1 LLD persisted. |
| M0R | `MEMORY_LEDGER_V0_1_M0R_DOCS_REHYDRATOR_GITHUB_PRESERVED` | Docs, troubleshooting guide, project rehydrator, validation, and GitHub preservation PASS. |
| M1 | `PASS_UNIT_AND_CLI_SMOKE_VALIDATED` | Store bootstrap implemented; unittest + CLI smoke PASS. |
| M2 | `PASS_UNIT_AND_CLI_SMOKE_VALIDATED` | Lifecycle + event integrity implemented; unittest + CLI smoke PASS. |
| M3 | `PASS_UNIT_AND_CLI_PATH_VALIDATED` | Policy + capture evidence implemented; unittest + CLI `suggest` path PASS. |
| M4 | `PASS_UNIT_AND_CLI_SMOKE_VALIDATED` | Redaction gate implemented; unittest + CLI smoke PASS. |
| M5 | `PASS_UNIT_AND_CLI_SMOKE_VALIDATED` | Recall boundary implemented; unittest + CLI smoke PASS. |
| M6 | `PASS_UNIT_VALIDATED` | Doctor + export/import DR matrix implemented; unittest PASS. |
| M7 | `PASS_UNIT_VALIDATED_NO_MEMORY_MD_WRITE` | Generated projection implemented; manifest parity/redaction/no `MEMORY.md` write covered. |
| M8 | `PASS_UNIT_VALIDATED_NO_HIDDEN_WRITE` | Reconcile implemented; projection parity, daily/context warnings/failures, no hidden write covered. |
| M9 | `PASS_UNIT_VALIDATED_NO_RUNTIME_PROMOTION` | Limited internal adoption for `system:memory-ledger` implemented; seed/recall/projection/doctor/DR/rollback covered. |
| M10 | `PASS_UNIT_VALIDATED_NO_RUNTIME_PROMOTION` | Optional read-only OpenClaw adapter canary implemented; off by default, fail-closed, no runtime promotion. |
| M11 | `MEMORY_LEDGER_V0_1_M11_PRODUCTION_READINESS_PLAN_READY_NO_APPLY` | Production readiness/runtime enablement plan ready; no apply, no runtime mutation. |
| M12 | `MEMORY_LEDGER_V0_1_M12_TINY_PRODUCTION_READONLY_CANARY_PASS_NO_AUTHORITY_PROMOTION` | Tiny runtime-adjacent read-only canary PASS; no writes, no authority promotion, rollback/off-by-default verified. |
| M13 | `MEMORY_LEDGER_V0_1_M13_CONTROLLED_PRODUCTION_INTEGRATION_PLAN_READY_NO_APPLY` | Controlled production integration plan ready; recommended operator-only CLI/local runtime-adjacent recall for M14; no apply. |
| M14 | `MEMORY_LEDGER_V0_1_M14_OPERATOR_ONLY_PRODUCTION_READONLY_RECALL_PASS_NO_AUTHORITY_PROMOTION` | Operator-only read-only recall PASS; explicit flag/confirmation/scope required; no writes or authority promotion. |
| M15 | `MEMORY_LEDGER_V0_1_M15_OPENCLAW_RUNTIME_OPERATOR_READONLY_RECALL_PASS_NO_AUTHORITY_PROMOTION` | One approved project scope added: `project:openclaw-runtime`; controlled seed + read-only operator recall PASS; no authority promotion. |
| M16 | `MEMORY_LEDGER_V0_1_M16_OPERATOR_RECALL_HARDENING_REPEATABILITY_PASS_NO_AUTHORITY_PROMOTION` | Operator recall hardening/repeatability PASS; exact two scopes preserved; no authority promotion. |
| M17 | `MEMORY_LEDGER_V0_1_M17_STICKBOT_TARS_OPERATOR_READONLY_RECALL_PASS_NO_AUTHORITY_PROMOTION` | Second approved project scope added: `project:stickbot-tars`; controlled seed + read-only operator recall PASS; final exact three-scope allowlist; no authority promotion. |
| M18 | `MEMORY_LEDGER_V0_1_M18_PRODUCTION_RELEASE_CANDIDATE_READY_NO_APPLY` | No-apply production release-candidate/cutover readiness packet for M19; no production enablement, no new scopes, no authority promotion. |
| M19 | `MEMORY_LEDGER_V0_1_M19_CONTROLLED_PRODUCTION_ENABLEMENT_PASS_NO_AUTHORITY_PROMOTION` | Controlled production enablement of operator-only read-only recall command; canonical production store setup + bounded recalls PASS; no authority promotion. |
| M20 | `HOLD_M20_DETACHED_OBSERVER_DID_NOT_EXECUTE_CHECKS_NO_PASS_UPGRADE` | Original 24h detached observer completed without executing required M20 checks; do not upgrade M20 to PASS. |
| M20R | `MEMORY_LEDGER_V0_1_M20R_DETERMINISTIC_OBSERVER_RECOVERY_PASS_NO_AUTHORITY_PROMOTION` | Deterministic observer recovery/redo PASS using harness; all M20R_G1..G30 gates passed; no authority promotion; M21/M22 not started. |
| CB-L0/CB-L1 | `CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L1_READONLY_AUDIT_PASS_NO_MUTATION` | CB-L0 contract accepted; CB-L1 read-only inventory audit PASS; 27/27 gates passed; no bridge/Ledger/runtime mutation; pushed at `b7140146a08693d7f3d43361123d0e5622c7ccb5`. |
| CB-L2 | `CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L2_CLOSEOUT_REPAIRED_PASS_NO_MUTATION` | Authority classification + drift matrix PASS; closeout metadata repaired from UNKNOWN/omitted to explicit PASS; no mutation. |
| CB-L3 | `CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L3_CLOSEOUT_REPAIRED_PASS_NO_MUTATION` | Shadow user-facing projection PASS; closeout metadata repaired from UNKNOWN/ambiguous to explicit PASS; no production wiring; no mutation. |
| CB-L4 | `CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L4_CLOSEOUT_REPAIRED_PASS_NO_PRODUCTION_WIRING` | Presentation sanitizer canary PASS; closeout metadata repaired from UNKNOWN/projector-facing in-progress ambiguity to explicit PASS; sanitizer hash unchanged; no production wiring; no mutation. |
| CB-L5 | `CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5_BLOCKED_DIRTY_LIVE_CONTEXT_BRIDGE_STATE` | Append-only Ledger status marker blocked before append because live `actions.json` was untracked and contained raw private identifier text; no marker append performed. |
| CB-L5R | `CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5R_ACTIONS_LEDGER_REDACTION_PROVENANCE_PASS_NO_MARKER_APPEND` | Actions ledger redaction/provenance repair PASS; one raw private identifier text redacted deterministically; action count/status counts preserved; `events.jsonl` unchanged; no marker append; CB-L6/M21/M22 not started. |

---

## M0 — Revised Design Closeout

Exit: `MEMORY_LEDGER_V0_1_M0_REVISED_DESIGN_READY_NO_APPLY`

Required gates:

- M0_G1 revised plan exists.
- M0_G2 clean-room rule explicit.
- M0_G3 runtime non-mutation explicit.
- M0_G4 redaction and recall trust explicit.
- M0_G5 owner review packet ready.

Current evidence:

- `docs/STICKBOT_MEMORY_LEDGER_V0_1_REVISED_IMPROVED_PLAN.md`

Status: `PASS_DESIGN_READY_NO_APPLY`

---

## M0R — Docs, Repair Guide, Rehydrator, GitHub Preservation

Exit: `MEMORY_LEDGER_V0_1_M0R_DOCS_REHYDRATOR_GITHUB_PRESERVED`

Required gates:

- M0R_G1 troubleshooting/repair/implementation guide exists.
- M0R_G2 project rehydrator doc exists.
- M0R_G3 executable rehydrator script exists.
- M0R_G4 generated latest rehydration packet exists.
- M0R_G5 clean-room notes exist.
- M0R_G6 branch is Memory Ledger branch, not unrelated TARS branch.
- M0R_G7 only project files staged/committed.
- M0R_G8 GitHub push succeeds.
- M0R_G9 validation commands pass.

Validation commands:

```bash
node projects/stickbot-memory-ledger-v0/scripts/stickbot-memory-ledger-rehydrate.mjs --status
node --check projects/stickbot-memory-ledger-v0/scripts/stickbot-memory-ledger-rehydrate.mjs
git diff --check -- projects/stickbot-memory-ledger-v0
```

Status: `MEMORY_LEDGER_V0_1_M0R_DOCS_REHYDRATOR_GITHUB_PRESERVED`

Validation:

- `node projects/stickbot-memory-ledger-v0/scripts/stickbot-memory-ledger-rehydrate.mjs --status` PASS.
- `node --check projects/stickbot-memory-ledger-v0/scripts/stickbot-memory-ledger-rehydrate.mjs` PASS.
- `git diff --check -- projects/stickbot-memory-ledger-v0` PASS.
- GitHub branch preservation PASS through pushed branch `feature/stickbot-memory-ledger-v0-1`.

---

## M1 — Store Bootstrap

Exit: `MEMORY_LEDGER_V0_1_M1_STORE_BOOTSTRAP_PASS_NO_RUNTIME_MUTATION`

Gates:

- migration from empty pass;
- unsupported newer schema fails closed;
- `store_meta` seeded;
- WAL/FTS enabled;
- permissions checked;
- event chain genesis created;
- mutation sentinel pass.

Status: `PASS_UNIT_AND_CLI_SMOKE_VALIDATED`

Validation:

- `python3 -m unittest discover -s test -v` PASS — 5/5 tests.
- Direct CLI smoke PASS after executable wrapper mode repair.

Implementation files:

- `src/stickbot_memory_ledger/store.py`
- `src/stickbot_memory_ledger/cli.py`
- `test/test_first_slice.py`

---

## M2 — Lifecycle + Event Integrity

Exit: `MEMORY_LEDGER_V0_1_M2_LIFECYCLE_EVENT_CHAIN_PASS`

Gates:

- create/update/archive/list/history pass;
- expected revision conflict pass;
- memory row + FTS + event atomic rollback pass;
- event hash chain verifies;
- tombstone behavior pass;
- no recall of archived records by default.

Status: `PASS_UNIT_AND_CLI_SMOKE_VALIDATED`

Validation:

- `python3 -m unittest discover -s test -v` PASS — 5/5 tests.
- Direct CLI smoke PASS after executable wrapper mode repair.

Implementation files:

- `src/stickbot_memory_ledger/store.py`
- `test/test_first_slice.py`

---

## M3 — Policy + Capture Evidence

Exit: `MEMORY_LEDGER_V0_1_M3_CAPTURE_POLICY_PASS`

Gates:

- explicit remember pass;
- exact duplicate pass;
- update candidate pass;
- related pass;
- uncertain pass;
- ambiguous scope hold pass;
- policy rejected writes nothing;
- bounded evidence caps enforced.

Status: `PASS_UNIT_AND_CLI_PATH_VALIDATED`

Validation:

- `python3 -m unittest discover -s test -v` PASS — 8/8 tests.
- Unit coverage includes CLI `suggest` invocation and store-level duplicate, update candidate, related, independent, uncertain, hold, and policy rejected paths.
- External direct shell CLI smoke is approval-gated in this environment and was not required for the M3 code-path gate.

Implementation files:

- `src/stickbot_memory_ledger/store.py`
- `src/stickbot_memory_ledger/cli.py`
- `test/test_first_slice.py`

Notes:

- `suggest` is read-only: it returns capture relationship evidence and does not create memory records, events, or persisted drafts.
- Relationship evidence is bounded and deterministic; candidates require shared terms or tags, not same-kind alone.
- Policy failures return `hold` or `policy_rejected` and write nothing.

---

## M4 — Redaction Gate

Exit: `MEMORY_LEDGER_V0_1_M4_REDACTION_GATE_PASS`

Gates:

- all secret fixtures detected;
- redacted placeholders allowed;
- events/projections/exports scanned;
- report prints categories only;
- repo-bound artifact scan pass.

Status: `PASS_UNIT_AND_CLI_SMOKE_VALIDATED`

Validation:

- `python3 -m unittest discover -s test -v` PASS — 5/5 tests.
- Direct CLI smoke PASS after executable wrapper mode repair.

Implementation files:

- `src/stickbot_memory_ledger/redaction.py`
- `src/stickbot_memory_ledger/store.py`
- `test/test_first_slice.py`

---

## M5 — Recall Boundary

Exit: `MEMORY_LEDGER_V0_1_M5_RECALL_BOUNDARY_PASS`

Gates:

- JSONL one-object-per-line pass;
- begin/end boundary pass;
- no write by default pass;
- injection-like memory quoted as data pass;
- output caps pass;
- source_ref_required included but not authority;
- mixed-scope restrictions pass.

Status: `PASS_UNIT_AND_CLI_SMOKE_VALIDATED`

Validation:

- `python3 -m unittest discover -s test -v` PASS — 5/5 tests.
- Direct CLI smoke PASS after executable wrapper mode repair.

Implementation files:

- `src/stickbot_memory_ledger/store.py`
- `test/test_first_slice.py`

---

## M6 — Doctor + Export/Import DR

Exit: `MEMORY_LEDGER_V0_1_M6_DOCTOR_DR_PASS`

Gates:

- doctor clean pass;
- corruption fail;
- event chain tamper fail;
- private export/import round trip pass;
- sanitized export excludes private fields;
- import conflicts dry-run pass;
- restored temp store doctor pass.

Status: `PASS_UNIT_VALIDATED`

Validation:

- `python3 -m unittest discover -s test -v` PASS — 11/11 tests.
- Doctor clean pass covered by H01/H03/H05/H12/H15/H16/H17/H18/H19.
- Record corruption fail covered by H19 content/content-identity/record hash verification.
- Event chain tamper fail covered by H16.
- Private export/import round trip covered, including import quarantine.
- Sanitized export covered, including private content redaction and event payload exclusion.
- Import conflicts dry-run covered and confirmed import blocks on conflicts.
- Restored temp store doctor pass covered.

Implementation files:

- `src/stickbot_memory_ledger/store.py`
- `src/stickbot_memory_ledger/cli.py`
- `test/test_first_slice.py`


---

## M7 — Generated Projection

Exit: `MEMORY_LEDGER_V0_1_M7_GENERATED_PROJECTION_PASS_NO_MEMORY_MD_WRITE`

Gates:

- generated projection build pass;
- manifest parity pass;
- redaction pass;
- Git safety pass;
- `MEMORY.md` unchanged;
- project rehydrator generated only under state path.

Status: `PASS_UNIT_VALIDATED_NO_MEMORY_MD_WRITE`

Validation:

- `python3 -m unittest discover -s test -v` PASS — 13/13 tests.
- Generated projection build covered by `generate_projection`.
- Manifest parity covered via projection SHA and record line ranges.
- Redaction pass/fail covered; projection blocks artifact write on redaction failure.
- Git safety covered by state-path generation and `.gitignore` state rules.
- `MEMORY.md` unchanged covered by regression test.
- Projection output stays under caller-supplied state/output path; no runtime adapter and no `MEMORY.md` write.

Implementation files:

- `src/stickbot_memory_ledger/store.py`
- `src/stickbot_memory_ledger/cli.py`
- `test/test_first_slice.py`

---

## M8 — Reconcile

Exit: `MEMORY_LEDGER_V0_1_M8_RECONCILE_PASS`

Gates:

- ledger vs generated projection pass;
- daily-only candidate warn;
- ledger-only candidate warn;
- contradiction fail;
- context bridge drift warn/fail distinction;
- no hidden write.

Status: `PASS_UNIT_VALIDATED_NO_HIDDEN_WRITE`

Validation:

- `python3 -m unittest discover -s test -v` PASS — 17/17 tests.
- Ledger vs generated projection parity pass/fail covered.
- Daily-only candidate warning covered via `MEMORY_LEDGER_CANDIDATE:` marker.
- Ledger-only candidate warning covered when projected ledger records are not referenced in daily memory.
- Contradiction fail covered via `MEMORY_LEDGER_CONTRADICTION:` marker and projection manifest mismatch.
- Context bridge drift distinction covered: WARN/drift signals return `warn`; FAIL/contradiction signals return `fail`.
- CLI `reconcile` path covered.
- No hidden write covered by event-count regression and `memory_writes=false` report.

Implementation files:

- `src/stickbot_memory_ledger/store.py`
- `src/stickbot_memory_ledger/cli.py`
- `test/test_first_slice.py`

---

## M9 — Limited Internal Adoption

Exit: `MEMORY_LEDGER_V0_1_M9_LIMITED_ADOPTION_PASS_NO_RUNTIME_PROMOTION`

First target: `system:memory-ledger`.

Gates:

- seed 5–10 curated records;
- recall packet useful;
- projection useful;
- doctor pass;
- import/export DR pass;
- rollback tested by archiving/moving local store only;
- no runtime promotion.

Status: `PASS_UNIT_VALIDATED_NO_RUNTIME_PROMOTION`

Validation:

- `python3 -m unittest discover -s test -v` PASS — 19/19 tests.
- Seed 5–10 curated records covered by explicit confirmed local `adopt-system --confirm` path.
- Recall packet usefulness covered by `runtime` recall returning seeded `system:memory-ledger` records.
- Projection usefulness covered by generated projection containing seeded records.
- Doctor pass covered after adoption.
- Import/export DR pass covered by private export/import into restored temp store and restored doctor pass.
- Rollback covered by archiving seeded records and moving a local store file aside, then confirming fresh store has no active seeded records.
- No runtime promotion covered by adoption report and doctor mutation sentinel fields.

Implementation files:

- `src/stickbot_memory_ledger/store.py`
- `src/stickbot_memory_ledger/cli.py`
- `test/test_first_slice.py`

---

## M10 — Optional Read-Only OpenClaw Adapter Canary

Exit: `MEMORY_LEDGER_V0_1_M10_READONLY_OPENCLAW_ADAPTER_CANARY_PASS_NO_RUNTIME_PROMOTION`

Only after M1–M9 pass.

Gates:

- `M10_G1` adapter is read-only by construction;
- `M10_G2` adapter cannot create/update/archive/delete ledger records;
- `M10_G3` adapter cannot mutate Gateway/config/model/provider/runtime memory routes;
- `M10_G4` recall packet includes trust boundary and `memory_writes=false`;
- `M10_G5` scope allowlist is explicit and narrow;
- `M10_G6` malicious memory-content fixture is rendered as quoted/untrusted data only;
- `M10_G7` runtime mutation sentinel PASS before and after canary;
- `M10_G8` canary uses `system:memory-ledger` first, not broad user/project memory;
- `M10_G9` failure mode is fail-closed/no-recall, not fallback-to-unsafe-recall;
- `M10_G10` rollback is adapter disable/remove only; ledger store remains intact;
- `M10_G11` adapter is off by default;
- `M10_G12` no private state, DB files, exports, health artifacts, or projections are tracked by Git;
- `M10_G13` existing M1–M9 behavior remains green.

Status: `PASS_UNIT_VALIDATED_NO_RUNTIME_PROMOTION`

Validation:

- M10-A approval packet created: `docs/M10_READ_ONLY_OPENCLAW_ADAPTER_CANARY_APPROVAL.md`.
- M10-B adapter implemented as `src/stickbot_memory_ledger/openclaw_readonly_adapter.py`.
- Adapter flag: `STICKBOT_MEMORY_LEDGER_OPENCLAW_READONLY_CANARY=1`; disabled by default.
- Explicit allowed scope: `system:memory-ledger`.
- `python3 -m unittest discover -s test -v` PASS — 23/23 tests.
- Focused M10 tests cover disabled default, explicit flag enablement, allowed/disallowed scopes, no mutation functions, malicious fixture as untrusted data, recall boundary, `memory_writes=false`, limit enforcement, source-ref retention, runtime mutation sentinel, and M1–M9 regression.
- Runtime/Gateway/model/provider/memory-route mutation: none.

Implementation files:

- `docs/M10_READ_ONLY_OPENCLAW_ADAPTER_CANARY_APPROVAL.md`
- `src/stickbot_memory_ledger/openclaw_readonly_adapter.py`
- `src/stickbot_memory_ledger/store.py`
- `test/test_first_slice.py`

---

## M11 — Production Readiness and Runtime Enablement Plan

Exit: `MEMORY_LEDGER_V0_1_M11_PRODUCTION_READINESS_PLAN_READY_NO_APPLY`

M11 is no-apply. It plans what must be true before any future live runtime enablement of the M10 read-only adapter.

Gates:

- M11_G1 production readiness summary covers M0–M10 and why M11 is no-apply;
- M11_G2 runtime wiring map covers direct chat, Telegram direct session, Gateway/UI, hot context, project rehydrator, context bridge, tool-routing, and agent-context injection points;
- M11_G3 future adapter enablement mechanism remains off by default, explicit-flagged, scope-allowlisted, read-only, no-authority-promotion, fail-closed, and trust-boundary-preserving;
- M11_G4 future environment/config diff plan documents before/after examples and states no current changes made;
- M11_G5 observability plan uses sanitized counters/markers and does not log raw memory content by default;
- M11_G6 runtime mutation sentinel plan covers Gateway config, model/provider/fallback routes, Telegram routes, runtime memory routes, production memory authority, and ledger record hashes/counts;
- M11_G7 scope expansion policy is staged and separately approved;
- M11_G8 M12 tiny production read-only canary success criteria are defined but not implemented;
- M11_G9 abort criteria include runtime mutation, route mutation, memory write, boundary failure, authority leak, scope bypass, private-data logging, missing explicit flag, and critical doctor failure;
- M11_G10 rollback proof requires flag removal, minimal restart if required, no recall availability, clean sentinel, intact ledger store, doctor/rehydrator pass, and closeout;
- M11_G11 operator approval checklist exists;
- M11_G12 M12 is proposed but not started;
- M11_G13 existing M10 behavior remains green;
- M11_G14 no runtime/Gateway/model/provider/fallback/Telegram/production memory-route mutation occurs.

Status: `MEMORY_LEDGER_V0_1_M11_PRODUCTION_READINESS_PLAN_READY_NO_APPLY`

Validation:

- Plan artifact: `docs/M11_PRODUCTION_READINESS_AND_RUNTIME_ENABLEMENT_PLAN.md`.
- Runtime production enablement: not performed.
- Adapter default: remains off by default behind `STICKBOT_MEMORY_LEDGER_OPENCLAW_READONLY_CANARY=1`.
- M12: proposed only; not started.

Implementation files:

- `docs/M11_PRODUCTION_READINESS_AND_RUNTIME_ENABLEMENT_PLAN.md`
- `README.md`
- `docs/MILESTONES.md`
- `docs/PROJECT_REHYDRATOR.md`
- `scripts/stickbot-memory-ledger-rehydrate.mjs`

---

## M12 — Tiny Production Read-Only Canary

Exit: `MEMORY_LEDGER_V0_1_M12_TINY_PRODUCTION_READONLY_CANARY_PASS_NO_AUTHORITY_PROMOTION`

M12 is a tiny, temporary, read-only canary using the smallest safe OpenClaw-facing path: a local runtime-adjacent harness over the existing M10 adapter contract. It does not wire the adapter into Telegram, direct chat, Gateway UI, hot context, context bridge, project rehydrator surfaces, provider/model routing, or tool routing.

Gates:

- `M12_G1` Pre-canary mutation sentinel PASS / all false;
- `M12_G2` adapter confirmed off by default before canary;
- `M12_G3` canary enablement requires explicit local/operator flag;
- `M12_G4` canary scope limited to `system:memory-ledger`;
- `M12_G5` successful bounded recall packet rendered;
- `M12_G6` recall packet includes trust boundary;
- `M12_G7` recall packet includes `memory_writes=false`;
- `M12_G8` recall packet includes `instruction_authority=none`;
- `M12_G9` disallowed scope fails closed/no-recall;
- `M12_G10` malicious instruction-like memory remains untrusted quoted data;
- `M12_G11` no create/update/archive/delete/write path exercised or exposed by canary;
- `M12_G12` no usage metadata written by default;
- `M12_G13` no raw private memory content logged into tracked artifacts;
- `M12_G14` post-canary adapter disabled/off by default;
- `M12_G15` post-canary mutation sentinel PASS / all false;
- `M12_G16` doctor PASS after canary;
- `M12_G17` rehydrator PASS after canary;
- `M12_G18` full unit suite PASS;
- `M12_G19` focused M10/M12 tests PASS;
- `M12_G20` Git safety clean;
- `M12_G21` no runtime/Gateway/model/provider/fallback/Telegram/memory-route mutation;
- `M12_G22` rollback proof completed;
- `M12_G23` clean-room scan remains PASS.

Status: `MEMORY_LEDGER_V0_1_M12_TINY_PRODUCTION_READONLY_CANARY_PASS_NO_AUTHORITY_PROMOTION`

Canary path:

- `python3 scripts/stickbot-memory-ledger-m12-canary.py --store /tmp/stickbot-memory-ledger-m11-doctor.sqlite --limit 2`
- Harness uses process-local `env={STICKBOT_MEMORY_LEDGER_OPENCLAW_READONLY_CANARY: "1"}` for adapter calls only.
- Store was an existing private seeded `/tmp` ledger store; harness itself did not create/update/archive/delete/import/export/write ledger data.

Canary counts:

- recall requests: 3;
- recall successes: 3;
- fail-closed successes from normal recall loop: 0;
- scope-denied fail-closed checks: 1;
- errors: 0;
- records rendered: sanitized count only, 6;
- raw memory content logged: false;
- before/after records: 6 -> 6;
- before/after events: 7 -> 7;
- store SHA256 unchanged: true.

Validation:

- full unit suite PASS — 23/23;
- focused M10 tests PASS — 4/4;
- M12 canary harness PASS;
- Python compile PASS;
- rehydrator PASS;
- `node --check` PASS;
- doctor PASS with H15 mutation sentinel false and H17 clean-room scan pass;
- `git diff --check -- .` PASS;
- Git safety clean.

Implementation files:

- `docs/M12_TINY_PRODUCTION_READONLY_CANARY.md`
- `scripts/stickbot-memory-ledger-m12-canary.py`
- `README.md`
- `docs/MILESTONES.md`
- `docs/PROJECT_REHYDRATOR.md`
- `scripts/stickbot-memory-ledger-rehydrate.mjs`

---

## M13 — Controlled Production Integration Plan

Exit: `MEMORY_LEDGER_V0_1_M13_CONTROLLED_PRODUCTION_INTEGRATION_PLAN_READY_NO_APPLY`

M13 is no-apply. It plans the smallest safe real production touchpoint for the next separately approved integration step.

Gates:

- `M13_G1` current state summary covers M0–M12 and preserved invariants;
- `M13_G2` candidate production touchpoints assessed: direct chat local runtime context, Telegram direct session, Gateway/UI recall panel, runtime hot context, project rehydrator view, context bridge packet, operator-only CLI/local runtime-adjacent recall, and health/doctor closeout surface;
- `M13_G3` recommended first touchpoint selected: operator-only CLI / local runtime-adjacent recall surface;
- `M13_G4` integration contract requires explicit operator invocation, explicit flag, scope allowlist, read-only recall, trust boundary, `memory_writes=false`, `instruction_authority=none`, no automatic prompt inclusion, no tool authorization, no runtime mutation, and fail-closed/no-recall;
- `M13_G5` M14 proposed as `M14 — Operator-Only Production Read-Only Recall Integration`, separately approved and not started;
- `M13_G6` production rollout ladder defined from current Stage 0 through broader Stage 6 candidate;
- `M13_G7` guardrail matrix covers enforcement, validation, and abort conditions;
- `M13_G8` observability/evidence plan uses sanitized counters only by default;
- `M13_G9` abort criteria cover runtime/config/route/memory mutation, write/usage writes, boundary/authority/scope/logging failures, missing explicit flag, doctor failure, and clean-room failure;
- `M13_G10` rollback plan defined for M14;
- `M13_G11` production readiness checklist for M14 requires explicit owner approval;
- `M13_G12` M13 closeout states no M14 start and no apply;
- `M13_G13` existing M1–M12 behavior remains green;
- `M13_G14` no runtime/Gateway/model/provider/fallback/Telegram/production memory-route mutation occurs;
- `M13_G15` adapter remains off by default.

Status: `MEMORY_LEDGER_V0_1_M13_CONTROLLED_PRODUCTION_INTEGRATION_PLAN_READY_NO_APPLY`

Validation:

- Plan artifact: `docs/M13_CONTROLLED_PRODUCTION_INTEGRATION_PLAN.md`.
- Runtime production enablement: not performed.
- M14: proposed only; not started.

Implementation files:

- `docs/M13_CONTROLLED_PRODUCTION_INTEGRATION_PLAN.md`
- `README.md`
- `docs/MILESTONES.md`
- `docs/PROJECT_REHYDRATOR.md`
- `scripts/stickbot-memory-ledger-rehydrate.mjs`

---

## M14 — Operator-Only Production Read-Only Recall Integration

Exit: `MEMORY_LEDGER_V0_1_M14_OPERATOR_ONLY_PRODUCTION_READONLY_RECALL_PASS_NO_AUTHORITY_PROMOTION`

M14 adds the first controlled operator-only production read-only recall surface. It is a local runtime-adjacent CLI command, not automatic model prompt injection, Telegram integration, direct chat integration, Gateway UI integration, hot-context insertion, context bridge injection, or production memory-route promotion.

Gates:

- `M14_G1` pre-integration mutation sentinel PASS / all false;
- `M14_G2` adapter/operator surface confirmed off or inert by default;
- `M14_G3` operator invocation requires explicit confirmation;
- `M14_G4` scope limited to `system:memory-ledger`;
- `M14_G5` successful bounded operator recall rendered;
- `M14_G6` recall packet includes trust boundary;
- `M14_G7` recall packet includes `memory_writes=false`;
- `M14_G8` recall packet includes `instruction_authority=none`;
- `M14_G9` disallowed scope fails closed/no-recall;
- `M14_G10` missing confirmation fails closed/no-recall;
- `M14_G11` malicious instruction-like memory remains untrusted quoted data;
- `M14_G12` no create/update/archive/delete/write path exposed;
- `M14_G13` no usage metadata written by default;
- `M14_G14` no raw private memory content logged into tracked artifacts;
- `M14_G15` memory store records/events unchanged by recall;
- `M14_G16` store hash unchanged by recall;
- `M14_G17` post-integration mutation sentinel PASS / all false;
- `M14_G18` doctor PASS after operator test;
- `M14_G19` rehydrator PASS after operator test;
- `M14_G20` full unit suite PASS;
- `M14_G21` focused M10/M12/M14 tests PASS;
- `M14_G22` Git safety clean;
- `M14_G23` clean-room scan H17 PASS;
- `M14_G24` no runtime/Gateway/model/provider/fallback/Telegram/memory-route mutation;
- `M14_G25` rollback proof completed;
- `M14_G26` adapter remains off/default inert after test.

Status: `MEMORY_LEDGER_V0_1_M14_OPERATOR_ONLY_PRODUCTION_READONLY_RECALL_PASS_NO_AUTHORITY_PROMOTION`

Operator surface:

- `scripts/stickbot-memory-ledger-operator-recall.py`
- Required activation: `STICKBOT_MEMORY_LEDGER_OPENCLAW_READONLY_CANARY=1` plus `--confirm-readonly` plus `--scope system:memory-ledger`.
- Default output is sanitized JSON; raw recall packet and raw memory content are omitted by default.

Operator test counts:

- operator invocations: 6;
- recall successes: 3;
- fail-closed: 3;
- denied-scope: 1;
- missing-confirmation denied: 1;
- missing-flag denied: 1;
- errors: 0;
- raw memory content logged: false;
- records/events unchanged: true;
- store SHA unchanged: true.

Validation:

- full unit suite PASS;
- focused M10 tests PASS;
- focused M14 test PASS;
- M12 harness PASS;
- Python compile PASS;
- rehydrator PASS;
- `node --check` PASS;
- doctor PASS with H15 mutation sentinel false and H17 clean-room scan pass;
- `git diff --check -- .` PASS;
- Git safety clean.

Implementation files:

- `docs/M14_OPERATOR_ONLY_PRODUCTION_READONLY_RECALL.md`
- `scripts/stickbot-memory-ledger-operator-recall.py`
- `test/test_first_slice.py`
- `README.md`
- `docs/MILESTONES.md`
- `docs/PROJECT_REHYDRATOR.md`
- `scripts/stickbot-memory-ledger-rehydrate.mjs`

---

## M15 — OpenClaw Runtime Operator-Only Read-Only Recall

Exit: `MEMORY_LEDGER_V0_1_M15_OPENCLAW_RUNTIME_OPERATOR_READONLY_RECALL_PASS_NO_AUTHORITY_PROMOTION`

M15 expands the operator-only read-only recall surface to exactly one approved project scope: `project:openclaw-runtime`. M15-A performs a controlled source-ref-backed seed only because no active project records existed. M15-B proves project recall remains manual, read-only at recall time, bounded, non-authoritative, fail-closed, and off/default inert.

Gates:

- `M15_G1` pre-M15 mutation sentinel PASS / all false;
- `M15_G2` adapter/operator surface confirmed off/default inert;
- `M15_G3` project scope limited to `project:openclaw-runtime`;
- `M15_G4` project seed uses explicit confirm path;
- `M15_G5` project seed source refs/redaction/events/revisions PASS;
- `M15_G6` operator invocation requires explicit confirmation;
- `M15_G7` successful bounded `project:openclaw-runtime` recall rendered;
- `M15_G8` prior `system:memory-ledger` recall still works;
- `M15_G9` recall packet includes trust boundary;
- `M15_G10` recall packet includes `memory_writes=false`;
- `M15_G11` recall packet includes `instruction_authority=none`;
- `M15_G12` disallowed scope fails closed/no-recall;
- `M15_G13` missing confirmation fails closed/no-recall;
- `M15_G14` missing flag fails closed/no-recall;
- `M15_G15` malicious instruction-like memory remains untrusted quoted data;
- `M15_G16` no create/update/archive/delete/write path exposed through operator recall;
- `M15_G17` no usage metadata written by recall;
- `M15_G18` no raw private memory content logged into tracked artifacts;
- `M15_G19` memory store records/events unchanged by recall;
- `M15_G20` store hash unchanged by recall;
- `M15_G21` post-M15 mutation sentinel PASS / all false;
- `M15_G22` doctor PASS after seed/test;
- `M15_G23` rehydrator PASS after seed/test;
- `M15_G24` full unit suite PASS;
- `M15_G25` focused M10/M12/M14/M15 tests PASS;
- `M15_G26` Git safety clean;
- `M15_G27` clean-room scan H17 PASS;
- `M15_G28` no runtime/Gateway/model/provider/fallback/Telegram/memory-route mutation;
- `M15_G29` no authority promotion;
- `M15_G30` rollback proof completed;
- `M15_G31` adapter/operator surface remains off/default inert after test.

Status: `MEMORY_LEDGER_V0_1_M15_OPENCLAW_RUNTIME_OPERATOR_READONLY_RECALL_PASS_NO_AUTHORITY_PROMOTION`

M15-A seed:

- Existing active `project:openclaw-runtime` records before seed: 0.
- Created: 6.
- Scope: `project:openclaw-runtime`.
- Authority class: `source_ref_required`.
- Sensitivity class: `repo_sanitized`.
- Projection policy: `generated_projection_only`.
- Source refs: repo runtime-kernel validation M23/M24/M25 summary artifacts.
- Redaction: PASS.
- Doctor after seed: PASS.
- Runtime mutation: false.

Operator surface:

- `scripts/stickbot-memory-ledger-operator-recall.py`
- Required activation: `STICKBOT_MEMORY_LEDGER_OPENCLAW_READONLY_CANARY=1` plus `--confirm-readonly` plus explicit `--scope`.
- Allowed scopes: `system:memory-ledger`, `project:openclaw-runtime`.
- Default output is sanitized JSON; raw recall packet and raw memory content are omitted by default.

Operator test counts:

- operator invocations: 7;
- project recall successes: 3;
- system recall successes: 1;
- fail-closed: 3;
- denied-scope: 1;
- missing-confirmation denied: 1;
- missing-flag denied: 1;
- trust-boundary pass count: 4;
- errors: 0;
- raw memory content logged: false;
- records/events changed during recall: false;
- store SHA changed during recall: false.

Validation:

- full unit suite PASS;
- focused M10 tests PASS;
- M12 harness PASS;
- focused M14 tests PASS;
- focused M15 tests PASS;
- Python compile PASS;
- rehydrator PASS;
- `node --check` PASS;
- doctor PASS with H15 mutation sentinel false and H17/H18 pass;
- `git diff --check -- .` PASS;
- Git safety clean.

Implementation files:

- `docs/M15_OPENCLAW_RUNTIME_OPERATOR_READONLY_RECALL.md`
- `src/stickbot_memory_ledger/store.py`
- `src/stickbot_memory_ledger/cli.py`
- `src/stickbot_memory_ledger/openclaw_readonly_adapter.py`
- `scripts/stickbot-memory-ledger-operator-recall.py`
- `test/test_first_slice.py`
- `README.md`
- `docs/MILESTONES.md`
- `docs/PROJECT_REHYDRATOR.md`
- `scripts/stickbot-memory-ledger-rehydrate.mjs`

---

## M16 — Operator Recall Hardening and Repeatability

Exit: `MEMORY_LEDGER_V0_1_M16_OPERATOR_RECALL_HARDENING_REPEATABILITY_PASS_NO_AUTHORITY_PROMOTION`

M16 hardens the M14/M15 operator-only recall path for repeatable, auditable production operator use. It does not expand scope, add automatic recall, add prompt injection, add Telegram/direct-chat/Gateway UI/hot-context/context-bridge integration, or promote memory authority.

Gates:

- `M16_G1` Pre-M16 mutation sentinel PASS / all false;
- `M16_G2` allowed scopes remain exactly `system:memory-ledger` and `project:openclaw-runtime`;
- `M16_G3` operator surface confirmed off/default inert;
- `M16_G4` operator runbook created;
- `M16_G5` repeatability harness added;
- `M16_G6` repeated `system:memory-ledger` recalls rendered;
- `M16_G7` repeated `project:openclaw-runtime` recalls rendered;
- `M16_G8` recall packets include trust boundary;
- `M16_G9` recall packets include `memory_writes=false`;
- `M16_G10` recall packets include `instruction_authority=none`;
- `M16_G11` disallowed scope fails closed/no-recall;
- `M16_G12` missing confirmation fails closed/no-recall;
- `M16_G13` missing flag fails closed/no-recall;
- `M16_G14` no create/update/archive/delete/write path exposed through operator recall;
- `M16_G15` no usage metadata written by recall;
- `M16_G16` no raw private memory content logged into tracked artifacts;
- `M16_G17` memory store records/events unchanged by recall;
- `M16_G18` store hash unchanged by recall;
- `M16_G19` post-M16 mutation sentinel PASS / all false;
- `M16_G20` doctor PASS after repeatability test;
- `M16_G21` rehydrator PASS after repeatability test;
- `M16_G22` full unit suite PASS;
- `M16_G23` focused M10/M12/M14/M15/M16 tests PASS;
- `M16_G24` Git safety clean;
- `M16_G25` clean-room scan H17 PASS;
- `M16_G26` no runtime/Gateway/model/provider/fallback/Telegram/memory-route mutation;
- `M16_G27` no authority promotion;
- `M16_G28` rollback/inert proof completed;
- `M16_G29` approval-gated verification handling documented;
- `M16_G30` M17 proposed but not started.

Status: `MEMORY_LEDGER_V0_1_M16_OPERATOR_RECALL_HARDENING_REPEATABILITY_PASS_NO_AUTHORITY_PROMOTION`

Harness:

- `scripts/stickbot-memory-ledger-m16-repeatability.py`
- Default action: 3 system recalls, 3 OpenClaw runtime project recalls, denied-scope fail-closed, missing-confirmation fail-closed, missing-flag fail-closed, rollback/inert proof without flag, store count/hash verification, mutation sentinel verification, tracked artifact scan.
- Output is sanitized JSON counts/metadata only; raw recall packet and raw memory content are not logged.

Operator repeatability counts:

- total invocations: 10;
- successful recalls: 6;
- system successes: 3;
- project successes: 3;
- fail-closed: 4;
- denied-scope: 1;
- missing-confirmation: 1;
- missing-flag: 2;
- errors: 0;
- raw memory content logged: false;
- records/events changed during recall: false;
- store SHA changed during recall: false.

Validation:

- full unit suite PASS;
- focused M10 tests PASS;
- M12 harness PASS;
- focused M14 tests PASS;
- focused M15 tests PASS;
- focused M16 tests PASS;
- M16 production repeatability harness PASS;
- Python compile PASS;
- rehydrator PASS;
- `node --check` PASS;
- doctor PASS with H15 mutation sentinel false and H17/H18 pass;
- `git diff --check -- .` PASS;
- Git safety clean.

Implementation files:

- `docs/M16_OPERATOR_RECALL_HARDENING_AND_REPEATABILITY.md`
- `scripts/stickbot-memory-ledger-m16-repeatability.py`
- `test/test_first_slice.py`
- `README.md`
- `docs/MILESTONES.md`
- `docs/PROJECT_REHYDRATOR.md`
- `docs/TROUBLESHOOTING_REPAIR_AND_IMPLEMENTATION_GUIDE.md`
- `scripts/stickbot-memory-ledger-rehydrate.mjs`

---

## M17 — Stickbot-TARS Operator-Only Read-Only Recall

Exit: `MEMORY_LEDGER_V0_1_M17_STICKBOT_TARS_OPERATOR_READONLY_RECALL_PASS_NO_AUTHORITY_PROMOTION`

M17 expands operator-only read-only recall by exactly one approved scope, `project:stickbot-tars`. It keeps recall manual, local, bounded, sanitized, read-only at recall time, off/default inert without the canary flag, and non-authoritative.

Gates:

- `M17_G1` pre-M17 mutation sentinel PASS / all false;
- `M17_G2` baseline active `project:stickbot-tars` readiness inspected;
- `M17_G3` controlled seed writes used only if no active TARS records existed;
- `M17_G4` M17-A seed writes use canonical confirmed ledger path only;
- `M17_G5` seed source refs are repo/workspace sanitized docs only;
- `M17_G6` seed redaction PASS;
- `M17_G7` seed creates only `project:stickbot-tars` records;
- `M17_G8` seed metadata reports no runtime promotion or route mutation;
- `M17_G9` final allowed scopes exactly `system:memory-ledger`, `project:openclaw-runtime`, `project:stickbot-tars`;
- `M17_G10` operator surface remains explicit flag + `--confirm-readonly` gated;
- `M17_G11` `project:stickbot-tars` recall succeeds;
- `M17_G12` prior `project:openclaw-runtime` recall still succeeds;
- `M17_G13` prior `system:memory-ledger` recall still succeeds;
- `M17_G14` unapproved `project:equipmentiq` fails closed/no packet;
- `M17_G15` missing confirmation fails closed/no packet;
- `M17_G16` missing flag/off-default path fails closed/no packet;
- `M17_G17` recall packets include trust boundary;
- `M17_G18` recall packets include `memory_writes=false`;
- `M17_G19` recall packets include `instruction_authority=none`;
- `M17_G20` malicious/instruction-like memory remains untrusted stored data;
- `M17_G21` no create/update/archive/delete/write path exposed through operator recall;
- `M17_G22` no usage metadata written by recall;
- `M17_G23` no raw private memory content logged into tracked artifacts;
- `M17_G24` memory store records/events unchanged by recall;
- `M17_G25` store hash unchanged by recall;
- `M17_G26` post-M17 mutation sentinel PASS / all false;
- `M17_G27` doctor PASS after seed/recall;
- `M17_G28` rehydrator PASS;
- `M17_G29` full unit suite PASS;
- `M17_G30` focused M10/M12/M14/M15/M16/M17 checks PASS;
- `M17_G31` Git safety/private artifact scan clean;
- `M17_G32` H17 clean-room PASS;
- `M17_G33` no runtime/Gateway/model/provider/fallback/Telegram/memory-route mutation;
- `M17_G34` no authority promotion and rollback/inert proof completed.

Status: `MEMORY_LEDGER_V0_1_M17_STICKBOT_TARS_OPERATOR_READONLY_RECALL_PASS_NO_AUTHORITY_PROMOTION`

Implementation files:

- `docs/M17_STICKBOT_TARS_OPERATOR_READONLY_RECALL.md`
- `src/stickbot_memory_ledger/store.py`
- `src/stickbot_memory_ledger/cli.py`
- `src/stickbot_memory_ledger/openclaw_readonly_adapter.py`
- `scripts/stickbot-memory-ledger-operator-recall.py`
- `scripts/stickbot-memory-ledger-m16-repeatability.py`
- `test/test_first_slice.py`
- `README.md`
- `docs/MILESTONES.md`
- `docs/PROJECT_REHYDRATOR.md`
- `docs/TROUBLESHOOTING_REPAIR_AND_IMPLEMENTATION_GUIDE.md`
- `scripts/stickbot-memory-ledger-rehydrate.mjs`

---

## M18 — Production Release Candidate / Cutover Readiness

Exit: `MEMORY_LEDGER_V0_1_M18_PRODUCTION_RELEASE_CANDIDATE_READY_NO_APPLY`

M18 is a no-apply release-candidate gate. It produces the M19 cutover readiness packet and validates that existing M1-M17 behavior remains green. It does not enable production, add scopes, add automatic recall, add prompt injection, integrate Telegram/direct-chat/Gateway UI/hot-context/context-bridge, promote memory routes, or promote memory authority.

Gates:

- `M18_G1` Current branch/head recorded;
- `M18_G2` Allowed scopes remain exactly `system:memory-ledger`, `project:openclaw-runtime`, `project:stickbot-tars`;
- `M18_G3` No new scope added;
- `M18_G4` No production enablement performed;
- `M18_G5` Operator surface remains off/default inert;
- `M18_G6` Exact M19 production command contract documented;
- `M18_G7` Production host/path assumptions documented or explicitly deferred to M19 preflight;
- `M18_G8` M19 cutover checklist documented;
- `M18_G9` M19 bounded production test plan documented;
- `M18_G10` M19 rollback plan documented;
- `M18_G11` M19 observability/evidence plan documented;
- `M18_G12` Approval-gated check handling documented;
- `M18_G13` Full unit suite PASS;
- `M18_G14` Focused M10/M12/M14/M15/M16/M17 tests PASS;
- `M18_G15` M16 repeatability harness PASS;
- `M18_G16` Doctor PASS including H15/H17/H18/H19 where available;
- `M18_G17` Rehydrator PASS;
- `M18_G18` Python compile PASS;
- `M18_G19` Node syntax PASS where applicable;
- `M18_G20` Git diff check PASS;
- `M18_G21` Git safety/private artifact scan clean;
- `M18_G22` Mutation sentinel clean/all false;
- `M18_G23` No runtime/Gateway/model/provider/fallback/Telegram/memory-route mutation;
- `M18_G24` No recall-time memory writes;
- `M18_G25` No authority promotion;
- `M18_G26` M19 proposed but not started.

Status: `MEMORY_LEDGER_V0_1_M18_PRODUCTION_RELEASE_CANDIDATE_READY_NO_APPLY`

Implementation files:

- `docs/M18_PRODUCTION_RELEASE_CANDIDATE_CUTOVER_READINESS.md`
- `README.md`
- `docs/MILESTONES.md`
- `docs/PROJECT_REHYDRATOR.md`
- `docs/TROUBLESHOOTING_REPAIR_AND_IMPLEMENTATION_GUIDE.md`
- `scripts/stickbot-memory-ledger-rehydrate.mjs`
- generated rehydration artifacts

---

## M19 — Controlled Production Enablement

Exit: `MEMORY_LEDGER_V0_1_M19_CONTROLLED_PRODUCTION_ENABLEMENT_PASS_NO_AUTHORITY_PROMOTION`

M19 is the first controlled production enablement. It enables only the operator-only production read-only recall command against the canonical production store path `state/stickbot-memory-ledger/v0/memory-ledger.sqlite`. It does not add scopes, automatic recall, prompt injection, Telegram/direct-chat/Gateway UI integration, hot-context insertion, context-bridge injection, memory-route promotion, runtime/Gateway/model/provider/fallback/Telegram route mutation, or authority promotion.

Gates:

- `M19_G1` Production branch/head recorded;
- `M19_G2` Working tree clean before production test;
- `M19_G3` Production store path resolved to `state/stickbot-memory-ledger/v0/memory-ledger.sqlite`;
- `M19_G4` Canonical production store exists or is safely hydrated through explicit confirmed canonical path;
- `M19_G5` Allowed scopes remain exactly `system:memory-ledger`, `project:openclaw-runtime`, `project:stickbot-tars`;
- `M19_G6` No new scope added;
- `M19_G7` Operator surface inert without flag;
- `M19_G8` Operator surface inert without `--confirm-readonly`;
- `M19_G9` Doctor PASS before production test;
- `M19_G10` Rehydrator PASS before production test;
- `M19_G11` Mutation sentinel clean before production test;
- `M19_G12` Git safety/private artifact scan clean;
- `M19_G13` Successful bounded production recall for `system:memory-ledger`;
- `M19_G14` Successful bounded production recall for `project:openclaw-runtime`;
- `M19_G15` Successful bounded production recall for `project:stickbot-tars`;
- `M19_G16` Denied scope fails closed/no-recall;
- `M19_G17` Missing confirmation fails closed/no-recall;
- `M19_G18` Missing flag fails closed/no-recall;
- `M19_G19` Recall packets include trust boundary;
- `M19_G20` Recall packets include `memory_writes=false`;
- `M19_G21` Recall packets include `instruction_authority=none`;
- `M19_G22` No raw private memory content logged into tracked artifacts;
- `M19_G23` Store record/event counts unchanged by recall;
- `M19_G24` Store hash unchanged by recall;
- `M19_G25` Mutation sentinel clean after production test;
- `M19_G26` Doctor PASS after production test;
- `M19_G27` Rehydrator PASS after production test;
- `M19_G28` Full unit suite PASS or production-equivalent test PASS;
- `M19_G29` Focused M10/M12/M14/M15/M16/M17 tests PASS or documented production-equivalent proof;
- `M19_G30` Clean-room scan PASS;
- `M19_G31` No runtime/Gateway/model/provider/fallback/Telegram/memory-route mutation;
- `M19_G32` No recall-time memory writes;
- `M19_G33` No authority promotion;
- `M19_G34` Rollback/inert proof completed;
- `M19_G35` Adapter/operator surface remains off/default inert after test;
- `M19_G36` M20 proposed and then started as observation-only after M19 closeout; M19 still remains no-authority-promotion.

Status: `MEMORY_LEDGER_V0_1_M19_CONTROLLED_PRODUCTION_ENABLEMENT_PASS_NO_AUTHORITY_PROMOTION`

Implementation files:

- `docs/M19_CONTROLLED_PRODUCTION_ENABLEMENT.md`
- `README.md`
- `docs/MILESTONES.md`
- `docs/PROJECT_REHYDRATOR.md`
- `docs/TROUBLESHOOTING_REPAIR_AND_IMPLEMENTATION_GUIDE.md`
- `scripts/stickbot-memory-ledger-rehydrate.mjs`
- generated rehydration artifacts

## M20 — 24h Post-Production Observation / Soak

Status: `HOLD_M20_DETACHED_OBSERVER_DID_NOT_EXECUTE_CHECKS_NO_PASS_UPGRADE`

M20 was scheduled as a read-only post-production observation/soak after M19 controlled production enablement. It is not a new authority promotion.

Known state:

- Started: `2026-07-06T17:49:33+10:00`
- Earliest final eligibility: `2026-07-07T17:49:33+10:00`
- Session target: `session:m20-post-production-observation`
- Gate: `CB-L3`
- Detached observer: yes; do not infer status only from current OpenClaw session/process handles.
- Checkpoint jobs:
  - T+2h: `8980885e-fc62-44e7-897f-ccc84e2f673c`
  - T+8h: `4334fb16-e319-4ef2-a804-bb83c1eef22b`
  - T+24h final: `72b92d09-602f-4649-9bd8-df7b91d3d4ce`

Closeout finding:

- Detached cron/agent observer sessions returned generic summaries instead of executing the required M20 checks.
- M20 therefore remains HOLD and must not be upgraded to PASS.
- Correct classification: `HOLD_M20_DETACHED_OBSERVER_DID_NOT_EXECUTE_CHECKS_NO_PASS_UPGRADE`.

Safety held:

- no M22 started;
- no promotion;
- no authority promotion;
- no runtime/Gateway/model/provider/fallback/Telegram/memory-route mutation;
- no recall-time memory writes.

---

## M20R — Deterministic Observer Recovery / Redo

Status: `MEMORY_LEDGER_V0_1_M20R_DETERMINISTIC_OBSERVER_RECOVERY_PASS_NO_AUTHORITY_PROMOTION`

M20R is a recovery closeout for the invalid M20 detached observer evidence. It is not M21, not M22, not a new feature milestone, and not a production expansion.

Evidence root:

```text
sharedspace/runtime-kernel-validation/memory-ledger/m20r_deterministic_observer_recovery_20260709T1345AEST_r1/
```

Primary closeout artifact:

```text
projects/stickbot-memory-ledger-v0/docs/M20R_DETERMINISTIC_OBSERVER_RECOVERY.md
sharedspace/runtime-kernel-validation/memory-ledger/m20r_deterministic_observer_recovery_20260709T1345AEST_r1/M20R_DETERMINISTIC_OBSERVER_RECOVERY_CLOSEOUT.md
```

Required gate result:

```text
M20R_G1 .. M20R_G30: PASS
```

Validation summary:

- deterministic harness launched and wrote `run_config.json`, `launch_proof.json`, `status.json`, `summary.json`, and `evidence_manifest.json`;
- child observer executed actual M20R checks, not only cron/Telegram delivery;
- approved-scope recall success/fail-closed/error counts: `3 / 3 / 0`;
- approved scopes remain exactly `system:memory-ledger`, `project:openclaw-runtime`, `project:stickbot-tars`;
- store records/events before and after: `19/20` -> `19/20`;
- store SHA unchanged: `f50ff3836724358d2ef99d92d7c32c2c07651138a749e2a03ce5c03c512807f6`;
- doctor status: `pass`;
- rehydrator status: `PASS`;
- mutation sentinel: `PASS_ALL_FALSE`;
- no runtime/Gateway/model/provider/fallback/Telegram/memory-route mutation;
- no recall-time memory writes;
- no authority promotion;
- no raw/private artifacts created or tracked;
- M21/M22 not started.

Next step: none until separate owner approval. Do not start M21/M22 automatically.

---

## CB-L0/CB-L1 — Context Bridge ↔ Mesh ↔ Ledger Read-Only Reconciliation

Status: `CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L1_READONLY_AUDIT_PASS_NO_MUTATION`

Expected CB-L0 terminal:

```text
CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L0_BASELINE_CONTRACT_ACCEPTED_NO_APPLY
```

Expected CB-L1 terminal:

```text
CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L1_READONLY_AUDIT_PASS_NO_MUTATION
```

Scope:

- CB-L0 baseline no-apply contract acceptance.
- CB-L1 read-only inventory audit.
- No CB-L2 automatic start.
- No CB-L3/CB-L4/CB-L5/CB-L6.
- No M21/M22.

Primary docs/scripts:

```text
docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L0_L1_READONLY_AUDIT.md
projects/stickbot-memory-ledger-v0/scripts/context_bridge_ledger_l0_l1_readonly_audit.py
```

Default evidence root:

```text
state/context-bridge-ledger-audit/<run_id>/
```

Hard no-apply boundaries:

- no Context Bridge writes/action edits/event appends;
- no Ledger DB/WAL/SHM writes or record/event writes;
- no automatic Ledger recall;
- no runtime/Gateway/model/provider/fallback/Telegram/memory-route mutation;
- no authority promotion;
- no raw/private content in reports.

Closeout evidence:

```text
state/context-bridge-ledger-audit/cb-l0-l1-20260709T1413AEST-r1/
```

Closeout summary:

- CB-L1 gates: `27 / 27` PASS.
- Stable report hash: `01f85915bc4d2e9dbf7463c73fc84d2a36948644395ab5518e50521ba247e632`.
- Bridge events/actions: `113 / 43`.
- Action status counts: `done=38`, `in_progress=5`.
- Ledger records/events: `19 / 20`.
- Ledger allowed scopes: `project:openclaw-runtime`, `project:stickbot-tars`, `system:memory-ledger`.
- Ledger recall authority: `none`.
- M19/M20R represented: `true / true`.
- Raw runtime blob/presentation risk found: `true`.
- Raw/private report scan hits: `[]`.
- Bridge changed: `false`.
- Ledger changed: `false`.
- Runtime/Gateway/model/provider/fallback/Telegram/memory-route mutation: `false`.
- Authority promotion: `false`.
- Recall-time memory writes: `false`.
- CB-L2 proposed but not started: `true`.
- M21/M22 started: `false`.

---

## CB-L2 — Context Bridge ↔ Mesh ↔ Ledger Authority Classification + Drift Matrix

Status: `CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L2_CLOSEOUT_REPAIRED_PASS_NO_MUTATION`

Expected terminal:

```text
CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L2_AUTHORITY_MATRIX_PASS_NO_MUTATION
```

Scope:

- read-only authority classification;
- read-only drift matrix;
- no Context Bridge mutation;
- no Ledger mutation;
- no runtime mutation;
- no authority promotion;
- no CB-L3/CB-L4/CB-L5/CB-L6;
- no M21/M22.

Primary docs/scripts:

```text
docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L2_AUTHORITY_MATRIX.md
projects/stickbot-memory-ledger-v0/scripts/context_bridge_ledger_l2_authority_matrix.py
```

Closeout repair summary:

- Initial substantive terminal: `CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L2_AUTHORITY_MATRIX_PASS_NO_MUTATION`.
- Hold classification: `HOLD_CB_L2_CLOSEOUT_STATUS_UNKNOWN_NEEDS_REPAIR` because summary closeout metadata was omitted/ambiguous.
- Final closeout status: `PASS`.
- Repair terminal: `CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L2_CLOSEOUT_REPAIRED_PASS_NO_MUTATION`.
- Authority matrix hash unchanged: `d4d619178b4fc5a408e353c024bcec1cee004f9e04627b829522ad3c3cf4b35c`.
- Drift matrix hash unchanged: `5d2d477c725c39efe6eec35491aa135fe644fd9d3acce4e75828d8fd005e0ed9`.
- No Context Bridge/Ledger/runtime mutation; no authority promotion; no CB-L3/M21/M22.

---

## CB-L3 — Context Bridge ↔ Mesh ↔ Ledger Shadow User-Facing Projection

Status: `CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L3_CLOSEOUT_REPAIRED_PASS_NO_MUTATION`

Expected terminal:

```text
CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L3_SHADOW_PROJECTION_PASS_NO_MUTATION
```

Scope:

- read-only shadow user-facing projection;
- sanitized operator/user-facing continuity summary;
- no production wiring;
- no Telegram presentation change;
- no Context Bridge mutation;
- no Ledger mutation;
- no runtime mutation;
- no authority promotion;
- no CB-L4/CB-L5/CB-L6;
- no M21/M22.

Primary docs/scripts:

```text
docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L3_SHADOW_PROJECTION.md
projects/stickbot-memory-ledger-v0/scripts/context_bridge_ledger_l3_shadow_projection.py
```

Closeout repair summary:

- Initial substantive terminal: `CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L3_SHADOW_PROJECTION_PASS_NO_MUTATION`.
- Hold classification: `HOLD_CB_L3_CLOSEOUT_STATUS_UNKNOWN_NEEDS_REPAIR` because closeout presentation was ambiguous/UNKNOWN.
- Final closeout status: `PASS`.
- Repair terminal: `CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L3_CLOSEOUT_REPAIRED_PASS_NO_MUTATION`.
- Projection hash unchanged: `f36a08cd3995e269910856f219859f2edc92bf58d469ebb28766938cbc0ccd04`.
- Sanitizer fixtures remain PASS; golden parity remains PASS.
- No Context Bridge/Ledger/runtime mutation; no authority promotion; no CB-L4/M21/M22.

---

## CB-L5 / CB-L5R — Context Bridge Actions Provenance Boundary

CB-L5 append-only Ledger status marker remains blocked until Context Bridge `actions.json` has clean provenance.

CB-L5 block status:

```text
CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5_BLOCKED_DIRTY_LIVE_CONTEXT_BRIDGE_STATE
```

CB-L5R terminal:

```text
CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5R_ACTIONS_LEDGER_REDACTION_PROVENANCE_PASS_NO_MARKER_APPEND
```

CB-L5R repaired only `sharedspace/context-bridge/actions.json` by replacing raw private identifier text with deterministic placeholders of the form:

```text
redacted:chat_account_message_id:<short_sha256>
```

No raw-to-redacted mapping is committed. `sharedspace/context-bridge/events.jsonl` remained unchanged; no CB-L5 marker append occurred during CB-L5R. Action count/status counts were preserved (`43`; `done=38`, `in_progress=5`). Context Bridge remains projection/dashboard state, not authority. Ledger remains operator-only manual read-only recall, not automatic runtime authority.

---

## CB-L4 — Context Bridge ↔ Mesh ↔ Ledger Presentation Sanitizer Canary

Status: `CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L4_CLOSEOUT_REPAIRED_PASS_NO_PRODUCTION_WIRING`

Substantive terminal:

```text
CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L4_SANITIZER_CANARY_PASS_NO_PRODUCTION_WIRING
```

Repair terminal:

```text
CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L4_CLOSEOUT_REPAIRED_PASS_NO_PRODUCTION_WIRING
```

Closeout status: `PASS`

Repair classification resolved: `HOLD_CB_L4_CLOSEOUT_STATUS_UNKNOWN_NEEDS_REPAIR`

Scope/result:

- test-harness-only presentation sanitizer canary PASS;
- no production wiring;
- no Telegram delivery/presentation change;
- no Context Bridge mutation;
- no Ledger mutation;
- no runtime mutation;
- no authority promotion;
- no CB-L5/CB-L6;
- no M21/M22.

Primary docs/scripts:

```text
docs/CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L4_SANITIZER_CANARY.md
projects/stickbot-memory-ledger-v0/scripts/context_bridge_ledger_l4_sanitizer_canary.py
```

Final evidence root: `state/context-bridge-ledger-audit/cb-l4-20260709T1552AEST-final/`.

Final sanitizer hash: `e95b5fea8464ad655a16c01e03d865e62e113e5574897cb11329c40ddac30f3f`.

Fixture results: `10` pass / `0` fail. Golden parity: PASS. Repeat deterministic hash: PASS.

---

## Closeout Record Template

```text
STATUS:
Milestone:
Branch:
Commit:
Validation:
Artifacts:
Runtime mutation:
Next step:
```
