#!/usr/bin/env python3
"""Build a bounded, non-authoritative rehydration packet for delivery-surface contract rearchitecture.

The script is local/read-only over allowlisted sources. It writes only generated
state under workspace/state by default. It does not mutate Gateway/config,
Ledger, Context Bridge, model routes, cron jobs, handlers, memory routes, or
surfaces; it does not schedule or run delivery.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "stickbot.delivery_surface_contract.rehydration.v1"
MAX_SOURCE_BYTES = 768 * 1024

PROJECT_SOURCES = (
    ("compaction_gap_proposal", "COMPACTION_GAP_RECOVERY_PROPOSAL.md", "design_reference_non_authoritative"),
    ("systemic_lld", "DURABLE_MEMORY_LEDGER_CONTEXT_CONTRACT_SURFACE_BROKER_LLD_AND_IMPLEMENTATION_PLAN.md", "design_reference_non_authoritative"),
    ("owner_supplied_broader_lld", "DURABLE_MEMORY_LEDGER_CONTEXT_CONTRACT_SURFACE_BROKER_LLD.md", "owner_supplied_design_reference_non_authoritative"),
    ("integration_order", "LEDGER_BROKER_INTEGRATION_AND_BUILD_ORDER.md", "design_reference_non_authoritative"),
    ("delivery_surface_notebook", "DELIVERY_SURFACE_CONTRACT_REARCHITECTURE_IMPLEMENTATION_TROUBLESHOOTING_REPAIR_NOTEBOOK.md", "working_notebook_non_authoritative"),
    ("m25i_lld", "M25I_DELIVERY_CONTEXT_BROKER_CONTRACT_LLD.md", "m25i_design_baseline_non_authoritative"),
    ("m25i_plan", "M25I_SYSTEM_IMPLEMENTATION_PLAN_M25J_TO_M25Z.md", "m25i_design_baseline_non_authoritative"),
    ("m25i_gates_health", "M25I_GLOBAL_HARD_GATES_AND_HEALTH_MODEL.md", "m25i_design_baseline_non_authoritative"),
    ("m25i_graph_contract", "M25I_FORWARD_CONTEXT_RECONSTRUCTION_GRAPH_CONTRACT.md", "m25i_design_baseline_non_authoritative"),
    ("m25i_rsb_contract", "M25I_RUNTIME_SERVICE_BROKER_CONTRACT.md", "m25i_design_baseline_non_authoritative"),
    ("m25i_umc_contract", "M25I_UMC_MODEL_CONTRACT_GENERALIZATION.md", "m25i_design_baseline_non_authoritative"),
    ("m25i_ssb_delivery_contract", "M25I_SURFACE_SERVICE_BROKER_AND_DELIVERY_CONTRACT.md", "m25i_design_baseline_non_authoritative"),
    ("m25i_rollback_plan", "M25I_ROLLBACK_COMPATIBILITY_AND_MIGRATION_PLAN.md", "m25i_design_baseline_non_authoritative"),
    ("m25i_test_strategy", "M25I_TEST_FIXTURE_AND_OBSERVATION_STRATEGY.md", "m25i_design_baseline_non_authoritative"),
    ("m25i_adrs", "M25I_ARCHITECTURE_DECISION_RECORDS.md", "m25i_design_baseline_non_authoritative"),
    ("m25j_prompt", "M25J_CONTRACT_SCHEMA_SKELETON_IMPLEMENTATION_PROMPT.md", "m25j_readiness_non_authoritative"),
)

WORKSPACE_SOURCES = (
    ("compaction_gap_latest_manifest", Path("state/durable-memory-architecture/compaction-gap-hydration/latest.json"), "generated_navigation_packet"),
    ("m25h_status", Path("sharedspace/runtime-kernel-validation/memory-ledger/m25h_delivery_contract_repair_final_proof_20260719T153336+1000/status.json"), "accepted_blocked_closeout_evidence"),
    ("m25h_summary", Path("sharedspace/runtime-kernel-validation/memory-ledger/m25h_delivery_contract_repair_final_proof_20260719T153336+1000/summary.json"), "accepted_blocked_closeout_evidence"),
    ("m25h_post_validation", Path("sharedspace/runtime-kernel-validation/memory-ledger/m25h_delivery_contract_repair_final_proof_20260719T153336+1000/post_validation.json"), "accepted_blocked_closeout_evidence"),
    ("m25h_safety_report", Path("sharedspace/runtime-kernel-validation/memory-ledger/m25h_delivery_contract_repair_final_proof_20260719T153336+1000/safety_report.json"), "accepted_blocked_closeout_evidence"),
    ("m25h_evidence_manifest", Path("sharedspace/runtime-kernel-validation/memory-ledger/m25h_delivery_contract_repair_final_proof_20260719T153336+1000/evidence_manifest.json"), "accepted_blocked_closeout_evidence"),
    ("memory_chunks", Path("memory/notebooks/delivery-surface-contract-rearchitecture-chunks.md"), "memory_navigation_non_authoritative"),
    ("m25i_inventory", Path("projects/durable-memory-architecture/M25I_SOURCE_AND_IMPLEMENTATION_INVENTORY.json"), "m25i_design_inventory_non_authoritative"),
    ("m25i_dependency_graph", Path("projects/durable-memory-architecture/M25I_CONTRACT_DEPENDENCY_GRAPH.json"), "m25i_design_inventory_non_authoritative"),
    ("m25i_hard_gate_registry", Path("projects/durable-memory-architecture/M25I_HARD_GATE_REGISTRY.json"), "m25i_design_inventory_non_authoritative"),
    ("m25i_health_model", Path("projects/durable-memory-architecture/M25I_HEALTH_MODEL.json"), "m25i_design_inventory_non_authoritative"),
    ("m25j_allowlist", Path("projects/durable-memory-architecture/M25J_FILE_ALLOWLIST_AND_TEST_MATRIX.json"), "m25j_readiness_non_authoritative"),
    ("m25j_srtr_schema_registry", Path("projects/durable-memory-architecture/contracts/m25j/schema_registry.json"), "m25j_srtr_contract_navigation_non_authoritative"),
    ("m25j_srtr_validator", Path("projects/durable-memory-architecture/contracts/m25j/validators.py"), "m25j_srtr_contract_navigation_non_authoritative"),
    ("m25j_srtr_repaired_security_fixture", Path("projects/durable-memory-architecture/contracts/m25j/fixtures/security/raw_telegram_identifier.json"), "m25j_srtr_security_fixture_repair_non_authoritative"),
)

FORBIDDEN_PATTERNS = (
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("bearer_token", re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{16,}")),
    (
        "credential_assignment",
        re.compile(
            r"(?i)[\"']?(?:api[_-]?key|bot[_-]?token|access[_-]?token|"
            r"refresh[_-]?token|password)[\"']?\s*[:=]\s*[\"']?"
            r"(?!redacted\b|none\b|disabled\b|unset\b|example\b)"
            r"[A-Za-z0-9._~+/=-]{16,}"
        ),
    ),
    ("raw_auth_header", re.compile(r"(?i)\bAuthorization\s*:\s*\S+")),
    ("raw_surface_target_identifier", re.compile(r"(?i)telegram:\d{4,}|\b(?:chat_id|message_id|sender_id)\b\s*[:=]?\s*\d{4,}")),
)

SUMMARY_JSON_FIELDS = (
    "schema",
    "status",
    "terminal_status",
    "terminal",
    "restart_sentinel_validation",
    "evidence_root",
    "evidence_manifest_sha256",
    "m25h_job_id",
    "m25h_run_count",
    "delivery_count",
    "handler_ended_dormant_unarmed",
    "retry_absent_not_runnable",
    "old_jobs_absent_not_runnable",
    "route_config_mutation",
    "ledger_mutations",
    "context_bridge_mutations",
    "authority_promotion",
    "m26_started",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_bounded(path: Path) -> tuple[bytes, str]:
    raw = path.read_bytes()
    if len(raw) > MAX_SOURCE_BYTES:
        raise ValueError(f"source exceeds {MAX_SOURCE_BYTES} bytes: {path}")
    return raw, raw.decode("utf-8")


def scan_forbidden(text: str) -> list[str]:
    return [name for name, pattern in FORBIDDEN_PATTERNS if pattern.search(text)]


def is_within(path: Path, roots: Iterable[Path]) -> bool:
    resolved = path.resolve()
    for root in roots:
        try:
            resolved.relative_to(root.resolve())
            return True
        except ValueError:
            continue
    return False


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def source_record(role: str, path: Path, content: bytes, authority: str) -> dict[str, Any]:
    return {
        "role": role,
        "path": str(path),
        "bytes": len(content),
        "sha256": sha256_bytes(content),
        "authority": authority,
    }


def summarize_json(text: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    summary: dict[str, Any] = {}
    for key in SUMMARY_JSON_FIELDS:
        if key not in parsed:
            continue
        value = parsed[key]
        if isinstance(value, str) and (key.endswith("_id") or key.endswith("JobId") or "job_id" in key.lower()):
            summary[f"{key}_sha256"] = sha256_bytes(value.encode("utf-8"))
            summary[f"{key}_redacted"] = True
            continue
        summary[key] = value
    return summary


def build_packet(workspace: Path, project_root: Path) -> tuple[dict[str, Any], str]:
    workspace = workspace.resolve()
    project_root = project_root.resolve()
    inventory: list[dict[str, Any]] = []
    scans: list[dict[str, Any]] = []
    mutation_checks: list[dict[str, Any]] = []
    errors: list[str] = []
    warnings: list[str] = []
    summaries: dict[str, Any] = {}
    before_hashes: dict[str, str] = {}

    for role, rel, authority in PROJECT_SOURCES:
        path = project_root / rel
        if not path.is_file():
            errors.append(f"missing project source: {path}")
            continue
        raw, text = read_bounded(path)
        findings = scan_forbidden(text)
        scans.append({"role": role, "findings": findings})
        if findings:
            errors.append(f"forbidden content in {role}: {','.join(findings)}")
            continue
        inventory.append(source_record(role, path, raw, authority))
        before_hashes[str(path)] = sha256_bytes(raw)
        maybe = summarize_json(text)
        if maybe is not None:
            summaries[role] = maybe

    for role, rel, authority in WORKSPACE_SOURCES:
        path = workspace / rel
        if not path.is_file():
            errors.append(f"missing workspace source: {path}")
            continue
        raw, text = read_bounded(path)
        findings = scan_forbidden(text)
        scans.append({"role": role, "findings": findings})
        if findings:
            errors.append(f"forbidden content in {role}: {','.join(findings)}")
            continue
        inventory.append(source_record(role, path, raw, authority))
        before_hashes[str(path)] = sha256_bytes(raw)
        maybe = summarize_json(text)
        if maybe is not None:
            summaries[role] = maybe

    for path_text, before in before_hashes.items():
        path = Path(path_text)
        after = sha256_bytes(path.read_bytes()) if path.is_file() else None
        unchanged = before == after
        mutation_checks.append({"path": path_text, "before_sha256": before, "after_sha256": after, "unchanged": unchanged})
        if not unchanged:
            errors.append(f"source changed while hydrating: {path_text}")

    status = "FAIL" if errors else "PASS"
    manifest: dict[str, Any] = {
        "schema": SCHEMA,
        "generated_utc": utc_now(),
        "status": status,
        "purpose": "rehydrate delivery-surface contract rearchitecture after compaction without authorizing runtime apply",
        "authority": "non_authoritative_navigation_only",
        "workspace": str(workspace),
        "project_root": str(project_root),
        "source_inventory": inventory,
        "forbidden_content_scans": scans,
        "source_mutation_checks": mutation_checks,
        "warnings": warnings,
        "errors": errors,
        "summaries": summaries,
        "fixed_boundaries": [
            "No handler arming, retry scheduling, cron run, delivery, Telegram send, Gateway/config mutation, Ledger mutation, Context Bridge mutation, route/model mutation, authority promotion, or M26 start.",
            "This packet is not automatic prompt injection and not an implementation milestone.",
            "M25H remains accepted as pushed BLOCKED; future repair requires separate owner authorization.",
        ],
        "initial_contract_focus": [
            "Distinguish explicit NO_REPLY/silent policy from missing deliverable payload.",
            "Bind job/run/session -> boundary decision -> reply payload -> message_sending gate -> delivery runtime -> message_sent receipt -> closeout.",
            "Make exactly-one delivery and dedupe contract-level properties.",
            "Keep Surface Service Broker privacy/rendering/delivery policy separate from Runtime Service Broker source authority.",
            "Keep Surface Response Target Resolver grants separate from surface authorization and raw provider target handles.",
            "Require UMC postcondition receipts before prose claims delivery/source success.",
        ],
    }

    inventory_lines = "\n".join(
        f"- `{item['role']}` — `{item['path']}` — {item['bytes']} bytes — sha256:`{item['sha256']}` — {item['authority']}"
        for item in inventory
    ) or "- No readable sources"
    summary_block = json.dumps(summaries, indent=2, sort_keys=True)

    markdown = f"""# Delivery Surface Contract Rearchitecture — Rehydration Packet

Generated: `{manifest['generated_utc']}`
Status: **{status}**
Authority: **non-authoritative navigation only**

## Mandatory interpretation

This packet restores design context and accepted M25H blocked-closeout coordinates. It does not authorize implementation, runtime mutation, handler arming, retry scheduling, delivery, Telegram sends, Ledger/Context Bridge/model-route changes, authority promotion, or M26/M2 successor work.

## Fixed boundaries

{chr(10).join(f'- {item}' for item in manifest['fixed_boundaries'])}

## Initial contract focus

{chr(10).join(f'- {item}' for item in manifest['initial_contract_focus'])}

## Bounded source summaries

```json
{summary_block}
```

## Source inventory

{inventory_lines}

## Warnings

{chr(10).join(f'- {item}' for item in warnings) if warnings else '- None'}

## Errors

{chr(10).join(f'- {item}' for item in errors) if errors else '- None'}
"""
    markdown = "\n".join(line.rstrip() for line in markdown.splitlines()) + "\n"
    return manifest, markdown


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=None)
    parser.add_argument("--project-root", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    script_path = Path(__file__).resolve()
    inferred_project = script_path.parent.parent
    project_root = (args.project_root or inferred_project).expanduser().resolve()
    inferred_workspace = project_root.parents[1]
    workspace = (args.workspace or inferred_workspace).expanduser().resolve()
    output_dir = (
        args.output_dir.expanduser().resolve()
        if args.output_dir
        else workspace / "state/durable-memory-architecture/delivery-surface-contract-rehydration"
    )
    if not is_within(output_dir, [workspace / "state", Path(tempfile.gettempdir())]):
        print(json.dumps({"status": "FAIL", "error": "output directory must be under workspace/state or temp", "output_dir": str(output_dir)}, indent=2), file=sys.stderr)
        return 2
    try:
        manifest, markdown = build_packet(workspace, project_root)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2

    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    markdown_bytes = (markdown.rstrip() + "\n").encode("utf-8")
    latest_json = output_dir / "latest.json"
    latest_md = output_dir / "latest.md"
    if not args.check_only:
        atomic_write(latest_json, manifest_bytes)
        atomic_write(latest_md, markdown_bytes)
    result = {
        "schema": SCHEMA,
        "status": manifest["status"],
        "generated_utc": manifest["generated_utc"],
        "check_only": args.check_only,
        "latest_json": None if args.check_only else str(latest_json),
        "latest_md": None if args.check_only else str(latest_md),
        "source_count": len(manifest["source_inventory"]),
        "warning_count": len(manifest["warnings"]),
        "error_count": len(manifest["errors"]),
        "warnings": manifest["warnings"],
        "errors": manifest["errors"],
        "packet_sha256": sha256_bytes(markdown_bytes),
        "manifest_sha256": sha256_bytes(manifest_bytes),
    }
    if args.status or args.check_only:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Rehydration packet written: {latest_md}")
        print(f"Status: {manifest['status']}")
    if manifest["status"] == "FAIL":
        return 1
    if manifest["status"] == "WARN" and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
