# Lesson Learned — EquipmentIQ Node Lakehouse SourceSchema

Date: 2026-06-14

## Summary

The EquipmentIQ Node app's automatic Douglas ZIP → Lakehouse load path created root-level Lakehouse tables via OneLake + Fabric Lakehouse Load Table API. DTB definitions for this path must omit `SourceSchema`. Using `SourceSchema: dbo` caused Fabric DTB mapping to look under `Tables/dbo/<table>` and fail with `PATH_NOT_FOUND`.

## Evidence

Failure observed for `DouglasBagmakerDTB_NodeDemo` / `Equipment_equipment`:

```text
[Server Error] [PATH_NOT_FOUND] Path does not exist:
abfss://e5532483-0114-4ac2-8d3f-8105c7eb5543@onelake.pbidedicated.windows.net/510cb653-2a04-48e2-bd93-48e6f321ff44/Tables/dbo/equipment
```

Fabric Lakehouse table list showed root table paths like:

```text
.../510cb653-2a04-48e2-bd93-48e6f321ff44/Tables/<tableName>
```

## Durable rule

- For app-loaded tables, Source schema must be blank / omitted.
- This includes JoinKey `_dtb` tables (`equipment_dtb`, `systems_dtb`, `parts_dtb`, `historian_timeseries_dtb`) created by the Lakehouse Load Table API; they live at root `Tables/<table>`, not `Tables/dbo/<table>`.
- Use `dbo` only for pre-existing schema-enabled Lakehouse tables where physical paths are actually `Tables/dbo/<table>`.
- If a DTB was created with the wrong SourceSchema, avoid repeated `updateDefinition`; it can fail non-retriably with `ALMOperationImportFailed` on EntityType import.
- Safer recovery is a fresh DTB item with SourceSchema omitted plus an associated on-demand DTB Flow.

## Recovery used

Fresh no-schema item created:

```text
DouglasBagmakerDTB_NodeDemo_NoSchema
ID: 47be9dd3-6656-4b6a-add0-b4baf4613a67
```

Existing Lakehouse:

```text
EquipmentIQ_Douglas_NodeDemo_Raw
ID: 510cb653-2a04-48e2-bd93-48e6f321ff44
```

## 2026-06-15 regression note

The first JoinKey item `DouglasBagmakerDTB_NodeDemo_JoinKey_20260615_1843` regressed this rule: its compile artifact used `source_schema: "dbo"`, so `Equipment_equipment_dtb` failed with `PATH_NOT_FOUND` at `.../Tables/dbo/equipment_dtb` (root activity ID `57fbcca1-f5d4-4c43-bfa5-4e63299457f6`). Fix was to default compiler/CLI source schema to omitted/null, add regression tests, and create a fresh `NoSchema` JoinKey DTB/flow rather than retrying or updating the bad item.
