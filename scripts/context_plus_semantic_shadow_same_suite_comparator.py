#!/usr/bin/env python3
"""Context+ Semantic Shadow same-suite comparator harness.

Safety contract:
- Defaults are read-only.
- Help, manifest build, compare, and report modes make zero Gateway/model/provider calls.
- run-production-replay refuses to execute unless --execute-approved is present.
- Even with --execute-approved, this script is intended to be run only after the
  separate replay approval artifact is reviewed and explicitly approved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

APPROVED_MANIFEST_SHA256 = "0c28b5f5080838ee80e77ee47845e108685019ad613401385d4796e3615b8188"
PROVIDER_CALLS_THIS_PROCESS = 0


class ComparatorError(RuntimeError):
    """Expected fail-closed comparator error."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ComparatorError(f"JSONL parse error at {path}:{line_no}: {exc}") from exc
            if not isinstance(rec, dict):
                raise ComparatorError(f"JSONL record is not an object at {path}:{line_no}")
            yield rec


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
            count += 1
    return count


def count_provider_call() -> None:
    global PROVIDER_CALLS_THIS_PROCESS
    PROVIDER_CALLS_THIS_PROCESS += 1


@dataclass
class ManifestBuildResult:
    status: str
    case_count: int
    unique_visible_user_text_sha256_count: int
    duplicate_visible_user_text_sha256_count: int
    missing_field_finding_count: int
    manifest_sha256: str | None
    summary: dict[str, Any]


def build_manifest_records(source: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    route_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    seen_hashes: set[str] = set()
    duplicate_hashes: list[str] = []
    missing_fields: list[dict[str, Any]] = []

    for line_no, rec in enumerate(iter_jsonl(source), start=1):
        gate = (rec.get("gate_results") or {}).get("M7_SHADOW_ONLY_RECORD") or {}
        visible = rec.get("visible_user_text")
        visible_sha = rec.get("visible_user_text_sha256")
        turn_id = rec.get("turn_id")

        if isinstance(visible, str) and visible_sha != sha256_text(visible):
            missing_fields.append({"line": line_no, "turn_id": turn_id, "error": "visible_user_text_sha256_mismatch"})

        required = ["turn_id", "fixture_id", "visible_user_text", "visible_user_text_sha256", "selected_route_class"]
        absent = [key for key in required if not rec.get(key)]
        if not gate.get("expected_route_class"):
            absent.append("gate_results.M7_SHADOW_ONLY_RECORD.expected_route_class")
        if absent:
            missing_fields.append({"line": line_no, "turn_id": turn_id, "missing": absent})

        visible_sha_str = str(visible_sha)
        if visible_sha_str in seen_hashes:
            duplicate_hashes.append(visible_sha_str)
        else:
            seen_hashes.add(visible_sha_str)

        route = str(rec.get("selected_route_class"))
        category = str(gate.get("category"))
        route_counts[route] = route_counts.get(route, 0) + 1
        category_counts[category] = category_counts.get(category, 0) + 1

        records.append({
            "case_index": len(records) + 1,
            "case_id": turn_id,
            "fixture_id": rec.get("fixture_id"),
            "visible_user_text": visible,
            "visible_user_text_sha256": visible_sha,
            "expected_route_class": gate.get("expected_route_class"),
            "shadow_selected_route_class": rec.get("selected_route_class"),
            "shadow_decision_type": rec.get("decision_type"),
            "shadow_confidence": rec.get("confidence"),
            "shadow_confidence_margin": rec.get("confidence_margin"),
            "hardcoded_phrase_used": rec.get("hardcoded_phrase_used"),
            "prompt_rewritten": rec.get("prompt_rewritten"),
            "context_as_instruction": rec.get("context_as_instruction"),
            "category": category,
            "source_turn_record_sha256": rec.get("record_sha256"),
            "source_journal_path": str(source),
        })

    summary = {
        "status": "M7_CASE_MANIFEST_READY" if not missing_fields else "M7_CASE_MANIFEST_HOLD_MISSING_FIELDS",
        "source_journal_path": str(source),
        "source_journal_sha256": sha256_file(source),
        "case_count": len(records),
        "unique_visible_user_text_sha256_count": len(seen_hashes),
        "duplicate_visible_user_text_sha256": duplicate_hashes[:20],
        "duplicate_visible_user_text_sha256_count": len(duplicate_hashes),
        "missing_field_findings": missing_fields[:50],
        "missing_field_finding_count": len(missing_fields),
        "route_counts": route_counts,
        "category_counts": category_counts,
        "gateway_model_provider_calls": PROVIDER_CALLS_THIS_PROCESS,
        "mutation_performed": False,
        "primary_key_requirement": "case_id/turn_id; visible_user_text_sha256 alone is not unique",
    }
    if duplicate_hashes and not missing_fields:
        summary["status"] = "M7_CASE_MANIFEST_READY_WITH_FINDINGS"
    return records, summary


def cmd_build_case_manifest(args: argparse.Namespace) -> int:
    source = Path(args.source)
    output = Path(args.output)
    summary_output = Path(args.summary_output)
    if not source.exists():
        raise ComparatorError(f"source journal missing: {source}")
    records, summary = build_manifest_records(source)
    manifest_sha: str | None = None
    if args.dry_run:
        output.parent.mkdir(parents=True, exist_ok=True)
        summary_output.parent.mkdir(parents=True, exist_ok=True)
        write_jsonl(output, records)
        manifest_sha = sha256_file(output)
        summary.update({
            "manifest_path": str(output),
            "manifest_sha256": manifest_sha,
            "dry_run": True,
            "classification": "PASS_MANIFEST_DRY_RUN_VALIDATED" if summary["missing_field_finding_count"] == 0 else "HOLD_CASE_MANIFEST_NOT_READY",
        })
        write_json(summary_output, summary)
    else:
        write_jsonl(output, records)
        manifest_sha = sha256_file(output)
        summary.update({
            "manifest_path": str(output),
            "manifest_sha256": manifest_sha,
            "dry_run": False,
            "classification": "PASS_MANIFEST_WRITTEN" if summary["missing_field_finding_count"] == 0 else "HOLD_CASE_MANIFEST_NOT_READY",
        })
        write_json(summary_output, summary)
    print(json.dumps(summary, sort_keys=True, ensure_ascii=False))
    return 0


def validate_manifest(path: Path, expected_sha: str | None) -> tuple[list[dict[str, Any]], str]:
    if not path.exists():
        raise ComparatorError(f"manifest missing: {path}")
    actual_sha = sha256_file(path)
    if expected_sha and actual_sha != expected_sha:
        raise ComparatorError(f"manifest SHA mismatch: expected {expected_sha}, got {actual_sha}")
    records = list(iter_jsonl(path))
    required = {"case_id", "visible_user_text", "visible_user_text_sha256", "expected_route_class", "shadow_selected_route_class"}
    missing: list[dict[str, Any]] = []
    for idx, rec in enumerate(records, start=1):
        absent = sorted(required - set(k for k, v in rec.items() if v not in (None, "")))
        if absent:
            missing.append({"case_index": idx, "case_id": rec.get("case_id"), "missing": absent})
    if missing:
        raise ComparatorError(f"manifest required fields missing: {missing[:5]}")
    return records, actual_sha


def cmd_run_production_replay(args: argparse.Namespace) -> int:
    manifest = Path(args.manifest)
    records, manifest_sha = validate_manifest(manifest, args.manifest_sha256)

    run_config = {
        "classification": "HOLD_FRESH_BASELINE_REPLAY_REQUIRED" if not args.execute_approved else "REPLAY_EXECUTION_APPROVED_BY_FLAG",
        "mode": "dry_run_boundary_validation" if not args.execute_approved or args.dry_run else "execution_requested",
        "manifest": str(manifest),
        "manifest_sha256": manifest_sha,
        "case_count": len(records),
        "transport": args.transport,
        "model": args.model,
        "expected_provider": args.expected_provider,
        "max_cases": args.max_cases,
        "chunk_size": args.chunk_size,
        "checkpoint_every": args.checkpoint_every,
        "min_delay_ms": args.min_delay_ms,
        "max_retries": args.max_retries,
        "abort_on_rate_limit": args.abort_on_rate_limit,
        "abort_on_provider_cooldown": args.abort_on_provider_cooldown,
        "abort_on_provider_path_mismatch": args.abort_on_provider_path_mismatch,
        "abort_on_mutation": args.abort_on_mutation,
        "require_mutation_sentinel": args.require_mutation_sentinel,
        "read_only": args.read_only,
        "no_route_config_gateway_memory_cache_mutation": args.no_route_config_gateway_memory_cache_mutation,
        "gateway_model_provider_calls": PROVIDER_CALLS_THIS_PROCESS,
        "mutation_performed": False,
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "run_config.json", run_config)

    if not args.execute_approved:
        write_json(out_dir / "replay_not_executed.json", {
            "classification": "HOLD_FRESH_BASELINE_REPLAY_REQUIRED",
            "reason": "--execute-approved not supplied; no Gateway/model/provider calls made",
            "gateway_model_provider_calls": PROVIDER_CALLS_THIS_PROCESS,
            "mutation_performed": False,
        })
        print(json.dumps(run_config, sort_keys=True, ensure_ascii=False))
        return 0

    # Deliberately fail closed until this function is reviewed for live replay.
    # This prevents accidental provider calls even if the explicit flag is present
    # before the implementation is separately approved.
    write_json(out_dir / "replay_blocked_pending_implementation_review.json", {
        "classification": "HOLD_REPLAY_BOUNDARY_UNCLEAR",
        "reason": "live replay execution implementation intentionally blocked pending separate approval/review",
        "gateway_model_provider_calls": PROVIDER_CALLS_THIS_PROCESS,
        "mutation_performed": False,
    })
    raise ComparatorError("live production replay execution is intentionally blocked in this script version; no provider calls made")


def load_by_case_id(path: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for rec in iter_jsonl(path):
        case_id = rec.get("case_id") or rec.get("turn_id")
        if not case_id:
            raise ComparatorError(f"record without case_id/turn_id in {path}")
        out[str(case_id)] = rec
    return out


def classify_fp(rec: dict[str, Any], side: str) -> bool:
    """Best-effort offline false-positive classifier over existing result records."""
    if side == "shadow":
        if rec.get("hardcoded_phrase_used") is True:
            return True
        if rec.get("prompt_rewritten") is True or rec.get("context_as_instruction") is True:
            return True
        if rec.get("disagreement"):
            return True
        verdict = rec.get("evaluator_verdict") or {}
        if verdict.get("overroute_risk") or verdict.get("unsafe_execution_risk"):
            return True
        return False
    # Production replay result schema is future-facing; support common fields.
    if rec.get("false_positive") is True:
        return True
    if rec.get("material_regression") in (1, True):
        return True
    if rec.get("unsafe_execution_risk") is True or rec.get("overroute_risk") is True:
        return True
    return False


def cmd_compare(args: argparse.Namespace) -> int:
    manifest_records, manifest_sha = validate_manifest(Path(args.manifest), None)
    shadow = load_by_case_id(Path(args.shadow_journal))
    production = load_by_case_id(Path(args.production_results))

    missing_shadow = []
    missing_production = []
    comparisons = []
    shadow_fp = 0
    production_fp = 0
    category_counts: dict[str, dict[str, int]] = {}

    for case in manifest_records:
        cid = str(case["case_id"])
        srec = shadow.get(cid)
        prec = production.get(cid)
        if srec is None:
            missing_shadow.append(cid)
            continue
        if prec is None:
            missing_production.append(cid)
            continue
        s_fp = classify_fp(srec, "shadow")
        p_fp = classify_fp(prec, "production")
        shadow_fp += int(s_fp)
        production_fp += int(p_fp)
        category = str(case.get("category"))
        bucket = category_counts.setdefault(category, {"cases": 0, "shadow_fp": 0, "production_fp": 0})
        bucket["cases"] += 1
        bucket["shadow_fp"] += int(s_fp)
        bucket["production_fp"] += int(p_fp)
        comparisons.append({"case_id": cid, "category": category, "shadow_false_positive": s_fp, "production_false_positive": p_fp})

    comparable = len(comparisons)
    if missing_shadow or missing_production:
        classification = "HOLD_COMMON_CASES_INSUFFICIENT"
    elif comparable == 0:
        classification = "HOLD_COMMON_CASES_INSUFFICIENT"
    elif shadow_fp == 0 and production_fp == 0 and args.equal_zero_zero_is_hold:
        classification = "HOLD_EQUAL_ZERO_ZERO"
    elif shadow_fp < production_fp:
        classification = "PASS_FALSE_POSITIVE_BASELINE_IMPROVED"
    else:
        classification = "FAIL_FALSE_POSITIVE_NOT_IMPROVED"

    if args.require_no_critical_category_worse:
        for data in category_counts.values():
            if data["shadow_fp"] > data["production_fp"]:
                classification = "FAIL_FALSE_POSITIVE_NOT_IMPROVED"
                break

    result = {
        "classification": classification,
        "manifest_sha256": manifest_sha,
        "manifest_cases": len(manifest_records),
        "comparable_cases": comparable,
        "missing_shadow_count": len(missing_shadow),
        "missing_production_count": len(missing_production),
        "shadow_false_positive_count": shadow_fp,
        "production_false_positive_count": production_fp,
        "shadow_false_positive_rate": (shadow_fp / comparable) if comparable else None,
        "production_false_positive_rate": (production_fp / comparable) if comparable else None,
        "category_counts": category_counts,
        "gateway_model_provider_calls": PROVIDER_CALLS_THIS_PROCESS,
        "mutation_performed": False,
    }
    write_json(Path(args.out_json), result)
    if args.out_md:
        write_report_md(Path(args.out_md), result)
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


def write_report_md(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# Same-Suite False-Positive Comparison Report",
        "",
        f"Classification: `{result.get('classification')}`",
        "",
        f"Comparable cases: `{result.get('comparable_cases')}`",
        f"Shadow false positives: `{result.get('shadow_false_positive_count')}`",
        f"Production false positives: `{result.get('production_false_positive_count')}`",
        "",
        "No promotion/mutation is performed by report writing.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def cmd_write_report(args: argparse.Namespace) -> int:
    comparison = read_json(Path(args.comparison_json))
    write_report_md(Path(args.out_md), comparison)
    print(json.dumps({
        "classification": comparison.get("classification", "UNKNOWN"),
        "out_md": args.out_md,
        "gateway_model_provider_calls": PROVIDER_CALLS_THIS_PROCESS,
        "mutation_performed": False,
    }, sort_keys=True, ensure_ascii=False))
    return 0


def add_build_case_manifest(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    p = sub.add_parser("build-case-manifest", help="Build/read an M7 replay case manifest from existing shadow journal; no provider calls")
    p.add_argument("--source", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--summary-output", required=True)
    p.add_argument("--dry-run", action="store_true", help="Validate and write manifest/summary without provider calls")
    p.set_defaults(func=cmd_build_case_manifest)


def add_run_production_replay(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    p = sub.add_parser("run-production-replay", help="Validate replay boundary; live replay requires --execute-approved and is fail-closed in this version")
    p.add_argument("--manifest", required=True)
    p.add_argument("--manifest-sha256", default=APPROVED_MANIFEST_SHA256)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--transport", required=True, choices=["gateway"])
    p.add_argument("--model", required=True)
    p.add_argument("--expected-provider", required=True)
    p.add_argument("--max-cases", type=int, default=440)
    p.add_argument("--chunk-size", type=int, default=25)
    p.add_argument("--checkpoint-every", type=int, default=25)
    p.add_argument("--min-delay-ms", type=int, default=2000)
    p.add_argument("--max-retries", type=int, default=0)
    p.add_argument("--abort-on-rate-limit", action="store_true")
    p.add_argument("--abort-on-provider-cooldown", action="store_true")
    p.add_argument("--abort-on-provider-path-mismatch", action="store_true")
    p.add_argument("--abort-on-mutation", action="store_true")
    p.add_argument("--require-mutation-sentinel", action="store_true")
    p.add_argument("--read-only", action="store_true")
    p.add_argument("--no-route-config-gateway-memory-cache-mutation", action="store_true")
    p.add_argument("--dry-run", action="store_true", help="Boundary validation only; zero provider calls")
    p.add_argument("--execute-approved", action="store_true", help="Explicit future approval flag; still fail-closed pending implementation review")
    p.set_defaults(func=cmd_run_production_replay)


def add_compare(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    p = sub.add_parser("compare", help="Compare existing shadow journal and existing production replay outputs; no provider calls")
    p.add_argument("--manifest", required=True)
    p.add_argument("--shadow-journal", required=True)
    p.add_argument("--production-results", required=True)
    p.add_argument("--provider-path-report")
    p.add_argument("--mutation-sentinel-report")
    p.add_argument("--out-json", required=True)
    p.add_argument("--out-md")
    p.add_argument("--equal-zero-zero-is-hold", action="store_true")
    p.add_argument("--require-strict-improvement", action="store_true")
    p.add_argument("--require-no-critical-category-worse", action="store_true")
    p.set_defaults(func=cmd_compare)


def add_write_report(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    p = sub.add_parser("write-report", help="Write markdown from existing comparison JSON; no provider calls")
    p.add_argument("--comparison-json", required=True)
    p.add_argument("--out-md", required=True)
    p.set_defaults(func=cmd_write_report)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Context+ Semantic Shadow same-suite comparator harness (read-only by default)")
    parser.add_argument("--version", action="version", version="context-plus-same-suite-comparator 0.1-readonly")
    sub = parser.add_subparsers(dest="subcommand", required=True)
    add_build_case_manifest(sub)
    add_run_production_replay(sub)
    add_compare(sub)
    add_write_report(sub)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except ComparatorError as exc:
        print(json.dumps({
            "classification": "HOLD_REPLAY_BOUNDARY_UNCLEAR",
            "error": str(exc),
            "gateway_model_provider_calls": PROVIDER_CALLS_THIS_PROCESS,
            "mutation_performed": False,
        }, sort_keys=True, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
