# M10B Context+ Production Apply Readiness

Date: 2026-07-09 AEST

## Closeout Classification

`PASS_M10B_PRODUCTION_APPLY_READINESS_READY`

Non-selected classifications:

- `HOLD_M10B_FULL_VALIDATION_FAILED`: not selected; local validation passed.
- `HOLD_M10B_ROLLBACK_NOT_EXECUTABLE`: not selected; exact rollback command is defined below for separate approval if apply is later executed.
- `HOLD_M10B_SMOKE_NOT_EXECUTABLE`: not selected; exact zero-provider `/route/dry-run` smoke/readback command is defined below.
- `HOLD_M10B_APPLY_TARGET_UNCLEAR`: not selected; target is the protected enforcement state file only.
- `HOLD_M10B_PROTECTION_BOUNDARY_UNCLEAR`: not selected; protection boundary is explicit and scoped below.
- `FAIL_M10B_APPLY_READINESS_UNSAFE`: not selected; this package is readiness-only and does not apply production.

## Boundary / Non-Execution Statement

M10B is a production-apply readiness package only.

- Production apply: `NOT_RUN`
- Native production-apply execution/card: `NOT_PREPARED` / `NOT_EXECUTED`
- Live-route enablement: `NOT_RUN`
- Live Gateway/config mutation: `NOT_RUN`
- Memory promotion: `NOT_RUN`
- Provider/model change: `NOT_RUN`
- Cache enablement: `NOT_RUN`
- Rollback execution against production: `NOT_RUN`
- Comparator rerun: `NOT_RUN`
- Replay/provider calls: `NOT_RUN`

Native production apply still requires separate explicit human approval after this M10B artifact is reviewed and preserved.

## Known State / M10A Evidence

M10A implementation: `PASS_M10A_CONTROL_SURFACE_IMPLEMENTED_VALIDATED`

Exact implementation commit:

```text
06764a3351de0bb19329baede1a499953a2d5354
```

Short commit:

```text
06764a335
```

Branch:

```text
evidence/context-plus-m10a-control-surface-implementation-20260709
```

Commit subject / marker:

```text
feat(context-plus): add M10A disabled control surface
M10A_CONTEXT_PLUS_CONTROL_SURFACE_IMPLEMENTED_VALIDATED_NO_APPLY
```

## Exact Files Changed By M10A

```text
scripts/context_plus_preselector_m10_production_package.py
services/intent-preselector-v5/config/enforcement.schema.json
services/intent-preselector-v5/test/enforcement-schema.test.mjs
services/token-solver-v4/src/config.js
services/token-solver-v4/src/intentPreselectorV5ControlSurface.js
services/token-solver-v4/src/v5Contract.js
services/token-solver-v4/test/intent-preselector-v5-enforcement.test.mjs
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/M10A_CONTEXT_PLUS_PRODUCTION_CONTROL_SURFACE_IMPLEMENTATION.md
tests/test_context_plus_m10_control_surface.py
```

## Exact Production Config / Schema Key

Protected runtime state path:

```text
/home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json
```

Schema path:

```text
/home/stickai/.openclaw/workspace/services/intent-preselector-v5/config/enforcement.schema.json
```

Schema id / production key:

```text
stickbot.context_plus_semantic_preselector.production_control_surface.v1
```

Subject:

```text
CONTEXT_PLUS_SEMANTIC_PRESELECTOR
```

Authority:

```text
lane_selection_only
```

Initial traffic scope:

```text
owner_operator_live_turns_only
```

Initial operator allowlist:

```text
telegram:8495203551
```

## Exact Default Value

Current readback during M10B validation:

```json
{
  "enforced": false,
  "exists": false,
  "mode": "shadow_contract_only",
  "ok": true,
  "reason": "state_file_missing_safe_default"
}
```

Default production influence is therefore:

```text
state file missing -> shadow_contract_only -> enforced=false -> no live-route influence
```

`TOKEN_SOLVER_V4_INTENT_PRESELECTOR_V5_ENFORCED=true` alone is not sufficient. M10A tests prove env enforcement is ignored unless a valid protected state file exists and the request matches the protected owner/operator scope.

## Exact Protected / Admin Mutation Surface

Only this file may be created/updated by the future production apply:

```text
/home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json
```

The future apply must create/update that file atomically after validating candidate state against the M10A helper/schema.

Forbidden in the future apply card:

- `/home/stickai/.openclaw/openclaw.json` mutation;
- Gateway route/default/fallback/model mutation;
- provider/model catalog or credential mutation;
- memory route/backend/promotion mutation;
- cache config/state mutation;
- M9 advisory key mutation;
- broad/all-live traffic enablement;
- comparator rerun;
- replay/provider calls.

## M10B Local Validation Run

Command approved and completed:

```bash
cd /home/stickai/.openclaw/workspace && \
node services/token-solver-v4/test/intent-preselector-v5-enforcement.test.mjs && \
node services/intent-preselector-v5/test/enforcement-schema.test.mjs && \
python3 tests/test_context_plus_m10_control_surface.py && \
python3 scripts/context_plus_preselector_m10_production_package.py readback --state-path /home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json && \
python3 scripts/context_plus_preselector_m10_production_package.py snapshot \
  --state-path /home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json \
  --watch /home/stickai/.openclaw/openclaw.json \
  --watch /home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json \
  --watch /home/stickai/.openclaw/workspace/services/token-solver-v4/src/config.js \
  --watch /home/stickai/.openclaw/workspace/services/token-solver-v4/src/v5Contract.js \
  --watch /home/stickai/.openclaw/workspace/services/token-solver-v4/src/intentPreselectorV5ControlSurface.js \
  --watch /home/stickai/.openclaw/workspace/services/intent-preselector-v5/config/enforcement.schema.json && \
python3 scripts/context_plus_preselector_m10_production_package.py smoke --token-solver-v4-url http://127.0.0.1:8800 && \
echo M10B_READINESS_LOCAL_VALIDATION_PASS provider_gateway_model_calls=0 production_apply=NOT_RUN
```

Observed PASS output summary:

```text
{"ok":true,"name":"intent-preselector-v5-enforcement","assertions":23,"provider_calls":0}
{"ok":true,"name":"intent-preselector-v5-enforcement-schema","assertions":16,"provider_calls":0}
{"ok": true, "name": "context_plus_m10_control_surface", "assertions": 18, "provider_calls": 0}
M10B_READINESS_LOCAL_VALIDATION_PASS provider_gateway_model_calls=0 production_apply=NOT_RUN
```

Test pass/fail counts:

- Test files run: `3`
- Test files passed: `3`
- Test files failed: `0`
- Assertions: `57`
- Provider/Gateway/model calls: `0`
- Production apply during validation: `NOT_RUN`

## Current Snapshot Evidence From M10B Validation

Dry-run snapshot manifest reported `mutation=none` and:

```text
/home/stickai/.openclaw/openclaw.json
  exists: true
  sha256: 3ad1452efd7e01a1300b974f7f13e874c427db3a007dd45752bf19b9a4c29483
  size: 27860

/home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json
  exists: false
  sha256: null
  size: null

/home/stickai/.openclaw/workspace/services/token-solver-v4/src/config.js
  exists: true
  sha256: 013fc764d610d67bb9244847d2b4a8d07c8e72df50f64d337571b531de9e8f79
  size: 4838

/home/stickai/.openclaw/workspace/services/token-solver-v4/src/v5Contract.js
  exists: true
  sha256: 5be813971c7f9fe732aea03485cf05c988a10ee099c3da17c8e45dffe535bd2d
  size: 7489

/home/stickai/.openclaw/workspace/services/token-solver-v4/src/intentPreselectorV5ControlSurface.js
  exists: true
  sha256: 15f32dfe992533e7117bbdd2248db3ee98f6b3baf79558c0f95e51570a7367f6
  size: 8621

/home/stickai/.openclaw/workspace/services/intent-preselector-v5/config/enforcement.schema.json
  exists: true
  sha256: 6376b093b07691dd81a00a532e6cc65e127e7560219f01a330110229aeb107f6
  size: 3633
```

## Exact Pre-Apply Snapshot Command

This command is safe/read-only and should be the first step inside any separately approved production-apply card:

```bash
python3 scripts/context_plus_preselector_m10_production_package.py snapshot \
  --state-path /home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json \
  --watch /home/stickai/.openclaw/openclaw.json \
  --watch /home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json \
  --watch /home/stickai/.openclaw/workspace/services/token-solver-v4/src/config.js \
  --watch /home/stickai/.openclaw/workspace/services/token-solver-v4/src/v5Contract.js \
  --watch /home/stickai/.openclaw/workspace/services/token-solver-v4/src/intentPreselectorV5ControlSurface.js \
  --watch /home/stickai/.openclaw/workspace/services/intent-preselector-v5/config/enforcement.schema.json \
  --out sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/m10b_production_apply_<UTC>/pre_apply_snapshot/manifest.json
```

## Exact Production Apply Command / Native Card Text

Do not run this during M10B. This is the exact text for a future separately approved native production-apply card.

```bash
set -euo pipefail
cd /home/stickai/.openclaw/workspace

run_id="m10b_production_apply_$(date -u +%Y%m%dT%H%M%SZ)"
evidence_root="sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/${run_id}"
state_path="/home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json"
state_dir="$(dirname "$state_path")"
mkdir -p "$evidence_root/pre_apply_snapshot" "$evidence_root/candidate" "$evidence_root/post_apply_snapshot"

python3 scripts/context_plus_preselector_m10_production_package.py snapshot \
  --state-path "$state_path" \
  --watch /home/stickai/.openclaw/openclaw.json \
  --watch "$state_path" \
  --watch /home/stickai/.openclaw/workspace/services/token-solver-v4/src/config.js \
  --watch /home/stickai/.openclaw/workspace/services/token-solver-v4/src/v5Contract.js \
  --watch /home/stickai/.openclaw/workspace/services/token-solver-v4/src/intentPreselectorV5ControlSurface.js \
  --watch /home/stickai/.openclaw/workspace/services/intent-preselector-v5/config/enforcement.schema.json \
  --out "$evidence_root/pre_apply_snapshot/manifest.json"

if test -e "$state_path"; then
  cp "$state_path" "$evidence_root/pre_apply_snapshot/enforcement.preimage.json"
else
  printf '%s\n' '{"exists":false,"reason":"missing_safe_default_shadow_only"}' > "$evidence_root/pre_apply_snapshot/enforcement.preimage.json"
fi

cat > "$evidence_root/candidate/enforcement.owner_operator_live_turns_only.json" <<'JSON'
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
JSON

python3 scripts/context_plus_preselector_m10_production_package.py validate \
  --candidate-state "$evidence_root/candidate/enforcement.owner_operator_live_turns_only.json" \
  --out "$evidence_root/apply_validation.json"

umask 077
mkdir -p "$state_dir"
tmp_state="$(mktemp "${state_dir}/.enforcement.json.tmp.XXXXXX")"
cp "$evidence_root/candidate/enforcement.owner_operator_live_turns_only.json" "$tmp_state"
chmod 600 "$tmp_state"
mv "$tmp_state" "$state_path"

python3 scripts/context_plus_preselector_m10_production_package.py readback \
  --state-path "$state_path" \
  --out "$evidence_root/post_apply_readback.json"

python3 scripts/context_plus_preselector_m10_production_package.py smoke \
  --token-solver-v4-url http://127.0.0.1:8800 \
  --state-path "$state_path" \
  --out "$evidence_root/post_apply_smoke_plan.json"

python3 scripts/context_plus_preselector_m10_production_package.py snapshot \
  --state-path "$state_path" \
  --watch /home/stickai/.openclaw/openclaw.json \
  --watch "$state_path" \
  --watch /home/stickai/.openclaw/workspace/services/token-solver-v4/src/config.js \
  --watch /home/stickai/.openclaw/workspace/services/token-solver-v4/src/v5Contract.js \
  --watch /home/stickai/.openclaw/workspace/services/token-solver-v4/src/intentPreselectorV5ControlSurface.js \
  --watch /home/stickai/.openclaw/workspace/services/intent-preselector-v5/config/enforcement.schema.json \
  --out "$evidence_root/post_apply_snapshot/manifest.json"

printf '%s\n' "M10B_PRODUCTION_APPLY_COMMAND_COMPLETED evidence_root=$evidence_root state_path=$state_path"
```

Important: the command above is the future production-apply card text only. It was not run during M10B.

## Exact Rollback Command

Do not run this during M10B. Use only after a separately approved apply if rollback criteria trigger.

```bash
set -euo pipefail
cd /home/stickai/.openclaw/workspace

: "${evidence_root:?Set evidence_root to the M10B apply evidence directory before rollback}"
state_path="/home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json"
preimage="$evidence_root/pre_apply_snapshot/enforcement.preimage.json"
rollback_report="$evidence_root/rollback_report.json"

if grep -q '"exists":false' "$preimage"; then
  rm -f "$state_path"
  action="removed_state_file_restored_missing_safe_default"
else
  umask 077
  tmp_state="$(mktemp "$(dirname "$state_path")/.enforcement.rollback.tmp.XXXXXX")"
  cp "$preimage" "$tmp_state"
  chmod 600 "$tmp_state"
  mv "$tmp_state" "$state_path"
  action="restored_pre_apply_state_file"
fi

python3 scripts/context_plus_preselector_m10_production_package.py readback \
  --state-path "$state_path" \
  --out "$evidence_root/post_rollback_readback.json"

python3 - <<PY
import json
from pathlib import Path
Path('$rollback_report').write_text(json.dumps({
  'ok': True,
  'action': '$action',
  'state_path': '$state_path',
  'production_promoted': False,
  'mode_expected_after_rollback': 'shadow_contract_only'
}, indent=2) + '\n')
PY

printf '%s\n' "M10B_ROLLBACK_COMPLETED evidence_root=$evidence_root action=$action"
```

## Exact Smoke / Readback Command

Post-apply smoke/readback must be zero-provider and scoped to Token Solver v4 route dry-run/readback. Do not call `/v1/responses`, `/v1/chat/completions`, replay harnesses, or external providers.

Minimum non-mutating command:

```bash
python3 scripts/context_plus_preselector_m10_production_package.py readback \
  --state-path /home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json \
  --out "$evidence_root/post_apply_readback.json"

python3 scripts/context_plus_preselector_m10_production_package.py smoke \
  --token-solver-v4-url http://127.0.0.1:8800 \
  --state-path /home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json \
  --out "$evidence_root/post_apply_smoke_plan.json"
```

Optional live local route dry-run assertion, still zero-provider, if Token Solver v4 auth is available to the operator-approved shell:

```bash
curl -fsS \
  -H "content-type: application/json" \
  ${TOKEN_SOLVER_V4_API_KEY:+-H "x-api-key: ${TOKEN_SOLVER_V4_API_KEY}"} \
  --data '{"model":"token-solver-v4/auto","prompt":"Inspect the current artifact status and summarize validation state","metadata":{"chat_id":"telegram:8495203551"}}' \
  http://127.0.0.1:8800/route/dry-run \
  > "$evidence_root/post_apply_route_dry_run_owner.json"
```

The optional curl must not be replaced with provider-forwarding endpoints.

## Exact Expected Post-Apply State

If the future apply is separately approved and succeeds:

```text
state/intent-preselector-v5/enforcement.json exists
schema = stickbot.context_plus_semantic_preselector.production_control_surface.v1
subject = CONTEXT_PLUS_SEMANTIC_PRESELECTOR
enabled = true
mode = enforced_route_contract
authority = lane_selection_only
traffic_scope = owner_operator_live_turns_only
operator_allowlist = ["telegram:8495203551"]
kill_switch = false
M6 evidence fields match PASS_FALSE_POSITIVE_BASELINE_IMPROVED evidence
provider/model/cache/memory guard flags remain false
```

Runtime behavior expected after future apply:

- only owner/operator allowlisted requests may mark `intent_preselector_v5.enforced=true`;
- non-allowlisted requests remain shadow-only or rejected by scope;
- `context_may_replace_prompt=false`;
- Gateway route/default/fallback/model config unchanged;
- provider/model catalog and credentials unchanged;
- cache unchanged and not enabled;
- memory route/backend/promotion unchanged;
- M9 advisory key remains advisory/run-local only.

## Exact Rollback Triggers

Rollback must be executed immediately if any of these are observed after future apply:

1. state file missing or invalid after apply;
2. readback does not report `enforced=true` / `mode=enforced_route_contract` for valid protected state;
3. owner/operator allowlist enforcement does not work;
4. non-allowlisted scope can enable live-route influence;
5. `context_may_replace_prompt` becomes true;
6. `prompt_preserved` becomes false;
7. deterministic hard gates are bypassed;
8. Gateway config route/default/fallback/model changes;
9. provider/model catalog or credential state changes;
10. cache config/state changes or becomes enabled;
11. memory route/backend/promotion changes;
12. M9 advisory key is mutated or reused as production authority;
13. route dry-run becomes unavailable or returns non-JSON/non-200 for bounded smoke;
14. any unexpected file diff appears outside the approved state/evidence paths;
15. evidence preservation cannot be written;
16. Stick/operator sends stop/abort/rollback.

## Exact Post-Apply Health Checks

After future apply, run:

```bash
python3 scripts/context_plus_preselector_m10_production_package.py readback --state-path /home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json
python3 scripts/context_plus_preselector_m10_production_package.py smoke --token-solver-v4-url http://127.0.0.1:8800 --state-path /home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json
python3 scripts/context_plus_preselector_m10_production_package.py snapshot --state-path /home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json --watch /home/stickai/.openclaw/openclaw.json --watch /home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json --watch /home/stickai/.openclaw/workspace/services/token-solver-v4/src/config.js --watch /home/stickai/.openclaw/workspace/services/token-solver-v4/src/v5Contract.js --watch /home/stickai/.openclaw/workspace/services/token-solver-v4/src/intentPreselectorV5ControlSurface.js --watch /home/stickai/.openclaw/workspace/services/intent-preselector-v5/config/enforcement.schema.json
```

Post-apply health must show:

- readback `ok=true`;
- readback `enforced=true` for protected state;
- smoke helper `ok=true`, `dry_run=true`, `provider_calls=0`, `mutation=none`;
- snapshot shows only `state/intent-preselector-v5/enforcement.json` changed from pre-apply unless expected evidence artifacts were written.

## Exact Side-Effect Checks For Provider / Model / Cache / Memory

Compare pre/post manifests and abort/rollback if any of these changed:

- `/home/stickai/.openclaw/openclaw.json` SHA;
- provider/model catalog/config/credentials;
- Gateway route/default/fallback/model settings;
- cache config/state;
- memory backend/route/promotion state;
- M9 advisory key artifacts;
- Token Solver v4 source files;
- intent-preselector-v5 schema/source files.

Allowed production apply mutation:

```text
/home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json
```

Allowed evidence mutation:

```text
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/m10b_production_apply_<UTC>/
```

## Exact Evidence Preservation Plan After Apply

Future apply evidence directory:

```text
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/m10b_production_apply_<UTC>/
```

Required evidence files:

```text
pre_apply_snapshot/manifest.json
pre_apply_snapshot/enforcement.preimage.json
candidate/enforcement.owner_operator_live_turns_only.json
apply_validation.json
post_apply_readback.json
post_apply_smoke_plan.json
post_apply_route_dry_run_owner.json      # if optional local dry-run is authorized and succeeds
post_apply_snapshot/manifest.json
rollback_report.json                     # only if rollback executed
post_rollback_readback.json              # only if rollback executed
preservation_manifest.json
git_commit.txt
git_push.txt
```

Future evidence branch:

```text
evidence/context-plus-m10b-production-apply-evidence-<YYYYMMDD-HHMMSS>
```

Future preservation marker after apply, if separately approved and executed:

```text
M10B_CONTEXT_PLUS_PRODUCTION_APPLY_EVIDENCE_PRESERVED
```

## M10B Preservation Plan

Preserve this readiness artifact only on:

```text
evidence/context-plus-m10b-production-apply-readiness-20260709
```

M10B preservation marker:

```text
M10B_CONTEXT_PLUS_PRODUCTION_APPLY_READINESS_READY_NO_APPLY
```

Expected staged path for M10B preservation:

```text
sharedspace/runtime-kernel-validation/context-plus-semantic-shadow/promotion-eligibility/hard_negative_case_suite_20260707/M10B_CONTEXT_PLUS_PRODUCTION_APPLY_READINESS.md
```

## Final Status

- Closeout: `PASS_M10B_PRODUCTION_APPLY_READINESS_READY`
- M10A commit verified: `06764a3351de0bb19329baede1a499953a2d5354`
- Full relevant local validation: `PASS`
- Default no live-route influence: `PASS`, state missing safe default
- Advisory M9 key remains advisory/run-local only: `PASS`
- New production key disabled by default: `PASS`
- Protected/admin-only mutation path: `DEFINED`
- Pre-apply snapshot command: `DEFINED`
- Production apply command/card text: `DEFINED_NOT_EXECUTED`
- Rollback command: `DEFINED_NOT_EXECUTED`
- Smoke/readback command: `DEFINED_NOT_EXECUTED`
- Provider/Gateway/model calls during M10B: `0`
- Production apply: `NOT_RUN`
- Native production-apply execution/card: `NOT_PREPARED`
- Live Gateway/config mutation: `NOT_RUN`
- Cache/memory/provider/model side effects: none

Native production apply requires a separate explicit human approval after this M10B readiness artifact is preserved.
