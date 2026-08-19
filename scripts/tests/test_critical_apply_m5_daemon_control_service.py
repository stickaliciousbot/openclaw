#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from m4_test_support import FIXTURE, cleanup, make_tmp
from critical_apply_ctl import control_client_contract, submit_execution_request, transport_policy
from critical_apply_controller import prepare_fixture_transaction, query_status
from critical_applyd import daemon_contract
from critical_apply_observer import observe_loop, observe_once
from critical_apply_service_template import service_unit_contract, service_unit_template, validate_service_unit_template


class M5DaemonControlServiceTemplateTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.tx, self.locks, self.shadow = make_tmp("m5-daemon-")

    def tearDown(self):
        cleanup(self.tmp)

    def test_control_client_contract_is_non_authoritative_and_fixture_only(self):
        c = control_client_contract()
        self.assertFalse(c["foreground_client_authoritative"])
        self.assertTrue(c["durable_transaction_truth"])
        self.assertFalse(c["may_install_or_start_service"])
        self.assertFalse(c["may_mutate_openclaw_package_gateway_cron_provider"])
        self.assertEqual(c["supported_fixture_transport"], "sealed_request_files")

    def test_transport_policy_declares_no_network_fixture_mode(self):
        p = transport_policy()
        self.assertFalse(p["controller_authoritative"])
        self.assertTrue(p["observer_or_journal_authoritative"])
        self.assertFalse(p["network_required_for_fixture_mode"])
        self.assertIn("execute", p["accepted_requests"])

    def test_daemon_contract_wraps_observer_without_default_production_authority(self):
        c = daemon_contract()
        self.assertEqual(c["component"], "critical_applyd")
        self.assertTrue(c["supervisor_required_for_production"])
        self.assertTrue(c["fixture_only_until_service_bootstrap_transaction_passes"])
        self.assertFalse(c["may_install_or_start_service"])
        self.assertFalse(c["may_mutate_openclaw_package_gateway_cron_provider"])
        self.assertFalse(c["observer_contract"]["production_install_authorised"])
        self.assertFalse(c["production_package_authority_default_enabled"])
        self.assertTrue(c["production_package_authority_requires_explicit_transaction"])
        self.assertEqual(c["production_package_authority_contract"]["default_state"], "disabled")
        self.assertTrue(c["production_package_authority_contract"]["production_mode_requires_exact_target_roots"])

    def test_service_template_is_offline_source_fixture_only(self):
        c = service_unit_contract()
        self.assertEqual(c["service_name"], "openclaw-critical-apply.service")
        self.assertTrue(c["source_fixture_only"])
        self.assertFalse(c["writes_service_file"])
        self.assertFalse(c["enables_or_starts_service"])
        self.assertTrue(c["uses_system_level_supervisor"])
        self.assertFalse(c["uses_user_session_bus"])
        self.assertTrue(c["contains_control_group_kill"])
        self.assertTrue(c["contains_strict_system_protection"])

    def test_service_template_validation_passes_and_has_exact_entrypoint(self):
        text = service_unit_template()
        v = validate_service_unit_template()
        self.assertTrue(v["ok"], v["reasons"])
        self.assertIn("ExecStart=/usr/bin/python3 /home/stickai/.openclaw/workspace/scripts/critical_applyd.py observe", text)
        self.assertIn("--transaction-root /home/stickai/.openclaw/artifacts/critical-apply/current", text)
        self.assertIn("--stay-alive-after-terminal", text)
        self.assertIn("--create-transaction-root", text)
        self.assertNotIn("systemctl --user", text)
        self.assertNotIn("ExecStart=/bin/sh", text)

    def test_daemon_service_mode_creates_missing_current_root_and_idles(self):
        state = self.tmp / "state"
        current = state / "current"
        script = Path(__file__).resolve().parents[1] / "critical_applyd.py"
        proc = subprocess.run([
            sys.executable,
            str(script),
            "observe",
            "--transaction-root", str(current),
            "--lock-root", str(self.locks),
            "--allowed-root", str(state),
            "--loop",
            "--max-iterations", "1",
            "--poll-seconds", "0.01",
            "--create-transaction-root",
        ], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["classification"], "NO_EXECUTE_REQUEST")
        self.assertTrue(current.is_dir())
        self.assertTrue((current / "receipts").is_dir())

    def test_daemon_service_loop_can_remain_alive_after_terminal_without_rerun(self):
        prepare_fixture_transaction(transaction_root=self.tx, lock_root=self.locks, executable=FIXTURE)
        submit_execution_request(self.tx)
        first = observe_loop(
            self.tx,
            lock_root=self.locks,
            allowed_roots=[self.tx, FIXTURE.parent],
            poll_seconds=0.01,
            max_iterations=2,
            return_after_terminal=False,
        )
        self.assertEqual(first["classification"], "NO_RERUN_AFTER_PRIMARY_EVIDENCE")
        result = json.loads((self.tx / "worker-result.json").read_text())
        self.assertEqual(result["classification"], "EXIT_ZERO")
        self.assertTrue((self.tx / "receipts" / "apply-child-spawned-blocked.json").exists())
        self.assertTrue((self.tx / "mutation.marker").exists())

    def test_ctl_submit_plus_daemon_observe_fixture_transaction(self):
        prepare_fixture_transaction(transaction_root=self.tx, lock_root=self.locks, executable=FIXTURE)
        before = query_status(self.tx)
        self.assertFalse(before["controller_authoritative"])
        req = submit_execution_request(self.tx)
        self.assertEqual(req.request, "execute")
        result = observe_once(self.tx, lock_root=self.locks, allowed_roots=[self.tx, FIXTURE.parent])
        self.assertEqual(result["primary_command_executions"], 1)
        after = query_status(self.tx)
        self.assertFalse(after["controller_authoritative"])
        self.assertTrue((self.tx / "mutation.marker").exists())

    def test_daemon_contract_error_becomes_durable_zero_mutation_hold(self):
        prepare_fixture_transaction(transaction_root=self.tx, lock_root=self.locks, executable=FIXTURE)
        submit_execution_request(self.tx)

        result = observe_once(self.tx, lock_root=self.locks, allowed_roots=[self.tx])

        self.assertEqual(result["classification"], "OBSERVER_CONTRACT_HOLD")
        self.assertEqual(result["primary_command_executions"], 0)
        self.assertEqual(result["approval_consumptions"], 0)
        self.assertEqual(result["mutation_releases"], 0)
        self.assertEqual(result["duplicate_recovery_executions"], 0)
        self.assertEqual(result["leaked_descendants"], 0)
        self.assertEqual(result["details"]["error_code"], "PATH_OUTSIDE_ALLOWED_FIXTURE_ROOTS")
        self.assertFalse(result["details"]["primary_execution_allowed"])
        self.assertFalse(result["details"]["package_gateway_provider_authority_granted"])
        self.assertTrue((self.tx / "worker-result.json").exists())
        self.assertFalse((self.tx / "mutation.marker").exists())


def _contract_case(key: str):
    def test(self):
        c = daemon_contract()
        self.assertIn(key, c)
    return test

for i, key in enumerate([
    "schema",
    "component",
    "stable_entrypoint",
    "observer_contract",
    "foreground_client_authoritative",
    "supervisor_required_for_production",
    "fixture_only_until_service_bootstrap_transaction_passes",
    "may_install_or_start_service",
    "may_mutate_openclaw_package_gateway_cron_provider",
    "service_unit_contract",
    "production_package_authority_contract",
    "production_package_authority_default_enabled",
    "production_package_authority_requires_explicit_transaction",
] * 3):
    setattr(M5DaemonControlServiceTemplateTest, f"test_daemon_contract_key_{i:03d}_{key}", _contract_case(key))


if __name__ == "__main__":
    unittest.main()
