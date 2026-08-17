#!/usr/bin/env python3
"""OpenClaw npm package critical-apply plugin.

This module is safe to import and its default operations are read-only. Mutation
entry points are explicit and are intended to be called only by the durable
critical apply observer runner after restore-point and approval gates pass.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import tarfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from critical_apply_contracts import (
    NpmBaseClassification,
    StagingDirClassification,
    ValidationResult,
    read_json,
    receipt,
    sha256_file,
    validate_restore_point_fresh,
    write_json,
)

CRITICAL_RELATIVE_FILES = [
    "package.json",
    "openclaw.mjs",
    "dist/index.js",
    "dist/extensions/speech-core/runtime-api.js",
]

DEFAULT_PACKAGE_ROOT = Path("/home/stickai/.npm-global/lib/node_modules/openclaw")
DEFAULT_NODE_MODULES = DEFAULT_PACKAGE_ROOT.parent
DEFAULT_CLI_LINK = Path("/home/stickai/.npm-global/bin/openclaw")
PACKAGE_PLUGIN_APPLY_SCHEMA = "critical_apply.openclaw_npm.apply_operation.v1"
PACKAGE_PLUGIN_RESTORE_SCHEMA = "critical_apply.openclaw_npm.restore_point_full.v1"


def _canonical_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def _exact_abs(path: str | Path, *, field: str) -> Path:
    p = Path(path)
    if not p.is_absolute():
        raise ValueError(f"{field}_must_be_absolute")
    if ".." in p.parts:
        raise ValueError(f"{field}_must_not_contain_parent_traversal")
    return p


def _copy_preserving_symlink(src: Path, dst: Path) -> dict[str, Any]:
    if dst.exists() or dst.is_symlink():
        if dst.is_dir() and not dst.is_symlink():
            shutil.rmtree(dst)
        else:
            dst.unlink()
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not src.exists() and not src.is_symlink():
        return {"source": str(src), "destination": str(dst), "state": "absent_no_copy"}
    if src.is_symlink():
        os.symlink(os.readlink(src), dst)
        return {"source": str(src), "destination": str(dst), "state": "symlink_copied", "link_target": os.readlink(src)}
    if src.is_dir():
        shutil.copytree(src, dst, symlinks=True, copy_function=shutil.copy2)
        return {"source": str(src), "destination": str(dst), "state": "directory_copied"}
    shutil.copy2(src, dst, follow_symlinks=False)
    return {"source": str(src), "destination": str(dst), "state": "file_copied"}


def create_full_restore_point(root: str | Path, package_root: str | Path = DEFAULT_PACKAGE_ROOT, cli_link: str | Path = DEFAULT_CLI_LINK) -> dict[str, Any]:
    """Create a copy-backed restore point for the package root and CLI link.

    This helper is safe for fixture roots and is production-capable only when
    called by a durable runner after authority, lock and watcher gates pass. It
    never restarts Gateway, calls providers, mutates cron/config, or touches
    hidden npm staging directories.
    """
    root = _exact_abs(root, field="restore_root")
    package_root = _exact_abs(package_root, field="package_root")
    cli_link = _exact_abs(cli_link, field="cli_link")
    snapshot = root / "snapshot"
    package_snapshot = snapshot / "package-root"
    cli_snapshot = snapshot / "cli-link"
    root.mkdir(parents=True, exist_ok=True)
    copies = [
        _copy_preserving_symlink(package_root, package_snapshot),
        _copy_preserving_symlink(cli_link, cli_snapshot),
    ]
    manifest = receipt(
        PACKAGE_PLUGIN_RESTORE_SCHEMA,
        package_root=str(package_root),
        cli_link=str(cli_link),
        snapshot_root=str(snapshot),
        package_snapshot=str(package_snapshot),
        cli_snapshot=str(cli_snapshot),
        created_at_epoch=time.time(),
        archive_created=False,
        implementation_level="COPY_BACKED_PACKAGE_ROOT_AND_CLI_LINK",
        copies=copies,
    )
    manifest["manifest_sha256"] = _canonical_sha(manifest)
    boundary = receipt(
        "critical_apply.restore_boundary.v1",
        allowed_mutations=["openclaw_package_root", "npm_cli_link"],
        forbidden_mutations=["gateway_restart", "cron_mutation", "protected_memory", "provider_call", "functional_smoke", "systemctl"],
    )
    write_json(root / "restore-manifest.json", manifest)
    write_json(root / "restore-boundary.json", boundary)
    return manifest


def extract_package_artifact(package_path: str | Path, staging_root: str | Path, *, expected_sha256: str) -> dict[str, Any]:
    package_path = _exact_abs(package_path, field="package_path")
    staging_root = _exact_abs(staging_root, field="staging_root")
    actual = sha256_file(package_path)
    if actual != expected_sha256:
        raise ValueError(f"package_sha256_mismatch:{actual}!={expected_sha256}")
    info = inspect_package_tar(package_path)
    if info.get("unsafe_members"):
        raise ValueError("unsafe_package_tar_members")
    if not all(info.get("critical_files_found", {}).get(rel) for rel in ("package.json", "openclaw.mjs", "dist/index.js")):
        raise ValueError("package_tar_missing_required_members")
    if staging_root.exists():
        shutil.rmtree(staging_root)
    staging_root.mkdir(parents=True, exist_ok=True)
    with tarfile.open(package_path, "r:gz") as tf:
        for member in tf.getmembers():
            name = member.name[2:] if member.name.startswith("./") else member.name
            if name.startswith("/") or ".." in Path(name).parts or not name.startswith("package"):
                raise ValueError(f"unsafe_member:{member.name}")
        tf.extractall(staging_root)
    return receipt(
        "critical_apply.openclaw_npm.extract_artifact.v1",
        package_path=str(package_path),
        package_sha256=actual,
        staging_root=str(staging_root),
        staged_package_root=str(staging_root / "package"),
        package_json=(info.get("package_json") or {}),
    )


def postcheck_package_identity(package_root: str | Path, cli_link: str | Path, *, expected_version: str = "2026.5.7") -> dict[str, Any]:
    package_root = _exact_abs(package_root, field="package_root")
    cli_link = _exact_abs(cli_link, field="cli_link")
    health = inspect_package_root(package_root, expected_version=expected_version)
    reasons: list[str] = []
    if health.get("package_name") != "openclaw":
        reasons.append("package_name_not_openclaw")
    if health.get("package_version") != expected_version:
        reasons.append("package_version_mismatch")
    for rel in ("package.json", "openclaw.mjs", "dist/index.js"):
        if not (package_root / rel).exists():
            reasons.append(f"missing:{rel}")
    if not (cli_link.exists() or cli_link.is_symlink()):
        reasons.append("cli_link_missing")
    return receipt(
        "critical_apply.openclaw_npm.postcheck.v1",
        ok=not reasons,
        reasons=reasons,
        package_root=str(package_root),
        cli_link=str(cli_link),
        health=health,
    )


def apply_staged_package(staged_package_root: str | Path, target_package_root: str | Path, target_cli_link: str | Path, *, cli_link_target: str = "../lib/node_modules/openclaw/openclaw.mjs") -> dict[str, Any]:
    """Replace exact package root and CLI link from verified staging.

    The caller must hold a maintenance lock and must have written durable
    apply-start/PID receipts before calling this function. This function is
    intentionally narrow: no Gateway restart, provider smoke, systemctl,
    config/cron, npm install, or git actions.
    """
    staged_package_root = _exact_abs(staged_package_root, field="staged_package_root")
    target_package_root = _exact_abs(target_package_root, field="target_package_root")
    target_cli_link = _exact_abs(target_cli_link, field="target_cli_link")
    check = postcheck_package_identity(staged_package_root, staged_package_root / "openclaw.mjs")
    if check["reasons"] and any(r.startswith("missing:") or r.startswith("package_") for r in check["reasons"]):
        raise ValueError("staged_package_identity_invalid:" + ",".join(check["reasons"]))
    parent = target_package_root.parent
    temp_new = parent / f".openclaw-new-{os.getpid()}-{int(time.time())}"
    backup = parent / f".openclaw-preapply-{os.getpid()}-{int(time.time())}"
    shutil.copytree(staged_package_root, temp_new, symlinks=True, copy_function=shutil.copy2)
    renamed_existing = False
    if target_package_root.exists() or target_package_root.is_symlink():
        os.replace(target_package_root, backup)
        renamed_existing = True
        existing_node_modules = backup / "node_modules"
        if existing_node_modules.is_dir() and not (temp_new / "node_modules").exists():
            shutil.copytree(existing_node_modules, temp_new / "node_modules", symlinks=True, copy_function=shutil.copy2)
    os.replace(temp_new, target_package_root)
    if target_cli_link.exists() or target_cli_link.is_symlink():
        target_cli_link.unlink()
    target_cli_link.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(cli_link_target, target_cli_link)
    return receipt(
        PACKAGE_PLUGIN_APPLY_SCHEMA,
        target_package_root=str(target_package_root),
        target_cli_link=str(target_cli_link),
        staged_package_root=str(staged_package_root),
        backup_path=str(backup) if renamed_existing else "",
        cli_link_target=cli_link_target,
        gateway_restart_actions=0,
        provider_or_live_smoke_calls=0,
        systemctl_actions=0,
        config_or_cron_mutations=0,
    )


def restore_from_full_restore_point(restore_root: str | Path, target_package_root: str | Path, target_cli_link: str | Path) -> dict[str, Any]:
    restore_root = _exact_abs(restore_root, field="restore_root")
    target_package_root = _exact_abs(target_package_root, field="target_package_root")
    target_cli_link = _exact_abs(target_cli_link, field="target_cli_link")
    package_snapshot = restore_root / "snapshot" / "package-root"
    cli_snapshot = restore_root / "snapshot" / "cli-link"
    copies = [
        _copy_preserving_symlink(package_snapshot, target_package_root),
        _copy_preserving_symlink(cli_snapshot, target_cli_link),
    ]
    return receipt("critical_apply.openclaw_npm.restore_operation.v1", restore_root=str(restore_root), copies=copies)


@dataclass
class PackageAuthority:
    package_path: str
    expected_sha256: str
    expected_version: str | None = None
    expected_source_commit: str | None = None
    authority_manifest_path: str | None = None
    authority_manifest_sha256: str | None = None

    def verify(self) -> ValidationResult:
        p = Path(self.package_path)
        reasons: list[str] = []
        details: dict[str, Any] = {"package_path": str(p)}
        if not p.exists():
            return ValidationResult(False, "PACKAGE_AUTHORITY_MISSING", [str(p)])
        if not p.is_file() or p.is_symlink():
            return ValidationResult(False, "PACKAGE_AUTHORITY_NOT_REGULAR_FILE", [str(p)])
        actual_sha = sha256_file(p)
        details["sha256"] = actual_sha
        if actual_sha != self.expected_sha256:
            reasons.append(f"package sha mismatch: {actual_sha} != {self.expected_sha256}")
        if actual_sha.startswith("098684"):
            reasons.append("superseded package SHA prefix 098684 is forbidden")
        try:
            tar_details = inspect_package_tar(p)
            details["tar"] = tar_details
            if tar_details.get("unsafe_members"):
                reasons.append(f"unsafe tar members: {tar_details['unsafe_members'][:5]}")
            pkg = tar_details.get("package_json") or {}
            if pkg.get("name") != "openclaw":
                reasons.append(f"package name is not openclaw: {pkg.get('name')!r}")
            if self.expected_version and pkg.get("version") != self.expected_version:
                reasons.append(f"version mismatch: {pkg.get('version')!r} != {self.expected_version!r}")
            commit = tar_details.get("source_commit")
            if self.expected_source_commit and commit != self.expected_source_commit:
                reasons.append(f"source commit mismatch: {commit!r} != {self.expected_source_commit!r}")
        except Exception as exc:  # noqa: BLE001
            reasons.append(f"tar inspection failed: {type(exc).__name__}: {exc}")
        if self.authority_manifest_path:
            mp = Path(self.authority_manifest_path)
            if not mp.is_file():
                reasons.append(f"authority manifest missing: {mp}")
            elif self.authority_manifest_sha256 and sha256_file(mp) != self.authority_manifest_sha256:
                reasons.append("authority manifest SHA mismatch")
        if reasons:
            return ValidationResult(False, "PACKAGE_AUTHORITY_INVALID", reasons, details)
        return ValidationResult(True, "PACKAGE_AUTHORITY_VALID", details=details)


@dataclass
class RestorePoint:
    path: str
    created_at_epoch: float
    manifest_sha256: str | None = None
    max_age_seconds: int = 3600

    def verify(self) -> ValidationResult:
        root = Path(self.path)
        reasons: list[str] = []
        details: dict[str, Any] = {"path": str(root)}
        if not root.is_dir():
            return ValidationResult(False, "RESTORE_POINT_DIR_MISSING", [str(root)])
        freshness = validate_restore_point_fresh(self.created_at_epoch, self.max_age_seconds)
        details["freshness"] = freshness.details
        if not freshness.ok:
            reasons.extend(freshness.reasons)
        manifest = root / "restore-manifest.json"
        if not manifest.is_file():
            reasons.append("restore-manifest.json missing")
        elif self.manifest_sha256 and sha256_file(manifest) != self.manifest_sha256:
            reasons.append("restore manifest SHA mismatch")
        boundary = root / "restore-boundary.json"
        if not boundary.is_file():
            reasons.append("restore-boundary.json missing")
        if reasons:
            return ValidationResult(False, "RESTORE_POINT_INVALID", reasons, details)
        return ValidationResult(True, "RESTORE_POINT_VALID", details=details)


def commit_from(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("sourceCommit", "source_commit", "gitCommit", "git_commit", "commit", "revision"):
            v = value.get(key)
            if isinstance(v, str) and len(v) >= 7:
                return v
        for v in value.values():
            found = commit_from(v)
            if found:
                return found
    if isinstance(value, list):
        for v in value:
            found = commit_from(v)
            if found:
                return found
    return ""


def inspect_package_tar(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    unsafe: list[str] = []
    package_json: dict[str, Any] | None = None
    build_info: dict[str, Any] | None = None
    members_checked = 0
    critical_found = {rel: False for rel in CRITICAL_RELATIVE_FILES}
    with tarfile.open(path, "r:gz") as tf:
        for m in tf.getmembers():
            members_checked += 1
            name = m.name
            normalized = name[2:] if name.startswith("./") else name
            if normalized.startswith("package/"):
                rel = normalized[len("package/") :]
            else:
                rel = normalized
            if name.startswith("/") or ".." in Path(name).parts:
                unsafe.append(name)
            if m.issym() or m.islnk():
                target = m.linkname or ""
                if target.startswith("/") or ".." in Path(target).parts:
                    unsafe.append(f"{name}->{target}")
            if rel in critical_found:
                critical_found[rel] = True
            if rel == "package.json" and m.isfile():
                with tf.extractfile(m) as f:  # type: ignore[arg-type]
                    package_json = json.loads(f.read().decode("utf-8"))
            if rel == "dist/build-info.json" and m.isfile():
                with tf.extractfile(m) as f:  # type: ignore[arg-type]
                    build_info = json.loads(f.read().decode("utf-8"))
    return {
        "members_checked": members_checked,
        "unsafe_members": unsafe,
        "package_json": package_json,
        "build_info": build_info,
        "source_commit": commit_from(build_info) or commit_from(package_json),
        "critical_files_found": critical_found,
    }


def safe_load_json(path: Path) -> Any:
    try:
        return read_json(path)
    except Exception:
        return None


def inspect_speech_surface(runtime_path: str | Path) -> dict[str, Any]:
    source = Path(runtime_path)
    result: dict[str, Any] = {
        "path": str(source),
        "exists": source.exists(),
        "regular_file": source.is_file(),
        "readable": os.access(source, os.R_OK),
        "sha256": "",
        "relative_import_count": 0,
        "missing_import_count": 0,
        "nonliteral_dynamic_import_count": 0,
        "classification": "",
        "imports": [],
    }
    if not source.exists():
        result["classification"] = "SPEECH_PUBLIC_SURFACE_FILE_MISSING"
        return result
    if not source.is_file() or not os.access(source, os.R_OK):
        result["classification"] = "SPEECH_PUBLIC_SURFACE_UNREADABLE"
        return result
    text = source.read_text(encoding="utf-8", errors="replace")
    result["sha256"] = sha256_file(source)
    patterns = [
        r'(?:import|export)\s+(?:[\s\S]*?\s+from\s*)?["\'](\.[^"\']+)["\']',
        r'import\s*\(\s*["\'](\.[^"\']+)["\']\s*\)',
    ]
    specs: list[str] = []
    for pattern in patterns:
        specs.extend(re.findall(pattern, text))
    specs = list(dict.fromkeys(specs))
    all_dynamic = len(re.findall(r"import\s*\(", text))
    literal_dynamic = len(re.findall(patterns[1], text))
    result["nonliteral_dynamic_import_count"] = max(0, all_dynamic - literal_dynamic)
    base = source.parent
    imports: list[dict[str, Any]] = []
    for spec in specs:
        raw = (base / spec).resolve()
        candidates = [raw]
        if not raw.suffix:
            candidates += [Path(str(raw) + ext) for ext in (".js", ".mjs", ".cjs", ".json", ".node")]
            candidates += [raw / ("index" + ext) for ext in (".js", ".mjs", ".cjs", ".json")]
        resolved = next((c for c in candidates if c.is_file()), None)
        imports.append(
            {
                "specifier": spec,
                "candidate_paths": [str(c) for c in candidates],
                "resolved_path": str(resolved) if resolved else "",
                "exists": resolved is not None,
                "sha256": sha256_file(resolved) if resolved else "",
            }
        )
    result["imports"] = imports
    result["relative_import_count"] = len(imports)
    result["missing_import_count"] = sum(not x["exists"] for x in imports)
    if result["missing_import_count"]:
        result["classification"] = "SPEECH_PUBLIC_SURFACE_IMPORT_MISSING"
    elif result["nonliteral_dynamic_import_count"]:
        result["classification"] = "SPEECH_PUBLIC_SURFACE_PARSE_UNRESOLVED"
    else:
        result["classification"] = "SPEECH_PUBLIC_SURFACE_COMPLETE"
    return result


def count_entries(root: Path, max_count: int = 100_000) -> int:
    count = 0
    for _ in root.rglob("*"):
        count += 1
        if count >= max_count:
            return count
    return count


def inspect_package_root(
    package_root: str | Path = DEFAULT_PACKAGE_ROOT,
    expected_version: str | None = None,
    expected_source_commit: str | None = None,
) -> dict[str, Any]:
    root = Path(package_root)
    critical = {rel: (root / rel).exists() for rel in CRITICAL_RELATIVE_FILES}
    out: dict[str, Any] = {
        "package_root": str(root),
        "root_exists": root.exists(),
        "root_type": "directory" if root.is_dir() else ("missing" if not root.exists() else "other"),
        "entry_count": count_entries(root) if root.is_dir() else 0,
        "critical_files": critical,
        "package_json_parse_ok": False,
        "package_name": "",
        "package_version": "",
        "version_matches": None,
        "source_commit": "",
        "source_commit_matches": None,
        "package_surface_complete": False,
        "speech_surface_complete": False,
        "classification": NpmBaseClassification.NPM_BASE_UNKNOWN.value,
    }
    if not root.exists():
        out["classification"] = NpmBaseClassification.NPM_BASE_MISSING.value
        return out
    if not root.is_dir():
        out["classification"] = NpmBaseClassification.NPM_BASE_UNKNOWN.value
        return out
    if out["entry_count"] == 0:
        out["classification"] = NpmBaseClassification.NPM_BASE_EMPTY.value
        return out
    pkg = safe_load_json(root / "package.json")
    build = safe_load_json(root / "dist/build-info.json")
    if isinstance(pkg, dict):
        out["package_json_parse_ok"] = True
        out["package_name"] = pkg.get("name", "")
        out["package_version"] = pkg.get("version", "")
        if expected_version is not None:
            out["version_matches"] = out["package_version"] == expected_version
    commit = commit_from(build) or commit_from(pkg)
    out["source_commit"] = commit
    if expected_source_commit is not None:
        out["source_commit_matches"] = commit == expected_source_commit
    speech = inspect_speech_surface(root / "dist/extensions/speech-core/runtime-api.js")
    out["speech_surface"] = speech
    out["speech_surface_complete"] = speech.get("classification") == "SPEECH_PUBLIC_SURFACE_COMPLETE"
    entry_candidates = ["dist/entry.js", "dist/entry.mjs", "dist/index.js"]
    gateway_candidates = ["dist/cli/gateway-lifecycle.runtime.js", "dist/cli/gateway-lifecycle.runtime.mjs", "dist/cli-startup-metadata.json"]
    registry_candidates = ["dist/plugins/public-surface-runtime.js", "dist/plugins/public-surface-runtime.mjs", "dist/extensions/speech-core/package.json"]
    ui_candidates = ["dist/control-ui/index.html", "dist/control-ui/assets", "dist/web/index.html", "dist/ui/index.html"]
    surfaces = {
        "runtime_entry": any((root / p).exists() for p in entry_candidates),
        "gateway_surface": any((root / p).exists() for p in gateway_candidates),
        "bundled_registry": any((root / p).exists() for p in registry_candidates),
        "control_ui": any((root / p).exists() for p in ui_candidates),
    }
    out["surfaces"] = surfaces
    package_surface_complete = (
        root.is_dir()
        and isinstance(pkg, dict)
        and pkg.get("name") == "openclaw"
        and all(critical.values())
        and all(surfaces.values())
        and out["speech_surface_complete"]
        and (expected_version is None or out["version_matches"] is True)
        and (expected_source_commit is None or out["source_commit_matches"] is True)
    )
    out["package_surface_complete"] = package_surface_complete
    if package_surface_complete:
        out["classification"] = NpmBaseClassification.NPM_BASE_COHERENT.value
    elif not all(critical.values()) or not isinstance(pkg, dict):
        out["classification"] = NpmBaseClassification.NPM_BASE_INCOMPLETE.value
    else:
        out["classification"] = NpmBaseClassification.NPM_BASE_UNKNOWN.value
    return out


def proc_text(pid: int, name: str, binary: bool = False) -> bytes | str:
    try:
        mode = "rb" if binary else "r"
        with open(f"/proc/{pid}/{name}", mode) as f:
            return f.read()
    except Exception:
        return b"" if binary else ""


def proc_link(pid: int, name: str) -> str:
    try:
        return os.readlink(f"/proc/{pid}/{name}")
    except Exception:
        return ""


def list_candidate_pids() -> list[int]:
    pids = []
    proc = Path("/proc")
    for child in proc.iterdir() if proc.exists() else []:
        if child.name.isdigit():
            pids.append(int(child.name))
    return pids


def process_references_path(pid: int, target: Path) -> dict[str, Any]:
    target_s = str(target)
    refs = {"pid": pid, "cwd": [], "exe": [], "cmdline": [], "maps": [], "fd": []}
    for key in ("cwd", "exe"):
        val = proc_link(pid, key)
        if target_s in val:
            refs[key].append(val)
    cmd_raw = proc_text(pid, "cmdline", True)
    if isinstance(cmd_raw, bytes):
        cmd = " ".join(x.decode("utf-8", "replace") for x in cmd_raw.split(b"\0") if x)
        if target_s in cmd:
            refs["cmdline"].append(cmd)
    maps = proc_text(pid, "maps")
    if isinstance(maps, str):
        refs["maps"] = [line for line in maps.splitlines() if target_s in line][:50]
    fd_dir = Path(f"/proc/{pid}/fd")
    if fd_dir.is_dir():
        try:
            fds = list(fd_dir.iterdir())[:2048]
        except PermissionError:
            refs["fd_permission_denied"] = True
            fds = []
        for fd in fds:
            try:
                val = os.readlink(fd)
            except (FileNotFoundError, PermissionError, OSError):
                continue
            if target_s in val:
                refs["fd"].append(f"{fd.name}->{val}")
    refs["referenced"] = any(refs[k] for k in ("cwd", "exe", "cmdline", "maps", "fd"))
    return refs


def inspect_staging_dirs(node_modules: str | Path = DEFAULT_NODE_MODULES, pids: list[int] | None = None) -> dict[str, Any]:
    root = Path(node_modules)
    pids = list_candidate_pids() if pids is None else pids
    rows: list[dict[str, Any]] = []
    if not root.is_dir():
        return {"node_modules": str(root), "exists": False, "staging_dirs": [], "classification": StagingDirClassification.NONE.value}
    for entry in sorted(root.iterdir(), key=lambda p: p.name):
        if not entry.name.startswith(".openclaw-"):
            continue
        entry_type = "symlink" if entry.is_symlink() else ("directory" if entry.is_dir() else "other")
        row: dict[str, Any] = {
            "path": str(entry),
            "name": entry.name,
            "name_pattern_valid": bool(re.fullmatch(r"\.openclaw-[A-Za-z0-9_-]+", entry.name)),
            "direct_child_of_node_modules": entry.parent.resolve() == root.resolve(),
            "type": entry_type,
            "live_references": [],
            "classification": StagingDirClassification.INACTIVE_CAN_QUARANTINE.value,
        }
        if not row["name_pattern_valid"] or not row["direct_child_of_node_modules"] or row["type"] != "directory":
            row["classification"] = StagingDirClassification.SUSPICIOUS_BLOCK.value
        else:
            refs = [process_references_path(pid, entry) for pid in pids]
            refs = [r for r in refs if r.get("referenced")]
            row["live_references"] = refs
            if refs:
                row["classification"] = StagingDirClassification.LIVE_REFERENCED_LEAVE_UNTOUCHED.value
        rows.append(row)
    overall = StagingDirClassification.NONE.value
    if any(r["classification"] == StagingDirClassification.SUSPICIOUS_BLOCK.value for r in rows):
        overall = StagingDirClassification.SUSPICIOUS_BLOCK.value
    elif any(r["classification"] == StagingDirClassification.LIVE_REFERENCED_LEAVE_UNTOUCHED.value for r in rows):
        overall = StagingDirClassification.LIVE_REFERENCED_LEAVE_UNTOUCHED.value
    elif rows:
        overall = StagingDirClassification.INACTIVE_CAN_QUARANTINE.value
    return {"node_modules": str(root), "exists": True, "staging_dirs": rows, "classification": overall}


def inspect_gateway_process(pid: int | None = None, port: int = 18789) -> dict[str, Any]:
    if pid is None:
        for candidate in list_candidate_pids():
            cmd_raw = proc_text(candidate, "cmdline", True)
            if isinstance(cmd_raw, bytes) and b"openclaw" in cmd_raw and b"gateway" in cmd_raw:
                pid = candidate
                break
    out: dict[str, Any] = {"pid": pid, "port": port, "found": False}
    if pid is None or not Path(f"/proc/{pid}").is_dir():
        return out
    out["found"] = True
    out["cwd"] = proc_link(pid, "cwd")
    out["exe"] = proc_link(pid, "exe")
    cmd_raw = proc_text(pid, "cmdline", True)
    out["cmdline"] = " ".join(x.decode("utf-8", "replace") for x in cmd_raw.split(b"\0") if x) if isinstance(cmd_raw, bytes) else ""
    out["cgroup"] = proc_text(pid, "cgroup")
    stat_text = proc_text(pid, "stat")
    if isinstance(stat_text, str) and ")" in stat_text:
        rest = stat_text[stat_text.rfind(")") + 2 :].split()
        out["start_ticks"] = int(rest[19]) if len(rest) > 19 and rest[19].isdigit() else None
    return out


def decide_recovery(package_health: dict[str, Any], staging: dict[str, Any], restore: ValidationResult) -> dict[str, Any]:
    classification = package_health.get("classification")
    staging_class = staging.get("classification")
    if classification == NpmBaseClassification.NPM_BASE_COHERENT.value:
        terminal = "FAIL_SAFE_NO_MUTATION"
        action = "NO_RESTORE_PACKAGE_COHERENT"
    elif classification in {
        NpmBaseClassification.NPM_BASE_MISSING.value,
        NpmBaseClassification.NPM_BASE_EMPTY.value,
        NpmBaseClassification.NPM_BASE_INCOMPLETE.value,
    }:
        if restore.ok:
            terminal = "ROLLBACK_REQUIRED"
            action = "RESTORE_FROM_VERIFIED_RESTORE_POINT"
        else:
            terminal = "ROLLBACK_FAIL_OPERATOR_REQUIRED"
            action = "NO_RESTORE_INVALID_RESTORE_POINT"
    else:
        terminal = "ROLLBACK_FAIL_OPERATOR_REQUIRED"
        action = "NO_RESTORE_UNKNOWN_PACKAGE_STATE"
    if staging_class == StagingDirClassification.SUSPICIOUS_BLOCK.value:
        terminal = "ROLLBACK_FAIL_OPERATOR_REQUIRED"
        action = "NO_RESTORE_SUSPICIOUS_STAGING"
    return receipt(
        "critical_apply.openclaw_npm.recovery_decision.v1",
        terminal=terminal,
        action=action,
        package_classification=classification,
        staging_classification=staging_class,
        restore_point_valid=restore.ok,
        restore_point_code=restore.code,
    )


def create_restore_point_skeleton(root: str | Path, package_root: str | Path = DEFAULT_PACKAGE_ROOT, cli_link: str | Path = DEFAULT_CLI_LINK) -> dict[str, Any]:
    """Create metadata-only restore point skeleton.

    M2 will add archive/copy behavior. This function is intentionally metadata
    only so M0/M1 can validate contract shape without package mutation.
    """
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    manifest = receipt(
        "critical_apply.restore_manifest.v1",
        package_root=str(package_root),
        cli_link=str(cli_link),
        created_at_epoch=time.time(),
        archive_created=False,
        implementation_level="M0_METADATA_ONLY",
    )
    boundary = receipt(
        "critical_apply.restore_boundary.v1",
        allowed_mutations=["openclaw_package_root", "npm_cli_link", "npm_metadata"],
        forbidden_mutations=["gateway_restart", "cron_mutation", "protected_memory", "provider_call", "functional_smoke"],
    )
    write_json(root / "restore-manifest.json", manifest)
    write_json(root / "restore-boundary.json", boundary)
    return manifest


__all__ = [
    "PackageAuthority",
    "RestorePoint",
    "apply_staged_package",
    "commit_from",
    "create_full_restore_point",
    "create_restore_point_skeleton",
    "decide_recovery",
    "extract_package_artifact",
    "inspect_gateway_process",
    "inspect_package_root",
    "inspect_package_tar",
    "inspect_speech_surface",
    "inspect_staging_dirs",
    "postcheck_package_identity",
    "restore_from_full_restore_point",
]
