# Independent adversarial tests

- Source: `independent_adversarial_tests.py`
- Result detail: `INDEPENDENT-ADVERSARIAL-TESTS.json`
- Exact disposable candidate copy: `/tmp/cah-j1-m2a-r1-verify-53c12224`
- Cases: **56** (all 26 prior unsafe mutations ported exactly + 30 fresh cases, including multi-artifact combination attacks)
- Rejected: **31**
- Unsafe accepted: **25**
- Direct baseline checks: **9**, failures **6**
- Terminal: **HOLD**

Every prior unsafe mutation was rejected. Fresh unsafe acceptances are listed individually in the JSON result and grouped in `DIRECT-FINDINGS.md`. The suite also directly detects that closeout continues canonically after `SUPERVISOR_CLOSED` and that no typed proof registry/content exists.
