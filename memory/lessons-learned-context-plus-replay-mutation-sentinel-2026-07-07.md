# Lessons learned — Context+ fresh replay mutation sentinel failure

Date: 2026-07-07 AEST

## Incident

Context+ fresh same-suite production replay `production_replay_approved_fresh_20260707` completed all requested work but closed unsafe:

- cases: `440/440`
- provider calls: `440/440`
- provider boundary: `PASS_PROVIDER_CALL_BOUNDARY`
- rate-limit/cooldown: `PASS_NO_RATE_LIMIT_OR_COOLDOWN`
- mutation sentinel: `FAIL_MUTATION_SENTINEL`
- final replay classification: `FAIL_REPLAY_UNSAFE / HOLD_NOT_PROMOTION_ELIGIBLE`
- comparator readiness: `HOLD_SAME_SUITE_COMPARATOR_NOT_READY`

Correct decision: do **not** run same-suite comparator, do **not** promote, and do **not** prepare M6 proposal from this replay.

## What the investigation found

Artifact: `sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/MUTATION_SENTINEL_FAILURE_INVESTIGATION.md`

The sentinel persisted both before and after filtered dirty-workspace lists:

- before filtered entries: `1522`
- after filtered entries: `1520`
- added entries: `0`
- removed entries: `2`
- removed delta entries: `M MEMORY.md`, `?? memory/2026-07-07.md`
- closeout classification: `HOLD_CONCURRENT_WORKSPACE_NOISE`

The full post-run dirty list still contained many pre-existing workspace paths, including protected/adjoining memory/context/state/config-adjacent paths. That keeps the replay unsafe for promotion eligibility even though replay code review found no writer outside its configured output directory.

## Mistakes / near-misses caught

1. **Truncated evidence read led to a wrong initial inference.**
   The first `read` of `mutation_sentinel_report.json` showed the huge `workspace_status_after_filtered_outside_output` list and truncated before the later `workspace_status_before_filtered_outside_output` key. I initially inferred the before-list was absent. A later key search showed it existed around line 1530, changing the correct classification from inconclusive/pre-existing-dirty toward `HOLD_CONCURRENT_WORKSPACE_NOISE`.

2. **Provider success was not promotion evidence.**
   Completing all 440 cases with clean provider path only proved the provider/call boundary. It did not override the mutation sentinel failure.

3. **Dirty workspace and concurrent memory edits contaminate replay evidence.**
   The actual delta was memory-related and outside replay output. Even if replay code did not cause it, a failed sentinel means the run cannot be comparator-ready or promotion-eligible.

4. **Failed replay evidence preservation can be already clean.**
   The approved terminal evidence files had no Git-visible changes, so there was nothing to selectively commit for that fileset. Do not invent a preservation commit when scoped status is empty.

## Durable rules

- For mutation-sentinel investigations, parse the full JSON or search exact keys before concluding fields are missing. Do not rely on a truncated `read` excerpt.
- Always compare `workspace_status_before_filtered_outside_output` and `workspace_status_after_filtered_outside_output` by path/status before classifying source.
- Treat `FAIL_MUTATION_SENTINEL` as promotion-blocking even when provider boundary, case count, and rate-limit gates pass.
- A clean rerun requires either a clean workspace or an explicit approved baseline snapshot, plus fresh replay approval. It must still not imply comparator readiness or promotion by itself.
- Keep no-comparator / no-promotion / no-M6-proposal boundaries explicit in every closeout after an unsafe replay.
- Late-approved commands must not be rerun; use their result once and reconcile it against current evidence.

## Safe next shape

Before any future Context+ fresh replay, use a deterministic preflight that records:

1. exact approved output directory;
2. clean or approved baseline `git status --short` snapshot;
3. before/after filtered status snapshots with hashes;
4. exact diff of before vs after;
5. explicit classification table for added, removed, and changed status entries;
6. fail-closed promotion/comparator gate if any protected/adjoining path changes outside the approved replay output.
