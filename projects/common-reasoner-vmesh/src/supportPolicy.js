// Support policy — defines required_support array per intent.
// Deterministic. No LLM.

const SUPPORT_MAP = {
  'simple_chat': [],
  'short_ambiguous_no_context': [],
  'short_ambiguous_with_valid_context': ['previous_state'],
  'memory_lookup': ['memory'],
  'context_bridge_read': ['context_bridge'],
  'runtime_status': ['runtime_status'],
  'debug_diagnostic': ['runtime_status'],
  'tool_action': [],
  'planning_request': [],
  'unsafe_or_unsupported': []
};

function required(intentFamily) {
  return SUPPORT_MAP[intentFamily] || [];
}

module.exports = { required };
