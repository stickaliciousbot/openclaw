// Compare policy tests — verifies downgrade detection between CR and v5/broker

const { compareDecision } = require('../src/comparePolicy');

let passed = 0;
let failed = 0;

function test(name, input, check) {
  const result = compareDecision(input);
  if (check(result)) {
    passed++;
    return true;
  }
  failed++;
  console.log(`FAIL: ${name}`);
  return false;
}

// Missing CR → fail_closed
test('missing_cr', { common_reasoner_decision: null }, (r) => !r.compatible && r.unsafe_downgrade === false);

// Equal → compatible
const baseCR = {
  intent_family: 'memory_lookup',
  obligation: 'memory_required',
  required_capabilities: { tools: true, memory: true, context_bridge: false, runtime_status: false, high_reasoning: false },
  minimum_lane_class: 'memory_capable'
};
const baseV5 = {
  obligation: 'memory_required',
  required_capabilities: { tools: true, memory: true, context_bridge: false, runtime_status: false, high_reasoning: false }
};

test('equal_compatible', { common_reasoner_decision: baseCR, v5_contract: baseV5 }, (r) => r.compatible && r.relationship === 'equal');

// CR stricter than v5 → compatible
const stricterCR = {
  ...baseCR,
  minimum_lane_class: 'high_reasoning_tool'
};
test('stricter_compatible', { common_reasoner_decision: stricterCR, v5_contract: baseV5 }, (r) => r.compatible && (r.relationship === 'equal' || r.relationship === 'safer'));

// Tool downgrade → incompatible
const weakCR = {
  intent_family: 'tool_action',
  obligation: 'answer_only',
  required_capabilities: { tools: false, memory: false, context_bridge: false, runtime_status: false, high_reasoning: false },
  minimum_lane_class: 'cheap_chat'
};
const toolV5 = {
  obligation: 'tool_required',
  required_capabilities: { tools: true, memory: false, context_bridge: false, runtime_status: false, high_reasoning: false }
};
test('tool_downgrade_incompatible', { common_reasoner_decision: weakCR, v5_contract: toolV5 }, (r) => !r.compatible && r.unsafe_downgrade);

// Memory downgrade → incompatible
const noMemCR = {
  intent_family: 'memory_lookup',
  obligation: 'answer_only',
  required_capabilities: { tools: false, memory: false, context_bridge: false, runtime_status: false, high_reasoning: false },
  minimum_lane_class: 'cheap_chat'
};
test('memory_downgrade_incompatible', { common_reasoner_decision: noMemCR, v5_contract: baseV5 }, (r) => !r.compatible && r.unsafe_downgrade);

// Obligation downgrade → incompatible
const obligationDownCR = {
  ...baseCR,
  obligation: 'answer_only'
};
test('obligation_downgrade_incompatible', { common_reasoner_decision: obligationDownCR, v5_contract: baseV5 }, (r) => !r.compatible && r.unsafe_downgrade);

console.log(`\nCompare tests: ${passed}/${passed + failed} PASS`);
if (failed > 0) process.exit(1);
