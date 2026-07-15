# M3 Source-Build Install Approval Card

Status: `HOLD_M3_SOURCE_BUILD_DEPENDENCY_HYDRATION_AWAITING_APPROVAL`

Actionability: **not actionable as an install card yet**.

Reason: the documented package manager is `pnpm@10.33.2`, but source-build validation failed before test/build execution with `pnpm: command not found`. I did not hydrate/install package tooling without explicit approval.

## Selected source path

`/home/stickai/.openclaw/worktrees/umc-m3g-observe-only-hook-source-20260711`

- Branch: `evidence/umc-m3g-observe-only-hook-source-20260711`
- Source commit to validate/install later: `a65a4ee34ef2322b441c0c579cb89666e3db0ce4`

## Build/package command

```sh
pnpm build
mkdir -p .artifacts/umc-m3-source-build-package
pnpm pack --pack-destination .artifacts/umc-m3-source-build-package
```

## Package/tarball

- Produced: no
- Path: blocked
- SHA256: blocked
- Blocker: `pnpm: command not found`

## Installed package root

`/home/stickai/.npm-global/lib/node_modules/openclaw`

## Expected files/classes to change

Final exact installed-file list is pending tarball production and package diff.

Source-intended changes:

- `src/auto-reply/reply/followup-runner.ts`
- `src/auto-reply/reply/followup-runner.test.ts`
- `src/auto-reply/reply/umc-m3-envelope-supervision.ts`

Installed expected classes after a validated package install:

- dist followup-runner chunk containing existing M2 queued route-admission hook plus M3 receipt wiring
- dist M3 envelope supervisor chunk/file containing `ContractEnvelope`, `ShadowObservationReceipt`, `ToolSupervisionReceipt`, `DeliveryReceipt(mode=no_send)`, `UniversalContractReceipt`, `TerminalContractCloseout`
- package metadata and plugin manifests preserved by npm package topology

## Plugin manifest preservation checks

Pending package production. Required checks after tarball exists:

```sh
tar -tf <package.tgz> | grep openclaw.plugin.json
# compare packaged plugin manifest list against installed package manifest list
# verify required bundled-plugin package.json files are preserved
```

## Backup path

Planned, not created:

`/home/stickai/.openclaw/backups/openclaw-m3-source-build-install-<UTC>/openclaw-installed-package/`

## Rollback command template

Not executable until backup exists:

```sh
openclaw gateway status && rsync -a --delete <backup_path>/ /home/stickai/.npm-global/lib/node_modules/openclaw/ && openclaw gateway restart
```

Gateway restart required for install/rollback: yes.  
Gateway restarted now: no.

## Gateway / Telegram read-only health checks

After install approval only:

- `openclaw gateway status`
- `channels.status probe=false` for Telegram readback only
- no Telegram send/probe

## Installed-runtime M3 verification checks

After install approval and restart only:

- grep installed dist for `ContractEnvelope`, `ShadowObservationReceipt`, `ToolSupervisionReceipt`, `DeliveryReceipt`, `UniversalContractReceipt`, `TerminalContractCloseout`
- verify `DeliveryReceipt` mode `no_send`
- verify `production_path` unchanged
- verify M2 route-admission hook terms remain present
- run installed-runtime no-send fixture with fixture-only env
- verify zero provider/model shadow calls, zero Telegram sends, zero external sends, zero real write tools

## M3O rerun plan

Planned after explicit install approval and restart only: owner-turn shadow observation in no-send mode. No M3O rerun was performed now.

## No-send / no-authority boundary now

- installed runtime mutation: 0
- direct dist hotpatch: 0
- package install: 0
- Gateway restart: 0
- Telegram send/probe: 0
- external send: 0
- provider/model shadow call: 0
- route/config mutation: 0
- durable memory mutation: 0
- Context Bridge mutation: 0
- production authority change: 0
- M3O rerun: 0
- M3P/M4/enforcement: not started

## Next required approval

`APPROVE_M3_SOURCE_BUILD_DEPENDENCY_HYDRATION`

After dependency/package-manager hydration and a passing package validation, the later install phase remains:

`APPROVE_M3_SOURCE_BUILD_STAGED_INSTALL`
