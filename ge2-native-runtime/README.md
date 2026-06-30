# GE2 Native Runtime Kit

This kit now provides a working native `/ge2` runtime core:

- canonical command parser (`src/ge2_command_router.mjs`)
- dispatcher with background run lifecycle (`src/ge2_dispatcher.mjs`)
- deterministic runtime + milestone emission (`src/ge2_runtime.mjs`)
- durable ledger/index/artifact persistence (`src/ge2_ledger.mjs`, `src/ge2_artifacts.mjs`)
- milestone vocabulary (`src/ge2_milestones.mjs`)
- snapshot helpers (`src/ge2_snapshot.mjs`)

## Supported commands

- `/ge2 run <task>`
- `/ge2 status`
- `/ge2 status <run_id>`
- `/ge2 artifacts <run_id>`
- `/ge2 cancel <run_id>`
- `/ge2 help`

## Runtime state

State is written under:

- `state/ge2-native/runs/`
- `state/ge2-native/runs.index.json`
- `state/ge2-native/*.jsonl`
- `state/ge2-native/artifacts/<run_id>/`

## Demo

```bash
node ge2-native-runtime/examples/demo_run.mjs
```

## Native registration path used in this workspace

`hooks/ge2-register/handler.js` registers `/ge2` at gateway startup so Telegram and WebUI use the same dispatcher path.
