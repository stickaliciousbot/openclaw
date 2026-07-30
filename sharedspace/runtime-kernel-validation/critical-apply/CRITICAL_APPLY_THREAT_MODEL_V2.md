# Critical Apply Observation Harness v2 — Threat Model

Status: M0 contract artifact. This document authorizes no production mutation.

## Scope

M0 defines threats, invariants, fail-closed outcomes, and milestone ownership for the Critical Apply Observation Harness v2. Production package apply, restart, cron mutation, provider/delivery calls, protected-memory writes, restore, recovery, service installation, and M1+ implementation are out of scope.

## Safety invariants

| ID | Invariant |
|---|---|
| INV-HRL3 | Critical production mutation requires a promoted HRL-3 supervisor-managed observer; foreground/ad hoc detached execution is forbidden. |
| INV-AUTH | Owner approval binds the complete authority envelope hash and is one-time/atomic. |
| INV-RESTORE | Restore point freshness is evaluated at MUTATION_RELEASE; restore point is evidence, not recovery authority. |
| INV-SURFACE | Primary mutation may touch only write_set; automatic recovery only recovery_write_set; forbidden_set is never accessed through mutation-capable paths. |
| INV-STATE | Terminal classification is a pure core function of state vectors and policy; plugins cannot assert PASS. |
| INV-EVIDENCE | PASS requires complete non-circular manifest and terminal seal; unknown/tampered evidence never maps to PASS. |
| INV-PROCESS | Process identity is never PID-only; PID/start-ticks/boot/cgroup/exe/cmd digest are required. |
| INV-BOUNDARY | Package apply, Gateway restart, and functional smoke are distinct transactions with distinct authority. |

## Threat coverage matrix

| Threat | Affected invariant | Prevention / detection mechanism | Required evidence | Fail-closed result | Proving milestone |
|---|---|---|---|---|---|
| Foreground client/session loss | INV-HRL3, INV-EVIDENCE | HRL-3 service owns mutation; foreground can prepare/status only | journal, supervisor receipt, terminal seal | APPROVED_NOT_STARTED or APPLY_STATE_UNKNOWN_OPERATOR_REQUIRED | M4/D1 |
| Observer SIGKILL | INV-HRL3 | supervisor restart + startup reconciliation | service restart receipt, journal head | no replay; safe reconciliation HOLD if ambiguous | M4/D1,D5 |
| WSL or host reboot | INV-HRL3, INV-PROCESS | boot-id bound reconciliation; no re-exec after release | boot id, phase receipt, cgroup scan | APPLY_STATE_UNKNOWN_OPERATOR_REQUIRED or recovery decision | M4/D5 |
| PID reuse | INV-PROCESS | compare PID + start ticks + boot ID + cgroup + exe digest | process identity record | RECOVERY_BLOCKED_STATE_UNKNOWN | M4/D3 |
| Child descendants escape immediate process | INV-PROCESS | cgroup/process-group descendant tracking | cgroup scan, timeout receipt | RECOVERY_BLOCKED_STATE_UNKNOWN | M4/D4 |
| System-clock changes | INV-RESTORE | wall UTC + monotonic same-boot cross-check | release-time age receipt | APPROVAL_EXPIRED_REPREPARE_REQUIRED or PRECONDITION_DRIFT_BLOCKED | M3/C1 |
| Huge or truncated output | INV-EVIDENCE | bounded logs to files, quota policy, no chat stdout authority | log refs, quota receipt | EVIDENCE_TAMPERED_OR_INCOMPLETE_HOLD | M1/B4 |
| Partial writes and ENOSPC | INV-EVIDENCE | atomic write/fsync, emergency reserve | atomic receipt proof | EVIDENCE_TAMPERED_OR_INCOMPLETE_HOLD | M1/B1,B4 |
| Stale restore point | INV-RESTORE | release-time freshness check | restore release receipt | APPROVAL_EXPIRED_REPREPARE_REQUIRED | M3/C1 |
| Corrupt restore point | INV-RESTORE | manifest/hash/path validation | restore manifest verification | ROLLBACK_FAIL_OPERATOR_REQUIRED | M3/C2 |
| Substituted restore point | INV-AUTH, INV-RESTORE | restore ID + manifest hash bound to envelope | authority envelope, manifest hash | PRECONDITION_DRIFT_BLOCKED | M2/M3 |
| Path-unsafe restore point | INV-RESTORE, INV-SURFACE | reject traversal/symlink/device/special files | path-safety inventory | ROLLBACK_FAIL_OPERATOR_REQUIRED | M3/C2 |
| Candidate substitution after approval | INV-AUTH | candidate authority hash bound and revalidated | approval binding matrix | PRECONDITION_DRIFT_BLOCKED | M2/A4,E1 |
| Runner drift | INV-AUTH | runner bundle hash bound | observed vs approved hash | PRECONDITION_DRIFT_BLOCKED | M2/A4 |
| Plugin drift | INV-AUTH | plugin bundle hash bound | observed vs approved hash | PRECONDITION_DRIFT_BLOCKED | M2/A4 |
| Contract drift | INV-AUTH | contract bundle hash bound | observed vs approved hash | PRECONDITION_DRIFT_BLOCKED | M2/A4 |
| Interpreter drift | INV-AUTH | interpreter identity hash bound | observed vs approved hash | PRECONDITION_DRIFT_BLOCKED | M2/A4 |
| Supervisor drift | INV-HRL3, INV-AUTH | supervisor-unit SHA bound | unit hash receipt | PRECONDITION_DRIFT_BLOCKED | M2/M4 |
| npm nonzero exit after effective install | INV-STATE | terminal derives from package state, not exit alone | exit + official generation vector | APPLY_EFFECTIVE_EXIT_NONZERO_HOLD | M6/F2 |
| npm removal/partial official root replacement | INV-STATE, INV-RESTORE | official root classifier; bounded recovery | root inventory, recovery decision | FAIL_MUTATION_PARTIAL_RECOVERY_REQUIRED | M5/M6 |
| Hidden .openclaw-* generations | INV-PROCESS, INV-SURFACE | staging inventory + process-reference scan | maps/fd/cwd/exe/cgroup refs | RECOVERY_BLOCKED_STATE_UNKNOWN if ambiguous | M5/E5 |
| Gateway running from old/hidden generation | INV-BOUNDARY, INV-PROCESS | running generation vector; restart separate | PID/start ticks/path refs | PASS_PACKAGE_INSTALLED_HOLD_FOR_SEPARATE_RESTART only if package coherent; no restart | M5/E4,G1 |
| Unrelated cron drift | INV-SURFACE | guard_set field-level policy | jobs.json/run-log hashes | PRECONDITION_DRIFT_BLOCKED or guard HOLD | M5/E7 |
| Unrelated memory drift | INV-SURFACE | protected-memory sentinel guard | sentinel SHA set | PRECONDITION_DRIFT_BLOCKED or guard HOLD | M5/E7 |
| Unrelated config drift | INV-SURFACE | config/route guard hashes | config digest | PRECONDITION_DRIFT_BLOCKED | M5/E7 |
| Unrelated route drift | INV-SURFACE | route guard hashes | route digest | PRECONDITION_DRIFT_BLOCKED | M5/E7 |
| Unrelated package drift | INV-SURFACE | global prefix guard | inventory digest | PRECONDITION_DRIFT_BLOCKED | M5/E7 |
| Unrelated provider drift | INV-SURFACE | provider counters read-only guard | counter digest when locally observable | guard HOLD; never provider call | M5/E7 |
| Interrupted recovery | INV-RESTORE, INV-EVIDENCE | recovery intent durable + idempotency key | recovery-intent/action receipts | RECOVERY_BLOCKED_STATE_UNKNOWN | M3/C4,M6 |
| Duplicate recovery attempts | INV-RESTORE | max one automatic recovery; idempotency marker | recovery count receipt | RECOVERY_BLOCKED_STATE_UNKNOWN | M3/C4 |
| Approval replay | INV-AUTH | one-time nonce atomic consumption | approval-consumed receipt | APPROVED_NOT_STARTED or replay block; no second mutation | M2/A4 |
| Evidence tampering | INV-EVIDENCE | hash-chain journal, manifest, terminal seal | seal validation | EVIDENCE_TAMPERED_OR_INCOMPLETE_HOLD | M1/B2,B3 |
| Supervisor/system-service infrastructure absence | INV-HRL3 | daemon unavailable is blocking contract state | service proof absent receipt | stop at architecture/prep; no mutation | M0/A1,M4 |

## M0 gates

M0 proves A1–A4 only:

- A1: no foreground/generic critical mutation path;
- A2: strict schema and canonical hash;
- A3: state-machine totality;
- A4: authority binding and one-time consumption.

M0 does not prove journal durability, locks, restore, process gates, classifiers, recovery, live read-only inspection, shadow, bootstrap, package apply, restart, or smoke.
