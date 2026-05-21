// Fail-closed policy — determines safe_escalation_allowed and fail_closed_if_unavailable.
// For unsafe/unsupported intents, fail closed aggressively.
// For all others, allow safe escalation unless explicitly dangerous.
// Deterministic. No LLM.

const FAIL_CLOSED = ['unsafe_or_unsupported'];

function evaluate(intentFamily) {
  if (FAIL_CLOSED.includes(intentFamily)) {
    return {
      safe_escalation_allowed: false,
      fail_closed_if_unavailable: true
    };
  }
  return {
    safe_escalation_allowed: true,
    fail_closed_if_unavailable: false
  };
}

module.exports = { evaluate };
