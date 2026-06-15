# Contoso Energy DTB Calibration — 2026-06-15

Purpose: treat the Microsoft Fabric Digital Twin Builder Contoso Energy tutorial as a separate baseline problem, then use the working tutorial shape to reason about the Douglas Bagmaker contextualization failure.

## Sources reviewed

- Microsoft Learn: Digital Twin Builder tutorial introduction.
- Microsoft Learn / fabric-docs raw: Part 2, **Add entity types and map data**.
- Microsoft Learn / fabric-docs raw: Part 3, **Define semantic relationship types between entity types**.
- Attached Contoso-style CSVs:
  - `AssetData---2982d4b2-e3d9-402b-9651-9412fa0521d1.csv`
  - `ProcessData---c3897655-d5fb-44ae-8a61-9edfbcb0bddc.csv`
  - `Technicians---f68b4bd9-0963-4dc9-b235-4ea3a44be02a.csv`
  - `MaintenanceRequests---7f80e37b-6e13-4df5-a426-90d4162a94f1.csv`

## Attached CSV baseline

The attached data matches the Contoso Energy tutorial ontology pattern, with different filename casing from the docs but equivalent tables:

| Tutorial table | Attached CSV | Observed role |
| --- | --- | --- |
| `assetdata` | `AssetData...csv` | Equipment metadata for Distiller / Condenser / Reboiler. |
| `processdata` | `ProcessData...csv` | Process/site rows keyed by `processId`, carrying `siteId`. |
| `technicians` | `Technicians...csv` | Technician dimension keyed by `Id`. |
| maintenance request table | `MaintenanceRequests...csv` | Work orders keyed by `WorkorderId`, with `EquipmentId`, `TechnicianId`, `Site`. |

Row counts observed from local files:

- `AssetData`: 30 data rows — 10 distillers (`D101`-`D110`), 10 condensers (`C201`-`C210`), 10 reboilers (`R401`-`R410`).
- `ProcessData`: 100 data rows — daily process/site observations across `DU-01` through `DU-10`.
- `Technicians`: 10 data rows — `T001` through `T010`.
- `MaintenanceRequests`: 5000 data rows.

## Tutorial entity model

The tutorial creates six entity types:

1. `Distiller` — system type `Equipment`.
2. `Condenser` — system type `Equipment`.
3. `Reboiler` — system type `Equipment`.
4. `Process` — system type `Process`.
5. `Technician` — system type `Generic`.
6. `MaintenanceRequest` — system type likely `Generic` / work-order style entity in the UI tutorial flow.

Important calibration point: the UI starts from system types, then adds user properties through mapping. System-type descriptors such as `DisplayName`, `Manufacturer`, and `SerialNumber` exist before or during mapping; the tutorial explicitly leaves some built-ins unmapped but still uses the UI-created property descriptor set.

## Tutorial mapping shape

### Distiller

Non-timeseries mapping:

- Source table: `assetdata`.
- Filter: `Name Contains distiller` (case-sensitive).
- Unique ID: `ID`.
- Property mappings:
  - `Name` -> `DisplayName`.
  - `ID` -> `DistillerId`.
  - `SiteId` -> `SiteId`.
  - `NumberOfTrays` -> `NumberOfTrays`.
  - `Manufacturer` and `SerialNumber` left unmapped.

Timeseries mapping from tutorial docs (not present in the four attached CSVs):

- Source table: `timeseries`.
- Filter: `assetId Contains D`.
- Link entity property: `DistillerId`.
- Link timeseries column: `assetId`.
- Map `sourceTimestamp` -> `Timestamp`; plus `RefluxRatio`, `MainTowerPressure`, `FeedFlowRate`, `FeedTrayTemperature`.

### Condenser

Non-timeseries mapping:

- Source table: `assetdata`.
- Filter: `Name Contains condenser`.
- Unique ID: `ID`.
- Properties:
  - `Name` -> `DisplayName`.
  - `ID` -> `CondenserId`.
  - `SiteId` -> `SiteId`.
  - `CoolingMedium` -> `CoolingMedium`.
  - `InstallationDate` -> `InstallationDate`.

Timeseries mapping from tutorial docs (not present in the four attached CSVs):

- Source table: `timeseries`.
- Filter: `assetId Contains C`.
- Link entity property: `CondenserId`.
- Link timeseries column: `assetId`.
- Map `sourceTimestamp` -> `Timestamp`; `Pressure`, `Power`, and `InletTemperature` -> `Temperature`.

### Reboiler

Non-timeseries mapping:

- Source table: `assetdata`.
- Filter: `Name Contains reboiler`.
- Unique ID: `ID`.
- Properties:
  - `Name` -> `DisplayName`.
  - `ID` -> `ReboilerId`.
  - `SiteId` -> `SiteId`.

Timeseries mapping from tutorial docs (not present in the four attached CSVs):

- Source table: `timeseries`.
- Filter: `assetId Contains R`.
- Link entity property: `ReboilerId`.
- Link timeseries column: `assetId`.
- Map `sourceTimestamp` -> `Timestamp`; `Pressure`, `InletTemperature`, `OutletTemperature`.

### Process

Non-timeseries mapping:

- Source table: `processdata`.
- Filter: none.
- Unique ID: `processId`.
- Properties:
  - leave `DisplayName` and `Type` unmapped.
  - `siteName` -> `siteName`.
  - `processId` -> `processId`.
  - `siteId` -> `SiteId`.

Calibration warning: `ProcessData` has 100 rows and `processId` appears per daily observation, so `SiteId` is not unique in `Process`. The tutorial still defines `Distiller/Reboiler/Condenser isPartOf Process` by joining `SiteId` to `SiteId`, meaning contextualization can create many asset-to-process links per site if process rows are event-like rather than one row per site.

### Technician

Expected mapping from attached data and tutorial relationship requirements:

- Source table: `technicians`.
- Unique ID: `Id`.
- Required relationship descriptor: map `Id` to entity property `TechnicianId`.
- Other likely properties: `name` -> `DisplayName` or `name`, `email` -> `email`.

### MaintenanceRequest

Expected mapping from attached data and tutorial relationship requirements:

- Source table: maintenance requests table.
- Unique ID: `WorkorderId`.
- Required relationship descriptors:
  - `EquipmentId` -> `EquipmentId`.
  - `TechnicianId` -> `TechnicianId`.
- Other likely properties: `WorkOrderType`, `Status`, `Priority`, dates, labour hours, `Site`.

## Tutorial contextualization shape from Part 3

Part 3 creates five relationship types and runs each relationship immediately from the Scheduling section after creation.

| Relationship phrase | First entity / join | Second entity / join | Relationship name | Cardinality |
| --- | --- | --- | --- | --- |
| `Distiller has MaintenanceRequest` | `Distiller.DistillerId` | `MaintenanceRequest.EquipmentId` | `has` | `1:N` |
| `Technician performs MaintenanceRequest` | `Technician.TechnicianId` | `MaintenanceRequest.TechnicianId` | `performs` | `1:N` |
| `Distiller isPartOf Process` | `Distiller.SiteId` | `Process.SiteId` | `isPartOf` | `N:1` |
| `Reboiler isPartOf Process` | `Reboiler.SiteId` | `Process.SiteId` | `isPartOf` | `N:1` |
| `Condenser isPartOf Process` | `Condenser.SiteId` | `Process.SiteId` | `isPartOf` | `N:1` |

This is the cleanest currently documented relationship/contextualization target shape.

## Calibration findings for Douglas

### 1. Relationship direction must follow semantic phrase, not just containment instinct

The tutorial uses first entity = the entity selected in the canvas and the subject of the phrase:

- `Distiller has MaintenanceRequest`: parent/source first, child/target second, `1:N`.
- `Distiller isPartOf Process`: child/source first, parent/target second, `N:1`.

So there is no universal parent-first rule. The correct pattern is:

> FirstEntity = semantic subject / selected entity; SecondEntity = semantic object; cardinality describes that phrase.

For Douglas `Equipment contains System`, parent-first `Equipment -> System` with `1:N` is aligned with the tutorial. But the tutorial also shows that `N:1` is valid and expected when the semantic phrase is child-to-parent (`isPartOf`).

### 2. Descriptor availability is the likely blocker, not cardinality alone

Douglas parent-first contextualization failed with:

> required property descriptor for column `EquipmentId` does not exist in the data model for the Equipment entity type.

The Contoso tutorial creates relationship join properties through UI mappings before contextualization:

- `DistillerId` is not simply a source column; it is explicitly added as an entity property while mapping `ID`.
- `SiteId`, `TechnicianId`, and `EquipmentId` must exist as entity properties on the corresponding entity types before relationship creation/run.

That supports the current hypothesis: our imported Douglas JSON may include `Properties` and `JoinColumns.AttributeName`, but the runtime contextualization engine is checking a model descriptor table populated by mapping/UI hydration, not just the import JSON property list.

### 3. System-type choice may matter

Tutorial equipment entities are created from the built-in `Equipment` system type, not a bare user type. The UI-created entity type includes built-in descriptors and then adds custom descriptors during mapping. Douglas imports currently use `BaseEntityTypeId: "2"` / namespace usertypes, but we have not proven that this is equivalent to creating an Equipment-derived entity in the DTB UI.

The live export from Douglas adding/retyping descriptors (for example extra `SerialNumber`) is consistent with Fabric normalizing toward a system type after import, but contextualization still failed. That means imported descriptor metadata may be incomplete even when export shows the property names.

### 4. Contoso uses exact relationship join property names that differ from source columns where needed

Example: `AssetData.ID` becomes entity property `DistillerId`; the relationship joins on `DistillerId`, not on raw source column `ID`.

Douglas should therefore contextualize only on entity property names that mapping has truly materialized as model descriptors. If `Equipment.EquipmentId` is inferred from JSON but not materialized by a completed non-timeseries mapping operation, contextualization can fail exactly as observed.

## Proposed next Douglas variant

Do not retry the failed Douglas DTB. Create a fresh variant that more closely follows the tutorial's descriptor/materialization semantics.

Variant name suggestion:

`DouglasBagmakerDTB_NodeDemo_UIShape_Descriptors_YYYYMMDD_HHMM`

Changes to test:

1. Keep semantic relationships:
   - `Equipment contains System`: `Equipment.EquipmentId` -> `System.EquipmentId`, cardinality `1:N`.
   - `System contains Part`: `System.SystemId` -> `Part.SystemId`, cardinality `1:N`.
2. Ensure every relationship join property is created through a non-timeseries mapping before contextualization:
   - `Equipment`: map source `EquipmentId` to entity property `EquipmentId`.
   - `System`: map source `SystemId` and `EquipmentId` to entity properties `SystemId`, `EquipmentId`.
   - `Part`: map source `PartId`, `SystemId` to entity properties.
3. Consider matching UI/system type base semantics rather than only usertype JSON:
   - verify `BaseEntityTypeId` for UI-created Equipment/Generic/Process entities from a working Contoso export if possible.
   - do not assume `BaseEntityTypeId: "2"` is enough.
4. If using Fabric UI as calibration, manually create one tiny Contoso DTB from the attached files, run mappings/contextualization, then export it and diff its `EntityTypes`, `MappingOperations`, `EntityTypeRelationships`, and `ContextualizationOperations` against importer output.

## Separate Contoso runbook

To reproduce the tutorial baseline manually or through browser automation:

1. Load attached CSVs into a clean lakehouse with tutorial-compatible table names:
   - `assetdata`
   - `processdata`
   - `technicians`
   - maintenance requests table name matching the UI selection.
2. Create a fresh DTB item.
3. Create entity types in this order:
   - Distiller, Condenser, Reboiler, Process, Technician, MaintenanceRequest.
4. Run non-timeseries mappings first for all entities.
5. If the `timeseries` table is absent, skip tutorial time-series mappings or create a synthetic tutorial-compatible `timeseries` table; the four attached CSVs do not include the tutorial `timeseries` source table referenced by Part 2.
6. Create the five relationships exactly as Part 3 documents.
7. Run each contextualization operation immediately from relationship Scheduling.
8. Export the working DTB definition and use it as the descriptor/schema baseline.

## Open questions

1. Does a working UI-created Contoso export include relationship join fields beyond `JoinColumns.{FirstColumn,SecondColumn}.AttributeName`, such as property descriptor IDs?
2. Does UI creation assign different `BaseEntityTypeId` values for Equipment / Process / Generic that our Douglas importer needs to preserve?
3. Does contextualization require completed mapping operation runs to populate a descriptor store before relationship execution, even when the imported `EntityTypes/*.json` already lists those properties?
4. What is the public REST equivalent of pressing **Run** on a DTB mapping/contextualization operation? Current public Job Scheduler `ExecuteOperations` tests returned `InvalidJobType`.

## Current conclusion

The Contoso tutorial confirms that the documented contextualization model is relationship-first and property-name-based at the UI level, but successful runtime execution likely depends on UI/mapping-created property descriptors. Douglas' failure after parent-first correction points to missing/incorrect descriptor materialization for join columns, not merely wrong relationship cardinality.

## 2026-06-15 update — Douglas UID / JoinKey workaround selected

Stick supplied an independent ChatGPT analysis of the Douglas ZIP and contextualization failure. The important new hypothesis is that Fabric DTB may bind contextualization descriptors differently when a column is both:

1. part of `EntityInstanceIdSchema`, and
2. used as a relationship/contextualization join attribute.

The recommended next Douglas experiment is therefore not another parent-first retry. It is a clean source/model split:

- `EquipmentUID`, `SystemUID`, `PartUID` are only internal DTB entity instance IDs.
- `EquipmentJoinKey`, `SystemJoinKey`, and optionally `PartJoinKey` are explicit mapped DTB properties for relationships.
- Business IDs (`EquipmentId`, `SystemId`, `PartId`) remain mapped properties for traceability, but relationship contextualization joins do not use them.

Local compiler state has been updated to this fresh variant:

- `System isPartOf Equipment`, `ManyToOne`, join `System.EquipmentJoinKey = Equipment.EquipmentJoinKey`.
- `Part isPartOf System`, `ManyToOne`, join `Part.SystemJoinKey = System.SystemJoinKey`.
- source tables now target `equipment_dtb`, `systems_dtb`, `parts_dtb`, and `historian_timeseries_dtb`.

This aligns with Contoso Part 3's `N:1` tutorial relationships such as `Distiller isPartOf Process`, while also removing the likely identity-vs-join descriptor ambiguity.

Local verification after the patch: `.venv/bin/pytest -q` → `25 passed in 0.49s`.

Important deployment guardrail: this variant requires DTB-facing Lakehouse tables/views to exist before deployment. It must not be pointed at the old raw `equipment`, `systems`, `parts`, and `historian_timeseries` table names without first creating the explicit UID/join-key shape.
