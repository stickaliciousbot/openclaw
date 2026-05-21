// Compare policy — compares Common Reasoner decision against supplied v5/broker metadata.
// Detects unsafe downgrades. Common Reasoner must be equal, stricter, or safer — never weaker.
// Deterministic. No LLM.

function compareDecision(input) {
  const { common_reasoner_decision: cr, v5_contract: v5, broker_route_explain: broker } = input;

  if (!cr) {
    return { ok: true, compatible: false, relationship: 'incompatible', unsafe_downgrade: false, required_action: 'fail_closed', reasons: ['missing common_reasoner_decision'] };
  }

  // Hard rules: if CR says tools_required=true but v5 says tools=false → downgrade
  const unsafe = [];
  const reasons = [];

  if (cr.required_capabilities && v5 && v5.required_capabilities) {
    if (v5.required_capabilities.tools === true && cr.required_capabilities.tools !== true) {
      unsafe.push('tool_downgrade');
      reasons.push('v5 contract requires tools but CR decision does not');
    }
    if (v5.required_capabilities.memory === true && cr.required_capabilities.memory !== true) {
      unsafe.push('memory_downgrade');
      reasons.push('v5 contract requires memory but CR decision does not');
    }
    if (v5.required_capabilities.context_bridge === true && cr.required_capabilities.context_bridge !== true) {
      unsafe.push('context_downgrade');
      reasons.push('v5 contract requires context_bridge but CR decision does not');
    }
  }

  // Obligation downgrade: CR must not be less strict than the existing v5/broker contract.
  const obligationSeverity = { 'fail_closed': 6, 'tool_required': 5, 'high_reasoning_required': 4, 'memory_required': 3, 'context_required': 3, 'runtime_tool_required': 3, 'clarify': 2, 'answer_only': 1 };
  if (v5 && v5.obligation && obligationSeverity[cr.obligation] < obligationSeverity[v5.obligation]) {
    unsafe.push('obligation_downgrade');
    reasons.push(`CR obligation ${cr.obligation} is weaker than v5 obligation ${v5.obligation}`);
  }

  const unsafeDowngrade = unsafe.length > 0;

  let relationship = 'equal';
  if (unsafeDowngrade) {
    relationship = 'weaker';
  } else if (reasons.length === 0) {
    relationship = 'equal';
  } else {
    relationship = 'safer';
  }

  return {
    ok: true,
    compatible: !unsafeDowngrade,
    relationship,
    unsafe_downgrade: unsafeDowngrade,
    unsafe_downgrade_types: unsafe.length > 0 ? unsafe : [],
    required_action: unsafeDowngrade ? 'fail_closed' : 'allow',
    reasons
  };
}

module.exports = { compareDecision };
