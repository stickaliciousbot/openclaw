# Compaction-Gap Recovery Hydration

This project includes a bounded, design-only rehydrator:

```bash
python3 projects/durable-memory-architecture/scripts/compaction_gap_rehydrate.py --status --strict
```

Default outputs (generated state; do not commit raw packets automatically):

```text
state/durable-memory-architecture/compaction-gap-hydration/latest.md
state/durable-memory-architecture/compaction-gap-hydration/latest.json
```

If the Ledger worktree moves:

```bash
python3 projects/durable-memory-architecture/scripts/compaction_gap_rehydrate.py \
  --ledger-root /path/to/projects/stickbot-memory-ledger-v0 \
  --status --strict
```

Validation without writing an output packet:

```bash
python3 projects/durable-memory-architecture/scripts/compaction_gap_rehydrate.py --check-only --strict
python3 projects/durable-memory-architecture/test/test_compaction_gap_rehydrate.py
python3 -m py_compile projects/durable-memory-architecture/scripts/compaction_gap_rehydrate.py
```

The script reads only allowlisted sources: the systemic LLD/seven-milestone plan, draft proposal, integration/build-order design, systemic lesson learned, Ledger project rehydrator, bounded latest Ledger manifest, and latest bounded M24 status when present. It verifies source hashes before/after reading, performs a credential/private-key scan, and emits a source inventory.

The packet is non-authoritative navigation data. It does not inject context, write memory, mutate Ledger/Context Bridge/runtime/config/routes, invoke network services, or start a milestone. Mutable Ledger state must always be verified from canonical artifacts before action. M24 PASS alone is not the Ledger completion boundary: do not begin the new LLD until a separate Ledger M25 final-completion/freeze milestone closes PASS and is verified from canonical evidence.

## M25I-A architecture baseline hydration

M25I-A adds a design-only architecture baseline for delivery/context/broker rearchitecture. Generated evidence lives under `sharedspace/runtime-kernel-validation/memory-ledger/m25i_a_architecture_baseline_<timestamp>/`. The baseline may update the delivery-surface rehydration packet, but the packet remains non-authoritative navigation only and must not inject context or start M25J/M26. Validate with scoped commands only: compaction-gap strict status, delivery-surface strict status, JSON parse checks, markdown path checks, privacy scan, and `git diff --check` on allowlisted paths.
