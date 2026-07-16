# M7 Model Eligibility Staged Install Approval Card

Status: `HOLD_M7_MODEL_ELIGIBILITY_INSTALL_AWAITING_OPERATOR_APPROVAL`

## Approval boundary

Do **not** install until Stick explicitly approves this card.

No Telegram send/probe. No external send. No live provider/model call. No config/route mutation beyond the approved staged runtime install. No durable memory mutation. No Context Bridge mutation. No production authority change. No enforcement. No M8.

Prior read-only helper approval cards from allowlist misses are stale and are **not** part of this approval.

## Selected source

- Source path: `/home/stickai/.openclaw/worktrees/umc-m3g-observe-only-hook-source-20260711`
- Branch: `evidence/umc-m3g-observe-only-hook-source-20260711`
- Source head to install: `1557ff822e0c9b86eded7c827543bf4866676671`
- Source-ready base commit: `73bb16549c73fab52b2d0fcbac0b2fbf35c52b8c`
- Source-ready evidence commit: `6105e2306ad25ec8ac50cb65f51bae5aff2f8637`

Note: source head includes the M7 source-ready commit plus a staged-install compatibility repair preserving M6 no-arg installed-regression behavior under the source-build package topology.

## Build/package

- Build command: `/home/stickai/.openclaw/workspace/tmp/openclaw-start-ack-pnpm-shim/pnpm build`
- Package command: `npm pack --ignore-scripts --pack-destination /home/stickai/.openclaw/workspace/tmp/umc-m7-package`
- Tarball: `/home/stickai/.openclaw/workspace/tmp/umc-m7-package/openclaw-2026.5.7.tgz`
- SHA256: `8814f2ee8e0cd5a6b7fbf8ba52f80f497a468404513ea865af9a729a8cd37717`
- Size: `23635839` bytes
- Extracted package validation: `PASS_M7_PACKAGE_EXTRACT_R2_VALIDATION`

## Installed package root

`/home/stickai/.npm-global/lib/node_modules/openclaw`

## Exact files expected to change

1. Add M7 runtime entry:
   - `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/auto-reply/reply/umc-m7-model-eligibility.js`
   - New SHA256: `d7de6cb9f6f4dc1006f0062fb77070535eb7198712647a4f152acce876191789`

2. Replace M6 entry with source-build chunk shim:
   - `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/auto-reply/reply/umc-m6-contract-build-lane.js`
   - Current SHA256: `5af495a685bc40fcbd8ebc51eea9d3785f93c76b26c59227981ed305f52ca2ac`
   - New SHA256: `9fb2893b5cc7c7a75c7aa15b93d3cfee53eac164970485ad597d72a47f7e8bbc`

3. Add M6 implementation chunk:
   - `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/umc-m6-contract-build-lane-B49r9Ao5.js`
   - New SHA256: `8416342de89bf8e525f477c4255c59b54f0a5a624d8a1c02dd2e783aa51a397a`

Preserved hashes:

- `package.json`: `9585403b5d52ef6b56a6faf6b958eb1ae22d14f7a581def93da13b597087b0ad`
- M4 VerifiedRoute: `9012c1d9ef5e651dfcf3b0dff533fa33b5ce08f226e21d3a7733b8faef02cff6`
- M5 capability manifest: `e5a1d1c32a97ace2fe33cc151d98bd8ff4afed17ae768a7cf351319ef15adfe2`
- Telegram plugin manifest: `a3bd23650c86763689c3c9227d13928ee78d4546e0b8e39864f440d926cc40bd`

## Backup

Backup path:

`/home/stickai/.openclaw/backups/openclaw-m7-model-eligibility-install-20260716T041957Z/openclaw-installed-package`

Backup command:

```sh
mkdir -p /home/stickai/.openclaw/backups/openclaw-m7-model-eligibility-install-20260716T041957Z && cp -a /home/stickai/.npm-global/lib/node_modules/openclaw /home/stickai/.openclaw/backups/openclaw-m7-model-eligibility-install-20260716T041957Z/openclaw-installed-package
```

## Approved install sequence, if explicitly approved

```sh
sha256sum /home/stickai/.openclaw/workspace/tmp/umc-m7-package/openclaw-2026.5.7.tgz
mkdir -p /home/stickai/.openclaw/backups/openclaw-m7-model-eligibility-install-20260716T041957Z && cp -a /home/stickai/.npm-global/lib/node_modules/openclaw /home/stickai/.openclaw/backups/openclaw-m7-model-eligibility-install-20260716T041957Z/openclaw-installed-package
npm install -g --ignore-scripts /home/stickai/.openclaw/workspace/tmp/umc-m7-package/openclaw-2026.5.7.tgz
openclaw gateway restart
```

Gateway restart is required because the global installed runtime changes and the running Gateway must reload the new package before installed-runtime verification.

## Rollback readiness

Rollback command:

```sh
npm install -g --ignore-scripts /home/stickai/.openclaw/workspace/tmp/umc-m6-package/openclaw-2026.5.7.tgz && openclaw gateway restart
```

Trusted M6 tarball SHA256: `4f3d07373f51a8a302078c9f72a5416775a4983db3486c7a9a14cda5a09b888d`

## Health checks

- Pre-install Gateway: `PASS_RUNNING_CONNECTIVITY_OK_ADMIN_CAPABLE`
- Pre-install Telegram: `PASS_ENABLED_CONFIGURED_RUNNING_CONNECTED`
- Post-restart Gateway: `openclaw gateway status` must report running/connectivity OK/admin-capable
- Post-restart Telegram: `openclaw channels status` must report Telegram enabled/configured/running/connected; no send/probe

## Installed-runtime verification plan

M7 must verify policy, fallback matrix, checker, fallback equivalence contract, eligible primary/fallback PASS, missing manifest HOLD, malformed manifest FAIL, unsupported no-send/ContractEnvelope/DeliveryReceipt HOLD, fallback contract/drop mode changes blocked, raw provider/model rejected, session/channel pin non-authority, worker route-authority false, production authority disabled, enforcement disabled.

## Regression plan

- M3 envelope/no-send receipt path still passes
- M4 VerifiedRoute/firewall still blocks raw provider/model authority
- M5 manifests still gate route eligibility
- M6 contract-build lane still builds valid contract-qualified lane, including no-arg installed-regression compatibility
- M7 fallback preservation remains enforced

## No-send/no-authority boundary

- Telegram send/probe count: `0`
- External send count: `0`
- Provider/model live call count: `0`
- Route/config mutation count before approval: `0`
- Durable memory mutation count: `0`
- Context Bridge mutation count: `0`
- Production authority change count: `0`
- Enforcement enabled: `false`
- M8 started: `false`

## Operator approval text

Approve M7 staged install of tarball `/home/stickai/.openclaw/workspace/tmp/umc-m7-package/openclaw-2026.5.7.tgz` with SHA256 `8814f2ee8e0cd5a6b7fbf8ba52f80f497a468404513ea865af9a729a8cd37717`, backup to `/home/stickai/.openclaw/backups/openclaw-m7-model-eligibility-install-20260716T041957Z/openclaw-installed-package`, `npm install -g --ignore-scripts`, and Gateway restart.
