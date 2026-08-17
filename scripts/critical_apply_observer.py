#!/usr/bin/env python3
"""Critical Apply M4 durable observer service code.

Source/fixture only. M4 does not install this as a live service. The observer
hydrates explicit transaction roots, consumes durable controller requests, and
runs fixture/shadow commands through the worker's blocked-child protocol.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from critical_apply_atomic_io import atomic_create_json, atomic_replace_json, read_json_artifact
from critical_apply_contracts import ContractError
from critical_apply_journal import read_boot_id
from critical_apply_process import EXEC_SPEC_SCHEMA, ExactExecSpec
from critical_apply_rehydrate import rehydrate_transaction
from critical_apply_worker import execute_fixture_transaction, write_heartbeat

OBSERVER_STATUS_SCHEMA = "critical_apply.observer_status.v2"
OBSERVER_CONTRACT_SCHEMA = "critical_apply.observer_contract.v2"

class ObserverError(ContractError):
    pass

@dataclass(frozen=True)
class ObserverStatus:
    schema: str
    transaction_root: str
    transaction_id: str | None
    observer_generation: int
    phase: str
    pid: int
    boot_id: str
    wall_time_utc: str
    controller_required: bool
    def to_json(self): return asdict(self)


def utc_now(): return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def _status(root: Path, *, tx: str | None, generation: int, phase: str) -> ObserverStatus:
    st=ObserverStatus(OBSERVER_STATUS_SCHEMA,str(root),tx,generation,phase,os.getpid(),read_boot_id(),utc_now(),False)
    atomic_replace_json(root/"observer-status.json", st.to_json(), root=root); return st


def _load_exec_spec(root: Path) -> ExactExecSpec:
    d=read_json_artifact(root/"exec-spec.json", root=root)
    return ExactExecSpec(d["schema"], d["executable"], tuple(d["argv"]), d["expected_sha256"], d["cwd"], dict(d.get("env",{})), d["stdout_path"], d["stderr_path"], d.get("stdin_policy","devnull"), d.get("uid"), d.get("gid"), int(d.get("umask",0o077)), float(d.get("timeout_seconds",5.0)), float(d.get("graceful_timeout_seconds",0.5)), float(d.get("forced_timeout_seconds",0.5)), bool(d.get("allow_script_interpreter", True)), d.get("resource_limits"))


def observer_contract() -> Mapping[str, Any]:
    return {"schema":OBSERVER_CONTRACT_SCHEMA,"foreground_client_authoritative":False,"durable_transaction_truth":True,"blocked_child_required":True,"receipt_before_mutation_release":True,"rerun_primary_after_rehydrate":False,"fixture_only_in_m4":True,"production_install_authorised":False}


def observe_once(transaction_root: Path, *, lock_root: Path | None = None, allowed_roots: Sequence[Path] | None = None) -> Mapping[str, Any]:
    root=Path(transaction_root).resolve(strict=True); (root/"receipts").mkdir(mode=0o700, exist_ok=True)
    reh=rehydrate_transaction(root, {"observer":"m4"})
    tx=reh.transaction_id; generation=reh.observer_generation
    _status(root, tx=tx, generation=generation, phase="rehydrated")
    if not (root/"requests/execute-request.json").exists():
        write_heartbeat(root, transaction_id=tx, observer_generation=generation, phase="waiting_for_request")
        return {"classification":"NO_EXECUTE_REQUEST", "rehydration": reh.to_json()}
    if (root/"worker-result.json").exists() or (root/"receipts/mutation-release.json").exists():
        # Never rerun primary. If worker result is missing after release, rehydrate/classify only.
        return {"classification":"NO_RERUN_AFTER_PRIMARY_EVIDENCE", "rehydration": reh.to_json()}
    env=read_json_artifact(root/"authority-envelope.json", root=root)
    spec=_load_exec_spec(root)
    lr=Path(lock_root or root/"locks"); lr.mkdir(mode=0o700, parents=True, exist_ok=True)
    roots=list(allowed_roots or [root])
    _status(root, tx=tx, generation=generation, phase="executing")
    res=execute_fixture_transaction(transaction_root=root, lock_root=lr, envelope=env, exec_spec=spec, allowed_roots=roots, observer_generation=generation)
    _status(root, tx=tx, generation=generation, phase="terminal_or_holding")
    return res.to_json()


def observe_loop(
    transaction_root: Path,
    *,
    lock_root: Path | None = None,
    allowed_roots: Sequence[Path] | None = None,
    poll_seconds: float = 0.05,
    max_iterations: int | None = None,
    return_after_terminal: bool = True,
) -> Mapping[str, Any]:
    i=0; last={"classification":"NOT_STARTED"}
    while max_iterations is None or i < max_iterations:
        last=observe_once(transaction_root, lock_root=lock_root, allowed_roots=allowed_roots)
        if last.get("classification") not in ("NO_EXECUTE_REQUEST",):
            if return_after_terminal:
                return last
        time.sleep(poll_seconds); i+=1
    return last


def _main(argv: Sequence[str] | None = None) -> int:
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd", required=True)
    o=sub.add_parser("observe"); o.add_argument("--transaction-root", required=True); o.add_argument("--lock-root"); o.add_argument("--allowed-root", action="append") ; o.add_argument("--loop", action="store_true")
    o.add_argument("--stay-alive-after-terminal", action="store_true")
    c=sub.add_parser("contract")
    ns=ap.parse_args(argv)
    if ns.cmd=="contract": print(json.dumps(observer_contract(), sort_keys=True)); return 0
    roots=[Path(x) for x in (ns.allowed_root or [ns.transaction_root])]
    result=observe_loop(Path(ns.transaction_root), lock_root=Path(ns.lock_root) if ns.lock_root else None, allowed_roots=roots, return_after_terminal=not ns.stay_alive_after_terminal) if ns.loop else observe_once(Path(ns.transaction_root), lock_root=Path(ns.lock_root) if ns.lock_root else None, allowed_roots=roots)
    print(json.dumps(result, sort_keys=True)); return 0

if __name__ == "__main__": raise SystemExit(_main())
