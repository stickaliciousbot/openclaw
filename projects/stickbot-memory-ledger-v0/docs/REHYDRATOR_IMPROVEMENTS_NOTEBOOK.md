# Stickbot Memory Ledger Rehydrator Improvements Notebook

## 2026-07-19 — M25B-R hash provenance and scoped push dirty-tree lesson

### Closeout state to rehydrate

- M25B-R terminal: `M25B_R_HASH_PROVENANCE_PASS_INSTALL_CAN_STAND_NO_RETRY_SCHEDULED`.
- Preservation push terminal: `M25B_R_PUSHED_HASH_PROVENANCE_PASS_INSTALL_CAN_STAND_NO_RETRY_SCHEDULED`.
- Installed boundary-handler runtime hash: `98a174e1767221f355d7a28364f738c2918eab320ed5373f9851d31da33b4347`.
- Prior runtime-output hash that caused the initial mismatch: `a9cf4a6deca4d045b116ef480dd3abb6747ed1cca838d6484513e74d902fdec5`.
- Provenance repair commit: `055a3f56076d6d804ec925a401e48dc2698bc895`.
- Provenance replacement/preservation commit: `1c119cf5d186dbde8be48977efae0245256b759a`.
- Final evidence commit: `fd00fb76518d463d009b055918d88bcf75d50b27`.
- Evidence root: `sharedspace/runtime-kernel-validation/memory-ledger/m25b_r_hash_provenance_or_rollback_20260719T050952+1000`.
- Remote branch pushed: `origin/evidence/umc-m3n-post-restart-health-failclosed-20260713`.

### Rehydration lesson

The initial M25B install closeout was safely blocked because a generated `status.json` PASS headline contradicted `install_proof.json`, which showed the installed runtime hash did not match the earlier recorded approved runtime-output hash. The correct recovery was not rollback-first and not blind acceptance; it was bounded provenance proof.

The bounded proof chain was:

1. Git pickaxe identified `055a3f56076d6d804ec925a401e48dc2698bc895` and `1c119cf5d186dbde8be48977efae0245256b759a` as the local commits carrying the installed hash.
2. `055a3f...` preserved `MEMORY_LEDGER_V0_1_M25B_RUNTIME_SOURCE_ROOT_REPAIRED_INSTALL_MANIFEST.json` with compiled runtime hash `98a174...`.
3. `1c119c...` preserved source-root replacement install/runtime validation artifacts with runtime hash `98a174...`, plus a preflight artifact that linked the replacement flow back to the prior `a9cf...` hash.
4. Active installed plugin readback matched `98a174...`, imported successfully, and registered `before_agent_reply`, `message_sending`, and `message_sent`.
5. No retry schedule, delivery/send, Ledger mutation, Context Bridge mutation, route/config mutation, or authority promotion occurred.

### Scoped preservation push rule

Future preservation push gates must distinguish two modes:

- **Global-clean push:** require no tracked worktree dirt anywhere.
- **Scoped committed-head push:** allowed only with explicit owner approval when unrelated dirty files are pre-existing and unstaged. Verify exact branch/head, remote old head, empty index, no rebase/merge in progress, committed diff scope is only the intended evidence/project root, private scan is clean, terminal status is PASS, no active retry/delivery/send/mutation flags, and push without force.

Do not silently downgrade global-clean requirements. If the prompt requires global clean, stop on unrelated dirt. If the owner explicitly authorizes scoped committed-head push, push the committed branch head only and never stage/commit/amend unrelated files.

### Git lock rule

A stale `.git/index.lock` may be removed only after confirming it is old/stale, zero-byte or otherwise clearly abandoned, and no active Git process owns it. Remove only `.git/index.lock`; never delete broader Git state.

## 2026-07-19 — M25C blocked retry and M25D arming-plan lesson

### Closeout state to rehydrate

- M25C pushed terminal: `M25C_PUSHED_BLOCKED_SAFE_SINGLE_RETRY_SCHEDULING_NOT_ESTABLISHED`.
- M25C evidence root: `sharedspace/runtime-kernel-validation/memory-ledger/m25c_single_boundary_handled_retry_20260719T053834+1000`.
- M25C evidence commit/pushed head: `3b36d0317b2b5d520be3b9c9de6e8c4eeab6d717`.
- M25D terminal: `M25D_BOUNDARY_HANDLER_ARMING_PLAN_READY_NO_APPLY`.
- M25D plan: `docs/M25D_BOUNDARY_HANDLER_ARMING_PLAN_NO_APPLY.md`.
- M25D tracked evidence: `artifacts/memory-ledger/m25d-boundary-handler-arming-plan/`.
- M25D runtime-local evidence: `sharedspace/runtime-kernel-validation/memory-ledger/m25d_boundary_handler_arming_plan_20260719T055127+1000`.

### Rehydration lesson

The installed M25B boundary handler being enabled is not enough to prove a boundary-handled retry. The active runtime entry loads the extension, but a real handled retry requires an exact armed config object. M25C correctly blocked rather than scheduling an ordinary unhandled retry.

M25D derived the installed handler's actual arming fields:

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

Several safety knobs are not installed-handler config fields (`expectedDeliverySurface`, `maxDeliveries`, `expiresAt`, `disarmAfterSuccess`, `disarmAfterFailure`, `evidenceRoot`). They must be enforced procedurally in M25E with bounded one-shot scheduling, explicit config disarm/removal, runtime receipts, and no duplicate/scheduled-retry postcondition checks unless a separate handler change is approved.

### Future M25E gate

Do not start M25E without separate owner approval. M25E must explicitly allow the otherwise-forbidden plugin config arming/disarming mutation, exactly one one-shot retry schedule/run, immediate disarm/removal, and sanitized evidence. It must not replace the plugin, mutate routes/model/provider/fallback/memory routes, mutate Ledger/Context Bridge, promote authority, or start M26.
