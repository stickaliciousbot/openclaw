# M8 Owner Contract Lane Install Approval Card

Status: `HOLD_M8_OWNER_CONTRACT_LANE_INSTALL_AWAITING_OPERATOR_APPROVAL`

No install has been run. This card requests explicit approval for the exact M8 staged source-build install below.

## Selected source

- Source path: `/home/stickai/.openclaw/worktrees/umc-m3g-observe-only-hook-source-20260711`
- Source branch/head: `evidence/umc-m3g-observe-only-hook-source-20260711` @ `e233663c2eed9ced3b97a6dc3bd015c1554f5c10`
- Source commit to install: `e233663c2eed9ced3b97a6dc3bd015c1554f5c10`

## Build/package

- Build command: `/home/stickai/.openclaw/workspace/tmp/openclaw-start-ack-pnpm-shim/pnpm build`
- Pack command: `npm pack --ignore-scripts --pack-destination /home/stickai/.openclaw/workspace/tmp/umc-m8-package`
- Tarball: `/home/stickai/.openclaw/workspace/tmp/umc-m8-package/openclaw-2026.5.7.tgz`
- Tarball SHA256: `c9b71a74644e871b413d1a5f7b1d3110934a99b39ca16758b6f8596483200da7`
- M8 dist entry SHA256: `ab0b66fb9578f1b99320b46590825a1a956a83152d5c653f0d00ca2386cdb44f`

## Installed target

- Installed package root: `/home/stickai/.npm-global/lib/node_modules/openclaw`
- Exact file expected to change:
  - Add `dist/auto-reply/reply/umc-m8-owner-contract-lane.js` with SHA256 `ab0b66fb9578f1b99320b46590825a1a956a83152d5c653f0d00ca2386cdb44f`

## Required preservation checks

- `package.json`: `9585403b5d52ef6b56a6faf6b958eb1ae22d14f7a581def93da13b597087b0ad`
- Telegram plugin manifest: `a3bd23650c86763689c3c9227d13928ee78d4546e0b8e39864f440d926cc40bd`
- M4 dist: `9012c1d9ef5e651dfcf3b0dff533fa33b5ce08f226e21d3a7733b8faef02cff6`
- M5 dist: `e5a1d1c32a97ace2fe33cc151d98bd8ff4afed17ae768a7cf351319ef15adfe2`
- M6 entry: `9fb2893b5cc7c7a75c7aa15b93d3cfee53eac164970485ad597d72a47f7e8bbc`
- M6 chunk: `8416342de89bf8e525f477c4255c59b54f0a5a624d8a1c02dd2e783aa51a397a`
- M7 dist: `d7de6cb9f6f4dc1006f0062fb77070535eb7198712647a4f152acce876191789`

## Backup

- Backup path: `/home/stickai/.openclaw/backups/openclaw-m8-owner-contract-lane-install-20260716T0519Z/openclaw-installed-package`
- Backup command:

```sh
mkdir -p /home/stickai/.openclaw/backups/openclaw-m8-owner-contract-lane-install-20260716T0519Z && cp -a /home/stickai/.npm-global/lib/node_modules/openclaw /home/stickai/.openclaw/backups/openclaw-m8-owner-contract-lane-install-20260716T0519Z/openclaw-installed-package
```

## Install command requiring approval

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

- M7 backup available: `/home/stickai/.openclaw/backups/openclaw-m7-model-eligibility-install-20260716T041957Z/openclaw-installed-package`

## Health checks

- Gateway before install: `PASS_RUNNING_CONNECTIVITY_OK_ADMIN_CAPABLE`
- Telegram before install: `PASS_ENABLED_CONFIGURED_RUNNING_CONNECTED`
- Required after restart: Gateway health + Telegram read-only health
- Telegram send/probe remains forbidden.

## Installed-runtime M8 verification plan

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

## M3/M4/M5/M6/M7 regression plan

- M3 envelope/no-send receipts still pass
- M4 raw provider/model bypass still blocked
- M5 manifests still gate route eligibility
- M6 contract-build lane still builds valid lane
- M7 model/fallback eligibility still passes
- Fallback contract preservation still enforced
- Worker model route authority remains false

## Enforced no-send canary validation plan

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

Approve or deny this exact staged install. Stop here until explicit approval.
