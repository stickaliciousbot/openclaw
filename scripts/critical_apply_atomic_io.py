#!/usr/bin/env python3
"""Crash-consistent evidence-kernel atomic I/O primitives (M1).

This module is deliberately filesystem-only. Every operation requires an
explicit caller-supplied root, validates containment, rejects symlink traversal,
and never infers or mutates production OpenClaw paths.
"""
from __future__ import annotations

import datetime as _dt
import errno
import hashlib
import json
import os
import secrets
import stat
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from critical_apply_contracts import ContractError, canonical_json_dumps, strict_json_loads

ARTIFACT_DIGEST_SCHEMA = "critical_apply.artifact_digest.v2"
RESERVE_SCHEMA = "critical_apply.evidence_reserve.v2"
RESERVE_RELEASE_SCHEMA = "critical_apply.evidence_reserve_release.v2"


class EvidenceIOError(ContractError):
    """Fail-closed atomic I/O error."""


@dataclass(frozen=True)
class ArtifactDigest:
    schema: str
    relative_path: str
    sha256: str
    byte_count: int
    device: int
    inode: int
    mode: str
    file_type: str
    published_wall_time: str
    monotonic_ns: int
    final_realpath: str

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ClassifiedTemp:
    relative_path: str
    sha256: str | None
    byte_count: int
    classification: str


@dataclass(frozen=True)
class EvidenceReserve:
    schema: str
    path: str
    byte_count: int
    allocation_method: str
    digest: ArtifactDigest
    released: bool = False

    def to_json(self) -> dict[str, Any]:
        d = asdict(self)
        d["digest"] = self.digest.to_json()
        return d


@dataclass(frozen=True)
class EvidenceReserveRelease:
    schema: str
    path: str
    released: bool
    already_released: bool
    wall_time: str
    monotonic_ns: int

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EmergencyReceipt:
    schema: str
    phase: str
    reason: str
    reserve_released: bool
    journal_head_preserved: Mapping[str, Any]
    evidence_degraded: bool = True

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


def utc_now() -> str:
    return _dt.datetime.now(_dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _file_type(st_mode: int) -> str:
    if stat.S_ISREG(st_mode):
        return "regular file"
    if stat.S_ISDIR(st_mode):
        return "directory"
    if stat.S_ISLNK(st_mode):
        return "symlink"
    if stat.S_ISFIFO(st_mode):
        return "fifo"
    if stat.S_ISSOCK(st_mode):
        return "socket"
    if stat.S_ISCHR(st_mode):
        return "character device"
    if stat.S_ISBLK(st_mode):
        return "block device"
    return "unknown"


def _resolve_root(root: Path) -> Path:
    r = Path(root).expanduser().resolve(strict=True)
    st = os.lstat(r)
    if not stat.S_ISDIR(st.st_mode):
        raise EvidenceIOError("ROOT_NOT_DIRECTORY", str(r))
    return r


def relative_to_root(path: Path, *, root: Path) -> str:
    r = _resolve_root(root)
    try:
        return str(Path(path).resolve(strict=False).relative_to(r))
    except ValueError as exc:
        raise EvidenceIOError("PATH_OUTSIDE_ROOT", str(path)) from exc


def validate_relative_path(rel: str) -> Path:
    p = Path(rel)
    if p.is_absolute() or ".." in p.parts or rel in ("", "."):
        raise EvidenceIOError("UNSAFE_RELATIVE_PATH", rel)
    return p


def validate_parent_for_write(path: Path, *, root: Path, allow_symlink_parent: bool = False) -> tuple[Path, Path, str]:
    r = _resolve_root(root)
    p = Path(path)
    if p.is_absolute():
        try:
            rel = p.resolve(strict=False).relative_to(r)
        except ValueError as exc:
            raise EvidenceIOError("PATH_OUTSIDE_ROOT", str(path)) from exc
    else:
        rel = validate_relative_path(str(p))
        p = r / rel
    if ".." in rel.parts:
        raise EvidenceIOError("PATH_TRAVERSAL", str(path))
    parent = p.parent
    parent_st = os.lstat(parent)
    if stat.S_ISLNK(parent_st.st_mode) and not allow_symlink_parent:
        raise EvidenceIOError("SYMLINK_PARENT_REJECTED", str(parent))
    parent_real = parent.resolve(strict=True)
    try:
        parent_real.relative_to(r)
    except ValueError as exc:
        raise EvidenceIOError("PARENT_OUTSIDE_ROOT", str(parent_real)) from exc
    if not parent_real.is_dir():
        raise EvidenceIOError("PARENT_NOT_DIRECTORY", str(parent_real))
    return r, parent_real / p.name, str(rel)


def validate_existing_regular(path: Path, *, root: Path) -> tuple[Path, os.stat_result, str]:
    r = _resolve_root(root)
    p = Path(path)
    if not p.is_absolute():
        relp = validate_relative_path(str(p))
        p = r / relp
    try:
        rel = p.resolve(strict=False).relative_to(r)
    except ValueError as exc:
        raise EvidenceIOError("PATH_OUTSIDE_ROOT", str(path)) from exc
    st = os.lstat(p)
    if stat.S_ISLNK(st.st_mode):
        raise EvidenceIOError("SYMLINK_REJECTED", str(p))
    if not stat.S_ISREG(st.st_mode):
        raise EvidenceIOError("NOT_REGULAR_FILE", str(p), details={"file_type": _file_type(st.st_mode)})
    return p, st, str(rel)


def _digest_for(path: Path, *, root: Path, wall_time: str | None = None) -> ArtifactDigest:
    p, st, rel = validate_existing_regular(path, root=root)
    digest = sha256_file(p)
    return ArtifactDigest(
        schema=ARTIFACT_DIGEST_SCHEMA,
        relative_path=rel,
        sha256=digest,
        byte_count=st.st_size,
        device=st.st_dev,
        inode=st.st_ino,
        mode=oct(stat.S_IMODE(st.st_mode)),
        file_type=_file_type(st.st_mode),
        published_wall_time=wall_time or utc_now(),
        monotonic_ns=time.monotonic_ns(),
        final_realpath=str(p.resolve(strict=True)),
    )


def _complete_write(fd: int, data: bytes, *, failpoint: str | None = None) -> None:
    view = memoryview(data)
    total = 0
    while total < len(data):
        if failpoint == "during_partial_write" and total == 0:
            first = max(1, len(data) // 2)
            os.write(fd, view[:first])
            os._exit(120)
        try:
            written = os.write(fd, view[total:])
        except InterruptedError:
            continue
        if written == 0:
            raise EvidenceIOError("SHORT_WRITE", "write returned zero")
        total += written


def _temp_name(target: Path) -> str:
    return f".{target.name}.critical-apply-tmp-{secrets.token_hex(16)}"


def _write_temp_bytes(target: Path, data: bytes, *, mode: int, failpoint: str | None = None) -> Path:
    if failpoint == "before_temp_create":
        os._exit(111)
    tmp = target.parent / _temp_name(target)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(tmp, flags, mode)
    try:
        if failpoint == "after_temp_create":
            os._exit(112)
        _complete_write(fd, data, failpoint=failpoint)
        if failpoint == "after_complete_write_before_file_fsync":
            os._exit(113)
        os.fsync(fd)
        if failpoint == "after_file_fsync":
            os._exit(114)
    finally:
        os.close(fd)
    return tmp


def _encode_json(value: Mapping[str, Any]) -> bytes:
    return (canonical_json_dumps(dict(value)) + "\n").encode("utf-8")


def atomic_create_bytes(path: Path, data: bytes, *, root: Path, mode: int = 0o600, failpoint: str | None = None) -> ArtifactDigest:
    r, target, _rel = validate_parent_for_write(path, root=root)
    if target.exists() or target.is_symlink():
        raise EvidenceIOError("IMMUTABLE_TARGET_EXISTS", str(target))
    tmp = _write_temp_bytes(target, data, mode=mode, failpoint=failpoint)
    try:
        if failpoint == "immediately_before_publication":
            os._exit(115)
        os.link(tmp, target)
        if failpoint == "immediately_after_publication":
            os._exit(116)
        os.unlink(tmp)
        if failpoint == "before_parent_dir_fsync":
            os._exit(117)
        _fsync_dir(target.parent)
        if failpoint == "after_parent_dir_fsync":
            os._exit(118)
        if failpoint == "before_final_digest_verification":
            os._exit(119)
        digest = _digest_for(target, root=r)
        if digest.sha256 != sha256_bytes(data) or digest.byte_count != len(data):
            raise EvidenceIOError("DIGEST_VERIFICATION_FAILED", str(target))
        if failpoint == "after_final_digest_verification":
            os._exit(121)
        return digest
    finally:
        if tmp.exists():
            try:
                st = os.lstat(tmp)
                if stat.S_ISREG(st.st_mode) and tmp.name.startswith(f".{target.name}.critical-apply-tmp-"):
                    tmp.unlink()
            except FileNotFoundError:
                pass


def atomic_replace_bytes(path: Path, data: bytes, *, root: Path, mode: int = 0o600, failpoint: str | None = None) -> ArtifactDigest:
    r, target, _rel = validate_parent_for_write(path, root=root)
    if target.exists():
        st = os.lstat(target)
        if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
            raise EvidenceIOError("REPLACE_TARGET_NOT_REGULAR", str(target))
    tmp = _write_temp_bytes(target, data, mode=mode, failpoint=failpoint)
    if failpoint == "immediately_before_publication":
        os._exit(115)
    os.replace(tmp, target)
    os.chmod(target, mode)
    if failpoint == "immediately_after_publication":
        os._exit(116)
    if failpoint == "before_parent_dir_fsync":
        os._exit(117)
    _fsync_dir(target.parent)
    if failpoint == "after_parent_dir_fsync":
        os._exit(118)
    digest = _digest_for(target, root=r)
    if digest.sha256 != sha256_bytes(data) or digest.byte_count != len(data):
        raise EvidenceIOError("DIGEST_VERIFICATION_FAILED", str(target))
    return digest


def atomic_create_json(path: Path, value: Mapping[str, Any], *, root: Path, mode: int = 0o600, failpoint: str | None = None) -> ArtifactDigest:
    return atomic_create_bytes(path, _encode_json(value), root=root, mode=mode, failpoint=failpoint)


def atomic_replace_json(path: Path, value: Mapping[str, Any], *, root: Path, mode: int = 0o600, failpoint: str | None = None) -> ArtifactDigest:
    return atomic_replace_bytes(path, _encode_json(value), root=root, mode=mode, failpoint=failpoint)


def read_json_artifact(path: Path, *, root: Path) -> Mapping[str, Any]:
    p, _st, _rel = validate_existing_regular(path, root=root)
    return strict_json_loads(p.read_text(encoding="utf-8"))


def classify_temp_artifacts(parent: Path, *, root: Path, target_name: str) -> list[ClassifiedTemp]:
    r = _resolve_root(root)
    real = Path(parent).resolve(strict=True)
    try:
        real.relative_to(r)
    except ValueError as exc:
        raise EvidenceIOError("PATH_OUTSIDE_ROOT", str(parent)) from exc
    out: list[ClassifiedTemp] = []
    prefix = f".{target_name}.critical-apply-tmp-"
    for item in sorted(real.iterdir()):
        if not item.name.startswith(prefix):
            continue
        st = os.lstat(item)
        if not stat.S_ISREG(st.st_mode):
            out.append(ClassifiedTemp(str(item.relative_to(r)), None, 0, "UNSAFE_TEMP_NOT_REGULAR"))
            continue
        digest = sha256_file(item)
        out.append(ClassifiedTemp(str(item.relative_to(r)), digest, st.st_size, "CLASSIFIED_ABANDONED_TEMP"))
    return out


def create_evidence_reserve(transaction_root: Path, *, bytes_required: int) -> EvidenceReserve:
    if bytes_required <= 0:
        raise EvidenceIOError("RESERVE_SIZE_INVALID", str(bytes_required))
    root = _resolve_root(transaction_root)
    reserve_dir = root / "reserve"
    reserve_dir.mkdir(mode=0o700, exist_ok=True)
    _fsync_dir(reserve_dir.parent)
    path = reserve_dir / "evidence-reserve.bin"
    if path.exists() or path.is_symlink():
        raise EvidenceIOError("RESERVE_ALREADY_EXISTS", str(path))
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    method = "write_fsync_fallback"
    try:
        if hasattr(os, "posix_fallocate"):
            try:
                os.posix_fallocate(fd, 0, bytes_required)
                method = "posix_fallocate"
            except OSError:
                method = "write_fsync_fallback"
                chunk = b"\0" * min(1024 * 1024, bytes_required)
                remaining = bytes_required
                while remaining:
                    n = min(len(chunk), remaining)
                    os.write(fd, chunk[:n])
                    remaining -= n
        else:
            chunk = b"\0" * min(1024 * 1024, bytes_required)
            remaining = bytes_required
            while remaining:
                n = min(len(chunk), remaining)
                os.write(fd, chunk[:n])
                remaining -= n
        os.fsync(fd)
    finally:
        os.close(fd)
    os.chmod(path, 0o600)
    _fsync_dir(path.parent)
    st = os.lstat(path)
    if st.st_size < bytes_required:
        raise EvidenceIOError("RESERVE_ALLOCATION_NOT_COMMITTED", str(path))
    return EvidenceReserve(RESERVE_SCHEMA, "reserve/evidence-reserve.bin", bytes_required, method, _digest_for(path, root=root))


def release_evidence_reserve(reserve: EvidenceReserve, *, transaction_root: Path) -> EvidenceReserveRelease:
    root = _resolve_root(transaction_root)
    rel = validate_relative_path(reserve.path)
    path = root / rel
    already = False
    try:
        st = os.lstat(path)
        if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
            raise EvidenceIOError("RESERVE_PATH_SUBSTITUTION", str(path))
        path.unlink()
        _fsync_dir(path.parent)
    except FileNotFoundError:
        already = True
    return EvidenceReserveRelease(RESERVE_RELEASE_SCHEMA, reserve.path, True, already, utc_now(), time.monotonic_ns())


def minimal_emergency_receipt(phase: str, reason: str, *, reserve_released: bool, journal_head: Mapping[str, Any]) -> Mapping[str, Any]:
    return EmergencyReceipt(
        schema="critical_apply.emergency_evidence_receipt.v2",
        phase=phase,
        reason=reason,
        reserve_released=reserve_released,
        journal_head_preserved=dict(journal_head),
    ).to_json()


def classify_evidence_space_failure(phase: str, *, mutation_released: bool) -> str:
    if not mutation_released:
        return "PRE_MUTATION_EVIDENCE_SPACE_HOLD_NO_APPROVAL_CONSUMED"
    return "POST_MUTATION_EVIDENCE_DEGRADED_HOLD_NO_UNQUALIFIED_SUCCESS"
