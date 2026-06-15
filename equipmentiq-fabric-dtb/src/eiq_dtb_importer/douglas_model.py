from __future__ import annotations

from .model import EntityType, Property, RelationshipType, TimeSeriesBinding

EQUIPMENT = EntityType(
    name="Equipment",
    table="equipment_dtb",
    key_columns=("EquipmentUID",),
    static_properties=(
        Property("EquipmentId"),
        Property("EquipmentJoinKey"),
        Property("DisplayName"),
        Property("Manufacturer"),
        Property("ModelNumber"),
    ),
)

SYSTEM = EntityType(
    name="System",
    table="systems_dtb",
    key_columns=("SystemUID",),
    static_properties=(
        Property("SystemId"),
        Property("SystemJoinKey"),
        Property("DisplayName"),
        Property("EquipmentId"),
        Property("EquipmentJoinKey"),
    ),
)

PART = EntityType(
    name="Part",
    table="parts_dtb",
    key_columns=("PartUID",),
    static_properties=(
        Property("PartId"),
        Property("PartJoinKey"),
        Property("DisplayName"),
        Property("Category"),
        Property("SystemId"),
        Property("SystemJoinKey"),
        Property("HistorianTag"),
    ),
    time_series_properties=(
        # DTB time-series mappings require the target timestamp property to be
        # named exactly Timestamp. The Douglas source column remains
        # PreciseTimestamp and is mapped to this canonical DTB property.
        Property("Timestamp", "DateTime"),
        Property("Value", "Double"),
    ),
)

ENTITIES = (EQUIPMENT, SYSTEM, PART)

RELATIONSHIPS = (
    RelationshipType(
        name="System_isPartOf_Equipment",
        source_entity="System",
        target_entity="Equipment",
        source_join_property="EquipmentJoinKey",
        target_join_property="EquipmentJoinKey",
        cardinality="ManyToOne",
        relationship_name="isPartOf",
    ),
    RelationshipType(
        name="Part_isPartOf_System",
        source_entity="Part",
        target_entity="System",
        source_join_property="SystemJoinKey",
        target_join_property="SystemJoinKey",
        cardinality="ManyToOne",
        relationship_name="isPartOf",
    ),
)

TIME_SERIES_BINDINGS = (
    TimeSeriesBinding(
        entity="Part",
        table="historian_timeseries_dtb",
        timestamp_column="PreciseTimestamp",
        value_column="Value",
        entity_link_property="HistorianTag",
        timeseries_link_column="HistorianTag",
    ),
)
