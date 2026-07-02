# Protected Gateway Config Control Surface Notebook

Purpose: troubleshooting, repair, and deployment runbook for OpenClaw work that must modify Gateway config paths blocked from the agent-facing `gateway config.patch` surface, especially plugin loader/entry paths such as `plugins.load.paths` and `plugins.entries.<pluginId>.*`.

Created after M11 production-canary rollout, which closed `PASS_APPLIED_CANARY`.

## Non-negotiable rule

If `gateway config.patch` rejects protected paths, that is a safety boundary, not a bug to bypass.

Do **not** fall back to shell editing `~/.openclaw/openclaw.json`, OpenClaw dist edits, or raw CLI mutation. Use an authorized owner/admin control surface, exact-scope approval, redacted evidence, restart-hold handling, and post-restart validation.

## Correct control path

Preferred order:

1. **Prepare package and rollback first**
   - Build the plugin/package/config payload in workspace evidence.
   - Validate package locally.
   - Prepare rollback artifact before mutation.
   - Record exact approved paths and forbidden paths.

2. **Try first-class agent-facing config tool only for unprotected paths**
   - `gateway.config.patch` is correct for normal allowed config.
   - If it rejects protected paths such as `plugins.load.paths` or `plugins.entries.*`, classify as `HOLD_ADMIN_ACTION_REQUIRED` or equivalent.
   - Do not retry the same protected patch through agent-facing wrappers.

3. **Use authorized owner/admin Control UI surface for protected paths**
   - OpenClaw Control UI Config page is a JS app, not an HTML form.
   - Advanced Config Apply uses Gateway WebSocket RPC:
     - `config.get`
     - `config.schema`
     - `config.apply`
     - `config.patch`
   - The Advanced Config Apply path calls:
     - `client.request("config.apply", { raw, baseHash, sessionKey })`
   - For protected config work, use owner/admin authorization and the same Control UI/Gateway WebSocket control-plane path, not a file edit fallback.

4. **Apply full config only with exact diff guard**
   - Fetch current config and hash with `config.get`.
   - Build full next config from current config.
   - Modify only the approved subtree.
   - Expand created parent objects into approved leaf paths before checking scope.
   - Abort before `config.apply` if any changed leaf is outside the approved list.
   - Record exact before/after JSON diff.
   - Call `config.apply` with current `baseHash`.

5. **Handle restart sentinel as a hard hold**
   - If apply emits restart sentinel, close/request `HOLD_RESTART_REQUIRED`.
   - Do not restart automatically unless the owner explicitly approves restart.
   - Use first-class `gateway.restart`, not `openclaw gateway stop && start`.

6. **Validate after restart before PASS**
   - Confirm Gateway healthy / config readback.
   - Confirm protected path is active after restart.
   - Run preserved smoke tests.
   - Prove no short-circuit, send, provider call, synthetic reply, or promotion.
   - Prove downstream milestone remains not started when required.
   - Only then close `PASS_*`.

## Credential and approval handling

Required:

- Owner approval for exact mutation scope.
- Gateway operator/admin authorization for protected paths.
- Separate owner approval for restart if required.
- Approval-capable channel/context for shell/Node validation commands.

Forbidden:

- Do not echo, log, commit, preserve, or paste raw gateway tokens.
- Do not put raw tokens into artifacts, memory, GitHub, command output, or notebooks.
- Prefer environment variables or authenticated Control UI session state; redact logs.
- Do not preserve raw chat IDs, account IDs, message IDs, auth headers, SecretRefs, or tokens in GitHub-bound evidence.

Approval syntax lesson:

- `/approve ... allow-once` must be sent as the actual approval command, not quoted inside explanatory prose or a code block.
- `allow-once` covers only one command. Any corrected retry needs a fresh approval.
- Do not claim a previous approval covers a new command, even if it is a bugfix retry.

## Browser and Chrome access runbook

Reminder to future Stickbot: **you do have Chrome access paths, but they can be brittle and may need troubleshooting. Do not stop after the first browser-tool failure.**

Known routes:

1. **OpenClaw browser tool**
   - Try `browser status`, `profiles`, `tabs`, and `start`.
   - Use the `browser-automation` skill for multi-step UI control.
   - Existing user profile attach can fail if Chrome is not running with remote debugging.

2. **WSL-owned/headless Chromium CDP**
   - A WSL-launched headless Chromium can expose CDP at `127.0.0.1:18800`.
   - Direct CDP scripts can open Control UI, inspect pages, and take screenshots.
   - Python Playwright may not be installed; direct Node/browser CDP can still work.

3. **Windows desktop Chrome via WSL interop**
   - Chrome may exist at `/mnt/c/Program Files/Google/Chrome/Application/chrome.exe`.
   - PowerShell may exist at `/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe` even if `powershell.exe` is not on PATH.
   - `cmd.exe` may exist at `/mnt/c/Windows/System32/cmd.exe`.
   - Launching an already-running normal Chrome may print `Opening in existing browser session` and ignore `--remote-debugging-port`; in that case CDP will not appear.
   - To attach to user-profile Chrome, Chrome must have been launched originally with remote debugging or the user must restart/open a dedicated Chrome instance with CDP enabled.

Browser lessons from M11:

- OpenClaw browser auto-detect failure does **not** mean no browser is available.
- Raw mode in Config page can be disabled (`Raw mode disabled (snapshot cannot safely round-trip raw text)`), so UI automation may need JS/app RPC inspection.
- Control UI is a bundled JS app; inspect the bundle for method names when forms are absent.
- Do not use visible Chrome with user auth as a secret extraction path. Use it only as an authorized surface; never scrape or print tokens.

## Exact protected-config workflow template

Use this skeleton for future protected config applies.

### 0. Define the scope

Write down:

- approved paths
- forbidden paths
- payload source
- rollback artifact
- validation gates
- final closeout states

Example M11 approved paths:

- `plugins.load.paths`
- `plugins.entries.work-lifecycle-production-canary.enabled`
- `plugins.entries.work-lifecycle-production-canary.hooks.*`
- `plugins.entries.work-lifecycle-production-canary.config.*`

Example M11 forbidden scope:

- broad `plugins.load` parent mutation unless proven only materializing `plugins.load.paths`
- broad `plugins.entries` mutation
- broad `plugins.entries.*` mutation
- route/provider/auth/memory/Gateway-wide config mutation
- exec/CLI fallback
- OpenClaw dist edit
- service restart without approval
- Telegram/runtime send
- provider/message API call
- production promotion
- next milestone start

### 1. Preflight

- Verify current git head if evidence branch matters.
- Verify package files exist.
- Verify rollback archive exists and SHA matches.
- Verify downstream milestone is not started.
- Validate package/scaffold/redaction/boundary.
- Save redacted config snapshot for the target subtree.

### 2. Build next config safely

- Fetch config with `config.get` and save `baseHash`.
- Clone current config.
- Apply only the intended subtree.
- Keep unrelated existing config intact.
- Use exact plugin path.
- Use fail-closed config flags:
  - `allowRuntimeSend:false`
  - `allowSyntheticReply:false`
  - `productionPromotion:false`
  - observe-only/no-short-circuit enforcement where applicable.

### 3. Diff guard

Do not compare only top-level parent paths. Parent-object creation can create false positives such as `plugins.load` or `plugins.entries.<id>`.

Instead:

- recursively expand object diffs to leaf paths;
- allow only exact approved leaf paths/families;
- abort before apply if anything else appears;
- record the leaf path list.

M11 bug fixed here: the first guard aborted because it treated newly-created parent containers as unapproved paths. Correct fix was leaf expansion plus exact approved families.

### 4. Apply through authorized control surface

- Use authenticated Gateway WebSocket/Control UI RPC `config.apply` with `{ raw, baseHash, sessionKey }`.
- Do not use `gateway config.patch` once protected-path rejection is known.
- Do not shell-edit config.
- Do not modify OpenClaw dist.
- Record apply result and readback.

### 5. Restart handling

If apply emits a restart sentinel:

- write a restart-hold artifact;
- stop with `HOLD_RESTART_REQUIRED`;
- ask for separate restart approval;
- use first-class `gateway.restart` when approved;
- after restart, resume validation.

M11 bug fixed here: config readback passed but plugin activation still required restart; do not run final smoke or claim PASS until after approved restart and validation.

### 6. Post-restart validation

Run preserved validation commands in approval-capable context.

Required proofs for plugin-style canary:

- Gateway/config readback sees plugin path + entry active.
- Smoke proves hook registration and decision behavior.
- Handler returns `handled:false`.
- No runtime/send/provider/message API call.
- No synthetic reply.
- No production promotion.
- Downstream milestone remains not started.
- Validation logs are written.

M11 final validation output:

- `M11E_POST_APPLY_LOCAL_SYNTHETIC_SMOKE_PASS`
- `M11E_CLOSEOUT_DELIVERY_VALIDATION_PASS`
- `M11_POST_RESTART_CONFIG_AND_BOUNDARY_READBACK`
- final: `PASS_APPLIED_CANARY`

## Bugs found and fixed during M11

### 1. Protected-path rejection misclassified as missing tool path

Symptom:

- Early apply path assumed lack of callable `gateway config.patch` was the primary blocker.
- Later `gateway config.patch` was callable but correctly rejected protected plugin paths.

Fix:

- Separate **tool exposure** from **authorization boundary**.
- Final classification: protected path requires owner/admin Control UI authority.

Lesson:

- A callable tool is not necessarily authorized for all config paths.
- Protected path rejection before mutation is a PASS of the safety boundary.

### 2. Repeated agent-facing patch attempts were unsafe/noisy

Symptom:

- It was tempting to retry `gateway config.patch` after tool surface became callable.

Fix:

- Locked out further agent-facing retries for plugin loader paths.
- Moved to admin-authorized control surface.

Lesson:

- Once protected-path rejection is proven, do not keep pushing the same surface.

### 3. Redaction validator self-match false positive

Symptom:

- Redaction scanner flagged examples in an evidence document because the raw pattern appeared in the scanner/test text itself.

Fix:

- Built sentinel strings from split fragments in the document/test.

Lesson:

- Evidence docs can self-trigger scanners. Avoid raw private identifier patterns even in examples.

### 4. Brittle M12 state check

Symptom:

- Text matching for `M12 NOT_STARTED` was brittle and risked false positives/negatives.

Fix:

- Replaced with semantic sidecar-state check / run-file absence check.

Lesson:

- For milestone state, inspect durable state artifacts, not prose.

### 5. Browser auto-detect failure caused premature blocker

Symptom:

- Initial browser tool path failed, leading to a temporary “browser unavailable” hold.

Fix:

- Recovered via WSL/headless Chromium CDP and direct CDP scripts.

Lesson:

- Browser access has multiple layers: OpenClaw browser tool, WSL Chromium, Windows Chrome, direct CDP. Try them in order before declaring impossible.

### 6. Windows Chrome CDP launch ambiguity

Symptom:

- Launching Windows Chrome from WSL opened in existing browser session and ignored remote-debugging flags; CDP fetch failed.

Fix:

- Diagnosed via launch log `Opening in existing browser session`.

Lesson:

- Existing Chrome sessions may swallow launch args. Need a dedicated Chrome instance/user-data-dir or user-launched remote-debugging Chrome for CDP attach.

### 7. `powershell.exe` PATH assumption was wrong

Symptom:

- `powershell.exe` returned `command not found` from gateway shell.

Fix:

- Probe explicit WSL interop paths like `/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe` and `/mnt/c/Windows/System32/cmd.exe`.

Lesson:

- Windows interop may exist even when Windows executables are not on PATH.

### 8. Control UI has no HTML form

Symptom:

- Browser/page introspection found no forms and only bundled app resources.

Fix:

- Inspected JS bundle and found WebSocket RPC calls.

Lesson:

- For modern JS Control UI, search bundle for method names (`config.get`, `config.apply`, `config.patch`, `baseHash`) rather than looking for forms.

### 9. Raw mode disabled

Symptom:

- Config page reported raw mode disabled because the snapshot could not safely round-trip raw text.

Fix:

- Used structured Control UI/Gateway RPC shape with full config raw generated from parsed config and hash.

Lesson:

- UI raw editor availability is not guaranteed. The authorized admin path may still exist as `config.apply` RPC.

### 10. `node:ws` is not a Node builtin

Symptom:

- First admin WS apply attempt failed before config call: `ERR_UNKNOWN_BUILTIN_MODULE: node:ws`.

Fix:

- Use Node 22 global `WebSocket` or an actual installed package import; do not import `node:ws`.

Lesson:

- `node:` prefix only works for real builtins. Verify transport dependency before approval-gated mutation commands.

### 11. Diff guard flagged parent containers as unapproved

Symptom:

- Second apply attempt aborted with `ABORT_UNAPPROVED_CONFIG_PATHS plugins.entries.work-lifecycle-production-canary,plugins.load`.

Fix:

- Expand object diffs to leaf paths and restrict to exact approved leaf families.

Lesson:

- Parent materialization is not necessarily broad mutation, but must be proven by leaf expansion before apply.

### 12. Approval command embedded in prose did not execute

Symptom:

- A quoted `/approve ...` line inside an explanatory message did not resume the pending command.

Fix:

- Ask for approval as a standalone command, first token.

Lesson:

- Treat approval UX literally. Do not assume a quoted approval is active.

### 13. Heartbeat cannot approve exec

Symptom:

- Post-restart validation attempted from heartbeat failed: `Exec approval is required, but Heartbeat does not support chat exec approvals`.

Fix:

- Wrote a validation hold artifact, then resumed from an approval-capable async context.

Lesson:

- Restart continuations may arrive through heartbeat. If validation needs `exec`, use Web UI/terminal/Telegram approval-capable context or pre-approved safe validation job.

### 14. Config apply result can be huge and contain redacted sensitive fields

Symptom:

- `config.apply` returned large config output with many redacted fields.

Fix:

- Preserve compact summaries and redacted artifacts, not raw secrets. Avoid committing huge raw config dumps unless deliberately scrubbed.

Lesson:

- Prefer targeted readbacks and compact extraction. Evidence should prove scope without preserving sensitive unrelated config.

### 15. Package-era closeout validator was not sufficient final proof

Symptom:

- Preserved `closeout-delivery-validation.mjs` proved M11E package-era closeout, not the full post-restart applied state.

Fix:

- Added post-restart config/boundary readback validation.

Lesson:

- Reuse preserved validators, but add new validation gates for newly changed state.

## Classification decision tree

- `ABORT_UNAPPROVED_CONFIG_PATHS` — diff expansion includes anything outside approved leaves; abort before apply.
- `HOLD_ADMIN_ACTION_REQUIRED` — protected path requires authorized Control UI/admin apply.
- `HOLD_RESTART_REQUIRED` — apply succeeded/readback passed but restart sentinel emitted.
- `HOLD_VALIDATION_EXEC_APPROVAL_UNAVAILABLE` — restart continuation cannot execute validation due channel/tool approval limits.
- `FAIL_ROLLBACK_REQUIRED` — apply failed and rollback has not completed.
- `FAIL_ROLLED_BACK` — apply failed and rollback succeeded.
- `PASS_APPLIED_CANARY` — apply, owner-approved restart if required, smoke, closeout validation, boundary proof, and downstream-not-started proof all pass.

## M11 final evidence map

- Apply package: `M11E_EXECUTABLE_PRODUCTION_CANARY_PACKAGE.md`
- External/admin authority handoff: `M11L_FINAL_EXTERNAL_APPLY_HANDOFF.md`
- Protected-path authority: `M11M_PROTECTED_PATH_APPLY_AUTHORITY.md`
- Restart hold: `M11N_ADMIN_APPLY_RESTART_HOLD.md`
- Heartbeat validation hold: `M11O_POST_RESTART_VALIDATION_HOLD_EXEC_APPROVAL_UNAVAILABLE.md`
- Final closeout: `M11P_PASS_APPLIED_CANARY_CLOSEOUT.md`
- Apply diff: `m11-admin-apply-approved-json-diff.json`
- Apply result: `m11-admin-apply-result.json`
- Apply log: `cdp-control-ui-admin-apply/m11_admin_ws_apply.log`
- Validation logs: `m11-post-restart-validation/`
- Final sidecar run: `state/work-lifecycle/runs/work_20260702T012600Z_lifecycle_ledger_m11p.json`
- Final sidecar event: `state/work-lifecycle/events/work_20260702T012600Z_lifecycle_ledger_m11p.jsonl`

## Future default behavior

When a task requires protected Gateway config mutation:

1. Stop and define exact scope.
2. Prepare rollback and validation.
3. Use agent-facing tools only until protected boundary appears.
4. Move to owner/admin Control UI/Gateway RPC authority.
5. Keep secrets redacted.
6. Use leaf-path diff guard.
7. Apply with `baseHash`.
8. Treat restart sentinel as hold.
9. Validate after restart.
10. Close with evidence, not confidence.
