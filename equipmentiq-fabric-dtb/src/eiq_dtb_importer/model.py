from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Property:
    name: str
    value_type: str = "String"
    source_column: str | None = None


@dataclass(frozen=True)
class EntityType:
    name: str
    table: str
    key_columns: tuple[str, ...]
    static_properties: tuple[Property, ...]
    time_series_properties: tuple[Property, ...] = ()


@dataclass(frozen=True)
class RelationshipType:
    name: str
    source_entity: str
    target_entity: str
    source_join_property: str
    target_join_property: str
    cardinality: Literal["OneToMany", "ManyToOne"] = "OneToMany"
    relationship_name: str = "contains"


@dataclass(frozen=True)
class TimeSeriesBinding:
    entity: str
    table: str
    timestamp_column: str
    value_column: str
    entity_link_property: str
    timeseries_link_column: str
