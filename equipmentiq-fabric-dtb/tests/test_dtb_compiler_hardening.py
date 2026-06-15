import base64
import json
from pathlib import Path

from eiq_dtb_importer.dtb_compat import LAWRENCE_F4_ENTITYTYPE_IMPORT_PROFILE
from eiq_dtb_importer.dtb_compiler import CompileContext, compile_douglas_dtb_definition


def _compile(tmp_path: Path):
    return compile_douglas_dtb_definition(
        CompileContext(
            workspace_id="11111111-1111-1111-1111-111111111111",
            lakehouse_id="22222222-2222-2222-2222-222222222222",
        ),
        tmp_path,
    )


def _decoded_parts(result):
    decoded = {}
    for part in result["parts"]:
        decoded[part["path"]] = json.loads(base64.b64decode(part["payload"]).decode("utf-8"))
    return decoded


def test_definition_payload_shape_for_update_definition(tmp_path: Path):
    result = _compile(tmp_path)
    payload = json.loads((tmp_path / "definition_payload.json").read_text())
    assert set(payload) == {"definition"}
    assert payload["definition"]["parts"] == result["parts"]
    assert all(set(part) == {"path", "payload", "payloadType"} for part in payload["definition"]["parts"])
    assert all(part["payloadType"] == "InlineBase64" for part in payload["definition"]["parts"])


def test_property_id_uniqueness(tmp_path: Path):
    parts = _decoded_parts(_compile(tmp_path))
    ids = []
    for path, payload in parts.items():
        if path.startswith("EntityTypes/"):
            ids.append(payload["Id"])
            ids.extend(prop["Id"] for prop in payload["Properties"])
            ids.extend(prop["Id"] for prop in payload["TimeseriesProperties"])
        elif path.startswith("EntityTypeRelationships/"):
            ids.append(payload["Id"])
        elif path.startswith("MappingOperations/"):
            ids.append(payload["operationId"])
        elif path.startswith("ContextualizationOperations/"):
            ids.append(payload["OperationId"])
    assert len(ids) == len(set(ids))


def test_entity_type_ids_use_observed_import_safe_band(tmp_path: Path):
    parts = _decoded_parts(_compile(tmp_path))
    entity_ids = [int(payload["Id"]) for path, payload in parts.items() if path.startswith("EntityTypes/")]
    assert entity_ids
    for entity_id in entity_ids:
        LAWRENCE_F4_ENTITYTYPE_IMPORT_PROFILE.validate_entity_type_id(entity_id)
        assert entity_id < 300_000_000_000_001


def test_compat_profile_rejects_known_bad_entity_type_id():
    try:
        LAWRENCE_F4_ENTITYTYPE_IMPORT_PROFILE.validate_entity_type_id(580_786_628_437_170)
    except ValueError as exc:
        assert "outside import-safe DTB profile" in str(exc)
    else:
        raise AssertionError("known Fabric-rejected EntityType ID should fail static validation")


def test_compile_idempotency(tmp_path: Path):
    a_dir = tmp_path / "a"
    b_dir = tmp_path / "b"
    _compile(a_dir)
    _compile(b_dir)
    for rel in ["definition_payload.json", "generated_ids.json", "manifest.json"]:
        assert (a_dir / rel).read_text() == (b_dir / rel).read_text()


def test_system_equipment_relationship_uses_join_key_many_to_one_contextualization(tmp_path: Path):
    parts = _decoded_parts(_compile(tmp_path))
    ids = json.loads((tmp_path / "generated_ids.json").read_text())
    rel = next(p for path, p in parts.items() if path.startswith("EntityTypeRelationships/") and p["Id"] == ids["relationships"]["System_isPartOf_Equipment"])
    ctx = next(p for path, p in parts.items() if path.startswith("ContextualizationOperations/") and p["EntityTypeRelationshipId"] == rel["Id"])

    # Keep entity instance identity columns out of relationship joins. The
    # contextualization engine failed descriptor binding when EquipmentId was
    # both the entity instance ID column and the relationship attribute.
    assert rel["RelationshipCardinality"] == "ManyToOne"
    assert rel["Name"] == "isPartOf"
    assert rel["FirstEntityTypeId"] == ids["entities"]["System"]
    assert rel["SecondEntityTypeId"] == ids["entities"]["Equipment"]
    assert ctx["JoinColumns"]["FirstColumn"] == {"EntityId": ids["entities"]["System"], "AttributeName": "ParentEquipmentJoinKey"}
    assert ctx["JoinColumns"]["SecondColumn"] == {"EntityId": ids["entities"]["Equipment"], "AttributeName": "EquipmentJoinKey"}


def test_part_system_relationship_uses_join_key_many_to_one_contextualization(tmp_path: Path):
    parts = _decoded_parts(_compile(tmp_path))
    ids = json.loads((tmp_path / "generated_ids.json").read_text())
    rel = next(p for path, p in parts.items() if path.startswith("EntityTypeRelationships/") and p["Id"] == ids["relationships"]["Part_isPartOf_System"])
    ctx = next(p for path, p in parts.items() if path.startswith("ContextualizationOperations/") and p["EntityTypeRelationshipId"] == rel["Id"])

    assert rel["RelationshipCardinality"] == "ManyToOne"
    assert rel["Name"] == "isPartOf"
    assert rel["FirstEntityTypeId"] == ids["entities"]["Part"]
    assert rel["SecondEntityTypeId"] == ids["entities"]["System"]
    assert ctx["JoinColumns"]["FirstColumn"] == {"EntityId": ids["entities"]["Part"], "AttributeName": "ParentSystemJoinKey"}
    assert ctx["JoinColumns"]["SecondColumn"] == {"EntityId": ids["entities"]["System"], "AttributeName": "SystemJoinKey"}


def test_mapping_unique_ids_are_not_relationship_join_properties(tmp_path: Path):
    parts = _decoded_parts(_compile(tmp_path))

    mappings_by_display = {
        payload["displayName"]: payload
        for path, payload in parts.items()
        if path.startswith("MappingOperations/") and payload["operationType"] == "Mapping"
    }

    assert mappings_by_display["Equipment_equipment_dtb"]["mappingOperationProperties"]["EntityInstanceIdSchema"] == ["EquipmentUID"]
    assert mappings_by_display["System_systems_dtb"]["mappingOperationProperties"]["EntityInstanceIdSchema"] == ["SystemUID"]
    assert mappings_by_display["Part_parts_dtb"]["mappingOperationProperties"]["EntityInstanceIdSchema"] == ["PartUID"]

    equipment_props = mappings_by_display["Equipment_equipment_dtb"]["mappingOperationProperties"]["MappedProperties"]
    system_props = mappings_by_display["System_systems_dtb"]["mappingOperationProperties"]["MappedProperties"]
    part_props = mappings_by_display["Part_parts_dtb"]["mappingOperationProperties"]["MappedProperties"]
    assert {"SourceColumn": "EquipmentJoinKey", "EntityTypePropertyName": "EquipmentJoinKey"} in equipment_props
    assert {"SourceColumn": "EquipmentJoinKey", "EntityTypePropertyName": "ParentEquipmentJoinKey"} in system_props
    assert {"SourceColumn": "SystemJoinKey", "EntityTypePropertyName": "ParentSystemJoinKey"} in part_props


def test_source_schema_none_omits_source_schema(tmp_path: Path):
    result = compile_douglas_dtb_definition(
        CompileContext(
            workspace_id="11111111-1111-1111-1111-111111111111",
            lakehouse_id="22222222-2222-2222-2222-222222222222",
            source_schema=None,
        ),
        tmp_path,
    )
    for path, payload in _decoded_parts(result).items():
        if path.startswith("MappingOperations/"):
            assert "SourceSchema" not in payload["sourceTableProperties"]


def test_default_source_schema_omits_source_schema_for_app_loaded_root_tables(tmp_path: Path):
    result = _compile(tmp_path)
    for path, payload in _decoded_parts(result).items():
        if path.startswith("MappingOperations/"):
            assert "SourceSchema" not in payload["sourceTableProperties"]


def test_time_series_entity_instance_id_schema_is_empty_array(tmp_path: Path):
    parts = _decoded_parts(_compile(tmp_path))
    ts = next(p for path, p in parts.items() if path.startswith("MappingOperations/") and p["mappingOperationProperties"]["MappingType"] == "TimeSeries")
    assert ts["mappingOperationProperties"]["EntityInstanceIdSchema"] == []


def test_time_series_timestamp_maps_to_required_dtb_timestamp_property(tmp_path: Path):
    parts = _decoded_parts(_compile(tmp_path))
    part_entity = next(p for path, p in parts.items() if path.startswith("EntityTypes/") and p["Name"] == "Part")
    assert {p["Name"] for p in part_entity["TimeseriesProperties"]} == {"Timestamp", "Value"}

    ts = next(p for path, p in parts.items() if path.startswith("MappingOperations/") and p["mappingOperationProperties"]["MappingType"] == "TimeSeries")
    mapped = ts["mappingOperationProperties"]["MappedProperties"]
    assert {"SourceColumn": "PreciseTimestamp", "EntityTypePropertyName": "Timestamp"} in mapped
    assert {"SourceColumn": "Value", "EntityTypePropertyName": "Value"} in mapped
