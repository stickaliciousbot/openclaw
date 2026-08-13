# CAH-J1 Final Independent Verification Summary

- **M1 permanent preservation: PASS_VERIFIED.** All manifests and named hashes match; permanent patch `0444`, 106031 bytes, SHA `7cde7ec7…b8d4bc`; Git-object-plus-permanent-patch reconstruction produced 7/7 exact candidate hashes with no `/tmp` input dependency.
- **M2A supervisor/ingress freeze: HOLD.** Six blocker groups. Candidate baseline validator passes and its 12/12 mutations pass, but verifier-authored testing found 18/26 unsafe mutations accepted.
- **Privacy: PASS.** Exact scanner `ce38bf…8115`; 31 exact hash-bound files + 53 persistent files; zero findings/blockers/issues.
- **Zero effect: PASS.** HEAD/index/tracked status and immutable inputs remained byte/hash-equal; zero verifier-owned process leaks; no operational/external effects; M2B not started.

## Minimal repair package

1. Encode canonical-event projection explicitly and enforce exact `SCOPE_LEASE_RELEASE_RECORDED` → `SUPERVISOR_CLOSED` adjacency; T22 must be provably noncanonical/nonsemantic, with a rejection mutation for any intervening canonical event.
2. Make N07 unconditional: governing response/receipt bytes in descriptor CAS, verified exact journal CAS reference, synced/reopened event, then AuthorityDB bind/full commit.
3. Define `action_allowed` as bounded non-provider child/action eligibility; add executable state/nonce cross-gates proving provider calls require exact N05/N06 journal+AuthorityDB barriers and remain forbidden in M2A.
4. Replace prefix-only N01–N11 validation with exact ordered identities and semantics.
5. Make every crash vector transition-specific with exact pre/post state, both sides, precise recovery proofs, and reject missing/duplicate side or generic proof.
6. Add executable schema/content gates and mutations for overlap exclusion, stale epoch/fence, child path authority, ACK ordering/replay conflict, N04, notification/witness non-authority, unknown-no-retry, strict ingress, single creator/writer, runtime/shadow non-authority, and meaningful ACK vectors.
7. Re-seal a repaired M2A candidate and run a fresh independent verification. **Do not start M2B before zero blockers.**
