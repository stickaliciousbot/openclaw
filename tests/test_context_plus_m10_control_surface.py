#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "context_plus_preselector_m10_production_package.py"


def run_cmd(*args: str) -> dict:
    proc = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=ROOT, text=True, capture_output=True, check=True)
    return json.loads(proc.stdout)


def valid_state() -> dict:
    return {
        "schema": "stickbot.context_plus_semantic_preselector.production_control_surface.v1",
        "subject": "CONTEXT_PLUS_SEMANTIC_PRESELECTOR",
        "enabled": True,
        "mode": "enforced_route_contract",
        "authority": "lane_selection_only",
        "traffic_scope": "owner_operator_live_turns_only",
        "operator_allowlist": ["telegram:8495203551"],
        "kill_switch": False,
        "m6_evidence": {
            "comparator_classification": "PASS_FALSE_POSITIVE_BASELINE_IMPROVED",
            "production_false_positives": "22/235",
            "context_plus_shadow_false_positives": "0/235",
            "proposal_commit": "871522c5204b6062419e48a5a47a4d9cd4cf97a6",
            "preflight_commit": "551c019bdee3704e3da2a8d4eb9eb9d4c10b388e",
            "runbook_hold_commit": "c2e2decfeaa4fad82e81a54362779d461d1ebf77",
            "m8_discovery_hold_commit": "1ce70de4b94c4916a8e0cdbfe37eeb2ed672fc20",
        },
        "guards": {
            "prompt_preserved_required": True,
            "context_may_replace_prompt": False,
            "remote_llm_for_scoring_allowed": False,
            "direct_provider_bypass_allowed": False,
            "cache_allowed": False,
            "artifact_memory_promotion_allowed": False,
            "default_model_change_allowed": False,
            "provider_model_change_allowed": False,
            "write_action_authority": "unchanged_existing_policy_only",
        },
    }


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        missing = tmp / "missing.json"
        readback = run_cmd("readback", "--state-path", str(missing))
        assert readback["ok"] is True
        assert readback["exists"] is False
        assert readback["enforced"] is False
        assert readback["mode"] == "shadow_contract_only"

        candidate = tmp / "candidate.json"
        candidate.write_text(json.dumps(valid_state(), indent=2))
        validation = run_cmd("validate", "--candidate-state", str(candidate))
        assert validation["ok"] is True
        assert validation["active"] is True

        apply_shape = run_cmd("apply", "--candidate-state", str(candidate), "--state-path", str(tmp / "enforcement.json"))
        assert apply_shape["ok"] is True
        assert apply_shape["dry_run"] is True
        assert apply_shape["mutation"] == "not_executed"

        rollback_shape = run_cmd("rollback", "--state-path", str(tmp / "enforcement.json"), "--snapshot", str(missing))
        assert rollback_shape["ok"] is True
        assert rollback_shape["dry_run"] is True
        assert rollback_shape["mutation"] == "not_executed"

        smoke_shape = run_cmd("smoke", "--token-solver-v4-url", "http://127.0.0.1:8800")
        assert smoke_shape["ok"] is True
        assert smoke_shape["dry_run"] is True
        assert smoke_shape["provider_calls"] == 0
        assert smoke_shape["mutation"] == "none"

    print(json.dumps({"ok": True, "name": "context_plus_m10_control_surface", "assertions": 18, "provider_calls": 0}))


if __name__ == "__main__":
    main()
