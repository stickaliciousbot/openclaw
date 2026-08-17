#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tarfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from m4_test_support import cleanup, make_tmp
from critical_apply_atomic_io import sha256_file
from critical_apply_observer_runner import DEFAULT_REQUIRED_AUTHORIZATION, execute_package_apply, prepare_transaction
from critical_apply_package_authority import make_package_apply_authority, package_transaction_spec_template
from critical_apply_contracts import write_json
from critical_apply_plugins.openclaw_npm_package import process_references_path


class ObserverRunnerPackageApplyTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.tx, self.locks, self.shadow = make_tmp("m8-r19-observer-runner-")
        self.pkg_root = self.tmp / "npm-global" / "lib" / "node_modules" / "openclaw"
        self.bin = self.tmp / "npm-global" / "bin" / "openclaw"
        self.pkg_root.mkdir(parents=True)
        self.bin.parent.mkdir(parents=True)
        write_json(self.pkg_root / "package.json", {"name": "openclaw", "version": "old"})
        (self.pkg_root / "openclaw.mjs").write_text("#!/usr/bin/env node\nconsole.log('old')\n", encoding="utf-8")
        (self.pkg_root / "dist").mkdir()
        (self.pkg_root / "dist" / "index.js").write_text("console.log('old dist')\n", encoding="utf-8")
        (self.pkg_root / "node_modules" / "https-proxy-agent").mkdir(parents=True)
        write_json(self.pkg_root / "node_modules" / "https-proxy-agent" / "package.json", {"name": "https-proxy-agent", "version": "fixture"})
        self.bin.symlink_to("../lib/node_modules/openclaw/openclaw.mjs")
        self.artifact = self.tmp / "openclaw-2026.5.7.tgz"
        self._make_artifact(self.artifact)
        self.artifact_sha = sha256_file(self.artifact)
        self.envelope = self.tmp / "enabled-envelope.json"
        self.review = self.tmp / "review-plan.json"
        self._write_envelope_and_review()

    def tearDown(self):
        cleanup(self.tmp)

    def _make_artifact(self, path: Path) -> None:
        build = self.tmp / "build" / "package"
        (build / "dist" / "extensions" / "speech-core").mkdir(parents=True)
        write_json(build / "package.json", {"name": "openclaw", "version": "2026.5.7"})
        (build / "openclaw.mjs").write_text("#!/usr/bin/env node\nconsole.log('candidate')\n", encoding="utf-8")
        (build / "dist" / "index.js").write_text("console.log('candidate dist')\n", encoding="utf-8")
        (build / "dist" / "extensions" / "speech-core" / "runtime-api.js").write_text("export const ok = true;\n", encoding="utf-8")
        with tarfile.open(path, "w:gz") as tf:
            for item in sorted(build.rglob("*")):
                tf.add(item, arcname="package/" + str(item.relative_to(build)))

    def _write_envelope_and_review(self) -> None:
        spec = package_transaction_spec_template(
            package_artifact_sha256=self.artifact_sha,
            source_package_path=str(self.artifact),
            target_roots=[str(self.pkg_root), str(self.bin)],
            restore_point_id="fixture-restore",
            restore_manifest_sha256="b" * 64,
            postcheck_sha256="c" * 64,
            rollback_plan_sha256="d" * 64,
        )
        auth = make_package_apply_authority(
            transaction_id="critical-apply-package-fixture-20260817T032000Z-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            package_spec=spec,
            authority_enabled=True,
            maintenance_lock_path=str(self.locks / "package-apply.lock"),
            independent_watcher_registration_path=str(self.tx / "watcher.json"),
            restore_point_id="fixture-restore",
            restore_manifest_sha256="b" * 64,
            owner="test-owner",
        )
        envelope = {
            "schema": "critical_apply.cah_j1.fixture.enabled_apply_envelope.v1",
            "status": "FROZEN_ENABLED_NOT_EXECUTED",
            "package_apply_authority": auth,
            "package_apply_authority_sha256": "e" * 64,
            "package_transaction_spec_sha256": auth["package_transaction_spec_sha256"],
        }
        write_json(self.envelope, envelope)
        write_json(self.review, {"schema": "critical_apply.cah_j1.fixture.review_plan.v1", "status": "FROZEN_REVIEW_ONLY_NOT_EXECUTABLE_FOR_APPLY"})

    def test_prepare_writes_review_only_transaction_without_mutation(self):
        prepared = prepare_transaction(transaction_root=self.tx, enabled_envelope=self.envelope, review_plan=self.review, name="fixture")
        self.assertEqual(prepared["phase"], "PREPARED_REVIEW_ONLY")
        self.assertFalse(prepared["live_apply_executed"])
        self.assertEqual(json.loads((self.pkg_root / "package.json").read_text())["version"], "old")
        self.assertTrue((self.tx / "transaction.json").exists())

    def test_execute_without_flag_holds_approved_not_started(self):
        status = execute_package_apply(
            transaction_root=self.tx,
            enabled_envelope=self.envelope,
            review_plan=self.review,
            owner_authorization_phrase=DEFAULT_REQUIRED_AUTHORIZATION,
            allowed_root=[str(self.tmp)],
            execute_live_package_apply=False,
        )
        self.assertEqual(status["terminal_status"], "APPROVED_NOT_STARTED")
        self.assertEqual(json.loads((self.pkg_root / "package.json").read_text())["version"], "old")

    def test_execute_fixture_package_apply_under_temp_allowed_root(self):
        status = execute_package_apply(
            transaction_root=self.tx,
            enabled_envelope=self.envelope,
            review_plan=self.review,
            owner_authorization_phrase=DEFAULT_REQUIRED_AUTHORIZATION,
            allowed_root=[str(self.tmp)],
            execute_live_package_apply=True,
            timeout_seconds=10,
        )
        self.assertEqual(status["terminal_status"], "PASS_PACKAGE_INSTALLED_HOLD_FOR_SEPARATE_RESTART", status)
        self.assertEqual(json.loads((self.pkg_root / "package.json").read_text())["version"], "2026.5.7")
        self.assertTrue((self.tx / "receipts" / "maintenance-lock-acquired.json").exists())
        self.assertTrue((self.tx / "receipts" / "maintenance-lock-released.json").exists())
        self.assertTrue((self.tx / "receipts" / "apply-start.json").exists())
        self.assertTrue((self.tx / "receipts" / "apply-exit.json").exists())
        self.assertTrue((self.tx / "receipts" / "postcheck.json").exists())
        self.assertTrue((self.pkg_root / "node_modules" / "https-proxy-agent" / "package.json").exists())
        self.assertEqual(status["gateway_restart_actions"], 0)
        self.assertEqual(status["provider_or_live_smoke_calls"], 0)

    def test_execute_rejects_target_outside_allowed_root(self):
        status = execute_package_apply(
            transaction_root=self.tx,
            enabled_envelope=self.envelope,
            review_plan=self.review,
            owner_authorization_phrase=DEFAULT_REQUIRED_AUTHORIZATION,
            allowed_root=[str(self.tmp / "not-parent")],
            execute_live_package_apply=True,
            timeout_seconds=10,
        )
        self.assertEqual(status["terminal_status"], "FAIL_SAFE_NO_MUTATION")
        self.assertIn("target_not_allowed", status["error"])
        self.assertEqual(json.loads((self.pkg_root / "package.json").read_text())["version"], "old")

    def test_proc_fd_permission_denied_does_not_raise(self):
        refs = process_references_path(1, self.pkg_root)
        self.assertIn("referenced", refs)
        self.assertIn("fd", refs)


if __name__ == "__main__":
    unittest.main()
