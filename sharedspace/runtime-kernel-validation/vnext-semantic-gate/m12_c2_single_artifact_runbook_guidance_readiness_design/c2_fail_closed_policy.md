# M12-C2 Fail-Closed Policy

C2 returns `HOLD` when any required authority or guard condition is not met.

Fail-closed cases:

- Missing artifact.
- Stale artifact SHA or content drift.
- Ambiguous artifact selection.
- Multiple artifacts selected or required.
- Unapproved source or arbitrary path.
- Artifact contains prompt-injection-like text that would affect the answer.
- Requested guidance would require an external action.
- Requested guidance would require exact code/config/routing/safety authority.
- Requested answer needs cross-artifact synthesis or comparison.
- Deterministic section extractor finds no supported steps/warnings/prerequisites.
- Optional model prose disagrees with deterministic extraction.
- Final guard cannot prove every guidance step from cited sections.

HOLD envelope requirements:

- `status = HOLD`
- `guidance_steps = []`
- `disposition = fail_closed_hold`
- `hold_reason` names the first blocking condition.
- cited source refs may include only diagnostic source refs from the single approved artifact, never alternate sources.
