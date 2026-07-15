# M3 Envelope Supervision Staged Install Plan

Status: `PASS_M3_ENVELOPE_SUPERVISION_STAGED_INSTALL_PLAN_READY`

This is a plan only. It was not executed.

## Source commit to install

`70ccd82feb4e80a77d54c38caac8e2502c370359`

Branch: `evidence/umc-m3n-post-restart-health-failclosed-20260713`

Source-only files:

- `umc_m3_envelope_supervision.mjs`
- `run_m3_envelope_supervision_fixtures.mjs`

## Build command

Use the project-equivalent OpenClaw source build after mapping the source-only M3 module into the proper source tree seam. Do not build from dirty installed dist.

Candidate command shape:

```sh
npm run build
```

The exact command must be resolved from the clean source checkout/package scripts during the approved install phase.

## Package / staged artifact path

No package or tarball was created in this source-only phase.

Install phase must create a staged package/artifact only after explicit approval.

## Expected installed files to change after approval

Expected, subject to source-build chunk names:

- `dist/agent-runner.runtime-*.js` or successor chunk at the M2 route-intent admission boundary.
- `dist/get-reply-*.js` or successor if direct owner-turn receipt readback needs reply-path integration.
- A source-owned M3 envelope supervision chunk/module emitted by the build.

Must remain absent:

- `dist/umc-owner-turn-shadow-hook-H1.js`

Must not be edited unless separately justified:

- `dist/route-reply-D6Nvzk_V.js`

## Plugin manifest preservation checks

1. Snapshot plugin manifests and channel plugin registry files before install.
2. Compare manifest paths/hashes after build/package.
3. Unexpected plugin manifest deletion/change is `HOLD`.
4. Telegram status validation must use read-only `channels.status probe=false` only.
5. Do not opportunistically repair plugin manifests in the M3 install lane.

## Gateway / Telegram validation after approved install

- Use first-class `gateway.restart` only if explicitly approved.
- Validate Gateway RPC via `cron.status` or equivalent read-only first-class RPC.
- Validate Telegram via `channels.status probe=false`; no live Telegram send/probe.
- Confirm M2 route-admission vocabulary remains present.
- Confirm M3 receipt vocabulary is now installed.
- Confirm the H1 helper remains absent.

## Rollback path

- Snapshot package/dist before install.
- If build/package fails before runtime mutation, discard staged artifacts and leave runtime untouched.
- If runtime mutation occurs and validation fails, restore exact pre-install snapshot and first-class restart only if approved.
- Preserve rollback evidence.
- Do not rerun M3O until rollback state is verified.

## Approval boundary

Explicit approval is required before:

- package build intended for runtime installation;
- tarball/package apply;
- installed runtime/dist mutation;
- Gateway restart/reload;
- Telegram probe beyond `channels.status probe=false`;
- M3O rerun.

## Post-install M3 verification

- Source fixture suite still passes.
- Installed no-send fixture/readback emits:
  - `ContractEnvelope`
  - `ShadowObservationReceipt`
  - `ToolSupervisionReceipt`
  - `DeliveryReceipt(mode=no_send)`
  - `UniversalContractReceipt`
  - `TerminalContractCloseout`
- Safety counters remain zero for sends, provider calls, real write tools, memory mutation, Context Bridge mutation, route/config mutation, and production authority change.
- Production response path remains unchanged.
- Ambient production delivery is classified separately from shadow no-send delivery.

## M3O rerun plan after install

Only after installed M3 verification passes, rerun `M3O_OWNER_TURN_SHADOW_OBSERVATION_NO_SEND` on an approved owner-turn observation method.

If any receipt is missing, classify as `HOLD`/`FAIL`, preserve evidence, and do not proceed to M3P/M4.

## Exact next milestone after PASS

`M3_ENVELOPE_SUPERVISION_STAGED_INSTALL_AND_M3O_RERUN`
