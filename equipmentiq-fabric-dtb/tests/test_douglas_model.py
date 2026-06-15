from eiq_dtb_importer.douglas_model import ENTITIES, RELATIONSHIPS, TIME_SERIES_BINDINGS


def test_douglas_model_shape():
    assert [e.name for e in ENTITIES] == ["Equipment", "System", "Part"]
    assert [r.name for r in RELATIONSHIPS] == ["Equipment_contains_System", "System_contains_Part"]
    assert [(r.source_entity, r.target_entity, r.cardinality) for r in RELATIONSHIPS] == [
        ("Equipment", "System", "OneToMany"),
        ("System", "Part", "OneToMany"),
    ]
    binding = TIME_SERIES_BINDINGS[0]
    part = ENTITIES[2]
    assert [p.name for p in part.time_series_properties] == ["Timestamp", "Value"]
    assert binding.entity == "Part"
    assert binding.timestamp_column == "PreciseTimestamp"
    assert binding.entity_link_property == "HistorianTag"
    assert binding.timeseries_link_column == "HistorianTag"
