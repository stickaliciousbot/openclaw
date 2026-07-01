# Lesson Learned — Work Lifecycle Ledger redaction and sidecar state

Date: 2026-07-01 AEST
Classification: `WORK_LIFECYCLE_M0_REDACTION_REPAIR_LESSON`

## What happened

During M0 contract/bootstrap for the Work Lifecycle Ledger, I created a sidecar run record at:

- `state/work-lifecycle/runs/work_20260701T043800Z_lifecycle_ledger_m0.json`

The first version stored the raw Telegram direct chat id in `chat_id` and a Telegram-shaped raw turn marker in `user_turn_id`.

That violated the spirit of the new lifecycle contract: lifecycle evidence and notification artifacts must not expose raw private identifiers. The contract explicitly requires secret/private identifier redaction for user-visible notices, and sidecar validation artifacts should follow the same discipline because they may be copied into notebooks, GitHub commits, or recovery bundles.

## Impact

- No external send or GitHub push had occurred yet.
- The raw id existed briefly in local sidecar state and a readback tool result during the same session.
- No Gateway/runtime/config/provider/route mutation occurred.

## Repair

- Replaced raw chat id with `telegram:direct:sha256-redacted` marker.
- Replaced raw turn marker with `telegram:turn:sha256-redacted` marker.
- Appended event `evt_20260701T045300Z_redaction_repair` to:
  - `state/work-lifecycle/events/work_20260701T043800Z_lifecycle_ledger_m0.jsonl`
- Updated M0 gate/summary classification to:
  - `WORK_LIFECYCLE_M0_CONTRACT_LOCAL_PASS_REDACTION_REPAIRED_PUSH_PENDING`
- Added `M0_G6_REDACTION_READBACK` as `PASS_AFTER_REPAIR`.

## Durable rule

Treat lifecycle sidecar state, validation mirrors, notebooks, and GitHub-bound artifacts as potentially exposed operator evidence.

Therefore:

1. Do not write raw chat ids, account ids, message/turn ids, tokens, auth headers, or private identifiers into lifecycle evidence artifacts.
2. Use hashed/redacted markers in repo-bound state and validation artifacts.
3. Keep reversible mappings only in approved runtime-private storage if a later implementation genuinely needs them.
4. Add redaction readback as an explicit gate before milestone closeout.

## Future implementation implication

M1/M2 schemas and store tests should include redaction-focused fixtures before any production hook exists. M4 notifier tests should treat redaction as a hard failure gate, not a formatting nicety.
