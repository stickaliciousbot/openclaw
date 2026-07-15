# M3 Source-Build Staged Install Approval Card

Status: `HOLD_M3_SOURCE_BUILD_STAGED_INSTALL_AWAITING_OPERATOR_APPROVAL`

Approval token: `APPROVE_M3_SOURCE_BUILD_STAGED_INSTALL`

## Source

- Selected source path: `/home/stickai/.openclaw/worktrees/umc-m3g-observe-only-hook-source-20260711`
- Branch: `evidence/umc-m3g-observe-only-hook-source-20260711`
- Source HEAD: `31a06c6cb64d52097e51f23b27898eff88e419ba`
- Source commits:
  - `a65a4ee34ef2322b441c0c579cb89666e3db0ce4`
  - `31a06c6cb64d52097e51f23b27898eff88e419ba`

## Validation already completed

- Dependency hydration: PASS — `corepack pnpm install --frozen-lockfile --store-dir "$PWD/.pnpm-store"`
- Focused Vitest: PASS — 6 passed / 30 skipped
- Build: PASS — `corepack pnpm build`
- Pack: PASS — tarball produced
- Tarball/plugin topology: PASS
- M3 symbols in tarball: PASS

## Package tarball

Path:

`/home/stickai/.openclaw/worktrees/umc-m3g-observe-only-hook-source-20260711/.artifacts/umc-m3-source-build-package/openclaw-2026.5.7.tgz`

SHA256:

`85baafd1b82e8e3aba6d4e11a5a3231dddc6b2cf8820ce74c31e8e2e71855801`

Size: `24530808` bytes  
Entries: `9715`

## Expected installed changes

Installed root:

`/home/stickai/.npm-global/lib/node_modules/openclaw`

Full bounded diff manifest:

`/home/stickai/.openclaw/worktrees/umc-m3g-observe-only-hook-source-20260711/.artifacts/umc-m3-source-build-package/tarball_to_installed_diff_bounded.json`

Manifest SHA256:

`e794fc9b2f68b6769f5bd06e72b16fa0cc4ee0a3bc8a034fd6d4a07e5fee134e`

Summary:

- Tarball files: `9715`
- Same vs installed: `5631`
- Changed: `1152`
- Added: `2932`
- Removed in bounded package dirs if package root is replaced from tarball: `2942`

Runtime chunk transition:

- Before: `dist/agent-runner.runtime-a09vVD0N.js`, `dist/agent-runner.runtime.js`
- After: `dist/agent-runner.runtime-DESbFJnG.js`, `dist/agent-runner.runtime.js`

Key added files:

- `dist/agent-runner.runtime-DESbFJnG.js`
- `dist/extensions/zalo/package.json`
- `dist/extensions/zalouser/package.json`
- `dist/plugin-sdk/src/auto-reply/reply/umc-m3-envelope-supervision.d.ts`

Key removed files if package root is replaced from tarball:

- `dist/agent-runner.runtime-a09vVD0N.js`
- `dist/agent-runner.runtime-a09vVD0N.js.bak-umc-m2q-20260711T0538Z`

Key changed files include:

- `dist/agent-runner.runtime.js`
- `dist/plugin-sdk/src/auto-reply/reply/followup-runner.d.ts`
- `package.json`

## Plugin manifest preservation

- Tarball plugin manifests: `94`
- Installed plugin manifests: `94`
- Missing from tarball vs installed: none
- Extra in tarball vs installed: none
- Tarball extension `package.json`: `93`
- Installed extension `package.json`: `91`
- Extra package.json entries in tarball: `zalo`, `zalouser`
- Missing package.json entries from tarball: none

## M3/M2 runtime symbols in tarball

Runner file: `dist/agent-runner.runtime-DESbFJnG.js`

Present:

- `ContractEnvelope`
- `ShadowObservationReceipt`
- `ToolSupervisionReceipt`
- `DeliveryReceipt`
- `UniversalContractReceipt`
- `TerminalContractCloseout`
- `PASS_M3_TERMINAL_CONTRACT_CLOSEOUT_EMITTED`
- `mode: "no_send"`
- `production_path`
- `resolveUmcV1DefaultRouteFromConfig`
- `applyUmcV1QueuedRouteAdmission`
- `umcV1QueuedRouteIntent`

## Backup path

`/home/stickai/.openclaw/backups/openclaw-m3-source-build-install-20260715T163100Z/openclaw-installed-package`

## Staged install command — for later approval only

```sh
set -euo pipefail
SRC_TARBALL='/home/stickai/.openclaw/worktrees/umc-m3g-observe-only-hook-source-20260711/.artifacts/umc-m3-source-build-package/openclaw-2026.5.7.tgz'
EXPECTED_SHA='85baafd1b82e8e3aba6d4e11a5a3231dddc6b2cf8820ce74c31e8e2e71855801'
INSTALL_ROOT='/home/stickai/.npm-global/lib/node_modules/openclaw'
BACKUP_ROOT='/home/stickai/.openclaw/backups/openclaw-m3-source-build-install-20260715T163100Z/openclaw-installed-package'
sha256sum "$SRC_TARBALL" | grep -F "$EXPECTED_SHA"
mkdir -p "$(dirname "$BACKUP_ROOT")"
rsync -a --delete "$INSTALL_ROOT/" "$BACKUP_ROOT/"
npm install -g "$SRC_TARBALL"
openclaw gateway restart
openclaw gateway status
```

## Rollback command — for later approval only

```sh
set -euo pipefail
INSTALL_ROOT='/home/stickai/.npm-global/lib/node_modules/openclaw'
BACKUP_ROOT='/home/stickai/.openclaw/backups/openclaw-m3-source-build-install-20260715T163100Z/openclaw-installed-package'
test -d "$BACKUP_ROOT"
rsync -a --delete "$BACKUP_ROOT/" "$INSTALL_ROOT/"
openclaw gateway restart
openclaw gateway status
```

## Gateway / Telegram read-only checks after install

- `openclaw gateway status`
- `channels.status` with `probe=false` for Telegram readback only
- No Telegram send/probe

## Installed-runtime M3 verification after install

- Verify installed runtime chunk exists or map chunk if npm rewrites names.
- Grep installed dist for M3 receipt symbols.
- Grep installed dist for `mode: "no_send"` and `production_path`.
- Grep installed dist for M2 route-admission symbols.
- Run installed-runtime no-send fixture only; verify zero provider/model shadow call, zero Telegram send, zero external send, zero write-tool execution.
- Run Telegram `channels.status probe=false` only.

## M3O rerun plan

Planned only after explicit staged install approval, Gateway restart, installed-runtime M3 verification PASS, and Telegram readback `probe=false` PASS.

Mode: owner-turn shadow observation `no_send`.

Still forbidden:

- shadow Telegram sends
- external sends
- provider/model live shadow calls
- real write tools
- route/fallback/config production mutation
- production authority change

## Boundary now

No install was performed while preparing this card.

- installed runtime mutation: `0`
- direct dist hotpatch: `0`
- package install into npm-global: `0`
- Gateway restart: `0`
- Telegram send/probe: `0`
- external send: `0`
- provider/model shadow call: `0`
- route/config mutation: `0`
- durable memory mutation: `0`
- Context Bridge mutation: `0`
- production authority change: `0`
- M3O rerun: `0`
- M3P/M4/enforcement: not started
