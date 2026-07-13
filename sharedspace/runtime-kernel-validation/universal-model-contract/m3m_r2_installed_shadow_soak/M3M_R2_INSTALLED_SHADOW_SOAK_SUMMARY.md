# M3M R2 Installed Observe-Only Shadow Soak Summary

Status: `FAIL_M3M_R2_INSTALLED_SHADOW_SOAK_ABORTED`

R2 preflight passed, bounds were written for 12h / 24 checkpoints / 30-minute cadence / hard stop, and the detached observer launched. The run aborted fail-closed at checkpoint 0001 with `FAIL_M3M_R2_ROUTE_PROVIDER_FALLBACK_DRIFT`.

Checkpoint 0001 showed Gateway reachable/RPC OK, Telegram ON/OK accounts 1/1, queue queued=0/running=0, installed/package hashes present, manifests present with expected hashes, logs clean, shadow/live send/mutation counters zero, and rollback backups present.

Classification: `VALIDATION_IMPLEMENTATION_FALSE_DRIFT_ABORT`. The production config hash was unchanged from preflight, but the observer hashed a different route fingerprint shape than preflight, producing a false route/provider/fallback drift abort. This is not a PASS and does not unlock M3N.

Next: `HOLD_M3M_R2_REPAIR_ROUTE_FINGERPRINT_VALIDATOR_AND_RERUN_R2; do not start M3N`.
