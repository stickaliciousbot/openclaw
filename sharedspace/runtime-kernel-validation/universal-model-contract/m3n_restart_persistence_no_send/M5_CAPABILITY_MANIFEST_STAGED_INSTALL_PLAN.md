# M5 Capability Manifest Staged Install Plan

Status: `PASS_M5_CAPABILITY_MANIFEST_STAGED_INSTALL_PLAN_READY`

This is a plan only. Do not install during `M5_CAPABILITY_MANIFEST_REGISTRY_NO_SEND`.

## Source

- Path: `/home/stickai/.openclaw/worktrees/umc-m3g-observe-only-hook-source-20260711`
- Branch: `evidence/umc-m3g-observe-only-hook-source-20260711`
- Head/source commit: `3aaf216bcfd8beb7988949b655441104e78176f8`

## Build/package command for the later staged-install milestone

```sh
pnpm build && npm pack --ignore-scripts
```

Tarball path: TBD in `M5_CAPABILITY_MANIFEST_STAGED_INSTALL_AND_REGRESSION`.

## Expected installed files changed

- `dist/auto-reply/reply/umc-m5-capability-manifest.js`
- `dist/auto-reply/reply/umc-m5-capability-manifest.schema.json`
- `dist/auto-reply/reply/umc-m5-seed-manifests.json`

## Manifest source locations

- `src/auto-reply/reply/umc-m5-capability-manifest.schema.json`
- `src/auto-reply/reply/umc-m5-seed-manifests.json`

## Backup and rollback

Trusted pre-M5 baseline backup: `/home/stickai/.openclaw/backups/openclaw-m4-verified-route-install-20260716T0022Z/openclaw-installed-package`

Next staged install should create a fresh backup at:

`/home/stickai/.openclaw/backups/openclaw-m5-capability-manifest-install-<UTC>/openclaw-installed-package`

Rollback command, if explicitly approved during staged install:

```sh
npm install -g --ignore-scripts /home/stickai/.openclaw/workspace/tmp/umc-m4-package-r2/openclaw-2026.5.7.tgz && openclaw gateway restart
```

Approved M4 R2 tarball SHA256: `6a2ec7a2318c8e56a565524f938831ca5d2a2de965e6e16bd2fbc5f4acd2f663`

## Post-install validation plan

- Gateway health: `openclaw gateway status` must report running/connectivity/admin-capable after restart.
- Telegram health: channel status must report Telegram enabled/configured/running/connected; no Telegram send/probe unless separately approved.
- M3 regression: installed no-send envelope fixture must emit terminal closeout/no-send receipts and zero forbidden counters.
- M4 regression: installed direct bypass firewall fixture must reject raw owner-scoped provider/model execution.
- M5 registry runtime validation: installed registry/schema/manifests exist and prove valid manifest PASS, missing manifest HOLD, unsupported capability HOLD, contradictory manifest FAIL, fallback preservation HOLD.
- Direct bypass/firewall validation: manifests cannot forge VerifiedRoute or bypass the M4 firewall.
- No-send/no-authority validation: Telegram sends, external sends, provider/model live calls, route/config mutation, durable memory mutation, Context Bridge mutation, production authority change, and enforcement all remain zero.

## Approval boundary

No package install, Gateway restart, live route/config mutation, Telegram probe, provider/model live call, production authority change, or enforcement without explicit staged-install approval.

## CPU/event-loop watch item

Known: yes. Blocking: no.

Root is not proven. Best current explanation is runtime load/event-loop saturation amplified by repeated status/validation CLI calls. It existed before M4, Gateway RPC and Telegram health passed, and it has not correlated with M5 no-apply readback failure. Treat it as blocking only if it worsens, correlates with health/readback failure, or violates M5 gates.
