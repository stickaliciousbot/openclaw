# Context+ Partial Replay — Aborted Superseded Approval

Generated: 2026-07-07 AEST
Classification: `ABORTED_SUPERSEDED_APPROVAL_PARTIAL_REPLAY`
Closeout classification: `HOLD_PARTIAL_REPLAY_EVIDENCE_PRESERVED`

## Executive decision

This partial replay evidence is preserved as an aborted/superseded-approval artifact.

It is **not valid promotion evidence** and must be excluded from promotion eligibility, production-readiness claims, same-suite final comparison claims, and M6 proposal preparation.

## Reason

- Replay began under stale/superseded approval.
- The executable live-replay implementation changed after the previous approval.
- The replay process was intentionally terminated once the stale approval issue and active process were discovered.
- Only 23/440 cases completed.
- Result is not valid promotion evidence.
- No further provider calls are running.

## Process / command evidence

- Replay process/session id: `brisk-ember`
- Native approval / command id: `f194897a-a752-40b6-988b-bb1814762527`
- Short command id: `f194897a`
- Termination evidence: `SIGTERM`; intentionally killed by Stickbot after discovering the replay process was still running under superseded approval.
- Latest process-list evidence after kill: `brisk-ember failed 5m20s :: python3 scripts/context_plus_s...me_suite_comparator.py`; no active replay/provider process remained in `process list`.

## Partial evidence path

Partial replay journal:

`sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/production_replay_approved_20260707T1621AEST/production_replay_journal.jsonl`

Partial run config:

`sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/production_replay_approved_20260707T1621AEST/run_config.json`

## Partial case count

- Completed/recorded cases: 23
- Expected full replay cases: 440
- Completion ratio: 23/440
- First recorded case id: `m7-live-0001`
- Last recorded case id: `m7-live-0023`

## Provider/model call count

Provider/model call count is available from the journal record count: `23`.

Observed from first and last records:

- Transport: `gateway`
- Requested model: `token-broker-vmesh/auto`
- Provider: `token-broker-vmesh`
- Output model field: `auto`
- `provider_path_verified_gateway_token_broker`: `true`
- `fallback_attempt_detected`: `false`
- `returncode`: `0`
- `output_present`: `true`

This artifact does not claim every line was independently revalidated after termination; it records the partial journal as aborted evidence and excludes it from promotion eligibility.

## Boundary / eligibility disposition

- Promotion evidence status: `EXCLUDED`
- Same-suite final comparison evidence status: `EXCLUDED`
- M6 proposal input status: `EXCLUDED`
- Replay final status: `ABORTED_SUPERSEDED_APPROVAL_PARTIAL_REPLAY`
- Replay closeout status: `HOLD_PARTIAL_REPLAY_EVIDENCE_PRESERVED`

A future valid replay must use a fresh approval against the preserved executable replay implementation and must write to a separate output path so this partial replay remains quarantined from valid replay evidence.

## No-promotion / no-mutation statement

No promotion occurred. No route/config/Gateway mutation was intentionally performed. No memory promotion occurred. No provider/model change occurred. No production apply occurred. No cache enablement occurred. No M6 proposal mutation occurred.

The replay process was stopped specifically to prevent further provider calls after the approval boundary changed.
