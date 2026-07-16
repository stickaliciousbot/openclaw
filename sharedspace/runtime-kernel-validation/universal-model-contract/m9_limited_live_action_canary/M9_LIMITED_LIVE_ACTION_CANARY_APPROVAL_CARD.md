# M9 Limited Live-Action Canary Approval Card

Status: `HOLD_M9_LIMITED_LIVE_ACTION_CANARY_AWAITING_OPERATOR_APPROVAL`

No live action has been executed.

## Exact approval text

`APPROVE_M9_LIMITED_LIVE_ACTION_CANARY_EXECUTION`

## Exact canary action after approval

Tool: `write`

Path: `sharedspace/runtime-kernel-validation/universal-model-contract/m9_limited_live_action_canary/M9_LOCAL_ARTIFACT_CANARY_TARGET.txt`

Expected SHA256: `1908d9158dc06e6c7127b86cde923361c3f86a13ba084c4f03746d4af49ff0cf`

Content:

```text
M9 local artifact write canary.
This file proves bounded live write execution under UMC contract control.
No external send.
No Telegram send.
No provider/model live call.
```

Maximum allowed action count: 1.

Expected receipts: WriteReceipt, DeliveryReceipt mode `local_artifact_write`, TerminalContractCloseout.

M10 is not authorized. Broad production authority is not authorized. Telegram/external send and provider/model live call remain forbidden.
