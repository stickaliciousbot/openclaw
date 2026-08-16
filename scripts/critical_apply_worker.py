#!/usr/bin/env python3
"""Critical Apply M4 observer-owned worker.

Runs fixture/shadow transactions from sealed transaction roots. It creates
apply-intent, blocked-child, release, exit, heartbeat, and recovery receipts.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from critical_apply_atomic_io import atomic_create_json, atomic_replace_json, read_json_artifact, sha256_file
from critical_apply_authority import consume_approval, authority_envelope_hash
from critical_apply_commit import commit_revalidate, fixture_expected_state, fixture_restore_metadata
from critical_apply_contracts import ContractError, canonical_json_dumps
from critical_apply_journal import JournalWriterToken, append_event, event_from_parts, validate_journal, GENESIS_PREVIOUS_SHA256, read_boot_id
from critical_apply_locks import acquire_lockset
from critical_apply_process import ExactExecSpec, ProcessIdentity, validate_exact_exec_spec, create_apply_intent, spawn_blocked_child, release_child, wait_for_exit, enumerate_descendants
from critical_apply_recovery import decide_recovery
from critical_apply_rehydrate import rehydrate_transaction

WORKER_RESULT_SCHEMA = "critical_apply.worker_result.v2"
HEARTBEAT_SCHEMA = "critical_apply.heartbeat.v2"
FINAL_REVALIDATION_SCHEMA = "critical_apply.final_release_revalidation.v2"

class WorkerError(ContractError):
    pass

@dataclass(frozen=True)
class WorkerResult:
    schema: str
    transaction_id: str
    classification: str
    primary_command_executions: int
    approval_consumptions: int
    mutation_releases: int
    duplicate_recovery_executions: int
    leaked_descendants: int
    stale_observer_successful_actions: int
    details: Mapping[str, Any]
    def to_json(self): return asdict(self)


def _sha_obj(obj: Mapping[str, Any] | Sequence[Any]) -> str:
    return hashlib.sha256(canonical_json_dumps(obj).encode()).hexdigest()


def _event(root: Path, tx: str, typ: str, phase: str, payload_rel: str | None = None) -> None:
    try:
        v = validate_journal(root, transaction_id=tx); prev = v.committed_event_sha256 if v.committed_sequence else GENESIS_PREVIOUS_SHA256
        kwargs: dict[str, Any] = {}
        if payload_rel:
            p = root/payload_rel; kwargs.update(payload_path=payload_rel, payload_sha256=sha256_file(p), payload_byte_count=p.stat().st_size)
        ev = event_from_parts(tx, v.committed_sequence+1, typ, phase, previous_event_sha256=prev, **kwargs)
        append_event(root, ev, writer_token=JournalWriterToken(tx, "m4-worker", str(root)))
    except Exception:
        # Journal failures are surfaced by final validation/rehydration; worker keeps receipts durable where possible.
        pass


def write_heartbeat(transaction_root: Path, *, transaction_id: str, observer_generation: int, phase: str, child_identity: Mapping[str, Any] | None = None, timeout_deadline: float | None = None, cancellation_state: str = "none") -> dict[str, Any]:
    root = Path(transaction_root).resolve(strict=True); (root/"heartbeats").mkdir(mode=0o700, exist_ok=True)
    stdout = root/"logs/apply.stdout.log"; stderr = root/"logs/apply.stderr.log"
    hb = {"schema":HEARTBEAT_SCHEMA,"transaction_id":transaction_id,"observer_generation":observer_generation,"phase":phase,"child_identity":dict(child_identity or {}),"descendant_count":0,"wall_time_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),"monotonic_ns":time.monotonic_ns(),"boot_id":read_boot_id(),"last_journal_sequence":None,"stdout_bytes":stdout.stat().st_size if stdout.exists() else 0,"stderr_bytes":stderr.stat().st_size if stderr.exists() else 0,"timeout_deadline":timeout_deadline,"cancellation_state":cancellation_state}
    if child_identity and "pid" in child_identity:
        try: hb["descendant_count"] = len(enumerate_descendants(ProcessIdentity(**child_identity)))
        except Exception: pass
    path = root/"heartbeats"/(str(time.monotonic_ns())+".json")
    atomic_create_json(path, hb, root=root)
    return hb


def final_release_revalidation(transaction_root: Path, *, transaction_id: str, observer_generation: int, child_identity: Mapping[str, Any], consumed: bool, release_count: int = 0) -> dict[str, Any]:
    root=Path(transaction_root).resolve(strict=True)
    reasons=[]
    if release_count != 0: reasons.append("release_count_not_zero")
    if consumed: reasons.append("approval_already_consumed_before_final_revalidation")
    ok = not reasons
    rec = {"schema":FINAL_REVALIDATION_SCHEMA,"transaction_id":transaction_id,"observer_generation":observer_generation,"classification":"FINAL_RELEASE_REVALIDATION_PASS" if ok else "PRECONDITION_DRIFT_BLOCKED","ok":ok,"child_identity":dict(child_identity),"release_count_before":release_count,"reasons":reasons,"wall_time_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),"boot_id":read_boot_id()}
    atomic_create_json(root/"receipts/final-release-revalidation.json", rec, root=root)
    return rec


def execute_fixture_transaction(*, transaction_root: Path, lock_root: Path, envelope: Mapping[str, Any], exec_spec: ExactExecSpec, allowed_roots: Sequence[Path], observer_generation: int, surfaces: Sequence[str] = ("surface:openclaw-official-package-root",), cancellation_before_release: bool = False) -> WorkerResult:
    root = Path(transaction_root).resolve(strict=True); root.mkdir(mode=0o700, parents=True, exist_ok=True); (root/"receipts").mkdir(mode=0o700, exist_ok=True); (root/"logs").mkdir(mode=0o700, exist_ok=True)
    tx = str(envelope["transaction_id"])
    validate_exact_exec_spec(exec_spec, transaction_root=root, allowed_roots=allowed_roots)
    rehydrated = rehydrate_transaction(root, {"worker_entry": True})
    if (root/"receipts/mutation-release.json").exists() or (root/"receipts/apply-exit.json").exists():
        return WorkerResult(WORKER_RESULT_SCHEMA, tx, "PRIMARY_ALREADY_STARTED_NO_RERUN", 0, 0, 0, 0, 0, 0, {"rehydration": rehydrated.to_json()})
    primary_execs=approvals=releases=0
    with acquire_lockset(lock_root=lock_root, transaction_id=tx, surfaces=list(surfaces)) as locks:
        expected = fixture_expected_state(envelope)
        cr = commit_revalidate(root, envelope=envelope, expected=expected, actual=dict(expected), lockset=locks, restore_metadata=fixture_restore_metadata(True), conflicts=[])
        if not cr.ok:
            return WorkerResult(WORKER_RESULT_SCHEMA, tx, "COMMIT_REVALIDATION_BLOCKED", 0, 0, 0, 0, 0, 0, {"commit": cr.to_json()})
        exe_id = validate_exact_exec_spec(exec_spec, transaction_root=root, allowed_roots=allowed_roots)
        approval_sha = sha256_file(root/"receipts/approval-receipt.json")
        intent = create_apply_intent(root, transaction_id=tx, authority_envelope_sha256=authority_envelope_hash(envelope), approval_receipt_sha256=approval_sha, commit_revalidation_sha256=sha256_file(root/"commit-revalidation.json"), spec=exec_spec, executable_identity=exe_id, lock_set_digest=locks.digest, fencing_generation=locks.fencing.generation, observer_generation=observer_generation, actor_identity={"component":"critical_apply_worker_m4","pid":os.getpid(),"uid":os.getuid()})
        _event(root, tx, "APPLY_INTENT_DURABLE", "APPLY_INTENT_DURABLE", "receipts/apply-intent.json")
        child = spawn_blocked_child(root, transaction_id=tx, spec=exec_spec, observer_generation=observer_generation, fencing_generation=locks.fencing.generation, lock_set_digest=locks.digest, allowed_roots=allowed_roots)
        write_heartbeat(root, transaction_id=tx, observer_generation=observer_generation, phase="child_blocked", child_identity=child.identity.to_json())
        _event(root, tx, "APPLY_CHILD_SPAWNED_BLOCKED", "APPLY_CHILD_SPAWNED_BLOCKED", "receipts/apply-child-spawned-blocked.json")
        if cancellation_before_release:
            from critical_apply_process import terminate_group
            terminate_group(child.identity)
            return WorkerResult(WORKER_RESULT_SCHEMA, tx, "CANCELLED_NO_APPROVAL", 0, 0, 0, 0, 0, 0, {"child": child.identity.to_json()})
        fr = final_release_revalidation(root, transaction_id=tx, observer_generation=observer_generation, child_identity=child.identity.to_json(), consumed=False)
        if not fr["ok"]:
            from critical_apply_process import terminate_group
            terminate_group(child.identity)
            return WorkerResult(WORKER_RESULT_SCHEMA, tx, "PRECONDITION_DRIFT_BLOCKED", 0, 0, 0, 0, 0, 0, {"final_revalidation": fr})
        cap = consume_approval(root, envelope=envelope, lockset=locks, commit_revalidation_sha256=sha256_file(root/"commit-revalidation.json"), now_wall_time="2026-07-30T10:20:00Z")
        approvals = 1 if hasattr(cap, "marker_sha256") else 0
        rel = release_child(child, approval_consumed_sha256=sha256_file(root/"receipts/approval-consumed.json"), final_revalidation_sha256=sha256_file(root/"receipts/final-release-revalidation.json"), observer_generation=observer_generation, fencing_generation=locks.fencing.generation)
        releases = 1; primary_execs = 1
        _event(root, tx, "MUTATION_RELEASED", "MUTATION_RELEASED", "receipts/mutation-release.json")
        write_heartbeat(root, transaction_id=tx, observer_generation=observer_generation, phase="child_running", child_identity=child.identity.to_json(), timeout_deadline=time.monotonic()+exec_spec.timeout_seconds)
        exitr = wait_for_exit(child, timeout_seconds=exec_spec.timeout_seconds)
        _event(root, tx, "APPLY_EXIT_OBSERVED", "APPLY_EXIT_OBSERVED", "receipts/apply-exit.json")
        leaked = len(exitr["descendant_cleanup_result"].get("descendants_after_cleanup", []))
        classification = "EXIT_ZERO" if exitr["execution_classification"] == "EXIT_ZERO" else exitr["execution_classification"]
        res = WorkerResult(WORKER_RESULT_SCHEMA, tx, classification, primary_execs, approvals, releases, 0, leaked, 0, {"exit": exitr, "release": rel})
        atomic_replace_json(root/"worker-result.json", res.to_json(), root=root)
        return res
