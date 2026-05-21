# M25A Spec Chunk 01 — Core Correction + Channel Separation
## Source: Stick messages 15204-15205, 2026-05-21 14:07 AEST

---

## The Error Being Corrected

The M25A preselector (visibleTextClassifier.js in common-reasoner-vmesh) was hardcoding
words and phrases. Stick's correction: "words are evidence, not routing rules."

**Must not classify user intent by fixed phrase matching** ("if prompt contains X then
route Y"), except for a tiny explicit deny/allow safety list or protocol markers already
part of the system contract.

---

## Required Behavior (7 Rules)

### 1. Preserve the user prompt as the primary instruction
- The visible user prompt is the ONLY instruction-bearing input.
- Context, memory, runtime state, prior turns, support packets, hydration, and bridge
  records may influence scoring, but must never replace the user prompt.
- Do NOT rewrite a short or ambiguous prompt into a different task because context
  suggests one.

### 2. Context gates the prompt; it does not become the prompt
- Context may raise or lower confidence for candidate intents.
- Context may add supporting signals (e.g., "this follows an active OpenClaw build thread").
- Context may NOT invent the instruction if the visible prompt does not support it.

### 3. Short ambiguous phrases → intent scoring, not hardcoded phrase routing
For prompts like "do it," "continue," "fix it," "go ahead," "same again," "try again":
do NOT route from the phrase alone.

Score candidate intents using:
a. current visible prompt shape
b. immediate prior action ledger
c. active task state
d. open obligation state
e. tool requirement likelihood
f. reversibility/risk
g. confidence threshold

If confidence is below threshold → safe clarification or simple chat, NOT speculative execution.

### 4. Deterministic heuristics + explicit weighted features, not keyword maps
Features may include:
- prompt length
- imperative form
- object presence
- code/config indicators
- attached file references
- active milestone state
- prior unresolved action
- tool dependency
- environment mutation risk
- execution reversibility

Words may be tokenized as evidence only inside general features, never as hardcoded routing triggers.

### 5. Separate channels/contracts
- **instruction_channel** = visible user prompt only. The instruction.
- **support_channel** = context, memory, runtime state, retrieval results, previous task
  state. Non-renderable. May influence scoring.
- **control_channel** = routing state, model/lane state, confidence, policy gates.
  Non-renderable.
- The preselector may read all three, but final intent must explain which visible prompt
  evidence and which support evidence contributed to the score.

### 6. Required output envelope
```json
{
  "intent": "...",
  "confidence": 0.0-1.0,
  "route_class": "chat|analysis|tool_required|coding|ops|clarify|blocked",
  "tool_required": true|false,
  "risk": "low|medium|high",
  "prompt_evidence": [...],
  "context_evidence": [...],
  "features": {...},
  "hardcoded_phrase_used": false,
  "decision_method": "deterministic_weighted_intent_v1",
  "fallback_reason": null|string
}
```

### 7. [Continued in Chunk 02]

---

## Additional: Tool/Risk Features + Confidence Controls

### Tool/risk features:
- requires_file_read
- requires_shell
- requires_git
- requires_network
- requires_config_mutation
- requires_service_restart
- requires_write_action
- reversible
- destructive
- security_sensitive

### Confidence controls:
- min_confidence_for_execution = 0.78
- min_confidence_for_tool_route = 0.72
- min_confidence_for_coding_route = 0.70
- clarify_below = 0.55
- simple_chat_default_below = 0.45

---

## Cross-reference
- Next chunk: 02 — Implementation approach + SQLite schema + pseudocode
- Current preselector: projects/common-reasoner-vmesh/src/visibleTextClassifier.js
- M23 closure: DONE. M24 readiness: READY.
