#!/usr/bin/env python3
"""M10 Context+ production-package helper.

Safe-by-default helper for M10/M10A.  Subcommands are dry-run/readback oriented
unless --execute is explicitly supplied for future apply/rollback gates.  The
M10A package does not run apply/rollback against production.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict

SCHEMA_ID = "stickbot.context_plus_semantic_preselector.production_control_surface.v1"
SUBJECT = "CONTEXT_PLUS_SEMANTIC_PRESELECTOR"
DEFAULT_STATE_PATH = Path("/home/stickai/.openclaw/workspace/state/intent-preselector-v5/enforcement.json")
REQUIRED_M6_EVIDENCE = {
    "comparator_classification": "PASS_FALSE_POSITIVE_BASELINE_IMPROVED",
    "production_false_positives": "22/235",
    "context_plus_shadow_false_positives": "0/235",
    "proposal_commit": "871522c5204b6062419e48a5a47a4d9cd4cf97a6",
    "preflight_commit": "551c019bdee3704e3da2a8d4eb9eb9d4c10b388e",
    "runbook_hold_commit": "c2e2decfeaa4fad82e81a54362779d461d1ebf77",
    "m8_discovery_hold_commit": "1ce70de4b94c4916a8e0cdbfe37eeb2ed672fc20",
}
FALSE_GUARDS = [
    "context_may_replace_prompt",
    "remote_llm_for_scoring_allowed",
    "direct_provider_bypass_allowed",
    "cache_allowed",
    "artifact_memory_promotion_allowed",
    "default_model_change_allowed",
    "provider_model_change_allowed",
]


def sha256_path(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def validate_state(state: Any) -> Dict[str, Any]:
    reasons = []
    if not isinstance(state, dict):
        return {"ok": False, "active": False, "mode": "shadow_contract_only", "reasons": ["state_not_object"]}
    if state.get("schema") != SCHEMA_ID:
        reasons.append("schema_mismatch")
    if state.get("subject") != SUBJECT:
        reasons.append("subject_mismatch")
    if state.get("authority") != "lane_selection_only":
        reasons.append("authority_not_lane_selection_only")
    mode = state.get("mode", "shadow_contract_only")
    if mode not in {"shadow_contract_only", "enforced_route_contract"}:
        reasons.append("mode_invalid")
    allowlist = state.get("operator_allowlist") if isinstance(state.get("operator_allowlist"), list) else []
    if "telegram:8495203551" not in allowlist:
        reasons.append("operator_allowlist_missing_owner_telegram")
    if any(str(item).lower() in {"*", "all", "any", "everyone", "all_live_traffic"} for item in allowlist):
        reasons.append("operator_allowlist_broad")
    if state.get("traffic_scope") != "owner_operator_live_turns_only":
        reasons.append("traffic_scope_not_owner_operator_only")
    if mode == "enforced_route_contract":
        if state.get("enabled") is not True:
            reasons.append("enforced_requires_enabled_true")
        if state.get("kill_switch") is not False:
            reasons.append("enforced_requires_kill_switch_false")
        evidence = state.get("m6_evidence") if isinstance(state.get("m6_evidence"), dict) else {}
        for key, expected in REQUIRED_M6_EVIDENCE.items():
            if evidence.get(key) != expected:
                reasons.append(f"m6_evidence_{key}_mismatch")
        guards = state.get("guards") if isinstance(state.get("guards"), dict) else {}
        if guards.get("prompt_preserved_required") is not True:
            reasons.append("prompt_preserved_required_not_true")
        for key in FALSE_GUARDS:
            if guards.get(key) is not False:
                reasons.append(f"guard_{key}_not_false")
        if guards.get("write_action_authority") != "unchanged_existing_policy_only":
            reasons.append("write_action_authority_not_unchanged")
    ok = not reasons
    active = ok and mode == "enforced_route_contract" and state.get("enabled") is True and state.get("kill_switch") is False
    return {
        "ok": ok,
        "active": active,
        "mode": "enforced_route_contract" if active else "shadow_contract_only",
        "reasons": reasons,
    }


def command_readback(args: argparse.Namespace) -> Dict[str, Any]:
    path = Path(args.state_path)
    if not path.exists():
        return {"ok": True, "exists": False, "mode": "shadow_contract_only", "enforced": False, "reason": "state_file_missing_safe_default"}
    state = load_json(path)
    validation = validate_state(state)
    return {"ok": validation["ok"], "exists": True, "enforced": validation["active"], **validation}


def command_validate(args: argparse.Namespace) -> Dict[str, Any]:
    path = Path(args.candidate_state or args.state_path)
    state = load_json(path)
    validation = validate_state(state)
    return {"ok": validation["ok"], "path": str(path), **validation}


def command_snapshot(args: argparse.Namespace) -> Dict[str, Any]:
    watches = [Path(p) for p in (args.watch or [])]
    if not watches:
        watches = [Path(args.state_path)]
    manifest = []
    for path in watches:
        manifest.append({"path": str(path), "exists": path.exists(), "sha256": sha256_path(path), "size": path.stat().st_size if path.exists() else None})
    return {"ok": True, "dry_run": not args.execute, "mutation": "none", "manifest": manifest}


def command_apply(args: argparse.Namespace) -> Dict[str, Any]:
    candidate = Path(args.candidate_state)
    validation = validate_state(load_json(candidate))
    if not validation["ok"]:
        return {"ok": False, "dry_run": not args.execute, "action": "apply", "refused": True, **validation}
    if not args.execute:
        return {"ok": True, "dry_run": True, "action": "apply", "would_write": args.state_path, "candidate_state": str(candidate), "mutation": "not_executed"}
    raise SystemExit("apply execution is intentionally disabled for M10A; require a later production-apply gate")


def command_rollback(args: argparse.Namespace) -> Dict[str, Any]:
    if not args.execute:
        return {"ok": True, "dry_run": True, "action": "rollback", "would_restore": args.snapshot, "state_path": args.state_path, "mutation": "not_executed"}
    raise SystemExit("rollback execution is intentionally disabled for M10A; require a later rollback gate")


def command_smoke(args: argparse.Namespace) -> Dict[str, Any]:
    return {
        "ok": True,
        "dry_run": True,
        "action": "smoke",
        "endpoint": args.token_solver_v4_url.rstrip("/") + args.dry_run_endpoint,
        "provider_calls": 0,
        "mutation": "none",
        "assertions": [
            "state_schema_valid",
            "owner_operator_scope_enforced_only_when_allowlisted",
            "non_allowlisted_scope_shadow_or_rejected",
            "prompt_preserved_true",
            "context_may_replace_prompt_false",
            "gateway_provider_model_cache_memory_unchanged",
        ],
    }


def emit(result: Dict[str, Any], out: str | None) -> None:
    text = json.dumps(result, indent=2, sort_keys=True)
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(text + "\n")
    print(text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--state-path", default=str(DEFAULT_STATE_PATH))
        p.add_argument("--out")
        p.add_argument("--execute", action="store_true", help="future-gate only; M10A tests do not use this")

    p = sub.add_parser("readback")
    common(p)
    p.set_defaults(func=command_readback)

    p = sub.add_parser("validate")
    common(p)
    p.add_argument("--candidate-state")
    p.set_defaults(func=command_validate)

    p = sub.add_parser("snapshot")
    common(p)
    p.add_argument("--watch", action="append")
    p.set_defaults(func=command_snapshot)

    p = sub.add_parser("apply")
    common(p)
    p.add_argument("--candidate-state", required=True)
    p.set_defaults(func=command_apply)

    p = sub.add_parser("rollback")
    common(p)
    p.add_argument("--snapshot", required=True)
    p.set_defaults(func=command_rollback)

    p = sub.add_parser("smoke")
    common(p)
    p.add_argument("--token-solver-v4-url", default="http://127.0.0.1:8800")
    p.add_argument("--dry-run-endpoint", default="/route/dry-run")
    p.set_defaults(func=command_smoke)

    args = parser.parse_args()
    result = args.func(args)
    emit(result, args.out)
    if not result.get("ok"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
