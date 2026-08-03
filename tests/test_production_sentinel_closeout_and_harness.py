#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from production_sentinel_comparator import SentinelComparatorError
from production_sentinel_closeout import production_sentinel_caused_deltas

HARNESS_PATH = ROOT / "scripts" / "long_running_cron_observer_harness.py"
spec = importlib.util.spec_from_file_location("long_running_cron_observer_harness", HARNESS_PATH)
harness = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = harness
spec.loader.exec_module(harness)


def sentinel(label="pre"):
    return {
        "schema": "critical_apply.r5r5b.production_sentinel.v1",
        "label": label,
        "utc": "2026-08-03T00:00:00Z",
        "package_exists": True,
        "/protected/config.json": {"exists": True, "sha256": "a" * 64, "size": 10},
        "/protected/missing.pid": {"exists": False, "sha256": None, "size": None},
    }


class RealCloseoutRequirementTest(unittest.TestCase):
    def test_req_close_001_identical_sentinel_has_no_delta_and_no_output_writes(self):
        with tempfile.TemporaryDirectory() as td:
            before = set(pathlib.Path(td).iterdir())
            cwd = os.getcwd()
            os.chdir(td)
            try:
                result = production_sentinel_caused_deltas(sentinel(), sentinel())
            finally:
                os.chdir(cwd)
            after = set(pathlib.Path(td).iterdir())
        self.assertEqual(result, 0)
        self.assertEqual(before, after)

    def test_req_close_001_protected_drift_returns_fail_closed_delta_record(self):
        pre = sentinel("pre")
        post = sentinel("post")
        post["/protected/config.json"]["sha256"] = "b" * 64
        result = production_sentinel_caused_deltas(pre, post)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["classification"], "protected_semantic_or_identity_drift")
        self.assertNotEqual(result["changes"], [])
        self.assertNotEqual(result["authoritative_digest_pre"], result["authoritative_digest_post"])

    def test_req_close_001_malformed_sentinel_fails_closed(self):
        with self.assertRaises(SentinelComparatorError):
            production_sentinel_caused_deltas(["not", "a", "sentinel"], sentinel())


class RealHarnessRequirementTest(unittest.TestCase):
    def test_req_harness_001_launch_pass_like_record_is_not_semantic_pass(self):
        records = [{"classification": "PASS_DETACHED_OBSERVER_LAUNCHED_EVIDENCE_WRITTEN"}]
        self.assertEqual(harness.terminal_precedence(records), "HOLD")

    def test_req_harness_001_mixed_or_missing_terminal_fails_closed_to_hold(self):
        self.assertEqual(harness.terminal_precedence([]), "HOLD")
        self.assertEqual(harness.terminal_precedence([{"terminal": "PASS"}, {"terminal": "FAIL"}]), "HOLD")
        self.assertEqual(harness.terminal_precedence([{"terminal": "PASS"}, {"state": "PASS"}]), "PASS")

    def test_req_harness_001_alert_watcher_receipt_is_known_evidence_artifact(self):
        self.assertIn("alert_watcher_identity_receipt.json", harness.EVIDENCE_ARTIFACTS)
        self.assertIn("terminal-seal.json", harness.EVIDENCE_ARTIFACTS)

    def test_req_harness_001_manifest_is_non_circular_for_manifest_and_terminal_seal(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / "evidence.json").write_text(json.dumps({"ok": True}))
            (root / "manifest.json").write_text("must be excluded")
            (root / "terminal-seal.json").write_text("must be excluded")
            manifest = harness.build_manifest(root, "PASS")
        self.assertEqual(manifest["terminal"], "PASS")
        self.assertEqual(manifest["non_circular_exclusions"], ["manifest.json", "terminal-seal.json"])
        self.assertEqual([entry["path"] for entry in manifest["files"]], ["evidence.json"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
