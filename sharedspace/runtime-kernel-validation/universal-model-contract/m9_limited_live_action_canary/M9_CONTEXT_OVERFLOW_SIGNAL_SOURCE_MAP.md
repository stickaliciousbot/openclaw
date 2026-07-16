# M9 Context Overflow Signal Source Map

Classification: `ACTIVE_OWNER_SESSION_CONTEXT_OVERFLOW`

Probe 6 original observer counted `6` context-overflow matches and `2` diag matches. Bounded source attribution found `2` matching log lines in the probe 5→6 window; `1` point directly to the active Telegram owner session.

Key signal:
- session key: `agent:main:telegram:direct:8495203551`
- provider: `openai-codex/gpt-5.5`
- messages: `503`
- session file: `/home/stickai/.openclaw/agents/main/sessions/a54ab0f2-fb7e-4640-ae12-bf37c5e5b2f4.jsonl`

Signals existed before M9 canary: `true` (count `22`).

Conclusion: this was a real owner-session context pressure event, not caused by the local artifact canary.
