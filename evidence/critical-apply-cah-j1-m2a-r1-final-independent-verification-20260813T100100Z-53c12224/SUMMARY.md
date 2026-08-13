# CAH-J1 M2A-R1 Final Independent Verification

## Terminal: HOLD

The repaired candidate’s own gates rerun cleanly in an exact disposable copy: `py_compile` PASS, validator PASS, **55/55** mutations rejected, and **26/26** supplied adversarial-port cases rejected. Immutable inputs and all three relevant manifests rehashed cleanly.

Fresh independent testing did not clear the contract. A new **56-case** suite (26 prior unsafe ports + 30 fresh cases/combinations) rejected 31 and accepted **25 unsafe mutations**. Direct review found three blocker groups:

1. The baseline marks receipt publication and lock release canonical after `SUPERVISOR_CLOSED`, contradicting M0-R3’s final-canonical-close and artifact-only receipt rules.
2. Crash vectors name proof IDs but provide no typed proof registry/content to resolve and verify.
3. Exact schema and cross-artifact gates remain incomplete; accepted attacks include unknown fields, schema-prefix spoofing, inconsistent state/child/ACK/concurrency/path/component contracts, tampered M0-R3/M1 bindings, and superficial design cross-reference passing.

Privacy: **PASS** (exact scanner `ce38bf…8115`, zero findings/blockers/issues). Zero effect: **PASS**; immutable inputs, HEAD/index/config and operational surfaces remained unchanged; zero process leaks.

**M2B remains not started and is not authorized.** No M2B proposal is issued because PASS was not reached. Minimal repairs are in `FINDINGS.json` and `DIRECT-FINDINGS.md`.
