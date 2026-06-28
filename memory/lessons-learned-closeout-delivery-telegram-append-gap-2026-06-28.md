# Lessons learned — Closeout delivery Telegram append gap (2026-06-28)

## Classification

`CLOSEOUT_DELIVERY_CONTRACT_PRODUCTION_HEALTH_PASS_TELEGRAM_APPEND_GAP`

## What happened

A production-compatible, patch-only closeout-delivery backport was installed over `openclaw@2026.5.7` using the validated artifact:

- `/tmp/openclaw-closeout-delivery-57-pack/openclaw-2026.5.7.tgz`
- SHA256 `9ffa4cafda8b1185b09cebb7905a063c3851d8f83d74abfee9017dcf18a1e616`

The Gateway health-gated restart passed even though `openclaw gateway restart` returned code `1`; this matched the already-known restart-wrapper false-negative class. Runtime stayed `OpenClaw 2026.5.7 (5c3a327)`, Gateway moved to PID `46341`, connectivity/admin/log/marker gates passed, and rollback was not performed.

The definitive current Telegram direct-turn smoke emitted a closeout payload via tool result in direct session line `2246`:

- title `TELEGRAM_DIRECT_CLOSEOUT_PROJECTOR_SMOKE_20260628T0700Z`
- `closeoutDelivered:false`
- `closeoutPending:true`

The normal final report delivered, but the runtime did not append a formatted source-visible closeout summary after it. Source-visible formatted summary count after the payload was `0`; duplicate count was also `0`.

## Key lesson

A closeout payload reaching the direct-session transcript is not sufficient proof that the source-visible closeout projector appended the summary. Future validation must inspect the post-tool-result source-visible assistant text and count formatted closeout summaries after the normal final report.

## Diagnostic boundary

When health gates pass and this failure class appears, do **not** rollback, reinstall, restart, or broaden Telegram changes. Diagnose only:

1. direct-chat closeout append projector path,
2. direct-session/source-reply routing,
3. pending closeout delivery handoff/clearing.

Keep unrelated Gateway config, route/cache/artifact-memory/runtime-authority, service PATH/systemd, and Telegram-wide behavior unchanged unless separately approved.

## Evidence

- Evidence note: `sharedspace/runtime-kernel-validation/closeout-delivery-production-apply/CLOSEOUT_DELIVERY_CONTRACT_PRODUCTION_HEALTH_PASS_TELEGRAM_APPEND_GAP_20260628.md`
- Evidence note SHA256: `2b9dd9d2adee5f7687de9bbe53172b157c4bf2202bfe56f85a940ce2c2ebb4f3`
- Preserved rollback backup: `backups/openclaw-global-closeout-delivery-57-20260628T055735Z.tar.gz`

## Recovery rule

The greenstate to preserve is:

- installed runtime: `OpenClaw 2026.5.7 (5c3a327)`
- installed package: `openclaw@2026.5.7`
- closeout backport artifact SHA verified
- Gateway running/admin-capable/connectivity OK
- memory and context bridge know the final classification
- production artifact retained
- rollback not performed
- next work limited to direct Telegram closeout append/session routing
