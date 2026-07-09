# M10C Context+ Post-Apply Health Watch

Date: 2026-07-09 AEST

## Closeout Classification

`PASS_M10C_POST_APPLY_HEALTH_WATCH_READY`

Non-selected classifications:

- `HOLD_M10C_OBSERVATION_WINDOW_INCOMPLETE`: not selected; immediate post-apply watch completed and evidence was captured. Longer soak may be scheduled separately, but no blocking trigger appeared in this watch.
- `HOLD_M10C_HEALTH_DEGRADED`: not selected; Token Solver v4 and Gateway probes were healthy for runtime/connectivity.
- `HOLD_M10C_ROLLBACK_TRIGGER_DETECTED`: not selected; no rollback trigger fired.
- `FAIL_M10C_POST_APPLY_UNSAFE`: not selected; no unsafe side effect was detected.

Final recommendation: `KEEP_PROMOTED`

## Boundary / Non-Mutation Statement

M10C was read-only post-apply observation.

Forbidden actions remained blocked:

- production apply: `NOT_RUN` during M10C
- rollback: `NOT_RUN` because no trigger fired
- Gateway/config mutation: `NOT_RUN`
- route mutation: `NOT_RUN`
- memory promotion: `NOT_RUN`
- provider/model change: `NOT_RUN`
- cache enablement: `NOT_RUN`
- comparator rerun: `NOT_RUN`
- replay/provider calls: `NOT_RUN`

Provider calls during watch: `0`.

## Known M10B Apply Evidence

- Apply evidence branch: `evidence/context-plus-m10b-production-apply-evidence-20260709T015158Z`
- Evidence commit: `b88503515ce88b27a8c1ff0fd8a29a15ba70fbba`
- Marker: `M10B_CONTEXT_PLUS_PRODUCTION_APPLY_EVIDENCE_PRESERVED`
- State file: `state/intent-preselector-v5/enforcement.json`
- M10B readback: `ok=true`, `active=true`, `enforced=true`, `mode=enforced_route_contract`
- M10B smoke: `ok=true`, `provider_calls=0`, `mutation=none`
- M10B side-effect check: `PASS_M10B_SIDE_EFFECT_CHECK_ONLY_ALLOWED_STATE_FILE_CHANGED`
- Rollback required after M10B: `false`

## M10C Evidence Root

```text
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/m10c_post_apply_health_watch_20260709T020257Z
```

The first M10C command timed out after producing the core readback/smoke/current-manifest artifacts. It was not rerun wholesale. The missing service/log evidence was filled by a bounded read-only continuation against the same evidence root.

## Enforcement Readback

Artifact:

```text
m10c_post_apply_health_watch_20260709T020257Z/enforcement_readback.json
```

Observed:

```json
{
  "active": true,
  "enforced": true,
  "exists": true,
  "mode": "enforced_route_contract",
  "ok": true,
  "reasons": []
}
```

Result: `PASS_ENFORCEMENT_STATE_REMAINS_ACTIVE_ENFORCED`

## Smoke / Readback Result

Artifact:

```text
m10c_post_apply_health_watch_20260709T020257Z/smoke_readback.json
```

Observed:

```json
{
  "action": "smoke",
  "dry_run": true,
  "endpoint": "http://127.0.0.1:8800/route/dry-run",
  "mutation": "none",
  "ok": true,
  "provider_calls": 0
}
```

Smoke assertions captured:

- `state_schema_valid`
- `owner_operator_scope_enforced_only_when_allowlisted`
- `non_allowlisted_scope_shadow_or_rejected`
- `prompt_preserved_true`
- `context_may_replace_prompt_false`
- `gateway_provider_model_cache_memory_unchanged`

Result: `PASS_SMOKE_READBACK_ZERO_PROVIDER_CALLS`

## Gateway / Service Health

Artifact:

```text
m10c_post_apply_health_watch_20260709T020257Z/service_health.json
```

Token Solver v4 health:

- `ok=true`
- service: `token-solver-v4`
- port: `8800`
- upstream v3: `ok=true`, status `200`, readiness `ok=true`
- scoring: `deterministic-local-only`

Gateway health/status:

- runtime: `running`, active/sub-running
- connectivity probe: `ok`
- capability: `admin-capable`
- listening: `*:18789`

Non-blocking finding: Gateway status reported service config looks out of date/non-standard because service PATH is missing `/home/stickai/.local/share/pnpm`, with recommendation to run `openclaw doctor`. This is not a Context+ rollback trigger because runtime/connectivity are healthy and no route/config mutation occurred during M10C.

Result: `PASS_WITH_FINDING_SERVICE_HEALTH_RUNNING_CONNECTIVITY_OK`

## Mutation / Side-Effect Check

Artifacts:

```text
m10c_post_apply_health_watch_20260709T020257Z/current_manifest.json
m10c_post_apply_health_watch_20260709T020257Z/side_effect_check.json
```

Compared against baseline:

```text
m10b_production_apply_20260709T015158Z/post_apply_snapshot/manifest.json
```

Result:

```text
PASS_M10C_SIDE_EFFECT_CHECK_NO_UNEXPECTED_MUTATION
```

Manifest comparison found no changes from the M10B post-apply baseline for:

- `/home/stickai/.openclaw/openclaw.json`
- `/home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json`
- `/home/stickai/.openclaw/workspace/services/token-solver-v4/src/config.js`
- `/home/stickai/.openclaw/workspace/services/token-solver-v4/src/v5Contract.js`
- `/home/stickai/.openclaw/workspace/services/token-solver-v4/src/intentPreselectorV5ControlSurface.js`
- `/home/stickai/.openclaw/workspace/services/intent-preselector-v5/config/enforcement.schema.json`

Provider/model/cache/memory/config mutation result: `false`.

## Log Scan / Route-Contract Health

Artifact:

```text
m10c_post_apply_health_watch_20260709T020257Z/log_scan.json
```

Raw bounded scan result:

```json
{
  "direct_provider_bypass": 1,
  "fallback_surprise": 0,
  "rollback_trigger": 0,
  "route_contract_failure": 0
}
```

Disposition:

- Raw `direct_provider_bypass=1` is a false-positive grep hit from the enforcement state guard line:
  - `"direct_provider_bypass_allowed": false,`
- Semantic direct-provider bypass count: `0`
- Fallback surprise count: `0`
- Route-contract failure count: `0`
- Rollback trigger count: `0`

Route-contract health result: `PASS_NO_ROUTE_CONTRACT_FAILURES_DETECTED`

## Rollback Trigger Status

Rollback trigger status: `NOT_DETECTED`

No trigger fired for:

- state file missing/invalid;
- enforcement inactive;
- smoke/readback failure;
- direct provider bypass;
- fallback surprise;
- route-contract failure;
- Gateway/service runtime failure;
- unexpected provider/model/cache/memory/config mutation;
- unexpected source/config hash drift;
- comparator/replay/provider execution.

Rollback executed: `NO`

## Required Closeout Fields

- Enforcement readback: `ok=true`, `active=true`, `enforced=true`, `mode=enforced_route_contract`
- Gateway/service health: `PASS_WITH_FINDING`, runtime/connectivity healthy; non-blocking PATH warning noted
- Smoke/readback result: `ok=true`, `provider_calls=0`, `mutation=none`
- Provider calls during watch: `0`
- Mutation result: `PASS_NO_UNEXPECTED_MUTATION`
- Side-effect check: `PASS_M10C_SIDE_EFFECT_CHECK_NO_UNEXPECTED_MUTATION`
- Rollback trigger status: `NOT_DETECTED`
- Route-contract health: `PASS_NO_ROUTE_CONTRACT_FAILURES_DETECTED`
- Direct-provider bypass count: raw `1`, semantic `0` after false-positive disposition
- Fallback surprise count: `0`
- Final recommendation: `KEEP_PROMOTED`

## Evidence Files

```text
m10c_post_apply_health_watch_20260709T020257Z/enforcement_readback.json
m10c_post_apply_health_watch_20260709T020257Z/smoke_readback.json
m10c_post_apply_health_watch_20260709T020257Z/current_manifest.json
m10c_post_apply_health_watch_20260709T020257Z/service_health.json
m10c_post_apply_health_watch_20260709T020257Z/log_scan.json
m10c_post_apply_health_watch_20260709T020257Z/side_effect_check.json
```

## Final Status

- Closeout: `PASS_M10C_POST_APPLY_HEALTH_WATCH_READY`
- Recommendation: `KEEP_PROMOTED`
- Rollback required: `false`
- Preserve evidence: `YES`, if scoped review is clean
