# Lesson Learned — EquipmentIQ DTB Parent-First Contextualization Fix

Date: 2026-06-15

## Issue

`DouglasBagmakerDTB_NodeDemo_NoSchema` successfully completed the Douglas entity and time-series mapping path, but failed at the first relationship contextualization operation:

```text
Equipment_contains_System_Contextualization
[User Error] The required property descriptor for column 'EquipmentId' does not exist in the data model (EntityTypeId=117233767744208). Root Activity Id: eaeb81ea-cee6-4a45-8e47-903fa648d5b8
```

The active DTB item at failure time was:

```text
DouglasBagmakerDTB_NodeDemo_NoSchema / 47be9dd3-6656-4b6a-add0-b4baf4613a67
```

## Why this was deceptive

The generated `System` entity type (`117233767744208`) did contain a static `EquipmentId` property. This was not a simple missing-property JSON defect.

The failure shape pointed at Fabric DTB contextualization binding the join descriptor through the relationship's first/second entity/cardinality contract. The local compiler emitted containment as a child-first relationship:

```text
System -> Equipment, ManyToOne, contains
Part   -> System,    ManyToOne, contains
```

The failed operation therefore joined:

```text
FirstColumn:  System.EquipmentId
SecondColumn: Equipment.EquipmentId
```

Fabric accepted/imported that definition, but runtime contextualization could not find the descriptor it expected for the child foreign-key column in that relationship shape.

## External evidence checked before fixing

Stick explicitly requested a research pass before implementing the fix. We checked Microsoft Learn DTB contextualization docs, Microsoft Learn DTB tutorial Part 3, Fabric REST DTB definition docs, Learn search, GitHub issue search, and public search surfaces.

Findings:

- No exact public Q&A/GitHub match was found for the literal error string.
- Microsoft Learn says relationship creation is configured through **First entity** and **Second entity**, each with a property to join.
- Microsoft Learn says `1:N` is the relationship type when one source/first entity connects to many target/second entities.
- Microsoft Learn tutorial Part 3 uses parent-first `1:N` for `Distiller has MaintenanceRequest`: first entity `Distiller`, second entity `MaintenanceRequest`.
- Fabric REST DTB definition docs model contextualization `JoinColumns` as `FirstColumn` and `SecondColumn`, aligned with the relationship's first/second entity type IDs.

## Durable rule

For Douglas-style containment in Fabric DTB, emit parent-first relationships:

```text
Equipment contains System: Equipment -> System, OneToMany, join Equipment.EquipmentId to System.EquipmentId
System contains Part:      System    -> Part,   OneToMany, join System.SystemId    to Part.SystemId
```

Do **not** emit semantically equivalent child-first `ManyToOne` containment for this demo path unless Fabric later documents/proves that shape works for contextualization.

## Implementation fix

Patch `src/eiq_dtb_importer/dtb_compiler.py` so relationship generation uses:

```text
first_entity  = rel.source_entity   # parent
second_entity = rel.target_entity   # child
RelationshipCardinality = OneToMany
FirstColumn  = parent/source join property
SecondColumn = child/target join property
```

This keeps `douglas_model.py` semantic relationship declarations unchanged while changing the DTB public definition projection to the Fabric-compatible parent-first UI shape.

## Recovery path

Do not retry the failed contextualization operation on the child-first item. Prefer a fresh no-schema parent-first DTB item because previous Fabric DTB evidence shows EntityType/relationship shape updates on already-hydrated items are fragile and can fail at import/runtime boundaries.

Recommended fresh item naming pattern:

```text
DouglasBagmakerDTB_NodeDemo_ParentFirst_NoSchema_<timestamp>
```

Manual operation order remains:

```text
Equipment mapping -> System mapping -> Part mapping -> Part time-series mapping -> Equipment->System contextualization -> System->Part contextualization
```

Expected validation gates:

```text
Equipment: 1
Systems: 6
Parts: 14
Relationships: 20
Part time-series: 2160 total, 1980 linked + 180 expected orphan rows
```

## Related prior lesson

This supersedes/refines `memory/lessons-learned-equipmentiq-dtb-parent-first-contextualization-2026-06-14.md` by adding the evidence-first research pass and concrete compiler fix.
