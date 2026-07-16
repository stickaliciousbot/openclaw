# M6 Contract-Build Lane Install Approval Card

Status: `HOLD_M6_CONTRACT_BUILD_LANE_INSTALL_AWAITING_OPERATOR_APPROVAL`

Approval phrase required before install:

`APPROVE_M6_CONTRACT_BUILD_LANE_STAGED_INSTALL`

Stop here unless that exact approval is given.

## Selected source

- Path: `/home/stickai/.openclaw/worktrees/umc-m3g-observe-only-hook-source-20260711`
- Branch: `evidence/umc-m3g-observe-only-hook-source-20260711`
- Head/source commit to install: `138e91ece8fd83d7e550a891222d8abefb3c75fa`

## Build and package

Build command already passed:

```sh
/home/stickai/.openclaw/workspace/tmp/openclaw-start-ack-pnpm-shim/pnpm build
```

Package command executed to create the approval tarball:

```sh
set -euo pipefail
PKGDIR=/home/stickai/.openclaw/workspace/tmp/umc-m6-package
rm -rf "$PKGDIR"
mkdir -p "$PKGDIR"
npm pack --ignore-scripts --pack-destination "$PKGDIR"
```

Package:

- Path: `/home/stickai/.openclaw/workspace/tmp/umc-m6-package/openclaw-2026.5.7.tgz`
- Size: `23632421` bytes
- Unpacked size: `71.9 MB`
- Total files: `9680`
- npm SHA1: `1319da6166e31985224b089ea19e1253c94a1aa6`
- SHA256: `4f3d07373f51a8a302078c9f72a5416775a4983db3486c7a9a14cda5a09b888d`

Tarball content presence check passed for:

- `package/dist/auto-reply/reply/umc-m6-contract-build-lane.js`
- `package/dist/auto-reply/reply/umc-m4-verified-route.js`
- `package/dist/auto-reply/reply/umc-m5-capability-manifest.js`
- `package/dist/auto-reply/reply/umc-m5-capability-manifest.schema.json`
- `package/dist/auto-reply/reply/umc-m5-seed-manifests.json`
- `package/dist/extensions/telegram/openclaw.plugin.json`

## Install scope after approval

Installed package root:

`/home/stickai/.npm-global/lib/node_modules/openclaw`

Exact install command after approval:

```sh
npm install -g --ignore-scripts /home/stickai/.openclaw/workspace/tmp/umc-m6-package/openclaw-2026.5.7.tgz
```

Expected installed file added/changed:

- `dist/auto-reply/reply/umc-m6-contract-build-lane.js`

Expected preserved files:

- `dist/auto-reply/reply/umc-m4-verified-route.js`
- `dist/auto-reply/reply/umc-m5-capability-manifest.js`
- `dist/auto-reply/reply/umc-m5-capability-manifest.schema.json`
- `dist/auto-reply/reply/umc-m5-seed-manifests.json`
- `dist/extensions/telegram/openclaw.plugin.json`

## Backup and rollback

Backup path before install:

`/home/stickai/.openclaw/backups/openclaw-m6-contract-build-lane-install-20260716T0224Z/openclaw-installed-package`

Backup marker:

`/home/stickai/.openclaw/backups/openclaw-m6-contract-build-lane-install-20260716T0224Z/PASS_BACKUP_CREATED`

Known rollback baseline:

`/home/stickai/.openclaw/backups/openclaw-m5-capability-manifest-install-20260716T0124Z/openclaw-installed-package`

Rollback command, only if needed and separately approved:

```sh
npm install -g --ignore-scripts /home/stickai/.openclaw/workspace/tmp/umc-m5-package/openclaw-2026.5.7.tgz && openclaw gateway restart
```

M5 rollback tarball SHA256:

`13850f7bd15224e295cc4bee6be184e4df3cd29ab30f191d6a757cd088bdcc06`

## Gateway restart requirement

Gateway restart required after install for activation.

Restart method: `openclaw gateway restart` because the first-class `gateway.restart` tool is not available in this session toolset.

Restart reason: `M6 contract-build lane staged install activation`

## Health and preservation checks

- Verify `dist/extensions/telegram/openclaw.plugin.json` exists after install.
- Verify Gateway status: running, connectivity OK, admin-capable.
- Verify Telegram status: enabled, configured, running, connected.
- No Telegram send/probe.

## Installed-runtime M6 verification checks

- `token-broker-vmesh/contract-build` lane present.
- M6 contract-build lane implementation present.
- Valid M2 route intent builds contract-qualified lane.
- Valid lane carries VerifiedRoute.
- Valid lane carries ContractEnvelope.
- Valid lane checks M5 capability manifest.
- Valid lane preserves M3 no-send DeliveryReceipt policy.
- Valid lane preserves terminal closeout policy.
- Worker model is metadata only and not route authority.
- Raw provider/model pin cannot build lane.
- Session/channel model pin becomes route intent only.
- Missing manifest produces typed HOLD.
- Unsupported worker capability produces typed HOLD.
- Fallback without contract preservation is blocked.
- Fallback preserving contract is eligible.
- Production authority remains disabled.
- Enforcement remains disabled.

## M3/M4/M5 regression plan

- M3 envelope/no-send receipt path still passes.
- M4 raw provider/model rejection still passes.
- M4 forged route rejection still passes.
- M5 valid manifest eligibility still passes.
- M5 missing manifest still HOLDs.
- M5 malformed manifest still FAILs.
- M5 unsupported capability still HOLDs.
- Fallback contract preservation still enforced.

## Contract-build lane validation plan

- Valid route intent lane build PASS.
- Raw provider/model bypass blocked.
- Missing manifest HOLD.
- Unsupported worker capability HOLD.
- Fallback without contract preservation blocked.
- Fallback preserving contract eligible.
- Worker model route authority false.
- VerifiedRoute preserved.
- ContractEnvelope preserved.
- DeliveryReceipt no_send preserved.
- Terminal closeout preserved.

## No-send / no-authority boundary

- Telegram send/probe count: `0`
- External send count: `0`
- Provider/model live call count: `0`
- Route/config mutation count: `0`
- Durable memory mutation count: `0`
- Context Bridge mutation count: `0`
- Production authority change count: `0`
- Cron re-enable count: `0`
- M7 started: `false`
- Enforcement enabled: `false`

## Operator decision

Reply exactly:

`APPROVE_M6_CONTRACT_BUILD_LANE_STAGED_INSTALL`

Only then may the staged install proceed.
