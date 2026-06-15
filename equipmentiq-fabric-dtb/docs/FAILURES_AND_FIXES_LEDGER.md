# Failures and fixes ledger

Purpose: record every straight-up, non-transient failure and its actual fix path. This is not a patch graveyard. If the failure is deterministic or semantic, address the core contract issue before adding more compatibility code.

## Classification rules

- **Transient / capacity-admission shaped**: capacity throttling, HTTP 429/430, `TooManyRequestsForCapacity`, slow Spark admission, temporary LRO wait, poll timeout where a later Fabric payload/UI shows success, or generic queued-job failure while capacity is under pressure. Mitigate with bounded retry/backoff, serialize work, capture capacity ID/SKU and operation/request/root-activity IDs, and label the entry as capacity/admission unless semantic evidence proves otherwise.
- **Non-transient / straight-up failure**: deterministic Fabric import rejection, schema mismatch, invalid generated definition, invalid source data, wrong API contract, wrong item linkage. Must get a root-cause record and a fix plan. Do not classify a Fabric preview/control-plane error as straight-up semantic until capacity/admission and metadata lag are ruled out with evidence.
- **Bundle defect**: source bundle should change. Report exact file/row/column/key and the correction.
- **Compiler/Fabric compatibility defect**: bundle is valid, but generated Fabric definition shape is wrong or unproven. Fix canonicalizer/profile/tests, not the bundle.
- **Operational blocker**: capacity/auth/permissions/item lifecycle. Record workaround separately from the canonical service path.

## Non-transient failures

### F001 — Full Douglas DTB import fails at EntityType boundary

- **Status:** open
- **Observed:** 2026-06-12
- **Error:** `ALMOperationImportFailed`; `Importing artifact definition for EntityType has failed.`
- **Operation IDs observed:**
  - `pbipwestus2tp1;DO-71d37903-c14c-408a-bcd5-a3be6cfa2aef`
  - `pbipwestus2tp0;DO-cf73f6ae-d958-4b26-95ce-18055c6c0231`
  - `pbipwestus2tp1;DO-de55429d-a75e-4535-96ce-dc3e409ecf9c`
  - `pbipwestus2tp1;DO-9d052333-bbaa-4f35-9527-f9c4d0d0e391`
- **Known not root cause:** raw bundle/table validity. Read-only OneLake validation passed all six tables and expected link/orphan counts.
- **Evidence:**
  - `runs/read-only-validate-onelake-20260612T063058Z/validation.json`
  - `runs/dtb-generated-entity-ladder-20260612T064809Z/entity_ladder.json`
- **Current narrowed boundary:** generated Equipment-only variant fails before System/Part/mapping/relationship/contextualization.
- **Core issue to solve:** identify the actual Fabric EntityType public-import contract for generated entity names/IDs/properties and implement an import-safe canonicalizer/profile.
- **Do not do:** blindly add more generated variants or patch around the symptom without a profile/test proving the contract.
- **Next fix path:** run fresh disposable-item matrix per variant, or export a tiny UI-authored DTB with matching generated field names and compare accepted EntityType JSON. Reused-item sequential update results are not sufficient because Fabric may guard existing ontology internals.

### F002 — Sequential EntityType compatibility matrix failed after control pass

- **Status:** evidence captured; diagnostic design corrected
- **Observed:** 2026-06-12
- **Run:** `dawn-forest` / approval `ea665086-ab29-4ffa-b10a-4c26da227b3b`
- **Result:** control docs-shaped EntityType passed, then every subsequent update variant failed.
- **Representative errors:**
  - `pbipwestus2tp0;DO-7de4bc58-d423-4dc8-a785-ac5c59badf6f`
  - `pbipwestus2tp1;DO-e46ab213-d88f-4472-9f22-9e6e60806d17`
  - `pbipwestus2tp0;DO-5eb7676f-eace-4fa4-83f7-b68bc1e44d30`
  - `pbipwestus2tp0;DO-4ced5934-843f-4a0f-b3de-29fb2ed41a10`
  - `pbipwestus2tp0;DO-95b4e08e-cb11-4b5a-b793-7e938b551c95`
  - `pbipwestus2tp1;DO-d5a2c4e4-fa7c-493b-b51a-e3b479fa72ae`
- **Core lesson:** sequential updates against the same DTB are not independent import tests. Failures can represent unsupported rename/remove/replace semantics, not just invalid EntityType shape.
- **Fix:** future compatibility matrix must use fresh disposable DTB item names per variant, or a cleanup-approved scratch workspace/item lifecycle. Mark reused-item matrices as update-semantics evidence only.

### F003 — DTB deployment without DigitalTwinBuilderFlow linkage is incomplete

- **Status:** on-demand linkage proven for smoke DTB; full Douglas operation set still pending compiler import fix
- **Observed:** 2026-06-12 owner requirement
- **Issue:** DTB definition can contain ontology/mapping parts, but internal mapped operations are not proven connected/runnable until a `DigitalTwinBuilderFlow` item links to the parent `DigitalTwinBuilderId` and assigns `OperationIds`.
- **Core fix:** final service must compile/deploy/roundtrip `DigitalTwinBuilderFlow` definitions after DTB definition import.
- **Implementation scaffold:** `src/eiq_dtb_importer/dtb_flow.py`
- **Local proof artifact:** `runs/dtb-flow-linkage-local-static/FLOW_LINKAGE_LOCAL_PROOF.md`
- **Completion gate:** Fabric `getDefinition` for flow must return expected `DigitalTwinBuilderId`, `OperationIds`, and `IsOnDemand`.
- **On-demand proof:** `runs/dtb-on-demand-flow-20260612T073243Z/deploy_on_demand_flow.json`
  - Flow name: `DouglasBagmakerDTB_OnDemandFlow`
  - Flow ID: `b3db5ae6-cce2-49f6-b9c8-7ed4da3a51a3`
  - `partCountSubmitted: 2`, `partCountExported: 2`
  - `digitalTwinBuilderItemReference.itemId: ee4825ce-d6bd-4f87-a654-a5f4f025b1c9`

### F004 — DigitalTwinBuilderFlow live export failed after local definition compile

- **Status:** scheduled-flow export issue remains open; on-demand flow path succeeded separately
- **Observed:** 2026-06-12
- **Run:** `swift-mist` / approval `b65769c8-8d4f-464a-a4ec-ef27f3f0d40e`
- **Context:** live proof attempted to restore known-good DTB mapping definition, compile a `DigitalTwinBuilderFlow`, deploy it, then roundtrip via `getDefinition`.
- **Succeeded before failure:** `DouglasBagmakerDTB` known-good one-entity/one-mapping definition update passed and exported with `partCountExported: 4`.
- **Local shape proof:** `good-rook` / approval `44e9243b-d904-4900-9c6e-fc33f49e42a9` compiled a two-part flow definition and validated:
  - `DigitalTwinBuilderId: ee4825ce-d6bd-4f87-a654-a5f4f025b1c9`
  - `OperationIds: [ce9d0ef9-d8f6-4391-9e37-8bdb91b1fc16]`
  - `IsOnDemand: false`
- **Failure:** Flow `getDefinition` LRO failed with `ALMOperationExportFailed` and message `Export of the artifact '{0}' threw an exception with this message: {1}`.
- **Follow-up list result:** the flow item exists, so create/update got far enough to materialize the item:
  - Flow ID: `cf7d124f-67b8-48d4-8c2d-3f0c54084278`
  - Display name: `DouglasBagmakerDTB_SmokeMappingFlow`
  - Type: `DigitalTwinBuilderFlow`
- **Narrowed boundary:** Fabric can list the flow item, but cannot export its definition via `getDefinition`.
- **Why this is non-transient:** Fabric returned `isRetriable: false`; failure occurs at artifact export/definition contract boundary, not Spark capacity or network.
- **Core issue to solve:** determine whether the flow item was created but not exportable, whether create/update body shape is wrong, whether `OperationIds` must reference operation IDs already materialized in a specific internal flow context, or whether the flow public API has additional hidden requirements.
- **Do not do:** mark flow linkage complete based only on local JSON shape; live roundtrip is mandatory.
- **Next fix path:** inspect item metadata; test an on-demand flow (`IsOnDemand=true`, empty `OperationIds`) separately in a fresh flow name; compare public docs and any live export from UI-created flow if available. Determine whether the hidden requirement is operation assignment semantics, flow item platform metadata, or unsupported public export for this item state.
- **Tutorial/UI evidence from owner screenshots:** Microsoft tutorial Part 2 creates flows through `Scheduling` -> `Schedule flow` -> `Create flow`, after a mapping operation exists. The flow appears to be an execution/schedule wrapper for mapping operations, not the ontology container. This suggests `DigitalTwinBuilderFlow` definitions may require schedule-context semantics or a UI-created scheduling state even though the public definition doc only shows `DigitalTwinBuilderId`, `OperationIds`, and `IsOnDemand`.
- **Proof-path correction:** owner guidance is to try one-time `Run now` hydration first, not scheduled flow creation. Repeated attempts may be required because current Fabric capacity can fail/admit jobs inconsistently. Capacity/admission run failures should be logged separately from flow-definition/export contract failures.
- **UI Run now evidence:** clicking `Run` on the mapping produced: `This digital twin builder does not have an associated on-demand flow to run.` This confirms the scheduled flow `DouglasBagmakerDTB_SmokeMappingFlow` is not the on-demand flow used by the Run button. Next fix is to create/update an on-demand `DigitalTwinBuilderFlow` with `IsOnDemand=true` and empty `OperationIds` linked to the same `DigitalTwinBuilderId`.
- **On-demand fix result:** creating `DouglasBagmakerDTB_OnDemandFlow` with `IsOnDemand=true` and empty `OperationIds` succeeded and exported. This does not resolve the scheduled flow export issue, but it fixes the missing on-demand association needed by the UI `Run` button.
- **UI proof after fix:** owner clicked `Run` after on-demand flow creation and Fabric showed success/queued. This proves the on-demand flow association is sufficient for the UI one-time run path. Any later failure after queue acceptance should be classified as runtime/capacity/hydration unless operation details prove otherwise.

### F005 — Public job API cannot currently start DTB Flow run even with observed UI job type

- **Status:** open; UI/Playwright fallback required unless Fabric documents/enables public run invocation
- **Observed:** 2026-06-12
- **Run:** `dawn-shell` / approval `cf1294dd-cf1c-4119-bb82-97881860c383`
- **Attempted endpoint:** `POST /workspaces/fff2e022-a257-469d-9b15-acc0d4dc2e14/items/cf7d124f-67b8-48d4-8c2d-3f0c54084278/jobs/DefaultJob/instances`
- **Flow item:** `DouglasBagmakerDTB_SmokeMappingFlow` / `cf7d124f-67b8-48d4-8c2d-3f0c54084278`
- **Error:** `HTTP 400`, `InvalidJobType`, `The requested job type is invalid`, `isRetriable: false`, request ID `ee3f8703-73ed-414f-82d2-208540cf4424`.
- **Follow-up on-demand flow attempt:** after creating valid on-demand flow `DouglasBagmakerDTB_OnDemandFlow` / `b3db5ae6-cce2-49f6-b9c8-7ed4da3a51a3`, `DefaultJob` still failed with `InvalidJobType`, request ID `0b87f206-3fc2-4de4-97ed-4162bd438ed7`, artifact `runs/dtb-run-now-api-ondemand-20260612T073819Z/ondemand_flow_defaultjob_run.json`.
- **Why this is non-transient:** Fabric explicitly rejected the job type with `isRetriable: false`.
- **Docs/spec result:** public `digitalTwinBuilder` and `digitalTwinBuilderFlow` item specs expose create/list/get/update/delete/getDefinition/updateDefinition but do not document an on-demand mapping/contextualization run job type.
- **Core issue to solve:** identify the valid job type/body for one-time DTB/Flow operation execution, or confirm no public API exists and keep Playwright/UI fallback for Gate 06.
- **Discovered valid UI job type:** querying the UI-created/manual run job instance `c12183bb-3860-45d8-a180-2b0ab026c360` showed `jobType: ExecuteOperations` and `invokeType: Manual`.
- **Evidence-backed retry:** `POST /workspaces/fff2e022-a257-469d-9b15-acc0d4dc2e14/items/b3db5ae6-cce2-49f6-b9c8-7ed4da3a51a3/jobs/ExecuteOperations/instances` failed with `InvalidJobType`, request ID `2691dc70-3e42-451d-bb3e-7709115cdb91`, artifact `runs/dtb-run-now-api-executeoperations-20260612T113223Z/ondemand_flow_executeoperations_run.json`.
- **2026-06-15 retry on fresh corrected NoSchema parent-first item:** fresh DTB `DouglasBagmakerDTB_NodeDemo_ParentFirst_NoSchema_20260615_1556` / `a15b7aa0-e65b-4a75-9d01-08429b271d8d` and on-demand flow `b2fcdefb-94c7-4445-9bd0-3f6289963bea` deployed/exported successfully. `POST /workspaces/e5532483-0114-4ac2-8d3f-8105c7eb5543/items/b2fcdefb-94c7-4445-9bd0-3f6289963bea/jobs/ExecuteOperations/instances` still failed HTTP 400 `InvalidJobType`, request ID `a73eb06a-d0e2-4424-8bdd-04a81d892209`, artifact `runs/node-demo-parentfirst-noschema-20260615T1556AEST/cleanup_old_and_executeoperations.json`.
- **2026-06-15 explicit-operation-flow retry:** created/exported dedicated flow `Run_Equipment_equipment_API_20260615_1609` / `0458f74e-f125-41d5-a70b-ccedea04963c` with `OperationIds=[78bd6721-8881-57b0-8fce-d48be0c0fe8e]` for fresh DTB `a15b7aa0-e65b-4a75-9d01-08429b271d8d`; roundtrip succeeded (`2/2` parts), but `POST /items/0458f74e-f125-41d5-a70b-ccedea04963c/jobs/ExecuteOperations/instances` still failed HTTP 400 `InvalidJobType`, request ID `38c83098-15e2-4feb-9da6-ceb4e826574e`, artifact `runs/node-demo-parentfirst-noschema-20260615T1556AEST/api_run_equipment_executeoperations.json`.
- **Updated interpretation:** public docs/logs may expose `ExecuteOperations` as an internal/manual UI job type, but the generic public item job endpoint does not accept it for API-created DTB Flow items in this tenant/item state. Until proven otherwise with a UI-created/exported flow or additional required execution payload, the reliable execution path remains Fabric UI Run against an associated on-demand flow.
- **Interpretation:** Fabric job-instance history exposes internal/UI job type `ExecuteOperations`, but the public Run On Demand Item Job endpoint rejects that same job type for this item. Either the public API blocks this DTB job type, requires hidden execution data/headers, or the UI uses an internal route not documented by the public job scheduler.
- **Next fix path:** stop public API run attempts without new evidence. Use UI/Playwright fallback for Gate 06 and raise this with Fabric engineering as a missing/blocked API surface.

### F006 — DTB on-demand run queues but fails with unknown root server error

- **Status:** open; runtime/backend failure boundary after queue acceptance
- **Observed:** 2026-06-12
- **UI path:** `DouglasBagmakerDTB` -> `Equipment1` -> `Scheduling` -> `Run`
- **Prerequisite fixed:** on-demand flow `DouglasBagmakerDTB_OnDemandFlow` / `b3db5ae6-cce2-49f6-b9c8-7ed4da3a51a3` exists and is linked to `DouglasBagmakerDTB` / `ee4825ce-d6bd-4f87-a654-a5f4f025b1c9`.
- **Queue result:** UI accepted/queued the flow successfully after on-demand flow creation.
- **Failure:** repeated on-demand runs failed in `Operation details` with `[Server Error] Operation failed due to an unknown error.`
- **Root Activity Id:** `11c8737e-3687-487c-8e72-2cfc51998daf`
- **Run history evidence:** at least three failed on-demand attempts visible around `2026-06-12 17:39`, `17:40`, and `17:42` AEST.
- **Later details panel evidence:** Job details showed:
  - Activity name: `DouglasBagmakerDTB_OnDemandFlow`
  - Job ID: `c12183bb-3860-45d8-a180-2b0ab026c360`
  - Status: `Failed`
  - Start time: `6/12/26, 7:44 AM`
  - End time: `6/12/26, 7:44 AM`
  - Duration: less than 1 minute
  - Capacity ID: `cd025fa9-4d1d-4534-8962-c0030880aee3`
  - Error code: `OperationFailure`
  - Error message: `Multiple operations failed (Mapping, Ontology). Select the activity name to view details.`
- **Job API evidence:** `GET /workspaces/.../items/b3db5ae6-cce2-49f6-b9c8-7ed4da3a51a3/jobs/instances/c12183bb-3860-45d8-a180-2b0ab026c360` returned:
  - `jobType: ExecuteOperations`
  - `invokeType: Manual`
  - `status: Failed`
  - `requestId: 4dd1c349-116e-4ebc-9932-218b22f8f6cc`
  - `rootActivityId: 92787f26-72c9-3d4b-75eb-4099d43eb94d`
  - `startTimeUtc: 2026-06-12T07:44:16.2679485`
  - `endTimeUtc: 2026-06-12T07:44:39.831457`
- **Timestamp interpretation:** start/end in the past is probably not the root cause; it appears to be the historical run timestamp, likely UTC/Fabric-local display. The immediate same-minute start/end indicates fast failure.
- **Classification:** not a DTB definition import failure and not missing flow linkage. This is a runtime/hydration/backend failure after successful queue acceptance. It may still be capacity/admission related, but Fabric does not expose enough detail in the UI error to prove that.
- **Microsoft troubleshooting doc implication:** DTB preview troubleshooting says Monitor hub has two relevant job layers: `DigitalTwinBuilderFlow` jobs and associated Lakehouse/Spark item jobs. Lakehouse item jobs can show `Succeeded` even when the DTB flow fails, because operation errors are written to logs that the DTB flow consumes. Therefore the top-level Fabric job API failure is insufficient. The deterministic diagnostic is the DTB **Manage operations** tab: open the failed operation, inspect **Runs**, select the failed status, and capture operation-level error text plus Monitor **Job instance ID**. If the failure message is empty, Microsoft explicitly recommends a support ticket with the job instance ID.
- **New schema-binding hypothesis:** Corrected OneLake Delta API probing shows both Altoura and Douglas expose logical `schema_name: "dbo"`, but storage paths differ. Altoura `GettingStartedRawData` stores `assetdata` at `Tables/dbo/assetdata`; Douglas `DouglasBagmakerRaw` exposes `schema_name: "dbo"` while storage locations are `Tables/equipment`, `Tables/systems`, etc. Therefore `SourceSchema: "dbo"` is not automatically wrong for Douglas, but DTB runtime may be sensitive to this logical/physical schema split. This is now a primary root-cause candidate alongside backend regression/capacity.
- **Core issue to solve:** retrieve per-activity Mapping/Ontology details if available, correlate root activity/job IDs with Fabric backend/support, and determine whether failure is capacity/admission, mapping execution, source table access, ontology materialization, or DTB runtime defect.
- **Required next evidence:** For both `DouglasBagmakerDTB_OnDemandFlow` and calibration `AltouraDigitalTwinTest` / `Equipment_assetdata`, capture failed operation name, operation Runs-tab error, flow/job instance ID, root activity/request IDs when available, and whether associated Lakehouse/Spark jobs show `Succeeded` while the DTB flow fails.
- **Do not do:** keep clicking retry indefinitely or classify as bundle/compiler failure without a semantic error.
- **Next fix path:** ask owner to open `Last run details` if it exposes more information; otherwise preserve root activity ID for Fabric engineering and continue with API/export inspection where possible.

### F007 — Definition-only rename/rebuild from Equipment1 to DouglasBagmaker rejected at EntityType import

- **Status:** open; API rebuild blocked by Fabric EntityType import/update semantics
- **Observed:** 2026-06-13
- **Owner intent:** stop troubleshooting stale UI state; delete/rebuild `Equipment1` as `DouglasBagmaker` using no-space naming convention, Equipment base type, no `SourceSchema` for Douglas tables.
- **Run:** `runs/douglasbagmaker-definition-resume-20260612T232736Z/`
- **Attempted payload:** one replacement `updateDefinition` with:
  - EntityType `Name: DouglasBagmaker`
  - `BaseEntityTypeId: 2`
  - generated entity id `580786628437170`
  - mapping `DouglasBagmaker_equipment`
  - source table `equipment`
  - no `SourceSchema`
- **Error:** `ALMOperationImportFailed`; `Importing artifact definition for EntityType has failed.`
- **Operation ID:** `pbipwestus2tp0;DO-3686ba12-ec17-445b-93a4-d35456c156c6`
- **Why not proven transient:** Fabric returned `isRetriable: false` before visible mapping/Spark execution; surface failure is at artifact import contract boundary.
- **Related evidence:** compatibility matrix `runs/dtb-entity-compat-matrix-20260612T065205Z/entity_compat_matrix.json` showed only the docs-shaped `Equipment1`/doc-props control imported; variants changing entity name/id/properties failed at the same EntityType import boundary. However, API import has succeeded before for docs-shaped one-entity/one-mapping, so this must not be interpreted as “API path impossible.”
- **Revised interpretation after owner correction:** likely a mixed Fabric preview/capacity/control-plane condition. Same-item EntityType rename/replacement via `updateDefinition` is unproven and currently rejected, but current capacity stress may be contributing to misleading import/runtime failures.
- **Core fix path:** first stabilize capacity/job-level bursting or scale SKU, then retry a bounded known-good/API import path. If rename/rebuild still fails after capacity is clean, use UI-supported deactivate/delete/recreate semantics or create a fresh target DTB item with the desired ontology from scratch and prove the import contract there.
- **Capacity relation:** do not classify this as independent of capacity until retested after bursting/SKU remediation. Spark 430 failures are definitely capacity; EntityType import failure may be control-plane/import semantics or capacity-adjacent preview instability.

### F008 — Clean Lawrence/F4 full Douglas DTB create still rejected at EntityType import

- **Status:** resolved for create/import by EntityType ID compatibility profile; next open gate is operation execution/domain-layer validation
- **Observed:** 2026-06-13
- **Run/artifact:** `runs/lawrence-clean-deploy-dtb-20260613T082142Z/FAILURE.json`
- **Target:** workspace `Lawrence` / `e5532483-0114-4ac2-8d3f-8105c7eb5543`; capacity `min` F4 / `32daf203-ebe9-4529-b6c3-576754392a6f`; lakehouse `DouglasBagmakerRaw` / `08264846-3d7e-481e-9758-21ab9993c4b8`
- **Preconditions passed:** clean lakehouse created, six tables loaded serially one at a time, Delta-log-aware validation `PASS`, generated DTB payload compiled with 13 parts, mappings target the new workspace/lakehouse, and `SourceSchema` is omitted.
- **Error:** `ALMOperationImportFailed`; `Importing artifact definition for EntityType has failed.`
- **Operation ID:** `pbipwestus2tp0;DO-85075167-d54c-4f8a-b8bd-3ba8784c1142`
- **Fabric payload:** `status: Failed`, `isRetriable: false`, created `2026-06-13T08:21:42Z`, last updated `2026-06-13T08:22:15Z`.
- **Interpretation:** table data, Lakehouse load, `SourceSchema`, and old/stale DTB item state are no longer primary explanations. This now points at the generated EntityType definition shape/IDs/properties, a Fabric preview public-import contract gap, or a capacity-adjacent control-plane/importer limitation that is not surfaced as capacity. Do not churn mappings/source tables in response to this error.
- **Next fix path:** inspect whether the failed create left a partial DTB item; then run a bounded fresh-item EntityType import ladder in the clean Lawrence workspace, starting from a docs-shaped/calibration-shaped one-entity control known to import, and add fields/name/IDs incrementally until the failing contract boundary is proven. Avoid old workspace repair scripts and avoid deletes unless explicitly approved.
- **Partial-item check:** clean. Read-only list after failed full create returned `{"count": 0, "items": []}`; no partial `DouglasBagmakerDTB` item was left behind in Lawrence.
- **Ladder pass/fail evidence so far:**
  - PASS `00_control_docs_equipment1_docprops`: docs/calibration EntityType ID `139950578358348`, name `Equipment1`, docs props; DTB `EntityLadder00ControlDocs` / `ba325879-3b95-46fd-b611-499940c84e66`; artifact `runs/lawrence-entity-ladder-00-control-20260613T082555Z/`.
  - PASS `01_docs_id_equipment_name_docprops`: same ID/properties, name changed to `Equipment`; DTB `EntityLadder01EquipmentName` / `30563dad-fd63-45c6-81b4-393840ad22f5`; artifact `runs/lawrence-entity-ladder-01-name-equipment-20260613T082744Z/`.
  - FAIL `02_generated_id_equipment1_docprops`: only EntityType ID changed to generated `580786628437170`; non-retriable EntityType import failure, operation `pbipwestus2tp0;DO-1c3e6e34-5b24-40fd-9a76-6a608c231758`; artifact `runs/lawrence-entity-ladder-02-generated-id-20260613T082933Z/FAILURE.json`.
  - PASS `03_doc_id_equipment1_generated_prop_names`: calibration EntityType ID with EquipmentIQ property names using doc-style property IDs; DTB `EntityLadder03GeneratedPropNames` / `6ae76d55-b496-41ae-a67e-157ae97cdcdd`.
  - PASS `04_doc_id_equipment1_generated_prop_ids`: calibration EntityType ID with EquipmentIQ property names and generated property IDs; DTB `EntityLadder04GeneratedPropIds` / `417a9ee7-386d-4341-86c0-fede94b01579`; artifact `runs/lawrence-entity-ladder-04-generated-prop-ids-20260613T083403Z/`.
  - PASS `05_doc_id_equipment_generated_prop_ids`: calibration EntityType ID with production-looking `Equipment` name and generated EquipmentIQ property IDs/names; DTB `EntityLadder05EquipmentGeneratedProps` / `c9ade4d0-c79a-4fa0-a951-49a5cd1d8b80`; artifact `runs/lawrence-entity-ladder-05-equipment-generated-props-20260613T083714Z/`.
  - FAIL `06_safe_range_id_equipment_generated_props`: EntityType ID `500000000000001` with otherwise accepted `Equipment` + generated props shape; non-retriable EntityType import failure, operation `pbipwestus2tp0;DO-0afbf8a2-7496-4f55-8fba-3a4fcec4d777`; artifact `runs/lawrence-entity-ladder-06-safe-range-id-20260613T084038Z/FAILURE.json`.
  - PASS `07_low_range_id_equipment_generated_props`: EntityType ID `100000000000001` with otherwise accepted `Equipment` + generated props shape; DTB `EntityLadder07LowRangeId` / `ea4f66a1-0d08-465c-b35f-a6f5e252754c`; artifact `runs/lawrence-entity-ladder-07-low-range-id-20260613T084311Z/`.
  - PASS `08_mid_range_id_equipment_generated_props`: EntityType ID `200000000000001` with otherwise accepted `Equipment` + generated props shape; DTB `EntityLadder08MidRangeId` / `6c3f7fea-94e3-465a-9641-60a76386642f`; artifact `runs/lawrence-entity-ladder-08-mid-range-id-20260613T084536Z/`.
  - FAIL `09_high_mid_range_id_equipment_generated_props`: EntityType ID `300000000000001` with otherwise accepted `Equipment` + generated props shape; non-retriable EntityType import failure, operation `pbipwestus2tp0;DO-f74ad272-6d21-42df-838f-49f7b0584de0`; artifact `runs/lawrence-entity-ladder-09-high-mid-range-id-20260613T084811Z/FAILURE.json`.
- **Current learned boundary:** production-looking single `Equipment` EntityType shape is accepted when the EntityType ID stays import-safe. EntityType display/name changes, EquipmentIQ property names, and generated property IDs are accepted. EntityType IDs `100000000000001` and `200000000000001` pass; IDs `300000000000001`, `500000000000001`, and `580786628437170` are rejected. Published Microsoft docs only say EntityType `Id` is BigInt, unique, file name equals ID, and value is always greater than 10,000; they do not document the observed upper/profile constraint. Do not use arbitrary/stable-generated EntityType IDs until an accepted numeric/profile allocator is proven.
- **2026-06-14 compiler fix path started:** added `src/eiq_dtb_importer/dtb_compat.py` with explicit `LAWRENCE_F4_ENTITYTYPE_IMPORT_PROFILE` and changed the compiler to generate deterministic EntityType IDs inside conservative `100000000000001..199999999999999` band. Added static tests asserting generated EntityType IDs validate against that profile and that known rejected ID `580786628437170` fails preflight validation.
- **2026-06-14 owner-approved proof PASS:** one scoped fresh DTB create against Lawrence/F4 succeeded using the ID-profile payload. Artifact: `runs/lawrence-idprofile-local-20260613T2214Z/deploy_result.json`. Result: `status=PASS`, `action=create`, `dtbName=DouglasBagmakerDTB_IDProfile_20260614_0800`, `dtbId=50034b64-8c41-4a03-8963-c8cfd2cc8fc2`, `partCountSubmitted=13`, `partCountExported=13`, `RequestId=ff51419f-64b9-4501-a258-f87ff07cfc58`, `tokensPersisted=false`. This proves the full Douglas definition now imports/exports through Fabric public DTB definition APIs when EntityType IDs stay in the compatibility profile. Next gates: run/observe mapping operations serially, run/observe contextualization serially, then validate the `dom` domain layer before wiring Power BI reports.
- **2026-06-14 Gate 1 prerequisite PASS / execution blocker:** created and roundtripped on-demand flow `DouglasBagmakerDTB_IDProfile_20260614_0800_OnDemandFlow` / `de2cd92c-18db-43fb-bc92-6e296f920217`, linked to DTB `50034b64-8c41-4a03-8963-c8cfd2cc8fc2`; artifact `runs/lawrence-idprofile-local-20260613T2214Z/deploy_ondemand_flow_result.json`; `partCountSubmitted=2`, `partCountExported=2`, RequestId `2b322e2b-49d7-45f8-8f94-57153977c240`, `tokensPersisted=false`. Mapping execution itself is blocked from this host because the public REST job endpoint is previously proven invalid for DTB Flow, OpenClaw browser/user-browser attach is unavailable, isolated browser start reports no supported browser, and Fabric CLI `fab` is not installed. Next action is Fabric UI Run on one non-time-series mapping operation, or provide a usable logged-in browser automation surface.

### F009 — Time-series mapping failed because timestamp target was not canonical `Timestamp`

- **Status:** local compiler fix ready; Fabric update pending owner approval
- **Observed:** 2026-06-14 during owner-driven Lawrence/F4 Gate 1 execution on DTB `DouglasBagmakerDTB_IDProfile_20260614_0800` / `50034b64-8c41-4a03-8963-c8cfd2cc8fc2`.
- **Good preceding evidence:** static mappings completed cleanly: `Equipment_equipment`, `System_systems`, and `Part_parts`.
- **Failure:** `Part_historian_timeseries_TimeSeries` queued and ran, then failed. Owner-captured operation details said DTB expected a timestamp property in the map but found none / time-temp is required for a time-series mapping.
- **Root cause:** compiler modeled the Douglas source timestamp column as the target DTB time-series property name: `PreciseTimestamp -> PreciseTimestamp`. Microsoft tutorial behavior and runtime error show the DTB target property must be the canonical `Timestamp`; the source column can remain bundle-specific.
- **Fix:** `src/eiq_dtb_importer/douglas_model.py` now defines Part time-series properties as `Timestamp` and `Value`; `src/eiq_dtb_importer/dtb_compiler.py` maps `SourceColumn: PreciseTimestamp` to `EntityTypePropertyName: Timestamp`. Added regression tests in `tests/test_douglas_model.py` and `tests/test_dtb_compiler_hardening.py`.
- **Local evidence:** `.venv/bin/pytest -q` passed `22 passed in 0.44s`; corrected artifact compiled at `runs/lawrence-idprofile-timestamp-fix-20260614T1516Z/dtb_definition/`; corrected mapping part contains `{SourceColumn: PreciseTimestamp, EntityTypePropertyName: Timestamp}` and `{SourceColumn: Value, EntityTypePropertyName: Value}`.
- **Current-item update result:** owner-approved `updateDefinition` against existing DTB `DouglasBagmakerDTB_IDProfile_20260614_0800` failed quickly at EntityType import: `ALMOperationImportFailed`, operation `pbipwestus2tp1;DO-02633eb5-2b8e-412e-8333-5b41f963b0bf`, `isRetriable=false`; artifact `runs/lawrence-idprofile-timestamp-fix-20260614T1516Z/update_current_dtb_timestamp_fix_FAILURE.json`.
- **Interpretation:** the fix is valid locally, but the current/hydrated DTB likely cannot accept an EntityType time-series property rename/change from `PreciseTimestamp` to `Timestamp` via public `updateDefinition`. This matches earlier learned update/rename fragility for EntityTypes. Do not retry the same update without new evidence.
- **Resolution evidence:** owner-approved fresh DTB create PASS: `DouglasBagmakerDTB_TimestampFix_20260614_1525 / 539e28c2-3e4e-47d3-aaf2-f01a97f09f3a`, parts `13/13`; on-demand flow PASS: `DouglasBagmakerDTB_TimestampFix_20260614_1525_OnDemandFlow / 2ea0a9de-e85d-473b-a72e-db9155c4dab6`, parts `2/2`; manual UI operations PASS for `Equipment_equipment`, `System_systems`, `Part_parts`, and the critical `Part_historian_timeseries_TimeSeries` gate. This proves the corrected mapping `PreciseTimestamp -> Timestamp`.
- **Next gate:** continue contextualization one at a time (`Equipment_contains_System`, then `System_contains_Part`) and then validate DTB domain-layer views. Do not fabricate source fields; if a future bundle lacks a real timestamp/time/temperature semantic, block and report the bundle defect.

### F010 — Child-first ManyToOne containment imports but fails contextualization descriptor binding

- **Status:** compiler fix applied locally; fresh parent-first NoSchema DTB deployment/execution pending
- **Observed:** 2026-06-15 on active item `DouglasBagmakerDTB_NodeDemo_NoSchema` / `47be9dd3-6656-4b6a-add0-b4baf4613a67` after owner manually completed entity and time-series mappings.
- **Failed operation:** `Equipment_contains_System_Contextualization`.
- **Error:** `[User Error] The required property descriptor for column 'EquipmentId' does not exist in the data model (EntityTypeId=117233767744208). Root Activity Id: eaeb81ea-cee6-4a45-8e47-903fa648d5b8`.
- **Why this is not a simple missing-property failure:** local generated EntityType `System` (`117233767744208`) contains static property `EquipmentId`; all relevant mappings had already passed in the NoSchema item.
- **Generated failing shape:** compiler emitted semantic containment as child-first `ManyToOne`:
  - `System -> Equipment`, relationship `contains`, `FirstEntityTypeId=System`, `SecondEntityTypeId=Equipment`
  - `Part -> System`, relationship `contains`, `FirstEntityTypeId=Part`, `SecondEntityTypeId=System`
  - `Equipment_contains_System_Contextualization` used `FirstColumn=System.EquipmentId`, `SecondColumn=Equipment.EquipmentId`.
- **Research evidence before fix:** Microsoft Learn contextualization docs say relationship setup is through **First entity** and **Second entity** join properties; `1:N` applies when one source/first entity connects to many target/second entities. Tutorial Part 3 creates parent-first `1:N` for `Distiller has MaintenanceRequest` (`Distiller` first, `MaintenanceRequest` second). Fabric REST DTB definition docs describe contextualization `FirstColumn`/`SecondColumn` aligned to the relationship's first/second entity IDs. Public Learn/GitHub/Q&A searches found no exact indexed match for the literal error.
- **Root-cause hypothesis:** Fabric DTB import accepts the child-first `ManyToOne` definition, but the runtime contextualizer's property-descriptor lookup for relationship hydration is sensitive to first/second entity and cardinality shape. For Douglas containment, it expects the UI/tutorial parent-first `OneToMany` descriptor binding.
- **Fix:** `src/eiq_dtb_importer/dtb_compiler.py` now emits containment as parent-first `OneToMany`:
  - `Equipment -> System`, join `Equipment.EquipmentId` to `System.EquipmentId`
  - `System -> Part`, join `System.SystemId` to `Part.SystemId`
- **Do not do:** do not blindly retry the failed contextualization on the child-first NoSchema item; do not mutate the hydrated failed item to change relationship shape without a separate owner-approved proof, because DTB update semantics around hydrated EntityType/relationship changes are fragile.
- **Next fix path:** create a fresh no-schema parent-first DTB item and on-demand flow using public Fabric APIs, then owner/manual-run operations serially: Equipment mapping, System mapping, Part mapping, Part time-series mapping, Equipment->System contextualization, System->Part contextualization. Validate Equipment=1, Systems=6, Parts=14, Relationships=20, Part time-series=2160 total with 1980 linked + 180 expected orphan rows.
- **Durable memory:** `memory/lessons-learned-equipmentiq-dtb-parent-first-contextualization-2026-06-15.md`.

## Operational blockers / transient-ish failures

### O001 — Fabric capacity/Spark admission blocked table load

- **Status:** proof unblocked; canonical service still requires Load Table API on sufficient capacity
- **Error:** `TooManyRequestsForCapacity`, HTTP 430
- **Scope:** current F2 proof environment / Spark-backed load jobs
- **Workaround used:** user manually loaded five tables; scoped non-canonical direct Delta upload created `systems`.
- **Canonical fix:** keep automated Lakehouse Load Table API as production path; use read-only OneLake validation to avoid Spark for validation.
- **Artifact:** `runs/direct-delta-systems-20260612T062642Z/direct_delta_systems.json`

### O002 — Spark 3.5/runtime instability may explain notebook/MLV symptoms but not DTB mapping by itself

- **Status:** monitoring / supporting evidence only
- **Observed:** 2026-06-12 after owner created a materialized lake view over `assetdata` and a Spark query failed immediately with HTTP 430 / API-rate-limit wording.
- **Owner clarification:** Stick later clarified Autoscale Billing for Spark is **not enabled**. Treat Autoscale Billing as an important DTB incompatibility guardrail, but not the active cause of the current failures.
- **External signal:** Microsoft Q&A `5562805` reports intermittent Synapse Spark pool failures and increased startup time after Spark 3.5 upgrade, including `Interpreter died`, package reattachment workarounds, and startup growth from ~5–6 minutes to ~15–20 minutes. Fabric Runtime 1.3 is Spark 3.5.5/Python 3.11/Delta 3.2.
- **Interpretation:** Spark/runtime/environment issues can explain notebook/materialized-lake-view instability, cold-start delays, and some 430/admission behavior. They do **not** prove the original DTB mapping failure. Separately, DTB Flow docs explicitly state DTB flows do not work when Autoscale Billing for Spark is enabled, so future DTB tests must keep autoscale off. However, because autoscale is currently not enabled, active root-cause ranking should prioritize DTB operation/runtime details, flow overlap, SQL endpoint/materialization, schema-resolution, and plain F2 headroom.
- **Immediate operator guidance:** keep Autoscale Billing for Spark off; use normal Fabric capacity for DTB Flow tests, then diagnose capacity separately. If F2 remains marginal, temporarily scale the actual Fabric SKU to F8/F16 instead of enabling Spark Autoscale Billing.
- **Flow hygiene:** disable/leave off scheduled DTB flows until manual mapping is stable. Avoid overlapping or repeated mapping execution, because DTB troubleshooting documents concurrent mapping instances as a known failure class (`Concurrent update to the log. Multiple streaming jobs detected`). Run non-time-series mappings first, then time-series mappings, then contextualization/relationship operations.
- **Next evidence:** capture DTB Manage operations → failed operation → Runs tab details, and use SQL endpoint `refreshMetadata` with `recreateTables:false` to test SQL/materialization visibility.

### O003 — SQL endpoint metadata sync/provisioning is not the simple primary blocker

- **Status:** evidence captured; downgraded as primary/simple root cause
- **Observed:** 2026-06-12 API diagnostics run `runs/api-diagnostics-20260612T130704Z/`
- **API action:** Fabric REST SQL endpoint `refreshMetadata` with `recreateTables:false` for:
  - raw source endpoint `DouglasBagmakerRaw` / `ee8df4d1-ec4b-4e99-a52d-3ebaa1ef2623`
  - DTB-created endpoint `DouglasBagmakerDTB_ManualSmokedtdm` / `a37a5da7-f115-488d-9d4e-76324438b54b`
- **Result:** both returned HTTP 200 synchronously; helper status `COMPLETED`; no table-level `Failure` entries observed. Tables returned `NotRun` with prior `lastSuccessfulSyncDateTime` values.
- **Source table evidence:** raw endpoint status includes `equipment`, `parts`, `historian_timeseries`, `ground_truth_bindings`, `historian_tags`, and `systems`, all with prior successful sync timestamps before the failed UI job.
- **DTB endpoint evidence:** DTB-created endpoint exists and reports expected internal/base-layer tables such as `entityinstance`, `entitytype`, `ontology`, property value tables, relationship tables, and time-series value tables.
- **Interpretation:** this weakens a simple “SQL endpoint missing/failed to sync” explanation. It does not rule out operation-level source-resolution bugs, but the metadata plane is not obviously failed.
- **Interesting anomaly:** raw endpoint status also included DTB-style internal tables. Investigate whether these were materialized into/associated with the raw endpoint context, or whether metadata/status reporting spans related DTB base-layer tables.
- **Next evidence:** DTB Manage operations → failed Mapping/Ontology operation → Runs tab error details. The API job instance still only reports `OperationFailure: Multiple operations failed (Mapping, Ontology)`.
- **Artifact summary:** `runs/api-diagnostics-20260612T130704Z/API_DIAGNOSTIC_SUMMARY.md`

## Required practice for future entries

Every non-transient failure entry must include:

1. Failure ID and status.
2. Exact error text and operation/run IDs.
3. Why it is not transient, or why transient classification is justified.
4. Root-cause hypothesis and evidence.
5. Core fix path.
6. Explicit warning if a workaround is proof-only or non-canonical.
7. Tests/artifacts that prove the fix.
