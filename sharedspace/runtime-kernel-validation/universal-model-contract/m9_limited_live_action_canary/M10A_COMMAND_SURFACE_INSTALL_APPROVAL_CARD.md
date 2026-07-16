# M10A Command Surface Staged Install Approval Card

Status: `HOLD_M10A_COMMAND_SURFACE_INSTALL_AWAITING_OPERATOR_APPROVAL`

This card prepares approval only. It does **not** approve or perform install, Gateway restart, M10A enablement, production authority change, Telegram probe/send, provider/model call, memory mutation, Context Bridge mutation, route/fallback/config mutation, or cron/job mutation.

## Candidate

- Source-ready commit: `9aaf679ff760908bdfaf94d0a92aff188e684b8d`
- Install-prep source commit: `1c5e48e9162c990f8e9e4ed933f85acd009b283a`
- Evidence commit before prep: `2630f3d0b2c1c26bb6da4b16a8d269e601ba385a`
- Candidate package: `/home/stickai/.openclaw/workspace/tmp/m10a-command-surface-staged-install-candidate/20260716T1325Z/m10a-command-surface-staged-install-candidate-20260716T1325Z.tar.gz`
- Candidate SHA256: `1c26049fab45d9afbadf3be4a33ef569b03184d65a05b81abdfcde85467ea71d`

## Expected changed files

- `package.json`
- `M10A_COMMAND_SURFACE_CANDIDATE_OVERLAY_MANIFEST.json`
- `scripts/m10a-owner-telegram-direct-observe.mjs`
- `scripts/m10a-owner-telegram-direct-control.mjs`

## Script SHA256

- `scripts/m10a-owner-telegram-direct-control.mjs`: `02b8d9182d39c040ed22f027da2489c209dc9ea2d569e989ea6149ac25207dd6`
- `scripts/m10a-owner-telegram-direct-observe.mjs`: `98b2f27d751055489c0e8b28ad4ba2b15c6a06adda3701f2217196fc02694c38`

## Preservation checks

- M8 canonical artifact: `dist/auto-reply/reply/umc-m8-owner-contract-lane.js`
  - expected/current SHA256: `27116a4374b699b7e98bc8ec9be98f3584bc14a8ca740d0723316deaa66088db`
- M10A runtime control-path artifact is preserved:
  - expected/current SHA256: `be56d6a5105d4d0a03085757483b3bb07374ff96b9db8ea44a1bcb164139e082`
- Candidate contains no `dist/`, config, route/fallback, memory, Context Bridge, cron/job, or plugin-manifest entries.

## Backup path

`/home/stickai/.openclaw/backups/openclaw-m10a-command-surface-staged-install-20260716T1325Z/openclaw-installed-package`

## Rollback command

```sh
rm -rf /home/stickai/.npm-global/lib/node_modules/openclaw && cp -a /home/stickai/.openclaw/backups/openclaw-m10a-command-surface-staged-install-20260716T1325Z/openclaw-installed-package /home/stickai/.npm-global/lib/node_modules/openclaw
```

## Gateway restart requirement

Not required for this overlay because it adds persistent package scripts/package metadata only and does not mutate runtime hooks/routes/config. Any restart would require separate approval.

## Post-install validation plan

1. Verify script presence and SHA256.
2. Verify M8 SHA remains `27116a4374b699b7e98bc8ec9be98f3584bc14a8ca740d0723316deaa66088db`.
3. Verify M10A runtime control-path SHA remains `be56d6a5105d4d0a03085757483b3bb07374ff96b9db8ea44a1bcb164139e082`.
4. Run control help/status dry-run.
5. Run enable/disable/status dry-runs only; do not enable M10A.
6. Run observe help/dry-run only.
7. Confirm M10A remains disabled, production authority false, broad enforcement false.
8. Confirm no Telegram send/probe, provider/model call, runtime write-tool execution, memory mutation, Context Bridge mutation, route/fallback/config mutation, or cron/job mutation.

## Hard stops

- M10A becomes enabled.
- Production authority changes.
- Broad enforcement becomes true.
- M8 SHA mismatch.
- M10A runtime control-path artifact overwritten.
- Telegram send/probe occurs.
- Provider/model live call occurs.
