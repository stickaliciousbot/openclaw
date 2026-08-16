from __future__ import annotations

import json
import os
import shutil
import stat
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import r0_1c_r1_sealed_closeout_worker as worker


class SealedCloseoutWorkerTests(unittest.TestCase):
    def setUp(self) -> None:
        fixture_parent = os.environ.get("R0_1C_R1_TEST_ROOT")
        if not fixture_parent:
            raise unittest.SkipTest("R0_1C_R1_TEST_ROOT is required for source-only fixture isolation")
        self.tmp = Path(fixture_parent).resolve() / self._testMethodName
        self.tmp.mkdir(parents=True, exist_ok=False)
        self.root = self.tmp / "governed-root"
        self.root.mkdir(mode=0o700)
        self._prepare_fixture_tree()
        self.matrix = self.root / "matrix-results.json"
        self.receipt = self.root / "validation-receipt.json"
        self.matrix.write_text(
            json.dumps(
                {
                    "schema": worker.MATRIX_SCHEMA,
                    "status": "PASS",
                    "case_count": 40,
                    "pass_count": 40,
                    "fail_count": 0,
                    "cases": [{"name": f"case-{i:02d}", "status": "PASS"} for i in range(1, 41)],
                    "real_harness_transaction": False,
                    "external_alerts": False,
                    "sealed_source_edited": False,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        self.receipt.write_text(
            json.dumps(
                {
                    "schema": worker.VALIDATION_RECEIPT_SCHEMA,
                    "status": "PASS",
                    "focused_tests": "PASS",
                    "syntax_validation": "PASS",
                    "static_validation": "PASS",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        self.source = self.tmp / "source.py"
        self.source.write_text("VALUE = 1\n", encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _prepare_fixture_tree(self) -> None:
        for case in worker.FIXTURE_CASES:
            (self.root / "fixtures" / case / "harness").mkdir(parents=True)
            (self.root / "fixtures" / case / "semantic").mkdir()
        for relative in worker.FIXTURE_ALLOWED_FILES:
            path = self.root / "fixtures" / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}\n", encoding="utf-8")

    def _build(self) -> dict[str, object]:
        return worker.build(self.root, [self.source], self.matrix, self.receipt)

    def test_precreated_root_publishes_without_overwrite(self) -> None:
        result = self._build()
        self.assertEqual(result["status"], "PASS")
        self.assertTrue((self.root / "manifest.json").is_file())
        self.assertTrue((self.root / "closeout" / "terminal-seal.json").is_file())
        self.assertTrue((self.root / "postseal" / "detached-receipt.json").is_file())
        self.assertTrue((self.root / "synthetic-proof-handoff-v3.json").is_file())
        self.assertFalse(any(self.tmp.glob(f".{self.root.name}.staging-*")))
        self.assertFalse((self.tmp / f".{self.root.name}.lock").exists())
        self.assertEqual(stat.S_IMODE(self.root.stat().st_mode), 0o700)

    def test_unexpected_root_entry_is_rejected_before_publication(self) -> None:
        (self.root / "unexpected.json").write_text("no\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            self._build()
        self.assertFalse((self.root / "manifest.json").exists())

    def test_wrong_mode_is_rejected(self) -> None:
        self.root.chmod(0o755)
        with self.assertRaises(ValueError):
            self._build()

    def test_replay_after_seal_is_rejected(self) -> None:
        self._build()
        with self.assertRaises(ValueError):
            self._build()

    def test_stale_lock_is_rejected(self) -> None:
        lock = self.tmp / f".{self.root.name}.lock"
        lock.write_text("stale\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            self._build()
        lock.unlink()


if __name__ == "__main__":
    unittest.main()
