#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from m4_test_support import FIXTURE, cleanup, make_tmp
from critical_apply_atomic_io import sha256_file
from critical_apply_package_authority import (
    PACKAGE_AUTHORITY_SCHEMA,
    PACKAGE_TRANSACTION_SPEC_SCHEMA,
    make_package_apply_authority,
    package_authority_contract,
    package_transaction_spec_template,
    validate_package_apply_authority,
    validate_package_transaction_spec,
)
from critical_apply_process import EXEC_SPEC_SCHEMA, ExactExecSpec, ProcessContractError, validate_exact_exec_spec

OPENCLAW_PACKAGE_ROOT = "/home/stickai/.npm-global/lib/node_modules/openclaw"
OPENCLAW_BIN = "/home/stickai/.npm-global/bin/openclaw"


class PackageAuthorityContractTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.tx, self.locks, self.shadow = make_tmp("m8-r10-package-authority-")

    def tearDown(self):
        cleanup(self.tmp)

    def package_spec(self, *, target_roots=None):
        return package_transaction_spec_template(
            package_artifact_sha256="a" * 64,
            source_package_path=str(self.tx / "candidate.tgz"),
            target_roots=target_roots or [OPENCLAW_PACKAGE_ROOT, OPENCLAW_BIN],
            restore_point_id="restore-m8-r10-fixture",
            restore_manifest_sha256="b" * 64,
            postcheck_sha256="c" * 64,
            rollback_plan_sha256="d" * 64,
        )

    def authority(self, *, enabled=True, spec=None):
        spec = spec or self.package_spec()
        return make_package_apply_authority(
            transaction_id="critical-apply-package-fixture-20260817T011700Z-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            package_spec=spec,
            authority_enabled=enabled,
            maintenance_lock_path=str(self.locks / "package-apply.lock"),
            independent_watcher_registration_path=str(self.tx / "watcher-registration.json"),
            restore_point_id="restore-m8-r10-fixture",
            restore_manifest_sha256="b" * 64,
        )

    def exec_spec(self, *, stdout_path=None, cwd=None):
        exe = FIXTURE.resolve()
        return ExactExecSpec(
            EXEC_SPEC_SCHEMA,
            str(exe),
            tuple([str(exe), str(self.tx / "marker")]),
            sha256_file(exe),
            str(cwd or self.tx),
            {"CRITICAL_APPLY_FIXTURE": "1"},
            str(stdout_path or (self.tx / "logs/out.log")),
            str(self.tx / "logs/err.log"),
            timeout_seconds=1.0,
        )

    def test_contract_is_disabled_by_default_and_requires_exact_authority(self):
        c = package_authority_contract()
        self.assertEqual(c["default_state"], "disabled")
        self.assertTrue(c["fixture_mode_package_roots_forbidden"])
        self.assertTrue(c["production_mode_requires_explicit_authority"])
        self.assertTrue(c["production_mode_requires_exact_target_roots"])
        self.assertTrue(c["production_mode_requires_checksum_pinned_package"])
        self.assertTrue(c["production_mode_requires_restore_point"])
        self.assertTrue(c["production_mode_requires_independent_watcher"])
        self.assertTrue(c["no_live_apply_in_contract_module"])

    def test_package_transaction_spec_accepts_exact_openclaw_targets(self):
        spec = self.package_spec()
        ok, reasons = validate_package_transaction_spec(spec)
        self.assertTrue(ok, reasons)
        self.assertEqual(spec["schema"], PACKAGE_TRANSACTION_SPEC_SCHEMA)
        self.assertEqual(spec["transaction_type"], "package_apply")
        self.assertFalse(spec["restart_authorised"])
        self.assertFalse(spec["functional_smoke_authorised"])

    def test_package_transaction_spec_rejects_broad_package_root(self):
        spec = self.package_spec(target_roots=["/home/stickai/.npm-global"])
        ok, reasons = validate_package_transaction_spec(spec)
        self.assertFalse(ok)
        self.assertIn("target_root_too_broad:/home/stickai/.npm-global", reasons)

    def test_package_authority_disabled_fails_when_enable_required(self):
        auth = self.authority(enabled=False)
        self.assertEqual(auth["schema"], PACKAGE_AUTHORITY_SCHEMA)
        ok, reasons = validate_package_apply_authority(auth, require_enabled=True)
        self.assertFalse(ok)
        self.assertIn("authority_not_enabled", reasons)

    def test_package_authority_enabled_requires_restore_lock_watcher_and_zero_counters(self):
        auth = self.authority(enabled=True)
        ok, reasons = validate_package_apply_authority(auth, require_enabled=True)
        self.assertTrue(ok, reasons)
        self.assertTrue(auth["maintenance_lock"]["required"])
        self.assertTrue(auth["restore_point"]["required"])
        self.assertTrue(auth["rollback"]["required"])
        self.assertTrue(auth["independent_watcher"]["required"])
        self.assertEqual(auth["forbidden_side_effect_counters"]["gateway_config_or_cron_mutations"], 0)

    def test_fixture_mode_rejects_package_root_even_when_allowed_root_is_broadly_added(self):
        spec = self.exec_spec(stdout_path=Path(OPENCLAW_PACKAGE_ROOT) / "logs/out.log")
        with self.assertRaises(ProcessContractError) as ctx:
            validate_exact_exec_spec(spec, transaction_root=self.tx, allowed_roots=[self.tx, FIXTURE.parent, Path(OPENCLAW_PACKAGE_ROOT)])
        self.assertIn("PRODUCTION_PATH_FORBIDDEN", str(ctx.exception))

    def test_production_mode_rejects_package_root_when_authority_disabled(self):
        spec = self.exec_spec(stdout_path=Path(OPENCLAW_PACKAGE_ROOT) / "logs/out.log")
        with self.assertRaises(Exception) as ctx:
            validate_exact_exec_spec(spec, transaction_root=self.tx, allowed_roots=[self.tx, FIXTURE.parent], package_authority=self.authority(enabled=False))
        self.assertIn("PACKAGE_AUTHORITY_INVALID", str(ctx.exception))

    def test_production_mode_accepts_exact_authorized_package_root_only(self):
        spec = self.exec_spec(stdout_path=Path(OPENCLAW_PACKAGE_ROOT) / "logs/out.log")
        identity = validate_exact_exec_spec(spec, transaction_root=self.tx, allowed_roots=[self.tx, FIXTURE.parent], package_authority=self.authority(enabled=True))
        self.assertEqual(identity.sha256, sha256_file(FIXTURE))

    def test_production_mode_rejects_package_path_outside_exact_authorized_roots(self):
        spec = self.exec_spec(stdout_path=Path("/home/stickai/.npm-global/lib/node_modules/not-openclaw/logs/out.log"))
        with self.assertRaises(ProcessContractError) as ctx:
            validate_exact_exec_spec(spec, transaction_root=self.tx, allowed_roots=[self.tx, FIXTURE.parent], package_authority=self.authority(enabled=True))
        self.assertIn("PATH_OUTSIDE_ALLOWED_FIXTURE_ROOTS", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
