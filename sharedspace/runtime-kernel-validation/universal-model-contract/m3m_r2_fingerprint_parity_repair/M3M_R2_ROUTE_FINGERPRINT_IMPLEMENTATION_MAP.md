# M3M R2 Route Fingerprint Implementation Map

Status: `M3M_R2_ROUTE_FINGERPRINT_IMPLEMENTATION_MAP_COMPLETE`

## Failed R2 mismatch

- Preflight: `scripts/m3m_r2_preflight_and_bounds.py` hashed `config_sha256` plus `default_model`.
- Observer checkpoint: `scripts/m3m_r2_installed_shadow_soak_observer.py` hashed `config_sha256` only.
- Closeout validation later identified the shape mismatch, but the observer had already aborted fail-closed.

## Canonical decision

`default_model` is canonical and must be included everywhere. Fallback models are also canonical. Full production config hash remains a separate drift signal; route/provider/fallback fingerprint uses the model route subset.

## Repair

New helper: `scripts/m3m_route_fingerprint.py`.

Used by:

- `scripts/m3m_r2b_preflight_and_bounds.py`
- `scripts/m3m_r2b_installed_shadow_soak_observer.py`
- `scripts/m3m_r2_fingerprint_parity_fixtures.py`

This is a validator/harness bug only. Production config hash was unchanged and production routing semantics were not modified.
