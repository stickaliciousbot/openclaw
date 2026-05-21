# Preflight Checklist (Before Build/Commit/Config Changes)

- [ ] Identify active project + task scope.
- [ ] Review matching entries in `sharedspace/developer-lessons-learned/lessons.jsonl` (use taxonomy in `CATEGORIES.md`).
- [ ] Apply required mitigations.
- [ ] Re-check for recurring/frequent lessons (`remindFrequency: frequent`).
- [ ] For any bug/regression fix, define the error shape and proactively audit sibling failure paths before live smoke: trigger, crossed boundary, leaked artifact/type, symptom, and analogous code paths (input extraction, prompt assembly, metadata forwarding, streaming/non-streaming render, sanitizer/final output, traces/evaluator fixtures).
- [ ] For long soaks/observability loops, launch via a durable detached runner (`start_new_session=True`, `stdin=DEVNULL`, `close_fds=True`, persistent stdout/stderr, persisted pid/state/artifact root) and schedule checks against that detached state, not transient OpenClaw exec/process session labels.
- [ ] Immediately verify soak detachment before saying it is safely running: persisted `state.pid` is non-null; `ps` shows the soak PID is not parented to the OpenClaw gateway/exec session; `PPID` is `systemd --user`/init or another durable supervisor; `SID` and `PGID` are the soak PID; stdout/stderr paths are durable.
- [ ] If task is user-facing communication, run `sharedspace/developer-lessons-learned/pre-send-checklist.md`.
- [ ] If mitigations changed code, update the lesson entry with what changed.
- [ ] For tool/gateway/environment changes, record config-risk notes and rollback plan.
- [ ] For any third-party skill install, enforce supply-chain gate:
  - VirusTotal status checked
  - verified publisher badge present
  - publisher reputation/account age passes sanity checks
  - no request for personal/configuration/secrets (block and escalate if requested)
- [ ] For GitHub code checks/changes, consult repo conventions first (`README.md`, `docs/CONTRIBUTING.md`, `docs/DECISIONS.md`) and enforce branch + PR model.
- [ ] Proceed with build/commit/change only after checks pass.
- [ ] **M25A preselector hard rule (2026-05-21):** Words are evidence, not routing rules. No route from a single word/phrase. Routes emerge from scored contract: prompt shape + context gate + active obligation + risk + confidence threshold. Short ambiguous phrases scored via multi-feature evidence, never phrase matching. Below-threshold → clarify/simple chat, never speculative execution. See `lesson-2026-05-21-hardcoded-phrase-preselector`.
