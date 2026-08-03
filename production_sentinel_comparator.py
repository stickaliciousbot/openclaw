#!/usr/bin/env python3
"""Isolated production sentinel comparator candidate.

Compares only authoritative protected semantic and identity fields.
Observation metadata (labels, timestamps, schema/format fields, ordering) is not
part of equality. Unknown top-level authoritative keys fail closed unless
allowlisted by the caller.
"""
from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from typing import Any

METADATA_KEYS = {
    "schema",
    "label",
    "utc",
    "generated_utc",
    "created_utc",
    "updated_utc",
    "started_utc",
    "finished_utc",
    "checked_utc",
    "captured_utc",
}
ENTRY_AUTHORITATIVE_FIELDS = ("exists", "sha256", "size", "path", "realpath", "dev", "ino", "uid", "gid", "mode")
ALLOWED_TOP_LEVEL_SCALARS = {"package_exists"}


class SentinelComparatorError(ValueError):
    """Malformed or unsupported sentinel input."""


@dataclass(frozen=True)
class SentinelComparison:
    status: str
    protected_match: bool
    authoritative_digest_pre: str
    authoritative_digest_post: str
    authoritative_pre: dict[str, Any]
    authoritative_post: dict[str, Any]
    changes: list[dict[str, Any]]
    ignored_metadata_keys: list[str]

    @property
    def abort(self) -> bool:
        return not self.protected_match


def _stable_digest(obj: Any) -> str:
    import hashlib
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _validate_entry(key: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SentinelComparatorError(f"sentinel entry {key!r} must be an object")
    allowed = set(ENTRY_AUTHORITATIVE_FIELDS)
    unknown = sorted(set(value) - allowed - METADATA_KEYS)
    if unknown:
        raise SentinelComparatorError(f"sentinel entry {key!r} has unsupported fields: {unknown}")
    if "exists" not in value:
        raise SentinelComparatorError(f"sentinel entry {key!r} missing authoritative field: exists")
    if value.get("exists") is True:
        for field in ("sha256", "size"):
            if field not in value:
                raise SentinelComparatorError(f"sentinel entry {key!r} missing authoritative field: {field}")
    return {field: copy.deepcopy(value[field]) for field in ENTRY_AUTHORITATIVE_FIELDS if field in value}


def authoritative_projection(sentinel: Any, *, allowed_added_keys: set[str] | None = None) -> dict[str, Any]:
    if not isinstance(sentinel, dict):
        raise SentinelComparatorError("sentinel must be an object")
    allowed_added_keys = allowed_added_keys or set()
    projected: dict[str, Any] = {}
    for key, value in sentinel.items():
        if key in METADATA_KEYS or key.endswith("_utc"):
            continue
        if isinstance(value, dict):
            projected[key] = _validate_entry(key, value)
        elif key in ALLOWED_TOP_LEVEL_SCALARS or key in allowed_added_keys:
            projected[key] = copy.deepcopy(value)
        else:
            raise SentinelComparatorError(f"unsupported top-level authoritative field: {key!r}")
    return projected


def compare_production_sentinels(pre: Any, post: Any, *, allowed_added_keys: set[str] | None = None) -> SentinelComparison:
    pre_proj = authoritative_projection(pre, allowed_added_keys=allowed_added_keys)
    post_proj = authoritative_projection(post, allowed_added_keys=allowed_added_keys)
    changes: list[dict[str, Any]] = []
    for key in sorted(set(pre_proj) | set(post_proj)):
        if pre_proj.get(key) != post_proj.get(key):
            changes.append({"path": key, "pre": pre_proj.get(key), "post": post_proj.get(key)})
    ignored = sorted(k for k in set(pre if isinstance(pre, dict) else {}) | set(post if isinstance(post, dict) else {}) if k in METADATA_KEYS or str(k).endswith("_utc"))
    match = not changes
    return SentinelComparison(
        status="PASS" if match else "ABORT",
        protected_match=match,
        authoritative_digest_pre=_stable_digest(pre_proj),
        authoritative_digest_post=_stable_digest(post_proj),
        authoritative_pre=pre_proj,
        authoritative_post=post_proj,
        changes=changes,
        ignored_metadata_keys=ignored,
    )


def legacy_compare(pre: Any, post: Any) -> bool:
    return pre == post
