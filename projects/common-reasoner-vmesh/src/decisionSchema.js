// Decision schema validation for Common Reasoner vMesh
// Rejects any decision that claims render/tool/memory/context write authority.
const REQUIRED = [
  'decision_schema', 'service', 'mode', 'turn_id', 'visible_user_text_hash',
  'intent_family', 'obligation', 'required_support', 'required_capabilities',
  'minimum_lane_class', 'safe_escalation_allowed', 'fail_closed_if_unavailable',
  'rendering_allowed', 'tool_execution_allowed', 'memory_write_allowed',
  'context_write_allowed', 'policy_reasons', 'confidence', 'ambiguity_score'
];

const VALID_INTENTS = [
  'simple_chat', 'short_ambiguous_no_context', 'short_ambiguous_with_valid_context',
  'memory_lookup', 'context_bridge_read', 'runtime_status', 'debug_diagnostic',
  'tool_action', 'planning_request', 'unsafe_or_unsupported'
];

const VALID_OBLIGATIONS = [
  'answer_only', 'clarify', 'memory_required', 'context_required',
  'runtime_tool_required', 'tool_required', 'high_reasoning_required', 'fail_closed'
];

const VALID_LANES = [
  'cheap_chat', 'continuity_capable', 'memory_capable', 'context_capable',
  'tool_capable', 'high_reasoning_tool', 'fail_closed'
];

// Hard constants — any violation means the decision is unsafe
const HARD_CONSTANTS = {
  mode: 'decision_only',
  rendering_allowed: false,
  tool_execution_allowed: false,
  memory_write_allowed: false,
  context_write_allowed: false
};

function validateDecision(decision) {
  if (!decision || typeof decision !== 'object') {
    return { ok: false, errors: ['decision is not an object'] };
  }

  const errors = [];

  // Required fields
  for (const f of REQUIRED) {
    if (decision[f] === undefined || decision[f] === null) {
      errors.push(`missing required field: ${f}`);
    }
  }

  // Intent validity
  if (decision.intent_family && !VALID_INTENTS.includes(decision.intent_family)) {
    errors.push(`unknown intent_family: ${decision.intent_family}`);
  }

  // Obligation validity
  if (decision.obligation && !VALID_OBLIGATIONS.includes(decision.obligation)) {
    errors.push(`unknown obligation: ${decision.obligation}`);
  }

  // Lane validity
  if (decision.minimum_lane_class && !VALID_LANES.includes(decision.minimum_lane_class)) {
    errors.push(`unknown minimum_lane_class: ${decision.minimum_lane_class}`);
  }

  // Hard constant enforcement
  for (const [key, value] of Object.entries(HARD_CONSTANTS)) {
    if (decision[key] !== value) {
      errors.push(`hard constant violation: ${key}=${decision[key]}, must be ${value}`);
    }
  }

  return { ok: errors.length === 0, errors };
}

module.exports = { validateDecision, REQUIRED, VALID_INTENTS, VALID_OBLIGATIONS, VALID_LANES, HARD_CONSTANTS };
