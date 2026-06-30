# GE2 Implementation, Diagnose, and Repair Notebook — From Scratch Path

Final promoted classification: `GE2_NATIVE_COMMAND_SURFACE_PROMOTED_PUSH_BLOCKED_HANDOFF_PRESERVED`

This notebook is the cleaned-up, from-scratch operator/developer guide for getting GE2 working properly as a native `/ge2` command surface across Telegram and OpenClaw WebUI/Control UI. It condenses the R0–R13 execution ledger into an implementation path, diagnosis ladder, repair decisions, and promotion evidence.

It supersedes the stale working-state headers in:

- `sharedspace/runtime-kernel-validation/ge2/GE2_DIAGNOSE_AND_REPAIR_NOTEBOOK_20260630.md`
- `sharedspace/runtime-kernel-validation/ge2/GE2_CURRENT_NOTEBOOK_20260630.md`

Those files remain useful as historical trace ledgers.

---

## 1. Non-negotiable constraints

- Do not retry cron closeout apply from the GE2 repair path.
- Do not claim GE2 live PASS unless `/ge2` is visible in the live command surface and dispatches through the native handler.
- Do not treat hook logs, local imports, or plugin-manager visibility as live Gateway proof.
- Do not live-smoke `/ge2` while it is absent from `commands.list`; invisible command text can fall through to model/chat handling.
- Do not hardcode `/ge2` as display-only in `commands.list`.
- Do not create placeholder success.
- Preserve authorization: `/ge2` requires auth.
- Preserve unrelated commands: `pair`, `dreaming`, `phone`, `voice`.
- Preserve fake-negative: fake GE2 command must remain absent.
- Avoid duplicate `/ge2` registrations.
- Snapshot, manifest, reverser, and health gates are mandatory before any production mutation.
- Promotion is a separate documentation/evidence act after P1/P2/P3 proof; it must not mutate routes, cache, artifact-memory, runtime-authority, model/provider routes, or Gateway config.

---

## 2. Target architecture

GE2 is a deterministic native command surface. The command text is `/ge2`, but the business logic is not embedded in Telegram or WebUI adapters. Both channels should converge on the same router/dispatcher/runtime.

### Runtime kit

Workspace source:

- `ge2-native-runtime/src/ge2_command_router.mjs`
- `ge2-native-runtime/src/ge2_dispatcher.mjs`
- `ge2-native-runtime/src/ge2_runtime.mjs`
- `ge2-native-runtime/src/ge2_ledger.mjs`
- `ge2-native-runtime/src/ge2_artifacts.mjs`
- `ge2-native-runtime/src/ge2_milestones.mjs`
- `ge2-native-runtime/src/ge2_snapshot.mjs`

Supported commands:

- `/ge2 help`
- `/ge2 status`
- `/ge2 run <task>`
- `/ge2 status <run_id>`
- `/ge2 artifacts <run_id>`
- `/ge2 cancel <run_id>`

Durable state:

- `state/ge2-native/runs/`
- `state/ge2-native/runs.index.json`
- `state/ge2-native/*.jsonl`
- `state/ge2-native/artifacts/<run_id>/`

### Command adapter shape

The native command descriptor must be visible to both listing and matching paths:

- name: `ge2`
- aliases/text aliases: `/ge2`
- source/plugin: `plugin`
- scope: `both`
- auth: required
- handler: routes to `ge2_command_router` + `ge2_dispatcher`

### Hook/plugin layer

Repository/workspace paths:

- Hook: `hooks/ge2-register/handler.js`
- Plugin source: `plugins/ge2-command/index.mjs`
- Plugin manifest: `plugins/ge2-command/openclaw.plugin.json`
- Managed extension path in production: `/home/stickai/.openclaw/extensions/ge2-command/`

The hook/plugin layer can bootstrap registration, but hook selftests alone are not authoritative. The public Gateway command list and real inbound dispatch path are authoritative.

---

## 3. Channel entrypoints that must work

### Telegram direct chat

Real inbound route proven in R11:

1. Telegram Bot API update enters Gateway.
2. `createTelegramBot` / `registerTelegramNativeCommands` registers bot command catalog.
3. Gateway calls `bot.handleUpdate`.
4. Telegram adapter extracts command body.
5. `matchPluginCommand(commandBody)` matches `/ge2`.
6. `executePluginCommand(...)` invokes GE2 native handler.
7. Reply returns through Telegram delivery path.
8. Durable ledger/artifact writes occur under `state/ge2-native`.

Important installed-dist modules observed:

- `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/bot-Ds7bwqAK.js`
- `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/bot-native-commands.runtime-OmS7iYqz.js`
- `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/commands-D2qp4St4.js`

### OpenClaw WebUI / Control UI

Real inbound route proven in R11:

1. WebUI sends Gateway RPC/chat turn.
2. Dispatch/get-reply command routing normalizes command body.
3. `commands-handlers.runtime` calls `handlePluginCommand` / `matchPluginCommand(commandBodyNormalized)`.
4. `executePluginCommand(...)` invokes GE2 native handler.
5. Chat transcript/live session receives the command response.
6. Durable ledger/artifact writes occur under `state/ge2-native`.

Important installed-dist modules observed:

- `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/commands-handlers.runtime-DlESKC_s.js`
- `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/commands-D2qp4St4.js`

---

## 4. Diagnosis ladder

Use this ladder in order. Do not skip levels or overclaim.

### Level 0 — Source/runtime files exist

Check that GE2 runtime source exists and imports locally.

Pass means only: source files exist and parse/import.

### Level 1 — Hook/plugin registration selftest

Check hook/plugin selftest and `sharedspace/ge2-register.log`.

Pass means only: hook/plugin can report registration success in its own context.

It does **not** prove public command visibility or live dispatch.

### Level 2 — Public command visibility

Run live command-list checks for Telegram and WebUI/Webchat surfaces.

Required pass gates:

- Telegram `/ge2` count exactly `1`
- WebUI/Webchat `/ge2` count exactly `1`
- fake command count `0`
- `pair`, `dreaming`, `phone`, `voice` preserved
- no duplicate `/ge2`

If this fails, do not send `/ge2` live.

### Level 3 — P1 installed-dist matcher/handler harness

Use installed production dist modules locally to invoke the matcher/handler path.

Pass means: installed matcher/handler can execute `/ge2 help/status/run/status/artifacts` and returns `continueAgent:false` without model/chat fallthrough.

It does **not** prove channel adapters or real inbound Gateway.

### Level 4 — P2 adapter fixture proof

Exercise Telegram/WebUI adapter fixture paths with controlled synthetic inputs.

Pass means: adapter-shaped requests reach the GE2 handler and produce durable ledger/artifact output.

It does **not** prove real inbound Gateway/UI traffic.

### Level 5 — P3 real inbound proof

Operator/user sends real commands through Telegram and WebUI/Control UI.

Required commands:

- `/ge2 help`
- `/ge2 status`
- `/ge2 run <task>`
- `/ge2 status <run_id>`
- `/ge2 artifacts <run_id>`

Pass requires live responses plus durable ledger/artifact/hash proof.

---

## 5. R0–R7 issue and fix chain

### R0/R1 — hook/plugin success did not equal live visibility

Symptoms:

- hook log showed registration success
- plugin-manager could report GE2 plugin metadata
- public `commands.list` still omitted `/ge2`

Learning:

- hook/plugin context was not the same authority as the public command registry used by Gateway command list and matchers.

### R2 — authoritative public command-list path identified

Public RPC path:

- `server-methods-Dw6hzI_j.js`
- `commandsHandlers["commands.list"]`
- `buildCommandsListResult()`
- `buildPluginCommandEntries()`
- `listPluginCommands()`
- command registry storage in installed command/types chunks

Loss point was registry/module-realm/lifecycle, not auth or filtering.

### R3/R4 — singleton/builder bridges failed

Singleton/effective-registry bridge and command-list builder bridge did not expose `/ge2` live. These repairs were insufficient because the durable lifecycle path still rebuilt/restored plugin command state without GE2.

### R5 — native command handler installed but lifecycle cleared it

R5 installed a native handler in the command chunk. Local P1-style validation worked, but live `commands.list` still omitted `/ge2` after PID turnover.

Learning:

- ad-hoc top-level registration can be cleared/rebuilt by plugin loader lifecycle.

### R6 — registry lifecycle target proven

R6 proved the patched command chunk was imported and the real public list/match paths used the expected modules. The issue was loader lifecycle/cache restoration.

### R7 — lifecycle registration fixed visibility

R7 targeted the plugin loader lifecycle path:

- installed file: `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/loader-Bfm_uDYG.js`
- reason: loader lifecycle clears/restores/registers plugin commands and registry state
- requirement: seed `/ge2` into both `pluginCommands` and `registry.commands` idempotently

R7 patch characteristics:

- idempotent registration
- exactly one `/ge2`
- fake absent
- `pair`, `dreaming`, `phone`, `voice` preserved
- handler backed by GE2 router/dispatcher/runtime
- reverser present

Important R7 artifacts:

- `sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/r7_loader_lifecycle_exact_target_and_repair_plan.md`
- `sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/install_manifest_ge2_r7_lifecycle_20260630T0812Z.json`
- `sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/reverser_ge2_r7_lifecycle_20260630T0812Z.mjs`

---

## 6. R8–R11 proof ladder

### R8 — P1 help/status native execution proof

Classification: `GE2_R8_HELP_STATUS_NATIVE_EXECUTION_PASS_RUN_PENDING`

Validated installed-dist matcher/handler path for native help/status execution.

### R9 — P1 run/status/artifacts proof

Classification: `GE2_R9_NATIVE_HANDLER_RUN_STATUS_ARTIFACTS_PASS_P2_PENDING`

Validated durable run lifecycle, status lookup, artifact listing, and artifact SHA.

Reference artifact:

- `sharedspace/runtime-kernel-validation/ge2/ge2_r9_native_run_lifecycle_proof/GE2_R9_NATIVE_HANDLER_RUN_STATUS_ARTIFACTS_CORRECTED_REPORT_20260630.md`

### R10 — P2 Telegram/WebUI adapter fixture proof

Classification: `GE2_R10_ADAPTER_FIXTURE_TELEGRAM_WEBUI_HELP_STATUS_RUN_PASS_P3_PENDING`

Validated adapter-shaped Telegram and WebUI fixture paths.

Reference artifact:

- `sharedspace/runtime-kernel-validation/ge2/ge2_r10_adapter_fixture_proof/GE2_R10_FINAL_OWNER_REQUIRED_REPORT_20260630.md`

### R11 — P3 real inbound Telegram + WebUI proof

Classification: `GE2_R11_REAL_INBOUND_GATEWAY_TELEGRAM_WEBUI_PASS_PROMOTION_PENDING`

Real inbound Gateway proof passed on both Telegram and WebUI/Control UI.

Telegram run:

- run id: `ge2-20260630101117-1fa6ed4d`
- artifact SHA256: `602031961d623f07130515a5ee7236021618909de6ec1e04268687d9205fda5e`

WebUI run:

- run id: `ge2-20260630102318-ae4b5942`
- artifact SHA256: `fea53254aa478892b55405c9db686245ec24707fed003bd9ea3e2be125f2d584`

Reference artifact:

- `sharedspace/runtime-kernel-validation/ge2/ge2_r11_real_inbound_gateway_smoke/GE2_R11_REAL_INBOUND_GATEWAY_TELEGRAM_WEBUI_PASS_PROMOTION_PENDING_20260630.md`

---

## 7. R12/R13 promotion and handoff

### R12 promotion-readiness packet

Classification: `GE2_R12_PROMOTION_READINESS_PACKET_READY`

Packet:

- `sharedspace/runtime-kernel-validation/ge2/ge2_r12_promotion_readiness_packet/GE2_R12_PROMOTION_READINESS_PACKET_READY_20260630.md`

Evidence manifest:

- `sharedspace/runtime-kernel-validation/ge2/ge2_r12_promotion_readiness_packet/r12_evidence.json`

Restore checklist:

- `sharedspace/runtime-kernel-validation/ge2/ge2_r12_promotion_readiness_packet/restore-checklist.md`

DR bundle:

- `sharedspace/disaster-recovery/ge2-r12-promotion-readiness-20260630/ge2-r12-promotion-readiness-20260630.tar.gz`
- SHA256: `474408c1ad4c4850ed21ded2c2231fc1e1e668fc4a4995d29a594e1b1c915c2d`

No-secrets scan: PASS.

### R13 promotion

Final amended classification:

`GE2_NATIVE_COMMAND_SURFACE_PROMOTED_PUSH_BLOCKED_HANDOFF_PRESERVED`

Promotion record:

- `sharedspace/runtime-kernel-validation/ge2/ge2_r13_promotion/GE2_NATIVE_COMMAND_SURFACE_PROMOTED_20260630.md`

Hard-stop verification:

- `sharedspace/runtime-kernel-validation/ge2/ge2_r13_promotion/GE2_NATIVE_COMMAND_SURFACE_PROMOTED_PUSH_BLOCKED_HANDOFF_PRESERVED_20260630.md`
- `sharedspace/runtime-kernel-validation/ge2/ge2_r13_promotion/hardstop-push-blocked-handoff-preserved-verification.json`

R13 handoff bundle:

- `sharedspace/disaster-recovery/ge2-r13-promotion-20260630/ge2-r13-promotion-20260630.tar.gz`
- SHA256: `b7509076f20dc5dc906a7343c92bb8d0bb5dee1d894242abbe2460b19c7a0f8c`

Push/commit initially blocked by broad pre-existing unrelated dirty tree; handoff preserved in the R13 bundle.

---

## 8. Proper from-scratch implementation checklist

Use this checklist when implementing GE2 cleanly in source rather than patching bundled dist files.

1. Add or verify GE2 runtime source under `ge2-native-runtime/src/`.
2. Add a small plugin/hook registration layer:
   - `plugins/ge2-command/index.mjs`
   - `plugins/ge2-command/openclaw.plugin.json`
   - `hooks/ge2-register/handler.js`
3. Register `/ge2` through the same authoritative registry lifecycle used by durable plugin commands.
4. Ensure registration writes both public listing and command matching state.
5. Make registration idempotent.
6. Preserve auth (`requireAuth:true`).
7. Preserve existing commands and fake-negative tests.
8. Validate in layers:
   - source/import
   - hook/plugin selftest
   - live `commands.list` visibility
   - P1 installed-dist matcher/handler
   - P2 Telegram/WebUI adapter fixtures
   - P3 real inbound Telegram/WebUI
9. Write durable ledger/artifact proof for `/ge2 run`.
10. Build DR bundle and no-secrets scan.
11. Promote only after R12-style packet gates pass and owner approval is explicit.

---

## 9. Validation commands and expected gates

Do not rely on any single command. The pass gate is the combined state.

Expected live visibility summary:

```json
{
  "telegram": { "ge2Count": 1, "fakeCount": 0 },
  "webchat": { "ge2Count": 1, "fakeCount": 0 },
  "preserved": ["pair", "dreaming", "phone", "voice"]
}
```

Expected health:

- Gateway running
- connectivity OK
- admin-capable

Expected `/ge2 run` proof:

- run ledger created
- status reaches `completed`
- milestones count `7`
- artifacts count `1`
- errors count `0`
- artifact SHA recorded and reproducible

---

## 10. Rollback and recovery

Use R12 restore checklist first:

- `sharedspace/runtime-kernel-validation/ge2/ge2_r12_promotion_readiness_packet/restore-checklist.md`

Important reverser:

- `sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/reverser_ge2_r7_lifecycle_20260630T0812Z.mjs`

Rollback is not automatic just because a later smoke/harness fails. Roll back only when health, command visibility, duplicate command, auth, or delivery safety gates fail and owner approval/rollback conditions are satisfied.

---

## 11. Durable lessons

- Hook success is not public command-surface proof.
- `commands.list` visibility is necessary before live command smoke.
- P1, P2, and P3 are distinct and must not be collapsed.
- Registry lifecycle is the durable authority; ad-hoc command insertion can disappear.
- Synthetic adapter tests do not replace real inbound Gateway tests.
- Promotion is documentation/evidence state, not a reason to mutate runtime code.
- Git push should use selective staging from a dirty workspace; never mix unrelated dirty files into a production evidence commit.
- DR bundles must exclude raw traces with secret-like values; include redacted copies plus no-secrets scan output.

---

## 12. Current final state

GE2 `/ge2` is promoted/durable with handoff preserved.

Final classification:

`GE2_NATIVE_COMMAND_SURFACE_PROMOTED_PUSH_BLOCKED_HANDOFF_PRESERVED`

Cron closeout retry remains a separate owner-gated task and must still respect quiet-success watcher/report-required delivery semantics.
