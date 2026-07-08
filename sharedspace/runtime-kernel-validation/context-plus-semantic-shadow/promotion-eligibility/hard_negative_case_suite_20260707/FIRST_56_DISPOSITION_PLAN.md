# First-56 Disposition Plan

Classification: `PASS_FIRST_56_DISPOSITION_PLAN_READY`

## Scope and Non-Actions

This is a decision plan only for resolving the legacy first-56 provider-boundary blocker so comparator readiness can be evaluated safely later.

- Cases affected: `hn-20260707-0001` → `hn-20260707-0056`
- Prior first-56 reconciliation plan: `PASS_PUSHED`
- Prior first-56 reconciliation commit: `d5351c668884cd750baeeabde7f2ad10ab7a3ec4`
- Legacy first-56 journal rows: `56`
- Legacy raw stdout/stderr availability: `0/56`
- Legacy provider metadata availability: `55/56`
- Legacy provider missing/null case: `hn-20260707-0056`
- Legacy local-only normalization possible: `false`
- Current comparator readiness: `NOT_READY_WITHOUT_SEPARATE_LIVE_REPLAY_OR_DISPOSITION_APPROVAL`
- Existing held cases outside this fragment: `hn-20260707-0145`, `hn-20260707-0153`

No replay, normalization, comparator execution, Gateway/model/provider calls, promotion, M6 proposal, post-0240 execution, route/config/Gateway mutation, memory promotion, provider/model change, production apply, cache enablement, commit, or push occurred while creating this plan.

## Recommendation

Recommended option: **Option A — narrow repaired-schema replay**, but only after a separate explicit replay approval and preservation preflight.

Rationale:

1. The project’s hard-negative evidence target is a 240-case production evidence set. Option A is the only option that can restore repaired-schema provider-boundary evidence for `hn-20260707-0001` → `hn-20260707-0056` while preserving full case coverage.
2. The existing legacy first-56 fragment is valid as duplicate-safe historical authority, but it is not comparator-authoritative because it lacks raw stdout/stderr and has incomplete provider metadata.
3. Option B avoids new provider calls but leaves comparator readiness `NOT_READY` unless a separate comparator-input policy explicitly accepts excluding the first 56 cases. That exclusion would materially change the evaluation basis and should not be treated as promotion-grade without a separate policy decision.

## Option A — Narrow Repaired-Schema Replay

### Decision

Replay only:

- `hn-20260707-0001` → `hn-20260707-0056`

Use:

- repaired provider-boundary schema
- repaired raw stdout/stderr capture
- source-aware rate/cooldown parser
- duplicate-call prevention ledger
- mutation sentinel before/after
- strict no comparator / no promotion / no M6 during replay

### Expected provider-call count

- Expected Gateway/model/provider calls if later approved: `56`

### Duplicate-safety treatment

- The legacy first-56 journal remains historical duplicate-safe authority proving prior attempts and preventing accidental silent double-counting.
- The replay output must use a new output directory and new run ID.
- The replay must explicitly supersede the legacy first-56 fragment for comparator input if and only if all 56 replay cases pass repaired-schema provider-boundary checks.
- The legacy first-56 fragment must be marked `SUPERSEDED_NON_COMPARATOR_AUTHORITY` or equivalent in any future aggregate readiness artifact.
- Comparator input must include either the repaired replay first-56 evidence or no first-56 evidence; it must not mix legacy first-56 rows with replay rows.
- Duplicate case IDs across comparator input must remain `0`.

### Comparator-input authority rules

For Option A to become comparator-ready later:

1. Replay evidence must cover exactly `hn-20260707-0001` → `hn-20260707-0056`.
2. Replay evidence must have exactly 56 terminal case rows.
3. Every replay case must preserve raw stdout/stderr, hashes, parse result, attempt lifecycle evidence, and provider metadata.
4. Provider boundary must classify all 56 cases under the repaired schema.
5. Provider mismatches must be `0`.
6. Rate/cooldown result must be clean under the source-aware parser.
7. Mutation sentinel must show outside-output unchanged, or otherwise hold.
8. Legacy first-56 evidence must be excluded/superseded from comparator input.
9. Aggregate readiness must be re-run after replay preservation.
10. Comparator remains blocked until the new aggregate readiness review returns ready and comparator execution is separately approved.

### Required preflight for any future replay

A future replay approval must name and verify:

- exact approved case range: `hn-20260707-0001` → `hn-20260707-0056`
- expected case count: `56`
- approved manifest SHA256: `4f5aaf3a24e68542f05445fe5f6aeab92795883c988fccdcc0490255bee9ebda`
- expected provider: `token-broker-vmesh`
- requested model: `token-broker-vmesh/auto`
- repaired harness commit/schema containing raw capture and source-aware rate/cooldown parser
- new output directory, empty before start
- duplicate-prevention report referencing the legacy first-56 journal SHA `8ebcceaf8d651929158eb430587963f1407ea5929b7401469bb6226e3d7e0446`
- explicit statement that legacy first-56 rows are superseded/excluded from comparator input if replay succeeds
- mutation sentinel preflight clean or explicitly approved baseline
- abort on provider mismatch, command failure, timeout, missing provider metadata, raw capture failure, rate/cooldown, mutation sentinel failure, or any case outside `0001` → `0056`

### Required preservation after future replay

After any approved replay:

1. Preserve replay evidence directory only, with selective staging.
2. Preserve a replay closeout artifact naming all 56 cases and boundary classifications.
3. Preserve duplicate-prevention and supersession/exclusion artifact for the legacy first-56 fragment.
4. Re-run aggregate production-evidence continuity / comparator-readiness review read-only.
5. Do not run comparator until the aggregate readiness artifact is preserved and comparator execution is separately approved.

### Replay risk

- Uses 56 new provider calls, which may encounter transport failures, rate/cooldown, timeout, or model/provider drift.
- It creates duplicate historical attempts, so strict supersession/exclusion rules are mandatory to prevent duplicate counting.
- Any replay failure may leave the system in another HOLD state requiring diagnosis.

### Comparator readiness after Option A

- Before replay: `NOT_READY`
- After approved replay succeeds and is preserved: `POTENTIALLY_READY_AFTER_AGGREGATE_READINESS_REVIEW`
- Comparator still: `BLOCKED_NOT_RUN` until separately approved.

## Option B — Formal Disqualification/Hold

### Decision

Do not replay the first-56 fragment.

Mark the legacy first-56 fragment as non-comparator-authoritative because preserved evidence is incomplete:

- raw stdout/stderr: `0/56`
- provider metadata: `55/56`
- provider missing/null: `hn-20260707-0056`
- local-only normalization possible: `false`

### Duplicate-safety treatment

- The legacy first-56 journal remains duplicate-safe historical authority only.
- It must not be counted as repaired-schema comparator input.
- It must remain available to prevent accidental rerun/duplicate counting unless a future explicit replay approval supersedes it.

### Comparator-input authority rules

Option B can only proceed toward comparator if a separate comparator-input policy explicitly authorizes excluding `hn-20260707-0001` → `hn-20260707-0056` from comparator input.

Without that policy:

- comparator input is incomplete
- comparator readiness remains `NOT_READY`
- promotion remains blocked
- M6 proposal remains blocked

### Required preservation after future disqualification

If Option B is later approved:

1. Preserve a formal first-56 disqualification/hold artifact.
2. Update aggregate readiness read-only to show first-56 excluded from comparator authority.
3. If exclusion is not policy-approved, aggregate readiness must remain `NOT_READY`.
4. If exclusion is policy-approved, comparator input must clearly report reduced/altered case basis and must not be treated as equivalent to full 240-case evidence without separate promotion policy approval.

### Disqualification risk

- Avoids new provider calls.
- Preserves strict evidence honesty.
- Leaves the 240-case comparator input incomplete unless exclusion is explicitly accepted.
- Weakens comparability and likely keeps promotion/M6 blocked.

### Comparator readiness after Option B

- Without explicit exclusion policy: `NOT_READY`
- With explicit exclusion policy: `POLICY_DEPENDENT_NOT_FULL_240_CASE_BASIS`
- Comparator still: `BLOCKED_NOT_RUN` until separately approved.

## Comparative Summary

| Field | Option A — narrow repaired-schema replay | Option B — formal disqualification/hold |
|---|---|---|
| Provider calls if later approved | `56` | `0` |
| Full 240-case basis possible | `yes`, if replay succeeds | `no`, unless exclusion policy accepts reduced basis |
| Duplicate counting risk | manageable only with supersession/exclusion | low |
| Evidence completeness | can become repaired-schema complete | remains incomplete for first 56 |
| Comparator readiness after option | potentially ready after replay preservation + aggregate readiness rerun | not ready unless exclusion policy changes comparator input authority |
| Promotion/M6 | blocked pending comparator result and approval | blocked |

## Final Decision Rule

Use Option A if the goal is to preserve a full 240-case comparator-authoritative production evidence set.

Use Option B only if the owner explicitly decides not to spend 56 provider calls and accepts that comparator readiness remains blocked or becomes policy-dependent on excluding the first 56 cases.

## Closeout

- Closeout classification: `PASS_FIRST_56_DISPOSITION_PLAN_READY`
- Recommended option: `Option A — narrow repaired-schema replay`, requiring separate explicit future approval.
- Exact cases affected: `hn-20260707-0001` → `hn-20260707-0056`
- Expected provider-call count if replay is later approved: `56`
- Legacy duplicate-safety treatment: historical duplicate-safe authority; supersede/exclude from comparator input if replay succeeds.
- Option A comparator readiness: `POTENTIALLY_READY_AFTER_REPLAY_PRESERVATION_AND_AGGREGATE_READINESS_RERUN`
- Option B comparator readiness: `NOT_READY_UNLESS_EXCLUSION_POLICY_EXPLICITLY_APPROVED`
- Comparator was not run.
- No replay occurred.
- No normalization occurred.
- No provider calls occurred.
- Promotion and M6 remain blocked.
