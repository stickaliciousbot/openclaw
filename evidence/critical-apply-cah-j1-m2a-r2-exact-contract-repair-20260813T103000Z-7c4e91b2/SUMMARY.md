# CAH-J1 M2A-R2 Exact Contract Repair

## Terminal: `PASS_CONSTRUCTION_HOLD_FOR_FRESH_INDEPENDENT_VERIFICATION`

B01 is repaired with exactly 23 canonical transitions ending at `SUPERVISOR_CLOSED`; receipt publication and lock release are two ordered noncanonical lifecycle operations that cannot mutate semantic, terminal-decision, or closeout heads. AP01 remains a noncanonical release-head side condition.

B02 is repaired with 46 canonical transition-side vectors, 2 artifact-preparation vectors, 4 lifecycle vectors, and 52 unique typed proofs (46 canonical + 6 artifact/lifecycle), all exactly resolved and action/provider-false until proof.

B03 is repaired with a strict per-object schema registry for 17 governing artifacts, frozen exact artifact semantics, exact cross-artifact gates, actual authority-file/manifest rehashing, and semantic design digest binding.

Tests: prior 55/55, prior 26/26, fresh R1 56/56 plus 9/9 direct checks, and new R2 18/18 combinations rejected: **155/155**, zero unsafe accepts. Clean validator and fresh disposable exact-copy exercise passed. Privacy passed with scanner `ce38bf…8115`; tracked parity, immutable input rehash, zero effect, and process leak checks passed.

M2B is not started or authorized. A fresh independent verifier must rehash this manifest, independently run all gates in a disposable copy, and issue PASS or exact HOLD.
