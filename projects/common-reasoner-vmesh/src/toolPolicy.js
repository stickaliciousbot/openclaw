// Tool policy — defines required_capabilities per intent.
// Determines what capabilities the execution lane must have.
// Deterministic. No LLM.

const CAPABILITY_MAP = {
  'simple_chat':             { tools: false, memory: false, context_bridge: false, runtime_status: false, high_reasoning: false },
  'short_ambiguous_no_context': { tools: false, memory: false, context_bridge: false, runtime_status: false, high_reasoning: false },
  'short_ambiguous_with_valid_context': { tools: false, memory: false, context_bridge: false, runtime_status: false, high_reasoning: false },
  'memory_lookup':           { tools: true,  memory: true,  context_bridge: false, runtime_status: false, high_reasoning: false },
  'context_bridge_read':     { tools: true,  memory: false, context_bridge: true,  runtime_status: false, high_reasoning: false },
  'runtime_status':          { tools: true,  memory: false, context_bridge: false, runtime_status: true,  high_reasoning: false },
  'debug_diagnostic':        { tools: true,  memory: false, context_bridge: false, runtime_status: true,  high_reasoning: true },
  'tool_action':             { tools: true,  memory: false, context_bridge: false, runtime_status: false, high_reasoning: false },
  'planning_request':        { tools: false, memory: false, context_bridge: false, runtime_status: false, high_reasoning: true },
  'unsafe_or_unsupported':   { tools: false, memory: false, context_bridge: false, runtime_status: false, high_reasoning: false }
};

function requiredCapabilities(intentFamily) {
  return CAPABILITY_MAP[intentFamily] || { tools: false, memory: false, context_bridge: false, runtime_status: false, high_reasoning: false };
}

module.exports = { requiredCapabilities };
