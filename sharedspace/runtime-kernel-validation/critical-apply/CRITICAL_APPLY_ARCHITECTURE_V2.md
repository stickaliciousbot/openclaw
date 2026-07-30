# Critical Apply Observation Harness Architecture v2.0

**Date:** 2026-07-30  
**Owner context:** Stick / Stickbot OpenClaw runtime operations  
**Status:** LOCKED ARCHITECTURE CONTRACT — design and preparation only  
**Production authority:** None. This document does not authorize deploy, install, restart, cron mutation, provider call, protected-memory mutation, or any other production mutation.

## 1. Executive decision

No critical OpenClaw mutation may be governed by a foreground chat, terminal, approval card, or tool invocation. A foreground session may prepare and seal a transaction plan, present its authority boundary, submit an owner approval, and read durable status. It must never be the mutation supervisor or the only source of truth.

Every critical apply must run as a **Harness Resiliency Level 3 (HRL-3)** transaction:

1. a verified restore point is fresh at the exact mutation-release boundary;
2. the transaction is executed by a pre-existing supervisor-managed observer, not an improvised detached process;
3. mutation intent, executable identity, authority, preconditions, and recovery policy are sealed before release;
4. the mutation child cannot start until its durable spawn receipt exists;
5. the observer owns post-state classification and bounded recovery;
6. install/apply, Gateway restart, and functional smoke remain separate transactions;
7. a fresh session can reconstruct truth from an append-only journal and sealed artifacts;
8. observer or host failure never causes blind mutation replay.

This architecture is the mandatory mutation substrate for the remaining Universal Runtime Kernel work. Runtime-kernel features may provide plugins and policies, but may not bypass this core.

## 2. Incident-derived problem statement

Foreground apply paths combine authority, execution, observation, and closeout in one brittle control plane. A chat compaction, tool timeout, WSL session loss, terminal disconnect, Gateway wedge, or lost stdout can remove the only observer while production is changing.

The npm/OpenClaw mixed-generation incident exposed a second danger: command exit status does not describe system truth. An installer can fail after moving the official package root, leave an empty or incomplete root, retain a running Gateway on an older hidden generation, and produce a state where a simple retry or restart worsens damage.

The architecture therefore treats:

- command execution,
- official package state,
- running process generation,
- hidden staging generations,
- protected adjacent state, and
- recovery state

as separate evidence dimensions.

## 3. Normative language

**MUST**, **MUST NOT**, **SHALL**, and **SHALL NOT** are hard gates.  
**SHOULD** is required unless a documented, evidence-backed exception is approved before mutation.  
“Verified” means independently recomputed from durable evidence, not merely asserted by a prior receipt.

## 4. Definitions

### 4.1 Critical apply

Any deploy, install, repair, restore, rollback, activation, migration, restart, route/config change, guarded cron mutation, protected-memory mutation, provider/auth/delivery change, or other operation whose failure can wedge OpenClaw, break replies, damage package state, or require recovery.

### 4.2 Foreground process

Any command whose safety depends on the current chat, terminal, tool call, or approval UI remaining alive and receiving ordered stdout/stderr or completion.

### 4.3 Durable observer

A pre-installed, supervisor-managed process with:

- a stable executable and code hash;
- a persistent state root;
- an OS-level single-writer lock;
- crash-consistent receipts;
- startup reconciliation;
- process/cgroup identity tracking;
- bounded timeout and recovery semantics; and
- no dependency on the initiating chat after transaction submission.

`nohup`, `disown`, ad hoc `setsid`, background shell jobs, raw detached subprocesses, and “leave this command running” are not durable observers.

### 4.4 Restore point

An immutable, verified snapshot of all surfaces required to return the transaction’s write set to its exact pre-apply state. A restore point is evidence, not authority. Recovery authority is granted separately in the transaction authority envelope.

### 4.5 Transaction campaign

A logical chain of separately authorised transactions, such as:

```text
PACKAGE_APPLY -> GATEWAY_RESTART -> FUNCTIONAL_SMOKE
```

A predecessor’s terminal seal may be a precondition for the next transaction, but it never grants authority to start it.

### 4.6 Surface sets

Each transaction declares:

- **read set** — surfaces the observer may inspect;
- **write set** — surfaces the primary mutation may change;
- **recovery write set** — surfaces automatic recovery may change;
- **guard set** — adjacent surfaces that must remain unchanged or drift only under a signed policy;
- **forbidden set** — surfaces that must not be accessed or changed.

## 5. Hard prohibitions

A critical apply SHALL NOT:

- run as a foreground exec;
- be started by a raw approval card whose command is the only observer;
- use an unsealed shell string or `shell=True`;
- use an arbitrary generic command runner;
- hold a production mutation lock while waiting indefinitely for chat approval;
- reuse an approval after any bound input changes;
- restart Gateway as part of a package apply transaction;
- run provider, Telegram, Gmail, or delivery smoke as part of package apply or restart;
- delete `.openclaw-*` or other staging directories automatically;
- retry an uncertain mutation automatically;
- restore from an unverified, unbound, or post-approval-substituted restore point;
- trust PID alone as process identity;
- trust exit code alone as system state;
- continue when evidence writes, fsync, manifest sealing, path validation, process-reference inspection, or guard checks are unknown;
- automatically break a stale maintenance lock in v1;
- mutate production when the HRL-3 supervisor is unavailable or unproven.

If no production-ready critical apply runner exists, work stops at architecture, code, fixtures, shadow execution, or read-only preparation.

## 6. Harness Resiliency Levels

| Level | Description | Critical production mutation |
|---|---|---|
| HRL-0 | Foreground command and live stdout | Forbidden |
| HRL-1 | Background/detached process with logs | Forbidden |
| HRL-2 | Durable receipts and session-loss survival, but no supervisor restart reconciliation or launch fencing | Insufficient |
| HRL-3 | Supervisor-managed observer, atomic journal, launch gate, single-writer fencing, startup reconciliation, idempotent recovery, terminal seal | Required |
| HRL-4 | Redundant external witness / remote control plane | Future enhancement, not required for v1 |

The observer itself must be launched by a proven OS supervisor. For this WSL deployment, the production design SHALL use the system service manager or another independently proven system-level supervisor; it SHALL NOT depend on the fragile per-user systemd session bus.

## 7. Bootstrap rule

The critical apply system has a bootstrap problem: its first installation cannot claim protection from a runner that does not yet exist.

The bootstrap is therefore a separately governed milestone, not an exception:

1. M0–M6 contracts, evidence primitives, restore logic, supervisor code, package classifiers, and recovery fixtures are completed without production OpenClaw mutation.
2. The observer service bundle is checksum-pinned and inspected offline.
3. Installation/activation of the observer service is performed only under the already-proven parent-thread observation harness architecture, with its own restore point, bounded authority, durable receipts, and no OpenClaw package/Gateway/cron/provider mutation.
4. The observer service must pass HRL-3 self-tests after installation.
5. Boundary enforcement, live read-only inspection, restore-point-only proof, and isolated shadow end-to-end validation then run under the bootstrapped service.
6. Only after those gates pass may the new runner govern a production package apply.

No `nohup`, `disown`, ad hoc backgrounding, or raw foreground installer may be used to bridge the bootstrap.

## 8. Authority model

Every mutation requires an immutable **Authority Envelope** containing:

- transaction ID and campaign ID;
- owner identity and approval mechanism;
- one-time nonce;
- approval issued time and expiry;
- exact transaction-spec hash;
- runner, contracts, plugin, interpreter, and supervisor unit hashes;
- exact candidate/package authority hash;
- exact apply argv hash and environment-policy hash;
- restore-point ID, manifest hash, and restore method;
- read, write, recovery-write, guard, and forbidden sets;
- timeout and resource policy;
- network policy;
- automatic recovery conditions and maximum recovery count;
- restart and smoke flags, both false unless the transaction type is explicitly that boundary.

Approval is consumed once. It cannot be transferred to a new restore point, command, plugin version, pre-state, environment, or transaction. Any drift invalidates it.

The owner approves the transaction, not a shell command.

## 9. Prepare/approve/commit separation

The observer SHALL use two lock scopes.

### 9.1 Prepare phase

Prepare may:

- classify scope;
- verify candidate authority;
- inspect current state;
- create or select a restore point;
- build guard sentinels;
- generate and seal the transaction plan;
- release any short-lived preparation lock;
- enter `AWAITING_APPROVAL`.

Prepare SHALL NOT hold the global production mutation lock while waiting for approval.

### 9.2 Commit phase

After approval, execute SHALL:

1. acquire the global critical-apply lock and all ordered surface locks;
2. verify the approval is valid and unconsumed;
3. re-hash runner/plugin/contracts/interpreter/candidate/spec;
4. re-check restore-point integrity and freshness;
5. re-check package-manager substrate, process identities, guard sentinels, free space, mount identity, and pre-state fingerprint;
6. prove no concurrent package/restart/recovery process exists;
7. invalidate and block on any drift;
8. durably record `COMMIT_VALIDATED`;
9. create a blocked mutation child;
10. durably record its full identity;
11. perform one final pre-release revalidation;
12. consume approval and release the child.

This closes the approval-to-execution time-of-check/time-of-use gap.

## 10. Restore-point contract

### 10.1 Freshness

A restore point MUST be no older than 3,600 seconds at `MUTATION_RELEASE`, not merely at prepare time.

If approval wait makes it stale, the transaction is blocked and must be re-prepared and re-approved with a new restore-point identity.

After mutation release, the restore point remains eligible for recovery for that transaction even if more than one hour elapses, provided:

- it was valid at mutation release;
- its immutable manifest and seal still verify;
- its pre-state fingerprint matches the transaction;
- it has not been substituted;
- recovery remains within the authority envelope.

A long-running failed apply must not lose its only rollback because wall-clock age crossed one hour after mutation began.

### 10.2 Contents

For an OpenClaw package transaction, the restore point includes at minimum:

- exact official OpenClaw package-root archive or filesystem snapshot;
- full type/mode/uid/gid/size/hash inventory and Merkle root;
- global npm prefix identity and mount/device identity;
- OpenClaw global bin-link state and target;
- relevant npm metadata and package-manager substrate identity;
- Node and npm executable realpaths, versions, and hashes where available;
- current official package generation: version, source commit, tree hash, inode/device identity;
- current Gateway process identity and running generation references;
- `.openclaw-*` sibling inventory with inode/device/type and live-reference status;
- strict `jobs.json` and protected-writer sentinels;
- protected-memory sentinels when adjacent to scope;
- restore method and exact recovery write set;
- verification receipt showing the snapshot can be read and reconstructs required critical surfaces.

### 10.3 Path and artifact safety

Restore creation and use SHALL:

- reject absolute/traversal archive entries;
- reject unsafe symlinks, hardlinks, devices, FIFOs, sockets, setuid/setgid content, and unexpected ownership;
- use `lstat`, dirfd-relative operations, and no-follow semantics for security-sensitive paths;
- verify same-filesystem assumptions before atomic rename;
- set umask `077`, directories `0700`, and evidence files `0600`;
- avoid placing secrets in receipts or logs;
- never use a mutable “latest” symlink as authority.

### 10.4 Recovery mechanism

Default package recovery is **verified filesystem reconstruction to a sibling staging path followed by an atomic rename**, because rerunning npm after npm-induced package damage can repeat the same failure.

A checksum-pinned offline npm reinstall is allowed only when:

- the package-manager substrate is independently coherent;
- the authority envelope explicitly allows that method;
- no staging collision or process-reference ambiguity exists;
- the candidate is the verified restore artifact; and
- the same postcheck and guard gates apply.

## 11. Durable journal and receipt model

Transaction truth SHALL be an append-only event journal plus derived projections.

### 11.1 Event journal

Each event includes:

```json
{
  "schema": "critical_apply.event.v2",
  "transaction_id": "...",
  "sequence": 17,
  "event_type": "MUTATION_RELEASED",
  "phase": "APPLY_RUNNING",
  "wall_time_utc": "...",
  "monotonic_ns": 0,
  "boot_id": "...",
  "actor": "critical_applyd",
  "payload_sha256": "...",
  "previous_event_sha256": "...",
  "event_sha256": "..."
}
```

The journal is hash-chained, sequence-checked, append-only, and fsynced at critical transitions. `transaction.json` is a projection, never the sole authority.

### 11.2 Atomic receipt writes

Every critical receipt SHALL be written as:

1. create a new temporary file in the destination directory;
2. write canonical JSON;
3. `fsync` the file;
4. atomic rename;
5. `fsync` the parent directory;
6. append and fsync the corresponding journal event.

Partial JSON, missing sequence, hash-chain break, or projection mismatch produces `EVIDENCE_TAMPERED_OR_INCOMPLETE_HOLD`.

### 11.3 Terminal seal

Finalization closes logs, hashes all governed artifacts, writes a non-circular canonical evidence manifest, and then writes a terminal seal containing the manifest hash and journal head hash. Status readers must validate the seal before reporting a terminal PASS.

## 12. Receipt-before-mutation launch gate

The current design requirement “write `apply-start.json` before exec with the child PID” is impossible without a launch gate, because the PID does not exist before spawn.

HRL-3 therefore uses four receipts:

1. `apply-intent.json` — exact argv, cwd, uid/gid, umask, executable realpath/hash, environment allowlist/hash, candidate hash, and authority hash; written before spawn.
2. `apply-spawned-blocked.json` — child PID, start ticks, PGID/cgroup, boot ID, and blocked-gate identity; written after spawn while the child cannot mutate.
3. `apply-release.json` — final precondition revalidation, approval consumption, and release decision; written and fsynced before the gate opens.
4. `apply-exit.json` — exit code/signal/timing and closed log references.

Implementation pattern:

```text
observer forks child
child blocks on inherited gate before execve
observer records PID/start-ticks/cgroup and fsyncs receipt
observer revalidates and writes release receipt
observer opens gate
child execves exact argv with no shell
```

If the observer dies before release, the blocked child is killed or reconciled as `APPROVED_NOT_STARTED`; no mutation occurred. If it dies after release, startup reconciliation SHALL never re-execute the apply. It observes or terminates the existing cgroup, performs postcheck, and invokes authorised recovery if required.

## 13. Process identity and quiescence

PID alone is insufficient. Every relevant process identity includes:

- PID;
- `/proc/<pid>/stat` start ticks;
- boot ID;
- cgroup path;
- UID/GID;
- cmdline hash;
- executable inode/device/realpath;
- service unit identity where available.

The observer SHALL use cgroup or equivalent descendant tracking. Before recovery changes package paths, the apply process group/cgroup must be proven quiescent. Permission-denied, PID-reuse ambiguity, escaped descendants, or unstable process scans fail closed.

`.openclaw-*` process-reference inspection must cover:

- maps;
- file descriptors;
- cwd;
- root;
- executable;
- cmdline arguments;
- cgroup membership; and
- service process inventory.

Live-referenced hidden generations are never moved or deleted.

## 14. Package generation model

The OpenClaw npm plugin SHALL report a generation vector:

| Generation | Meaning |
|---|---|
| `G_candidate` | checksum-pinned package being applied |
| `G_restore` | pre-apply verified restore generation |
| `G_official` | package at the official global npm path |
| `G_running` | code generation referenced by the running Gateway |
| `G_staging[]` | hidden `.openclaw-*` or other sibling generations |

Each generation records version, source commit, critical-surface hash, tree/Merkle hash, inode/device, and process references where applicable.

A successful package-only apply commonly ends with:

```text
G_official = G_candidate
G_running  = G_restore or prior generation
terminal   = PASS_PACKAGE_INSTALLED_HOLD_FOR_SEPARATE_RESTART
```

This intentional mixed generation is not itself package corruption. It becomes a restart precondition and must be clearly reported.

## 15. State classification

The observer SHALL classify independent axes before deriving a terminal:

### 15.1 Execution axis

- NOT_STARTED
- RUNNING
- EXIT_ZERO
- EXIT_NONZERO
- SIGNALLED
- TIMEOUT_KILLED
- EXIT_UNKNOWN

### 15.2 Official package axis

- MISSING
- EMPTY
- INCOMPLETE
- COHERENT_PRE_GENERATION
- COHERENT_CANDIDATE_GENERATION
- COHERENT_OTHER_GENERATION
- UNKNOWN

### 15.3 Package-manager substrate axis

- COHERENT
- DEGRADED
- BROKEN
- UNKNOWN

### 15.4 Guard axis

- UNCHANGED
- ALLOWED_DRIFT
- FORBIDDEN_DRIFT
- UNKNOWN

### 15.5 Recovery axis

- NOT_REQUIRED
- AUTHORISED_PENDING
- PASS
- FAIL
- BLOCKED
- NOT_AUTHORISED

A nonzero installer exit with `G_official = G_candidate` is not automatically rolled back; it is `APPLY_EFFECTIVE_EXIT_NONZERO_HOLD` unless guard or coherence checks fail. A nonzero exit with the exact pre-state restored and all write/guard sentinels unchanged may be `FAIL_SAFE_NO_MUTATION`. That terminal is forbidden unless equality is proven across the complete declared write and guard sets.

## 16. Automatic recovery policy

Recovery evaluation runs when any of these occur:

- apply exits nonzero or by signal;
- apply times out;
- observer restarts with a released but unfinalized transaction;
- postcheck is non-PASS after exit zero;
- official root is missing, empty, incomplete, unknown, or a forbidden generation;
- bin link or npm metadata is incoherent;
- guard drift is detected.

Recovery SHALL NOT begin until the apply cgroup is quiescent.

### 16.1 Decision matrix

| Observed state | Action |
|---|---|
| Apply not released | Cancel blocked child; `APPROVED_NOT_STARTED`; no recovery |
| Exact pre-state and all write/guard sentinels unchanged | `FAIL_SAFE_NO_MUTATION`; no restore |
| Candidate coherent, guards unchanged, exit nonzero | Preserve logs; `APPLY_EFFECTIVE_EXIT_NONZERO_HOLD`; no blind rollback |
| Official root missing/empty/incomplete; restore bound and valid | Preserve/quarantine incomplete official root if safe; reconstruct official root from restore point; verify |
| Official root damaged; live hidden generation referenced | Leave hidden generation untouched; restore only official path; no restart |
| Inactive valid staging collision | Atomically quarantine only if necessary, within recovery authority; never delete |
| Package-manager substrate broken | Use authorised filesystem restore; do not invoke npm |
| Restore artifact invalid/substituted or was stale at mutation release | `ROLLBACK_FAIL_OPERATOR_REQUIRED`; no restart |
| Process/cgroup or path state unknown | `RECOVERY_BLOCKED_STATE_UNKNOWN`; no mutation |
| Guard set has forbidden drift | Preserve evidence; recover only declared write set; terminal operator HOLD even if package restoration passes |

Recovery is at most once automatically. Re-entry is idempotent: if recovery receipts show the action already committed, the observer verifies its result and never repeats it blindly.

## 17. Concurrency, locks, and fencing

The observer holds:

1. a global critical-apply OS lock;
2. ordered per-surface locks;
3. a transaction generation/fencing token.

The lock is a held kernel lock (`flock` or equivalent), not merely a JSON file. The receipt records holder identity, but the file does not create safety by itself.

Precheck SHALL detect concurrent npm, OpenClaw install/recovery, Gateway restart, package-root writer, or another critical apply. It SHALL not kill or override them automatically.

Stale locks are manual-only in v1 and require a separate read-only reconciliation report proving:

- holder process identity is gone;
- no mutation cgroup remains;
- no unfinalized released transaction exists;
- evidence journal is consistent;
- production pre-state is classified.

## 18. Resource and evidence safety

Before mutation release, the observer SHALL verify:

- sufficient free bytes and inodes for logs, restore staging, quarantine, and evidence;
- writable evidence and restore roots;
- stable mount/device identity;
- open-file and process limits;
- bounded stdout/stderr size policy;
- timeout and kill policy;
- clock sanity and boot ID;
- receipt fsync test.

A reserved emergency evidence file SHOULD be preallocated. On `ENOSPC`, it can be released to write a terminal failure receipt. If durable evidence cannot be guaranteed before mutation, apply is blocked.

Secrets, tokens, provider credentials, full environment dumps, and sensitive config values SHALL NOT be written to logs or receipts. Only an explicit allowlist and redacted hashes are recorded.

## 19. OpenClaw package substrate policy

Before package apply, the plugin SHALL verify:

- canonical Node and npm executable paths and versions;
- expected global prefix;
- no shell alias/function substitution;
- official OpenClaw path is exactly the authorised direct child of the expected global `node_modules`;
- candidate is a regular non-symlink file with exact SHA-256, package name, version, source commit, and safe archive contents;
- required critical surfaces are derived from a pinned authority manifest, with built-in minimums;
- global bin link points to the expected official package surface;
- no unrelated global package mutation is authorised;
- install is offline and registry/provider network access is forbidden;
- npm audit/fund/update-notifier and other uncontrolled network side effects are disabled;
- no active package-manager operation conflicts with the transaction.

Postcheck compares the entire relevant global-prefix inventory and fails on unrelated package or link changes.

## 20. Restart boundary

Package apply never restarts Gateway.

A restart transaction:

- has a new transaction ID, nonce, approval, restore point, locks, and terminal seal;
- consumes the sealed package-apply result as a precondition only;
- captures old and new PID/start-ticks/cgroup identities;
- proves the new process maps the intended official package generation;
- performs bounded systemd/service, port, HTTP, and WebSocket readiness checks;
- does not call providers or delivery surfaces;
- classifies HTTP warnings separately from package corruption;
- has its own bounded restart recovery policy.

No package rollback is triggered solely by an HTTP or provider-level warning unless the restart transaction’s policy explicitly proves package corruption.

## 21. Functional smoke boundary

Functional smoke is a third transaction. It requires explicit target, content, provider/delivery authority, and data-handling rules.

A smoke failure is classified in the provider, route, control-plane, or delivery domain. It does not automatically trigger package reinstall or rollback.

## 22. Universal Runtime Kernel plugin contract

The core critical apply engine is generic only at the policy level; it is not an arbitrary command runner.

Every kernel mutation plugin declares:

```text
plugin identity and code hash
transaction type
read/write/recovery/guard/forbidden surface sets
typed input schema
preconditions
exact command builder or internal mutation primitive
post-state classifier
recovery planner
idempotency key
resource policy
network policy
required locks
expected predecessor seals
```

Initial and later plugins:

1. `openclaw_npm_package`
2. `gateway_restart`
3. `gateway_config_apply`
4. `cron_guarded_update`
5. `protected_memory_writer_state`
6. `model_route_apply`
7. other Universal Runtime Kernel surfaces only after independent fixture, shadow, and live-read-only promotion

A plugin cannot broaden authority at runtime. The core validates its declared surface set against policy before approval and again before mutation release.

## 23. Rehydration and reboot reconciliation

On service start or host boot, the observer scans all nonterminal transactions.

Rules:

- before release: cancel blocked children and require fresh commit validation;
- released and child/cgroup running: observe, do not re-execute;
- released and child gone without exit receipt: classify execution unknown, run postcheck, then authorised recovery if necessary;
- recovery intent durable but action uncertain: verify actual filesystem state and idempotency marker before any further write;
- terminal without valid seal: downgrade to evidence-integrity HOLD;
- no automatic restart, smoke, cron mutation, or provider call during reconciliation.

Rehydration proves safe classification; it does not imply automatic continuation across an authority boundary.

## 24. Required high-level state machine

```text
CREATED
  -> PREPARING
  -> RESTORE_POINT_SELECTED_OR_CREATED
  -> PRECHECK_PASS
  -> PLAN_SEALED
  -> AWAITING_APPROVAL
  -> APPROVAL_RECORDED
  -> COMMIT_LOCKS_ACQUIRED
  -> COMMIT_REVALIDATING
     -> PRECONDITION_DRIFT_BLOCKED
     -> COMMIT_VALIDATED
  -> APPLY_INTENT_DURABLE
  -> APPLY_CHILD_SPAWNED_BLOCKED
  -> FINAL_PRE_RELEASE_REVALIDATION
     -> RELEASE_BLOCKED
     -> APPROVAL_CONSUMED
  -> MUTATION_RELEASED
  -> APPLY_RUNNING
  -> APPLY_EXIT_OBSERVED_OR_UNKNOWN
  -> POSTCHECK
     -> PRIMARY_STATE_PASS
     -> RECOVERY_DECIDING
        -> RECOVERY_NOT_REQUIRED
        -> RECOVERY_BLOCKED
        -> RECOVERY_INTENT_DURABLE
        -> RECOVERY_RUNNING
        -> POST_RECOVERY_CHECK
  -> FINALIZING
  -> TERMINAL_SEALED
```

Every transition has an allowed predecessor set, required receipt, invariant checks, and failure terminal. Unknown transitions fail closed.

## 25. Minimum terminal set

- CANCELLED_NO_APPROVAL
- APPROVAL_EXPIRED_REPREPARE_REQUIRED
- APPROVED_NOT_STARTED
- PRECONDITION_DRIFT_BLOCKED
- APPLY_STATE_UNKNOWN_OPERATOR_REQUIRED
- FAIL_SAFE_NO_MUTATION
- APPLY_EFFECTIVE_EXIT_NONZERO_HOLD
- PASS_PACKAGE_INSTALLED_HOLD_FOR_SEPARATE_RESTART
- FAIL_MUTATION_PARTIAL_RECOVERY_REQUIRED
- RECOVERY_PASS_HOLD_FOR_SEPARATE_RESTART
- RECOVERY_PASS_WITH_GUARD_WARNING_OPERATOR_HOLD
- RECOVERY_BLOCKED_STATE_UNKNOWN
- ROLLBACK_FAIL_OPERATOR_REQUIRED
- EVIDENCE_TAMPERED_OR_INCOMPLETE_HOLD
- PASS_CONTROLLED_GATEWAY_RESTART
- PASS_FUNCTIONAL_SMOKE
- FUNCTIONAL_SMOKE_FAIL_NO_PACKAGE_RECOVERY

Terminal names may be extended, but their semantics may not be weakened.

## 26. Production-readiness gates

The critical apply substrate is not production-ready until it proves:

1. HRL-3 supervisor bootstrap and restart reconciliation;
2. atomic journal, receipt, projection, manifest, and seal integrity;
3. launch-gate receipt-before-mutation;
4. stale approval, candidate drift, code drift, restore drift, and pre-state drift rejection;
5. restore freshness at mutation release and continued transaction-bound eligibility afterward;
6. process/cgroup identity, PID reuse, escaped descendant, and quiescence handling;
7. missing/empty/incomplete/coherent/unknown package classification;
8. generation-vector classification for official, running, staging, candidate, and restore generations;
9. idempotent recovery and crash injection at every recovery boundary;
10. disk-full, fsync-failure, clock-change, reboot, and observer-SIGKILL tests;
11. unrelated global-package, cron, protected-memory, config, route, and provider guards;
12. strict apply/restart/smoke transaction separation;
13. shadow end-to-end recovery on an isolated copy of current OpenClaw;
14. live read-only precheck and restore-point-only transaction;
15. owner-approved package-only production canary.

Failure of any gate blocks production mutation.

## 27. Global operating rule

For every future request containing “apply”, “deploy”, “install”, “repair”, “restart”, “roll back”, “restore”, “activate”, “migrate”, “mutate runtime”, “cron change”, “route change”, or “critical apply”:

1. classify whether it is critical;
2. if critical, require this architecture;
3. if the HRL-3 runner or required plugin is unavailable or unproven, stop at architecture/preparation;
4. never improvise a foreground mutation;
5. never infer authority from a previous transaction or conversational intent.

## 28. Locked non-action statement

This architecture strengthens the contract only. It performs and authorises no deploy, install, restart, cron mutation, provider call, protected-memory change, package-root mutation, service activation, or recovery action.
