#!/usr/bin/env python3
"""Critical Apply v2 M2 held-kernel-lock and fencing primitives.

Fixture/future-root only. This module never infers production roots, never
executes commands, and never mutates OpenClaw/Gateway/cron/provider surfaces.
"""
from __future__ import annotations

import datetime as _dt
import fcntl
import hashlib
import os
import pickle
import secrets
import stat
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from critical_apply_atomic_io import EvidenceIOError, atomic_create_json, atomic_replace_json, read_json_artifact, sha256_bytes
from critical_apply_contracts import ContractError, canonical_json_dumps, is_sha256, strict_json_loads

LOCK_RECEIPT_SCHEMA = "critical_apply.kernel_lock_receipt.v2"
FENCING_STATE_SCHEMA = "critical_apply.fencing_registry.v2"
FENCING_CAPABILITY_SCHEMA = "critical_apply.fencing_capability.v2"
LOCKSET_SCHEMA = "critical_apply.lock_set.v2"

RANK_GLOBAL = 0
RANK_PREFIX = 1
RANK_SURFACE = 2
RANK_JOURNAL = 3
LOCK_RANKS = {
    "global:critical-apply": RANK_GLOBAL,
    "package-manager:global-prefix": RANK_PREFIX,
    "transaction:journal": RANK_JOURNAL,
}
SURFACE_ALIASES = {
    "npm-prefix": "package-manager:global-prefix",
    "global-prefix": "package-manager:global-prefix",
    "openclaw-package": "surface:openclaw-official-package-root",
    "openclaw-official-package-root": "surface:openclaw-official-package-root",
    "npm-link": "surface:npm-executable-link",
    "npm-executable-link": "surface:npm-executable-link",
}
SURFACE_IDENTITIES = {
    "global critical apply": "global:critical-apply",
    "npm/global prefix": "package-manager:global-prefix",
    "OpenClaw official package root": "surface:openclaw-official-package-root",
    "npm executable link": "surface:npm-executable-link",
    "npm metadata": "surface:npm-metadata",
    "Gateway lifecycle": "surface:gateway-lifecycle",
    "Gateway config/routes": "surface:gateway-config-routes",
    "strict cron definitions": "surface:strict-cron-definitions",
    "scheduler state": "surface:scheduler-state",
    "protected writer state": "surface:protected-writer-state",
    "protected memory": "surface:protected-memory",
    "Runtime Kernel": "surface:runtime-kernel",
    "Ledger": "surface:ledger",
    "Context Bridge": "surface:context-bridge",
    "model routing": "surface:model-routing",
    "provider/delivery surface": "surface:provider-delivery",
    "transaction journal": "transaction:journal",
}

class LockError(ContractError):
    pass

class LockAcquireBlocked(LockError):
    def __init__(self, lock_id: str):
        super().__init__("LOCK_ACQUIRE_BLOCKED", lock_id, details={"lock_id": lock_id})

@dataclass(frozen=True)
class FencingCapability:
    schema: str
    lock_root_realpath: str
    transaction_id: str
    generation: int
    token_sha256: str
    boot_id: str
    _token: str = field(repr=False, compare=False)
    _active: bool = field(default=True, repr=False, compare=False)

    def to_receipt(self) -> dict[str, Any]:
        return {"schema": self.schema, "lock_root_realpath": self.lock_root_realpath, "transaction_id": self.transaction_id, "generation": self.generation, "token_sha256": self.token_sha256, "boot_id": self.boot_id, "token_redacted": True}

    def assert_active(self, *, lock_root: Path, transaction_id: str) -> None:
        if not self._active:
            raise LockError("FENCING_TOKEN_INACTIVE", transaction_id)
        if self.lock_root_realpath != str(Path(lock_root).resolve(strict=True)):
            raise LockError("FENCING_TOKEN_ROOT_MISMATCH", transaction_id)
        if self.transaction_id != transaction_id:
            raise LockError("FENCING_TOKEN_TRANSACTION_MISMATCH", transaction_id)
        if hashlib.sha256(self._token.encode()).hexdigest() != self.token_sha256:
            raise LockError("FENCING_TOKEN_HASH_MISMATCH", transaction_id)

    def _released(self) -> "FencingCapability":
        return FencingCapability(self.schema, self.lock_root_realpath, self.transaction_id, self.generation, self.token_sha256, self.boot_id, self._token, False)

@dataclass
class KernelLock:
    lock_root: Path
    lock_id: str
    transaction_id: str
    surface_sets_sha256: str
    expected_rank: int
    fd: int
    path: Path
    receipt: Mapping[str, Any]
    released: bool = False

    @classmethod
    def acquire(cls, *, lock_root: Path, lock_id: str, transaction_id: str, surface_sets_sha256: str, expected_rank: int, nonblocking: bool = True) -> "KernelLock":
        root = _trusted_root(lock_root)
        lid = canonical_lock_id(lock_id)
        rank = lock_rank(lid)
        if rank != expected_rank:
            raise LockError("LOCK_RANK_MISMATCH", lid, details={"expected": expected_rank, "actual": rank})
        if not is_sha256(surface_sets_sha256):
            raise LockError("SURFACE_SET_HASH_INVALID", surface_sets_sha256)
        lock_dir = root / "locks" / str(rank)
        lock_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        _reject_symlink_chain(lock_dir, root)
        path = lock_dir / (_lock_key(lid) + ".lock")
        flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
        fd = os.open(path, flags, 0o600)
        try:
            st = os.fstat(fd)
            if not stat.S_ISREG(st.st_mode):
                raise LockError("LOCK_NOT_REGULAR", str(path))
            if st.st_nlink != 1:
                raise LockError("LOCK_HARDLINK_POLICY", str(path), details={"nlink": st.st_nlink})
            how = fcntl.LOCK_EX | (fcntl.LOCK_NB if nonblocking else 0)
            try:
                fcntl.flock(fd, how)
            except BlockingIOError as exc:
                raise LockAcquireBlocked(lid) from exc
            flags_now = fcntl.fcntl(fd, fcntl.F_GETFD)
            if not (flags_now & fcntl.FD_CLOEXEC):
                fcntl.fcntl(fd, fcntl.F_SETFD, flags_now | fcntl.FD_CLOEXEC)
            if not (fcntl.fcntl(fd, fcntl.F_GETFD) & fcntl.FD_CLOEXEC):
                raise LockError("FD_CLOEXEC_NOT_SET", lid)
            receipt = _lock_receipt(lid, path, transaction_id, surface_sets_sha256, st)
            os.ftruncate(fd, 0)
            os.write(fd, (canonical_json_dumps(receipt) + "\n").encode())
            os.fsync(fd)
            return cls(root, lid, transaction_id, surface_sets_sha256, expected_rank, fd, path, receipt)
        except Exception:
            try: os.close(fd)
            except OSError: pass
            raise

    def assert_held(self) -> None:
        if self.released:
            raise LockError("LOCK_RELEASED", self.lock_id)
        try:
            os.fstat(self.fd)
        except OSError as exc:
            self.released = True
            raise LockError("LOCK_DESCRIPTOR_CLOSED", self.lock_id) from exc

    def release(self) -> None:
        if self.released:
            return
        try:
            fcntl.flock(self.fd, fcntl.LOCK_UN)
        finally:
            os.close(self.fd)
            self.released = True

    def __getstate__(self):
        raise TypeError("KernelLock is a live capability and is not serialisable")

@dataclass
class LockSet:
    locks: list[KernelLock]
    fencing: FencingCapability
    surface_set_sha256: str
    acquisition_order: tuple[str, ...]
    released: bool = False

    def assert_live(self) -> None:
        if self.released:
            raise LockError("LOCKSET_RELEASED", "released")
        self.fencing.assert_active(lock_root=self.locks[0].lock_root, transaction_id=self.locks[0].transaction_id)
        for lk in self.locks:
            lk.assert_held()
            if lk.surface_sets_sha256 != self.surface_set_sha256:
                raise LockError("LOCKSET_SURFACE_DIGEST_MISMATCH", lk.lock_id)

    @property
    def digest(self) -> str:
        self.assert_live()
        payload = {"schema": LOCKSET_SCHEMA, "locks": [l.lock_id for l in self.locks], "fencing": self.fencing.to_receipt(), "surface_set_sha256": self.surface_set_sha256}
        return hashlib.sha256(canonical_json_dumps(payload).encode()).hexdigest()

    def release(self) -> None:
        if self.released:
            return
        for lk in reversed(self.locks):
            lk.release()
        self.fencing = self.fencing._released()
        self.released = True

    def __enter__(self):
        self.assert_live(); return self
    def __exit__(self, *_):
        self.release()
    def __getstate__(self):
        raise TypeError("LockSet is a live capability and is not serialisable")

def utc_now() -> str:
    return _dt.datetime.now(_dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

def read_boot_id() -> str:
    try: return Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    except FileNotFoundError: return 'fixture-boot-id'

def process_start_ticks(pid: int | None = None) -> int:
    pid = pid or os.getpid()
    try: return int(Path(f'/proc/{pid}/stat').read_text().split()[21])
    except Exception: return 1

def _trusted_root(root: Path) -> Path:
    original = Path(root)
    try:
        st0 = os.lstat(original)
        if stat.S_ISLNK(st0.st_mode):
            raise LockError("LOCK_ROOT_SYMLINK", str(root))
    except FileNotFoundError:
        raise
    r = original.resolve(strict=True)
    st = os.lstat(r)
    if not stat.S_ISDIR(st.st_mode) or stat.S_ISLNK(st.st_mode):
        raise LockError("LOCK_ROOT_UNTRUSTED", str(root))
    return r

def _reject_symlink_chain(path: Path, root: Path) -> None:
    p = Path(path)
    p.resolve(strict=True).relative_to(root)
    cur = root
    for part in p.relative_to(root).parts:
        cur = cur / part
        if os.path.islink(cur):
            raise LockError("LOCK_PATH_SYMLINK", str(cur))

def canonical_lock_id(lock_id: str) -> str:
    if not isinstance(lock_id, str) or not lock_id:
        raise LockError("LOCK_ID_INVALID", str(lock_id))
    if lock_id in SURFACE_ALIASES:
        lock_id = SURFACE_ALIASES[lock_id]
    if any(x in lock_id for x in ['..','/','\\','*','?']) or lock_id.startswith('.'):
        raise LockError("LOCK_ID_TRAVERSAL_OR_AMBIGUOUS", lock_id)
    if lock_id in LOCK_RANKS or lock_id.startswith('surface:') or lock_id.startswith('transaction:journal:'):
        return lock_id
    raise LockError("LOCK_ID_UNKNOWN", lock_id)

def canonical_surface_id(surface: str) -> str:
    sid = SURFACE_IDENTITIES.get(surface, SURFACE_ALIASES.get(surface, surface))
    if not sid.startswith('surface:') and sid not in LOCK_RANKS:
        raise LockError("SURFACE_ID_UNKNOWN", surface)
    return canonical_lock_id(sid)

def surface_set_digest(surfaces: Sequence[str]) -> str:
    canonical = canonicalize_surface_locks(surfaces)
    return hashlib.sha256(canonical_json_dumps({"schema":"critical_apply.surface_set.v2","surfaces":canonical}).encode()).hexdigest()

def canonicalize_surface_locks(surfaces: Sequence[str]) -> tuple[str, ...]:
    ids = [canonical_surface_id(s) for s in surfaces]
    if len(set(ids)) != len(ids):
        raise LockError("DUPLICATE_OR_ALIAS_SURFACE", ','.join(ids))
    return tuple(sorted(ids))

def lock_rank(lock_id: str) -> int:
    lid = canonical_lock_id(lock_id)
    if lid in LOCK_RANKS:
        return LOCK_RANKS[lid]
    if lid.startswith('surface:'):
        return RANK_SURFACE
    if lid.startswith('transaction:journal:'):
        return RANK_JOURNAL
    raise LockError("LOCK_RANK_UNKNOWN", lid)

def _lock_key(lock_id: str) -> str:
    return hashlib.sha256(lock_id.encode()).hexdigest()

def _lock_receipt(lock_id: str, path: Path, transaction_id: str, surface_hash: str, st: os.stat_result) -> dict[str, Any]:
    token_hash_placeholder = hashlib.sha256(f"{transaction_id}:{lock_id}".encode()).hexdigest()
    return {"schema":LOCK_RECEIPT_SCHEMA,"lock_id":lock_id,"canonical_lock_path":str(path.resolve(strict=False)),"transaction_id":transaction_id,"fencing_generation":None,"fencing_token_sha256":token_hash_placeholder,"pid":os.getpid(),"process_start_ticks":process_start_ticks(),"boot_id":read_boot_id(),"uid":os.getuid(),"gid":os.getgid(),"cgroup_or_service_unit_identity":"fixture_or_unsupplied","acquisition_wall_time_utc":utc_now(),"acquisition_monotonic_ns":time.monotonic_ns(),"surface_set_sha256":surface_hash,"file_device":st.st_dev,"file_inode":st.st_ino,"mode":oct(stat.S_IMODE(st.st_mode)),"kernel_lock_mechanism":"fcntl.flock(LOCK_EX)"}

def issue_fencing(lock_root: Path, transaction_id: str) -> FencingCapability:
    root = _trusted_root(lock_root)
    reg = root / 'fencing'
    reg.mkdir(mode=0o700, exist_ok=True)
    path = reg / 'generation.json'
    if path.exists():
        state = read_json_artifact(path, root=root)
        if state.get('schema') != FENCING_STATE_SCHEMA or not isinstance(state.get('generation'), int) or state['generation'] < 0:
            raise LockError("FENCING_STATE_CORRUPT", str(path))
        generation = state['generation'] + 1
    else:
        generation = 1
    if generation >= 2**63:
        raise LockError("FENCING_GENERATION_WRAP", str(generation))
    token = secrets.token_hex(32)
    token_sha = hashlib.sha256(token.encode()).hexdigest()
    state = {"schema":FENCING_STATE_SCHEMA,"generation":generation,"last_transaction_id":transaction_id,"token_sha256":token_sha,"boot_id":read_boot_id(),"updated_wall_time_utc":utc_now(),"updated_monotonic_ns":time.monotonic_ns()}
    atomic_replace_json(path, state, root=root)
    return FencingCapability(FENCING_CAPABILITY_SCHEMA, str(root), transaction_id, generation, token_sha, state['boot_id'], token)

def validate_fencing_current(lock_root: Path, cap: FencingCapability) -> bool:
    cap.assert_active(lock_root=lock_root, transaction_id=cap.transaction_id)
    state = read_json_artifact(Path(lock_root)/'fencing/generation.json', root=Path(lock_root))
    if state.get('generation') != cap.generation or state.get('token_sha256') != cap.token_sha256 or state.get('last_transaction_id') != cap.transaction_id:
        raise LockError("FENCING_TOKEN_STALE", cap.transaction_id)
    return True

def validate_lock_acquisition_order(lock_ids: Sequence[str]) -> tuple[str, ...]:
    canonical = tuple(canonical_lock_id(x) for x in lock_ids)
    expected = tuple(sorted(canonical, key=lambda x: (lock_rank(x), x)))
    if canonical != expected:
        raise LockError("LOCK_ORDER_INVALID", canonical_json_dumps({"got": canonical, "expected": expected}))
    return canonical


def acquire_lockset(*, lock_root: Path, transaction_id: str, surfaces: Sequence[str], include_prefix: bool = True, allow_disjoint_without_global: bool = False) -> LockSet:
    root = _trusted_root(lock_root)
    surface_locks = canonicalize_surface_locks(surfaces)
    lock_ids: list[str] = []
    if not allow_disjoint_without_global:
        lock_ids.append('global:critical-apply')
    if include_prefix:
        lock_ids.append('package-manager:global-prefix')
    lock_ids.extend(surface_locks)
    lock_ids.append('transaction:journal:' + hashlib.sha256(transaction_id.encode()).hexdigest())
    if len(lock_ids) != len(set(lock_ids)):
        raise LockError("DUPLICATE_LOCK_ID", ','.join(lock_ids))
    ordered = sorted(lock_ids, key=lambda x: (lock_rank(x), x))
    validate_lock_acquisition_order(lock_ids)
    if 'global:critical-apply' in lock_ids:
        fencing = issue_fencing(root, transaction_id)
    else:
        token = secrets.token_hex(32)
        fencing = FencingCapability(FENCING_CAPABILITY_SCHEMA, str(root), transaction_id, 0, hashlib.sha256(token.encode()).hexdigest(), read_boot_id(), token)
    ssha = surface_set_digest(surfaces)
    locks: list[KernelLock] = []
    try:
        for lid in lock_ids:
            locks.append(KernelLock.acquire(lock_root=root, lock_id=lid, transaction_id=transaction_id, surface_sets_sha256=ssha, expected_rank=lock_rank(lid)))
        ls = LockSet(locks, fencing, ssha, tuple(lock_ids))
        ls.assert_live()
        return ls
    except Exception:
        for lk in reversed(locks): lk.release()
        raise

def classify_stale_holder(*, live_lock_held: bool, old_metadata: bool, unfinalized_mutation_released: bool, reconciliation_receipt: Mapping[str, Any] | None) -> str:
    if live_lock_held: return 'LIVE_HELD_KERNEL_LOCK_BLOCKS'
    if unfinalized_mutation_released: return 'UNFINALIZED_RELEASED_TRANSACTION_BLOCKS'
    if old_metadata and not reconciliation_receipt: return 'STALE_HOLDER_RECONCILIATION_REQUIRED'
    if reconciliation_receipt and reconciliation_receipt.get('schema') == 'critical_apply.stale_holder_reconciliation.v2' and reconciliation_receipt.get('fixture_only') is True and reconciliation_receipt.get('journal_valid') is True and reconciliation_receipt.get('holder_gone') is True and not reconciliation_receipt.get('mutation_child_remaining'):
        return 'STALE_HOLDER_RECONCILED_FIXTURE_ONLY'
    if reconciliation_receipt: return 'STALE_HOLDER_RECONCILIATION_INVALID'
    if old_metadata: return 'STALE_METADATA_NON_AUTHORITATIVE'
    return 'NO_STALE_HOLDER_CONFLICT'

def assert_lock_receipt_not_authority(receipt: Mapping[str, Any]) -> None:
    raise LockError('LOCK_RECEIPT_NOT_LIVE_AUTHORITY', str(receipt.get('lock_id')))

def pickle_roundtrip_rejected(obj: Any) -> bool:
    try:
        pickle.dumps(obj)
        return False
    except Exception:
        return True
