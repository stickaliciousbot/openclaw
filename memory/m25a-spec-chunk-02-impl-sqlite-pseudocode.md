# M25A Spec Chunk 02 — Implementation Approach + SQLite + Pseudocode
## Source: Stick messages 15205-15206, 2026-05-21 14:07 AEST

---

## Implementation Approach: Build Beside, Not Replace

### Location
```
~/.openclaw/workspace/services/m25a-intent-shadow/
```

Do NOT mutate the existing preselector, routes, or gateway config.

### Suggested Files
```
src/
  scorer.js          — weighted candidate scorer
  features.js        — prompt shape, context gate, risk feature extractors
  envelope.js        — instruction/support/control channel envelope schema
  contextGate.js     — context-to-confidence gating (never prompt replacement)
  risk.js            — risk feature extraction
  explain.js         — explainability output
  sqliteStore.js     — SQLite decision logging
  compare.js         — shadow-vs-existing comparison
  server.js          — shadow service entry point

tests/
  fixtures/
    short_ambiguous.jsonl
    openclaw_ops.jsonl
    coding_tasks.jsonl
    false_positive_keywords.jsonl
    context_injection.jsonl
  scorer.test.js
  gates.test.js

scripts/
  run_shadow_eval.sh
  run_hard_gates.sh
  export_report.sh

data/
  intent_shadow.sqlite
  decisions.jsonl
```

---

## SQLite Schema

```sql
CREATE TABLE IF NOT EXISTS intent_decisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  request_id TEXT NOT NULL,
  visible_user_text TEXT NOT NULL,
  support_hash TEXT NOT NULL,
  control_hash TEXT NOT NULL,
  selected_intent TEXT NOT NULL,
  route_class TEXT NOT NULL,
  confidence REAL NOT NULL,
  tool_required INTEGER NOT NULL,
  risk TEXT NOT NULL,
  hardcoded_phrase_used INTEGER NOT NULL DEFAULT 0,
  decision_method TEXT NOT NULL,
  prompt_evidence_json TEXT NOT NULL,
  context_evidence_json TEXT NOT NULL,
  features_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS preselector_comparison (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  request_id TEXT NOT NULL,
  existing_intent TEXT,
  shadow_intent TEXT,
  existing_route_class TEXT,
  shadow_route_class TEXT,
  match INTEGER NOT NULL,
  shadow_confidence REAL NOT NULL,
  divergence_reason TEXT
);

CREATE TABLE IF NOT EXISTS gate_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  gate_id TEXT NOT NULL,
  gate_name TEXT NOT NULL,
  status TEXT NOT NULL,
  details_json TEXT NOT NULL
);
```

---

## Pseudocode: Deterministic Weighted Intent Scorer

```javascript
export function scoreIntent(envelope) {
  const prompt = envelope.instruction_channel.visible_user_text || "";
  const promptFeatures = extractPromptShapeFeatures(prompt);
  const contextFeatures = extractContextGateFeatures(envelope.support_channel);
  const riskFeatures = extractRiskFeatures(
    prompt, envelope.support_channel, envelope.control_channel
  );

  const candidates = buildCandidateIntents();
  const scored = candidates.map(candidate => {
    const featureScore = scoreCandidate({
      candidate,
      promptFeatures,
      contextFeatures,
      riskFeatures
    });
    return {
      candidate,
      score: clamp(featureScore.total, 0, 1),
      prompt_evidence: featureScore.promptEvidence,
      context_evidence: featureScore.contextEvidence,
      features: featureScore.features
    };
  }).sort((a, b) => b.score - a.score);

  const winner = scored[0];

  // Confidence thresholds
  if (winner.score < 0.45) {
    return simpleChatResult(winner, "low_confidence_default");
  }
  if (winner.score < 0.55 && promptFeatures.ambiguity_score > 0.7) {
    return clarificationResult(winner, "ambiguous_prompt_low_confidence");
  }
  if (winner.candidate.tool_required && winner.score < 0.72) {
    return clarificationResult(winner, "tool_route_below_threshold");
  }

  return {
    intent: winner.candidate.intent,
    confidence: winner.score,
    route_class: winner.candidate.route_class,
    tool_required: winner.candidate.tool_required,
    risk: riskFeatures.risk,
    prompt_evidence: winner.prompt_evidence,
    context_evidence: winner.context_evidence,
    features: winner.features,
    hardcoded_phrase_used: false,
    decision_method: "deterministic_weighted_intent_v1",
    fallback_reason: null
  };
}
```

---

## Cross-reference
- Previous chunk: 01 — Core correction + channel separation + output envelope
- Next chunk: 03 — Hard PASS validation gates G0-G10
