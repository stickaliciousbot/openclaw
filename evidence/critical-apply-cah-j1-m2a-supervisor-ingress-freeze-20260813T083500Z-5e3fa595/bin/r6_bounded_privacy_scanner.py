#!/usr/bin/env python3
"""R6-R6 Phase A R2 — Bounded privacy scanner.

Scans evidence-local Phase A artifacts for credential-shaped patterns.
Dual scope: persistent semantic evidence (top-down, pruned) and exact frozen
tool/fixture source files (hash-bound). Detector regex literals in the scanner
and selftest source are classified as pattern literals, not runtime secrets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

os.umask(0o077)

DETECTOR_VERSION = "r6-r6-phase-a.v2"
PATTERN_SPECS = [
    ("PRIVATE_KEY_PEM_LINE", r"^-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.M),
    ("OPENAI_STYLE_KEY", r"\bsk-[A-Za-z0-9_-]{20,}\b", 0),
    ("GITHUB_STYLE_TOKEN", r"\b(?:ghp|gho|ghu|ghs|github_pat)_[A-Za-z0-9_]{20,}\b", 0),
    ("BEARER_VALUE", r'\bauthorization\s*[:=]\s*["\']?bearer\s+[A-Za-z0-9._~+/=-]{16,}', re.I),
    ("GENERIC_SECRET_ASSIGNMENT", r'\b(api[_-]?key|secret|token|password)\s*[:=]\s*["\'][A-Za-z0-9_./+=-]{24,}["\']', re.I),
]
PATTERNS = [(name, re.compile(pattern, flags)) for name, pattern, flags in PATTERN_SPECS]
DETECTOR_CONFIG_CANONICAL = json.dumps(
    {"version": DETECTOR_VERSION, "patterns": [(n, p, int(f)) for n, p, f in PATTERN_SPECS]},
    sort_keys=True,
    separators=(",", ":"),
)
DETECTOR_CONFIG_SHA256 = hashlib.sha256(DETECTOR_CONFIG_CANONICAL.encode()).hexdigest()

PRUNED_DIRS = {".git", "node_modules", ".pnpm", "runtime", "harness", "post-terminal", "checker", "observer-semantic", "attempts", "synthetic", "__pycache__"}
ROOT_EXCLUDED_NAMES = {"manifest.json", "manifest.sha256", "terminal-seal.json"}


def sha_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fp(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--scanner-sha256", required=True)
    ap.add_argument("--detector-config-sha256", required=True)
    ap.add_argument("--max-bytes", type=int, default=2_000_000)
    args = ap.parse_args()

    root = Path(args.root).resolve()
    out = Path(args.out).resolve()
    scanner = Path(__file__).resolve()
    scanner_actual = sha_file(scanner)
    scanner_ok = scanner_actual == args.scanner_sha256
    detector_ok = DETECTOR_CONFIG_SHA256 == args.detector_config_sha256

    findings: list[dict] = []
    issues: list[dict] = []
    excluded: list[dict] = []
    pruned: list[str] = []
    scanned_persistent = 0
    scanned_exact = 0
    binary = 0

    scanner_literal_paths = {scanner.resolve(), (root / "selftest" / "run_selftests.py").resolve()}

    def scan_text(p: Path, logical: str, scope: str, allow_pattern_literal: bool = False) -> None:
        nonlocal scanned_persistent, scanned_exact, binary
        if p.is_symlink():
            issues.append({"path": logical, "scope": scope, "reason": "unexpected_symlink"})
            return
        try:
            size = p.stat().st_size
        except OSError as e:
            issues.append({"path": logical, "scope": scope, "reason": type(e).__name__})
            return
        if size > args.max_bytes:
            issues.append({"path": logical, "scope": scope, "reason": "oversized", "bytes": size})
            return
        try:
            data = p.read_bytes()
        except OSError as e:
            issues.append({"path": logical, "scope": scope, "reason": type(e).__name__})
            return
        if b"\0" in data:
            if scope == "exact_tool_source":
                issues.append({"path": logical, "scope": scope, "reason": "binary_exact_source"})
            else:
                binary += 1
                excluded.append({"path": logical, "scope": scope, "reason": "binary_nul", "bytes": size})
            return
        text = data.decode("utf-8", "replace")
        if scope == "exact_tool_source":
            scanned_exact += 1
        else:
            scanned_persistent += 1
        for detector, pattern in PATTERNS:
            for match in pattern.finditer(text):
                literal = allow_pattern_literal and p.resolve() in scanner_literal_paths
                findings.append({
                    "path": logical,
                    "scope": scope,
                    "detector": detector,
                    "classification": "SCANNER_PATTERN_LITERAL_WITHOUT_RUNTIME_VALUE" if literal else "BLOCKING_SECRET_PATTERN",
                    "fingerprint": fp(match.group(0)),
                })

    root_excluded = {root / name for name in ROOT_EXCLUDED_NAMES}
    root_excluded.add(out)
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        base = Path(dirpath)
        before = set(dirnames)
        dirnames[:] = sorted(d for d in dirnames if d not in PRUNED_DIRS)
        for d in sorted(before - set(dirnames)):
            pruned.append(str((base / d).relative_to(root)))
        for name in sorted(filenames):
            p = base / name
            logical = str(p.relative_to(root))
            if p.resolve() in root_excluded:
                excluded.append({"path": logical, "scope": "persistent_evidence", "reason": "mutable_or_recursive_output_exclusion"})
                continue
            scan_text(p, logical, "persistent_evidence", allow_pattern_literal=True)

    try:
        frozen = load(root / "frozen-tool-identities.json")
        expected_paths = sorted(frozen.get("files", {}).keys())
    except Exception as e:
        issues.append({"path": "frozen-tool-identities.json", "scope": "exact_tool_source", "reason": type(e).__name__})
        expected_paths = []
        frozen = {"files": {}}

    for rel in expected_paths:
        relp = Path(rel)
        if relp.is_absolute() or ".." in relp.parts:
            issues.append({"path": rel, "scope": "exact_tool_source", "reason": "unsafe_relative_path"})
            continue
        p = root / relp
        if not p.is_file() or p.is_symlink():
            issues.append({"path": rel, "scope": "exact_tool_source", "reason": "missing_or_nonregular_or_symlink"})
            continue
        actual = sha_file(p)
        expected = frozen["files"][rel]["sha256"]
        if actual != expected:
            issues.append({"path": rel, "scope": "exact_tool_source", "reason": "source_hash_mismatch", "expected_sha256": expected, "actual_sha256": actual})
            continue
        scan_text(p, rel, "exact_tool_source", allow_pattern_literal=True)

    blocking = [x for x in findings if x["classification"] == "BLOCKING_SECRET_PATTERN"]
    ok = scanner_ok and detector_ok and scanned_exact == len(expected_paths) and not blocking and not issues
    receipt = {
        "schema": "approval_grant_broker.r6_r6.phase_a.bounded_privacy_scan.v2",
        "status": "R6_R6_PHASE_A_BOUNDED_PRIVACY_SCAN_PASS" if ok else "HOLD_R6_R6_PRIVACY_FAILED",
        "scanner_name": "R6_R6_PHASE_A_BOUNDED_PRIVACY_SCANNER",
        "scanner_sha256_expected": args.scanner_sha256,
        "scanner_sha256_actual": scanner_actual,
        "scanner_identity_ok": scanner_ok,
        "detector_version": DETECTOR_VERSION,
        "detector_config_sha256_expected": args.detector_config_sha256,
        "detector_config_sha256_actual": DETECTOR_CONFIG_SHA256,
        "detector_config_identity_ok": detector_ok,
        "root": str(root),
        "persistent_scope": "top-down pruned semantic evidence",
        "exact_tool_source_scope": f"exact hash-bound {len(expected_paths)} frozen tool source files",
        "pruned_dirs": sorted(set(pruned)),
        "scanned_persistent_text_files": scanned_persistent,
        "scanned_exact_tool_source_files": scanned_exact,
        "binary_files": binary,
        "excluded": excluded,
        "issues": issues,
        "findings": findings,
        "blocking_count": len(blocking),
        "scanner_literals_classified_by_exact_source_hash": True,
        "no_test_or_path_allowlist_for_exact_source": True,
        "gca_scan_secrets_claimed": False,
        "git_history_scan_claimed": False,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out.chmod(0o600)
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
