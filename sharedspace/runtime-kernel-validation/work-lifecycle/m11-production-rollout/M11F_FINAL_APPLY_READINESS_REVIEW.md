# M11F Final Production-Canary Apply Readiness Review — READ-ONLY

Terminal classification: `PASS_READY_FOR_OPERATOR_APPLY_APPROVAL`

M11F reviewed the preserved M11E production-canary apply package for currency, boundedness, rollback readiness, and executable apply-readiness. This is a review-only milestone. It is **not** an M11 production apply approval request and it does **not** start M12.

## Current branch/head

- Branch: `stickbot/v3-selected-model-persona-injection`
- HEAD: `97153d28410aa3f9ce9f606356d81654692c350d`
- HEAD subject: `feat(work-lifecycle): preserve M11E production canary package`

## Git status readback

Read-only `git status --short` showed broad pre-existing workspace noise outside the M11E package area. The M11E preserved package paths were not reported as modified after the preservation commit.

The tracked-preservation readback confirmed these files are present at `HEAD`:

- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/M11E_EXECUTABLE_PRODUCTION_CANARY_PACKAGE.md`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package/work-lifecycle-production-canary/closeout-delivery-validation.mjs`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package/work-lifecycle-production-canary/index.mjs`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package/work-lifecycle-production-canary/openclaw.plugin.json`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package/work-lifecycle-production-canary/package.json`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package/work-lifecycle-production-canary/post-apply-smoke.mjs`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package/work-lifecycle-production-canary/validate-package.mjs`

Additional unrelated dirty/untracked workspace files do not change the M11F package-readiness classification because M11F is not committing/pushing or applying anything.

## Package files reviewed

Package root:

`sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package/work-lifecycle-production-canary/`

Files reviewed:

- `package.json`
- `openclaw.plugin.json`
- `index.mjs`
- `validate-package.mjs`
- `post-apply-smoke.mjs`
- `closeout-delivery-validation.mjs`

## Package manifest/readme/config patch readback

Package identity and manifest are concrete:

- npm package name: `@stickbot/openclaw-work-lifecycle-production-canary`
- plugin id: `work-lifecycle-production-canary`
- version: `0.0.0-m11e-prep`
- activation: `onStartup: true`
- OpenClaw extension entry: `./index.mjs`
- declared compatibility: `2026.5.7`

Prepared config patch remains concrete and bounded. Future approved apply adds only:

- `plugins.load.paths` entry for the local package path
- `plugins.entries.work-lifecycle-production-canary` with:
  - `enabled: true`
  - `mode: "production_canary"`
  - `productionPromotion: false`
  - `allowRuntimeSend: false`
  - `allowSyntheticReply: false`
  - `enforcement: "observe_only_no_short_circuit"`
  - `before_agent_reply` timeout `1000`

## Runtime package boundary review

`index.mjs` remains bounded:

- registers only `api.on('before_agent_reply', handler, { priority: -100, timeoutMs: 1000 })`
- evaluates the canary marker `WORK_LIFECYCLE_M11_CANARY_SMOKE`
- always returns `handled:false`
- has boundary fields false for mutation, external send, runtime send, provider/message API call, production promotion, and M12 start
- rejects config if `productionPromotion`, `allowRuntimeSend`, or `allowSyntheticReply` are anything other than `false`
- uses `observe_only_no_short_circuit`

## Redaction scan readback

The broad redaction scan stopped with code `7` because it matched a literal denied auth-header sentinel in `validate-package.mjs`.

Manual inspection classified this as a **safe denied-sentinel string**, not a credential or raw auth header. M11G-R1 supersedes this example by constructing denied sentinels from split fragments at runtime so repo-bound evidence does not contain raw auth-header-shaped text.

No actual credential, raw Telegram chat id, auth-header value, provider auth credential, or provider key was identified in the reviewed package/artifact content.

## Rollback command

Rollback is concrete and state-only. Before any future config mutation, create the rollback package:

```bash
set -euo pipefail
cd /home/stickai/.openclaw/workspace
ROLLBACK_DIR="/home/stickai/.openclaw/workspace/state/work-lifecycle/rollback/m11e-production-canary"
ROLLBACK_TGZ="$ROLLBACK_DIR/openclaw-config-and-plugin-preapply-20260701T141000Z.tar.gz"
mkdir -p "$ROLLBACK_DIR"
tar -czf "$ROLLBACK_TGZ" \
  -C /home/stickai/.openclaw openclaw.json \
  -C /home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package work-lifecycle-production-canary
sha256sum "$ROLLBACK_TGZ" > "$ROLLBACK_TGZ.sha256"
test -s "$ROLLBACK_TGZ"
test -s "$ROLLBACK_TGZ.sha256"
```

Rollback package path:

`/home/stickai/.openclaw/workspace/state/work-lifecycle/rollback/m11e-production-canary/openclaw-config-and-plugin-preapply-20260701T141000Z.tar.gz`

Rollback hash sidecar:

`/home/stickai/.openclaw/workspace/state/work-lifecycle/rollback/m11e-production-canary/openclaw-config-and-plugin-preapply-20260701T141000Z.tar.gz.sha256`

Rollback procedure remains first-class Gateway config apply/restart only; do not shell-edit live config.

## Pre-apply validation command

Before any future approved apply, run:

```bash
set -euo pipefail
cd /home/stickai/.openclaw/workspace
PKG="sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package/work-lifecycle-production-canary"
node --check "$PKG/index.mjs"
node "$PKG/validate-package.mjs" > sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11e-package-validation.json
node --experimental-strip-types --test src/work-lifecycle/work-runtime-canary-hook.test.mjs > sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11e-existing-hook-scaffold-test.txt
```

Required first-class readiness lookups before future apply:

- `gateway.config.schema.lookup(path="plugins.load")` must show `plugins.load.paths` array exists.
- `gateway.config.schema.lookup(path="plugins.entries.*")` must show `enabled`, `hooks`, and `config` are valid entry fields.
- `gateway.config.get(path="plugins")` must confirm no `plugins.allow` allowlist exists, or that it includes `work-lifecycle-production-canary`; otherwise abort and prepare a revised package.

## Apply command

Only after separate future M11 production-canary apply approval, first create the rollback package above, then use the first-class Gateway config patch:

- `gateway.config.patch`
  - `patch`: exact JSON payload from `M11E_EXECUTABLE_PRODUCTION_CANARY_PACKAGE.md` under **Exact config diff**
  - `note`: `M11 production-canary apply: load work-lifecycle-production-canary before_agent_reply observer; no production promotion; no direct message/provider sends.`
  - `continuationMessage`: `Verify M11 production canary: plugin registered before_agent_reply, handler returns handled:false, Gateway healthy, no production promotion, M12 NOT_STARTED.`

Then run first-class restart only if required to load the new plugin path:

- `gateway.restart`
  - `reason`: `M11 production-canary apply: load newly configured local work-lifecycle-production-canary plugin path.`
  - `continuationMessage`: `Run M11E post-apply smoke and closeout validation; do not start M12.`

## Post-apply smoke command

These commands do not send Telegram messages and do not call provider/message APIs:

```bash
set -euo pipefail
cd /home/stickai/.openclaw/workspace
PKG="sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package/work-lifecycle-production-canary"
openclaw plugins inspect work-lifecycle-production-canary --runtime --json > sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11e-post-apply-plugin-inspect.json
node "$PKG/post-apply-smoke.mjs" > sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11e-post-apply-local-smoke.json
```

Pass criteria:

- runtime inspect shows plugin id `work-lifecycle-production-canary` loaded/enabled
- runtime inspect shows `before_agent_reply` registration, or at minimum no import/config error
- local smoke prints `M11E_POST_APPLY_LOCAL_SYNTHETIC_SMOKE_PASS`
- smoke result has `handled:false`, `sendsMessages:false`, and `productionPromotion:false`

## Closeout-delivery validation command

```bash
set -euo pipefail
cd /home/stickai/.openclaw/workspace
PKG="sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package/work-lifecycle-production-canary"
node "$PKG/closeout-delivery-validation.mjs" > sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11e-closeout-delivery-validation.json
```

This validates durable local closeout evidence only. It must not send Telegram/runtime messages and must not call provider/message APIs.

## Hard abort triggers

Abort before config patch/restart if any of these are true:

- rollback package creation fails, is empty, or hash sidecar is missing
- `plugins.allow` exists and does not include `work-lifecycle-production-canary`
- `plugins.load.paths` already contains a conflicting path for this plugin id
- any current plugin entry already uses `work-lifecycle-production-canary` with a different config
- `node --check` or `validate-package.mjs` fails
- M11 apply approval is still `NOT_READY` at actual apply time
- any requested command would edit OpenClaw packaged `dist/` files
- any requested command would send Telegram/runtime messages or call provider/message APIs
- any requested command would set `productionPromotion:true`, `allowRuntimeSend:true`, `allowSyntheticReply:true`, or an enforcement mode other than `observe_only_no_short_circuit`
- any requested command would start M12
- Gateway config schema for `plugins.load` or `plugins.entries.*` no longer matches this package

Abort after config patch/restart and immediately rollback if any of these are true:

- Gateway fails health/readiness after the approved restart
- runtime inspect cannot import the plugin or reports config validation errors
- hook smoke returns `handled:true`
- any user-visible message is sent by the plugin or any provider/message API call is observed
- M11 closeout evidence cannot be written/read back

## Safety-boundary readback

During M11F:

- production apply executed: `false`
- enforcement enabled: `false`
- live Gateway config mutation: `false`
- live plugin registration: `false`
- OpenClaw packaged `dist/` edits: `false`
- service restart: `false`
- Telegram/runtime send: `false`
- provider/message API call: `false`
- production promotion: `false`
- M12 start: `false`
- commit/push: `false`
- M11 apply request: `false`

## Carry-forward state

- M11E package preservation: `PASS_PUSHED`
- M11E: `PASS_APPLY_PACKAGE_READY`
- M11F: `PASS_READY_FOR_OPERATOR_APPLY_APPROVAL`
- M11 apply approval: `NOT_READY`
- M12: `NOT_STARTED`

## Close statement

M11F is closed as `PASS_READY_FOR_OPERATOR_APPLY_APPROVAL`. The preserved M11E package is current at branch head, bounded to observe-only/no-short-circuit behavior, rollback-ready, and has concrete validation, apply, smoke, and closeout commands. No production mutation occurred during M11F, and this closeout does not request M11 apply approval.
