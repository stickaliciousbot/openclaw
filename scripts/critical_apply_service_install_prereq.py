#!/usr/bin/env python3
"""Critical Apply service-install prerequisite child entrypoint.

This child owns the file-level service-unit install primitive for the future
M7/M8 durable parent observer transaction. It can render, snapshot, write, and
verify a service unit path, but it never runs systemctl, never enables/starts a
service, and never restarts Gateway or mutates OpenClaw packages.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from critical_apply_service_template import service_unit_template

SCHEMA = "critical_apply.service_install_prereq.v1"
DEFAULT_MODE = 0o644
SYSTEM_SERVICE_ROOT = Path("/etc/systemd/system")


class ServiceInstallPrereqError(ValueError):
    pass


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_json(path: Path, data: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _stat_record(path: Path) -> Mapping[str, Any]:
    if not path.exists():
        return {"exists": False, "path": str(path)}
    st = path.stat()
    return {
        "exists": True,
        "path": str(path),
        "is_file": stat.S_ISREG(st.st_mode),
        "is_dir": stat.S_ISDIR(st.st_mode),
        "mode": oct(stat.S_IMODE(st.st_mode)),
        "uid": st.st_uid,
        "gid": st.st_gid,
        "size": st.st_size,
        "sha256": _sha256_file(path),
    }


def _validate_exact_path(path: Path, *, field: str) -> Path:
    if not path.is_absolute():
        raise ServiceInstallPrereqError(f"{field}_must_be_absolute")
    if ".." in path.parts:
        raise ServiceInstallPrereqError(f"{field}_must_not_contain_parent_traversal")
    return path


def _system_service_path(path: Path) -> bool:
    try:
        path.resolve().relative_to(SYSTEM_SERVICE_ROOT)
        return True
    except ValueError:
        return False


def _pid_alive(pid: int) -> bool | None:
    if pid <= 0:
        return None
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return None


def _read_lock_state(lock_path: Path) -> Mapping[str, Any]:
    try:
        data = json.loads(lock_path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"unparseable": True}
    except Exception as exc:  # noqa: BLE001 - stale lock inspection must fail closed
        return {"read_error": type(exc).__name__ + ":" + str(exc)}


def _clear_stale_maintenance_lock(lock_path: Path, *, receipt_root: Path) -> Mapping[str, Any]:
    state = _read_lock_state(lock_path)
    pid = int(state.get("pid") or 0) if isinstance(state.get("pid"), int) or str(state.get("pid") or "").isdigit() else 0
    alive = _pid_alive(pid)
    detected = {
        "schema": SCHEMA + ".stale_maintenance_lock_detected",
        "lock_path": str(lock_path),
        "previous_state": state,
        "previous_pid": pid or None,
        "previous_pid_alive": alive,
        "wall_time_utc": _utc_now(),
    }
    _write_json(receipt_root / "stale-maintenance-lock-detected.json", detected)
    if alive is not False:
        raise ServiceInstallPrereqError("maintenance_lock_exists_and_is_not_proven_stale")
    lock_path.unlink()
    cleared = {**detected, "schema": SCHEMA + ".stale_maintenance_lock_cleared", "cleared": True, "cleared_wall_time_utc": _utc_now()}
    _write_json(receipt_root / "stale-maintenance-lock-cleared.json", cleared)
    return cleared


def _acquire_maintenance_lock(lock_root: Path | None, *, receipt_root: Path) -> Mapping[str, Any]:
    if lock_root is None:
        return {"required": False, "acquired": False, "released": False}
    lock_root = _validate_exact_path(lock_root, field="lock_root")
    lock_root.mkdir(parents=True, mode=0o700, exist_ok=True)
    lock_path = lock_root / "critical-apply-service-install.lock"
    stale_recovery: Mapping[str, Any] | None = None
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        stale_recovery = _clear_stale_maintenance_lock(lock_path, receipt_root=receipt_root)
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    acquired = {"schema": SCHEMA + ".maintenance_lock", "required": True, "acquired": True, "released": False, "lock_path": str(lock_path), "pid": os.getpid(), "stale_recovery": stale_recovery, "wall_time_utc": _utc_now()}
    os.write(fd, (json.dumps(acquired, sort_keys=True) + "\n").encode("utf-8"))
    os.close(fd)
    _write_json(receipt_root / "maintenance-lock-acquired.json", acquired)
    return acquired


def _release_maintenance_lock(lock_state: Mapping[str, Any], *, receipt_root: Path) -> Mapping[str, Any]:
    if not lock_state.get("acquired"):
        return dict(lock_state)
    lock_path = Path(str(lock_state["lock_path"]))
    released = {**dict(lock_state), "released": True, "released_wall_time_utc": _utc_now()}
    try:
        lock_path.unlink()
    except FileNotFoundError:
        released = {**released, "release_warning": "lock_already_absent"}
    _write_json(receipt_root / "maintenance-lock-released.json", released)
    return released


def _snapshot_existing_unit(*, service_unit_path: Path, snapshot_root: Path) -> Mapping[str, Any]:
    snapshot_root.mkdir(parents=True, mode=0o700, exist_ok=True)
    pre = _stat_record(service_unit_path)
    if pre.get("exists") and service_unit_path.is_file():
        copy_path = snapshot_root / "previous-service-unit"
        shutil.copy2(service_unit_path, copy_path)
        os.chmod(copy_path, 0o600)
        pre = {**pre, "snapshot_copy": str(copy_path), "snapshot_sha256": _sha256_file(copy_path)}
    else:
        marker = snapshot_root / "previous-service-unit.absent.json"
        _write_json(marker, {"schema": SCHEMA + ".absent", "service_unit_path": str(service_unit_path), "wall_time_utc": _utc_now()})
        pre = {**pre, "snapshot_absent_marker": str(marker)}
    _write_json(snapshot_root / "snapshot-state.json", {"schema": SCHEMA + ".snapshot", "service_unit_path": str(service_unit_path), "pre_state": pre, "wall_time_utc": _utc_now()})
    return pre


def render_install_verify_service_unit(*, service_unit_path: Path, receipt_root: Path, restore_root: Path, expected_mode: int = DEFAULT_MODE, lock_root: Path | None = None, allow_system_path: bool = False) -> Mapping[str, Any]:
    service_unit_path = _validate_exact_path(service_unit_path, field="service_unit_path")
    receipt_root = _validate_exact_path(receipt_root, field="receipt_root")
    restore_root = _validate_exact_path(restore_root, field="restore_root")
    if _system_service_path(service_unit_path) and not allow_system_path:
        raise ServiceInstallPrereqError("system_service_path_requires_explicit_allow_system_path")
    if _system_service_path(service_unit_path) and lock_root is None:
        raise ServiceInstallPrereqError("system_service_path_requires_maintenance_lock_root")
    receipt_root.mkdir(parents=True, mode=0o700, exist_ok=True)
    lock_state = _acquire_maintenance_lock(lock_root, receipt_root=receipt_root)
    try:
        restore_root.mkdir(parents=True, mode=0o700, exist_ok=True)
        snapshot_root = restore_root / f"service-install-{int(time.time())}-{os.getpid()}"
        pre = _snapshot_existing_unit(service_unit_path=service_unit_path, snapshot_root=snapshot_root)
        text = service_unit_template()
        rendered_sha = _sha256_text(text)
        _write_json(receipt_root / "pre-service-unit-state.json", {"schema": SCHEMA + ".pre", "service_unit_path": str(service_unit_path), "pre_state": pre, "rendered_sha256": rendered_sha, "snapshot_root": str(snapshot_root), "wall_time_utc": _utc_now()})
        service_unit_path.parent.mkdir(parents=True, mode=0o755, exist_ok=True)
        tmp = service_unit_path.with_name(f".{service_unit_path.name}.tmp-{os.getpid()}")
        tmp.write_text(text, encoding="utf-8")
        os.chmod(tmp, expected_mode)
        os.replace(tmp, service_unit_path)
        os.chmod(service_unit_path, expected_mode)
        post = _stat_record(service_unit_path)
        reasons: list[str] = []
        if not service_unit_path.is_file():
            reasons.append("service_unit_missing_after_write")
        if post.get("sha256") != rendered_sha:
            reasons.append("service_unit_sha256_mismatch")
        if post.get("mode") != oct(expected_mode):
            reasons.append("service_unit_mode_mismatch")
        lock_state = _release_maintenance_lock(lock_state, receipt_root=receipt_root)
    except Exception:
        _release_maintenance_lock(lock_state, receipt_root=receipt_root)
        raise
    status = {
        "schema": SCHEMA + ".status",
        "status": "PASS" if not reasons else "HOLD",
        "closeout_status": "PASS" if not reasons else "HOLD",
        "terminal": "PASS_SERVICE_INSTALL_PREREQ_RENDERED_WRITTEN_VERIFIED" if not reasons else "HOLD_SERVICE_INSTALL_PREREQ_VALIDATION_FAILED",
        "terminal_status": "PASS_SERVICE_INSTALL_PREREQ_RENDERED_WRITTEN_VERIFIED" if not reasons else "HOLD_SERVICE_INSTALL_PREREQ_VALIDATION_FAILED",
        "pass": not reasons,
        "failed_gates": reasons,
        "service_unit_path": str(service_unit_path),
        "receipt_root": str(receipt_root),
        "restore_root": str(restore_root),
        "snapshot_root": str(snapshot_root),
        "rendered_sha256": rendered_sha,
        "maintenance_lock": lock_state,
        "system_path_authorized": bool(allow_system_path),
        "pre_state": pre,
        "post_state": post,
        "filesystem_mutations": 1,
        "restore_snapshot_mutations": 1,
        "systemctl_actions": 0,
        "service_enable_start_actions": 0,
        "daemon_reload_actions": 0,
        "gateway_config_or_cron_mutations": 0,
        "network_or_provider_calls": 0,
        "installs_restarts_or_production_mutations": 0,
        "service_or_runtime_activation_actions": 0,
        "wall_time_utc": _utc_now(),
    }
    summary = {
        "schema": SCHEMA + ".summary",
        "ok": not reasons,
        "closeout_status": status["closeout_status"],
        "terminal_status": status["terminal_status"],
        "classification": "SERVICE_INSTALL_PREREQ_RENDERED_WRITTEN_VERIFIED" if not reasons else "SERVICE_INSTALL_PREREQ_VALIDATION_FAILED",
        "service_unit_path": str(service_unit_path),
        "receipt_root": str(receipt_root),
        "restore_root": str(restore_root),
        "snapshot_root": str(snapshot_root),
        "failed_gates": reasons,
        "wall_time_utc": status["wall_time_utc"],
    }
    _write_json(receipt_root / "STATUS.json", status)
    _write_json(receipt_root / "status.json", status)
    _write_json(receipt_root / "summary.json", summary)
    return status


def _failure_status(*, receipt_root: Path | None, service_unit_path: Path | None, restore_root: Path | None, reason: str) -> Mapping[str, Any]:
    status = {
        "schema": SCHEMA + ".status",
        "status": "HOLD",
        "closeout_status": "HOLD",
        "terminal": "HOLD_SERVICE_INSTALL_PREREQ_EXCEPTION_FAILED_CLOSED",
        "terminal_status": "HOLD_SERVICE_INSTALL_PREREQ_EXCEPTION_FAILED_CLOSED",
        "pass": False,
        "failed_gates": [reason],
        "service_unit_path": str(service_unit_path) if service_unit_path else None,
        "receipt_root": str(receipt_root) if receipt_root else None,
        "restore_root": str(restore_root) if restore_root else None,
        "systemctl_actions": 0,
        "service_enable_start_actions": 0,
        "daemon_reload_actions": 0,
        "gateway_config_or_cron_mutations": 0,
        "network_or_provider_calls": 0,
        "installs_restarts_or_production_mutations": 0,
        "service_or_runtime_activation_actions": 0,
        "wall_time_utc": _utc_now(),
    }
    if receipt_root is not None:
        try:
            receipt_root.mkdir(parents=True, mode=0o700, exist_ok=True)
            _write_json(receipt_root / "STATUS.json", status)
            _write_json(receipt_root / "status.json", status)
            _write_json(receipt_root / "summary.json", {"schema": SCHEMA + ".summary", "ok": False, "closeout_status": "HOLD", "terminal_status": status["terminal_status"], "classification": "SERVICE_INSTALL_PREREQ_EXCEPTION_FAILED_CLOSED", "failed_gates": [reason], "wall_time_utc": status["wall_time_utc"]})
        except Exception:
            pass
    return status


def _main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Critical Apply service install prerequisite child")
    ap.add_argument("--service-unit-path", required=True)
    ap.add_argument("--receipt-root", required=True)
    ap.add_argument("--restore-root", required=True)
    ap.add_argument("--expected-mode", default="0644")
    ap.add_argument("--lock-root")
    ap.add_argument("--allow-system-path", action="store_true")
    ns = ap.parse_args(argv)
    service_unit_path = Path(ns.service_unit_path)
    receipt_root = Path(ns.receipt_root)
    restore_root = Path(ns.restore_root)
    try:
        status = render_install_verify_service_unit(
            service_unit_path=service_unit_path,
            receipt_root=receipt_root,
            restore_root=restore_root,
            expected_mode=int(str(ns.expected_mode), 8),
            lock_root=Path(ns.lock_root) if ns.lock_root else None,
            allow_system_path=ns.allow_system_path,
        )
    except Exception as exc:  # noqa: BLE001 - child must fail closed with semantic receipts
        status = _failure_status(receipt_root=receipt_root if receipt_root.is_absolute() else None, service_unit_path=service_unit_path, restore_root=restore_root, reason=type(exc).__name__ + ":" + str(exc))
    print(json.dumps(status, sort_keys=True))
    return 0 if status.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(_main())
