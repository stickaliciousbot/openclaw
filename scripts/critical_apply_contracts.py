#!/usr/bin/env python3
"""Critical Apply contract primitives.

This module is intentionally stdlib-only so it can run during degraded
OpenClaw recovery. It defines the durable receipt vocabulary used by the
critical apply observer runner and plugins.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable


class CriticalApplyPhase(str, Enum):
    INIT = "INIT"
    LOCK_ACQUIRED = "LOCK_ACQUIRED"
    SCOPE_CLASSIFIED = "SCOPE_CLASSIFIED"
    RESTORE_POINT_VERIFIED = "RESTORE_POINT_VERIFIED"
    RESTORE_POINT_CREATED = "RESTORE_POINT_CREATED"
    PRECHECK_PASS = "PRECHECK_PASS"
    ARMED = "ARMED"
    APPROVAL_SEEN = "APPROVAL_SEEN"
    APPLY_STARTING = "APPLY_STARTING"
    APPLY_RUNNING = "APPLY_RUNNING"
    APPLY_EXITED = "APPLY_EXITED"
    POSTCHECK_RUNNING = "POSTCHECK_RUNNING"
    RECOVERY_DECIDING = "RECOVERY_DECIDING"
    RECOVERY_RUNNING = "RECOVERY_RUNNING"
    FINAL = "FINAL"


class CriticalApplyPhaseV2(str, Enum):
    """v2 transaction phases from the HRL-3 critical-apply contract.

    The v1 enum above is retained for compatibility with the initial skeleton.
    Production promotion must use the v2 phase vocabulary.
    """

    CREATED = "CREATED"
    PREPARING = "PREPARING"
    RESTORE_POINT_READY = "RESTORE_POINT_READY"
    PRECHECK_PASS = "PRECHECK_PASS"
    PLAN_SEALED = "PLAN_SEALED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVAL_RECORDED = "APPROVAL_RECORDED"
    COMMIT_LOCKS_ACQUIRED = "COMMIT_LOCKS_ACQUIRED"
    COMMIT_REVALIDATING = "COMMIT_REVALIDATING"
    COMMIT_VALIDATED = "COMMIT_VALIDATED"
    APPLY_INTENT_DURABLE = "APPLY_INTENT_DURABLE"
    APPLY_CHILD_SPAWNED_BLOCKED = "APPLY_CHILD_SPAWNED_BLOCKED"
    MUTATION_RELEASED = "MUTATION_RELEASED"
    APPLY_RUNNING = "APPLY_RUNNING"
    APPLY_EXIT_OBSERVED = "APPLY_EXIT_OBSERVED"
    APPLY_EXIT_UNKNOWN = "APPLY_EXIT_UNKNOWN"
    POSTCHECK_RUNNING = "POSTCHECK_RUNNING"
    RECOVERY_DECIDING = "RECOVERY_DECIDING"
    RECOVERY_INTENT_DURABLE = "RECOVERY_INTENT_DURABLE"
    RECOVERY_RUNNING = "RECOVERY_RUNNING"
    POST_RECOVERY_CHECK = "POST_RECOVERY_CHECK"
    FINALIZING = "FINALIZING"
    TERMINAL = "TERMINAL"


class CriticalApplyTerminal(str, Enum):
    NO_APPROVAL = "NO_APPROVAL"
    APPROVED_NOT_STARTED = "APPROVED_NOT_STARTED"
    STARTED_NO_EXIT = "STARTED_NO_EXIT"
    EXITED_UNVERIFIED = "EXITED_UNVERIFIED"
    PASS = "PASS"
    FAIL_SAFE_NO_MUTATION = "FAIL_SAFE_NO_MUTATION"
    FAIL_MUTATION_PARTIAL = "FAIL_MUTATION_PARTIAL"
    ROLLBACK_REQUIRED = "ROLLBACK_REQUIRED"
    ROLLBACK_PASS = "ROLLBACK_PASS"
    ROLLBACK_FAIL_OPERATOR_REQUIRED = "ROLLBACK_FAIL_OPERATOR_REQUIRED"
    RECOVERED_WITH_WARNING = "RECOVERED_WITH_WARNING"
    HOLD_FOR_SEPARATE_RESTART = "HOLD_FOR_SEPARATE_RESTART"
    HOLD_FOR_SEPARATE_FUNCTIONAL_SMOKE = "HOLD_FOR_SEPARATE_FUNCTIONAL_SMOKE"


class CriticalApplyTerminalV2(str, Enum):
    CANCELLED_NO_APPROVAL = "CANCELLED_NO_APPROVAL"
    APPROVAL_EXPIRED_REPREPARE_REQUIRED = "APPROVAL_EXPIRED_REPREPARE_REQUIRED"
    APPROVED_NOT_STARTED = "APPROVED_NOT_STARTED"
    PRECONDITION_DRIFT_BLOCKED = "PRECONDITION_DRIFT_BLOCKED"
    APPLY_STATE_UNKNOWN_OPERATOR_REQUIRED = "APPLY_STATE_UNKNOWN_OPERATOR_REQUIRED"
    FAIL_SAFE_NO_MUTATION = "FAIL_SAFE_NO_MUTATION"
    APPLY_EFFECTIVE_EXIT_NONZERO_HOLD = "APPLY_EFFECTIVE_EXIT_NONZERO_HOLD"
    PASS_PACKAGE_INSTALLED_HOLD_FOR_SEPARATE_RESTART = "PASS_PACKAGE_INSTALLED_HOLD_FOR_SEPARATE_RESTART"
    FAIL_MUTATION_PARTIAL_RECOVERY_REQUIRED = "FAIL_MUTATION_PARTIAL_RECOVERY_REQUIRED"
    RECOVERY_PASS_HOLD_FOR_SEPARATE_RESTART = "RECOVERY_PASS_HOLD_FOR_SEPARATE_RESTART"
    RECOVERY_PASS_WITH_GUARD_WARNING_OPERATOR_HOLD = "RECOVERY_PASS_WITH_GUARD_WARNING_OPERATOR_HOLD"
    RECOVERY_BLOCKED_STATE_UNKNOWN = "RECOVERY_BLOCKED_STATE_UNKNOWN"
    ROLLBACK_FAIL_OPERATOR_REQUIRED = "ROLLBACK_FAIL_OPERATOR_REQUIRED"
    EVIDENCE_TAMPERED_OR_INCOMPLETE_HOLD = "EVIDENCE_TAMPERED_OR_INCOMPLETE_HOLD"
    PASS_CONTROLLED_GATEWAY_RESTART = "PASS_CONTROLLED_GATEWAY_RESTART"
    PASS_FUNCTIONAL_SMOKE = "PASS_FUNCTIONAL_SMOKE"
    FUNCTIONAL_SMOKE_FAIL_NO_PACKAGE_RECOVERY = "FUNCTIONAL_SMOKE_FAIL_NO_PACKAGE_RECOVERY"


class ExecutionState(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    RUNNING = "RUNNING"
    EXIT_ZERO = "EXIT_ZERO"
    EXIT_NONZERO = "EXIT_NONZERO"
    SIGNALLED = "SIGNALLED"
    TIMEOUT_KILLED = "TIMEOUT_KILLED"
    EXIT_UNKNOWN = "EXIT_UNKNOWN"


class OfficialPackageState(str, Enum):
    MISSING = "MISSING"
    EMPTY = "EMPTY"
    INCOMPLETE = "INCOMPLETE"
    COHERENT_PRE_GENERATION = "COHERENT_PRE_GENERATION"
    COHERENT_CANDIDATE_GENERATION = "COHERENT_CANDIDATE_GENERATION"
    COHERENT_OTHER_GENERATION = "COHERENT_OTHER_GENERATION"
    UNKNOWN = "UNKNOWN"


class PackageSubstrateState(str, Enum):
    COHERENT = "COHERENT"
    DEGRADED = "DEGRADED"
    BROKEN = "BROKEN"
    UNKNOWN = "UNKNOWN"


class GuardState(str, Enum):
    UNCHANGED = "UNCHANGED"
    ALLOWED_DRIFT = "ALLOWED_DRIFT"
    FORBIDDEN_DRIFT = "FORBIDDEN_DRIFT"
    UNKNOWN = "UNKNOWN"


class RecoveryState(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    AUTHORISED_PENDING = "AUTHORISED_PENDING"
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    NOT_AUTHORISED = "NOT_AUTHORISED"


class NpmBaseClassification(str, Enum):
    NPM_BASE_MISSING = "NPM_BASE_MISSING"
    NPM_BASE_EMPTY = "NPM_BASE_EMPTY"
    NPM_BASE_INCOMPLETE = "NPM_BASE_INCOMPLETE"
    NPM_BASE_COHERENT = "NPM_BASE_COHERENT"
    NPM_BASE_UNKNOWN = "NPM_BASE_UNKNOWN"


class StagingDirClassification(str, Enum):
    NONE = "NONE"
    LIVE_REFERENCED_LEAVE_UNTOUCHED = "LIVE_REFERENCED_LEAVE_UNTOUCHED"
    INACTIVE_CAN_QUARANTINE = "INACTIVE_CAN_QUARANTINE"
    SUSPICIOUS_BLOCK = "SUSPICIOUS_BLOCK"


@dataclass
class ValidationResult:
    ok: bool
    code: str
    reasons: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class Transaction:
    transaction_id: str
    root: str
    plugin: str
    phase: str = CriticalApplyPhase.INIT.value
    terminal: str | None = None
    critical: bool = True
    restart_in_scope: bool = False
    functional_smoke_in_scope: bool = False
    forbidden: list[str] = field(default_factory=list)
    created_at_utc: str = field(default_factory=lambda: utc_now())

    @property
    def root_path(self) -> Path:
        return Path(self.root)


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def argv_sha256(argv: Iterable[str]) -> str:
    return sha256_bytes(canonical_json_bytes(list(argv)))


def ensure_dir(path: str | Path, mode: int = 0o700) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(p, mode)
    except PermissionError:
        pass
    return p


def write_json(path: str | Path, obj: Any) -> None:
    p = Path(path)
    ensure_dir(p.parent)
    tmp = p.with_name(f".{p.name}.tmp-{os.getpid()}")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, p)


def read_json(path: str | Path) -> Any:
    with Path(path).open(encoding="utf-8") as f:
        return json.load(f)


def receipt(schema: str, **fields: Any) -> dict[str, Any]:
    return {"schema": schema, "generated_at_utc": utc_now(), **fields}


def validate_transaction_id(transaction_id: str) -> ValidationResult:
    if re.fullmatch(r"critical-apply-[a-z0-9-]+-\d{8}T\d{6}Z-[a-f0-9]{32}", transaction_id):
        return ValidationResult(True, "TRANSACTION_ID_VALID")
    return ValidationResult(False, "TRANSACTION_ID_INVALID", [transaction_id])


def validate_argv_exact(actual: list[str], expected: list[str]) -> ValidationResult:
    if actual == expected:
        return ValidationResult(True, "ARGV_EXACT_MATCH", details={"argv_sha256": argv_sha256(actual)})
    return ValidationResult(
        False,
        "ARGV_MISMATCH",
        ["actual argv does not match approval boundary"],
        {"actual": actual, "expected": expected, "actual_sha256": argv_sha256(actual), "expected_sha256": argv_sha256(expected)},
    )


def validate_restore_point_fresh(created_at_epoch: float, max_age_seconds: int = 3600, now_epoch: float | None = None) -> ValidationResult:
    now = time.time() if now_epoch is None else now_epoch
    age = now - created_at_epoch
    if age < 0:
        return ValidationResult(False, "RESTORE_POINT_FROM_FUTURE", [f"age={age:.3f}s"])
    if age <= max_age_seconds:
        return ValidationResult(True, "RESTORE_POINT_FRESH", details={"age_seconds": age, "max_age_seconds": max_age_seconds})
    return ValidationResult(False, "RESTORE_POINT_STALE", [f"age={age:.3f}s > {max_age_seconds}s"], {"age_seconds": age})


def validate_receipt(path: str | Path, expected_schema: str | None = None) -> ValidationResult:
    p = Path(path)
    if not p.is_file():
        return ValidationResult(False, "RECEIPT_MISSING", [str(p)])
    try:
        obj = read_json(p)
    except Exception as exc:  # noqa: BLE001 - validator must report all parse failures
        return ValidationResult(False, "RECEIPT_JSON_INVALID", [f"{type(exc).__name__}: {exc}"])
    schema = obj.get("schema") if isinstance(obj, dict) else None
    if not schema:
        return ValidationResult(False, "RECEIPT_SCHEMA_MISSING", [str(p)])
    if expected_schema and schema != expected_schema:
        return ValidationResult(False, "RECEIPT_SCHEMA_MISMATCH", [f"expected={expected_schema} actual={schema}"])
    return ValidationResult(True, "RECEIPT_VALID", details={"schema": schema, "path": str(p)})


def manifest_directory(root: str | Path, exclude_names: set[str] | None = None) -> dict[str, Any]:
    root_p = Path(root)
    exclude = exclude_names or {"evidence-manifest.json", "evidence-manifest.sha256"}
    entries: list[dict[str, Any]] = []
    for p in sorted(root_p.rglob("*")):
        rel = p.relative_to(root_p).as_posix()
        if p.name in exclude:
            continue
        if p.is_dir():
            entries.append({"path": rel, "type": "directory"})
        elif p.is_file():
            entries.append({"path": rel, "type": "regular_file", "size": p.stat().st_size, "sha256": sha256_file(p)})
        elif p.is_symlink():
            entries.append({"path": rel, "type": "symlink", "target": os.readlink(p)})
        else:
            entries.append({"path": rel, "type": "other"})
    return receipt("critical_apply.evidence_manifest.v1", root=str(root_p), entries=entries, entry_count=len(entries))


def write_manifest(root: str | Path) -> str:
    root_p = Path(root)
    manifest = manifest_directory(root_p)
    manifest_path = root_p / "evidence-manifest.json"
    write_json(manifest_path, manifest)
    digest = sha256_file(manifest_path)
    (root_p / "evidence-manifest.sha256").write_text(f"{digest}  evidence-manifest.json\n", encoding="utf-8")
    return digest


def validation_result_to_dict(result: ValidationResult) -> dict[str, Any]:
    return asdict(result)


def validate_no_foreground_apply_text(text: str) -> ValidationResult:
    """Static guard for docs/scripts: reject obvious foreground critical apply instructions."""
    forbidden_patterns = [
        r"exec\([^\n]*npm install",
        r"/usr/bin/npm\s+install\s+-g[^\n]*#?\s*foreground",
        r"run .*apply.*foreground",
        r"gateway restart.*&&.*npm install",
    ]
    hits = []
    for pattern in forbidden_patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            hits.append(pattern)
    if hits:
        return ValidationResult(False, "FOREGROUND_CRITICAL_APPLY_PATTERN_FOUND", hits)
    return ValidationResult(True, "NO_FOREGROUND_CRITICAL_APPLY_PATTERN")


__all__ = [
    "CriticalApplyPhase",
    "CriticalApplyPhaseV2",
    "CriticalApplyTerminal",
    "CriticalApplyTerminalV2",
    "ExecutionState",
    "OfficialPackageState",
    "PackageSubstrateState",
    "GuardState",
    "RecoveryState",
    "NpmBaseClassification",
    "StagingDirClassification",
    "Transaction",
    "ValidationResult",
    "argv_sha256",
    "canonical_json_bytes",
    "ensure_dir",
    "manifest_directory",
    "read_json",
    "receipt",
    "sha256_file",
    "utc_now",
    "validate_argv_exact",
    "validate_no_foreground_apply_text",
    "validate_receipt",
    "validate_restore_point_fresh",
    "validate_transaction_id",
    "validation_result_to_dict",
    "write_json",
    "write_manifest",
]
