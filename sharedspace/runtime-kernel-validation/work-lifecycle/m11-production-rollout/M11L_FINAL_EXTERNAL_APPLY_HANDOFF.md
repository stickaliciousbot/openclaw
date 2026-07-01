# M11L Final External Apply Executor Handoff — NO APPLY

Final classification: `HOLD_EXTERNAL_GATEWAY_PATCH_TOOL_REQUIRED`

Handoff status: `HANDOFF_READY_FOR_EXTERNAL_EXECUTOR`

M12 status: `NOT_STARTED`

M11L finalizes the M11 production-canary apply handoff after M11K-R2 closed `HOLD_GATEWAY_PATCH_TOOL_NOT_EXPOSED`. This artifact is for an external approved OpenClaw/Gateway execution context where the first-class Gateway mutation tool is actually callable.

No config mutation, Gateway mutation, plugin registration, exec/CLI fallback, service restart, Telegram/runtime send, provider/message API call, production apply, production promotion, M12 start, commit, or push occurred during M11L.

## Final current state

- M11K-R2: `HOLD_GATEWAY_PATCH_TOOL_NOT_EXPOSED`
- Preflight: `PASS`
- Apply: `NOT_RUN`
- Config/plugin change applied: none
- Gateway/service restart: none
- Post-apply smoke: not run because apply did not occur
- Closeout-delivery validation: not run because apply did not occur
- M12: `NOT_STARTED`

Reason:

- The first-class Gateway mutation tool surface `gateway` with `action: "config.patch"` is not exposed in this assistant execution surface.
- Exec/CLI config mutation fallback remains forbidden.
- Therefore M11 cannot progress to applied canary from this surface.

## Supersession / correction chain

- M11I conclusion is superseded: schema lookup was observable, but callable `config.patch` mutation was not available in this assistant surface.
- M11J remains the external-context handoff basis.
- M11K-R1 repaired M11J preflight gates and preserved the repair.
- M11L is the final external executor handoff and no-retry lockout for this assistant surface.

## Current preserved head

Use preserved head:

`7673ffe97c3a22723645c61bb9e712f7b8bdaa8a`

This head includes M11K-R1 repair preservation.

## Latest M11K-R2 preflight results

M11K-R2 preflight completed `PASS` before apply was held.

Verified:

- HEAD: `7673ffe97c3a22723645c61bb9e712f7b8bdaa8a`
- M11E: `PASS`
- M11F: `PASS`
- M11G-R1: `PASS`
- M11H: `PASS`
- M11J: `PASS_HANDOFF_READY`
- M11K-R1: `PASS_LOCAL_VALIDATED`
- Package validation: `PASS`
- Scaffold test: `PASS`
- Redaction scan: `PASS`
- Semantic M12 state check: `PASS`
- `git diff --check`: `PASS`
- Boundary check: `PASS`

Validated package hash readback:

- `package.json`: `0b27f9d7a16fa2c064cb04a621f6971e3c28dff5fc671a18a2bb30c3d9f443e3`
- `openclaw.plugin.json`: `61fc6c2566ad9816dcf783c818a396c65e6cbb1322b3251b04780034a3825fcb`
- `index.mjs`: `f878f1b31bf6a478bd13006eef531e18062d9c5a7464dc8d9120626b02da1e74`
- `validate-package.mjs`: `5f8adb9c5b9772c5b003d4672ba2702c164a6bed776d958100224b523966271f`
- `post-apply-smoke.mjs`: `359104c6b664ecabd90313b65dcc7c9f305cf462ce52e2440b97012c4e57ba11`
- `closeout-delivery-validation.mjs`: `8311e4ffade19cf91342c9948b1f45dd23d968dd635958bd5af78680bd1ddde5`

## Required external executor

Required executor:

- an approved OpenClaw/Gateway tool context where the first-class Gateway mutation tool is exposed and callable
- tool: `gateway`
- action: `config.patch`
- no shell/exec/CLI config mutation fallback

If the external context cannot call `gateway` with `action: "config.patch"`, stop and classify:

`HOLD_EXTERNAL_GATEWAY_PATCH_TOOL_REQUIRED`

## Preserved patch payload location

Primary source:

- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/M11E_EXECUTABLE_PRODUCTION_CANARY_PACKAGE.md`
- Section: `Exact future gateway.config.patch payload`

Handoff source:

- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/M11J_APPLY_SURFACE_HANDOFF.md`
- Section: `Exact first-class Gateway config patch payload`

Use only the preserved M11E production-canary patch payload.

## Exact required external tool call

Use a first-class Gateway tool call equivalent to:

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
- configure mode `production_canary`
- configure enforcement `observe_only_no_short_circuit`
- keep `productionPromotion:false`
- keep `allowRuntimeSend:false`
- keep `allowSyntheticReply:false`
- set `before_agent_reply` hook timeout to `1000`

## Rollback package

Rollback package path:

`/home/stickai/.openclaw/workspace/state/work-lifecycle/rollback/m11e-production-canary/openclaw-config-and-plugin-preapply-20260701T141000Z.tar.gz`

Rollback package SHA256:

`3f68e3ac32ebeb341b65317ec16fec6f72c436ccf35a66fb44ab61049ec46609`

Rollback must use first-class Gateway config apply in the approved external context. Do not shell-edit live config.

## Restart rule

Do not restart Gateway automatically.

- If the first-class config patch succeeds and smoke passes without restart, close `PASS_APPLIED_CANARY`.
- If the patch reports restart required, or smoke proves the plugin is not active because Gateway must reload, close `HOLD_RESTART_REQUIRED` with evidence.
- Restart requires separate explicit approval.

## Post-apply smoke command

Run only after first-class config patch returns success and no unapproved restart is required:

```bash
set -euo pipefail
cd /home/stickai/.openclaw/workspace
PKG="sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package/work-lifecycle-production-canary"
openclaw plugins inspect work-lifecycle-production-canary --runtime --json > sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11e-post-apply-plugin-inspect.json
node "$PKG/post-apply-smoke.mjs" > sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11e-post-apply-local-smoke.json
```

Required smoke proof:

- runtime inspect shows plugin id `work-lifecycle-production-canary` loaded/enabled, or at minimum no runtime plugin import/config error
- local smoke marker `M11E_POST_APPLY_LOCAL_SYNTHETIC_SMOKE_PASS`
- `handled:false`
- `sendsMessages:false`
- `productionPromotion:false`

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
- closeout status remains `PASS_APPLY_PACKAGE_READY`

## Required external closeout report

External executor must report:

- exact config/plugin change applied
- Gateway/service restart status
- rollback package path and SHA
- post-apply smoke result
- closeout-delivery validation result
- proof handler remains `handled:false`
- proof no Telegram/runtime/provider send occurred
- proof no production promotion occurred
- M12 remains `NOT_STARTED`

## Hard abort triggers

Abort before config patch if any are true:

- current head is not `7673ffe97c3a22723645c61bb9e712f7b8bdaa8a` or a later explicitly preserved M11 handoff head
- M11E/M11F/M11G-R1/M11H/M11J/M11K-R1 evidence is missing, dirty, or not PASS/HOLD as expected
- rollback package missing or SHA mismatch
- package validation fails
- scaffold test fails
- redaction scan fails
- semantic M12 state check fails
- `git diff --check` fails
- config drift outside approved plugin canary path is detected
- external context cannot call first-class `gateway action="config.patch"`
- exec/CLI config mutation fallback would be needed
- patch would set `productionPromotion:true`, `allowRuntimeSend:true`, `allowSyntheticReply:true`, or enforcement other than `observe_only_no_short_circuit`
- patch would edit OpenClaw packaged `dist` files
- patch would start M12
- patch would send Telegram/runtime messages or call provider/message APIs

Abort after config patch and rollback if any are true:

- Gateway health/readiness fails after approved apply
- runtime inspect cannot import the plugin or reports config validation errors
- smoke result returns `handled:true`
- any user-visible message is sent by the plugin
- any provider/message API call is observed
- production promotion is detected
- M12 starts
- closeout validation cannot be written/read back

## Valid external classifications

- `PASS_APPLIED_CANARY`: first-class config patch, smoke, and closeout validation pass; no unapproved restart; handler remains `handled:false`; no send/promotion; M12 remains `NOT_STARTED`.
- `HOLD_RESTART_REQUIRED`: patch reports restart required or smoke proves plugin inactive pending reload; restart not approved.
- `FAIL_ROLLED_BACK`: apply failed and rollback succeeded.
- `FAIL_ROLLBACK_REQUIRED`: apply failed and rollback has not completed.
- `ABORT`: hard abort fires before apply.
- `HOLD_EXTERNAL_GATEWAY_PATCH_TOOL_REQUIRED`: first-class patch tool unavailable in executor context.

## Assistant-surface lockout

This assistant surface must not retry M11 apply again.

Allowed from this surface after M11L:

- preserve evidence when explicitly approved
- summarize status
- prepare handoffs
- wait for external executor result

Forbidden from this surface:

- config mutation
- Gateway mutation
- plugin registration
- exec/CLI config fallback
- service restart
- production apply
- production promotion
- M12 start before external M11 result

## M12 gate

M12 remains `NOT_STARTED`.

Do not start M12 until external M11 apply closes one of:

- `PASS_APPLIED_CANARY`
- `FAIL_ROLLED_BACK`
- `ABORT`
- `HOLD` with preserved evidence

## Boundary readback for M11L

During M11L:

- config mutation: `false`
- Gateway mutation: `false`
- plugin registration: `false`
- exec/CLI fallback: `false`
- service restart: `false`
- Telegram/runtime send: `false`
- provider/message API call: `false`
- production apply: `false`
- production promotion: `false`
- M12 start: `false`
- commit/push: `false`

## Close statement

M11L closes as `HOLD_EXTERNAL_GATEWAY_PATCH_TOOL_REQUIRED` and `HANDOFF_READY_FOR_EXTERNAL_EXECUTOR`. The M11 production-canary apply cannot proceed from this assistant surface, but the exact external first-class Gateway tool payload, rollback package, preflight expectations, smoke validation, closeout validation, restart rule, and abort criteria are preserved here for an approved external executor.
