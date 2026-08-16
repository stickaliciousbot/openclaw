#!/usr/bin/env python3
"""Critical Apply M5 service unit template contract.

This module is source/fixture evidence only. It renders a pinned service-unit
proposal for offline inspection. It never writes systemd files, never enables or
starts a service, and never mutates production.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

SERVICE_TEMPLATE_SCHEMA = "critical_apply.service_unit_template.v1"
SERVICE_NAME = "openclaw-critical-apply.service"
STATE_ROOT = "/home/stickai/.openclaw/artifacts/critical-apply"
SERVICE_TRANSACTION_ROOT = STATE_ROOT + "/current"
LOCK_ROOT = "/home/stickai/.openclaw/locks"
RESTORE_ROOT = "/home/stickai/.openclaw/restore-points"
EXEC_START = " ".join([
    "/usr/bin/python3",
    "/home/stickai/.openclaw/workspace/scripts/critical_applyd.py",
    "observe",
    "--transaction-root", SERVICE_TRANSACTION_ROOT,
    "--lock-root", LOCK_ROOT,
    "--allowed-root", STATE_ROOT,
    "--allowed-root", RESTORE_ROOT,
    "--loop",
    "--poll-seconds", "5",
    "--create-transaction-root",
])


def service_unit_template() -> str:
    return "\n".join([
        "[Unit]",
        "Description=OpenClaw Critical Apply HRL-3 Observer",
        "Documentation=https://docs.openclaw.ai",
        "After=network-online.target",
        "",
        "[Service]",
        "Type=simple",
        "User=stickai",
        "Group=stickai",
        "UMask=0077",
        f"ExecStart={EXEC_START}",
        "Restart=on-failure",
        "RestartSec=2",
        "KillMode=control-group",
        "NoNewPrivileges=true",
        "PrivateTmp=true",
        "ProtectSystem=strict",
        "ProtectHome=read-only",
        f"ReadWritePaths={STATE_ROOT}",
        f"ReadWritePaths={LOCK_ROOT}",
        f"ReadWritePaths={RESTORE_ROOT}",
        "ReadWritePaths=/home/stickai/.npm-global/lib/node_modules",
        "ReadWritePaths=/home/stickai/.npm-global/bin",
        "",
        "[Install]",
        "WantedBy=multi-user.target",
        "",
    ])


def service_unit_contract() -> Mapping[str, Any]:
    text = service_unit_template()
    return {
        "schema": SERVICE_TEMPLATE_SCHEMA,
        "service_name": SERVICE_NAME,
        "exec_start": EXEC_START,
        "state_root": STATE_ROOT,
        "service_transaction_root": SERVICE_TRANSACTION_ROOT,
        "lock_root": LOCK_ROOT,
        "restore_root": RESTORE_ROOT,
        "source_fixture_only": True,
        "writes_service_file": False,
        "enables_or_starts_service": False,
        "uses_system_level_supervisor": True,
        "uses_user_session_bus": False,
        "contains_restart_policy": "Restart=on-failure" in text,
        "contains_control_group_kill": "KillMode=control-group" in text,
        "contains_strict_system_protection": "ProtectSystem=strict" in text,
    }


def validate_service_unit_template() -> Mapping[str, Any]:
    text = service_unit_template()
    reasons = []
    required = [
        "ExecStart=" + EXEC_START,
        "critical_applyd.py observe",
        "--transaction-root " + SERVICE_TRANSACTION_ROOT,
        "--lock-root " + LOCK_ROOT,
        "--create-transaction-root",
        "Restart=on-failure",
        "KillMode=control-group",
        "NoNewPrivileges=true",
        "ProtectSystem=strict",
        "ProtectHome=read-only",
        "ReadWritePaths=" + STATE_ROOT,
        "ReadWritePaths=" + LOCK_ROOT,
        "ReadWritePaths=" + RESTORE_ROOT,
    ]
    for item in required:
        if item not in text:
            reasons.append("missing:" + item)
    forbidden = ["systemctl --user", "WantedBy=default.target", "ExecStart=/bin/sh", "ExecStart=/usr/bin/env bash"]
    for item in forbidden:
        if item in text:
            reasons.append("forbidden:" + item)
    return {"schema": SERVICE_TEMPLATE_SCHEMA + ".validation", "ok": not reasons, "reasons": reasons, "line_count": len(text.splitlines())}


if __name__ == "__main__":
    print(service_unit_template())
