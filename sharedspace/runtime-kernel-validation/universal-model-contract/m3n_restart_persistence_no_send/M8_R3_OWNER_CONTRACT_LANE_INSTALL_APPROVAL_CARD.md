# M8 R3 Owner Contract Lane Install Approval Card

Status: `HOLD_M8_R3_OWNER_CONTRACT_LANE_INSTALL_AWAITING_OPERATOR_APPROVAL`

No install has been run. This R3 card repairs the M8 authority-mode literal.

## Source

- Branch: `evidence/umc-m3g-observe-only-hook-source-20260711`
- Commit: `4ead371c40b1aca97059f41255341d57c6d61055`

## Package

- Tarball: `/home/stickai/.openclaw/workspace/tmp/umc-m8-r3-package/openclaw-2026.5.7.tgz`
- SHA256: `1f6bd7fed192b1413f6320a69ca56cc528e807c81c2dae36473e14bc9ddbc9a0`
- M8 artifact SHA256: `27116a4374b699b7e98bc8ec9be98f3584bc14a8ca740d0723316deaa66088db`

## Expected installed change

- Replace `dist/auto-reply/reply/umc-m8-owner-contract-lane.js`
  - before: `ab0b66fb9578f1b99320b46590825a1a956a83152d5c653f0d00ca2386cdb44f`
  - after: `27116a4374b699b7e98bc8ec9be98f3584bc14a8ca740d0723316deaa66088db`

M7/M6/M5/M4/M3/plugin/package hashes are preserved.

- M3 artifact: `dist/umc-m3-envelope-supervision-CZFFPUFB.js`
- M3 SHA256: `9af1b667eb69a32c7d7f9bd28c3bd72843e331d63cc8bf8e81399479a6a7dfba`

## Install command requiring approval

```sh
npm install -g --ignore-scripts /home/stickai/.openclaw/workspace/tmp/umc-m8-r3-package/openclaw-2026.5.7.tgz
```

Gateway restart is required after install. Telegram send/probe remains forbidden.

## Rollback

Primary rollback to current M8 R2 state:

```sh
npm install -g --ignore-scripts /home/stickai/.openclaw/workspace/tmp/umc-m8-package/openclaw-2026.5.7.tgz && openclaw gateway restart
```

Emergency rollback to M7 remains available.

## Boundary

No send, no provider live call, no config/memory/Context Bridge mutation, no production authority, no live-action canary, no broad enforcement, no M9.

Approve with: `APPROVE_M8_R3_OWNER_CONTRACT_LANE_STAGED_INSTALL`
