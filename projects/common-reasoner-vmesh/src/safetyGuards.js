// Safety guards — final enforcement layer.
// Strips any field that would allow render/tool/memory/context authority.
// Acts as a belt-and-suspenders after schema validation.
// Deterministic. No LLM.

const FORCED_VALUES = {
  mode: 'decision_only',
  rendering_allowed: false,
  tool_execution_allowed: false,
  memory_write_allowed: false,
  context_write_allowed: false
};

const FORBIDDEN_FIELDS = [
  'final_answer',
  'response_text',
  'tool_calls',
  'tool_call',
  'memory_operations',
  'context_mutations',
  'gateway_action',
  'route_override',
  'fallback_override'
];

function safetyGuard(decision) {
  if (!decision) return decision;

  const cleaned = { ...decision };

  // Force hard constants
  for (const [key, value] of Object.entries(FORCED_VALUES)) {
    cleaned[key] = value;
  }

  // Remove forbidden fields
  for (const field of FORBIDDEN_FIELDS) {
    delete cleaned[field];
  }

  return cleaned;
}

module.exports = { safetyGuard };
