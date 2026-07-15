# M3O Owner-Turn Shadow Observation Result

Status: `BLOCKED_M3O_OWNER_TURN_SHADOW_HOOK_NOT_INSTALLED_IN_RUNTIME`

## Owner turn

- Turn ID: `telegram:8495203551:38576`
- Channel: `telegram`
- Session: `agent:main:telegram:direct:8495203551`
- Timestamp: `2026-07-15T14:34:00Z`

## Production path

- Result: normal production reply delivered
- Ambient production delivery count: `1`
- Classification: ambient production delivery, not UMC shadow send

## UMC shadow path

- Shadow admission: `NOT_ADMITTED_HOOK_NOT_INSTALLED`
- `ContractEnvelope` emitted: `false`
- Shadow receipt emitted: `false`
- `UniversalContractReceipt` emitted: `false`
- `DeliveryReceipt` emitted: `false`
- `DeliveryReceipt.mode`: `null`
- Terminal closeout emitted: `false`
- Would-be result: `HOLD_HOOK_NOT_INSTALLED`

## Shadow safety counters

All zero — no shadow path was active to cause any violation.

## Root cause

The UMC v1 shadow hook is not installed in the production OpenClaw runtime at `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/`. A grep of the runtime dist for `ContractEnvelope`, `UniversalContractReceipt`, `DeliveryReceipt`, `umc.shadow`, and `UMC_SHADOW` returned zero matches. The shadow hook exists only as a contract specification in workspace artifacts; it was never deployed into the runtime.

Without the hook installed, no owner turn can produce shadow receipts.

## Recommendation

M3O is blocked until the UMC v1 shadow hook is installed into the production runtime in observe-only/no-send mode. The next milestone should be installing the shadow hook, or a decision point about whether to install it.
