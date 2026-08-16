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

from critical_apply_service_activation import DEFAULT_SERVICE_NAME, ServiceActivationError, activate_service


FAKE_SYSTEMCTL = r'''#!/usr/bin/env python3
import json, os, sys
state_path = os.environ.get("FAKE_SYSTEMCTL_STATE") or sys.argv[0] + ".state.json"
try:
    state=json.load(open(state_path))
except FileNotFoundError:
    state={"enabled":False,"active":False,"calls":[]}
cmd=sys.argv[1:]
state.setdefault("calls", []).append(cmd)
rc=0; out=""
if cmd == ["daemon-reload"]:
    state["daemon_reload"] = state.get("daemon_reload", 0) + 1
elif len(cmd) == 2 and cmd[0] == "enable":
    state["enabled"] = True
elif len(cmd) == 2 and cmd[0] == "start":
    state["active"] = True
elif len(cmd) == 2 and cmd[0] == "is-enabled":
    rc = 0 if state.get("enabled") else 1; out = "enabled\n" if rc == 0 else "disabled\n"
elif len(cmd) == 2 and cmd[0] == "is-active":
    rc = 0 if state.get("active") else 3; out = "active\n" if rc == 0 else "inactive\n"
else:
    rc=2
json.dump(state, open(state_path, "w"))
sys.stdout.write(out)
sys.exit(rc)
'''


class ServiceActivationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="service-activation-"))
        self.unit = self.tmp / "openclaw-critical-apply.service"
        self.unit.write_text("[Unit]\nDescription=test\n")
        self.receipts = self.tmp / "receipts"
        self.locks = self.tmp / "locks"
        self.fake = self.tmp / "fake-systemctl.py"
        self.fake.write_text(FAKE_SYSTEMCTL)
        os.chmod(self.fake, 0o755)
        self.state = self.tmp / "fake-state.json"
        self.old_env = os.environ.get("FAKE_SYSTEMCTL_STATE")
        os.environ["FAKE_SYSTEMCTL_STATE"] = str(self.state)

    def tearDown(self):
        if self.old_env is None:
            os.environ.pop("FAKE_SYSTEMCTL_STATE", None)
        else:
            os.environ["FAKE_SYSTEMCTL_STATE"] = self.old_env
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_activation_runs_exact_order_and_verifies_state(self):
        status = activate_service(service_name=DEFAULT_SERVICE_NAME, service_unit_path=self.unit, receipt_root=self.receipts, lock_root=self.locks, systemctl_path=self.fake, timeout_seconds=5)
        self.assertTrue(status["pass"], status)
        self.assertEqual(status["daemon_reload_actions"], 1)
        self.assertEqual(status["service_enable_start_actions"], 2)
        self.assertEqual(status["systemctl_actions"], 3)
        state = json.loads(self.state.read_text())
        self.assertEqual(state["calls"][:3], [["is-enabled", DEFAULT_SERVICE_NAME], ["is-active", DEFAULT_SERVICE_NAME], ["daemon-reload"]])
        self.assertIn(["enable", DEFAULT_SERVICE_NAME], state["calls"])
        self.assertIn(["start", DEFAULT_SERVICE_NAME], state["calls"])
        self.assertTrue((self.receipts / "status.json").exists())
        self.assertTrue((self.receipts / "maintenance-lock-released.json").exists())
        self.assertFalse((self.locks / "critical-apply-service-activation.lock").exists())

    def test_missing_service_unit_fails_closed_before_systemctl(self):
        self.unit.unlink()
        with self.assertRaises(ServiceActivationError):
            activate_service(service_name=DEFAULT_SERVICE_NAME, service_unit_path=self.unit, receipt_root=self.receipts, lock_root=self.locks, systemctl_path=self.fake)
        self.assertFalse(self.state.exists())

    def test_wrong_service_name_rejected(self):
        with self.assertRaises(ServiceActivationError):
            activate_service(service_name="ssh.service", service_unit_path=self.unit, receipt_root=self.receipts, lock_root=self.locks, systemctl_path=self.fake)

    def test_cli_emits_hold_receipts_on_wrong_service_name(self):
        script = ROOT / "scripts" / "critical_apply_service_activation.py"
        proc = subprocess.run([
            sys.executable, str(script),
            "--service-name", "ssh.service",
            "--service-unit-path", str(self.unit),
            "--receipt-root", str(self.receipts),
            "--lock-root", str(self.locks),
            "--systemctl-path", str(self.fake),
        ], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertNotEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], "HOLD")
        self.assertEqual(payload["systemctl_actions"], 0)
        self.assertTrue((self.receipts / "status.json").exists())

    def test_cli_fixture_success(self):
        script = ROOT / "scripts" / "critical_apply_service_activation.py"
        proc = subprocess.run([
            sys.executable, str(script),
            "--service-unit-path", str(self.unit),
            "--receipt-root", str(self.receipts),
            "--lock-root", str(self.locks),
            "--systemctl-path", str(self.fake),
        ], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["pass"])
        self.assertEqual(payload["terminal_status"], "PASS_SERVICE_ACTIVATION_DAEMON_RELOAD_ENABLE_START_VERIFIED")


def _contract_case(name: str):
    def test(self):
        status = activate_service(service_name=DEFAULT_SERVICE_NAME, service_unit_path=self.unit, receipt_root=self.receipts, lock_root=self.locks, systemctl_path=self.fake)
        self.assertIn(name, status)
    return test

for i, name in enumerate([
    "schema", "status", "closeout_status", "terminal_status", "service_name", "service_unit_path", "receipt_root", "systemctl_path", "maintenance_lock", "pre_state", "post_state", "command_results", "systemctl_actions", "daemon_reload_actions", "service_enable_start_actions", "gateway_config_or_cron_mutations", "package_or_runtime_mutations", "network_or_provider_calls"
] * 2):
    setattr(ServiceActivationTest, f"test_status_contract_key_{i:03d}_{name}", _contract_case(name))


if __name__ == "__main__":
    unittest.main()
