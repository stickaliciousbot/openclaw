# EquipmentIQ → Microsoft Fabric Digital Twin Builder

API-first importer/compiler for the Douglas Bagmaker EquipmentIQ bundle.

## V1 target

```text
EquipmentIQ Douglas bagmaker zip
  -> importer/compiler service
  -> Fabric Lakehouse tables in OneLake
  -> Digital Twin Builder public definition parts
  -> Digital Twin Builder work item
  -> mapping/contextualization flow execution
  -> validation through DTB domain views + explorer
```

Fabric IQ is generated as an optional mirror / v2 investigation path. DTB public definition parts are the v1 deployment source of truth.

## Current Fabric decisions

- Dedicated workspace target: `StickbotDigitalTwin`
- Calibration source workspace: `My workspace`
- Calibration DTB: `AltouraDigitalTwinTest`
- Final DTB item: `DouglasBagmakerDTB`
- Final raw lakehouse: `DouglasBagmakerRaw`
- Playwright fallback: acceptable for triggering operation runs if no public run API is found
- Spark proof mode: tiny/cost-controlled cluster, slow starts and ~5 minute timeout expected

## Current Douglas DTB implementation shape

The active Douglas compiler target is the **role-specific JoinKey / child-first ManyToOne** diagnostic variant. This supersedes the earlier raw-key parent-first and same-name JoinKey attempts for contextualization testing.

Why: Fabric DTB mappings completed, but contextualization failed with missing property-descriptor errors when `EquipmentId` / `SystemId` were used as both identity and relationship join attributes, and again when same-name JoinKey descriptors (`System.EquipmentJoinKey`, `System.SystemJoinKey`) were selected. The source ZIP/data is structurally sound; the suspected failure is descriptor hydration/binding inside DTB contextualization.

Current rule:

```text
DTB-facing source tables:
  equipment_dtb              uses EquipmentUID as identity, EquipmentJoinKey as equipment join identity
  systems_dtb                uses SystemUID as identity, source EquipmentJoinKey -> System.ParentEquipmentJoinKey, SystemJoinKey as system join identity
  parts_dtb                  uses PartUID as identity, source SystemJoinKey -> Part.ParentSystemJoinKey
  historian_timeseries_dtb   keeps PreciseTimestamp, HistorianTag, Value

Relationships:
  System isPartOf Equipment  ManyToOne  System.ParentEquipmentJoinKey = Equipment.EquipmentJoinKey
  Part   isPartOf System     ManyToOne  Part.ParentSystemJoinKey      = System.SystemJoinKey
```

Do not deploy this definition until the four `_dtb` Lakehouse tables/views exist. Do not retry failed contextualization on older raw-key or same-name JoinKey DTB items without new evidence.

For app-loaded Douglas/JoinKey tables, generated MappingOperations must **omit** `SourceSchema`. The `_dtb` tables are root Lakehouse tables (`Tables/equipment_dtb`, etc.); `SourceSchema: dbo` makes Fabric look under `Tables/dbo/<table>` and causes `PATH_NOT_FOUND`.

## Local first commands

```bash
python -m eiq_dtb_importer inspect --zip ./samples/dbm-rh-m5-dtb-e2e-kit.zip
pytest
```

No Fabric/Azure mutation is performed by inspect/tests.
