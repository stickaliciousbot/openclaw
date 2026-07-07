# Lessons Learned — M20 Detached Cron Observer Non-Execution

Date: 2026-07-07 AEST
Scope: Stickbot Memory Ledger v0.1 M20 / OpenClaw cron detached observer / long-running observer launch discipline

## What happened

M20 was scheduled as a detached cron-backed observation/soak with T+2h, T+8h, and T+24h final jobs targeting `session:m20-post-production-observation`.

The cron jobs finished with status `ok` and Telegram delivery was reported as delivered, but reconciliation showed the detached sessions did **not** execute the requested M20 checks. Instead, each session returned a generic project-ledger summary.

The final cron delivery classifier also reported `PAYLOAD_ANCHOR_NOT_OBSERVED`. Source inspection showed that this gate is a reporting-evidence gate, not a semantic M20 gate. However, the detached session transcripts revealed the stronger defect: the M20 observer prompt was not executed.

## Evidence

- T+2h/T+8h detached session transcript: `/home/stickai/.openclaw/agents/main/sessions/62b1ae3c-d1ba-48ee-81ef-6d271f76cf88.jsonl`
- T+24h detached session transcript: `/home/stickai/.openclaw/agents/main/sessions/bf1655f2-555f-4a21-b671-368a1c8741af.jsonl`
- Final cron run ledger: `/home/stickai/.openclaw/cron/runs/72b92d09-602f-4649-9bd8-df7b91d3d4ce.jsonl`
- Reconciliation artifact: `sharedspace/runtime-kernel-validation/memory-ledger/M20_DETACHED_OBSERVER_RECONCILIATION_20260707.md`

## Correct classification

```text
HOLD_M20_DETACHED_OBSERVER_DID_NOT_EXECUTE_CHECKS_NO_PASS_UPGRADE
```

Do **not** classify as M20 PASS.

Do **not** classify as a true observed M20 safety-gate failure either; no required M20 semantic checks actually ran.

## Root cause class

Cron/agent detached observer non-execution: the agent turn accepted a long operational prompt but returned a generic summary instead of performing the requested tools/checks/writes.

Secondary reporting issue: `PAYLOAD_ANCHOR_NOT_OBSERVED` can be a closeout verifier/reporting false-positive or ambiguity when `payloadAnchorObserved` is not populated, so it must not be treated alone as semantic milestone failure or PASS evidence.

## Durable rule

For future long-running cron/observer work:

1. Do not rely on a detached cron agent prompt to execute a complex observer checklist directly.
2. Use a deterministic harness that makes the cron/agent perform one small action: launch a local observer command and write launch evidence.
3. The harness must:
   - avoid shell command construction;
   - create the artifact directory before child launch;
   - detach using `subprocess.Popen(start_new_session=True)` or an approved service manager;
   - record PID/PGID/SID proof;
   - write `run_config.json`, `launch_proof.json`, `status.json`, `summary.json`, and `evidence_manifest.json` before reporting launch PASS;
   - update a durable registry;
   - print an explicit PASS anchor only after required files exist;
   - make semantic PASS the child observer's responsibility, not the launcher’s.
4. First-run verification must read the detached session transcript or harness evidence and prove the job actually executed the harness. A generic summary is HOLD/invalid.
5. Terminal milestone PASS requires the child observer’s final artifacts, not just cron `ok` status or Telegram delivery.

## Implemented repair aid

Added reusable harness:

```text
scripts/long_running_cron_observer_harness.py
```

Self-test result:

```text
LONG_RUNNING_CRON_OBSERVER_HARNESS_LAUNCH_PASS
PASS_DETACHED_OBSERVER_LAUNCHED_EVIDENCE_WRITTEN
```

Self-test artifact:

```text
/tmp/long-running-cron-observer-harness-selftest-20260707T0809Z
```

## Safety boundaries preserved during reconciliation

- No M22 started.
- No promotion performed.
- No authority promotion claimed.
- No Gateway/runtime/model/provider/fallback/Telegram/memory-route mutation.
- No raw memory DB/private content included in the reconciliation artifact.
