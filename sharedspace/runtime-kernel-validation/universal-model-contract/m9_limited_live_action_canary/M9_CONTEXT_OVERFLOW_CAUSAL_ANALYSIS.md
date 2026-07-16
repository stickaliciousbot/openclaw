# M9 Context Overflow Causal Analysis

Causal classification: `OWNER_SESSION_ACCUMULATION_CAUSAL`

The local artifact canary remained clean and did not cause the overflow. Probe 6 lines point to active owner Telegram session accumulation: `agent:main:telegram:direct:8495203551`, messages `503`, provider `openai-codex/gpt-5.5`.

Pre-M9 context-overflow-related signals existed: `22`, so the signal did not appear only after the canary.
