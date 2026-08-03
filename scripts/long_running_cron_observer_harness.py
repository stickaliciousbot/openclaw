#!/usr/bin/env python3
"""Clean-lineage durable observer candidate.

This file is an isolated candidate implementation. It is inert until a later,
separately authorised isolated validation phase imports or executes it. It does
not contain production defaults, live service endpoints, or repository target
paths. All filesystem/process inputs are injected by a caller.
"""
from __future__ import annotations

import hashlib
import json
import os
import signal
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Literal

TERMINALS = {"PASS", "FAIL", "HOLD", "BLOCKED"}
STATES = [
    "PREPARED", "OBSERVER_STARTING", "OBSERVER_READY", "APPLY_NOT_STARTED",
    "APPLY_RUNNING", "APPLY_EXITED_SUCCESS", "APPLY_EXITED_FAILURE",
    "APPLY_IDENTITY_LOST", "PACKAGE_HEALTH_CHECK", "ROLLBACK_ELIGIBILITY_CHECK",
    "ROLLBACK_REQUIRED", "ROLLBACK_NOT_AUTHORISED", "ROLLBACK_RUNNING",
    "ROLLBACK_SUCCEEDED", "ROLLBACK_FAILED", "TERMINALISING",
    "PASS", "FAIL", "HOLD", "BLOCKED",
]
PERMITTED_TRANSITIONS = {
    ("PREPARED", "OBSERVER_STARTING", "controller"),
    ("OBSERVER_STARTING", "OBSERVER_READY", "observer"),
    ("OBSERVER_READY", "APPLY_NOT_STARTED", "observer"),
    ("APPLY_NOT_STARTED", "APPLY_RUNNING", "observer"),
    ("APPLY_RUNNING", "APPLY_EXITED_SUCCESS", "observer"),
    ("APPLY_RUNNING", "APPLY_EXITED_FAILURE", "observer"),
    ("APPLY_RUNNING", "APPLY_IDENTITY_LOST", "observer"),
    ("APPLY_EXITED_FAILURE", "PACKAGE_HEALTH_CHECK", "observer"),
    ("PACKAGE_HEALTH_CHECK", "ROLLBACK_ELIGIBILITY_CHECK", "observer"),
    ("ROLLBACK_ELIGIBILITY_CHECK", "ROLLBACK_REQUIRED", "observer"),
    ("ROLLBACK_ELIGIBILITY_CHECK", "ROLLBACK_NOT_AUTHORISED", "observer"),
    ("ROLLBACK_REQUIRED", "ROLLBACK_RUNNING", "observer"),
    ("ROLLBACK_RUNNING", "ROLLBACK_SUCCEEDED", "observer"),
    ("ROLLBACK_RUNNING", "ROLLBACK_FAILED", "observer"),
    ("APPLY_EXITED_SUCCESS", "TERMINALISING", "observer"),
    ("ROLLBACK_SUCCEEDED", "TERMINALISING", "observer"),
    ("ROLLBACK_NOT_AUTHORISED", "TERMINALISING", "observer"),
    ("ROLLBACK_FAILED", "TERMINALISING", "observer"),
    ("APPLY_IDENTITY_LOST", "TERMINALISING", "observer"),
    ("TERMINALISING", "PASS", "observer"),
    ("TERMINALISING", "FAIL", "observer"),
    ("TERMINALISING", "HOLD", "observer"),
    ("TERMINALISING", "BLOCKED", "observer"),
}
EVIDENCE_ARTIFACTS = [
    "observer_identity_receipt.json", "controller_to_observer_handoff.json",
    "apply_child_identity_receipt.json", "alert_watcher_identity_receipt.json",
    "heartbeat.jsonl", "state_transition_journal.jsonl",
    "package_health_classification.json", "restore_point_verification_receipt.json",
    "rollback_authority_decision.json", "cleanup_receipt.json",
    "terminal_record.json", "manifest.json", "terminal-seal.json",
]
PACKAGE_HEALTH_STATES = {"healthy", "missing", "empty", "incomplete"}
TRANSACTION_TYPES = {"install/apply", "Gateway or service restart", "functional smoke"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json_bytes(data: Any) -> bytes:
    return (json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fsync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_write_bytes(path: Path, payload: bytes, *, mode: int = 0o600) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}-{uuid.uuid4().hex}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(tmp, flags, mode)
    try:
        os.write(fd, payload)
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, path)
    os.chmod(path, mode)
    try:
        fsync_directory(path.parent)
    except OSError:
        pass
    return sha256_bytes(payload)


def atomic_write_json(path: Path, data: Any) -> str:
    return atomic_write_bytes(path, canonical_json_bytes(data))


def proc_start_identity(pid: int) -> str | None:
    try:
        return Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").split()[21]
    except Exception:
        return None


def classify_pid(pid: int, expected_starttime: str | None) -> str:
    actual = proc_start_identity(pid)
    if actual is None:
        return "pid_missing"
    if expected_starttime is not None and actual != expected_starttime:
        return "pid_reused"
    return "pid_matches"


@dataclass(frozen=True)
class ProcessIdentity:
    role: Literal["controller", "observer", "apply_child", "alert_watcher"]
    pid: int
    proc_starttime: str | None
    argv_sha256: str | None = None
    cwd_sha256: str | None = None

    def is_current(self) -> bool:
        return classify_pid(self.pid, self.proc_starttime) == "pid_matches"


@dataclass
class SequenceEnforcer:
    last_sequence: int = 0

    def next(self) -> int:
        self.last_sequence += 1
        return self.last_sequence

    def require_next(self, sequence: int) -> None:
        if sequence != self.last_sequence + 1:
            raise ValueError("sequence_gap_or_replay_detected")
        self.last_sequence = sequence


@dataclass
class EvidenceWriter:
    root: Path
    run_id: str
    actor: str
    process_identity: ProcessIdentity
    sequence: SequenceEnforcer = field(default_factory=SequenceEnforcer)
    previous_hash: str = "0" * 64

    def record(self, name: str, classification: str, details: dict[str, Any]) -> dict[str, Any]:
        if name not in EVIDENCE_ARTIFACTS and not name.endswith(".jsonl"):
            raise ValueError("unknown_evidence_artifact")
        sequence = self.sequence.next()
        record = {
            "schema": "critical_apply.clean_lineage_candidate.evidence.v1",
            "run_id": self.run_id,
            "sequence": sequence,
            "utc": utc_now(),
            "monotonic_ns": time.monotonic_ns(),
            "actor": self.actor,
            "pid": self.process_identity.pid,
            "proc_starttime": self.process_identity.proc_starttime,
            "sha256_prev": self.previous_hash,
            "classification": classification,
            "details": details,
        }
        payload = canonical_json_bytes(record)
        digest = sha256_bytes(payload)
        if name.endswith(".jsonl"):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0), 0o600)
            try:
                os.write(fd, payload)
                os.fsync(fd)
            finally:
                os.close(fd)
        else:
            atomic_write_bytes(self.root / name, payload)
        self.previous_hash = digest
        return record


def validate_transition(current: str, new: str, actor: str) -> None:
    if current not in STATES or new not in STATES:
        raise ValueError("unknown_state")
    if (current, new, actor) not in PERMITTED_TRANSITIONS:
        raise ValueError("invalid_or_actor_unauthorised_transition")
    if current in TERMINALS:
        raise ValueError("terminal_state_is_final")


def reject_combined_transactions(transactions: Iterable[str], authority_token: str) -> None:
    unique = {t for t in transactions if t in TRANSACTION_TYPES}
    if len(unique) != 1:
        raise ValueError("combined_or_missing_transaction_authority")
    if not authority_token or ":" in authority_token and authority_token.count(":") != 1:
        raise ValueError("ambiguous_authority_token")


def classify_package_base(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return "missing"
    regular_count = sum(1 for e in entries if e.get("type") == "regular")
    dir_count = sum(1 for e in entries if e.get("type") == "directory")
    if regular_count == 0 and dir_count == 0:
        return "empty"
    required = {"package.json", "dist"}
    observed = {str(e.get("name")) for e in entries}
    if required.issubset(observed):
        return "healthy"
    return "incomplete"


def decide_rollback(package_health: str, restore_verified: bool, rollback_authorised: bool) -> str:
    if package_health == "healthy":
        return "rollback_not_required"
    if package_health not in PACKAGE_HEALTH_STATES:
        return "rollback_hold_unknown_package_health"
    if not restore_verified:
        return "rollback_blocked_restore_not_verified"
    if not rollback_authorised:
        return "rollback_hold_outside_authority"
    return "rollback_required_authorised"


def plan_cleanup(identities: list[ProcessIdentity], allow_escalation: bool, grace_seconds: float) -> dict[str, Any]:
    actions = []
    for ident in identities:
        state = classify_pid(ident.pid, ident.proc_starttime)
        actions.append({"role": ident.role, "pid": ident.pid, "identity_state": state, "signal_plan": "none" if state != "pid_matches" else "graceful_then_optional_escalation", "grace_seconds": grace_seconds, "escalation_authorised": allow_escalation})
    incomplete = any(a["identity_state"] == "pid_matches" and not allow_escalation for a in actions)
    return {"actions": actions, "cleanup_classification": "HOLD_INCOMPLETE_CLEANUP_PROOF" if incomplete else "CLEANUP_PLAN_DETERMINISTIC"}


def terminal_precedence(records: list[dict[str, Any]]) -> str:
    terminals = [r for r in records if r.get("state") in TERMINALS or r.get("terminal") in TERMINALS]
    if not terminals:
        return "HOLD"
    values = {r.get("state") or r.get("terminal") for r in terminals}
    if len(values) != 1:
        return "HOLD"
    return values.pop()


def build_manifest(root: Path, terminal: str) -> dict[str, Any]:
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name not in {"manifest.json", "terminal-seal.json"}:
            files.append({"path": str(path.relative_to(root)), "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    return {"schema": "critical_apply.clean_lineage_candidate.manifest.v1", "terminal": terminal, "generated_utc": utc_now(), "non_circular_exclusions": ["manifest.json", "terminal-seal.json"], "files": files, "file_count": len(files)}


def build_terminal_seal(manifest_sha256: str, terminal: str, final_state: str) -> dict[str, Any]:
    return {"schema": "critical_apply.clean_lineage_candidate.terminal_seal.v1", "terminal": terminal, "final_state": final_state, "manifest_sha256": manifest_sha256, "generated_utc": utc_now()}
