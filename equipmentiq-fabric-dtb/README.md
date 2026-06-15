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

The active Douglas compiler target is the **JoinKey / ManyToOne** variant. This supersedes the earlier raw-key parent-first attempt for contextualization testing.

Why: Fabric DTB mappings completed, but contextualization failed with missing property-descriptor errors when `EquipmentId` / `SystemId` were used both as `EntityInstanceIdSchema` identity columns and relationship join attributes. The source ZIP/data is structurally sound; the suspected failure is descriptor binding inside DTB contextualization.

Current rule:

```text
DTB-facing source tables:
  equipment_dtb              uses EquipmentUID as identity, EquipmentJoinKey as relationship key
  systems_dtb                uses SystemUID as identity, EquipmentJoinKey/SystemJoinKey as relationship keys
  parts_dtb                  uses PartUID as identity, SystemJoinKey as relationship key
  historian_timeseries_dtb   keeps PreciseTimestamp, HistorianTag, Value

Relationships:
  System isPartOf Equipment  ManyToOne  System.EquipmentJoinKey = Equipment.EquipmentJoinKey
  Part   isPartOf System     ManyToOne  Part.SystemJoinKey      = System.SystemJoinKey
```

Do not deploy this definition until the four `_dtb` Lakehouse tables/views exist. Do not retry failed contextualization on older raw-key DTB items without new evidence.

## Local first commands

```bash
python -m eiq_dtb_importer inspect --zip ./samples/dbm-rh-m5-dtb-e2e-kit.zip
pytest
```

No Fabric/Azure mutation is performed by inspect/tests.
