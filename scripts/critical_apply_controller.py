#!/usr/bin/env python3
"""Critical Apply M4 controller/client interface.

The controller prepares fixture transactions and durable requests. It never
spawns the mutation child; the observer/worker owns execution and timeout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import stat
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from critical_apply_atomic_io import atomic_create_json, atomic_replace_json, read_json_artifact, sha256_file
from critical_apply_authority import make_fixture_envelope
from critical_apply_commit import prepare_transaction, record_synthetic_approval
from critical_apply_contracts import canonical_json_dumps
from critical_apply_journal import create_transaction_journal, read_boot_id
from critical_apply_process import EXEC_SPEC_SCHEMA, ExactExecSpec

REQUEST_SCHEMA = "critical_apply.controller_request.v2"
STATUS_SCHEMA = "critical_apply.controller_status.v2"

@dataclass(frozen=True)
class ControllerRequest:
    schema: str
    transaction_id: str
    request: str
    exec_spec_path: str | None
    envelope_path: str | None
    submitted_by: Mapping[str, Any]
    wall_time_utc: str
    monotonic_ns: int
    boot_id: str
    def to_json(self): return asdict(self)


def utc_now(): return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
def _sha_obj(obj: Mapping[str, Any]) -> str: return hashlib.sha256(canonical_json_dumps(obj).encode()).hexdigest()


def prepare_fixture_transaction(*, transaction_root: Path, lock_root: Path, executable: Path, argv_extra: Sequence[str] = (), marker_name: str = "mutation.marker", timeout_seconds: float = 5.0) -> Mapping[str, Any]:
    root = Path(transaction_root).resolve(); root.mkdir(mode=0o700, parents=True, exist_ok=True)
    (root/"logs").mkdir(mode=0o700, exist_ok=True); (root/"requests").mkdir(mode=0o700, exist_ok=True); (root/"receipts").mkdir(mode=0o700, exist_ok=True)
    tx = "critical-apply-m4-fixture-" + time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "-" + secrets.token_hex(16)
    campaign = "critical-campaign-m4-fixture-" + time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "-" + secrets.token_hex(16)
    spec_obj = {"sha256": "a"*64, "fixture_only": True, "marker_name": marker_name}
    env = make_fixture_envelope(tx, campaign, "nonce-"+secrets.token_hex(8), expires_at="2099-01-01T00:00:00Z")
    env["transaction_spec_sha256"] = spec_obj["sha256"]
    env["exec_spec_sha256"] = "b"*64
    create_transaction_journal(root, transaction_id=tx)
    plan = prepare_transaction(root, transaction_spec=spec_obj, envelope=env, surfaces=["surface:openclaw-official-package-root"], plan_sealed_at="2026-07-30T10:05:00Z")
    approval = record_synthetic_approval(root, envelope=env, plan=plan, approved_time="2026-07-30T10:10:00Z")
    exe = Path(executable).resolve(strict=True)
    exec_spec = ExactExecSpec(EXEC_SPEC_SCHEMA, str(exe), tuple([str(exe), str(root/marker_name), *argv_extra]), sha256_file(exe), str(root), {"CRITICAL_APPLY_FIXTURE":"1"}, str(root/"logs/apply.stdout.log"), str(root/"logs/apply.stderr.log"), timeout_seconds=timeout_seconds)
    atomic_create_json(root/"authority-envelope.json", env, root=root)
    atomic_create_json(root/"exec-spec.json", exec_spec.to_json(), root=root)
    return {"transaction_id": tx, "campaign_id": campaign, "transaction_root": str(root), "lock_root": str(Path(lock_root).resolve()), "envelope": env, "exec_spec": exec_spec.to_json(), "approval": approval, "plan": plan.to_json()}


def submit_execution_request(transaction_root: Path) -> ControllerRequest:
    root=Path(transaction_root).resolve(strict=True); (root/"requests").mkdir(mode=0o700, exist_ok=True)
    tx = read_json_artifact(root/"authority-envelope.json", root=root)["transaction_id"]
    req = ControllerRequest(REQUEST_SCHEMA, tx, "execute", "exec-spec.json", "authority-envelope.json", {"component":"critical_apply_controller_m4","pid":os.getpid(),"uid":os.getuid()}, utc_now(), time.monotonic_ns(), read_boot_id())
    atomic_create_json(root/"requests/execute-request.json", req.to_json(), root=root)
    return req


def request_cancellation(transaction_root: Path) -> Mapping[str, Any]:
    root=Path(transaction_root).resolve(strict=True); (root/"requests").mkdir(mode=0o700, exist_ok=True)
    obj={"schema":REQUEST_SCHEMA,"request":"cancel","submitted_by":{"component":"critical_apply_controller_m4","pid":os.getpid()},"wall_time_utc":utc_now(),"monotonic_ns":time.monotonic_ns(),"boot_id":read_boot_id()}
    atomic_replace_json(root/"requests/cancel-request.json", obj, root=root); return obj


def query_status(transaction_root: Path) -> Mapping[str, Any]:
    root=Path(transaction_root).resolve(strict=True)
    files = ["worker-result.json","receipts/rehydration.json","receipts/apply-intent.json","receipts/apply-child-spawned-blocked.json","receipts/mutation-release.json","receipts/apply-exit.json","terminal-seal.json"]
    present={f:(root/f).exists() for f in files}
    result=None
    if present["worker-result.json"]:
        result=read_json_artifact(root/"worker-result.json", root=root)
    return {"schema":STATUS_SCHEMA,"transaction_root":str(root),"present":present,"worker_result":result,"controller_authoritative":False}


def retrieve_final_report(transaction_root: Path) -> str | None:
    p=Path(transaction_root).resolve(strict=True)/"final-report.md"
    return p.read_text(encoding="utf-8") if p.exists() else None


def _main(argv: Sequence[str] | None = None) -> int:
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd", required=True)
    q=sub.add_parser("status"); q.add_argument("--transaction-root", required=True)
    s=sub.add_parser("submit"); s.add_argument("--transaction-root", required=True)
    c=sub.add_parser("cancel"); c.add_argument("--transaction-root", required=True)
    ns=ap.parse_args(argv)
    if ns.cmd=="status": print(json.dumps(query_status(Path(ns.transaction_root)), sort_keys=True)); return 0
    if ns.cmd=="submit": print(json.dumps(submit_execution_request(Path(ns.transaction_root)).to_json(), sort_keys=True)); return 0
    if ns.cmd=="cancel": print(json.dumps(request_cancellation(Path(ns.transaction_root)), sort_keys=True)); return 0
    return 2

if __name__ == "__main__": raise SystemExit(_main())
