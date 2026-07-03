# Stickbot-TARS deterministic rehydration

Use this before Stickbot-TARS voice/audio development, live demos, or repair work to avoid lengthy rediscovery.

## Command

```bash
npm run rehydrate:tars
```

Outputs:

```text
artifacts/rehydration/stickbot-tars/latest.md
artifacts/rehydration/stickbot-tars/latest.json
artifacts/rehydration/stickbot-tars/<timestamp>/stickbot-tars-rehydration.md
artifacts/rehydration/stickbot-tars/<timestamp>/stickbot-tars-rehydration.json
```

Optional local git status snapshot:

```bash
npm run rehydrate:tars -- --status
```

Markdown to stdout only:

```bash
npm run rehydrate:tars -- --md --stdout-only
```

JSON to stdout only:

```bash
npm run rehydrate:tars -- --json --stdout-only
```

## What it rehydrates

- Project thesis, current live status, Git branch/remote, and local runtime roots.
- LAN/loopback URLs, XTTS URL, HTTPS certificate location, local model/reference/STT/FFmpeg paths.
- Guardrails: no Gateway/OpenClaw/NOA routing mutation, no cloud STT, no browser Web Speech API, no raw mic transcript durable storage, no `/mnt/c` runtime/model/audio paths, no generated audio commits.
- Proven milestone chain from M3 through M7P and M5.6.
- Resume commands for checks, XTTS, HTTPS LAN demo, and health probes.
- Curated source inventory with SHA256 hashes, line counts, and headings.
- Runtime path inventory for model/reference/whisper/ffmpeg/certs without storing secrets.
- Local generated-artifact pointers only; generated audio is not committed.

## Grounding rule

The rehydrator restores context. It does not prove current readiness by itself.

Before claiming a live demo is ready, still run:

```bash
npm run check
curl -k -fsS https://127.0.0.1:19890/health
curl -k -fsS https://192.168.1.107:19890/health
curl -fsS http://127.0.0.1:8020/ready
```

For subjective audio quality changes, ask Stick to A/B the LAN browser output. The script can prove structure and artifacts; Stick's ear is still the final voice-body gate.
