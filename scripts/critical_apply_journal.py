#!/usr/bin/env python3
"""Hash-chained journal and projection primitives for Critical Apply M1."""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import sqlite3
import stat
import time
import fcntl
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from critical_apply_atomic_io import (
    ArtifactDigest,
    EvidenceIOError,
    atomic_create_json,
    atomic_replace_json,
    read_json_artifact,
    relative_to_root,
    sha256_file,
    validate_existing_regular,
    validate_parent_for_write,
    validate_relative_path,
)
from critical_apply_contracts import Phase, Terminal, canonical_json_dumps, is_sha256, strict_json_loads

EVENT_SCHEMA = "critical_apply.event.v2"
JOURNAL_HEAD_SCHEMA = "critical_apply.journal_head.v2"
JOURNAL_VALIDATION_SCHEMA = "critical_apply.validated_journal.v2"
PROJECTION_SCHEMA = "critical_apply.projection.v2"
GENESIS_PREVIOUS_SHA256 = "0" * 64


class JournalClassification(str, Enum):
    JOURNAL_VALID = "JOURNAL_VALID"
    JOURNAL_VALID_WITH_UNCOMMITTED_COMPLETE_TAIL = "JOURNAL_VALID_WITH_UNCOMMITTED_COMPLETE_TAIL"
    JOURNAL_TORN_TAIL = "JOURNAL_TORN_TAIL"
    JOURNAL_HEAD_AHEAD_OF_DURABLE_DATA = "JOURNAL_HEAD_AHEAD_OF_DURABLE_DATA"
    JOURNAL_CHAIN_INVALID = "JOURNAL_CHAIN_INVALID"
    JOURNAL_TAMPERED = "JOURNAL_TAMPERED"
    JOURNAL_IDENTITY_MISMATCH = "JOURNAL_IDENTITY_MISMATCH"
    JOURNAL_UNKNOWN = "JOURNAL_UNKNOWN"


@dataclass(frozen=True)
class ActorIdentity:
    component: str
    pid: int
    process_start_ticks: int
    uid: int
    boot_id: str

    @classmethod
    def synthetic(cls, component: str = "m1_fixture") -> "ActorIdentity":
        return cls(component, os.getpid(), 1, os.getuid(), read_boot_id())

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class JournalWriterToken:
    transaction_id: str
    writer_id: str
    root_realpath: str


@dataclass(frozen=True)
class JournalAppendResult:
    schema: str
    transaction_id: str
    committed_sequence: int
    event_sha256: str
    previous_event_sha256: str
    previous_offset: int
    committed_offset: int
    journal_device: int
    journal_inode: int
    head_digest: ArtifactDigest

    def to_json(self) -> dict[str, Any]:
        d = asdict(self)
        d["head_digest"] = self.head_digest.to_json()
        return d


@dataclass(frozen=True)
class ValidatedJournal:
    schema: str
    transaction_id: str
    classification: JournalClassification
    committed_sequence: int
    committed_event_sha256: str
    committed_offset: int
    journal_device: int | None
    journal_inode: int | None
    events: tuple[Mapping[str, Any], ...]
    uncommitted_tail_events: tuple[Mapping[str, Any], ...] = ()
    reasons: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return self.classification in {JournalClassification.JOURNAL_VALID, JournalClassification.JOURNAL_VALID_WITH_UNCOMMITTED_COMPLETE_TAIL}

    def to_json(self) -> dict[str, Any]:
        d = asdict(self)
        d["classification"] = self.classification.value
        d["events"] = [dict(e) for e in self.events]
        d["uncommitted_tail_events"] = [dict(e) for e in self.uncommitted_tail_events]
        return d


@dataclass(frozen=True)
class ProjectionVerification:
    schema: str
    projection_path: str
    ok: bool
    classification: str
    expected_sha256: str | None = None
    actual_sha256: str | None = None
    details: Mapping[str, Any] | None = None

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class JournalIdempotencyAck:
    """Stable ACK reconstructed exclusively from verified journal bytes."""

    schema: str
    transaction_id: str
    event_id: str
    proposal_sha256: str
    sequence: int
    event_sha256: str
    previous_event_sha256: str
    committed_offset: int

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


class JournalIntegrityError(EvidenceIOError):
    """Canonical journal integrity or idempotency conflict."""


class JournalPostSyncCrash(RuntimeError):
    """Test-only crash boundary after durable event/head and before ACK return."""


def utc_now() -> str:
    return _dt.datetime.now(_dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_boot_id() -> str:
    try:
        return Path("/proc/sys/kernel/random/boot_id").read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return "fixture-boot-id"


def event_hash(event_without_hash: Mapping[str, Any]) -> str:
    event = dict(event_without_hash)
    event.pop("event_sha256", None)
    return hashlib.sha256(canonical_json_dumps(event).encode("utf-8")).hexdigest()


def encode_event_line(event: Mapping[str, Any]) -> bytes:
    return (canonical_json_dumps(dict(event)) + "\n").encode("utf-8")


def event_from_parts(transaction_id: str, sequence: int, event_type: str, phase: str, *, previous_event_sha256: str, actor: ActorIdentity | None = None, payload_path: str | None = None, payload_sha256: str | None = None, payload_byte_count: int | None = None, terminal: str | None = None) -> dict[str, Any]:
    actor = actor or ActorIdentity.synthetic()
    event: dict[str, Any] = {
        "schema": EVENT_SCHEMA,
        "transaction_id": transaction_id,
        "sequence": sequence,
        "event_type": event_type,
        "phase": phase,
        "wall_time_utc": utc_now(),
        "monotonic_ns": time.monotonic_ns(),
        "boot_id": actor.boot_id,
        "actor_identity": actor.to_json(),
        "payload_path": payload_path,
        "payload_sha256": payload_sha256,
        "payload_byte_count": payload_byte_count,
        "previous_event_sha256": previous_event_sha256,
    }
    if terminal is not None:
        event["terminal"] = terminal
    event["event_sha256"] = event_hash(event)
    return event


def validate_event_shape(event: Mapping[str, Any], *, expected_transaction_id: str, expected_sequence: int, expected_previous: str) -> tuple[bool, str]:
    if event.get("schema") != EVENT_SCHEMA:
        return False, "invalid event schema"
    if event.get("transaction_id") != expected_transaction_id:
        return False, "changed transaction ID"
    if event.get("sequence") != expected_sequence:
        return False, "duplicate or skipped sequence"
    if event.get("previous_event_sha256") != expected_previous:
        return False, "wrong previous hash"
    got = event.get("event_sha256")
    if not isinstance(got, str) or not is_sha256(got):
        return False, "invalid event hash"
    if event_hash(event) != got:
        return False, "changed historical event"
    return True, "ok"


def create_transaction_journal(transaction_root: Path, *, transaction_id: str) -> ArtifactDigest:
    root = Path(transaction_root).resolve(strict=True)
    journal_dir = root / "journal"
    journal_dir.mkdir(mode=0o700, exist_ok=True)
    journal = journal_dir / "events.jsonl"
    if not journal.exists():
        digest = atomic_create_json(journal_dir / "journal-created.json", {"schema": "critical_apply.journal_created.v2", "transaction_id": transaction_id, "wall_time_utc": utc_now()}, root=root)
        fd = os.open(journal, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        _replace_head(root, transaction_id, 0, GENESIS_PREVIOUS_SHA256, 0, journal)
        return digest
    return validate_existing_regular(journal, root=root) and _head_digest(root)


def _journal_path(root: Path) -> Path:
    return Path(root).resolve(strict=True) / "journal" / "events.jsonl"


def _head_path(root: Path) -> Path:
    return Path(root).resolve(strict=True) / "journal" / "journal-head.json"


def _head_digest(root: Path) -> ArtifactDigest:
    return validate_existing_regular(_head_path(root), root=root) and ArtifactDigest(**read_json_artifact(_head_path(root), root=root).get("artifact_digest", {}))


def _replace_head(root: Path, transaction_id: str, seq: int, event_sha: str, offset: int, journal: Path) -> ArtifactDigest:
    st = os.lstat(journal)
    head = {
        "schema": JOURNAL_HEAD_SCHEMA,
        "transaction_id": transaction_id,
        "committed_sequence": seq,
        "committed_event_sha256": event_sha,
        "committed_journal_byte_offset": offset,
        "journal_device": st.st_dev,
        "journal_inode": st.st_ino,
        "updated_wall_time_utc": utc_now(),
        "monotonic_ns": time.monotonic_ns(),
        "boot_id": read_boot_id(),
    }
    digest = atomic_replace_json(_head_path(root), head, root=root)
    head["artifact_digest"] = digest.to_json()
    return atomic_replace_json(_head_path(root), head, root=root)


def _append_event_locked(transaction_root: Path, event_without_hash: Mapping[str, Any], *, writer_token: JournalWriterToken) -> JournalAppendResult:
    """Append while the per-journal append lock is held by the caller."""
    root = Path(transaction_root).resolve(strict=True)
    if writer_token.root_realpath != str(root):
        raise EvidenceIOError("WRITER_TOKEN_ROOT_MISMATCH", writer_token.root_realpath)
    journal = _journal_path(root)
    head_path = _head_path(root)
    validate_existing_regular(journal, root=root)
    head = read_json_artifact(head_path, root=root)
    if head.get("transaction_id") != writer_token.transaction_id:
        raise EvidenceIOError("HEAD_TRANSACTION_ID_MISMATCH", str(head_path))
    st = os.lstat(journal)
    if head.get("journal_device") != st.st_dev or head.get("journal_inode") != st.st_ino:
        raise EvidenceIOError("JOURNAL_IDENTITY_MISMATCH", str(journal))
    expected_offset = int(head["committed_journal_byte_offset"])
    expected_sequence = int(head["committed_sequence"]) + 1
    previous = str(head["committed_event_sha256"])
    event = dict(event_without_hash)
    event["sequence"] = expected_sequence
    event["previous_event_sha256"] = previous if expected_sequence != 1 else GENESIS_PREVIOUS_SHA256
    if expected_sequence == 1 and previous != GENESIS_PREVIOUS_SHA256:
        raise EvidenceIOError("GENESIS_PREVIOUS_INVALID", previous)
    event["event_sha256"] = event_hash(event)
    ok, reason = validate_event_shape(event, expected_transaction_id=writer_token.transaction_id, expected_sequence=expected_sequence, expected_previous=event["previous_event_sha256"])
    if not ok:
        raise EvidenceIOError("EVENT_SCHEMA_INVALID", reason)
    line = encode_event_line(event)
    fd = os.open(journal, os.O_WRONLY | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0))
    try:
        current_size = os.fstat(fd).st_size
        if current_size != expected_offset:
            raise EvidenceIOError("JOURNAL_OFFSET_MISMATCH", f"{current_size}!={expected_offset}")
        previous_offset = current_size
        view = memoryview(line)
        written_total = 0
        while written_total < len(line):
            try:
                n = os.write(fd, view[written_total:])
            except InterruptedError:
                continue
            if n == 0:
                raise EvidenceIOError("JOURNAL_SHORT_WRITE", str(journal))
            written_total += n
        if hasattr(os, "fdatasync"):
            os.fdatasync(fd)
        else:
            os.fsync(fd)
        committed_offset = previous_offset + len(line)
    finally:
        os.close(fd)
    head_digest = _replace_head(root, writer_token.transaction_id, expected_sequence, event["event_sha256"], committed_offset, journal)
    reread = read_json_artifact(head_path, root=root)
    if reread.get("committed_event_sha256") != event["event_sha256"] or int(reread.get("committed_journal_byte_offset", -1)) != committed_offset:
        raise EvidenceIOError("HEAD_REREAD_MISMATCH", str(head_path))
    verified = validate_journal(root, transaction_id=writer_token.transaction_id)
    if (
        not verified.ok
        or verified.committed_sequence != expected_sequence
        or verified.committed_event_sha256 != event["event_sha256"]
        or verified.committed_offset != committed_offset
    ):
        raise EvidenceIOError("JOURNAL_POST_SYNC_REOPEN_VERIFY_FAILED", str(journal))
    return JournalAppendResult("critical_apply.journal_append_result.v2", writer_token.transaction_id, expected_sequence, event["event_sha256"], event["previous_event_sha256"], previous_offset, committed_offset, st.st_dev, st.st_ino, head_digest)


def append_event(transaction_root: Path, event_without_hash: Mapping[str, Any], *, writer_token: JournalWriterToken) -> JournalAppendResult:
    """Serialize head-read, append-sync, head publication, and reopen verification."""
    root = Path(transaction_root).resolve(strict=True)
    lock_path = root / "journal" / "append.lock"
    created = not lock_path.exists()
    lock_fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        if created:
            parent_fd = os.open(lock_path.parent, os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0))
            try:
                os.fsync(parent_fd)
            finally:
                os.close(parent_fd)
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        return _append_event_locked(root, event_without_hash, writer_token=writer_token)
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        finally:
            os.close(lock_fd)


def _parse_lines(data: bytes) -> tuple[list[Mapping[str, Any]], bool, str | None]:
    events: list[Mapping[str, Any]] = []
    if not data:
        return events, False, None
    lines = data.splitlines(keepends=True)
    for raw in lines:
        if not raw.endswith(b"\n"):
            return events, True, raw.decode("utf-8", "replace")
        try:
            text = raw.decode("utf-8")[:-1]
            obj = strict_json_loads(text)
        except Exception as exc:  # noqa: BLE001 - validation classification
            return events, True, str(exc)
        events.append(obj)
    return events, False, None


def validate_payload_reference(event: Mapping[str, Any], *, transaction_root: Path) -> tuple[bool, str]:
    payload_path = event.get("payload_path")
    if not payload_path:
        return True, "no payload"
    try:
        rel = validate_relative_path(str(payload_path))
        p, st, _ = validate_existing_regular(Path(transaction_root) / rel, root=transaction_root)
        if event.get("payload_byte_count") is not None and int(event["payload_byte_count"]) != st.st_size:
            return False, "payload byte count mismatch"
        if event.get("payload_sha256") != sha256_file(p):
            return False, "payload digest mismatch"
        return True, "payload ok"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def validate_journal(transaction_root: Path, *, transaction_id: str) -> ValidatedJournal:
    root = Path(transaction_root).resolve(strict=True)
    journal = _journal_path(root)
    head_path = _head_path(root)
    if not journal.exists():
        return ValidatedJournal(JOURNAL_VALIDATION_SCHEMA, transaction_id, JournalClassification.JOURNAL_VALID, 0, GENESIS_PREVIOUS_SHA256, 0, None, None, ())
    try:
        _p, jst, _rel = validate_existing_regular(journal, root=root)
        head = read_json_artifact(head_path, root=root)
    except Exception as exc:  # noqa: BLE001
        return ValidatedJournal(JOURNAL_VALIDATION_SCHEMA, transaction_id, JournalClassification.JOURNAL_UNKNOWN, 0, GENESIS_PREVIOUS_SHA256, 0, None, None, (), reasons=(str(exc),))
    if head.get("transaction_id") != transaction_id:
        return ValidatedJournal(JOURNAL_VALIDATION_SCHEMA, transaction_id, JournalClassification.JOURNAL_IDENTITY_MISMATCH, 0, GENESIS_PREVIOUS_SHA256, 0, jst.st_dev, jst.st_ino, (), reasons=("head transaction id mismatch",))
    if head.get("journal_device") != jst.st_dev or head.get("journal_inode") != jst.st_ino:
        return ValidatedJournal(JOURNAL_VALIDATION_SCHEMA, transaction_id, JournalClassification.JOURNAL_IDENTITY_MISMATCH, 0, GENESIS_PREVIOUS_SHA256, 0, jst.st_dev, jst.st_ino, (), reasons=("journal inode/device changed",))
    committed_offset = int(head.get("committed_journal_byte_offset", 0))
    if committed_offset > jst.st_size:
        return ValidatedJournal(JOURNAL_VALIDATION_SCHEMA, transaction_id, JournalClassification.JOURNAL_HEAD_AHEAD_OF_DURABLE_DATA, int(head.get("committed_sequence", 0)), str(head.get("committed_event_sha256", "")), committed_offset, jst.st_dev, jst.st_ino, (), reasons=("head ahead of durable data",))
    data = journal.read_bytes()
    committed_data = data[:committed_offset]
    tail_data = data[committed_offset:]
    events, torn, reason = _parse_lines(committed_data)
    if torn:
        return ValidatedJournal(JOURNAL_VALIDATION_SCHEMA, transaction_id, JournalClassification.JOURNAL_TORN_TAIL, 0, GENESIS_PREVIOUS_SHA256, committed_offset, jst.st_dev, jst.st_ino, tuple(events), reasons=(reason or "torn committed data",))
    previous = GENESIS_PREVIOUS_SHA256
    for idx, event in enumerate(events, start=1):
        ok, why = validate_event_shape(event, expected_transaction_id=transaction_id, expected_sequence=idx, expected_previous=previous)
        if not ok:
            cls = JournalClassification.JOURNAL_IDENTITY_MISMATCH if "transaction ID" in why else JournalClassification.JOURNAL_CHAIN_INVALID
            return ValidatedJournal(JOURNAL_VALIDATION_SCHEMA, transaction_id, cls, idx - 1, previous, committed_offset, jst.st_dev, jst.st_ino, tuple(events[: idx - 1]), reasons=(why,))
        pok, pwhy = validate_payload_reference(event, transaction_root=root)
        if not pok:
            return ValidatedJournal(JOURNAL_VALIDATION_SCHEMA, transaction_id, JournalClassification.JOURNAL_TAMPERED, idx, str(event["event_sha256"]), committed_offset, jst.st_dev, jst.st_ino, tuple(events[:idx]), reasons=(pwhy,))
        previous = str(event["event_sha256"])
    head_seq = int(head.get("committed_sequence", 0))
    head_hash = str(head.get("committed_event_sha256", GENESIS_PREVIOUS_SHA256))
    if head_seq != len(events) or head_hash != previous:
        return ValidatedJournal(JOURNAL_VALIDATION_SCHEMA, transaction_id, JournalClassification.JOURNAL_CHAIN_INVALID, len(events), previous, committed_offset, jst.st_dev, jst.st_ino, tuple(events), reasons=("head references different event hash",))
    tail_events: tuple[Mapping[str, Any], ...] = ()
    if tail_data:
        parsed_tail, torn_tail, tail_reason = _parse_lines(tail_data)
        if torn_tail:
            return ValidatedJournal(JOURNAL_VALIDATION_SCHEMA, transaction_id, JournalClassification.JOURNAL_TORN_TAIL, head_seq, head_hash, committed_offset, jst.st_dev, jst.st_ino, tuple(events), reasons=(tail_reason or "torn tail",))
        tail_events = tuple(parsed_tail)
        return ValidatedJournal(JOURNAL_VALIDATION_SCHEMA, transaction_id, JournalClassification.JOURNAL_VALID_WITH_UNCOMMITTED_COMPLETE_TAIL, head_seq, head_hash, committed_offset, jst.st_dev, jst.st_ino, tuple(events), tail_events)
    return ValidatedJournal(JOURNAL_VALIDATION_SCHEMA, transaction_id, JournalClassification.JOURNAL_VALID, head_seq, head_hash, committed_offset, jst.st_dev, jst.st_ino, tuple(events))


def rebuild_transaction_projection(validated_journal: ValidatedJournal) -> Mapping[str, Any]:
    phases = [str(e.get("phase")) for e in validated_journal.events]
    terminals = [str(e.get("terminal")) for e in validated_journal.events if e.get("terminal")]
    return {
        "schema": PROJECTION_SCHEMA,
        "projection_type": "transaction",
        "transaction_id": validated_journal.transaction_id,
        "journal_classification": validated_journal.classification.value,
        "journal_head_sha256": validated_journal.committed_event_sha256,
        "committed_sequence": validated_journal.committed_sequence,
        "event_count": len(validated_journal.events),
        "current_phase": phases[-1] if phases else None,
        "terminal": terminals[-1] if terminals else None,
        "phases_seen": phases,
        "terminals_seen": terminals,
    }


def rebuild_status_projection(validated_journal: ValidatedJournal) -> Mapping[str, Any]:
    tx = rebuild_transaction_projection(validated_journal)
    status = "HOLD" if not validated_journal.ok else ("TERMINAL" if tx["terminal"] else "IN_PROGRESS")
    return {
        "schema": PROJECTION_SCHEMA,
        "projection_type": "status",
        "transaction_id": validated_journal.transaction_id,
        "status": status,
        "current_phase": tx["current_phase"],
        "terminal": tx["terminal"],
        "journal_head_sha256": validated_journal.committed_event_sha256,
        "committed_sequence": validated_journal.committed_sequence,
    }


def write_projections(transaction_root: Path, validated_journal: ValidatedJournal) -> tuple[ArtifactDigest, ArtifactDigest]:
    root = Path(transaction_root).resolve(strict=True)
    proj = root / "projections"
    proj.mkdir(mode=0o700, exist_ok=True)
    tx_digest = atomic_replace_json(proj / "transaction.json", rebuild_transaction_projection(validated_journal), root=root)
    status_digest = atomic_replace_json(proj / "status.json", rebuild_status_projection(validated_journal), root=root)
    return tx_digest, status_digest


def verify_projection_parity(validated_journal: ValidatedJournal, projection_path: Path) -> ProjectionVerification:
    root = Path(projection_path).resolve(strict=False).parents[1]
    try:
        actual = read_json_artifact(projection_path, root=root)
        expected = rebuild_transaction_projection(validated_journal) if actual.get("projection_type") == "transaction" else rebuild_status_projection(validated_journal)
        expected_sha = hashlib.sha256((canonical_json_dumps(expected) + "\n").encode()).hexdigest()
        actual_sha = hashlib.sha256((canonical_json_dumps(actual) + "\n").encode()).hexdigest()
        ok = actual == expected
        return ProjectionVerification("critical_apply.projection_verification.v2", str(projection_path), ok, "PROJECTION_PARITY_PASS" if ok else "PROJECTION_PARITY_MISMATCH", expected_sha, actual_sha)
    except Exception as exc:  # noqa: BLE001
        return ProjectionVerification("critical_apply.projection_verification.v2", str(projection_path), False, "PROJECTION_MISSING_OR_INVALID", details={"error": str(exc)})


def phase_terminal_fixture_events(transaction_id: str) -> list[Mapping[str, Any]]:
    actor = ActorIdentity.synthetic("m1_phase_terminal_fixture")
    events: list[Mapping[str, Any]] = []
    prev = GENESIS_PREVIOUS_SHA256
    seq = 1
    for phase in Phase:
        e = event_from_parts(transaction_id, seq, "phase_seen", phase.value, previous_event_sha256=prev, actor=actor)
        events.append(e); prev = e["event_sha256"]; seq += 1
    for terminal in Terminal:
        e = event_from_parts(transaction_id, seq, "terminal_seen", Phase.TERMINAL.value, previous_event_sha256=prev, actor=actor, terminal=terminal.value)
        events.append(e); prev = e["event_sha256"]; seq += 1
    return events


_IDEMPOTENCY_SYSTEM_FIELDS = {
    "sequence", "previous_event_sha256", "event_sha256", "proposal_sha256", "event_id"
}


def proposal_hash(proposal: Mapping[str, Any]) -> str:
    """Digest caller-controlled proposal bytes, excluding journal-assigned fields."""
    semantic = {k: v for k, v in dict(proposal).items() if k not in _IDEMPOTENCY_SYSTEM_FIELDS}
    return hashlib.sha256(canonical_json_dumps(semantic).encode("utf-8")).hexdigest()


def _ack_from_event(event: Mapping[str, Any], committed_offset: int) -> JournalIdempotencyAck:
    return JournalIdempotencyAck(
        schema="critical_apply.journal_idempotency_ack.v1",
        transaction_id=str(event["transaction_id"]),
        event_id=str(event["event_id"]),
        proposal_sha256=str(event["proposal_sha256"]),
        sequence=int(event["sequence"]),
        event_sha256=str(event["event_sha256"]),
        previous_event_sha256=str(event["previous_event_sha256"]),
        committed_offset=committed_offset,
    )


def reconstruct_idempotency_map(validated: ValidatedJournal) -> dict[tuple[str, str], dict[str, Any]]:
    """Rebuild canonical idempotency state only from a verified journal."""
    if not validated.ok:
        raise JournalIntegrityError("JOURNAL_NOT_VERIFIED", validated.classification.value)
    out: dict[tuple[str, str], dict[str, Any]] = {}
    offset = 0
    for event in validated.events:
        offset += len(encode_event_line(event))
        event_id = event.get("event_id")
        proposal_sha256 = event.get("proposal_sha256")
        if event_id is None and proposal_sha256 is None:
            continue  # predecessor event, not part of the explicit-idempotency map
        if not isinstance(event_id, str) or not event_id or not isinstance(proposal_sha256, str) or not is_sha256(proposal_sha256):
            raise JournalIntegrityError("IDEMPOTENCY_FIELDS_INVALID", str(event.get("sequence")))
        if proposal_hash(event) != proposal_sha256:
            raise JournalIntegrityError("PROPOSAL_SHA256_MISMATCH", event_id)
        key = (validated.transaction_id, event_id)
        ack = _ack_from_event(event, offset).to_json()
        prior = out.get(key)
        if prior is not None:
            if prior["proposal_sha256"] != proposal_sha256:
                raise JournalIntegrityError("INTEGRITY_CONFLICT_HOLD", event_id)
            raise JournalIntegrityError("DUPLICATE_CANONICAL_EVENT_ID", event_id)
        out[key] = {
            "proposal_sha256": proposal_sha256,
            "sequence": int(event["sequence"]),
            "event_sha256": str(event["event_sha256"]),
            "ack": ack,
        }
    return out


def _ack_from_json(value: Mapping[str, Any]) -> JournalIdempotencyAck:
    return JournalIdempotencyAck(**{k: value[k] for k in JournalIdempotencyAck.__dataclass_fields__})


def append_event_idempotent(
    transaction_root: Path,
    proposal: Mapping[str, Any],
    *,
    event_id: str,
    writer_token: JournalWriterToken,
    progressdb_path: Path | None = None,
    failpoint: str | None = None,
) -> JournalIdempotencyAck:
    """Append exactly once by ``(transaction_id,event_id)``.

    Duplicate decisions always come from a fully verified journal. ProgressDB is
    rebuilt first when absent, stale, or corrupt and is only an acceleration.
    """
    if not isinstance(event_id, str) or not event_id or len(event_id.encode("utf-8")) > 512:
        raise JournalIntegrityError("EVENT_ID_INVALID", repr(event_id))
    root = Path(transaction_root).resolve(strict=True)
    if writer_token.root_realpath != str(root):
        raise JournalIntegrityError("WRITER_TOKEN_ROOT_MISMATCH", writer_token.root_realpath)
    if proposal.get("transaction_id") != writer_token.transaction_id:
        raise JournalIntegrityError("PROPOSAL_TRANSACTION_ID_MISMATCH", str(proposal.get("transaction_id")))
    digest = proposal_hash(proposal)
    lock_path = root / "journal" / "idempotency.lock"
    lock_fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        validated = validate_journal(root, transaction_id=writer_token.transaction_id)
        canonical = reconstruct_idempotency_map(validated)
        from critical_apply_progress import ProgressDB

        progress = ProgressDB(progressdb_path or (root / "journal" / "progress.sqlite3"))
        progress.ensure_current(
            transaction_id=writer_token.transaction_id,
            head_sequence=validated.committed_sequence,
            head_event_sha256=validated.committed_event_sha256,
            canonical_entries=canonical,
        )
        key = (writer_token.transaction_id, event_id)
        prior = canonical.get(key)
        if prior is not None:
            if prior["proposal_sha256"] != digest:
                raise JournalIntegrityError("INTEGRITY_CONFLICT_HOLD", event_id)
            return _ack_from_json(prior["ack"])
        event = dict(proposal)
        for field in ("sequence", "previous_event_sha256", "event_sha256", "proposal_sha256", "event_id"):
            event.pop(field, None)
        event["event_id"] = event_id
        event["proposal_sha256"] = digest
        result = append_event(root, event, writer_token=writer_token)
        if failpoint == "after_event_sync_before_ack":
            raise JournalPostSyncCrash(event_id)
        verified = validate_journal(root, transaction_id=writer_token.transaction_id)
        canonical = reconstruct_idempotency_map(verified)
        exact = canonical.get(key)
        if exact is None or exact["event_sha256"] != result.event_sha256:
            raise JournalIntegrityError("POST_APPEND_REOPEN_VERIFY_FAILED", event_id)
        progress.rebuild(
            transaction_id=writer_token.transaction_id,
            head_sequence=verified.committed_sequence,
            head_event_sha256=verified.committed_event_sha256,
            entries=canonical,
        )
        return _ack_from_json(exact["ack"])
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        finally:
            os.close(lock_fd)
