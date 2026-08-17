#!/usr/bin/env python3
"""Critical Apply M4 exact execution, blocked-child, identity and containment.

Fixture/shadow-root only. This module never accepts shell strings, never searches
PATH, and never infers production OpenClaw/Gateway/npm locations.
"""
from __future__ import annotations

import hashlib
import json
import os
import resource
import signal
import stat
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from critical_apply_atomic_io import atomic_create_json, atomic_replace_json, sha256_file
from critical_apply_contracts import ContractError, canonical_json_dumps, is_sha256
from critical_apply_journal import read_boot_id

APPLY_INTENT_SCHEMA = "critical_apply.apply_intent.v2"
BLOCKED_CHILD_SCHEMA = "critical_apply.apply_child_spawned_blocked.v2"
MUTATION_RELEASE_SCHEMA = "critical_apply.mutation_release.v2"
APPLY_EXIT_SCHEMA = "critical_apply.apply_exit.v2"
EXEC_SPEC_SCHEMA = "critical_apply.exact_exec_spec.v2"

FORBIDDEN_ROOTS = tuple(Path(p) for p in (
    "/usr", "/usr/local", "/home/stickai/.npm-global",
    "/home/stickai/.openclaw/protected-memory",
))

class ProcessContractError(ContractError):
    pass

@dataclass(frozen=True)
class ExecutableIdentity:
    realpath: str
    sha256: str
    device: int
    inode: int
    mode: str
    byte_count: int
    interpreter_realpath: str | None = None
    interpreter_sha256: str | None = None

    def to_json(self) -> dict[str, Any]:
        return asdict(self)

@dataclass(frozen=True)
class ExactExecSpec:
    schema: str
    executable: str
    argv: tuple[str, ...]
    expected_sha256: str
    cwd: str
    env: Mapping[str, str]
    stdout_path: str
    stderr_path: str
    stdin_policy: str = "devnull"
    uid: int | None = None
    gid: int | None = None
    umask: int = 0o077
    timeout_seconds: float = 5.0
    graceful_timeout_seconds: float = 0.5
    forced_timeout_seconds: float = 0.5
    allow_script_interpreter: bool = True
    resource_limits: Mapping[str, int] | None = None

    def to_json(self) -> dict[str, Any]:
        d = asdict(self); d["argv"] = list(self.argv); return d

@dataclass(frozen=True)
class ProcessIdentity:
    pid: int
    start_ticks: int
    boot_id: str
    process_group_id: int
    session_id: int
    pid_namespace: str
    executable_intended: str
    argv_sha256: str
    pidfd_available: bool
    pidfd_opened: bool
    cgroup_path: str | None
    cgroup_inode: int | None

    def to_json(self) -> dict[str, Any]:
        return asdict(self)

@dataclass
class BlockedChild:
    transaction_root: Path
    transaction_id: str
    spec: ExactExecSpec
    identity: ProcessIdentity
    release_fd: int
    pidfd: int | None
    stdout_file: Path
    stderr_file: Path
    released: bool = False


def _sha_obj(obj: Mapping[str, Any] | Sequence[Any]) -> str:
    return hashlib.sha256(canonical_json_dumps(obj).encode()).hexdigest()


def _under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def _reject_forbidden_path(path: Path, allowed_roots: Sequence[Path], *, package_authority: Mapping[str, Any] | None = None) -> None:
    rp = path.resolve()
    if not any(_under(rp, a) for a in allowed_roots):
        raise ProcessContractError("PATH_OUTSIDE_ALLOWED_FIXTURE_ROOTS", str(rp))
    for f in FORBIDDEN_ROOTS:
        if _under(rp, f):
            if package_authority is not None:
                from critical_apply_package_authority import path_authorized_by_package_authority
                if path_authorized_by_package_authority(rp, package_authority):
                    return
            raise ProcessContractError("PRODUCTION_PATH_FORBIDDEN", str(rp))


def read_start_ticks(pid: int) -> int:
    stat_text = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8", errors="replace")
    after = stat_text.rsplit(")", 1)[1].strip().split()
    return int(after[19])


def _pid_namespace(pid: int) -> str:
    try: return os.readlink(f"/proc/{pid}/ns/pid")
    except OSError: return "unavailable"


def _cgroup(pid: int) -> tuple[str | None, int | None]:
    try:
        lines = Path(f"/proc/{pid}/cgroup").read_text().splitlines()
        cg = lines[0].split(":",2)[-1] if lines else None
        inode = os.stat(f"/proc/{pid}/cgroup").st_ino
        return cg, inode
    except OSError:
        return None, None


def identify_executable(path: Path, expected_sha256: str, *, allow_script_interpreter: bool = True) -> ExecutableIdentity:
    p = path.resolve(strict=True)
    st = os.lstat(p)
    if not stat.S_ISREG(st.st_mode):
        raise ProcessContractError("EXECUTABLE_NOT_REGULAR", str(p))
    if stat.S_ISLNK(st.st_mode):
        raise ProcessContractError("EXECUTABLE_SYMLINK_FORBIDDEN", str(p))
    actual = sha256_file(p)
    if not is_sha256(expected_sha256) or actual != expected_sha256:
        raise ProcessContractError("EXECUTABLE_SHA256_MISMATCH", str(p), details={"actual": actual, "expected": expected_sha256})
    interp_r = interp_s = None
    if allow_script_interpreter:
        head = p.read_bytes()[:256]
        if head.startswith(b"#!"):
            first = head.splitlines()[0][2:].decode("utf-8", "replace").strip().split()[0]
            interp = Path(first).resolve(strict=True)
            ist = os.lstat(interp)
            if not stat.S_ISREG(ist.st_mode):
                raise ProcessContractError("INTERPRETER_NOT_REGULAR", str(interp))
            interp_r, interp_s = str(interp), sha256_file(interp)
    return ExecutableIdentity(str(p), actual, st.st_dev, st.st_ino, oct(stat.S_IMODE(st.st_mode)), st.st_size, interp_r, interp_s)


def validate_exact_exec_spec(spec: ExactExecSpec, *, transaction_root: Path, allowed_roots: Sequence[Path], package_authority: Mapping[str, Any] | None = None) -> ExecutableIdentity:
    if spec.schema != EXEC_SPEC_SCHEMA:
        raise ProcessContractError("EXEC_SPEC_SCHEMA_INVALID", spec.schema)
    if not isinstance(spec.argv, tuple) or not spec.argv:
        raise ProcessContractError("ARGV_EMPTY_OR_NOT_TUPLE", "argv")
    exe = Path(spec.executable)
    if not exe.is_absolute():
        raise ProcessContractError("EXECUTABLE_MUST_BE_ABSOLUTE", spec.executable)
    if spec.argv[0] != str(exe):
        raise ProcessContractError("ARGV0_EXECUTABLE_MISMATCH", spec.argv[0])
    if any("=" in k or "\x00" in k or "\x00" in v for k,v in spec.env.items()):
        raise ProcessContractError("ENV_POLICY_INVALID", "env")
    forbidden_env = {"HTTP_PROXY","HTTPS_PROXY","ALL_PROXY","NO_PROXY","OPENAI_API_KEY","ANTHROPIC_API_KEY","OPENCLAW_TOKEN"}
    if forbidden_env & set(spec.env):
        raise ProcessContractError("ENV_FORBIDDEN_SECRET_OR_PROXY", ",".join(sorted(forbidden_env & set(spec.env))))
    roots = [Path(a).resolve() for a in allowed_roots] + [Path(transaction_root).resolve()]
    if package_authority is not None:
        from critical_apply_package_authority import authorized_package_roots
        roots.extend(root.resolve() for root in authorized_package_roots(package_authority, require_enabled=True))
    for p in (exe, Path(spec.cwd), Path(spec.stdout_path), Path(spec.stderr_path)):
        _reject_forbidden_path(p, roots, package_authority=package_authority)
    cwd = Path(spec.cwd).resolve(strict=True)
    if not cwd.is_dir():
        raise ProcessContractError("CWD_NOT_DIRECTORY", str(cwd))
    return identify_executable(exe, spec.expected_sha256, allow_script_interpreter=spec.allow_script_interpreter)


def create_apply_intent(transaction_root: Path, *, transaction_id: str, authority_envelope_sha256: str, approval_receipt_sha256: str, commit_revalidation_sha256: str, spec: ExactExecSpec, executable_identity: ExecutableIdentity, lock_set_digest: str, fencing_generation: int, observer_generation: int, actor_identity: Mapping[str, Any], boot_id: str | None = None) -> dict[str, Any]:
    root = Path(transaction_root).resolve(strict=True)
    (root/"receipts").mkdir(mode=0o700, exist_ok=True)
    intent = {
        "schema": APPLY_INTENT_SCHEMA,
        "transaction_id": transaction_id,
        "authority_envelope_sha256": authority_envelope_sha256,
        "approval_receipt_sha256": approval_receipt_sha256,
        "commit_revalidation_sha256": commit_revalidation_sha256,
        "exact_exec_spec": spec.to_json(),
        "executable_identity": executable_identity.to_json(),
        "argv_sha256": _sha_obj(list(spec.argv)),
        "environment_policy_sha256": _sha_obj(dict(spec.env)),
        "working_directory_identity": str(Path(spec.cwd).resolve()),
        "timeout_policy": {"execution_timeout_seconds": spec.timeout_seconds, "graceful_timeout_seconds": spec.graceful_timeout_seconds, "forced_timeout_seconds": spec.forced_timeout_seconds},
        "resource_policy": dict(spec.resource_limits or {}),
        "network_policy": "fixture_no_network",
        "process_isolation_policy": "new_session_process_group",
        "stdout_path": str(Path(spec.stdout_path).resolve()),
        "stderr_path": str(Path(spec.stderr_path).resolve()),
        "expected_blocked_child_mechanism": "fork_pipe_block_before_execve",
        "lock_set_digest": lock_set_digest,
        "fencing_generation": fencing_generation,
        "observer_generation": observer_generation,
        "actor_identity": dict(actor_identity),
        "wall_time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "monotonic_ns": time.monotonic_ns(),
        "boot_id": boot_id or read_boot_id(),
    }
    atomic_create_json(root/"receipts/apply-intent.json", intent, root=root)
    return intent


def spawn_blocked_child(transaction_root: Path, *, transaction_id: str, spec: ExactExecSpec, observer_generation: int, fencing_generation: int, lock_set_digest: str, allowed_roots: Sequence[Path]) -> BlockedChild:
    root = Path(transaction_root).resolve(strict=True)
    validate_exact_exec_spec(spec, transaction_root=root, allowed_roots=allowed_roots)
    outp = Path(spec.stdout_path).resolve(); errp = Path(spec.stderr_path).resolve()
    outp.parent.mkdir(mode=0o700, parents=True, exist_ok=True); errp.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    rfd, wfd = os.pipe2(os.O_CLOEXEC)
    outfd = os.open(outp, os.O_WRONLY|os.O_CREAT|os.O_TRUNC|getattr(os,"O_CLOEXEC",0)|getattr(os,"O_NOFOLLOW",0), 0o600)
    errfd = os.open(errp, os.O_WRONLY|os.O_CREAT|os.O_TRUNC|getattr(os,"O_CLOEXEC",0)|getattr(os,"O_NOFOLLOW",0), 0o600)
    pid = os.fork()
    if pid == 0:
        try:
            os.close(wfd)
            os.setsid()
            os.umask(spec.umask)
            os.chdir(spec.cwd)
            if spec.resource_limits:
                if "cpu_seconds" in spec.resource_limits:
                    resource.setrlimit(resource.RLIMIT_CPU, (int(spec.resource_limits["cpu_seconds"]), int(spec.resource_limits["cpu_seconds"])+1))
                if "file_size_bytes" in spec.resource_limits:
                    resource.setrlimit(resource.RLIMIT_FSIZE, (int(spec.resource_limits["file_size_bytes"]), int(spec.resource_limits["file_size_bytes"])))
            devnull = os.open(os.devnull, os.O_RDONLY)
            os.dup2(devnull, 0); os.dup2(outfd, 1); os.dup2(errfd, 2)
            for fd in range(3, 256):
                if fd == rfd: continue
                try: os.close(fd)
                except OSError: pass
            token = os.read(rfd, 1)
            if token != b"R":
                os._exit(125)
            os.execve(spec.executable, list(spec.argv), dict(spec.env))
        except BaseException:
            os._exit(126)
    os.close(rfd); os.close(outfd); os.close(errfd)
    time.sleep(0.02)
    pidfd = None; pidfd_opened = False
    if hasattr(os, "pidfd_open"):
        try:
            pidfd = os.pidfd_open(pid, 0); pidfd_opened = True
        except OSError:
            pidfd = None
    cg, cgi = _cgroup(pid)
    ident = ProcessIdentity(pid, read_start_ticks(pid), read_boot_id(), os.getpgid(pid), os.getsid(pid), _pid_namespace(pid), spec.executable, _sha_obj(list(spec.argv)), hasattr(os,"pidfd_open"), pidfd_opened, cg, cgi)
    receipt = {
        "schema": BLOCKED_CHILD_SCHEMA,
        "transaction_id": transaction_id,
        "apply_intent_sha256": sha256_file(root/"receipts/apply-intent.json") if (root/"receipts/apply-intent.json").exists() else None,
        **ident.to_json(),
        "current_child_state": "blocked_before_execve",
        "gate_mechanism": "parent_child_pipe_release_byte",
        "release_descriptor_identity": {"parent_fd": wfd, "cloexec": True},
        "observer_generation": observer_generation,
        "fencing_generation": fencing_generation,
        "lock_set_digest": lock_set_digest,
        "child_ready_acknowledgement": "process_exists_and_waiting_on_pipe",
        "target_marker_absent_before_release": True,
        "spawn_wall_time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "spawn_monotonic_ns": time.monotonic_ns(),
    }
    atomic_create_json(root/"receipts/apply-child-spawned-blocked.json", receipt, root=root)
    return BlockedChild(root, transaction_id, spec, ident, wfd, pidfd, outp, errp)


def verify_process_identity(identity: ProcessIdentity) -> bool:
    if read_boot_id() != identity.boot_id: return False
    try:
        if read_start_ticks(identity.pid) != identity.start_ticks: return False
        if os.getpgid(identity.pid) != identity.process_group_id: return False
        if os.getsid(identity.pid) != identity.session_id: return False
        if _pid_namespace(identity.pid) != identity.pid_namespace: return False
    except OSError:
        return False
    return True


def release_child(child: BlockedChild, *, approval_consumed_sha256: str, final_revalidation_sha256: str, observer_generation: int, fencing_generation: int) -> dict[str, Any]:
    if child.released:
        raise ProcessContractError("RELEASE_ALREADY_USED", child.transaction_id)
    if not verify_process_identity(child.identity):
        terminate_group(child.identity, signal.SIGKILL)
        raise ProcessContractError("CHILD_IDENTITY_MISMATCH_BEFORE_RELEASE", child.transaction_id)
    receipt = {
        "schema": MUTATION_RELEASE_SCHEMA,
        "transaction_id": child.transaction_id,
        "child_receipt_sha256": sha256_file(child.transaction_root/"receipts/apply-child-spawned-blocked.json"),
        "approval_consumed_sha256": approval_consumed_sha256,
        "final_revalidation_sha256": final_revalidation_sha256,
        "observer_generation": observer_generation,
        "fencing_generation": fencing_generation,
        "release_ordinal": 1,
        "release_mechanism": "pipe_byte_R",
        "release_wall_time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "release_monotonic_ns": time.monotonic_ns(),
        "boot_id": read_boot_id(),
    }
    atomic_create_json(child.transaction_root/"receipts/mutation-release.json", receipt, root=child.transaction_root)
    os.write(child.release_fd, b"R")
    os.close(child.release_fd)
    child.released = True
    return receipt


def terminate_group(identity: ProcessIdentity, sig: signal.Signals | int = signal.SIGTERM) -> bool:
    if not verify_process_identity(identity):
        return False
    os.killpg(identity.process_group_id, sig)
    return True


def enumerate_descendants(identity: ProcessIdentity) -> list[int]:
    tx_pgid = identity.process_group_id
    pids = []
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit(): continue
        pid = int(entry.name)
        try:
            if os.getpgid(pid) == tx_pgid:
                pids.append(pid)
        except OSError:
            pass
    return sorted(set(pids))


def wait_for_exit(child: BlockedChild, *, timeout_seconds: float | None = None, cancellation_state: str = "none") -> dict[str, Any]:
    deadline = time.monotonic() + (timeout_seconds if timeout_seconds is not None else child.spec.timeout_seconds)
    timed_out = False; status = None
    while True:
        try:
            pid, status = os.waitpid(child.identity.pid, os.WNOHANG)
        except ChildProcessError:
            pid = child.identity.pid; status = None; break
        if pid == child.identity.pid: break
        if time.monotonic() >= deadline:
            timed_out = True
            terminate_group(child.identity, signal.SIGTERM)
            time.sleep(child.spec.graceful_timeout_seconds)
            if enumerate_descendants(child.identity):
                try: terminate_group(child.identity, signal.SIGKILL)
                except Exception: pass
                time.sleep(child.spec.forced_timeout_seconds)
            try: pid, status = os.waitpid(child.identity.pid, 0)
            except ChildProcessError: pass
            break
        time.sleep(0.01)
    stdout_sha = sha256_file(child.stdout_file) if child.stdout_file.exists() else "0"*64
    stderr_sha = sha256_file(child.stderr_file) if child.stderr_file.exists() else "0"*64
    exit_code = None; sig = None; classification = "EXIT_UNKNOWN"
    if timed_out:
        classification = "TIMEOUT_KILLED"
    elif status is not None:
        if os.WIFEXITED(status):
            exit_code = os.WEXITSTATUS(status); classification = "EXIT_ZERO" if exit_code == 0 else "EXIT_NONZERO"
        elif os.WIFSIGNALED(status):
            sig = os.WTERMSIG(status); classification = "SIGNALLED"
    cleanup = {"descendants_after_cleanup": enumerate_descendants(child.identity)}
    receipt = {
        "schema": APPLY_EXIT_SCHEMA,
        "transaction_id": child.transaction_id,
        "child_identity": child.identity.to_json(),
        "observer_generation": None,
        "start_wall_time_utc": None,
        "release_wall_time_utc": None,
        "exit_observed_wall_time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "exit_observed_monotonic_ns": time.monotonic_ns(),
        "exit_code": exit_code,
        "signal": sig,
        "timeout_state": "timed_out" if timed_out else "not_timed_out",
        "cancellation_state": cancellation_state,
        "process_group_cleanup_state": "clean" if not cleanup["descendants_after_cleanup"] else "leaked",
        "descendant_cleanup_result": cleanup,
        "stdout_path": str(child.stdout_file), "stdout_sha256": stdout_sha, "stdout_bytes": child.stdout_file.stat().st_size if child.stdout_file.exists() else 0,
        "stderr_path": str(child.stderr_file), "stderr_sha256": stderr_sha, "stderr_bytes": child.stderr_file.stat().st_size if child.stderr_file.exists() else 0,
        "resource_usage": {},
        "journal_sequence": None,
        "execution_classification": classification,
    }
    atomic_replace_json(child.transaction_root/"receipts/apply-exit.json", receipt, root=child.transaction_root)
    return receipt
