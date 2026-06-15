from eiq_dtb_importer.douglas_model import ENTITIES, RELATIONSHIPS, TIME_SERIES_BINDINGS


def test_douglas_model_shape():
    assert [e.name for e in ENTITIES] == ["Equipment", "System", "Part"]
    assert [r.name for r in RELATIONSHIPS] == ["System_isPartOf_Equipment", "Part_isPartOf_System"]
    assert [(r.source_entity, r.target_entity, r.cardinality, r.relationship_name) for r in RELATIONSHIPS] == [
        ("System", "Equipment", "ManyToOne", "isPartOf"),
        ("Part", "System", "ManyToOne", "isPartOf"),
    ]
    binding = TIME_SERIES_BINDINGS[0]
    part = ENTITIES[2]
    assert [p.name for p in part.time_series_properties] == ["Timestamp", "Value"]
    assert binding.entity == "Part"
    assert binding.timestamp_column == "PreciseTimestamp"
    assert binding.entity_link_property == "HistorianTag"
    assert binding.timeseries_link_column == "HistorianTag"


def test_douglas_model_separates_instance_ids_from_join_keys():
    by_name = {entity.name: entity for entity in ENTITIES}

    assert by_name["Equipment"].table == "equipment_dtb"
    assert by_name["Equipment"].key_columns == ("EquipmentUID",)
    assert {p.name for p in by_name["Equipment"].static_properties} >= {"EquipmentId", "EquipmentJoinKey"}

    assert by_name["System"].table == "systems_dtb"
    assert by_name["System"].key_columns == ("SystemUID",)
    assert {p.name for p in by_name["System"].static_properties} >= {
        "SystemId",
        "SystemJoinKey",
        "EquipmentId",
        "EquipmentJoinKey",
    }

    assert by_name["Part"].table == "parts_dtb"
    assert by_name["Part"].key_columns == ("PartUID",)
    assert {p.name for p in by_name["Part"].static_properties} >= {"PartId", "PartJoinKey", "SystemId", "SystemJoinKey"}
    assert TIME_SERIES_BINDINGS[0].table == "historian_timeseries_dtb"
