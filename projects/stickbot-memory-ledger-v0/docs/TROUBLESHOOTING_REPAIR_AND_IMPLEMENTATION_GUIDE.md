# Stickbot Memory Ledger v0.1 — Troubleshooting, Repair, and Detailed Implementation Guide

**Status:** `GUIDE_READY_NO_APPLY`
**Scope:** Local Memory Ledger implementation, validation, recovery, and rehydration.
**Non-scope:** Gateway/runtime/model/provider route mutation; production `MEMORY.md` writes; production OpenClaw adapter activation without later explicit approval.

---

## 1. Purpose

This guide exists so a future Stickbot session can immediately continue implementation, diagnose failures, repair local state, and preserve evidence without relying on fragile chat history.

Use this guide with:

- `docs/STICKBOT_MEMORY_LEDGER_V0_1_REVISED_IMPROVED_PLAN.md`
- `docs/PROJECT_REHYDRATOR.md`
- `docs/MILESTONES.md`
- generated packet: `artifacts/rehydration/stickbot-memory-ledger/latest.md`

---

## 2. Golden Rules

1. **Do not mutate OpenClaw runtime authority.** No Gateway config, provider route, model fallback, Telegram/Gmail hook, or production memory-route changes.
2. **Do not write `MEMORY.md` in v0.1.** Projection files only.
3. **Do not copy Nuzo code.** Nuzo is design inspiration only; implementation must be Stickbot-native.
4. **Treat memory as untrusted data.** Recall packets never become system/developer/user instructions.
5. **Redaction is a hard gate.** Raw chat IDs, message IDs, account IDs, auth headers, tokens, keys, cookies, and private identifiers must not appear in records/events/health/projections/sanitized exports.
6. **Archive is default forget.** Hard deletion is not a v0.1 default.
7. **Expected revision is mandatory for updates.** No silent retry after revision conflict.
8. **Source refs do not grant authority.** Source refs support review; actions must still obey current instructions and source-authority gates.

---

## 3. File and Directory Map

Recommended project root:

```text
projects/stickbot-memory-ledger-v0/
```

Design and docs:

```text
docs/STICKBOT_MEMORY_LEDGER_V0_1_REVISED_IMPROVED_PLAN.md
docs/TROUBLESHOOTING_REPAIR_AND_IMPLEMENTATION_GUIDE.md
docs/PROJECT_REHYDRATOR.md
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
```

Current first-slice implementation:

```text
pyproject.toml
src/stickbot_memory_ledger/__init__.py
src/stickbot_memory_ledger/constants.py
src/stickbot_memory_ledger/util.py
src/stickbot_memory_ledger/redaction.py
src/stickbot_memory_ledger/store.py
src/stickbot_memory_ledger/cli.py
src/stickbot_memory_ledger/openclaw_readonly_adapter.py
scripts/stickbot-memory-ledger-cli.py
test/test_first_slice.py
```

Future modules may still be split further as the implementation grows:

```text
src/stickbot_memory_ledger/capture.py
src/stickbot_memory_ledger/relationships.py
src/stickbot_memory_ledger/projection.py
src/stickbot_memory_ledger/reconcile.py
src/stickbot_memory_ledger/mutation_sentinel.py
```

Local generated runtime state, private by default:

```text
state/stickbot-memory-ledger/v0/memory-ledger.sqlite
state/stickbot-memory-ledger/v0/exports/private/
state/stickbot-memory-ledger/v0/exports/sanitized/
state/stickbot-memory-ledger/v0/health/
state/stickbot-memory-ledger/v0/projections/
state/stickbot-memory-ledger/v0/reconcile/
```

Rehydration artifacts:

```text
projects/stickbot-memory-ledger-v0/artifacts/rehydration/stickbot-memory-ledger/latest.md
projects/stickbot-memory-ledger-v0/artifacts/rehydration/stickbot-memory-ledger/latest.json
```

---

## 4. Build Order

### Slice A — M1/M2/M4/M5-partial

Implement first:

1. Project package scaffold.
2. SQLite store and migration bootstrap.
3. `store_meta`, `schema_migrations`, `memory_records`, `memory_events`.
4. FTS table.
5. Event hash chain genesis.
6. Lifecycle operations: create/update/archive/list/history.
7. Expected-revision conflict handling.
8. Redaction scanner.
9. JSONL recall boundary.
10. Doctor checks: H01/H03/H05/H12/H15/H16/H17/H18.
11. Private export/import round trip.
12. Rehydrator update.

Do **not** implement projection-to-`MEMORY.md` or OpenClaw runtime adapter in this slice.

### Slice B — M3

Status: implemented in the first local slice.

Capture suggestion and relationship evidence now cover:

- exact duplicate;
- update candidate;
- related;
- independent;
- uncertain when same-scope search is non-exhaustive;
- ambiguous scope hold;
- policy rejected;
- bounded deterministic term/tag evidence;
- no persisted drafts by default.

Operational rule: `suggest` is read-only. It must not insert memory records, append events, or create durable drafts. Same-kind alone is not relationship evidence; candidates require shared terms or tags.

### Slice C — M6/M7/M8

M6 status: implemented in the local slice.

M6 doctor/DR now covers:

- doctor clean pass;
- SQLite quick check;
- event chain tamper fail;
- record content/content-identity/record-hash corruption fail;
- private export/import round trip;
- import quarantine to `authority_class=forbidden_as_authority`;
- sanitized export that excludes private content and event payloads;
- import conflict dry-run and confirmed import conflict block;
- restored temp store doctor pass.

M7 status: implemented in the local slice.

M7 generated projection now covers:

- generated projection build;
- manifest parity via projection hash and record line ranges;
- redaction pass/fail before artifact write;
- state/output path generation only;
- no `MEMORY.md` write;
- no runtime adapter.

M8 status: implemented in the local slice.

M8 reconcile now covers:

- ledger vs generated projection manifest parity;
- projection SHA/redaction verification;
- daily-only candidate warnings via `MEMORY_LEDGER_CANDIDATE:` markers;
- ledger-only candidate warnings when projected records are not referenced in daily memory;
- contradiction failures via `MEMORY_LEDGER_CONTRADICTION:` markers and projection manifest mismatches;
- context bridge WARN/drift vs FAIL/contradiction distinction;
- no hidden write.

### Slice D — M9/M10

M9 status: implemented in the local slice.

M9 limited adoption now covers:

- explicit confirmed local `adopt-system --confirm` seed for `system:memory-ledger`;
- 5–10 curated records about Memory Ledger boundaries, recall trust, projection, validation, and runtime-promotion constraints;
- useful recall and projection from the seeded records;
- doctor/export/import DR pass;
- rollback by archiving seeded records or moving the local store file aside;
- no runtime promotion.

M10 status: implemented in the local slice as an off-by-default no-promotion canary.

M10 read-only adapter canary now covers:

- no-apply approval packet in `docs/M10_READ_ONLY_OPENCLAW_ADAPTER_CANARY_APPROVAL.md`;
- feature flag `STICKBOT_MEMORY_LEDGER_OPENCLAW_READONLY_CANARY=1` required for any packet rendering;
- explicit narrow scope allowlist: `system:memory-ledger`;
- fail-closed/no-recall on disabled flag, missing store, missing scope, disallowed scope, invalid boundary, or recall exception;
- existing recall renderer reuse rather than a separate authority format;
- no exposed create/update/archive/delete surface;
- malicious memory fixture remains quoted/untrusted stored data;
- source-ref-required record retains source pointer;
- runtime mutation sentinel fields remain false before/after canary;
- no Gateway/model/provider/runtime memory-route mutation.

Remaining Slice D work requires separate owner approval:

- any runtime enablement outside local tests;
- any scope expansion beyond `system:memory-ledger`;
- any production canary or monitoring integration.

---

## 5. Health Checks to Keep Green

Minimum first-slice doctor checks:

| ID | Check | Repair if failing |
|---|---|---|
| H01 | schema version | Stop; inspect migration. Do not auto-upgrade unsupported newer schema. |
| H03 | SQLite integrity | Restore from last private export or backup; do not continue writes. |
| H05 | redaction | Quarantine offending record/export/projection; repair with redacted placeholder; rerun scanner. |
| H12 | recall envelope | Disable recall output path until JSONL boundary and no-write guarantee pass. |
| H15 | mutation sentinel | Abort; inspect touched files; revert any Gateway/model/provider/runtime mutation. |
| H16 | event hash chain | Stop writes; locate first broken event; restore or append repair event only after owner review. |
| H17 | clean-room dependency | Remove Nuzo dependency/import/source/test artifact; document repair. |
| H18 | Git safety | Remove private DB/export from index; update `.gitignore`; verify no private artifact tracked. |
| H19 | record hash/content integrity | Stop writes; inspect content/content hash/identity hash/record hash mismatch; restore from private export or owner-reviewed repair packet. |

---

## 6. Common Failure Modes and Repairs

### 6.1 Schema migration failed

Symptoms:

- `MEMORY_LEDGER_SCHEMA_UNSUPPORTED`
- missing table/index
- migration partial state

Repair:

1. Stop all ledger writes.
2. Copy DB to private local quarantine path.
3. Run SQLite integrity check.
4. Inspect `store_meta` and `schema_migrations`.
5. If migration failed mid-transaction, store should be unchanged; rerun after code fix.
6. If store is inconsistent, restore from last private export/backup.
7. Add regression test before retry.

Never silently downgrade a newer schema.

### 6.2 Redaction failure

Symptoms:

- H05 `FAIL_REDACTION`
- sanitized export blocked
- projection blocked

Repair:

1. Do not print the matched secret fragment.
2. Identify category and affected record IDs only.
3. Archive/repair affected record with redacted placeholder.
4. Append `redaction_repaired` event with metadata only.
5. Rerun doctor.
6. Confirm generated artifacts contain no raw private identifiers.

### 6.3 Event hash chain broken

Symptoms:

- H16 `FAIL_EVENT_CHAIN`
- event hash mismatch

Repair:

1. Stop writes.
2. Locate first broken event.
3. Compare DB to latest private export or backup.
4. If corruption is accidental and backup exists, restore.
5. If no backup exists, create a repair report and owner-review packet.
6. Do not rewrite event history without explicit owner approval.

### 6.3a Record hash/content integrity broken

Symptoms:

- H19 failure;
- `content_sha256`, `normalized_identity_sha256`, or `record_sha256` mismatch;
- content changed outside ledger APIs.

Repair:

1. Stop writes.
2. Identify the first broken record ID from H19 detail.
3. Compare against the latest private export/backup.
4. Restore from known-good private export when available.
5. If no backup exists, create an owner-review repair packet; do not silently recompute hashes over tampered content.

### 6.4 Recall boundary failure

Symptoms:

- recall output lacks boundary markers;
- content creates fake JSONL lines;
- `memory_writes` absent or true;
- archived records appear by default.

Repair:

1. Disable runtime-facing recall path.
2. Fix JSON escaping and one-object-per-line renderer.
3. Add regression fixture using malicious instruction-like memory.
4. Rerun H12.

### 6.4a M10 read-only adapter canary failure

Symptoms:

- adapter returns `fail_closed` unexpectedly;
- packet boundary lacks `memory_writes=false` or `instruction_authority=none`;
- disallowed scopes render records;
- mutation sentinel changes from false;
- adapter exposes mutation-capable functions.

Repair:

1. Keep `STICKBOT_MEMORY_LEDGER_OPENCLAW_READONLY_CANARY` unset outside focused local tests.
2. Do not add runtime integration while repairing M10.
3. Verify requested scopes are exactly allowlisted and include `system:memory-ledger` first.
4. Confirm the adapter calls `MemoryLedger.recall_jsonl` and does not invent a new recall authority format.
5. If runtime mutation sentinel changes, abort with `MEMORY_LEDGER_V0_1_M10_BLOCKED_RUNTIME_MUTATION_DETECTED`.
6. Add/repair focused tests before re-running the full suite.

### 6.5 Clean-room failure

Symptoms:

- Nuzo package in dependency tree;
- Nuzo source/test/schema filename copied;
- implementation imports Nuzo.

Repair:

1. Remove dependency/import/file.
2. Rewrite code/test independently from this Stickbot plan.
3. Update `docs/CLEAN_ROOM_NOTES.md` with conceptual-only reference note if needed.
4. Rerun H17.

### 6.6 Git safety failure

Symptoms:

- private DB/export tracked;
- `state/stickbot-memory-ledger/v0/exports/private/` in Git;
- private-local record content in sanitized artifact.

Repair:

1. Remove file from index.
2. Add/verify `.gitignore` rules.
3. If pushed, treat as incident and rotate any exposed credentials if applicable.
4. Regenerate sanitized artifacts.
5. Rerun H18 and sanitized-export tests.

### 6.7 Mutation sentinel failure

Symptoms:

- Gateway config diff;
- provider/model route diff;
- production memory-route file changed;
- Telegram/Gmail hook changed.

Repair:

1. Abort ledger task.
2. Capture diff for owner review.
3. Revert mutation unless explicitly owner-approved for a separate milestone.
4. Rerun H15.
5. Do not mark Memory Ledger milestone PASS until sentinel is clean.

### 6.8 Capture suggestion false positive

Symptoms:

- `suggest` classifies unrelated records as `related` or `update_candidate`;
- same-kind records are matched without shared content/tag evidence;
- returned candidates exceed bounded evidence caps.

Repair:

1. Confirm `suggest` remains read-only by comparing `memory_events` count before/after.
2. Require shared deterministic terms or tags before returning a candidate.
3. Keep `same_kind` as a strengthener only after actual evidence exists.
4. Cap evaluated candidates and returned evidence.
5. Add/extend regression tests for duplicate, update candidate, related, independent, uncertain, hold, and policy-rejected paths.

### 6.9 Generated projection failure

Symptoms:

- projection body/manifest redaction failure;
- manifest record count or line ranges do not match projection;
- projection writes outside the state/output path;
- `MEMORY.md` changes during projection.

Repair:

1. Abort projection closeout; do not write to `MEMORY.md`.
2. Fix projection generation to write only under the caller-provided output/state directory.
3. Regenerate projection and manifest together.
4. Verify projection SHA, manifest record count, and record line ranges.
5. Add/extend tests for redaction-blocked projection, manifest parity, and unchanged `MEMORY.md`.

### 6.10 Reconcile failure or unexpected warning

Symptoms:

- `R01_PROJECTION_PARITY` fail;
- daily-only or ledger-only candidate warning;
- `R04_CONTRADICTION` fail;
- context bridge drift unexpectedly escalates to fail;
- reconcile appends events or writes records.

Repair:

1. Treat reconcile as read-only; if event count changes, abort and fix before continuing.
2. Regenerate projection from the current ledger before investigating parity failures.
3. For daily-only warnings, review `MEMORY_LEDGER_CANDIDATE:` lines and either capture explicitly or leave as warning.
4. For ledger-only warnings, decide whether the ledger record should be projected, archived, or linked in daily/project notes.
5. For contradiction failures, stop and create an owner-review packet; do not auto-repair records.
6. For context bridge FAIL/contradiction signals, inspect the bridge event before marking M8 PASS.

### 6.11 Limited adoption rollback

Symptoms:

- seeded `system:memory-ledger` records need to be rolled back;
- adoption was run against the wrong local store;
- seeded recall/projection is not useful.

Repair:

1. Do not mutate OpenClaw runtime routes or `MEMORY.md`.
2. Prefer archive rollback: list seeded `system:memory-ledger` records and archive them with expected revisions.
3. If the whole local store is disposable, stop the ledger process and move the local store file aside as a rollback artifact.
4. Re-run doctor on the remaining/restored store.
5. If seed content is wrong, update the seed list and rerun tests; do not silently edit production memory files.

---

## 7. Detailed Implementation Guidance

### 7.1 IDs

Use Stickbot-native IDs, e.g.:

```text
mem_<timestamp>_<short-random>
evt_<timestamp>_<short-random>
src_<timestamp>_<short-random>
mlh_<timestamp>_<short-random>
```

Avoid copying another project’s ID generator.

### 7.2 Event hash

Hash canonical event fields excluding `event_hash` itself:

```text
event_hash = sha256(previous_event_hash + canonical_json(event_without_event_hash))
```

Genesis event has `previous_event_hash=null`.

### 7.3 Record hash

Hash normalized record fields that define durable state:

- id;
- revision;
- status;
- scope;
- kind;
- trust_level;
- authority_class;
- sensitivity_class;
- content_sha256;
- source_ref_id;
- tags_json;
- supersession fields.

Do not include transient timestamps in `normalized_identity_sha256`.

### 7.4 Redaction scanner

Prefer high-confidence regexes and category-only output. Never print the matched value in test logs or doctor reports.

### 7.5 Transactions

Write operations must commit atomically:

```text
memory row + FTS update + event append + hash chain update
```

If event append fails, memory row must roll back.

### 7.6 Recall renderer

Always use JSON serialization. Never manually concatenate unescaped content into JSONL.

### 7.7 Import quarantine

Imported records default to:

```text
authority_class=forbidden_as_authority
confirmation_state=approved_import
```

until reviewed and updated.

---

## 8. M15 OpenClaw Runtime Operator Recall Recovery

M15 adds exactly one approved project recall scope:

```text
project:openclaw-runtime
```

Allowed operator scopes after M15:

```text
system:memory-ledger
project:openclaw-runtime
```

The operator recall command must remain explicit and inert by default:

```bash
STICKBOT_MEMORY_LEDGER_OPENCLAW_READONLY_CANARY=1 \
python3 scripts/stickbot-memory-ledger-operator-recall.py \
  --store <store> \
  --scope project:openclaw-runtime \
  --query "runtime memory route" \
  --limit 2 \
  --confirm-readonly
```

If project records are missing, use only the explicit seed command:

```bash
./scripts/stickbot-memory-ledger-cli.py \
  --store <store> \
  adopt-openclaw-runtime \
  --source-root <repo-root> \
  --confirm
```

Seed invariants:

- creates only `project:openclaw-runtime` records;
- uses `source_ref_required` records with repo summary source refs;
- redaction must pass;
- doctor must pass after seed;
- runtime/Gateway/model/provider/fallback/Telegram/memory-route mutation must remain false.

Operator recall rollback:

- remove the env flag or omit `--confirm-readonly`;
- command must fail closed/no-recall;
- no restart is required.

Seed rollback:

- archive each seeded `project:openclaw-runtime` record with its expected revision;
- do not hard-delete by default;
- run doctor after rollback.

Example archive rollback command:

```bash
./scripts/stickbot-memory-ledger-cli.py --store <store> archive --id <record_id> --expected-revision 1 --confirm
```

---

## 9. M16 Operator Repeatability Recovery

M16 adds a repeatability harness without adding any new runtime surface:

```bash
python3 scripts/stickbot-memory-ledger-m16-repeatability.py --store <store> --limit 2
```

Expected PASS invariants:

- allowed scopes remain exactly `system:memory-ledger` and `project:openclaw-runtime`;
- at least 3 successful `system:memory-ledger` recalls;
- at least 3 successful `project:openclaw-runtime` recalls;
- denied scope fails closed/no-recall;
- missing confirmation fails closed/no-recall;
- missing flag fails closed/no-recall;
- recall packets preserve trust boundary;
- `memory_writes=false`;
- `instruction_authority=none`;
- store records/events unchanged;
- store hash unchanged;
- mutation sentinel before/after all false;
- no raw recall packet or raw memory content in tracked artifacts;
- adapter/operator inert without the flag.

If the harness blocks because the store is missing, do not create a production store implicitly. Use an existing validation/production operator store, or run the explicit M9/M15 seed commands only when separately approved for that store.

If a required executable check is approval-gated and no current-milestone prior result exists, stop with:

```text
MEMORY_LEDGER_V0_1_M16_BLOCKED_REPEATABILITY_NOT_ESTABLISHED
```

If mutation, write, or authority leakage is detected, stop with the relevant abort status:

```text
MEMORY_LEDGER_V0_1_M16_ABORT_RUNTIME_MUTATION_DETECTED
MEMORY_LEDGER_V0_1_M16_ABORT_RECALL_MEMORY_WRITE_DETECTED
MEMORY_LEDGER_V0_1_M16_ABORT_RECALL_AUTHORITY_LEAK
```

Do not force duplicate approval-gated executable checks merely for cosmetic verification. Report the gating honestly and use source-level confirmation only when the same behavior was already validated in the current milestone.

---

## 10. M17 Stickbot-TARS Operator Recall Recovery

M17 adds exactly one additional approved project recall scope:

```text
project:stickbot-tars
```

Allowed operator scopes after M17:

```text
system:memory-ledger
project:openclaw-runtime
project:stickbot-tars
```

If TARS records are missing, use only the explicit source-ref-backed seed command:

```bash
./scripts/stickbot-memory-ledger-cli.py \
  --store <store> \
  adopt-stickbot-tars \
  --source-root /home/stickai/.openclaw/workspace \
  --confirm
```

Seed invariants:

- creates only `project:stickbot-tars` records;
- uses `source_ref_required` records with sanitized Stickbot-TARS source refs;
- redaction must pass;
- doctor must pass after seed;
- runtime/Gateway/model/provider/fallback/Telegram/memory-route mutation must remain false;
- seed writes are distinct from recall-time reads.

Operator recall command:

```bash
STICKBOT_MEMORY_LEDGER_OPENCLAW_READONLY_CANARY=1 \
python3 scripts/stickbot-memory-ledger-operator-recall.py \
  --store <store> \
  --scope project:stickbot-tars \
  --query "prosody canonical text" \
  --limit 2 \
  --confirm-readonly
```

M17 repeatability harness expectations:

- successful recalls for all three approved scopes;
- denied unapproved `project:equipmentiq` fails closed/no-recall;
- missing confirmation and missing flag fail closed/no-recall;
- store record/event counts and SHA unchanged by recall;
- raw recall packets and raw memory content omitted from tracked artifacts;
- adapter/operator remains inert without the flag.

Abort statuses:

```text
MEMORY_LEDGER_V0_1_M17_ABORT_RUNTIME_MUTATION_DETECTED
MEMORY_LEDGER_V0_1_M17_ABORT_RECALL_MEMORY_WRITE_DETECTED
MEMORY_LEDGER_V0_1_M17_ABORT_RECALL_AUTHORITY_LEAK
MEMORY_LEDGER_V0_1_M17_BLOCKED_SAFE_PROJECT_SCOPE_RECALL_NOT_ESTABLISHED
MEMORY_LEDGER_V0_1_M17A_BLOCKED_PROJECT_SCOPE_SEED_NOT_SAFE
```

---

## 11. M18 Production Release-Candidate / Cutover Readiness Recovery

M18 is a no-apply release-candidate gate. It must never enable production by itself.

M18 closeout status:

```text
MEMORY_LEDGER_V0_1_M18_PRODUCTION_RELEASE_CANDIDATE_READY_NO_APPLY
```

Primary M18 artifact:

```text
docs/M18_PRODUCTION_RELEASE_CANDIDATE_CUTOVER_READINESS.md
```

M18 recovery rules:

- Allowed scopes remain exactly `system:memory-ledger`, `project:openclaw-runtime`, `project:stickbot-tars`.
- Do not add new scopes.
- Do not enable production.
- Do not persist the canary flag globally.
- Do not add automatic recall, prompt injection, Telegram/direct-chat/Gateway UI integration, hot-context insertion, context-bridge injection, memory-route promotion, or authority promotion.
- M19 production host/path values must be verified in M19 preflight; do not guess them in M18.

M19 may proceed only after separate owner approval and only after checking the go/no-go list in the M18 packet.

M18 abort statuses:

```text
MEMORY_LEDGER_V0_1_M18_ABORT_RUNTIME_MUTATION_DETECTED
MEMORY_LEDGER_V0_1_M18_ABORT_RECALL_MEMORY_WRITE_DETECTED
MEMORY_LEDGER_V0_1_M18_ABORT_RECALL_AUTHORITY_LEAK
MEMORY_LEDGER_V0_1_M18_BLOCKED_CUTOVER_READINESS_NOT_ESTABLISHED
```

---

## 12. M19 Controlled Production Enablement Recovery

M19 enables only the operator-only production read-only recall command against the canonical production store:

```text
state/stickbot-memory-ledger/v0/memory-ledger.sqlite
```

M19 closeout status:

```text
MEMORY_LEDGER_V0_1_M19_CONTROLLED_PRODUCTION_ENABLEMENT_PASS_NO_AUTHORITY_PROMOTION
```

Primary M19 artifact:

```text
docs/M19_CONTROLLED_PRODUCTION_ENABLEMENT.md
```

M19 recovery rules:

- Do not track the production store, WAL/SHM files, private exports, raw recall logs, health reports, or private projections.
- The process-local flag must remain per invocation only; do not persist it globally.
- Operator recall must still require `--confirm-readonly`.
- Allowed scopes remain exactly `system:memory-ledger`, `project:openclaw-runtime`, `project:stickbot-tars`.
- If rollback is needed, stop using/unset the process-local flag and confirm missing-flag/missing-confirmation calls fail closed/no packet.
- No restart is required unless a future production host behavior proves otherwise.

M19 abort statuses:

```text
MEMORY_LEDGER_V0_1_M19_ABORT_RUNTIME_MUTATION_DETECTED
MEMORY_LEDGER_V0_1_M19_ABORT_RECALL_MEMORY_WRITE_DETECTED
MEMORY_LEDGER_V0_1_M19_ABORT_RECALL_AUTHORITY_LEAK
MEMORY_LEDGER_V0_1_M19_BLOCKED_SAFE_PRODUCTION_ENABLEMENT_NOT_ESTABLISHED
MEMORY_LEDGER_V0_1_M19_BLOCKED_PRODUCTION_STORE_NOT_READY
```

---

## 13. M20 / M20R Detached Observer Recovery

If a long-running detached cron/agent observer reports `ok` or delivers Telegram output, do not treat that as semantic milestone PASS by itself. Inspect whether the observer actually executed the required checks and wrote semantic closeout artifacts.

M20 closeout classification after reconciliation:

```text
HOLD_M20_DETACHED_OBSERVER_DID_NOT_EXECUTE_CHECKS_NO_PASS_UPGRADE
```

Use M20R when M20 detached observer evidence is invalid because the detached observer returned generic summaries or otherwise failed to execute the required checks.

M20R terminal PASS status:

```text
MEMORY_LEDGER_V0_1_M20R_DETERMINISTIC_OBSERVER_RECOVERY_PASS_NO_AUTHORITY_PROMOTION
```

M20R abort statuses:

```text
MEMORY_LEDGER_V0_1_M20R_ABORT_OBSERVER_DID_NOT_EXECUTE_CHECKS
MEMORY_LEDGER_V0_1_M20R_ABORT_RUNTIME_MUTATION_DETECTED
MEMORY_LEDGER_V0_1_M20R_ABORT_RECALL_MEMORY_WRITE_DETECTED
MEMORY_LEDGER_V0_1_M20R_ABORT_AUTHORITY_PROMOTION_DETECTED
```

Required recovery pattern:

1. Use the deterministic observer harness, not a free-form detached agent prompt.
2. Prove the harness wrote `run_config.json`, `launch_proof.json`, `status.json`, `summary.json`, and `evidence_manifest.json`.
3. Prove the child observer executed actual M20R checks and wrote semantic artifacts.
4. Use the canonical production store path from the worktree root:

```text
state/stickbot-memory-ledger/v0/memory-ledger.sqlite
```

5. Run bounded operator-only read-only recalls for exactly:

```text
system:memory-ledger
project:openclaw-runtime
project:stickbot-tars
```

6. Verify fail-closed behavior for denied scope, missing canary flag, and missing `--confirm-readonly`.
7. Verify store records/events and SHA are unchanged before/after recall.
8. Verify doctor PASS, rehydrator PASS, mutation sentinel all false, git/private-artifact scan clean, no authority promotion, and M21/M22 not started.
9. Do not track raw recall packets, private DB/WAL/SHM files, tokens/auth headers, raw chat/account/message IDs, pycache/pyc, or temp state files.

M20R R1 known-good evidence root:

```text
sharedspace/runtime-kernel-validation/memory-ledger/m20r_deterministic_observer_recovery_20260709T1345AEST_r1/
```

Known-good result summary:

- recall success/fail-closed/error counts: `3 / 3 / 0`;
- store records/events unchanged: `19 / 20` before and after;
- store SHA unchanged: `f50ff3836724358d2ef99d92d7c32c2c07651138a749e2a03ce5c03c512807f6`;
- doctor `pass`;
- rehydrator `PASS`;
- mutation sentinel `PASS_ALL_FALSE`;
- no runtime/Gateway/model/provider/fallback/Telegram/memory-route mutation;
- no recall-time memory writes;
- no authority promotion;
- no raw/private artifacts created or tracked.

---

## 14. Context Bridge ↔ Mesh ↔ Ledger CB-L0/CB-L1 Read-Only Audit Recovery

CB-L0/CB-L1 is a no-apply reconciliation lane after accepted M20R. It observes Context Bridge and Ledger state without mutating either system.

Expected terminals:

```text
CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L0_BASELINE_CONTRACT_ACCEPTED_NO_APPLY
CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L1_READONLY_AUDIT_PASS_NO_MUTATION
```

Audit script:

```text
projects/stickbot-memory-ledger-v0/scripts/context_bridge_ledger_l0_l1_readonly_audit.py
```

Default evidence root:

```text
state/context-bridge-ledger-audit/<run_id>/
```

Required artifacts:

```text
run_config.json
status.json
summary.json
audit_report.json
audit_report.md
evidence_manifest.json
```

Read-only inputs:

```text
sharedspace/context-bridge/events.jsonl
sharedspace/context-bridge/actions.json
state/stickbot-memory-ledger/v0/memory-ledger.sqlite
projects/stickbot-memory-ledger-v0/artifacts/rehydration/stickbot-memory-ledger/latest.json
projects/stickbot-memory-ledger-v0/artifacts/rehydration/stickbot-memory-ledger/latest.md
selected daily memory anchors
MEMORY.md
```

Hard rules:

- Do not write Context Bridge files.
- Do not edit Context Bridge actions.
- Do not append bridge events.
- Do not write Ledger DB/WAL/SHM or Ledger records/events.
- Do not run automatic Ledger recall.
- Do not mutate runtime/Gateway/model/provider/fallback/Telegram/memory-route config.
- Do not promote authority.
- Do not start CB-L2 automatically.
- Do not start CB-L3/CB-L4/CB-L5/CB-L6 or M21/M22.
- Do not include unsanitized Ledger recall packets, unsanitized memory/bridge dumps, raw chat/account/message IDs, tokens/auth headers, private DB contents, pycache/pyc, or temp files in tracked artifacts.

Abort statuses:

```text
CONTEXT_BRIDGE_LEDGER_RECONCILIATION_ABORT_BRIDGE_MUTATION_DETECTED
CONTEXT_BRIDGE_LEDGER_RECONCILIATION_ABORT_LEDGER_WRITE_DETECTED
CONTEXT_BRIDGE_LEDGER_RECONCILIATION_ABORT_RAW_PRIVATE_CONTENT_DETECTED
CONTEXT_BRIDGE_LEDGER_RECONCILIATION_ABORT_AUTHORITY_PROMOTION_DETECTED
CONTEXT_BRIDGE_LEDGER_RECONCILIATION_ABORT_RUNTIME_ROUTE_MUTATION_DETECTED
```

Required recovery checks before committing:

1. Confirm current branch is `feature/stickbot-memory-ledger-v0-1`.
2. Confirm input before/after hashes are recorded and unchanged.
3. Confirm all `CBL1_G1` through `CBL1_G27` gates pass.
4. Confirm `closeoutStatus` is explicit and not `UNKNOWN`.
5. Confirm reports are sanitized with a private/raw scan.
6. Confirm evidence manifest includes artifact paths and hashes.
7. Confirm `git diff --check -- .` passes.
8. Confirm no DB/WAL/SHM/private/raw/temp/pycache artifacts are staged.
9. Commit only docs/script/tests/prompt-intake/safe owner-facing artifacts if CB-L1 passes.
10. Do not push until owner asks for preservation push.

---

## 15. Context Bridge ↔ Mesh ↔ Ledger CB-L2 Authority Matrix Recovery

CB-L2 is a no-apply authority classification and drift matrix after accepted/pushed CB-L1. It observes cross-system state and writes sanitized reports only under `state/context-bridge-ledger-audit/<run_id>/`.

Expected terminal:

```text
CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L2_AUTHORITY_MATRIX_PASS_NO_MUTATION
```

Authority matrix script:

```text
projects/stickbot-memory-ledger-v0/scripts/context_bridge_ledger_l2_authority_matrix.py
```

Required artifacts:

```text
run_config.json
status.json
summary.json
authority_matrix.json
authority_matrix.md
drift_matrix.json
drift_matrix.md
evidence_manifest.json
```

Hard rules:

- Do not write Context Bridge files.
- Do not edit Context Bridge actions.
- Do not append bridge events.
- Do not write Ledger DB/WAL/SHM or Ledger records/events.
- Do not write daily memory or `MEMORY.md`.
- Do not run automatic Ledger recall.
- Do not mutate runtime/Gateway/model/provider/fallback/Telegram/memory-route config.
- Do not promote authority.
- Do not start CB-L3/CB-L4/CB-L5/CB-L6 or M21/M22.
- Do not track audit reports under `state/context-bridge-ledger-audit/` unless separately approved.

Required checks before committing:

1. Confirm CB-L1 pushed baseline head is current.
2. Confirm all read-only input hashes/mtimes are recorded and unchanged.
3. Confirm all `CBL2_G1` through `CBL2_G30` gates pass.
4. Confirm authority matrix/drift matrix stable hashes match a repeat run, excluding timestamp/run-id fields.
5. Confirm findings, recommendations, and proposed actions are separate, and proposed actions are explicitly `no_apply`.
6. Confirm no raw/private content in reports or tracked files.
7. Confirm evidence manifest includes artifact paths and hashes.
8. Confirm no DB/WAL/SHM/private/raw/temp/pycache artifacts are staged.
9. Commit only docs/script/tests/prompt-intake/safe rehydrator updates if CB-L2 passes.
10. Do not push until owner asks.

---

## 16. Context Bridge ↔ Mesh ↔ Ledger CB-L3 Shadow Projection Recovery

CB-L3 is a read-only shadow user-facing projection. It generates a sanitized operator/user-facing continuity summary without changing production output.

Expected terminal:

```text
CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L3_SHADOW_PROJECTION_PASS_NO_MUTATION
```

Shadow projection script:

```text
projects/stickbot-memory-ledger-v0/scripts/context_bridge_ledger_l3_shadow_projection.py
```

Required artifacts:

```text
run_config.json
status.json
summary.json
shadow_projection.json
shadow_projection.md
sanitizer_fixture_results.json
golden_parity.json
safety_report.json
evidence_manifest.json
```

Hard rules:

- Do not wire shadow output into production.
- Do not change Telegram presentation.
- Do not write Context Bridge files.
- Do not edit Context Bridge actions.
- Do not append bridge events.
- Do not write Ledger DB/WAL/SHM or Ledger records/events.
- Do not write daily memory or `MEMORY.md`.
- Do not run automatic Ledger recall.
- Do not mutate runtime/Gateway/model/provider/fallback/Telegram/memory-route config.
- Do not promote authority.
- Do not start CB-L4/CB-L5/CB-L6 or M21/M22.
- Do not track shadow reports under `state/context-bridge-ledger-audit/` unless separately approved.

Required checks before committing:

1. Confirm CB-L2 pushed head `fcf63c161cfa7fd8632f830fee9b5299f5635336` is current.
2. Confirm all read-only input hashes/mtimes are recorded and unchanged.
3. Confirm all `CBL3_G1` through `CBL3_G31` gates pass.
4. Confirm repeat run produces a stable projection hash, excluding timestamp/run-id fields.
5. Confirm sanitizer fixtures pass and raw runtime/internal blobs are reduced to safe labels.
6. Confirm golden parity preserves CB-L1/CB-L2 counts/statuses.
7. Confirm no raw/private content in reports or tracked files.
8. Confirm no DB/WAL/SHM/private/raw/temp/pycache artifacts are staged.
9. Commit only docs/script/tests/safe rehydrator updates if CB-L3 passes.
10. Do not push until owner asks.

---

## 17. Context Bridge ↔ Mesh ↔ Ledger CB-L5R Actions Ledger Redaction / Provenance Repair

CB-L5 append-only Ledger status marker must not run until live Context Bridge provenance is clean.

Block status:

```text
CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5_BLOCKED_DIRTY_LIVE_CONTEXT_BRIDGE_STATE
```

Repair target:

```text
CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5R_ACTIONS_LEDGER_REDACTION_PROVENANCE_PASS_NO_MARKER_APPEND
```

Repair script:

```text
projects/stickbot-memory-ledger-v0/scripts/context_bridge_actions_l5r_redact_provenance.py
```

Rules:

- Use `--dry-run` first; it must not write files.
- Use `--confirm-repair` only after dry-run passes.
- Repair may write only `sharedspace/context-bridge/actions.json`.
- Do not edit or append `sharedspace/context-bridge/events.jsonl`.
- Do not append the CB-L5 Ledger marker in CB-L5R.
- Do not commit raw private identifiers or raw-to-redacted mappings.
- Deterministic placeholders must use `redacted:chat_account_message_id:<short_sha256>`.
- Preserve action count and action status counts.
- Preserve non-sensitive action semantics.
- Verify events hash/count unchanged.
- Verify Ledger hash/counts unchanged.
- Verify runtime/Gateway/model/provider/fallback/Telegram/memory-route mutation false.
- Verify authority promotion false.
- Do not start CB-L6/M21/M22.

If raw private identifiers remain after repair, stop with:

```text
CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5R_ABORT_RAW_PRIVATE_IDENTIFIER_REMAINS
```

If action semantics change unexpectedly, stop with:

```text
CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5R_ABORT_ACTION_SEMANTICS_CHANGED
```

If `events.jsonl` changes, stop with:

```text
CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5R_ABORT_EVENTS_MUTATION_DETECTED
```

---

## 18. Context Bridge ↔ Mesh ↔ Ledger CB-L4 Sanitizer Canary Recovery

CB-L4 is a test-harness-only presentation sanitizer canary. It proves noisy/raw Context Bridge/runtime digest material can be reduced into Telegram-safe/user-facing summaries without production wiring.

Expected terminal:

```text
CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L4_SANITIZER_CANARY_PASS_NO_PRODUCTION_WIRING
```

Canary script:

```text
projects/stickbot-memory-ledger-v0/scripts/context_bridge_ledger_l4_sanitizer_canary.py
```

Required artifacts:

```text
run_config.json
status.json
summary.json
sanitizer_canary_report.json
sanitizer_canary_report.md
fixture_results.json
golden_parity.json
safety_report.json
evidence_manifest.json
```

Hard rules:

- Do not wire canary output into production.
- Do not change Telegram delivery or presentation.
- Do not write Context Bridge files.
- Do not edit Context Bridge actions.
- Do not append bridge events.
- Do not write Ledger DB/WAL/SHM or Ledger records/events.
- Do not write daily memory or `MEMORY.md`.
- Do not run automatic Ledger recall.
- Do not mutate runtime/Gateway/model/provider/fallback/Telegram/memory-route config.
- Do not promote authority.
- Do not start CB-L5/CB-L6 or M21/M22.
- Do not track canary reports under `state/context-bridge-ledger-audit/` unless separately approved.

Required checks before committing:

1. Confirm CB-L3 pushed head `0fbc7d2666a76384ebc63a867c749fdc66fd6193` is current.
2. Confirm all read-only input hashes/mtimes are recorded and unchanged.
3. Confirm all `CBL4_G1` through `CBL4_G35` gates pass.
4. Confirm repeat run produces a stable sanitizer hash, excluding timestamp/run-id fields.
5. Confirm 10 fixture categories pass.
6. Confirm golden parity preserves CB-L3 counts/statuses/classifications.
7. Confirm no raw/private content in reports or tracked files.
8. Confirm no DB/WAL/SHM/private/raw/temp/pycache artifacts are staged.
9. Commit only docs/script/tests/safe rehydrator updates if CB-L4 passes.
10. Do not push until owner asks.

---

## 19. Rehydration Procedure After Crash/New Session

1. Read `docs/PROJECT_REHYDRATOR.md`.
2. Run:

```bash
node projects/stickbot-memory-ledger-v0/scripts/stickbot-memory-ledger-rehydrate.mjs --status
```

3. Read generated:

```text
projects/stickbot-memory-ledger-v0/artifacts/rehydration/stickbot-memory-ledger/latest.md
```

4. Confirm branch and Git state:

```bash
git status --short --branch
```

5. Resume from `docs/MILESTONES.md` latest incomplete milestone.
6. Do not continue implementation if H15/H17/H18 are failing.

---

## 20. GitHub Preservation Rule

Milestones, docs, and rehydrator updates should be committed to the Memory Ledger feature branch:

```text
feature/stickbot-memory-ledger-v0-1
```

Keep repo clean by staging only project-specific files under:

```text
projects/stickbot-memory-ledger-v0/
```

Do not stage unrelated workspace memory, runtime state, generated private DBs, or other project artifacts.

---

## 21. Closeout Format

Every significant milestone should close with:

```text
STATUS: <PASS|FAIL|HOLD|ABORT>
Milestone: <Mx>
Branch: feature/stickbot-memory-ledger-v0-1
Commit: <sha or pending>
Validation: <commands + PASS/FAIL>
Artifacts: <paths + hashes>
Runtime mutation: none / explain
Next step: <one concrete next action>
```
