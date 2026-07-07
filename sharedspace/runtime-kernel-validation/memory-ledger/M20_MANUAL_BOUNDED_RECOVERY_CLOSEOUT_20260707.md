# M20 Manual Bounded Recovery Closeout — 2026-07-07

## Classification

```text
MEMORY_LEDGER_V0_1_M20_RECOVERY_FINAL_VALIDATION_PASS_NO_AUTHORITY_PROMOTION_ORIGINAL_DETACHED_OBSERVER_INVALID
```

This is a **manual bounded recovery validation**, not a retroactive PASS for the original detached observer.

Original detached-observer state remains:

```text
HOLD_M20_DETACHED_OBSERVER_DID_NOT_EXECUTE_CHECKS_NO_PASS_UPGRADE
```

## Why this separate lane exists

The original M20 T+2h/T+8h/T+24h cron sessions finished `ok` but returned generic project-ledger summaries instead of executing required M20 checks. The original detached observer therefore cannot be upgraded to PASS from its own evidence.

After the Context+ replay reached terminal state, Stick approved a separate bounded M20 recovery closeout lane. This lane re-ran bounded read-only final validation checks against the existing M19-controlled production store and operator-only recall surface.

## Scope

Project: Stickbot Memory Ledger v0.1

Worktree:

```text
/tmp/stickbot-memory-ledger-v0-worktree
```

Project path:

```text
/tmp/stickbot-memory-ledger-v0-worktree/projects/stickbot-memory-ledger-v0
```

Production store:

```text
/tmp/stickbot-memory-ledger-v0-worktree/state/stickbot-memory-ledger/v0/memory-ledger.sqlite
```

Approved scopes checked:

```text
system:memory-ledger
project:openclaw-runtime
project:stickbot-tars
```

## Recovery checks performed

### 1. Prior defect evidence confirmed

Evidence read:

- `sharedspace/runtime-kernel-validation/memory-ledger/M20_DETACHED_OBSERVER_RECONCILIATION_20260707.md`
- `/home/stickai/.openclaw/cron/runs/72b92d09-602f-4649-9bd8-df7b91d3d4ce.jsonl`
- `/home/stickai/.openclaw/agents/main/sessions/62b1ae3c-d1ba-48ee-81ef-6d271f76cf88.jsonl`
- `/home/stickai/.openclaw/agents/main/sessions/bf1655f2-555f-4a21-b671-368a1c8741af.jsonl`

Result: original detached observer did not execute required checks; it remains invalid for PASS.

### 2. Rehydrator check

Command:

```text
node projects/stickbot-memory-ledger-v0/scripts/stickbot-memory-ledger-rehydrate.mjs --project-root projects/stickbot-memory-ledger-v0 --check
```

Result: rehydrator regenerated packet with `status: PASS`.

Because rehydrator generation refreshed tracked latest artifacts, those generated changes were restored after evidence capture so M20 remained observation-only/no tracked Ledger worktree changes.

### 3. Doctor check

Command:

```text
python3 scripts/stickbot-memory-ledger-cli.py --store /tmp/stickbot-memory-ledger-v0-worktree/state/stickbot-memory-ledger/v0/memory-ledger.sqlite doctor
```

Result: `status: pass`.

Checks passed:

```text
H01 schema_version=1
H03 ok
H05 finding_count=0 categories=[]
H12 recall boundary
H15 runtime_mutation_allowed=false
H16 event chain
H19 record hashes
H17 nuzo_dependency_files=0
H18 tracked_private=0
```

Mutation sentinel:

```json
{
  "gateway_config_changed": false,
  "model_routes_changed": false,
  "provider_routes_changed": false,
  "runtime_memory_route_changed": false
}
```

### 4. Approved-scope operator recalls

Each approved-scope recall used process-local:

```text
STICKBOT_MEMORY_LEDGER_OPENCLAW_READONLY_CANARY=1
```

and required:

```text
--confirm-readonly
```

Successful scopes:

```text
system:memory-ledger
project:openclaw-runtime
project:stickbot-tars
```

For each successful recall:

```text
status=ok
packet_rendered=true
content_omitted=true
raw_memory_content_logged=false
read_only=true
memory_writes=false
instruction_authority=none
runtime_promotion=false
store_counts_before={records: 19, events: 20}
store_counts_after={records: 19, events: 20}
store_sha256_unchanged=true
trust_boundary begin/end present
mutation_sentinel_before all false
mutation_sentinel_after all false
flag_persisted_by_command=false
restart_required=false
```

### 5. Fail-closed checks

Denied scope:

```text
scope=project:unauthorized
status=fail_closed
exit_code=2
packet_rendered=false
reason=scope denied
```

Missing process-local flag:

```text
scope=system:memory-ledger
status=fail_closed
exit_code=2
packet_rendered=false
reason=STICKBOT_MEMORY_LEDGER_OPENCLAW_READONLY_CANARY=1 is required
```

Missing `--confirm-readonly`:

```text
scope=system:memory-ledger
status=fail_closed
exit_code=2
packet_rendered=false
reason=--confirm-readonly is required
```

All fail-closed checks reported:

```text
memory_writes=false
runtime_promotion=false
raw_memory_content_logged=false
mutation_sentinel_before all false
mutation_sentinel_after all false
```

### 6. Worktree restoration/readback

After rehydrator regeneration was restored, Ledger worktree status was clean:

```text
git status --porcelain=v1
# no output
```

## Decision

Manual bounded recovery validation passes.

The original detached observer remains invalid and must not be cited as M20 PASS evidence.

Use this terminal recovery status only:

```text
MEMORY_LEDGER_V0_1_M20_RECOVERY_FINAL_VALIDATION_PASS_NO_AUTHORITY_PROMOTION_ORIGINAL_DETACHED_OBSERVER_INVALID
```

## Safety boundary readback

- No M22 started.
- No authority promotion performed.
- No production memory-route promotion performed.
- No automatic recall enabled.
- No Gateway/runtime/model/provider/fallback/Telegram/memory-route config mutation performed.
- No raw memory content logged into this tracked artifact.
- No DB/WAL/SHM/private store artifact tracked.
- No Ledger worktree tracked changes remain after restore.
