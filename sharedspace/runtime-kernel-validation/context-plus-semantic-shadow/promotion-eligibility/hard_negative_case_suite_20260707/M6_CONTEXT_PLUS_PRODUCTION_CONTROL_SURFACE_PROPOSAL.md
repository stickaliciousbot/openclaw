# M6 Context+ Production Control-Surface Proposal

Date: 2026-07-09 AEST

## Classification

`PASS_CONTROL_SURFACE_PROPOSAL_READY`

## Boundary

This is a prep-only implementation proposal. It is not production apply.

Actions not performed:

- production apply: `NOT_RUN`
- native production apply card: `NOT_PREPARED`
- route/config/Gateway mutation: `NOT_RUN`
- memory promotion: `NOT_RUN`
- provider/model change: `NOT_RUN`
- cache enablement: `NOT_RUN`
- live-route influence: `NOT_RUN`
- rollback execution: `NOT_RUN`
- provider/Gateway/model calls: `NOT_RUN`
- comparator rerun: `NOT_RUN`

## Starting State

Preserved evidence chain:

- M6 comparator: `PASS_FALSE_POSITIVE_BASELINE_IMPROVED`
- M6 proposal: `PASS_PUSHED`
- M6 production apply runbook: preserved, but closes `HOLD_CONTROL_SURFACE_AMBIGUOUS`
- M8 packet discovery: preserved, but closes `HOLD_M8_PACKET_READINESS_ONLY_NO_APPLY_TARGET`
- Exact existing production target: `NOT_FOUND`
- Exact production rollback command: `NOT_FOUND`
- Exact production smoke command: `NOT_FOUND`
- Production apply: `NOT_RUN`
- Production promoted: `NO`

Preserved HOLD artifacts:

- `M6_PRODUCTION_APPLY_RUNBOOK.md`
  - commit: `c2e2decfeaa4fad82e81a54362779d461d1ebf77`
  - branch: `evidence/context-plus-m6-production-apply-runbook-hold-20260709`
- `M6_PRODUCTION_TARGET_DISCOVERY_FROM_M8_PACKET.md`
  - commit: `1ce70de4b94c4916a8e0cdbfe37eeb2ed672fc20`
  - branch: `evidence/context-plus-m6-production-target-discovery-m8-hold-20260709`

## Source Findings Used For This Proposal

### Existing runtime decision point

Token Solver v4 already invokes the Context+ / intent-preselector-v5 decision path on every scored request:

- File: `services/token-solver-v4/src/server.js`
- Function: `scoreForRequest(...)`
- Decision call:
  - `buildV5ShadowContract({ prompt, selectedModel, rawBody, previousState, routeScore, path, sessionKey, config })`
- Enforcement call:
  - `applyV5EnforcedRouteContract(baseScore, intentPreselectorV5)`

The enforcement function already has the live-route influence point:

```text
applyV5EnforcedRouteContract(score, intentPreselectorV5)
```

Behavior:

- If `intentPreselectorV5.enforced` is not true, return the deterministic/base score unchanged.
- If `intentPreselectorV5.enforced` is true and the Context+ selected lane differs, replace `score.recommendedLane` with the Context+ selected lane and mark:
  - `routeContractApplied: true`
  - `routeContractSource: intent-preselector-v5`

### Existing config/state hook

Token Solver v4 config already declares an intent-preselector-v5 enforcement state hook:

- File: `services/token-solver-v4/src/config.js`
- State path default:
  - `/home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json`
- Env override:
  - `TOKEN_SOLVER_V4_INTENT_PRESELECTOR_V5_STATE_PATH`
- Mode/env flags:
  - `TOKEN_SOLVER_V4_INTENT_PRESELECTOR_V5_MODE`
  - `TOKEN_SOLVER_V4_INTENT_PRESELECTOR_V5_ENFORCED`
  - `TOKEN_SOLVER_V4_INTENT_PRESELECTOR_V5_SHADOW`
  - `TOKEN_SOLVER_V4_INTENT_PRESELECTOR_V5_TRACE`

Current state-file read result:

- `state/intent-preselector-v5/enforcement.json`: `MISSING`

Current default remains safe because absent state falls back to shadow-only / not enforced.

### Existing route dry-run smoke point

Token Solver v4 exposes a read-only route dry-run endpoint:

- File: `services/token-solver-v4/src/server.js`
- Endpoint: `POST /route/dry-run`
- Handler: `handleRouteDryRun(req, res)`
- Output includes:
  - `score`
  - `target_v3_model`
  - `intent_preselector_v5`

This is the right non-provider smoke/readback point for future production control-surface verification, because it exercises the same `buildV5ShadowContract` and `applyV5EnforcedRouteContract` route path without forwarding to upstream providers.

## Why Existing M9 Advisory Key Is Insufficient

Existing M8/M9 key:

```text
context_plus_semantic_preselector.m9_advisory_canary.enabled
```

Rejected as production target because M8/M9 define it as:

- `advisory_canary_shadow_contract_only`,
- run-local artifact/advisory canary only,
- fixture/operator allowlist only,
- no broad live traffic,
- no live route influence,
- no Gateway/config/default-route mutation,
- no production apply.

M9 status explicitly says:

- `apply_scope: run_local_sidecar_advisory_canary_only`
- `live_route_influence: false`
- `m10_or_production_started: false`
- `gateway_config_route_fallback_memory_runtime_model_mutated: false`

Therefore the M9 key is useful historical/advisory evidence only; it must remain separate from production enforcement.

## Why M8 Readiness Packet Is Not Sufficient

M8 packet status is:

```text
CONTEXT_PLUS_PRESELECTOR_M8_PROMOTION_READINESS_PACKET_PASS
```

But M8 also states:

- `apply_performed: false`
- `m8_packet_only: true`
- `m9_started: false`
- `live_route_influence: false`
- M8 is not approval
- M9 would require separate exact approval phrase

It predates the current hard-negative M6 comparator result and does not define a current M6 production target, rollback command, or smoke command.

## Exact Intended Production Behavior

Introduce a protected Token Solver v4 / intent-preselector-v5 production control surface that can make Context+ route contracts authoritative for lane selection only when all guard conditions are satisfied.

Intended behavior when disabled/default:

- Context+ remains shadow-only.
- `intent_preselector_v5.mode = shadow_contract_only`.
- `intent_preselector_v5.enforced = false`.
- `score.recommendedLane` remains the deterministic/base v4 score.
- Advisory M9 artifacts remain separate and do not affect production.

Intended behavior when separately approved and enabled:

- Token Solver v4 continues to score normally with deterministic/base score first.
- Context+ builds an `intent_preselector_v5` route contract from the isolated visible user prompt and support context.
- If the production control state validates and authorizes enforcement, `applyV5EnforcedRouteContract(...)` may replace `score.recommendedLane` with the Context+ selected lane.
- Enforcement is fail-closed:
  - no prompt replacement,
  - no provider/model selection outside existing v4 lane map,
  - no memory promotion,
  - no cache enablement,
  - no direct provider bypass,
  - no live route influence outside approved scope.

Initial production behavior should be bounded canary production, not all-traffic promotion:

```text
traffic_scope = owner_operator_live_turns_only
operator_allowlist = ["telegram:8495203551"]
```

Broad/default live traffic requires a later, separate proposal and owner/operator approval after canary soak evidence.

## Exact Runtime Route / Decision Point Affected

Runtime service:

```text
token-solver-v4
```

Runtime files/functions:

```text
services/token-solver-v4/src/server.js::scoreForRequest(...)
services/token-solver-v4/src/server.js::applyV5EnforcedRouteContract(...)
services/token-solver-v4/src/v5Contract.js::buildV5ShadowContract(...)
services/token-solver-v4/src/config.js::loadIntentPreselectorV5State(...)
```

Exact decision point:

```text
score.recommendedLane selection before v3 upstream forwarding
```

No Gateway routing key is proposed as the owner. Gateway should continue to route to `token-solver-v4/auto` / broker-selected v4 as before. The production control surface belongs below Gateway, inside Token Solver v4's route-contract enforcement path.

## Exact Config / Schema Key To Add Or Use

Use existing state path, but formalize it with an explicit schema and validation:

```text
/home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json
```

Proposed schema file to add:

```text
services/intent-preselector-v5/config/enforcement.schema.json
```

Proposed state schema:

```json
{
  "schema": "stickbot.context_plus_semantic_preselector.production_control_surface.v1",
  "subject": "CONTEXT_PLUS_SEMANTIC_PRESELECTOR",
  "enabled": true,
  "mode": "enforced_route_contract",
  "authority": "lane_selection_only",
  "traffic_scope": "owner_operator_live_turns_only",
  "operator_allowlist": ["telegram:8495203551"],
  "kill_switch": false,
  "m6_evidence": {
    "comparator_classification": "PASS_FALSE_POSITIVE_BASELINE_IMPROVED",
    "production_false_positives": "22/235",
    "context_plus_shadow_false_positives": "0/235",
    "proposal_commit": "871522c5204b6062419e48a5a47a4d9cd4cf97a6",
    "runbook_hold_commit": "c2e2decfeaa4fad82e81a54362779d461d1ebf77",
    "m8_discovery_hold_commit": "1ce70de4b94c4916a8e0cdbfe37eeb2ed672fc20"
  },
  "guards": {
    "prompt_preserved_required": true,
    "context_may_replace_prompt": false,
    "remote_llm_for_scoring_allowed": false,
    "direct_provider_bypass_allowed": false,
    "cache_allowed": false,
    "artifact_memory_promotion_allowed": false,
    "default_model_change_allowed": false,
    "provider_model_change_allowed": false,
    "write_action_authority": "unchanged_existing_policy_only"
  },
  "rollback": {
    "safe_disabled_state": {
      "enabled": false,
      "mode": "shadow_contract_only",
      "kill_switch": true
    }
  }
}
```

Required validation rules:

- `schema` must match exactly.
- `subject` must be `CONTEXT_PLUS_SEMANTIC_PRESELECTOR`.
- `enabled` must be boolean.
- `mode` must be one of:
  - `shadow_contract_only`
  - `enforced_route_contract`
- `mode=enforced_route_contract` is valid only if `enabled=true` and `kill_switch=false`.
- `authority` must be `lane_selection_only`.
- `traffic_scope` must initially be `owner_operator_live_turns_only`; `all_live_traffic` must be rejected until a separate approval artifact exists.
- `m6_evidence.comparator_classification` must equal `PASS_FALSE_POSITIVE_BASELINE_IMPROVED`.
- Provider/model/cache/memory mutation flags must all be false.
- If validation fails, runtime must fall back to `shadow_contract_only` and emit a degraded/readback reason.

## Admin / Protected Status

The state file must be admin/protected.

Rules:

- Only native approval or an owner-approved production package may create/update it.
- It must not be writable by ordinary chat/tool flow.
- It must not be changed by heartbeat, cron, replay, comparator, or advisory canary runs.
- Any apply must stage/preserve only the approved state file and relevant implementation/tests.
- Any unexpected staged/config/source diff must abort.

## How Live Route Influence Is Enabled

Implementation requirement:

- Update Token Solver v4 to read and validate the enforcement state at route time or via safe mtime-cached reload.
- Pass the validated enforcement state into `buildV5ShadowContract(...)` / compact decision.
- `intentPreselectorV5.enforced` becomes true only when:
  - state validates,
  - `enabled=true`,
  - `mode=enforced_route_contract`,
  - `kill_switch=false`,
  - traffic scope and operator allowlist match the incoming request headers/session,
  - M6 evidence fields validate.
- `applyV5EnforcedRouteContract(...)` is the only place allowed to change live lane selection.

Live route influence is therefore limited to:

```text
score.recommendedLane replacement inside token-solver-v4 before upstream v3 forwarding
```

It must not change:

- Gateway route config,
- model provider catalog,
- default model/fallback order,
- memory backend/routes,
- cache behavior,
- provider credentials,
- user prompt contents.

## How Observe-Only / Advisory Mode Is Preserved Separately

Observe-only modes remain:

1. `intentPreselectorV5ShadowEnabled=true`, `intentPreselectorV5Enforced=false`
   - production shadow contract metadata only,
   - no route influence.
2. M9 advisory canary key:
   - `context_plus_semantic_preselector.m9_advisory_canary.enabled`
   - run-local/advisory-only,
   - no live route influence.

The new production state file must not reuse the M9 key. It must be named and validated separately as production control state.

## Exact Rollback Mechanism

Rollback target:

```text
/home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json
```

Rollback method:

1. Restore the pre-apply snapshot of the state file if it existed.
2. If no pre-apply state file existed, remove the file or replace it with safe disabled state.
3. Confirm Token Solver v4 readback reports shadow/not enforced.

Safe disabled state:

```json
{
  "schema": "stickbot.context_plus_semantic_preselector.production_control_surface.v1",
  "subject": "CONTEXT_PLUS_SEMANTIC_PRESELECTOR",
  "enabled": false,
  "mode": "shadow_contract_only",
  "authority": "lane_selection_only",
  "traffic_scope": "owner_operator_live_turns_only",
  "operator_allowlist": ["telegram:8495203551"],
  "kill_switch": true
}
```

Future exact rollback command after implementation must be generated with concrete artifact paths, for example:

```bash
python3 scripts/context_plus_preselector_m6_control_surface_apply.py \
  rollback \
  --state-path /home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json \
  --snapshot sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/<apply-run>/pre_apply_snapshot/enforcement.json \
  --out sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/<apply-run>/rollback_report.json
```

This proposal does not create or run that command.

## Exact Smoke Test Command

Future smoke command after implementation and approved apply:

```bash
python3 scripts/context_plus_preselector_m6_control_surface_smoke.py \
  --state-path /home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json \
  --token-solver-v4-url http://127.0.0.1:8800 \
  --expected-mode enforced_route_contract \
  --expected-enforced true \
  --expected-traffic-scope owner_operator_live_turns_only \
  --expected-comparator PASS_FALSE_POSITIVE_BASELINE_IMPROVED \
  --dry-run-endpoint /route/dry-run \
  --out sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/<apply-run>/post_apply_smoke.json
```

Smoke behavior requirements:

- Use `/route/dry-run`, not `/v1/chat/completions` or `/v1/responses`, for zero-provider-call route assertion.
- Assert `intent_preselector_v5.enforced=true` only for allowlisted owner/operator scope.
- Assert non-allowlisted dry-run remains shadow/not enforced or rejected by scope.
- Assert `score.recommendedLane` changes only when Context+ contract authorizes a different safe lane.
- Assert `prompt_preserved=true` and `context_may_replace_prompt=false`.
- Assert provider/model/cache/memory/default model fields did not change.

This proposal does not run smoke.

## Exact Mutation Sentinel

Future mutation sentinel command after implementation:

```bash
python3 scripts/context_plus_preselector_m6_control_surface_sentinel.py \
  --state-path /home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json \
  --watch /home/stickai/.openclaw/openclaw.json \
  --watch /home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json \
  --watch /home/stickai/.openclaw/workspace/services/token-solver-v4/src/config.js \
  --watch /home/stickai/.openclaw/workspace/services/token-solver-v4/src/server.js \
  --watch /home/stickai/.openclaw/workspace/services/token-solver-v4/src/v5Contract.js \
  --watch /home/stickai/.openclaw/workspace/services/intent-preselector-v5/config/enforcement.schema.json \
  --watch /home/stickai/.openclaw/workspace/services/intent-preselector-v5/src/decision_engine.js \
  --watch /home/stickai/.openclaw/workspace/services/intent-preselector-v5/config/route_policy.json \
  --out sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/<apply-run>/mutation_sentinel_report.json
```

Allowed mutation during apply:

- the exact enforcement state file,
- implementation files listed in this proposal if they are part of separately approved implementation,
- test/smoke/sentinel scripts,
- evidence artifacts under the approved apply-run directory.

Forbidden mutation:

- Gateway config route/fallback/default model,
- provider/model catalog/credentials,
- cache enablement,
- memory route/backend/promotion,
- broad live-traffic enablement,
- M9 advisory key reuse as production target.

## Exact Side-Effect Checks

Future side-effect check command:

```bash
python3 scripts/context_plus_preselector_m6_control_surface_side_effect_check.py \
  --before sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/<apply-run>/pre_apply_snapshot/manifest.json \
  --after sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/<apply-run>/post_apply_snapshot/manifest.json \
  --allowed /home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json \
  --out sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/<apply-run>/side_effect_check.json
```

Required assertions:

- Gateway config route/fallback/default model unchanged.
- Provider/model config unchanged.
- Cache config/state unchanged and not enabled.
- Memory config/route/backend unchanged and not promoted.
- M9 advisory key unchanged and not used as production key.
- Token Solver v4 default model/provider selection unchanged.
- Only allowed enforcement-state/implementation artifacts changed.

## Exact Files Likely Needing Code / Config Changes

Implementation files likely needed:

```text
services/token-solver-v4/src/config.js
services/token-solver-v4/src/server.js
services/token-solver-v4/src/v5Contract.js
services/intent-preselector-v5/config/enforcement.schema.json
scripts/context_plus_preselector_m6_control_surface_apply.py
scripts/context_plus_preselector_m6_control_surface_smoke.py
scripts/context_plus_preselector_m6_control_surface_sentinel.py
scripts/context_plus_preselector_m6_control_surface_side_effect_check.py
```

Existing relevant tests / fixtures discovered read-only:

```text
scripts/context_plus_preselector_validate_fixtures.py
scripts/context_plus_preselector_unit_tests.py
scripts/context_plus_preselector_route_contract_tests.py
scripts/context_plus_preselector_route_quality_evaluator_tests.py
scripts/context_plus_preselector_g10_journal_tests.py
scripts/context_plus_preselector_replay_journal.py
scripts/context_plus_preselector_compare_sentinels.py
scripts/context_plus_preselector_sentinel_snapshot.py
scripts/context_plus_preselector_side_by_side_smoke.py
scripts/context_plus_preselector_m9_advisory_canary_20260623.py  # existing advisory evidence only; do not rerun as production apply
services/token-solver-v4/scripts/v4_v5_shadow_contract_fixture_test.mjs
services/token-solver-v4/scripts/v4_scoring_fixture_test.mjs
services/token-solver-v4/scripts/v4_turn_contract_fixture_test.mjs
services/token-solver-v4/scripts/v4_routing_architecture_fixture_test.mjs
services/token-solver-v4/scripts/v4_prompt_precedence_fixture_test.mjs
services/token-solver-v4/scripts/v4_tool_boundary_memory_leak_regression_test.mjs
tests/test_context_plus_preselector_tool_action_boundary.py
```

New implementation tests likely required:

```text
tests/test_context_plus_m6_control_surface.py
services/token-solver-v4/test/intent-preselector-v5-enforcement.test.mjs
services/intent-preselector-v5/test/enforcement-schema.test.mjs
```

Runtime state path, created only during separately approved apply:

```text
state/intent-preselector-v5/enforcement.json
```

## Exact Tests Required Before Production Apply

Required zero-provider-call tests before production apply can be approved:

```bash
python3 scripts/context_plus_preselector_validate_fixtures.py
python3 scripts/context_plus_preselector_unit_tests.py
python3 scripts/context_plus_preselector_route_contract_tests.py
python3 scripts/context_plus_preselector_route_quality_evaluator_tests.py
python3 scripts/context_plus_preselector_g10_journal_tests.py
python3 scripts/context_plus_preselector_replay_journal.py \
  sharedspace/runtime-kernel-validation/vnext-semantic-gate/context_plus_preselector_m6_fresh_trace_shadow_run_20260622/context_plus_preselector_m6_6_targeted_coverage_journal.jsonl \
  sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/<preapply-run>/replay_summary.json \
  sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/<preapply-run>/sqlite_query_report.json
python3 scripts/context_plus_preselector_m6_control_surface_apply.py validate --state-template <candidate-state.json> --out <preapply-run>/apply_validation.json
python3 scripts/context_plus_preselector_m6_control_surface_smoke.py --mode preapply --expected-mode shadow_contract_only --out <preapply-run>/preapply_smoke.json
python3 scripts/context_plus_preselector_m6_control_surface_sentinel.py --out <preapply-run>/preapply_mutation_sentinel.json
python3 scripts/context_plus_preselector_m6_control_surface_side_effect_check.py --before <preapply-run>/before_manifest.json --after <preapply-run>/after_manifest.json --out <preapply-run>/side_effect_check.json
```

Required existing Node/Python regression tests before implementation approval:

```bash
node services/token-solver-v4/scripts/v4_v5_shadow_contract_fixture_test.mjs
node services/token-solver-v4/scripts/v4_scoring_fixture_test.mjs
node services/token-solver-v4/scripts/v4_turn_contract_fixture_test.mjs
node services/token-solver-v4/scripts/v4_routing_architecture_fixture_test.mjs
node services/token-solver-v4/scripts/v4_prompt_precedence_fixture_test.mjs
node services/token-solver-v4/scripts/v4_tool_boundary_memory_leak_regression_test.mjs
python3 -m pytest tests/test_context_plus_preselector_tool_action_boundary.py
```

Required new Node tests after implementation:

```bash
node --test services/token-solver-v4/test/intent-preselector-v5-enforcement.test.mjs
node --test services/intent-preselector-v5/test/enforcement-schema.test.mjs
```

No provider/model/Gateway calls are required for these tests.

## Exact Operator Approvals Required

Separate approvals required in order:

1. Implementation approval:
   - create code/schema/smoke/sentinel/apply helpers only,
   - no production state enablement.
2. Preapply validation approval:
   - run zero-provider-call tests and create preapply evidence.
3. Production apply approval:
   - create/update `state/intent-preselector-v5/enforcement.json` only after implementation and preapply PASS.
4. Post-apply smoke approval if smoke uses live service endpoint beyond `/route/dry-run`.
5. Broad traffic approval, if ever requested, after owner/operator canary soak PASS.

Production apply must not be approved until the control surface exists, tests pass, rollback is executable, smoke is executable, and side-effect checks are defined with concrete artifact paths.

## How M6 Comparator PASS Evidence Links To The Future Control Surface

The enforcement state must embed or reference the M6 evidence:

- comparator classification: `PASS_FALSE_POSITIVE_BASELINE_IMPROVED`
- production FP: `22/235`
- Context+ shadow FP: `0/235`
- M6 proposal commit: `871522c5204b6062419e48a5a47a4d9cd4cf97a6`
- M6 runbook HOLD commit: `c2e2decfeaa4fad82e81a54362779d461d1ebf77`
- M8 discovery HOLD commit: `1ce70de4b94c4916a8e0cdbfe37eeb2ed672fc20`

Runtime validation should refuse enforcement if the state file lacks these references or names a non-PASS comparator classification.

## Safety Rationale

This proposal uses the existing Token Solver v4 enforcement hook instead of inventing a Gateway route key.

Advantages:

- The production decision point already exists in code.
- Default behavior remains shadow-only if the state file is absent or invalid.
- Live route influence is limited to lane selection before upstream forwarding.
- `/route/dry-run` enables smoke without provider calls.
- M9 advisory key remains separate and cannot accidentally become production authority.
- Rollback can be reduced to restoring/removing one protected state file, plus reverting implementation if needed.

## Closeout

- Proposal result: `PASS_CONTROL_SURFACE_PROPOSAL_READY`
- Production apply: `NOT_RUN`
- Native apply card: `NOT_PREPARED`
- Production promoted: `NO`
- Existing exact runtime decision point: `token-solver-v4 scoreForRequest -> buildV5ShadowContract -> applyV5EnforcedRouteContract`
- Existing proposed state path: `/home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json`
- Current state file: `MISSING_SAFE_DEFAULT_SHADOW_ONLY`
- Existing M9 advisory key reused as production target: `NO`
- M8 readiness packet sufficient for production apply: `NO`
- Next safe step: implementation approval for disabled-by-default control-surface package only, not production apply
