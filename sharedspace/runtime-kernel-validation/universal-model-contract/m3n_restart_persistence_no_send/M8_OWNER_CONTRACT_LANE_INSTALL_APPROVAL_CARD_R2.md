# M8 Owner Contract Lane Install Approval Card R2

Status: `HOLD_M8_OWNER_CONTRACT_LANE_INSTALL_R2_AWAITING_OPERATOR_APPROVAL`

**R1 is superseded and must not be used.** No install has been run.

R2 correction: the exact M8 source-build tarball adds M8 **and** replaces the M7 dist entry. The M7 replacement is now explicitly in scope and must pass post-install M7 regression.

## Selected source

- Source path: `/home/stickai/.openclaw/worktrees/umc-m3g-observe-only-hook-source-20260711`
- Source branch/head: `evidence/umc-m3g-observe-only-hook-source-20260711` @ `e233663c2eed9ced3b97a6dc3bd015c1554f5c10`
- Source commit to install: `e233663c2eed9ced3b97a6dc3bd015c1554f5c10`

## Build/package

- Build command: `/home/stickai/.openclaw/workspace/tmp/openclaw-start-ack-pnpm-shim/pnpm build`
- Pack command: `npm pack --ignore-scripts --pack-destination /home/stickai/.openclaw/workspace/tmp/umc-m8-package`
- Tarball: `/home/stickai/.openclaw/workspace/tmp/umc-m8-package/openclaw-2026.5.7.tgz`
- Tarball SHA256: `c9b71a74644e871b413d1a5f7b1d3110934a99b39ca16758b6f8596483200da7`

## Installed target

- Installed package root: `/home/stickai/.npm-global/lib/node_modules/openclaw`

Exact files expected to change:

1. Replace `dist/auto-reply/reply/umc-m7-model-eligibility.js`
   - Before: `d7de6cb9f6f4dc1006f0062fb77070535eb7198712647a4f152acce876191789`
   - After expected: `85e80863ee7720453e57c62b5c7955a681a0e8398e80a9ab9d026fcb66c4f996`
   - Required regression: `PASS_M7_MODEL_ELIGIBILITY_AND_FALLBACK_EQUIVALENCE_INSTALLED_REGRESSION`

2. Add `dist/auto-reply/reply/umc-m8-owner-contract-lane.js`
   - After expected: `ab0b66fb9578f1b99320b46590825a1a956a83152d5c653f0d00ca2386cdb44f`
   - Required verification: `PASS_M8_OWNER_CONTRACT_LANE_INSTALLED_RUNTIME_VERIFIED`

## Required preservation checks

- `package.json`: `9585403b5d52ef6b56a6faf6b958eb1ae22d14f7a581def93da13b597087b0ad`
- Telegram plugin manifest: `a3bd23650c86763689c3c9227d13928ee78d4546e0b8e39864f440d926cc40bd`
- M4 dist: `9012c1d9ef5e651dfcf3b0dff533fa33b5ce08f226e21d3a7733b8faef02cff6`
- M5 dist: `e5a1d1c32a97ace2fe33cc151d98bd8ff4afed17ae768a7cf351319ef15adfe2`
- M6 dist entry: `9fb2893b5cc7c7a75c7aa15b93d3cfee53eac164970485ad597d72a47f7e8bbc`

## Backup

- Backup path: `/home/stickai/.openclaw/backups/openclaw-m8-owner-contract-lane-install-r2-20260716T0524Z/openclaw-installed-package`
- Backup command:

```sh
mkdir -p /home/stickai/.openclaw/backups/openclaw-m8-owner-contract-lane-install-r2-20260716T0524Z && cp -a /home/stickai/.npm-global/lib/node_modules/openclaw /home/stickai/.openclaw/backups/openclaw-m8-owner-contract-lane-install-r2-20260716T0524Z/openclaw-installed-package
```

## Install command requiring R2 approval

```sh
npm install -g --ignore-scripts /home/stickai/.openclaw/workspace/tmp/umc-m8-package/openclaw-2026.5.7.tgz
```

Before install, verify:

```sh
sha256sum /home/stickai/.openclaw/workspace/tmp/umc-m8-package/openclaw-2026.5.7.tgz
```

Expected SHA256: `c9b71a74644e871b413d1a5f7b1d3110934a99b39ca16758b6f8596483200da7`

## Gateway restart requirement

Gateway restart is required after install to load the staged runtime, using the first-class `gateway.restart` tool / SIGUSR1 safe restart. No restart has been run.

## Rollback readiness

- Rollback tarball: `/home/stickai/.openclaw/workspace/tmp/umc-m7-package/openclaw-2026.5.7.tgz`
- Rollback tarball SHA256: `8814f2ee8e0cd5a6b7fbf8ba52f80f497a468404513ea865af9a729a8cd37717`
- Rollback command:

```sh
npm install -g --ignore-scripts /home/stickai/.openclaw/workspace/tmp/umc-m7-package/openclaw-2026.5.7.tgz && openclaw gateway restart
```

## Health checks

- Gateway before install: `PASS_RUNNING_CONNECTIVITY_OK_ADMIN_CAPABLE`
- Telegram before install: `PASS_ENABLED_CONFIGURED_RUNNING_CONNECTED`
- Required after restart: Gateway health + Telegram read-only health
- Telegram send/probe remains forbidden.

## Verification/regression plan

Installed-runtime M8 verification:

- M8 enforced no-send owner contract lane present
- Contract decisions enforced
- Side effects forbidden
- Delivery mode remains `no_send`
- Authority mode is `enforced_no_send`
- Production authority remains `false`
- Scope is owner-turn contract lane only
- Raw provider/model authority blocked
- Missing receipt / VerifiedRoute / manifest / unsupported fallback cannot PASS
- Tool/postcondition gaps produce HOLD/FAIL
- Live-action canary and broad production enforcement remain disabled

M3/M4/M5/M6/M7 regression:

- M3 envelope/no-send receipts still pass
- M4 raw provider/model bypass still blocked
- M5 manifests still gate route eligibility
- M6 contract-build lane still builds valid lane
- M7 model/fallback eligibility still passes after explicit M7 dist replacement
- Fallback contract preservation still enforced
- Worker model route authority remains false

Enforced no-send canary validation:

- Valid contract produces enforced PASS no-send
- Missing VerifiedRoute produces enforced HOLD/FAIL
- Missing manifest produces enforced HOLD
- Malformed manifest produces enforced FAIL
- Missing ContractEnvelope / DeliveryReceipt / TerminalContractCloseout produces enforced HOLD/FAIL
- DeliveryReceipt mode not `no_send` produces enforced FAIL
- Raw provider/model authority produces enforced FAIL/HOLD
- Fallback contract drop produces enforced HOLD/FAIL
- Side-effect attempt produces enforced FAIL
- Ambient production delivery classified separately

## No-send/no-authority boundary

Must remain clean:

- Telegram send/probe: `0`
- External send: `0`
- Provider/model live call: `0`
- Route/config production mutation: `0`
- Durable memory mutation: `0`
- Context Bridge mutation: `0`
- Production authority change: `0`
- Live-action canary: `false`
- Broad production enforcement: `false`
- M9 started: `false`

## Operator decision required

Approve or deny this exact **R2** staged install. Do not use R1. Stop here until explicit R2 approval.
