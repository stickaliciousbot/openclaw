# M3H Dependency Manager Discovery

Status: `PASS_M3H_DEPENDENCY_MANAGER_DISCOVERY`
Generated: `2026-07-11T22:53:00Z`

## Package manager

- `packageManager`: `pnpm@10.33.2+sha512.a90faf6feeab71ad6c6e57f94e0fe1a12f5dcc22cd754db40ae9593eb6a3e0b6b12e3540218bb37ae083404b1f2ce6db2a4121e979829b4aff94b99f49da1cf8`
- Required manager: `pnpm`
- Required version: `10.33.2`
- `corepack`: present, version `0.34.6`

## Lockfiles

- `pnpm-lock.yaml`: present, SHA256 `bfa22169730e5710a7c8a821250a8c0b9868b4298f63fe36a28f0f823e227585`
- `package-lock.json`: absent
- `yarn.lock`: absent
- `package.json`: SHA256 `6e7592f379ac216d7ea00f50d38ed8ed7b328438c417cd8656d0a4f2b840a7c0`

## Hydration plan

Exact proposed command from source worktree:

```bash
corepack pnpm install --frozen-lockfile --store-dir "$PWD/.pnpm-store"
```

Working directory:

```text
/home/stickai/.openclaw/worktrees/umc-m3g-observe-only-hook-source-20260711
```

Properties:

- Lockfile frozen: yes (`--frozen-lockfile`)
- Lockfile mutation forbidden: yes
- Package manifest mutation forbidden: yes
- Dependency store confined to source worktree: `.pnpm-store`
- Node modules confined to source worktree: `node_modules`
- Network access may be used: yes
- Offline cache observed: no (`~/.cache/node/corepack`, `~/.local/share/pnpm/store`, and `~/.pnpm-store` absent)

Expected created paths:

- `node_modules`
- `.pnpm-store`

Expected unchanged paths:

- `package.json`
- `pnpm-lock.yaml`
- `/home/stickai/.npm-global`
- `/home/stickai/.npm-global/lib/node_modules/openclaw/dist/agent-runner.runtime-a09vVD0N.js`

No build, apply, production install, installed-dist patch, Gateway restart, provider/model call, Telegram send, or external send is included in this dependency-prep approval.
