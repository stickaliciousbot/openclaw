# M3N cron/agent job-source inventory

Status: `PASS_M3N_CRON_AGENT_JOB_SOURCE_INVENTORY_READY`

OpenClaw scheduler candidates: `26`.

## Daily Gmail action summary (7pm Sydney) (187cdfa9-7fd2-4bb7-8148-811247569066)
- source: `OpenClaw scheduler` enabled=`True` cadence=`cron 0 19 * * * tz=Australia/Sydney`
- last/next: `None` / `None` status=`None` duration_ms=`None`
- overlaps M3N liveness windows: `True`; event-loop correlation: `True`; getMe correlation: `False`
- safe to pause later with approval: `False`; required for M3N evidence: `False`; required for Gateway/Telegram health: `False`
- artifact root: `None`

## context-bridge:morning-sync-check (395199ad-5da5-4e66-a4ec-a5a462771914)
- source: `OpenClaw scheduler` enabled=`True` cadence=`cron 40 6 * * * tz=Australia/Sydney`
- last/next: `None` / `None` status=`None` duration_ms=`None`
- overlaps M3N liveness windows: `True`; event-loop correlation: `False`; getMe correlation: `False`
- safe to pause later with approval: `False`; required for M3N evidence: `False`; required for Gateway/Telegram health: `False`
- artifact root: `None`

## context-plus-semantic-shadow-pass-watch (b29e6275-9bad-4622-8a56-041e5a2dc864)
- source: `OpenClaw scheduler` enabled=`True` cadence=`every 300000ms`
- last/next: `None` / `None` status=`None` duration_ms=`None`
- overlaps M3N liveness windows: `True`; event-loop correlation: `True`; getMe correlation: `False`
- safe to pause later with approval: `True`; required for M3N evidence: `False`; required for Gateway/Telegram health: `False`
- artifact root: `script: scripts/context_plus_semantic_shadow_pass_watch_quiet.py; stdout-only watcher`

## memory-drift:daily-reconcile-plus-one-compact (bb4b1687-68ce-4735-b548-4ca2de076148)
- source: `OpenClaw scheduler` enabled=`True` cadence=`cron 50 6 * * * tz=Australia/Sydney`
- last/next: `None` / `None` status=`None` duration_ms=`None`
- overlaps M3N liveness windows: `True`; event-loop correlation: `True`; getMe correlation: `False`
- safe to pause later with approval: `False`; required for M3N evidence: `False`; required for Gateway/Telegram health: `False`
- artifact root: `None`

## Daily 6am repin Stickbot to gpt-5.5 for vNext-Mesh Semantic Gate (203069e0-3109-4ef2-bf01-baa97bb2f211)
- source: `OpenClaw scheduler` enabled=`True` cadence=`cron 0 6 * * * tz=Australia/Sydney`
- last/next: `None` / `None` status=`None` duration_ms=`None`
- overlaps M3N liveness windows: `False`; event-loop correlation: `False`; getMe correlation: `False`
- safe to pause later with approval: `False`; required for M3N evidence: `False`; required for Gateway/Telegram health: `False`
- artifact root: `None`

## Daily shared-state sync summary (dashboard + memory) (f31a76fb-1a4e-43a3-b32d-222bed3d9046)
- source: `OpenClaw scheduler` enabled=`True` cadence=`cron 30 6 * * * tz=Australia/Sydney`
- last/next: `None` / `None` status=`None` duration_ms=`None`
- overlaps M3N liveness windows: `False`; event-loop correlation: `False`; getMe correlation: `False`
- safe to pause later with approval: `False`; required for M3N evidence: `False`; required for Gateway/Telegram health: `False`
- artifact root: `None`

## Gmail hourly triage + fast follow-up (cb301445-7936-40ac-814e-6be606782f51)
- source: `OpenClaw scheduler` enabled=`False` cadence=`cron 0 * * * * tz=Australia/Sydney`
- last/next: `None` / `None` status=`None` duration_ms=`None`
- overlaps M3N liveness windows: `False`; event-loop correlation: `False`; getMe correlation: `False`
- safe to pause later with approval: `False`; required for M3N evidence: `False`; required for Gateway/Telegram health: `False`
- artifact root: `None`

## M20 post-production observation T+24h final closeout (72b92d09-602f-4649-9bd8-df7b91d3d4ce)
- source: `OpenClaw scheduler` enabled=`False` cadence=`at 2026-07-07T07:49:33.000Z`
- last/next: `None` / `None` status=`None` duration_ms=`None`
- overlaps M3N liveness windows: `False`; event-loop correlation: `False`; getMe correlation: `False`
- safe to pause later with approval: `False`; required for M3N evidence: `False`; required for Gateway/Telegram health: `False`
- artifact root: `None`

## M20 post-production observation T+2h checkpoint (8980885e-fc62-44e7-897f-ccc84e2f673c)
- source: `OpenClaw scheduler` enabled=`False` cadence=`at 2026-07-06T09:49:33.000Z`
- last/next: `None` / `None` status=`None` duration_ms=`None`
- overlaps M3N liveness windows: `False`; event-loop correlation: `False`; getMe correlation: `False`
- safe to pause later with approval: `False`; required for M3N evidence: `False`; required for Gateway/Telegram health: `False`
- artifact root: `None`

## M20 post-production observation T+8h checkpoint (4334fb16-e319-4ef2-a804-bb83c1eef22b)
- source: `OpenClaw scheduler` enabled=`False` cadence=`at 2026-07-06T15:49:33.000Z`
- last/next: `None` / `None` status=`None` duration_ms=`None`
- overlaps M3N liveness windows: `False`; event-loop correlation: `False`; getMe correlation: `False`
- safe to pause later with approval: `False`; required for M3N evidence: `False`; required for Gateway/Telegram health: `False`
- artifact root: `None`

## Morning Fabric DTB API diagnostics summary (f018a5c6-ea4f-4021-bfce-eccfa738692e)
- source: `OpenClaw scheduler` enabled=`False` cadence=`at 2026-06-12T22:00:00.000Z`
- last/next: `None` / `None` status=`None` duration_ms=`None`
- overlaps M3N liveness windows: `False`; event-loop correlation: `False`; getMe correlation: `False`
- safe to pause later with approval: `False`; required for M3N evidence: `False`; required for Gateway/Telegram health: `False`
- artifact root: `None`

## Nightly backup integrity check (post-backup) (28f44861-c79e-473f-8ce8-e210c98a43ae)
- source: `OpenClaw scheduler` enabled=`False` cadence=`cron 10 6 * * * tz=Australia/Sydney`
- last/next: `None` / `None` status=`None` duration_ms=`None`
- overlaps M3N liveness windows: `False`; event-loop correlation: `False`; getMe correlation: `False`
- safe to pause later with approval: `False`; required for M3N evidence: `False`; required for Gateway/Telegram health: `False`
- artifact root: `None`

## XR coordination watcher tick 17:34 AEST (128cd026-8809-41e3-8eeb-84ab5b962740)
- source: `OpenClaw scheduler` enabled=`False` cadence=`at 2026-06-09T07:34:00.000Z`
- last/next: `None` / `None` status=`None` duration_ms=`None`
- overlaps M3N liveness windows: `False`; event-loop correlation: `False`; getMe correlation: `False`
- safe to pause later with approval: `False`; required for M3N evidence: `False`; required for Gateway/Telegram health: `False`
- artifact root: `None`

## codex-cowork:morning-memory-watch (13adb9c2-9ce5-41eb-be54-16a99e1ea9b9)
- source: `OpenClaw scheduler` enabled=`True` cadence=`cron 30 8 * * * tz=Australia/Sydney`
- last/next: `None` / `None` status=`None` duration_ms=`None`
- overlaps M3N liveness windows: `False`; event-loop correlation: `False`; getMe correlation: `False`
- safe to pause later with approval: `False`; required for M3N evidence: `False`; required for Gateway/Telegram health: `False`
- artifact root: `None`

## context-bridge:daily-2am-reconcile (c8499a92-ed1e-43cf-bd34-0e8cb1547104)
- source: `OpenClaw scheduler` enabled=`True` cadence=`cron 0 6 * * * tz=Australia/Sydney`
- last/next: `None` / `None` status=`None` duration_ms=`None`
- overlaps M3N liveness windows: `False`; event-loop correlation: `False`; getMe correlation: `False`
- safe to pause later with approval: `False`; required for M3N evidence: `False`; required for Gateway/Telegram health: `False`
- artifact root: `None`

## gmail-auth:daily-7am-status (0f59aead-684e-47ca-bfca-6a63df11d85d)
- source: `OpenClaw scheduler` enabled=`True` cadence=`cron 0 7 * * * tz=Australia/Sydney`
- last/next: `None` / `None` status=`None` duration_ms=`None`
- overlaps M3N liveness windows: `False`; event-loop correlation: `False`; getMe correlation: `False`
- safe to pause later with approval: `False`; required for M3N evidence: `False`; required for Gateway/Telegram health: `False`
- artifact root: `None`

## live-app-runtime-codex-completion-monitor (1666ec17-27dc-484b-bca7-77a48dcfb1fc)
- source: `OpenClaw scheduler` enabled=`False` cadence=`every 1800000ms`
- last/next: `None` / `None` status=`None` duration_ms=`None`
- overlaps M3N liveness windows: `False`; event-loop correlation: `False`; getMe correlation: `False`
- safe to pause later with approval: `False`; required for M3N evidence: `False`; required for Gateway/Telegram health: `False`
- artifact root: `None`

## long-process-watch:every-50m (0d7d143c-5ed5-4a2d-886c-cbee8666c5c0)
- source: `OpenClaw scheduler` enabled=`True` cadence=`every 3000000ms`
- last/next: `None` / `None` status=`None` duration_ms=`None`
- overlaps M3N liveness windows: `False`; event-loop correlation: `False`; getMe correlation: `False`
- safe to pause later with approval: `False`; required for M3N evidence: `False`; required for Gateway/Telegram health: `False`
- artifact root: `None`

## m3m-r2b-early-abort-sentinel (5bd9c18f-98b0-44d4-a169-33e1f1af33de)
- source: `OpenClaw scheduler` enabled=`True` cadence=`every 1800000ms`
- last/next: `None` / `None` status=`None` duration_ms=`None`
- overlaps M3N liveness windows: `False`; event-loop correlation: `False`; getMe correlation: `False`
- safe to pause later with approval: `False`; required for M3N evidence: `False`; required for Gateway/Telegram health: `False`
- artifact root: `sharedspace/runtime-kernel-validation/universal-model-contract/m3m_r2b_installed_shadow_soak`

## memory-drift:post-compact-watchdog-main-escalator (486bc9e0-b5d4-4046-bd57-acd6b2e9f5ed)
- source: `OpenClaw scheduler` enabled=`True` cadence=`cron 10 7 * * * tz=Australia/Sydney`
- last/next: `None` / `None` status=`None` duration_ms=`None`
- overlaps M3N liveness windows: `False`; event-loop correlation: `False`; getMe correlation: `False`
- safe to pause later with approval: `False`; required for M3N evidence: `False`; required for Gateway/Telegram health: `False`
- artifact root: `None`

## memory-integrity:daily-silent-rollup (461cecb7-1b1c-41d5-a40d-33a66af0ca04)
- source: `OpenClaw scheduler` enabled=`True` cadence=`cron 20 6 * * * tz=Australia/Sydney`
- last/next: `None` / `None` status=`None` duration_ms=`None`
- overlaps M3N liveness windows: `False`; event-loop correlation: `False`; getMe correlation: `False`
- safe to pause later with approval: `False`; required for M3N evidence: `False`; required for Gateway/Telegram health: `False`
- artifact root: `None`

## monthly-recall-eval-thinmem-vs-openclaw (fadf5630-c432-4614-a85d-3a8849ec21ec)
- source: `OpenClaw scheduler` enabled=`True` cadence=`cron 15 9 1 * * tz=Australia/Sydney`
- last/next: `None` / `None` status=`None` duration_ms=`None`
- overlaps M3N liveness windows: `False`; event-loop correlation: `False`; getMe correlation: `False`
- safe to pause later with approval: `False`; required for M3N evidence: `False`; required for Gateway/Telegram health: `False`
- artifact root: `None`

## recommendation-check:shadow-long-process-watch-deepseek:2026-06-13-0818 (fc7cdc5c-6301-472b-bead-9429d1b1d8c4)
- source: `OpenClaw scheduler` enabled=`False` cadence=`at 2026-06-12T22:18:00.000Z`
- last/next: `None` / `None` status=`None` duration_ms=`None`
- overlaps M3N liveness windows: `False`; event-loop correlation: `False`; getMe correlation: `False`
- safe to pause later with approval: `False`; required for M3N evidence: `False`; required for Gateway/Telegram health: `False`
- artifact root: `None`

## shadow-soak:long-process-watch:deepseek-v4-pro:24h:2026-06-12 (39a9e6c7-bcac-4f50-b544-5f2f21c82d53)
- source: `OpenClaw scheduler` enabled=`False` cadence=`every 3000000ms`
- last/next: `None` / `None` status=`None` duration_ms=`None`
- overlaps M3N liveness windows: `False`; event-loop correlation: `False`; getMe correlation: `False`
- safe to pause later with approval: `False`; required for M3N evidence: `False`; required for Gateway/Telegram health: `False`
- artifact root: `None`

## token-solver:fleet-auto-heal (db9b80ca-92de-4af9-ba32-c2677c198df5)
- source: `OpenClaw scheduler` enabled=`False` cadence=`every 900000ms`
- last/next: `None` / `None` status=`None` duration_ms=`None`
- overlaps M3N liveness windows: `False`; event-loop correlation: `False`; getMe correlation: `False`
- safe to pause later with approval: `False`; required for M3N evidence: `False`; required for Gateway/Telegram health: `False`
- artifact root: `None`

## verify final-mile closeout append smoke after current Telegram turn (e02852f1-d885-410f-8159-bb310377a51f)
- source: `OpenClaw scheduler` enabled=`False` cadence=`at 2026-06-28T09:17:30.000Z`
- last/next: `None` / `None` status=`None` duration_ms=`None`
- overlaps M3N liveness windows: `False`; event-loop correlation: `False`; getMe correlation: `False`
- safe to pause later with approval: `False`; required for M3N evidence: `False`; required for Gateway/Telegram health: `False`
- artifact root: `None`
