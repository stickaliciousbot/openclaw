# M10A Control Path Install Approval Card

Status: `HOLD_M10A_CONTROL_PATH_INSTALL_AWAITING_OPERATOR_APPROVAL`

No install has been run. This card requests approval to install the M10A control-path module only. It does **not** enable M10A, approve production enforcement, or change production authority.

## Selected source

- Source path: `/home/stickai/.openclaw/worktrees/umc-m3g-observe-only-hook-source-20260711`
- Source branch/head: `evidence/umc-m3g-observe-only-hook-source-20260711` @ `7fbb19038154e1b4c8bb2545f4b29547505185d9`
- Source commit to install: `7fbb19038154e1b4c8bb2545f4b29547505185d9`

## Build/package

- Source build command used: `npm_execpath=/home/stickai/.openclaw/workspace/tmp/umc-m10a-pnpm-runner/pnpm.js node scripts/build-all.mjs gatewayWatch`
- Pack command used: `npm pack --ignore-scripts --pack-destination /home/stickai/.openclaw/workspace/tmp/umc-m10a-package`
- Tarball: `/home/stickai/.openclaw/workspace/tmp/umc-m10a-package/openclaw-2026.5.7.tgz`
- Tarball SHA256: `6c680ce7572099b930ec6c1739f8b93be6b6964f5d25c10978a3714073c24a8c`
- M10A dist entry: `package/dist/auto-reply/reply/umc-m10a-owner-telegram-direct-control-path.js`
- M10A dist entry SHA256: `be56d6a5105d4d0a03085757483b3bb07374ff96b9db8ea44a1bcb164139e082`

## Installed target

- Installed package root: `/home/stickai/.npm-global/lib/node_modules/openclaw`
- Exact file expected to change:
  - Add `dist/auto-reply/reply/umc-m10a-owner-telegram-direct-control-path.js` with SHA256 `be56d6a5105d4d0a03085757483b3bb07374ff96b9db8ea44a1bcb164139e082`
- Pre-install readback: M10A installed dist file is absent.

## Required preservation checks before install

- `package.json`: `9585403b5d52ef6b56a6faf6b958eb1ae22d14f7a581def93da13b597087b0ad`
- Telegram plugin manifest: `a3bd23650c86763689c3c9227d13928ee78d4546e0b8e39864f440d926cc40bd`
- M4 dist: `9012c1d9ef5e651dfcf3b0dff533fa33b5ce08f226e21d3a7733b8faef02cff6`
- M5 dist: `e5a1d1c32a97ace2fe33cc151d98bd8ff4afed17ae768a7cf351319ef15adfe2`
- M6 dist: `9fb2893b5cc7c7a75c7aa15b93d3cfee53eac164970485ad597d72a47f7e8bbc`
- M7 dist: `85e80863ee7720453e57c62b5c7955a681a0e8398e80a9ab9d026fcb66c4f996`
- M8 dist: `27116a4374b699b7e98bc8ec9be98f3584bc14a8ca740d0723316deaa66088db`

## Backup

- Backup path: `/home/stickai/.openclaw/backups/openclaw-m10a-control-path-install-20260716T111530Z/openclaw-installed-package`
- Backup command:

```sh
mkdir -p /home/stickai/.openclaw/backups/openclaw-m10a-control-path-install-20260716T111530Z && cp -a /home/stickai/.npm-global/lib/node_modules/openclaw /home/stickai/.openclaw/backups/openclaw-m10a-control-path-install-20260716T111530Z/openclaw-installed-package
```

## Install command requiring approval

```sh
set -euo pipefail
TARBALL=/home/stickai/.openclaw/workspace/tmp/umc-m10a-package/openclaw-2026.5.7.tgz
EXPECTED_SHA256=6c680ce7572099b930ec6c1739f8b93be6b6964f5d25c10978a3714073c24a8c
echo "$EXPECTED_SHA256  $TARBALL" | sha256sum -c -
mkdir -p /home/stickai/.openclaw/backups/openclaw-m10a-control-path-install-20260716T111530Z
cp -a /home/stickai/.npm-global/lib/node_modules/openclaw /home/stickai/.openclaw/backups/openclaw-m10a-control-path-install-20260716T111530Z/openclaw-installed-package
npm install -g --ignore-scripts "$TARBALL"
```

## Gateway restart requirement

Gateway restart is required after the approved package install to load the staged runtime. Use the first-class `gateway.restart` tool. No restart has been run.

## Rollback readiness

Rollback command, if the staged install fails or validation requires rollback:

```sh
rm -rf /home/stickai/.npm-global/lib/node_modules/openclaw && cp -a /home/stickai/.openclaw/backups/openclaw-m10a-control-path-install-20260716T111530Z/openclaw-installed-package /home/stickai/.npm-global/lib/node_modules/openclaw && openclaw gateway restart
```

Post-rollback readback must show Gateway read-only health OK, Telegram read-only health OK, M10A installed module absent or disabled, production authority false, and broad enforcement false.

## Health checks

- Gateway before install: `PASS_GATEWAY_READ_ONLY_HEALTH_OK`
- Telegram before install: `PASS_TELEGRAM_READ_ONLY_HEALTH_OK`
- Required after restart: Gateway read-only health + Telegram read-only health
- Telegram send/probe remains forbidden.

## Installed-runtime M10A verification plan

- M10A control module present
- M10A schema/status/readback path present
- M10A disabled by default
- `production_authority=false`
- `broad_enforcement=false`
- external sends/provider calls/write tools/durable memory mutation/Context Bridge mutation all false
- Telegram direct owner scope and owner chat id `8495203551` encoded
- Web UI, LAN/browser, and external surfaces excluded

## M2-M9 regression plan

Run installed-runtime M10A regression equivalent proving M2-M9 still pass and no send/provider/config/memory/context/authority mutation occurs.

## Enable/disable dry-run validation plan

Fixture/mock dry-run only:

- Exact owner Telegram direct enable accepted
- Wrong owner rejected
- Web UI rejected
- External sends rejected
- Provider calls rejected
- Memory mutation rejected
- Context Bridge mutation rejected
- Off-switch returns disabled state
- Status/readback reports disabled after off-switch

## No-production-authority boundary

Must remain clean:

- M10A enabled: `false`
- Production authority change: `0`
- Broad enforcement: `false`
- Telegram send/probe: `0`
- External send: `0`
- Provider/model live call: `0`
- Write tool execution: `0`
- Durable memory mutation: `0`
- Context Bridge mutation: `0`
- Route/config production mutation: `0`

## Operator decision required

Approve or deny this exact staged install. Stop here until explicit approval.
