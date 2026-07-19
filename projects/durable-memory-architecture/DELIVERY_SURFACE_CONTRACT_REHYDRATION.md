# Delivery Surface Contract Rearchitecture Rehydration

Status: started; read-only generated navigation packet; no runtime apply.

## Run

```bash
python3 projects/durable-memory-architecture/scripts/delivery_surface_contract_rehydrate.py --status --strict
```

## Validate without writing output

```bash
python3 projects/durable-memory-architecture/scripts/delivery_surface_contract_rehydrate.py --check-only --strict
python3 -m py_compile projects/durable-memory-architecture/scripts/delivery_surface_contract_rehydrate.py
```

## Default outputs

```text
state/durable-memory-architecture/delivery-surface-contract-rehydration/latest.json
state/durable-memory-architecture/delivery-surface-contract-rehydration/latest.md
```

## Sources

The rehydrator reads only allowlisted local design/evidence/navigation files:

- compaction-gap proposal;
- systemic durable-memory/contract/RSB/SSB LLD;
- Ledger/Broker integration and build order;
- delivery-surface implementation/troubleshooting/repair notebook;
- latest compaction-gap generated manifest;
- accepted M25H blocked closeout evidence files;
- delivery-surface memory chunks notebook.

## Boundaries

The packet is non-authoritative navigation data. It does not inject context, mutate Gateway/config/Ledger/Context Bridge/runtime/routes/model settings, arm handlers, schedule or run cron jobs, send Telegram, run delivery, promote authority, or start M26/implementation milestones.

## M25J-R SRTR rehydration anchor

Current M25J rehydration must include the SRTR extension: sanitized target request/grant/receipt schemas, synthetic raw-target security fixtures, target gates/health checks, and milestone sequence updates. The rehydrator remains non-authoritative navigation only and must not expose raw target IDs or inject target handles into prompts, Context Bridge, UMC prose, or evidence.
