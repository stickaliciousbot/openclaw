#!/usr/bin/env python3
"""Critical Apply production package authority contracts.

This module is source/fixture prep only. It does not apply packages, restart
Gateway, mutate config/cron, call providers, or grant authority by default.
It defines the narrow data contract required before exact-exec may touch package
roots that are forbidden in fixture mode.
"""
from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from critical_apply_contracts import ContractError, canonical_json_dumps, is_sha256

PACKAGE_AUTHORITY_SCHEMA = "critical_apply.package_apply_authority.v1"
PACKAGE_TRANSACTION_SPEC_SCHEMA = "critical_apply.package_apply_transaction_spec.v1"
PACKAGE_AUTHORITY_CONTRACT_SCHEMA = "critical_apply.package_apply_authority_contract.v1"

DEFAULT_PRODUCTION_PACKAGE_ROOTS = tuple(Path(p) for p in (
    "/home/stickai/.npm-global/lib/node_modules/openclaw",
    "/home/stickai/.npm-global/bin/openclaw",
))

BROAD_PACKAGE_ROOTS = tuple(Path(p) for p in (
    "/",
    "/usr",
    "/usr/local",
    "/home",
    "/home/stickai",
    "/home/stickai/.npm-global",
    "/home/stickai/.npm-global/lib",
    "/home/stickai/.npm-global/lib/node_modules",
    "/home/stickai/.npm-global/bin",
))

FORBIDDEN_SIDE_EFFECT_COUNTERS = (
    "gateway_restart_actions",
    "gateway_config_or_cron_mutations",
    "provider_or_live_smoke_calls",
    "systemctl_restart_actions",
    "systemctl_start_stop_actions",
)


class PackageAuthorityError(ContractError):
    pass


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def canonical_sha(obj: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_dumps(dict(obj)).encode()).hexdigest()


def _under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def _strict_abs(path_text: str, *, field: str) -> Path:
    path = Path(path_text)
    if not path.is_absolute():
        raise PackageAuthorityError(f"{field.upper()}_MUST_BE_ABSOLUTE", path_text)
    if ".." in path.parts:
        raise PackageAuthorityError(f"{field.upper()}_MUST_NOT_CONTAIN_PARENT_TRAVERSAL", path_text)
    return path


def package_authority_contract() -> Mapping[str, Any]:
    return {
        "schema": PACKAGE_AUTHORITY_CONTRACT_SCHEMA,
        "component": "critical_apply_package_authority",
        "default_state": "disabled",
        "fixture_mode_package_roots_forbidden": True,
        "production_mode_requires_explicit_authority": True,
        "production_mode_requires_exact_target_roots": True,
        "production_mode_rejects_broad_package_roots": True,
        "production_mode_requires_checksum_pinned_package": True,
        "production_mode_requires_restore_point": True,
        "production_mode_requires_rollback_plan": True,
        "production_mode_requires_independent_watcher": True,
        "production_mode_requires_maintenance_lock": True,
        "production_mode_forbids_gateway_config_cron_provider_side_effects": True,
        "default_allowed_package_roots": [str(p) for p in DEFAULT_PRODUCTION_PACKAGE_ROOTS],
        "broad_roots_rejected": [str(p) for p in BROAD_PACKAGE_ROOTS],
        "no_live_apply_in_contract_module": True,
    }


def package_transaction_spec_template(*, package_artifact_sha256: str, source_package_path: str, target_roots: Sequence[str], restore_point_id: str, restore_manifest_sha256: str, postcheck_sha256: str, rollback_plan_sha256: str) -> Mapping[str, Any]:
    return {
        "schema": PACKAGE_TRANSACTION_SPEC_SCHEMA,
        "transaction_type": "package_apply",
        "package_artifact_sha256": package_artifact_sha256,
        "source_package_path": source_package_path,
        "target_roots": list(target_roots),
        "restore_point_id": restore_point_id,
        "restore_manifest_sha256": restore_manifest_sha256,
        "rollback_plan_sha256": rollback_plan_sha256,
        "postcheck_sha256": postcheck_sha256,
        "max_primary_mutations": 1,
        "restart_authorised": False,
        "functional_smoke_authorised": False,
        "network_policy": "no_provider_or_live_smoke_during_package_apply",
        "forbidden_side_effect_counters": {name: 0 for name in FORBIDDEN_SIDE_EFFECT_COUNTERS},
    }


def validate_package_transaction_spec(spec: Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if spec.get("schema") != PACKAGE_TRANSACTION_SPEC_SCHEMA:
        reasons.append("schema_mismatch")
    if spec.get("transaction_type") != "package_apply":
        reasons.append("transaction_type_not_package_apply")
    for field in ("package_artifact_sha256", "restore_manifest_sha256", "rollback_plan_sha256", "postcheck_sha256"):
        if not is_sha256(str(spec.get(field, ""))):
            reasons.append(field + "_invalid_sha256")
    try:
        _strict_abs(str(spec.get("source_package_path", "")), field="source_package_path")
    except PackageAuthorityError as exc:
        reasons.append(exc.code.lower())
    target_roots = spec.get("target_roots")
    if not isinstance(target_roots, list) or not target_roots:
        reasons.append("target_roots_missing")
    else:
        for item in target_roots:
            try:
                root = _strict_abs(str(item), field="target_roots")
                if any(root.resolve() == broad.resolve() for broad in BROAD_PACKAGE_ROOTS):
                    reasons.append("target_root_too_broad:" + str(root))
            except PackageAuthorityError as exc:
                reasons.append(exc.code.lower())
    counters = spec.get("forbidden_side_effect_counters")
    if not isinstance(counters, dict):
        reasons.append("forbidden_side_effect_counters_missing")
    else:
        for name in FORBIDDEN_SIDE_EFFECT_COUNTERS:
            if counters.get(name) != 0:
                reasons.append("forbidden_counter_not_zero:" + name)
    if spec.get("max_primary_mutations") != 1:
        reasons.append("max_primary_mutations_must_equal_1")
    if spec.get("restart_authorised") is not False:
        reasons.append("package_apply_must_not_authorise_restart")
    if spec.get("functional_smoke_authorised") is not False:
        reasons.append("package_apply_must_not_authorise_functional_smoke")
    return not reasons, tuple(reasons)


def make_package_apply_authority(*, transaction_id: str, package_spec: Mapping[str, Any], authority_enabled: bool = False, maintenance_lock_path: str, independent_watcher_registration_path: str, restore_point_id: str, restore_manifest_sha256: str, owner: str = "fixture-owner-m8-r10") -> Mapping[str, Any]:
    return {
        "schema": PACKAGE_AUTHORITY_SCHEMA,
        "transaction_id": transaction_id,
        "owner": owner,
        "transaction_type": "package_apply",
        "authority_enabled": authority_enabled,
        "package_transaction_spec_sha256": canonical_sha(package_spec),
        "package_transaction_spec": dict(package_spec),
        "exact_target_roots": list(package_spec.get("target_roots", [])),
        "maintenance_lock": {
            "required": True,
            "lock_path": maintenance_lock_path,
        },
        "restore_point": {
            "required": True,
            "restore_point_id": restore_point_id,
            "restore_manifest_sha256": restore_manifest_sha256,
            "max_age_seconds": 3600,
        },
        "rollback": {
            "required": True,
            "rollback_plan_sha256": package_spec.get("rollback_plan_sha256"),
        },
        "independent_watcher": {
            "required": True,
            "registration_path": independent_watcher_registration_path,
        },
        "forbidden_side_effect_counters": dict(package_spec.get("forbidden_side_effect_counters", {})),
        "issued_wall_time_utc": utc_now(),
    }


def validate_package_apply_authority(authority: Mapping[str, Any], *, require_enabled: bool = True) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if authority.get("schema") != PACKAGE_AUTHORITY_SCHEMA:
        reasons.append("schema_mismatch")
    if authority.get("transaction_type") != "package_apply":
        reasons.append("transaction_type_not_package_apply")
    if require_enabled and authority.get("authority_enabled") is not True:
        reasons.append("authority_not_enabled")
    spec = authority.get("package_transaction_spec")
    if not isinstance(spec, dict):
        reasons.append("package_transaction_spec_missing")
    else:
        ok, spec_reasons = validate_package_transaction_spec(spec)
        if not ok:
            reasons.extend("spec:" + r for r in spec_reasons)
        if authority.get("package_transaction_spec_sha256") != canonical_sha(spec):
            reasons.append("package_transaction_spec_sha256_mismatch")
    exact_roots = authority.get("exact_target_roots")
    if not isinstance(exact_roots, list) or not exact_roots:
        reasons.append("exact_target_roots_missing")
    else:
        for item in exact_roots:
            try:
                root = _strict_abs(str(item), field="exact_target_roots")
                if any(root.resolve() == broad.resolve() for broad in BROAD_PACKAGE_ROOTS):
                    reasons.append("exact_target_root_too_broad:" + str(root))
            except PackageAuthorityError as exc:
                reasons.append(exc.code.lower())
    lock = authority.get("maintenance_lock")
    if not isinstance(lock, dict) or lock.get("required") is not True or not lock.get("lock_path"):
        reasons.append("maintenance_lock_required")
    else:
        try:
            _strict_abs(str(lock["lock_path"]), field="maintenance_lock.lock_path")
        except PackageAuthorityError as exc:
            reasons.append(exc.code.lower())
    restore = authority.get("restore_point")
    if not isinstance(restore, dict) or restore.get("required") is not True:
        reasons.append("restore_point_required")
    else:
        if not restore.get("restore_point_id"):
            reasons.append("restore_point_id_required")
        if not is_sha256(str(restore.get("restore_manifest_sha256", ""))):
            reasons.append("restore_manifest_sha256_invalid")
    rollback = authority.get("rollback")
    if not isinstance(rollback, dict) or rollback.get("required") is not True or not is_sha256(str(rollback.get("rollback_plan_sha256", ""))):
        reasons.append("rollback_plan_required")
    watcher = authority.get("independent_watcher")
    if not isinstance(watcher, dict) or watcher.get("required") is not True or not watcher.get("registration_path"):
        reasons.append("independent_watcher_required")
    else:
        try:
            _strict_abs(str(watcher["registration_path"]), field="independent_watcher.registration_path")
        except PackageAuthorityError as exc:
            reasons.append(exc.code.lower())
    counters = authority.get("forbidden_side_effect_counters")
    if not isinstance(counters, dict):
        reasons.append("forbidden_side_effect_counters_missing")
    else:
        for name in FORBIDDEN_SIDE_EFFECT_COUNTERS:
            if counters.get(name) != 0:
                reasons.append("forbidden_counter_not_zero:" + name)
    return not reasons, tuple(reasons)


def authorized_package_roots(authority: Mapping[str, Any], *, require_enabled: bool = True) -> tuple[Path, ...]:
    ok, reasons = validate_package_apply_authority(authority, require_enabled=require_enabled)
    if not ok:
        raise PackageAuthorityError("PACKAGE_AUTHORITY_INVALID", ",".join(reasons))
    return tuple(_strict_abs(str(p), field="exact_target_roots") for p in authority.get("exact_target_roots", []))


def path_authorized_by_package_authority(path: Path, authority: Mapping[str, Any] | None) -> bool:
    if authority is None:
        return False
    try:
        roots = authorized_package_roots(authority, require_enabled=True)
    except PackageAuthorityError:
        return False
    rp = path.resolve()
    return any(_under(rp, root) for root in roots)


if __name__ == "__main__":
    import json
    print(json.dumps(package_authority_contract(), sort_keys=True))
