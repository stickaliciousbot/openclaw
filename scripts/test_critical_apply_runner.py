#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from critical_apply_contracts import (  # noqa: E402
    CriticalApplyTerminal,
    argv_sha256,
    validate_argv_exact,
    validate_no_foreground_apply_text,
    validate_restore_point_fresh,
    validate_transaction_id,
)

RUNNER = SCRIPTS / "critical_apply_observer_runner.py"


class ContractTests(unittest.TestCase):
    def test_transaction_id_validation(self):
        self.assertTrue(validate_transaction_id("critical-apply-openclaw-npm-package-20260730T010203Z-abcdef12").ok)
        self.assertFalse(validate_transaction_id("bad-id").ok)

    def test_argv_hash_and_exact_validation(self):
        argv = ["/usr/bin/npm", "install", "-g", "--offline", "pkg.tgz"]
        self.assertEqual(argv_sha256(argv), argv_sha256(list(argv)))
        self.assertTrue(validate_argv_exact(argv, argv).ok)
        self.assertFalse(validate_argv_exact(argv, argv + ["extra"]).ok)

    def test_restore_point_freshness(self):
        self.assertTrue(validate_restore_point_fresh(1000, 3600, now_epoch=1200).ok)
        self.assertFalse(validate_restore_point_fresh(1000, 3600, now_epoch=5000).ok)

    def test_foreground_apply_static_guard(self):
        self.assertTrue(validate_no_foreground_apply_text("observer transaction only").ok)
        self.assertFalse(validate_no_foreground_apply_text("exec('/usr/bin/npm install -g foo')").ok)


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="critical-apply-test-"))
        self.root = self.tmp / "tx"
        self.lock = self.tmp / "critical-apply.lock"
        self.spec = self.tmp / "spec.json"
        self.spec.write_text(
            json.dumps(
                {
                    "name": "openclaw-npm-package",
                    "plugin": "openclaw_npm_package",
                    "scope": {"name": "openclaw-npm-package", "critical": True},
                    "apply_argv": ["/usr/bin/npm", "install", "-g", "--offline", "/tmp/openclaw.tgz"],
                    "allowed_mutations": ["transaction_evidence"],
                    "forbidden": ["gateway_restart", "cron_mutation", "provider_call"],
                    "restore_policy": {"max_age_seconds": 3600, "create_if_missing": True},
                }
            )
        )

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_runner(self, *args):
        return subprocess.run(
            [sys.executable, str(RUNNER), "--root", str(self.root), "--lock", str(self.lock), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_prepare_status_validate_and_execute_refusal(self):
        cp = self.run_runner("prepare", "--spec", str(self.spec))
        self.assertEqual(cp.returncode, 0, cp.stderr)
        out = json.loads(cp.stdout)
        txid = out["transaction_id"]
        txroot = self.root / txid
        self.assertTrue((txroot / "transaction.json").is_file())
        self.assertTrue((txroot / "approval-boundary.json").is_file())
        self.assertTrue((txroot / "final-report.json").is_file())
        final = json.loads((txroot / "final-report.json").read_text())
        self.assertEqual(final["terminal"], CriticalApplyTerminal.NO_APPROVAL.value)
        cp = self.run_runner("status", "--transaction", txid)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertIn("approval-boundary.json", json.loads(cp.stdout)["files"])
        cp = self.run_runner("validate", "--transaction", txid)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertTrue(json.loads(cp.stdout)["all_pass"])
        cp = self.run_runner("execute", "--transaction", txid)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        refusal = json.loads(cp.stdout)
        self.assertEqual(refusal["schema"], "critical_apply.execute_refusal.v1")
        self.assertFalse(refusal["production_mutation_performed"])
        self.assertTrue((txroot / "execute-refusal.json").is_file())


if __name__ == "__main__":
    unittest.main()
