# M6 Context+ Production Apply Runbook

Date: 2026-07-09 AEST

## Classification

`HOLD_CONTROL_SURFACE_AMBIGUOUS`

Secondary classifications:

- `HOLD_PRODUCTION_TARGET_NOT_FOUND`
- `HOLD_ROLLBACK_COMMAND_NOT_FOUND`
- `HOLD_SMOKE_COMMAND_NOT_FOUND`

## Boundary

This artifact is discovery/runbook-only. It does not approve or execute production apply.

Actions not performed:

- production apply: `NOT_RUN`
- route/config/Gateway mutation: `NOT_RUN`
- memory promotion: `NOT_RUN`
- provider/model change: `NOT_RUN`
- cache enablement: `NOT_RUN`
- rollback execution: `NOT_RUN`
- live smoke: `NOT_RUN`
- replay/provider calls: `NOT_RUN`

## Inputs / Evidence Reviewed

### Preserved M6 and preflight state

- M6 proposal: `M6_CONTEXT_PLUS_PRODUCTION_PROPOSAL.md`
  - classification: `PROPOSAL_ONLY_NOT_APPLIED`
  - production apply: `NOT_APPROVED`
  - comparator: `PASS_FALSE_POSITIVE_BASELINE_IMPROVED`
  - production false positives: `22/235`
  - Context+ shadow false positives: `0/235`
  - provider/Gateway/model calls during comparator: `0`
- M6 preflight: `M6_PRODUCTION_APPLY_PREFLIGHT.md`
  - classification: `HOLD_M6_PRODUCTION_APPLY_SCOPE_UNCLEAR`
  - secondary: `HOLD_ROLLBACK_NOT_READY`, `HOLD_LIVE_SMOKE_NOT_READY`
  - preserved commit: `551c019bdee3704e3da2a8d4eb9eb9d4c10b388e`
  - preserved branch: `evidence/context-plus-m6-production-apply-preflight-20260709`
  - marker: `M6_PRODUCTION_APPLY_PREFLIGHT_PUSHED`

### Earlier Context+ preselector promotion-readiness packet

Late-approved read-only search found the older Context+ semantic preselector M8/M9 chain:

- Source generator: `scripts/build_context_plus_preselector_m8_packet_20260623.py`
- M8 packet: `sharedspace/runtime-kernel-validation/vnext-semantic-gate/context_plus_preselector_m8_promotion_readiness_packet_20260623/M8_PROMOTION_READINESS_PACKET.json`
- M8 rollback plan: `sharedspace/runtime-kernel-validation/vnext-semantic-gate/context_plus_preselector_m8_promotion_readiness_packet_20260623/rollback_plan.md`
- M9 advisory runner: `scripts/context_plus_preselector_m9_advisory_canary_20260623.py`
- M9 status: `sharedspace/runtime-kernel-validation/vnext-semantic-gate/context_plus_preselector_m9_advisory_canary_20260623/status.json`

Important discovered facts:

- M8 status: `CONTEXT_PLUS_PRESELECTOR_M8_PROMOTION_READINESS_PACKET_PASS`
- M8 apply performed: `false`
- M8 subject: `CONTEXT_PLUS_SEMANTIC_PRESELECTOR`
- M8 owner approval phrase for M9: `STICKBOT APPROVE CONTEXT_PLUS_SEMANTIC_PRESELECTOR M9 ADVISORY CANARY APPLY`
- M9 status: `CONTEXT_PLUS_PRESELECTOR_M9_ADVISORY_CANARY_PASS`
- M9 apply scope: `run_local_sidecar_advisory_canary_only`
- M9 `live_route_influence`: `false`
- M9 `m10_or_production_started`: `false`
- M9 `gateway_config_route_fallback_memory_runtime_model_mutated`: `false`
- M9 direct provider bypass: `0`
- M9 replay failures: `0`
- M9 blocking/unclassified disagreements: `0`

### OpenClaw source search follow-up

A late-approved read-only source search for context/hydration/preselector names under the installed OpenClaw package returned only:

- `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/snapshot-hydration-BheMT0zb.js`
- `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/plugin-sdk/src/agents/skills/snapshot-hydration.d.ts`

Readback showed these define only generic skill snapshot helpers:

- `hydrateResolvedSkills(snapshot, rebuild)`
- `hydrateResolvedSkillsAsync(snapshot, rebuild)`

They do not expose Context+ semantic preselector promotion, route authority, rollback, smoke, or production control-surface operations.

### Gateway config schema inspection

Read-only schema lookup results:

| Path | Result |
| --- | --- |
| `contextPlus` | schema path not found |
| `semanticShadow` | schema path not found |
| `preselector` | schema path not found |
| `routing` | schema path not found |
| `runtime` | schema path not found |
| `agents` | exists; model/tool/agent runtime configuration root, not a Context+ semantic-shadow production promotion surface |
| `models` | exists; model catalog/provider definitions, not a Context+ production promotion surface |
| `plugins` | exists; plugin loader/entries surface |
| `gateway` | exists; Gateway bind/auth/control surfaces, not Context+ promotion surface |
| `memory` | exists; memory backend configuration, not Context+ promotion surface |
| `hooks.internal.entries.context-bridge-hot-hydration` | exists with schema keys `enabled`, `env`, and wildcard additional keys |

## Exact Production Target

Exact production target for M6 production apply: `NOT_FOUND`

A related non-production/advisory target was found:

```text
context_plus_semantic_preselector.m9_advisory_canary.enabled
```

But this is **not** an M6 production promotion target. It is explicitly described as:

- `mode`: `advisory_canary_shadow_contract_only`
- `scope`: `run_local_artifact_only` / `run_local_sidecar_advisory_canary_only`
- `default_enabled`: `false`
- `live_route_influence`: `false`
- `m10_or_production_started`: `false`
- no Gateway/config/default-route mutation

Therefore, the discovered M8/M9 surface resolves an earlier advisory canary, not a current executable production promotion.

## Exact Config Key / Path / Route / Control-Surface Operation

### Found: advisory/run-local only

```text
context_plus_semantic_preselector.m9_advisory_canary.enabled = true
```

Evidence:

- M8 feature flag proposal: `feature_flag_proposal.flag_name`
- M9 `feature_flags.json`: `context_plus_semantic_preselector.m9_advisory_canary.enabled: true`
- M9 status: `apply_scope: run_local_sidecar_advisory_canary_only`

### Not found: production route/control surface

No reviewed artifact or schema identifies a safe production operation such as:

- a Gateway config key that makes Context+ the production preselector,
- a token-solver-v4 route key that makes Context+ authoritative,
- an `intent-preselector-v5` live-route switch,
- a `hooks.internal` env key for Context+ production cutover,
- a plugin/control-surface API endpoint for Context+ production promotion,
- a CLI/admin command for Context+ production promotion.

Candidate production-adjacent surfaces remain ambiguous:

1. `hooks.internal.entries.context-bridge-hot-hydration.enabled`
   - currently enabled;
   - no evidence this promotes Context+ semantic preselector;
   - not accepted as target.
2. `hooks.internal.entries.context-bridge-hot-hydration.env.*`
   - wildcard env surface exists;
   - no exact key found;
   - not accepted as target.
3. `services/intent-preselector-v5/*`
   - source/config files are in the M8 protected-state list;
   - no production loader/route mutation operation found;
   - not accepted as target.
4. `services/token-solver-v4/src/*`
   - source files are in the M8 protected-state list;
   - no production cutover patch/flag found;
   - not accepted as target.

## Exact Pre-Apply Snapshot Command

### For production M6 apply

`NOT_PREPARED_TARGET_NOT_FOUND`

A production snapshot command cannot be exact because no production target is known.

### Existing advisory/M9 snapshot pattern found

The M9 runner has a snapshot routine over these protected paths:

- `/home/stickai/.openclaw/openclaw.json`
- `/home/stickai/.openclaw/workspace/state/runtime-kernel/candidate-lanes.yaml`
- `/home/stickai/.openclaw/workspace/state/runtime-kernel/memory-primary-route.json`
- `/home/stickai/.openclaw/workspace/services/token-solver-v4/src/config.js`
- `/home/stickai/.openclaw/workspace/services/token-solver-v4/src/server.js`
- `/home/stickai/.openclaw/workspace/services/token-solver-v4/src/forward.js`
- `/home/stickai/.openclaw/workspace/services/token-solver-v4/src/v5Contract.js`
- `/home/stickai/.openclaw/workspace/services/intent-preselector-v5/config/lanes.json`
- `/home/stickai/.openclaw/workspace/services/intent-preselector-v5/config/route_policy.json`
- `/home/stickai/.openclaw/workspace/services/intent-preselector-v5/src/index.js`
- `/home/stickai/.openclaw/workspace/services/intent-preselector-v5/src/server.js`
- `/home/stickai/.openclaw/workspace/services/intent-preselector-v5/src/decision_engine.js`
- `/home/stickai/.openclaw/workspace/services/intent-preselector-v5/src/local_advisor.js`
- `/home/stickai/.openclaw/workspace/scripts/context_plus_preselector/scorer.py`
- `/home/stickai/.openclaw/workspace/scripts/context_plus_preselector/risk_gate.py`
- `/home/stickai/.openclaw/workspace/scripts/context_plus_preselector/route_contracts.py`
- `/home/stickai/.openclaw/workspace/scripts/context_plus_preselector/route_quality_evaluator.py`
- `/home/stickai/.openclaw/workspace/scripts/context_plus_preselector/side_by_side_harness.py`

M9 snapshot implementation:

```text
scripts/context_plus_preselector_m9_advisory_canary_20260623.py::snapshot_for_rollback()
```

But this is an advisory/run-local snapshot pattern, not an exact production snapshot command.

## Exact Production Apply Command / Native Approval Card Command

`NOT_PREPARED_CONTROL_SURFACE_AMBIGUOUS`

No production apply command/card is safe to prepare now.

The only exact apply-like command found is for the already-completed M9 advisory canary:

```bash
python3 scripts/context_plus_preselector_m9_advisory_canary_20260623.py
```

That command is **not** production apply. It is run-local sidecar advisory canary only and may perform Gateway/provider trace capture as part of its own M9 evidence. It must not be re-run here and must not be represented as M6 production promotion.

## Exact Rollback Command

### Production rollback

`NOT_FOUND`

No production rollback command exists because no production apply target exists.

### Existing advisory/M9 rollback plan found

If an M9 advisory apply had an existing snapshot, M8 defined these rollback commands:

```bash
python3 scripts/context_plus_preselector_sentinel_snapshot.py <artifact_dir>/post_rollback_sentinel.json
cp -a <snapshot_dir>/openclaw.json /home/stickai/.openclaw/openclaw.json
cp -a <snapshot_dir>/state/runtime-kernel/candidate-lanes.yaml /home/stickai/.openclaw/workspace/state/runtime-kernel/candidate-lanes.yaml  # only if it existed at snapshot time
cp -a <snapshot_dir>/state/runtime-kernel/memory-primary-route.json /home/stickai/.openclaw/workspace/state/runtime-kernel/memory-primary-route.json  # only if it existed at snapshot time
cp -a <snapshot_dir>/services/token-solver-v4/src/config.js /home/stickai/.openclaw/workspace/services/token-solver-v4/src/config.js
cp -a <snapshot_dir>/services/token-solver-v4/src/server.js /home/stickai/.openclaw/workspace/services/token-solver-v4/src/server.js
cp -a <snapshot_dir>/services/token-solver-v4/src/forward.js /home/stickai/.openclaw/workspace/services/token-solver-v4/src/forward.js
cp -a <snapshot_dir>/services/token-solver-v4/src/v5Contract.js /home/stickai/.openclaw/workspace/services/token-solver-v4/src/v5Contract.js
python3 scripts/context_plus_preselector_compare_sentinels.py <artifact_dir>/pre_apply_sentinel.json <artifact_dir>/post_rollback_sentinel.json <artifact_dir>/rollback_compare_report.json
```

Those commands are not exact for M6 production because `<artifact_dir>` and `<snapshot_dir>` are placeholders and the command set is tied to M9 advisory scope, not a found production cutover.

## Exact Live Smoke Command

### Production live smoke

`NOT_FOUND`

No exact live smoke command was found for M6 Context+ production promotion.

### Existing advisory/M9 smoke/evidence command

The M9 advisory runner included route coverage, replay, provider-path, disagreement, and mutation-sentinel checks inside:

```bash
python3 scripts/context_plus_preselector_m9_advisory_canary_20260623.py
```

That is not a production live smoke and must not be used as proof that Context+ is production-active.

## Exact Post-Apply Health Checks

For production M6 apply: `NOT_PREPARED_TARGET_NOT_FOUND`

Known M9/advisory checks that a future production runbook may adapt:

- direct provider bypass: `0`
- replay failures: `0`
- blocking disagreements: `0`
- unclassified disagreements: `0`
- gateway/provider errors: `0`
- mutation sentinel: PASS
- cache enabled: `false`
- artifact memory promoted: `false`
- default model changed: `false`
- scope expanded: `false`
- watcher checkpoint silent skip: `false`
- route coverage present across Context+ route classes

Additional production-only checks still needed:

- production target readback equals expected value,
- Context+ is active in production only for approved route/preselector surface,
- non-target config diff is empty,
- provider/model/cache/memory side-effect diffs are empty,
- rollback sentinel remains available immediately after apply.

## Exact Rollback Trigger Criteria

A future production apply must rollback immediately if any of these occur:

- Gateway unhealthy after apply.
- Target readback differs from expected state.
- Any non-target Gateway/config/routes/cache/memory/provider/model diff appears.
- Smoke command fails, times out, or produces ambiguous output.
- Provider/model calls occur when smoke promised zero provider/model calls.
- Cache enablement or memory promotion occurs unexpectedly.
- Context+ is not active where expected, or active outside intended scope.
- Hard-negative guard regressions appear: false-positive regression, ambiguity/continuation regression, phrase-hardcoded regression, routing regression.
- Rollback sentinel cannot be verified immediately after apply.
- Any M9-style abort gate trips: direct provider bypass, unauthorized mutation, scope expansion, blocking/unclassified disagreement, replay failure, Gateway instability, watcher/checkpoint silent skip.

These criteria are exact enough as policy, but still lack an executable production rollback command.

## Exact Expected Post-Apply State

`NOT_DEFINED_PRODUCTION_TARGET_NOT_FOUND`

The desired high-level state remains:

- Context+ semantic preselector/shadow evidence is promoted to the exact approved production decision surface.
- Comparator-improved behavior is active in production.
- Production false-positive baseline is improved without provider/model/cache/memory side effects.
- Rollback remains available until smoke and side-effect checks pass.

But no exact production state can be asserted because no production target is found.

## Exact Files / Config / Routes Expected To Change

For production M6 apply: `NONE_APPROVED`

Expected files/config/routes to change now: `none`

Production approval that changes files/config/routes before this field is concrete should be rejected as unsafe.

M8/M9 advisory protected-state files are known, but the M9 status says no Gateway/config/default-route mutation and no live route influence occurred.

## Exact Side-Effect Checks

Future side-effect checks must compare pre/post snapshots for:

- `/home/stickai/.openclaw/openclaw.json`
- `state/runtime-kernel/candidate-lanes.yaml`
- `state/runtime-kernel/memory-primary-route.json`
- `services/token-solver-v4/src/config.js`
- `services/token-solver-v4/src/server.js`
- `services/token-solver-v4/src/forward.js`
- `services/token-solver-v4/src/v5Contract.js`
- `services/intent-preselector-v5/config/lanes.json`
- `services/intent-preselector-v5/config/route_policy.json`
- `services/intent-preselector-v5/src/index.js`
- `services/intent-preselector-v5/src/server.js`
- `services/intent-preselector-v5/src/decision_engine.js`
- `services/intent-preselector-v5/src/local_advisor.js`
- `scripts/context_plus_preselector/scorer.py`
- `scripts/context_plus_preselector/risk_gate.py`
- `scripts/context_plus_preselector/route_contracts.py`
- `scripts/context_plus_preselector/route_quality_evaluator.py`
- `scripts/context_plus_preselector/side_by_side_harness.py`

Side-effect assertions must include:

- provider/model config unchanged unless exact production target explicitly includes it,
- cache remains disabled/unmodified,
- artifact memory not promoted,
- default model unchanged,
- memory route unchanged unless exact production target explicitly includes it,
- no broad live traffic,
- no live route authority outside approved scope.

## Native Approval Requirement

Native approval required for future production apply: `YES`

Native approval card prepared now: `NO`

Reason: a Context+ advisory canary control surface exists, but no production promotion control surface exists.

## Rollback Executable Before Apply?

For production M6 apply: `NO`

Reason: no exact production target/snapshot/apply path exists.

For the older M9 advisory scope only: `PARTIAL_PATTERN_EXISTS`

Reason: M8/M9 define rollback snapshot and rollback commands, but they are scoped to M9 advisory canary and contain placeholders. They are not a production rollback command.

## Smoke Executable Before Apply?

For production M6 apply: `NO`

Reason: no exact Context+ production smoke command or expected production route assertion exists.

For the older M9 advisory scope only: `ALREADY_COMPLETED_NOT_PRODUCTION`

Reason: M9 advisory canary already passed, but its report explicitly states it does not make Context+ production-active.

## Can Production Apply Now Be Approved?

`NO`

Approval would be unsafe because the only exact Context+ control surface found is advisory/run-local and explicitly non-production.

## Required Follow-Up To Reach PASS

To reach `PASS_M6_PRODUCTION_APPLY_RUNBOOK_READY`, a future prep-only artifact must bridge from the proven M8/M9 advisory surface to an explicit production surface by naming:

1. exact production package/plugin/hook/route/control-surface ID,
2. exact production flag/key and desired value,
3. exact source patch or config patch that makes Context+ production-active,
4. exact snapshot command with concrete artifact directory, no placeholders,
5. exact rollback command with concrete snapshot directory and target paths,
6. exact bounded production smoke command,
7. exact production route/readback assertion,
8. exact side-effect checks for provider/model/cache/memory/default route,
9. preservation marker/branch for apply/smoke/rollback evidence,
10. explicit owner/operator approval after this runbook is preserved.

If no existing production control surface exists, the next safe artifact is a prep-only `M10` or equivalent Context+ production package proposal, not production apply.

## Closeout

- Runbook result: `HOLD_CONTROL_SURFACE_AMBIGUOUS`
- Production apply: `NOT_RUN`
- Production promoted: `NO`
- Native production apply card: `NOT_PREPARED`
- Production rollback command: `NOT_FOUND`
- Production smoke command: `NOT_FOUND`
- Advisory control surface found: `context_plus_semantic_preselector.m9_advisory_canary.enabled`
- Advisory status: `CONTEXT_PLUS_PRESELECTOR_M9_ADVISORY_CANARY_PASS`
- Production apply can now be approved: `NO`
