# Stickbot-TARS local voice smoke

Local-only Stickbot/TARS voice and audio development workspace.

## Rehydrate first

```bash
npm run rehydrate:tars -- --status
```

Read:

```text
artifacts/rehydration/stickbot-tars/latest.md
```

That packet restores the project thesis, paths, Git branch/remote, current milestone state, guardrails, runtime locations, and resume commands.

## Core guardrails

- No OpenClaw Gateway/routing/default/fallback/NOA/provider mutation without explicit approval.
- Do not use reserved port `8787`.
- No cloud STT or browser Web Speech API by default.
- No durable raw mic transcript storage.
- No `/mnt/c` runtime/model/audio/venv/cache paths.
- No generated audio/model/venv/cache/private-key artifacts committed.
- Canonical assistant text stays authoritative; prosody/DSP/mastering must not rewrite it.

## Current live demo path

```text
https://192.168.1.107:19890/
```

XTTS loopback:

```text
http://127.0.0.1:8020
```

Run checks:

```bash
npm run check
```
