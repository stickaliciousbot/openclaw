# GE2-R8 Native Execution Route Discovery — Intake Hold

Status: `GE2_R8_INTAKE_HOLD_UNTIL_BANANA`

Reason: Stick instructed to read the prompt until `banana`, save bits to memory and implementation notebooks before implementing. The received prompt segment has not yet included `banana`, so implementation is intentionally held.

## Current carry-forward state

Classification entering R8:

`GE2_R7_COMMAND_REGISTRY_VISIBILITY_PASS_HELP_STATUS_PENDING`

Known good state:

- Health re-check PASS
- PID changed: `303370 -> 307081`
- service: running
- runtime: running
- listener: present
- connectivity: ok
- admin: admin-capable
- fatal/missing-module/mixed-runtime scan: PASS, count `0`
- rollback: no

Live `commands.list` gates passed:

| Surface | `/ge2` | duplicate count | total | existing commands | fake |
|---|---:|---:|---:|---|---|
| default | present | 1 | 61 | preserved | absent |
| telegram/both | present | 1 | 61 | preserved | absent |
| telegram/text | present | 1 | 61 | preserved | absent |

Existing commands preserved:

- `pair`
- `dreaming`
- `phone`
- `voice`

Relevant R7 addendum:

`sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/r7_async_direct_command_rpc_probe_addendum_20260630.md`

Async probe found only:

```text
commands.list
```

## R8 goal from received prompt segment

Find or create a safe, non-model native execution proof path for `/ge2 help` and `/ge2 status`.

No production mutation.

## Hard stops from prompt segment

- no model/chat spoofing
- no outbound bot message spoof
- no production patch
- no Gateway restart
- no rollback
- no cron closeout apply
- no `/ge2 run` until help/status execution proof exists
- no plugin-manager bridge patch

## Required R8 diagnosis from prompt segment

Trace Telegram native command path:

- where Telegram message text enters command recognizer
- where `/ge2` is matched after visibility
- where native command handler is called
- where native command response is written to session/outbound delivery

Trace WebUI native command path:

- where WebUI command text enters command recognizer
- where native command handler is called
- where response is returned/displayed

Determine whether a non-model internal harness/test entry point exists:

- command dispatcher function
- bot native command runtime function
- Telegram update handler fixture
- WebUI command handler fixture
- existing tests around `bot-native-commands.runtime`

Safe proof route candidates:

- internal handler harness using production-installed code
- controlled local import of installed dist
- Gateway admin method if one exists
- test fixture that uses exact production command matcher/handler

Explicit rejects:

- model-mediated chat prompt
- prompt suffix trick
- fake outbound bot message
- bash wrapper as proof of native command surface

## Initial expert augmentation / missing pieces to resolve after banana

The received prompt is strong. Missing pieces I should add to the R8 build once the `banana` gate is satisfied:

1. Define proof levels:
   - P0 local handler import only: not enough for live proof.
   - P1 installed-dist matcher+execute using production registry state: useful harness proof.
   - P2 channel adapter fixture that enters at Telegram/WebUI native command recognizer: stronger.
   - P3 real inbound Telegram/WebUI event through Gateway: final live proof.
2. Separate “native execution proof” from “delivery proof”:
   - `/ge2 help/status` native handler result can pass even if outbound channel delivery has a separate issue.
   - R8 should record both handler result and delivery/session/outbound write path if available.
3. Avoid mutating production state:
   - use read-only imports and temporary fixture contexts only.
   - do not call `/ge2 run`.
   - use `/ge2 status` because it reads current GE2 state; it may read existing state but should not create a new run.
4. Build a trace-first script that emits a table before executing any harness.
5. Prefer installed-dist harness entry from `bot-native-commands.runtime-*.js` if it imports `matchPluginCommand` and `executePluginCommand` from the production command chunk.
6. If no safe P2/P3 route exists, classify honestly rather than spoof.

## Gate

Implementation not started. Awaiting the remainder of the prompt and literal `banana`.
