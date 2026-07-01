# Lesson Learned — Work Lifecycle Ledger redaction test fixture hygiene

Date: 2026-07-01 AEST
Classification: `WORK_LIFECYCLE_M4_REDACTION_FIXTURE_REPAIR_LESSON`

## What happened

During Work Lifecycle Ledger M4 focused validation, the first M4 command passed the notifier tests but failed the repo-bound redaction scan:

- Validation command id: `ea3f4c2c-d169-471e-9177-7db809ef79fa`
- Tests: 7
- Passed: 7
- Failed: 0
- Redaction scan: failed on `src/work-lifecycle/work-notifier.test.mjs`

Root issue: the test fixture used a raw Telegram-shaped identifier while testing notification redaction.

The notifier redacted output correctly, but the source test file itself was repo-bound evidence and therefore must not contain raw private identifiers.

## Repair

- Replaced the raw Telegram-shaped fixture value with non-sensitive sentinel `123456789`.
- Preserved the redaction assertion against the sentinel and secret-like string.
- Re-ran validation:
  - Command id: `bdd3e44b-7012-4117-9035-9591e3620642`
  - Tests: 7
  - Passed: 7
  - Failed: 0
  - `M4_REDACTION_SCAN_PASS`
  - `M4_FOCUSED_VALIDATION_PASS_AFTER_REPAIR`

## Durable rule

Redaction tests must use synthetic sentinel values, not real raw identifiers. Repo-bound tests, fixtures, notebooks, validation summaries, and failure records are evidence artifacts and must obey the same no-raw-ID policy as production logs and notifications.

## Future implementation implication

M8 failure-injection fixtures should include fake secret/id sentinel values only. If testing detection of realistic formats, use deterministic synthetic examples that cannot identify a real chat/user/account/session.
