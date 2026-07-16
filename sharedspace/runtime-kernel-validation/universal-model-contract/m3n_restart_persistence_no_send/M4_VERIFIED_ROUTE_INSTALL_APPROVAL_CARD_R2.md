# M4 VerifiedRoute Install Approval Card — R2

Status: `HOLD_M4_VERIFIED_ROUTE_INSTALL_AWAITING_OPERATOR_APPROVAL`

## Summary

R2 source/build inclusion repair succeeded. The rebuilt package tarball contains the compiled M4 VerifiedRoute/firewall runtime artifact and passed focused package validation. No install is authorized or performed in this phase.

## Selected source

- Source path: `/home/stickai/.openclaw/worktrees/umc-m3g-observe-only-hook-source-20260711`
- Branch: `evidence/umc-m3g-observe-only-hook-source-20260711`
- Source commit to install if approved: `c0bd5adebeb1b2e59406a87fdb2fac33a01a5777`
- Previous source commit: `e9b3f0ff7b99cb98c70ad303d58d15b71d26d9c5`
- Repair commit message: `Include UMC M4 VerifiedRoute in package build`

## R2 package produced

- Tarball path: `/home/stickai/.openclaw/workspace/tmp/umc-m4-package-r2/openclaw-2026.5.7.tgz`
- SHA256: `6a2ec7a2318c8e56a565524f938831ca5d2a2de965e6e16bd2fbc5f4acd2f663`
- SHA1: `cdf43b1cd91a5198f6d7ecffecc69223711422d0`
- Size: `23625162` bytes
- Total files: `9673`

Old invalid tarball remains rejected: `/home/stickai/.openclaw/workspace/tmp/umc-m4-package/openclaw-2026.5.7.tgz`, SHA256 `92634bc0a599a16a687e4ef50575f8ca8ade7d367afc47a16090949c61b1f7e5`. Do **not** install it.

## Build commands/results

- `/home/stickai/.openclaw/workspace/tmp/openclaw-start-ack-pnpm-shim/pnpm build` — PASS, async approved command `b897a8e1`, code `0`.
- `npm pack --ignore-scripts --pack-destination /home/stickai/.openclaw/workspace/tmp/umc-m4-package-r2` — PASS.
- `ui:build` was not rerun for R2; prior status remains missing UI runner, and no dependency install was approved or performed.

## Package validation

- Contains M4 artifact: `true`
- M4 artifact path: `package/dist/auto-reply/reply/umc-m4-verified-route.js`
- Contains M4 symbols: `true` (`M4_VERIFIED_ROUTE_VERSION`, `VERIFIED_ROUTE_UMC_V1_M4`, `verifyM4RouteIntent`, `enforceM4VerifiedRouteFirewall`)
- Source `dist` has M4 artifact: `true`
- Contains M3 envelope/no-send artifact: `true`
- Contains M2 route-admission symbols: `true`
- Plugin manifest count: `95`
- Telegram manifest present: `true`
- Classification: `PACKAGE_INSTALL_CARD_READY_M4_RUNTIME_ARTIFACT_PRESENT`

## Exact installed package root for future approved install

`/home/stickai/.npm-global/lib/node_modules/openclaw`

## Backup and rollback for future approved install

- Backup path: `/home/stickai/.openclaw/backups/openclaw-m4-verified-route-install-<UTC>/openclaw-installed-package`
- Rollback: restore backed-up installed package root, then use first-class `gateway.restart` only after explicit operator approval.

## Future installed-runtime verification plan

- VerifiedRoute brand present
- Route verifier/brander present
- Direct bypass firewall present
- Raw provider/model execution rejected before execution
- Forged/deserialized/untrusted route rejected
- Fallback without VerifiedRoute rejected
- Session/channel pins treated as route intent only
- Fallback preserves `contract_version` and `authority_mode`
- Typed HOLD/FAIL emitted for invalid route
- Production authority disabled and enforcement disabled

## M3 regression plan

- Eligible owner turn emits `ContractEnvelope`
- `ShadowObservationReceipt` emitted
- `UniversalContractReceipt` emitted
- `DeliveryReceipt` emitted with mode `no_send`
- `TerminalContractCloseout` emitted
- Shadow send/provider/write/config/memory/Context Bridge counters remain zero

## Direct bypass firewall validation plan

- Raw provider/model rejected
- Missing VerifiedRoute rejected
- Forged VerifiedRoute rejected
- Deserialized route rejected
- Fallback without VerifiedRoute rejected
- Session/channel model pin cannot directly authorize execution
- Unsupported provider/model produces typed HOLD
- No provider/model live call during rejection checks

## No-send / no-authority boundary

- Installed runtime mutation count: `0`
- Direct dist hotpatch count: `0`
- Gateway restart count: `0`
- Telegram send/probe count: `0`
- External send count: `0`
- Provider/model live call count: `0`
- Route/config mutation count: `0`
- Durable memory mutation count: `0`
- Context Bridge mutation count: `0`
- Production authority change count: `0`
- Production enforcement enabled: `false`
- M5 started: `false`

## Operator decision needed

If and only if Stick explicitly approves staged install, install exactly the R2 tarball above after creating the backup path. Until then, remain `HOLD_M4_VERIFIED_ROUTE_INSTALL_AWAITING_OPERATOR_APPROVAL` and do not install.
