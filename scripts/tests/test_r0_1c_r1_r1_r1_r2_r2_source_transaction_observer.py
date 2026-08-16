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

from scripts import r0_1c_r1_r1_r1_r2_r2_source_transaction_observer as observer


class FakeDetachedProcess:
    pid = os.getpid()


class SourceTransactionObserverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="r0-1c-observer-test-"))
        self.addCleanup(shutil.rmtree, self.tmpdir, True)

    def write_json_new(self, path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")

    def approval_binding_case(self, name: str) -> tuple[Path, Path, Path, dict[str, object], dict[str, object]]:
        governed_root = self.tmpdir / (observer.RUN_PREFIX + f"-20260806T000000Z-{name[:32]}")
        obs_root = observer.observer_root_for(governed_root)
        binding_path = self.tmpdir / f"detached-launch-approval-binding-{name}.v1.json"
        contract = observer.build_contract(governed_root, obs_root, approval_binding_path=binding_path)
        binding = observer.approval_binding_document(
            governed_root,
            obs_root,
            contract=contract,
            platform_metadata={"provider": "native-approval-card", "record_state": "partial"},
        )
        return governed_root, obs_root, binding_path, contract, binding

    def assert_binding_rejected(self, name: str, mutate) -> None:
        governed_root, obs_root, binding_path, contract, binding = self.approval_binding_case(name)
        mutate(binding)
        self.write_json_new(binding_path, binding)
        with self.assertRaisesRegex(ValueError, observer.HOLD_APPROVAL_BINDING):
            observer.validate_approval_binding(binding_path, governed_root, obs_root, contract)

    def test_validate_approval_binding_accepts_explicit_partial_platform_metadata_only(self) -> None:
        governed_root, obs_root, binding_path, contract, binding = self.approval_binding_case("aaaavalidpartialbinding000000000000")
        self.write_json_new(binding_path, binding)
        result = observer.validate_approval_binding(binding_path, governed_root, obs_root, contract)
        self.assertEqual(result["status"], "PASS")

        governed_root, obs_root, binding_path, contract, binding = self.approval_binding_case("bbbbvalidrecoveryincomplete000000")
        binding["platform_metadata"]["record_state"] = "recovery-incomplete"
        self.write_json_new(binding_path, binding)
        result = observer.validate_approval_binding(binding_path, governed_root, obs_root, contract)
        self.assertEqual(result["status"], "PASS")

    def test_validate_approval_binding_rejects_partial_without_explicit_metadata_record_state(self) -> None:
        cases = {
            "ccccmetafalse00000000000000000000": lambda b: (b.update({"platform_metadata_supplied": False, "platform_metadata": None})),
            "ddddmetaflagmissing00000000000000": lambda b: b.pop("platform_metadata_supplied"),
            "eeeemetanull000000000000000000000": lambda b: b.update({"platform_metadata_supplied": True, "platform_metadata": None}),
            "ffffrecordmissing0000000000000000": lambda b: b["platform_metadata"].pop("record_state"),
            "ggggrecordmalformed00000000000000": lambda b: b["platform_metadata"].update({"record_state": "Partial"}),
            "hhhhalLOWEDfalse0000000000000000": lambda b: b["platform_metadata_policy"].update({"partial_platform_metadata_allowed": False}),
            "iiiifabricatednativeid0000000000": lambda b: b["platform_metadata"].update({"approval_id": "native-approval-123"}),
            "jjjjownerboolnoinfer000000000000": lambda b: b.update({"platform_metadata_supplied": False, "platform_metadata": None, "owner_approved": True}),
        }
        for name, mutate in cases.items():
            with self.subTest(name=name):
                self.assert_binding_rejected(name, mutate)

    def test_validate_approval_binding_rejects_stale_wrong_or_mutated_binding_fields(self) -> None:
        cases = {
            "kkkkwrongroot0000000000000000000": lambda b: b.update({"governed_root": str(self.tmpdir / "wrong-root")}),
            "llllpreviewhash00000000000000000": lambda b: b.update({"package_preview_sha256": "0" * 64}),
            "mmmmcommandargv00000000000000000": lambda b: b["launch_argv"].append("--mutated"),
            "nnnnobserversha00000000000000000": lambda b: b.update({"observer_script_sha256": "0" * 64}),
            "oooostagebsha000000000000000000": lambda b: b.update({"stage_b_runner_sha256": "0" * 64}),
            "ppppexpired00000000000000000000": lambda b: b.update({"expires_utc": "2000-01-01T00:00:00Z"}),
            "qqqqbadtimeorder000000000000000": lambda b: b.update({"created_utc": "2099-01-02T00:00:00Z", "expires_utc": "2099-01-01T00:00:00Z"}),
            "rrrrsourcepackagemutate000000000": lambda b: b["source_registry_shas"].update({"registry_sha256": "0" * 64}),
        }
        for name, mutate in cases.items():
            with self.subTest(name=name):
                self.assert_binding_rejected(name, mutate)

    def test_preview_exposes_one_launch_transaction_and_all_four_phases(self) -> None:
        doc = observer.approval_preview_document()
        self.assertEqual(doc["status"], "PREVIEW_ONLY_NOT_EXECUTED")
        self.assertEqual(doc["command_count_decision"], "one launch transaction containing four named phases")
        self.assertEqual(doc["approval_action_count"], 1)
        self.assertEqual(doc["owned_phase_count"], 4)
        self.assertFalse(doc["hidden_fifth_action"])
        self.assertIn("replaced by one detached source-only observer launch", doc["replacement_explanation"])
        self.assertIn("does not hide a fifth Stage-B execution command", doc["replacement_explanation"])
        self.assertEqual([p["label"] for p in doc["owned_phases"]], ["A", "B", "C", "D"])
        self.assertEqual([p["name"] for p in doc["owned_phases"]], ["A-prepare", "B-validate", "C-matrices", "D-seal"])
        self.assertEqual(doc["launch_transaction"]["exact_argv"][:4], [observer.PY312, "-B", str(observer.OBSERVER_SCRIPT), "launch"])
        self.assertIn("READ_ONLY_COMPLETION_CHECK_NOT_STAGE_B_ACTION", doc["independent_read_only_completion_check_contract"]["label"])
        self.assertEqual(doc["predecessor_package_status"]["future_approval_package_superseded_by_v4"], True)
        self.assertEqual(doc["predecessor_package_status"]["old_exactly_four_direct_exec_package_governing_future_approval"], False)

    def test_launch_receipts_exist_before_detach_and_child_argv_is_exact(self) -> None:
        missing_root = self.tmpdir / (observer.RUN_PREFIX + "-20260806T000000Z-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
        with self.assertRaisesRegex(ValueError, observer.HOLD_APPROVAL_BINDING):
            observer.launch(missing_root)
        self.assertFalse((observer.observer_root_for(missing_root) / "observer-child.stdout.log").exists())

        governed_root = self.tmpdir / (observer.RUN_PREFIX + "-20260806T000000Z-0123456789abcdef0123456789abcdef")
        obs_root = observer.observer_root_for(governed_root)
        binding_path = self.tmpdir / "detached-launch-approval-binding.v1.json"
        contract = observer.build_contract(governed_root, obs_root, approval_binding_path=binding_path)
        binding = observer.approval_binding_document(governed_root, obs_root, contract=contract, platform_metadata={"provider": "native-approval-card", "record_state": "partial"})
        self.write_json_new(binding_path, binding)
        contract_seen: list[list[str]] = []

        def fake_popen(argv, **kwargs):
            contract_path = obs_root / "observer-contract.json"
            pre_path = obs_root / "launch-receipt.pre-child.json"
            self.assertTrue(contract_path.is_file(), "contract must be written before child spawn")
            self.assertTrue(pre_path.is_file(), "pre-child receipt must be written before child spawn")
            self.assertIs(kwargs.get("shell"), None, "shell must not be enabled")
            self.assertTrue(kwargs.get("start_new_session"), "detached child must start a new session")
            self.assertEqual(kwargs.get("cwd"), str(observer.WORKSPACE))
            self.assertIs(kwargs.get("stdin"), subprocess.DEVNULL)
            contract_seen.append(list(argv))
            return FakeDetachedProcess()

        with mock.patch.object(observer.subprocess, "Popen", side_effect=fake_popen):
            result = observer.launch(governed_root, binding_path)
        self.assertEqual(result["status"], observer.DETACHED_LAUNCHED)
        expected = [observer.PY312, "-B", str(observer.OBSERVER_SCRIPT), "_child", "--contract", str(obs_root / "observer-contract.json")]
        self.assertEqual(contract_seen, [expected])
        self.assertTrue((obs_root / "detached-launch-approval-binding.validation.json").is_file())
        self.assertTrue((obs_root / "launch-receipt.post-child.json").is_file())
        self.assertTrue((obs_root / "observer-child.stdout.log").is_file())
        self.assertTrue((obs_root / "observer-child.stderr.log").is_file())
        self.assertFalse(governed_root.exists(), "launch must not create the governed Stage-B root; phase A owns it")

        mismatch_root = self.tmpdir / (observer.RUN_PREFIX + "-20260806T000000Z-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")
        with self.assertRaisesRegex(ValueError, observer.HOLD_APPROVAL_BINDING):
            observer.launch(mismatch_root, binding_path)
        stale_root = self.tmpdir / (observer.RUN_PREFIX + "-20260806T000000Z-cccccccccccccccccccccccccccccccc")
        stale_obs = observer.observer_root_for(stale_root)
        stale_binding_path = self.tmpdir / "detached-launch-approval-binding-stale.v1.json"
        stale_contract = observer.build_contract(stale_root, stale_obs, approval_binding_path=stale_binding_path)
        stale = observer.approval_binding_document(
            stale_root,
            stale_obs,
            contract=stale_contract,
            platform_metadata={"provider": "native-approval-card", "record_state": "partial"},
            expires_utc="2000-01-01T00:00:00Z",
        )
        self.write_json_new(stale_binding_path, stale)
        with self.assertRaisesRegex(ValueError, observer.HOLD_APPROVAL_BINDING):
            observer.launch(stale_root, stale_binding_path)

    def test_child_runs_exact_argv_preserves_failure_and_does_not_retry_or_continue(self) -> None:
        obs_root = self.tmpdir / "observer-root"
        obs_root.mkdir(mode=0o700)
        (obs_root / "phase-receipts").mkdir(mode=0o700)
        (obs_root / "progress").mkdir(mode=0o700)
        marker = self.tmpdir / "phase-b-marker.txt"
        phases = [
            {
                "label": "A",
                "name": "A-fails",
                "absolute_executable": sys.executable,
                "exact_argv": [sys.executable, "-c", "import sys; print('phase-a'); sys.exit(7)"],
                "cwd": str(self.tmpdir),
                "timeout_seconds": 10.0,
                "expected_exit_code": 0,
                "failure_terminal": "HOLD_SOURCE_TRANSACTION_OBSERVER_PHASE_A_FAILED_PRESERVED_NO_RETRY",
            },
            {
                "label": "B",
                "name": "B-must-not-run",
                "absolute_executable": sys.executable,
                "exact_argv": [sys.executable, "-c", f"from pathlib import Path; Path({str(marker)!r}).write_text('bad')"],
                "cwd": str(self.tmpdir),
                "timeout_seconds": 10.0,
                "expected_exit_code": 0,
                "failure_terminal": "HOLD_SOURCE_TRANSACTION_OBSERVER_PHASE_B_FAILED_PRESERVED_NO_RETRY",
            },
        ]
        contract = observer.build_contract(str(self.tmpdir / "governed-root"), str(obs_root))
        contract["owned_phases"] = phases
        contract["execution_model"]["bounded_heartbeat_seconds"] = 0.05
        contract["execution_model"]["total_watchdog_seconds"] = 20.0
        contract_path = obs_root / "observer-contract.json"
        self.write_json_new(contract_path, contract)
        result = observer.run_child_contract(contract_path)
        self.assertEqual(result["status"], "HOLD_SOURCE_TRANSACTION_OBSERVER_PHASE_A_FAILED_PRESERVED_NO_RETRY")
        self.assertEqual(result["completed_phases"], [])
        self.assertEqual(len(result["phase_receipts"]), 1)
        self.assertEqual(result["phase_receipts"][0]["retry_attempts"], 0)
        self.assertTrue(result["preserved_on_failure"])
        self.assertFalse(marker.exists(), "phase B must not run after phase A failure")
        self.assertTrue((obs_root / "phase-receipts" / "A.stdout.log").is_file())
        self.assertTrue((obs_root / "phase-receipts" / "A.stderr.log").is_file())
        self.assertTrue((obs_root / "final-state.json").is_file())

    def test_source_has_no_live_harness_or_provider_alert_invocation(self) -> None:
        source = observer.OBSERVER_SCRIPT.read_text(encoding="utf-8")
        tree = compile(source, str(observer.OBSERVER_SCRIPT), "exec", dont_inherit=True)
        self.assertIsNotNone(tree)
        doc = observer.approval_preview_document()
        executable_payload = json.dumps({
            "launch": doc["launch_transaction"]["exact_argv"],
            "phases": [phase["exact_argv"] for phase in doc["owned_phases"]],
            "check": doc["independent_read_only_completion_check_contract"]["exact_argv"],
        }, sort_keys=True)
        forbidden_exec_tokens = [
            "long_running_cron_observer_harness.py",
            "long_running_observer_telegram_alert.py",
            "critical_apply_independent_completion_checker.py",
        ]
        for token in forbidden_exec_tokens:
            self.assertNotIn(token, executable_payload)
        self.assertNotIn("--" + "no-alert-watch", source)
        self.assertEqual(doc["no_external_effect_declaration"], observer.NO_EXTERNAL_EFFECTS)
        self.assertFalse(any(doc["no_external_effect_declaration"].values()))


if __name__ == "__main__":
    unittest.main()
