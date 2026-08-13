# Critical Apply Supervisor-Owned Append-Only Event Journal

**Low-Level Design and Implementation Plan**  
**Version:** 1.0-draft  
**Date:** 2026-08-13 (Australia/Sydney)  
**Status:** DESIGN ONLY — no runtime, Gateway, configuration, provider, or production mutation  
**Owner:** Stick  
**Prepared by:** Stickbot

---

## 0. Executive decision

Replace the current multi-writer, multi-projection observation model with a **durable supervisor that exclusively owns one append-only event journal per transaction**.

The journal becomes the sole operational source of truth. A deterministic canonical reducer derives all human- and machine-readable state from a committed journal prefix. Files such as `status.json`, `summary.json`, the run registry, heartbeat, watchdog, and notification state become **rebuildable projections**, never competing authorities.

The central invariant is:

> A transaction state exists because the supervisor durably committed an event—not because a child process, watcher, registry row, PID probe, or status file said it exists.

This directly removes the R18-R4 failure mode in which semantic evidence had terminalised HOLD while the harness projection remained `RUNNING`.

### Recommended implementation shape

- One detached `critical_apply_supervisor.py` process per transaction.
- One supervisor-exclusive lock and one journal writer.
- Child processes submit bounded event proposals over a private Unix-domain socket.
- Every accepted event is authenticated to a spawned process identity and role.
- Critical event submission uses **commit-before-ack** semantics.
- The canonical reducer is a pure deterministic function of a verified journal prefix plus hash-bound registered artifacts.
- Terminal state is monotonic and seal-bound.
- Independent health checking reads the journal and verifies supervisor/process identity; it does not write canonical state.
- Owner notification is an orthogonal plane with its own receipts and cannot rewrite semantic outcome.

---

## 1. Problem statement

The existing harness has made important advances—detached execution, exact-path registration, independent alarm wiring, semantic reduction, hash-chained events, and terminal seals—but authority remains split:

1. The harness writes `harness-artifacts/status.json` and a mutable registry row.
2. The semantic coordinator and reducer write root `STATUS.json`, `SUMMARY.json`, manifest, and seal.
3. Watchers infer semantic paths from mutable registry data or command arguments.
4. Child-produced artifacts are discovered and later appended to a child-owned journal.
5. PID lifecycle, harness lifecycle, semantic state, alarm state, and owner-delivery state can disagree.
6. The existing `Journal.append()` is not safe for concurrent writers: sequence and predecessor are read before append without an exclusive writer lock.
7. `events.jsonl` and `HEAD.json` form a two-file commit protocol with crash windows.
8. Mutable registry replacement can lose concurrent updates.
9. A semantic terminal may exist while a stale harness projection remains `RUNNING` indefinitely.

The desired architecture must make those contradictions representable as health findings, but impossible as competing canonical states.

---

## 2. Scope

### 2.1 In scope

- Transaction-supervisor lifecycle.
- Supervisor-owned append-only journal.
- Event ingress and acknowledgements.
- Process identity, role, and lease enforcement.
- Exact-path artifact registration and hash binding.
- Canonical deterministic reducer.
- Semantic, lifecycle, recovery, notification, and owner-closeout state.
- Crash/torn-write recovery.
- Independent health checker and alarm integration.
- Evidence manifest and terminal seal.
- Compatibility projections for existing harness consumers.
- Adversarial tests, health gates, rollout, rollback, and promotion.

### 2.2 Out of scope for this build

- Changing Critical Apply product policy.
- Automatically authorizing a production mutation.
- Combining install/apply, Gateway restart, and provider smoke.
- Reusing or retrying consumed one-call model authority.
- Gateway/config/provider/model route changes.
- Telegram delivery implementation beyond consuming an existing, explicitly authorized notification adapter.
- Cross-host distributed consensus.

The first production version is deliberately **single host, one transaction root, one supervisor writer**.

---

## 3. Design principles

1. **Single canonical writer.** Only the supervisor may append canonical events.
2. **Journal first.** Durable event commit precedes any projection update or critical acknowledgement.
3. **Reducer purity.** The reducer does no process control, networking, provider calls, notifications, or mutation.
4. **Projection disposability.** Deleting `status.json` must be recoverable by replay.
5. **Terminal monotonicity.** Once a semantic terminal decision is committed, it cannot return to `RUNNING`.
6. **Identity over PID.** Process identity is PID + `/proc` start ticks + boot ID + executable/script identity + supervisor epoch.
7. **Explicit ownership.** Every mutable directory and file has one owning component.
8. **Exact paths only.** No recursive discovery is required for correctness.
9. **Bounded work.** All reads, event sizes, artifact sizes, waits, scans, and retries have hard limits.
10. **Fail closed.** Ambiguous authority, corrupt journal, lost lock, conflicting event, or invalid artifact can never produce PASS.
11. **Notification separation.** Semantic PASS does not prove owner-visible delivery; delivery failure cannot erase semantic facts.
12. **No foreground critical apply.** Launch preparation may be foreground; execution remains detached and supervised.

---

## 4. Trust and authority model

### 4.1 Authority order

1. Verified committed journal prefix.
2. Canonical reducer result for that exact prefix.
3. Manifest and terminal seal binding that prefix and registered artifacts.
4. Independent checker receipt binding journal head, reducer version, and seal.
5. Rebuildable projections.
6. Process-lifecycle probes.
7. Notification and owner-visible delivery receipts.

PID state never outranks a committed semantic terminal.

### 4.2 Component roles

| Component | May append journal? | May control children? | May derive projections? | May notify owner? |
|---|---:|---:|---:|---:|
| Supervisor | Yes, exclusively | Yes | Invokes reducer | No direct provider send by default |
| Event client library | No; submits proposals | No | No | No |
| Worker/coordinator | No | Only explicitly delegated descendants | No | No |
| Canonical reducer | No | No | Yes | No |
| Independent checker | No | No | Read-only verification only | No |
| Alarm watcher | No | No | Reads checker/reducer outputs | May invoke authorized notification adapter |
| Notification adapter | No | No | No | Yes, within explicit authority |
| Compatibility projector | No | No | Yes, from reducer output only | No |

### 4.3 Single-owner filesystem table

| Path | Owner | Write rule |
|---|---|---|
| `journal/events-000001.jsonl` | Supervisor | Append only |
| `journal/CHECKPOINT.json` | Supervisor | Atomic replace; cache only |
| `journal/LOCK` | Supervisor | Held open with exclusive advisory lock |
| `journal/RECOVERY.json` | Recovering supervisor | Create once per recovery epoch |
| `control/events.sock` | Supervisor | Create/remove only under lease |
| `control/supervisor.json` | Supervisor | Atomic projection |
| `registration/EXACT-PATHS.json` | Prepare phase; then immutable | Create once; supervisor verifies hash |
| `artifacts/<role>/...` | Registered role owner | Atomic create/replace according to registration |
| `projections/*.json` | Projection writer invoked by supervisor | Atomic replace; rebuildable |
| `seal/MANIFEST.json` | Supervisor after reducer terminal | Atomic create once |
| `seal/TERMINAL-SEAL.json` | Supervisor | Atomic create once |
| `notifications/*` | Notification adapter | Exact registered paths only |
| `logs/*` | Supervisor stream capturer | Append only with byte caps |

A component must not pre-create another component’s mutable directory unless the contract explicitly says it owns initialization. This rule prevents the duplicate `nonce-ledger/` creation defect.

---

## 5. Transaction directory layout

```text
<transaction-root>/
  contract/
    TRANSACTION.json
    AUTHORITY.json
    COMMAND.json
    TIMEOUT-BUDGET.json
    OWNERSHIP.json
  registration/
    EXACT-PATHS.json
    ROLES.json
    CONTRACT-SEAL.json
  journal/
    LOCK
    events-000001.jsonl
    CHECKPOINT.json
    RECOVERY-<epoch>.json
    emergency-000001.bin
  control/
    events.sock
    supervisor.json
    children.json
  artifacts/
    supervisor/
    worker/
    checker/
    watcher/
    recovery/
  logs/
    child.stdout.log
    child.stderr.log
    supervisor.log
  projections/
    status.json
    summary.json
    health.json
    process-lifecycle.json
    notification.json
    compatibility-harness-status.json
    compatibility-registry-row.json
  seal/
    MANIFEST.json
    TERMINAL-SEAL.json
    INDEPENDENT-VERIFICATION.json
  notifications/
    ALERT.json
    ALERT-RESULT.json
    OWNER-DELIVERY-RECEIPT.json
  closeout/
    FINAL-REPORT.json
    MEMORY-HANDOFF.json
```

### Filesystem requirements

- Root and mutable directories: owner-only, mode `0700`.
- Journal, contracts, projections, and receipts: mode `0600` unless a narrower execution environment requires read-group access.
- `lstat()` every registered ancestor; reject symlink traversal.
- Resolve and verify device/inode for transaction root at prepare, supervisor acquisition, and seal.
- Reject hard-linked canonical files (`st_nlink != 1`).
- Use same-filesystem temp file + `fsync(file)` + `rename()` + `fsync(parent)` for atomic projections.
- Journal append uses `O_APPEND|O_WRONLY|O_CLOEXEC|O_NOFOLLOW` where supported.
- Never use recursive scans to find governing artifacts.

---

## 6. Supervisor lifecycle

### 6.1 Bootstrap sequence

```text
PREPARE_CONTRACT
  -> VERIFY_TRANSACTION_ROOT
  -> VERIFY_CONTRACT_SEAL
  -> ACQUIRE_EXCLUSIVE_LOCK
  -> RECOVER_JOURNAL_PREFIX
  -> CREATE_SUPERVISOR_EPOCH
  -> OPEN_EVENT_SOCKET
  -> COMMIT SUPERVISOR_STARTED
  -> SPAWN_AND_VERIFY_INDEPENDENT_WATCHER
  -> COMMIT WATCHER_ARMED
  -> VERIFY_AUTHORITY_BOUNDARY
  -> COMMIT AUTHORITY_BOUND
  -> SPAWN_CHILD
  -> VERIFY_CHILD_IDENTITY
  -> COMMIT CHILD_STARTED
  -> RUN/OBSERVE/RECOVER
  -> COMMIT TERMINAL_DECISION
  -> REDUCE + MANIFEST + SEAL
  -> COMMIT RUN_SEALED
  -> REQUEST NOTIFICATION
  -> COMMIT NOTIFICATION_RESULT
  -> CLEANUP OWNED CHILDREN
  -> COMMIT SUPERVISOR_CLOSED
  -> RELEASE LOCK
```

### 6.2 Supervisor lease

The supervisor acquires an exclusive `flock(LOCK_EX|LOCK_NB)` on `journal/LOCK` and keeps the file descriptor open for its lifetime.

`control/supervisor.json` records:

- schema version;
- transaction ID;
- supervisor epoch UUID;
- PID;
- `/proc/<pid>/stat` start ticks;
- boot ID;
- executable realpath and SHA-256;
- source/contract SHA-256;
- UID/GID;
- process group/session IDs;
- acquired UTC and monotonic timestamp;
- journal device/inode;
- last committed sequence/hash;
- lifecycle state.

A second supervisor must fail immediately while the lock is held. A takeover after process death requires:

1. lock acquisition;
2. old identity proven dead or from a different boot ID;
3. journal recovery PASS;
4. no live owned process group left ambiguous;
5. recovery event committed under a new epoch before further action.

Time expiry alone never transfers authority.

---

## 7. Event ingress

### 7.1 Transport

Use an owner-only Unix-domain socket at `control/events.sock`.

Preferred Linux transport: `AF_UNIX` + `SOCK_SEQPACKET` to preserve message boundaries. If unavailable, use `SOCK_STREAM` with an unsigned 32-bit big-endian length prefix and exact reads.

Socket rules:

- mode `0600`;
- path confined to transaction root;
- `SO_PEERCRED` required;
- peer UID must match supervisor UID;
- peer PID must match a supervisor-spawned, currently registered process identity;
- message maximum: 64 KiB default, 256 KiB absolute;
- JSON UTF-8, duplicate keys rejected;
- unknown fields rejected for critical event types;
- no raw secrets or arbitrary environment dumps.

### 7.2 Commit-before-ack protocol

Client sends:

```json
{
  "schema": "critical_apply.event_proposal.v1",
  "transaction_id": "...",
  "supervisor_epoch": "...",
  "event_id": "uuid-v4",
  "role": "worker",
  "event_type": "ARTIFACT_READY",
  "client_sequence": 7,
  "payload": {},
  "artifact_refs": []
}
```

Supervisor performs:

1. framing and schema validation;
2. peer credential and role validation;
3. epoch and transaction binding;
4. role/event allowlist validation;
5. event ID deduplication;
6. artifact path/hash/size/mode validation when referenced;
7. canonical event construction;
8. append full line;
9. `fdatasync()` journal;
10. update checkpoint projection atomically;
11. return committed sequence and event hash.

Response:

```json
{
  "schema": "critical_apply.event_ack.v1",
  "status": "COMMITTED",
  "event_id": "...",
  "journal_sequence": 42,
  "event_sha256": "...",
  "supervisor_epoch": "..."
}
```

### 7.3 Idempotence

- `event_id` is globally unique within the transaction.
- Retrying the same `event_id` with the same canonical proposal hash returns the original acknowledgement.
- Same `event_id` with different bytes commits `INTEGRITY_CONFLICT_DETECTED` and forces HOLD/FAIL according to phase.
- Critical actions must not occur until the prerequisite event acknowledgement is received.

Examples:

- `APPLY_START_AUTHORIZED` must be committed before spawning an apply process.
- `PROVIDER_CALL_RESERVED` must be committed before initiating the call.
- `RECOVERY_ACTION_AUTHORIZED` must be committed before restore begins.

### 7.4 Event role allowlist

| Role | Allowed proposal classes |
|---|---|
| worker | phase/checkpoint, artifact-ready, bounded progress, requested terminal evidence |
| checker | checker receipt only |
| watcher | watcher readiness and observation receipt only |
| notification adapter | notification attempt/result only |
| recovery plugin | precheck/postcheck/recovery evidence only |

Children never submit canonical `TERMINAL_DECISION`, `RUN_SEALED`, `SUPERVISOR_CLOSED`, lock, or authority events. Those are supervisor-only.

---

## 8. Journal format and durability

### 8.1 Canonical event schema

```json
{
  "schema": "critical_apply.journal_event.v1",
  "transaction_id": "uuid",
  "run_id": "human-stable-id",
  "supervisor_epoch": "uuid",
  "sequence": 42,
  "event_id": "uuid",
  "event_type": "CHILD_EXITED",
  "actor": {
    "role": "supervisor",
    "pid": 1234,
    "start_ticks": "98765",
    "boot_id": "uuid",
    "uid": 1000
  },
  "phase": "EXECUTION",
  "wall_time_utc": "2026-08-13T00:00:00.000000Z",
  "monotonic_ns": 123456789,
  "previous_event_sha256": "64-lower-hex",
  "contract_sha256": "64-lower-hex",
  "payload_sha256": "64-lower-hex",
  "payload": {},
  "artifact_refs": [
    {
      "path_id": "child_exit",
      "relative_path": "artifacts/supervisor/CHILD-EXIT.json",
      "sha256": "64-lower-hex",
      "bytes": 123,
      "mode": "0600",
      "schema": "critical_apply.child_exit.v1"
    }
  ],
  "event_sha256": "64-lower-hex"
}
```

Hash canonicalization:

- UTF-8;
- RFC 8785/JCS-compatible canonical JSON or a frozen equivalent with test vectors;
- no NaN/Infinity;
- integer range bounded to signed 64-bit unless encoded as string;
- `event_sha256` hashes all event fields except itself;
- payload hash binds canonical payload bytes.

### 8.2 Journal commit authority

A **complete, schema-valid, hash-chain-valid line that is present after recovery in the fsynced journal prefix is committed authority**. `CHECKPOINT.json` is an acceleration cache, not a second commit authority.

Recovery rules:

- valid prefix + zero tail: PASS;
- valid prefix + incomplete final line: quarantine/truncate torn tail under recovery authority, emit recovery event;
- valid prefix + complete duplicate idempotent event after stale checkpoint: retain and rebuild checkpoint;
- hash/sequence break inside complete prefix: `JOURNAL_CORRUPT`, no PASS, no automatic mutation;
- checkpoint ahead of journal: checkpoint discarded and rebuilt; health HOLD;
- checkpoint behind journal: replay and rebuild;
- unexpected second journal file/segment: HOLD unless segment rotation event binds it.

### 8.3 Segmenting

Version 1 may use one segment capped at 64 MiB. Rotation is allowed only through supervisor events:

1. commit `SEGMENT_ROTATION_INTENT`;
2. fsync current segment;
3. create next segment with `O_EXCL`;
4. first event binds previous segment terminal hash;
5. fsync file and directory;
6. update checkpoint projection.

No segment deletion occurs before an independently verified archival policy exists.

### 8.4 Disk-full emergency evidence

Prepare a fixed-size emergency segment before authority is armed. Recommended size: 1 MiB with fixed framed slots, owner-only and fsynced. It may record only:

- journal write failure;
- process identity;
- phase;
- mutation-started flag;
- child termination/recovery action;
- terminal emergency classification.

Slots are write-once. Tests must prove emergency records remain readable after simulated `ENOSPC`. If the reserve cannot be created and verified, launch HOLDs.

---

## 9. Event taxonomy

### 9.1 Contract and authority

- `TRANSACTION_PREPARED`
- `CONTRACT_VERIFIED`
- `SUPERVISOR_STARTED`
- `SUPERVISOR_RECOVERED`
- `WATCHER_ARMED`
- `AUTHORITY_BOUND`
- `AUTHORITY_REJECTED`
- `CALL_AUTHORITY_RESERVED`
- `CALL_AUTHORITY_CONSUMED`
- `NONCE_RETIRED`

### 9.2 Process lifecycle

- `CHILD_SPAWN_INTENT`
- `CHILD_STARTED`
- `CHILD_CHECKPOINT`
- `CHILD_EXITED`
- `CHILD_SIGNAL_SENT`
- `CHILD_REAPED`
- `OWNED_PROCESS_CLEANUP_COMPLETE`
- `UNOWNED_PROCESS_CONFLICT`

### 9.3 Execution and recovery

- `PRECHECK_COMPLETE`
- `APPLY_START_AUTHORIZED`
- `APPLY_STARTED`
- `APPLY_EXITED`
- `POSTCHECK_COMPLETE`
- `RECOVERY_DECISION`
- `RECOVERY_ACTION_AUTHORIZED`
- `RECOVERY_STARTED`
- `RECOVERY_EXITED`
- `RECOVERY_POSTCHECK_COMPLETE`

### 9.4 Evidence and health

- `ARTIFACT_READY`
- `CHECKER_COMPLETE`
- `WATCHER_OBSERVATION`
- `TIMEOUT_REACHED`
- `INTEGRITY_CONFLICT_DETECTED`
- `JOURNAL_RECOVERY_COMPLETE`
- `HEALTH_CHECKPOINT`

### 9.5 Terminal and notification

- `TERMINAL_DECISION`
- `MANIFEST_CREATED`
- `TERMINAL_SEAL_CREATED`
- `RUN_SEALED`
- `NOTIFICATION_REQUESTED`
- `NOTIFICATION_SUBMITTED`
- `OWNER_DELIVERY_CONFIRMED`
- `OWNER_DELIVERY_UNKNOWN`
- `SUPERVISOR_CLOSED`

---

## 10. State model

Use orthogonal state planes instead of one overloaded status string.

### 10.1 Execution plane

```text
CREATED
 -> PREPARED
 -> ARMED
 -> AUTHORITY_BOUND
 -> STARTING
 -> RUNNING
 -> POSTCHECK
 -> RECOVERY (optional)
 -> TERMINAL_DECIDED
 -> SEALED
 -> CLOSED
```

### 10.2 Semantic result plane

- `UNDECIDED`
- `PASS`
- `HOLD`
- `FAIL`
- `ABORT`

Severity precedence for conflicting evidence:

```text
ABORT > FAIL > HOLD > PASS > UNDECIDED
```

The reducer may downgrade a proposed PASS to HOLD/FAIL. It may never upgrade committed terminal evidence through projection logic.

### 10.3 Process-health plane

- `NOT_STARTED`
- `ALIVE_VERIFIED`
- `EXITED_REAPED`
- `MISSING_IDENTITY_UNRESOLVED`
- `ORPHANED_OWNED_PROCESS`
- `CLEAN`

### 10.4 Notification plane

- `NOT_REQUESTED`
- `REQUESTED`
- `SUBMITTED`
- `DELIVERED_CONFIRMED`
- `DELIVERY_UNKNOWN`
- `DELIVERY_FAILED`

### 10.5 Recovery plane

- `NOT_REQUIRED`
- `DECISION_REQUIRED`
- `AUTHORIZED`
- `RUNNING`
- `PASS`
- `FAIL_OPERATOR_REQUIRED`

### 10.6 Terminal invariants

- One canonical `TERMINAL_DECISION` per epoch lineage.
- Any conflicting later decision is an integrity fault, never a replacement.
- `RUN_SEALED` requires terminal decision, deterministic reduction, manifest, terminal seal, and owned-process cleanup classification.
- Notification may continue after `RUN_SEALED` but cannot alter semantic result.
- `SUPERVISOR_CLOSED` requires no live owned child or an explicit unresolved-orphan terminal classification.

---

## 11. Canonical reducer

### 11.1 Interface

```bash
critical_apply_reducer.py \
  --contract contract/TRANSACTION.json \
  --journal journal/events-000001.jsonl \
  --through-sequence <N> \
  --output-dir projections.staging/
```

Inputs are read-only. Outputs are deterministic bytes for the same:

- reducer version/hash;
- contract hash;
- journal prefix sequence/hash;
- hash-bound artifact bytes.

### 11.2 Reducer responsibilities

1. Validate contract and exact-path registration.
2. Validate journal schema, chain, sequence, event IDs, actor roles, and epochs.
3. Validate state transitions.
4. Validate referenced artifacts by exact registered path, hash, size, mode, schema, and confinement.
5. Compute each orthogonal state plane.
6. Enforce policy predicates needed for PASS.
7. Produce canonical status, summary, health findings, and manifest inputs.
8. Refuse PASS on unknown critical event/schema versions.

### 11.3 Reducer must not

- inspect arbitrary processes;
- infer paths from command text;
- search directories recursively;
- call providers or notification APIs;
- mutate journal or artifacts;
- use wall-clock freshness as sole authority;
- trust child self-certification without supervisor-bound identity and artifact hashes.

### 11.4 PASS predicate

PASS requires, at minimum:

- contract and authority binding valid;
- supervisor lease history valid;
- watcher armed before child start;
- expected process identities and exits valid;
- no timeout/integrity conflict/unresolved orphan;
- execution, checker, watcher, postcheck, and cleanup predicates pass;
- one-call ledger/nonce/transport receipt predicates pass when applicable;
- every governing artifact journal-bound;
- no unregistered governing artifact required for decision;
- privacy and mutation-sentinel gates pass;
- terminal manifest and seal verify.

### 11.5 Projection generation

Reducer produces under a staging directory:

- `status.json`
- `summary.json`
- `health.json`
- `process-lifecycle.json`
- `notification.json`
- compatibility files

Supervisor verifies output hashes, then atomically swaps each projection. Partial projection publication can never alter journal authority; replay repairs it.

---

## 12. Manifest and terminal seal

### 12.1 Terminal sequence

1. Supervisor commits `TERMINAL_DECISION` at sequence `N`.
2. Reducer replays through `N` and emits deterministic terminal projections.
3. Supervisor creates `MANIFEST.json` binding:
   - transaction/contract hash;
   - reducer identity/hash;
   - journal segment device/inode/size;
   - sequence `N` and event hash;
   - all governing artifact hashes/sizes/modes/schemas;
   - terminal projection hashes;
   - ownership and process-cleanup receipts.
4. Supervisor creates `TERMINAL-SEAL.json` binding manifest bytes and semantic result.
5. Supervisor commits `RUN_SEALED`, referencing manifest and seal hashes.
6. Independent checker verifies the final journal prefix and seal and writes a noncanonical verification receipt.

### 12.2 Seal rules

- Create once with `O_EXCL`; never overwrite.
- Seal mismatch is terminal integrity failure.
- A stale compatibility `RUNNING` projection is automatically rebuilt from the sealed result.
- The seal binds semantic result; notification receipts are appended later and reported separately.

---

## 13. Health model

### 13.1 Liveness

Supervisor writes a lightweight liveness projection every 10–15 seconds and commits bounded `HEALTH_CHECKPOINT` events at phase boundaries or at most every 60 seconds during long phases.

Liveness fields:

- supervisor identity/epoch;
- last journal sequence/hash;
- current phase;
- current child identity;
- monotonic age;
- next checkpoint deadline;
- mutation-started flag;
- alarm identity/readiness;
- disk free and journal bytes;
- cleanup deadline.

Liveness projection is advisory. A verified terminal journal event always wins.

### 13.2 Readiness

The supervisor is ready to cross a mutation/call boundary only if:

- exclusive lock held;
- journal recovery PASS;
- contract and tool hashes valid;
- root/path/mode/symlink gates pass;
- free-space and emergency segment gates pass;
- event socket self-test passes;
- canonical reducer self-test passes;
- independent watcher is alive and readback-verified;
- exact semantic paths registered;
- restore point fresh and verified when required;
- required authority bound;
- no conflicting live transaction owns the same maintenance scope.

### 13.3 Dependency health

Dependencies are explicit and hash-bound:

- Python/runtime identity;
- reducer and supervisor identities;
- checker/watcher identities;
- target/plugin identity;
- filesystem device and free-space floor;
- `/proc` availability for process identity;
- notification adapter readiness, if authorized;
- restore point, if critical apply.

### 13.4 Staleness classification

Independent checker logic:

1. Verify terminal seal/journal first.
2. If terminal exists: report terminal regardless of PID/projection.
3. Else verify supervisor lock holder and full process identity.
4. If identity alive and checkpoint within deadline: RUNNING.
5. If identity alive but checkpoint overdue: DEGRADED/STUCK; alarm.
6. If identity missing: attempt journal recovery classification.
7. If mutation never started: `HOLD_SUPERVISOR_LOST_BEFORE_MUTATION`.
8. If mutation started and no terminal: `FAIL_ORPHANED_AFTER_MUTATION_RECOVERY_REQUIRED`.
9. Never leave canonical state as `RUNNING + pid_missing`.

---

## 14. Failure handling

| Failure | Required behavior |
|---|---|
| Child exits before registration | Commit exit; terminal HOLD; no inferred success |
| Supervisor crashes before mutation | Recovery supervisor verifies journal; HOLD unless safe resume contract explicitly permits |
| Supervisor crashes after mutation starts | Acquire lock only after old death; classify target state; enter bounded recovery decision |
| Journal torn tail | Preserve copy/hash; truncate only uncommitted incomplete tail; emit recovery event |
| Journal chain corruption | Stop; FAIL/HOLD integrity; no automatic mutation |
| Projection write fails | Journal remains authoritative; retry bounded; closeout HOLD if owner view cannot be rebuilt |
| Event socket unavailable | Critical client stops; no action without commit acknowledgement |
| Duplicate event ID/same payload | Return original ack |
| Duplicate event ID/different payload | Integrity conflict; terminal HOLD/FAIL |
| PID reused | Reject via start ticks/boot ID/executable mismatch |
| Lock lost or filesystem replaced | Stop mutation; terminate owned child if safe; terminal integrity failure |
| Disk free below floor before mutation | Launch HOLD |
| ENOSPC after mutation | Write emergency record; stop/kill bounded; invoke authorized recovery decision |
| Watcher dies before child start | Do not start child |
| Watcher dies during run | Commit degradation; terminal cannot PASS until watcher evidence is restored or policy says HOLD |
| Notification timeout | Semantic result preserved; notification `DELIVERY_UNKNOWN`; owner closeout HOLD on delivery plane |
| Reducer crash | Supervisor records failure; retry only identical local reducer within bounded count; never rerun provider/apply child |
| Conflicting terminal artifacts | Journal wins; integrity finding; no PASS |

---

## 15. Security and adversarial model

### Threats addressed

- competing supervisors;
- concurrent journal writers;
- forged child events;
- child role escalation;
- PID reuse;
- replay from prior supervisor epoch;
- symlink/hardlink/path escape;
- journal truncation or replacement;
- torn writes;
- stale checkpoints;
- unbounded payload/resource exhaustion;
- status/registry spoofing;
- notification spoofing;
- secret leakage into evidence;
- post-terminal mutation of governing artifacts;
- duplicate directory/file ownership;
- inherited file descriptors and process escape.

### Required controls

- exclusive writer lock;
- UDS peer credentials and spawn registry;
- per-role event allowlist;
- frozen contract hash on every event;
- path registration and `lstat` confinement;
- `O_NOFOLLOW`, `O_EXCL`, owner-only modes;
- hash-chain and deterministic canonicalization;
- bounded event/artifact/log sizes;
- secret redaction before commit;
- close-on-exec file descriptors;
- new process sessions and captured process groups;
- explicit child reap and cleanup receipt;
- privacy scanner against the final frozen package and generated fixtures.

The selected bounded scanner is the independently reviewed snapshot whose SHA-256 is:

`ce38bf7811561c096bfe72ef12fc799712986d77ff86cb62b8e099eedc481115`

---

## 16. Proposed modules and interfaces

```text
scripts/critical_apply/
  supervisor.py
  journal.py
  event_schema.py
  event_client.py
  process_identity.py
  path_guard.py
  reducer.py
  projections.py
  terminal_seal.py
  independent_checker.py
  alarm_watcher.py
  migrate_legacy.py
  cli.py
  plugins/
    base.py
    openclaw_npm_package.py
```

### CLI

```bash
critical-apply prepare --spec transaction-spec.json --root <root>
critical-apply validate --root <root>
critical-apply launch --root <root>
critical-apply status --root <root> --verify
critical-apply reduce --root <root> --through-sequence N
critical-apply recover --root <root> --classification-only
critical-apply seal --root <root>
critical-apply verify-seal --root <root>
critical-apply project-legacy --root <root>
```

`launch` starts the detached supervisor and exits only after receiving a durable `SUPERVISOR_STARTED` + `WATCHER_ARMED` readback. It does not claim the transaction passed.

### Python interfaces

```python
class JournalWriter:
    def recover(self) -> RecoveryResult: ...
    def append(self, event: EventProposal, actor: ActorIdentity) -> CommitAck: ...
    def checkpoint(self) -> JournalCheckpoint: ...

class CanonicalReducer:
    def reduce(self, contract: Contract, events: Sequence[Event], artifacts: ArtifactReader) -> ProjectionSet: ...

class Supervisor:
    def acquire(self) -> LeaseReceipt: ...
    def arm_watcher(self) -> WatcherReceipt: ...
    def spawn_child(self, role: str, argv: list[str]) -> ChildIdentity: ...
    def terminalise(self) -> TerminalReceipt: ...
```

---

## 17. Compatibility strategy

During migration, generate—but never trust—legacy shapes:

- harness `status.json`;
- registry row;
- root `STATUS.json`/`SUMMARY.json` variants;
- heartbeat/progress/watchdog files.

Each compatibility file includes:

```json
{
  "authority": "projection_only",
  "source_journal_sequence": 42,
  "source_journal_event_sha256": "...",
  "reducer_sha256": "...",
  "rebuildable": true
}
```

Legacy watcher reads must be changed to:

1. locate exact registered journal path;
2. run/read independent journal verification;
3. derive terminal;
4. only use compatibility projection for display.

No semantic path inference from command text remains after migration.

### Mandatory bridge repair before shadow/canary

Independent inspection found a concrete split-authority defect in the present launcher: explicit `--semantic-artifact-dir`, `--semantic-status-path`, and `--semantic-summary-path` are used when constructing completion-checker registration, but the mutable registry row is populated again from command-derived path inference. The watcher later consumes that registry row and can therefore fall back to harness lifecycle files instead of the registered semantic root.

Before any shadow transaction or canary:

1. Construct one immutable `SemanticPathRegistration` object from the explicit launch arguments.
2. Validate that root, status, summary, manifest, and terminal-seal paths are all non-null, exact, confined, and mutually coherent.
3. Hash and commit that registration before watcher launch.
4. Pass the same object—not a reconstructed dictionary—to completion checker, supervisor, registry compatibility projection, watcher, and reducer.
5. Remove command-text inference from all correctness paths; retain it only in an isolated legacy migration tool that can never yield PASS.
6. Add a launch HOLD: `HOLD_EXPLICIT_SEMANTIC_PATH_REGISTRATION_MISSING_OR_DIVERGENT`.
7. Add a regression where command-derived paths point at harness status while explicit paths point at a sealed semantic HOLD; every component must report the semantic HOLD.

This bridge repair is required even if the new journal implementation is otherwise complete, because migration code must not recreate the old split authority at the boundary.

---

## 18. Test strategy

### 18.1 Unit tests

- canonical JSON vectors;
- event hash vectors;
- transition table;
- role/event authorization;
- event idempotence/conflict;
- path confinement and mode rules;
- process identity and PID reuse;
- reducer determinism;
- terminal precedence;
- manifest/seal verification;
- projection regeneration.

### 18.2 Journal durability fixtures

Run each failure point before and after every syscall boundary:

- append before write;
- partial line write;
- complete write before `fdatasync`;
- after `fdatasync` before ack;
- checkpoint temp write;
- checkpoint rename before parent `fsync`;
- segment creation;
- terminal decision before projection;
- manifest before seal;
- seal before `RUN_SEALED`.

Expected result is always one of:

- exact committed prefix recovered;
- idempotent event rediscovered;
- torn uncommitted tail quarantined;
- explicit integrity HOLD/FAIL.

Never silent data loss and never false PASS.

### 18.3 Concurrency tests

- 2, 5, 20 clients submitting concurrently;
- duplicate same event from concurrent clients;
- conflicting duplicate event IDs;
- second supervisor lock attempt;
- takeover after supervisor death;
- client from wrong UID/role/PID;
- child fork attempting inherited authority;
- concurrent projection readers during atomic replacement.

### 18.4 Filesystem adversarial tests

- pre-existing correct directory;
- missing directory;
- file where directory expected;
- directory where file expected;
- symlink at leaf and ancestor;
- hard link;
- wrong owner/mode;
- read-only filesystem;
- ENOSPC;
- inode replacement;
- root rename;
- segment size bound;
- oversized artifact/event/log;
- permission loss during run.

### 18.5 Lifecycle and observer tests

- child exits 0 immediately;
- child exits nonzero immediately;
- child hangs;
- child forks and parent exits;
- supervisor receives SIGTERM/SIGKILL;
- watcher exits before/after child start;
- stale heartbeat with live PID;
- PID missing with sealed HOLD/PASS;
- `RUNNING` projection manually left stale after semantic terminal;
- orphaned process after supervisor loss;
- cleanup warning with terminal result preserved.

### 18.6 Semantic tests

- PASS with all required facts;
- every required PASS predicate missing individually;
- PASS plus timeout;
- PASS plus unjournaled governing artifact;
- HOLD/FAIL/ABORT precedence;
- unknown critical schema/event;
- forged terminal artifact without journal event;
- modified governing artifact after journal binding;
- seal mismatch;
- notification failure after semantic PASS.

### 18.7 Privacy and no-effect tests

- canonical bounded privacy scan;
- fixture secret literals vs actual values classification;
- environment redaction;
- raw stdout/stderr caps and deletion policy;
- zero provider/model calls in all offline milestones;
- zero Gateway/config/runtime/cron/production mutation sentinels;
- no out-of-root writes except explicitly registered test temp roots.

---

## 19. Health gates

A milestone may close PASS only when all gates assigned to it pass. Gate failure yields HOLD; validators are never weakened to obtain PASS.

### HG-00 — Scope and authority freeze

**Checks**

- exact source paths and base hashes frozen;
- ownership table complete;
- no production/apply/provider authority present;
- mutation sentinels armed;
- expected artifacts listed.

**PASS artifact:** `HG-00-SCOPE-AUTHORITY.json`

### HG-01 — Contract and schema integrity

**Checks**

- schemas parse with duplicate-key rejection;
- canonicalization vectors stable across runs;
- event/state enums closed;
- unknown critical versions fail closed;
- contract seal binds all tools and policy.

**PASS threshold:** 100% required schema/vector tests.

### HG-02 — Single-writer and lease safety

**Checks**

- second supervisor cannot acquire lock;
- stale PID alone cannot authorize takeover;
- boot ID/start ticks prevent PID reuse;
- root/device/inode replacement detected;
- only supervisor appends journal.

**PASS threshold:** all adversarial lease cases pass, concurrency 20/20.

### HG-03 — Journal durability and recovery

**Checks**

- crash matrix around every commit boundary;
- torn tail recovery;
- checkpoint ahead/behind handling;
- idempotent retry after ack loss;
- emergency ENOSPC evidence;
- no false PASS under corruption.

**PASS threshold:** zero lost acknowledged events; zero false PASS; deterministic recovery in every fixture.

### HG-04 — Reducer determinism and terminal monotonicity

**Checks**

- repeated replay byte-identical;
- shuffled projection publication does not alter result;
- semantic terminal supersedes stale `RUNNING` automatically;
- terminal conflict fails closed;
- PASS predicates complete.

**PASS threshold:** byte-identical outputs for at least 100 replays per fixture corpus.

### HG-05 — Process ownership and cleanup

**Checks**

- PID/start-ticks/boot-ID/PGID/SID bound;
- fork/parent-exit cases classified;
- owned children signalled, reaped, and verified absent;
- unowned processes never killed;
- cleanup receipt journal-bound.

**PASS threshold:** all lifecycle fixtures; zero surviving owned children.

### HG-06 — Exact paths and filesystem safety

**Checks**

- no governing recursive scans;
- symlink/hardlink/wrong-type/wrong-mode cases fail closed;
- duplicate path ownership rejected before launch;
- exact artifact hashes and sizes bound;
- bounded files/bytes/time enforced.

**PASS threshold:** all path fixtures; no out-of-root writes.

### HG-07 — Independent observer and alert health

**Checks**

- watcher ready before child start;
- watcher verifies journal before PID state;
- sealed terminal detected with stale/dead process;
- system-event submission distinguished from owner delivery;
- notification timeout becomes `DELIVERY_UNKNOWN` without semantic rewrite.

**PASS threshold:** all terminal/liveness/notification matrix cases.

### HG-08 — Security and privacy

**Checks**

- UDS peer/role spoof attempts rejected;
- replay and epoch mismatch rejected;
- payload/artifact/log bounds enforced;
- canonical bounded privacy scanner PASS;
- no actual secret or private value findings;
- dependency/tool identity hashes match.

**PASS threshold:** zero blocking privacy/security findings.

### HG-09 — Offline end-to-end proof

**Checks**

- full PREP_ONLY transaction under durable supervisor;
- independent watcher active;
- synthetic PASS/HOLD/FAIL/ABORT corpus;
- restart/recovery and stale projection cases;
- manifest/seal/independent verification;
- zero external calls/effects.

**PASS threshold:** all cases correctly terminalised and sealed.

### HG-10 — Shadow compatibility

**Checks**

- new reducer observes current harness fixtures read-only;
- compatibility projections match expected user-visible classifications;
- disagreements are explained, never normalized away;
- existing authority remains unchanged.

**PASS threshold:** 100% explained classification, zero mutation.

### HG-11 — Governed canary readiness

**Checks**

- frozen package and independent verification;
- rollback/off-switch proven;
- restore point verified where applicable;
- independent completion check scheduled;
- owner authority exact and time-bounded;
- canary is no-op/read-only before any mutation canary.

**PASS threshold:** explicit owner authorization after all prior gates.

### HG-12 — Production promotion

**Checks**

- install/apply performed as a separate Critical Apply transaction;
- restart, if needed, is separate;
- provider smoke, if needed, is separate;
- post-promotion runtime consumption verified;
- rollback tested and retained;
- owner-visible closeout confirmed.

**PASS threshold:** production evidence complete; no implicit promotion.

---

## 20. Implementation milestones

Each milestone requires a **STARTED notice** stating scope, gates, expected closeout artifacts, independent alert wiring, and ETA. Each closes proactively with PASS/HOLD/FAIL/ABORT and a next-milestone proposal.

### M0 — Architecture freeze and source authority

**Goal:** convert this document into sealed implementation contracts.

**Work**

- freeze terminology, state planes, event taxonomy, ownership table, and PASS predicates;
- inventory current harness/reducer/checker interfaces;
- freeze exact base/source authority;
- freeze and test the mandatory explicit-semantic-path bridge repair;
- define JSON schemas and test vectors;
- produce threat model and migration map.

**Gates:** HG-00, design portion of HG-01, explicit semantic-path divergence launch-HOLD fixture.  
**Closeout artifacts:** architecture seal, source manifest, ownership manifest, schema set, threat model, gap matrix, bridge-repair contract.  
**No external calls/effects.**

### M1 — Journal core and lease

**Goal:** build local single-writer journal and recovery primitives.

**Work**

- `journal.py`, canonicalization, append/fsync, checkpoint cache;
- exclusive lock and supervisor epoch;
- recovery parser and torn-tail handling;
- idempotency index;
- emergency segment;
- unit, crash, and concurrency fixtures.

**Gates:** HG-01, HG-02, HG-03.  
**Closeout artifacts:** test report, crash matrix, concurrency report, package manifest, zero-effect receipt.

### M2 — Supervisor and event ingress

**Goal:** establish the detached durable process boundary.

**Work**

- supervisor bootstrap/recovery;
- UDS server and client library;
- peer credentials and role authorization;
- child spawn identity and process group ownership;
- watcher-before-child launch sequencing;
- bounded logs and liveness projection.

**Gates:** HG-02, HG-05, ingress portions of HG-08.  
**Closeout artifacts:** lifecycle matrix, peer-auth tests, lock/takeover receipts, cleanup receipts.

### M3 — Canonical reducer and sealing

**Goal:** make all state replay-derived and terminal monotonic.

**Work**

- transition reducer;
- PASS predicate modules;
- artifact verifier;
- orthogonal projections;
- manifest/seal protocol;
- compatibility projectors;
- stale `RUNNING` supersession regression.

**Gates:** HG-04, HG-06.  
**Closeout artifacts:** deterministic replay report, terminal matrix, projection regeneration proof, seal verification.

### M4 — Independent checker and notification plane

**Goal:** independently observe journal authority and owner-closeout health.

**Work**

- exact-path journal checker;
- lock/process/liveness reconciliation;
- terminal-first alarm logic;
- delivery receipt states;
- timeout and watcher-death fixtures;
- dry-run notification adapter only.

**Gates:** HG-07 and remaining HG-08.  
**Closeout artifacts:** checker manifest, alarm matrix, delivery-state report, privacy receipt.

### M5 — Offline integrated resilience proof

**Goal:** prove the full architecture under deterministic faults without production effects.

**Work**

- full synthetic transactions;
- kill/restart at commit boundaries;
- PID reuse/orphan/fork fixtures;
- ENOSPC/read-only/path replacement fixtures;
- PASS/HOLD/FAIL/ABORT and recovery flows;
- independent review of frozen bytes.

**Gates:** HG-09.  
**Closeout artifacts:** integrated evidence root, journal corpus, manifests/seals, independent verification, zero-call/effect ledger.

### M6 — Legacy shadow and migration tooling

**Goal:** compare against preserved historical/current harness fixtures.

**Work**

- read-only legacy importer;
- replay R17/R18 and prior stale-observer cases;
- generate compatibility projections;
- produce divergence ledger;
- prove no old evidence mutation.

**Gates:** HG-10.  
**Closeout artifacts:** compatibility matrix, divergence classifications, preserved-root sentinels.

### M7 — Read-only/no-op governed canary

**Goal:** exercise production-like process supervision with no target mutation and no provider call.

**Work**

- freeze canary package;
- independent verify;
- explicit owner approval;
- durable launch with independent watcher;
- no-op/read-only child;
- terminal seal and owner delivery proof;
- off-switch exercise.

**Gates:** HG-11.  
**Closeout artifacts:** authority receipt, canary journal/seal, watcher/alarm receipts, owner-delivery receipt, rollback proof.

### M8 — Promotion preparation

**Goal:** prepare—not automatically execute—the production Critical Apply transaction.

**Work**

- installation package and exact hashes;
- fresh restore point plan;
- install/apply authority proposal;
- separate restart proposal;
- separate provider smoke proposal;
- rollback and independent completion wiring.

**Gates:** readiness portion of HG-12.  
**Closeout artifact:** owner-ready production promotion package.

### M9 — Production install/apply transaction

**Requires separate explicit owner authorization.**

Install only. No automatic Gateway restart or provider smoke. Governed by the already-proven supervisor and its own restore point, observer, journal, recovery policy, and closeout.

### M10 — Separate runtime activation/restart transaction

**Requires separate explicit owner authorization.**

Verify active runtime consumption and health. No provider smoke unless separately authorized.

### M11 — Separate functional/provider smoke

**Requires separate explicit owner authorization.**

Bound exact calls, messages, recipients, retries, fallbacks, and cleanup. This milestone is not implied by install or restart success.

---

## 21. Rollout and rollback

### Rollout phases

1. **Library only:** no launcher integration.
2. **Offline fixtures:** temporary roots only.
3. **Read-only legacy replay:** preserved evidence remains immutable.
4. **Shadow projections:** new outputs not consumed by current harness.
5. **No-op canary:** new supervisor authoritative only for a nonmutating transaction.
6. **Low-risk governed apply:** only after explicit approval and all gates.
7. **General Critical Apply adoption.**

### Off-switch

- Do not launch new transactions with the new supervisor.
- Existing transactions continue to terminal or are recovered under their frozen version.
- Never switch an in-flight transaction to a different supervisor/reducer version unless a specific migration event and independent verification authorize it.
- Preserve old harness for rollback during canary period, but never run both as canonical writers for one transaction.

### Rollback trigger examples

- acknowledged event missing after recovery;
- false terminal classification;
- reducer nondeterminism;
- lock bypass;
- unowned process termination;
- journal corruption under normal operation;
- privacy leak;
- owner notification misrepresented as delivered;
- projection consumed as authority by a production path.

Any trigger stops promotion and returns to the last proven harness version for new transactions.

---

## 22. Operational runbook

### Normal status check

1. Verify exact transaction root and contract hash.
2. Verify journal chain through latest sequence.
3. Verify seal first; if valid, report semantic terminal.
4. If unsealed, verify lock holder identity and liveness deadline.
5. Verify child identities and mutation-started flag.
6. Report semantic, process, recovery, and notification planes separately.
7. Never report `RUNNING` solely from a projection.

### Recovery status check

1. Do not start a second supervisor until lock acquisition proves exclusivity.
2. Preserve journal and projections before repair.
3. Rebuild checkpoint/projections from journal.
4. Identify whether mutation started.
5. Reconcile owned processes using full identity.
6. Commit recovery epoch and classification.
7. Resume only if frozen policy explicitly permits; otherwise terminal HOLD/FAIL and request owner decision.

### Terminal closeout

Report:

- semantic result;
- last committed sequence/hash;
- manifest/seal hashes;
- process cleanup;
- recovery state;
- notification delivery state;
- external/provider/production effects;
- exact next authority boundary.

---

## 23. Acceptance criteria for production readiness

The architecture is production-ready only when all are true:

- every health gate HG-00 through HG-11 passes;
- independent review verifies frozen implementation bytes;
- no test found a false PASS;
- no acknowledged event is lost across crash recovery;
- 20-client concurrency is deterministic;
- stale `RUNNING` is automatically superseded by terminal journal authority;
- PID reuse, fork escape, wrong UID, wrong role, replay, and competing supervisor tests fail closed;
- exact-path, symlink, hardlink, wrong-type, wrong-mode, and ENOSPC fixtures pass;
- privacy scan has zero blocking findings;
- no-op canary proves independent alert and owner-visible closeout;
- rollback/off-switch is tested;
- an owner-ready production install proposal exists;
- Stick separately authorizes production promotion.

---

## 24. Immediate next action

Recommended next milestone:

`CAH-J1-M0_ARCHITECTURE_FREEZE_AND_EVENT_CONTRACTS`

It should remain **PREP_ONLY and zero-call**. It will freeze schemas, state transitions, exact source authority, ownership, threat model, and test vectors. It must not modify the current production harness, Gateway, configuration, routes, providers, runtime package, or any consumed R18 one-call authority.

Expected closeout:

- `PASS_CAH_J1_M0_ARCHITECTURE_AND_EVENT_CONTRACTS_FROZEN_NO_PRODUCTION_EFFECT`, or
- an explicit HOLD naming the unresolved invariant.

---

## Appendix A — Minimum event transition constraints

| Current execution state | Event | Next state | Invalid when |
|---|---|---|---|
| CREATED | TRANSACTION_PREPARED | PREPARED | contract missing/unsealed |
| PREPARED | SUPERVISOR_STARTED | ARMED_PENDING_WATCHER | lock/recovery invalid |
| ARMED_PENDING_WATCHER | WATCHER_ARMED | ARMED | watcher identity/readback invalid |
| ARMED | AUTHORITY_BOUND | AUTHORITY_BOUND | authority absent/expired/mismatched |
| AUTHORITY_BOUND | CHILD_SPAWN_INTENT | STARTING | watcher not armed |
| STARTING | CHILD_STARTED | RUNNING | process identity invalid |
| RUNNING | CHILD_EXITED | POSTCHECK | exit identity mismatch |
| POSTCHECK | RECOVERY_DECISION | RECOVERY or TERMINAL_PENDING | evidence incomplete |
| any preterminal | TERMINAL_DECISION | TERMINAL_DECIDED | conflicting prior terminal |
| TERMINAL_DECIDED | RUN_SEALED | SEALED | reducer/manifest/seal invalid |
| SEALED | SUPERVISOR_CLOSED | CLOSED | owned-process cleanup unresolved without explicit terminal finding |

## Appendix B — Required invariants suitable for property tests

1. Sequence strictly increments by one.
2. Every event hash verifies.
3. Every predecessor hash equals prior event hash.
4. Every event binds the same transaction and contract.
5. Epoch changes only through valid recovery transition.
6. Only supervisor actor emits supervisor-only event types.
7. Every artifact ref is registered, confined, and hash-valid.
8. A committed terminal cannot transition to nonterminal.
9. PASS implies all PASS predicates.
10. Notification state cannot change semantic result.
11. Projection deletion and replay preserve terminal bytes.
12. Concurrent client ordering may differ, but each committed total order reduces deterministically.
13. Duplicate idempotent proposal does not create a second semantic event.
14. Conflicting duplicate never passes.
15. No critical side effect starts before its prerequisite commit acknowledgement.
16. No second supervisor writes while the lease is held.
17. Process identity mismatch never grants cleanup/kill authority.
18. A sealed terminal outranks dead PID and stale projection.
19. Unknown critical schema/event cannot produce PASS.
20. Every terminal closeout explicitly reports provider/model calls and production effects.

## Appendix C — Source lessons incorporated

- Critical mutations must not be governed by foreground chat processes.
- Independent watcher registration precedes child launch.
- Semantic root and verified terminal seal outrank harness lifecycle status.
- `RUNNING + pid_missing` must reconcile, never persist as primary truth.
- Wake submission is not owner-visible delivery proof.
- Governing scans are exact-path and bounded; no unbounded `rglob`.
- Every long observer exposes phase, progress, heartbeat, timeout budget, and terminal closeout.
- Directory/file creation has one owner.
- Failed local execution consumes no implicit retry authority.
- Exact model/provider identity and one-call constraints remain separately enforced where applicable.

---

**End of design.**
