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
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import critical_apply_service_install_prereq as service_install
from critical_apply_service_install_prereq import ServiceInstallPrereqError, render_install_verify_service_unit
from critical_apply_service_template import service_unit_template


class ServiceInstallPrereqTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="service-install-prereq-"))
        self.unit = self.tmp / "systemd" / "openclaw-critical-apply.service"
        self.receipts = self.tmp / "receipts"
        self.restore = self.tmp / "restore-points"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_renders_writes_verifies_unit_in_fixture(self):
        status = render_install_verify_service_unit(service_unit_path=self.unit, receipt_root=self.receipts, restore_root=self.restore)
        self.assertTrue(status["pass"], status)
        self.assertTrue(self.unit.is_file())
        self.assertEqual(oct(self.unit.stat().st_mode & 0o777), "0o644")
        self.assertIn("critical_applyd.py observe", self.unit.read_text())
        self.assertEqual(status["systemctl_actions"], 0)
        self.assertEqual(status["service_enable_start_actions"], 0)
        self.assertTrue((self.receipts / "status.json").exists())
        self.assertTrue((self.receipts / "summary.json").exists())
        self.assertTrue(Path(status["snapshot_root"]).is_dir())

    def test_existing_unit_is_snapshotted_before_replacement(self):
        self.unit.parent.mkdir(parents=True)
        self.unit.write_text("old unit\n")
        os.chmod(self.unit, 0o644)
        status = render_install_verify_service_unit(service_unit_path=self.unit, receipt_root=self.receipts, restore_root=self.restore)
        self.assertTrue(status["pass"], status)
        pre = status["pre_state"]
        self.assertTrue(pre["exists"])
        copy = Path(pre["snapshot_copy"])
        self.assertTrue(copy.is_file())
        self.assertEqual(copy.read_text(), "old unit\n")
        self.assertEqual(oct(copy.stat().st_mode & 0o777), "0o600")

    def test_absent_unit_writes_absent_snapshot_marker(self):
        status = render_install_verify_service_unit(service_unit_path=self.unit, receipt_root=self.receipts, restore_root=self.restore)
        marker = Path(status["pre_state"]["snapshot_absent_marker"])
        self.assertTrue(marker.is_file())
        payload = json.loads(marker.read_text())
        self.assertEqual(payload["service_unit_path"], str(self.unit))

    def test_cli_fixture_execution(self):
        script = ROOT / "scripts" / "critical_apply_service_install_prereq.py"
        proc = subprocess.run([
            sys.executable,
            str(script),
            "--service-unit-path", str(self.unit),
            "--receipt-root", str(self.receipts),
            "--restore-root", str(self.restore),
        ], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["pass"])
        self.assertEqual(payload["daemon_reload_actions"], 0)
        self.assertEqual(payload["service_or_runtime_activation_actions"], 0)

    def test_maintenance_lock_receipts_are_written_and_released(self):
        locks = self.tmp / "locks"
        status = render_install_verify_service_unit(service_unit_path=self.unit, receipt_root=self.receipts, restore_root=self.restore, lock_root=locks)
        self.assertTrue(status["pass"], status)
        self.assertTrue(status["maintenance_lock"]["acquired"])
        self.assertTrue(status["maintenance_lock"]["released"])
        self.assertTrue((self.receipts / "maintenance-lock-acquired.json").exists())
        self.assertTrue((self.receipts / "maintenance-lock-released.json").exists())
        self.assertFalse((locks / "critical-apply-service-install.lock").exists())

    def test_system_service_path_requires_explicit_authority_and_lock(self):
        system_path = Path("/etc/systemd/system/openclaw-critical-apply.service")
        with self.assertRaises(ServiceInstallPrereqError):
            render_install_verify_service_unit(service_unit_path=system_path, receipt_root=self.receipts, restore_root=self.restore)
        with self.assertRaises(ServiceInstallPrereqError):
            render_install_verify_service_unit(service_unit_path=system_path, receipt_root=self.receipts, restore_root=self.restore, allow_system_path=True)

    def test_maintenance_lock_is_released_when_post_acquire_step_raises(self):
        locks = self.tmp / "locks"
        with mock.patch.object(service_install, "_snapshot_existing_unit", side_effect=PermissionError("synthetic snapshot failure")):
            with self.assertRaises(PermissionError):
                render_install_verify_service_unit(service_unit_path=self.unit, receipt_root=self.receipts, restore_root=self.restore, lock_root=locks)
        released = json.loads((self.receipts / "maintenance-lock-released.json").read_text())
        self.assertTrue(released["released"])
        self.assertFalse((locks / "critical-apply-service-install.lock").exists())

    def test_dead_pid_stale_maintenance_lock_is_cleared_with_receipts(self):
        locks = self.tmp / "locks"
        locks.mkdir()
        stale_lock = locks / "critical-apply-service-install.lock"
        stale_lock.write_text(json.dumps({"pid": 999999999, "schema": "stale.fixture"}) + "\n")
        status = render_install_verify_service_unit(service_unit_path=self.unit, receipt_root=self.receipts, restore_root=self.restore, lock_root=locks)
        self.assertTrue(status["pass"], status)
        self.assertTrue((self.receipts / "stale-maintenance-lock-detected.json").exists())
        cleared = json.loads((self.receipts / "stale-maintenance-lock-cleared.json").read_text())
        self.assertTrue(cleared["cleared"])
        self.assertFalse((locks / "critical-apply-service-install.lock").exists())

    def test_live_or_unknown_maintenance_lock_fails_closed(self):
        locks = self.tmp / "locks"
        locks.mkdir()
        stale_lock = locks / "critical-apply-service-install.lock"
        stale_lock.write_text(json.dumps({"pid": os.getpid(), "schema": "live.fixture"}) + "\n")
        with self.assertRaises(ServiceInstallPrereqError):
            render_install_verify_service_unit(service_unit_path=self.unit, receipt_root=self.receipts, restore_root=self.restore, lock_root=locks)
        self.assertTrue(stale_lock.exists())
        detected = json.loads((self.receipts / "stale-maintenance-lock-detected.json").read_text())
        self.assertIs(detected["previous_pid_alive"], True)
        self.assertFalse((self.receipts / "stale-maintenance-lock-cleared.json").exists())

    def test_relative_paths_fail_closed(self):
        script = ROOT / "scripts" / "critical_apply_service_install_prereq.py"
        proc = subprocess.run([
            sys.executable,
            str(script),
            "--service-unit-path", "relative.service",
            "--receipt-root", str(self.receipts),
            "--restore-root", str(self.restore),
        ], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse((self.tmp / "relative.service").exists())

    def test_cli_system_path_without_authority_emits_hold_receipts(self):
        script = ROOT / "scripts" / "critical_apply_service_install_prereq.py"
        proc = subprocess.run([
            sys.executable,
            str(script),
            "--service-unit-path", "/etc/systemd/system/openclaw-critical-apply.service",
            "--receipt-root", str(self.receipts),
            "--restore-root", str(self.restore),
        ], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertNotEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], "HOLD")
        self.assertEqual(payload["terminal_status"], "HOLD_SERVICE_INSTALL_PREREQ_EXCEPTION_FAILED_CLOSED")
        self.assertTrue((self.receipts / "status.json").exists())
        self.assertTrue((self.receipts / "summary.json").exists())
        self.assertIn("system_service_path_requires_explicit_allow_system_path", payload["failed_gates"][0])

    def test_template_has_no_systemctl_or_shell_start(self):
        text = service_unit_template()
        self.assertNotIn("systemctl", text)
        self.assertNotIn("ExecStart=/bin/sh", text)
        self.assertIn("NoNewPrivileges=true", text)


def _contract_case(name: str):
    def test(self):
        status = render_install_verify_service_unit(service_unit_path=self.unit, receipt_root=self.receipts, restore_root=self.restore)
        self.assertIn(name, status)
    return test

for i, name in enumerate([
    "schema",
    "status",
    "closeout_status",
    "terminal_status",
    "service_unit_path",
    "receipt_root",
    "restore_root",
    "snapshot_root",
    "rendered_sha256",
    "maintenance_lock",
    "system_path_authorized",
    "pre_state",
    "post_state",
    "systemctl_actions",
    "service_enable_start_actions",
    "daemon_reload_actions",
    "service_or_runtime_activation_actions",
] * 2):
    setattr(ServiceInstallPrereqTest, f"test_status_contract_key_{i:03d}_{name}", _contract_case(name))


if __name__ == "__main__":
    unittest.main()
