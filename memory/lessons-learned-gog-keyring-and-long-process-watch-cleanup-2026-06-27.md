# Lessons learned — gog keyring wrapper stale blob + long-process stale registry cleanup — 2026-06-27

## 1. gog keyauth wrapper can fail even when OAuth and live keyring are healthy

### Symptom

`gog` OAuth/keyring appeared healthy through the live Gateway environment, but the keyauth wrapper path failed with:

```text
read token for stickaliciousbot@gmail.com: read token: aes.KeyUnwrap(): integrity check failed.
```

### Root cause

The encrypted wrapper blob at `state/secrets/gog-keyring-password.enc.json` was stale/wrong. The wrapper correctly decrypted a value, but that value was no longer the password that could unwrap gog's file-keyring token. The current inherited `GOG_KEYRING_PASSWORD` in the Gateway environment was the valid one.

This is the inverse of the earlier 2026-06-03 failure where the inherited env was stale and the encrypted wrapper was the repair. The durable rule is therefore: neither inherited env nor the encrypted blob is automatically authoritative; verify the actual gog command path.

### Safe repair pattern

- Do not print, log, or store the secret in memory/chat.
- Confirm wrapper decrypts with `python3 scripts/gog_keyring_secret.py verify`.
- Confirm the failing path using `python3 scripts/gog_keyring_secret.py run -- gog auth list --no-input`.
- If the inherited env is known-good, reseal the encrypted blob from that env without printing it.
- Verify all three gates:
  - `python3 scripts/gog_keyring_secret.py verify`
  - `python3 scripts/gog_keyring_secret.py run -- gog auth list --no-input`
  - `bash scripts/gmail_auth_health_check.sh`

### 2026-06-27 fix evidence

- Resealed blob from known-good env without printing the secret.
- Wrapper verify changed from stale secret length 7 to current secret length 10.
- Wrapper `gog auth list --no-input` passed for `stickaliciousbot@gmail.com` with `calendar,gmail` OAuth.
- `scripts/gmail_auth_health_check.sh` passed live Gmail read probe.

## 2. Long-process watcher stale registry row can keep alerting after terminal PASS

### Symptom

Repeated alert:

```text
LONG_PROCESS_WATCH_STALE
token_broker_vmesh_18840_m12_c1r10r pid_missing
```

### Root cause

`state/long-process-watch/registry.json` still contained PID registration `token_broker_vmesh_18840_m12_c1r10r` even though the run's status artifact was already terminal PASS:

`M12_C1R10R_PROVIDER_PATH_TOKEN_BROKER_READINESS_REPAIR_PASS`

The PID was gone, so every watcher check classified the stale registry row as `pid_missing`. `long_process_watch.py dismiss` returned `DISMISS_MISS` because it dismisses pending completion notices, not raw registry rows.

### Safe cleanup pattern

- Read the registered status artifact first.
- Only remove the registry row if the artifact status is terminal/PASS or otherwise owner-closed.
- Do not dismiss/delete active RUNNING rows just because a PID is missing.
- After cleanup, verify:
  - `python3 scripts/long_process_watch.py check` returns `WATCH_OK`
  - `state/long-process-watch/last-check.json` has `ok: true` and `stale: []`

### 2026-06-27 fix evidence

- Confirmed status artifact `sharedspace/runtime-kernel-validation/vnext-semantic-gate/m12_c1r10r_provider_path_token_broker_readiness_repair/status.json` was terminal PASS.
- Removed only registry id `token_broker_vmesh_18840_m12_c1r10r`.
- Verified `WATCH_OK`; registry is empty; `last-check.json` has `ok: true`, `stale: []`.
