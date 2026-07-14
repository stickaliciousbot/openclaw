# M3N cron/job rescoping preflight

Status: `PASS_M3N_CRON_JOB_RESCOPING_PREFLIGHT`

The previous targeted PID cleanup phase is blocked because no safe stale observer PID was identified. Gateway PID 122580 was not targeted. Cleanup, Gateway restart, Telegram send/probe, config mutation, and N2/N3 retry remain not executed. This phase rescopes to read-only recurring job-source discovery.
