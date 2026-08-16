#!/usr/bin/env python3
"""Critical Apply M5 control client facade.

Source/fixture only. This module intentionally does not install, start, or talk to
any live service. It exposes the stable HRL-3 control-client vocabulary expected
by the bootstrap architecture while delegating fixture transaction preparation
and sealed request/status file handling to the preserved M4 controller module.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from critical_apply_controller import (
    prepare_fixture_transaction,
    query_status,
    request_cancellation,
    retrieve_final_report,
    submit_execution_request,
)

CTL_CONTRACT_SCHEMA = "critical_apply.ctl_contract.v1"
CTL_TRANSPORT_SCHEMA = "critical_apply.ctl_transport_policy.v1"


def control_client_contract() -> Mapping[str, Any]:
    return {
        "schema": CTL_CONTRACT_SCHEMA,
        "component": "critical_apply_ctl",
        "foreground_client_authoritative": False,
        "durable_transaction_truth": True,
        "supported_fixture_transport": "sealed_request_files",
        "future_production_transport": "unix_domain_socket_or_sealed_inbox",
        "may_install_or_start_service": False,
        "may_mutate_openclaw_package_gateway_cron_provider": False,
        "fixture_only_until_bootstrap_service_transaction_passes": True,
    }


def transport_policy() -> Mapping[str, Any]:
    return {
        "schema": CTL_TRANSPORT_SCHEMA,
        "accepted_requests": ["execute", "cancel", "status"],
        "request_files": ["requests/execute-request.json", "requests/cancel-request.json"],
        "controller_authoritative": False,
        "observer_or_journal_authoritative": True,
        "network_required_for_fixture_mode": False,
    }


def _main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Critical Apply HRL-3 control facade (fixture/source only)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("contract")
    sub.add_parser("transport-policy")
    st = sub.add_parser("status"); st.add_argument("--transaction-root", required=True)
    sb = sub.add_parser("submit"); sb.add_argument("--transaction-root", required=True)
    cn = sub.add_parser("cancel"); cn.add_argument("--transaction-root", required=True)
    rp = sub.add_parser("report"); rp.add_argument("--transaction-root", required=True)
    ns = ap.parse_args(argv)
    if ns.cmd == "contract":
        print(json.dumps(control_client_contract(), sort_keys=True)); return 0
    if ns.cmd == "transport-policy":
        print(json.dumps(transport_policy(), sort_keys=True)); return 0
    if ns.cmd == "status":
        print(json.dumps(query_status(Path(ns.transaction_root)), sort_keys=True)); return 0
    if ns.cmd == "submit":
        print(json.dumps(submit_execution_request(Path(ns.transaction_root)).to_json(), sort_keys=True)); return 0
    if ns.cmd == "cancel":
        print(json.dumps(request_cancellation(Path(ns.transaction_root)), sort_keys=True)); return 0
    if ns.cmd == "report":
        report = retrieve_final_report(Path(ns.transaction_root))
        print(report or ""); return 0 if report else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(_main())
