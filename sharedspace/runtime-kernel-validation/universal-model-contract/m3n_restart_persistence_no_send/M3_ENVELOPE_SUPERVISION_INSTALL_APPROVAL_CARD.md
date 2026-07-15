# M3 Envelope Supervision Install Approval Card

Status: `HOLD_M3_ENVELOPE_SUPERVISION_INSTALL_AWAITING_OPERATOR_APPROVAL`

## Short version

I cannot honestly prepare an executable exact install card yet without one operator decision.

The source-ready milestone is valid, but it produced a source-only module under the UMC evidence folder. The installed OpenClaw npm package contains `dist/`, docs, patches, and skills, but not the source tree/build config needed to turn that module into a source-built runtime artifact.

So I am stopping at the approval boundary rather than inventing a direct dist patch.

## Source commit to install

`70ccd82feb4e80a77d54c38caac8e2502c370359`

Supporting commits:

- staged install plan: `0b9dda06110d75edf6fefb96b30404bfaee1497b`
- source-ready result: `09994af8814377e34d8711ad10e75d2d6a3e0280`

## Exact install fields

Not executable yet:

- exact build/package command: `null`
- exact artifact path: `null`
- exact installed files expected to change: `null`
- exact backup path: `null`
- exact rollback command: `null`

Reason: the staged plan says the exact build command must be resolved from a clean OpenClaw source checkout/source integration path. The installed package has no `src` tree or `tsup.config.ts` available at the checked paths.

## Operator decision required

### Recommended: Path A — clean source-build install

Authorize/provide a clean OpenClaw source checkout or source worktree mapping so I can integrate the source-only M3 module into the real source seam, produce a package/artifact, and then prepare a truly exact install approval card.

This matches the staged plan and avoids repeating the H1 class of direct installed-runtime patch risk.

### Alternative: Path B — explicit direct dist hotpatch

Explicitly authorize preparing a direct installed-dist hotpatch card. That would copy the validated M3 module into installed `dist/` and patch `agent-runner.runtime-a09vVD0N.js` with a backup and rollback command.

I am not treating this as authorized by default because the previous H1 rollback was caused by a redundant runtime patch.

## Boundaries reaffirmed

No approval is currently granted for:

- Telegram send/probe;
- external send;
- provider/model shadow live call;
- route/fallback/config production mutation except an exact approved staged runtime install;
- durable memory mutation;
- Context Bridge mutation;
- production authority change;
- M3P/M4/enforcement.

## Required checks for whichever exact card comes next

- Plugin manifest snapshot and hash compare.
- Gateway RPC health via first-class read-only RPC.
- Telegram health via `channels.status probe=false` only.
- Confirm `umc-owner-turn-shadow-hook-H1.js` remains absent.
- Confirm M2 route-admission vocabulary remains present.
- Confirm M3 receipt path is installed.
- Verify installed-runtime emissions:
  - `ContractEnvelope`
  - `ShadowObservationReceipt`
  - `UniversalContractReceipt`
  - `DeliveryReceipt(mode=no_send)`
  - `TerminalContractCloseout`
- Verify all send/provider/write/memory/Context Bridge/route/config/authority counters remain zero.

## Stop condition

No install, Gateway restart, Telegram probe/send, M3O rerun, M3P, M4, or enforcement has been started.
