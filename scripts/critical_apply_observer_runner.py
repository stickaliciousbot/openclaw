#!/usr/bin/env python3
"""Durable Critical Apply observer runner for OpenClaw package transactions.

This runner is intentionally narrow. It can prepare/review transactions without
mutation, and its execute path requires explicit package-apply flags plus exact
root allowlisting. It never restarts Gateway, calls providers, mutates config or
cron, runs systemctl, or performs git operations.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
from pathlib import Path
from subprocess import DEVNULL, PIPE, Popen, TimeoutExpired
from typing import Any, Mapping, Sequence

from critical_apply_atomic_io import sha256_file
from critical_apply_contracts import canonical_json_dumps, read_json, write_json
from critical_apply_package_authority import validate_package_apply_authority
from critical_apply_plugins.openclaw_npm_package import (
    create_full_restore_point,
    extract_package_artifact,
    inspect_package_root,
    inspect_staging_dirs,
    postcheck_package_identity,
    apply_staged_package,
    restore_from_full_restore_point,
)

RUNNER_SCHEMA = "critical_apply.observer_runner.v1"
PREP_SCHEMA = RUNNER_SCHEMA + ".prepare"
STATUS_SCHEMA = RUNNER_SCHEMA + ".status"
FINAL_SCHEMA = RUNNER_SCHEMA + ".final"
LOCK_SCHEMA = RUNNER_SCHEMA + ".maintenance_lock"
APPLY_START_SCHEMA = RUNNER_SCHEMA + ".apply_start"
APPLY_EXIT_SCHEMA = RUNNER_SCHEMA + ".apply_exit"

DEFAULT_REQUIRED_AUTHORIZATION = (
    "Authorize M8-R18 live package install/apply for OpenClaw package roots only, "
    "using the frozen M8-R16 envelope and M8-R17 review plan. No Gateway restart "
    "or provider smoke unless separately authorized."
)


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha_obj(obj: Any) -> str:
    return __import__("hashlib").sha256(canonical_json_dumps(obj).encode()).hexdigest()


def exact_abs(path: str | Path, *, field: str) -> Path:
    p = Path(path)
    if not p.is_absolute():
        raise ValueError(f"{field}_must_be_absolute")
    if ".." in p.parts:
        raise ValueError(f"{field}_must_not_contain_parent_traversal")
    return p


def under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def load_json(path: str | Path) -> Any:
    return read_json(path)


def write_receipt(path: Path, obj: Mapping[str, Any]) -> Mapping[str, Any]:
    write_json(path, dict(obj))
    return obj


def transaction_paths(root: Path) -> dict[str, Path]:
    return {name: root / name for name in ("receipts", "logs", "staging", "restore-point")}


def ensure_transaction_root(root: str | Path) -> Path:
    root = exact_abs(root, field="transaction_root")
    root.mkdir(parents=True, exist_ok=True)
    for p in transaction_paths(root).values():
        p.mkdir(parents=True, exist_ok=True)
    return root


def envelope_authority(envelope: Mapping[str, Any]) -> Mapping[str, Any]:
    authority = envelope.get("package_apply_authority")
    if not isinstance(authority, dict):
        raise ValueError("package_apply_authority_missing")
    ok, reasons = validate_package_apply_authority(authority, require_enabled=True)
    if not ok:
        raise ValueError("package_apply_authority_invalid:" + ",".join(reasons))
    return authority


def revalidate_bound_hashes(envelope: Mapping[str, Any], *, expected_authority_sha256: str | None = None, expected_spec_sha256: str | None = None) -> dict[str, Any]:
    authority = envelope_authority(envelope)
    authority_sha = str(envelope.get("package_apply_authority_sha256") or sha_obj(authority))
    spec_sha = str(envelope.get("package_transaction_spec_sha256") or authority.get("package_transaction_spec_sha256"))
    reasons: list[str] = []
    if expected_authority_sha256 and authority_sha != expected_authority_sha256:
        reasons.append("authority_sha256_mismatch")
    if expected_spec_sha256 and spec_sha != expected_spec_sha256:
        reasons.append("transaction_spec_sha256_mismatch")
    return {"ok": not reasons, "reasons": reasons, "authority_sha256": authority_sha, "transaction_spec_sha256": spec_sha, "authority": authority}


def acquire_lock(lock_path: str | Path, receipt_root: Path) -> tuple[int, dict[str, Any]]:
    lock_path = exact_abs(lock_path, field="lock_path")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    receipt = {"schema": LOCK_SCHEMA, "acquired": True, "released": False, "lock_path": str(lock_path), "pid": os.getpid(), "wall_time_utc": utc_now()}
    os.write(fd, (json.dumps(receipt, sort_keys=True) + "\n").encode())
    write_receipt(receipt_root / "maintenance-lock-acquired.json", receipt)
    return fd, receipt


def release_lock(fd: int | None, lock_receipt: Mapping[str, Any] | None, receipt_root: Path) -> None:
    if fd is None or not lock_receipt:
        return
    try:
        os.close(fd)
    except OSError:
        pass
    released = dict(lock_receipt)
    released.update({"released": True, "released_wall_time_utc": utc_now()})
    try:
        Path(str(lock_receipt["lock_path"])).unlink()
    except FileNotFoundError:
        released["release_warning"] = "lock_already_absent"
    write_receipt(receipt_root / "maintenance-lock-released.json", released)


def validate_targets_allowed(targets: Sequence[str], allowed_roots: Sequence[str]) -> None:
    allowed = [exact_abs(x, field="allowed_root") for x in allowed_roots]
    if not allowed:
        raise ValueError("allowed_roots_required_for_execute")
    for target in targets:
        tp = exact_abs(target, field="target")
        if not any(tp.resolve() == root.resolve() or under(tp, root) for root in allowed):
            raise ValueError(f"target_not_allowed:{tp}")


def prepare_transaction(*, transaction_root: str | Path, enabled_envelope: str | Path, review_plan: str | Path, name: str) -> dict[str, Any]:
    root = ensure_transaction_root(transaction_root)
    envelope_path = exact_abs(enabled_envelope, field="enabled_envelope")
    review_plan_path = exact_abs(review_plan, field="review_plan")
    envelope = load_json(envelope_path)
    review = load_json(review_plan_path)
    reval = revalidate_bound_hashes(envelope)
    status = {
        "schema": PREP_SCHEMA,
        "name": name,
        "transaction_root": str(root),
        "enabled_envelope_path": str(envelope_path),
        "enabled_envelope_sha256": sha256_file(envelope_path),
        "review_plan_path": str(review_plan_path),
        "review_plan_sha256": sha256_file(review_plan_path),
        "authority_sha256": reval["authority_sha256"],
        "transaction_spec_sha256": reval["transaction_spec_sha256"],
        "authority_valid": reval["ok"],
        "authority_reasons": reval["reasons"],
        "review_plan_status": review.get("status"),
        "phase": "PREPARED_REVIEW_ONLY",
        "live_apply_executed": False,
        "wall_time_utc": utc_now(),
    }
    write_receipt(root / "transaction.json", status)
    write_receipt(root / "receipts" / "authority-revalidation.json", {k: v for k, v in status.items() if k != "schema"} | {"schema": RUNNER_SCHEMA + ".authority_revalidation"})
    return status


def child_apply(transaction_root: str, staged_package_root: str, target_package_root: str, target_cli_link: str) -> int:
    root = exact_abs(transaction_root, field="transaction_root")
    try:
        result = apply_staged_package(staged_package_root, target_package_root, target_cli_link)
        write_receipt(root / "receipts" / "child-apply-result.json", result)
        return 0
    except Exception as exc:  # noqa: BLE001
        write_receipt(root / "receipts" / "child-apply-result.json", {"schema": RUNNER_SCHEMA + ".child_apply_result", "ok": False, "error": type(exc).__name__ + ":" + str(exc), "wall_time_utc": utc_now()})
        return 1


def execute_package_apply(*, transaction_root: str | Path, enabled_envelope: str | Path, review_plan: str | Path, owner_authorization_phrase: str, allowed_root: Sequence[str], expected_authority_sha256: str | None = None, expected_spec_sha256: str | None = None, execute_live_package_apply: bool = False, timeout_seconds: float = 120.0) -> dict[str, Any]:
    root = ensure_transaction_root(transaction_root)
    receipts = root / "receipts"
    logs = root / "logs"
    envelope_path = exact_abs(enabled_envelope, field="enabled_envelope")
    review_plan_path = exact_abs(review_plan, field="review_plan")
    if owner_authorization_phrase != DEFAULT_REQUIRED_AUTHORIZATION:
        status = {"schema": STATUS_SCHEMA, "status": "HOLD", "terminal_status": "NO_APPROVAL", "reason": "owner_authorization_phrase_mismatch", "live_apply_executed": False, "wall_time_utc": utc_now()}
        write_receipt(root / "STATUS.json", status)
        return status
    if not execute_live_package_apply:
        status = {"schema": STATUS_SCHEMA, "status": "HOLD", "terminal_status": "APPROVED_NOT_STARTED", "reason": "execute_live_package_apply_flag_missing", "live_apply_executed": False, "wall_time_utc": utc_now()}
        write_receipt(root / "STATUS.json", status)
        return status
    envelope = load_json(envelope_path)
    review = load_json(review_plan_path)
    reval = revalidate_bound_hashes(envelope, expected_authority_sha256=expected_authority_sha256, expected_spec_sha256=expected_spec_sha256)
    if not reval["ok"]:
        status = {"schema": STATUS_SCHEMA, "status": "HOLD", "terminal_status": "PRECONDITION_DRIFT_BLOCKED", "revalidation": reval, "live_apply_executed": False, "wall_time_utc": utc_now()}
        write_receipt(root / "STATUS.json", status)
        return status
    authority = reval["authority"]
    spec = authority["package_transaction_spec"]
    targets = list(spec["target_roots"])
    lock_fd: int | None = None
    lock_receipt: Mapping[str, Any] | None = None
    try:
        validate_targets_allowed(targets, allowed_root)
        package_root, cli_link = targets
        lock_fd, lock_receipt = acquire_lock(authority["maintenance_lock"]["lock_path"], receipts)
        restore = create_full_restore_point(root / "restore-point", package_root, cli_link)
        write_receipt(receipts / "restore-point.json", restore)
        precheck = {
            "schema": RUNNER_SCHEMA + ".precheck",
            "package_health": inspect_package_root(package_root, expected_version="2026.5.7"),
            "staging_dirs": inspect_staging_dirs(Path(package_root).parent),
            "wall_time_utc": utc_now(),
        }
        write_receipt(receipts / "precheck.json", precheck)
        artifact = spec["source_package_path"]
        extract = extract_package_artifact(artifact, root / "staging", expected_sha256=spec["package_artifact_sha256"])
        write_receipt(receipts / "artifact-extract.json", extract)
        child_stdout = logs / "apply-child.stdout.log"
        child_stderr = logs / "apply-child.stderr.log"
        argv = [sys.executable, str(Path(__file__).resolve()), "_apply-child", "--transaction-root", str(root), "--staged-package-root", str(root / "staging" / "package"), "--target-package-root", package_root, "--target-cli-link", cli_link]
        start = {"schema": APPLY_START_SCHEMA, "argv": argv, "cwd": str(root), "stdout_path": str(child_stdout), "stderr_path": str(child_stderr), "wall_time_utc": utc_now()}
        with child_stdout.open("wb") as out, child_stderr.open("wb") as err:
            proc = Popen(argv, stdin=DEVNULL, stdout=out, stderr=err, cwd=str(root), start_new_session=True)
            start.update({"child_pid": proc.pid, "child_process_group_id": proc.pid})
            write_receipt(receipts / "apply-start.json", start)
            try:
                rc = proc.wait(timeout=timeout_seconds)
                timed_out = False
            except TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                rc = proc.wait(timeout=5)
                timed_out = True
        exit_receipt = {"schema": APPLY_EXIT_SCHEMA, "returncode": rc, "timed_out": timed_out, "stdout_path": str(child_stdout), "stderr_path": str(child_stderr), "wall_time_utc": utc_now()}
        write_receipt(receipts / "apply-exit.json", exit_receipt)
        post = postcheck_package_identity(package_root, cli_link, expected_version="2026.5.7")
        write_receipt(receipts / "postcheck.json", post)
        if rc == 0 and post.get("ok"):
            terminal = "PASS_PACKAGE_INSTALLED_HOLD_FOR_SEPARATE_RESTART"
            status_value = "PASS"
            recovery = {"schema": RUNNER_SCHEMA + ".recovery_decision", "required": False, "terminal": terminal, "wall_time_utc": utc_now()}
        else:
            recovery = {"schema": RUNNER_SCHEMA + ".recovery_decision", "required": True, "terminal": "ROLLBACK_REQUIRED", "reason": "apply_exit_or_postcheck_failed", "wall_time_utc": utc_now()}
            write_receipt(receipts / "recovery-decision.json", recovery)
            restore_result = restore_from_full_restore_point(root / "restore-point", package_root, cli_link)
            write_receipt(receipts / "recovery-action.json", restore_result)
            terminal = "ROLLBACK_PASS" if postcheck_package_identity(package_root, cli_link, expected_version="2026.5.7").get("ok") else "ROLLBACK_FAIL_OPERATOR_REQUIRED"
            status_value = "HOLD" if terminal != "ROLLBACK_PASS" else "PASS"
        write_receipt(receipts / "recovery-decision.json", recovery)
        status = {"schema": STATUS_SCHEMA, "status": status_value, "terminal_status": terminal, "live_apply_executed": True, "restart_authorised": False, "functional_smoke_authorised": False, "provider_or_live_smoke_calls": 0, "gateway_restart_actions": 0, "systemctl_actions": 0, "config_or_cron_mutations": 0, "target_roots": targets, "wall_time_utc": utc_now()}
        write_receipt(root / "STATUS.json", status)
        write_receipt(root / "final-report.json", {"schema": FINAL_SCHEMA, "terminal_status": terminal, "status": status_value, "next_boundary": "separate_gateway_restart_or_smoke_only_if_authorized", "wall_time_utc": utc_now()})
        return status
    except Exception as exc:  # noqa: BLE001
        status = {"schema": STATUS_SCHEMA, "status": "HOLD", "terminal_status": "FAIL_SAFE_NO_MUTATION", "error": type(exc).__name__ + ":" + str(exc), "live_apply_executed": False, "wall_time_utc": utc_now()}
        write_receipt(root / "STATUS.json", status)
        return status
    finally:
        release_lock(lock_fd, lock_receipt, receipts)


def query_status(transaction_root: str | Path) -> dict[str, Any]:
    root = exact_abs(transaction_root, field="transaction_root")
    status_path = root / "STATUS.json"
    return load_json(status_path) if status_path.exists() else {"schema": STATUS_SCHEMA, "status": "UNKNOWN", "transaction_root": str(root)}


def final_report(transaction_root: str | Path) -> str:
    root = exact_abs(transaction_root, field="transaction_root")
    path = root / "final-report.json"
    return path.read_text(encoding="utf-8") if path.exists() else json.dumps(query_status(root), indent=2, sort_keys=True)


def _main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Critical Apply durable observer runner")
    sub = ap.add_subparsers(dest="cmd", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--name", required=True)
    prep.add_argument("--transaction-root", required=True)
    prep.add_argument("--enabled-envelope", required=True)
    prep.add_argument("--review-plan", required=True)
    exe = sub.add_parser("execute")
    exe.add_argument("--transaction-root", required=True)
    exe.add_argument("--enabled-envelope", required=True)
    exe.add_argument("--review-plan", required=True)
    exe.add_argument("--owner-authorization-phrase", required=True)
    exe.add_argument("--execute-live-package-apply", action="store_true")
    exe.add_argument("--allowed-root", action="append", default=[])
    exe.add_argument("--expected-authority-sha256")
    exe.add_argument("--expected-spec-sha256")
    exe.add_argument("--timeout-seconds", type=float, default=120.0)
    st = sub.add_parser("status")
    st.add_argument("--transaction-root", required=True)
    fr = sub.add_parser("final-report")
    fr.add_argument("--transaction-root", required=True)
    child = sub.add_parser("_apply-child")
    child.add_argument("--transaction-root", required=True)
    child.add_argument("--staged-package-root", required=True)
    child.add_argument("--target-package-root", required=True)
    child.add_argument("--target-cli-link", required=True)
    ns = ap.parse_args(argv)
    if ns.cmd == "prepare":
        print(json.dumps(prepare_transaction(transaction_root=ns.transaction_root, enabled_envelope=ns.enabled_envelope, review_plan=ns.review_plan, name=ns.name), sort_keys=True))
        return 0
    if ns.cmd == "execute":
        result = execute_package_apply(transaction_root=ns.transaction_root, enabled_envelope=ns.enabled_envelope, review_plan=ns.review_plan, owner_authorization_phrase=ns.owner_authorization_phrase, allowed_root=ns.allowed_root, expected_authority_sha256=ns.expected_authority_sha256, expected_spec_sha256=ns.expected_spec_sha256, execute_live_package_apply=ns.execute_live_package_apply, timeout_seconds=ns.timeout_seconds)
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get("status") == "PASS" else 1
    if ns.cmd == "status":
        print(json.dumps(query_status(ns.transaction_root), sort_keys=True)); return 0
    if ns.cmd == "final-report":
        print(final_report(ns.transaction_root)); return 0
    if ns.cmd == "_apply-child":
        return child_apply(ns.transaction_root, ns.staged_package_root, ns.target_package_root, ns.target_cli_link)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main())
