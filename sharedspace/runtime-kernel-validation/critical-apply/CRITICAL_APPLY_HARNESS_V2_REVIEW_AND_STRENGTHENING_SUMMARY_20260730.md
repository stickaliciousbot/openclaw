# Critical Apply Harness Review — Findings and Strengthening Summary

**Date:** 2026-07-30  
**Reviewed:**
- `critical-apply-observation-harness-architecture-2026-07-30.md`
- `CRITICAL_APPLY_OBSERVER_LOW_LEVEL_DESIGN_AND_BUILD_PLAN_20260730.md`

**Result:** The original documents establish the correct governing principle and a strong initial milestone ladder, but they were not yet safe enough to govern production mutation or the remaining Universal Runtime Kernel delivery. The v2 replacements close the principal contract gaps below.

## 1. Production-blocking gaps found

### 1.1 “Detached” was not a durable topology

The original architecture defined the observation harness as detached and receipt-driven, but did not require a pre-existing OS supervisor, service restart policy, startup reconciliation, or a safe bootstrap path. A detached shell process, `nohup`, or `setsid` can still die, become orphaned, or lose its parent/exit status.

**Strengthening:** v2 requires Harness Resiliency Level 3: system-supervised observer, persistent state, single-writer fencing, launch gate, process/cgroup tracking, reboot reconciliation, and no ad hoc detach.

### 1.2 Receipt-before-mutation was internally impossible

The original `apply-start.json` was required to exist before execution while also containing the child PID. A PID cannot be known before the child is created, and a normal `Popen` child can mutate before the parent durably records it.

**Strengthening:** v2 splits this into `apply-intent`, `apply-spawned-blocked`, `apply-release`, and `apply-exit`. The child blocks before `execve` until its identity and release receipt are fsynced.

### 1.3 Approval could become stale before execution

The original state machine acquired the maintenance lock early and did not fully specify immutable approval binding, expiry, one-time consumption, code/candidate/restore hashes, or immediate pre-release revalidation. Holding a lock across chat approval is brittle; releasing it without revalidation creates a TOCTOU race.

**Strengthening:** v2 separates prepare, approval, and commit. Commit reacquires locks and revalidates all bound inputs. Any drift invalidates approval.

### 1.4 Restore freshness semantics could block the only safe recovery

The original recovery decision required a restore point to remain fresh. A restore point valid before mutation could cross the one-hour threshold during a long apply and become unusable precisely when needed.

**Strengthening:** freshness is checked at `MUTATION_RELEASE`. After release, the exact bound restore artifact remains eligible for that transaction if its seal and pre-state binding still verify.

### 1.5 Exit status and system state were conflated

The original classifications did not fully distinguish:
- installer exit;
- official package generation;
- running Gateway generation;
- hidden staging generations;
- package-manager substrate;
- protected adjacent state;
- recovery state.

This can cause a successful effective install with nonzero exit to be rolled back, or a coherent root with unrelated mutation to be called “no mutation.”

**Strengthening:** v2 uses a multidimensional state vector and a generation model (`candidate`, `restore`, `official`, `running`, `staging`). `FAIL_SAFE_NO_MUTATION` requires full equality proof.

### 1.6 Recovery depended too heavily on npm

When npm or the global package substrate is the failure source, invoking npm again is unsafe.

**Strengthening:** v2 makes verified filesystem reconstruction plus atomic rename the default recovery. Offline npm reinstall is secondary and only allowed when the npm substrate is independently coherent and explicitly authorised.

### 1.7 Evidence was not fully crash-consistent or tamper-evident

The original receipts and manifest did not define atomic write/fsync semantics, append-only ordering, journal projection rules, tamper detection, or terminal sealing.

**Strengthening:** v2 defines a hash-chained event journal, canonical atomic receipts, fsync ordering, projections, non-circular evidence manifest, and terminal seal.

### 1.8 Observer failure and reboot semantics were incomplete

The original session-loss test focused on killing the foreground reader. It did not fully define observer SIGKILL, WSL reboot, unknown child exit, recovery interruption, or replay prevention.

**Strengthening:** v2 adds phase-specific startup reconciliation, cgroup identity, no blind re-exec after mutation release, and idempotent recovery.

### 1.9 Locking was documentary, not a fencing mechanism

The original lock receipt could be mistaken for the lock itself and did not define lock order, conflict detection, or transaction fencing.

**Strengthening:** v2 requires held kernel locks, ordered surface locks, process identity, and a generation token. Stale lock break remains manual.

### 1.10 Resource exhaustion could destroy the evidence needed for recovery

There was no hard free-space/inode gate, log quota, fsync test, or emergency receipt reserve.

**Strengthening:** v2 blocks before release when durable evidence capacity is unproven and adds an emergency terminal-receipt reserve for post-release `ENOSPC`.

### 1.11 Package apply did not fully guard the global npm prefix

The original package checks focused on OpenClaw critical files but did not require strict comparison of unrelated global packages, bin links, executable identity, npm prefix, or uncontrolled installer network side effects.

**Strengthening:** v2 separates package-manager substrate from OpenClaw root health and guards unrelated global prefix state.

### 1.12 Universal Runtime Kernel integration was not yet a governed plugin model

The original plugin interface was imperative and package-specific. It did not define capability/surface declarations, predecessor seals, no-authority-inheritance, or a repeatable promotion ladder for later kernel mutations.

**Strengthening:** v2 defines a typed plugin contract with read/write/recovery/guard/forbidden sets and requires each later plugin to pass contract, fixture, crash, shadow, live-read-only, restore, and canary stages independently.

## 2. Important retained strengths

The following original decisions were retained and made stricter:

- no foreground production mutation;
- fresh restore point before apply;
- observer-owned npm/package classification;
- automatic bounded recovery for missing/empty/incomplete official root;
- process-reference inspection before touching `.openclaw-*`;
- no hidden-directory deletion;
- package apply, restart, and functional smoke as separate transactions;
- protected cron/memory sentinels;
- milestone progression from contracts and fixtures to shadow and owner-approved canary;
- no production mutation while the runner is absent or unproven.

## 3. Recommended build order

1. M0 strict contracts and threat model.
2. M1 crash-consistent evidence kernel.
3. M2 authority, locks, and commit fencing.
4. M3 restore subsystem and idempotent recovery.
5. M4 HRL-3 observer and launch gate.
6. M5 package/generation classifiers.
7. M6 recovery matrix.
8. M6B observer service bootstrap under the previously proven harness.
9. M7 boundary/campaign enforcement.
10. M8–M10 live read-only, restore-only, and isolated shadow validation.
11. M11 first owner-approved package-only production canary.
12. M12 restart and M13 functional smoke as separate approvals.
13. M14+ remaining Universal Runtime Kernel plugins, each repeating the promotion ladder.

## 4. Current authority statement

This review and the v2 documents are architecture and preparation artifacts only. No deploy, install, service activation, restart, cron mutation, provider call, package mutation, protected-memory mutation, or recovery action was performed or authorised.
