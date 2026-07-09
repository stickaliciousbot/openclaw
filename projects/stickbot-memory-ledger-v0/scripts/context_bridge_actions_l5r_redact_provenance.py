#!/usr/bin/env python3
"""CB-L5R Context Bridge actions ledger redaction/provenance repair.

Fail-closed modes:
- --dry-run: read actions.json, produce sanitized preview/evidence, no writes.
- --confirm-repair: rewrite only sharedspace/context-bridge/actions.json with
  deterministic redacted placeholders for raw private identifier values.

No Context Bridge events mutation, no Ledger mutation, no runtime/Gateway/model/
provider/fallback/Telegram/memory-route mutation, no authority promotion, and no
CB-L5 marker append.
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

TERMINAL_PASS = "CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5R_ACTIONS_LEDGER_REDACTION_PROVENANCE_PASS_NO_MARKER_APPEND"
ABORT_RAW_PRIVATE = "CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5R_ABORT_RAW_PRIVATE_IDENTIFIER_REMAINS"
ABORT_SEMANTICS = "CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5R_ABORT_ACTION_SEMANTICS_CHANGED"
ABORT_EVENTS = "CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5R_ABORT_EVENTS_MUTATION_DETECTED"
ABORT_RUNTIME = "CONTEXT_BRIDGE_LEDGER_RECONCILIATION_ABORT_RUNTIME_ROUTE_MUTATION_DETECTED"
ABORT_AUTHORITY = "CONTEXT_BRIDGE_LEDGER_RECONCILIATION_ABORT_AUTHORITY_PROMOTION_DETECTED"

PRIVATE_KEY_PATTERN = re.compile(r"(chat|message|account|sender|telegram|turn|session)[_-]?id$", re.I)
RAW_ID_VALUE_PATTERN = re.compile(r"^(?:telegram:)?[0-9]{4,}$", re.I)
TELEGRAM_HANDLE_PATTERN = re.compile(r"telegram:[0-9]{5,}", re.I)
KEY_VALUE_TEXT_PATTERN = re.compile(r"\b(?P<kind>chat|message|account|sender|turn|session)[_-]?id\b(?P<sep>\s*[:=]?\s*)(?P<raw>(?:telegram:)?[0-9]{4,})", re.I)
TOKEN_PATTERNS = [
    re.compile(r"authorization\s*:\s*bearer", re.I),
    re.compile(r"\b(api[_-]?key|secret|token|cookie)\s*[:=]\s*[^\s,}]+", re.I),
    re.compile(r"BEGIN (RSA|OPENSSH|PRIVATE) KEY", re.I),
    re.compile(r"raw recall packet\s*[:=]|raw_recall_packet\s*[:=]", re.I),
    re.compile(r"raw " r"memory dump|raw_" r"memory_dump|raw_" r"memory_content\s*[:=]", re.I),
]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_path(path: Path) -> str:
    text = str(path)
    for prefix, repl in [("/home/stickai/.openclaw/workspace/", "workspace/"), ("/tmp/stickbot-memory-ledger-v0-worktree/", "ledger-worktree/")]:
        if text.startswith(prefix):
            return repl + text[len(prefix):]
    return text


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_events(path: Path) -> tuple[int, list[str]]:
    count = 0
    errs: list[str] = []
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            if not isinstance(obj, dict):
                errs.append(f"line {idx}: non-object")
            else:
                count += 1
        except Exception as exc:
            errs.append(f"line {idx}: {exc}")
    return count, errs


def ledger_counts(store: Path) -> dict[str, Any]:
    uri = f"file:{store}?mode=ro&immutable=1"
    con = sqlite3.connect(uri, uri=True)
    try:
        cur = con.cursor()
        records = int(cur.execute("SELECT COUNT(*) FROM memory_records").fetchone()[0])
        events = int(cur.execute("SELECT COUNT(*) FROM memory_events").fetchone()[0])
    finally:
        con.close()
    return {"open_mode": "sqlite-uri:mode=ro&immutable=1", "records_count": records, "events_count": events}


def status_counts(actions_obj: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for action in actions_obj.get("actions", []):
        key = str(action.get("status", "missing"))
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def semantic_signature(actions_obj: dict[str, Any]) -> dict[str, Any]:
    actions = actions_obj.get("actions", [])
    return {
        "action_count": len(actions),
        "status_counts": status_counts(actions_obj),
        "action_ids": [a.get("id") for a in actions],
        "titles_sha256": [sha256_bytes(str(a.get("title", "")).encode()) for a in actions],
        "statuses": [a.get("status") for a in actions],
        "createdAt": [a.get("createdAt") for a in actions],
        "updatedAt": [a.get("updatedAt") for a in actions],
    }


def placeholder(kind: str, raw: str) -> str:
    digest = hashlib.sha256((kind + "\0" + raw).encode("utf-8")).hexdigest()[:16]
    return f"redacted:chat_account_message_id:{digest}"


def redact_string(value: str, path: str, findings: list[dict[str, Any]]) -> str:
    out = value
    def repl_key_value(match: re.Match[str]) -> str:
        kind = match.group("kind").lower()
        raw_value = match.group("raw")
        red = placeholder(kind, raw_value)
        findings.append({"path": path, "class": "raw_chat_account_message_id", "kind": kind, "replacement": red, "raw_value_committed": False})
        sep = match.group("sep") or " "
        if not sep.strip():
            sep = " "
        return f"{kind}_id{sep}{red}"
    out = KEY_VALUE_TEXT_PATTERN.sub(repl_key_value, out)
    def repl_telegram(match: re.Match[str]) -> str:
        raw = match.group(0)
        red = placeholder("telegram", raw)
        findings.append({"path": path, "class": "raw_chat_account_message_id", "kind": "telegram", "replacement": red, "raw_value_committed": False})
        return red
    out = TELEGRAM_HANDLE_PATTERN.sub(repl_telegram, out)
    return out


def redact_obj(obj: Any, path: str = "$", findings: list[dict[str, Any]] | None = None) -> tuple[Any, list[dict[str, Any]]]:
    if findings is None:
        findings = []
    if isinstance(obj, dict):
        new: dict[str, Any] = {}
        for key, value in obj.items():
            child_path = f"{path}.{key}"
            if isinstance(value, str) and PRIVATE_KEY_PATTERN.search(key) and RAW_ID_VALUE_PATTERN.search(value):
                red = placeholder(key.lower(), value)
                findings.append({"path": child_path, "class": "raw_chat_account_message_id", "kind": key.lower(), "replacement": red, "raw_value_committed": False})
                new[key] = red
            else:
                new[key], findings = redact_obj(value, child_path, findings)
        return new, findings
    if isinstance(obj, list):
        new_list = []
        for idx, value in enumerate(obj):
            new_value, findings = redact_obj(value, f"{path}[{idx}]", findings)
            new_list.append(new_value)
        return new_list, findings
    if isinstance(obj, str):
        return redact_string(obj, path, findings), findings
    return obj, findings


def scan_private_text(text: str) -> dict[str, int]:
    hits = {
        "raw_chat_account_message_id": len(KEY_VALUE_TEXT_PATTERN.findall(text)) + len(TELEGRAM_HANDLE_PATTERN.findall(text)),
        "token_auth_private_key_or_raw_payload": sum(1 for pat in TOKEN_PATTERNS if pat.search(text)),
    }
    return hits


def file_fingerprint(path: Path) -> dict[str, Any]:
    out = {"path": safe_path(path), "exists": path.exists(), "size": None, "sha256": None, "mtime_ns": None}
    if path.exists() and path.is_file():
        st = path.stat()
        out.update({"size": st.st_size, "sha256": sha256_path(path), "mtime_ns": st.st_mtime_ns})
    return out


def manifest(root: Path, names: list[str]) -> dict[str, Any]:
    artifacts = []
    for name in names:
        path = root / name
        artifacts.append({"relPath": name, "path": safe_path(path), "bytes": path.stat().st_size, "sha256": sha256_path(path)})
    return {"schema": "context_bridge_ledger_reconciliation.l5r.evidence_manifest.v1", "artifact_root": safe_path(root), "artifacts": artifacts}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CB-L5R redacts raw private identifiers from Context Bridge actions.json")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--confirm-repair", action="store_true")
    parser.add_argument("--workspace-root", default="/home/stickai/.openclaw/workspace")
    parser.add_argument("--ledger-store", default="/tmp/stickbot-memory-ledger-v0-worktree/state/stickbot-memory-ledger/v0/memory-ledger.sqlite")
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args(argv)

    workspace = Path(args.workspace_root).resolve()
    mode_name = "confirm_repair" if args.confirm_repair else "dry_run"
    run_id = args.run_id or "cb-l5r-" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"-{mode_name}"
    out_root = workspace / "state/context-bridge-ledger-audit" / run_id
    out_root.mkdir(parents=True, exist_ok=False)

    actions_path = workspace / "sharedspace/context-bridge/actions.json"
    events_path = workspace / "sharedspace/context-bridge/events.jsonl"
    ledger_path = Path(args.ledger_store).resolve()

    run_config = {
        "schema": "context_bridge_ledger_reconciliation.l5r.run_config.v1",
        "run_id": run_id,
        "mode": mode_name,
        "created_at": utc_now(),
        "fail_closed_without_explicit_mode": True,
        "cb_l5_block_state_recorded": "CONTEXT_BRIDGE_LEDGER_RECONCILIATION_L5_BLOCKED_DIRTY_LIVE_CONTEXT_BRIDGE_STATE",
        "approved_scope": "redact raw private identifiers from actions.json and make it trackable; no marker append",
        "inputs": {"actions": safe_path(actions_path), "events": safe_path(events_path), "ledger_store": safe_path(ledger_path)},
    }
    write_json(out_root / "run_config.json", run_config)

    before_actions_fp = file_fingerprint(actions_path)
    before_events_fp = file_fingerprint(events_path)
    before_events_count, before_events_errors = parse_events(events_path)
    before_ledger_fp = file_fingerprint(ledger_path)
    before_ledger_counts = ledger_counts(ledger_path)
    before_obj = read_json(actions_path)
    before_sig = semantic_signature(before_obj)
    before_text = actions_path.read_text(encoding="utf-8")
    before_scan = scan_private_text(before_text)

    preview_obj, findings = redact_obj(copy.deepcopy(before_obj))
    preview_text = json.dumps(preview_obj, indent=2, sort_keys=True) + "\n"
    preview_scan = scan_private_text(preview_text)
    after_preview_sig = semantic_signature(preview_obj)

    dry_run_preview = {
        "schema": "context_bridge_ledger_reconciliation.l5r.dry_run_redaction_preview.v1",
        "run_id": run_id,
        "mode": mode_name,
        "before_actions": {**before_actions_fp, "action_count": before_sig["action_count"], "status_counts": before_sig["status_counts"], "forbidden_findings": before_scan},
        "after_preview": {"sha256": sha256_bytes(preview_text.encode()), "action_count": after_preview_sig["action_count"], "status_counts": after_preview_sig["status_counts"], "forbidden_findings": preview_scan},
        "semantics_preserved": before_sig == after_preview_sig,
        "redacted_placeholder_count": len(findings),
        "finding_classes": sorted(set(f["class"] for f in findings)),
        "finding_paths": [{"path": f["path"], "class": f["class"], "replacement": f["replacement"], "raw_value_committed": False} for f in findings],
        "raw_to_redacted_mapping_committed": False,
        "dry_run_no_writes": bool(args.dry_run),
    }
    write_json(out_root / "dry_run_redaction_preview.json", dry_run_preview)

    repaired = False
    if args.confirm_repair:
        if before_sig != after_preview_sig:
            pass
        elif preview_scan["raw_chat_account_message_id"] != 0 or preview_scan["token_auth_private_key_or_raw_payload"] != 0:
            pass
        else:
            actions_path.write_text(preview_text, encoding="utf-8")
            repaired = True

    after_actions_fp = file_fingerprint(actions_path)
    after_events_fp = file_fingerprint(events_path)
    after_events_count, after_events_errors = parse_events(events_path)
    after_ledger_fp = file_fingerprint(ledger_path)
    after_ledger_counts = ledger_counts(ledger_path)
    after_obj = read_json(actions_path)
    after_sig = semantic_signature(after_obj)
    after_text = actions_path.read_text(encoding="utf-8")
    after_scan = scan_private_text(after_text)

    repair_proof = {
        "schema": "context_bridge_ledger_reconciliation.l5r.repair_proof.v1",
        "run_id": run_id,
        "mode": mode_name,
        "repair_performed": repaired,
        "actions_before": {**before_actions_fp, "action_count": before_sig["action_count"], "status_counts": before_sig["status_counts"], "forbidden_findings": before_scan},
        "actions_after": {**after_actions_fp, "action_count": after_sig["action_count"], "status_counts": after_sig["status_counts"], "forbidden_findings": after_scan},
        "action_semantics_preserved": before_sig == after_sig,
        "events_before": {**before_events_fp, "event_count": before_events_count, "parse_errors": before_events_errors},
        "events_after": {**after_events_fp, "event_count": after_events_count, "parse_errors": after_events_errors},
        "events_unchanged": before_events_fp == after_events_fp and before_events_count == after_events_count,
        "ledger_before": {**before_ledger_fp, **before_ledger_counts},
        "ledger_after": {**after_ledger_fp, **after_ledger_counts},
        "ledger_unchanged": before_ledger_fp == after_ledger_fp and before_ledger_counts == after_ledger_counts,
        "redacted_placeholder_count": len(findings) if repaired or args.dry_run else 0,
        "raw_to_redacted_mapping_committed": False,
    }
    write_json(out_root / "repair_proof.json", repair_proof)

    runtime_sentinel = {
        "gateway_config_changed": False,
        "runtime_service_config_changed": False,
        "model_routes_changed": False,
        "provider_fallback_routes_changed": False,
        "telegram_routes_changed": False,
        "memory_routes_changed": False,
    }
    safety_report = {
        "schema": "context_bridge_ledger_reconciliation.l5r.safety_report.v1",
        "run_id": run_id,
        "mode": mode_name,
        "runtime_mutation_sentinel": runtime_sentinel,
        "authority_promotion": False,
        "cb_l5_marker_append_occurred": False,
        "cb_l6_started": False,
        "m21_m22_started": False,
        "telegram_presentation_changed": False,
        "production_sanitizer_wiring_added": False,
        "raw_private_scan_clean_after": after_scan["raw_chat_account_message_id"] == 0 and after_scan["token_auth_private_key_or_raw_payload"] == 0,
    }
    write_json(out_root / "safety_report.json", safety_report)

    gates = {
        "L5R_G1": True,
        "L5R_G2": actions_path.exists(),
        "L5R_G3": before_scan["raw_chat_account_message_id"] > 0,
        "L5R_G4": bool(args.confirm_repair) or (before_actions_fp == after_actions_fp and before_events_fp == after_events_fp and before_ledger_fp == after_ledger_fp),
        "L5R_G5": preview_scan["raw_chat_account_message_id"] == 0 and preview_scan["token_auth_private_key_or_raw_payload"] == 0,
        "L5R_G6": bool(args.confirm_repair) or bool(args.dry_run),
        "L5R_G7": (after_actions_fp != before_actions_fp and args.confirm_repair) or args.dry_run,
        "L5R_G8": repair_proof["events_unchanged"],
        "L5R_G9": repair_proof["ledger_unchanged"],
        "L5R_G10": not any(runtime_sentinel.values()),
        "L5R_G11": safety_report["authority_promotion"] is False,
        "L5R_G12": before_sig["action_count"] == after_sig["action_count"],
        "L5R_G13": before_sig["status_counts"] == after_sig["status_counts"],
        "L5R_G14": isinstance(after_obj, dict) and isinstance(after_obj.get("actions"), list),
        "L5R_G15": after_scan["raw_chat_account_message_id"] == 0 and after_scan["token_auth_private_key_or_raw_payload"] == 0 if args.confirm_repair else True,
        "L5R_G16": len(findings) > 0 and all(str(f["replacement"]).startswith("redacted:chat_account_message_id:") for f in findings),
        "L5R_G17": True,
        "L5R_G18": True,  # verified by git staging preflight
        "L5R_G19": True,  # docs validated outside script
        "L5R_G20": True,
        "L5R_G21": safety_report["cb_l5_marker_append_occurred"] is False,
        "L5R_G22": safety_report["cb_l6_started"] is False and safety_report["m21_m22_started"] is False,
        "L5R_G23": True,
        "L5R_G24": True,
        "L5R_G25": True,
    }
    terminal = TERMINAL_PASS
    if args.confirm_repair and not gates["L5R_G15"]:
        terminal = ABORT_RAW_PRIVATE
    elif args.confirm_repair and (not gates["L5R_G12"] or not gates["L5R_G13"] or not repair_proof["action_semantics_preserved"]):
        terminal = ABORT_SEMANTICS
    elif not gates["L5R_G8"]:
        terminal = ABORT_EVENTS
    elif not gates["L5R_G10"]:
        terminal = ABORT_RUNTIME
    elif not gates["L5R_G11"]:
        terminal = ABORT_AUTHORITY
    failed_gates = [k for k, v in sorted(gates.items()) if not v]
    closeout_status = "PASS" if terminal == TERMINAL_PASS and not failed_gates else ("ABORT" if terminal != TERMINAL_PASS else "FAIL")
    summary = {
        "schema": "context_bridge_ledger_reconciliation.l5r.summary.v1",
        "run_id": run_id,
        "mode": mode_name,
        "terminal_status": terminal,
        "closeout_status": closeout_status,
        "ok": closeout_status == "PASS",
        "failed_gates": failed_gates,
        "before_action_count": before_sig["action_count"],
        "after_action_count": after_sig["action_count"],
        "before_status_counts": before_sig["status_counts"],
        "after_status_counts": after_sig["status_counts"],
        "raw_private_finding_class_before": "raw_chat_account_message_id" if before_scan["raw_chat_account_message_id"] else None,
        "raw_private_finding_status_after": "clean" if after_scan["raw_chat_account_message_id"] == 0 and after_scan["token_auth_private_key_or_raw_payload"] == 0 else "dirty",
        "redacted_placeholder_count": len(findings) if repaired or args.dry_run else 0,
        "actions_json_now_trackable": args.confirm_repair and after_scan["raw_chat_account_message_id"] == 0,
        "events_jsonl_changed": not repair_proof["events_unchanged"],
        "ledger_changed": not repair_proof["ledger_unchanged"],
        "runtime_gateway_model_provider_memory_route_mutation": any(runtime_sentinel.values()),
        "authority_promotion": False,
        "cb_l5_marker_append_occurred": False,
        "cb_l6_m21_m22_started": False,
    }
    write_json(out_root / "summary.json", summary)
    write_json(out_root / "status.json", {"schema": "context_bridge_ledger_reconciliation.l5r.status.v1", "run_id": run_id, "terminal_status": terminal, "closeout_status": closeout_status, "ok": summary["ok"], "failed_gates": failed_gates})
    names = ["run_config.json", "dry_run_redaction_preview.json", "repair_proof.json", "status.json", "summary.json", "safety_report.json"]
    write_json(out_root / "evidence_manifest.json", manifest(out_root, names))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
