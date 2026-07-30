#!/usr/bin/env python3
"""Critical Apply Observation Harness v2 strict contracts (M0).

M0 is contract-only. This module defines strict enums, immutable records,
canonical JSON/hash helpers, phase transitions, terminal derivation, surface-set
and authority-envelope validation. It intentionally does not implement or launch
mutation, recovery, service supervision, package installation, Gateway restart,
cron, providers, delivery, or arbitrary command execution.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
import re
import time
from dataclasses import asdict, dataclass, field, replace
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

HEX_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
RFC3339_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")
TRANSACTION_ID_RE = re.compile(r"^critical-apply-[a-z0-9-]+-\d{8}T\d{6}Z-[a-f0-9]{32,}$")
CAMPAIGN_ID_RE = re.compile(r"^critical-campaign-[a-z0-9-]+-\d{8}T\d{6}Z-[a-f0-9]{32,}$")


class ContractError(ValueError):
    """Fail-closed contract validation error."""

    def __init__(self, code: str, message: str, *, details: Mapping[str, Any] | None = None):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.details = dict(details or {})


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    code: str
    reasons: tuple[str, ...] = ()
    details: Mapping[str, Any] = field(default_factory=dict)


# Legacy names retained so pre-M0 scaffold imports remain inspectable. They are
# not production-promotion vocabulary.
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


class CriticalApplyTerminal(str, Enum):
    NO_APPROVAL = "NO_APPROVAL"
    APPROVED_NOT_STARTED = "APPROVED_NOT_STARTED"
    FAIL_SAFE_NO_MUTATION = "FAIL_SAFE_NO_MUTATION"
    ROLLBACK_FAIL_OPERATOR_REQUIRED = "ROLLBACK_FAIL_OPERATOR_REQUIRED"


class Phase(str, Enum):
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


CriticalApplyPhaseV2 = Phase


class Terminal(str, Enum):
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


CriticalApplyTerminalV2 = Terminal


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


class EvidenceIntegrityState(str, Enum):
    COMPLETE_SEALED = "COMPLETE_SEALED"
    INCOMPLETE = "INCOMPLETE"
    TAMPERED = "TAMPERED"
    UNKNOWN = "UNKNOWN"


class AuthorityValidityState(str, Enum):
    VALID_UNCONSUMED = "VALID_UNCONSUMED"
    VALID_CONSUMED = "VALID_CONSUMED"
    EXPIRED = "EXPIRED"
    DRIFTED = "DRIFTED"
    REPLAYED = "REPLAYED"
    UNKNOWN = "UNKNOWN"


class SurfaceType(str, Enum):
    FILE = "FILE"
    DIRECTORY = "DIRECTORY"
    SERVICE = "SERVICE"
    PROCESS = "PROCESS"
    CRON_JOB = "CRON_JOB"
    CONFIG_KEY = "CONFIG_KEY"
    PROVIDER = "PROVIDER"
    MODEL_ROUTE = "MODEL_ROUTE"
    PROTECTED_MEMORY = "PROTECTED_MEMORY"
    NETWORK_TARGET = "NETWORK_TARGET"


class SurfaceSetName(str, Enum):
    READ = "read_set"
    WRITE = "write_set"
    RECOVERY_WRITE = "recovery_write_set"
    GUARD = "guard_set"
    FORBIDDEN = "forbidden_set"


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


class Actor(str, Enum):
    ASSISTANT_PREPARE = "assistant_prepare"
    OWNER = "owner"
    CRITICAL_APPLYD = "critical_applyd"
    SUPERVISOR = "supervisor"
    CONTRACT_VALIDATOR = "contract_validator"


class TransactionType(str, Enum):
    PACKAGE_APPLY = "package_apply"
    PACKAGE_ONLY_RECOVERY = "package_only_recovery"
    GATEWAY_RESTART = "gateway_restart"
    FUNCTIONAL_SMOKE = "functional_smoke"
    GUARDED_CRON_UPDATE = "guarded_cron_update"
    PROTECTED_MEMORY_WRITER_STATE = "protected_memory_writer_state"
    MODEL_ROUTE_APPLY = "model_route_apply"


@dataclass(frozen=True)
class ProcessIdentity:
    pid: int
    start_ticks: int
    boot_id: str
    cgroup: str
    exe_realpath: str
    command_digest_sha256: str
    supervisor_identity: str = ""

    def validate(self) -> ValidationResult:
        if self.pid <= 0 or self.start_ticks < 0:
            return fail("PROCESS_IDENTITY_INVALID", "pid and start_ticks required")
        if not self.boot_id or not self.cgroup or not self.exe_realpath:
            return fail("PROCESS_IDENTITY_NOT_PID_ONLY", "boot/cgroup/exe identity required")
        if not is_sha256(self.command_digest_sha256):
            return fail("COMMAND_DIGEST_INVALID", "lowercase SHA-256 required")
        return ok("PROCESS_IDENTITY_VALID")


@dataclass(frozen=True)
class FilesystemIdentity:
    realpath: str
    device: str
    inode: int
    mount_id: str
    symlink_policy: str
    mount_crossing_policy: str


@dataclass(frozen=True)
class GenerationIdentity:
    generation_kind: str
    path_realpath: str
    tree_sha256: str
    version: str = ""
    source_commit: str = ""


@dataclass(frozen=True)
class Surface:
    identifier: str
    surface_type: SurfaceType
    canonical: str
    symlink_policy: str = "no_follow"
    mount_policy: str = "same_mount_required"
    allowed_drift_fields: tuple[str, ...] = ()
    bounded_expansion: tuple[str, ...] = ()

    def validate(self) -> ValidationResult:
        if not self.identifier or not self.canonical:
            return fail("SURFACE_IDENTIFIER_MISSING", "surface requires identifier and canonical id")
        if ".." in Path(self.canonical).parts:
            return fail("SURFACE_PATH_TRAVERSAL", self.canonical)
        if any(ch in self.canonical for ch in ["\x00", "\n"]):
            return fail("SURFACE_UNSAFE_CHAR", self.canonical)
        if "*" in self.canonical and not self.bounded_expansion:
            return fail("SURFACE_WILDCARD_UNBOUNDED", self.canonical)
        if self.symlink_policy not in {"no_follow", "follow_if_bound", "not_applicable"}:
            return fail("SURFACE_SYMLINK_POLICY_INVALID", self.symlink_policy)
        if self.mount_policy not in {"same_mount_required", "cross_mount_explicit", "not_applicable"}:
            return fail("SURFACE_MOUNT_POLICY_INVALID", self.mount_policy)
        return ok("SURFACE_VALID")


@dataclass(frozen=True)
class SurfaceSets:
    read_set: tuple[Surface, ...]
    write_set: tuple[Surface, ...]
    recovery_write_set: tuple[Surface, ...]
    guard_set: tuple[Surface, ...]
    forbidden_set: tuple[Surface, ...]

    def validate(self, transaction_type: TransactionType | str | None = None) -> ValidationResult:
        reasons: list[str] = []
        seen: dict[str, list[str]] = {}
        for set_name in SurfaceSetName:
            for surface in getattr(self, set_name.value):
                r = surface.validate()
                if not r.ok:
                    reasons.append(f"{set_name.value}:{surface.identifier}:{r.code}")
                seen.setdefault(surface.canonical, []).append(set_name.value)
        for canonical, owners in seen.items():
            uniq = sorted(set(owners))
            if SurfaceSetName.FORBIDDEN.value in uniq and len(uniq) > 1:
                reasons.append(f"FORBIDDEN_SURFACE_CONFLICT:{canonical}:{uniq}")
            if SurfaceSetName.WRITE.value in uniq and SurfaceSetName.GUARD.value in uniq:
                reasons.append(f"WRITE_GUARD_CONFLICT:{canonical}")
            if SurfaceSetName.WRITE.value in uniq and SurfaceSetName.RECOVERY_WRITE.value in uniq:
                # Legal only when explicitly represented as same boundary surface; default fail closed.
                reasons.append(f"PRIMARY_RECOVERY_AMBIGUOUS:{canonical}")
        if transaction_type == TransactionType.PACKAGE_APPLY:
            forbidden_ids = {s.identifier for s in self.forbidden_set}
            if "gateway_restart" not in forbidden_ids or "functional_smoke" not in forbidden_ids:
                reasons.append("PACKAGE_APPLY_BOUNDARY_MUST_FORBID_RESTART_AND_SMOKE")
        return fail("SURFACE_SETS_INVALID", "; ".join(reasons)) if reasons else ok("SURFACE_SETS_VALID")

    def digest(self) -> str:
        return sha256_bytes(canonical_json_bytes(self.to_json()))

    def to_json(self) -> dict[str, Any]:
        return {name.value: [surface_to_json(s) for s in getattr(self, name.value)] for name in SurfaceSetName}


@dataclass(frozen=True)
class StateVector:
    transaction_type: TransactionType
    execution_state: ExecutionState
    official_package_state: OfficialPackageState
    package_substrate_state: PackageSubstrateState
    guard_state: GuardState
    recovery_state: RecoveryState
    evidence_integrity_state: EvidenceIntegrityState
    authority_validity_state: AuthorityValidityState
    running_generation_state: str = "UNKNOWN"
    staging_generation_state: str = "UNKNOWN"
    terminal_seal_valid: bool = False
    write_set_equal_pre_state: bool = False
    no_unresolved_mutation_evidence: bool = False
    restart_authorised: bool = False
    functional_smoke_authorised: bool = False
    policy: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AuthorityEnvelope:
    schema: str
    transaction_id: str
    campaign_id: str
    owner: str
    approval_mechanism: str
    one_time_nonce: str
    issued_at_utc: str
    expires_at_utc: str
    transaction_spec_sha256: str
    runner_bundle_sha256: str
    contract_bundle_sha256: str
    plugin_bundle_sha256: str
    interpreter_identity_sha256: str
    supervisor_unit_sha256: str
    candidate_authority_sha256: str
    exact_argv_exec_spec_sha256: str
    environment_policy_sha256: str
    restore_point_id: str
    restore_manifest_sha256: str
    restore_method: str
    pre_state_fingerprint_sha256: str
    surface_sets_sha256: str
    resource_policy_sha256: str
    timeout_policy_sha256: str
    network_policy_sha256: str
    recovery_policy_sha256: str
    max_primary_mutations: int
    max_automatic_recoveries: int
    restart_authorised: bool
    functional_smoke_authorised: bool

    def to_json(self) -> dict[str, Any]:
        return asdict(self)

    def hash(self) -> str:
        return sha256_bytes(canonical_json_bytes(self.to_json()))

    def validate(self) -> ValidationResult:
        return validate_authority_envelope(self.to_json())


@dataclass(frozen=True)
class ApprovalState:
    authority_envelope_sha256: str
    nonce: str
    consumed: bool = False
    consumed_at_phase: str | None = None
    consumption_receipt_sha256: str | None = None


def ok(code: str, **details: Any) -> ValidationResult:
    return ValidationResult(True, code, (), details)


def fail(code: str, reason: str, **details: Any) -> ValidationResult:
    return ValidationResult(False, code, (reason,), details)


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(HEX_SHA256_RE.fullmatch(value))


def validate_sha256(value: Any, field: str = "sha256") -> None:
    if not is_sha256(value):
        raise ContractError("SHA256_INVALID", f"{field} must be lowercase SHA-256")


def parse_utc_rfc3339(value: str) -> _dt.datetime:
    if not isinstance(value, str) or not RFC3339_UTC_RE.fullmatch(value):
        raise ContractError("UTC_TIMESTAMP_INVALID", "timestamp must be UTC RFC3339 with Z")
    normalised = value[:-1] + "+00:00"
    dt = _dt.datetime.fromisoformat(normalised)
    if dt.tzinfo != _dt.timezone.utc:
        raise ContractError("UTC_TIMESTAMP_AMBIGUOUS", "timestamp must be UTC")
    return dt


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ContractError("JSON_DUPLICATE_KEY", f"duplicate key: {key}")
        out[key] = value
    return out


def _reject_non_finite(value: Any) -> None:
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        raise ContractError("JSON_NON_FINITE_NUMBER", "NaN/Infinity rejected")
    if isinstance(value, Mapping):
        for v in value.values():
            _reject_non_finite(v)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for v in value:
            _reject_non_finite(v)


def strict_json_loads(text: str) -> Any:
    try:
        value = json.loads(text, object_pairs_hook=_reject_duplicate_keys, parse_constant=lambda c: (_ for _ in ()).throw(ContractError("JSON_NON_FINITE_NUMBER", c)))
    except ContractError:
        raise
    except json.JSONDecodeError as exc:
        raise ContractError("JSON_PARSE_ERROR", str(exc)) from exc
    _reject_non_finite(value)
    return value


def canonical_json_bytes(value: Any) -> bytes:
    _reject_non_finite(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def canonical_json_dumps(value: Any) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_hash(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def argv_sha256(argv: Iterable[str]) -> str:
    return canonical_hash(list(argv))


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def validate_transaction_id(transaction_id: str) -> ValidationResult:
    if not isinstance(transaction_id, str) or not TRANSACTION_ID_RE.fullmatch(transaction_id):
        return fail("TRANSACTION_ID_INVALID", "transaction id must include >=128-bit lowercase hex random suffix")
    suffix = transaction_id.rsplit("-", 1)[-1]
    if len(suffix) < 32:
        return fail("TRANSACTION_ID_RANDOMNESS_TOO_LOW", "random suffix must be >=128 bits")
    return ok("TRANSACTION_ID_VALID")


def validate_campaign_id(campaign_id: str) -> ValidationResult:
    return ok("CAMPAIGN_ID_VALID") if isinstance(campaign_id, str) and CAMPAIGN_ID_RE.fullmatch(campaign_id) else fail("CAMPAIGN_ID_INVALID", "campaign id invalid")


PHASE_ORDER: tuple[Phase, ...] = tuple(Phase)


def _transition(preds: Sequence[Phase], succ: Phase, receipts: Sequence[str], actor: Actor, lock: str, approval: str, primary: bool, recovery: bool, terminals: Sequence[Terminal] = ()) -> dict[str, Any]:
    return {
        "phase": succ.value,
        "allowed_predecessors": [p.value for p in preds],
        "allowed_successors": [],
        "required_receipts": list(receipts),
        "permitted_actor": actor.value,
        "lock_requirements": lock,
        "approval_state_required": approval,
        "primary_mutation_may_have_occurred": primary,
        "recovery_may_have_occurred": recovery,
        "valid_terminal_derivations": [t.value for t in terminals],
        "prohibited_transitions": "all unlisted predecessor/successor pairs fail closed",
    }


_TRANSITIONS: list[dict[str, Any]] = [
    _transition([], Phase.CREATED, ["transaction-spec"], Actor.ASSISTANT_PREPARE, "none", "none", False, False),
    _transition([Phase.CREATED], Phase.PREPARING, ["prepare-start"], Actor.CRITICAL_APPLYD, "preparation_lock_only", "none", False, False),
    _transition([Phase.PREPARING], Phase.RESTORE_POINT_READY, ["restore-point"], Actor.CRITICAL_APPLYD, "preparation_lock_only", "none", False, False),
    _transition([Phase.RESTORE_POINT_READY], Phase.PRECHECK_PASS, ["precheck"], Actor.CRITICAL_APPLYD, "preparation_lock_only", "none", False, False),
    _transition([Phase.PRECHECK_PASS], Phase.PLAN_SEALED, ["plan-seal", "authority-envelope"], Actor.CRITICAL_APPLYD, "preparation_lock_only_then_release", "none", False, False),
    _transition([Phase.PLAN_SEALED], Phase.AWAITING_APPROVAL, ["approval-boundary"], Actor.CRITICAL_APPLYD, "no_mutation_locks_held", "unapproved", False, False, [Terminal.CANCELLED_NO_APPROVAL, Terminal.APPROVAL_EXPIRED_REPREPARE_REQUIRED]),
    _transition([Phase.AWAITING_APPROVAL], Phase.APPROVAL_RECORDED, ["approval-receipt"], Actor.OWNER, "no_mutation_locks_held", "valid_unconsumed", False, False),
    _transition([Phase.APPROVAL_RECORDED], Phase.COMMIT_LOCKS_ACQUIRED, ["commit-locks"], Actor.CRITICAL_APPLYD, "global_and_surface_locks", "valid_unconsumed", False, False),
    _transition([Phase.COMMIT_LOCKS_ACQUIRED], Phase.COMMIT_REVALIDATING, ["commit-revalidation-start"], Actor.CRITICAL_APPLYD, "global_and_surface_locks", "valid_unconsumed", False, False, [Terminal.PRECONDITION_DRIFT_BLOCKED]),
    _transition([Phase.COMMIT_REVALIDATING], Phase.COMMIT_VALIDATED, ["commit-validation"], Actor.CRITICAL_APPLYD, "global_and_surface_locks", "valid_unconsumed", False, False),
    _transition([Phase.COMMIT_VALIDATED], Phase.APPLY_INTENT_DURABLE, ["apply-intent"], Actor.CRITICAL_APPLYD, "global_and_surface_locks", "valid_unconsumed", False, False),
    _transition([Phase.APPLY_INTENT_DURABLE], Phase.APPLY_CHILD_SPAWNED_BLOCKED, ["apply-spawned-blocked"], Actor.CRITICAL_APPLYD, "global_and_surface_locks", "valid_unconsumed", False, False, [Terminal.APPROVED_NOT_STARTED]),
    _transition([Phase.APPLY_CHILD_SPAWNED_BLOCKED], Phase.MUTATION_RELEASED, ["apply-release", "approval-consumed"], Actor.CRITICAL_APPLYD, "global_and_surface_locks", "consumed_atomically_at_release", True, False),
    _transition([Phase.MUTATION_RELEASED], Phase.APPLY_RUNNING, ["apply-running"], Actor.CRITICAL_APPLYD, "global_and_surface_locks", "consumed", True, False),
    _transition([Phase.APPLY_RUNNING], Phase.APPLY_EXIT_OBSERVED, ["apply-exit"], Actor.CRITICAL_APPLYD, "global_and_surface_locks", "consumed", True, False),
    _transition([Phase.MUTATION_RELEASED, Phase.APPLY_RUNNING], Phase.APPLY_EXIT_UNKNOWN, ["execution-unknown"], Actor.CRITICAL_APPLYD, "global_and_surface_locks", "consumed", True, False, [Terminal.APPLY_STATE_UNKNOWN_OPERATOR_REQUIRED]),
    _transition([Phase.APPLY_EXIT_OBSERVED, Phase.APPLY_EXIT_UNKNOWN], Phase.POSTCHECK_RUNNING, ["postcheck-start"], Actor.CRITICAL_APPLYD, "global_and_surface_locks", "consumed", True, False),
    _transition([Phase.POSTCHECK_RUNNING], Phase.RECOVERY_DECIDING, ["postcheck", "recovery-decision"], Actor.CRITICAL_APPLYD, "global_and_surface_locks", "consumed", True, False, [Terminal.FAIL_SAFE_NO_MUTATION, Terminal.APPLY_EFFECTIVE_EXIT_NONZERO_HOLD, Terminal.PASS_PACKAGE_INSTALLED_HOLD_FOR_SEPARATE_RESTART, Terminal.FAIL_MUTATION_PARTIAL_RECOVERY_REQUIRED, Terminal.RECOVERY_BLOCKED_STATE_UNKNOWN]),
    _transition([Phase.RECOVERY_DECIDING], Phase.RECOVERY_INTENT_DURABLE, ["recovery-intent"], Actor.CRITICAL_APPLYD, "global_and_surface_locks", "consumed", True, False),
    _transition([Phase.RECOVERY_INTENT_DURABLE], Phase.RECOVERY_RUNNING, ["recovery-action-start"], Actor.CRITICAL_APPLYD, "global_and_surface_locks", "consumed", True, True),
    _transition([Phase.RECOVERY_RUNNING], Phase.POST_RECOVERY_CHECK, ["recovery-action", "post-recovery-check"], Actor.CRITICAL_APPLYD, "global_and_surface_locks", "consumed", True, True, [Terminal.RECOVERY_PASS_HOLD_FOR_SEPARATE_RESTART, Terminal.RECOVERY_PASS_WITH_GUARD_WARNING_OPERATOR_HOLD, Terminal.ROLLBACK_FAIL_OPERATOR_REQUIRED]),
    _transition([Phase.RECOVERY_DECIDING, Phase.POST_RECOVERY_CHECK], Phase.FINALIZING, ["final-report", "evidence-manifest"], Actor.CRITICAL_APPLYD, "release_locks_after_terminal_seal", "terminal_authority_state", True, True),
    _transition([Phase.AWAITING_APPROVAL, Phase.COMMIT_REVALIDATING, Phase.APPLY_CHILD_SPAWNED_BLOCKED, Phase.RECOVERY_DECIDING, Phase.POST_RECOVERY_CHECK, Phase.FINALIZING], Phase.TERMINAL, ["terminal-seal"], Actor.CRITICAL_APPLYD, "none_after_seal", "terminal", True, True, tuple(Terminal)),
]


def transition_table() -> list[dict[str, Any]]:
    table = [dict(row) for row in _TRANSITIONS]
    successors: dict[str, set[str]] = {p.value: set() for p in Phase}
    for row in table:
        for pred in row["allowed_predecessors"]:
            successors[pred].add(row["phase"])
    for row in table:
        row["allowed_successors"] = sorted(successors[row["phase"]])
    return table


def legal_transition_pairs() -> set[tuple[Phase | None, Phase]]:
    pairs: set[tuple[Phase | None, Phase]] = set()
    for row in _TRANSITIONS:
        nxt = Phase(row["phase"])
        if not row["allowed_predecessors"]:
            pairs.add((None, nxt))
        for pred in row["allowed_predecessors"]:
            pairs.add((Phase(pred), nxt))
    return pairs


def validate_transition(previous: Phase | str | None, next_phase: Phase | str, context: Mapping[str, Any] | None = None) -> ValidationResult:
    context = dict(context or {})
    prev = None if previous is None else Phase(previous)
    nxt = Phase(next_phase)
    if (prev, nxt) not in legal_transition_pairs():
        return fail("TRANSITION_ILLEGAL", f"{prev}->{nxt}")
    if nxt == Phase.MUTATION_RELEASED:
        required = ["blocked_child_identity_durable", "commit_revalidated", "restore_valid_at_release", "approval_consumed_atomically"]
        missing = [name for name in required if context.get(name) is not True]
        if missing:
            return fail("MUTATION_RELEASE_BLOCKED_MISSING_RECEIPTS", ",".join(missing))
    if prev == Phase.RECOVERY_DECIDING and nxt == Phase.RECOVERY_RUNNING:
        return fail("RECOVERY_REQUIRES_DURABLE_INTENT", "RECOVERY_INTENT_DURABLE phase required before RECOVERY_RUNNING")
    if nxt == Phase.TERMINAL and context.get("terminal", "").startswith("PASS") and context.get("terminal_seal_valid") is not True:
        return fail("PASS_REQUIRES_TERMINAL_SEAL", "terminal PASS requires valid seal")
    if nxt.value.startswith("APPLY") and context.get("approval_already_consumed_before_new_primary") is True:
        return fail("SECOND_PRIMARY_MUTATION_BLOCKED", "consumed approval cannot launch another primary mutation")
    return ok("TRANSITION_VALID")


def terminal_derivation_table() -> list[dict[str, Any]]:
    return [
        {"terminal": Terminal.EVIDENCE_TAMPERED_OR_INCOMPLETE_HOLD.value, "requires": {"evidence_integrity_state": ["INCOMPLETE", "TAMPERED", "UNKNOWN"]}, "pass": False},
        {"terminal": Terminal.APPROVAL_EXPIRED_REPREPARE_REQUIRED.value, "requires": {"authority_validity_state": "EXPIRED"}, "pass": False},
        {"terminal": Terminal.PRECONDITION_DRIFT_BLOCKED.value, "requires": {"authority_validity_state": "DRIFTED"}, "pass": False},
        {"terminal": Terminal.APPROVED_NOT_STARTED.value, "requires": {"execution_state": "NOT_STARTED", "authority_validity_state": "VALID_CONSUMED"}, "pass": False},
        {"terminal": Terminal.APPLY_STATE_UNKNOWN_OPERATOR_REQUIRED.value, "requires": {"execution_state": "EXIT_UNKNOWN"}, "pass": False},
        {"terminal": Terminal.FAIL_SAFE_NO_MUTATION.value, "requires": {"official_package_state": "COHERENT_PRE_GENERATION", "write_set_equal_pre_state": True, "no_unresolved_mutation_evidence": True}, "pass": False},
        {"terminal": Terminal.APPLY_EFFECTIVE_EXIT_NONZERO_HOLD.value, "requires": {"execution_state": "EXIT_NONZERO", "official_package_state": "COHERENT_CANDIDATE_GENERATION", "guard_state": ["UNCHANGED", "ALLOWED_DRIFT"]}, "pass": False},
        {"terminal": Terminal.PASS_PACKAGE_INSTALLED_HOLD_FOR_SEPARATE_RESTART.value, "requires": {"transaction_type": "package_apply", "execution_state": "EXIT_ZERO", "official_package_state": "COHERENT_CANDIDATE_GENERATION", "package_substrate_state": "COHERENT", "guard_state": ["UNCHANGED", "ALLOWED_DRIFT"], "terminal_seal_valid": True}, "pass": True},
        {"terminal": Terminal.RECOVERY_PASS_HOLD_FOR_SEPARATE_RESTART.value, "requires": {"transaction_type": "package_apply", "recovery_state": "PASS", "guard_state": "UNCHANGED", "terminal_seal_valid": True}, "pass": False},
        {"terminal": Terminal.RECOVERY_PASS_WITH_GUARD_WARNING_OPERATOR_HOLD.value, "requires": {"recovery_state": "PASS", "guard_state": "ALLOWED_DRIFT"}, "pass": False},
        {"terminal": Terminal.RECOVERY_BLOCKED_STATE_UNKNOWN.value, "requires": {"recovery_state": ["BLOCKED", "NOT_AUTHORISED"]}, "pass": False},
        {"terminal": Terminal.PASS_CONTROLLED_GATEWAY_RESTART.value, "requires": {"transaction_type": "gateway_restart", "restart_authorised": True, "terminal_seal_valid": True}, "pass": True},
        {"terminal": Terminal.PASS_FUNCTIONAL_SMOKE.value, "requires": {"transaction_type": "functional_smoke", "functional_smoke_authorised": True, "terminal_seal_valid": True}, "pass": True},
        {"terminal": Terminal.FUNCTIONAL_SMOKE_FAIL_NO_PACKAGE_RECOVERY.value, "requires": {"transaction_type": "functional_smoke", "recovery_state": "NOT_AUTHORISED"}, "pass": False},
    ]


def derive_terminal(state: StateVector) -> Terminal:
    if state.evidence_integrity_state != EvidenceIntegrityState.COMPLETE_SEALED:
        return Terminal.EVIDENCE_TAMPERED_OR_INCOMPLETE_HOLD
    if state.authority_validity_state == AuthorityValidityState.EXPIRED:
        return Terminal.APPROVAL_EXPIRED_REPREPARE_REQUIRED
    if state.authority_validity_state == AuthorityValidityState.DRIFTED:
        return Terminal.PRECONDITION_DRIFT_BLOCKED
    if state.authority_validity_state in {AuthorityValidityState.REPLAYED, AuthorityValidityState.UNKNOWN}:
        return Terminal.APPLY_STATE_UNKNOWN_OPERATOR_REQUIRED
    if state.execution_state == ExecutionState.EXIT_UNKNOWN:
        return Terminal.APPLY_STATE_UNKNOWN_OPERATOR_REQUIRED
    if OfficialPackageState.UNKNOWN == state.official_package_state or PackageSubstrateState.UNKNOWN == state.package_substrate_state or GuardState.UNKNOWN == state.guard_state:
        return Terminal.RECOVERY_BLOCKED_STATE_UNKNOWN
    if state.guard_state == GuardState.FORBIDDEN_DRIFT:
        return Terminal.FAIL_MUTATION_PARTIAL_RECOVERY_REQUIRED
    if state.transaction_type == TransactionType.FUNCTIONAL_SMOKE:
        if state.execution_state == ExecutionState.EXIT_ZERO and state.functional_smoke_authorised and state.terminal_seal_valid:
            return Terminal.PASS_FUNCTIONAL_SMOKE
        return Terminal.FUNCTIONAL_SMOKE_FAIL_NO_PACKAGE_RECOVERY
    if state.transaction_type == TransactionType.GATEWAY_RESTART:
        if state.execution_state == ExecutionState.EXIT_ZERO and state.restart_authorised and state.terminal_seal_valid:
            return Terminal.PASS_CONTROLLED_GATEWAY_RESTART
        return Terminal.APPLY_STATE_UNKNOWN_OPERATOR_REQUIRED
    if state.recovery_state == RecoveryState.PASS:
        if state.guard_state == GuardState.UNCHANGED:
            return Terminal.RECOVERY_PASS_HOLD_FOR_SEPARATE_RESTART
        return Terminal.RECOVERY_PASS_WITH_GUARD_WARNING_OPERATOR_HOLD
    if state.recovery_state in {RecoveryState.BLOCKED, RecoveryState.NOT_AUTHORISED}:
        return Terminal.RECOVERY_BLOCKED_STATE_UNKNOWN
    if state.official_package_state == OfficialPackageState.COHERENT_PRE_GENERATION and state.write_set_equal_pre_state and state.no_unresolved_mutation_evidence:
        return Terminal.FAIL_SAFE_NO_MUTATION
    if state.execution_state == ExecutionState.EXIT_NONZERO and state.official_package_state == OfficialPackageState.COHERENT_CANDIDATE_GENERATION and state.package_substrate_state == PackageSubstrateState.COHERENT and state.guard_state in {GuardState.UNCHANGED, GuardState.ALLOWED_DRIFT}:
        return Terminal.APPLY_EFFECTIVE_EXIT_NONZERO_HOLD
    if state.execution_state == ExecutionState.EXIT_ZERO and state.official_package_state == OfficialPackageState.COHERENT_CANDIDATE_GENERATION and state.package_substrate_state == PackageSubstrateState.COHERENT and state.guard_state in {GuardState.UNCHANGED, GuardState.ALLOWED_DRIFT} and state.terminal_seal_valid:
        return Terminal.PASS_PACKAGE_INSTALLED_HOLD_FOR_SEPARATE_RESTART
    if state.official_package_state in {OfficialPackageState.MISSING, OfficialPackageState.EMPTY, OfficialPackageState.INCOMPLETE, OfficialPackageState.COHERENT_OTHER_GENERATION}:
        return Terminal.FAIL_MUTATION_PARTIAL_RECOVERY_REQUIRED
    return Terminal.APPLY_STATE_UNKNOWN_OPERATOR_REQUIRED


def validate_authority_envelope(value: Mapping[str, Any]) -> ValidationResult:
    required = set(AuthorityEnvelope.__dataclass_fields__.keys())
    keys = set(value.keys())
    missing = sorted(required - keys)
    unknown = sorted(keys - required)
    reasons: list[str] = []
    if missing:
        reasons.append("missing:" + ",".join(missing))
    if unknown:
        reasons.append("unknown:" + ",".join(unknown))
    if value.get("schema") != "critical_apply.authority_envelope.v2":
        reasons.append("schema mismatch")
    if not validate_transaction_id(str(value.get("transaction_id", ""))).ok:
        reasons.append("transaction_id invalid")
    if not validate_campaign_id(str(value.get("campaign_id", ""))).ok:
        reasons.append("campaign_id invalid")
    for field_name in [k for k in required if k.endswith("sha256")]:
        if not is_sha256(value.get(field_name)):
            reasons.append(f"{field_name} invalid")
    for field_name in ["issued_at_utc", "expires_at_utc"]:
        try:
            parse_utc_rfc3339(str(value.get(field_name, "")))
        except ContractError:
            reasons.append(f"{field_name} invalid")
    if isinstance(value.get("max_primary_mutations"), bool) or value.get("max_primary_mutations") != 1:
        reasons.append("max_primary_mutations must be exactly 1")
    if isinstance(value.get("max_automatic_recoveries"), bool) or value.get("max_automatic_recoveries") not in {0, 1}:
        reasons.append("max_automatic_recoveries must be 0 or 1")
    if not isinstance(value.get("restart_authorised"), bool) or not isinstance(value.get("functional_smoke_authorised"), bool):
        reasons.append("restart/smoke flags must be booleans")
    if reasons:
        return fail("AUTHORITY_ENVELOPE_INVALID", "; ".join(reasons))
    return ok("AUTHORITY_ENVELOPE_VALID", authority_envelope_sha256=canonical_hash(dict(value)))


def validate_approval_binding(envelope: Mapping[str, Any], approval: Mapping[str, Any], *, now_utc: str, consumed_nonces: set[str] | None = None, observed_hashes: Mapping[str, str] | None = None) -> ValidationResult:
    env_validation = validate_authority_envelope(envelope)
    if not env_validation.ok:
        return env_validation
    env_hash = canonical_hash(dict(envelope))
    reasons: list[str] = []
    consumed_nonces = consumed_nonces or set()
    observed_hashes = observed_hashes or {}
    if approval.get("authority_envelope_sha256") != env_hash:
        reasons.append("authority hash mismatch")
    if approval.get("one_time_nonce") != envelope.get("one_time_nonce"):
        reasons.append("wrong nonce")
    if approval.get("one_time_nonce") in consumed_nonces:
        reasons.append("reused nonce")
    if parse_utc_rfc3339(now_utc) >= parse_utc_rfc3339(str(envelope["expires_at_utc"])):
        reasons.append("expired approval")
    for key, observed in observed_hashes.items():
        if key in envelope and envelope[key] != observed:
            reasons.append(f"drift:{key}")
    return fail("APPROVAL_BINDING_INVALID", "; ".join(reasons)) if reasons else ok("APPROVAL_BINDING_VALID", authority_envelope_sha256=env_hash)


def consume_approval_once(state: ApprovalState, *, phase: Phase, receipt_sha256: str) -> ApprovalState:
    if state.consumed:
        raise ContractError("APPROVAL_REPLAY_BLOCKED", "approval already consumed")
    if phase != Phase.MUTATION_RELEASED:
        raise ContractError("APPROVAL_CONSUMPTION_PHASE_INVALID", "consume only at MUTATION_RELEASED")
    validate_sha256(receipt_sha256, "consumption_receipt_sha256")
    return replace(state, consumed=True, consumed_at_phase=phase.value, consumption_receipt_sha256=receipt_sha256)


def validate_restore_release(created_at_utc: str, release_at_utc: str, *, max_age_seconds: int = 3600, created_monotonic_ns: int | None = None, release_monotonic_ns: int | None = None, same_boot: bool = True) -> ValidationResult:
    created = parse_utc_rfc3339(created_at_utc)
    release = parse_utc_rfc3339(release_at_utc)
    age = (release - created).total_seconds()
    if age < 0:
        return fail("RESTORE_CLOCK_ROLLBACK_OR_NEGATIVE_AGE", f"age={age}")
    if same_boot:
        if created_monotonic_ns is None or release_monotonic_ns is None:
            return fail("RESTORE_MONOTONIC_EVIDENCE_MISSING", "same-boot release requires monotonic evidence")
        if release_monotonic_ns < created_monotonic_ns:
            return fail("RESTORE_MONOTONIC_ROLLBACK", "release monotonic before create")
    if age > max_age_seconds:
        return fail("RESTORE_STALE_AT_MUTATION_RELEASE", f"age={age} > {max_age_seconds}", age_seconds=age)
    return ok("RESTORE_VALID_AT_MUTATION_RELEASE", age_seconds=age, remains_recovery_eligible_after_one_hour=True)


def surface_to_json(surface: Surface) -> dict[str, Any]:
    d = asdict(surface)
    d["surface_type"] = surface.surface_type.value
    d["allowed_drift_fields"] = list(surface.allowed_drift_fields)
    d["bounded_expansion"] = list(surface.bounded_expansion)
    return d


def surface(identifier: str, surface_type: SurfaceType, canonical: str, **kw: Any) -> Surface:
    return Surface(identifier=identifier, surface_type=surface_type, canonical=canonical, **kw)


def fixture_surface_profiles() -> dict[str, Any]:
    f = SurfaceType
    profiles = {
        "package_apply": SurfaceSets(
            read_set=(surface("openclaw_package_root", f.DIRECTORY, "/home/stickai/.npm-global/lib/node_modules/openclaw"), surface("npm_prefix", f.DIRECTORY, "/home/stickai/.npm-global")),
            write_set=(surface("openclaw_package_root", f.DIRECTORY, "/home/stickai/.npm-global/lib/node_modules/openclaw"), surface("openclaw_bin_link", f.FILE, "/home/stickai/.npm-global/bin/openclaw")),
            recovery_write_set=(surface("openclaw_package_root_recovery", f.DIRECTORY, "/home/stickai/.npm-global/lib/node_modules/openclaw.recovery"),),
            guard_set=(surface("strict_jobs_json", f.FILE, "/home/stickai/.openclaw/jobs.json"), surface("gateway_pid", f.PROCESS, "openclaw-gateway:no-restart", symlink_policy="not_applicable", mount_policy="not_applicable"), surface("provider_invocation_counts", f.PROVIDER, "provider-counters:read-only", symlink_policy="not_applicable", mount_policy="not_applicable")),
            forbidden_set=(surface("gateway_restart", f.SERVICE, "openclaw-gateway:restart", symlink_policy="not_applicable", mount_policy="not_applicable"), surface("cron_mutation", f.CRON_JOB, "cron:*", symlink_policy="not_applicable", mount_policy="not_applicable", bounded_expansion=("declared-cron-ids-only",)), surface("functional_smoke", f.NETWORK_TARGET, "delivery-smoke:*", symlink_policy="not_applicable", mount_policy="not_applicable", bounded_expansion=("none",))),
        ),
        "package_only_recovery": SurfaceSets((), (surface("official_root_restore", f.DIRECTORY, "/home/stickai/.npm-global/lib/node_modules/openclaw"),), (surface("official_root_restore", f.DIRECTORY, "/home/stickai/.npm-global/lib/node_modules/openclaw.restore"),), (surface("hidden_generations", f.DIRECTORY, "/home/stickai/.npm-global/lib/node_modules/.openclaw-*", bounded_expansion=("direct-siblings-only",)),), (surface("gateway_restart", f.SERVICE, "openclaw-gateway:restart", symlink_policy="not_applicable", mount_policy="not_applicable"),)),
        "gateway_restart": SurfaceSets((surface("service_unit", f.SERVICE, "openclaw-gateway.service", symlink_policy="not_applicable", mount_policy="not_applicable"),), (surface("gateway_lifecycle", f.SERVICE, "openclaw-gateway:controlled-restart", symlink_policy="not_applicable", mount_policy="not_applicable"),), (), (surface("openclaw_package_root", f.DIRECTORY, "/home/stickai/.npm-global/lib/node_modules/openclaw"),), (surface("provider_delivery", f.PROVIDER, "provider:*", symlink_policy="not_applicable", mount_policy="not_applicable", bounded_expansion=("none",)),)),
        "functional_smoke": SurfaceSets((surface("delivery_target", f.NETWORK_TARGET, "delivery-authorised-target", symlink_policy="not_applicable", mount_policy="not_applicable"),), (), (), (surface("package_generation", f.DIRECTORY, "/home/stickai/.npm-global/lib/node_modules/openclaw"),), (surface("package_recovery", f.DIRECTORY, "/home/stickai/.npm-global/lib/node_modules/openclaw:recovery", symlink_policy="not_applicable", mount_policy="not_applicable"),)),
        "guarded_cron_update": SurfaceSets((surface("jobs_json", f.FILE, "/home/stickai/.openclaw/jobs.json"),), (surface("specific_job_definition", f.CRON_JOB, "cron-job:bound-id", symlink_policy="not_applicable", mount_policy="not_applicable"),), (), (surface("scheduler_state", f.FILE, "/home/stickai/.openclaw/jobs-state.json", allowed_drift_fields=("lastRunAt",)),), (surface("package_root", f.DIRECTORY, "/home/stickai/.npm-global/lib/node_modules/openclaw"),)),
        "protected_memory_writer_state": SurfaceSets((surface("protected_writer_state", f.PROTECTED_MEMORY, "protected-writer:bound-id", symlink_policy="not_applicable", mount_policy="not_applicable"),), (surface("writer_enabled_state", f.PROTECTED_MEMORY, "protected-writer:enabled-field", symlink_policy="not_applicable", mount_policy="not_applicable"),), (), (surface("memory_files", f.FILE, "/home/stickai/.openclaw/workspace/memory/*.md", bounded_expansion=("current-day-and-declared-ledgers",)),), (surface("provider_calls", f.PROVIDER, "provider:*", symlink_policy="not_applicable", mount_policy="not_applicable", bounded_expansion=("none",)),)),
        "model_route_apply": SurfaceSets((surface("route_config", f.CONFIG_KEY, "gateway:model-routes", symlink_policy="not_applicable", mount_policy="not_applicable"),), (surface("route_config", f.CONFIG_KEY, "gateway:model-routes:bound-fields", symlink_policy="not_applicable", mount_policy="not_applicable"),), (), (surface("auth_profiles", f.CONFIG_KEY, "gateway:auth-profiles:hash-only", symlink_policy="not_applicable", mount_policy="not_applicable"),), (surface("provider_call", f.PROVIDER, "provider:live-call", symlink_policy="not_applicable", mount_policy="not_applicable"),)),
    }
    return {name: sets.to_json() for name, sets in profiles.items()}


def validate_no_foreground_apply_text(text: str) -> ValidationResult:
    patterns = [r"execute-foreground", r"shell\s*=\s*True", r"subprocess\.", r"os\.system", r"nohup", r"disown", r"setsid", r"npm\s+install.*gateway\s+restart", r"generic arbitrary command", r"exec\([^\n]*npm\s+install"]
    hits = [p for p in patterns if re.search(p, text, flags=re.IGNORECASE)]
    return fail("FOREGROUND_OR_GENERIC_MUTATION_PATTERN_FOUND", ",".join(hits)) if hits else ok("NO_FOREGROUND_OR_GENERIC_CRITICAL_MUTATION_PATH")


def validate_argv_exact(actual: list[str], expected: list[str]) -> ValidationResult:
    return ok("ARGV_EXACT_MATCH", argv_sha256=argv_sha256(actual)) if actual == expected else fail("ARGV_MISMATCH", "actual argv does not match expected", actual_sha256=argv_sha256(actual), expected_sha256=argv_sha256(expected))


def validate_receipt(value: Mapping[str, Any] | str | Path, expected_schema: str | None = None) -> ValidationResult:
    if isinstance(value, (str, Path)):
        try:
            obj = strict_json_loads(Path(value).read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 - validator reports fail closed
            return fail("RECEIPT_JSON_INVALID", str(exc))
    else:
        obj = dict(value)
    schema = obj.get("schema")
    if not schema:
        return fail("RECEIPT_SCHEMA_MISSING", "schema required")
    if expected_schema and schema != expected_schema:
        return fail("RECEIPT_SCHEMA_MISMATCH", f"expected={expected_schema} actual={schema}")
    return ok("RECEIPT_VALID", schema=schema)


def validation_result_to_dict(result: ValidationResult) -> dict[str, Any]:
    return {"ok": result.ok, "code": result.code, "reasons": list(result.reasons), "details": dict(result.details)}


def receipt(schema: str, **fields: Any) -> dict[str, Any]:
    return {"schema": schema, "generated_at_utc": utc_now(), **fields}


def read_json(path: str | Path) -> Any:
    return strict_json_loads(Path(path).read_text(encoding="utf-8"))


def ensure_dir(path: str | Path, mode: int = 0o700) -> Path:
    """Compatibility helper for the pre-M0 read-only scaffold.

    This is filesystem-only evidence/fixture support. It is not a mutation
    runner and must not be used for production package/Gateway/cron/provider
    surfaces in M0.
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    try:
        p.chmod(mode)
    except PermissionError:
        pass
    return p


def write_json(path: str | Path, obj: Any) -> None:
    p = Path(path)
    ensure_dir(p.parent)
    text = json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    p.write_text(text, encoding="utf-8")


def validate_restore_point_fresh(created_at_epoch: float, max_age_seconds: int = 3600, now_epoch: float | None = None) -> ValidationResult:
    now = time.time() if now_epoch is None else now_epoch
    age = now - created_at_epoch
    if age < 0:
        return fail("RESTORE_POINT_FROM_FUTURE", f"age={age:.3f}s")
    if age <= max_age_seconds:
        return ok("RESTORE_POINT_FRESH", age_seconds=age, max_age_seconds=max_age_seconds)
    return fail("RESTORE_POINT_STALE", f"age={age:.3f}s > {max_age_seconds}s", age_seconds=age)


def write_artifact_json(path: str | Path, value: Any, *, safe_root: str | Path) -> str:
    target = Path(path).resolve()
    root = Path(safe_root).resolve()
    if root not in target.parents and target != root:
        raise ContractError("ARTIFACT_WRITE_OUTSIDE_SAFE_ROOT", str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    text = canonical_json_dumps(value) + "\n"
    target.write_text(text, encoding="utf-8")
    return sha256_bytes(text.encode("utf-8"))


def manifest_directory(root: str | Path, exclude_names: set[str] | None = None) -> dict[str, Any]:
    root_p = Path(root).resolve()
    exclude = exclude_names or {"evidence_manifest.json", "evidence_manifest.sha256", "terminal-seal.json"}
    entries: list[dict[str, Any]] = []
    for p in sorted(root_p.rglob("*")):
        if p.name in exclude:
            continue
        rel = p.relative_to(root_p).as_posix()
        if p.is_file():
            entries.append({"path": rel, "type": "regular_file", "size": p.stat().st_size, "sha256": sha256_file(p)})
        elif p.is_dir():
            entries.append({"path": rel, "type": "directory"})
    return {"schema": "critical_apply.evidence_manifest.v2", "policy": "NON_CIRCULAR_EVIDENCE_MANIFEST_POLICY_V1", "root": str(root_p), "entries": entries, "entry_count": len(entries)}


def write_manifest(root: str | Path) -> str:
    manifest = manifest_directory(root)
    root_p = Path(root).resolve()
    digest = write_artifact_json(root_p / "evidence_manifest.json", manifest, safe_root=root_p)
    (root_p / "evidence_manifest.sha256").write_text(f"{digest}  evidence_manifest.json\n", encoding="utf-8")
    return digest


@dataclass(frozen=True)
class Transaction:
    transaction_id: str
    root: str
    plugin: str
    phase: str = Phase.CREATED.value
    terminal: str | None = None
    critical: bool = True
    restart_in_scope: bool = False
    functional_smoke_in_scope: bool = False
    forbidden: list[str] = field(default_factory=list)
    created_at_utc: str = field(default_factory=utc_now)

    @property
    def root_path(self) -> Path:
        return Path(self.root)


__all__ = [name for name in globals() if not name.startswith("_")]
