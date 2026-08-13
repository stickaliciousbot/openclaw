# Failed attempts

Five verifier-owned, pre-closeout attempts are preserved:

1. Confined baseline-directory setup race/stale-directory condition; fixed with idempotent setup.
2. Fresh-test inventory assertion typo (42 declared vs 50 actual proof mutations); corrected to 50/104.
3. Tar member-list directory-suffix canonicalization and over-broad schema baseline interpretation.
4. Remaining over-broad schema-registry interpretation.
5. Seven schema mutation diagnostics relied only on candidate rejection after the audit was narrowed; explicit independent top-level/nested schema diagnostics were added.

None attempted or completed a write outside the fresh evidence root or verifier-owned `/tmp`; none changed candidate/source/prior evidence/archive/Git/config/runtime/production state; no candidate repair or validator weakening occurred. Final execution passed 104/104 and 52/52.

The prior verifier-boundary HOLD remains preserved and non-authoritative for candidate findings. The prohibited archival R1 script was identified during source inspection and never executed.
