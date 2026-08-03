#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from production_sentinel_comparator import SentinelComparatorError, compare_production_sentinels, legacy_compare

R3_PROD = pathlib.Path('/home/stickai/.openclaw/artifacts/critical-apply/critical-apply-m4r2b-r5-r5b-r3-short-path-validation-20260731T150049Z-c38a164e7058fe9042a4fbb69c30c5bb/m4r2b_r5r5b_r3_production_absence.json')
R4_REPRO = pathlib.Path('/home/stickai/.openclaw/artifacts/critical-apply/critical-apply-m4r2b-r5-r5b-r4-sentinel-classification-20260731T152947Z-3cdc78a77fc3339ad6e4deb61711b7f0/m4r2b_r5r5b_r4_current_comparator_reproduction.json')


def base():
    return {
        "schema": "critical_apply.r5r5b.production_sentinel.v1",
        "label": "pre",
        "utc": "2026-07-31T00:00:00Z",
        "package_exists": True,
        "/protected/config.json": {"exists": True, "sha256": "a" * 64, "size": 10},
        "/protected/missing.pid": {"exists": False, "sha256": None, "size": None},
    }


class ProductionSentinelComparatorTest(unittest.TestCase):

    def test_00_req_src_imports_candidate_from_repository_root_not_fixture_candidate_dir(self):
        imported_path = pathlib.Path(sys.modules["production_sentinel_comparator"].__file__).resolve()
        self.assertEqual(imported_path, ROOT / "production_sentinel_comparator.py")
        self.assertNotIn("candidate", imported_path.parts)

    def assert_pass(self, pre, post):
        result = compare_production_sentinels(pre, post)
        self.assertEqual(result.status, "PASS")
        self.assertTrue(result.protected_match)
        self.assertEqual(result.changes, [])
        self.assertEqual(result.authoritative_digest_pre, result.authoritative_digest_post)

    def assert_abort(self, pre, post):
        result = compare_production_sentinels(pre, post)
        self.assertEqual(result.status, "ABORT")
        self.assertFalse(result.protected_match)
        self.assertNotEqual(result.changes, [])

    def test_01_identical_sentinels_pass(self):
        pre = base(); self.assert_pass(pre, copy.deepcopy(pre))

    def test_02_timestamp_only_drift_pass(self):
        pre = base(); post = copy.deepcopy(pre); post["utc"] = "2026-08-01T00:00:00Z"; self.assert_pass(pre, post)

    def test_03_label_only_drift_pass(self):
        pre = base(); post = copy.deepcopy(pre); post["label"] = "post"; self.assert_pass(pre, post)

    def test_04_timestamp_and_label_drift_pass(self):
        pre = base(); post = copy.deepcopy(pre); post["label"] = "post"; post["utc"] = "2026-08-01T00:00:00Z"; self.assert_pass(pre, post)

    def test_05_serialization_order_or_formatting_only_drift_pass(self):
        pre = base(); post = {k: pre[k] for k in reversed(list(pre.keys()))}; self.assert_pass(pre, post)

    def test_06_protected_semantic_value_drift_aborts(self):
        pre = base(); post = copy.deepcopy(pre); post["/protected/config.json"]["sha256"] = "b" * 64; self.assert_abort(pre, post)

    def test_07_protected_identity_drift_aborts(self):
        pre = base(); post = copy.deepcopy(pre); post["/protected/config-renamed.json"] = post.pop("/protected/config.json"); self.assert_abort(pre, post)

    def test_08_missing_authoritative_field_aborts(self):
        pre = base(); post = copy.deepcopy(pre); del post["/protected/config.json"]["sha256"]
        with self.assertRaises(SentinelComparatorError): compare_production_sentinels(pre, post)

    def test_09_added_unexpected_authoritative_field_aborts(self):
        pre = base(); post = copy.deepcopy(pre); post["/protected/new.json"] = {"exists": True, "sha256": "c"*64, "size": 1}; self.assert_abort(pre, post)

    def test_10_mixed_metadata_and_semantic_drift_aborts(self):
        pre = base(); post = copy.deepcopy(pre); post["label"] = "post"; post["utc"] = "later"; post["package_exists"] = False; self.assert_abort(pre, post)

    def test_11_malformed_sentinel_input_aborts(self):
        with self.assertRaises(SentinelComparatorError): compare_production_sentinels(["not", "object"], base())

    def test_12_current_r3_pre_post_replay_passes_under_repaired_comparator(self):
        prod = json.loads(R3_PROD.read_text())
        repro = json.loads(R4_REPRO.read_text())
        self.assertFalse(legacy_compare(prod["pre"], prod["post"]))
        result = compare_production_sentinels(prod["pre"], prod["post"])
        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.authoritative_digest_pre, "7ec9110321971a281830840c1f6885c0eb059bbcbf766ee6d5ad599b056ef60c")
        self.assertEqual(result.authoritative_digest_post, "7ec9110321971a281830840c1f6885c0eb059bbcbf766ee6d5ad599b056ef60c")
        self.assertTrue(repro["current_comparator_equal"] is False)
        self.assertTrue(repro["authoritative_comparator_equal"] is True)

    def test_13_existing_genuine_production_drift_fixture_remains_abort(self):
        # Model a genuine drift from existing mutation-sentinel pattern: protected hash changes while metadata may drift.
        pre = base(); post = copy.deepcopy(pre); post["label"] = "post"; post["/protected/config.json"]["sha256"] = "d" * 64
        self.assert_abort(pre, post)


if __name__ == "__main__":
    unittest.main(verbosity=2)
