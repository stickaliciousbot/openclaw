# Critical Apply — Restore Script Repurpose Notes (2026-07-30)

Source inspected read-only:

- `/home/stickai/.openclaw/media/inbound/recover_openclaw_cli_gateway_speech_surface---bdfc3ad2-6f75-49d6-a6e1-4dd4acbb508c.sh`
- SHA-256: `282b52ac57dc96d89ac7b3661a1cbf63fd1d8d55c19570449bd0d79da972baf8`
- Lines: 2013

## Core conclusion
The restore script contains valuable recovery logic, but the new architecture must move responsibility downward into the observer. The foreground wrapper must not decide “npm is healthy enough” or manually invoke restore after the fact. The critical apply observer must own:

1. npm/package health classification;
2. detection of missing/empty/incomplete package base;
3. `.openclaw-*` staging/process-reference inspection;
4. restore/reinstall invocation from verified restore point;
5. post-restore verification and final classification.

## Code/ideas to repurpose directly

### 1. Evidence-first mode separation
Existing script pattern:

- default `--report` is read-only;
- `--repair`, `--restart-only`, and `--rollback` are separate modes;
- install and restart are never combined;
- provider/delivery probes are excluded.

Repurpose into critical apply phases:

- `prepare/report`;
- `apply`;
- `recover`;
- `restart` as separate transaction;
- `functional-smoke` as separate transaction.

### 2. Exact package authority verification
Function: `verify_package_authority` lines 666–745.

Repurpose:

- exact package path;
- SHA-256 verification;
- reject superseded package SHA prefix `098684` style mistake;
- inspect tar safely without extracting;
- verify package name/version/source commit;
- verify authority manifest hash;
- reject unsafe archive paths.

This should become a reusable plugin method:

- `OpenClawNpmPackageAuthority.verify()`.

### 3. Restore/rollback authority verification
Function: `verify_rollback_authority` lines 746–1081.

Repurpose:

- authenticate handoff by SHA;
- verify rollback archive SHA;
- ensure rollback archive is distinct from install package;
- resolve only manifest-listed paths under manifest root;
- authenticate scheduler policy and semantic baseline;
- verify strict sentinels: `jobs.json`, protected writer run logs, protected memory.

This should become:

- `RestorePoint.verify(max_age_seconds=3600)`;
- `SchedulerGuard.verify_semantic_policy()`;
- `ProtectedMemoryGuard.verify()`.

### 4. Package coherence inspection
Function: `inspect_package` lines 312–404.

Repurpose checks:

- package root exists and is directory;
- `package.json` parse/name/version;
- bin metadata and resolved bin target;
- build-info/source commit;
- runtime entry candidates;
- Gateway lifecycle surface;
- bundled public-surface registry;
- Control UI surface.

Add critical apply generalization:

- return `PACKAGE_ROOT_MISSING`, `PACKAGE_ROOT_EMPTY`, `PACKAGE_ROOT_INCOMPLETE`, `PACKAGE_COHERENT`, `PACKAGE_UNKNOWN_GENERATION`.

### 5. Speech/public-surface import-chain check
Function: `inspect_speech_surface` lines 405–480.

Repurpose:

- verify `dist/extensions/speech-core/runtime-api.js` exists/readable;
- compute SHA;
- enumerate relative imports/exports;
- resolve extension/index candidates;
- detect missing imports;
- run local `node --check` syntax test;
- classify `SPEECH_PUBLIC_SURFACE_FILE_MISSING`, `IMPORT_MISSING`, `PARSE_UNRESOLVED`, `COMPLETE`.

This becomes one package-coherence plugin check, not the whole health decision.

### 6. Listener/service authority discovery
Function: `inspect_listener_and_service` lines 529–628.

Repurpose:

- listener PID/start ticks;
- executable/cmdline/cwd;
- allowlisted environment capture;
- parent command;
- cgroup service extraction;
- `systemctl show` evidence;
- restart argv derivation.

Critical apply observer should use this in precheck and postcheck. Restart remains a separate transaction unless explicitly in scope.

### 7. npm staging/process-reference inspection
Function block: `checksum_pinned_reinstall` lines 1483–1594.

This is essential. Repurpose almost directly:

- find sibling `.openclaw-*` dirs;
- validate name pattern, direct child of `node_modules`, plain directory, distinct from package root;
- inspect process references:
  - cwd;
  - root;
  - exe;
  - cmdline;
  - maps;
  - fd targets;
- classify:
  - safe to quarantine;
  - preserve in place;
  - unsafe type/name/location → block;
- never delete hidden staging automatically.

In the new architecture this belongs inside observer failure handling as:

- `NpmBaseInspector.inspect_staging_dirs(listener_pid)`.

### 8. Incomplete package preservation before reinstall
Function block: `checksum_pinned_reinstall` lines 1620–1640.

Repurpose:

- if official package root exists but is incomplete, require it is a plain directory;
- refuse to displace coherent package;
- require same filesystem for atomic move;
- move incomplete official root into evidence;
- leave live-referenced staging in place;
- never restart.

New observer action:

- `preserve_incomplete_official_root()`.

### 9. Observer-governed npm install
Function block: lines 1642–1695.

Repurpose with important change:

- existing script uses `observer_run` but the foreground script still decides next recovery behavior;
- new architecture must have observer own post-failure npm-base inspection and restore.

Keep:

- exact `/usr/bin/npm install -g --offline <package>` argv;
- stdout/stderr artifacts;
- repair receipt;
- post-verification;
- no restart.

Change:

- observer writes `apply-start.json` before npm exec;
- observer checks package base immediately after failure;
- observer restores/reinstalls from fresh restore point if root is missing/empty/incomplete;
- foreground sees only final transaction classification.

### 10. Package-only rollback copy
Function: `package_only_rollback` lines 1742–1895.

Repurpose:

- verify rollback archive still matches SHA at time of use;
- inspect archive members for unsafe paths;
- extract to staged evidence dir;
- find exactly one OpenClaw package tree;
- derive CLI link from signed handoff or verified package bin metadata;
- displace current package root;
- copy staged package under observer;
- verify package and speech surface after copy;
- if verification fails, restore pre-rollback package and CLI link;
- write repair receipt;
- never restart.

Change:

- this becomes an observer-internal recovery operation, not a separately foreground-driven mode when automatic recovery is authorized.

### 11. Decision/classification logic
Function: `classify_generation_and_decide` lines 1294–1415.

Repurpose categories:

- `INCOMPLETE_NEW_DISK_PACKAGE`;
- `WRONG_PACKAGE_ROOT_OR_LAUNCHER_AUTHORITY`;
- `UNKNOWN_OR_MIXED_GENERATION`;
- `STALE_RUNNING_PROCESS_WITH_COHERENT_NEW_DISK_PACKAGE`;
- `COHERENT_CURRENT_RUNTIME`;
- decisions `CHECKSUM_PINNED_REINSTALL`, `CONTROLLED_RESTART`, `NO_ACTION`, `BLOCKED_AUTHORITY_INCOMPLETE`.

Update categories for critical apply:

- `NPM_BASE_MISSING`;
- `NPM_BASE_EMPTY`;
- `NPM_BASE_INCOMPLETE`;
- `NPM_BASE_COHERENT`;
- `HIDDEN_GENERATION_LIVE_REFERENCED`;
- `RESTORE_POINT_REQUIRED`;
- `RESTORE_POINT_VERIFIED`;
- `AUTO_RESTORE_FROM_RESTORE_POINT`;
- `ROLLBACK_FAIL_OPERATOR_REQUIRED`.

### 12. Health checks
Function: `inspect_gateway_health` lines 629–665 and `controlled_restart` lines 1697–1741.

Repurpose:

- HTTP `/` check;
- WebSocket upgrade check;
- origin-blocked detection;
- service restart receipts.

Change:

- add bounded readiness polling before failure classification;
- if WebSocket passes but HTTP fails, classify `RECOVERED_WITH_HTTP_HEALTH_WARNING`, not generic `NO_ACTION` or failure requiring reinstall;
- restart remains separate transaction.

## Code not to reuse as-is

### `observer_run` polling loop
Function: `observer_run` lines 1129–1236.

Useful concept, but not enough for critical apply because it still acts like a wrapper around a child command. It needs to evolve into a transaction supervisor that owns state machine and recovery.

Problems to fix:

- foreground still loops/checks observer;
- command stdout/stderr are replayed back into foreground;
- failure handling happens after return in wrapper;
- `sleep 1` polling is acceptable in an observer process but not as the governing chat turn;
- `set +e` / `set -e` sections caused receipt fragility in earlier recovery.

### Bash heredoc-embedded Python
The existing script uses many heredocs. They are okay inside a standalone recovery utility, but OpenClaw tool approval paths treat heredoc shell commands as approval-sensitive and brittle. For the new runner, prefer real Python modules/files and argv JSON.

### Immediate restart HTTP failure
`controlled_restart` checks once and can false-fail while Gateway is still starting. Replace with bounded readiness polling.

## New observer responsibility model

The observer must not simply run npm and report rc. It must own this sequence:

```text
apply-start
run npm/apply command
if rc == 0:
  inspect npm base/package coherence
  if coherent: PASS or HOLD_FOR_RESTART
  else: FAIL_MUTATION_PARTIAL -> recover from restore point
else:
  inspect npm base
  if root missing/empty/incomplete:
    inspect .openclaw-* process references
    if restore point fresh+verified:
      restore/reinstall from restore point
      postcheck
      classify ROLLBACK_PASS / ROLLBACK_FAIL_OPERATOR_REQUIRED
    else:
      ROLLBACK_FAIL_OPERATOR_REQUIRED
  else:
    FAIL_SAFE_NO_MUTATION or EXITED_UNVERIFIED
```

## Concrete implementation extraction plan

1. Create `scripts/critical_apply_observer_runner.py` for transaction state machine.
2. Create `scripts/critical_apply_plugins/openclaw_npm_package.py` and port the Python logic from this restore script into functions:
   - `verify_package_authority()`;
   - `verify_restore_point()`;
   - `inspect_package_root()`;
   - `inspect_speech_surface()`;
   - `inspect_listener_and_service()`;
   - `inspect_staging_dirs()`;
   - `preserve_incomplete_root()`;
   - `restore_from_archive()`;
   - `postcheck_package_coherence()`.
3. Keep Bash only as thin launch shim if needed; no shell heredoc in critical path.
4. Use argv JSON for commands.
5. Write receipts before and after every mutation.
6. Add tests/fixtures for:
   - complete package;
   - missing package root;
   - empty package root;
   - incomplete official package with live `.openclaw-*` generation;
   - inactive staging collision;
   - npm failure after partial root creation;
   - failed restore copy;
   - restart readiness delayed.

## Bottom line
The restore script is a strong prototype for the OpenClaw npm package plugin. The most important repurposed behavior is: **after any apply failure, the observer itself must classify npm/package health and invoke restore from a verified fresh restore point when official package base is missing, empty, or incomplete.**
