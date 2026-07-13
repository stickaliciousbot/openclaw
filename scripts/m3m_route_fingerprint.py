#!/usr/bin/env python3
"""Canonical route/provider/fallback fingerprint helper for UMC M3M soak validation.

This helper intentionally separates:
- production_config_sha256: full config drift evidence; and
- route_provider_fallback_sha256: canonical route/model/fallback drift evidence.

All M3M preflight/checkpoint/closeout validators must call this helper so field shape cannot diverge.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

SCHEMA = "umc.v1.route_provider_fallback_fingerprint.v1"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path | str) -> str:
    p = Path(path)
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json_bytes(obj: Any) -> bytes:
    """Stable JSON canonicalization used for every fingerprint hash."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _normalize_model(value: Any) -> Optional[str]:
    """Explicit missing/null handling: missing and null both canonicalize to None."""
    if value is None:
        return None
    if isinstance(value, str):
        v = value.strip()
        return v or None
    return str(value).strip() or None


def _normalize_fallbacks(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        v = value.strip()
        return [v] if v else []
    if isinstance(value, Iterable):
        out: List[str] = []
        for item in value:
            normalized = _normalize_model(item)
            if normalized is not None:
                out.append(normalized)
        return out
    normalized = _normalize_model(value)
    return [normalized] if normalized is not None else []


def canonical_fingerprint_from_config(config: Mapping[str, Any]) -> Tuple[Dict[str, Any], str]:
    agents = config.get("agents") if isinstance(config.get("agents"), Mapping) else {}
    defaults = agents.get("defaults") if isinstance(agents.get("defaults"), Mapping) else {}
    model = defaults.get("model") if isinstance(defaults.get("model"), Mapping) else {}

    default_model = _normalize_model(model.get("primary"))
    fallback_models = _normalize_fallbacks(model.get("fallbacks"))

    route_model_config = {
        "default_model": default_model,
        "fallback_models": fallback_models,
    }
    route_model_config_sha256 = sha256_bytes(canonical_json_bytes(route_model_config))

    fingerprint: Dict[str, Any] = {
        "schema": SCHEMA,
        "default_model": default_model,
        "fallback_models": fallback_models,
        "route_model_config_sha256": route_model_config_sha256,
    }
    return fingerprint, sha256_bytes(canonical_json_bytes(fingerprint))


def canonical_fingerprint_from_config_file(config_path: Path | str) -> Dict[str, Any]:
    path = Path(config_path)
    config = json.loads(path.read_text())
    fingerprint, route_hash = canonical_fingerprint_from_config(config)
    return {
        "production_config_sha256": sha256_path(path),
        "route_provider_fallback_fingerprint": fingerprint,
        "route_provider_fallback_sha256": route_hash,
    }


def compare_fingerprints(preflight: Mapping[str, Any], checkpoint: Mapping[str, Any]) -> Dict[str, Any]:
    pre_fp = preflight.get("route_provider_fallback_fingerprint")
    chk_fp = checkpoint.get("route_provider_fallback_fingerprint")
    pre_hash = preflight.get("route_provider_fallback_sha256")
    chk_hash = checkpoint.get("route_provider_fallback_sha256")
    pre_config = preflight.get("production_config_sha256")
    chk_config = checkpoint.get("production_config_sha256")
    shape_parity = isinstance(pre_fp, Mapping) and isinstance(chk_fp, Mapping) and sorted(pre_fp.keys()) == sorted(chk_fp.keys())
    hash_match = pre_hash == chk_hash
    config_match = pre_config == chk_config
    return {
        "shape_parity": shape_parity,
        "hash_match": hash_match,
        "production_config_hash_match": config_match,
        "production_config_drift": not config_match,
        "route_provider_fallback_drift": shape_parity and not hash_match,
        "validator_shape_mismatch": not shape_parity,
        "preflight_keys": sorted(pre_fp.keys()) if isinstance(pre_fp, Mapping) else None,
        "checkpoint_keys": sorted(chk_fp.keys()) if isinstance(chk_fp, Mapping) else None,
        "preflight_hash": pre_hash,
        "checkpoint_hash": chk_hash,
    }


if __name__ == "__main__":
    import sys
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/home/stickai/.openclaw/openclaw.json")
    print(json.dumps(canonical_fingerprint_from_config_file(target), indent=2, sort_keys=True))
