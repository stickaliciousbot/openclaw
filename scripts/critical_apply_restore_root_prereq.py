#!/usr/bin/python3
"""Critical Apply M6 restore-root prerequisite child entrypoint.

This is an exact child entrypoint for the bootstrap prerequisite transaction. It
can create and mode-check a restore root when executed by a durable parent
observer. Tests use temporary fixture roots only; production restore-root use is
not authorised by importing this module.
"""
from __future__ import annotations

import argparse
import json
import os
import stat
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA = "critical_apply.restore_root_prereq.v1"
DEFAULT_MODE = 0o700


class RestoreRootPrereqError(ValueError):
    pass


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _stat_record(path: Path) -> Mapping[str, Any]:
    if not path.exists():
        return {"exists": False, "path": str(path)}
    st = path.stat()
    return {
        "exists": True,
        "path": str(path),
        "is_dir": stat.S_ISDIR(st.st_mode),
        "mode": oct(stat.S_IMODE(st.st_mode)),
        "uid": st.st_uid,
        "gid": st.st_gid,
        "size": st.st_size,
    }


def _write_json(path: Path, data: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def validate_restore_root(path: Path, *, expected_uid: int | None = None, expected_gid: int | None = None, expected_mode: int = DEFAULT_MODE) -> list[str]:
    reasons: list[str] = []
    if not path.exists():
        reasons.append("restore_root_missing")
        return reasons
    st = path.stat()
    if not stat.S_ISDIR(st.st_mode):
        reasons.append("restore_root_not_directory")
    if stat.S_IMODE(st.st_mode) != expected_mode:
        reasons.append("restore_root_mode_mismatch")
    if expected_uid is not None and st.st_uid != expected_uid:
        reasons.append("restore_root_uid_mismatch")
    if expected_gid is not None and st.st_gid != expected_gid:
        reasons.append("restore_root_gid_mismatch")
    return reasons


def ensure_restore_root(*, restore_root: Path, receipt_root: Path, expected_uid: int | None = None, expected_gid: int | None = None, expected_mode: int = DEFAULT_MODE) -> Mapping[str, Any]:
    restore_root = restore_root.resolve()
    receipt_root = receipt_root.resolve()
    receipt_root.mkdir(parents=True, mode=0o700, exist_ok=True)
    pre = _stat_record(restore_root)
    _write_json(receipt_root / "pre-restore-root-state.json", {"schema": SCHEMA + ".pre", "wall_time_utc": _utc_now(), "restore_root": pre})
    restore_root.mkdir(parents=True, exist_ok=True)
    os.chmod(restore_root, expected_mode)
    post = _stat_record(restore_root)
    reasons = validate_restore_root(restore_root, expected_uid=expected_uid, expected_gid=expected_gid, expected_mode=expected_mode)
    status = {
        "schema": SCHEMA + ".status",
        "terminal": "PASS_RESTORE_ROOT_PREREQ_CREATED_OR_VERIFIED" if not reasons else "HOLD_RESTORE_ROOT_PREREQ_VALIDATION_FAILED",
        "pass": not reasons,
        "failed_gates": reasons,
        "restore_root": str(restore_root),
        "receipt_root": str(receipt_root),
        "pre_exists": bool(pre.get("exists")),
        "post_state": post,
        "filesystem_mutations": 1,
        "service_or_runtime_activation_actions": 0,
        "installs_restarts_or_production_mutations": 0,
        "gateway_config_or_cron_mutations": 0,
        "network_or_provider_calls": 0,
        "wall_time_utc": _utc_now(),
    }
    _write_json(receipt_root / "STATUS.json", status)
    return status


def _main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Critical Apply restore-root prerequisite child")
    ap.add_argument("--restore-root", required=True)
    ap.add_argument("--receipt-root", required=True)
    ap.add_argument("--expected-uid", type=int)
    ap.add_argument("--expected-gid", type=int)
    ap.add_argument("--expected-mode", default="0700")
    ns = ap.parse_args(argv)
    mode = int(str(ns.expected_mode), 8)
    status = ensure_restore_root(
        restore_root=Path(ns.restore_root),
        receipt_root=Path(ns.receipt_root),
        expected_uid=ns.expected_uid,
        expected_gid=ns.expected_gid,
        expected_mode=mode,
    )
    print(json.dumps(status, sort_keys=True))
    return 0 if status["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(_main())
