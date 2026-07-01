# M11D Live Insertion-Point Discovery — Work Lifecycle Ledger

Status: `PASS_INSERTION_POINT_IDENTIFIED`
Prepared at: 2026-07-01T13:33:00Z
Updated at: 2026-07-01T13:40:00Z
M11C: `HOLD_LIVE_HOOK_INSERTION_UNSAFE`
M11 apply approval: `NOT_READY`
M12: `NOT_STARTED`

## Executive classification

Required classification: `PASS_INSERTION_POINT_IDENTIFIED`

M11D identified an exact safe disabled-by-default live Gateway/runtime insertion point for the Work Lifecycle canary hook:

- file: `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/get-reply-DGnDV9U-.js`
- source-region marker: `//#region src/auto-reply/reply/get-reply.ts`
- function: `async function getReplyFromConfig(ctx, opts, configOverride)`
- insertion point: existing `before_agent_reply` global hook dispatch, immediately after inline/native/directive handling and immediately before `runPreparedReply(...)`
- approximate dist lines from direct readback: `3875-3900` for the `hasHooks("before_agent_reply")` gate and `runBeforeAgentReply(...)` call; `3912+` for the following `runPreparedReply(...)` call

Why this is safe enough for M11D:

- It is already on the live inbound reply path used by `getReplyFromConfig`.
- It is guarded by `if (!useFastTestBootstrap)` and `hookRunner?.hasHooks("before_agent_reply")`; when no hook is registered, behavior remains unchanged.
- `runBeforeAgentReply` is a claiming hook: first `{ handled: true }` result wins; a disabled/default Work Lifecycle canary can return no result / `{ handled: false }` and preserve behavior.
- It occurs before model/agent reply execution (`runPreparedReply(...)`), making it a bounded accepted-work / before-agent-dispatch checkpoint.
- The hook context includes `agentId`, `sessionKey`, `sessionId`, `workspaceDir`, trigger, channel fields, message provider, and cleaned body; this is enough for a disabled-by-default Work Lifecycle production canary adapter to decide PASS/HOLD without sending messages or mutating runtime config.

M11 production apply approval remains `NOT_READY`; M11D only proves a candidate insertion point. A concrete M11 apply package still needs a separate prepared patch/smoke/rollback package and separate approval.

## Exact files inspected

Files inspected directly during M11D:

1. `/home/stickai/.npm-global/lib/node_modules/openclaw/package.json`
   - Version observed: `2026.5.7`.
   - `bin.openclaw`: `openclaw.mjs`.
   - `main`: `dist/index.js`.
   - package `files` list includes `dist/`, `openclaw.mjs`, docs/scripts/skills, and explicitly excludes `dist/**/*.map`.
2. `/home/stickai/.npm-global/lib/node_modules/openclaw/openclaw.mjs`
   - Launcher surface only; ensures Node version, compile cache, and respawns/imports runtime/CLI entrypoint.
   - Not a bounded lifecycle decision point.
3. `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/index.js`
   - Main package entrypoint imports CLI legacy runner and `library-*.js` when imported as a library.
   - Not a verified channel/runtime lifecycle decision point.
4. `/home/stickai/.npm-global/lib/node_modules/openclaw/docs/gateway/configuration-reference.md`
   - Configuration reference confirms config schema is the field-level authority.
   - Does not document a specific Work Lifecycle runtime insertion point.
5. `src/work-lifecycle/work-runtime-hook-config.ts`
   - M11B disabled-by-default config helper; local scaffold only.
6. `src/work-lifecycle/work-runtime-canary-hook.ts`
   - M11B bounded decision adapter; local scaffold only.
7. `src/work-lifecycle/work-runtime-canary-hook.test.mjs`
   - M11B focused disabled-by-default tests/evidence generator.
8. `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/library-BA_EkDlC.js`
   - Source-region marker: `//#region src/library.ts`.
   - Exports `getReplyFromConfig` via lazy import of `reply.runtime.js`; rejected as insertion point itself but confirms the library path to reply runtime.
9. `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/reply.runtime.js`
   - Re-export wrapper for `reply.runtime-CQ3prhSo.js`.
10. `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/reply.runtime-CQ3prhSo.js`
   - Re-exports `getReplyFromConfig` from `get-reply-DGnDV9U-.js`.
11. `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/get-reply-DGnDV9U-.js`
   - Source-region markers include `src/auto-reply/reply/get-reply.ts`, `message-preprocess-hooks.ts`, `session.ts`, and related reply runtime modules.
   - Verified `getReplyFromConfig(...)` live inbound reply path.
   - Verified `before_agent_reply` existing global hook gate immediately before `runPreparedReply(...)`.
12. `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/hook-runner-global-CCAcWVdN.js`
   - Source-region marker: `src/plugins/hooks.ts`.
   - Defines `runBeforeAgentReply(event, ctx)` as a claiming hook over `before_agent_reply`.
   - Also exposes relevant hook concepts: `before_dispatch`, `reply_dispatch`, `before_tool_call`, `agent_end`, `message_sending`, `message_sent`, etc.
13. `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/internal-hooks-C9TbPRWK.js`
   - Source-region marker: `src/hooks/internal-hooks.ts`.
   - Existing internal events are fire-and-forget observers, not the recommended M11D insertion point.
14. Prior memory note `memory/2026-06-30-ge2-r8-result.md`
   - Identified older dist chunk names for GE2 native command route discovery; useful precedent but not the M11D recommended insertion point.

## Package/runtime entrypoints inspected

| Entry | Evidence | Insertion status |
| --- | --- | --- |
| `openclaw.mjs` | package `bin.openclaw` | rejected: launcher/respawn surface, too broad |
| `dist/index.js` | package `main` | rejected: CLI/library entrypoint, not accepted-work/closeout boundary |
| `dist/library-BA_EkDlC.js` | lazy-loads `reply.runtime.js`, exports `getReplyFromConfig` | accepted as routing evidence, rejected as insertion point itself |
| `dist/reply.runtime.js` / `dist/reply.runtime-CQ3prhSo.js` | re-export chain to `get-reply-DGnDV9U-.js` | accepted as routing evidence, rejected as insertion point itself |
| `dist/get-reply-DGnDV9U-.js` | `getReplyFromConfig`, `before_agent_reply` gate, `runPreparedReply` tail | **recommended insertion point identified** |
| `dist/hook-runner-global-CCAcWVdN.js` | `runBeforeAgentReply`, claiming hook semantics | accepted as hook-runner semantics evidence |
| `dist/cli/run-main.js` | dynamically imported by `dist/index.js` for legacy CLI | rejected: CLI entrypoint, not owner-visible runtime lifecycle boundary |
| GE2 native command dist modules from prior memory (`commands-*`, `bot-*`, `bot-native-commands.runtime-*`) | prior discovery artifact/memory | rejected for M11D: command-specific native route, not general lifecycle enforcement point |

## Candidate insertion points found

### Candidate A — `before_agent_reply` in `getReplyFromConfig` — SELECTED

Evidence:

- file: `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/get-reply-DGnDV9U-.js`
- source-region marker: `//#region src/auto-reply/reply/get-reply.ts`
- function: `async function getReplyFromConfig(ctx, opts, configOverride)`
- approximate dist readback lines: `3875-3900`
- code shape:
  - `if (!useFastTestBootstrap) {`
  - `const { getGlobalHookRunner } = await loadHookRunnerGlobal();`
  - `const hookRunner = getGlobalHookRunner();`
  - `if (hookRunner?.hasHooks("before_agent_reply")) {`
  - `const hookResult = await hookRunner.runBeforeAgentReply({ cleanedBody }, { ...context... });`
  - `if (hookResult?.handled) return hookResult.reply ?? { text: "NO_REPLY" };`
- immediately following path: `return runPreparedReply({ ... })`, approximate dist readback lines `3912+`.

Hook semantics:

- file: `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/hook-runner-global-CCAcWVdN.js`
- source-region marker: `//#region src/plugins/hooks.ts`
- function: `async function runBeforeAgentReply(event, ctx)`
- implementation: `return runClaimingHook("before_agent_reply", event, ctx);`
- comment: first handler returning `{ handled: true }` wins and short-circuits the LLM agent.

Why selected:

- It is an existing live hook boundary, not a new runtime import point.
- It is disabled by default when no hook is registered (`hookRunner?.hasHooks(...)` guard).
- A Work Lifecycle canary hook can be registered later as a plugin/internal hook implementation that returns no handled result unless explicitly enabled/scoped.
- It occurs after command/directive/native inline handling but before agent/model reply generation, giving a bounded accepted-work/before-agent-dispatch checkpoint.
- It does not require Telegram send, provider/message API call, config mutation, restart, production apply, CLI registration, or promotion during discovery.

### Candidate B — `before_tool_call`

Evidence:

- file: `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/hook-runner-global-CCAcWVdN.js`
- function: `async function runBeforeToolCall(event, ctx)`
- semantics: modifying hook can block tool calls with `{ block: true }`.

Rejected for M11D apply package readiness.

Reason: hook-runner function exists, but M11D did not map the exact current packaged runtime call site before concrete tool side effects. This remains useful as a later hardening candidate, not the selected insertion point.

### Candidate C — `reply_dispatch`

Evidence:

- file: `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/hook-runner-global-CCAcWVdN.js`
- function: `async function runReplyDispatch(event, ctx)`
- semantics: claiming hook can own reply dispatch.

Rejected for Work Lifecycle canary start.

Reason: it is closer to dispatch/side-effect behavior than the desired accepted-work checkpoint and was not mapped to an exact call site in this discovery pass.

## Rejected insertion points and reasons

### `openclaw.mjs`

Rejected.

Reason: package launcher/respawn surface. Importing Work Lifecycle there would be global process behavior, not a bounded canary hook. It would risk live Gateway behavior change before config gating.

### `dist/index.js`

Rejected.

Reason: package CLI/library entrypoint. It imports CLI runner or library dependencies but is not an accepted-work, tool, closeout, reply-dispatch, or notification lifecycle boundary.

### `dist/cli/run-main.js`

Rejected.

Reason: CLI surface. M11D forbids CLI registration and seeks runtime canary enforcement, not CLI handling.

### Prior GE2 native command route files

Rejected for Work Lifecycle insertion.

Reason: prior GE2 files were used to discover `/ge2` native command matching/handling. That route is plugin/command-specific and does not cover general owner-visible lifecycle-managed work.

### `hooks.internal.entries.*` config surface alone

Rejected as a live insertion point.

Reason: M11B proved this is a schema-backed config surface, but config alone does not execute Work Lifecycle decisions unless a live runtime caller is verified.

## Final recommended insertion point

Recommended insertion point: existing `before_agent_reply` global hook in `getReplyFromConfig`.

Exact path:

1. package entry `dist/index.js` exports `getReplyFromConfig` from `dist/library-BA_EkDlC.js`.
2. `dist/library-BA_EkDlC.js` lazy-loads `dist/reply.runtime.js` for `getReplyFromConfig`.
3. `dist/reply.runtime.js` re-exports `dist/reply.runtime-CQ3prhSo.js`.
4. `dist/reply.runtime-CQ3prhSo.js` re-exports `getReplyFromConfig` from `dist/get-reply-DGnDV9U-.js`.
5. `dist/get-reply-DGnDV9U-.js` runs the `before_agent_reply` hook immediately before `runPreparedReply(...)`.

Recommended future implementation shape:

- Register a Work Lifecycle canary handler on the existing `before_agent_reply` hook.
- Handler must default to disabled/noop.
- Handler must only act when both global hook registration and Work Lifecycle canary config are explicitly enabled.
- Handler must scope to the production canary lane only.
- Handler must return no result / `{ handled: false }` for normal traffic and for disabled config.
- Handler may return `{ handled: true, reply: { text: "..." } }` only for explicitly enabled canary HOLD cases after separate apply approval.

## Can M11 apply package now be prepared?

Yes, but only as the next planning artifact; not applied.

M11D proves an insertion point exists, so a future M11 apply package can be prepared around the existing `before_agent_reply` hook path. It still requires a separate patch/apply/rollback/smoke package and separate owner approval before any production-affecting apply.

M11 apply approval remains `NOT_READY`.

## Completed async dist inventory evidence

The broader packaged `dist/` inventory/search command completed successfully after the initial M11D closeout.

Raw evidence artifact:

- path: `sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout/M11D_DIST_DISCOVERY_RAW.txt`
- SHA256: `969a8f4df704d3d58b0f1d903b3612f934a795e355032f878554155f7b373c9d`
- line count: `1203`
- completion marker: `M11D_DIST_DISCOVERY_RAW_WRITTEN`

Key supporting findings from raw inventory:

- package root: `/home/stickai/.npm-global/lib/node_modules/openclaw`
- package version: `2026.5.7`
- package main: `dist/index.js`
- package bin: `openclaw.mjs`
- `DIST_MAP_COUNT 0`
- `DIST_SRC_DIR_EXISTS False`
- `hooks.internal` / config support appears in `dist/runtime-schema-CeZMTU8i.js` around schema paths including `hooks.internal`, `hooks.internal.enabled`, `hooks.internal.entries`, and `hooks.internal.load`.
- internal hook loading/runtime paths appear in `dist/server-startup-post-attach-BfICbOVy.js`, `dist/loader-Ce6u83c4.js`, and `dist/internal-hooks-C9TbPRWK.js`.
- inbound/message lifecycle internal hook emissions appear in `dist/monitor-ClXG8xsZ.js`, `dist/get-reply-DGnDV9U-.js`, `dist/delivery-DEQ0qbCk.js`, and `dist/deliver-DW6FPE_u.js`.
- tool-side-effect hardening path exists through `dist/pi-tool-definition-adapter-BTdk51zC.js` and `dist/pi-tools.before-tool-call--tH0cf3r.js`, but this remains rejected for M11D because the selected insertion point is accepted-work / before-agent-dispatch and the tool path would be a later hardening candidate.
- reply-dispatch/delivery paths appear in `dist/run-delivery.runtime-hWnxkRAr.js`, `dist/reply-dispatch-runtime-D741PTo5.js`, `dist/monitor-ClXG8xsZ.js`, channel runtimes, and delivery chunks, but they remain rejected for this canary start because they are closer to outbound side effects than the selected accepted-work checkpoint.

Effect on classification:

- No downgrade.
- No runtime mutation occurred.
- M11D remains `PASS_INSERTION_POINT_IDENTIFIED` based on the existing `before_agent_reply` boundary in `getReplyFromConfig`.

## Safety-boundary readback

- production apply: false
- enforcement enablement: false
- live Gateway behavior change: false
- config mutation: false
- service restart: false
- Telegram/runtime send: false
- provider/message API call: false
- CLI registration: false
- production promotion: false
- M11 apply request: false
- M12 start: false

## Terminal closeout

M11D classification: `PASS_INSERTION_POINT_IDENTIFIED`

M11 apply approval: `NOT_READY`

M12: `NOT_STARTED`

No runtime code was modified. Discovery only.
