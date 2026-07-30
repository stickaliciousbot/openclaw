# Critical Apply Observer — Low-Level Design, Contract, and Build Plan

Date: 2026-07-30
Owner context: Stick / Stickbot OpenClaw runtime operations
Status: DESIGN CONTRACT — no production mutation authorized by this document

## 0. Non-negotiable global rule

No critical production apply/deploy/install/recovery/runtime mutation may be governed by a foreground chat/session process or raw foreground approval exec.

Foreground turns may:

- prepare evidence;
- generate a transaction plan;
- ask Stick for approval;
- read observer status/final reports.

Foreground turns must not:

- run the mutation directly;
- be the only observer;
- decide recovery from live stdout only;
- combine apply/install, restart, and functional smoke;
- continue after session loss without durable transaction receipts.

If the critical apply runner does not exist or fails its own gates, stop at architecture/prep.

---

## 1. Scope

### 1.1 Critical apply definition

A task is a **critical apply** if it mutates, installs, repairs, restarts, rolls back, activates, migrates, or materially touches any of:

- OpenClaw global npm package;
- OpenClaw installed runtime/dist;
- Gateway service lifecycle;
- Gateway config or routes;
- cron jobs/state where protected writers may be affected;
- protected memory / context bridge / ledger;
- model routing/provider auth/delivery surface;
- anything whose failure can wedge replies or require package/service recovery.

### 1.2 Initial implementation target

Milestone 1 implementation target is OpenClaw global npm package apply/recovery only:

- install exact checksum-pinned OpenClaw package;
- detect npm/package failure;
- restore/reinstall package from verified fresh restore point;
- never restart unless invoked as a separate restart transaction;
- never run provider/Telegram/Gmail/delivery smoke unless separately authorized.

---

## 2. Design goals

1. **Durable over conversational.** Transaction truth lives in files, not chat output.
2. **Restore before risk.** A fresh restore point is mandatory before mutation.
3. **Observer owns recovery.** The observer, not foreground chat, determines npm/package health and invokes restore when authorized.
4. **Small mutation boundaries.** Apply/install, restart, and functional smoke are separate transactions.
5. **Receipt every transition.** Every phase writes a receipt before and after mutation.
6. **Automatic fail-safe.** If npm/package base is missing/empty/incomplete after failure, observer restores from verified fresh restore point if authority permits.
7. **No hidden deletion.** `.openclaw-*` staging dirs are never deleted automatically and are only moved/quarantined if process references prove inactive.
8. **Rehydration-safe.** A fresh session can classify the transaction from files alone.

---

## 3. Deliverables

### 3.1 Code deliverables

```text
scripts/critical_apply_observer_runner.py
scripts/critical_apply_contracts.py
scripts/critical_apply_plugins/__init__.py
scripts/critical_apply_plugins/openclaw_npm_package.py
scripts/critical_apply_plugins/filesystem_restore.py
scripts/critical_apply_plugins/gateway_restart.py        # later milestone
scripts/critical_apply_check.py
scripts/test_critical_apply_runner.py
scripts/test_openclaw_npm_package_plugin.py
```

### 3.2 Documentation deliverables

```text
sharedspace/runtime-kernel-validation/critical-apply/CRITICAL_APPLY_OBSERVER_LOW_LEVEL_DESIGN_AND_BUILD_PLAN_20260730.md
sharedspace/runtime-kernel-validation/critical-apply/CRITICAL_APPLY_CONTRACT.md
sharedspace/runtime-kernel-validation/critical-apply/CRITICAL_APPLY_OPERATOR_RUNBOOK.md
```

### 3.3 Evidence root convention

```text
/home/stickai/.openclaw/artifacts/critical-apply/<transaction-id>/
```

Transaction ID format:

```text
critical-apply-<scope>-<YYYYMMDDTHHMMSSZ>-<short-random>
```

Example:

```text
critical-apply-openclaw-npm-package-20260730T061500Z-a1b2c3
```

---

## 4. Low-level component design

## 4.1 `critical_apply_contracts.py`

Purpose: typed schemas, constants, and validators shared by runner/plugins/tests.

### Core enums

```python
class CriticalApplyPhase(str, Enum):
    INIT = "INIT"
    LOCK_ACQUIRED = "LOCK_ACQUIRED"
    SCOPE_CLASSIFIED = "SCOPE_CLASSIFIED"
    RESTORE_POINT_VERIFIED = "RESTORE_POINT_VERIFIED"
    RESTORE_POINT_CREATED = "RESTORE_POINT_CREATED"
    PRECHECK_PASS = "PRECHECK_PASS"
    ARMED = "ARMED"
    APPROVAL_SEEN = "APPROVAL_SEEN"
    APPLY_STARTING = "APPLY_STARTING"
    APPLY_RUNNING = "APPLY_RUNNING"
    APPLY_EXITED = "APPLY_EXITED"
    POSTCHECK_RUNNING = "POSTCHECK_RUNNING"
    RECOVERY_DECIDING = "RECOVERY_DECIDING"
    RECOVERY_RUNNING = "RECOVERY_RUNNING"
    FINAL = "FINAL"
```

```python
class CriticalApplyTerminal(str, Enum):
    NO_APPROVAL = "NO_APPROVAL"
    APPROVED_NOT_STARTED = "APPROVED_NOT_STARTED"
    STARTED_NO_EXIT = "STARTED_NO_EXIT"
    EXITED_UNVERIFIED = "EXITED_UNVERIFIED"
    PASS = "PASS"
    FAIL_SAFE_NO_MUTATION = "FAIL_SAFE_NO_MUTATION"
    FAIL_MUTATION_PARTIAL = "FAIL_MUTATION_PARTIAL"
    ROLLBACK_REQUIRED = "ROLLBACK_REQUIRED"
    ROLLBACK_PASS = "ROLLBACK_PASS"
    ROLLBACK_FAIL_OPERATOR_REQUIRED = "ROLLBACK_FAIL_OPERATOR_REQUIRED"
    RECOVERED_WITH_WARNING = "RECOVERED_WITH_WARNING"
    HOLD_FOR_SEPARATE_RESTART = "HOLD_FOR_SEPARATE_RESTART"
    HOLD_FOR_SEPARATE_FUNCTIONAL_SMOKE = "HOLD_FOR_SEPARATE_FUNCTIONAL_SMOKE"
```

```python
class NpmBaseClassification(str, Enum):
    NPM_BASE_MISSING = "NPM_BASE_MISSING"
    NPM_BASE_EMPTY = "NPM_BASE_EMPTY"
    NPM_BASE_INCOMPLETE = "NPM_BASE_INCOMPLETE"
    NPM_BASE_COHERENT = "NPM_BASE_COHERENT"
    NPM_BASE_UNKNOWN = "NPM_BASE_UNKNOWN"
```

```python
class StagingDirClassification(str, Enum):
    NONE = "NONE"
    LIVE_REFERENCED_LEAVE_UNTOUCHED = "LIVE_REFERENCED_LEAVE_UNTOUCHED"
    INACTIVE_CAN_QUARANTINE = "INACTIVE_CAN_QUARANTINE"
    SUSPICIOUS_BLOCK = "SUSPICIOUS_BLOCK"
```

### Validators

- `validate_transaction_json(path)`
- `validate_receipt(path, schema_name)`
- `validate_no_forbidden_mutations(pre, post, scope)`
- `validate_manifest_non_circular(root)`
- `validate_argv_exact(actual, expected)`
- `validate_restore_point_fresh(created_at, max_age_seconds=3600)`

Hard requirement: validators must fail closed and produce machine-readable reasons.

---

## 4.2 `critical_apply_observer_runner.py`

Purpose: durable state machine and process supervisor.

### CLI shape

```bash
critical_apply_observer_runner.py prepare --spec <apply-spec.json>
critical_apply_observer_runner.py execute --transaction <id>
critical_apply_observer_runner.py status --transaction <id>
critical_apply_observer_runner.py recover --transaction <id>
critical_apply_observer_runner.py final-report --transaction <id>
critical_apply_observer_runner.py validate --transaction <id>
```

### Responsibilities

1. Create transaction directory.
2. Acquire maintenance lock.
3. Load plugin.
4. Verify or create restore point.
5. Run precheck.
6. Write approval boundary artifact.
7. After approval receipt exists, execute apply argv as child process group.
8. Write `apply-start.json` before exec.
9. Stream stdout/stderr to files.
10. Write heartbeat receipts.
11. On child exit or timeout, run plugin postcheck.
12. If apply failed or postcheck is unsafe, invoke plugin recovery decision.
13. If authorized, invoke plugin recovery action.
14. Write final report.
15. Release lock.

### Process supervision details

- Use `subprocess.Popen(..., start_new_session=True)`.
- Capture child PID and process group.
- Write `apply-start.json` before the process is allowed to mutate when possible. For commands where mutation begins immediately, write receipt immediately before `Popen` and include monotonic timestamp.
- Write heartbeats every 5–15 seconds while child runs.
- On timeout, record timeout, send SIGTERM to process group, wait bounded interval, then SIGKILL if necessary.
- Never discard stdout/stderr; write to `logs/apply.stdout.log` and `logs/apply.stderr.log`.
- All runner exceptions must write `runner-error.json` and attempt a status/final classification.

### Maintenance lock

Lock path:

```text
/home/stickai/.openclaw/locks/critical-apply.lock
```

Receipt:

```json
{
  "schema": "critical_apply.lock.v1",
  "transaction_id": "...",
  "lock_path": "...",
  "pid": 123,
  "acquired_at": "...",
  "hostname": "...",
  "stale_lock_policy": "manual_only"
}
```

Hard rule: no stale-lock auto-break in v1.

---

## 4.3 Transaction directory contract

Every transaction directory must contain:

```text
transaction.json
scope.json
approval-boundary.json
restore-point.json
precheck.json
apply-start.json                 # if apply started
heartbeat.jsonl
apply-exit.json                  # if child exited or was killed
postcheck.json
recovery-decision.json
recovery-action.json             # if recovery performed
final-report.json
hard-gates.json
evidence-manifest.json
evidence-manifest.sha256
logs/apply.stdout.log
logs/apply.stderr.log
logs/observer.log
```

### `transaction.json`

```json
{
  "schema": "critical_apply.transaction.v1",
  "transaction_id": "critical-apply-openclaw-npm-package-...",
  "created_at_utc": "...",
  "phase": "PRECHECK_PASS",
  "terminal": null,
  "critical": true,
  "plugin": "openclaw_npm_package",
  "scope_sha256": "...",
  "apply_argv_sha256": "...",
  "restore_policy": {"max_age_seconds": 3600, "create_if_missing": true},
  "restart_in_scope": false,
  "functional_smoke_in_scope": false,
  "forbidden": ["gateway_restart", "provider_call", "cron_mutation"]
}
```

### `approval-boundary.json`

Must be produced before asking Stick for approval.

```json
{
  "schema": "critical_apply.approval_boundary.v1",
  "transaction_id": "...",
  "requires_owner_approval": true,
  "approval_mode": "allow-once-or-explicit-phrase",
  "allowed_mutations": ["openclaw_package_root", "npm_bin_link", "npm_metadata", "transaction_evidence"],
  "forbidden_mutations": ["gateway_restart", "cron_mutation", "protected_memory", "provider_call", "functional_smoke"],
  "exact_apply_argv": ["/usr/bin/npm", "install", "-g", "--offline", "...tgz"],
  "apply_argv_sha256": "...",
  "restore_point_verified": true,
  "precheck_pass": true,
  "operator_text": "Approve transaction <id> only if this exact boundary is acceptable."
}
```

### `apply-start.json`

```json
{
  "schema": "critical_apply.apply_start.v1",
  "transaction_id": "...",
  "started_at_utc": "...",
  "monotonic_start_ns": 123,
  "argv": ["/usr/bin/npm", "install", "-g", "--offline", "...tgz"],
  "argv_sha256": "...",
  "cwd": "/home/stickai/.openclaw/workspace",
  "pid": 12345,
  "process_group_id": 12345,
  "stdout_path": "logs/apply.stdout.log",
  "stderr_path": "logs/apply.stderr.log",
  "mutation_boundary": "openclaw_npm_package_install_only"
}
```

### `final-report.json`

```json
{
  "schema": "critical_apply.final_report.v1",
  "transaction_id": "...",
  "terminal": "HOLD_FOR_SEPARATE_RESTART",
  "safe_to_continue": false,
  "operator_action_required": "approve separate restart transaction if desired",
  "mutation_performed": true,
  "recovery_performed": false,
  "restart_performed": false,
  "functional_smoke_performed": false,
  "hard_gates_passed": true,
  "warnings": [],
  "next_allowed_transactions": ["controlled_gateway_restart", "functional_smoke"]
}
```

---

## 4.4 `openclaw_npm_package.py` plugin

Purpose: OpenClaw npm package-specific authority/precheck/apply postcheck/recovery logic.

### Plugin interface

```python
class CriticalApplyPlugin(Protocol):
    def verify_or_create_restore_point(self, tx: Transaction) -> RestorePointResult: ...
    def precheck(self, tx: Transaction) -> PrecheckResult: ...
    def postcheck(self, tx: Transaction, apply_exit: ApplyExit | None) -> PostcheckResult: ...
    def decide_recovery(self, tx: Transaction, post: PostcheckResult) -> RecoveryDecision: ...
    def recover(self, tx: Transaction, decision: RecoveryDecision) -> RecoveryActionResult: ...
    def final_classify(self, tx: Transaction) -> FinalClassification: ...
```

### Repurposed functions

From restore script SHA `282b52ac57dc96d89ac7b3661a1cbf63fd1d8d55c19570449bd0d79da972baf8`:

- `verify_package_authority` → `PackageAuthority.verify()`
- `verify_rollback_authority` → `RestorePoint.verify()`
- `inspect_package` → `PackageRootInspector.inspect()`
- `inspect_speech_surface` → `SpeechSurfaceInspector.inspect()`
- `inspect_listener_and_service` → `GatewayProcessInspector.inspect()`
- `.openclaw-*` block in `checksum_pinned_reinstall` → `NpmStagingInspector.inspect()`
- incomplete-root preservation → `PackageRootPreserver.preserve_incomplete_root()`
- `package_only_rollback` → `RestorePoint.restore_package_only()`
- `classify_generation_and_decide` → `OpenClawNpmDecision.classify()`

### Package authority contract

Inputs:

```json
{
  "package_path": "/path/openclaw-2026.5.7.tgz",
  "expected_sha256": "09510...",
  "expected_version": "2026.5.7",
  "expected_source_commit": "c01c063...",
  "authority_manifest_path": "/path/evidence_manifest.json",
  "authority_manifest_sha256": "..."
}
```

Checks:

- package exists, regular file, not symlink;
- SHA matches exactly;
- tar path safety: no absolute paths, no `..`, no unsafe symlinks/hardlinks;
- root package is `openclaw` and version matches;
- build/source commit matches;
- package contains required critical surfaces or plugin knows how to validate after install.

Hard fail if any check fails.

### Restore point contract

Restore point can be created or selected.

For OpenClaw npm package v1, restore point includes:

- archive/copy of current official package root;
- npm CLI link state;
- npm package metadata relevant to global prefix;
- package-root inventory manifest;
- current Gateway process identity;
- `.openclaw-*` sibling inventory;
- strict `jobs.json` SHA;
- protected writer run-log SHA/size;
- protected memory SHA set if adjacent/in scope;
- restore boundary.

Restore point must be newer than 3600 seconds at apply start.

### NPM base health contract

`PackageRootInspector.inspect()` returns:

```json
{
  "classification": "NPM_BASE_COHERENT",
  "root_exists": true,
  "root_type": "directory",
  "entry_count": 44848,
  "critical_files": {
    "package.json": true,
    "openclaw.mjs": true,
    "dist/index.js": true,
    "dist/extensions/speech-core/runtime-api.js": true
  },
  "package_surface_complete": true,
  "speech_surface_complete": true,
  "source_commit_matches": true,
  "version_matches": true
}
```

Classification rules:

- missing root → `NPM_BASE_MISSING`;
- root dir exists with zero or near-zero package content → `NPM_BASE_EMPTY`;
- critical files missing or package parse invalid → `NPM_BASE_INCOMPLETE`;
- required files/import chain/source/version pass → `NPM_BASE_COHERENT`;
- conflicting evidence → `NPM_BASE_UNKNOWN` and fail closed.

### Staging dir inspection contract

`NpmStagingInspector.inspect()` checks sibling directories matching `.openclaw-*`.

For each staging dir:

```json
{
  "path": "/home/stickai/.npm-global/lib/node_modules/.openclaw-hVrJrege",
  "name_pattern_valid": true,
  "direct_child_of_node_modules": true,
  "type": "directory",
  "live_references": {
    "maps": ["pid 36075 ... vec0.so"],
    "fd": [],
    "cwd": [],
    "exe": [],
    "cmdline": []
  },
  "classification": "LIVE_REFERENCED_LEAVE_UNTOUCHED"
}
```

Hard rules:

- live-referenced staging dirs are never moved or deleted;
- inactive dirs may be preserved/quarantined only if needed and only within transaction evidence;
- symlink/suspicious staging path blocks automatic recovery.

### Recovery decision contract

If apply exits nonzero or postcheck finds package not coherent:

1. Inspect official package root.
2. Inspect `.openclaw-*` staging dirs and process references.
3. Verify restore point still fresh and complete.
4. Decide:

| Official root | Restore point | Staging refs | Decision |
|---|---|---|---|
| coherent | n/a | any | `FAIL_SAFE_NO_MUTATION` or `EXITED_UNVERIFIED` |
| missing/empty/incomplete | fresh verified | live referenced | preserve official incomplete root; leave hidden dir; restore official from restore point |
| missing/empty/incomplete | fresh verified | inactive collision | quarantine inactive blocker; restore official from restore point |
| missing/empty/incomplete | absent/stale/bad | any | `ROLLBACK_FAIL_OPERATOR_REQUIRED` |
| unknown | any | suspicious | `ROLLBACK_FAIL_OPERATOR_REQUIRED` |

Recovery action must write `recovery-action.json` before mutation and `post-recovery-check.json` after.

---

## 5. Hard validation gates

## Gate group A — static design and no-foreground enforcement

### A1: No critical apply foreground path exists

Validation:

- grep/source audit finds no documentation or scripts that instruct running critical mutation via foreground exec;
- AGENTS.md contains critical apply hard rule;
- runner refuses `--execute-foreground` or equivalent.

PASS criteria:

```text
A1_PASS_NO_FOREGROUND_CRITICAL_APPLY_PATH
```

### A2: Contract schemas validate

Validation:

- all JSON schema examples validate;
- malformed receipts fail closed;
- unknown terminal classifications rejected.

PASS criteria:

```text
A2_PASS_CONTRACT_SCHEMA_VALIDATION
```

### A3: State machine totality

Validation:

- every phase transition is enumerated;
- every failure path maps to a terminal classification;
- no exception path leaves transaction without `final-report.json` or `runner-error.json`.

PASS criteria:

```text
A3_PASS_STATE_MACHINE_TOTALITY
```

---

## Gate group B — restore point gates

### B1: Fresh restore point required

Validation:

- with no restore point and create disabled, runner blocks;
- with stale restore point >3600s, runner blocks or creates new if policy permits;
- with fresh restore point, runner proceeds.

PASS criteria:

```text
B1_PASS_RESTORE_POINT_FRESHNESS_GATE
```

### B2: Restore point creation and verification

Validation:

- fixture package root archived/copied;
- manifest SHA/size counts match;
- restore boundary generated;
- symlink/path traversal rejected;
- ownership/same-filesystem checks emitted.

PASS criteria:

```text
B2_PASS_RESTORE_POINT_CREATE_VERIFY
```

### B3: Restore point restore drill

Validation:

- deliberately damage fixture package root;
- restore from restore point;
- verify exact package coherence;
- verify no out-of-bound files touched.

PASS criteria:

```text
B3_PASS_RESTORE_POINT_RESTORE_DRILL
```

---

## Gate group C — OpenClaw npm plugin gates

### C1: Package authority fixture validation

Validation:

- valid package passes;
- wrong SHA fails;
- wrong version fails;
- wrong source commit fails;
- unsafe tar path fails;
- superseded package SHA fails.

PASS criteria:

```text
C1_PASS_PACKAGE_AUTHORITY_MATRIX
```

### C2: Package root health classifier

Validation fixtures:

- missing root;
- empty root;
- incomplete root missing `runtime-api.js`;
- incomplete root missing `dist/index.js`;
- coherent root;
- conflicting/unknown root.

PASS criteria:

```text
C2_PASS_NPM_BASE_HEALTH_CLASSIFIER_MATRIX
```

### C3: Speech import chain classifier

Validation:

- complete runtime-api import chain passes;
- missing relative import fails;
- syntax error fails;
- nonliteral dynamic import classified unresolved;
- missing runtime-api file classified missing.

PASS criteria:

```text
C3_PASS_SPEECH_SURFACE_CLASSIFIER_MATRIX
```

### C4: Staging/process-reference classifier

Validation fixtures:

- no staging dirs;
- inactive valid `.openclaw-*`;
- live-referenced staging via fake `/proc` fixture maps/fd/cwd/exe/cmdline;
- suspicious symlink staging;
- staging outside node_modules.

PASS criteria:

```text
C4_PASS_STAGING_PROCESS_REFERENCE_CLASSIFIER
```

### C5: Protected scheduler/memory guard

Validation:

- strict `jobs.json` changed → fail;
- volatile `jobs-state.json` timestamp drift under signed policy → pass;
- protected writer execution field changed → fail;
- protected run-log SHA changed → fail;
- protected memory SHA changed without rebaseline → fail.

PASS criteria:

```text
C5_PASS_PROTECTED_SCHEDULER_MEMORY_GUARD
```

---

## Gate group D — observer resiliency gates

### D1: Receipt-before-mutation

Validation:

- instrument apply command fixture;
- prove `apply-start.json` exists before child starts mutation marker;
- command hash matches approval boundary.

PASS criteria:

```text
D1_PASS_RECEIPT_BEFORE_MUTATION
```

### D2: Session-loss recovery

Validation:

- start transaction;
- kill foreground/client/status reader;
- observer continues;
- `status --transaction` later reconstructs phase from files.

PASS criteria:

```text
D2_PASS_SESSION_LOSS_REHYDRATION
```

### D3: Child timeout and process-group cleanup

Validation:

- child ignores SIGTERM;
- observer escalates to SIGKILL after bounded interval;
- process group is gone;
- terminal classification is `STARTED_NO_EXIT` or `EXITED_UNVERIFIED` with artifacts.

PASS criteria:

```text
D3_PASS_TIMEOUT_PROCESS_GROUP_CLEANUP
```

### D4: stdout/stderr durability

Validation:

- child emits large stdout/stderr;
- logs are complete and referenced by receipt;
- chat truncation cannot lose evidence.

PASS criteria:

```text
D4_PASS_STDOUT_STDERR_DURABILITY
```

---

## Gate group E — automatic recovery gates

### E1: Apply fails before mutation, package intact

Validation:

- fixture apply exits nonzero without touching root;
- observer classifies `FAIL_SAFE_NO_MUTATION`;
- no restore action performed.

PASS criteria:

```text
E1_PASS_FAIL_SAFE_NO_MUTATION
```

### E2: Apply fails and official root missing

Validation:

- fixture deletes package root then exits nonzero;
- observer classifies `NPM_BASE_MISSING`;
- restore point fresh;
- observer restores root;
- postcheck coherent;
- terminal `ROLLBACK_PASS` or `RECOVERED_WITH_WARNING` depending service health scope.

PASS criteria:

```text
E2_PASS_AUTO_RESTORE_MISSING_ROOT
```

### E3: Apply fails and official root empty

Same as E2 but root exists empty.

PASS criteria:

```text
E3_PASS_AUTO_RESTORE_EMPTY_ROOT
```

### E4: Apply fails and official root incomplete with live hidden generation

Validation:

- fixture official root missing critical files;
- fake/live process references `.openclaw-*` staging dir;
- observer leaves hidden dir untouched;
- preserves incomplete official root to evidence;
- restores official path from restore point;
- postcheck coherent.

PASS criteria:

```text
E4_PASS_AUTO_RESTORE_INCOMPLETE_ROOT_LIVE_STAGING_UNTOUCHED
```

### E5: Restore point stale/invalid

Validation:

- apply failure damages root;
- restore point stale or bad SHA;
- observer refuses automatic recovery;
- terminal `ROLLBACK_FAIL_OPERATOR_REQUIRED`;
- no restart.

PASS criteria:

```text
E5_PASS_STALE_RESTORE_BLOCKS_AUTO_RECOVERY
```

---

## Gate group F — boundary separation gates

### F1: Apply does not restart

Validation:

- package apply succeeds;
- no `systemctl restart`, Gateway restart, or PID change is performed by apply transaction;
- final report says `HOLD_FOR_SEPARATE_RESTART` if restart required.

PASS criteria:

```text
F1_PASS_APPLY_RESTART_BOUNDARY
```

### F2: Restart transaction has separate gates

Validation:

- restart transaction requires its own restore point and approval boundary;
- bounded readiness polling implemented;
- HTTP warning is classified `RECOVERED_WITH_HTTP_HEALTH_WARNING`, not package failure.

PASS criteria:

```text
F2_PASS_RESTART_SEPARATE_TRANSACTION
```

### F3: Functional smoke separate

Validation:

- Telegram/provider/Gmail smoke cannot run in package apply transaction;
- separate smoke transaction requires explicit approval.

PASS criteria:

```text
F3_PASS_FUNCTIONAL_SMOKE_SEPARATION
```

---

## 6. Build milestones

## Milestone M0 — Contract finalization

Goal: land the contract and schema fixtures only.

Deliverables:

- `CRITICAL_APPLY_CONTRACT.md`
- schema definitions in `critical_apply_contracts.py`
- fixture JSON examples
- no mutation code beyond test fixtures

Hard gates:

- A1, A2, A3 pass.

Closeout terminal:

```text
M0_PASS_CRITICAL_APPLY_CONTRACT_FINALIZED_NO_MUTATION
```

---

## Milestone M1 — Runner skeleton and durable receipts

Goal: build transaction directory, lock, state machine, status/final-report, no real apply plugin.

Deliverables:

- `critical_apply_observer_runner.py prepare/status/final-report`
- lock acquisition/release
- heartbeat writer
- final classification for no-op fixture

Hard gates:

- A1, A2, A3
- D2 basic rehydration
- D4 logging fixture

Closeout terminal:

```text
M1_PASS_RUNNER_SKELETON_DURABLE_RECEIPTS
```

---

## Milestone M2 — Restore point subsystem

Goal: create/verify/restore package-root restore points in fixtures only.

Deliverables:

- restore point create/verify code
- path-safety and manifest validation
- restore drill fixture

Hard gates:

- B1, B2, B3
- A2 schema validation

Closeout terminal:

```text
M2_PASS_RESTORE_POINT_SUBSYSTEM_FIXTURE_DRILL
```

---

## Milestone M3 — OpenClaw npm plugin classifiers

Goal: implement read-only npm/package/speech/staging/scheduler classifiers.

Deliverables:

- `openclaw_npm_package.py` read-only classifier APIs
- fixtures for coherent/missing/empty/incomplete roots
- fake `/proc` fixture support
- scheduler/memory guard fixtures

Hard gates:

- C1, C2, C3, C4, C5
- no live npm/package mutation

Closeout terminal:

```text
M3_PASS_OPENCLAW_NPM_PLUGIN_CLASSIFIER_MATRIX_READ_ONLY
```

---

## Milestone M4 — Observer execution supervisor

Goal: run fixture apply commands under observer with receipts, logs, timeout, process-group control.

Deliverables:

- `execute` implementation using argv JSON
- process group management
- timeout handling
- receipt-before-mutation fixture

Hard gates:

- D1, D2, D3, D4
- A3 state-machine totality

Closeout terminal:

```text
M4_PASS_OBSERVER_EXECUTION_SUPERVISOR_FIXTURE_SAFE
```

---

## Milestone M5 — Automatic recovery fixture matrix

Goal: observer-owned recovery from verified restore point for fixture npm roots.

Deliverables:

- recovery decision implementation
- restore action implementation
- missing/empty/incomplete official root recovery fixtures
- live hidden staging untouched fixture

Hard gates:

- E1, E2, E3, E4, E5
- B3 restore drill
- C4 staging classifier

Closeout terminal:

```text
M5_PASS_OBSERVER_OWNED_AUTO_RECOVERY_FIXTURE_MATRIX
```

---

## Milestone M6 — Boundary separation transactions

Goal: enforce apply/restart/smoke separation.

Deliverables:

- package apply transaction cannot restart
- restart transaction skeleton with bounded readiness polling fixture
- functional smoke transaction skeleton requiring separate approval

Hard gates:

- F1, F2, F3
- D2 rehydration

Closeout terminal:

```text
M6_PASS_APPLY_RESTART_SMOKE_BOUNDARY_ENFORCEMENT
```

---

## Milestone M7 — Local dry-run against live state, no mutation

Goal: run read-only prepare/precheck against current live OpenClaw to prove classifier can observe reality without touching it.

Allowed:

- read package root;
- read `.openclaw-*` sibling metadata;
- read `/proc` references;
- read service identity;
- read cron/protected-memory sentinels;
- create evidence under transaction directory.

Forbidden:

- npm install;
- package root mutation;
- Gateway restart/reload;
- cron mutation/calls;
- provider/delivery/smoke.

Hard gates:

- C classifiers pass on live read-only state;
- B restore point policy reports whether fresh restore point exists or would be created, but does not mutate unless explicitly scoped as restore-point-only milestone;
- no forbidden mutation.

Closeout terminal:

```text
M7_PASS_LIVE_READ_ONLY_PRECHECK_NO_MUTATION
```

---

## Milestone M8 — Restore-point-only live transaction

Goal: create a fresh restore point under critical apply runner with no apply.

Allowed:

- create verified restore point;
- create evidence;
- read package/root/process/scheduler/memory.

Forbidden:

- npm install;
- package root replacement;
- Gateway restart;
- cron/provider/delivery.

Hard gates:

- B1, B2 live
- restore point age < 1 hour at closeout
- manifest validates
- no package mutation beyond restore-point evidence

Closeout terminal:

```text
M8_PASS_LIVE_RESTORE_POINT_ONLY_NO_APPLY
```

---

## Milestone M9 — Shadow apply simulation on copied package root

Goal: run the full apply/recovery state machine on a copied fixture of current OpenClaw package, not production path.

Allowed:

- copy package root to isolated temp/evidence dir;
- run npm/package simulation against copy;
- damage copy to exercise recovery;
- restore copy from restore point.

Forbidden:

- production package mutation;
- Gateway restart;
- cron/provider/delivery.

Hard gates:

- E1–E5 pass on copied root;
- D gates pass;
- no production sentinels changed.

Closeout terminal:

```text
M9_PASS_SHADOW_APPLY_RECOVERY_ON_COPIED_ROOT_NO_PRODUCTION_MUTATION
```

---

## Milestone M10 — Owner-approved production package apply, package-only

Goal: first real production package apply under critical apply runner.

Preconditions:

- M0–M9 PASS;
- restore point fresh within 1 hour or created in same transaction;
- exact package authority verified;
- no pending stale approvals;
- Stick approves exact transaction boundary.

Allowed:

- package root/npm link/npm metadata mutation only;
- transaction evidence;
- automatic package-only restore from restore point if npm base missing/empty/incomplete.

Forbidden:

- Gateway restart/reload;
- cron mutation/calls;
- protected memory mutation except evidence;
- provider/delivery;
- functional smoke;
- DISABLE/activation follow-ons.

Hard gates:

- restore point fresh verified;
- apply-start receipt exists before npm child;
- child PID/process group receipt;
- npm stdout/stderr artifacts;
- package coherence postcheck;
- if failure: npm base classified and recovery decision/action receipts complete;
- strict jobs/protected-memory sentinels unchanged;
- no restart observed.

Closeout terminals:

Success:

```text
M10_PASS_PRODUCTION_PACKAGE_APPLY_PACKAGE_ONLY_NO_RESTART
```

Recovered:

```text
M10_PASS_RECOVERED_FROM_APPLY_FAILURE_PACKAGE_ONLY_NO_RESTART
```

Blocked:

```text
M10_HOLD_OPERATOR_REQUIRED_NO_UNVERIFIED_MUTATION
```

---

## Milestone M11 — Separately approved Gateway restart transaction

Goal: restart Gateway only after package apply says restart is needed.

Preconditions:

- M10 PASS/HOLD_FOR_SEPARATE_RESTART;
- restart transaction restore point fresh;
- Stick approves restart boundary.

Hard gates:

- old PID/start ticks captured;
- restart command under observer;
- new PID/start ticks captured;
- systemd active/running;
- port bound;
- WebSocket 101;
- HTTP check with bounded readiness polling;
- if HTTP warning only, classify warning not package failure;
- no provider/delivery smoke.

Closeout terminal:

```text
M11_PASS_CONTROLLED_GATEWAY_RESTART_OBSERVED
```

or

```text
M11_RECOVERED_WITH_HTTP_HEALTH_WARNING_NO_PACKAGE_REPAIR_NEEDED
```

---

## Milestone M12 — Separately authorized functional smoke

Goal: minimal Telegram/provider/control-plane functional verification after package+restart.

Preconditions:

- M10/M11 pass;
- Stick explicitly approves smoke target and content.

Hard gates:

- smoke boundary explicit;
- no package/config mutation;
- result recorded;
- failures classified as output/provider/control-plane issue, not package reinstall trigger by default.

Closeout terminal:

```text
M12_PASS_FUNCTIONAL_SMOKE_SEPARATE_TRANSACTION
```

---

## 7. Test matrix summary

Minimum automated tests before any live apply:

| Group | Count | Required before live apply |
|---|---:|---|
| Schema/state-machine | 20+ | M0 |
| Restore point | 15+ | M2 |
| Package authority | 10+ | M3 |
| Package root classifier | 12+ | M3 |
| Speech import chain | 8+ | M3 |
| Staging/process refs | 10+ | M3 |
| Observer process control | 10+ | M4 |
| Auto recovery | 15+ | M5 |
| Boundary separation | 8+ | M6 |
| Shadow end-to-end | 5+ | M9 |

All tests must write JUnit or JSON result artifacts and a human-readable summary.

---

## 8. Owner approval boundaries

Before any production mutation, foreground assistant must present:

1. transaction id;
2. exact mutation boundary;
3. exact argv hash and argv list;
4. restore point id, age, and manifest SHA;
5. forbidden surfaces;
6. expected final state;
7. automatic recovery authority;
8. statement that restart/smoke are not included unless explicitly in scope.

Approval text should approve the **transaction**, not a foreground shell command.

Example:

```text
APPROVE CRITICAL APPLY TRANSACTION <id> PACKAGE-ONLY — ALLOW OBSERVER TO RUN EXACT ARGV SHA <sha> AND AUTO-RESTORE PACKAGE ROOT FROM RESTORE POINT <restore-id> IF NPM BASE IS MISSING/EMPTY/INCOMPLETE — NO GATEWAY RESTART — NO CRON — NO PROVIDER — NO SMOKE
```

---

## 9. Non-goals for v1

- No generic arbitrary command runner for all production mutation.
- No automatic deletion of staging directories.
- No automatic Gateway restart after package apply.
- No Telegram/provider/Gmail smoke in package transaction.
- No live production apply before fixture, shadow, and restore-point-only milestones pass.
- No stale-lock auto-break.

---

## 10. Build order recommendation

Recommended next task:

```text
M0 — Contract finalization
```

Do not jump to M10. The first safe implementation step is schema/state-machine/fixture-only work.

Owner-ready STARTED notice for M0 should say:

```text
STARTED M0 Critical Apply Contract Finalization.
Pass criteria: contract schemas validate, state machine totality proven, no foreground critical apply path remains, no production mutation. Closeout artifacts: CRITICAL_APPLY_CONTRACT.md, critical_apply_contracts.py, schema fixtures, hard_gates.json, evidence manifest.
```

---

## 11. Final acceptance criteria for the whole build

The critical apply system is production-ready only when all are true:

1. M0–M9 pass with evidence manifests.
2. Runner can survive foreground/session death and resume status from files.
3. Restore point creation and restore drill pass.
4. OpenClaw npm package plugin classifies missing/empty/incomplete/coherent roots correctly.
5. Live `.openclaw-*` process references are detected and left untouched.
6. Observer automatically restores official package root from verified fresh restore point when npm base is missing/empty/incomplete after apply failure.
7. Apply transaction cannot restart Gateway.
8. Restart transaction cannot run without its own boundary and readiness polling.
9. Functional smoke cannot run without separate explicit boundary.
10. A stale/invalid restore point blocks automatic recovery and escalates to operator.

If any one of these fails, production critical apply remains blocked.
