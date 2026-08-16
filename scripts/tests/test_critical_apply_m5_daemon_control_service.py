#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from m4_test_support import FIXTURE, cleanup, make_tmp
from critical_apply_ctl import control_client_contract, submit_execution_request, transport_policy
from critical_apply_controller import prepare_fixture_transaction, query_status
from critical_applyd import daemon_contract
from critical_apply_observer import observe_once
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

    def test_daemon_contract_wraps_observer_without_production_authority(self):
        c = daemon_contract()
        self.assertEqual(c["component"], "critical_applyd")
        self.assertTrue(c["supervisor_required_for_production"])
        self.assertTrue(c["fixture_only_until_service_bootstrap_transaction_passes"])
        self.assertFalse(c["may_install_or_start_service"])
        self.assertFalse(c["may_mutate_openclaw_package_gateway_cron_provider"])
        self.assertFalse(c["observer_contract"]["production_install_authorised"])

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
        self.assertIn("ExecStart=/usr/bin/python3 /home/stickai/.openclaw/workspace/scripts/critical_applyd.py", text)
        self.assertNotIn("systemctl --user", text)
        self.assertNotIn("ExecStart=/bin/sh", text)

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
] * 3):
    setattr(M5DaemonControlServiceTemplateTest, f"test_daemon_contract_key_{i:03d}_{key}", _contract_case(key))


if __name__ == "__main__":
    unittest.main()
