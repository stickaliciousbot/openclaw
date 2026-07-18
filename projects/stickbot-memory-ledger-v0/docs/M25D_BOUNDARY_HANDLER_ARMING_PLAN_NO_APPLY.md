# M25D — Boundary Handler Arming Plan / No-Apply

Terminal target: `M25D_BOUNDARY_HANDLER_ARMING_PLAN_READY_NO_APPLY`

## 1. Executive summary

- The M25B boundary handler is installed, enabled, and provenance-proven.
- M25B-R accepted terminal: `M25B_R_PUSHED_HASH_PROVENANCE_PASS_INSTALL_CAN_STAND_NO_RETRY_SCHEDULED`.
- M25C accepted terminal: `M25C_PUSHED_BLOCKED_SAFE_SINGLE_RETRY_SCHEDULING_NOT_ESTABLISHED`.
- Retry remains blocked because the installed handler is unarmed. The plugin entry is enabled, but the handler config does not contain `armed: true` and the required exact arming fields.
- M25D is **no-apply only**. It documents the exact future arming contract and proof plan; it does not arm the plugin, mutate Gateway/plugin config, schedule a retry, run delivery, send Telegram, mutate Ledger/Context Bridge, promote authority, or start M25E/M26.
- A future boundary-handled retry requires separate explicit approval for a narrow Gateway/plugin config mutation plus separate one-shot retry scheduling/execution.
- Retry scheduling remains separate from this M25D plan.

## 2. Current handler state

| Field | Value |
|---|---|
| Plugin name | `stickbot-memory-ledger-m25b-boundary-handler` |
| Version | `0.0.4-m25b-runtime-root-repair` |
| Installed `dist/index.js` hash | `98a174e1767221f355d7a28364f738c2918eab320ed5373f9851d31da33b4347` |
| Provenance status | PASS; M25B-R proved installed hash and pushed evidence |
| Hooks | `before_agent_reply`, `message_sending`, `message_sent` |
| Current plugin entry | enabled: `true` |
| Current handler config | no arming payload present (`config: null` in readback; effectively enabled-only) |
| Armed status | `false` |
| Gateway health | PASS (`Runtime: running`, `Connectivity probe: ok`) |
| Retry scheduled status | no enabled M25C/M25 retry-like job observed during M25D readback |
| Delivery status | none in M25D; M25C delivery count `0` |

Runtime-local evidence root: `sharedspace/runtime-kernel-validation/memory-ledger/m25d_boundary_handler_arming_plan_20260719T055127+1000`.

## 3. Required arming contract

### Actual installed handler fields

Derived from installed source and manifest:

- `armed`
- `expectedJobId`
- `expectedAgentId`
- `expectedSessionKey`
- `expectedCallerPromptSha256`
- `expectedT0CallerSha256`
- `expectedCandidateSourceSha256`
- `eventsPath`
- `expectedEventsSha256`
- `actionsPath`
- `expectedActionsSha256`
- `ledgerMode`
- `ledgerPath`
- `expectedLedgerSha256`
- `validatedLedgerRecords`
- `validatedLedgerEvents`
- `localDate`

Inspection basis:

- `src/boundary-handler.ts`: `parseConfig` rejects unarmed config and requires all fields above.
- `src/boundary-handler.ts`: `evaluateBoundary` requires cron trigger, exact `expectedJobId`, exact agent/session identity, caller prompt hashes, candidate source hash, Context Bridge/Ledger snapshot, sanitized render postconditions, and privacy receipt.
- `src/input-loader.ts`: `CANDIDATE_SOURCE_FILES` and `hashSourceEntries` define the candidate source hash algorithm.
- `openclaw.plugin.json`: `configSchema` requires the same fields when `armed: true`.

### Requested field names mapped to actual fields

| Requested field | Actual installed-handler representation |
|---|---|
| `enabled` | outer plugin entry `plugins.entries.<id>.enabled`; not part of `M25bConfig` |
| `armed` | actual field |
| `expectedJobId` | actual field |
| `expectedSessionKey` | actual field |
| `expectedCallerPromptSha256` | actual field |
| `expectedSourceSha256` | actual field is `expectedCandidateSourceSha256` |
| `expectedContextBridgeEventsSha256` | actual field is `expectedEventsSha256` plus `eventsPath` |
| `expectedContextBridgeActionsSha256` | actual field is `expectedActionsSha256` plus `actionsPath` |
| `expectedLedgerStoreSha256` | actual field is `expectedLedgerSha256` |
| `expectedLedgerPosture` | actual fields are `ledgerMode`, `ledgerPath`, `validatedLedgerRecords`, `validatedLedgerEvents`, `expectedLedgerSha256` |
| `expectedLocalDate` | actual field is `localDate` |
| `expectedDeliverySurface` | **not present** in config; must be enforced by approved future job/session/surface selection and message-hook evidence |
| `maxDeliveries` | **not present** in config; installed handler enforces duplicate prevention in memory through `deliveredReceiptKeys` per `receiptKey` while process state lives |
| `expiresAt` | **not present** in config; future plan must bound by one-shot cron `--at`/delete-after-run plus external watchdog/disarm |
| `disarmAfterSuccess` | **not present** in config; future plan must perform explicit post-run config disarm |
| `disarmAfterFailure` | **not present** in config; future plan must perform explicit post-run config disarm in both PASS and abort paths |
| `evidenceRoot` | **not present** in config; future evidence root must be external to config |

M25D conclusion: arming requirements are fully derived for the installed handler. Several owner-requested safety knobs are not installed-handler config fields; they must be implemented as future M25E procedural guards and postcondition evidence, or require a separate handler change milestone before M25E.

## 4. Hash input plan

All future hashes must be recomputed immediately before arming and again immediately after disarm for drift proof.

| Input | Source/path | Command / algorithm | Tracked or runtime-local | Raw/private content | Stability window | Failure behavior |
|---|---|---|---|---|---|---|
| Caller prompt / retry payload | exact future one-shot cron/agent cleaned body | `sha256(event.cleanedBody)` as in `sha256Bytes(event.cleanedBody)` | runtime-local scheduler payload | sanitized payload only; no raw/private artifacts committed | from disabled job creation through single run | abort if `expectedCallerPromptSha256` or `expectedT0CallerSha256` mismatch |
| One-shot job definition | future disabled cron job JSON/readback | hash the exact cleaned body and preserve sanitized job metadata; do not commit raw IDs | runtime-local | no raw chat/account/message IDs in Git artifacts | disabled creation to execution | abort if job ID/session differs or payload hash changes |
| Candidate source | installed plugin source files: `index.ts`, `openclaw.plugin.json`, `package.json`, `src/boundary-handler.ts`, `src/input-loader.ts`, `src/sanitized-renderer.ts`, `src/types.ts` | installed algorithm: sort entries by path; hash `path + NUL + bytes + NUL` | installed runtime source; evidence records only hashes | source code is local but not private; hash inventory sanitized | recompute immediately pre-arm | abort on `BINDING_SOURCE_DRIFT` |
| Context Bridge events | `sharedspace/context-bridge/events.jsonl` | `sha256sum` / `sha256Bytes(readFile(eventsPath))` | runtime-local/protected live file | raw content not copied to Git; hash only | read-before-arm to handler read; handler also checks changed-during-read | abort on `EVENTS_FINGERPRINT_DRIFT` or `EVENTS_CHANGED_DURING_READ` |
| Context Bridge actions | `sharedspace/context-bridge/actions.json` | `sha256sum` / `sha256Bytes(readFile(actionsPath))` | runtime-local/protected live file | raw content not copied to Git; hash only | read-before-arm to handler read; handler also checks changed-during-read | abort on `ACTIONS_FINGERPRINT_DRIFT` or `ACTIONS_CHANGED_DURING_READ` |
| Ledger store | either validated M22 posture or readonly SQLite path | for `validated_m22_posture`, fixed posture hash/counts; for `readonly_sqlite`, `sha256sum` plus readonly table counts | runtime-local | do not commit database/raw rows | stable through handler read; readonly path is read-before/read-after checked | abort on `VALIDATED_M22_LEDGER_POSTURE_DRIFT`, `LEDGER_FINGERPRINT_DRIFT`, or `LEDGER_CHANGED_DURING_READ` |
| Ledger posture summary | `ledgerMode`, `ledgerPath`, `validatedLedgerRecords`, `validatedLedgerEvents`, `expectedLedgerSha256` | structured config fields; M25D dry-run found runtime `state/stickbot-memory-ledger/v0/memory-ledger.sqlite` absent, so future plan should use `validated_m22_posture` unless a readonly store is explicitly approved/present | config fields/evidence summary | no raw/private content | recompute at arming | abort if posture does not match exactly |
| Local date/timezone | runtime local date in Australia/Sydney | `date +%F`; config field `localDate` (`YYYY-MM-DD`) | runtime-local | no private content | must match run date; if delayed across midnight, recompute/re-arm or abort | abort on `CONFIG_LOCALDATE_INVALID` or renderer/date mismatch policy |
| Delivery surface | future approved delivery surface/session | not an installed config field; prove via cron/session metadata, `message_sending`, and `message_sent` receipts | runtime-local; sanitized receipts only | redact channel/to/message IDs in Git artifacts | only the approved single run | abort on unexpected surface/session/recipient or missing receipt |

M25D dry-run sample hashes:

- Synthetic sample prompt hash: `120ea147b65c9f0603de21181cb856c67d874b06b37078d9e62c9e2dbff21947`.
- Candidate source hash: `dec25b28503614eefbbf8ba763eda3a9d48f93dbbd306921197ece262e42a4e3`.
- Context Bridge events hash: `f0f7f59ed0028d2f2f250934b62b6f3f3e8aa3cbf3ed1d6454d71b2a63d269b3`.
- Context Bridge actions hash: `a7b0d3d4bd1a9c8bb0da20a1f92cc248f3f37dbf551c66a361330076777bba63`.
- Runtime Ledger store hash: unavailable (`state/stickbot-memory-ledger/v0/memory-ledger.sqlite` absent).
- Validated M22 posture hash: `f50ff3836724358d2ef99d92d7c32c2c07651138a749e2a03ce5c03c512807f6`.
- Local date sample: `2026-07-19`.

These are dry-run samples only and are not authority to arm or run.

## 5. One-shot scheduling design

Future M25E safe one-shot sequence:

1. Create a disabled one-shot job definition with the exact future retry cleaned body and intended session/agent, using OpenClaw cron support for one-shot execution and delete-after-run where available.
2. Read back the disabled job definition; capture sanitized metadata and hash the exact cleaned body.
3. Compute exact arming inputs: `expectedJobId`, `expectedAgentId`, `expectedSessionKey`, `expectedCallerPromptSha256`, `expectedT0CallerSha256`, `expectedCandidateSourceSha256`, Context Bridge hashes, Ledger posture/hash, and `localDate`.
4. Apply the narrow plugin config arming diff for only that job after separate M25E owner approval.
5. Verify config applied and handler is armed for exactly the expected job/session/hash set.
6. Enable/run once.
7. Verify the handler returns `PASS_M25B_BOUNDARY_READY_FOR_SINGLE_SCHEDULED_ANNOUNCE`, prepares outbound delivery for the run, gates `message_sending`, and records `message_sent` receipt if delivery succeeds.
8. Disarm plugin immediately after success or failure.
9. Remove the one-shot schedule or confirm delete-after-run removed it.
10. Validate no retry remains scheduled and no duplicate delivery occurred.

No recurring schedule is allowed. If `--delete-after-run` or equivalent cannot be proven, M25E must remove the job explicitly before closeout.

## 6. Gateway/plugin config mutation plan

This is documentation only. Do not apply in M25D.

### Future mutation surface

Preferred future surface: first-class OpenClaw config patch/apply mechanism if available; otherwise a carefully approved atomic edit to `/home/stickai/.openclaw/openclaw.json` followed by Gateway reload/restart only if documented as required by the active plugin config surface.

Future config path:

```text
plugins.entries.stickbot-memory-ledger-m25b-boundary-handler
```

Current shape observed in M25D:

```json
{
  "enabled": true
}
```

Future armed shape (example placeholders only):

```json
{
  "enabled": true,
  "config": {
    "armed": true,
    "expectedJobId": "<future-one-shot-job-id>",
    "expectedAgentId": "main",
    "expectedSessionKey": "<future-session-key>",
    "expectedCallerPromptSha256": "<sha256-of-exact-cleaned-body>",
    "expectedT0CallerSha256": "<same-sha256-at-T0>",
    "expectedCandidateSourceSha256": "<candidate-source-hash>",
    "eventsPath": "sharedspace/context-bridge/events.jsonl",
    "expectedEventsSha256": "<events-sha256>",
    "actionsPath": "sharedspace/context-bridge/actions.json",
    "expectedActionsSha256": "<actions-sha256>",
    "ledgerMode": "validated_m22_posture",
    "ledgerPath": null,
    "expectedLedgerSha256": "f50ff3836724358d2ef99d92d7c32c2c07651138a749e2a03ce5c03c512807f6",
    "validatedLedgerRecords": 19,
    "validatedLedgerEvents": 20,
    "localDate": "<YYYY-MM-DD>"
  }
}
```

Rollback/disarm shape:

```json
{
  "enabled": true
}
```

or, if the runtime requires a config object to satisfy schema:

```json
{
  "enabled": true,
  "config": { "armed": false }
}
```

Future M25E must determine which disarm shape the active OpenClaw plugin config loader preserves without quarantine.

### Required diff bounding

The approved M25E config diff must be limited to:

- adding/replacing `plugins.entries.stickbot-memory-ledger-m25b-boundary-handler.config` with the exact arming object;
- later removing that `config` object or setting `{ "armed": false }`;
- no route/model/provider/fallback/memory-route changes;
- no channel config changes;
- no plugin install/replacement;
- no unrelated Gateway config mutation.

Before/after full config hashes must be captured. A Gateway restart/reload, if required, must be explicitly approved and verified by health probe. If hot reload is sufficient, avoid restart.

## 7. Handler behavior proof plan

Future M25E proof requirements:

- Handler observes `armed === true` and does not return `DORMANT_M25B_BOUNDARY_HANDLER`.
- `ctx.trigger` is `cron`.
- `ctx.jobId` equals `expectedJobId`.
- `ctx.agentId` equals `expectedAgentId`.
- `ctx.sessionKey` equals `expectedSessionKey`.
- `sha256(event.cleanedBody)` equals both `expectedCallerPromptSha256` and `expectedT0CallerSha256`.
- Candidate source hash equals `expectedCandidateSourceSha256`.
- Context Bridge events/actions paths and hashes match and remain stable during read.
- Ledger posture/hash/counts match.
- Sanitized renderer returns `noSend: true`, `deliveryOperationsExposed: 0`, `authorityPromotion: false`, `recallTimeMemoryWrites: false`, `automaticLedgerRecall: false`.
- Privacy receipt is clean.
- `READY_FOR_SINGLE_SCHEDULED_ANNOUNCE` status is `PASS_M25B_BOUNDARY_READY_FOR_SINGLE_SCHEDULED_ANNOUNCE`.
- Outbound delivery is prepared exactly once for the run ID.
- `message_sending` sees exact expected sanitized content and does not cancel.
- `message_sent` records a delivery receipt with mutation counters `ledger: 0`, `contextBridge: 0`, `authorityPromotions: 0`, `recallTimeWrites: 0`.
- Duplicate delivery is blocked or absent.
- Handler is disarmed after completion.
- No retry remains scheduled.

## 8. Abort criteria

Future armed retry must abort if any of these occur:

- any hash mismatches;
- job ID, agent ID, or session key mismatch;
- local date mismatch or crossing midnight without re-arm approval;
- Context Bridge events/actions hash mismatch or changed-during-read;
- Ledger hash/posture/count mismatch;
- delivery surface/session/recipient mismatch;
- delivery count exceeds one;
- closeout anchor missing;
- terminal payload anchor missing;
- Gateway/plugin config mutation exceeds the approved diff;
- plugin config loader quarantines or rewrites unexpected fields;
- retry remains scheduled after run/abort;
- duplicate delivery occurs;
- authority promotion occurs;
- Ledger or Context Bridge mutation occurs;
- raw/private content appears in evidence;
- Gateway health fails after mutation or disarm;
- rollback/disarm cannot be verified.

## 9. Rollback/disarm plan

Future M25E rollback/disarm sequence:

1. Immediately set plugin entry back to the pre-arm shape (`enabled: true` with no `config`) or to `{ "config": { "armed": false } }` if runtime schema requires an explicit object.
2. Apply/hot-reload/restart only through the approved config surface.
3. Verify live plugin readback reports unarmed.
4. Remove the one-shot schedule, or confirm delete-after-run removed it.
5. Verify no enabled M25E/M25 retry-like cron/timer remains.
6. Verify no delivery can occur: handler returns dormant/not armed for non-prepared sends and `message_sending` has no prepared run for the session.
7. Verify Gateway health PASS.
8. Verify no unrelated route/model/provider/fallback/memory-route mutation remains.
9. Verify Ledger and Context Bridge hashes/counts are unchanged from pre-arm baselines.
10. Preserve rollback evidence with sanitized config diffs, hashes, schedule state, and private scan.

## 10. M25E recommendation

Recommended next milestone:

```text
M25E — Boundary Handler Armed One-Shot Retry Controlled Execution
```

M25E requires separate owner approval and must not be started by M25D.

M25E should allow exactly:

- bounded plugin config arming for one job;
- one-shot retry scheduling;
- one execution;
- mandatory disarm/removal afterward;
- sanitized proof artifacts and closeout.

M25E should not allow plugin replacement, Gateway/model/provider/fallback/memory-route changes, Ledger/Context Bridge mutation, authority promotion, recurring schedules, broad Telegram sends, or M26 start.
