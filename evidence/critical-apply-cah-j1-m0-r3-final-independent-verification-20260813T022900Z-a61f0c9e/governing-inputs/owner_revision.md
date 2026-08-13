# Critical Apply Supervisor-Owned Event Journal

**Low-Level Design, Security Model, Health Gates, Implementation Plan, and Production Rollout**

**Version:** 1.0  
**Date:** 2026-08-13  
**Status:** DESIGN — no production mutation authorized  
**Owner:** Stick

---

# 0. Executive decision

Critical Apply will move from a multi-writer collection of lifecycle files, status projections, registry rows, watchers, alarms, and terminal artifacts to a **supervisor-owned transaction architecture built around one append-only canonical event journal**.

The governing rule is:

> A Critical Apply fact becomes authoritative only when the transaction supervisor durably commits it to the canonical journal.

Everything else is either:

- immutable evidence referenced by the journal;
- a deterministic projection derived from the journal;
- an independent witness to the journal;
- or authority for a different concern such as cross-transaction locking.

A PID, heartbeat, registry row, status file, alarm state, or notification receipt can never override a valid sealed semantic terminal.

The canonical authority order is:

```text
Canonical journal prefix
    ↓
Deterministic reducer result
    ↓
Terminal manifest + seal
    ↓
Independent witness/checker
    ↓
Rebuildable projections / ProgressDB
    ↓
Process-lifecycle observations
    ↓
Notification / owner-delivery receipts
```

A stale `RUNNING` projection is therefore not a conflicting state. It is simply a stale projection that must be rebuilt.

---

# 1. Architecture objectives

The new design must eliminate the recurring class of Critical Apply defects where independently maintained representations disagree about one transaction.

It must guarantee:

1. **One canonical writer.**
   Only the supervisor may commit canonical events.

2. **One canonical semantic history.**
   The journal is the sole source of operational truth.

3. **Terminal monotonicity.**
   Once a terminal decision has been deterministically committed, the transaction can never return to `RUNNING`.

4. **Lifecycle and semantics remain separate.**
   Process death does not itself imply PASS, HOLD, FAIL, or ABORT.

5. **Notification remains separate.**
   Owner-delivery failure cannot rewrite a semantic PASS/HOLD/FAIL.

6. **Critical actions require durable authorization state first.**
   No protected side effect starts before the corresponding journal event is committed and acknowledged.

7. **Every mutable path has one owner.**

8. **Governing artifacts become immutable after acceptance.**

9. **Every transaction can be reconstructed without trusting projections.**

10. **Cross-transaction mutation authority is explicit.**

11. **Crash recovery produces deterministic classification, never guessed success.**

12. **No unbounded filesystem discovery is needed for correctness.**

---

# 2. Non-goals

Version 1 deliberately does not attempt:

- distributed multi-host consensus;
- automatic production authorization;
- replacing owner approvals;
- automatically retrying consumed external authority;
- combining install, restart, provider smoke, or deployment into one transaction;
- changing OpenClaw business policy;
- depending on Gateway availability for Critical Apply authority;
- using SQLite as the canonical event store;
- making notification delivery part of semantic authority;
- recovering an arbitrary partially completed mutation without an explicit recovery policy.

The first production version is:

```text
single host
single transaction root
single supervisor writer
single canonical journal
```

---

# 3. Core storage architecture

Critical Apply uses five distinct storage responsibilities.

They must not be conflated.

## 3.1 Canonical journal

```text
journal/events-000001.jsonl
```

Purpose:

> What happened?

Properties:

- sole canonical event history;
- append-only;
- one supervisor writer;
- hash chained;
- sequence ordered;
- commit-before-ack for critical events;
- crash recoverable;
- human inspectable;
- independently replayable.

SQLite is **not** canonical authority in version 1.

---

## 3.2 Content-addressed artifact store

```text
objects/sha256/<prefix>/<sha256>
```

Purpose:

> What exact bytes did the transaction rely on?

Properties:

- supervisor-owned;
- immutable after creation;
- content-addressed;
- governing child-produced artifacts copied here before event acknowledgement;
- reducer reads governing evidence from CAS rather than mutable child paths.

---

## 3.3 ProgressDB

```text
index/progress.db
```

Purpose:

> What is the current derived state and how can it be queried efficiently?

Properties:

- SQLite;
- rebuildable;
- non-authoritative;
- indexed by transaction/event/artifact;
- used for fast status, dedup lookup, progress views, administrative search;
- safe to delete and rebuild entirely from journal + CAS.

A ProgressDB mismatch never overrides the journal.

---

## 3.4 WitnessDB

Maintained by the independent checker, not the supervisor.

Example location:

```text
~/.openclaw/critical-apply-witness/witness.db
```

Purpose:

> Can an independent component prove that an earlier journal head or terminal existed?

Properties:

- append-only logical model;
- stores observed journal head hashes;
- stores terminal/seal witnesses;
- independent of transaction root;
- detects later truncation/replacement;
- never rewrites semantic outcome.

---

## 3.5 AuthorityDB

Example:

```text
~/.openclaw/critical-apply-authority/authority.db
```

Purpose:

> Who currently owns a shared mutation scope or consumed nonce?

This database governs **cross-transaction authority**, not transaction semantics.

Examples:

- OpenClaw package mutation lease;
- Gateway restart lease;
- production configuration lease;
- one-call authority nonce;
- approval nonce consumption;
- maintenance scope exclusion.

---

# 4. Authority model

Different stores govern different facts.

| Question | Authority |
|---|---|
| What happened in this transaction? | Canonical journal |
| What evidence bytes governed it? | Journal-bound CAS |
| What semantic result follows? | Canonical reducer |
| Has that historical journal head been independently witnessed? | WitnessDB |
| What is the fast current status? | ProgressDB projection |
| Who owns a shared production mutation scope? | AuthorityDB |
| Is the supervisor alive now? | Process identity + lease |
| Was the owner notified? | Notification plane |

No two components own the same fact.

---

# 5. Transaction directory

```text
<transaction-root>/
  contract/
    TRANSACTION.json
    AUTHORITY.json
    COMMAND.json
    TIMEOUT-BUDGET.json
    OWNERSHIP.json
    SEMANTIC-PATHS.json
    CONTRACT-SEAL.json

  registration/
    ROLES.json
    EXACT-PATHS.json
    TOOL-IDENTITIES.json

  journal/
    LOCK
    events-000001.jsonl
    CHECKPOINT.json
    RECOVERY-<epoch>.json
    emergency.bin

  objects/
    sha256/
      ab/
        abcdef...

  index/
    progress.db

  control/
    supervisor.json
    children.json

  artifacts/
    worker/
    checker/
    recovery/
    notification/

  logs/
    supervisor.log
    child.stdout.log
    child.stderr.log

  projections/
    status.json
    summary.json
    health.json
    process-lifecycle.json
    notification.json
    compatibility-harness-status.json
    compatibility-registry-row.json

  seal/
    REDUCTION.json
    MANIFEST.json
    TERMINAL-SEAL.json

  closeout/
    TERMINAL.txt
    FINAL-REPORT.json
    ZERO-EFFECTS.json
    COMPLETION-RECEIPT.json
```

The event socket should **not** live under a potentially very long transaction path.

Recommended Linux runtime path:

```text
/run/user/<uid>/critical-apply/<short-transaction-id>/events.sock
```

The transaction contract binds that socket identity back to the evidence root.

---

# 6. Filesystem requirements

Canonical Critical Apply state must live on a Linux filesystem whose semantics have passed the filesystem capability fixture.

For WSL deployments, governing transaction state should normally reside on the WSL Linux filesystem rather than `/mnt/c`.

Required semantics include:

- advisory `flock`;
- stable device/inode behavior;
- Unix ownership and modes;
- atomic rename;
- `fsync`/`fdatasync`;
- Unix-domain sockets;
- symlink inspection;
- hard-link detection.

Required root properties:

```text
owner = expected Critical Apply user
directory mode = 0700
canonical file mode = 0600
```

Before launch:

- `lstat()` every registered ancestor;
- reject symlink traversal;
- reject unexpected hard links;
- bind root device/inode;
- bind boot ID;
- verify free-space threshold.

---

# 7. Ownership model

Every mutable path has exactly one creator/writer.

Example:

| Object | Owner |
|---|---|
| Canonical journal | Supervisor |
| Journal lock | Supervisor |
| ProgressDB | Supervisor/indexer |
| CAS objects | Supervisor |
| Supervisor runtime projection | Supervisor |
| Worker artifacts | Worker |
| Canonical projections | Reducer publication path controlled by supervisor |
| WitnessDB | Independent checker |
| AuthorityDB lease rows | Authority service/library |
| Notification receipts | Notification adapter |
| Terminal manifest/seal | Supervisor |
| Final completion receipt | Completion checker |

Duplicate ownership is a launch-time error.

Example:

```text
HOLD_DUPLICATE_MUTABLE_PATH_OWNERSHIP
```

---

# 8. Semantic path registration

Critical Apply must use one immutable semantic-path registration object.

Example:

```json
{
  "schema": "critical_apply.semantic_paths.v1",
  "transaction_id": "...",
  "root": "...",
  "journal": "...",
  "terminal_seal": "...",
  "manifest": "...",
  "status_projection": "...",
  "summary_projection": "...",
  "completion_receipt": "..."
}
```

This exact object is passed to:

- supervisor;
- reducer;
- checker;
- watcher;
- compatibility projector;
- completion checker.

Correctness paths must never reconstruct semantic paths from command text.

Legacy command-based inference may exist only in migration tooling and can never produce PASS.

---

# 9. Supervisor identity and lease

Supervisor identity consists of:

```text
transaction_id
supervisor_epoch
PID
/proc start_ticks
boot_id
executable realpath
executable SHA256
UID
GID
PGID
SID
contract SHA256
```

The supervisor acquires:

```text
flock(LOCK_EX | LOCK_NB)
```

on `journal/LOCK`.

The descriptor remains open until supervisor closeout.

A PID alone never establishes ownership.

---

# 10. Monotonic lease semantics

Heartbeat/lease logic uses monotonic time only inside one boot generation.

Required invariant:

> A monotonic deadline is comparable only while `boot_id` is unchanged.

After reboot:

- previous monotonic timestamps are not evaluated for elapsed time;
- old process identity is classified as prior-generation;
- recovery requires lock acquisition;
- journal recovery;
- new supervisor epoch.

Wall-clock timestamps remain useful for operator reporting but not primary lease authority.

---

# 11. Cross-transaction authority

Per-transaction `flock` prevents competing writers to one transaction.

It does not prevent:

```text
transaction A → mutate OpenClaw installation
transaction B → mutate OpenClaw installation
```

Therefore Critical Apply uses a separate scope authority mechanism.

Example AuthorityDB schema:

```sql
CREATE TABLE scope_leases (
    scope_hash TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL,
    supervisor_epoch TEXT NOT NULL,
    boot_id TEXT NOT NULL,
    pid INTEGER NOT NULL,
    start_ticks TEXT NOT NULL,
    lease_nonce TEXT NOT NULL,
    state TEXT NOT NULL,
    acquired_at_utc TEXT NOT NULL
);

CREATE TABLE consumed_authorities (
    nonce_sha256 TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL,
    authority_id TEXT NOT NULL,
    consumed_sequence INTEGER NOT NULL,
    consumed_event_sha256 TEXT NOT NULL
);
```

Examples of scope:

```text
openclaw:npm-package
openclaw:gateway-restart
openclaw:production-config
openclaw:cron
openclaw:model-route
```

The journal records the hash of the AuthorityDB lease/nonce receipt.

The AuthorityDB does not record semantic PASS/HOLD.

---

# 12. Event ingress

Workers do not write the canonical journal.

They submit proposals over an owner-only UDS.

Preferred Linux transport:

```text
AF_UNIX + SOCK_SEQPACKET
```

Fallback:

```text
SOCK_STREAM + 32-bit length prefix
```

Required controls:

- `SO_PEERCRED`;
- expected UID;
- expected registered PID;
- start-ticks verification;
- process role verification;
- current supervisor epoch;
- current transaction ID;
- event-size bounds;
- duplicate-key rejection;
- closed schema for critical event types.

---

# 13. Proposal versus commit identity

Every canonical event distinguishes:

### Proposer

The component asserting a fact.

Example:

```text
worker
checker
watcher
recovery plugin
notification adapter
```

### Committer

Always the supervisor for canonical journal events.

Canonical event therefore contains both.

Example:

```json
{
  "proposer": {
    "role": "worker",
    "pid": 12345,
    "start_ticks": "...",
    "boot_id": "...",
    "process_identity_sha256": "..."
  },
  "committer": {
    "role": "supervisor",
    "pid": 12300,
    "start_ticks": "...",
    "supervisor_epoch": "..."
  }
}
```

This prevents later ambiguity over who asserted versus who authenticated/committed the fact.

---

# 14. Event proposal

Example:

```json
{
  "schema": "critical_apply.event_proposal.v1",
  "transaction_id": "...",
  "supervisor_epoch": "...",
  "event_id": "...",
  "client_sequence": 12,
  "role": "worker",
  "event_type": "ARTIFACT_READY",
  "payload": {},
  "artifact_refs": []
}
```

The proposal receives its own canonical SHA256.

That hash is included in the canonical event.

---

# 15. Commit-before-ack

For a critical event:

```text
receive proposal
→ authenticate proposer
→ validate schema
→ validate role/event permission
→ verify artifact references
→ capture governing artifact into CAS
→ construct canonical event
→ append journal bytes
→ fdatasync journal
→ update in-memory canonical head
→ ACK client
→ update ProgressDB/checkpoint asynchronously
```

The journal commit, not `CHECKPOINT.json`, defines durability.

If checkpoint/index publication later fails, the event remains committed.

---

# 16. Critical action barrier

A protected side effect cannot begin before its prerequisite journal acknowledgement.

Examples:

```text
APPLY_START_AUTHORIZED
    must be committed before apply process spawn

GATEWAY_RESTART_AUTHORIZED
    must be committed before restart

PROVIDER_CALL_RESERVED
    must be committed before provider invocation

RECOVERY_ACTION_AUTHORIZED
    must be committed before rollback/restore

AUTHORITY_NONCE_CONSUMED
    must be committed before protected use
```

This turns journal commit into an execution barrier.

---

# 17. Event idempotence

`event_id` is unique within a transaction.

If the same ID is retried:

### Same proposal hash

Return the original committed ACK.

No second event is appended.

### Different proposal hash

Commit or emergency-record:

```text
INTEGRITY_CONFLICT_DETECTED
```

and fail closed.

---

# 18. Canonical event schema

Example:

```json
{
  "schema": "critical_apply.journal_event.v1",
  "transaction_id": "...",
  "run_id": "...",
  "supervisor_epoch": "...",
  "sequence": 42,
  "event_id": "...",
  "event_type": "CHILD_EXITED",
  "phase": "EXECUTION",

  "proposer": {
    "role": "worker",
    "process_identity_sha256": "..."
  },

  "committer": {
    "role": "supervisor",
    "process_identity_sha256": "..."
  },

  "wall_time_utc": "...",
  "monotonic_ns": 123456789,

  "previous_event_sha256": "...",
  "contract_sha256": "...",
  "proposal_sha256": "...",
  "payload_sha256": "...",

  "payload": {},

  "artifact_refs": [],

  "event_sha256": "..."
}
```

---

# 19. Canonicalization

Use a frozen deterministic JSON canonicalization specification.

Preferred:

```text
RFC 8785 / JCS-compatible
```

Requirements:

- UTF-8;
- sorted object keys;
- duplicate keys rejected during parse;
- no NaN/Infinity;
- defined signed integer bounds;
- no locale-sensitive encoding;
- no whitespace significance;
- test vectors published and frozen.

`event_sha256` hashes all canonical event fields except itself.

---

# 20. Journal durability

Journal file:

```text
journal/events-000001.jsonl
```

Open with appropriate flags such as:

```text
O_APPEND
O_WRONLY
O_CLOEXEC
O_NOFOLLOW
```

where supported.

Each critical committed event requires:

```text
write complete line
fdatasync journal
ACK
```

Telemetry does not require an fsync every few seconds.

---

# 21. Checkpoint semantics

`journal/CHECKPOINT.json` is only a cache.

It may contain:

```text
last sequence
last event hash
journal byte offset
current segment
```

It is not required in the event ACK critical path.

Recovery rules:

### Checkpoint behind journal

Replay journal and rebuild.

### Checkpoint ahead of journal

Discard checkpoint and classify a health anomaly.

### Checkpoint corrupt

Delete/rebuild under recovery authority.

No checkpoint condition can override valid journal bytes.

---

# 22. ProgressDB design

ProgressDB is an efficient materialized index.

Suggested tables:

```sql
CREATE TABLE events (
    transaction_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    event_id TEXT NOT NULL,
    event_sha256 TEXT NOT NULL,
    previous_event_sha256 TEXT NOT NULL,
    proposal_sha256 TEXT NOT NULL,
    event_type TEXT NOT NULL,
    phase TEXT,
    supervisor_epoch TEXT NOT NULL,
    proposer_identity_sha256 TEXT,
    monotonic_ns INTEGER,
    PRIMARY KEY (transaction_id, sequence),
    UNIQUE (transaction_id, event_id)
);

CREATE TABLE transaction_heads (
    transaction_id TEXT PRIMARY KEY,
    head_sequence INTEGER NOT NULL,
    head_sha256 TEXT NOT NULL,
    execution_state TEXT,
    semantic_result TEXT,
    process_health TEXT,
    recovery_state TEXT,
    notification_state TEXT,
    terminal_sequence INTEGER,
    terminal_sha256 TEXT,
    reducer_sha256 TEXT
);

CREATE TABLE artifacts (
    transaction_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    path_id TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    bytes INTEGER NOT NULL,
    mode TEXT NOT NULL,
    schema TEXT,
    PRIMARY KEY (transaction_id, sequence, path_id)
);
```

Recommended SQLite mode:

```text
WAL
```

because the DB is rebuildable and read-heavy.

---

# 23. ProgressDB invariants

ProgressDB must never become semantic authority.

Required property test:

```text
delete progress.db
delete all projections
delete CHECKPOINT.json
replay journal + CAS
→ identical canonical reducer output
→ reconstructed ProgressDB
```

If this does not work, the design has accidentally created a second authority.

---

# 24. Content-addressed artifact capture

A worker may create evidence in its registered output path.

But governing evidence should not remain dependent on mutable worker-owned bytes.

Acceptance sequence:

```text
worker finishes artifact atomically
↓
worker proposes ARTIFACT_READY
↓
supervisor validates:
  exact registered path
  lstat confinement
  owner
  mode
  bytes
  schema
  SHA256
↓
supervisor copies/streams artifact into CAS
↓
CAS file fsync
↓
CAS hash independently rechecked
↓
journal event references CAS object
↓
fdatasync journal
↓
ACK
```

The original path remains provenance.

The CAS object becomes canonical reducer input.

---

# 25. CAS filesystem format

Example:

```text
objects/
  sha256/
    8f/
      8f0d0be3...
```

CAS object requirements:

- create with `O_EXCL`;
- no symlink following;
- immutable application convention;
- mode `0600`;
- hash verified before and after publication;
- collisions require identical bytes;
- no overwrite.

---

# 26. Independent WitnessDB

The checker independently witnesses significant journal heads.

Suggested schema:

```sql
CREATE TABLE journal_witnesses (
    transaction_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    event_sha256 TEXT NOT NULL,
    contract_sha256 TEXT NOT NULL,
    supervisor_epoch TEXT NOT NULL,
    checker_identity_sha256 TEXT NOT NULL,
    boot_id TEXT NOT NULL,
    observed_monotonic_ns INTEGER NOT NULL,
    observed_utc TEXT NOT NULL,
    PRIMARY KEY (transaction_id, sequence, checker_identity_sha256)
);

CREATE TABLE terminal_witnesses (
    transaction_id TEXT NOT NULL,
    terminal_sequence INTEGER NOT NULL,
    terminal_event_sha256 TEXT NOT NULL,
    reduction_sha256 TEXT NOT NULL,
    manifest_sha256 TEXT NOT NULL,
    terminal_seal_sha256 TEXT NOT NULL,
    checker_identity_sha256 TEXT NOT NULL,
    observed_utc TEXT NOT NULL
);
```

The witness database should not normally duplicate every heartbeat.

Recommended witness boundaries:

- `WATCHER_ARMED`;
- `AUTHORITY_BOUND`;
- first mutation authorization;
- mutation start;
- recovery start;
- terminal candidate;
- terminal decision;
- terminal seal.

---

# 27. Witness disagreement semantics

Example:

Journal currently reports:

```text
head = sequence 80 / hash H80
```

WitnessDB proves:

```text
previously observed sequence 90 / hash H90
```

This indicates journal truncation/replacement.

Classification:

```text
INTEGRITY_HOLD_JOURNAL_HISTORY_DIVERGED_FROM_INDEPENDENT_WITNESS
```

WitnessDB does not “replace” journal semantic outcome.

It produces an integrity finding which prevents trustworthy promotion/closeout.

---

# 28. Process model

Supervisor spawns children in controlled process sessions/groups.

For every child record:

```text
PID
start ticks
boot ID
executable realpath
executable SHA256
argv digest
PGID
SID
role
spawn event sequence
```

Cleanup authority requires full identity match.

Never kill a process based only on:

- PID;
- name;
- grep output;
- stale registry row.

---

# 29. Same-UID threat model

Unix mode bits do not prevent another process running as the same UID from modifying supervisor-owned files.

Version 1 must explicitly freeze one of two threat models.

## Model A — detect, not fully prevent

Workers are trusted not to intentionally tamper with supervisor canonical files.

The architecture detects unexpected modification using:

- inode binding;
- hashes;
- journal chain;
- WitnessDB;
- CAS;
- independent checker.

This protects strongly against accidental and out-of-contract writes.

## Model B — hostile child in scope

If workers are considered potentially malicious, enforce OS isolation such as:

- dedicated worker UID;
- mount namespace;
- read-only transaction control/journal mount;
- writable registered artifact directory only;
- Landlock or equivalent Linux restriction.

The implementation must not claim filesystem permission isolation against same-UID children unless it actually provides it.

---

# 30. Supervisor lifecycle

Recommended lifecycle:

```text
PREPARE
  ↓
VERIFY CONTRACT
  ↓
ACQUIRE TRANSACTION LOCK
  ↓
ACQUIRE CROSS-TRANSACTION SCOPE LEASE
  ↓
RECOVER JOURNAL
  ↓
CREATE SUPERVISOR EPOCH
  ↓
OPEN EVENT SOCKET
  ↓
SUPERVISOR_STARTED
  ↓
ARM INDEPENDENT CHECKER/WATCHER
  ↓
WATCHER_ARMED
  ↓
AUTHORITY_BOUND
  ↓
SPAWN CHILD
  ↓
CHILD_STARTED
  ↓
EXECUTION
  ↓
POSTCHECK
  ↓
OPTIONAL RECOVERY
  ↓
OWNED CHILD CLEANUP
  ↓
FREEZE TERMINAL JOURNAL HEAD
  ↓
DETERMINISTIC TERMINAL REDUCTION
  ↓
TERMINAL_DECISION
  ↓
VERIFY TERMINAL REPLAY
  ↓
MANIFEST
  ↓
TERMINAL SEAL
  ↓
RUN_SEALED
  ↓
NOTIFICATION
  ↓
INDEPENDENT TERMINAL WITNESS
  ↓
SUPERVISOR_CLOSED
  ↓
RELEASE LEASES/LOCK
```

---

# 31. Terminal reduction protocol

The supervisor must not guess the semantic result and then ask the reducer to justify it.

Instead:

## Step 1 — freeze preterminal head

Suppose current committed head is:

```text
sequence H
hash HH
```

No more worker semantic evidence is accepted after terminal reduction begins except specifically permitted closeout events.

---

## Step 2 — reducer computes terminal candidate

Reducer reads journal through `H`.

It produces:

```text
REDUCTION.json
```

binding:

```text
through_sequence
through_event_sha256
contract_sha256
reducer_sha256
semantic_result
health_findings
PASS predicate results
reduction_sha256
```

---

## Step 3 — supervisor verifies reduction

Supervisor verifies reducer identity and reduction inputs.

---

## Step 4 — commit terminal decision

Canonical event:

```text
TERMINAL_DECISION
```

contains:

```text
reduced_through_sequence
reduced_head_sha256
reducer_sha256
reduction_sha256
semantic_result
```

---

## Step 5 — verification replay

Reducer replays through the new terminal event and verifies that:

```text
committed decision ==
deterministically derived terminal candidate
```

Mismatch is integrity failure.

---

# 32. No generic terminal precedence

There is exactly one canonical terminal decision.

Possible semantic results:

```text
PASS
HOLD
FAIL
ABORT
```

They are classifications, not a conflict-resolution ordering.

Two different canonical terminal decisions are not reconciled by choosing the “more severe” result.

They indicate:

```text
INTEGRITY_CONFLICT
```

Severity ordering may still be used for noncanonical operator findings.

---

# 33. Execution state plane

```text
CREATED
PREPARED
ARMED_PENDING_WATCHER
ARMED
AUTHORITY_BOUND
STARTING
RUNNING
POSTCHECK
RECOVERY
CLEANUP
TERMINAL_REDUCING
TERMINAL_DECIDED
SEALED
CLOSED
```

---

# 34. Semantic result plane

```text
UNDECIDED
PASS
HOLD
FAIL
ABORT
```

---

# 35. Process-health plane

```text
NOT_STARTED
ALIVE_VERIFIED
EXITED_REAPED
ORPHANED_OWNED_PROCESS
MISSING_IDENTITY_UNRESOLVED
CLEAN
```

---

# 36. Recovery plane

```text
NOT_REQUIRED
DECISION_REQUIRED
AUTHORIZED
RUNNING
PASS
FAIL_OPERATOR_REQUIRED
```

---

# 37. Notification plane

```text
NOT_REQUESTED
REQUESTED
SUBMITTED
DELIVERED_CONFIRMED
DELIVERY_UNKNOWN
DELIVERY_FAILED
```

Notification state cannot alter semantic result.

Example:

```text
semantic_result = PASS
notification = DELIVERY_UNKNOWN
owner_closeout = HOLD
```

The PASS fact remains historical truth.

---

# 38. Process cleanup before seal

Owned child cleanup participates in semantic readiness.

Before terminal reduction:

1. expected child exits identified;
2. owned process group reconciled;
3. remaining owned descendants terminated only if policy authorizes;
4. all owned processes reaped/verified absent;
5. unowned processes never killed;
6. cleanup receipt committed.

Only then may a clean PASS terminal be derived.

The supervisor itself remains alive through sealing and notification.

---

# 39. Canonical reducer

The reducer is pure.

Suggested interface:

```bash
critical_apply_reducer.py \
  --contract contract/TRANSACTION.json \
  --journal journal/events-000001.jsonl \
  --objects objects/sha256 \
  --through-sequence N \
  --output-dir reducer-output/
```

Inputs are immutable/read-only.

---

# 40. Reducer responsibilities

The reducer validates:

- contract;
- journal schema;
- sequence;
- hash chain;
- supervisor epochs;
- proposer roles;
- event transitions;
- event-type permissions;
- exact artifact registrations;
- CAS hashes;
- process lifecycle evidence;
- authority receipts;
- recovery evidence;
- cleanup;
- required PASS predicates.

Outputs:

```text
semantic result
execution plane
process plane
recovery plane
notification plane
health findings
projection bytes
manifest input
```

---

# 41. Reducer forbidden actions

Reducer must not:

- inspect arbitrary live PIDs;
- spawn/kill processes;
- perform filesystem discovery;
- call providers;
- send notifications;
- mutate journal;
- alter artifacts;
- modify ProgressDB;
- infer semantic paths from argv;
- use current wall clock as sole evidence;
- trust worker assertions without supervisor-authenticated events.

---

# 42. PASS predicate

A transaction may derive PASS only if all required predicates for that transaction class are satisfied.

Generic baseline:

- contract valid;
- canonical journal valid;
- transaction lease history valid;
- cross-transaction lease valid where required;
- watcher armed before protected child;
- authority correctly bound;
- no unacknowledged protected action;
- process identities valid;
- postchecks pass;
- cleanup complete;
- no integrity conflict;
- no unresolved orphan;
- governing artifacts CAS-bound;
- required recovery successful or not required;
- required privacy/no-effect checks pass;
- required one-call/nonce receipts valid;
- terminal reduction deterministic.

Notification delivery is normally not part of semantic PASS unless the transaction contract explicitly makes delivery the operation itself.

---

# 43. Manifest

After terminal decision verification, supervisor creates:

```text
seal/MANIFEST.json
```

binding:

- transaction ID;
- contract SHA;
- original base/source identities;
- canonical journal head;
- terminal event;
- reducer identity;
- reduction hash;
- every governing CAS object;
- ownership receipts;
- process cleanup;
- scope authority receipt;
- terminal projections.

Create atomically with `O_EXCL`.

---

# 44. Terminal seal

`seal/TERMINAL-SEAL.json` binds:

```text
transaction_id
semantic_result
terminal_sequence
terminal_event_sha256
reduction_sha256
manifest_sha256
contract_sha256
reducer_sha256
created_at
```

Create once.

Never replace.

After seal creation:

```text
RUN_SEALED
```

is committed referencing manifest and seal hashes.

---

# 45. Independent checker

The checker is not a canonical writer.

It independently verifies:

1. exact transaction root;
2. contract;
3. journal prefix;
4. journal head;
5. reducer identity;
6. reduction;
7. manifest;
8. terminal seal;
9. supervisor/process identity if unsealed;
10. cross-transaction authority;
11. optional WitnessDB consistency.

It writes only checker-owned receipts and WitnessDB records.

---

# 46. Terminal-first checker algorithm

Status resolution order:

```text
1. verify terminal seal
2. verify journal/reduction binding
3. if valid terminal:
       report terminal
       ignore stale RUNNING projection
4. otherwise inspect current supervisor lease
5. inspect process identity
6. inspect heartbeat/checkpoint
7. classify recovery requirement
```

Never:

```text
projection RUNNING + missing PID = RUNNING
```

---

# 47. Liveness

A lightweight liveness projection may update every 10–15 seconds.

Example:

```json
{
  "supervisor_epoch": "...",
  "phase": "RUNNING",
  "last_journal_sequence": 52,
  "last_journal_sha256": "...",
  "monotonic_age_ms": 3700,
  "child_identity_sha256": "...",
  "mutation_started": true,
  "next_checkpoint_deadline_ms": 45000
}
```

It is advisory only.

---

# 48. Health checkpoint cadence

Avoid journaling high-frequency telemetry.

Recommended:

- liveness projection: 10–15 seconds;
- canonical `HEALTH_CHECKPOINT`: phase boundaries and at most ~60 seconds during long phases;
- important state transitions: immediate canonical event.

This keeps fsync cost focused on meaningful authority.

---

# 49. Failure classification

## Supervisor lost before mutation

```text
HOLD_SUPERVISOR_LOST_BEFORE_MUTATION
```

unless explicit safe-resume policy exists.

## Supervisor lost after mutation began

```text
FAIL_ORPHANED_AFTER_MUTATION_RECOVERY_REQUIRED
```

or transaction-specific recovery classification.

## Stale RUNNING projection with sealed terminal

Projection is rebuilt.

Semantic terminal remains authoritative.

## Child exit without expected semantic evidence

HOLD/FAIL according to transaction contract.

Never inferred PASS.

---

# 50. Journal recovery

Recovery scans from the first event.

Possible outcomes:

### Valid complete prefix

PASS.

### Incomplete final line

- preserve original bytes/hash;
- quarantine torn tail;
- truncate only uncommitted incomplete tail;
- commit recovery event.

### Checkpoint stale

Rebuild.

### Sequence/hash break inside complete prefix

```text
JOURNAL_CORRUPT
```

No automatic semantic recovery.

### Unexpected segment

HOLD unless valid segment-rotation event binds it.

---

# 51. Segment rotation

Version 1 may cap a segment at:

```text
64 MiB
```

Rotation:

```text
SEGMENT_ROTATION_INTENT
↓
fdatasync current
↓
create new segment O_EXCL
↓
first event binds old terminal hash
↓
fsync
↓
continue
```

No deletion in version 1.

---

# 52. ENOSPC emergency evidence

Before protected mutation, create and verify a reserved emergency evidence file.

Example:

```text
journal/emergency.bin
```

Recommended capacity:

```text
1 MiB
```

Write-once framed slots record only essential facts:

- journal write failure;
- supervisor identity;
- transaction;
- phase;
- mutation-started;
- child identity;
- recovery action;
- emergency classification.

If emergency reserve cannot be prepared:

```text
HOLD_EMERGENCY_EVIDENCE_RESERVE_NOT_READY
```

before mutation.

---

# 53. Event taxonomy

## Contract / authority

```text
TRANSACTION_PREPARED
CONTRACT_VERIFIED
SUPERVISOR_STARTED
SUPERVISOR_RECOVERED
WATCHER_ARMED
SCOPE_LEASE_ACQUIRED
AUTHORITY_BOUND
AUTHORITY_REJECTED
CALL_AUTHORITY_RESERVED
CALL_AUTHORITY_CONSUMED
NONCE_RETIRED
```

## Process

```text
CHILD_SPAWN_INTENT
CHILD_STARTED
CHILD_CHECKPOINT
CHILD_EXITED
CHILD_SIGNAL_SENT
CHILD_REAPED
OWNED_PROCESS_CLEANUP_COMPLETE
UNOWNED_PROCESS_CONFLICT
```

## Execution

```text
PRECHECK_COMPLETE
APPLY_START_AUTHORIZED
APPLY_STARTED
APPLY_EXITED
POSTCHECK_COMPLETE
RECOVERY_DECISION
RECOVERY_ACTION_AUTHORIZED
RECOVERY_STARTED
RECOVERY_EXITED
RECOVERY_POSTCHECK_COMPLETE
```

## Evidence / health

```text
ARTIFACT_READY
ARTIFACT_CAPTURED
CHECKER_COMPLETE
WATCHER_OBSERVATION
HEALTH_CHECKPOINT
TIMEOUT_REACHED
INTEGRITY_CONFLICT_DETECTED
JOURNAL_RECOVERY_COMPLETE
```

## Terminal

```text
TERMINAL_REDUCTION_PREPARED
TERMINAL_DECISION
MANIFEST_CREATED
TERMINAL_SEAL_CREATED
RUN_SEALED
SUPERVISOR_CLOSED
```

## Notification

```text
NOTIFICATION_REQUESTED
NOTIFICATION_SUBMITTED
OWNER_DELIVERY_CONFIRMED
OWNER_DELIVERY_UNKNOWN
OWNER_DELIVERY_FAILED
```

---

# 54. Role/event allowlist

Children may propose only predefined classes.

Example:

| Role | Event classes |
|---|---|
| Worker | progress, artifact-ready, bounded execution facts |
| Checker | checker observation |
| Watcher | watcher readiness/observation |
| Recovery plugin | recovery pre/post evidence |
| Notification adapter | delivery attempt/result |

Only supervisor can canonically emit:

- terminal decision;
- authority acquisition;
- supervisor recovery;
- process spawn canonicalization;
- manifest/seal;
- supervisor close.

---

# 55. Compatibility projections

During migration, generate old shapes such as:

```text
STATUS.json
SUMMARY.json
heartbeat.json
harness status
registry row
```

Every generated compatibility object must state:

```json
{
  "authority": "projection_only",
  "source_journal_sequence": 42,
  "source_journal_event_sha256": "...",
  "reducer_sha256": "...",
  "rebuildable": true
}
```

No legacy consumer may treat these as higher authority than journal verification.

---

# 56. Security model

Threats include:

- competing supervisors;
- duplicate journal writers;
- forged event proposals;
- role escalation;
- stale epoch replay;
- PID reuse;
- symlink escape;
- hard-link substitution;
- journal replacement;
- truncation;
- torn writes;
- status spoofing;
- same-UID accidental mutation;
- oversized event/resource exhaustion;
- notification spoofing;
- secret leakage;
- duplicate mutable ownership;
- nonce reuse;
- cross-transaction maintenance conflicts;
- worker process escape.

---

# 57. Mandatory security controls

- supervisor `flock`;
- AuthorityDB scope leases;
- full process identity;
- UDS peer credential validation;
- proposal role allowlist;
- contract hash in every event;
- journal hash chain;
- event idempotency;
- CAS;
- WitnessDB;
- exact path registration;
- symlink/hardlink rejection;
- file/size bounds;
- immutable terminal seal;
- secret redaction/privacy scan;
- process groups/sessions;
- close-on-exec descriptors;
- no provider/apply side effect before commit ACK.

---

# 58. Logging

Supervisor captures child stdout/stderr into bounded append-only logs.

Controls:

- byte cap;
- retention policy;
- no unrestricted environment dump;
- secret sanitization;
- truncation event if cap reached.

Logs are not semantic authority unless explicitly captured into CAS and journal-bound.

---

# 59. Proposed modules

```text
scripts/critical_apply/
  cli.py
  supervisor.py

  journal.py
  journal_recovery.py
  event_schema.py
  event_client.py

  cas.py
  progress_db.py
  authority_db.py

  process_identity.py
  process_supervision.py
  filesystem_guard.py
  semantic_paths.py

  reducer.py
  projections.py
  terminal_reduction.py
  terminal_seal.py

  independent_checker.py
  witness_db.py
  alarm_watcher.py

  privacy.py
  migrate_legacy.py

  plugins/
    base.py
    openclaw_package.py
    gateway_restart.py
```

---

# 60. CLI

```bash
critical-apply prepare --spec <spec> --root <root>
critical-apply validate --root <root>
critical-apply launch --root <root>
critical-apply status --root <root> --verify
critical-apply reduce --root <root> --through-sequence N
critical-apply recover --root <root> --classification-only
critical-apply verify-journal --root <root>
critical-apply verify-seal --root <root>
critical-apply rebuild-index --root <root>
critical-apply rebuild-projections --root <root>
critical-apply project-legacy --root <root>
```

`launch` returns only after durable readback of:

```text
SUPERVISOR_STARTED
WATCHER_ARMED
```

It does not report semantic PASS.

---

# 61. Key internal interfaces

```python
class JournalWriter:
    def recover(self) -> RecoveryResult: ...
    def append(self, proposal: EventProposal, proposer: ProcessIdentity) -> CommitAck: ...
    def head(self) -> JournalHead: ...

class ArtifactStore:
    def capture(self, registered_path: RegisteredArtifact) -> CASObject: ...
    def verify(self, sha256: str) -> bool: ...

class ProgressIndex:
    def apply_event(self, event: CanonicalEvent) -> None: ...
    def rebuild(self, journal: JournalReader) -> None: ...

class AuthorityStore:
    def acquire_scope(self, scope: str, owner: AuthorityOwner) -> LeaseReceipt: ...
    def consume_nonce(self, nonce_hash: str, receipt: EventRef) -> ConsumeReceipt: ...

class CanonicalReducer:
    def reduce(
        self,
        contract: Contract,
        journal: JournalPrefix,
        artifacts: ArtifactReader
    ) -> ReductionResult: ...

class IndependentChecker:
    def verify(self, root: Path) -> VerificationResult: ...
    def witness(self, result: VerificationResult) -> WitnessReceipt: ...
```

---

# 62. Health gates

## HG-00 — Architecture and authority freeze

Must prove:

- exact source authority;
- storage authority roles frozen;
- journal canonical;
- ProgressDB non-authoritative;
- WitnessDB independent;
- AuthorityDB cross-transaction only;
- ownership table complete;
- WSL filesystem strategy frozen;
- UDS path strategy frozen;
- same-UID threat model frozen;
- semantic-path bridge fixed by design;
- duplicate nonce-ledger ownership resolved.

PASS:

```text
PASS_HG00_ARCHITECTURE_AUTHORITY_FROZEN
```

---

## HG-01 — Event/contract integrity

Must prove:

- schema vectors;
- duplicate-key rejection;
- canonical JSON vectors;
- proposer/committer schema;
- event hash vectors;
- terminal reduction binding;
- unknown critical schemas fail closed.

Threshold:

```text
100% required vectors
```

---

## HG-02 — Lease and single-writer safety

Must prove:

- competing supervisor rejected;
- PID reuse rejected;
- stale PID cannot seize authority;
- cross-transaction scope collision rejected;
- wrong boot generation rejected;
- root inode replacement detected.

---

## HG-03 — Journal durability

Required crash matrix around:

- pre-write;
- partial write;
- complete write/pre-fsync;
- post-fsync/pre-ACK;
- post-ACK immediate kill;
- index failure;
- checkpoint failure;
- segment rotation;
- ENOSPC.

Threshold:

```text
0 acknowledged events lost
0 false PASS
```

---

## HG-04 — Reducer and terminal monotonicity

Must prove:

- repeat replay byte-identical;
- terminal candidate/decision binding;
- terminal cannot regress;
- conflicting terminal is integrity failure;
- stale RUNNING projection never wins.

At least:

```text
100 deterministic replays per fixture corpus
```

---

## HG-05 — Process ownership

Must prove:

- PID/start ticks/boot ID identity;
- fork/parent exit classification;
- owned descendants cleaned;
- unowned process never killed;
- cleanup occurs before PASS seal;
- watcher failure domain independent where required.

---

## HG-06 — Filesystem and CAS

Must prove:

- exact paths;
- no governing recursive scans;
- symlink rejection;
- hard-link rejection;
- wrong type/mode rejected;
- CAS immutable capture;
- mutation of original artifact after CAS capture has no semantic effect;
- no out-of-root writes.

---

## HG-07 — Independent checker/witness

Must prove:

- terminal-first status;
- sealed PASS/HOLD with stale process reports correctly;
- WitnessDB records terminal head;
- later journal truncation is detected;
- notification does not rewrite semantic result.

---

## HG-08 — Security/privacy

Must prove:

- wrong UID/PID/role rejected;
- wrong epoch rejected;
- event replay handling;
- resource bounds;
- same-UID threat model behaves as declared;
- privacy scan clean;
- tool hashes exact.

---

## HG-09 — Offline integrated resilience

Full PREP_ONLY synthetic transactions:

```text
PASS
HOLD
FAIL
ABORT
supervisor crash
worker crash
watcher crash
PID reuse
ENOSPC
corrupt projection
deleted ProgressDB
deleted checkpoint
stale RUNNING
```

Delete all derived state and rebuild.

Canonical outcome must remain identical.

---

## HG-10 — Legacy shadow

Must prove:

- old evidence untouched;
- explicit semantic paths govern;
- compatibility projections explain all differences;
- no command-derived path correctness logic;
- status query uses index rather than recursive scans.

---

## HG-11 — Governed no-op canary

Must prove:

- exact frozen package;
- explicit owner authorization;
- independent checker;
- no-op child;
- ProgressDB deletion/recovery;
- watcher alert;
- owner closeout;
- off-switch.

No mutation canary yet.

---

## HG-12 — Production promotion

Requires separate transactions for:

1. installation/apply;
2. runtime restart/activation;
3. functional/provider smoke.

No implicit chaining.

---

# 63. Performance and efficiency measurements

Correctness is primary, but operational efficiency must be measured.

Collect:

```text
journal commit latency p50/p95/p99
20-client ingress latency
64 MiB journal replay duration
ProgressDB rebuild duration
status query latency
CAS capture throughput
terminal reduction duration
WitnessDB write latency
```

Production thresholds should be set from actual WSL/Inspiron measurements rather than invented in advance.

---

# 64. Unit tests

Required test families:

- canonical JSON;
- hash chain;
- event schema;
- role/event permission;
- event idempotency;
- state transitions;
- reduction;
- terminal candidate;
- manifest;
- seal;
- CAS;
- ProgressDB replay;
- AuthorityDB lease;
- WitnessDB;
- semantic paths;
- process identity;
- filesystem guard.

---

# 65. Crash tests

Inject termination around every durability boundary.

Expected result must always be exactly one of:

```text
valid committed prefix
idempotent recovered commit
quarantined torn uncommitted tail
explicit integrity HOLD/FAIL
```

Never:

```text
silent event loss
silent duplicate side effect
false PASS
```

---

# 66. Concurrency tests

Test:

```text
2
5
20
```

concurrent event clients.

Also:

- duplicate same event;
- conflicting duplicate;
- competing supervisor;
- cross-transaction scope conflict;
- concurrent ProgressDB readers;
- AuthorityDB nonce collision.

---

# 67. Filesystem adversarial tests

- missing directory;
- pre-existing valid directory;
- file where directory expected;
- directory where file expected;
- leaf symlink;
- ancestor symlink;
- hard link;
- wrong owner;
- wrong mode;
- read-only filesystem;
- filesystem replacement;
- root rename;
- ENOSPC;
- oversized event;
- oversized artifact;
- oversized log;
- long UDS path;
- unsupported filesystem semantics.

---

# 68. Lifecycle tests

- child immediate success;
- child immediate failure;
- child hang;
- child forks;
- parent exits first;
- supervisor SIGTERM;
- supervisor SIGKILL;
- watcher dies before launch;
- watcher dies during execution;
- stale heartbeat;
- stale projection;
- PID missing after semantic terminal;
- process orphan after supervisor loss.

---

# 69. Semantic tests

- valid PASS;
- every individual PASS predicate absent;
- timeout plus otherwise successful evidence;
- unjournaled governing artifact;
- corrupt artifact;
- wrong CAS hash;
- terminal conflict;
- seal mismatch;
- unknown critical event;
- notification failure after PASS;
- independent witness mismatch.

---

# 70. Privacy/no-effect tests

Must verify:

- no actual private key or credential values in evidence;
- scanner-pattern literals classified separately;
- environment redaction;
- bounded logs;
- zero provider calls in offline milestones;
- zero production mutation;
- exact mutation sentinels unchanged.

---

# 71. Implementation milestones

## M0 — Architecture freeze

Goal:

Freeze all contracts before runtime implementation.

Deliver:

- event schemas;
- reducer contract;
- storage authority model;
- ownership table;
- state machine;
- terminal algorithm;
- threat model;
- semantic-path registration;
- AuthorityDB model;
- ProgressDB model;
- WitnessDB model;
- CAS model;
- WSL filesystem contract;
- test vectors.

Gates:

```text
HG-00
design portion HG-01
```

No runtime integration.

---

## M1 — Journal, CAS, ProgressDB, AuthorityDB core

Build:

- canonicalization;
- journal writer;
- crash recovery;
- exclusive lease;
- event idempotency;
- CAS;
- ProgressDB;
- cross-transaction AuthorityDB;
- emergency reserve.

Gates:

```text
HG-01
HG-02
HG-03
core HG-06
```

---

## M2 — Supervisor and ingress

Build:

- supervisor lifecycle;
- short-path UDS;
- peer credentials;
- proposer registry;
- child spawn;
- process groups;
- liveness;
- watcher-before-child.

Gates:

```text
HG-02
HG-05
ingress HG-08
```

---

## M3 — Reducer and terminal sealing

Build:

- reducer;
- orthogonal states;
- terminal candidate protocol;
- final terminal decision;
- manifest;
- seal;
- projection rebuild;
- compatibility projection.

Gates:

```text
HG-04
HG-06
```

---

## M4 — Independent checker and WitnessDB

Build:

- journal checker;
- witness store;
- terminal-first reconciliation;
- liveness checker;
- alert logic;
- delivery-state handling.

Gates:

```text
HG-07
remaining HG-08
```

---

## M5 — Offline resilience proof

Execute full deterministic failure corpus.

Include:

- kills;
- crashes;
- PID reuse;
- orphaning;
- torn writes;
- ENOSPC;
- deleted ProgressDB;
- deleted projections;
- corrupted checkpoint;
- witness mismatch;
- CAS mutation attempt.

Gate:

```text
HG-09
```

---

## M6 — Legacy migration/shadow

Implement:

- read-only legacy importer;
- immutable semantic path bridge;
- compatibility projectors;
- historical stale-observer replay;
- divergence ledger.

Gate:

```text
HG-10
```

No old evidence mutation.

---

## M7 — Read-only governed canary

Production-like launch with:

- exact package;
- owner authorization;
- no-op/read-only child;
- real independent checker;
- real notification closeout;
- off-switch.

Gate:

```text
HG-11
```

---

## M8 — Promotion preparation

Prepare:

- frozen release package;
- restore-point strategy;
- install proposal;
- restart proposal;
- provider-smoke proposal;
- rollback plan;
- independent verification.

No production mutation.

---

## M9 — Production install/apply

Separate explicit owner authorization.

Install only.

No automatic Gateway restart.

---

## M10 — Runtime activation/restart

Separate explicit owner authorization.

Verify runtime health and exact package consumption.

---

## M11 — Functional/provider smoke

Separate explicit owner authorization.

Bound:

- exact calls;
- exact recipients;
- exact retries;
- fallbacks;
- cleanup.

---

# 72. Rollout

Promotion sequence:

```text
library only
↓
offline fixtures
↓
historical replay
↓
shadow projections
↓
read-only/no-op canary
↓
low-risk governed transaction
↓
general Critical Apply adoption
```

No stage is skipped because later stages appear healthy.

---

# 73. Off-switch

To disable the new architecture:

- stop launching new transactions with it;
- allow active transactions to finish under their frozen supervisor/reducer version;
- never switch an active transaction between old and new authority systems;
- preserve all journals/CAS/witnesses;
- fall back to last proven harness for new runs.

Never run two canonical writers for the same transaction.

---

# 74. Rollback triggers

Stop promotion immediately on:

- acknowledged event missing after recovery;
- false PASS;
- terminal nondeterminism;
- lock bypass;
- scope lease bypass;
- unowned process killed;
- CAS corruption;
- journal corruption during normal operation;
- WitnessDB proves truncation;
- secret/privacy leak;
- notification incorrectly reported as delivered;
- projection consumed as canonical authority.

---

# 75. Normal status runbook

1. Resolve exact transaction root.
2. Verify contract hash.
3. Verify journal.
4. Check terminal seal first.
5. If sealed, report semantic terminal.
6. If unsealed, verify supervisor lock and full identity.
7. Check monotonic lease only within matching boot ID.
8. Reconcile child identities.
9. Report separately:
   - semantic;
   - execution;
   - process;
   - recovery;
   - notification.
10. Never report `RUNNING` solely from projection state.

---

# 76. Recovery runbook

1. Do not start second supervisor until lock proves exclusivity.
2. Preserve journal before repair.
3. Verify WitnessDB against journal.
4. Recover exact valid prefix.
5. Rebuild ProgressDB/checkpoint/projections.
6. Identify whether mutation began.
7. Reconcile owned processes.
8. Create new supervisor epoch.
9. Commit recovery event.
10. Resume only if frozen policy allows safe resume.
11. Otherwise terminalise HOLD/FAIL and request owner decision.

---

# 77. Terminal closeout

Every closeout reports:

```text
semantic result
terminal journal sequence/hash
reduction hash
manifest hash
seal hash
process cleanup
recovery state
scope lease release
notification state
owner delivery state
provider/model calls
production effects
next authority boundary
```

A terminal closeout is incomplete without a local completion receipt.

---

# 78. Production-readiness acceptance criteria

The architecture is ready for production promotion only when:

- HG-00 through HG-11 all PASS;
- no false PASS exists in the fixture corpus;
- zero acknowledged events are lost under crash recovery;
- 20-client concurrency passes;
- journal replay is deterministic;
- ProgressDB can be completely rebuilt;
- deleted projections reproduce identically;
- stale RUNNING never overrides terminal;
- PID reuse fails closed;
- scope lease collision fails closed;
- wrong UID/PID/role/epoch fails closed;
- exact path/symlink/hardlink tests pass;
- CAS mutation tests pass;
- WitnessDB truncation detection passes;
- privacy has zero blocking findings;
- no-op canary passes;
- off-switch works;
- rollback plan is proven;
- owner-ready production promotion artifacts exist;
- owner separately authorizes promotion.

---

# 79. Core invariants for property testing

1. Sequence increments by one.
2. Every event hash verifies.
3. Every predecessor hash equals prior event hash.
4. Every event binds the same transaction and contract.
5. Epoch changes only through a valid recovery transition.
6. Supervisor is the only canonical committer.
7. Proposer identity is independently recorded.
8. Every governing artifact is CAS-bound.
9. Every governing artifact path was pre-registered.
10. A terminal decision cannot transition back to nonterminal.
11. Conflicting terminals are integrity faults.
12. PASS implies every required PASS predicate.
13. Notification cannot alter semantic outcome.
14. Projection deletion does not alter semantic outcome.
15. ProgressDB deletion does not alter semantic outcome.
16. Checkpoint deletion does not alter semantic outcome.
17. Concurrent proposal order may vary, but any committed total order reduces deterministically.
18. Idempotent duplicate event does not create another semantic event.
19. Conflicting duplicate event never passes.
20. No protected side effect begins before required committed ACK.
21. Second supervisor cannot commit while lease is held.
22. Cross-transaction conflicting scope cannot be acquired.
23. Process identity mismatch never grants kill authority.
24. Sealed terminal outranks process lifecycle and stale projection.
25. Unknown critical schema cannot produce PASS.
26. Witness mismatch prevents trustworthy closeout.
27. Monotonic lease comparisons never cross boot IDs.
28. Enabled mutation authority cannot survive unproven nonce reuse.
29. CAS object hash is stable for the lifetime of the transaction.
30. Every terminal explicitly reports production/provider effects.

---

# 80. Recommended immediate milestone

The first implementation milestone should be:

```text
CAH-J1-M0_ARCHITECTURE_AUTHORITY_AND_EVENT_CONTRACT_FREEZE
```

It remains:

```text
PREP_ONLY
zero production mutation
zero Gateway mutation
zero provider calls
zero consumed production authority
```

M0 should freeze:

- this authority hierarchy;
- journal schema;
- proposal/committer schema;
- reducer contract;
- terminal reduction protocol;
- CAS contract;
- ProgressDB contract;
- WitnessDB contract;
- AuthorityDB contract;
- semantic-path registration;
- filesystem/WSL requirements;
- socket strategy;
- ownership table;
- same-UID threat model;
- state transitions;
- health gates;
- test vectors;
- migration boundaries.

Expected M0 terminal:

```text
PASS_CAH_J1_M0_SUPERVISOR_EVENT_JOURNAL_ARCHITECTURE_AUTHORITY_STORAGE_AND_SECURITY_CONTRACTS_FROZEN_NO_PRODUCTION_EFFECT
```

or a specific HOLD naming the unresolved invariant.

---

# 81. Architectural summary

The system deliberately answers five different questions with five different mechanisms:

### What happened?

```text
Canonical append-only journal
```

### What exact evidence did it rely on?

```text
Supervisor-owned content-addressed store
```

### What is happening right now?

```text
Rebuildable ProgressDB + projections
```

### Can an independent component prove that history existed?

```text
Checker-owned WitnessDB
```

### Who owns a shared mutation authority or consumed nonce?

```text
AuthorityDB
```

No one of those stores is permitted to silently take over another store's authority.

The central invariant remains:

> A Critical Apply state exists because the supervisor durably committed the facts from which the deterministic reducer derives it.

Everything else is evidence, acceleration, independent witnessing, or authority for a separate domain.

That is the foundation on which observer staleness becomes a recoverable projection problem rather than a competing source of truth.