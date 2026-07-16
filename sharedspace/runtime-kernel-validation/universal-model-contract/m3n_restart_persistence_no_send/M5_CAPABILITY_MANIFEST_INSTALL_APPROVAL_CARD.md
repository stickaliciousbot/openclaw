# M5 Capability Manifest Install Approval Card

Status: `HOLD_M5_CAPABILITY_MANIFEST_INSTALL_AWAITING_OPERATOR_APPROVAL`

This card is for the staged install milestone:

`M5_CAPABILITY_MANIFEST_STAGED_INSTALL_AND_REGRESSION`

Nothing has been installed yet.

## Selected source

- Source path: `/home/stickai/.openclaw/worktrees/umc-m3g-observe-only-hook-source-20260711`
- Branch: `evidence/umc-m3g-observe-only-hook-source-20260711`
- Source commit to install: `3a9abe46293294da7c73432d74f6c32e3fd1deaf`
- M5 source-ready base: `3aaf216bcfd8beb7988949b655441104e78176f8`
- Build-inclusion repair: `3a9abe46293294da7c73432d74f6c32e3fd1deaf`

Why repair was needed: M5 source-ready existed, but staged install preflight found it needed a stable `tsdown` package entry plus postbuild JSON asset copy so installed runtime can contain/verifiably expose M5 registry/schema/seed files.

## Build/package

- Requested approved build command: `/home/stickai/.local/share/pnpm/pnpm build`
- Actual successful build command: `/home/stickai/.openclaw/workspace/tmp/openclaw-start-ack-pnpm-shim/pnpm build`
- Package command: `npm pack --ignore-scripts`
- Tarball: `/home/stickai/.openclaw/workspace/tmp/umc-m5-package/openclaw-2026.5.7.tgz`
- SHA256: `13850f7bd15224e295cc4bee6be184e4df3cd29ab30f191d6a757cd088bdcc06`
- Size: `23629030` bytes

## Tarball content validation

Present in tarball:

- `dist/auto-reply/reply/umc-m5-capability-manifest.js`
  - SHA256: `62c71597611586c90a1b54c938ab24cd4b5778cfabad8916552b9f4fd2853a99`
- `dist/auto-reply/reply/umc-m5-capability-manifest.schema.json`
  - SHA256: `4bfd667c7c390d3d53610c923a49a155eed2ebfec6d0f3e7230d5e250ad5384f`
- `dist/auto-reply/reply/umc-m5-seed-manifests.json`
  - SHA256: `38d3df45abd70322a53fe1f01da9d853ebf943dec68955c3772d7245d6405dd7`
- `dist/auto-reply/reply/umc-m4-verified-route.js`
- `dist/extensions/telegram/openclaw.plugin.json`
  - SHA256: `a3bd23650c86763689c3c9227d13928ee78d4546e0b8e39864f440d926cc40bd`

## Installed package root

`/home/stickai/.npm-global/lib/node_modules/openclaw`

## Expected installed files changed/added

- `dist/auto-reply/reply/umc-m5-capability-manifest.js`
- `dist/auto-reply/reply/umc-m5-capability-manifest.schema.json`
- `dist/auto-reply/reply/umc-m5-seed-manifests.json`

## Required backup before install

Backup path:

`/home/stickai/.openclaw/backups/openclaw-m5-capability-manifest-install-20260716T0124Z/openclaw-installed-package`

Trusted previous backup:

`/home/stickai/.openclaw/backups/openclaw-m4-verified-route-install-20260716T0022Z/openclaw-installed-package`

## Exact approved install sequence if this card is approved

### 1. Backup installed package

```sh
mkdir -p /home/stickai/.openclaw/backups/openclaw-m5-capability-manifest-install-20260716T0124Z && cp -a /home/stickai/.npm-global/lib/node_modules/openclaw /home/stickai/.openclaw/backups/openclaw-m5-capability-manifest-install-20260716T0124Z/openclaw-installed-package && test -f /home/stickai/.openclaw/backups/openclaw-m5-capability-manifest-install-20260716T0124Z/openclaw-installed-package/package.json
```

### 2. Verify tarball SHA256 before install

```sh
printf '%s  %s\n' 13850f7bd15224e295cc4bee6be184e4df3cd29ab30f191d6a757cd088bdcc06 /home/stickai/.openclaw/workspace/tmp/umc-m5-package/openclaw-2026.5.7.tgz | sha256sum -c -
```

### 3. Install package

```sh
npm install -g --ignore-scripts /home/stickai/.openclaw/workspace/tmp/umc-m5-package/openclaw-2026.5.7.tgz
```

### 4. Restart Gateway for activation

```sh
openclaw gateway restart
```

## Rollback readiness

Rollback tarball:

`/home/stickai/.openclaw/workspace/tmp/umc-m4-package-r2/openclaw-2026.5.7.tgz`

Rollback tarball SHA256:

`6a2ec7a2318c8e56a565524f938831ca5d2a2de965e6e16bd2fbc5f4acd2f663`

Rollback command, only if required and approved:

```sh
npm install -g --ignore-scripts /home/stickai/.openclaw/workspace/tmp/umc-m4-package-r2/openclaw-2026.5.7.tgz && openclaw gateway restart
```

## Gateway/Telegram health validation plan

- Gateway: `openclaw gateway status` must report running, connectivity OK, admin-capable.
- Telegram: `openclaw channels status` must report Telegram enabled/configured/running/connected.
- No Telegram send/probe is authorized.
- CPU/event-loop degradation remains a watch item; block only if it worsens, correlates with health/readback failure, or violates gates.

## Installed-runtime verification plan

- Verify installed M5 registry JS exists and exports M5 helpers.
- Verify installed M5 schema and seed manifest JSON exist and parse.
- Verify valid manifest PASS, missing manifest HOLD, malformed manifest FAIL, unsupported capabilities HOLD, fallback without contract preservation blocked.
- Verify manifest cannot forge VerifiedRoute, cannot bypass M4 firewall, and cannot enable production authority.

## M3/M4 regression plan

M3 no-send/mock regression must preserve:

- ContractEnvelope
- ShadowObservationReceipt
- UniversalContractReceipt
- DeliveryReceipt mode `no_send`
- TerminalContractCloseout
- production path unchanged
- all forbidden counters zero

M4 regression must reject before execution:

- raw provider/model
- missing VerifiedRoute
- forged VerifiedRoute
- deserialized/untrusted route
- fallback without VerifiedRoute

## No-send/no-authority boundary

Not authorized:

- Telegram send/probe
- external send
- provider/model live call
- route/config production mutation
- durable memory mutation
- Context Bridge mutation
- production authority change
- cron re-enable
- M6
- enforcement

## Approval state

Awaiting explicit operator approval for this exact M5 install card/sequence. Do not use stale M4 approval cards.
