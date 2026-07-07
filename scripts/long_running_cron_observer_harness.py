#!/usr/bin/env python3
"""Deterministic harness for cron-triggered long-running observers.

Purpose
-------
OpenClaw cron agent turns can fail by summarizing a task instead of executing the
required observer checks. For future long observer work, the cron/agent should do
one small deterministic action: execute this harness with an argv-safe command
JSON. The harness owns the durable launch and evidence-writing boundary.

Hard guarantees provided by this harness:
- no shell command construction;
- artifact directory is created before child launch;
- required terminal-evidence files are written immediately;
- child is detached with subprocess.Popen(start_new_session=True);
- PID/PGID/SID detachment proof is recorded;
- a durable registry row is updated atomically;
- stdout emits a stable PASS anchor only after evidence files exist.

The child observer command is still responsible for its own semantic checks and
final closeout. This harness proves only launch/detachment/evidence wiring.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WORKSPACE = Path("/home/stickai/.openclaw/workspace")
DEFAULT_REGISTRY = WORKSPACE / "state/long-running-cron-observers/registry.json"
PASS_ANCHOR = "LONG_RUNNING_CRON_OBSERVER_HARNESS_LAUNCH_PASS"
SCHEMA = "stickbot.long_running_cron_observer_harness.v1"
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{2,120}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json_atomic(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_command_json(value: str) -> list[str]:
    if value.startswith("@"):
        raw = Path(value[1:]).read_text(encoding="utf-8")
    else:
        raw = value
    parsed = json.loads(raw)
    if not isinstance(parsed, list) or not parsed or not all(isinstance(x, str) and x for x in parsed):
        raise SystemExit("command-json must be a non-empty JSON array of non-empty strings")
    if any("\x00" in x for x in parsed):
        raise SystemExit("command-json entries must not contain NUL bytes")
    return parsed


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def safe_getpgid(pid: int) -> int | None:
    try:
        return os.getpgid(pid)
    except Exception:
        return None


def safe_getsid(pid: int) -> int | None:
    try:
        return os.getsid(pid)
    except Exception:
        return None


def load_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema": SCHEMA + ".registry", "runs": []}
    data = read_json(path)
    if not isinstance(data, dict):
        raise SystemExit(f"registry is not an object: {path}")
    data.setdefault("schema", SCHEMA + ".registry")
    data.setdefault("runs", [])
    if not isinstance(data["runs"], list):
        raise SystemExit(f"registry runs is not a list: {path}")
    return data


def update_registry(path: Path, row: dict[str, Any]) -> None:
    data = load_registry(path)
    runs = [r for r in data["runs"] if not (isinstance(r, dict) and r.get("run_id") == row["run_id"])]
    runs.append(row)
    data["runs"] = runs
    data["updated_utc"] = utc_now()
    write_json_atomic(path, data)


def build_manifest(artifact_dir: Path, files: list[Path], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    entries = []
    for path in files:
        entries.append({
            "path": str(path),
            "relPath": str(path.relative_to(artifact_dir)),
            "exists": path.exists(),
            "bytes": path.stat().st_size if path.exists() else None,
            "sha256": sha256_file(path) if path.exists() else None,
        })
    return {
        "schema": SCHEMA + ".evidence_manifest",
        "generated_utc": utc_now(),
        "artifact_dir": str(artifact_dir),
        "required_files": entries,
        **(extra or {}),
    }


def launch(args: argparse.Namespace) -> int:
    run_id = args.run_id
    if not RUN_ID_RE.match(run_id):
        raise SystemExit("run-id must match ^[A-Za-z0-9][A-Za-z0-9_.:-]{2,120}$")

    artifact_dir = Path(args.artifact_dir).expanduser().resolve()
    if artifact_dir.exists() and not args.allow_existing_artifact_dir:
        raise SystemExit(f"artifact dir already exists; refusing overlap: {artifact_dir}")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = artifact_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    cmd = parse_command_json(args.command_json)
    status_path = artifact_dir / "status.json"
    summary_path = artifact_dir / "summary.json"
    run_config_path = artifact_dir / "run_config.json"
    launch_proof_path = artifact_dir / "launch_proof.json"
    manifest_path = artifact_dir / "evidence_manifest.json"
    stdout_path = logs_dir / "observer.stdout.log"
    stderr_path = logs_dir / "observer.stderr.log"

    started_utc = utc_now()
    run_config = {
        "schema": SCHEMA + ".run_config",
        "run_id": run_id,
        "created_utc": started_utc,
        "command": cmd,
        "cwd": str(Path(args.cwd).expanduser().resolve()) if args.cwd else str(WORKSPACE),
        "artifact_dir": str(artifact_dir),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "expected_child_anchor": args.expected_child_anchor,
        "cron_job_id": args.cron_job_id,
        "session_target": args.session_target,
        "owner_note": args.owner_note,
        "safety_contract": {
            "no_shell": True,
            "detached_with_start_new_session": True,
            "evidence_written_before_pass_anchor": True,
            "registry_updated_before_pass_anchor": True,
            "child_semantics_not_certified_by_harness": True,
        },
    }
    write_json_atomic(run_config_path, run_config)
    write_json_atomic(status_path, {
        "schema": SCHEMA + ".status",
        "run_id": run_id,
        "status": "launching",
        "updated_utc": utc_now(),
        "artifact_dir": str(artifact_dir),
    })

    stdout_f = stdout_path.open("ab")
    stderr_f = stderr_path.open("ab")
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=run_config["cwd"],
            stdin=subprocess.DEVNULL,
            stdout=stdout_f,
            stderr=stderr_f,
            start_new_session=True,
            close_fds=True,
        )
    finally:
        stdout_f.close()
        stderr_f.close()

    if args.initial_wait_sec > 0:
        time.sleep(args.initial_wait_sec)

    pgid = safe_getpgid(proc.pid)
    sid = safe_getsid(proc.pid)
    alive = pid_alive(proc.pid)
    return_code = proc.poll()
    detached = pgid == proc.pid and sid == proc.pid
    launched_ok = detached and (alive or return_code == 0)

    launch_proof = {
        "schema": SCHEMA + ".launch_proof",
        "run_id": run_id,
        "started_utc": started_utc,
        "checked_utc": utc_now(),
        "pid": proc.pid,
        "pgid": pgid,
        "sid": sid,
        "parent_pid": os.getpid(),
        "pid_alive_after_initial_wait": alive,
        "return_code_after_initial_wait": return_code,
        "session_detached": detached,
        "start_new_session_requested": True,
        "launched_ok": launched_ok,
    }
    write_json_atomic(launch_proof_path, launch_proof)

    status = {
        "schema": SCHEMA + ".status",
        "run_id": run_id,
        "status": "RUNNING" if alive else ("EXITED_ZERO_DURING_INITIAL_WAIT" if return_code == 0 else "LAUNCH_HOLD"),
        "updated_utc": utc_now(),
        "pid": proc.pid,
        "artifact_dir": str(artifact_dir),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "session_detached": detached,
        "pid_alive": alive,
        "return_code_after_initial_wait": return_code,
        "expected_child_anchor": args.expected_child_anchor,
        "harness_pass_anchor": PASS_ANCHOR if launched_ok else None,
        "failed_gates": [] if launched_ok else ["DETACHMENT_OR_CHILD_START_VERIFICATION_FAILED"],
    }
    write_json_atomic(status_path, status)

    summary = {
        "schema": SCHEMA + ".summary",
        "run_id": run_id,
        "classification": "PASS_DETACHED_OBSERVER_LAUNCHED_EVIDENCE_WRITTEN" if launched_ok else "HOLD_DETACHED_OBSERVER_LAUNCH_NOT_PROVEN",
        "pid": proc.pid,
        "artifact_dir": str(artifact_dir),
        "status_path": str(status_path),
        "evidence_manifest_path": str(manifest_path),
        "registry_path": str(Path(args.registry).expanduser().resolve()),
        "safety_readback": [
            "no shell command construction",
            "artifact directory created before child launch",
            "status/summary/evidence manifest written by harness",
            "child detached with start_new_session=True",
            "semantic observer PASS remains child responsibility",
        ],
    }
    write_json_atomic(summary_path, summary)

    manifest = build_manifest(
        artifact_dir,
        [run_config_path, launch_proof_path, status_path, summary_path, stdout_path, stderr_path],
        {"run_id": run_id, "harness_pass_anchor": PASS_ANCHOR if launched_ok else None},
    )
    write_json_atomic(manifest_path, manifest)

    registry_path = Path(args.registry).expanduser().resolve()
    update_registry(registry_path, {
        "run_id": run_id,
        "registered_utc": utc_now(),
        "pid": proc.pid,
        "artifact_dir": str(artifact_dir),
        "status_path": str(status_path),
        "summary_path": str(summary_path),
        "evidence_manifest_path": str(manifest_path),
        "expected_child_anchor": args.expected_child_anchor,
        "harness_status": summary["classification"],
        "command": cmd,
        "cron_job_id": args.cron_job_id,
        "session_target": args.session_target,
    })

    # Re-read after all writes. This catches partial/failed write bugs before PASS.
    missing = [p.name for p in [run_config_path, launch_proof_path, status_path, summary_path, manifest_path] if not p.exists() or p.stat().st_size <= 0]
    if missing:
        print(json.dumps({"ok": False, "missing_required_files": missing, "artifact_dir": str(artifact_dir)}, indent=2, sort_keys=True))
        return 2

    if launched_ok:
        print(PASS_ANCHOR)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    print("LONG_RUNNING_CRON_OBSERVER_HARNESS_LAUNCH_HOLD")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 1


def validate(args: argparse.Namespace) -> int:
    artifact_dir = Path(args.artifact_dir).expanduser().resolve()
    required = [
        artifact_dir / "run_config.json",
        artifact_dir / "launch_proof.json",
        artifact_dir / "status.json",
        artifact_dir / "summary.json",
        artifact_dir / "evidence_manifest.json",
    ]
    missing = [str(p) for p in required if not p.exists() or p.stat().st_size <= 0]
    status = read_json(artifact_dir / "status.json") if (artifact_dir / "status.json").exists() else {}
    proof = read_json(artifact_dir / "launch_proof.json") if (artifact_dir / "launch_proof.json").exists() else {}
    pid = int(status.get("pid") or proof.get("pid") or 0)
    result = {
        "schema": SCHEMA + ".validate",
        "artifact_dir": str(artifact_dir),
        "missing_required_files": missing,
        "pid": pid or None,
        "pid_alive": pid_alive(pid) if pid else False,
        "session_detached": proof.get("session_detached") is True,
        "harness_anchor_present": status.get("harness_pass_anchor") == PASS_ANCHOR,
        "validation_utc": utc_now(),
    }
    ok = not missing and result["session_detached"] and result["harness_anchor_present"]
    result["ok"] = ok
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if ok else 1


def cron_payload(args: argparse.Namespace) -> int:
    cmd = [
        "python3",
        str(WORKSPACE / "scripts/long_running_cron_observer_harness.py"),
        "launch",
        "--run-id", args.run_id,
        "--artifact-dir", args.artifact_dir,
        "--command-json", args.command_json,
        "--expected-child-anchor", args.expected_child_anchor,
    ]
    if args.cron_job_id:
        cmd += ["--cron-job-id", args.cron_job_id]
    if args.session_target:
        cmd += ["--session-target", args.session_target]
    payload = f"""Run exactly one exec tool call with this argv-safe command, then stop. Do not summarize the task instead of executing it. Treat success only if stdout starts with `{PASS_ANCHOR}`. If the exec tool is unavailable or the anchor is absent, report HOLD and do not mark the observer PASS.\n\nCommand:\n{' '.join(json.dumps(part) for part in cmd)}\n"""
    print(payload)
    return 0


def self_test(args: argparse.Namespace) -> int:
    artifact_dir = Path(args.artifact_dir).expanduser().resolve()
    command = json.dumps([sys.executable, "-c", "import time; print('SELF_TEST_CHILD_STARTED', flush=True); time.sleep(2)"])
    ns = argparse.Namespace(
        run_id=args.run_id,
        artifact_dir=str(artifact_dir),
        command_json=command,
        expected_child_anchor="SELF_TEST_CHILD_STARTED",
        cwd=str(WORKSPACE),
        registry=str(Path(args.registry).expanduser().resolve()),
        cron_job_id="self-test",
        session_target="self-test",
        owner_note="self-test",
        initial_wait_sec=0.25,
        allow_existing_artifact_dir=args.allow_existing_artifact_dir,
    )
    code = launch(ns)
    if code != 0:
        return code
    return validate(argparse.Namespace(artifact_dir=str(artifact_dir)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deterministic long-running cron observer launch harness")
    sub = parser.add_subparsers(dest="command", required=True)

    p_launch = sub.add_parser("launch")
    p_launch.add_argument("--run-id", required=True)
    p_launch.add_argument("--artifact-dir", required=True)
    p_launch.add_argument("--command-json", required=True, help="JSON argv array, or @path containing JSON argv array")
    p_launch.add_argument("--expected-child-anchor", default=None)
    p_launch.add_argument("--cwd", default=str(WORKSPACE))
    p_launch.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    p_launch.add_argument("--cron-job-id", default=None)
    p_launch.add_argument("--session-target", default=None)
    p_launch.add_argument("--owner-note", default=None)
    p_launch.add_argument("--initial-wait-sec", type=float, default=1.0)
    p_launch.add_argument("--allow-existing-artifact-dir", action="store_true")
    p_launch.set_defaults(func=launch)

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("--artifact-dir", required=True)
    p_validate.set_defaults(func=validate)

    p_payload = sub.add_parser("cron-payload")
    p_payload.add_argument("--run-id", required=True)
    p_payload.add_argument("--artifact-dir", required=True)
    p_payload.add_argument("--command-json", required=True)
    p_payload.add_argument("--expected-child-anchor", default=None)
    p_payload.add_argument("--cron-job-id", default=None)
    p_payload.add_argument("--session-target", default=None)
    p_payload.set_defaults(func=cron_payload)

    p_self = sub.add_parser("self-test")
    p_self.add_argument("--run-id", default="self-test-long-running-cron-observer-harness")
    p_self.add_argument("--artifact-dir", required=True)
    p_self.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    p_self.add_argument("--allow-existing-artifact-dir", action="store_true")
    p_self.set_defaults(func=self_test)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
