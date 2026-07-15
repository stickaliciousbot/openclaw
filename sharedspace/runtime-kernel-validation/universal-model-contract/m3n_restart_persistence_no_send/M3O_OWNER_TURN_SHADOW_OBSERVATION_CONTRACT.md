# M3O Owner-Turn Shadow Observation Contract

Status: `PASS_M3O_OWNER_TURN_SHADOW_CONTRACT_DEFINED`

Milestone: `M3O_OWNER_TURN_SHADOW_OBSERVATION_NO_SEND`

## Contract

- Mode: observe-only
- UMC shadow delivery: no-send
- Authority: non-authoritative
- Scope: owner turns only
- Production response path: unchanged
- Shadow receipts: required
- `ContractEnvelope`: required
- Shadow receipt: required
- `UniversalContractReceipt`: required
- `DeliveryReceipt`: required
- `DeliveryReceipt.mode`: `no_send`
- Terminal closeout: required

## Required zero counts

- Provider/model live calls caused by shadow: `0`
- Telegram sends caused by shadow: `0`
- External sends caused by shadow: `0`
- Real write tools caused by shadow: `0`
- Memory mutation caused by shadow: `0`
- Context Bridge mutation caused by shadow: `0`
- Route/config mutation caused by shadow: `0`
- Production authority change: `0`

## Classification rule

Normal production owner-chat replies are ambient production deliveries and must be classified separately from UMC shadow sends. They do not count as UMC shadow sends unless directly caused by the shadow path.

## Hard boundaries

No UMC shadow send, no external send caused by shadow, no provider/model live call caused by shadow, no real write tool caused by shadow, no route/fallback/config mutation, no durable memory mutation, no Context Bridge mutation, no production authority change, no M4, no VerifiedRoute enforcement, and no contract enforcement.
