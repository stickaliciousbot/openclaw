# M10A Runtime-Dependency Repaired Control Path Install Approval Card

Status: `HOLD_M10A_RUNTIME_DEPENDENCY_REPAIRED_INSTALL_AWAITING_OPERATOR_APPROVAL`

## Root cause

The previous scoped overlay preserved M8 but copied only the M10A entry file. The built M10A entry imports generated support chunks through the M8/M7/M6 chain, so the overlay must include the full runtime dependency closure while still excluding preserved M2-M9 entry artifacts such as the canonical M8 entry file.

## Repair summary

Extended the scoped preservation guard to require, hash-check, and copy the generated runtime dependency closure alongside the M10A entry while continuing to reject preserved M2-M9 runtime entry artifacts such as the canonical M8 entry file.

## Candidate

- Path: `/home/stickai/.openclaw/workspace/tmp/umc-m10a-repaired-scoped-overlay-r2/m10a-control-path-scoped-overlay-r2-20260716T1200Z.tar.gz`
- SHA256: `c0fdd546016071cf2cfbcca802bf458261d5e5fac07fd38e7797ceace9aba83d`
- M10A dist SHA256: `be56d6a5105d4d0a03085757483b3bb07374ff96b9db8ea44a1bcb164139e082`
- Required dependency closure:
  - `dist/umc-m8-owner-contract-lane-CdxuqyX4.js`: `70e580814a1649068dcd173d979ac31d579b5ef7ae85866753c1503133815ed7`
  - `dist/umc-m7-model-eligibility-ovqh9OfD.js`: `e25711e5809835085d4c5450f5b1fb4e479b6f9e29631b538fd1f9908e78b9bd`
  - `dist/umc-m6-contract-build-lane-B49r9Ao5.js`: `8416342de89bf8e525f477c4255c59b54f0a5a624d8a1c02dd2e783aa51a397a`
  - `dist/umc-m5-capability-manifest-DBUsXqaz.js`: `3f4dc6191a7e4ffced65b95aaeb9113964f2c9c36c1958c634fbdefb5d059745`
  - `dist/umc-m4-verified-route-B8LC1Bgv.js`: `8fd34dd344ec074204feb6231127ae0ff9bf7655f5273b864103cf5b457b5cc2`
  - `dist/umc-m3-envelope-supervision-CZFFPUFB.js`: `9af1b667eb69a32c7d7f9bd28c3bd72843e331d63cc8bf8e81399479a6a7dfba`

## Expected installed files changed

- add `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/auto-reply/reply/umc-m10a-owner-telegram-direct-control-path.js` SHA256 `be56d6a5105d4d0a03085757483b3bb07374ff96b9db8ea44a1bcb164139e082`
- add `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/umc-m8-owner-contract-lane-CdxuqyX4.js` SHA256 `70e580814a1649068dcd173d979ac31d579b5ef7ae85866753c1503133815ed7`
- replace `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/umc-m7-model-eligibility-ovqh9OfD.js` SHA256 `e25711e5809835085d4c5450f5b1fb4e479b6f9e29631b538fd1f9908e78b9bd`
- replace `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/umc-m6-contract-build-lane-B49r9Ao5.js` SHA256 `8416342de89bf8e525f477c4255c59b54f0a5a624d8a1c02dd2e783aa51a397a`
- replace `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/umc-m5-capability-manifest-DBUsXqaz.js` SHA256 `3f4dc6191a7e4ffced65b95aaeb9113964f2c9c36c1958c634fbdefb5d059745`
- replace `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/umc-m4-verified-route-B8LC1Bgv.js` SHA256 `8fd34dd344ec074204feb6231127ae0ff9bf7655f5273b864103cf5b457b5cc2`
- replace `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/umc-m3-envelope-supervision-CZFFPUFB.js` SHA256 `9af1b667eb69a32c7d7f9bd28c3bd72843e331d63cc8bf8e81399479a6a7dfba`

## Preservation

M8 remains required at `27116a4374b699b7e98bc8ec9be98f3584bc14a8ca740d0723316deaa66088db`. The canonical M8 entry file is excluded from the overlay and remains protected by the preservation guard.

## Approved install command template

```sh
node /home/stickai/.openclaw/worktrees/umc-m3g-observe-only-hook-source-20260711/scripts/umc-m10a-preservation-guard.mjs --mode apply --overlay /home/stickai/.openclaw/workspace/tmp/umc-m10a-repaired-scoped-overlay-r2/m10a-control-path-scoped-overlay-r2-20260716T1200Z.tar.gz --installed-root /home/stickai/.npm-global/lib/node_modules/openclaw --expected-overlay-sha256 c0fdd546016071cf2cfbcca802bf458261d5e5fac07fd38e7797ceace9aba83d --expected-m10a-sha256 be56d6a5105d4d0a03085757483b3bb07374ff96b9db8ea44a1bcb164139e082 --backup-path /home/stickai/.openclaw/backups/openclaw-m10a-runtime-dependency-repaired-install-20260716T1200Z/openclaw-installed-package
```

No install, Gateway restart, M10A enablement, production authority change, send/probe, provider call, durable memory mutation, or Context Bridge mutation was performed in this no-apply repair.
