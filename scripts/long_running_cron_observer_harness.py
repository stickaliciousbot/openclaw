#!/usr/bin/python3.12
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
- an internal alert watcher is launched by default and records terminal/stale/abort alerts;
- PID/PGID/SID detachment proof is recorded;
- a durable registry row is updated atomically;
- stdout emits a stable PASS anchor only after evidence files exist.

Production-hook absence checks
------------------------------
For hook/component observers, the child must not declare a production hook absent
from a single negative search for future/spec vocabulary. The launch evidence now
records the required rule: first identify the installed milestone level and
implementation vocabulary from prior checkpoint/observation artifacts, then search
that implementation vocabulary as well as the future/spec vocabulary. A hook with
implementation vocabulary present but future receipt vocabulary absent is a
milestone-level/vocabulary mismatch, not an absence proof.

The child observer command is still responsible for its own semantic checks and
final closeout. This harness proves launch/detachment/evidence wiring and owns a
durable alert-on-terminal watcher for PASS/FAIL/HOLD/ABORT/STALE visibility.
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

try:
    import critical_apply_independent_completion_checker as completion_checker
except ImportError:  # pragma: no cover - direct script execution fallback
    from scripts import critical_apply_independent_completion_checker as completion_checker

WORKSPACE = Path("/home/stickai/.openclaw/workspace")
DEFAULT_REGISTRY = WORKSPACE / "state/long-running-cron-observers/registry.json"
DEFAULT_ALERT_COMMAND_PATH = WORKSPACE / "state/long-running-cron-observers/default-alert-command.json"
PASS_ANCHOR = "LONG_RUNNING_CRON_OBSERVER_HARNESS_LAUNCH_PASS"
ALERT_ANCHOR = "LONG_RUNNING_CRON_OBSERVER_HARNESS_ALERT_RAISED"
SCHEMA = "stickbot.long_running_cron_observer_harness.v1"
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{2,120}$")
PY312 = "/usr/bin/python3.12"
WATCHER_HEARTBEAT = "heartbeat.json"
WATCHER_PROGRESS = "progress.json"
WATCHER_WATCHDOG = "watchdog.json"
H4_VALIDATION = "h4-validation.json"


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


def validate_alert_command(command: list[str]) -> list[str]:
    """Require the governed, explicit provider adapter invocation."""
    if len(command) < 2 or command[0] != PY312:
        raise SystemExit(f"alert command must begin with {PY312}")
    adapter = Path(command[1])
    if not adapter.is_absolute() or adapter.name != "long_running_observer_telegram_alert.py":
        raise SystemExit("alert command must use the absolute long_running_observer_telegram_alert.py adapter")
    if not adapter.is_file():
        raise SystemExit(f"alert adapter does not exist: {adapter}")
    if any(Path(part).name in {"python", "python3", "env", "sh", "bash"} for part in command):
        raise SystemExit("generic interpreter/shell fallback is forbidden")
    return command


def validate_child_command(command: list[str]) -> list[str]:
    """Reject generic interpreter/PATH/shell fallbacks for governed children."""
    if not command or Path(command[0]).name in {"python", "python3", "env", "sh", "bash"}:
        raise SystemExit("child command must not use generic interpreter/PATH/shell fallback")
    if any(Path(part).name in {"python", "python3", "env", "sh", "bash"} for part in command):
        raise SystemExit("generic interpreter/PATH/shell fallback is forbidden")
    return command


def exact_path(path_value: str | Path, *, field: str) -> str:
    value = str(path_value)
    if not value or not Path(value).is_absolute() or any(ch in value for ch in "*?[]"):
        raise SystemExit(f"{field} must be an absolute exact path without glob syntax")
    if ".." in Path(value).parts:
        raise SystemExit(f"{field} must not contain parent traversal")
    return str(Path(value).expanduser().resolve())


def default_alert_command_json(explicit_value: str | None) -> str | None:
    """Resolve alert command JSON.

    Explicit --alert-command-json wins. Otherwise use the local operator-owned
    default command file when it exists. This preserves argv-only execution and
    prevents silent alert-artifact-only launches after we have configured a
    notification command.
    """
    if explicit_value:
        return explicit_value
    env_value = os.environ.get("LONG_RUNNING_OBSERVER_ALERT_COMMAND_JSON")
    if env_value:
        return env_value
    if DEFAULT_ALERT_COMMAND_PATH.exists():
        return "@" + str(DEFAULT_ALERT_COMMAND_PATH)
    return None


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


def proc_starttime(pid: int) -> str | None:
    try:
        return Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").split()[21]
    except Exception:
        return None


def pid_state(pid: int, expected_starttime: str | None = None) -> tuple[bool, str]:
    actual = proc_starttime(pid)
    if actual is None:
        return False, "pid_missing"
    if expected_starttime and actual != expected_starttime:
        return False, "pid_reused"
    return True, "running"


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


def save_registry(path: Path, data: dict[str, Any]) -> None:
    data["updated_utc"] = utc_now()
    write_json_atomic(path, data)


def command_arg(command: list[str], flag: str) -> str | None:
    for i, part in enumerate(command):
        if part == flag and i + 1 < len(command):
            return command[i + 1]
        prefix = flag + "="
        if part.startswith(prefix):
            return part[len(prefix):]
    return None


def semantic_artifact_paths(row: dict[str, Any]) -> dict[str, str | None]:
    command = row.get("command") if isinstance(row.get("command"), list) else []
    artifact_dir = row.get("semantic_artifact_dir") or command_arg(command, "--artifact-root") or command_arg(command, "--receipt-root")
    if not artifact_dir:
        for part in command:
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            if key.endswith("_ROOT") and "HARNESS" not in key and value.startswith("/"):
                artifact_dir = value
                break
    if artifact_dir:
        status_path = row.get("semantic_status_path") or str(Path(str(artifact_dir)) / "status.json")
        summary_path = row.get("semantic_summary_path") or str(Path(str(artifact_dir)) / "summary.json")
    else:
        status_path = row.get("semantic_status_path") or row.get("status_path")
        summary_path = row.get("semantic_summary_path") or row.get("summary_path")
    return {"semantic_artifact_dir": str(artifact_dir) if artifact_dir else None, "semantic_status_path": status_path, "semantic_summary_path": summary_path}


def read_json_obj(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    try:
        p = Path(path)
        if not p.exists() or p.stat().st_size > 10_000_000:
            return {}
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def semantic_terminal(status_obj: dict[str, Any], summary_obj: dict[str, Any]) -> tuple[bool, str | None, str | None]:
    terminal_status = (
        status_obj.get("terminal_status")
        or summary_obj.get("terminal_status")
        or status_obj.get("child_observer_terminal_status")
        or summary_obj.get("child_observer_terminal_status")
        or status_obj.get("m20r_terminal_status")
        or summary_obj.get("m20r_terminal_status")
    )
    closeout_status = status_obj.get("closeout_status") or summary_obj.get("closeout_status")
    status = str(status_obj.get("status") or closeout_status or "").upper()
    term_upper = str(terminal_status or "").upper()

    def inferred_closeout() -> str | None:
        explicit = str(closeout_status or "").upper()
        if explicit in {"PASS", "FAIL", "FAILED", "HOLD", "ABORT"}:
            return "FAIL" if explicit == "FAILED" else explicit
        if "ABORT" in term_upper:
            return "ABORT"
        if "HOLD" in term_upper:
            return "HOLD"
        if "FAIL" in term_upper:
            return "FAIL"
        if "PASS" in term_upper:
            return "PASS"
        if status in {"PASS", "FAIL", "FAILED", "HOLD", "ABORT"}:
            return "FAIL" if status == "FAILED" else status
        return None

    if status in {"PASS", "FAIL", "FAILED", "HOLD", "ABORT", "DONE", "COMPLETE", "COMPLETED"}:
        return True, str(inferred_closeout() or closeout_status or status), str(terminal_status or summary_obj.get("classification") or status)
    if closeout_status or terminal_status:
        close = str(closeout_status or "").upper()
        if close in {"PASS", "FAIL", "FAILED", "HOLD", "ABORT"} or any(marker in term_upper for marker in ("PASS", "FAIL", "HOLD", "ABORT")):
            return True, str(inferred_closeout() or closeout_status or "terminal"), str(terminal_status or summary_obj.get("classification") or closeout_status)
    if summary_obj.get("ok") is True:
        return True, "PASS", str(summary_obj.get("terminal_status") or summary_obj.get("classification") or "PASS")
    if summary_obj.get("ok") is False and (summary_obj.get("failed_gates") or summary_obj.get("terminal_status")):
        return True, str(summary_obj.get("closeout_status") or "HOLD"), str(summary_obj.get("terminal_status") or "HOLD")
    return False, None, None


def completed_line(row: dict[str, Any], status: str | None, terminal_status: str | None, paths: dict[str, str | None]) -> str:
    run_id = row.get("run_id") or "unknown"
    artifact = paths.get("semantic_artifact_dir") or row.get("artifact_dir") or "artifact=unspecified"
    return f"{run_id} status={status or 'completed'} terminal_status={terminal_status or 'terminal'} artifact={artifact}"


def alert_paths(artifact_dir: Path, run_id: str) -> dict[str, Path]:
    alerts_dir = artifact_dir / "alerts"
    safe_run_id = re.sub(r"[^A-Za-z0-9_.:-]", "_", run_id)
    return {
        "alerts_dir": alerts_dir,
        "alert_json": alerts_dir / f"{safe_run_id}.alert.json",
        "alert_log": alerts_dir / f"{safe_run_id}.alert.jsonl",
    }


def append_jsonl(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data, sort_keys=True) + "\n")


def build_alert_event(
    row: dict[str, Any],
    *,
    classification: str,
    closeout_status: str | None,
    terminal_status: str | None,
    detail: str | None,
    paths: dict[str, str | None],
) -> dict[str, Any]:
    return {
        "schema": SCHEMA + ".alert",
        "alert_anchor": ALERT_ANCHOR,
        "run_id": row.get("run_id") or "unknown",
        "classification": classification,
        "closeout_status": closeout_status,
        "terminal_status": terminal_status,
        "detail": detail,
        "artifact_dir": row.get("artifact_dir"),
        "semantic_artifact_dir": paths.get("semantic_artifact_dir"),
        "semantic_status_path": paths.get("semantic_status_path"),
        "semantic_summary_path": paths.get("semantic_summary_path"),
        "pid": row.get("pid"),
        "pid_alive": row.get("pid_alive"),
        "expected_child_anchor": row.get("expected_child_anchor"),
        "owner_note": row.get("owner_note"),
        "created_utc": utc_now(),
    }


def raise_alert(row: dict[str, Any], event: dict[str, Any], alert_command: list[str] | None = None) -> dict[str, Any]:
    artifact_dir = Path(str(row.get("artifact_dir") or ".")).expanduser().resolve()
    run_id = str(row.get("run_id") or "unknown")
    paths = alert_paths(artifact_dir, run_id)
    write_json_atomic(paths["alert_json"], event)
    append_jsonl(paths["alert_log"], event)

    result = {
        "schema": SCHEMA + ".alert_result",
        "alert_path": str(paths["alert_json"]),
        "alert_log_path": str(paths["alert_log"]),
        "alert_command_invoked": False,
        "alert_command_returncode": None,
        "updated_utc": utc_now(),
    }
    if alert_command:
        env = dict(os.environ)
        env.update({
            "LONG_RUNNING_OBSERVER_ALERT_PATH": str(paths["alert_json"]),
            "LONG_RUNNING_OBSERVER_RUN_ID": run_id,
            "LONG_RUNNING_OBSERVER_CLOSEOUT_STATUS": str(event.get("closeout_status") or ""),
            "LONG_RUNNING_OBSERVER_TERMINAL_STATUS": str(event.get("terminal_status") or ""),
        })
        stdout_path = paths["alerts_dir"] / f"{run_id}.alert-command.stdout.log"
        stderr_path = paths["alerts_dir"] / f"{run_id}.alert-command.stderr.log"
        try:
            proc = subprocess.run(alert_command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=60)
            stdout_path.write_bytes(proc.stdout)
            stderr_path.write_bytes(proc.stderr)
            result.update({
                "alert_command_invoked": True,
                "alert_command_returncode": proc.returncode,
                "alert_command_stdout_path": str(stdout_path),
                "alert_command_stderr_path": str(stderr_path),
                "alert_command_stdout_sha256": sha256_file(stdout_path),
                "alert_command_stderr_sha256": sha256_file(stderr_path),
            })
            try:
                stdout_obj = json.loads(proc.stdout.decode("utf-8")) if proc.stdout else {}
            except (UnicodeDecodeError, json.JSONDecodeError):
                stdout_obj = {}
            registration = read_json_obj(str(row.get("completion_checker_registration_path")))
            delivery = completion_checker.classify_delivery(
                alert_result=result,
                registration=registration,
                command_stdout=stdout_obj if isinstance(stdout_obj, dict) else {},
            )
            result.update({
                "delivery_classification": delivery.get("classification"),
                "owner_visible_delivery_proven": delivery.get("owner_visible") is True,
                "delivery_retry_allowed": False,
                "delivery_reason": delivery.get("reason"),
            })
        except subprocess.TimeoutExpired as exc:
            stdout_path.write_bytes(exc.stdout or b"")
            stderr_path.write_bytes(exc.stderr or b"")
            result.update({
                "alert_command_invoked": True,
                "alert_command_returncode": None,
                "alert_command_timed_out": True,
                "alert_command_timeout_sec": 60,
                "alert_command_stdout_path": str(stdout_path),
                "alert_command_stderr_path": str(stderr_path),
                "alert_command_stdout_sha256": sha256_file(stdout_path),
                "alert_command_stderr_sha256": sha256_file(stderr_path),
                "delivery_classification": completion_checker.DELIVERY_UNKNOWN,
                "owner_visible_delivery_proven": False,
                "delivery_retry_allowed": False,
                "delivery_timeout_detail": "alert subprocess exceeded timeout; provider receipt reconciliation required; no retry",
            })
    write_json_atomic(paths["alerts_dir"] / f"{run_id}.alert-result.json", result)
    return result


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
    alert_command_json = default_alert_command_json(args.alert_command_json)
    if not alert_command_json:
        raise SystemExit("mandatory alert watcher command is not configured")
    alert_command = validate_alert_command(parse_command_json(alert_command_json))

    artifact_dir = Path(args.artifact_dir).expanduser().resolve()
    if artifact_dir.exists() and not args.allow_existing_artifact_dir:
        raise SystemExit(f"artifact dir already exists; refusing overlap: {artifact_dir}")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = artifact_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    cmd = validate_child_command(parse_command_json(args.command_json))
    status_path = artifact_dir / "status.json"
    summary_path = artifact_dir / "summary.json"
    run_config_path = artifact_dir / "run_config.json"
    launch_proof_path = artifact_dir / "launch_proof.json"
    manifest_path = artifact_dir / "evidence_manifest.json"
    stdout_path = logs_dir / "observer.stdout.log"
    stderr_path = logs_dir / "observer.stderr.log"
    alert_stdout_path = logs_dir / "alert-watcher.stdout.log"
    alert_stderr_path = logs_dir / "alert-watcher.stderr.log"
    alert_watch_proof_path = artifact_dir / "alert_watch_proof.json"
    completion_registration_path = artifact_dir / "completion-checker-registration.json"
    completion_preflight_path = artifact_dir / "completion-checker-preflight.json"
    heartbeat_path = artifact_dir / WATCHER_HEARTBEAT
    progress_path = artifact_dir / WATCHER_PROGRESS
    watchdog_path = artifact_dir / WATCHER_WATCHDOG
    h4_validation_path = artifact_dir / H4_VALIDATION
    watcher_startup_path = artifact_dir / "alert-watch-startup.json"

    # Independent completion is a mandatory launch contract.  Registration is
    # exact-path metadata only; it does not read or mutate the semantic root.
    semantic_paths = semantic_artifact_paths({"command": cmd})
    semantic_artifact_dir = getattr(args, "semantic_artifact_dir", None) or semantic_paths.get("semantic_artifact_dir") or str(artifact_dir / "semantic")
    provider_receipt_path = exact_path(args.provider_receipt_path, field="provider-receipt-path") if args.provider_receipt_path else None
    if not provider_receipt_path:
        raise SystemExit("provider-receipt-path is mandatory")
    completion_registration = completion_checker.build_registration(
        run_id=run_id,
        harness_artifact_dir=artifact_dir,
        semantic_artifact_dir=semantic_artifact_dir,
        semantic_status_path=getattr(args, "semantic_status_path", None) or semantic_paths.get("semantic_status_path"),
        semantic_summary_path=getattr(args, "semantic_summary_path", None) or semantic_paths.get("semantic_summary_path"),
        terminal_seal_path=getattr(args, "terminal_seal_path", None),
        manifest_path=getattr(args, "semantic_manifest_path", None),
        detached_receipt_path=getattr(args, "detached_receipt_path", None),
        notification_plane_path=getattr(args, "notification_plane_path", None),
        alert_result_path=getattr(args, "alert_result_path", None),
        provider_receipt_path=provider_receipt_path,
    )
    completion_preflight = completion_checker.preflight_registration(completion_registration)
    write_json_atomic(completion_registration_path, completion_registration)
    write_json_atomic(completion_preflight_path, completion_preflight)
    if not completion_preflight.get("ok"):
        raise SystemExit("independent completion checker registration preflight failed")

    h4_validation = {
        "schema": SCHEMA + ".h4_validation",
        "status": "PASS",
        "checked_utc": utc_now(),
        "registered_paths_exact": True,
        "recursive_scan": False,
        "rglob": False,
        "os_walk": False,
        "max_paths": completion_checker.MAX_REGISTERED_PATHS,
        "max_file_bytes": completion_checker.MAX_FILE_BYTES,
        "provider_receipt_path": provider_receipt_path,
    }
    write_json_atomic(h4_validation_path, h4_validation)
    write_json_atomic(heartbeat_path, {"schema": SCHEMA + ".heartbeat", "phase": "prelaunch", "tick": 0, "updated_utc": utc_now(), "status": "ARMED"})
    write_json_atomic(progress_path, {"schema": SCHEMA + ".progress", "phase": "prelaunch", "items_seen": 0, "updated_utc": utc_now(), "status": "ARMED"})
    write_json_atomic(watchdog_path, {"schema": SCHEMA + ".watchdog", "status": "ARMED", "updated_utc": utc_now(), "heartbeat_path": str(heartbeat_path), "progress_path": str(progress_path)})

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
        "alert_watch": {
            "enabled": True,
            "interval_sec": args.alert_check_interval_sec,
            "timeout_sec": args.alert_timeout_sec,
            "command_configured": True,
            "command": alert_command,
            "provider_receipt_path": provider_receipt_path,
            "heartbeat_path": str(heartbeat_path),
            "progress_path": str(progress_path),
            "watchdog_path": str(watchdog_path),
            "startup_readback_path": str(watcher_startup_path),
        },
        "completion_checker": {
            "schema": completion_checker.SCHEMA,
            "required": True,
            "registration_path": str(completion_registration_path),
            "preflight_path": str(completion_preflight_path),
            "read_only": True,
            "exact_paths_only": True,
            "worker_self_certification_ignored": True,
            "provider_receipt_required_for_owner_delivery": True,
            "delivery_unknown_on_timeout": True,
            "retry_on_timeout": False,
            "h4_validation_path": str(h4_validation_path),
        },
        "safety_contract": {
            "no_shell": True,
            "detached_with_start_new_session": True,
            "evidence_written_before_pass_anchor": True,
            "registry_updated_before_pass_anchor": True,
            "alert_watcher_started_before_child_launch": True,
            "independent_completion_checker_registered_before_child_launch": True,
            "independent_completion_checker_preflight_passed_before_child_launch": completion_preflight.get("ok") is True,
            "child_semantics_not_certified_by_harness": True,
            "production_hook_absence_rule": {
                "required_for_hook_observers": True,
                "must_identify_installed_milestone_level_first": True,
                "must_use_prior_checkpoint_implementation_vocabulary": True,
                "must_not_treat_spec_vocabulary_zero_matches_as_absence": True,
                "implementation_vocabulary_present_spec_vocabulary_absent_classification": "HOOK_PRESENT_MILESTONE_LEVEL_MISMATCH",
            },
        },
    }
    write_json_atomic(run_config_path, run_config)
    write_json_atomic(status_path, {
        "schema": SCHEMA + ".status",
        "run_id": run_id,
        "status": "ARMED",
        "updated_utc": utc_now(),
        "artifact_dir": str(artifact_dir),
        "alert_watch_enabled": True,
        "heartbeat_path": str(heartbeat_path),
        "progress_path": str(progress_path),
        "watchdog_path": str(watchdog_path),
        "h4_validation_path": str(h4_validation_path),
        "provider_receipt_path": provider_receipt_path,
    })

    registry_path = Path(args.registry).expanduser().resolve()
    initial_row = {
        "run_id": run_id, "registered_utc": utc_now(), "pid": 0,
        "proc_starttime": None, "launch_state": "WATCHER_STARTUP",
        "artifact_dir": str(artifact_dir), "status_path": str(status_path),
        "summary_path": str(summary_path), "evidence_manifest_path": str(manifest_path),
        **semantic_artifact_paths({"command": cmd}),
        "semantic_artifact_dir": str(semantic_artifact_dir) if semantic_artifact_dir else None,
        "semantic_status_path": getattr(args, "semantic_status_path", None) or str(Path(str(semantic_artifact_dir)) / "status.json") if semantic_artifact_dir else None,
        "semantic_summary_path": getattr(args, "semantic_summary_path", None) or str(Path(str(semantic_artifact_dir)) / "summary.json") if semantic_artifact_dir else None,
        "expected_child_anchor": args.expected_child_anchor,
        "harness_status": "ARMED", "command": cmd,
        "cron_job_id": args.cron_job_id, "session_target": args.session_target,
        "owner_note": args.owner_note, "alert_watch_enabled": True,
        "completion_checker_required": True,
        "completion_checker_registration_path": str(completion_registration_path),
        "completion_checker_preflight_path": str(completion_preflight_path),
        "provider_receipt_path": provider_receipt_path,
        "heartbeat_path": str(heartbeat_path), "progress_path": str(progress_path),
        "watchdog_path": str(watchdog_path), "h4_validation_path": str(h4_validation_path),
        "abort_artifact_path": getattr(args, "abort_artifact_path", None),
    }
    update_registry(registry_path, initial_row)
    alert_cmd = [PY312, str(Path(__file__).resolve()), "watch-alert", "--run-id", run_id,
                 "--registry", str(registry_path), "--artifact-dir", str(artifact_dir),
                 "--interval-sec", str(args.alert_check_interval_sec),
                 "--timeout-sec", str(args.alert_timeout_sec), "--startup-path", str(watcher_startup_path),
                 "--alert-command-json", alert_command_json]
    stdout_alert = alert_stdout_path.open("ab")
    stderr_alert = alert_stderr_path.open("ab")
    try:
        alert_proc: subprocess.Popen[bytes] = subprocess.Popen(
            alert_cmd, cwd=run_config["cwd"], stdin=subprocess.DEVNULL,
            stdout=stdout_alert, stderr=stderr_alert, start_new_session=True, close_fds=True,
        )
    finally:
        stdout_alert.close(); stderr_alert.close()
    startup_deadline = time.monotonic() + max(5.0, min(args.alert_startup_timeout_sec, 60.0))
    startup_obj: dict[str, Any] = {}
    while time.monotonic() < startup_deadline:
        startup_obj = read_json_obj(str(watcher_startup_path))
        if startup_obj.get("status") == "READY":
            break
        if alert_proc.poll() is not None:
            raise SystemExit("alert watcher exited before startup readiness")
        time.sleep(0.05)
    if startup_obj.get("status") != "READY":
        raise SystemExit("alert watcher startup readiness timeout")
    watcher_pid = int(startup_obj.get("pid") or 0)
    watcher_starttime = str(startup_obj.get("proc_starttime") or "")
    watcher_alive, watcher_state = pid_state(watcher_pid, watcher_starttime)
    if not watcher_alive or watcher_state != "running" or int(startup_obj.get("heartbeat_tick") or 0) < 1 or startup_obj.get("readback_verified") is not True:
        raise SystemExit("alert watcher PID/start-tick/readback verification failed")
    alert_watch_proof = {
        "schema": SCHEMA + ".alert_watch_proof", "run_id": run_id,
        "started_utc": startup_obj.get("started_utc"), "verified_utc": utc_now(),
        "pid": watcher_pid, "proc_starttime": watcher_starttime,
        "pgid": safe_getpgid(watcher_pid), "sid": safe_getsid(watcher_pid),
        "session_detached": safe_getpgid(watcher_pid) == watcher_pid and safe_getsid(watcher_pid) == watcher_pid,
        "heartbeat_tick": startup_obj.get("heartbeat_tick"), "readback_verified": True,
        "alert_command_configured": True, "provider_receipt_path": provider_receipt_path,
        "heartbeat_path": str(heartbeat_path), "progress_path": str(progress_path),
        "watchdog_path": str(watchdog_path), "h4_validation_path": str(h4_validation_path),
        "stdout_path": str(alert_stdout_path), "stderr_path": str(alert_stderr_path),
    }
    write_json_atomic(alert_watch_proof_path, alert_watch_proof)
    status = read_json_obj(str(status_path))
    status.update({"alert_watch_pid": watcher_pid, "alert_watch_proof_path": str(alert_watch_proof_path), "alert_watch_ready": True})
    write_json_atomic(status_path, status)
    update_registry(registry_path, {**initial_row, "alert_watch_pid": watcher_pid, "alert_watch_proc_starttime": watcher_starttime, "alert_watch_proof_path": str(alert_watch_proof_path), "launch_state": "WATCHER_READY"})

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
        "alert_watch_enabled": True,
        "completion_checker_required": True,
        "completion_checker_registration_path": str(completion_registration_path),
        "completion_checker_preflight_path": str(completion_preflight_path),
        "failed_gates": [] if launched_ok else ["DETACHMENT_OR_CHILD_START_VERIFICATION_FAILED"],
    }
    write_json_atomic(status_path, status)
    update_registry(registry_path, {
        **initial_row,
        "pid": proc.pid,
        "proc_starttime": proc_starttime(proc.pid),
        "launch_state": "CHILD_STARTED" if launched_ok else "CHILD_LAUNCH_HOLD",
        "harness_status": "RUNNING" if launched_ok else "HOLD",
        "alert_watch_pid": watcher_pid,
        "alert_watch_proc_starttime": watcher_starttime,
        "alert_watch_proof_path": str(alert_watch_proof_path),
    })

    summary = {
        "schema": SCHEMA + ".summary",
        "run_id": run_id,
        "classification": "PASS_DETACHED_OBSERVER_LAUNCHED_EVIDENCE_WRITTEN" if launched_ok else "HOLD_DETACHED_OBSERVER_LAUNCH_NOT_PROVEN",
        "pid": proc.pid,
        "artifact_dir": str(artifact_dir),
        "status_path": str(status_path),
        "evidence_manifest_path": str(manifest_path),
        "registry_path": str(Path(args.registry).expanduser().resolve()),
        "alert_watch_enabled": True,
        "completion_checker_required": True,
        "completion_checker_registration_path": str(completion_registration_path),
        "completion_checker_preflight_path": str(completion_preflight_path),
        "alert_stdout_path": str(alert_stdout_path),
        "alert_stderr_path": str(alert_stderr_path),
        "safety_readback": [
            "no shell command construction",
            "artifact directory created before child launch",
            "status/summary/evidence manifest written by harness",
            "child detached with start_new_session=True",
            "internal alert watcher starts and is verified before child launch",
            "semantic observer PASS remains child responsibility",
            "hook absence requires milestone-level + implementation-vocabulary check, not spec vocabulary alone",
        ],
    }
    write_json_atomic(summary_path, summary)

    manifest = build_manifest(
        artifact_dir,
        [run_config_path, launch_proof_path, status_path, summary_path, stdout_path, stderr_path, completion_registration_path, completion_preflight_path, heartbeat_path, progress_path, watchdog_path, h4_validation_path, alert_watch_proof_path, alert_stdout_path, alert_stderr_path],
        {"run_id": run_id, "harness_pass_anchor": PASS_ANCHOR if launched_ok else None, "completion_checker_required": True, "alert_watch_enabled": True, "h4_validation_path": str(h4_validation_path)},
    )
    write_json_atomic(manifest_path, manifest)

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


def read_abort_artifact(path_value: str | None) -> tuple[bool, str | None, str | None]:
    """Read one explicitly registered abort path; never scan a directory."""
    if not path_value:
        return False, None, None
    path = Path(path_value)
    try:
        data = read_json_obj(str(path))
    except Exception:
        return True, "abort_artifact_unparseable", str(path)
    if not data:
        return False, None, None
    reason = data.get("reason") or data.get("abort_reason") or data.get("errors_warnings") or "abort_artifact_found"
    return True, str(reason), str(path)



def cleanup_warning_from_result(result: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if "stdout" not in result and "stdout_path" not in result:
        warnings.append("stdout_missing")
    if "stderr" not in result and "stderr_path" not in result:
        warnings.append("stderr_missing")
    return warnings


def terminalise_harness_status(artifact_dir: str | Path, *, semantic_artifact_dir: str | Path | None = None, cleanup_result: dict[str, Any] | None = None) -> dict[str, Any]:
    artifact = Path(artifact_dir).expanduser().resolve()
    status_path = artifact / "status.json"
    status_obj = read_json_obj(str(status_path)) if status_path.exists() else {}
    semantic_dir = Path(semantic_artifact_dir).expanduser().resolve() if semantic_artifact_dir else None
    sem_status = read_json_obj(str(semantic_dir / "status.json")) if semantic_dir else {}
    sem_summary = read_json_obj(str(semantic_dir / "summary.json")) if semantic_dir else {}
    terminal, closeout_status, terminal_status = semantic_terminal(sem_status, sem_summary)
    warnings = cleanup_warning_from_result(cleanup_result or {"stdout_path": status_obj.get("stdout_path", "known"), "stderr_path": status_obj.get("stderr_path", "known")})
    if not terminal:
        result = {
            "schema": SCHEMA + ".terminalisation",
            "classification": "HARNESS_STATUS_STALE_BLOCKED",
            "launch_state": status_obj.get("status"),
            "semantic_state": sem_status.get("status"),
            "cleanup_state": "warning" if warnings else "not_run",
            "cleanup_warnings": warnings,
            "updated_utc": utc_now(),
        }
        write_json_atomic(artifact / "terminalisation.json", result)
        return result
    result = {
        "schema": SCHEMA + ".terminalisation",
        "classification": "HARNESS_TERMINAL_WITH_CLEANUP_WARNING" if warnings else "HARNESS_TERMINALISED_CLEANLY",
        "launch_state": status_obj.get("status"),
        "semantic_state": str(closeout_status or sem_status.get("status") or "terminal"),
        "cleanup_state": "warning" if warnings else "clean",
        "cleanup_warnings": warnings,
        "terminal_status": str(terminal_status or terminal),
        "closeout_status": str(closeout_status or "terminal"),
        "semantic_artifact_dir": str(semantic_dir) if semantic_dir else None,
        "updated_utc": utc_now(),
    }
    merged = dict(status_obj)
    merged.update({
        "status": "TERMINAL",
        "semantic_state": result["semantic_state"],
        "cleanup_state": result["cleanup_state"],
        "terminal_status": result["terminal_status"],
        "closeout_status": result["closeout_status"],
        "terminalisation_classification": result["classification"],
        "updated_utc": result["updated_utc"],
    })
    write_json_atomic(status_path, merged)
    write_json_atomic(artifact / "terminalisation.json", result)
    return result

def check(args: argparse.Namespace) -> int:
    registry_path = Path(args.registry).expanduser().resolve()
    data = load_registry(registry_path)
    stale: list[str] = []
    aborted: list[str] = []
    completed: list[str] = []
    ok_items: list[str] = []
    remaining: list[dict[str, Any]] = []
    checked_utc = utc_now()

    for raw in data.get("runs", []):
        if not isinstance(raw, dict):
            continue
        row = dict(raw)
        run_id = str(row.get("run_id") or "unknown")
        pid = int(row.get("pid") or 0)
        alive, detail = pid_state(pid, row.get("proc_starttime")) if pid else (False, "pid_missing")
        paths = semantic_artifact_paths(row)
        status_obj = read_json_obj(paths.get("semantic_status_path"))
        summary_obj = read_json_obj(paths.get("semantic_summary_path"))
        terminal, closeout_status, terminal_status = semantic_terminal(status_obj, summary_obj)
        row["last_checked_utc"] = checked_utc
        row["last_state"] = detail
        row["pid_alive"] = alive
        row.update({k: v for k, v in paths.items() if v and not row.get(k)})

        if terminal:
            completed.append(completed_line(row, closeout_status, terminal_status, paths))
            try:
                terminalise_harness_status(Path(row.get("artifact_dir") or ""), semantic_artifact_dir=paths.get("semantic_artifact_dir"))
            except Exception as exc:  # noqa: BLE001
                row["terminalisation_warning"] = str(exc)
            continue
        if alive:
            row["last_seen_running_utc"] = checked_utc
            ok_items.append(run_id)
            remaining.append(row)
            continue
        # PID missing — scan for early-abort artifacts before classifying as mere STALE
        artifact_dir = paths.get("semantic_artifact_dir") or row.get("artifact_dir")
        abort_found, abort_reason, abort_path = read_abort_artifact(row.get("abort_artifact_path"))
        if abort_found:
            aborted.append(f"{run_id} ABORTED reason={abort_reason} abort_artifact={abort_path}")
            remaining.append(row)
            continue
        stale.append(f"{run_id} {detail} artifact={artifact_dir or 'unspecified'}")
        remaining.append(row)

    if remaining != data.get("runs", []):
        data["runs"] = remaining
        save_registry(registry_path, data)

    status_report = {
        "schema": SCHEMA + ".watch_check",
        "checked_utc": checked_utc,
        "ok": not stale and not completed and not aborted,
        "ok_items": ok_items,
        "completed": completed,
        "aborted": aborted,
        "stale": stale,
        "registry_path": str(registry_path),
    }
    watch_status_path = registry_path.parent / "last-check.json"
    write_json_atomic(watch_status_path, status_report)

    if completed:
        print("LONG_RUNNING_CRON_OBSERVER_COMPLETED")
        for line in completed:
            print(line)
        if aborted:
            print("LONG_RUNNING_CRON_OBSERVER_ABORTED")
            for line in aborted:
                print(line)
        if stale:
            print("LONG_RUNNING_CRON_OBSERVER_STALE")
            for line in stale:
                print(line)
            return 2
        return 3
    if aborted:
        print("LONG_RUNNING_CRON_OBSERVER_ABORTED")
        for line in aborted:
            print(line)
        if stale:
            print("LONG_RUNNING_CRON_OBSERVER_STALE")
            for line in stale:
                print(line)
        return 4
    if stale:
        print("LONG_RUNNING_CRON_OBSERVER_STALE")
        for line in stale:
            print(line)
        return 2
    print("WATCH_OK")
    return 0


def find_registry_row(registry_path: Path, run_id: str) -> dict[str, Any] | None:
    data = load_registry(registry_path)
    for row in data.get("runs", []):
        if isinstance(row, dict) and row.get("run_id") == run_id:
            return dict(row)
    return None


def watch_alert(args: argparse.Namespace) -> int:
    registry_path = Path(args.registry).expanduser().resolve()
    artifact_dir = Path(args.artifact_dir).expanduser().resolve()
    alert_command_json = args.alert_command_json
    alert_command = parse_command_json(alert_command_json) if alert_command_json else None
    deadline = None if args.timeout_sec <= 0 else time.monotonic() + args.timeout_sec
    interval = max(args.interval_sec, 0.25)
    startup_path = Path(args.startup_path).expanduser().resolve() if getattr(args, "startup_path", None) else artifact_dir / "alert-watch-startup.json"
    heartbeat_path = artifact_dir / WATCHER_HEARTBEAT
    progress_path = artifact_dir / WATCHER_PROGRESS
    watchdog_path = artifact_dir / WATCHER_WATCHDOG
    startup_started = utc_now()
    write_json_atomic(heartbeat_path, {"schema": SCHEMA + ".heartbeat", "phase": "watcher_startup", "tick": 1, "updated_utc": utc_now(), "status": "RUNNING"})
    write_json_atomic(progress_path, {"schema": SCHEMA + ".progress", "phase": "watcher_startup", "items_seen": 0, "updated_utc": utc_now(), "status": "RUNNING"})
    write_json_atomic(watchdog_path, {"schema": SCHEMA + ".watchdog", "status": "WATCHER_READY", "updated_utc": utc_now(), "heartbeat_path": str(heartbeat_path), "progress_path": str(progress_path)})
    startup = {
        "schema": SCHEMA + ".alert_watch_startup",
        "status": "READY",
        "run_id": args.run_id,
        "started_utc": startup_started,
        "pid": os.getpid(),
        "proc_starttime": proc_starttime(os.getpid()),
        "heartbeat_tick": 1,
        "heartbeat_path": str(heartbeat_path),
        "progress_path": str(progress_path),
        "watchdog_path": str(watchdog_path),
        "readback_verified": all(p.is_file() and p.stat().st_size > 0 for p in (registry_path, heartbeat_path, progress_path, watchdog_path)),
        "recursive_scan": False,
        "h4_exact_path_validation": True,
    }
    write_json_atomic(startup_path, startup)

    while True:
        row = find_registry_row(registry_path, args.run_id)
        if row is None:
            row = {"run_id": args.run_id, "artifact_dir": str(artifact_dir), "pid": 0}
            event = build_alert_event(
                row,
                classification="REGISTRY_ROW_MISSING",
                closeout_status="STALE",
                terminal_status="REGISTRY_ROW_MISSING",
                detail="registry row missing while alert watcher was active",
                paths={"semantic_artifact_dir": None, "semantic_status_path": None, "semantic_summary_path": None},
            )
            result = raise_alert(row, event, alert_command)
            print(ALERT_ANCHOR)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 2

        row.setdefault("artifact_dir", str(artifact_dir))
        pid = int(row.get("pid") or 0)
        if pid <= 0 or row.get("launch_state") in {"WATCHER_STARTUP", "WATCHER_READY"}:
            tick = int(read_json_obj(str(heartbeat_path)).get("tick") or 1) + 1
            write_json_atomic(heartbeat_path, {"schema": SCHEMA + ".heartbeat", "phase": "await_child_registration", "tick": tick, "updated_utc": utc_now(), "status": "RUNNING"})
            write_json_atomic(progress_path, {"schema": SCHEMA + ".progress", "phase": "await_child_registration", "items_seen": 0, "updated_utc": utc_now(), "status": "WAITING"})
            if deadline is not None and time.monotonic() >= deadline:
                raise SystemExit("alert watcher timed out before child registration")
            time.sleep(interval)
            continue
        alive, detail = pid_state(pid, row.get("proc_starttime")) if pid else (False, "pid_missing")
        row["pid_alive"] = alive
        paths = semantic_artifact_paths(row)
        tick = int(read_json_obj(str(heartbeat_path)).get("tick") or 1) + 1
        write_json_atomic(heartbeat_path, {"schema": SCHEMA + ".heartbeat", "phase": "reconcile_semantic_terminal", "tick": tick, "updated_utc": utc_now(), "status": "RUNNING", "pid_alive": alive})
        write_json_atomic(progress_path, {"schema": SCHEMA + ".progress", "phase": "reconcile_semantic_terminal", "items_seen": tick, "updated_utc": utc_now(), "status": "RUNNING"})
        write_json_atomic(watchdog_path, {"schema": SCHEMA + ".watchdog", "status": "WATCHING", "updated_utc": utc_now(), "last_heartbeat_tick": tick, "pid_alive": alive})
        status_obj = read_json_obj(paths.get("semantic_status_path"))
        if status_obj.get("semantic_artifact_dir") and not paths.get("semantic_artifact_dir"):
            paths["semantic_artifact_dir"] = str(status_obj.get("semantic_artifact_dir"))
            paths["semantic_status_path"] = str(Path(paths["semantic_artifact_dir"] or "") / "status.json")
            paths["semantic_summary_path"] = str(Path(paths["semantic_artifact_dir"] or "") / "summary.json")
            status_obj = read_json_obj(paths.get("semantic_status_path"))
        summary_obj = read_json_obj(paths.get("semantic_summary_path"))
        terminal, closeout_status, terminal_status = semantic_terminal(status_obj, summary_obj)
        if terminal:
            try:
                terminalise_harness_status(artifact_dir, semantic_artifact_dir=paths.get("semantic_artifact_dir"))
            except Exception as exc:  # noqa: BLE001
                row["terminalisation_warning"] = str(exc)
            event = build_alert_event(
                row,
                classification="TERMINAL",
                closeout_status=closeout_status,
                terminal_status=terminal_status,
                detail="semantic terminal detected by internal harness alert watcher",
                paths=paths,
            )
            result = raise_alert(row, event, alert_command)
            print(ALERT_ANCHOR)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 3

        if not alive:
            abort_found, abort_reason, abort_path = read_abort_artifact(row.get("abort_artifact_path"))
            classification = "ABORTED" if abort_found else "STALE"
            event = build_alert_event(
                row,
                classification=classification,
                closeout_status="ABORT" if abort_found else "STALE",
                terminal_status=classification,
                detail=f"{detail}; abort_reason={abort_reason}; abort_path={abort_path}" if abort_found else detail,
                paths=paths,
            )
            result = raise_alert(row, event, alert_command)
            print(ALERT_ANCHOR)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 4 if abort_found else 2

        if deadline is not None and time.monotonic() >= deadline:
            event = build_alert_event(
                row,
                classification="WATCH_TIMEOUT",
                closeout_status="STALE",
                terminal_status="WATCH_TIMEOUT",
                detail=f"alert watcher timeout after {args.timeout_sec} seconds",
                paths=paths,
            )
            result = raise_alert(row, event, alert_command)
            print(ALERT_ANCHOR)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 2

        time.sleep(interval)


def done(args: argparse.Namespace) -> int:
    registry_path = Path(args.registry).expanduser().resolve()
    data = load_registry(registry_path)
    before = len(data.get("runs", []))
    data["runs"] = [r for r in data.get("runs", []) if not (isinstance(r, dict) and r.get("run_id") == args.run_id)]
    save_registry(registry_path, data)
    print(f"DONE_OK run_id={args.run_id} removed={before - len(data['runs'])}")
    return 0


def list_runs(args: argparse.Namespace) -> int:
    registry_path = Path(args.registry).expanduser().resolve()
    data = load_registry(registry_path)
    print(json.dumps(data, indent=2, sort_keys=True))
    return 0


def cron_payload(args: argparse.Namespace) -> int:
    cmd = [
        PY312,
        str(WORKSPACE / "scripts/long_running_cron_observer_harness.py"),
        "launch",
        "--run-id", args.run_id,
        "--artifact-dir", args.artifact_dir,
        "--command-json", args.command_json,
        "--expected-child-anchor", args.expected_child_anchor,
        "--provider-receipt-path", str(Path(args.artifact_dir).expanduser().resolve() / "provider-receipt.json"),
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
    command = json.dumps([PY312, "-c", "import time; print('SELF_TEST_CHILD_STARTED', flush=True); time.sleep(2)"])
    provider_receipt_path = artifact_dir / "provider-receipt.json"
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
        alert_check_interval_sec=0.25,
        alert_timeout_sec=10.0,
        alert_startup_timeout_sec=10.0,
        alert_command_json=None,
        semantic_artifact_dir=str(artifact_dir / "semantic"),
        provider_receipt_path=str(provider_receipt_path),
        semantic_status_path=None,
        semantic_summary_path=None,
        terminal_seal_path=None,
        semantic_manifest_path=None,
        detached_receipt_path=None,
        notification_plane_path=None,
        alert_result_path=None,
        abort_artifact_path=None,
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
    p_launch.add_argument("--alert-check-interval-sec", type=float, default=5.0)
    p_launch.add_argument("--alert-timeout-sec", type=float, default=0.0, help="0 means no timeout")
    p_launch.add_argument("--alert-startup-timeout-sec", type=float, default=15.0)
    p_launch.add_argument("--alert-command-json", default=None, help="Optional argv JSON command invoked when an alert is raised; alert path is provided in env")
    p_launch.add_argument("--semantic-artifact-dir", default=None, help="Registered semantic root; exact paths only, no recursive scan")
    p_launch.add_argument("--semantic-status-path", default=None)
    p_launch.add_argument("--semantic-summary-path", default=None)
    p_launch.add_argument("--terminal-seal-path", default=None)
    p_launch.add_argument("--semantic-manifest-path", default=None)
    p_launch.add_argument("--detached-receipt-path", default=None)
    p_launch.add_argument("--notification-plane-path", default=None)
    p_launch.add_argument("--alert-result-path", default=None)
    p_launch.add_argument("--provider-receipt-path", required=True, help="Mandatory exact provider receipt path")
    p_launch.add_argument("--abort-artifact-path", default=None, help="Optional exact abort artifact path; no directory scan")
    p_launch.set_defaults(func=launch)

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("--artifact-dir", required=True)
    p_validate.set_defaults(func=validate)

    p_check = sub.add_parser("check")
    p_check.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    p_check.set_defaults(func=check)

    p_watch_alert = sub.add_parser("watch-alert")
    p_watch_alert.add_argument("--run-id", required=True)
    p_watch_alert.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    p_watch_alert.add_argument("--artifact-dir", required=True)
    p_watch_alert.add_argument("--interval-sec", type=float, default=5.0)
    p_watch_alert.add_argument("--timeout-sec", type=float, default=0.0)
    p_watch_alert.add_argument("--alert-command-json", default=None)
    p_watch_alert.add_argument("--startup-path", default=None)
    p_watch_alert.set_defaults(func=watch_alert)

    p_done = sub.add_parser("done")
    p_done.add_argument("run_id")
    p_done.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    p_done.set_defaults(func=done)

    p_list = sub.add_parser("list")
    p_list.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    p_list.set_defaults(func=list_runs)

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
