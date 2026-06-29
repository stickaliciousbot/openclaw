# Closeout delivery-boundary projector backport — 2026-06-29

## Current classification

`DELIVERY_BOUNDARY_PROJECTOR_INSTALL_HEALTH_PASS_SMOKE_TIMEOUT_NO_ROLLBACK`

The patch-only `openclaw@2026.5.7` delivery-boundary closeout projector is installed in production and health-gated, but final direct Telegram closeout delivery is not yet proven because the product smoke timed out through the Gateway agent path and attempted embedded fallback.

## Problem statement

Earlier production smokes showed a valid closeout-shaped payload could reach the direct Telegram session transcript while the visible final assistant delivery still lacked the formatted closeout summary. This created an append gap: transcript payload visibility was being mistaken for user-visible delivery.

The required delivery invariant is:

```text
Tool result / transcript window
  -> Closeout extractor
  -> Strongest valid closeout candidate selection
  -> resolveCloseoutDeliveryDecision(...)
  -> Delivery-boundary projector
  -> ReplyPayload.text
  -> Telegram outbound send
  -> sent-message evidence / pending debt clear
```

For direct Telegram final assistant replies, if the current turn contains a valid closeout-shaped payload, runtime must either append the closeout exactly once to `ReplyPayload.text` or persist pending closeout debt. Silent drop is not allowed.

## Source behavior implemented

The source backport keeps closeout status logic centralized and uses existing helpers:

- closeout extraction and strongest multi-JSON candidate selection;
- explicit PASS/UNKNOWN/FAIL handling with weak UNKNOWN deprioritization;
- `resolveCloseoutDeliveryDecision(...)`;
- normalized `Closeout: PASS` formatter;
- duplicate prevention;
- false-status guard (`Failed: FAIL` / `Failed gates: none` must not appear from empty failed fields);
- direct Telegram final reply delivery-boundary projector in `dispatchReplyFromConfig(...)`;
- append to `ReplyPayload.text` with normal final answer first;
- direct-chat/message_tool_only/send-policy/group-channel-room suppression checks;
- pending closeout debt write when visible final delivery is not confirmed;
- matching pending debt clear only after confirmed visible delivery.

## Source validation

The source/package gate passed before production apply:

- focused delivery-boundary projector tests: PASS;
- source-reply dispatch tests: PASS — 2 files / 35 tests;
- PI / close-loop regression: PASS — 1 file / 24 tests;
- final-path regression: PASS — 1 file / 3 tests;
- runner e2e: PASS — 1 file / 39 tests;
- `git diff --check`: PASS;
- `tsgo:core`: PASS;
- `tsgo:test:src`: PASS;
- `build:plugin-sdk:dts`: PASS;
- `build-all`: PASS;
- real source `npm pack`: PASS;
- temp-prefix install: PASS;
- staged CLI version/help: PASS;
- source + temp-dist marker checks: PASS.

Fresh package artifact:

- `/tmp/openclaw-closeout-delivery-boundary-projector-57-pack/openclaw-2026.5.7.tgz`
- SHA256 `40b0bab7fc2322ad993a962a5ad207d1a0c9b92a540629f0a054f7ed866fe1b8`
- package `openclaw@2026.5.7`, not `2026.6.10`

## Production apply evidence

Production apply used staged-prefix copy/swap, not direct production `npm install -g`.

- staged prefix: `/tmp/openclaw-closeout-delivery-boundary-projector-prod-stage-20260629T030839Z`
- production bin symlink: `../lib/node_modules/openclaw/openclaw.mjs`
- rollback backup: `.artifacts/closeout-delivery-boundary-projector-prod-apply-20260629T030839Z/openclaw-global-delivery-boundary-projector-57-20260629T030839Z.tar.gz`
- rollback backup SHA256: `1a62ad1566b6a4b6bec53ff4bc0dd05bcdf20a6b48adc7d80a983d0adb4461fa`
- runtime before/after: `OpenClaw 2026.5.7 (5c3a327)`
- Gateway PID: `136182` -> `159418`
- health/connectivity/admin: PASS
- marker checks: PASS
- fatal scan: PASS, excluding known `ge2-register`
- rollback performed: no

## Smoke timeout lesson

The final direct Telegram product smoke did **not** prove delivery. The Gateway `openclaw agent --deliver` path timed out after about 630 seconds and attempted embedded fallback. The fallback was stopped and must not be counted as production-Gateway delivery evidence.

Do not classify append count `0` as projector failure unless the smoke harness proves it exercised the real production Telegram/Gateway delivery boundary.

A trustworthy smoke must report a correlation table:

| Stage                              | Required evidence          |
| ---------------------------------- | -------------------------- |
| Gateway received smoke request     | yes/no + id                |
| Direct Telegram session resolved   | yes/no + session key       |
| Gateway agent run started          | yes/no + run id            |
| Tool-result payload emitted        | yes/no + line/id           |
| Final assistant delivery attempted | yes/no + payload field     |
| Telegram send attempted            | yes/no + provider evidence |
| Sent-message record written        | yes/no + message id/file   |
| Timeout location                   | exact stage                |
| Fallback triggered                 | yes/no                     |
| Fallback disabled/fail-closed      | yes/no                     |

## Next milestones

1. Freeze current green production state and DR checkpoint.
2. Diagnose Gateway smoke timeout separately from projector logic.
3. Build a trustworthy smoke harness that disables/fails-closed embedded fallback.
4. Run one corrected direct Telegram final-mile smoke.
5. Only if the valid smoke reaches delivery and append is missing, identify the exact drop point and patch source.
6. If a new package is needed, apply by the same staged-prefix copy/swap method.
7. Final target: `CLOSEOUT_DELIVERY_CONTRACT_PRODUCTION_PASS` with health PASS, valid smoke PASS, append count 1, duplicate 0, false-status 0, no stale pending debt, evidence/memory/docs/GitHub/DR complete.
