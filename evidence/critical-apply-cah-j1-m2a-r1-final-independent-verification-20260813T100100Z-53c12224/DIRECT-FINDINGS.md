# Direct findings

Direct review was performed against the repaired design, all 13 contract fixtures, validator, supplied 55-case suite, supplied 26-case adversarial port, prior six blocker groups, and bound M0-R3/M1 authorities. Local PASS claims were not trusted.

## Verified repairs

- **B01 partial repair:** exact release-recorded → supervisor-close adjacency is present; preimage preparation is separated and bound to release head.
- **B02:** N07 exact nine-token sequence unconditionally captures descriptor-bound bytes, reopens SHA/size/path, commits and reopens the exact journal reference, then binds/reopens AuthorityDB.
- **B03:** `action_allowed` is typed as bounded non-provider child eligibility, true only at T09; `provider_call_allowed` and legacy alias are false; future N05+N06 gate is inactive.
- **B04:** N01–N11 IDs/order/semantics/critical predicates are compared exactly.
- **B05 partial repair:** 25 transitions × two named sides = 50 canonical vectors, plus two separate artifact vectors; IDs, observed side states, and proof-ID strings are checked.
- **B06 partial repair:** supplied validator contains executable checks for the enumerated baseline invariants and rejects all 55 supplied mutations plus all 26 supplied adversarial cases.

## Blocking direct findings

### M2A-R1-FINAL-B01 — canonical closeout contradicts M0-R3

M0-R3 freezes `SUPERVISOR_CLOSED` as the **final canonical journal event**, receipt publication as artifact-only/nonsemantic with no journal append, and lock release as OS-lock lifecycle action. The repaired state machine instead includes `COMPLETION_RECEIPT_PUBLISHED` and `TRANSACTION_LOCK_RELEASED` in `canonical_projection` and marks both corresponding transitions `canonical:true`. Thus the baseline itself violates the governing closeout contract. It also has no executable field/property proving receipt publication cannot alter `closeout_head`.

Minimal repair: make the canonical chain end at `SUPERVISOR_CLOSED`; move receipt publication and lock release to separate noncanonical artifact/lifecycle vectors; bind publication to the already-fixed closeout head and explicitly prohibit semantic/head mutation.

### M2A-R1-FINAL-B02 — crash recovery proof content is unbound

The crash fixture contains proof-ID strings only. There is no typed proof registry or proof-content object, so proof IDs cannot resolve to exact transition/side-specific journal head, epoch/fence, and bound-artifact requirements. This fails the mandatory “side-specific proof IDs **and proof content**” and cross-artifact resolution requirement.

Minimal repair: add a sealed typed proof registry (or equivalent exact objects), require every canonical/artifact vector proof ID to resolve exactly, enforce transition/side/content equality, and add wrong-content/unresolved/cross-side mutations.

### M2A-R1-FINAL-B03 — validator/schema/cross-artifact gates remain weak

The fresh 56-case suite rejected all 26 prior unsafe mutations but accepted **25/30 fresh unsafe mutations**. Accepted categories include prefix-only schema identities; unknown top-level/nested/transition/ACK fields; action and future-provider gate disagreement between state and child contracts; removed child fence/result/ACK requirements; drifted declared adjacency/state chain/transition authority; meaningless ACK input; concurrency vector labels with contradictory scope content; renamed/untrusted paths and wrong writer authority; weakened/extra component objects; tampered M0-R3/M1 immutable bindings; and a contradictory design sentence that passed because cross-reference validation is string-presence only.

Minimal repair: enforce exact schemas with allowed-key/type/value sets at every object level; exact cross-artifact equality for action/child/ACK/concurrency/crash/path/component contracts; exact immutable authority binding and rehash; semantic design cross-reference binding; and mutations for every accepted case plus combination attacks.

## Superficial-string assessment

The validator performs many real structural equality checks, so it is not merely a grep script. However, material gates remain superficial: schema acceptance is `startswith`, design validation is filename presence only, proof identifiers are accepted without proof bodies, and several declarations/fixtures are validated independently rather than cross-consistently. Those weaknesses explain the 25 unsafe acceptances.
