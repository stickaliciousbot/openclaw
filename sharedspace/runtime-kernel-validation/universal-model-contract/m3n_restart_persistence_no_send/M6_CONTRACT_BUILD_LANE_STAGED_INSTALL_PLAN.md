# M6 Contract-Build Lane Staged Install Plan

Status: `PASS_M6_CONTRACT_BUILD_LANE_STAGED_INSTALL_PLAN_READY`

This is a staged install plan only. Do not install during `M6_TOKEN_BROKER_VMESH_CONTRACT_BUILD_LANE_SOURCE_NO_APPLY`.

## Source

- Path: `/home/stickai/.openclaw/worktrees/umc-m3g-observe-only-hook-source-20260711`
- Branch: `evidence/umc-m3g-observe-only-hook-source-20260711`
- Head/source commit: `138e91ece8fd83d7e550a891222d8abefb3c75fa`

## Build/package command

```sh
/home/stickai/.openclaw/workspace/tmp/openclaw-start-ack-pnpm-shim/pnpm build && npm pack --ignore-scripts
```

Tarball path: TBD in `M6_CONTRACT_BUILD_LANE_STAGED_INSTALL_AND_REGRESSION`.

## Expected installed files changed

- `dist/auto-reply/reply/umc-m6-contract-build-lane.js`

## Backup and rollback

Trusted pre-M6 baseline backup:

`/home/stickai/.openclaw/backups/openclaw-m5-capability-manifest-install-20260716T0124Z/openclaw-installed-package`

Next staged install should create a fresh backup at:

`/home/stickai/.openclaw/backups/openclaw-m6-contract-build-lane-install-<UTC>/openclaw-installed-package`

Rollback command, only if required and approved:

```sh
npm install -g --ignore-scripts /home/stickai/.openclaw/workspace/tmp/umc-m5-package/openclaw-2026.5.7.tgz && openclaw gateway restart
```

M5 rollback tarball SHA256: `13850f7bd15224e295cc4bee6be184e4df3cd29ab30f191d6a757cd088bdcc06`

## Validation plan

- Gateway health: running/connectivity/admin-capable after restart.
- Telegram health: enabled/configured/running/connected; no Telegram send/probe unless separately approved.
- M3 regression: no-send receipts, terminal closeout, production path unchanged, all forbidden counters zero.
- M4 regression: raw provider/model, missing VerifiedRoute, forged/deserialized route, and fallback without VerifiedRoute reject before execution.
- M5 regression: valid manifest PASS, missing manifest HOLD, malformed manifest FAIL, unsupported capability HOLD, fallback preservation enforced.
- M6 installed-runtime validation: installed contract-build artifact exists; valid M2 owner-turn intent builds lane; raw provider/model bypass fails; worker model is not route authority; ContractEnvelope/no_send/terminal closeout preserved.

## Approval boundary

No package install, Gateway restart, Telegram probe, provider/model live call, config mutation, durable memory mutation, Context Bridge mutation, production authority/enforcement, cron re-enable, or M7 without explicit staged-install approval.
