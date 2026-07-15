# M3 Envelope Supervision Source Seam Map

Status: `PASS_M3_ENVELOPE_SUPERVISION_SOURCE_SEAMS_MAPPED`

This is a source-only/no-apply seam map. It does not mutate installed runtime and does not replace the existing M2 route-admission hook.

## Existing M2 admission seam

The existing production hook is the M2 route-admission/interception layer. It remains authoritative for owner-turn route intent capture.

Known implementation terms:

- `resolveUmcV1DefaultRouteFromConfig`
- `isUmcV1QueuedOwnerScope`
- `applyUmcV1QueuedRouteAdmission`
- `umcV1QueuedRouteIntent`

M3 consumes the M2 `route_intent`; it does not reinstall a hook.

## M3 source seams

| Required seam | Source-only implementation seam | Safety note |
|---|---|---|
| Owner-turn admission from M2 hook | `runM3EnvelopeSupervisor(input)` consumes `route_intent` | No M2 replacement |
| `ContractEnvelope` construction | `buildContractEnvelope(input, timestamps)` | `authority_mode=observe_only`, `delivery_mode=no_send` |
| Shadow observation receipt | `buildShadowObservationReceipt(...)` | Pure receipt emission only |
| Tool proposal supervision boundary | `buildToolSupervisionReceipt(...)` | Observes proposals; real write execution count remains 0 |
| `DeliveryReceipt no_send` | `buildDeliveryReceipt(...)` | No Telegram/external delivery |
| `UniversalContractReceipt` | `buildUniversalContractReceipt(...)` | Binds route intent + all receipts |
| Terminal closeout | `buildTerminalContractCloseout(...)` | Explicit PASS/HOLD/FAIL status required |
| Production reply path separation | `production_path.unchanged=true` | Does not alter production response path |
| Ambient owner-chat delivery classification | `ambient_delivery_classification` | Production delivery is separate from shadow no-send |
| Safety counter collection | `createZeroSafetyCounters(...)` | Required shadow/prod mutation counters stay zero |

## Source-only files

- `umc_m3_envelope_supervision.mjs`
- `run_m3_envelope_supervision_fixtures.mjs`

## Non-apply boundary

- No installed runtime mutation.
- No package install or tarball apply.
- No Gateway restart.
- No Telegram send/probe.
- No provider/model shadow call.
- No route/config production mutation.
- No memory or Context Bridge mutation.
- No M3O rerun, M3P, M4, or enforcement.
