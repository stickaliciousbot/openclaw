#!/usr/bin/env python3

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "DURABLE_MEMORY_LEDGER_CONTEXT_CONTRACT_SURFACE_BROKER_LLD_AND_IMPLEMENTATION_PLAN.md"


class SystemicLldPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = PLAN.read_text(encoding="utf-8")

    def test_seven_milestones_are_present_and_ordered(self) -> None:
        positions = []
        for number in range(1, 8):
            match = re.search(rf"^# Milestone {number} — ", self.text, flags=re.MULTILINE)
            self.assertIsNotNone(match, f"missing Milestone {number}")
            positions.append(match.start())
        self.assertEqual(positions, sorted(positions))
        self.assertIn("Milestone 1 — Resume M24", self.text)

    def test_global_hard_gates_are_complete(self) -> None:
        for number in range(1, 21):
            self.assertIn(f"HG-{number:02d}", self.text)
        self.assertIn("No silent successor", self.text)
        self.assertIn("No summary, model prose, graph score, vector score", self.text)

    def test_health_checks_are_complete(self) -> None:
        for number in range(1, 17):
            self.assertIn(f"HC-{number:02d}", self.text)
        for state in ("GREEN", "YELLOW", "RED"):
            self.assertIn(f"**{state}:**", self.text)

    def test_key_authority_and_surface_boundaries(self) -> None:
        required = (
            "Runtime Service Broker",
            "Universal Model Contract",
            "Surface Service Broker",
            "Context Bridge remains a sanitized operational projection",
            "No model/provider directly calls the reconstruction service without an RSB grant",
            "read-only Context Reconstruction",
            "no recall-time writes",
            "duplicate or unexpected sends zero",
            "loopback is default",
            "RFC 8785",
            "idempotency_key",
            "monotonic time controls deadlines",
            "Bridge-specific keyed/HMAC aliases",
            "TTL no greater than 24 hours",
            "Submilestone 1A",
            "Submilestone 1B",
            "must not create an `SSB-equivalent` reusable shim",
            "HOLD_NO_ELIGIBLE_OWNER_DIRECT_TRAFFIC",
            "Submilestone 1B — Ledger M25 final completion/freeze",
            "M24 HOLD/ABORT blocks M25",
            "only M25 PASS formally completes Ledger v0.1",
        )
        for phrase in required:
            self.assertIn(phrase, self.text)

    def test_m24_terminals_and_overall_terminal_present(self) -> None:
        terminals = (
            "MEMORY_LEDGER_V0_1_M24_SANITIZED_PRESENTATION_DEFAULT_SWITCH_OBSERVATION_PASS_NO_AUTHORITY_PROMOTION",
            "MEMORY_LEDGER_V0_1_M24_HOLD_NO_SCHEDULED_PRESENTATION_BOUNDARY_OBSERVED",
            "MEMORY_LEDGER_V0_1_M25_FINAL_COMPLETION_FREEZE_PASS_NO_AUTHORITY_PROMOTION",
            "MEMORY_LEDGER_V0_1_M25_HOLD_FINAL_COMPLETION_GATES_INCOMPLETE",
            "DURABLE_MEMORY_SYSTEM_M2_CONTRACT_ALIGNMENT_PASS_NO_RUNTIME_INTEGRATION",
            "DURABLE_MEMORY_SYSTEM_M3_OFFLINE_CORE_PASS_NO_RUNTIME_INTEGRATION",
            "DURABLE_MEMORY_SYSTEM_M4_SHADOW_RECONSTRUCTION_PASS_NO_PROMPT_INJECTION",
            "DURABLE_MEMORY_SYSTEM_M5_RUNTIME_SERVICE_BROKER_READONLY_PASS_NO_SURFACE_EXPANSION",
            "DURABLE_MEMORY_SYSTEM_M6_OWNER_DIRECT_COMMERCIAL_CANARY_PASS_NO_AUTHORITY_PROMOTION",
            "DURABLE_MEMORY_LEDGER_CONTEXT_CONTRACT_SURFACE_BROKER_V1_PASS_BOUNDED_PRODUCTION",
        )
        for terminal in terminals:
            self.assertIn(terminal, self.text)

    def test_no_unresolved_template_markers(self) -> None:
        for marker in ("TBD", "TODO", "CHANGEME", "<INSERT"):
            self.assertNotIn(marker, self.text)


if __name__ == "__main__":
    unittest.main()
