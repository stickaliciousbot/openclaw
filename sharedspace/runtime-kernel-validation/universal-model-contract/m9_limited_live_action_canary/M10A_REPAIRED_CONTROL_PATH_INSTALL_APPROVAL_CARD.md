# M10A Repaired Control Path Install Approval Card

Status: `HOLD_M10A_REPAIRED_INSTALL_AWAITING_OPERATOR_APPROVAL`

## Root cause

The M10A source build regenerated existing M8 dist content to a different hash. The full npm package tarball included that regenerated M8 file, and npm install copied the whole package/dist tree. The M10A module itself did not collide with M8; the install mechanism was too broad for a single-file preservation boundary.

## Repair summary

Added scoped overlay preservation guard. The repaired install path validates overlay SHA, rejects overlays containing M8/M2-M9 artifacts, verifies preserved installed hashes before and after, and in apply mode copies only the M10A dist file.

## Source

- Source path: `/home/stickai/.openclaw/worktrees/umc-m3g-observe-only-hook-source-20260711`
- Source branch: `evidence/umc-m3g-observe-only-hook-source-20260711`
- Source commit: `32c02611898dca57f8c27982b3a60c087970d0f4`

## Candidate tarball

- Path: `/home/stickai/.openclaw/workspace/tmp/umc-m10a-repaired-scoped-overlay/m10a-control-path-scoped-overlay-20260716T1133Z.tar.gz`
- SHA256: `be66f39008d09e8a04c848a50a3842b8553743a5bd4b0a9541218f3a32204587`
- M10A dist SHA256: `be56d6a5105d4d0a03085757483b3bb07374ff96b9db8ea44a1bcb164139e082`

## Expected installed files changed

- Add `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/auto-reply/reply/umc-m10a-owner-telegram-direct-control-path.js` with SHA256 `be56d6a5105d4d0a03085757483b3bb07374ff96b9db8ea44a1bcb164139e082`

## Preserved files

- M8: `27116a4374b699b7e98bc8ec9be98f3584bc14a8ca740d0723316deaa66088db`
- Telegram plugin manifest: `a3bd23650c86763689c3c9227d13928ee78d4546e0b8e39864f440d926cc40bd`
- M4/M5/M6/M7/package.json as recorded in the JSON card.

## Approved install command template

```sh
node /home/stickai/.openclaw/worktrees/umc-m3g-observe-only-hook-source-20260711/scripts/umc-m10a-preservation-guard.mjs --mode apply --overlay /home/stickai/.openclaw/workspace/tmp/umc-m10a-repaired-scoped-overlay/m10a-control-path-scoped-overlay-20260716T1133Z.tar.gz --installed-root /home/stickai/.npm-global/lib/node_modules/openclaw --expected-overlay-sha256 be66f39008d09e8a04c848a50a3842b8553743a5bd4b0a9541218f3a32204587 --expected-m10a-sha256 be56d6a5105d4d0a03085757483b3bb07374ff96b9db8ea44a1bcb164139e082 --backup-path /home/stickai/.openclaw/backups/openclaw-m10a-repaired-control-path-install-20260716T1133Z/openclaw-installed-package
```

## Hard stops

- Stop if M8 drift recurs.
- Stop if any preserved M2-M9 artifact drifts.
- Stop if M10A is enabled by default.
- Stop if production authority changes.

No install, Gateway restart, M10A enablement, production authority change, send/probe, provider call, write tool execution, durable memory mutation, or Context Bridge mutation was performed in this milestone.
