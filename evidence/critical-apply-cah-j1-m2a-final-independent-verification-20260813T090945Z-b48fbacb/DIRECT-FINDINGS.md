# Direct Findings

## M1 preservation

PASS_VERIFIED. Every named input and manifest entry rehashed. Permanent patch mode `0444`, size `106031`, SHA-256 `7cde7ec7…b8d4bc`. Reconstruction used only Git object `b48fbacb…910` plus the permanent patch in a disposable non-Git `/tmp` destination; no temporary original and no development-worktree source files. Exact seven candidate hashes matched. `/tmp` appears only as a disposable reconstruction destination/historical receipt, not an input dependency.

## M2A direct contract review

- Fixture seals, schemas, and design cross-references verified.
- Candidate contains 26 transitions and 52 crash vectors, globally unique IDs, nominal before/after windows for every transition, and 2/5/20 same-scope plus overlap/disjoint/stale epoch/stale fence fixtures.
- Candidate correctly declares journal semantic authority, ProgressDB/notification non-authority, no runtime/production/shadow authority, strict ingress fields, one scalar creator/writer per listed path, and STOP_BEFORE_M2B.
- These declarations are insufficient because executable enforcement is materially incomplete; see blockers.

## Mandatory adjudications

**A — BLOCKER.** The state graph introduces T22 as a lifecycle transition/state between release-recorded and closed. Filtering `artifact_only` yields direct canonical event adjacency, but the validator has no executable canonical-vs-noncanonical adjacency property and accepts a mutation that turns T22 into an intervening journal event. Prose intent cannot supply the missing gate.

**B — BLOCKER.** N07 says `capture governing response bytes if required`. That is optional and does not unconditionally require governing response bytes/receipt in descriptor CAS plus an exact verified journal CAS reference before AuthorityDB bind. This is weaker than the verified M1 source gate.

**C — BLOCKER.** `action_allowed=true` at SCOPE_ACTIVE is not typed as bounded child/action eligibility. `call_allowed` is false in the frozen candidate, but the validator accepts both an early `action_allowed=true` and `call_allowed=true` at T07. Thus provider-call eligibility and N05/N06 barriers are not executable state-machine properties.

**D — BLOCKER.** The suspicious exact-set expression is a no-op. The later gate checks only set length and N01…N11 prefixes, and accepts `N07_SKIP_CAS_AND_BIND`; exact transition identities/suffix semantics are not enforced.

## Threshold adjudication

The nominal counts pass, but exact crash proof does not: after-commit vectors retain the pre-transition `observed_state`, and generic recovery-proof text is reused. The validator checks only transition-ID set, count, false action/call flags, and non-empty proof list; it accepts a missing exact side and a meaningless one-string proof. ACK, overlap, stale fence, path writer, ingress strictness, child path authority, notification/witness authority, and unknown-outcome rules are likewise declared but not sufficiently executable.
