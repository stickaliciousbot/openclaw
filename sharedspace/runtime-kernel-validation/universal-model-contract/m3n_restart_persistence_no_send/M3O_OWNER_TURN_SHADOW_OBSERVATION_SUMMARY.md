# M3O Owner-Turn Shadow Observation Summary

Final status: `BLOCKED_M3O_OWNER_TURN_SHADOW_HOOK_NOT_INSTALLED_IN_RUNTIME`

## What happened

M3O attempted to observe a real owner turn (Stick's "Banana please begin" request) with the UMC v1 shadow path in observe-only/no-send mode. The production path handled the turn normally and delivered a reply. The UMC shadow path produced zero receipts.

## Root cause

The UMC v1 shadow hook is not installed in the production OpenClaw runtime at `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/`. A grep of the runtime dist for `ContractEnvelope`, `UniversalContractReceipt`, `DeliveryReceipt`, `umc.shadow`, and `UMC_SHADOW` returned zero matches. The shadow hook exists only as a contract specification in workspace artifacts; it was never deployed into the runtime.

## Safety

All shadow safety counters are zero — no shadow path was active to cause any violation. The production path was unchanged. No sends, provider calls, mutations, or authority changes occurred.

## Recommendation

M3O is blocked until the UMC v1 shadow hook is installed into the production runtime in observe-only/no-send mode. The next milestone should be installing the shadow hook, or a decision point about whether to install it.

## Next milestone

`M3O_PRE_HOOK_INSTALL_DECISION_OR_M3P_SKIP`
