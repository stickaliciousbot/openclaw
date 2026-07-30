#!/usr/bin/env python3
"""Fixture-only filesystem safety helpers for Critical Apply M3.

No production paths are inferred here. Every mutating caller supplies explicit
roots and declared write boundaries.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
import time
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from critical_apply_contracts import canonical_json_dumps, is_sha256

FILESYSTEM_POLICY_SHA256 = hashlib.sha256(b"critical-apply-m3-filesystem-policy-v1").hexdigest()
PATH_SAFETY_POLICY_SHA256 = hashlib.sha256(b"critical-apply-m3-path-safety-policy-v1").hexdigest()
OWNERSHIP_MODE_POLICY_SHA256 = hashlib.sha256(b"critical-apply-m3-ownership-mode-policy-v1").hexdigest()

class FilesystemSafetyError(ValueError):
    pass

@dataclass(frozen=True)
class Boundary:
    schema: str
    target_root: str
    allowed_relative_paths: tuple[str, ...]
    recovery_write_set: tuple[str, ...]
    guard_set: tuple[str, ...]
    forbidden_set: tuple[str, ...]
    max_file_count: int = 10000
    max_logical_bytes: int = 256 * 1024 * 1024
    max_individual_file_size: int = 64 * 1024 * 1024
    max_path_depth: int = 32
    max_path_length: int = 240
    symlink_policy: str = "reject"
    hardlink_policy: str = "reject"
    mount_policy: str = "same-device"
    mode_policy_sha256: str = OWNERSHIP_MODE_POLICY_SHA256
    path_policy_sha256: str = PATH_SAFETY_POLICY_SHA256

    def to_json(self) -> dict[str, Any]: return asdict(self)


def sha256_bytes(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

def canonical_json_sha(obj: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_dumps(obj).encode()).hexdigest()

def utc_now() -> str:
    import datetime as dt
    return dt.datetime.now(dt.UTC).strftime('%Y-%m-%dT%H:%M:%SZ')

def read_boot_id() -> str:
    try: return Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    except FileNotFoundError: return 'fixture-boot-id'

def real_dir(path: Path, *, label: str) -> Path:
    p=Path(path)
    st=os.lstat(p)
    if stat.S_ISLNK(st.st_mode): raise FilesystemSafetyError(f'{label}_SYMLINK')
    if not stat.S_ISDIR(st.st_mode): raise FilesystemSafetyError(f'{label}_NOT_DIRECTORY')
    return p.resolve(strict=True)

def is_relative_safe(rel: str, *, max_depth: int = 32, max_length: int = 240) -> bool:
    if rel in ('', '.') or '//' in rel or '\x00' in rel: return False
    p=Path(rel)
    if p.is_absolute() or '..' in p.parts: return False
    if len(rel) > max_length or len(p.parts) > max_depth: return False
    if any(part in ('', '.', '..') for part in p.parts): return False
    return True

def validate_relative_path(rel: str, *, max_depth: int = 32, max_length: int = 240) -> str:
    rel=rel.replace('\\','/')
    if not is_relative_safe(rel, max_depth=max_depth, max_length=max_length):
        raise FilesystemSafetyError('PATH_UNSAFE:'+rel)
    return rel

def resolve_under(root: Path, rel: str) -> Path:
    root=real_dir(root,label='ROOT')
    safe=validate_relative_path(rel)
    p=(root/safe).resolve(strict=False)
    try: p.relative_to(root)
    except ValueError as exc: raise FilesystemSafetyError('PATH_ESCAPES_ROOT:'+rel) from exc
    return p

def classify_filetype(path: Path) -> str:
    st=os.lstat(path)
    if stat.S_ISREG(st.st_mode): return 'regular'
    if stat.S_ISDIR(st.st_mode): return 'directory'
    if stat.S_ISLNK(st.st_mode): return 'symlink'
    if stat.S_ISFIFO(st.st_mode): return 'fifo'
    if stat.S_ISSOCK(st.st_mode): return 'socket'
    if stat.S_ISCHR(st.st_mode): return 'char-device'
    if stat.S_ISBLK(st.st_mode): return 'block-device'
    return 'unknown'

def stable_file_copy(src: Path, dst: Path, *, root: Path) -> Mapping[str, Any]:
    src=Path(src); dst=Path(dst); root=real_dir(root,label='SOURCE_ROOT')
    fd=os.open(src, os.O_RDONLY | getattr(os,'O_NOFOLLOW',0))
    try:
        pre=os.fstat(fd)
        if not stat.S_ISREG(pre.st_mode): raise FilesystemSafetyError('SOURCE_NOT_REGULAR')
        h=hashlib.sha256(); total=0
        dst.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        out=os.open(dst, os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0), stat.S_IMODE(pre.st_mode)&0o777)
        try:
            while True:
                data=os.read(fd,1024*1024)
                if not data: break
                h.update(data); total += len(data); os.write(out,data)
            os.fsync(out)
        finally: os.close(out)
        post=os.fstat(fd)
        stable=(pre.st_dev,pre.st_ino,pre.st_mode,pre.st_uid,pre.st_gid,pre.st_size,pre.st_mtime_ns,pre.st_nlink)==(post.st_dev,post.st_ino,post.st_mode,post.st_uid,post.st_gid,post.st_size,post.st_mtime_ns,post.st_nlink)
        if not stable: raise FilesystemSafetyError('SOURCE_UNSTABLE')
        if total != pre.st_size: raise FilesystemSafetyError('SOURCE_SIZE_CHANGED')
        digest=h.hexdigest()
        if sha256_file(dst)!=digest: raise FilesystemSafetyError('COPIED_HASH_MISMATCH')
        return {'path':str(src),'device':pre.st_dev,'inode':pre.st_ino,'mode':oct(stat.S_IMODE(pre.st_mode)),'uid':pre.st_uid,'gid':pre.st_gid,'size':pre.st_size,'mtime_ns':pre.st_mtime_ns,'nlink':pre.st_nlink,'sha256':digest,'byte_count':total}
    finally: os.close(fd)

def inventory_tree(root: Path, *, boundary: Boundary | None = None, allow_symlinks: bool = False) -> Mapping[str, Any]:
    root=real_dir(root,label='INVENTORY_ROOT')
    base_dev=os.lstat(root).st_dev
    entries=[]; seen_norm=set(); total=files=dirs=symlinks=0
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        d=Path(dirpath); dst=os.lstat(d)
        if dst.st_dev != base_dev: raise FilesystemSafetyError('MOUNT_CROSSING')
        rel_dir='.' if d==root else str(d.relative_to(root))
        for name in list(dirnames):
            p=d/name; st=os.lstat(p)
            if stat.S_ISLNK(st.st_mode): raise FilesystemSafetyError('DIR_SYMLINK_UNSAFE')
            if st.st_dev != base_dev: raise FilesystemSafetyError('MOUNT_CROSSING')
        names=sorted(dirnames)+sorted(filenames)
        for name in names:
            p=d/name; rel=str(p.relative_to(root)); rel=validate_relative_path(rel, max_depth=boundary.max_path_depth if boundary else 32, max_length=boundary.max_path_length if boundary else 240)
            norm=unicodedata.normalize('NFC', rel).casefold()
            if norm in seen_norm: raise FilesystemSafetyError('PATH_COLLISION:'+rel)
            seen_norm.add(norm)
            st=os.lstat(p); ft=classify_filetype(p)
            if stat.S_ISLNK(st.st_mode):
                if not allow_symlinks: raise FilesystemSafetyError('SYMLINK_UNSAFE:'+rel)
                link=os.readlink(p)
                if Path(link).is_absolute() or '..' in Path(link).parts: raise FilesystemSafetyError('SYMLINK_UNSAFE:'+rel)
                symlinks += 1; sha=None; size=0
            elif stat.S_ISREG(st.st_mode):
                if st.st_nlink > 1: raise FilesystemSafetyError('HARDLINK_UNSAFE:'+rel)
                if stat.S_IMODE(st.st_mode)&0o6000: raise FilesystemSafetyError('SETUID_SETGID_UNSAFE:'+rel)
                if boundary and st.st_size > boundary.max_individual_file_size: raise FilesystemSafetyError('FILE_TOO_LARGE:'+rel)
                sha=sha256_file(p); size=st.st_size; total += size; files += 1
            elif stat.S_ISDIR(st.st_mode):
                sha=None; size=0; dirs += 1
            else: raise FilesystemSafetyError('FILETYPE_UNSAFE:'+rel)
            entries.append({'path':rel,'type':ft,'mode':oct(stat.S_IMODE(st.st_mode)),'uid':st.st_uid,'gid':st.st_gid,'size':size,'sha256':sha,'device':st.st_dev,'inode':st.st_ino,'mtime_ns':st.st_mtime_ns})
            if boundary and len(entries) > boundary.max_file_count: raise FilesystemSafetyError('FILE_COUNT_LIMIT')
            if boundary and total > boundary.max_logical_bytes: raise FilesystemSafetyError('LOGICAL_BYTES_LIMIT')
    return {'schema':'critical_apply.inventory.v2','root':str(root),'file_count':files,'directory_count':dirs,'symlink_count':symlinks,'total_logical_bytes':total,'entries':sorted(entries,key=lambda e:e['path']),'inventory_sha256':canonical_json_sha({'entries':sorted(entries,key=lambda e:e['path'])})}

def compare_inventories(a: Mapping[str,Any], b: Mapping[str,Any]) -> bool:
    strip=lambda x:[{k:v for k,v in e.items() if k not in ('device','inode','mtime_ns')} for e in x.get('entries',[])]
    return strip(a)==strip(b)

def fsync_tree(root: Path) -> None:
    root=real_dir(root,label='FSYNC_ROOT')
    for dirpath, dirnames, filenames in os.walk(root, topdown=False, followlinks=False):
        for fn in filenames:
            p=Path(dirpath)/fn
            if stat.S_ISREG(os.lstat(p).st_mode):
                fd=os.open(p,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)); os.fsync(fd); os.close(fd)
        fd=os.open(dirpath, os.O_RDONLY|getattr(os,'O_DIRECTORY',0)); os.fsync(fd); os.close(fd)

def ensure_same_filesystem(a: Path, b: Path) -> int:
    da=os.lstat(a).st_dev; db=os.lstat(b).st_dev
    if da!=db: raise FilesystemSafetyError('FILESYSTEM_POLICY_MISMATCH')
    return da

def boundary_digest(boundary: Boundary) -> str: return canonical_json_sha(boundary.to_json())

def assert_write_allowed(boundary: Boundary, rel: str) -> None:
    rel=validate_relative_path(rel,max_depth=boundary.max_path_depth,max_length=boundary.max_path_length)
    allowed=set(boundary.recovery_write_set)
    if rel not in allowed and not any(rel.startswith(x.rstrip('/')+'/') for x in allowed):
        raise FilesystemSafetyError('WRITE_OUTSIDE_RECOVERY_SET:'+rel)
    if rel in boundary.guard_set or rel in boundary.forbidden_set:
        raise FilesystemSafetyError('WRITE_GUARD_OR_FORBIDDEN:'+rel)
