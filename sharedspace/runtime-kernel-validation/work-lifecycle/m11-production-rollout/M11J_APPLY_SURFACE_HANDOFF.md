# M11J Apply-Surface Handoff Package — NO APPLY

Terminal classification: `HOLD_EXTERNAL_GATEWAY_TOOL_CONTEXT_REQUIRED`

Handoff readiness: `PASS_HANDOFF_READY`

M11J produces a safe operator handoff for executing the already validated M11 production-canary apply from an approved OpenClaw/Gateway execution context where the first-class Gateway config patch mutation surface is actually exposed and callable.

No config mutation, Gateway mutation, plugin registration, exec/CLI config patch fallback, service restart, Telegram/runtime send, provider/message API call, production apply, production promotion, M12 start, commit, or push occurred during M11J.

## Supersedes / correction

M11I's prior classification `PASS_CALLABLE_TOOL_SURFACE_IDENTIFIED` is superseded for the actual assistant execution surface.

Corrected conclusion:

- Gateway schema lookup was observable from this assistant surface.
- The callable first-class Gateway mutation surface `gateway action="config.patch"` was not available to complete the apply from this assistant surface.
- Therefore M11 production-canary apply cannot be executed from this context without violating the approved boundary.
- Exec/CLI config mutation fallback remains forbidden.

Corrected blocker:

`HOLD_GATEWAY_PATCH_TOOL_NOT_EXPOSED_IN_ASSISTANT_SURFACE`

## Current state before handoff

- M11 final apply retry: `HOLD_APPROVAL_TRANSPORT_BLOCKED`
- More precise blocker: `HOLD_GATEWAY_PATCH_TOOL_NOT_EXPOSED_IN_ASSISTANT_SURFACE`
- Preflight: `PASS`
- Rollback package: verified
- Config/plugin change applied: none
- Gateway/service restart: none
- Post-apply smoke: not run because apply did not occur
- Closeout-delivery validation: not run because apply did not occur
- M12: `NOT_STARTED`

Latest verified preflight:

- HEAD: `a96f8c063dd50ee86f5b859b28c59262d0538a38`
- M11E: `PASS`
- M11F: `PASS`
- M11G-R1: `PASS`
- M11H: `PASS`
- M11I: `PASS` artifact exists but callable-surface conclusion superseded by M11J
- Package validation: `PASS`
- Scaffold test: `PASS`
- Redaction scan: `PASS`
- `git diff --check`: `PASS`
- Boundary check: `PASS`

## Required execution context

The M11 apply must be performed from another approved OpenClaw/Gateway tool context that can actually invoke the first-class config mutation tool:

- Tool: `gateway`
- Action: `config.patch`
- Invocation type: first-class OpenClaw Gateway config tool call, not shell/exec/CLI config mutation
- Required arguments: preserved M11E patch payload, note, and continuation message below

If that context cannot call `gateway` with `action="config.patch"`, the operator must stop and classify:

`HOLD_GATEWAY_PATCH_TOOL_NOT_EXPOSED_IN_EXECUTION_CONTEXT`

Do not use `openclaw` CLI, direct file edits, shell redirection, `jq`, `sed`, or any exec fallback to mutate Gateway config.

## Required preflight before any external-context apply

Run these checks immediately before applying from the approved external Gateway tool context.

Expected HEAD:

`a96f8c063dd50ee86f5b859b28c59262d0538a38`

Expected rollback package:

`/home/stickai/.openclaw/workspace/state/work-lifecycle/rollback/m11e-production-canary/openclaw-config-and-plugin-preapply-20260701T141000Z.tar.gz`

Expected rollback SHA256:

`3f68e3ac32ebeb341b65317ec16fec6f72c436ccf35a66fb44ab61049ec46609`

Preflight command bundle, read-only except writing local validation outputs under the M11 evidence directory:

```bash
set -u -o pipefail
ROOT="sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout"
M11E="$ROOT/M11E_EXECUTABLE_PRODUCTION_CANARY_PACKAGE.md"
M11F="$ROOT/M11F_FINAL_APPLY_READINESS_REVIEW.md"
M11GR1="$ROOT/M11G_R1_REDACTION_VALIDATOR_REPAIR.md"
M11H="$ROOT/M11H_GATEWAY_CONFIG_TOOL_AVAILABILITY.md"
M11I="$ROOT/M11I_GATEWAY_TOOL_SURFACE_RECONCILIATION.md"
M11J="$ROOT/M11J_APPLY_SURFACE_HANDOFF.md"
PKG="$ROOT/apply-package/work-lifecycle-production-canary"
EXPECTED_HEAD="a96f8c063dd50ee86f5b859b28c59262d0538a38"
ROLLBACK_TGZ="/home/stickai/.openclaw/workspace/state/work-lifecycle/rollback/m11e-production-canary/openclaw-config-and-plugin-preapply-20260701T141000Z.tar.gz"
EXPECTED_ROLLBACK_SHA="3f68e3ac32ebeb341b65317ec16fec6f72c436ccf35a66fb44ab61049ec46609"

CURRENT_HEAD="$(git rev-parse HEAD)"
printf 'current_head=%s\nexpected_head=%s\n' "$CURRENT_HEAD" "$EXPECTED_HEAD"
[ "$CURRENT_HEAD" = "$EXPECTED_HEAD" ] || { echo 'ABORT_HEAD_MISMATCH'; exit 20; }

# Package/evidence files must be clean at apply time.
git status --short -- "$M11E" "$M11F" "$M11GR1" "$M11H" "$M11I" "$M11J" "$PKG"
[ -z "$(git status --short -- "$M11E" "$M11F" "$M11GR1" "$M11H" "$M11I" "$M11J" "$PKG")" ] || { echo 'ABORT_PACKAGE_ARTIFACT_DIRTY'; exit 21; }

grep -q 'Terminal classification: `PASS_APPLY_PACKAGE_READY`' "$M11E" || { echo 'ABORT_M11E_NOT_PASS'; exit 22; }
grep -q 'Terminal classification: `PASS_READY_FOR_OPERATOR_APPLY_APPROVAL`' "$M11F" || { echo 'ABORT_M11F_NOT_PASS'; exit 23; }
grep -q 'Terminal local validation: `PASS_LOCAL_VALIDATED`' "$M11GR1" || { echo 'ABORT_M11G_R1_NOT_PASS'; exit 24; }
grep -q 'Terminal classification: `PASS_TOOL_AVAILABLE`' "$M11H" || { echo 'ABORT_M11H_NOT_PASS'; exit 25; }
grep -q 'HOLD_GATEWAY_PATCH_TOOL_NOT_EXPOSED_IN_ASSISTANT_SURFACE' "$M11J" || { echo 'ABORT_M11J_HANDOFF_NOT_CURRENT'; exit 26; }

test -s "$ROLLBACK_TGZ" || { echo 'ABORT_ROLLBACK_PACKAGE_MISSING'; exit 27; }
ACTUAL_ROLLBACK_SHA="$(sha256sum "$ROLLBACK_TGZ" | awk '{print $1}')"
[ "$ACTUAL_ROLLBACK_SHA" = "$EXPECTED_ROLLBACK_SHA" ] || { echo 'ABORT_ROLLBACK_SHA_MISMATCH'; exit 28; }

python3 - <<'PY'
from pathlib import Path
import json, sys
run_dir = Path('state/work-lifecycle/runs')
started = []
for path in sorted(run_dir.glob('work_*lifecycle_ledger_m12*.json')):
    try:
        data = json.loads(path.read_text())
    except Exception as exc:
        started.append((str(path), f'parse_error:{exc}'))
        continue
    status = data.get('status') or data.get('m12Status') or data.get('current_status')
    started.append((str(path), str(status)))
if started:
    print('M12_STATE_CHECK_FAIL')
    for path, status in started:
        print(f'{path}\t{status}')
    sys.exit(29)
print('M12_STATE_CHECK_PASS')
PY

node --check "$PKG/index.mjs" || exit 30
node "$PKG/validate-package.mjs" > "$ROOT/m11j-preapply-package-validation.json" || exit 31
node --experimental-strip-types --test src/work-lifecycle/work-runtime-canary-hook.test.mjs > "$ROOT/m11j-preapply-existing-hook-scaffold-test.txt" || exit 32

python3 - <<'PY'
from pathlib import Path
import re
root = Path('sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout')
paths = [
  root/'M11E_EXECUTABLE_PRODUCTION_CANARY_PACKAGE.md',
  root/'M11F_FINAL_APPLY_READINESS_REVIEW.md',
  root/'M11G_R1_REDACTION_VALIDATOR_REPAIR.md',
  root/'M11H_GATEWAY_CONFIG_TOOL_AVAILABILITY.md',
  root/'M11I_GATEWAY_TOOL_SURFACE_RECONCILIATION.md',
  root/'M11J_APPLY_SURFACE_HANDOFF.md',
  root/'m11j-preapply-package-validation.json',
  root/'m11j-preapply-existing-hook-scaffold-test.txt'
]
paths += sorted((root/'apply-package/work-lifecycle-production-canary').glob('**/*'))
patterns = {
  'raw_owner_numeric_id': re.compile(''.join(['849', '520', '3551'])),
  'bot_token_shape': re.compile(r'\b\d{6,12}:[A-Za-z0-9_-]{20,}\b'),
  'auth_header_literal': re.compile(''.join(['Authorization', r'\s*', ':', r'\s*', 'Bearer']), re.I),
  'api_key_assignment': re.compile(r'(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*["\']?[^"\'\s]{8,}'),
  'bearer_token': re.compile(''.join(['Bearer', r'\s+', r'[A-Za-z0-9._~+/-]+=*']), re.I),
  'raw_source_surface': re.compile(''.join(['telegram', ':', 'direct', ':(?!sha256-redacted)']))
}
hits=[]
for p in paths:
    if not p.is_file():
        continue
    text=p.read_text(errors='replace')
    for name,rx in patterns.items():
        for m in rx.finditer(text):
            line=text.count('\n',0,m.start())+1
            hits.append((str(p), line, name))
if hits:
    print('REDACTION_SCAN_FAIL')
    for row in hits:
        print('\t'.join(map(str,row)))
    raise SystemExit(32)
print('REDACTION_SCAN_PASS')
PY

git diff --check || exit 33

echo 'M11J_EXTERNAL_CONTEXT_PREFLIGHT_PASS'
```

## Exact first-class Gateway config patch payload

Use only the first-class Gateway config tool in the approved external context.

Do not run this from shell. Do not translate it into CLI config edits.

```json
{
  "action": "config.patch",
  "patch": {
    "plugins": {
      "load": {
        "paths": [
          "/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package/work-lifecycle-production-canary"
        ]
      },
      "entries": {
        "work-lifecycle-production-canary": {
          "enabled": true,
          "hooks": {
            "timeouts": {
              "before_agent_reply": 1000
            }
          },
          "config": {
            "enabled": true,
            "mode": "production_canary",
            "canaryOwner": "stickbot",
            "canaryMarker": "WORK_LIFECYCLE_M11_CANARY_SMOKE",
            "productionPromotion": false,
            "allowRuntimeSend": false,
            "allowSyntheticReply": false,
            "enforcement": "observe_only_no_short_circuit",
            "evidenceRoot": "sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout"
          }
        }
      }
    }
  },
  "note": "M11 production-canary apply: load work-lifecycle-production-canary before_agent_reply observer; no production promotion; no direct message/provider sends.",
  "continuationMessage": "Verify M11 production canary: plugin registered before_agent_reply, handler returns handled:false, Gateway healthy, no production promotion, M12 NOT_STARTED."
}
```

Approved config/plugin change:

- add the local plugin package path to `plugins.load.paths`
- add/enable `plugins.entries.work-lifecycle-production-canary`
- set plugin mode `production_canary`
- set enforcement `observe_only_no_short_circuit`
- keep `productionPromotion:false`
- keep `allowRuntimeSend:false`
- keep `allowSyntheticReply:false`
- set `before_agent_reply` hook timeout to `1000`

## Restart boundary

The approved assistant-surface boundary did not permit a service restart unless separately approved.

External operator rule:

- If `gateway action="config.patch"` reports that a restart is required to load the plugin path, stop immediately.
- Do not restart automatically from this handoff.
- Classify as `HOLD_RESTART_APPROVAL_REQUIRED` and request separate approval with exact reason:

`M11 production-canary apply requires Gateway restart to load newly configured local work-lifecycle-production-canary plugin path.`

## Post-apply smoke command

Run only after the first-class Gateway config patch succeeds and the plugin is loaded without requiring an unapproved restart.

```bash
set -euo pipefail
cd /home/stickai/.openclaw/workspace
PKG="sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package/work-lifecycle-production-canary"
openclaw plugins inspect work-lifecycle-production-canary --runtime --json > sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11e-post-apply-plugin-inspect.json
node "$PKG/post-apply-smoke.mjs" > sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11e-post-apply-local-smoke.json
```

Required smoke proof:

- runtime inspect shows plugin id `work-lifecycle-production-canary` loaded/enabled, or at minimum no runtime plugin import/config error
- local smoke prints `M11E_POST_APPLY_LOCAL_SYNTHETIC_SMOKE_PASS`
- smoke result has `handled:false`
- smoke result has `sendsMessages:false`
- smoke result has `productionPromotion:false`

## Closeout-delivery validation command

Run only after apply and smoke pass:

```bash
set -euo pipefail
cd /home/stickai/.openclaw/workspace
PKG="sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package/work-lifecycle-production-canary"
node "$PKG/closeout-delivery-validation.mjs" > sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11e-closeout-delivery-validation.json
```

Required closeout proof:

- marker `M11E_CLOSEOUT_DELIVERY_VALIDATION_PASS`
- `runtimeSend:false`
- `messageApiCall:false`
- `closeoutStatus: PASS_APPLY_PACKAGE_READY`

## Rollback package and rollback procedure

Rollback package:

`/home/stickai/.openclaw/workspace/state/work-lifecycle/rollback/m11e-production-canary/openclaw-config-and-plugin-preapply-20260701T141000Z.tar.gz`

SHA256:

`3f68e3ac32ebeb341b65317ec16fec6f72c436ccf35a66fb44ab61049ec46609`

Rollback remains first-class Gateway config apply/restart only. Do not shell-edit live config.

If rollback is required, extract for review:

```bash
set -euo pipefail
TMP_ROLLBACK="/tmp/m11e-production-canary-rollback-20260701T141000Z"
rm -rf "$TMP_ROLLBACK"
mkdir -p "$TMP_ROLLBACK"
tar -xzf /home/stickai/.openclaw/workspace/state/work-lifecycle/rollback/m11e-production-canary/openclaw-config-and-plugin-preapply-20260701T141000Z.tar.gz -C "$TMP_ROLLBACK"
test -s "$TMP_ROLLBACK/openclaw.json"
```

Then use the first-class Gateway tool in the approved external context:

```json
{
  "action": "config.apply",
  "raw": "<exact contents of /tmp/m11e-production-canary-rollback-20260701T141000Z/openclaw.json>",
  "note": "M11E rollback restored pre-apply OpenClaw config from state/work-lifecycle rollback package.",
  "continuationMessage": "Verify M11E rollback: work-lifecycle-production-canary plugin entry/load path absent or disabled, Gateway healthy, M11 apply approval NOT_READY, M12 NOT_STARTED."
}
```

If rollback apply reports restart required, stop and request separate restart approval unless the operator already granted it.

## Hard abort triggers

Abort before config patch if any of these occur:

- current HEAD is not `a96f8c063dd50ee86f5b859b28c59262d0538a38`
- M11E/M11F/M11G-R1/M11H/M11J evidence is missing, dirty, or not PASS/HOLD as expected
- rollback package missing or SHA mismatch
- package validation fails
- scaffold test fails
- redaction scan fails
- `git diff --check` fails
- any config drift outside the approved plugin canary path is detected
- the execution context cannot call first-class `gateway action="config.patch"`
- an exec/CLI config mutation fallback would be needed
- schema paths for `plugins.load.paths` or `plugins.entries.*` are unavailable
- the patch would set `productionPromotion:true`, `allowRuntimeSend:true`, `allowSyntheticReply:true`, or enforcement other than `observe_only_no_short_circuit`
- the patch would edit OpenClaw packaged `dist` files
- the patch would start M12
- the patch would trigger Telegram/runtime send or provider/message API call

Abort after config patch and rollback if any of these occur:

- Gateway health/readiness fails after approved apply
- runtime inspect cannot import the plugin or reports config validation errors
- smoke result returns `handled:true`
- any user-visible message is sent by the plugin
- any provider/message API call is observed
- production promotion is detected
- M12 starts
- closeout validation cannot be written/read back

## Success closeout criteria for external context

Classify `PASS_APPLIED_CANARY` only if all are true:

- first-class Gateway config patch succeeds
- no unapproved restart occurs
- exact plugin config is present and bounded
- post-apply smoke passes
- closeout-delivery validation passes
- handler remains `handled:false`
- no Telegram/runtime/provider send occurred
- no production promotion occurred
- M12 remains `NOT_STARTED`

Classify `FAIL_ROLLED_BACK` only if apply failed and rollback completed successfully.

Classify `FAIL_ROLLBACK_REQUIRED` if apply failed and rollback has not completed.

Classify `HOLD_RESTART_APPROVAL_REQUIRED` if config patch succeeds or partially applies but requires restart to load plugin and restart was not separately approved.

Classify `HOLD_EXTERNAL_GATEWAY_TOOL_CONTEXT_REQUIRED` if the first-class patch tool is still unavailable in the execution context.

## Boundary readback for M11J

During M11J:

- config mutation: `false`
- Gateway mutation: `false`
- plugin registration: `false`
- exec/CLI config patch fallback: `false`
- service restart: `false`
- Telegram/runtime send: `false`
- provider/message API call: `false`
- production apply: `false`
- production promotion: `false`
- M12 start: `false`
- commit/push: `false`

## Carry-forward state

- M11J: `HOLD_EXTERNAL_GATEWAY_TOOL_CONTEXT_REQUIRED`
- Handoff readiness: `PASS_HANDOFF_READY`
- M11 apply from this assistant surface: blocked; do not retry here
- M11 apply from approved external Gateway tool context: handoff ready, requires explicit operator action/approval in that context
- M12: `NOT_STARTED`

## Close statement

M11J closes as `HOLD_EXTERNAL_GATEWAY_TOOL_CONTEXT_REQUIRED` with `PASS_HANDOFF_READY`. The validated M11 production-canary apply can only be executed from an approved OpenClaw/Gateway context where `gateway action="config.patch"` is actually callable. This assistant surface must not retry the apply and must not use exec/CLI config mutation fallback.
