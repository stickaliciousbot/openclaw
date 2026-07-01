# Lesson Learned — Work Lifecycle Ledger closeout summary JSON edit pattern

Date: 2026-07-01 AEST
Classification: `WORK_LIFECYCLE_CLOSEOUT_SUMMARY_JSON_EDIT_REPAIR_LESSON`

## What happened

During Work Lifecycle Ledger closeout metadata updates, the same precise-edit pattern twice introduced malformed JSON in milestone summary files:

- M4: malformed `summary.json` caused the closeout preservation command to fail safely at JSON parse.
- M5: malformed `summary.json` was caught by manual readback before running the closeout preservation command.

The bad shape was an accidental `}, {` inserted after the `OWNER_GITHUB_PUSH_BEFORE_NEXT_MILESTONE` gate field.

## Impact

- No runtime/Gateway/config/service mutation occurred.
- M4 closeout preservation failed safely before staging/commit/push.
- M5 was repaired before the preservation command ran.
- The issue was limited to validation evidence JSON files.

## Repair

- Repaired each `gates` object to valid JSON.
- Added event-log entries documenting the repair.
- Added this lesson so future closeout metadata updates avoid repeating the edit pattern.

## Durable rule

After any exact-text edit to JSON evidence, especially around object/array boundaries, perform a JSON parse/readback before staging or preservation. Prefer rewriting small JSON evidence files whole over surgical edits when modifying adjacent braces/commas.

## Future implementation implication

M6+ closeout metadata generation should use structured JSON writers or scripts instead of manual string edits for status/classification/githubPreservation updates.
