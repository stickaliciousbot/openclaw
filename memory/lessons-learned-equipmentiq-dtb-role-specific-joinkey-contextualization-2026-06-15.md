# Lesson Learned — EquipmentIQ DTB Role-Specific JoinKey Diagnostic Variant

Date: 2026-06-15

## Issue

Fresh NoSchema JoinKey DTB item `DouglasBagmakerDTB_NodeDemo_JoinKey_NoSchema_20260615_1920` / `a27bf542-4f52-4ad4-8b0c-4a28d503ee8c` completed mapping operations, but contextualization still failed on `System` custom join descriptors.

Correct semantic relationship:

```text
System isPartOf Equipment
System.EquipmentJoinKey = Equipment.EquipmentJoinKey
Many System per Equipment / N:1
```

Failure:

```text
[User Error] The required property descriptor for column 'EquipmentJoinKey' does not exist in the data model (EntityTypeId=117233767744208).
Root Activity Id: e67f2a41-c9ec-411f-b93d-82be6bc283f8
```

Manual wrong-join experiment:

```text
System.SystemJoinKey = Equipment.EquipmentJoinKey
```

also failed:

```text
[User Error] The required property descriptor for column 'SystemJoinKey' does not exist in the data model (EntityTypeId=117233767744208).
Root Activity Id: c25f33d1-1404-4c43-9964-b4295897d2d0
```

`117233767744208` is `System`.

## Evidence captured

Exported live item after failure:

```text
equipmentiq-fabric-dtb/runs/node-demo-joinkey-noschema-20260615T1920AEST/export_after_contextualization_descriptor_fail
```

The export roundtripped `13/13` definition parts and showed:

- `EntityTypes/117233767744208.json` includes both `SystemJoinKey` and `EquipmentJoinKey`.
- `MappingOperations/10cba043-c8bc-53ca-bac7-d7bc77475a59.json` maps both properties from `systems_dtb`.
- UI-edited contextualization persisted to definition JSON, proving UI edits can update public JoinColumns but did not solve descriptor resolution.

## Interpretation

This is not a missing Lakehouse column and not a missing public EntityType property. The failure is earlier than data-value matching: the contextualization worker cannot resolve the selected property as a hydrated DTB data-model descriptor.

Same-name JoinKey ambiguity is possible but not sufficient to explain the failure, because `SystemJoinKey` also failed. The next diagnostic should still remove same-name ambiguity while preserving source-table stability.

## Implemented diagnostic variant

Keep physical `_dtb` source columns stable, but map child-side parent references into role-specific modeled properties:

```text
systems_dtb.EquipmentJoinKey -> System.ParentEquipmentJoinKey
parts_dtb.SystemJoinKey      -> Part.ParentSystemJoinKey
```

Relationship definitions:

```text
System isPartOf Equipment  ManyToOne  System.ParentEquipmentJoinKey = Equipment.EquipmentJoinKey
Part   isPartOf System     ManyToOne  Part.ParentSystemJoinKey      = System.SystemJoinKey
```

This avoids:

- using entity instance ID columns as relationship join attributes,
- using identical child/parent attribute names for parent references,
- requiring another Lakehouse `_dtb` table reload.

## Current status

Implemented locally in both compilers/docs as a diagnostic branch. Not proven until a fresh Fabric DTB item is deployed and run.

## Rules going forward

- Do not retry contextualization blindly on failed/stale DTB items.
- Use fresh DTB items for relationship/contextualization shape changes.
- Preserve exports and root activity IDs after every failure.
- Query DTB SQL/domain views for `dom.*_property` JoinKey/Parent*JoinKey columns to distinguish ontology definition from hydrated descriptors.
- If role-specific properties still fail, escalate to Fabric engineering: public definition/import can create visible properties and mappings, but contextualization worker cannot resolve hydrated descriptors for imported custom properties.
