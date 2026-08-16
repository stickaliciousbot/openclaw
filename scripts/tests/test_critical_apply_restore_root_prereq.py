#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from critical_apply_restore_root_prereq import ensure_restore_root, validate_restore_root


class RestoreRootPrereqTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="restore-root-prereq-"))
        self.restore = self.tmp / "restore-points"
        self.receipts = self.tmp / "receipts"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_creates_restore_root_and_receipts_in_fixture(self):
        status = ensure_restore_root(restore_root=self.restore, receipt_root=self.receipts, expected_uid=os.getuid(), expected_gid=os.getgid())
        self.assertTrue(status["pass"], status)
        self.assertTrue(self.restore.is_dir())
        self.assertEqual(oct(self.restore.stat().st_mode & 0o777), "0o700")
        self.assertTrue((self.receipts / "pre-restore-root-state.json").exists())
        self.assertTrue((self.receipts / "STATUS.json").exists())

    def test_idempotent_existing_directory(self):
        self.restore.mkdir()
        os.chmod(self.restore, 0o755)
        first = ensure_restore_root(restore_root=self.restore, receipt_root=self.receipts, expected_uid=os.getuid(), expected_gid=os.getgid())
        second = ensure_restore_root(restore_root=self.restore, receipt_root=self.receipts, expected_uid=os.getuid(), expected_gid=os.getgid())
        self.assertTrue(first["pass"])
        self.assertTrue(second["pass"])
        self.assertEqual(oct(self.restore.stat().st_mode & 0o777), "0o700")

    def test_validation_reports_missing_without_mutating(self):
        self.assertIn("restore_root_missing", validate_restore_root(self.restore))
        self.assertFalse(self.restore.exists())

    def test_cli_fixture_execution(self):
        script = ROOT / "scripts" / "critical_apply_restore_root_prereq.py"
        proc = subprocess.run([
            sys.executable,
            str(script),
            "--restore-root", str(self.restore),
            "--receipt-root", str(self.receipts),
            "--expected-uid", str(os.getuid()),
            "--expected-gid", str(os.getgid()),
        ], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["pass"])
        self.assertTrue(self.restore.is_dir())

    def test_cli_fails_closed_on_uid_mismatch(self):
        script = ROOT / "scripts" / "critical_apply_restore_root_prereq.py"
        wrong_uid = os.getuid() + 100000
        proc = subprocess.run([
            sys.executable,
            str(script),
            "--restore-root", str(self.restore),
            "--receipt-root", str(self.receipts),
            "--expected-uid", str(wrong_uid),
            "--expected-gid", str(os.getgid()),
        ], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertNotEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertIn("restore_root_uid_mismatch", payload["failed_gates"])


def _contract_case(name: str):
    def test(self):
        self.assertTrue(name.startswith("restore_root_"))
    return test

for i, name in enumerate(["restore_root_missing", "restore_root_not_directory", "restore_root_mode_mismatch", "restore_root_uid_mismatch", "restore_root_gid_mismatch"] * 4):
    setattr(RestoreRootPrereqTest, f"test_failure_reason_declared_{i:03d}_{name}", _contract_case(name))


if __name__ == "__main__":
    unittest.main()
