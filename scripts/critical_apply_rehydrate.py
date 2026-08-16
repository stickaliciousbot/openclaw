#!/usr/bin/env python3
"""Critical Apply M4 durable rehydration state machine."""
from __future__ import annotations

import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from critical_apply_atomic_io import atomic_replace_json, read_json_artifact
from critical_apply_contracts import ContractError
from critical_apply_journal import validate_journal, read_boot_id
from critical_apply_process import ProcessIdentity, verify_process_identity

REHYDRATION_SCHEMA = "critical_apply.rehydration.v2"
REHYDRATION_CLASSIFICATIONS = (
    "REHYDRATED_PREPARED_NO_APPROVAL",
    "REHYDRATED_APPROVED_NOT_STARTED",
    "REHYDRATED_CHILD_BLOCKED_APPROVAL_UNCONSUMED",
    "REHYDRATED_CHILD_BLOCKED_APPROVAL_CONSUMED",
    "REHYDRATED_CHILD_RUNNING",
    "REHYDRATED_CHILD_EXITED_RECEIPT_PENDING",
    "REHYDRATED_EXIT_RECEIPT_PRESENT",
    "REHYDRATED_RECOVERY_PENDING",
    "REHYDRATED_RECOVERY_RUNNING",
    "REHYDRATED_TERMINAL",
    "REHYDRATION_PROCESS_IDENTITY_CONFLICT",
    "REHYDRATION_EVIDENCE_TAMPERED",
    "REHYDRATION_STATE_UNKNOWN_OPERATOR_HOLD",
)

class RehydrationError(ContractError):
    pass

@dataclass(frozen=True)
class RehydrationResult:
    schema: str
    transaction_id: str
    classification: str
    observer_generation: int
    may_continue_same_child: bool
    may_spawn_primary_child: bool
    may_consume_approval: bool
    may_run_recovery: bool
    reasons: tuple[str, ...]
    boot_id: str

    def to_json(self) -> dict[str, Any]: return asdict(self)


def _exists(root: Path, rel: str) -> bool: return (root/rel).exists()
def _read(root: Path, rel: str) -> Mapping[str, Any]: return read_json_artifact(root/rel, root=root)


def next_observer_generation(transaction_root: Path) -> int:
    root = Path(transaction_root).resolve(strict=True)
    gen_path = root/"observer-generation.json"
    old = 0
    if gen_path.exists():
        try: old = int(_read(root, "observer-generation.json").get("observer_generation", 0))
        except Exception: old = 0
    new = old + 1
    atomic_replace_json(gen_path, {"schema":"critical_apply.observer_generation.v2","observer_generation":new,"pid":os.getpid(),"boot_id":read_boot_id(),"wall_time_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),"monotonic_ns":time.monotonic_ns()}, root=root)
    return new


def identity_from_child_receipt(receipt: Mapping[str, Any]) -> ProcessIdentity:
    return ProcessIdentity(
        int(receipt["pid"]), int(receipt["start_ticks"]), str(receipt["boot_id"]), int(receipt["process_group_id"]), int(receipt["session_id"]), str(receipt["pid_namespace"]), str(receipt["executable_intended"]), str(receipt["argv_sha256"]), bool(receipt.get("pidfd_available")), bool(receipt.get("pidfd_opened")), receipt.get("cgroup_path"), receipt.get("cgroup_inode")
    )


def derive_rehydration_classification(transaction_root: Path, *, supervisor_context: Mapping[str, Any] | None = None, increment_generation: bool = True) -> RehydrationResult:
    root = Path(transaction_root).resolve(strict=True)
    tx = root.name
    if _exists(root, "plan-sealed.json"):
        try: tx = str(_read(root, "plan-sealed.json").get("transaction_id", tx))
        except Exception: pass
    generation = next_observer_generation(root) if increment_generation else int(_read(root,"observer-generation.json").get("observer_generation",0)) if _exists(root,"observer-generation.json") else 0
    try:
        if _exists(root, "journal/events.jsonl"):
            # journal validation is authoritative; unknown/tampered blocks.
            # Use tx from receipts when plan is absent.
            for rel in ("plan-sealed.json", "receipts/apply-intent.json", "receipts/apply-child-spawned-blocked.json"):
                if _exists(root, rel):
                    tx = str(_read(root, rel).get("transaction_id", tx)); break
            v = validate_journal(root, transaction_id=tx)
            if not v.ok:
                cls = "REHYDRATION_EVIDENCE_TAMPERED"
                res = RehydrationResult(REHYDRATION_SCHEMA, tx, cls, generation, False, False, False, False, (v.classification.value,), read_boot_id())
                atomic_replace_json(root/"receipts/rehydration.json", res.to_json(), root=root); return res
    except Exception as exc:
        res = RehydrationResult(REHYDRATION_SCHEMA, tx, "REHYDRATION_EVIDENCE_TAMPERED", generation, False, False, False, False, (str(exc),), read_boot_id())
        (root/"receipts").mkdir(mode=0o700, exist_ok=True); atomic_replace_json(root/"receipts/rehydration.json", res.to_json(), root=root); return res

    receipts = root/"receipts"; receipts.mkdir(mode=0o700, exist_ok=True)
    approval = _exists(root,"receipts/approval-receipt.json")
    consumed = _exists(root,"receipts/approval-consumed.json")
    intent = _exists(root,"receipts/apply-intent.json")
    child = _exists(root,"receipts/apply-child-spawned-blocked.json")
    release = _exists(root,"receipts/mutation-release.json")
    exitr = _exists(root,"receipts/apply-exit.json")
    rec_intent = _exists(root,"receipts/recovery-intent.json")
    rec_post = _exists(root,"receipts/post-recovery.json")
    terminal = _exists(root,"terminal-seal.json")

    reasons: list[str] = []
    cls = "REHYDRATION_STATE_UNKNOWN_OPERATOR_HOLD"
    may_continue = may_recover = False
    may_spawn = may_consume = False

    if terminal:
        cls = "REHYDRATED_TERMINAL"
    elif exitr:
        cls = "REHYDRATED_EXIT_RECEIPT_PRESENT" if not rec_intent else ("REHYDRATED_RECOVERY_PENDING" if not rec_post else "REHYDRATED_TERMINAL")
        may_recover = bool(rec_intent and not rec_post)
    elif rec_intent:
        cls = "REHYDRATED_RECOVERY_RUNNING"
        may_recover = True
    elif child:
        cr = _read(root,"receipts/apply-child-spawned-blocked.json")
        try:
            ident = identity_from_child_receipt(cr)
            alive = verify_process_identity(ident)
        except Exception as exc:
            alive = False; reasons.append("identity_error:"+str(exc))
        if not alive:
            cls = "REHYDRATION_PROCESS_IDENTITY_CONFLICT" if release else "REHYDRATED_APPROVED_NOT_STARTED"
        elif not release:
            cls = "REHYDRATED_CHILD_BLOCKED_APPROVAL_CONSUMED" if consumed else "REHYDRATED_CHILD_BLOCKED_APPROVAL_UNCONSUMED"
            may_continue = True; may_consume = not consumed
        else:
            cls = "REHYDRATED_CHILD_RUNNING"
            may_continue = True
    elif intent:
        cls = "REHYDRATED_APPROVED_NOT_STARTED" if approval else "REHYDRATED_PREPARED_NO_APPROVAL"
        may_spawn = bool(approval and not consumed)
        may_consume = False
    elif approval:
        cls = "REHYDRATED_APPROVED_NOT_STARTED"
        may_spawn = not consumed
    elif _exists(root,"plan-sealed.json"):
        cls = "REHYDRATED_PREPARED_NO_APPROVAL"
    else:
        reasons.append("no known durable phase")

    res = RehydrationResult(REHYDRATION_SCHEMA, tx, cls, generation, may_continue, may_spawn, may_consume, may_recover, tuple(reasons), read_boot_id())
    atomic_replace_json(root/"receipts/rehydration.json", res.to_json(), root=root)
    return res


def rehydrate_transaction(transaction_root: Path, supervisor_context: Mapping[str, Any] | None = None) -> RehydrationResult:
    return derive_rehydration_classification(transaction_root, supervisor_context=supervisor_context, increment_generation=True)


def rehydration_contract() -> Mapping[str, Any]:
    return {"schema":"critical_apply.rehydration_contract.v2","classifications":list(REHYDRATION_CLASSIFICATIONS),"no_primary_rerun":True,"unknown_state_holds":True,"approval_recreated":False,"second_primary_child_allowed":False}
