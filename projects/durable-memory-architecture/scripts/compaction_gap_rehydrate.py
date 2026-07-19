#!/usr/bin/env python3
"""Build a bounded, non-authoritative hydration packet for durable-memory work.

The tool is intentionally local, read-only with respect to source material, and
network/subprocess free. It writes only a generated packet and manifest under an
operator-selected state directory. It does not inject context, mutate Ledger,
write memory, alter routes, or start an implementation milestone.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "stickbot.durable_memory.compaction_gap_hydration.v1"
MAX_SOURCE_BYTES = 512 * 1024

REQUIRED_DESIGN_SOURCES = (
    ("systemic_lld", "DURABLE_MEMORY_LEDGER_CONTEXT_CONTRACT_SURFACE_BROKER_LLD_AND_IMPLEMENTATION_PLAN.md"),
    ("proposal", "COMPACTION_GAP_RECOVERY_PROPOSAL.md"),
    ("integration_order", "LEDGER_BROKER_INTEGRATION_AND_BUILD_ORDER.md"),
)

REQUIRED_WORKSPACE_SOURCES = (
    (
        "systemic_lesson",
        Path("memory/lessons-learned-durable-memory-ledger-contract-surface-broker-systemic-build-order-2026-07-17.md"),
    ),
)

LEDGER_REHYDRATOR_REL = Path("docs/PROJECT_REHYDRATOR.md")
LEDGER_LATEST_REL = Path("artifacts/rehydration/stickbot-memory-ledger/latest.json")
M24_STATUS_GLOB = Path(
    "state/stickbot-memory-ledger/"
    "m24-sanitized-presentation-default-switch-observation/"
    "m24-observation-*/status.json"
)

FORBIDDEN_PATTERNS = (
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("bearer_token", re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{16,}")),
    (
        "credential_assignment",
        re.compile(
            r"(?i)[\"']?(?:api[_-]?key|bot[_-]?token|access[_-]?token|"
            r"refresh[_-]?token|password)[\"']?\s*[:=]\s*[\"']?"
            r"(?!redacted\b|none\b|disabled\b|unset\b|example\b)"
            r"[A-Za-z0-9._~+/=-]{16,}"
        ),
    ),
)

LEDGER_FIELDS = (
    "schema",
    "status",
    "project",
    "branch",
    "preferredWorktree",
    "acceptedBaselineHead",
    "currentMilestone",
    "currentTerminal",
    "currentCloseoutStatus",
    "currentGateResult",
    "nextBoundary",
    "gitBoundary",
    "invariants",
)

M24_FIELDS = (
    "schema",
    "status",
    "checkpoint",
    "boundary_observed",
    "closeout_status",
    "terminal_status",
    "failed_gates",
    "updated_utc",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_bounded(path: Path, max_bytes: int = MAX_SOURCE_BYTES) -> tuple[bytes, str]:
    raw = path.read_bytes()
    if len(raw) > max_bytes:
        raise ValueError(f"source exceeds {max_bytes} bytes: {path}")
    return raw, raw.decode("utf-8")


def scan_forbidden(text: str) -> list[str]:
    return [name for name, pattern in FORBIDDEN_PATTERNS if pattern.search(text)]


def is_within(path: Path, roots: Iterable[Path]) -> bool:
    resolved = path.resolve()
    for root in roots:
        try:
            resolved.relative_to(root.resolve())
            return True
        except ValueError:
            continue
    return False


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def default_ledger_candidates(workspace: Path) -> list[Path]:
    candidates: list[Path] = []
    env_root = os.environ.get("STICKBOT_LEDGER_ROOT")
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend(
        [
            Path("/tmp/context-bridge-ledger-v0-1-completion-20260717/projects/stickbot-memory-ledger-v0"),
            workspace / "projects/stickbot-memory-ledger-v0",
        ]
    )
    deduped: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate.resolve())
        if key not in seen:
            seen.add(key)
            deduped.append(candidate)
    return deduped


def discover_ledger_root(workspace: Path, explicit: Path | None) -> tuple[Path | None, list[str]]:
    candidates = [explicit] if explicit else default_ledger_candidates(workspace)
    checked: list[str] = []
    for candidate in candidates:
        if candidate is None:
            continue
        resolved = candidate.expanduser().resolve()
        checked.append(str(resolved))
        if (resolved / LEDGER_REHYDRATOR_REL).is_file():
            return resolved, checked
    return None, checked


def load_json(path: Path) -> dict[str, Any]:
    raw, text = read_bounded(path)
    del raw
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError(f"expected JSON object: {path}")
    return parsed


def select_fields(data: dict[str, Any], fields: Iterable[str]) -> dict[str, Any]:
    return {key: data[key] for key in fields if key in data}


def discover_m24_status(ledger_root: Path) -> tuple[Path | None, dict[str, Any] | None]:
    # Tracked project content lives under <worktree>/projects/<project>, while
    # runtime observation state normally lives at <worktree>/state. Fixtures
    # and standalone copies may instead place state directly under project root.
    search_roots = [ledger_root]
    if ledger_root.parent.name == "projects":
        search_roots.append(ledger_root.parent.parent)
    matches: list[Path] = []
    seen: set[str] = set()
    for root in search_roots:
        for path in root.glob(str(M24_STATUS_GLOB)):
            key = str(path.resolve())
            if path.is_file() and key not in seen:
                seen.add(key)
                matches.append(path)
    if not matches:
        return None, None
    latest = max(matches, key=lambda item: item.stat().st_mtime_ns)
    return latest, select_fields(load_json(latest), M24_FIELDS)


def source_record(role: str, path: Path, content: bytes, authority: str) -> dict[str, Any]:
    return {
        "role": role,
        "path": str(path),
        "bytes": len(content),
        "sha256": sha256_bytes(content),
        "authority": authority,
    }


def build_packet(
    *,
    workspace: Path,
    project_root: Path,
    ledger_root: Path | None = None,
) -> tuple[dict[str, Any], str]:
    workspace = workspace.resolve()
    project_root = project_root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    scans: list[dict[str, Any]] = []
    inventory: list[dict[str, Any]] = []
    sections: dict[str, str] = {}
    before_hashes: dict[str, str] = {}

    for role, relative_name in REQUIRED_DESIGN_SOURCES:
        path = project_root / relative_name
        if not path.is_file():
            errors.append(f"missing required design source: {path}")
            continue
        content, text = read_bounded(path)
        findings = scan_forbidden(text)
        scans.append({"role": role, "findings": findings})
        if findings:
            errors.append(f"forbidden content in {role}: {','.join(findings)}")
            continue
        inventory.append(source_record(role, path, content, "design_only_non_authoritative"))
        before_hashes[str(path)] = sha256_bytes(content)
        sections[role] = text.rstrip()

    for role, relative_path in REQUIRED_WORKSPACE_SOURCES:
        path = workspace / relative_path
        if not path.is_file():
            errors.append(f"missing required workspace source: {path}")
            continue
        content, text = read_bounded(path)
        findings = scan_forbidden(text)
        scans.append({"role": role, "findings": findings})
        if findings:
            errors.append(f"forbidden content in {role}: {','.join(findings)}")
            continue
        inventory.append(source_record(role, path, content, "lesson_non_authoritative_navigation"))
        before_hashes[str(path)] = sha256_bytes(content)
        sections[role] = text.rstrip()

    resolved_ledger, checked = discover_ledger_root(workspace, ledger_root)
    ledger_snapshot: dict[str, Any] | None = None
    m24_snapshot: dict[str, Any] | None = None

    if resolved_ledger is None:
        warnings.append("Ledger project root not found; pass --ledger-root after Ledger worktree relocation")
    else:
        rehydrator_path = resolved_ledger / LEDGER_REHYDRATOR_REL
        content, text = read_bounded(rehydrator_path)
        findings = scan_forbidden(text)
        scans.append({"role": "ledger_rehydrator", "findings": findings})
        if findings:
            errors.append(f"forbidden content in Ledger rehydrator: {','.join(findings)}")
        else:
            inventory.append(
                source_record(
                    "ledger_rehydrator",
                    rehydrator_path,
                    content,
                    "tracked_navigation_snapshot_verify_live_state",
                )
            )
            before_hashes[str(rehydrator_path)] = sha256_bytes(content)
            sections["ledger_rehydrator"] = text.rstrip()

        latest_path = resolved_ledger / LEDGER_LATEST_REL
        if latest_path.is_file():
            latest_raw, latest_text = read_bounded(latest_path)
            latest_findings = scan_forbidden(latest_text)
            scans.append({"role": "ledger_latest", "findings": latest_findings})
            if latest_findings:
                errors.append(f"forbidden content in Ledger latest.json: {','.join(latest_findings)}")
            else:
                inventory.append(
                    source_record(
                        "ledger_latest",
                        latest_path,
                        latest_raw,
                        "tracked_navigation_snapshot_verify_live_state",
                    )
                )
                before_hashes[str(latest_path)] = sha256_bytes(latest_raw)
                ledger_snapshot = select_fields(json.loads(latest_text), LEDGER_FIELDS)
        else:
            warnings.append(f"Ledger latest.json missing: {latest_path}")

        try:
            m24_path, m24_snapshot = discover_m24_status(resolved_ledger)
            if m24_path is not None:
                m24_raw, m24_text = read_bounded(m24_path)
                m24_findings = scan_forbidden(m24_text)
                scans.append({"role": "m24_live_status", "findings": m24_findings})
                if m24_findings:
                    errors.append(f"forbidden content in M24 status: {','.join(m24_findings)}")
                else:
                    inventory.append(
                        source_record(
                            "m24_live_status",
                            m24_path,
                            m24_raw,
                            "runtime_observation_snapshot_not_terminal_authority",
                        )
                    )
                    before_hashes[str(m24_path)] = sha256_bytes(m24_raw)
            else:
                warnings.append("No M24 runtime status found; rely on the latest tracked Ledger rehydrator")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            warnings.append(f"M24 status unavailable: {exc}")
            m24_snapshot = None

    mutation_checks: list[dict[str, Any]] = []
    for path_text, before in before_hashes.items():
        path = Path(path_text)
        after = sha256_bytes(path.read_bytes()) if path.is_file() else None
        unchanged = before == after
        mutation_checks.append(
            {"path": path_text, "before_sha256": before, "after_sha256": after, "unchanged": unchanged}
        )
        if not unchanged:
            errors.append(f"source changed while hydrating: {path_text}")

    if errors:
        status = "FAIL"
    elif resolved_ledger is None or warnings:
        status = "WARN"
    else:
        status = "PASS"

    manifest: dict[str, Any] = {
        "schema": SCHEMA,
        "generated_utc": utc_now(),
        "status": status,
        "purpose": "restore design-level understanding after compaction without granting authority",
        "authority": "non_authoritative_navigation_only",
        "boundaries": [
            "Finish the currently authorized Memory Ledger work before implementation or surface expansion",
            "Verify mutable Ledger and runtime state from canonical sources before acting",
            "No automatic prompt injection or hot-context insertion",
            "No recall-time memory writes or authority promotion",
            "No Gateway, model, provider, route, Telegram, Context Bridge, or Ledger mutation",
            "No implementation milestone or UMC surface expansion is started by this script",
        ],
        "resume_order": [
            "Read the live M24 and later M25/terminal Ledger state first",
            "Read the Ledger project rehydrator and verify it against canonical artifacts",
            "Read the systemic LLD and seven-milestone implementation plan",
            "Read the integration/build-order design, proposal, and systemic lesson",
            "Do not implement Milestone 2 after M24 alone; require Ledger M25 final-completion/freeze PASS and new milestone authorization",
        ],
        "workspace": str(workspace),
        "project_root": str(project_root),
        "ledger_root": str(resolved_ledger) if resolved_ledger else None,
        "ledger_candidates_checked": checked,
        "ledger_snapshot": ledger_snapshot,
        "m24_runtime_snapshot": m24_snapshot,
        "source_inventory": inventory,
        "forbidden_content_scans": scans,
        "source_mutation_checks": mutation_checks,
        "warnings": warnings,
        "errors": errors,
    }

    ledger_summary = json.dumps(ledger_snapshot, indent=2, sort_keys=True) if ledger_snapshot else "null"
    m24_summary = json.dumps(m24_snapshot, indent=2, sort_keys=True) if m24_snapshot else "null"
    inventory_lines = "\n".join(
        f"- `{item['role']}` — `{item['path']}` — {item['bytes']} bytes — sha256:`{item['sha256']}` — {item['authority']}"
        for item in inventory
    ) or "- No readable sources"

    markdown = f"""# Durable Memory Architecture — Compaction-Gap Hydration Packet

Generated: `{manifest['generated_utc']}`
Status: **{status}**
Authority: **non-authoritative navigation only**

## Mandatory interpretation

This packet restores retrieval coordinates, design decisions, and build ordering. It does not prove mutable production state and does not authorize implementation. Verify the current Ledger terminal and canonical sources before acting.

## Resume order

{chr(10).join(f'{index}. {item}' for index, item in enumerate(manifest['resume_order'], 1))}

## Preserved boundaries

{chr(10).join(f'- {item}' for item in manifest['boundaries'])}

## Current Ledger snapshot

Tracked rehydrator summary (may lag uncommitted observation state):

```json
{ledger_summary}
```

Latest bounded M24 runtime observation snapshot, when available:

```json
{m24_summary}
```

## How the capabilities fit together

- **Ledger:** durable, scoped, hashed write model and continuity spine.
- **Source registry:** authority and canonical readback resolver.
- **Knowledge graph:** rebuildable relationship/provenance read model.
- **Vector/FTS:** disposable candidate discovery accelerators.
- **Runtime Service Broker:** scoped capability grants and service receipts.
- **UMC:** turn-level contract, supervision, postcondition proof, and closeout.
- **Surface Service Broker:** channel privacy/capability/rendering boundary.
- **Context Bridge:** sanitized operational projection, never raw memory authority.

## Systemic LLD and seven-milestone implementation plan

{sections.get('systemic_lld', '[missing systemic LLD]')}

## Integration and recommended build order

{sections.get('integration_order', '[missing integration design]')}

## Draft compaction-gap recovery proposal

{sections.get('proposal', '[missing proposal]')}

## Systemic lesson learned

{sections.get('systemic_lesson', '[missing systemic lesson]')}

## Ledger project rehydrator snapshot

{sections.get('ledger_rehydrator', '[Ledger rehydrator unavailable; provide --ledger-root]')}

## Source inventory

{inventory_lines}

## Warnings

{chr(10).join(f'- {item}' for item in warnings) if warnings else '- None'}

## Errors

{chr(10).join(f'- {item}' for item in errors) if errors else '- None'}
"""
    markdown = "\n".join(line.rstrip() for line in markdown.splitlines()) + "\n"
    return manifest, markdown


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=None)
    parser.add_argument("--project-root", type=Path, default=None)
    parser.add_argument("--ledger-root", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--check-only", action="store_true", help="validate and print status without writing")
    parser.add_argument("--status", action="store_true", help="print machine-readable result")
    parser.add_argument("--strict", action="store_true", help="treat WARN as a non-zero exit")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    script_path = Path(__file__).resolve()
    inferred_project = script_path.parent.parent
    project_root = (args.project_root or inferred_project).expanduser().resolve()
    inferred_workspace = project_root.parents[1]
    workspace = (args.workspace or inferred_workspace).expanduser().resolve()
    ledger_root = args.ledger_root.expanduser().resolve() if args.ledger_root else None
    output_dir = (
        args.output_dir.expanduser().resolve()
        if args.output_dir
        else workspace / "state/durable-memory-architecture/compaction-gap-hydration"
    )

    allowed_output_roots = [workspace / "state", Path(tempfile.gettempdir())]
    if not is_within(output_dir, allowed_output_roots):
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "error": "output directory must be under workspace/state or the system temporary directory",
                    "output_dir": str(output_dir),
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2

    try:
        manifest, markdown = build_packet(
            workspace=workspace,
            project_root=project_root,
            ledger_root=ledger_root,
        )
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2

    latest_json = output_dir / "latest.json"
    latest_md = output_dir / "latest.md"
    if not args.check_only:
        manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
        markdown_bytes = (markdown.rstrip() + "\n").encode("utf-8")
        atomic_write(latest_json, manifest_bytes)
        atomic_write(latest_md, markdown_bytes)
    else:
        manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
        markdown_bytes = (markdown.rstrip() + "\n").encode("utf-8")

    result = {
        "schema": SCHEMA,
        "status": manifest["status"],
        "generated_utc": manifest["generated_utc"],
        "check_only": args.check_only,
        "latest_json": None if args.check_only else str(latest_json),
        "latest_md": None if args.check_only else str(latest_md),
        "source_count": len(manifest["source_inventory"]),
        "warning_count": len(manifest["warnings"]),
        "error_count": len(manifest["errors"]),
        "packet_sha256": sha256_bytes(markdown_bytes),
        "manifest_sha256": sha256_bytes(manifest_bytes),
        "ledger_root": manifest["ledger_root"],
        "m24_runtime_snapshot": manifest["m24_runtime_snapshot"],
    }

    if args.status or args.check_only:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Hydration packet written: {latest_md}")
        print(f"Status: {manifest['status']}")

    if manifest["status"] == "FAIL":
        return 1
    if manifest["status"] == "WARN" and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
