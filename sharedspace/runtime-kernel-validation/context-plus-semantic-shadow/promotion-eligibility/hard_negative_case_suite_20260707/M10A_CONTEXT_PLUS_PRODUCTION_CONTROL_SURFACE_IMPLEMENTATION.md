# M10A Context+ Production Control Surface Implementation

Date: 2026-07-09 AEST

## Closeout Classification

`PASS_M10A_CONTROL_SURFACE_IMPLEMENTED_VALIDATED`

Non-selected classifications:

- `HOLD_M10A_SOURCE_TARGET_UNCLEAR`: not selected; the implementation uses the existing Token Solver v4 decision point.
- `HOLD_M10A_TESTS_FAILING`: not selected; local zero-provider tests passed.
- `HOLD_M10A_ROLLBACK_OR_SMOKE_INCOMPLETE`: not selected; rollback/readback/smoke helper shapes are implemented as dry-run/non-mutating commands.
- `FAIL_M10A_IMPLEMENTATION_UNSAFE`: not selected; production apply/live enablement remained blocked.

## Boundary / Non-Execution Statement

This is a disabled-by-default implementation package. It does not apply production.

Actions not performed:

- production apply: `NOT_RUN`
- native production-apply card: `NOT_PREPARED`
- live-route enablement: `NOT_RUN`
- live Gateway/config/routes mutation: `NOT_RUN`
- memory promotion: `NOT_RUN`
- provider/model change: `NOT_RUN`
- cache enablement: `NOT_RUN`
- comparator rerun: `NOT_RUN`
- replay/provider calls: `NOT_RUN`
- rollback execution: `NOT_RUN`
- production smoke execution: `NOT_RUN`

Provider/Gateway/model calls during validation: `0`.

## Prerequisites

- M10 proposal: `PASS_PUSHED`
- Branch: `evidence/context-plus-m10-production-package-proposal-20260709`
- Marker: `M10_CONTEXT_PLUS_PRODUCTION_PACKAGE_PROPOSAL_READY_NO_APPLY`
- Production apply before M10A: `NOT_RUN`
- Gateway/config/routes/cache/memory/provider/model before M10A: unchanged by M10.

## Files Changed

Implementation / runtime source:

```text
services/token-solver-v4/src/config.js
services/token-solver-v4/src/v5Contract.js
services/token-solver-v4/src/intentPreselectorV5ControlSurface.js
```

Protected schema:

```text
services/intent-preselector-v5/config/enforcement.schema.json
```

Dry-run/non-mutating helper tooling:

```text
scripts/context_plus_preselector_m10_production_package.py
```

Tests:

```text
services/token-solver-v4/test/intent-preselector-v5-enforcement.test.mjs
services/intent-preselector-v5/test/enforcement-schema.test.mjs
tests/test_context_plus_m10_control_surface.py
```

Closeout artifact:

```text
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/M10A_CONTEXT_PLUS_PRODUCTION_CONTROL_SURFACE_IMPLEMENTATION.md
```

## Exact Control Surface Added

Control surface module:

```text
services/token-solver-v4/src/intentPreselectorV5ControlSurface.js
```

Surface constants:

```text
schema: stickbot.context_plus_semantic_preselector.production_control_surface.v1
subject: CONTEXT_PLUS_SEMANTIC_PRESELECTOR
authority: lane_selection_only
default state path: /home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json
initial traffic scope: owner_operator_live_turns_only
required operator allowlist member: telegram:8495203551
```

The module adds:

- strict protected-state validation;
- required M6 evidence matching;
- provider/model/cache/memory guard validation;
- broad/wildcard traffic rejection;
- safe shadow-only fallback on missing/invalid state;
- request-scope allowlist enforcement before route contracts can be marked enforced.

## Exact Protected Config / Schema Path

Protected runtime state path, not created by M10A:

```text
/home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json
```

Schema path added:

```text
/home/stickai/.openclaw/workspace/services/intent-preselector-v5/config/enforcement.schema.json
```

Required schema id:

```text
stickbot.context_plus_semantic_preselector.production_control_surface.v1
```

Required subject:

```text
CONTEXT_PLUS_SEMANTIC_PRESELECTOR
```

Required M6 eligibility evidence:

```text
PASS_FALSE_POSITIVE_BASELINE_IMPROVED
production false positives: 22/235
Context+ shadow false positives: 0/235
M6 proposal commit: 871522c5204b6062419e48a5a47a4d9cd4cf97a6
M6 preflight commit: 551c019bdee3704e3da2a8d4eb9eb9d4c10b388e
M6 runbook HOLD commit: c2e2decfeaa4fad82e81a54362779d461d1ebf77
M8 discovery HOLD commit: 1ce70de4b94c4916a8e0cdbfe37eeb2ed672fc20
```

M6 comparator PASS is treated as eligibility evidence only. It does not create or imply automatic apply authority.

## Default State

Default state remains no production influence:

- if `state/intent-preselector-v5/enforcement.json` is missing: `shadow_contract_only`, `enforced=false`;
- if `TOKEN_SOLVER_V4_INTENT_PRESELECTOR_V5_ENFORCED=true` is set without a valid protected state: ignored, `shadow_contract_only`, `enforced=false`;
- if state is malformed/invalid: fail closed to `shadow_contract_only`, `enforced=false`;
- if state validates but is disabled/kill-switched: `shadow_contract_only`, `enforced=false`.

Current known runtime state file from earlier readback: `MISSING`, which is safe default shadow-only.

## Exact Runtime Decision Point

Existing runtime path preserved:

```text
services/token-solver-v4/src/server.js::scoreForRequest(...)
  -> scoreRequest(...)
  -> buildV5ShadowContract(...)
  -> applyV5EnforcedRouteContract(baseScore, intentPreselectorV5)
```

M10A changes enforcement eligibility before the contract can mark itself `enforced=true`:

```text
services/token-solver-v4/src/v5Contract.js::buildV5ShadowContract(...)
```

`applyV5EnforcedRouteContract(...)` remains the only live lane replacement point. It still requires `intentPreselectorV5.enforced=true` and a selected lane.

## Advisory / Live-Route Separation Proof

M9 advisory key remains separate:

```text
context_plus_semantic_preselector.m9_advisory_canary.enabled
```

M10A does not read or honor that key as production authority. Tests assert that an advisory-shaped object containing only the M9 advisory key fails protected-state validation and cannot enforce live routing.

Live-route influence now requires all of the following:

1. valid protected state schema `stickbot.context_plus_semantic_preselector.production_control_surface.v1`;
2. subject `CONTEXT_PLUS_SEMANTIC_PRESELECTOR`;
3. `enabled=true`, `mode=enforced_route_contract`, `kill_switch=false`;
4. authority `lane_selection_only`;
5. traffic scope `owner_operator_live_turns_only`;
6. operator allowlist match, initially `telegram:8495203551`;
7. exact M6 PASS evidence fields;
8. guard fields proving no prompt replacement, provider/model/cache/memory mutation, or direct provider bypass;
9. per-request allowlist match at `buildV5ShadowContract(...)`.

Without all of the above, Context+ remains shadow-only.

## Rollback / Readback / Smoke Implementation Status

Helper script added:

```text
scripts/context_plus_preselector_m10_production_package.py
```

Implemented subcommands:

```text
readback   # non-mutating state readback; missing state reports safe shadow-only
validate   # non-mutating candidate-state validation
snapshot   # dry-run manifest of watched paths unless future --execute gate is used
apply      # dry-run shape by default; refuses execution for M10A
rollback   # dry-run shape by default; refuses execution for M10A
smoke      # dry-run/non-mutating smoke-plan output; provider_calls=0
```

Rollback/readback/smoke are prepared as command shapes for a future package, not executed against production.

## Tests Run

Command that passed:

```bash
cd /home/stickai/.openclaw/workspace && \
node services/token-solver-v4/test/intent-preselector-v5-enforcement.test.mjs && \
node services/intent-preselector-v5/test/enforcement-schema.test.mjs && \
python3 tests/test_context_plus_m10_control_surface.py && \
echo M10A_LOCAL_TESTS_PASS provider_gateway_model_calls=0 production_apply=NOT_RUN
```

Observed output:

```text
{"ok":true,"name":"intent-preselector-v5-enforcement","assertions":23,"provider_calls":0}
{"ok":true,"name":"intent-preselector-v5-enforcement-schema","assertions":16,"provider_calls":0}
{"ok": true, "name": "context_plus_m10_control_surface", "assertions": 18, "provider_calls": 0}
M10A_LOCAL_TESTS_PASS provider_gateway_model_calls=0 production_apply=NOT_RUN
```

Test pass/fail counts:

- Test files run: `3`
- Test files passed: `3`
- Test files failed: `0`
- Assertions reported: `57`
- Provider/Gateway/model calls: `0`

## Test Coverage Summary

`services/token-solver-v4/test/intent-preselector-v5-enforcement.test.mjs` proves:

- env `TOKEN_SOLVER_V4_INTENT_PRESELECTOR_V5_ENFORCED=true` alone is ignored without protected state;
- missing state remains `shadow_contract_only`;
- M9 advisory key does not validate as production control surface;
- broad/all traffic and wildcard allowlists are rejected;
- valid protected state can become active;
- non-allowlisted sessions cannot get live-route enforcement;
- allowlisted owner/operator session can mark route contract enforced only when protected state validates;
- prompt preservation and `context_may_replace_prompt=false` hold at v5 contract boundary.

`services/intent-preselector-v5/test/enforcement-schema.test.mjs` proves:

- schema id/subject/authority/traffic scope are exact;
- owner Telegram allowlist requirement is encoded;
- M6 comparator PASS evidence is encoded;
- provider/model/cache/memory guard fields are false;
- enforced mode requires `enabled=true` and `kill_switch=false`.

`tests/test_context_plus_m10_control_surface.py` proves:

- readback missing state is safe shadow-only;
- candidate protected state validation works;
- apply helper defaults to dry-run and `mutation=not_executed`;
- rollback helper defaults to dry-run and `mutation=not_executed`;
- smoke helper is dry-run/non-mutating and reports `provider_calls=0`.

## Side Effects

- Production apply: `NOT_RUN`
- Native production-apply card: `NOT_PREPARED`
- Live Gateway/config/routes mutation: `NOT_RUN`
- Cache side effects: none
- Memory side effects: none
- Provider/model side effects: none
- Replay/provider calls: `0`
- Comparator rerun: `NOT_RUN`

## Preservation Plan

If scoped review is clean, preserve only the M10A implementation package on:

```text
evidence/context-plus-m10a-control-surface-implementation-20260709
```

Suggested marker:

```text
M10A_CONTEXT_PLUS_CONTROL_SURFACE_IMPLEMENTED_VALIDATED_NO_APPLY
```

Expected staged paths:

```text
services/token-solver-v4/src/config.js
services/token-solver-v4/src/v5Contract.js
services/token-solver-v4/src/intentPreselectorV5ControlSurface.js
services/intent-preselector-v5/config/enforcement.schema.json
scripts/context_plus_preselector_m10_production_package.py
services/token-solver-v4/test/intent-preselector-v5-enforcement.test.mjs
services/intent-preselector-v5/test/enforcement-schema.test.mjs
tests/test_context_plus_m10_control_surface.py
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/M10A_CONTEXT_PLUS_PRODUCTION_CONTROL_SURFACE_IMPLEMENTATION.md
```

## Final Status

- Closeout: `PASS_M10A_CONTROL_SURFACE_IMPLEMENTED_VALIDATED`
- Exact control surface added: `Token Solver v4 intent-preselector-v5 protected enforcement state`
- Exact protected schema path: `services/intent-preselector-v5/config/enforcement.schema.json`
- Default state: `shadow_contract_only`, `enforced=false`
- Advisory/run-local M9 key reused as production authority: `NO`
- Live-route influence requires explicit protected/admin mutation later: `YES`
- Rollback/readback/smoke tooling: `IMPLEMENTED_DRY_RUN_NON_MUTATING`
- Tests: `PASS`, 3 files, 57 assertions
- Provider/Gateway/model calls: `0`
- Production apply: `NOT_RUN`
- Live Gateway/config mutation: `NOT_RUN`
- Cache/memory/provider/model side effects: none
