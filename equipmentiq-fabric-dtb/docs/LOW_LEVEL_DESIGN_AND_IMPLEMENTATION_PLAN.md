The reliable design is **not** “EquipmentIQ export → Fabric task-flow import.” It should be:

```text
EquipmentIQ Douglas bagmaker zip
   ↓
Importer/compiler service
   ↓
Fabric Lakehouse tables in OneLake
   ↓
Digital Twin Builder public definition parts
   ↓
Digital Twin Builder work item
   ↓
Mapping/contextualization flow execution
   ↓
Validation through DTB domain views + explorer
```

Use **Fabric IQ** as a parallel ontology mirror and v2 investigation path, but make **Digital Twin Builder’s own public definition** the v1 deployment target. Current public DTB definition docs list DTB-owned `EntityTypes`, `EntityTypeRelationships`, `MappingOperations`, and `ContextualizationOperations`, with `definition.json` tied to a `LakehouseId`; they do **not** show a documented external Fabric IQ `OntologyId` reference. ([Microsoft Learn][1])

---

# 1. Critical findings from the Douglas bagmaker zip

I inspected your uploaded kit. It contains:

```text
README.md
equipment.csv
systems.csv
parts.csv
historian_tags.csv
historian_timeseries.csv
ground_truth_bindings.csv
```

The important schema facts:

```text
equipment.csv                1 row
systems.csv                  6 rows
parts.csv                   14 rows
historian_tags.csv          12 rows
historian_timeseries.csv  2160 rows
ground_truth_bindings.csv   12 rows
```

The ontology implied by the export is clean:

```text
Equipment
  └── System
        └── Part
              └── Time series via HistorianTag
```

The time-series design is intentionally narrow:

```text
PreciseTimestamp, HistorianTag, Value
```

Source-truth rule: do not invent fields if the bundle is missing them. For Douglas, source inspection proves `historian_timeseries.csv` really has `PreciseTimestamp`, `HistorianTag`, and `Value`, and `parts.csv` really has `HistorianTag`. Therefore the compiler can map source `PreciseTimestamp` to DTB's required canonical time-series target property `Timestamp`. That is a DTB target-contract translation, not fabricated source data. If a future bundle lacks a real timestamp/time/temperature semantic, the importer must block and report the bundle defect instead of synthesizing one.

The README is right to use `HistorianTag` as the DTB link key. Microsoft’s DTB tutorial says a time-series mapping must link a time-series column to a non-time-series entity property, and the values must exactly match. ([Microsoft Learn][2])

There is one nuance that should be captured in the exporter and validator:

```text
historian_timeseries.csv has 12 tags × 180 timestamps = 2160 rows.
parts.csv has 11 tagged parts and 3 deliberately untagged parts.
M5_AUX_VIB09.PV is a deliberate decoy with no ontology target.
```

So a correct DTB run should **not** necessarily create 2160 linked `Part` time-series rows. The expected pass condition is:

```text
11 linked historian tags × 180 timestamps = 1980 linked rows
1 decoy tag × 180 timestamps = 180 intentionally unmatched rows
3 parts have no HistorianTag and should have no time-series rows
```

That gives you a strong negative-control test: the importer should prove the join works **and** that it does not force-bind the decoy tag.

---

# 2. Target end state in Fabric

Create a dedicated Fabric workspace on Fabric capacity rather than relying on `My workspace` for the service workflow. DTB requires a Fabric-enabled workspace/capacity, DTB enabled in tenant settings, and no Autoscale Billing for Spark on that tenant. ([Microsoft Learn][3])

The final workspace should contain:

```text
DouglasBagmakerRaw              Lakehouse
DouglasBagmakerDTB              Digital Twin Builder item
DouglasBagmakerDTBOnDemand      DTB flow child item, created by DTB
DouglasBagmakerDTBdtdm          DTB-associated lakehouse / SQL endpoint
DouglasBagmakerIQ               Optional Fabric IQ Ontology mirror
```

The DTB work item should contain:

```text
Entity types:
- Equipment
- System
- Part

Static mappings:
- Equipment ← equipment
- System    ← systems
- Part      ← parts

Time-series mapping:
- Part ← historian_timeseries
- Timestamp column: PreciseTimestamp
- Value column: Value
- Link: Part.HistorianTag = historian_timeseries.HistorianTag

Relationship/contextualization:
- System isPartOf Equipment
- Part isPartOf System
```

Updated 2026-06-15 contextualization implementation shape: use DTB-facing tables/views with explicit identity and relationship-key separation. `EquipmentUID`, `SystemUID`, and `PartUID` are only `EntityInstanceIdSchema` fields. `EquipmentJoinKey` and `SystemJoinKey` are separately mapped DTB properties and are the only relationship join attributes. This avoids the observed descriptor-binding failure where Fabric contextualization could not bind `EquipmentId` after that field had also been used as an entity identity column.

```text
equipment_dtb:
  EquipmentUID, EquipmentId, EquipmentJoinKey, DisplayName, Manufacturer, ModelNumber

systems_dtb:
  SystemUID, SystemId, SystemJoinKey, EquipmentId, EquipmentJoinKey, DisplayName

parts_dtb:
  PartUID, PartId, PartJoinKey, DisplayName, Category, SystemId, SystemJoinKey, HistorianTag

historian_timeseries_dtb:
  PreciseTimestamp, HistorianTag, Value

Relationship/contextualization:
  System isPartOf Equipment, ManyToOne, System.EquipmentJoinKey = Equipment.EquipmentJoinKey
  Part   isPartOf System,    ManyToOne, Part.SystemJoinKey      = System.SystemJoinKey
```

The validation target is the DTB domain layer. Microsoft’s DTB tutorial states that the DTB-associated lakehouse exposes a `dom` domain layer where each entity type appears as `entityname_property` and `entityname_timeseries`, and the `relationships` view captures relationship instances. ([Microsoft Learn][4])

---

# 3. Architectural decision

## V1: direct DTB compiler

Build a compiler that converts the EquipmentIQ bundle into **Digital Twin Builder definition parts**.

This is the main path because DTB already has REST APIs for create, get definition, and update definition. The create API accepts a public definition with base64-encoded definition parts such as `definition.json`, `.platform`, `EntityTypes/...`, `MappingOperations/...`, and `ContextualizationOperations/...`. ([Microsoft Learn][5])

## V1.5: Fabric IQ ontology mirror

Also generate a Fabric IQ Ontology item from the same bundle. Fabric IQ Ontology APIs support create/update with public definition and support user, service principal, and managed identity auth. ([Microsoft Learn][6])

This is useful for:

```text
- Validating the EquipmentIQ semantic export shape
- Proving a future Fabric IQ-first architecture
- Testing whether DTB can reference IQ-created ontologies
```

But v1 should not depend on that reference until proven.

## V2: IQ as source of truth, DTB as projection

Only move to this once the “Ontology-item question” is answered. Current public DTB definition parts do not document a Fabric IQ ontology reference, while the Fabric IQ Ontology definition has its own `EntityTypes`, `DataBindings`, `RelationshipTypes`, and `Contextualizations` structure. ([Microsoft Learn][7])

---

# 4. Authentication design

This matters because the APIs are inconsistent today.

## DTB APIs

Digital Twin Builder create/update/get definition currently support **user identity** but not service principals or managed identities. ([Microsoft Learn][5])

That means the first reliable workflow must use a delegated user token:

```bash
az login --use-device-code

FABRIC_TOKEN=$(az account get-access-token \
  --resource https://api.fabric.microsoft.com \
  --query accessToken -o tsv)
```

## OneLake / Lakehouse

Use OneLake ADLS-compatible APIs or SDKs for file upload. OneLake supports access through ADLS/Blob-compatible APIs and SDKs, using OneLake URIs. ([Microsoft Learn][8])

You’ll need a storage audience token:

```bash
STORAGE_TOKEN=$(az account get-access-token \
  --resource https://storage.azure.com/ \
  --query accessToken -o tsv)
```

## Fabric IQ

Fabric IQ Ontology can be automated later using a managed identity or service principal, because the Ontology APIs support those identities. ([Microsoft Learn][6])

## Production implication

A truly headless Azure-hosted service cannot be fully service-principal-only until DTB adds service principal / managed identity support. For now:

```text
Local POC:
  delegated user token for everything

Azure-hosted v1:
  managed identity for Lakehouse + optional IQ
  delegated user token for DTB create/update/run steps

Azure-hosted v2:
  fully managed identity once DTB supports it, or if DTB can consume a Fabric IQ ontology created by MI
```

---

# 5. Low-level component design

Create a repo named:

```text
equipmentiq-fabric-dtb
```

Recommended structure:

```text
equipmentiq-fabric-dtb/
  AGENTS.md
  README.md
  SETUP.md
  pyproject.toml

  src/eiq_dtb_importer/
    __init__.py
    cli.py
    config.py
    auth.py
    fabric_client.py
    onelake.py
    lakehouse.py
    equipmentiq_zip.py
    model.py
    sanitizer.py
    ids.py
    dtb_definition.py
    dtb_items.py
    dtb_flows.py
    iq_ontology.py
    validator.py
    playwright_runner.py
    report.py

  tests/
    test_zip_reader.py
    test_sanitizer.py
    test_ids.py
    test_dtb_definition.py
    test_iq_definition.py
    test_expected_counts.py

  templates/
    baseline_dtb_export/
      README.md
      definition_parts/

  samples/
    dbm-rh-m5-dtb-e2e-kit.zip

  scripts/
    00_bootstrap_wsl.sh
    10_preflight.sh
    20_import_zip.sh
    30_create_or_update_dtb.sh
    40_run_dtb_operations.sh
    50_validate.sh

  runs/
    .gitkeep

  infra/
    containerapps/
      main.bicep
    docker/
      Dockerfile
```

Use Python for the importer because it gives you strong CSV/schema handling, API clients, Playwright, and easy packaging into Azure Container Apps.

Suggested dependencies:

```toml
[project]
dependencies = [
  "typer",
  "rich",
  "pydantic",
  "pandas",
  "pyarrow",
  "httpx",
  "tenacity",
  "azure-identity",
  "azure-storage-file-datalake",
  "xxhash",
  "python-slugify",
  "playwright",
]
```

---

# 6. Configuration contract

Create a run config like:

```yaml
tenant_id: "<tenant-guid>"
subscription_id: "<subscription-guid>"

workspace:
  id: "<fabric-workspace-guid>"
  name: "IndustrialAITest"

source:
  zip_path: "/mnt/data/dbm-rh-m5-dtb-e2e-kit.zip"
  equipmentiq_manifest_path: null

fabric:
  lakehouse_name: "DouglasBagmakerRaw"
  dtb_name: "DouglasBagmakerDTB"
  iq_ontology_name: "DouglasBagmakerIQ"
  create_iq_mirror: true

deployment:
  mode: "reuse_or_create"     # reuse_or_create | recreate | update_existing
  allow_delete: false
  run_operations: true
  run_operations_strategy: "api_then_playwright"
  validate: true

sanitizer:
  profile: "fabric_preview_strict"
  max_property_length: 26
  max_entity_length: 26
  collision_hash_length: 6

tables:
  equipment: "equipment"
  systems: "systems"
  parts: "parts"
  historian_tags: "historian_tags"
  historian_timeseries: "historian_timeseries"
  ground_truth_bindings: "ground_truth_bindings"
```

The `runs/<timestamp>/state.json` file should persist:

```json
{
  "workspaceId": "...",
  "lakehouseId": "...",
  "dtbId": "...",
  "dtbOnDemandFlowId": "...",
  "iqOntologyId": "...",
  "uploadedFiles": [],
  "loadedTables": [],
  "operationIds": [],
  "definitionHash": "...",
  "validation": {}
}
```

---

# 7. EquipmentIQ import model

The importer should normalize the bundle into an internal model:

```python
class EntityType:
    name: str
    table: str
    key_columns: list[str]
    static_properties: list[Property]
    time_series_properties: list[Property]

class RelationshipType:
    name: str
    source_entity: str
    target_entity: str
    source_join_property: str
    target_join_property: str
    cardinality: Literal["OneToMany", "ManyToOne"]

class TimeSeriesBinding:
    entity: str
    table: str
    timestamp_column: str
    value_column: str
    entity_link_property: str
    timeseries_link_column: str
```

For the Douglas bagmaker, compile:

```yaml
entityTypes:
  Equipment:
    table: equipment_dtb
    uniqueId: [EquipmentUID]
    properties:
      - EquipmentUID
      - EquipmentId
      - EquipmentJoinKey
      - DisplayName
      - Manufacturer
      - ModelNumber

  System:
    table: systems_dtb
    uniqueId: [SystemUID]
    properties:
      - SystemUID
      - SystemId
      - SystemJoinKey
      - DisplayName
      - EquipmentId
      - EquipmentJoinKey

  Part:
    table: parts_dtb
    uniqueId: [PartUID]
    properties:
      - PartUID
      - PartId
      - PartJoinKey
      - DisplayName
      - Category
      - SystemId
      - SystemJoinKey
      - HistorianTag
    timeseriesProperties:
      - Timestamp: DateTime
      - Value: Double

relationships:
  System_isPartOf_Equipment:
    relationshipName: isPartOf
    firstEntity: System
    firstJoinProperty: EquipmentJoinKey
    secondEntity: Equipment
    secondJoinProperty: EquipmentJoinKey
    cardinality: ManyToOne

  Part_isPartOf_System:
    relationshipName: isPartOf
    firstEntity: Part
    firstJoinProperty: SystemJoinKey
    secondEntity: System
    secondJoinProperty: SystemJoinKey
    cardinality: ManyToOne

timeSeries:
  Part_Value:
    entity: Part
    table: historian_timeseries_dtb
    timestampColumn: PreciseTimestamp
    valueColumn: Value
    entityLinkProperty: HistorianTag
    timeseriesLinkColumn: HistorianTag
```

The Microsoft DTB public definition supports relationship files with `FirstEntityTypeId`, `SecondEntityTypeId`, cardinality, and contextualization operations with join columns; mapping operations support source table details, mapped properties, unique ID schema, and time-series link properties. ([Microsoft Learn][1])

### 7.1 Relationship contextualization compatibility lesson — 2026-06-15

Do not compile Douglas contextualization by reusing entity instance ID columns (`EquipmentId`, `SystemId`, `PartId`) as relationship join attributes. Both the original child-first `ManyToOne contains` shape and the later parent-first `OneToMany contains` shape imported and mapped, but runtime contextualization failed with missing property descriptor errors.

Original child-first failure on `DouglasBagmakerDTB_NodeDemo_NoSchema`:

```text
[User Error] The required property descriptor for column 'EquipmentId' does not exist in the data model (EntityTypeId=117233767744208). Root Activity Id: eaeb81ea-cee6-4a45-8e47-903fa648d5b8
```

Parent-first retry on a fresh item later failed looking for the same `EquipmentId` column on the parent `Equipment` entity. Generated/exported EntityTypes contained the property names in both cases, so the failure is a relationship/contextualization descriptor-binding issue, not a missing-property source/model issue.

Evidence checked before fixing:

```text
Microsoft Learn contextualization docs: First entity + Second entity join properties, with 1:N when one source/first entity connects to many target/second entities.
Microsoft Learn tutorial Part 3: both parent-first 1:N and child-to-parent N:1 examples exist; `isPartOf` is explicitly N:1.
Fabric REST DTB definition docs: contextualization JoinColumns are FirstColumn/SecondColumn aligned with relationship first/second entity IDs.
Public Learn/GitHub/Q&A search: no exact indexed match for the literal error string.
```

Active compiler rule:

```text
UID columns are identity-only: EquipmentUID, SystemUID, PartUID.
JoinKey columns are normal mapped relationship properties: EquipmentJoinKey, SystemJoinKey, PartJoinKey.
RelationshipType name = isPartOf for child-to-parent hierarchy links.
RelationshipCardinality = ManyToOne.
Contextualization FirstColumn = child/source JoinKey property.
Contextualization SecondColumn = parent/target JoinKey property.
```

For Douglas specifically:

```text
System -> Equipment, ManyToOne, System.EquipmentJoinKey = Equipment.EquipmentJoinKey
Part   -> System,    ManyToOne, Part.SystemJoinKey      = System.SystemJoinKey
```

Recovery rule: do not retry contextualization blindly on a failed item. Create a fresh no-schema JoinKey DTB item only after source/definition shape changes, then rerun operations serially.

---

# 8. Naming and sanitizer rules

Adopt a conservative sanitizer now, even if the APIs allow more. Your exporter should be stricter than the preview UI.

## Item names

DTB names can include letters, numbers, and underscores, with no spaces or dashes in the tutorial UI; the REST API also says the DTB display name should start with a letter, contain only letters/numbers/underscore, and be under 100 chars. ([Microsoft Learn][9])

## Entity/property names

Fabric IQ Ontology public definition permits entity and property names matching:

```regex
^[a-zA-Z][a-zA-Z0-9_-]{0,127}$
```

([Microsoft Learn][7])

But your exporter should use:

```text
Start with letter
Allow letters, numbers, underscore
Max 26 chars for entity/property names until preview behavior is calibrated
Preserve original source column names
Preserve original row values
Emit a name map file
```

Important: the long `SystemId` values are **row values**, not property names. Do not sanitize them unless DTB rejects them as join values. The current static property names are all safe:

```text
EquipmentId       11
DisplayName       11
Manufacturer      12
ModelNumber       11
SystemId           8
PartId             6
Category           8
HistorianTag      12
PreciseTimestamp  16
Value              5
```

Generate a sanitizer / DTB-target trace. Preserve source column names, but distinguish
source names from DTB-required target property names. For time-series mappings, the
Microsoft DTB runtime requires the target timestamp property to be the canonical
`Timestamp`, even when the source bundle uses a richer source column name such as
`PreciseTimestamp`.

```json
{
  "sourceName": "PreciseTimestamp",
  "targetName": "Timestamp",
  "changed": true,
  "reason": "DTB canonical time-series target property; source timestamp semantic verified in bundle"
}
```

For future DTDL exports, use collision-safe shortening:

```text
MotorControllerOutputTemperature
→ MotorControllerOutput_ab12cd
```

---

# 9. Stable IDs

DTB entity type IDs must be BigInt values greater than 10,000. ([Microsoft Learn][1])

Use deterministic IDs so re-running the importer updates the same logical definition:

```python
def stable_bigint(namespace: str, name: str) -> str:
    raw = xxhash.xxh64_intdigest(f"{namespace}:{name}")
    value = raw & 0x7FFF_FFFF_FFFF_FFFF
    if value <= 10000:
        value += 10000
    return str(value)
```

Use deterministic UUIDv5 for operation IDs:

```python
uuid.uuid5(RUN_NAMESPACE, "Mapping:Part:parts_dtb:NonTimeSeries")
uuid.uuid5(RUN_NAMESPACE, "Mapping:Part:historian_timeseries_dtb:TimeSeries")
uuid.uuid5(RUN_NAMESPACE, "Contextualization:Part_isPartOf_System")
```

Persist all generated IDs in:

```text
runs/<run-id>/generated_ids.json
```

---

# 10. Fabric API execution flow

## Step 0 — Preflight

Commands:

```bash
az login --use-device-code
az account show

python -m eiq_dtb_importer preflight \
  --config config.douglas.yaml
```

Preflight checks:

```text
- Fabric token can be acquired
- Storage token can be acquired
- Workspace exists
- Workspace is on Fabric capacity
- Workspace/capacity SKU is sized for Spark-backed API work, not merely present
- DTB preview is enabled
- Autoscale Billing for Spark is not enabled
- User has Contributor role or sufficient write permissions
- Existing item names are checked
```

DTB prerequisites are important because Microsoft explicitly lists DTB preview enablement and no Autoscale Billing for Spark as prerequisites/limitations. ([Microsoft Learn][3])

## Capacity sizing and API failure semantics

Treat Fabric capacity as part of the API contract. Several Fabric REST calls are thin control-plane wrappers around Spark, Lakehouse metadata, SQL endpoint sync, or DTB backend work. A valid request can therefore fail, stall, time out, or return a misleading generic API error when the backing Fabric capacity is undersized, cold, saturated, or admitting too many jobs.

Do **not** automatically classify these symptoms as bad OAuth, bad JSON, broken schema, or an impossible API path:

```text
- HTTP 429/430, especially TooManyRequestsForCapacity
- long-running operations that sit in NotStarted/Running for unusually long periods
- API pollers timing out while Fabric later reports Succeeded / 100%
- ALMOperationImportFailed or OperationFailure during preview/control-plane instability
- generic Server Error / unknown error after a job has already been queued
- SQL endpoint or Lakehouse metadata visibility lag immediately after table loads
```

Implementation rule:

1. Capture the operation ID, request ID, root activity ID, capacity ID/SKU, timestamps, and final LRO payload.
2. Check whether the operation is capacity/admission-shaped before changing data or definition code.
3. Retry only with bounded backoff and a serialized plan. For Lakehouse table loads, load one table at a time and write a separate artifact per table.
4. If capacity symptoms repeat, stop retrying and mark the gate `blocked_capacity_sizing` or equivalent. The fix is capacity/headroom/admin action, not more payload churn.
5. Only promote a failure to a semantic/compiler defect after capacity/admission and metadata lag have been ruled out with evidence.

For this project, F2 was too marginal for reliable proof work and F4 still needs serialized table loads. Production guidance should size capacity for the expected number of concurrent Lakehouse loads, DTB operations, SQL endpoint refreshes, and user workloads, then validate under that concurrency. Small proof SKUs are acceptable only when the implementation deliberately serializes work and labels capacity blockers honestly.

## Step 1 — Create or reuse lakehouse

API:

```http
POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/lakehouses
```

Body:

```json
{
  "displayName": "DouglasBagmakerRaw"
}
```

Fabric automatically provisions a SQL analytics endpoint with the lakehouse. ([Microsoft Learn][10])

Then get properties:

```http
GET https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/lakehouses/{lakehouseId}
```

Capture:

```text
oneLakeFilesPath
oneLakeTablesPath
sqlEndpointProperties.connectionString
```

Microsoft’s lakehouse API returns the OneLake file/table paths and SQL endpoint properties. ([Microsoft Learn][10])

## Step 2 — Upload EquipmentIQ CSVs to OneLake

Upload to:

```text
Files/equipmentiq/douglas_bagmaker/equipment.csv
Files/equipmentiq/douglas_bagmaker/systems.csv
Files/equipmentiq/douglas_bagmaker/parts.csv
Files/equipmentiq/douglas_bagmaker/historian_tags.csv
Files/equipmentiq/douglas_bagmaker/historian_timeseries.csv
Files/equipmentiq/douglas_bagmaker/ground_truth_bindings.csv
```

Use the OneLake GUID URI form:

```text
https://onelake.dfs.fabric.microsoft.com/<workspaceGuid>/<lakehouseGuid>/Files/equipmentiq/douglas_bagmaker/equipment.csv
```

OneLake supports GUID-based paths, which are stable across renames. ([Microsoft Learn][8])

Implementation options:

```text
Preferred:
  azure-storage-file-datalake with custom OneLake endpoint

Fallback:
  raw ADLS REST calls using PUT create file + PATCH append + PATCH flush
```

Microsoft shows the create-file pattern for OneLake over ADLS APIs. ([Microsoft Learn][8])

## Step 3 — Load CSV files into Delta tables

Use Lakehouse Load Table API. Microsoft describes this as the programmatic equivalent of “Load to Tables.” ([Microsoft Learn][10])

Capacity note: each Lakehouse Load Table API call can admit Spark-backed work even for tiny CSV files. Do not run all table loads in parallel on small proof capacity. Load tables serially, poll each operation to terminal state, and persist one run artifact per table before starting the next. Parallel load failures on small SKUs are capacity-sizing/admission evidence unless the operation details prove a data/schema error.

For each file:

```http
POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/lakehouses/{lakehouseId}/tables/equipment/load
```

Body:

```json
{
  "relativePath": "Files/equipmentiq/douglas_bagmaker/equipment.csv",
  "pathType": "File",
  "mode": "Overwrite",
  "formatOptions": {
    "header": true,
    "delimiter": ",",
    "format": "Csv"
  }
}
```

Repeat for:

```text
equipment
systems
parts
historian_tags
historian_timeseries
ground_truth_bindings
```

Poll:

```http
GET https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/lakehouses/{lakehouseId}/operations/{operationId}
```

The load status values are:

```text
1 = Not started
2 = Running
3 = Success
4 = Failed
```

([Microsoft Learn][10])

Then list tables:

```http
GET https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/lakehouses/{lakehouseId}/tables
```

Confirm all six Delta tables exist.

---

# 11. DTB definition compiler

The compiler emits this logical part tree:

```text
definition.json
.platform

EntityTypes/<equipmentEntityTypeId>.json
EntityTypes/<systemEntityTypeId>.json
EntityTypes/<partEntityTypeId>.json

EntityTypeRelationships/<equipmentContainsSystemRelationshipId>.json
EntityTypeRelationships/<systemContainsPartRelationshipId>.json

MappingOperations/<equipmentStaticMappingOperationId>.json
MappingOperations/<systemStaticMappingOperationId>.json
MappingOperations/<partStaticMappingOperationId>.json
MappingOperations/<partTimeSeriesMappingOperationId>.json

ContextualizationOperations/<equipmentContainsSystemContextOperationId>.json
ContextualizationOperations/<systemContainsPartContextOperationId>.json
```

Root `definition.json`:

```json
{
  "LakehouseId": "<DouglasBagmakerRaw lakehouse item id>"
}
```

DTB public definition requires `definition.json` and uses `LakehouseId` as the parent lakehouse reference. ([Microsoft Learn][1])

Example entity type part for `Part`:

```json
{
  "Id": "<partEntityTypeId>",
  "Namespace": "usertypes",
  "BaseEntityTypeId": "2",
  "Name": "Part",
  "Properties": [
    { "Id": "<partIdPropId>", "Name": "PartId", "ValueType": "String" },
    { "Id": "<partDisplayNamePropId>", "Name": "DisplayName", "ValueType": "String" },
    { "Id": "<categoryPropId>", "Name": "Category", "ValueType": "String" },
    { "Id": "<systemIdPropId>", "Name": "SystemId", "ValueType": "String" },
    { "Id": "<historianTagPropId>", "Name": "HistorianTag", "ValueType": "String" }
  ],
  "TimeseriesProperties": [
    { "Id": "<timestampPropId>", "Name": "Timestamp", "ValueType": "DateTime" },
    { "Id": "<valuePropId>", "Name": "Value", "ValueType": "Double" }
  ]
}
```

Use a calibration export before hard-coding `BaseEntityTypeId`. The public example uses `BaseEntityTypeId: "2"`, but a one-time `getDefinition` from your existing working `AltouraDigitalTwinTest` should be the source of truth for the current preview environment. The get-definition API returns the DTB public definition as base64 parts. ([Microsoft Learn][11])

## EntityType import lessons from Lawrence/F4 ladder

Treat EntityType IDs as a Fabric import-contract field, not a free deterministic ID namespace. The clean Lawrence/F4 ladder proved:

```text
PASS: docs/calibration EntityType ID 139950578358348 + name Equipment1 + docs properties
PASS: same EntityType ID/properties + name Equipment
FAIL: only EntityType ID changed to generated 580786628437170
PASS: same EntityType ID + EquipmentIQ-style property names with doc-style property IDs
PASS: same EntityType ID + EquipmentIQ-style property names with generated property IDs
PASS: same EntityType ID + name Equipment + EquipmentIQ-style property names/generated property IDs
FAIL: EntityType ID 500000000000001 + otherwise accepted Equipment/generated-props shape
PASS: EntityType ID 100000000000001 + otherwise accepted Equipment/generated-props shape
PASS: EntityType ID 200000000000001 + otherwise accepted Equipment/generated-props shape
FAIL: EntityType ID 300000000000001 + otherwise accepted Equipment/generated-props shape
```

Published Microsoft rules/conventions from the DTB definition docs:

```text
- EntityType file name is the entity type ID: EntityTypes/<Id>.json
- EntityType.Id type: BigInt
- EntityType.Id is required and unique
- EntityType.Id value is always greater than 10,000
- Namespace allowed value: usertypes
- BaseEntityTypeId type: BigInt; docs examples use "2" for Equipment-like base type
- EntityTypeProperty.Id type: long
- DTB item displayName must start with a letter, contain only letters/numbers/underscore, and be under 100 characters
```

The docs do **not** publish a maximum EntityType ID value or allocator algorithm. The Lawrence ladder proves there is nevertheless a hidden importer profile/range constraint.

Implementation consequence: do not use arbitrary stable-generated EntityType IDs for production DTB imports until an accepted Fabric ID allocator/profile is proven. Prefer a calibration-derived/import-safe EntityType ID strategy, or create a minimal accepted DTB and roundtrip-export Fabric-assigned IDs before expanding the definition. A production-looking single `Equipment` EntityType is accepted when the EntityType ID stays import-safe. Entity display names, EquipmentIQ property names, and generated property IDs are not the current blocker; generated/high EntityType ID shape/range is. The current empirical boundary is `200000000000001` PASS and `300000000000001` FAIL for the same otherwise accepted shape.

Every EntityType compatibility result must update both the failures/lessons ledger and this implementation section with the variant, changed variable, pass/fail status, Fabric operation ID when failed, DTB item ID when passed, and artifact path.

Example time-series mapping operation for `Part`.

Important runtime lesson from Lawrence/F4 on 2026-06-14: `SourceColumn` may be
the EquipmentIQ bundle column (`PreciseTimestamp`), but `EntityTypePropertyName`
for the timestamp must be the DTB canonical target property `Timestamp`. The
incorrect mapping `PreciseTimestamp -> PreciseTimestamp` imported but failed at
run time with “expected a timestamp property in the map but found none / time or
temp is required for a timeseries mapping.” The corrected fresh DTB
`DouglasBagmakerDTB_TimestampFix_20260614_1525` proved the resolution when
`Part_historian_timeseries_TimeSeries` completed successfully.

```json
{
  "OperationId": "<uuid>",
  "DisplayName": "Part_Value_TimeSeries",
  "OperationType": "Mapping",
  "EntityTypeId": "<partEntityTypeId>",
  "MappingOperationProperties": {
    "MappingType": "TimeSeries",
    "MappedProperties": [
      {
        "SourceColumn": "PreciseTimestamp",
        "EntityTypePropertyName": "Timestamp"
      },
      {
        "SourceColumn": "Value",
        "EntityTypePropertyName": "Value"
      }
    ],
    "ProcessingType": "Incremental",
    "EntityInstanceIdSchema": null,
    "TimeseriesEntityLinkProperties": {
      "EntityProperty": "HistorianTag",
      "TimeseriesProperty": "HistorianTag"
    }
  },
  "SourceTableProperties": {
    "SourceType": "LakehouseTables",
    "WorkspaceId": "<workspaceId>",
    "ItemId": "<lakehouseId>",
    "SourceTableName": "historian_timeseries",
    "SourceSchema": null
  },
  "Filters": null
}
```

The docs show `TimeseriesEntityLinkProperties` as the mechanism linking an entity property to a time-series column. ([Microsoft Learn][1])

---

# 12. Create/update DTB item

Preferred sequence:

```text
1. Create lakehouse
2. Upload/load tables
3. Create DTB item with minimal definition
4. Let Fabric provision DTB child resources
5. Get DTB definition as baseline
6. Update DTB definition with generated full definition
7. Run mapping/contextualization operations
```

Why create minimal first? Because DTB creates child flow items and backing DTB resources. The DTB flow docs state an on-demand flow is created by default when the DTB item is created. ([Microsoft Learn][12])

Create:

```http
POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/digitaltwinbuilders
```

Body:

```json
{
  "displayName": "DouglasBagmakerDTB",
  "description": "EquipmentIQ Douglas DBM RH M5 Bagmaker import",
  "definition": {
    "parts": [
      {
        "path": "definition.json",
        "payload": "<base64 { \"LakehouseId\": \"...\" }>",
        "payloadType": "InlineBase64"
      }
    ]
  }
}
```

Update full definition:

```http
POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/digitaltwinbuilders/{digitaltwinbuilderId}/updateDefinition
```

The update-definition API overrides the current DTB definition and supports LRO/polling. ([Microsoft Learn][13])

---

# 13. Running DTB mappings and contextualization

This is the one execution gap to handle explicitly.

The DTB public definition can define mapping/contextualization operations, and the definition docs say mapping/contextualization operations can be run using a `DigitalTwinBuilderFlow` artifact. ([Microsoft Learn][1]) The flow docs say DTB flows execute mapping and contextualization operations, an on-demand flow is created by default, and users run on-demand operations from the Scheduling tab. ([Microsoft Learn][12])

The public docs I verified do **not** clearly expose a simple documented “run this DTB flow now” REST endpoint in the same way they document create/update/get definition. Therefore build the runner with two strategies:

## Strategy A — API runner

Codex should first search the installed/public Fabric REST surface for:

```text
DigitalTwinBuilderFlow run
Fabric item jobs
Run on-demand flow
Schedule flow
```

Allowed result:

```text
A documented public Fabric API endpoint that runs DTB flow items or item jobs.
```

Disallowed result:

```text
Calling undocumented portal/private backend endpoints in production.
```

## Strategy B — Playwright fallback

Use Playwright only to click **Run** for existing operations. Do **not** use Playwright to build the ontology canvas.

Scope:

```text
- Open DTB item URL
- Go to Manage operations or Scheduling tab
- Trigger static mappings first
- Wait for Completed
- Trigger time-series mapping
- Wait for Completed
- Trigger contextualization operations
- Wait for Completed
- Capture screenshots and operation statuses
```

Run order should be explicit:

```text
1. `Equipment_equipment_dtb` non-time-series mapping
2. `System_systems_dtb` non-time-series mapping
3. `Part_parts_dtb` non-time-series mapping
4. `Part_historian_timeseries_dtb_TimeSeries` mapping
5. `System_isPartOf_Equipment_Contextualization`
6. `Part_isPartOf_System_Contextualization`
```

Avoid putting too much in a single scheduled flow. Microsoft warns that DTB flows execute mappings first, then contextualization, and a failed operation cancels downstream operations; separate schedules/flows reduce blast radius. ([Microsoft Learn][12])

---

# 14. Fabric IQ ontology mirror

Create this as a parallel output, not the DTB source of truth.

Fabric IQ Ontology definition parts include:

```text
definition.json
.platform
EntityTypes/{ID}/definition.json
EntityTypes/{ID}/DataBindings/{bindingId}.json
RelationshipTypes/{ID}/definition.json
RelationshipTypes/{ID}/Contextualizations/{contextualizationId}.json
```

([Microsoft Learn][7])

For Fabric IQ:

```text
EntityTypes:
- Equipment
- System
- Part

DataBindings:
- Equipment non-time-series binding → equipment
- System non-time-series binding → systems
- Part non-time-series binding → parts
- Part time-series binding → historian_timeseries

RelationshipTypes:
- contains, Equipment → System
- contains, System → Part

Contextualizations:
- EquipmentId binding
- SystemId binding
```

Fabric IQ data bindings explicitly support `NonTimeSeries` and `TimeSeries`, a timestamp column for time-series, property bindings, and Lakehouse table source properties. ([Microsoft Learn][7])

Create:

```http
POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/ontologies
```

Update:

```http
POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/ontologies/{ontologyId}/updateDefinition
```

The point of this mirror is to answer:

```text
Can a DTB item reference an API-created Fabric IQ Ontology item?
```

Test plan:

```text
1. Create DouglasBagmakerIQ by API.
2. Create DouglasBagmakerDTB by API.
3. Export DTB definition with getDefinition.
4. Search all DTB definition parts for ontologyId / Ontology / IQ / external reference.
5. Try portal path: create/open DTB and inspect whether an existing IQ ontology can be selected.
6. If no reference exists, mark v2 architecture as “generate both DTB and IQ from EquipmentIQ manifest.”
```

Expected result based on current public definition: DTB owns its own ontology model; Fabric IQ is a sibling/mirror, not a referenced source.

---

# 15. Validation plan

The validator should produce a machine-readable report:

```json
{
  "lakehouse": {
    "tables": {
      "equipment": 1,
      "systems": 6,
      "parts": 14,
      "historian_tags": 12,
      "historian_timeseries": 2160,
      "ground_truth_bindings": 12
    }
  },
  "dtb": {
    "entityTypes": ["Equipment", "System", "Part"],
    "relationships": ["System_isPartOf_Equipment", "Part_isPartOf_System"],
    "sourceTables": ["equipment_dtb", "systems_dtb", "parts_dtb", "historian_timeseries_dtb"],
    "mappingsCompleted": true,
    "contextualizationsCompleted": true
  },
  "expectedResults": {
    "equipmentInstances": 1,
    "systemInstances": 6,
    "partInstances": 14,
    "linkedTimeSeriesRows": 1980,
    "unmatchedTimeSeriesRows": 180,
    "equipmentSystemRelationships": 6,
    "systemPartRelationships": 14
  }
}
```

## Lakehouse validation

Before DTB:

```sql
SELECT COUNT(*) FROM equipment;                 -- 1
SELECT COUNT(*) FROM systems;                   -- 6
SELECT COUNT(*) FROM parts;                     -- 14
SELECT COUNT(*) FROM historian_timeseries;      -- 2160
```

Time-series join validation:

```sql
SELECT COUNT(*) AS linked_rows
FROM historian_timeseries ts
JOIN parts p
  ON ts.HistorianTag = p.HistorianTag;
-- Expected: 1980
```

Decoy validation:

```sql
SELECT ts.HistorianTag, COUNT(*) AS orphan_rows
FROM historian_timeseries ts
LEFT JOIN parts p
  ON ts.HistorianTag = p.HistorianTag
WHERE p.PartId IS NULL
GROUP BY ts.HistorianTag;
-- Expected: M5_AUX_VIB09.PV, 180 rows
```

Relationship validation:

```sql
SELECT COUNT(*) FROM systems s
JOIN equipment e
  ON s.EquipmentId = e.EquipmentId;
-- Expected: 6

SELECT COUNT(*) FROM parts p
JOIN systems s
  ON p.SystemId = s.SystemId;
-- Expected: 14
```

## DTB domain-layer validation

After DTB operations complete, query the associated `DouglasBagmakerDTBdtdm` SQL endpoint:

```sql
SELECT COUNT(*) FROM dom.Equipment_property;      -- 1
SELECT COUNT(*) FROM dom.System_property;         -- 6
SELECT COUNT(*) FROM dom.Part_property;           -- 14
SELECT COUNT(*) FROM dom.Part_timeseries;         -- 1980 expected
SELECT COUNT(*) FROM dom.relationships;           -- 20 expected if both relationships land
```

The DTB tutorial says the associated SQL endpoint has a `dbo` base layer and `dom` domain layer, with property/timeseries views per entity and a `relationships` view. ([Microsoft Learn][4])

## Explorer validation

Use either Playwright or manual spot check:

```text
Search: Jaw Assembly
Expected instance: m1_part_10
Chart: Value
Expected trend: M5_JAW_TQ007.PV climbs toward threshold in final ~15 minutes
```

---

# 16. Exporter calibration matrix

These are the observations you specifically asked to capture, converted into pass/fail criteria.

| Observation            | Test                                                                                                                            | Expected result                                                                    | Exporter decision                                     |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ----------------------------------------------------- |
| Naming limits          | Try generated names using strict 26-char sanitizer; also run a controlled test with a >26-char property in a throwaway DTB item | Current Douglas names pass. Long test determines actual preview rejection behavior | Keep strict 26-char profile until proven safe         |
| Time-series link       | Map `Part.HistorianTag` to `historian_timeseries.HistorianTag`                                                                  | 1980 linked rows; 180 decoy rows unmatched                                         | Narrow format is validated                            |
| Contextualization      | Run `EquipmentId` and `SystemId` contextualizations                                                                             | 6 Equipment→System and 14 System→Part relationships                                | Keep current exported relationship keys               |
| Hierarchy rendering    | Explore Equipment → Systems → Parts                                                                                             | Useful top-down hierarchy                                                          | If backwards, flip relationship direction/cardinality |
| Ontology-item question | Create Fabric IQ ontology by API and inspect whether DTB can reference it                                                       | Expected: no documented reference today                                            | v2 generates DTB + IQ from same manifest              |
| UI drift               | Compare README click path to actual preview UI                                                                                  | Differences recorded                                                               | Update `SETUP.md`, not importer core                  |
| Decoy behavior         | Confirm `M5_AUX_VIB09.PV` does not bind                                                                                         | 180 orphan rows, no false Part binding                                             | Keep decoy as regression test                         |
| Untagged parts         | Confirm 3 untagged parts still appear as Part instances                                                                         | 14 part instances, 11 with time series                                             | Exporter must allow nullable HistorianTag             |

---

# 17. Implementation phases for OpenClaw + Codex CLI

## Phase 0 — Agent setup

Use OpenClaw as coordinator and Codex CLI as implementation agent. The workflow should be:

```text
OpenClaw:
  owns plan, task decomposition, checkpoints, acceptance criteria

Codex CLI:
  writes code, tests, scripts, docs

Human:
  performs az login/browser auth when needed
  supplies workspace/capacity details
  approves destructive actions
```

Create `AGENTS.md`:

```md
# Agent Rules

Goal: get the Douglas bagmaker EquipmentIQ export running as a Microsoft Fabric Digital Twin Builder work item with complete ontology, mappings, time-series link, and relationships.

Do not implement Fabric task-flow import. It is not the deployment path.

Use public Fabric APIs first. Do not call undocumented/private portal APIs in production code.

Use Playwright only as a fallback to trigger DTB run operations if no documented public run API exists. Do not use Playwright to author the ontology canvas.

Keep all generated definition JSON in runs/<run-id>/definition_parts before sending to Fabric.

Never delete Fabric items unless --allow-delete is explicitly set.

Use delegated user auth for DTB APIs because current DTB create/update/get definition APIs do not support service principals or managed identities.

Validate row counts, time-series link behavior, decoy tag behavior, and relationship counts before marking success.
```

## Phase 1 — Scaffold and local tests

Codex tasks:

```text
1. Create Python package.
2. Implement CLI with Typer.
3. Implement zip reader.
4. Implement schema validator.
5. Implement sanitizer.
6. Implement stable ID generator.
7. Add unit tests for Douglas kit expected counts.
```

CLI:

```bash
python -m eiq_dtb_importer inspect \
  --zip ./samples/dbm-rh-m5-dtb-e2e-kit.zip
```

Expected output:

```text
equipment: 1
systems: 6
parts: 14
historian_tags: 12
historian_timeseries: 2160
ground_truth_bindings: 12

linked_ts_rows_expected: 1980
orphan_ts_rows_expected: 180
orphan_tags: M5_AUX_VIB09.PV
```

## Phase 2 — Fabric client

Implement:

```python
class FabricClient:
    def get(self, path): ...
    def post(self, path, json=None): ...
    def patch(self, path, json=None): ...
    def delete(self, path): ...
    def poll_lro(self, response): ...
```

Requirements:

```text
- Use Retry-After when present
- Handle 429
- Capture x-ms-operation-id
- Capture request IDs on errors
- Scrub tokens from logs
- Save every request/response summary to run log
```

## Phase 3 — Lakehouse provision + upload + load

Commands:

```bash
python -m eiq_dtb_importer lakehouse ensure \
  --config config.douglas.yaml

python -m eiq_dtb_importer lakehouse upload \
  --config config.douglas.yaml

python -m eiq_dtb_importer lakehouse load \
  --config config.douglas.yaml
```

Acceptance:

```text
All six tables are loaded as managed Delta tables.
Pre-DTB SQL/count validation passes.
```

## Phase 4 — DTB baseline export

Use your existing manually-built item if possible:

```bash
python -m eiq_dtb_importer dtb export-definition \
  --workspace-id <workspaceId> \
  --dtb-id <existingAltouraDigitalTwinTestId> \
  --out templates/baseline_dtb_export
```

Purpose:

```text
- Confirm current enum casing: NonTimeSeries vs non-timeseries
- Confirm BaseEntityTypeId values
- Confirm .platform format
- Confirm actual definition shape in your tenant
```

Do not skip this. It is a preview product; this one export de-risks the compiler.

## Phase 5 — Generate DTB definition

Command:

```bash
python -m eiq_dtb_importer dtb compile \
  --config config.douglas.yaml \
  --out runs/<run-id>/dtb_definition
```

Acceptance:

```text
- definition.json generated
- EntityTypes generated
- Relationship files generated
- MappingOperations generated
- ContextualizationOperations generated
- All payloads serializable as InlineBase64
- All IDs deterministic
- Name map emitted
```

## Phase 6 — Create/update DTB

Command:

```bash
python -m eiq_dtb_importer dtb apply \
  --config config.douglas.yaml \
  --definition runs/<run-id>/dtb_definition \
  --mode reuse_or_create
```

Acceptance:

```text
- DouglasBagmakerDTB exists
- DTB getDefinition roundtrip returns expected parts
- Default on-demand child flow exists or is discoverable
```

## Phase 7 — Run operations

Command:

```bash
python -m eiq_dtb_importer dtb run-operations \
  --config config.douglas.yaml \
  --strategy api_then_playwright
```

Execution sequence:

```text
1. Run static mappings.
2. Wait until completed.
3. Run time-series mapping.
4. Wait until completed.
5. Run relationship contextualizations.
6. Wait until completed.
```

If API runner is unavailable:

```bash
python -m playwright install chromium

python -m eiq_dtb_importer dtb run-operations \
  --config config.douglas.yaml \
  --strategy playwright \
  --interactive-browser true
```

The Playwright fallback should save:

```text
runs/<run-id>/screenshots/
runs/<run-id>/operation_status.json
runs/<run-id>/ui_drift_notes.md
```

## Phase 8 — Validate

Command:

```bash
python -m eiq_dtb_importer validate \
  --config config.douglas.yaml
```

Validation gates:

```text
Lakehouse tables loaded
DTB definition present
Static mappings completed
Time-series mapping completed
Contextualizations completed
DTB domain views queryable
Expected row counts pass
Decoy tag remains unmatched
Jaw Assembly time series visible
```

## Phase 9 — Fabric IQ mirror

Command:

```bash
python -m eiq_dtb_importer iq compile \
  --config config.douglas.yaml \
  --out runs/<run-id>/iq_definition

python -m eiq_dtb_importer iq apply \
  --config config.douglas.yaml \
  --definition runs/<run-id>/iq_definition
```

Then:

```bash
python -m eiq_dtb_importer iq test-dtb-reference \
  --config config.douglas.yaml
```

Acceptance:

```text
- IQ ontology item exists
- Same entity/relationship/data-binding model exists in IQ
- Report says whether DTB can reference it
```

Expected v1 outcome:

```text
DTB cannot directly reference API-created IQ Ontology through documented DTB definition.
Generate both from the same EquipmentIQ manifest instead.
```

---

# 18. Azure-hosted service design

After local success, containerize the importer.

## Azure resources

```text
Resource group: rg-equipmentiq-fabric-dtb-dev
Container registry: acrEquipmentIQFabric
Container Apps environment: cae-equipmentiq-dev
Container Apps job: job-equipmentiq-dtb-importer
Key Vault: kv-equipmentiq-fabric-dev
Log Analytics workspace: law-equipmentiq-fabric-dev
Storage account: staging bundle uploads / run artifacts
Managed identity: mi-equipmentiq-fabric-importer
```

## Container job

Docker image includes:

```text
Python runtime
Azure CLI
Playwright Chromium
Importer package
```

Run modes:

```text
local-auth:
  operator logs in locally
  runs importer from WSL

hybrid-auth:
  Azure job uses managed identity for lakehouse/IQ
  DTB step uses delegated token supplied at runtime

future-headless:
  managed identity for all steps once DTB supports it
```

## Deployment command

```bash
az containerapp job start \
  --name job-equipmentiq-dtb-importer \
  --resource-group rg-equipmentiq-fabric-dtb-dev \
  --env-vars \
    CONFIG_BLOB_URI=<...> \
    RUN_MODE=apply_and_validate
```

Do not overbuild this until local v1 is stable. The main blocker to full production automation is DTB’s current lack of service principal / managed identity support.

---

# 19. What EquipmentIQ should export next

Your current kit is enough for v1. To make the API importer durable, add this file to future exports:

```text
equipmentiq_manifest.json
```

Proposed manifest:

```json
{
  "exporter": {
    "name": "EquipmentIQ",
    "version": "0.1.0",
    "source": "Douglas DBM RH M5",
    "generatedAt": "2026-06-10T07:29:00Z"
  },
  "target": {
    "fabric": {
      "dtbName": "DouglasBagmakerDTB",
      "lakehouseName": "DouglasBagmakerRaw"
    }
  },
  "entities": [
    {
      "name": "Equipment",
      "table": "equipment_dtb",
      "id": ["EquipmentUID"],
      "displayName": "DisplayName",
      "properties": ["EquipmentUID", "EquipmentId", "EquipmentJoinKey", "DisplayName", "Manufacturer", "ModelNumber"]
    },
    {
      "name": "System",
      "table": "systems_dtb",
      "id": ["SystemUID"],
      "displayName": "DisplayName",
      "properties": ["SystemUID", "SystemId", "SystemJoinKey", "DisplayName", "EquipmentId", "EquipmentJoinKey"]
    },
    {
      "name": "Part",
      "table": "parts_dtb",
      "id": ["PartUID"],
      "displayName": "DisplayName",
      "properties": ["PartUID", "PartId", "PartJoinKey", "DisplayName", "Category", "SystemId", "SystemJoinKey", "HistorianTag"],
      "timeSeries": {
        "table": "historian_timeseries_dtb",
        "timestampColumn": "PreciseTimestamp",
        "valueColumn": "Value",
        "link": {
          "entityProperty": "HistorianTag",
          "timeseriesColumn": "HistorianTag"
        }
      }
    }
  ],
  "relationships": [
    {
      "name": "isPartOf",
      "sourceEntity": "System",
      "targetEntity": "Equipment",
      "sourceProperty": "EquipmentJoinKey",
      "targetProperty": "EquipmentJoinKey",
      "cardinality": "ManyToOne"
    },
    {
      "name": "isPartOf",
      "sourceEntity": "Part",
      "targetEntity": "System",
      "sourceProperty": "SystemJoinKey",
      "targetProperty": "SystemJoinKey",
      "cardinality": "ManyToOne"
    }
  ],
  "expected": {
    "equipmentRows": 1,
    "systemRows": 6,
    "partRows": 14,
    "timeSeriesRows": 2160,
    "linkedTimeSeriesRows": 1980,
    "unmatchedTimeSeriesRows": 180,
    "unmatchedTags": ["M5_AUX_VIB09.PV"]
  }
}
```

This manifest removes guesswork from the importer and becomes the stable contract between EquipmentIQ and Fabric.

---

# 20. OpenClaw handoff prompt

Paste this into OpenClaw as the execution brief:

```text
You are coordinating Codex CLI to build an API-first importer that takes the EquipmentIQ Douglas bagmaker zip and deploys it into Microsoft Fabric as a Digital Twin Builder work item.

Ultimate goal:
Get the uploaded Douglas bagmaker EquipmentIQ export running in Fabric as a Digital Twin Builder item named DouglasBagmakerDTB, with a complete ontology: Equipment, System, Part, static mappings, Part time-series mapping through HistorianTag, and System→Equipment / Part→System JoinKey contextualization.

Do not use Fabric task-flow import. Task flows are not the deployment mechanism.

Implementation repo:
equipmentiq-fabric-dtb

Build in Python. Use Typer CLI, pydantic, pandas, httpx, tenacity, azure-identity, azure-storage-file-datalake, xxhash, pytest, and Playwright.

Key API facts:
- Lakehouse is created through Fabric REST API.
- CSVs are uploaded to OneLake Files using ADLS-compatible OneLake APIs.
- CSVs are loaded to Delta tables using Lakehouse Load Table API.
- Digital Twin Builder item is created/updated through Fabric DigitalTwinBuilder REST APIs.
- DTB definition parts are base64 InlineBase64 payloads.
- DTB create/update/get definition require delegated user auth today; do not assume service principal works for DTB.
- Fabric IQ Ontology can be created/updated as a mirror, but it is not the v1 DTB runtime source of truth unless proven.

Data facts:
Zip contains equipment.csv, systems.csv, parts.csv, historian_tags.csv, historian_timeseries.csv, ground_truth_bindings.csv.
Expected raw counts:
equipment 1
systems 6
parts 14
historian_tags 12
historian_timeseries 2160
ground_truth_bindings 12

Time-series behavior:
historian_timeseries has 12 tags × 180 timestamps.
parts.csv has 11 tagged parts and 3 untagged parts.
M5_AUX_VIB09.PV is a decoy with no ontology target.
Expected linked time-series rows are 1980.
Expected unmatched rows are 180.
Do not force-bind the decoy.

Ontology/source shape for active DTB compiler:
Equipment:
  table equipment_dtb
  unique ID EquipmentUID
  properties EquipmentUID, EquipmentId, EquipmentJoinKey, DisplayName, Manufacturer, ModelNumber

System:
  table systems_dtb
  unique ID SystemUID
  properties SystemUID, SystemId, SystemJoinKey, DisplayName, EquipmentId, EquipmentJoinKey

Part:
  table parts_dtb
  unique ID PartUID
  properties PartUID, PartId, PartJoinKey, DisplayName, Category, SystemId, SystemJoinKey, HistorianTag
  time series from historian_timeseries_dtb
  timestamp PreciseTimestamp
  value Value
  link Part.HistorianTag = historian_timeseries.HistorianTag

Relationships:
System isPartOf Equipment:
  System.EquipmentJoinKey = Equipment.EquipmentJoinKey
  ManyToOne

Part isPartOf System:
  Part.SystemJoinKey = System.SystemJoinKey
  ManyToOne

Implementation phases:
1. Scaffold repo and AGENTS.md.
2. Implement zip inspection and schema validation.
3. Implement strict sanitizer: letters/numbers/underscore, starts with letter, max 26 for entity/property names, stable hash on collision.
4. Implement deterministic BigInt IDs and UUIDv5 operation IDs.
5. Implement FabricClient with LRO polling, Retry-After, 429 handling, request ID logging.
6. Implement Lakehouse ensure/upload/load/list tables.
7. Implement DTB baseline export from an existing working DTB item if supplied.
8. Implement DTB definition compiler from EquipmentIQ model.
9. Implement DTB create/update/getDefinition roundtrip.
10. Implement operation runner: public API if documented; otherwise Playwright fallback only to trigger Run and observe status.
11. Implement validator for raw lakehouse counts, HistorianTag join, decoy behavior, DTB dom views, relationships, and Jaw Assembly chart visibility.
12. Implement optional Fabric IQ ontology mirror and test whether DTB can reference it.
13. Write SETUP.md with exact commands, required user inputs, and UI drift notes.

Do not call undocumented/private portal APIs in production code. You may inspect network traffic only to discover whether a documented public endpoint exists. If not, use Playwright fallback.

Acceptance criteria:
- DouglasBagmakerRaw lakehouse exists with six loaded Delta tables.
- DouglasBagmakerDTB exists as a Digital Twin Builder item.
- DTB definition includes Equipment, System, Part, mappings, time-series mapping, and contextualization operations.
- Static mappings complete.
- Part time-series mapping completes.
- Equipment/System and System/Part contextualizations complete.
- dom.Equipment_property has 1 row.
- dom.System_property has 6 rows.
- dom.Part_property has 14 rows.
- dom.Part_timeseries has 1980 linked rows.
- M5_AUX_VIB09.PV remains unmatched with 180 rows.
- dom.relationships contains 20 total relationship instances, or 6 and 14 by relationship type.
- Explorer can find Jaw Assembly and show its Value series.
- Report generated under runs/<run-id>/validation_report.json.
```

---

# 21. Inputs still needed before execution

You need to provide these to OpenClaw/Codex:

```text
1. Fabric workspace ID or workspace name
2. Confirmation whether to use current workspace or create a dedicated workspace
3. Whether DTB preview is enabled in tenant settings
4. Whether Autoscale Billing for Spark is disabled
5. Whether to reuse AltouraDigitalTwinTest as calibration export source
6. Whether final DTB item should be DouglasBagmakerDTB or another name
7. Whether Playwright fallback is acceptable for triggering operation runs if no public run API is found
```

The most important implementation choice: **build the v1 importer around DTB public definitions, not Fabric task flows and not Fabric IQ as the runtime source.** Fabric IQ should be generated in parallel to answer the v2 architecture question.

---

# 22. 2026-06-14 DTB EntityType ID compiler correction

Fresh Lawrence/F4 ladder evidence isolated the latest full-Douglas import failure to the EntityType ID band, not the Douglas table load, source schema omission, entity display name, EquipmentIQ property names, or generated property IDs. Public docs only say EntityType IDs are BigInt and >10,000, but Fabric accepted `100000000000001`/`200000000000001` and rejected `300000000000001`/`500000000000001`/`580786628437170`.

Implementation decision: keep DTB EntityType IDs in a conservative observed-safe band until Microsoft publishes the real allocator/range. The active compatibility profile is `LAWRENCE_F4_ENTITYTYPE_IMPORT_PROFILE` in `src/eiq_dtb_importer/dtb_compat.py`; generated EntityType IDs now map deterministic raw hashes into `100000000000001..199999999999999`. This is a Fabric compatibility patch, not a source-bundle correction.

Next gates:

1. Run local pytest for compiler and hardening tests.
2. Compile a fresh Douglas definition and inspect generated IDs/artifact.
3. With explicit external-mutation approval, deploy one fresh DTB item in Lawrence using the corrected profile.
4. If EntityType import passes, continue to mapping/contextualization and flow/run validation; if it fails, capture operation ID and update `F008` with the new narrowed boundary.

[1]: https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/digital-twin-builder-definition "Digital twin builder item definition - Microsoft Fabric REST APIs | Microsoft Learn"
[2]: https://learn.microsoft.com/en-us/fabric/real-time-intelligence/digital-twin-builder/tutorial-2-add-entities-map-data "Digital Twin Builder (Preview) Tutorial Part 2: Add Entity Types and Map Data - Microsoft Fabric | Microsoft Learn"
[3]: https://learn.microsoft.com/en-us/fabric/real-time-intelligence/digital-twin-builder/tutorial-0-introduction "Digital Twin Builder (Preview) Tutorial Introduction - Microsoft Fabric | Microsoft Learn"
[4]: https://learn.microsoft.com/en-us/fabric/real-time-intelligence/digital-twin-builder/tutorial-4-explore-ontology "Digital Twin Builder (Preview) Tutorial Part 4: Explore Your Ontology - Microsoft Fabric | Microsoft Learn"
[5]: https://learn.microsoft.com/en-us/rest/api/fabric/digitaltwinbuilder/items/create-digital-twin-builder "Items - Create Digital Twin Builder - REST API (DigitalTwinBuilder) | Microsoft Learn"
[6]: https://learn.microsoft.com/en-us/rest/api/fabric/ontology/items/create-ontology "Items - Create Ontology - REST API (Ontology) | Microsoft Learn"
[7]: https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/ontology-definition "Ontology item definition - Microsoft Fabric REST APIs | Microsoft Learn"
[8]: https://learn.microsoft.com/en-us/fabric/onelake/onelake-access-api "How do I connect to OneLake? - Microsoft Fabric | Microsoft Learn"
[9]: https://learn.microsoft.com/en-us/fabric/real-time-intelligence/digital-twin-builder/tutorial-1-set-up-resources "Digital Twin Builder (Preview) Tutorial Part 1: Set Up Resources - Microsoft Fabric | Microsoft Learn"
[10]: https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-api "Manage a lakehouse with the REST API - Microsoft Fabric | Microsoft Learn"
[11]: https://learn.microsoft.com/en-us/rest/api/fabric/digitaltwinbuilder/items/get-digital-twin-builder-definition "Items - Get Digital Twin Builder Definition - REST API (DigitalTwinBuilder) | Microsoft Learn"
[12]: https://learn.microsoft.com/en-us/fabric/real-time-intelligence/digital-twin-builder/concept-flows "Digital Twin Builder (Preview) Flow - Microsoft Fabric | Microsoft Learn"
[13]: https://learn.microsoft.com/en-us/rest/api/fabric/digitaltwinbuilder/items/update-digital-twin-builder-definition "Items - Update Digital Twin Builder Definition - REST API (DigitalTwinBuilder) | Microsoft Learn"
