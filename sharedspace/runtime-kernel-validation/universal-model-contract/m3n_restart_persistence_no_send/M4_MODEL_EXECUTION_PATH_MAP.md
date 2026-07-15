# M4 Model Execution Path Map

Status: PASS_M4_MODEL_EXECUTION_PATHS_MAPPED

| source file | function | current authority | raw provider/model | uses route intent | M3 context | can bypass M3 | can bypass M2 | insertion point |
|---|---|---|---:|---:|---:|---:|---:|---|
| `src/auto-reply/reply/agent-runner-execution.ts` | `runAgentTurnWithFallback` | resolved followup run provider/model plus configured fallback chain | yes | no | no | yes | yes | Immediately before runWithModelFallback and carry VerifiedRoute into each embedded/CLI candidate attempt. |
| `src/auto-reply/reply/agent-runner-execution.ts` | `runWithModelFallback callback in runAgentTurnWithFallback` | fallback candidate provider/model chosen by runWithModelFallback | yes | no | no | yes | yes | Firewall every candidate before runCliAgent/runEmbeddedPiAgent; fallback candidate must preserve contract_version and authority_mode. |
| `src/auto-reply/reply/followup-runner.ts` | `applyUmcV1QueuedRouteAdmission` | M2 queued route admission intercepts owner queued raw selection to default route | yes | yes | yes | no | no | Brand queueAdmission.intent after M2 admission and before queued runWithModelFallback. |
| `src/auto-reply/reply/followup-runner.ts` | `createFollowupRunner` | queueAdmission provider/model or original queued run provider/model | yes | yes | yes | no | no | Pass branded VerifiedRoute from queueAdmission into fallback loop and embedded execution parameters. |
| `src/auto-reply/reply/model-selection.ts` | `createModelSelectionState` | session/parent stored override, heartbeat override, directive/catalog allowlist | yes | no | no | yes | yes | Convert session/channel/model directive selections into route intent only; do not mark as route authority until verifier brands it. |
| `src/agents/model-fallback.ts` | `runWithModelFallback` | primary provider/model plus configured fallbacks/allowlist | yes | no | no | yes | yes | API contract should require VerifiedRoute or verified candidate callback metadata before invoking run(provider, model). |
| `src/agents/pi-embedded-runner/run/setup.ts` | `resolveHookModelSelection` | before_model_resolve / before_agent_start hook overrides | yes | no | no | yes | yes | Treat hook overrides as route intent; require verifier before effective runtime model use. |
| `src/agents/agent-command.ts` | `runAgentCommand fallback loop` | direct CLI/subagent command model override plus fallback chain | yes | no | no | yes | yes | When owner-chat surfaced, require VerifiedRoute before attemptExecutionRuntime.runAgentAttempt. |
