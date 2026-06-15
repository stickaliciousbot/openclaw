# Agent Rules

Goal: get the Douglas bagmaker EquipmentIQ export running as a Microsoft Fabric Digital Twin Builder work item with complete ontology, mappings, time-series link, and relationships.

Do not implement Fabric task-flow import. It is not the deployment path.

Use public Fabric APIs first. Do not call undocumented/private portal APIs in production code.

Use Playwright only as a fallback to trigger DTB run operations if no documented public run API exists. Do not use Playwright to author the ontology canvas.

Keep all generated definition JSON in `runs/<run-id>/definition_parts` before sending to Fabric.

Never delete Fabric items unless `--allow-delete` is explicitly set.

Use delegated user auth for DTB APIs because current DTB create/update/get definition APIs do not support service principals or managed identities.

Validate row counts, time-series link behavior, decoy tag behavior, and relationship counts before marking success.

## Current contextualization rule

The active Douglas DTB compiler shape is **role-specific JoinKey / child-first ManyToOne**, not the older raw-key `contains` shape or same-name JoinKey shape.

- Use `EquipmentUID`, `SystemUID`, and `PartUID` only for `EntityInstanceIdSchema` identity.
- Keep physical `_dtb` source columns stable, but map child-side parent references to role-specific modeled properties:
  - `systems_dtb.EquipmentJoinKey -> System.ParentEquipmentJoinKey`
  - `parts_dtb.SystemJoinKey -> Part.ParentSystemJoinKey`
- Use child-to-parent tutorial-aligned relationships:
  - `System isPartOf Equipment`, `ManyToOne`, `System.ParentEquipmentJoinKey = Equipment.EquipmentJoinKey`
  - `Part isPartOf System`, `ManyToOne`, `Part.ParentSystemJoinKey = System.SystemJoinKey`
- Source tables for this variant are `equipment_dtb`, `systems_dtb`, `parts_dtb`, and `historian_timeseries_dtb`.

Do not point the role-specific JoinKey compiler output at the old raw tables. Do not tell the operator to run Fabric hydration until the `_dtb` source tables/views have been created and a fresh DTB + on-demand flow has roundtripped. This variant is diagnostic until a fresh Fabric run passes; preserve root activity IDs and exports if it fails.

For app-loaded Douglas/JoinKey tables, never emit `SourceSchema` in MappingOperations. The `_dtb` tables are root Lakehouse tables; `dbo` recreates the known `Tables/dbo/<table>` `PATH_NOT_FOUND` failure.

## Failure discipline

For straight-up non-transient failures, update `docs/FAILURES_AND_FIXES_LEDGER.md` with the exact error, operation/run IDs, classification, root-cause hypothesis, and core fix path before adding workaround code.

Do not patch over deterministic Fabric import failures with ad-hoc branches. First identify the contract gap, then encode it in a compatibility profile/canonicalizer plus tests/static validation.

DigitalTwinBuilder deployment is not complete until mapped ontology operations are connected to the DTB item through `DigitalTwinBuilderFlow` definitions and that linkage roundtrips with the expected `DigitalTwinBuilderId` and `OperationIds`.

If/when Codex CLI is assigned fix work, start it in goal mode from `docs/CODEX_GOAL_DTB_COMPILER_FIX.md`; full control is allowed inside this repo, but no token persistence, no Fabric deletes, and no raw-data reading when compact artifacts suffice.

## Token-efficiency rule

Do not make Codex or another agent read raw data if a compact summary answers the question. Prefer bounded command output, helper scripts, targeted snippets/diffs, explicit do-not-read boundaries, and concise validation-backed reporting.
