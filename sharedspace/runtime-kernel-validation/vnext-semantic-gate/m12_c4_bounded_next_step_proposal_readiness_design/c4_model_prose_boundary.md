# C4 Model Prose Boundary

Recommended design decision accepted: deterministic proposal skeleton/kernel first, optional non-authoritative prose rendering second.

Model prose is optional and non-authoritative only.

Model prose must not:

- alter proposal_steps.
- alter citations.
- remove uncertainty.
- turn proposal into execution.
- choose PROPOSAL/HOLD/REJECT status.
- add facts or source authority.
- resolve conflicts.
- approve actions.
- override fail-closed behavior.

Provider/model authoritative proposal calls allowed: 0.
