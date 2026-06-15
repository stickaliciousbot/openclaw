from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
from typing import Any

from .dtb_compiler import CompileContext, _json_bytes


def _part(path: str, obj: Any) -> dict[str, str]:
    return {"path": path, "payload": base64.b64encode(_json_bytes(obj)).decode("ascii"), "payloadType": "InlineBase64"}


def write_payload(out: Path, parts: list[dict[str, str]]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "definition_payload.json").write_text(json.dumps({"definition": {"parts": parts}}, indent=2), encoding="utf-8")
    for part in parts:
        target = out / part["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(base64.b64decode(part["payload"]))
    (out / "manifest.json").write_text(json.dumps({"parts": [{"path": p["path"]} for p in parts]}, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile minimal DTB import smoke variants")
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--lakehouse-id", required=True)
    parser.add_argument("--dtb-name", default="DouglasBagmakerDTB")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    ctx = CompileContext(args.workspace_id, args.lakehouse_id, args.dtb_name)

    platform = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "DigitalTwinBuilder", "displayName": ctx.dtb_name},
        "config": {"version": "2.0", "logicalId": "00000000-0000-0000-0000-000000000000"},
    }
    definition = {"LakehouseId": ctx.lakehouse_id}

    # This follows the public docs example closely: one EntityType, no IsLocked,
    # simple property names, calibration-sized IDs.
    equipment_entity = {
        "Id": "139950578358348",
        "Namespace": "usertypes",
        "BaseEntityTypeId": "2",
        "Name": "Equipment1",
        "Properties": [
            {"Id": "9171801103292694528", "Name": "DisplayName", "ValueType": "String"},
            {"Id": "9171801103292694529", "Name": "SerialNumber", "ValueType": "String"},
            {"Id": "9171801103292694530", "Name": "Manufacturer", "ValueType": "String"},
        ],
        "TimeseriesProperties": [],
    }

    equipment_mapping_pascal = {
        "OperationId": "ce9d0ef9-d8f6-4391-9e37-8bdb91b1fc16",
        "DisplayName": "Equipment1_equipment",
        "OperationType": "Mapping",
        "EntityTypeId": "139950578358348",
        "MappingOperationProperties": {
            "MappingType": "NonTimeSeries",
            "MappedProperties": [
                {"SourceColumn": "DisplayName", "EntityTypePropertyName": "DisplayName"},
                {"SourceColumn": "EquipmentId", "EntityTypePropertyName": "SerialNumber"},
                {"SourceColumn": "Manufacturer", "EntityTypePropertyName": "Manufacturer"},
            ],
            "ProcessingType": "Iterative",
            "EntityInstanceIdSchema": ["EquipmentId"],
            "TimeseriesEntityLinkProperties": None,
        },
        "SourceTableProperties": {
            "SourceType": "LakehouseTables",
            "WorkspaceId": ctx.workspace_id,
            "ItemId": ctx.lakehouse_id,
            "SourceTableName": "equipment",
        },
        "Filters": None,
    }

    variants = {
        "00_definition_only": [_part("definition.json", definition), _part(".platform", platform)],
        "01_one_entity_docs_shape": [
            _part("definition.json", definition),
            _part(".platform", platform),
            _part("EntityTypes/139950578358348.json", equipment_entity),
        ],
        "02_one_entity_one_mapping_docs_shape": [
            _part("definition.json", definition),
            _part(".platform", platform),
            _part("EntityTypes/139950578358348.json", equipment_entity),
            _part("MappingOperations/ce9d0ef9-d8f6-4391-9e37-8bdb91b1fc16.json", equipment_mapping_pascal),
        ],
    }
    for name, parts in variants.items():
        write_payload(args.out / name, parts)
    print(json.dumps({"status": "ok", "variants": list(variants)}, indent=2))


if __name__ == "__main__":
    main()
