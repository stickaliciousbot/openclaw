# Critical Apply Observation Harness v2 — M1 Crash-Consistent Evidence Kernel

Status: M1 implementation artifact. This document authorizes no production mutation.

## Scope

M1 implements only the crash-consistent evidence substrate for later Critical Apply transactions:

- atomic immutable receipt creation;
- atomic replaceable projection/head writes;
- append-only hash-chained transaction journal;
- journal validation and crash/corruption classification;
- journal-derived transaction/status projections;
- non-circular evidence manifest and sidecar;
- deterministic terminal integrity seal;
- emergency evidence reserve primitives;
- fixture-only crash, corruption and disk-full simulations.

M1 deliberately does not implement approval recording/consumption, prepare/approve/commit fencing, production/global/surface locks, restore creation/recovery, daemon/service supervision, blocked-child launch, npm/Gateway/cron/provider/delivery execution, protected-memory mutation, or production mutation paths.

## Module boundary

Production M1 modules:

- `scripts/critical_apply_atomic_io.py`
- `scripts/critical_apply_journal.py`
- `scripts/critical_apply_manifest.py`

All production APIs require explicit roots or paths. They do not infer `/home/stickai/.openclaw`, import `subprocess`, execute commands, inspect or signal processes, access the network, call cron/providers/delivery, or mutate package/config/cron/memory surfaces.

Test modules may import `subprocess` only for isolated crash fixtures.

## Atomic I/O

Immutable artifacts are created by `atomic_create_json` / `atomic_create_bytes` and must not already exist. Replaceable projections/heads are written by `atomic_replace_json` / `atomic_replace_bytes`. Both use same-directory temporaries, restrictive modes, complete-write loops, `fsync`, atomic publication/replacement, parent-directory `fsync`, final regular-file validation, and digest verification.

Failpoints cover: before temp creation, after temp creation, during partial write, after complete write before file fsync, after file fsync, before/after publication, before/after parent fsync, before/after final digest verification.

## Journal

Journal event schema: `critical_apply.event.v2`.

Genesis rule: sequence `1` must use `previous_event_sha256 = 0000000000000000000000000000000000000000000000000000000000000000`; no alternate genesis representation is accepted.

The journal head schema is `critical_apply.journal_head.v2` and records committed sequence, committed event SHA, committed byte offset, journal device/inode, wall/monotonic time, and boot ID. Head update follows journal fsync and never precedes durable append.

Crash/corruption classifications:

- `JOURNAL_VALID`
- `JOURNAL_VALID_WITH_UNCOMMITTED_COMPLETE_TAIL`
- `JOURNAL_TORN_TAIL`
- `JOURNAL_HEAD_AHEAD_OF_DURABLE_DATA`
- `JOURNAL_CHAIN_INVALID`
- `JOURNAL_TAMPERED`
- `JOURNAL_IDENTITY_MISMATCH`
- `JOURNAL_UNKNOWN`

No invalid classification is a PASS terminal.

## Projections

`projections/transaction.json` and `projections/status.json` are deterministic replaceable caches derived from the committed journal. The journal is authoritative. Missing projections are rebuildable. Manual edits and stale projections are detected by parity verification. Projection mismatch never mutates the journal.

## Manifest

Manifest schema: `critical_apply.evidence_manifest.v2`.

Policy: `NON_CIRCULAR_EVIDENCE_MANIFEST_POLICY_V1`.

Governed entries record relative path, type, SHA-256, byte count, mode, device, inode, role, artifact kind, and schema where applicable. The manifest rejects absolute/outside paths, `..`, symlinks, duplicate paths, missing files, non-regular governed files, unstable files, and mode policy violations.

Explicit exclusions:

- `manifest.json`
- `manifest.sha256`
- `manifests/evidence-manifest.json`
- `manifests/evidence-manifest.sha256`
- `terminal-seal.json`
- `reserve/evidence-reserve.bin`

## Code bundle

The code-bundle digest binds deterministic path/SHA/byte-count inventory for:

- `scripts/critical_apply_contracts.py`
- `scripts/critical_apply_atomic_io.py`
- `scripts/critical_apply_journal.py`
- `scripts/critical_apply_manifest.py`
- applicable fixture schema definitions.

No `.pyc`, cache, evidence, temporary, or unrelated repository files are included.

## Terminal seal

Terminal seal schema: `critical_apply.terminal_seal.v2`.

The seal binds transaction ID, terminal, committed journal-head SHA, evidence-manifest SHA, runner/code-bundle SHA, wall/monotonic time, boot ID, and schema version. It is deterministic integrity evidence only, not external identity signing.

PASS is not valid merely because a final report, projection, terminal event, or manifest exists. Without a valid seal, finalization classifies as `EVIDENCE_TAMPERED_OR_INCOMPLETE_HOLD`.

## Evidence reserve

The reserve lives at `reserve/evidence-reserve.bin`, mode `0600`, beneath the explicit transaction root. `posix_fallocate` is used where available; write-and-fsync fallback is accurately classified. Release is idempotent and fsyncs the parent. The reserve is not transaction payload, restore content, or governed manifest content after release.

Pre-mutation evidence-space failure blocks progress and cannot consume approval or launch mutation. Post-mutation evidence-space failure releases reserve, writes a minimal emergency receipt where possible, preserves the last valid head, records degradation, and prevents unqualified PASS. M1 tests simulate this only.

## Gates

- B1: `B1_PASS_ATOMIC_RECEIPT_CRASH_MATRIX`
- B2: `B2_PASS_HASH_CHAIN_AND_PROJECTION_PARITY`
- B3: `B3_PASS_TERMINAL_SEAL_NON_CIRCULAR_MANIFEST`
- B4: `B4_PASS_DISK_FULL_EVIDENCE_FAILSAFE`
