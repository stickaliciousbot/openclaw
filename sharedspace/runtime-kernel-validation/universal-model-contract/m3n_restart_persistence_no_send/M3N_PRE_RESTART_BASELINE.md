# M3N Pre-Restart Baseline

Status: `PASS_M3N_PRE_RESTART_BASELINE_CAPTURED`

Scope: `M3N_PRE_RESTART_BASELINE_CAPTURE_ONLY`

## Dependency

- N0 artifact: `M3N_RESTART_PERSISTENCE_PREFLIGHT.json`
- N0 status: `PASS_M3N_RESTART_PERSISTENCE_PREFLIGHT`
- Stale M3M R2B `status.json`: `NON_AUTHORITATIVE_TERMINAL_CLOSEOUT_PRESENT`

## Baseline

- Gateway PID: `3063179`
- Gateway health: reachable/RPC OK
- Telegram health: ON/OK, accounts `1/1`
- Queue depth: `running=0`, `queued=0`, `resting=true`
- Old runner: present, SHA256 `6567099cf446f8675a00dd6a800b786013d0effbaae5c1b633d528272c0ab014`
- Required runtime chunk: present, SHA256 `e6ebc69bea65beefb20b3e118748ff1badcab76058816b11c5fe7ad35cfa4cf4`
- Zalo manifest: present, SHA256 `635c83aa3b28d07c85cf55257e084dd678fcbe9808bc2b76db19edadcc43dcb1`
- Zalouser manifest: present, SHA256 `03874c85b9a212217e25b55aeb75eed46f9252e56246d0b9b178176ccf823fae`
- Route/provider/fallback fingerprint SHA256: `0489015c7c22264b5d607ae18b88a2391a0bca8b4923b238a746d7087fd7e30c`
- Production config SHA256: `a4f0aac75704eb7d171e528c0486fd8baa95260450d38653aea5ba3226e2d859`
- Hook disabled by default: `true`
- Hook fixture active: `false`
- Hook fixture env: all `null`
- Rollback backups present: `true`
- Bounded fresh log scan: `PASS`, hits `0`

## Corrections applied during N1 validation

- Initial baseline collector recorded PID `104070`, which was the collector shell, not Gateway.
- Correct Gateway PID is `3063179`, visible in the same N1 process scan and in `M3M_R2B_CHECKPOINT_0024.json`.
- Initial manifest path probe guessed `/dist/zalo/manifest.json` and `/dist/zalouser/manifest.json`; those guessed paths were non-authoritative.
- Canonical installed manifest presence/hash readback comes from `M3M_R2B_CHECKPOINT_0024.installed`.

## Safety counters

All required safety counters remain zero:

- Provider/model live shadow execution: `0`
- Telegram sends caused by shadow: `0`
- External sends: `0`
- Real write tools: `0`
- Memory mutation: `0`
- Context Bridge mutation: `0`
- Production config mutation: `0`
- Route/fallback mutation: `0`
- Would-be HOLD/FAIL: `0`

## Boundary confirmation

No Gateway restart was performed in N1. No sends, provider calls, package install, tarball apply, runtime/config mutation, route mutation, memory mutation, Context Bridge mutation, M3O, M4, or enforcement occurred.

Exact next phase: `M3N_GATEWAY_RESTART_RESULT`.
