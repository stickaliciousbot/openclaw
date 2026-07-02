# Stickbot TARS M2.5 Hardening Repair Plan

Generated: 2026-07-02T03:03:00Z / 2026-07-02 13:03 AEST

## Classification

Current state: `STICKBOT_TARS_M25_HARDENING_CLOSEOUT_BLOCKED_FAIL_CLOSED`

Read-only repo audit: `STICKBOT_TARS_REPO_AUDIT_READ_ONLY_COMPLETE`

Do **not** proceed to M3 model acquisition/load until the next valid classification is:

`STICKBOT_TARS_M25_HARDENING_CLOSEOUT_PASS_READY_FOR_M3`

## Proposed branch

Preferred: `feature/stickbot-tars-m25-hardening-repair`

Alternate: `m25/stickbot-tars-hardening-failclosed-repair`

Branch creation is **not executed** by this artifact.

## Scope boundaries

Allowed next write phase scope:

- `projects/stickbot-tars-smoke/**`
- Optional project-local evidence under `projects/stickbot-tars-smoke/docs/**`
- Optional project-local state under `projects/stickbot-tars-smoke/state/**`

Explicitly out of scope:

- OpenClaw Gateway config/routing/defaults/fallbacks
- Gateway restart or service authority changes
- Telegram/runtime send or provider/message API calls
- M3 model acquisition/load
- `.pth`/XTTS model loading in OpenClaw/Gateway process
- LAN exposure or binding to port `8787`
- `/mnt/c` model files, venvs, node_modules, uploaded/generated audio, or traces

## Target project-local layout

```text
projects/stickbot-tars-smoke/
  server.js
  package.json
  src/
    config.js
  http/
  safety/
    network-policy.js
    origin-policy.js
    csrf.js
    limits.js
    audio-path-policy.js
  adapters/
  ledgers/
  public/
  data/
    audio/
      input/
      output/
    traces/
  test/
    config-failclosed.test.*
    audio-path-policy.test.*
    origin-csrf.test.*
    limits.test.*
  docs/
    IMPLEMENTATION_PLAN.md
    LOW_LEVEL_DESIGN_AND_IMPLEMENTATION_PLAN.md
    M25_REPAIR_PLAN.md
    m25-hardening-closeout/
  state/
    status.json
    audit.json
```

## Ignore / do not commit

Runtime/generated blobs should remain ignored and uncommitted:

- `projects/stickbot-tars-smoke/data/audio/**`
- `projects/stickbot-tars-smoke/data/traces/**`
- `projects/stickbot-tars-smoke/models/**`
- `projects/stickbot-tars-smoke/xtts_models/**`
- `projects/stickbot-tars-smoke/.venv/**`
- `projects/stickbot-tars-smoke/venv/**`
- `projects/stickbot-tars-smoke/node_modules/**`
- `projects/stickbot-tars-smoke/cache/**`

## Repair order

Fix only the M2.5 blockers, in this order:

1. `config.js` fail-closed startup validation.
2. LAN/non-loopback refusal unless `VOICE_DEMO_ALLOW_LAN=true`.
3. UUID-only audio route enforcement.
4. Separate text body and audio upload limits.
5. Origin check plus CSRF/session nonce.
6. Tests for every blocker.
7. Rerun smoke and fail-closed validation.
8. Write M2.5 repair closeout.
9. Only then classify as ready for M3.

## Required validation commands for next write phase

Run from `projects/stickbot-tars-smoke/` unless noted:

```sh
npm run check
node test/config-failclosed.test.*
node test/audio-path-policy.test.*
node test/origin-csrf.test.*
node test/limits.test.*
# local-only smoke on 127.0.0.1, non-8787
git diff --check
# verify no /mnt/c paths in project policy/runtime artifacts
# verify no OpenClaw production mutation sentinel
```

## Stop condition

If any hardening gate fails, retain or return to:

`STICKBOT_TARS_M25_HARDENING_CLOSEOUT_BLOCKED_FAIL_CLOSED`

No model download, no `.pth`, no XTTS load, and no M3 until all M2.5 gates pass.
