#!/usr/bin/env python3
"""Critical Apply service activation child entrypoint.

This child is for the future root/operator durable harness transaction that
activates the already-installed Critical Apply service unit. It runs only an
explicit, ordered systemctl action set, records pre/post receipts, and emits
semantic PASS/HOLD receipts. Tests use a fake systemctl path; importing this
module never mutates a live service.
"""
from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA = "critical_apply.service_activation.v1"
DEFAULT_SERVICE_NAME = "openclaw-critical-apply.service"
DEFAULT_ALLOWED_ACTIONS = ("daemon-reload", "enable", "start")
DEFAULT_SYSTEMCTL = "/usr/bin/systemctl"


class ServiceActivationError(ValueError):
    pass


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _write_json(path: Path, data: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _exact_abs(path: Path, *, field: str) -> Path:
    if not path.is_absolute():
        raise ServiceActivationError(f"{field}_must_be_absolute")
    if ".." in path.parts:
        raise ServiceActivationError(f"{field}_must_not_contain_parent_traversal")
    return path


def _stat_record(path: Path) -> Mapping[str, Any]:
    if not path.exists():
        return {"exists": False, "path": str(path)}
    st = path.stat()
    return {
        "exists": True,
        "path": str(path),
        "is_file": stat.S_ISREG(st.st_mode),
        "mode": oct(stat.S_IMODE(st.st_mode)),
        "uid": st.st_uid,
        "gid": st.st_gid,
        "size": st.st_size,
    }


def _acquire_lock(lock_root: Path | None, *, receipt_root: Path) -> Mapping[str, Any]:
    if lock_root is None:
        raise ServiceActivationError("maintenance_lock_root_required")
    lock_root = _exact_abs(lock_root, field="lock_root")
    lock_root.mkdir(parents=True, mode=0o700, exist_ok=True)
    lock_path = lock_root / "critical-apply-service-activation.lock"
    fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    state = {"schema": SCHEMA + ".maintenance_lock", "acquired": True, "released": False, "lock_path": str(lock_path), "pid": os.getpid(), "wall_time_utc": _utc_now()}
    os.write(fd, (json.dumps(state, sort_keys=True) + "\n").encode("utf-8"))
    os.close(fd)
    _write_json(receipt_root / "maintenance-lock-acquired.json", state)
    return state


def _release_lock(lock_state: Mapping[str, Any], *, receipt_root: Path) -> Mapping[str, Any]:
    if not lock_state.get("acquired"):
        return dict(lock_state)
    released = {**dict(lock_state), "released": True, "released_wall_time_utc": _utc_now()}
    try:
        Path(str(lock_state["lock_path"])).unlink()
    except FileNotFoundError:
        released["release_warning"] = "lock_already_absent"
    _write_json(receipt_root / "maintenance-lock-released.json", released)
    return released


def _run_systemctl(systemctl: Path, argv: Sequence[str], *, timeout: float) -> Mapping[str, Any]:
    cmd = [str(systemctl), *argv]
    proc = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout, check=False)
    return {"cmd": cmd, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def _query_state(systemctl: Path, service_name: str, *, timeout: float) -> Mapping[str, Any]:
    return {
        "is_enabled": _run_systemctl(systemctl, ["is-enabled", service_name], timeout=timeout),
        "is_active": _run_systemctl(systemctl, ["is-active", service_name], timeout=timeout),
    }


def activate_service(*, service_name: str, service_unit_path: Path, receipt_root: Path, lock_root: Path, systemctl_path: Path = Path(DEFAULT_SYSTEMCTL), actions: Sequence[str] = DEFAULT_ALLOWED_ACTIONS, timeout_seconds: float = 30.0, allow_service_name: str = DEFAULT_SERVICE_NAME) -> Mapping[str, Any]:
    if service_name != allow_service_name:
        raise ServiceActivationError("service_name_not_explicitly_allowed")
    if tuple(actions) != DEFAULT_ALLOWED_ACTIONS:
        raise ServiceActivationError("actions_must_be_exact_daemon_reload_enable_start")
    service_unit_path = _exact_abs(service_unit_path, field="service_unit_path")
    receipt_root = _exact_abs(receipt_root, field="receipt_root")
    systemctl_path = _exact_abs(systemctl_path, field="systemctl_path")
    if not systemctl_path.exists() or not os.access(systemctl_path, os.X_OK):
        raise ServiceActivationError("systemctl_path_not_executable")
    receipt_root.mkdir(parents=True, mode=0o700, exist_ok=True)
    if not service_unit_path.is_file():
        raise ServiceActivationError("service_unit_missing_before_activation")
    lock_state: Mapping[str, Any] | None = None
    command_results: list[Mapping[str, Any]] = []
    reasons: list[str] = []
    try:
        lock_state = _acquire_lock(lock_root, receipt_root=receipt_root)
        pre = {"service_unit": _stat_record(service_unit_path), "systemctl_state": _query_state(systemctl_path, service_name, timeout=timeout_seconds)}
        _write_json(receipt_root / "pre-activation-state.json", {"schema": SCHEMA + ".pre", "pre_state": pre, "wall_time_utc": _utc_now()})
        for action in actions:
            argv = [action] if action == "daemon-reload" else [action, service_name]
            result = _run_systemctl(systemctl_path, argv, timeout=timeout_seconds)
            command_results.append(result)
            if result["returncode"] != 0:
                reasons.append("systemctl_" + action.replace("-", "_") + "_failed")
                break
        post = {"service_unit": _stat_record(service_unit_path), "systemctl_state": _query_state(systemctl_path, service_name, timeout=timeout_seconds)}
    except Exception as exc:  # noqa: BLE001
        pre = locals().get("pre", {"service_unit": _stat_record(service_unit_path)})
        post = {"service_unit": _stat_record(service_unit_path)}
        reasons.append(type(exc).__name__ + ":" + str(exc))
    finally:
        if lock_state is not None:
            lock_state = _release_lock(lock_state, receipt_root=receipt_root)
    if command_results and not reasons:
        enabled_rc = post["systemctl_state"]["is_enabled"]["returncode"]
        active_rc = post["systemctl_state"]["is_active"]["returncode"]
        if enabled_rc != 0:
            reasons.append("service_not_enabled_after_activation")
        if active_rc != 0:
            reasons.append("service_not_active_after_activation")
    terminal = "PASS_SERVICE_ACTIVATION_DAEMON_RELOAD_ENABLE_START_VERIFIED" if not reasons else "HOLD_SERVICE_ACTIVATION_FAILED_CLOSED"
    status = {
        "schema": SCHEMA + ".status",
        "status": "PASS" if not reasons else "HOLD",
        "closeout_status": "PASS" if not reasons else "HOLD",
        "terminal": terminal,
        "terminal_status": terminal,
        "pass": not reasons,
        "failed_gates": reasons,
        "service_name": service_name,
        "service_unit_path": str(service_unit_path),
        "receipt_root": str(receipt_root),
        "systemctl_path": str(systemctl_path),
        "maintenance_lock": lock_state,
        "pre_state": pre,
        "post_state": post,
        "command_results": command_results,
        "systemctl_actions": len(command_results),
        "daemon_reload_actions": sum(1 for r in command_results if r["cmd"][1] == "daemon-reload"),
        "service_enable_start_actions": sum(1 for r in command_results if r["cmd"][1] in {"enable", "start"}),
        "gateway_config_or_cron_mutations": 0,
        "package_or_runtime_mutations": 0,
        "network_or_provider_calls": 0,
        "wall_time_utc": _utc_now(),
    }
    summary = {"schema": SCHEMA + ".summary", "ok": not reasons, "closeout_status": status["closeout_status"], "terminal_status": terminal, "classification": "SERVICE_ACTIVATION_VERIFIED" if not reasons else "SERVICE_ACTIVATION_FAILED_CLOSED", "failed_gates": reasons, "wall_time_utc": status["wall_time_utc"]}
    _write_json(receipt_root / "STATUS.json", status)
    _write_json(receipt_root / "status.json", status)
    _write_json(receipt_root / "summary.json", summary)
    return status


def _main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Critical Apply service activation child")
    ap.add_argument("--service-name", default=DEFAULT_SERVICE_NAME)
    ap.add_argument("--allow-service-name", default=DEFAULT_SERVICE_NAME)
    ap.add_argument("--service-unit-path", required=True)
    ap.add_argument("--receipt-root", required=True)
    ap.add_argument("--lock-root", required=True)
    ap.add_argument("--systemctl-path", default=DEFAULT_SYSTEMCTL)
    ap.add_argument("--timeout-seconds", type=float, default=30.0)
    ns = ap.parse_args(argv)
    try:
        status = activate_service(service_name=ns.service_name, allow_service_name=ns.allow_service_name, service_unit_path=Path(ns.service_unit_path), receipt_root=Path(ns.receipt_root), lock_root=Path(ns.lock_root), systemctl_path=Path(ns.systemctl_path), timeout_seconds=ns.timeout_seconds)
    except Exception as exc:  # noqa: BLE001
        receipt = Path(ns.receipt_root)
        status = {"schema": SCHEMA + ".status", "status": "HOLD", "closeout_status": "HOLD", "terminal": "HOLD_SERVICE_ACTIVATION_FAILED_CLOSED", "terminal_status": "HOLD_SERVICE_ACTIVATION_FAILED_CLOSED", "pass": False, "failed_gates": [type(exc).__name__ + ":" + str(exc)], "service_name": ns.service_name, "service_unit_path": ns.service_unit_path, "receipt_root": ns.receipt_root, "systemctl_actions": 0, "daemon_reload_actions": 0, "service_enable_start_actions": 0, "gateway_config_or_cron_mutations": 0, "package_or_runtime_mutations": 0, "network_or_provider_calls": 0, "wall_time_utc": _utc_now()}
        if receipt.is_absolute():
            try:
                _write_json(receipt / "STATUS.json", status)
                _write_json(receipt / "status.json", status)
                _write_json(receipt / "summary.json", {"schema": SCHEMA + ".summary", "ok": False, "closeout_status": "HOLD", "terminal_status": status["terminal_status"], "classification": "SERVICE_ACTIVATION_FAILED_CLOSED", "failed_gates": status["failed_gates"], "wall_time_utc": status["wall_time_utc"]})
            except Exception:
                pass
    print(json.dumps(status, sort_keys=True))
    return 0 if status.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(_main())
