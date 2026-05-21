// Obligation analyzer — maps intent_family to obligation class.
// Deterministic mapping. No LLM.

const OBLIGATION_MAP = {
  'simple_chat': 'answer_only',
  'short_ambiguous_no_context': 'clarify',
  'short_ambiguous_with_valid_context': 'answer_only', // context provides actionable prior; but obligation class stays answer_only unless prior overrides
  'memory_lookup': 'memory_required',
  'context_bridge_read': 'context_required',
  'runtime_status': 'runtime_tool_required',
  'debug_diagnostic': 'high_reasoning_required',
  'tool_action': 'tool_required',
  'planning_request': 'high_reasoning_required',
  'unsafe_or_unsupported': 'fail_closed'
};

function analyze(intentFamily, previousState = {}) {
  // For ambiguous with valid context, inherit obligation from prior if available
  if (intentFamily === 'short_ambiguous_with_valid_context' && previousState.actionable_intent) {
    const prior = OBLIGATION_MAP[previousState.actionable_intent];
    if (prior && prior !== 'fail_closed') return prior;
  }
  return OBLIGATION_MAP[intentFamily] || 'answer_only';
}

module.exports = { analyze };
