# M3M R2 Canonical Route Fingerprint Contract

Status: `M3M_R2_CANONICAL_ROUTE_FINGERPRINT_CONTRACT_DEFINED`

Helper: `scripts/m3m_route_fingerprint.py`.

Canonical route/provider/fallback fingerprint fields:

- `schema`
- `default_model`
- `fallback_models`
- `route_model_config_sha256`

`production_config_sha256` is recorded separately and still aborts on drift, but it is not used to hide or weaken route/provider/fallback drift.

## Default model

`default_model` is canonical and included everywhere. Missing and null canonicalize to `null`; empty strings canonicalize to `null`.

## Fallbacks

`fallback_models` is canonical and included everywhere as an ordered array. Missing/null canonicalizes to `[]`.

## Hashing

Every caller uses stable JSON canonicalization: `sort_keys=True`, compact separators, UTF-8 bytes, SHA256.

## Drift comparison

- Shape parity is required before route drift classification.
- Shape mismatch is a validator/harness failure, not production route drift unless production config also changed.
- Real `default_model`, provider, fallback, or model-route config changes still produce route/provider/fallback drift.
- Full production config drift is reported and aborts separately.
