#!/usr/bin/env python3
"""Critical Apply M5 daemon facade.

Source/fixture only. This is the stable daemon entrypoint expected by the HRL-3
bootstrap architecture. It does not install itself as a service and does not run
production mutations. Fixture execution is delegated to the preserved observer
module, which owns rehydration and worker launch-gate semantics.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from critical_apply_observer import observe_loop, observe_once, observer_contract
from critical_apply_service_template import service_unit_contract, service_unit_template

DAEMON_CONTRACT_SCHEMA = "critical_apply.daemon_contract.v1"


def daemon_contract() -> Mapping[str, Any]:
    base = dict(observer_contract())
    return {
        "schema": DAEMON_CONTRACT_SCHEMA,
        "component": "critical_applyd",
        "stable_entrypoint": "scripts/critical_applyd.py",
        "observer_contract": base,
        "foreground_client_authoritative": False,
        "supervisor_required_for_production": True,
        "fixture_only_until_service_bootstrap_transaction_passes": True,
        "may_install_or_start_service": False,
        "may_mutate_openclaw_package_gateway_cron_provider": False,
        "service_unit_contract": service_unit_contract(),
    }


def _main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Critical Apply HRL-3 daemon facade (fixture/source only)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("contract")
    sub.add_parser("service-unit-template")
    obs = sub.add_parser("observe")
    obs.add_argument("--transaction-root", required=True)
    obs.add_argument("--lock-root")
    obs.add_argument("--allowed-root", action="append")
    obs.add_argument("--loop", action="store_true")
    obs.add_argument("--max-iterations", type=int)
    obs.add_argument("--poll-seconds", type=float, default=5.0)
    obs.add_argument("--create-transaction-root", action="store_true")
    obs.add_argument("--stay-alive-after-terminal", action="store_true")
    ns = ap.parse_args(argv)
    if ns.cmd == "contract":
        print(json.dumps(daemon_contract(), sort_keys=True)); return 0
    if ns.cmd == "service-unit-template":
        print(service_unit_template()); return 0
    transaction_root = Path(ns.transaction_root)
    if ns.create_transaction_root:
        transaction_root.mkdir(parents=True, mode=0o700, exist_ok=True)
    roots = [Path(x) for x in (ns.allowed_root or [transaction_root])]
    if ns.loop:
        result = observe_loop(
            transaction_root,
            lock_root=Path(ns.lock_root) if ns.lock_root else None,
            allowed_roots=roots,
            poll_seconds=ns.poll_seconds,
            max_iterations=ns.max_iterations,
            return_after_terminal=not ns.stay_alive_after_terminal,
        )
    else:
        result = observe_once(transaction_root, lock_root=Path(ns.lock_root) if ns.lock_root else None, allowed_roots=roots)
    print(json.dumps(result, sort_keys=True)); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
