# CAH-J1-M0 independent protocol review

**Review root:** `evidence/critical-apply-cah-j1-m0-independent-review-20260813T004300Z-9f62c1a4/`  
**Review class:** independent read-only requirements oracle; not final verification of the builder package  
**Scope:** owner revision, M0 adjudication, current `critical_apply_*` source/tests, R18 nonce-ledger ownership and stale-`RUNNING` observations  
**Boundary:** no source/design/memory/builder edits; no provider/model calls; no Gateway/config/runtime/git/install/production mutation

## 1. Adjudication

The owner revision is coherent as the governing M0 input, but the adjudication is correct: it is **not yet a frozen v1 protocol**. M0 remains HOLD until B1–B6 and S1–S4 exist as closed schemas, legal transition tables, executable crash vectors, and health gates.

This review is complete as an independent requirements oracle. It does not attest that an as-yet-unseen builder package meets the oracle.

```text
PASS_REVIEW_COMPLETE_REQUIREMENTS_ORACLE
HOLD_M0_FREEZE_PENDING_CONTRACT_IMPLEMENTATION_AND_LATER_FINAL_VERIFICATION
```

## 2. Immutable reviewed inputs

The exact input inventory is in `INPUT-HASHES.json`. Governing anchors:

- owner revision: `6d80167ba92e1a68c9d17d6027135b289f88c6b9f3d6fd9e24ea86aedab459af`
- M0 adjudication: `1d2853fba832ebc243423c3c2dac00def80c3c2b56d892ee8c83aeff96c34427`
- R18 PREP closeout: `ef2552f482a36fefbc52d87bb7d647712589385dab104d080ddee76ab113612c`
- R18 materializer: `e7ce8c1a3819e6bf558b28642afb8612fb2174d1b3292a508c2db7ca10e3820f`
- R18 live runner: `35906404235b4bd536676555a1da9fda6e893bce1fc4738c23054f01339cb806`
- R18 broker/ledger writer: `8ade0a138f02b825684a1d2551fd1c58b6e160ab53f7a47c31702b9fc1885953`
- historical R18 duplicate-creator failure receipt: `b5ea3cb57e2eaba69f6c696a718843dd0eff59f130393d83cbb2134855832bce`
- historical R18 terminal seal: `dc799507f6ba6939fb38f111325e2bff32cdb63d5df4e26cdb0cde7e7ea89e67`
- historical stale harness `RUNNING` status: `e2bec16b3a813893b4e68dc95341f21d1f42fad608267e9aea9cf2fe5ce3c746`

All 19 current source modules and 23 current Critical Apply tests are individually hashed in `INPUT-HASHES.json`.

## 3. Exact protocol invariants required for freeze

The machine-readable exact field lists, enums, nullability, crash cases, and verifier gates are in `REQUIREMENTS-ORACLE.json`. The non-negotiable invariants are:

1. **Journal-only transaction facts.** The hash-chained canonical journal is the sole transaction-fact authority. ProgressDB, checkpoints, receipts, status, heartbeat, registry, and compatibility files are rebuildable projections or evidence, never semantic authority.
2. **CAS-bound governing bytes.** A reducer consumes only the frozen journal prefix and journal-referenced immutable CAS objects.
3. **One fact, one authority.** AuthorityDB owns only cross-transaction scope leases and nonce consumption. WitnessDB witnesses history. Neither may store or choose semantic PASS/HOLD/FAIL/ABORT.
4. **Closed schemas.** Exact keys/types/enums/nullability; duplicate keys, invalid UTF-8, non-finite numbers, unknown critical values, and noncanonical paths fail closed.
5. **Authenticated commit identity.** Every canonical event binds transaction, contract, supervisor epoch, sequence/hash chain, event ID, proposal hash, proposer identity, supervisor committer identity, payload hash, and CAS refs.
6. **Journal-derived idempotency.** `(transaction_id,event_id)` maps to proposal hash, sequence, event hash, and original ACK by journal replay. ProgressDB may accelerate only after head parity.
7. **Committed terminal fence.** `TERMINAL_REDUCTION_PREPARED` is a canonical event and closes semantic input. Reduction is rerunnable over that exact prefix.
8. **Three distinct heads.** `semantic_reduction_head`, `terminal_decision_head`, and `closeout_head` have separate names and bindings. Later closeout cannot rewrite semantics.
9. **Cleanup before PASS seal.** Owned descendants are reconciled/reaped and cleanup is journal committed before terminal reduction. Unowned processes are never killed.
10. **Single mutable-path owner.** Every normalized directory and leaf has one creator and one writer. Aliases and mutually exclusive variants are checked before launch; duplicates cause `HOLD_DUPLICATE_MUTABLE_PATH_OWNERSHIP`.
11. **Immutable semantic paths.** One closed, hash-bound registration object is passed byte-identically to all components. Correctness paths are never inferred from command text or recursive discovery.
12. **Authority before action.** No protected action starts before its prerequisite canonical ACK and active fenced AuthorityDB state.

### Required AuthorityDB transition legality

```text
ABSENT
  -> RESERVED_PENDING_JOURNAL
  -> JOURNAL_COMMITTED
  -> ACTIVE or CONSUMED
  -> RELEASE_PENDING
  -> RELEASED
```

- Supervisor epoch must be committed before an AuthorityDB row binds it.
- Journal sequence/hash are nullable only while pending.
- Pending, mismatched, orphan, or journal-less `ACTIVE` rows never authorize.
- Release is monotonic; no protected action is allowed after release intent.

### Required nonce/call transition legality

```text
ABSENT
  -> RESERVED_PENDING_JOURNAL
  -> COMMITTED_NOT_USED
  -> CALL_START_COMMITTED
  -> OUTCOME_RECORDED or UNKNOWN_CONSUMED
  -> RETIRED
```

Also legal: `COMMITTED_NOT_USED -> RETIRED` for explicit no-call retirement.

- Call is forbidden before durable `CALL_START_COMMITTED` ACK.
- A crash after call-start commit with no durable outcome defaults to `UNKNOWN_CONSUMED`.
- `UNKNOWN_CONSUMED` is non-retryable; a later attempt needs new owner authority and a new nonce.
- Retirement/consumption survives semantic validation HOLD.

### Required closeout order

```text
cleanup committed
-> terminal input fence committed
-> pure reduction
-> terminal decision committed and replay verified
-> create-once manifest/seal
-> notification terminal outcome
-> independent witness
-> release intent
-> AuthorityDB release
-> release-recorded event
-> completion receipt preparation
-> SUPERVISOR_CLOSED as closeout head
-> completion receipt binds closeout head
-> transaction lock release
```

## 4. R18 duplicate nonce-ledger ownership — confirmed blocker

The R18 evidence demonstrates the exact ownership class M0 must prevent:

- Materializer creates `nonce-ledger/` while creating the run root.
- Live runner later calls `ledger_root.mkdir(mode=0o700)` without `exist_ok=True`.
- The historical run result records `failure_code: "[Errno 17] File exists"`.
- The broker writes `nonce-ledger/nonce-ledger.json` under a per-run root.
- The synthetic runner also writes that same leaf under an alternate runner path.

This yields three distinct issues:

1. **Duplicate directory creator:** materializer and live runner both claim creation.
2. **Unfrozen alternate leaf writers:** fixture and live paths target the same mutable leaf without a machine-checked variant guard.
3. **Wrong authority scope:** a per-run JSON ledger cannot prove cross-transaction nonce uniqueness.

Required v1 repair:

- Authority service/library is the single creator/writer for AuthorityDB directory, DB, WAL, SHM, scope rows, and nonce rows.
- Supervisor journals authority receipt hashes but never writes DB files directly.
- Materializer, runner, broker, checker, reducer, worker, and compatibility code have zero mkdir/write authority for nonce storage.
- Legacy `nonce-ledger` is absent from new transactions or registered read-only migration input. A mutable live legacy ledger blocks launch.
- Static ownership closure and dynamic write receipts both prove one owner and no alias.

A narrow legacy-only repair may designate the materializer as sole directory creator and make the runner validate-only, but that does **not** resolve cross-transaction nonce authority; AuthorityDB is still required.

## 5. R18 stale `RUNNING` semantics — canonical regression fixture

Historical R18 evidence contains:

- semantic `STATUS.json`: terminal `HOLD`, updated `2026-08-12T23:47:09Z`;
- valid terminal seal: `terminal = HOLD`, explicitly says semantic terminal outranks process lifecycle;
- harness status: `RUNNING`, updated earlier at `23:46:00Z`;
- harness progress: `RUNNING / reconcile_semantic_terminal` at `23:47:09Z`;
- detached completion receipt later records PASS for harness detachment/completion mechanics, not semantic PASS.

Correct resolution is deterministic:

```text
semantic result = HOLD
harness RUNNING files = stale rebuildable projections
harness detached PASS = process/observer plane only
```

The terminal-first checker must verify seal → manifest/reduction/journal bindings, return HOLD immediately, then rebuild only registered projection paths. It must not inspect stale RUNNING first, mutate the sealed terminal, or infer that the transaction remains live.

## 6. Crash matrix required

`REQUIREMENTS-ORACLE.json` defines 32 named cases. Minimum closure includes:

- every boundary from supervisor epoch → AuthorityDB pending → journal event → row activation;
- every release-intent → DB release → journal release-recorded boundary;
- nonce reserve → reservation journal → committed-not-used;
- call-start append pre/post sync and ACK;
- invoked/no response; response received/not journaled; outcome journaled/not DB-bound; retirement;
- journal full-line/pre-sync, post-sync/pre-ACK, post-ACK/pre-index;
- terminal fence, reduction, terminal decision, seal, and stale projection;
- CAS temp write, object sync, publish, directory sync, reopen/rehash, journal event, ACK.

Every crash must reduce to exactly one of:

```text
valid committed prefix
idempotent recovered commit
quarantined unacknowledged tail/orphan object
explicit integrity HOLD/FAIL
```

Forbidden outcomes: unauthorized protected action, ambiguous active lease, retry after ambiguous call, duplicate side effect, lost ACKed event, or false PASS.

## 7. Journal-only semantic authority tests

Required destructive-fixture tests (never against production evidence):

- delete ProgressDB/checkpoint/all projections and reproduce byte-identical reduction;
- forge stale/corrupt ProgressDB and prove journal wins;
- forge `RUNNING` after each sealed terminal and prove terminal wins;
- forge projection PASS without decision/seal and reject it;
- delete/corrupt ProgressDB after ACK, retry same event, and return original journal-derived ACK;
- conflicting duplicate event ID commits integrity conflict and blocks PASS;
- inject semantic result into AuthorityDB/WitnessDB and reject/ignore it;
- mutate original artifact after CAS capture and preserve reduction;
- mutate an unregistered artifact and prove no semantic effect;
- truncate behind WitnessDB head and HOLD trustworthy closeout without inventing semantics.

## 8. Descriptor-bound CAS acceptance

Path validation followed by path reopen is insufficient. Required order:

```text
verified parent directory FD
-> openat/openat2 + O_NOFOLLOW registered leaf
-> fstat and bind device/inode/uid/gid/mode/nlink/size
-> stream/hash from that same FD
-> post-copy fstat stability check
-> same-filesystem O_EXCL temp
-> complete write + fdatasync
-> no-overwrite atomic publish
-> fsync affected directories
-> reopen published object O_NOFOLLOW
-> fstat + rehash
-> append/fdatasync journal artifact event
-> ACK
```

Tests must race replacement, symlink swap, hardlink injection, truncation, extension, overwrite, chmod/chown, rename, and concurrent duplicate publication. Orphan unreferenced objects are permitted; missing/corrupt journal-referenced objects are integrity failures.

## 9. SQLite/WAL authority gates

AuthorityDB and WitnessDB require:

- proven local Linux filesystem; not `/mnt/c`;
- database and parent-directory durability on creation;
- asserted `journal_mode=WAL` and `synchronous=FULL`;
- `BEGIN IMMEDIATE` for lease/nonce mutations;
- bounded busy timeout and fail-closed contention;
- exact schema, `user_version`, application identity, constraints, and migration policy;
- startup integrity checks and WAL/SHM ownership/mode validation;
- backup through SQLite backup API or a proven quiesce/checkpoint protocol;
- never copy only the main DB while WAL may contain authority rows;
- crash tests around transaction commit, WAL sync, checkpoint, backup, and restore;
- Witness grade frozen as `WITNESS_GRADE_1_SAME_HOST_SAME_UID_INDEPENDENT_PROCESS_DETECTION`.

ProgressDB may be weaker only because it is fully rebuildable and never authoritative.

## 10. Current-source implementation hazards

The current source is useful prior fixture infrastructure but is not the owner-revision protocol. Principal hazards:

1. `critical_apply_authority.py` states the consumption marker is authoritative and journal append is best-effort—directly contrary to journal-only transaction facts and B1.
2. Consumption reconciliation searches raw journal text for `approval_consumed` instead of validating exact event/nonce/sequence/hash binding.
3. Current event schema lacks event ID/proposal hash/contract/supervisor epoch/proposer-versus-committer/CAS refs.
4. Current writer token does not itself prove held supervisor lock, epoch, fence, or authenticated role.
5. Current recovery treats `journal-head.json` as committed-offset authority; the frozen protocol must derive canonical committed history from journal durability and never lose an ACKed event if a cache update failed.
6. No journal-derived idempotency map exists.
7. Rehydration and controller status rely substantially on receipt/path presence rather than terminal-first reduction.
8. Current seal omits the three heads, reducer, reduction, contract, and cleanup bindings.
9. Current manifest reopens paths and uses replacement publication; it is not descriptor-bound create-once CAS.
10. No AuthorityDB/ProgressDB/WitnessDB SQLite/WAL implementation or immutable semantic-path/ownership registry exists.
11. Current lifecycle table predates terminal fence and corrected release/close ordering.
12. `exist_ok=True` in multiple components can mask duplicate ownership instead of proving it absent.

These are expected deltas, not a claim that current fixture tests are valueless. They are blockers to declaring the new architecture frozen or implemented.

## 11. Later final verifier gates

A later verifier must receive a frozen builder package and independently execute:

- **FV-00:** package/input hash closure;
- **FV-01:** closed schemas and canonical vectors;
- **FV-02:** machine-checked state/lifecycle legality;
- **FV-03:** exhaustive AuthorityDB↔journal and nonce/call crash matrix;
- **FV-04:** journal-only semantics and idempotency under deleted/corrupt derived state;
- **FV-05:** semantic paths, static/dynamic one-owner closure, and R18 duplicate-ledger regression;
- **FV-06:** descriptor-bound CAS adversarial/crash corpus;
- **FV-07:** SQLite/WAL filesystem, durability, contention, integrity, backup, and restore;
- **FV-08:** terminal monotonicity and stale-`RUNNING` reconciliation, including R18;
- **FV-09:** independent checker/Witness grade and truncation detection;
- **FV-10:** privacy, zero-effect, and evidence-manifest integrity.

Final M0 PASS is forbidden until all gates pass against the immutable builder package and no second semantic authority is introduced.

## 12. Review closeout

**Review completeness:**

```text
PASS_CAH_J1_M0_INDEPENDENT_REQUIREMENTS_ORACLE_COMPLETE
```

**Architecture freeze readiness at this review boundary:**

```text
HOLD_FOR_CAH_J1_M0_BUILDER_CONTRACT_COMPLETION_AND_LATER_FINAL_VERIFIER_GATES_FV_00_THROUGH_FV_10
```
