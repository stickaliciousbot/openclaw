# Claude / Engineering Agent Notes — EquipmentIQ Fabric DTB

This repo is the Python/source-of-truth compiler for the Douglas Bagmaker EquipmentIQ → Microsoft Fabric Digital Twin Builder path.

## Current active shape

Use the **JoinKey / ManyToOne** Douglas shape.

Do **not** revert to the older raw-key relationship model without explicit evidence. The older variants imported and mapped but failed contextualization with Fabric DTB missing property-descriptor errors.

### Source tables required before Fabric hydration

```text
equipment_dtb
systems_dtb
parts_dtb
historian_timeseries_dtb
```

The `_dtb` tables deliberately separate entity identity from relationship join keys:

```text
Equipment:
  EntityInstanceIdSchema: EquipmentUID
  Relationship property: EquipmentJoinKey

System:
  EntityInstanceIdSchema: SystemUID
  Relationship properties: EquipmentJoinKey, SystemJoinKey

Part:
  EntityInstanceIdSchema: PartUID
  Relationship property: SystemJoinKey
```

### Relationships

```text
System isPartOf Equipment
  RelationshipCardinality: ManyToOne
  Join: System.EquipmentJoinKey = Equipment.EquipmentJoinKey

Part isPartOf System
  RelationshipCardinality: ManyToOne
  Join: Part.SystemJoinKey = System.SystemJoinKey
```

This mirrors the Microsoft Contoso tutorial's valid child-to-parent `N:1` relationship style while avoiding identity-vs-join descriptor ambiguity.

Source-path guard: generated mappings for these app-loaded `_dtb` tables must omit `SourceSchema`. `SourceSchema: dbo` makes Fabric look under `Tables/dbo/<table>` and fails with `PATH_NOT_FOUND` because these tables are loaded at root `Tables/<table>` paths.

## Operation order once a fresh item is deployed

Run operations serially in Fabric:

1. `Equipment_equipment_dtb`
2. `System_systems_dtb`
3. `Part_parts_dtb`
4. `Part_historian_timeseries_dtb_TimeSeries`
5. `System_isPartOf_Equipment_Contextualization`
6. `Part_isPartOf_System_Contextualization`

Do not tell the operator to run these until the `_dtb` tables exist and the fresh DTB + on-demand flow roundtrip has passed.

## Validation

Run:

```bash
.venv/bin/pytest -q
```

Expected local gate after the JoinKey patch: all tests pass.

## Documentation to keep in sync

- `README.md`
- `AGENTS.md`
- `docs/FAILURES_AND_FIXES_LEDGER.md`
- `docs/CONTOSO_ENERGY_DTB_CALIBRATION_2026-06-15.md`
- Node handoff repo/docs if changing public operator behavior.
