// Route policy — emits minimum_lane_class per intent.
// Common Reasoner does NOT choose exact models. It outputs the minimum safe lane class.
// Downstream Token Broker/v5 maps this to concrete routes.
// Deterministic. No LLM.

const LANE_MAP = {
  'simple_chat': 'cheap_chat',
  'short_ambiguous_no_context': 'continuity_capable',
  'short_ambiguous_with_valid_context': 'continuity_capable',
  'memory_lookup': 'memory_capable',
  'context_bridge_read': 'context_capable',
  'runtime_status': 'tool_capable',
  'debug_diagnostic': 'high_reasoning_tool',
  'tool_action': 'tool_capable',
  'planning_request': 'high_reasoning_tool',
  'unsafe_or_unsupported': 'fail_closed'
};

function minimumLane(intentFamily) {
  return LANE_MAP[intentFamily] || 'cheap_chat';
}

module.exports = { minimumLane };
