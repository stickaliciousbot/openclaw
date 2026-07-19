#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/compaction_gap_rehydrate.py"
SPEC = importlib.util.spec_from_file_location("compaction_gap_rehydrate", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CompactionGapRehydrateTests(unittest.TestCase):
    def build_fixture(self, root: Path) -> tuple[Path, Path, Path]:
        workspace = root / "workspace"
        project = workspace / "projects/durable-memory-architecture"
        ledger = root / "ledger/projects/stickbot-memory-ledger-v0"
        project.mkdir(parents=True)
        (project / "DURABLE_MEMORY_LEDGER_CONTEXT_CONTRACT_SURFACE_BROKER_LLD_AND_IMPLEMENTATION_PLAN.md").write_text(
            "# Systemic LLD\n\nM24 then M25 final freeze form Milestone 1; no successor starts automatically.\n",
            encoding="utf-8",
        )
        (project / "COMPACTION_GAP_RECOVERY_PROPOSAL.md").write_text(
            "# Proposal\n\nVectors generate candidates; sources provide authority.\n",
            encoding="utf-8",
        )
        (project / "LEDGER_BROKER_INTEGRATION_AND_BUILD_ORDER.md").write_text(
            "# Integration\n\nFinish Ledger, then build core, broker, and surfaces.\n",
            encoding="utf-8",
        )
        lesson = workspace / "memory/lessons-learned-durable-memory-ledger-contract-surface-broker-systemic-build-order-2026-07-17.md"
        lesson.parent.mkdir(parents=True)
        lesson.write_text(
            "# Lesson\n\nCore before integration; Runtime Broker before Surface Broker expansion.\n",
            encoding="utf-8",
        )
        (ledger / "docs").mkdir(parents=True)
        (ledger / "docs/PROJECT_REHYDRATOR.md").write_text(
            "# Ledger Rehydrator\n\nM24 is observation-only.\n",
            encoding="utf-8",
        )
        latest = ledger / "artifacts/rehydration/stickbot-memory-ledger/latest.json"
        latest.parent.mkdir(parents=True)
        latest.write_text(
            json.dumps(
                {
                    "schema": "ledger.fixture",
                    "status": "PASS",
                    "currentMilestone": "M23B",
                    "nextBoundary": "M24 observation",
                    "unapproved_field": "must not be copied into snapshot",
                }
            ),
            encoding="utf-8",
        )
        m24 = (
            ledger
            / "state/stickbot-memory-ledger/m24-sanitized-presentation-default-switch-observation"
            / "m24-observation-fixture/status.json"
        )
        m24.parent.mkdir(parents=True)
        m24.write_text(
            json.dumps(
                {
                    "schema": "stickbot.memory_ledger.m24.status.v1",
                    "status": "RUNNING",
                    "checkpoint": "t2h",
                    "boundary_observed": False,
                    "failed_gates": [],
                    "updated_utc": "2026-07-17T11:25:56Z",
                    "private_extra": "must not be copied into snapshot",
                }
            ),
            encoding="utf-8",
        )
        return workspace, project, ledger

    def test_builds_bounded_packet_with_ledger_and_m24(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace, project, ledger = self.build_fixture(Path(temp))
            manifest, markdown = MODULE.build_packet(
                workspace=workspace,
                project_root=project,
                ledger_root=ledger,
            )
            self.assertEqual(manifest["status"], "PASS")
            self.assertEqual(len(manifest["source_inventory"]), 7)
            self.assertEqual(manifest["ledger_snapshot"]["currentMilestone"], "M23B")
            self.assertNotIn("unapproved_field", manifest["ledger_snapshot"])
            self.assertEqual(manifest["m24_runtime_snapshot"]["checkpoint"], "t2h")
            self.assertNotIn("private_extra", manifest["m24_runtime_snapshot"])
            self.assertIn("M24 then M25 final freeze form Milestone 1", markdown)
            self.assertIn("Vectors generate candidates", markdown)
            self.assertIn("Finish Ledger", markdown)
            self.assertIn("Runtime Broker before Surface Broker", markdown)
            self.assertTrue(all(item["unchanged"] for item in manifest["source_mutation_checks"]))

    def test_missing_ledger_is_warn_not_false_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace, project, _ = self.build_fixture(Path(temp))
            missing = Path(temp) / "missing-ledger"
            manifest, markdown = MODULE.build_packet(
                workspace=workspace,
                project_root=project,
                ledger_root=missing,
            )
            self.assertEqual(manifest["status"], "WARN")
            self.assertIsNone(manifest["ledger_root"])
            self.assertIn("provide --ledger-root", markdown)

    def test_forbidden_credential_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace, project, ledger = self.build_fixture(Path(temp))
            (project / "COMPACTION_GAP_RECOVERY_PROPOSAL.md").write_text(
                '# Proposal\napi_key="abcdefghijklmnop123456"\n',
                encoding="utf-8",
            )
            manifest, _ = MODULE.build_packet(
                workspace=workspace,
                project_root=project,
                ledger_root=ledger,
            )
            self.assertEqual(manifest["status"], "FAIL")
            self.assertTrue(any("forbidden content" in item for item in manifest["errors"]))

    def test_output_path_guard(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp) / "workspace"
            allowed = workspace / "state/rehydration"
            denied = workspace / "projects/rehydration"
            self.assertTrue(MODULE.is_within(allowed, [workspace / "state"]))
            self.assertFalse(MODULE.is_within(denied, [workspace / "state"]))


if __name__ == "__main__":
    unittest.main()
