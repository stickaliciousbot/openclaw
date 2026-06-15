from __future__ import annotations

import base64
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .douglas_model import ENTITIES, RELATIONSHIPS, TIME_SERIES_BINDINGS
from .dtb_compat import LAWRENCE_F4_ENTITYTYPE_IMPORT_PROFILE
from .ids import stable_bigint, stable_uuid


@dataclass(frozen=True)
class CompileContext:
    workspace_id: str
    lakehouse_id: str
    dtb_name: str = "DouglasBagmakerDTB"
    source_schema: str | None = None


def _json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, indent=2, sort_keys=False).encode("utf-8")


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_json_bytes(obj))


def _prop_id(entity_name: str, prop_name: str) -> str:
    return stable_bigint("EntityTypeProperty", f"{entity_name}:{prop_name}")


def _entity_id(entity_name: str) -> str:
    raw = int(stable_bigint("EntityType", entity_name))
    return LAWRENCE_F4_ENTITYTYPE_IMPORT_PROFILE.entity_type_id_from_raw(raw)


def _relationship_id(name: str) -> str:
    return stable_bigint("EntityTypeRelationship", name)


def _operation_id(kind: str, name: str) -> str:
    return stable_uuid(kind, name)


def compile_douglas_dtb_definition(ctx: CompileContext, out_dir: Path) -> dict[str, Any]:
    """Emit Douglas Digital Twin Builder definition parts to a directory.

    The output is a local artifact only. Applying it to Fabric is a separate,
    explicit mutation-gated phase.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    parts: list[dict[str, Any]] = []
    ids: dict[str, Any] = {"entities": {}, "properties": {}, "relationships": {}, "operations": {}}

    def source_table_properties(table_name: str) -> dict[str, Any]:
        props: dict[str, Any] = {
            "SourceType": "LakehouseTables",
            "WorkspaceId": ctx.workspace_id,
            "ItemId": ctx.lakehouse_id,
            "SourceTableName": table_name,
        }
        if ctx.source_schema:
            props["SourceSchema"] = ctx.source_schema
        return props

    def add(path: str, obj: Any) -> None:
        target = out_dir / path
        _write_json(target, obj)
        payload = base64.b64encode(_json_bytes(obj)).decode("ascii")
        parts.append({"path": path, "payload": payload, "payloadType": "InlineBase64"})

    add("definition.json", {"LakehouseId": ctx.lakehouse_id})
    platform_part = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "DigitalTwinBuilder", "displayName": ctx.dtb_name},
        "config": {"version": "2.0", "logicalId": "00000000-0000-0000-0000-000000000000"},
    }

    for entity in ENTITIES:
        entity_id = _entity_id(entity.name)
        ids["entities"][entity.name] = entity_id
        props = []
        ts_props = []
        ids["properties"][entity.name] = {}
        for prop in entity.static_properties:
            pid = _prop_id(entity.name, prop.name)
            ids["properties"][entity.name][prop.name] = pid
            props.append({"Id": pid, "Name": prop.name, "ValueType": prop.value_type})
        for prop in entity.time_series_properties:
            pid = _prop_id(entity.name, f"ts:{prop.name}")
            ids["properties"][entity.name][f"ts:{prop.name}"] = pid
            ts_props.append({"Id": pid, "Name": prop.name, "ValueType": prop.value_type})
        add(
            f"EntityTypes/{entity_id}.json",
            {
                "Id": entity_id,
                "Namespace": "usertypes",
                "BaseEntityTypeId": "2",
                "Name": entity.name,
                "Properties": props,
                "TimeseriesProperties": ts_props,
            },
        )

    for entity in ENTITIES:
        op_id = _operation_id("Mapping", f"{entity.name}:{entity.table}:NonTimeSeries")
        ids["operations"][f"Mapping:{entity.name}:NonTimeSeries"] = op_id
        add(
            f"MappingOperations/{op_id}.json",
            {
                # Tenant calibration export uses lower/camel root keys for mappings.
                "operationId": op_id,
                "displayName": f"{entity.name}_{entity.table}",
                "operationType": "Mapping",
                "entityTypeId": ids["entities"][entity.name],
                "mappingOperationProperties": {
                    "MappingType": "NonTimeSeries",
                    "MappedProperties": [
                        {"SourceColumn": prop.name, "EntityTypePropertyName": prop.name}
                        for prop in entity.static_properties
                    ],
                    "ProcessingType": "Iterative",
                    "EntityInstanceIdSchema": list(entity.key_columns),
                    "TimeseriesEntityLinkProperties": None,
                },
                "sourceTableProperties": source_table_properties(entity.table),
                "filters": None,
            },
        )

    for binding in TIME_SERIES_BINDINGS:
        entity = next(e for e in ENTITIES if e.name == binding.entity)
        op_id = _operation_id("Mapping", f"{binding.entity}:{binding.table}:TimeSeries")
        ids["operations"][f"Mapping:{binding.entity}:TimeSeries"] = op_id
        add(
            f"MappingOperations/{op_id}.json",
            {
                "operationId": op_id,
                "displayName": f"{binding.entity}_{binding.table}_TimeSeries",
                "operationType": "Mapping",
                "entityTypeId": ids["entities"][binding.entity],
                "mappingOperationProperties": {
                    "MappingType": "TimeSeries",
                    "MappedProperties": [
                        # DTB requires the mapped timestamp target to be named
                        # exactly Timestamp; the source column can keep the
                        # bundle-specific name such as PreciseTimestamp.
                        {"SourceColumn": binding.timestamp_column, "EntityTypePropertyName": "Timestamp"},
                        {"SourceColumn": binding.value_column, "EntityTypePropertyName": binding.value_column},
                    ],
                    "ProcessingType": "Incremental",
                    "EntityInstanceIdSchema": [],
                    "TimeseriesEntityLinkProperties": {
                        "EntityProperty": binding.entity_link_property,
                        "TimeseriesProperty": binding.timeseries_link_column,
                    },
                },
                "sourceTableProperties": source_table_properties(binding.table),
                "filters": None,
            },
        )

    for rel in RELATIONSHIPS:
        rel_id = _relationship_id(rel.name)
        ids["relationships"][rel.name] = rel_id
        first_entity = rel.source_entity
        second_entity = rel.target_entity
        add(
            f"EntityTypeRelationships/{rel_id}.json",
            {
                "Id": rel_id,
                "Namespace": "usertypes",
                "RelationshipCardinality": rel.cardinality,
                "Name": rel.relationship_name,
                "FirstEntityTypeId": ids["entities"][first_entity],
                "SecondEntityTypeId": ids["entities"][second_entity],
            },
        )
        op_id = _operation_id("Contextualization", rel.name)
        ids["operations"][f"Contextualization:{rel.name}"] = op_id
        add(
            f"ContextualizationOperations/{op_id}.json",
            {
                # Docs use PascalCase for contextualization operations.
                "OperationId": op_id,
                "DisplayName": f"{rel.name}_Contextualization",
                "OperationType": "Contextualization",
                "EntityTypeRelationshipId": rel_id,
                "JoinColumns": {
                    "FirstColumn": {
                        "EntityId": ids["entities"][first_entity],
                        "AttributeName": rel.source_join_property,
                    },
                    "SecondColumn": {
                        "EntityId": ids["entities"][second_entity],
                        "AttributeName": rel.target_join_property,
                    },
                },
            },
        )

    # Match live Fabric export ordering: definition/entity/mapping/... parts,
    # then .platform metadata last.
    add(".platform", platform_part)

    manifest = {
        "parts": [
            {
                "path": part["path"],
                "payloadType": part["payloadType"],
                "bytes": len(base64.b64decode(part["payload"])),
                "json": part["path"].endswith(".json") or part["path"] == ".platform",
            }
            for part in parts
        ]
    }
    definition_payload = {"definition": {"parts": parts}}
    (out_dir / "definition_payload.json").write_text(json.dumps(definition_payload, indent=2), encoding="utf-8")
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (out_dir / "generated_ids.json").write_text(json.dumps(ids, indent=2), encoding="utf-8")
    (out_dir / "compile_context.json").write_text(json.dumps(asdict(ctx), indent=2), encoding="utf-8")
    return {"parts": parts, "ids": ids, "manifest": manifest}
