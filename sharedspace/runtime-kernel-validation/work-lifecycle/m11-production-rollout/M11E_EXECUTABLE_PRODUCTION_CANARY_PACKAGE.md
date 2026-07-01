# M11E Executable Production-Canary Apply Package — PREP ONLY

Terminal classification: `PASS_APPLY_PACKAGE_READY`

This package is concrete and reviewable, but it has **not** been applied. M11 apply approval remains `NOT_READY`. M12 remains `NOT_STARTED`.

## Scope and boundary

- Milestone: Work Lifecycle Ledger `M11E`
- Mode: production-canary apply package preparation only
- Production apply executed in M11E: `false`
- Live Gateway behavior changed in M11E: `false`
- Config mutation in M11E: `false`
- Service restart in M11E: `false`
- Telegram/runtime send in M11E: `false`
- Provider/message API call in M11E: `false`
- CLI registration in M11E: `false`
- Production promotion in M11E: `false`

## Verified insertion point used

- File: `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/get-reply-DGnDV9U-.js`
- Source-region: `src/auto-reply/reply/get-reply.ts`
- Function: `getReplyFromConfig(ctx, opts, configOverride)`
- Existing hook: `before_agent_reply`
- Runtime handling: `hookRunner.runBeforeAgentReply({ cleanedBody }, ctx)` runs before `runPreparedReply(...)`; only `hookResult?.handled === true` short-circuits the model reply.
- Safety property: if no hook is registered, there is no behavior change. If this M11E plugin is registered, its prepared canary contract still returns `handled:false` and never sends directly.

## Exact apply mode

`production_canary` / `observe_only_no_short_circuit`.

The canary package registers a plugin `before_agent_reply` handler, but the prepared handler is deliberately non-authoritative:

- It returns `{ handled: false, reason }` for every path.
- It does not return a synthetic reply.
- It does not call a messaging/provider API.
- It does not mutate config, memory, ledger state, routes, auth, or provider selection.
- It recognizes the marker `WORK_LIFECYCLE_M11_CANARY_SMOKE` only as a bounded smoke marker and still does not short-circuit.

This is production canary because the hook can be loaded by the live Gateway for bounded observation and runtime-registration validation. It is not production promotion because it does not enforce general traffic, does not alter model routing, and does not become authoritative for Work Lifecycle transitions.

## Exact proposed hook registration mechanism

Use a local native OpenClaw plugin loaded through `plugins.load.paths`, not a direct edit to OpenClaw `dist/` files.

Prepared plugin root:

`/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package/work-lifecycle-production-canary`

Prepared runtime file:

`/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package/work-lifecycle-production-canary/index.mjs`

Mechanism:

1. Plugin manifest declares id `work-lifecycle-production-canary` and `activation.onStartup: true`.
2. Runtime entry exports a native plugin object.
3. `register(api)` calls:
   - `api.on("before_agent_reply", handler, { priority: -100, timeoutMs: 1000 })`
4. Handler evaluates the canary config and always returns `handled:false`.
5. Because the verified insertion point only short-circuits on `handled:true`, disabled/no-op behavior remains safe.

## Exact config diff

Current relevant config has `plugins.entries` for `duckduckgo`, `openai`, `google`, `ollama`, and `webwright`, with no persisted `plugins.load.paths` and no `plugins.allow` allowlist found in the retrieved config. The future approved apply adds only the following plugin load path and plugin entry.

```diff
 plugins:
+  load:
+    paths:
+      - "/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package/work-lifecycle-production-canary"
   entries:
+    work-lifecycle-production-canary:
+      enabled: true
+      hooks:
+        timeouts:
+          before_agent_reply: 1000
+      config:
+        enabled: true
+        mode: "production_canary"
+        canaryOwner: "stickbot"
+        canaryMarker: "WORK_LIFECYCLE_M11_CANARY_SMOKE"
+        productionPromotion: false
+        allowRuntimeSend: false
+        allowSyntheticReply: false
+        enforcement: "observe_only_no_short_circuit"
+        evidenceRoot: "sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout"
```

Exact future `gateway.config.patch` payload, to run only after separate M11 production-canary apply approval:

```json
{
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
}
```

## Exact files expected to change

### Written by M11E prep now

- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/M11E_EXECUTABLE_PRODUCTION_CANARY_PACKAGE.md`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package/work-lifecycle-production-canary/package.json`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package/work-lifecycle-production-canary/openclaw.plugin.json`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package/work-lifecycle-production-canary/index.mjs`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package/work-lifecycle-production-canary/validate-package.mjs`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package/work-lifecycle-production-canary/post-apply-smoke.mjs`
- `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package/work-lifecycle-production-canary/closeout-delivery-validation.mjs`
- `state/work-lifecycle/runs/work_20260701T141000Z_lifecycle_ledger_m11e.json`
- `state/work-lifecycle/events/work_20260701T141000Z_lifecycle_ledger_m11e.jsonl`

### Expected to change during a future approved apply only

- `/home/stickai/.openclaw/openclaw.json` via first-class `gateway.config.patch`
- Gateway runtime process after first-class `gateway.restart`, if restart is required to load the new plugin path

No OpenClaw packaged `dist/` file is expected to change.

## Exact backup/rollback package path

Future approved apply must create this backup before config patch/restart:

`/home/stickai/.openclaw/workspace/state/work-lifecycle/rollback/m11e-production-canary/openclaw-config-and-plugin-preapply-20260701T141000Z.tar.gz`

Hash sidecar:

`/home/stickai/.openclaw/workspace/state/work-lifecycle/rollback/m11e-production-canary/openclaw-config-and-plugin-preapply-20260701T141000Z.tar.gz.sha256`

This rollback package stays under `state/` because it may contain the live OpenClaw config with secrets. It must not be copied into GitHub-bound/sharedspace evidence.

## Concrete rollback package creation command

Future approved apply must run this before any config mutation:

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

## Concrete rollback command

Use first-class Gateway config apply/restart, not shell editing of config.

1. Extract the rollback package for review:

```bash
set -euo pipefail
TMP_ROLLBACK="/tmp/m11e-production-canary-rollback-20260701T141000Z"
rm -rf "$TMP_ROLLBACK"
mkdir -p "$TMP_ROLLBACK"
tar -xzf /home/stickai/.openclaw/workspace/state/work-lifecycle/rollback/m11e-production-canary/openclaw-config-and-plugin-preapply-20260701T141000Z.tar.gz -C "$TMP_ROLLBACK"
test -s "$TMP_ROLLBACK/openclaw.json"
```

2. Then perform the rollback with the first-class OpenClaw Gateway tool:

- `gateway.config.apply`
  - `raw`: exact contents of `/tmp/m11e-production-canary-rollback-20260701T141000Z/openclaw.json`
  - `note`: `M11E rollback restored pre-apply OpenClaw config from state/work-lifecycle rollback package.`
  - `continuationMessage`: `Verify M11E rollback: work-lifecycle-production-canary plugin entry/load path absent or disabled, Gateway healthy, M11 apply approval NOT_READY, M12 NOT_STARTED.`

3. If the apply tool reports restart required or Gateway health requires it, run first-class `gateway.restart` with reason:

`M11E rollback: unload work-lifecycle-production-canary plugin and restore pre-apply Gateway config.`

## Concrete pre-apply validation commands

Run all of these before future apply. Abort on first failure.

```bash
set -euo pipefail
cd /home/stickai/.openclaw/workspace
PKG="sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package/work-lifecycle-production-canary"
node --check "$PKG/index.mjs"
node "$PKG/validate-package.mjs" > sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11e-package-validation.json
node --experimental-strip-types --test src/work-lifecycle/work-runtime-canary-hook.test.mjs > sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11e-existing-hook-scaffold-test.txt
```

First-class schema/readiness lookups that must also pass before future apply:

- `gateway.config.schema.lookup(path="plugins.load")` must show `plugins.load.paths` array exists.
- `gateway.config.schema.lookup(path="plugins.entries.*")` must show `enabled`, `hooks`, and `config` are valid entry fields.
- `gateway.config.get(path="plugins")` must confirm no `plugins.allow` allowlist exists, or if it exists it already includes `work-lifecycle-production-canary`; otherwise abort and produce a new package revision.

## Concrete apply command

Only after separate M11 apply approval, perform the rollback package creation command above, then run this first-class config patch:

- `gateway.config.patch`
  - `patch`: the exact JSON payload in **Exact config diff** above
  - `note`: `M11 production-canary apply: load work-lifecycle-production-canary before_agent_reply observer; no production promotion; no direct message/provider sends.`
  - `continuationMessage`: `Verify M11 production canary: plugin registered before_agent_reply, handler returns handled:false, Gateway healthy, no production promotion, M12 NOT_STARTED.`

Then run first-class restart only if required to load the new plugin path:

- `gateway.restart`
  - `reason`: `M11 production-canary apply: load newly configured local work-lifecycle-production-canary plugin path.`
  - `continuationMessage`: `Run M11E post-apply smoke and closeout validation; do not start M12.`

## Concrete post-apply smoke commands

These commands do not send Telegram messages and do not call provider/message APIs.

```bash
set -euo pipefail
cd /home/stickai/.openclaw/workspace
PKG="sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package/work-lifecycle-production-canary"
openclaw plugins inspect work-lifecycle-production-canary --runtime --json > sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11e-post-apply-plugin-inspect.json
node "$PKG/post-apply-smoke.mjs" > sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11e-post-apply-local-smoke.json
```

Pass criteria:

- Runtime inspect shows plugin id `work-lifecycle-production-canary` loaded/enabled.
- Runtime inspect shows hook capability/registration for `before_agent_reply`, or at minimum no runtime plugin import/config error.
- Local smoke prints `M11E_POST_APPLY_LOCAL_SYNTHETIC_SMOKE_PASS`.
- Smoke result has `handled:false`, `sendsMessages:false`, and `productionPromotion:false`.

## Concrete closeout-delivery validation command

```bash
set -euo pipefail
cd /home/stickai/.openclaw/workspace
PKG="sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package/work-lifecycle-production-canary"
node "$PKG/closeout-delivery-validation.mjs" > sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11e-closeout-delivery-validation.json
```

This validates durable local closeout evidence only. It must not send a Telegram/runtime message and must not call a provider/message API.

## Hard abort triggers

Abort before config patch/restart if any of these are true:

- Rollback package creation fails, is empty, or hash sidecar is missing.
- `plugins.allow` exists and does not include `work-lifecycle-production-canary`.
- `plugins.load.paths` already contains a conflicting path for this plugin id.
- Any current plugin entry already uses `work-lifecycle-production-canary` with a different config.
- `node --check` or `validate-package.mjs` fails.
- M11 apply approval is still `NOT_READY` at actual apply time.
- Any requested command would edit OpenClaw packaged `dist/` files.
- Any requested command would send Telegram/runtime messages or call provider/message APIs.
- Any requested command would set `productionPromotion:true`, `allowRuntimeSend:true`, `allowSyntheticReply:true`, or an enforcement mode other than `observe_only_no_short_circuit`.
- Any requested command would start M12.
- Gateway config schema for `plugins.load` or `plugins.entries.*` no longer matches this package.

Abort after config patch/restart and immediately rollback if any of these are true:

- Gateway fails health/readiness after the approved restart.
- Runtime inspect cannot import the plugin or reports config validation errors.
- Hook smoke returns `handled:true`.
- Any user-visible message is sent by the plugin or any provider/message API call is observed.
- M11 closeout evidence cannot be written/read back.

## Expected evidence paths

- Package artifact: `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/M11E_EXECUTABLE_PRODUCTION_CANARY_PACKAGE.md`
- Plugin package root: `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/apply-package/work-lifecycle-production-canary/`
- Pre-apply validation output: `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11e-package-validation.json`
- Existing scaffold test output: `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11e-existing-hook-scaffold-test.txt`
- Post-apply runtime inspect: `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11e-post-apply-plugin-inspect.json`
- Post-apply local smoke: `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11e-post-apply-local-smoke.json`
- Closeout delivery validation: `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/m11e-closeout-delivery-validation.json`
- Sidecar run: `state/work-lifecycle/runs/work_20260701T141000Z_lifecycle_ledger_m11e.json`
- Sidecar events: `state/work-lifecycle/events/work_20260701T141000Z_lifecycle_ledger_m11e.jsonl`
- Rollback package: `state/work-lifecycle/rollback/m11e-production-canary/openclaw-config-and-plugin-preapply-20260701T141000Z.tar.gz`
- Rollback hash: `state/work-lifecycle/rollback/m11e-production-canary/openclaw-config-and-plugin-preapply-20260701T141000Z.tar.gz.sha256`

## Safety-boundary readback

- M11E did not apply the production canary.
- M11E did not mutate config.
- M11E did not restart Gateway.
- M11E did not register the plugin in live Gateway.
- M11E did not edit packaged OpenClaw runtime files.
- M11E did not send Telegram/runtime messages.
- M11E did not call provider/message APIs.
- M11E did not start M12.
- M11 apply approval remains `NOT_READY`.

## Why disabled/no-hook behavior remains safe

The verified runtime only changes behavior when `hookRunner.hasHooks("before_agent_reply")` is true and the hook result has `handled:true`. With no registered hook, execution continues directly to `runPreparedReply(...)` as before. With this prepared plugin registered, the handler still returns `handled:false`; therefore the existing reply path remains authoritative and no synthetic answer or silence is injected.

## Why this is production canary, not production promotion

- Canary is limited to loading one local plugin and one `before_agent_reply` observer.
- The observer is explicitly `observe_only_no_short_circuit`.
- The config asserts `productionPromotion:false`.
- No default model, route, auth, memory, command, tool, message, or channel policy is promoted.
- No M12 work starts from this package.
- Any future apply still requires separate owner approval after this `PASS_APPLY_PACKAGE_READY` closeout.
