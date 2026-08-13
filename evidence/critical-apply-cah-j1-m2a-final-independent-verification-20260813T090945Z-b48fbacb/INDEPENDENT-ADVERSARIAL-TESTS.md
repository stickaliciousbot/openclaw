# Independent Adversarial Tests

- Candidate validator baseline: PASS, return code 0.
- Candidate mutation suite: 12/12 expected rejections PASS.
- Verifier-authored adversarial suite: 26 cases; 8 unsafe mutations rejected, **18 unsafe mutations accepted**.

Accepted unsafe mutations included: overlap dual-active; child self-registration/path creation; ACK before sync/bind; replay conflict execution; stale fence result acceptance; contradictory N04 bypass; intervening canonical close event; notification authority; witness terminal authority; automatic unknown-outcome retry; shadow authority; missing exact transition side; generic crash proof; `N07_SKIP_CAS_AND_BIND`; `call_allowed=true` before nonce barriers; pre-scope action; permissive ingress unknown fields; multiple path writers; meaningless ACK vector.

Machine-readable per-case evidence: `INDEPENDENT-ADVERSARIAL-TESTS.json`.
