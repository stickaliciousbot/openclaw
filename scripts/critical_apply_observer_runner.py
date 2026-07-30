#!/usr/bin/env python3
"""Critical Apply Observer Runner.

M0/M1 implementation: durable transaction preparation, contract receipts,
status/final-report/validation, and explicit refusal of foreground critical
mutation. Real apply execution is intentionally blocked until later milestones
pass.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import secrets
import sys
import time
from pathlib import Path
from typing import Any

from critical_apply_contracts import (
    CriticalApplyPhase,
    CriticalApplyTerminal,
    Transaction,
    argv_sha256,
    ensure_dir,
    read_json,
    receipt,
    validate_receipt,
    validate_transaction_id,
    validation_result_to_dict,
    write_json,
    write_manifest,
)

DEFAULT_ROOT = Path("/home/stickai/.openclaw/artifacts/critical-apply")
DEFAULT_LOCK = Path("/home/stickai/.openclaw/locks/critical-apply.lock")


class CriticalApplyError(RuntimeError):
    pass


class MaintenanceLock:
    def __init__(self, path: Path):
        self.path = path
        self.file = None

    def __enter__(self):
        ensure_dir(self.path.parent)
        self.file = self.path.open("a+")
        try:
            fcntl.flock(self.file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise CriticalApplyError(f"maintenance lock busy: {self.path}") from exc
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.file:
            fcntl.flock(self.file.fileno(), fcntl.LOCK_UN)
            self.file.close()


def utc_id() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def load_spec(path: Path) -> dict[str, Any]:
    spec = read_json(path)
    if not isinstance(spec, dict):
        raise CriticalApplyError("spec must be JSON object")
    return spec


def transaction_id(scope_name: str) -> str:
    safe_scope = "".join(c if c.isalnum() or c == "-" else "-" for c in scope_name.lower()).strip("-") or "unknown"
    return f"critical-apply-{safe_scope}-{utc_id()}-{secrets.token_hex(4)}"


def write_heartbeat(root: Path, phase: str, message: str) -> None:
    with (root / "heartbeat.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), "phase": phase, "message": message}, sort_keys=True) + "\n")


def prepare(args: argparse.Namespace) -> dict[str, Any]:
    spec = load_spec(Path(args.spec))
    scope = spec.get("scope") or {}
    scope_name = str(scope.get("name") or spec.get("name") or "openclaw-npm-package")
    tx_id = transaction_id(scope_name)
    root = ensure_dir(Path(args.root) / tx_id)

    with MaintenanceLock(Path(args.lock)):
        tx = Transaction(
            transaction_id=tx_id,
            root=str(root),
            plugin=str(spec.get("plugin") or "openclaw_npm_package"),
            phase=CriticalApplyPhase.INIT.value,
            restart_in_scope=bool(spec.get("restart_in_scope", False)),
            functional_smoke_in_scope=bool(spec.get("functional_smoke_in_scope", False)),
            forbidden=list(spec.get("forbidden", [])),
        )
        id_validation = validate_transaction_id(tx_id)
        if not id_validation.ok:
            raise CriticalApplyError(f"generated invalid transaction id: {id_validation.reasons}")
        write_json(root / "transaction.json", {"schema": "critical_apply.transaction.v1", **tx.__dict__})
        write_json(root / "scope.json", receipt("critical_apply.scope.v1", scope=scope, raw_spec=spec))
        lock_receipt = receipt(
            "critical_apply.lock.v1",
            transaction_id=tx_id,
            lock_path=str(args.lock),
            pid=os.getpid(),
            hostname=os.uname().nodename,
            stale_lock_policy="manual_only",
        )
        write_json(root / "lock.json", lock_receipt)
        write_heartbeat(root, CriticalApplyPhase.LOCK_ACQUIRED.value, "maintenance lock acquired for prepare")

        apply_argv = spec.get("apply_argv") or []
        if not isinstance(apply_argv, list) or not all(isinstance(x, str) for x in apply_argv):
            raise CriticalApplyError("apply_argv must be a list of strings")
        approval = receipt(
            "critical_apply.approval_boundary.v1",
            transaction_id=tx_id,
            requires_owner_approval=True,
            approval_mode="explicit-transaction-approval-required",
            allowed_mutations=spec.get("allowed_mutations", []),
            forbidden_mutations=spec.get("forbidden", []),
            exact_apply_argv=apply_argv,
            apply_argv_sha256=argv_sha256(apply_argv),
            restore_policy=spec.get("restore_policy", {"max_age_seconds": 3600, "create_if_missing": True}),
            restart_in_scope=tx.restart_in_scope,
            functional_smoke_in_scope=tx.functional_smoke_in_scope,
            foreground_apply_forbidden=True,
        )
        write_json(root / "approval-boundary.json", approval)

        restore_stub = receipt(
            "critical_apply.restore_point.v1",
            transaction_id=tx_id,
            status="NOT_CREATED_BY_M0_RUNNER",
            required_before_execute=True,
            max_age_seconds=(spec.get("restore_policy") or {}).get("max_age_seconds", 3600),
        )
        write_json(root / "restore-point.json", restore_stub)
        precheck = receipt(
            "critical_apply.precheck.v1",
            transaction_id=tx_id,
            status="M0_CONTRACT_ONLY_NOT_LIVE_PRECHECK",
            production_mutation_performed=False,
        )
        write_json(root / "precheck.json", precheck)
        final = receipt(
            "critical_apply.final_report.v1",
            transaction_id=tx_id,
            terminal=CriticalApplyTerminal.NO_APPROVAL.value,
            safe_to_continue=False,
            mutation_performed=False,
            recovery_performed=False,
            restart_performed=False,
            functional_smoke_performed=False,
            operator_action_required="M0/M1 runner prepared transaction only; execute is blocked until later gates pass.",
            hard_gates_passed=False,
            warnings=["execute intentionally unavailable in current milestone"],
        )
        write_json(root / "final-report.json", final)
        hard_gates = receipt(
            "critical_apply.hard_gates.v1",
            transaction_id=tx_id,
            phase="M0_PREPARE",
            gates={
                "transaction_id_valid": True,
                "approval_boundary_written": True,
                "foreground_apply_forbidden": True,
                "production_mutation_performed": False,
            },
            all_pass=True,
            pass_count=4,
            total=4,
        )
        write_json(root / "hard-gates.json", hard_gates)
        manifest_sha = write_manifest(root)
        return {"transaction_id": tx_id, "root": str(root), "manifest_sha256": manifest_sha, "terminal": final["terminal"]}


def status(args: argparse.Namespace) -> dict[str, Any]:
    root = resolve_transaction_root(args.transaction, Path(args.root))
    files = {}
    for name in ["transaction.json", "approval-boundary.json", "restore-point.json", "precheck.json", "apply-start.json", "apply-exit.json", "postcheck.json", "recovery-decision.json", "final-report.json", "hard-gates.json"]:
        p = root / name
        files[name] = read_json(p) if p.exists() else None
    return {"transaction_id": args.transaction, "root": str(root), "files": files}


def final_report(args: argparse.Namespace) -> dict[str, Any]:
    root = resolve_transaction_root(args.transaction, Path(args.root))
    p = root / "final-report.json"
    if not p.exists():
        raise CriticalApplyError(f"final-report missing for {args.transaction}")
    return read_json(p)


def validate(args: argparse.Namespace) -> dict[str, Any]:
    root = resolve_transaction_root(args.transaction, Path(args.root))
    checks = {
        "transaction": validation_result_to_dict(validate_receipt(root / "transaction.json", "critical_apply.transaction.v1")),
        "approval_boundary": validation_result_to_dict(validate_receipt(root / "approval-boundary.json", "critical_apply.approval_boundary.v1")),
        "final_report": validation_result_to_dict(validate_receipt(root / "final-report.json", "critical_apply.final_report.v1")),
        "hard_gates": validation_result_to_dict(validate_receipt(root / "hard-gates.json", "critical_apply.hard_gates.v1")),
    }
    all_pass = all(v["ok"] for v in checks.values())
    return {"transaction_id": args.transaction, "root": str(root), "all_pass": all_pass, "checks": checks}


def execute(args: argparse.Namespace) -> dict[str, Any]:
    root = resolve_transaction_root(args.transaction, Path(args.root))
    refusal = receipt(
        "critical_apply.execute_refusal.v1",
        transaction_id=args.transaction,
        terminal=CriticalApplyTerminal.NO_APPROVAL.value,
        reason="Execution is intentionally blocked in M0/M1. No foreground or unvalidated critical apply path is allowed.",
        production_mutation_performed=False,
    )
    write_json(root / "execute-refusal.json", refusal)
    write_manifest(root)
    return refusal


def resolve_transaction_root(transaction: str, root: Path) -> Path:
    tx_root = root / transaction
    if not tx_root.is_dir():
        raise CriticalApplyError(f"transaction root not found: {tx_root}")
    return tx_root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Critical Apply Observer Runner")
    parser.add_argument("--root", default=str(DEFAULT_ROOT))
    parser.add_argument("--lock", default=str(DEFAULT_LOCK))
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--spec", required=True)
    p.set_defaults(func=prepare)
    p = sub.add_parser("status")
    p.add_argument("--transaction", required=True)
    p.set_defaults(func=status)
    p = sub.add_parser("final-report")
    p.add_argument("--transaction", required=True)
    p.set_defaults(func=final_report)
    p = sub.add_parser("validate")
    p.add_argument("--transaction", required=True)
    p.set_defaults(func=validate)
    p = sub.add_parser("execute")
    p.add_argument("--transaction", required=True)
    p.set_defaults(func=execute)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = args.func(args)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except CriticalApplyError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
