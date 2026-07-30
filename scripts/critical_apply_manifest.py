#!/usr/bin/env python3
"""Non-circular manifest and terminal seal primitives for Critical Apply M1."""
from __future__ import annotations

import datetime as _dt
import hashlib
import os
import stat
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from critical_apply_atomic_io import ArtifactDigest, EvidenceIOError, atomic_create_json, atomic_replace_bytes, atomic_replace_json, relative_to_root, sha256_file, validate_existing_regular, validate_relative_path
from critical_apply_contracts import canonical_json_dumps, is_sha256, strict_json_loads

MANIFEST_SCHEMA = "critical_apply.evidence_manifest.v2"
MANIFEST_SIDECAR_SCHEMA = "critical_apply.evidence_manifest_sidecar.v2"
TERMINAL_SEAL_SCHEMA = "critical_apply.terminal_seal.v2"
CODE_BUNDLE_SCHEMA = "critical_apply.code_bundle_digest.v2"
NON_CIRCULAR_POLICY = "NON_CIRCULAR_EVIDENCE_MANIFEST_POLICY_V1"
EXCLUDED_FROM_GOVERNED = {
    "manifest.json",
    "manifest.sha256",
    "manifests/evidence-manifest.json",
    "manifests/evidence-manifest.sha256",
    "terminal-seal.json",
    "reserve/evidence-reserve.bin",
}


@dataclass(frozen=True)
class ManifestEntry:
    relative_path: str
    file_type: str
    sha256: str
    byte_count: int
    mode: str
    device: int
    inode: int
    role: str
    artifact_kind: str
    governing_schema: str | None = None

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceManifestResult:
    schema: str
    manifest_digest: ArtifactDigest
    sidecar_digest: ArtifactDigest
    manifest_sha256: str
    entries_count: int
    exclusions: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "manifest_digest": self.manifest_digest.to_json(),
            "sidecar_digest": self.sidecar_digest.to_json(),
            "manifest_sha256": self.manifest_sha256,
            "entries_count": self.entries_count,
            "exclusions": list(self.exclusions),
        }


@dataclass(frozen=True)
class CodeBundleDigest:
    schema: str
    sha256: str
    files: tuple[Mapping[str, Any], ...]

    def to_json(self) -> dict[str, Any]:
        return {"schema": self.schema, "sha256": self.sha256, "files": [dict(f) for f in self.files]}


@dataclass(frozen=True)
class TerminalSealVerification:
    schema: str
    ok: bool
    classification: str
    details: Mapping[str, Any]

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


def utc_now() -> str:
    return _dt.datetime.now(_dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _file_type(st_mode: int) -> str:
    if stat.S_ISREG(st_mode): return "regular file"
    if stat.S_ISDIR(st_mode): return "directory"
    if stat.S_ISLNK(st_mode): return "symlink"
    if stat.S_ISFIFO(st_mode): return "fifo"
    if stat.S_ISSOCK(st_mode): return "socket"
    if stat.S_ISCHR(st_mode): return "character device"
    if stat.S_ISBLK(st_mode): return "block device"
    return "unknown"


def _schema_for(path: Path) -> str | None:
    if path.suffix != ".json":
        return None
    try:
        obj = strict_json_loads(path.read_text(encoding="utf-8"))
        schema = obj.get("schema") if isinstance(obj, dict) else None
        return str(schema) if schema else None
    except Exception:
        return None


def _entry_for(path: Path, *, root: Path, role: str, artifact_kind: str) -> ManifestEntry:
    p, st1, rel = validate_existing_regular(path, root=root)
    if rel in EXCLUDED_FROM_GOVERNED:
        raise EvidenceIOError("MANIFEST_SELF_OR_EXCLUDED_PATH", rel)
    sha1 = sha256_file(p)
    st2 = os.lstat(p)
    sha2 = sha256_file(p)
    if (st1.st_size, st1.st_mtime_ns, st1.st_ino, st1.st_dev, sha1) != (st2.st_size, st2.st_mtime_ns, st2.st_ino, st2.st_dev, sha2):
        raise EvidenceIOError("UNSTABLE_FILE_DURING_HASH", rel)
    mode = stat.S_IMODE(st2.st_mode)
    if mode & 0o077:
        raise EvidenceIOError("MANIFEST_MODE_POLICY_VIOLATION", rel, details={"mode": oct(mode)})
    return ManifestEntry(rel, _file_type(st2.st_mode), sha2, st2.st_size, oct(mode), st2.st_dev, st2.st_ino, role, artifact_kind, _schema_for(p))


def build_manifest_object(transaction_root: Path, *, governed_paths: Sequence[Path], code_bundle_paths: Sequence[Path]) -> Mapping[str, Any]:
    root = Path(transaction_root).resolve(strict=True)
    seen: set[str] = set()
    entries: list[ManifestEntry] = []
    for path in governed_paths:
        original = Path(path)
        candidate = original if original.is_absolute() else root / validate_relative_path(str(original))
        if candidate.exists() or candidate.is_symlink():
            st0 = os.lstat(candidate)
            if stat.S_ISLNK(st0.st_mode):
                raise EvidenceIOError("SYMLINK_GOVERNED_ARTIFACT", str(candidate))
        rel = relative_to_root(path, root=root)
        validate_relative_path(rel)
        if rel in seen:
            raise EvidenceIOError("DUPLICATE_MANIFEST_PATH", rel)
        seen.add(rel)
        entries.append(_entry_for(root / rel, root=root, role="governed", artifact_kind="immutable_or_derived"))
    code_bundle = compute_code_bundle_digest(code_bundle_paths)
    return {
        "schema": MANIFEST_SCHEMA,
        "policy": NON_CIRCULAR_POLICY,
        "transaction_root": str(root),
        "generated_wall_time_utc": utc_now(),
        "monotonic_ns": time.monotonic_ns(),
        "entries": [e.to_json() for e in sorted(entries, key=lambda e: e.relative_path)],
        "exclusions": sorted(EXCLUDED_FROM_GOVERNED),
        "code_bundle": code_bundle.to_json(),
    }


def build_evidence_manifest(transaction_root: Path, *, governed_paths: Sequence[Path], code_bundle_paths: Sequence[Path]) -> EvidenceManifestResult:
    root = Path(transaction_root).resolve(strict=True)
    manifest_dir = root / "manifests"
    manifest_dir.mkdir(mode=0o700, exist_ok=True)
    manifest = build_manifest_object(root, governed_paths=governed_paths, code_bundle_paths=code_bundle_paths)
    manifest_path = manifest_dir / "evidence-manifest.json"
    digest = atomic_replace_json(manifest_path, manifest, root=root)
    manifest_sha = digest.sha256
    sidecar = {
        "schema": MANIFEST_SIDECAR_SCHEMA,
        "format": "sha256-canonical-json",
        "manifest_path": "manifests/evidence-manifest.json",
        "manifest_sha256": manifest_sha,
        "generated_wall_time_utc": utc_now(),
    }
    sidecar_digest = atomic_replace_json(manifest_dir / "evidence-manifest.sha256", sidecar, root=root)
    verify_manifest_sidecar(root)
    return EvidenceManifestResult("critical_apply.evidence_manifest_result.v2", digest, sidecar_digest, manifest_sha, len(manifest["entries"]), tuple(sorted(EXCLUDED_FROM_GOVERNED)))


def verify_manifest_sidecar(transaction_root: Path) -> bool:
    root = Path(transaction_root).resolve(strict=True)
    manifest = root / "manifests" / "evidence-manifest.json"
    sidecar = root / "manifests" / "evidence-manifest.sha256"
    actual = sha256_file(manifest)
    obj = strict_json_loads(sidecar.read_text(encoding="utf-8"))
    if obj.get("schema") != MANIFEST_SIDECAR_SCHEMA:
        raise EvidenceIOError("MANIFEST_SIDECAR_SCHEMA_INVALID", str(sidecar))
    if obj.get("manifest_sha256") != actual:
        raise EvidenceIOError("MANIFEST_SIDECAR_MISMATCH", str(sidecar))
    return True


def compute_code_bundle_digest(paths: Sequence[Path]) -> CodeBundleDigest:
    files: list[Mapping[str, Any]] = []
    cwd = Path.cwd().resolve(strict=True)
    for p in sorted((Path(x).resolve(strict=True) for x in paths), key=lambda x: str(x)):
        if p.name.endswith(('.pyc', '.tmp')) or '__pycache__' in p.parts:
            continue
        st = os.lstat(p)
        if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
            raise EvidenceIOError("CODE_BUNDLE_FILE_INVALID", str(p))
        try:
            recorded_path = str(p.relative_to(cwd))
        except ValueError:
            recorded_path = str(p)
        files.append({"path": recorded_path, "sha256": sha256_file(p), "byte_count": st.st_size})
    bundle = {"schema": CODE_BUNDLE_SCHEMA, "files": files}
    return CodeBundleDigest(CODE_BUNDLE_SCHEMA, hashlib.sha256(canonical_json_dumps(bundle).encode()).hexdigest(), tuple(files))


def create_terminal_seal(transaction_root: Path, *, transaction_id: str, terminal: str, journal_head_sha256: str, evidence_manifest_sha256: str, runner_code_bundle_sha256: str, boot_id: str) -> ArtifactDigest:
    if not all(is_sha256(x) for x in (journal_head_sha256, evidence_manifest_sha256, runner_code_bundle_sha256)):
        raise EvidenceIOError("TERMINAL_SEAL_HASH_INVALID", transaction_id)
    root = Path(transaction_root).resolve(strict=True)
    seal_path = root / "terminal-seal.json"
    seal = {
        "schema": TERMINAL_SEAL_SCHEMA,
        "transaction_id": transaction_id,
        "terminal": terminal,
        "journal_head_sha256": journal_head_sha256,
        "evidence_manifest_sha256": evidence_manifest_sha256,
        "runner_code_bundle_sha256": runner_code_bundle_sha256,
        "seal_wall_time_utc": utc_now(),
        "monotonic_ns": time.monotonic_ns(),
        "boot_id": boot_id,
        "schema_version": "v2",
    }
    return atomic_create_json(seal_path, seal, root=root)


def verify_terminal_seal(transaction_root: Path, *, transaction_id: str, terminal: str, journal_head_sha256: str, evidence_manifest_sha256: str, runner_code_bundle_sha256: str) -> TerminalSealVerification:
    root = Path(transaction_root).resolve(strict=True)
    try:
        seal = strict_json_loads((root / "terminal-seal.json").read_text(encoding="utf-8"))
        expected = {
            "transaction_id": transaction_id,
            "terminal": terminal,
            "journal_head_sha256": journal_head_sha256,
            "evidence_manifest_sha256": evidence_manifest_sha256,
            "runner_code_bundle_sha256": runner_code_bundle_sha256,
        }
        for k, v in expected.items():
            if seal.get(k) != v:
                return TerminalSealVerification("critical_apply.terminal_seal_verification.v2", False, "TERMINAL_SEAL_BINDING_MISMATCH", {"field": k})
        if seal.get("schema") != TERMINAL_SEAL_SCHEMA:
            return TerminalSealVerification("critical_apply.terminal_seal_verification.v2", False, "TERMINAL_SEAL_SCHEMA_INVALID", {})
        return TerminalSealVerification("critical_apply.terminal_seal_verification.v2", True, "TERMINAL_SEAL_VALID", {"seal_sha256": sha256_file(root / "terminal-seal.json")})
    except FileNotFoundError:
        return TerminalSealVerification("critical_apply.terminal_seal_verification.v2", False, "TERMINAL_SEAL_MISSING", {})
    except Exception as exc:  # noqa: BLE001
        return TerminalSealVerification("critical_apply.terminal_seal_verification.v2", False, "TERMINAL_SEAL_INVALID", {"error": str(exc)})


def classify_finalization_integrity(*, final_report_exists: bool, terminal_event_exists: bool, terminal_seal_valid: bool) -> str:
    if terminal_seal_valid:
        return "TERMINAL_SEAL_VALID"
    if final_report_exists or terminal_event_exists:
        return "EVIDENCE_TAMPERED_OR_INCOMPLETE_HOLD"
    return "EVIDENCE_INCOMPLETE_HOLD"
