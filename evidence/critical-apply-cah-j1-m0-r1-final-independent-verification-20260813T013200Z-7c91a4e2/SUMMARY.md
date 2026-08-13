# CAH-J1-M0-R1 Final Independent Verification

**Status:** `HOLD`

**Terminal:** `HOLD_CAH_J1_M0_R1_FOR_CLOSEOUT_PREIMAGE_FIXED_POINT_AND_NONCE_N04_N07_MATRIX_ORDER_CORRECTIONS_NO_PRODUCTION_EFFECT`

Mechanical and identity checks passed:

- expected manifest SHA-256 exact;
- expected privacy receipt SHA-256 exact;
- all four governing input identities exact;
- all 25 manifest-listed hashes and byte sizes exact;
- all 25 candidate JSON files parse;
- candidate validator returned PASS, exit 0;
- privacy receipt reports zero findings/issues;
- no candidate or production mutation occurred.

The prior post-freeze allowlist blocker is resolved: cleanup and reconciliation are pre-fence and rejected afterward, and `TERMINAL_SEAL_RECORDED` is named.

Two blockers remain:

1. The completion preimage includes `close_event_payload_sha256`, while `SUPERVISOR_CLOSED` payload binds the preimage hash. This is a hash fixed-point cycle, contradicting the claimed noncircular one-pass precomputation and leaving closeout non-executable.
2. The nonce matrix is count-complete but not protocol-complete. Its N04 vectors place AuthorityDB rebinding before the required `CALL_SAFE_RESUME_AUTHORIZED` journal event, and its N07 vectors place AuthorityDB outcome binding before the required `CALL_OUTCOME_RECORDED` journal commit. Both reverse the normative state-machine ordering.

CAS covers all 13 publication steps pre/post plus required faults. The closeout matrix covers preimage construction through lock release, but its underlying close-event algorithm remains blocked by item 1.

B1, B3, B5, B6, S2, S3, S4 and sole-journal semantic authority pass. B2 is held by item 2; B4/S1 by item 1.

See `FINDINGS.json` for exact evidence and corrections.
