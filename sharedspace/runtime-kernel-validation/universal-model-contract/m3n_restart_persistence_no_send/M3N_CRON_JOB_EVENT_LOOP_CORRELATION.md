# M3N cron job / event-loop correlation

Status: `PASS_M3N_CRON_JOB_EVENT_LOOP_CORRELATION_READY`

Likely: `3`; possible: `1`.

## LIKELY_EVENT_LOOP_PRESSURE_SOURCE: context-plus-semantic-shadow-pass-watch (b29e6275-9bad-4622-8a56-041e5a2dc864)
- score: `9`
- reasons: job id appears as active agent:main:cron in Telegram liveness warning windows; logs correlate with event_loop_delay/liveness warning; 5-minute cadence matches repeated warning spacing

## LIKELY_EVENT_LOOP_PRESSURE_SOURCE: Daily Gmail action summary (7pm Sydney) (187cdfa9-7fd2-4bb7-8148-811247569066)
- score: `8`
- reasons: job id appears as active agent:main:cron in Telegram liveness warning windows; logs correlate with event_loop_delay/liveness warning

## LIKELY_EVENT_LOOP_PRESSURE_SOURCE: memory-drift:daily-reconcile-plus-one-compact (bb4b1687-68ce-4735-b548-4ca2de076148)
- score: `8`
- reasons: job id appears as active agent:main:cron in Telegram liveness warning windows; logs correlate with event_loop_delay/liveness warning

## POSSIBLE_EVENT_LOOP_PRESSURE_SOURCE: context-bridge:morning-sync-check (395199ad-5da5-4e66-a4ec-a5a462771914)
- score: `5`
- reasons: job id appears as active agent:main:cron in Telegram liveness warning windows

## UNLIKELY_EVENT_LOOP_PRESSURE_SOURCE: context-bridge:daily-2am-reconcile (c8499a92-ed1e-43cf-bd34-0e8cb1547104)
- score: `0`
- reasons: none

## UNLIKELY_EVENT_LOOP_PRESSURE_SOURCE: gmail-auth:daily-7am-status (0f59aead-684e-47ca-bfca-6a63df11d85d)
- score: `0`
- reasons: none

## UNLIKELY_EVENT_LOOP_PRESSURE_SOURCE: Daily shared-state sync summary (dashboard + memory) (f31a76fb-1a4e-43a3-b32d-222bed3d9046)
- score: `0`
- reasons: none

## UNLIKELY_EVENT_LOOP_PRESSURE_SOURCE: memory-integrity:daily-silent-rollup (461cecb7-1b1c-41d5-a40d-33a66af0ca04)
- score: `0`
- reasons: none

## UNLIKELY_EVENT_LOOP_PRESSURE_SOURCE: monthly-recall-eval-thinmem-vs-openclaw (fadf5630-c432-4614-a85d-3a8849ec21ec)
- score: `0`
- reasons: none

## UNLIKELY_EVENT_LOOP_PRESSURE_SOURCE: memory-drift:post-compact-watchdog-main-escalator (486bc9e0-b5d4-4046-bd57-acd6b2e9f5ed)
- score: `0`
- reasons: none

## UNLIKELY_EVENT_LOOP_PRESSURE_SOURCE: long-process-watch:every-50m (0d7d143c-5ed5-4a2d-886c-cbee8666c5c0)
- score: `0`
- reasons: none

## UNLIKELY_EVENT_LOOP_PRESSURE_SOURCE: Daily 6am repin Stickbot to gpt-5.5 for vNext-Mesh Semantic Gate (203069e0-3109-4ef2-bf01-baa97bb2f211)
- score: `0`
- reasons: none
