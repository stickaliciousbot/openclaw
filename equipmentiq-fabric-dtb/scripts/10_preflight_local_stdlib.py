#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eiq_dtb_importer.equipmentiq_zip import inspect_zip  # noqa: E402
from eiq_dtb_importer.ids import stable_bigint, stable_uuid  # noqa: E402
from eiq_dtb_importer.sanitizer import sanitize_name  # noqa: E402
from eiq_dtb_importer.douglas_model import ENTITIES, RELATIONSHIPS, TIME_SERIES_BINDINGS  # noqa: E402

sample = ROOT / "samples" / "dbm-rh-m5-dtb-e2e-kit.zip"
result = inspect_zip(sample)

expected_rows = {
    "equipment.csv": 1,
    "systems.csv": 6,
    "parts.csv": 14,
    "historian_tags.csv": 12,
    "historian_timeseries.csv": 2160,
    "ground_truth_bindings.csv": 12,
}

print("EquipmentIQ bundle counts:")
for name, expected in expected_rows.items():
    actual = result.files[name].rows
    print(f"  {name}: {actual}")
    assert actual == expected, (name, actual, expected)

assert result.linked_ts_rows_expected == 1980
assert result.orphan_ts_rows_expected == 180
assert result.orphan_tags == ("M5_AUX_VIB09.PV",)
assert result.untagged_parts == 3

assert stable_bigint("EntityType", "Part") == stable_bigint("EntityType", "Part")
assert int(stable_bigint("EntityType", "Part")) > 10_000
assert stable_uuid("Mapping", "Part:historian_timeseries:TimeSeries") == stable_uuid("Mapping", "Part:historian_timeseries:TimeSeries")
assert sanitize_name("HistorianTag").target == "HistorianTag"
assert len(sanitize_name("MotorControllerOutputTemperature").target) <= 26
assert [e.name for e in ENTITIES] == ["Equipment", "System", "Part"]
assert [r.name for r in RELATIONSHIPS] == ["System_isPartOf_Equipment", "Part_isPartOf_System"]
assert [r.cardinality for r in RELATIONSHIPS] == ["ManyToOne", "ManyToOne"]
assert [r.relationship_name for r in RELATIONSHIPS] == ["isPartOf", "isPartOf"]
assert TIME_SERIES_BINDINGS[0].entity_link_property == "HistorianTag"

print("\nExpected behavior:")
print(f"  linked_ts_rows_expected: {result.linked_ts_rows_expected}")
print(f"  orphan_ts_rows_expected: {result.orphan_ts_rows_expected}")
print(f"  orphan_tags: {', '.join(result.orphan_tags)}")
print(f"  untagged_parts: {result.untagged_parts}")
print("\nPASS: stdlib local preflight")
