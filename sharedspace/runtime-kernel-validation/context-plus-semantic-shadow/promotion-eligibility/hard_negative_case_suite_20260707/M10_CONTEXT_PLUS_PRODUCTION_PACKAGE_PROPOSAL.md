# M10 Context+ Production Package Proposal

Date: 2026-07-09 AEST

## Closeout Classification

Primary classification: `PASS_M10_PRODUCTION_PACKAGE_PROPOSAL_READY`

Secondary state carried forward until this artifact is preserved and reviewed:

- `HOLD_CONTROL_SURFACE_PROPOSAL_UNPRESERVED` — the earlier M6 control-surface proposal is known present locally but was not proven committed/pushed because exec approval/allowlist timeouts blocked preservation. This M10 artifact must also be preserved before any downstream implementation/apply work relies on it.

Non-selected failure/hold classifications and rationale:

- `HOLD_PRODUCTION_SURFACE_UNRESOLVED`: not selected for this proposal because the package proposes a specific production surface below; implementation/review still required before apply.
- `HOLD_RUNTIME_DECISION_POINT_NOT_FOUND`: not selected; the runtime decision point is already visible in Token Solver v4.
- `HOLD_ROLLBACK_OR_SMOKE_DESIGN_UNCLEAR`: not selected; exact rollback/smoke command shapes and trigger criteria are defined below, but not executed.
- `FAIL_M10_PACKAGE_UNSAFE`: not selected; this is proposal-only, bounded, and explicitly forbids production apply.

## Boundary / Non-Execution Statement

This artifact is an operator-reviewable production package proposal only.

Actions not performed:

- production apply: `NOT_RUN`
- native production-apply card: `NOT_PREPARED`
- Gateway/config/route mutation: `NOT_RUN`
- live-route influence: `NOT_RUN`
- rollback execution: `NOT_RUN`
- live smoke: `NOT_RUN`
- memory promotion: `NOT_RUN`
- provider/model change: `NOT_RUN`
- cache enablement: `NOT_RUN`
- comparator rerun: `NOT_RUN`
- replay/provider calls: `NOT_RUN`

Production apply remains forbidden until this package is reviewed, implementation/preapply evidence closes PASS, and a separate explicit owner/operator production-apply approval is given.

## Starting Evidence

Known current state:

- Daily context-bridge reconcile: `PASS`
- Drift resolution daily: `PASS`
- Context+ hard-negative comparator: `PASS_FALSE_POSITIVE_BASELINE_IMPROVED`
- Production false positives: `22/235`
- Context+ shadow false positives: `0/235`
- Authoritative comparator cases: `235`
- Held/non-authoritative cases excluded from promotion basis: `hn-20260707-0008`, `hn-20260707-0027`, `hn-20260707-0133`, `hn-20260707-0145`, `hn-20260707-0153`
- M6 proposal commit: `871522c5204b6062419e48a5a47a4d9cd4cf97a6`
- M6 production-apply preflight commit: `551c019bdee3704e3da2a8d4eb9eb9d4c10b388e`
- M6 runbook hold commit: `c2e2decfeaa4fad82e81a54362779d461d1ebf77`
- M8 target-discovery hold commit: `1ce70de4b94c4916a8e0cdbfe37eeb2ed672fc20`
- Production apply: `NOT_RUN`
- Production promoted: `NO`
- Existing state file readback: `/home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json` is currently missing, which is the safe shadow-only default.

## Exact Intended Production Control Surface

The intended production control surface is a Token Solver v4 / intent-preselector-v5 protected enforcement state file plus schema validation:

```text
state file: /home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json
schema file to add: /home/stickai/.openclaw/workspace/services/intent-preselector-v5/config/enforcement.schema.json
surface id: stickbot.context_plus_semantic_preselector.production_control_surface.v1
subject: CONTEXT_PLUS_SEMANTIC_PRESELECTOR
authority: lane_selection_only
initial traffic scope: owner_operator_live_turns_only
operator allowlist: ["telegram:8495203551"]
```

The surface must be treated as admin/protected state. It must not be writable by ordinary chat/tool flows, heartbeat, cron, replay, comparator, advisory canary runs, or memory promotion.

## Exact Runtime Decision Point To Modify

Runtime service:

```text
token-solver-v4
```

Exact current decision path:

```text
services/token-solver-v4/src/server.js::scoreForRequest(...)
  -> scoreRequest(...)
  -> buildV5ShadowContract(...)
  -> applyV5EnforcedRouteContract(baseScore, intentPreselectorV5)
  -> v3ModelForLane(score.recommendedLane)
```

Exact live decision point:

```text
services/token-solver-v4/src/server.js::applyV5EnforcedRouteContract(...)
```

Exact value that may change after separate approved apply:

```text
score.recommendedLane
```

Bounded authority:

- Context+ may influence lane selection only.
- Deterministic hard gates remain higher priority than Context+.
- Context+ must not replace the user prompt.
- Context+ must not directly select provider credentials, bypass token-solver lanes, change default model/fallback order, enable cache, promote memory, or mutate Gateway routes.

## Exact Config / Schema Key To Add Or Use

Use the existing Token Solver v4 state path and add strict schema validation.

Existing loader/config surface:

```text
services/token-solver-v4/src/config.js::loadIntentPreselectorV5State()
TOKEN_SOLVER_V4_INTENT_PRESELECTOR_V5_STATE_PATH
TOKEN_SOLVER_V4_INTENT_PRESELECTOR_V5_MODE
TOKEN_SOLVER_V4_INTENT_PRESELECTOR_V5_ENFORCED
TOKEN_SOLVER_V4_INTENT_PRESELECTOR_V5_SHADOW
TOKEN_SOLVER_V4_INTENT_PRESELECTOR_V5_TRACE
```

Required production schema key/state object:

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
    "preflight_commit": "551c019bdee3704e3da2a8d4eb9eb9d4c10b388e",
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
  }
}
```

Validation rules:

- `schema` must equal `stickbot.context_plus_semantic_preselector.production_control_surface.v1`.
- `subject` must equal `CONTEXT_PLUS_SEMANTIC_PRESELECTOR`.
- `mode` must be `shadow_contract_only` or `enforced_route_contract` only.
- `mode=enforced_route_contract` is valid only when `enabled=true` and `kill_switch=false`.
- `authority` must equal `lane_selection_only`.
- Initial `traffic_scope` must equal `owner_operator_live_turns_only`; `all_live_traffic` is invalid until a later owner-approved package exists.
- `operator_allowlist` must include `telegram:8495203551` and must not include broad wildcard scopes.
- M6 evidence fields must match the PASS evidence above.
- All provider/model/cache/memory mutation guard flags must remain false.
- Any validation failure must force `shadow_contract_only` and emit a degraded/readback reason.

## Exact Admin / Protected Mutation Path

Admin/protected future mutation path:

```text
owner approval -> native approval for implementation/preapply package -> zero-provider preapply PASS -> separate owner production-apply approval -> protected local apply helper writes state/intent-preselector-v5/enforcement.json -> readback/smoke -> preservation
```

Only this file may be changed by the final production apply step:

```text
/home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json
```

Implementation approval may separately allow changes to the implementation/test/helper files listed later. Production apply must not piggyback implementation edits.

Forbidden mutation surfaces:

- `/home/stickai/.openclaw/openclaw.json`
- Gateway route/default/fallback/model config
- provider/model catalog or credentials
- memory backend/route/promotion state
- cache config/state
- M9 advisory canary feature flag
- broad traffic/default routing controls

## Exact Pre-Apply Snapshot Command Shape

Do not execute now. Future exact command shape after implementation approval:

```bash
python3 scripts/context_plus_preselector_m10_production_package.py snapshot \
  --state-path /home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json \
  --schema-path /home/stickai/.openclaw/workspace/services/intent-preselector-v5/config/enforcement.schema.json \
  --watch /home/stickai/.openclaw/openclaw.json \
  --watch /home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json \
  --watch /home/stickai/.openclaw/workspace/services/token-solver-v4/src/config.js \
  --watch /home/stickai/.openclaw/workspace/services/token-solver-v4/src/server.js \
  --watch /home/stickai/.openclaw/workspace/services/token-solver-v4/src/v5Contract.js \
  --watch /home/stickai/.openclaw/workspace/services/intent-preselector-v5/config/enforcement.schema.json \
  --out sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/m10_production_package_apply_<UTC>/pre_apply_snapshot
```

Snapshot requirements:

- capture SHA256, size, existence, and redacted content for the enforcement state file;
- capture SHA256/existence only for sensitive Gateway/provider config unless a separate redacted snapshot helper is approved;
- record current `token-solver-v4` health/readback without modifying service state;
- record current state file as `MISSING_SAFE_DEFAULT_SHADOW_ONLY` if absent.

## Exact Apply Command Shape

Do not execute now. Do not prepare a native production-apply card now.

Future exact production apply command shape after implementation/preapply PASS and separate owner approval:

```bash
python3 scripts/context_plus_preselector_m10_production_package.py apply \
  --state-path /home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json \
  --schema-path /home/stickai/.openclaw/workspace/services/intent-preselector-v5/config/enforcement.schema.json \
  --candidate-state sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/m10_production_package_apply_<UTC>/candidate/enforcement.owner_operator_live_turns_only.json \
  --expected-preimage sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/m10_production_package_apply_<UTC>/pre_apply_snapshot/enforcement.preimage.json \
  --evidence-root sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/m10_production_package_apply_<UTC> \
  --require-comparator PASS_FALSE_POSITIVE_BASELINE_IMPROVED \
  --require-production-fp 22/235 \
  --require-shadow-fp 0/235 \
  --traffic-scope owner_operator_live_turns_only \
  --operator telegram:8495203551 \
  --no-gateway-config-change \
  --no-provider-model-change \
  --no-cache-enable \
  --no-memory-promotion
```

Apply requirements:

- atomic write only to `state/intent-preselector-v5/enforcement.json`;
- refuse if preimage does not match snapshot;
- refuse if schema validation fails;
- refuse if candidate enables broad/all-live traffic;
- refuse if candidate permits provider/model/cache/memory/default-route mutation;
- refuse if M6 comparator evidence is missing or mismatched;
- write `apply_report.json` and `post_apply_readback.json` under the apply evidence root.

## Exact Rollback Command Shape

Do not execute now.

Future exact rollback command shape:

```bash
python3 scripts/context_plus_preselector_m10_production_package.py rollback \
  --state-path /home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json \
  --snapshot sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/m10_production_package_apply_<UTC>/pre_apply_snapshot/enforcement.preimage.json \
  --safe-disabled-template sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/m10_production_package_apply_<UTC>/candidate/enforcement.safe_disabled.json \
  --out sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/m10_production_package_apply_<UTC>/rollback_report.json \
  --post-rollback-readback sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/m10_production_package_apply_<UTC>/post_rollback_readback.json
```

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

Rollback requirements:

- restore the exact preimage if the state file existed;
- otherwise remove the state file or write the safe disabled state;
- verify post-rollback `/route/dry-run` reports `intent_preselector_v5.enforced=false` or `mode=shadow_contract_only`;
- preserve rollback report and readback before closing PASS.

## Exact Live Smoke / Readback Checks

Preferred smoke endpoint is zero-provider-call route dry-run:

```text
POST http://127.0.0.1:8800/route/dry-run
```

Do not call provider forwarding endpoints for this package smoke.

Future exact smoke command shape:

```bash
python3 scripts/context_plus_preselector_m10_production_package.py smoke \
  --token-solver-v4-url http://127.0.0.1:8800 \
  --state-path /home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json \
  --expected-schema stickbot.context_plus_semantic_preselector.production_control_surface.v1 \
  --expected-subject CONTEXT_PLUS_SEMANTIC_PRESELECTOR \
  --expected-mode enforced_route_contract \
  --expected-enforced true \
  --expected-traffic-scope owner_operator_live_turns_only \
  --expected-operator telegram:8495203551 \
  --expected-comparator PASS_FALSE_POSITIVE_BASELINE_IMPROVED \
  --dry-run-endpoint /route/dry-run \
  --out sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/m10_production_package_apply_<UTC>/post_apply_smoke.json
```

Smoke/readback assertions:

- state schema validates;
- readback reports `mode=enforced_route_contract`, `enabled=true`, `kill_switch=false` only for allowlisted owner/operator scope;
- non-allowlisted scope remains shadow/not enforced or is rejected by scope guard;
- `score.recommendedLane` changes only when Context+ selects a safe lane and deterministic hard gates do not override;
- `routeContractApplied=true` appears only on enforced route-contract decisions;
- `routeContractSource=intent-preselector-v5` or `deterministic-hard-gate-over-v5` appears as expected;
- `prompt_preserved=true` and `context_may_replace_prompt=false`;
- `target_v3_model` remains derived from approved Token Solver v4 lane mapping;
- no provider/model call is made by smoke.

## Exact Rollback Trigger Criteria

Rollback must run immediately if any of these occur during apply/smoke/watch:

1. state file schema validation fails;
2. `/route/dry-run` is unavailable or returns non-JSON / non-200 for bounded smoke;
3. `intent_preselector_v5.enforced` is false for allowlisted owner/operator scope after approved apply;
4. `intent_preselector_v5.enforced` is true for non-allowlisted or broad scope;
5. `context_may_replace_prompt` is true or `prompt_preserved` is false;
6. `score.recommendedLane` changes outside `applyV5EnforcedRouteContract(...)` authority;
7. deterministic hard gate is bypassed by Context+;
8. Gateway config route/default/fallback/model changes;
9. provider/model catalog or credentials change;
10. cache state/config changes or becomes enabled;
11. memory backend/route/promotion changes;
12. M9 advisory key is mutated or reused as production authority;
13. any unexpected workspace/config diff outside allowed apply/evidence paths appears;
14. evidence preservation for apply/smoke cannot be written;
15. human/operator sends stop/abort/rollback instruction.

## Exact Expected Post-Apply State

After future separate approved apply, expected state is:

- `state/intent-preselector-v5/enforcement.json` exists and validates against `enforcement.schema.json`;
- schema is `stickbot.context_plus_semantic_preselector.production_control_surface.v1`;
- `enabled=true`, `mode=enforced_route_contract`, `kill_switch=false`;
- `authority=lane_selection_only`;
- `traffic_scope=owner_operator_live_turns_only`;
- allowlist includes only explicit approved owner/operator identities, starting with `telegram:8495203551`;
- M6 comparator evidence references match the preserved evidence chain;
- Token Solver v4 `/route/dry-run` readback shows enforcement only for allowlisted scope;
- Gateway route/default/fallback/model config unchanged;
- provider/model/cache/memory state unchanged;
- M9 advisory key unchanged and remains non-production.

## Exact Files / Config / Routes Expected To Change

During M10 proposal creation now:

```text
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/M10_CONTEXT_PLUS_PRODUCTION_PACKAGE_PROPOSAL.md
```

During a later implementation approval, likely files to add/change:

```text
services/token-solver-v4/src/config.js
services/token-solver-v4/src/server.js
services/token-solver-v4/src/v5Contract.js
services/intent-preselector-v5/config/enforcement.schema.json
scripts/context_plus_preselector_m10_production_package.py
services/token-solver-v4/test/intent-preselector-v5-enforcement.test.mjs
services/intent-preselector-v5/test/enforcement-schema.test.mjs
tests/test_context_plus_m10_control_surface.py
```

During a later production apply approval, only this runtime state file should change:

```text
state/intent-preselector-v5/enforcement.json
```

Routes expected to change:

```text
none at Gateway level
```

Runtime route behavior expected to change only within Token Solver v4 lane selection for allowlisted owner/operator traffic:

```text
score.recommendedLane may be replaced by Context+ selected_lane inside applyV5EnforcedRouteContract(...)
```

## Exact Side-Effect Checks For Provider / Model / Cache / Memory

Future side-effect command shape:

```bash
python3 scripts/context_plus_preselector_m10_production_package.py side-effects \
  --before sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/m10_production_package_apply_<UTC>/pre_apply_snapshot/manifest.json \
  --after sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/m10_production_package_apply_<UTC>/post_apply_snapshot/manifest.json \
  --allowed /home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json \
  --out sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/m10_production_package_apply_<UTC>/side_effect_check.json
```

Required assertions:

- `/home/stickai/.openclaw/openclaw.json` unchanged except redacted metadata expected by approved tooling, if any;
- Gateway route/default/fallback/model routing unchanged;
- provider/model catalog and credentials unchanged;
- Token Solver v4 provider/model mapping unchanged;
- cache config/state unchanged and not enabled;
- memory config/route/backend unchanged and not promoted;
- M9 advisory key unchanged;
- no direct provider bypass introduced;
- no replay/provider calls made by preapply/smoke;
- only allowed enforcement state and approved implementation/evidence paths changed.

## Exact Preservation Plan For Apply / Smoke / Rollback Evidence

Evidence root for future implementation/preapply/apply:

```text
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/m10_production_package_apply_<UTC>/
```

Required evidence files:

```text
run_config.json
pre_apply_snapshot/manifest.json
pre_apply_snapshot/enforcement.preimage.json
candidate/enforcement.owner_operator_live_turns_only.json
candidate/enforcement.safe_disabled.json
apply_validation.json
apply_report.json
post_apply_readback.json
post_apply_smoke.json
post_apply_snapshot/manifest.json
side_effect_check.json
rollback_report.json              # only if rollback executed
post_rollback_readback.json        # only if rollback executed
preservation_manifest.json
git_commit.txt
git_push.txt
```

Preservation branch names:

```text
proposal branch: evidence/context-plus-m10-production-package-proposal-20260709
future implementation branch: evidence/context-plus-m10-production-package-implementation-<YYYYMMDD>
future apply evidence branch: evidence/context-plus-m10-production-package-apply-<YYYYMMDD-HHMM>
```

Required marker for proposal preservation:

```text
M10_CONTEXT_PLUS_PRODUCTION_PACKAGE_PROPOSAL_READY_NO_APPLY
```

Required marker for future apply preservation, if separately approved and executed:

```text
M10_CONTEXT_PLUS_PRODUCTION_PACKAGE_APPLY_EVIDENCE_PRESERVED
```

## Exact Operator Approval Gates

Gate 0 — Proposal preservation:

- allowed action: stage/commit/push only this proposal artifact;
- forbidden: implementation, production apply, config mutation, Gateway mutation, provider/model/cache/memory mutation.

Gate 1 — Implementation approval:

- add disabled-by-default schema/helper/tests;
- no production enforcement state enablement;
- no live-route influence.

Gate 2 — Preapply validation approval:

- run zero-provider-call tests and snapshot/sentinel checks;
- no production state write except temporary evidence files under the approved evidence root.

Gate 3 — Production apply approval:

- separately approved native apply command writes only `state/intent-preselector-v5/enforcement.json`;
- no implementation edits in same gate;
- no Gateway/config/routes/provider/model/cache/memory mutation.

Gate 4 — Post-apply smoke/readback:

- `/route/dry-run` only by default;
- provider-forwarding live smoke requires a separate explicit approval and should not be part of first apply.

Gate 5 — Broader traffic, if ever requested:

- separate package after owner/operator canary soak PASS;
- all-live traffic is explicitly out of scope for this package.

## M6 Comparator PASS Linkage

M6 comparator PASS evidence is necessary but not sufficient for production apply.

It justifies this package because it shows the Context+ shadow path eliminated observed false positives in the hard-negative suite:

```text
production false positives: 22/235
Context+ shadow false positives: 0/235
classification: PASS_FALSE_POSITIVE_BASELINE_IMPROVED
```

The future enforcement state must embed these exact evidence fields and commits. The apply helper must refuse enforcement if they are missing or mismatched.

M6 does not by itself authorize production because M6 did not define the exact production control surface, executable rollback, smoke/readback, side-effect sentinel, or operator approval gates. This M10 package closes the design proposal gap only; it does not execute promotion.

## Why Advisory / Run-Local M9 Key Is Insufficient

Existing key:

```text
context_plus_semantic_preselector.m9_advisory_canary.enabled
```

It is insufficient and must not be reused because its own evidence classifies it as:

- `apply_scope=run_local_sidecar_advisory_canary_only`
- `mode=advisory_canary_shadow_contract_only`
- `live_route_influence=false`
- `m10_or_production_started=false`
- `broad_live_traffic=false`
- `cache_enabled=false`
- `artifact_memory_promoted=false`
- `gateway_config_route_fallback_memory_runtime_model_mutated=false`

M9 is historical advisory evidence. It is not a production promotion target, not a Token Solver v4 enforcement state, and not an approval to influence live routing.

## Why Production Apply Is Still Forbidden

Production apply remains forbidden because this artifact is a proposal, not an executed implementation/runbook. Before any production apply:

1. this proposal must be preserved;
2. an implementation package must add the schema/helper/tests disabled by default;
3. preapply validation must close PASS with zero provider/model/replay calls;
4. rollback and smoke helpers must be executable and validated;
5. side-effect sentinels must prove Gateway/provider/model/cache/memory are unchanged;
6. the operator must approve a separate native production-apply command/card;
7. broad traffic must remain out of scope.

Any attempt to enable production from only M6/M9 evidence, or by toggling the M9 advisory key, must fail closed as unsafe.

## Final Status

- Proposal artifact: `M10_CONTEXT_PLUS_PRODUCTION_PACKAGE_PROPOSAL.md`
- Classification: `PASS_M10_PRODUCTION_PACKAGE_PROPOSAL_READY`
- Production apply: `NOT_RUN`
- Native production-apply card: `NOT_PREPARED`
- Production promoted: `NO`
- Runtime decision point: `FOUND`
- Intended production control surface: `DEFINED_AS_PROTECTED_TOKEN_SOLVER_V4_INTENT_PRESELECTOR_V5_ENFORCEMENT_STATE`
- Rollback design: `DEFINED_NOT_EXECUTED`
- Smoke/readback design: `DEFINED_NOT_EXECUTED`
- M9 key reused as production target: `NO`
- Next safe step: preserve this proposal artifact only, then review/approve a disabled-by-default implementation package if desired.
