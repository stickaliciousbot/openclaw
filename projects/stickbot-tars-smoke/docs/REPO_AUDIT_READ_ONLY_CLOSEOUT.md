# Stickbot TARS Read-only Repo Audit Closeout

Generated: 2026-07-02T03:03:00Z / 2026-07-02 13:03 AEST

## Final classification

`STICKBOT_TARS_REPO_AUDIT_READ_ONLY_COMPLETE`

## Completed approved audits

- `9c48a2eb-97e4-4efb-a6c5-76264d4b0c7c` / session `tender-cedar` / exit `0`
  - Initial read-only audit.
  - Final marker: `REPO_AUDIT_READONLY_COMPLETE`.
- `e34313ae-e260-432c-ae5a-806379d3be11` / session `briny-canyon` / exit `0`
  - Refined read-only TARS audit plus non-executed branch/separation proposal.
  - Final marker: `STICKBOT_TARS_REPO_AUDIT_READ_ONLY_COMPLETE`.

## Safety assertions

The approved audit phase was read-only:

- No file remediation.
- No deletes.
- No branch creation/switch.
- No staging.
- No commit.
- No force-push.
- No OpenClaw production/runtime/config/routing/default/fallback mutation.
- No M3 model acquisition/load.

## Current hardening state

Current M2.5 artifact:

- `projects/stickbot-tars-smoke/docs/m25-hardening-closeout/m25-hardening-closeout.json`

Current classification:

`STICKBOT_TARS_M25_HARDENING_CLOSEOUT_BLOCKED_FAIL_CLOSED`

Known failed M2.5 gates:

- `configFailClosedImplemented`
- `unsafeLanRefusesStartup`
- `uuidOnlyAudioRoute`
- `separateAudioLimitExists`
- `originHostCsrfChecksExist`

`npm run check` previously passed, but that does not satisfy the missing hardening gates.

## Production/OpenClaw runtime readback

Observed during approved audit:

- `/home/stickai/.openclaw/openclaw.json` exists, mode `600`, bytes `27481`, mtime `2026-07-02 11:20:40.560128383 +1000`.
- `/home/stickai/.openclaw/restart-sentinel.json` was missing.

This readback is evidence only; no production mutation was performed.

## Clean branch proposal

Preferred branch:

`feature/stickbot-tars-m25-hardening-repair`

Alternate branch:

`m25/stickbot-tars-hardening-failclosed-repair`

Status: proposed only, not executed.

## Artifact placement decision

Keep these in memory/context bridge:

- `memory/context-bridge-events/*stickbot-tars*.json`
- Daily memory lines/summaries mentioning Stickbot TARS / TARS / XTTS / voice demo

Keep project-local evidence here:

- `projects/stickbot-tars-smoke/docs/**`
- `projects/stickbot-tars-smoke/state/**`

Do not commit runtime blobs:

- `projects/stickbot-tars-smoke/data/audio/**`
- `projects/stickbot-tars-smoke/data/traces/**`
- `projects/stickbot-tars-smoke/models/**`
- `projects/stickbot-tars-smoke/xtts_models/**`
- `projects/stickbot-tars-smoke/.venv/**`
- `projects/stickbot-tars-smoke/node_modules/**`
- `projects/stickbot-tars-smoke/cache/**`

## Next allowed work

Only after explicit write-phase approval:

1. Create/switch to `feature/stickbot-tars-m25-hardening-repair`.
2. Stage only explicit TARS project files and project-local audit/repair artifacts.
3. Repair M2.5 blockers only.
4. Run validation gates.
5. Write M2.5 repair closeout.

## Stop condition

No M3 until:

`STICKBOT_TARS_M25_HARDENING_CLOSEOUT_PASS_READY_FOR_M3`
