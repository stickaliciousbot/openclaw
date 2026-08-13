# CAH-J1 M1 FINAL Independent Verification R1 — START

- Verifier session: `agent:main:subagent:db9985b0-e1a8-473c-b60b-3380139a1cba`
- Started: 2026-08-13 15:31 AEST (declared)
- Scope: independent read-only verification of the M1 offline core candidate.
- Candidate construction sources and all existing evidence/worktrees are read-only.
- Disposable candidate root: `/tmp/cah-j1-m1-final-verifier-r1-db9985b0/candidate`
- Forbidden path `/tmp/cah-j1-m1-core-20260813T1240AEST/worktree` will not be accessed.
- Production/config/Gateway/runtime/provider/network/install/commit/push/cron/systemd/external effects are forbidden.

## Pass criteria
1. Immutable base, patch, seven changed paths, manifests, construction evidence, frozen M0 receipts, owner revision and adjudication bind exactly.
2. Direct source review satisfies every frozen M0-R3 executable contract for journal, CAS, ProgressDB, and AuthorityDB; constant-only tests without source gates are blockers.
3. Independent adversarial suite covers all requested tamper, concurrency, crash/recovery, identity, fencing, N04/N07, UNKNOWN_CONSUMED, and 2/5/20 contention properties.
4. `py_compile`, focused 48 tests, relevant predecessor tests, independent tests, construction broad-suite seal, privacy scan, and zero-effect checks pass.
5. Zero blockers and no effects/process leaks.

## Expected closeout artifacts
`INPUT-BINDING.md`, `DIRECT-SOURCE-FINDINGS.md`, adversarial test source/results/logs, `TEST-RESULTS.md`, `PRIVACY-RECEIPT.md`, `ZERO-EFFECT-RECEIPT.md`, `FINDINGS.md`, `INDEPENDENT-RECEIPT.md`, `STATUS`, `SUMMARY.md`, and `EVIDENCE-SHA256.txt`.
