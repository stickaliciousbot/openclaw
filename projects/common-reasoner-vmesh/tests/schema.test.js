// Schema validation tests for Common Reasoner vMesh
// Ensures schema rejects invalid decisions and accepts valid ones.

const { validateDecision, HARD_CONSTANTS } = require('../src/decisionSchema');

const VALID_DECISION = {
  decision_schema: 'common-reasoner-decision.v1',
  service: 'common-reasoner-vmesh',
  mode: 'decision_only',
  turn_id: 'test-turn',
  visible_user_text_hash: 'sha256:abcd1234',
  intent_family: 'simple_chat',
  obligation: 'answer_only',
  required_support: [],
  required_capabilities: { tools: false, memory: false, context_bridge: false, runtime_status: false, high_reasoning: false },
  minimum_lane_class: 'cheap_chat',
  safe_escalation_allowed: true,
  fail_closed_if_unavailable: false,
  rendering_allowed: false,
  tool_execution_allowed: false,
  memory_write_allowed: false,
  context_write_allowed: false,
  policy_reasons: ['test'],
  confidence: 0.95,
  ambiguity_score: 0.1
};

let passed = 0;
let failed = 0;

function test(name, decision, expectedOk) {
  const result = validateDecision(decision);
  if (result.ok === expectedOk) {
    passed++;
    return true;
  }
  failed++;
  console.log(`FAIL: ${name} — expected ok=${expectedOk} got ok=${result.ok} errors=${JSON.stringify(result.errors)}`);
  return false;
}

// Valid decision must pass
test('valid_decision_accepted', { ...VALID_DECISION }, true);

// Missing required fields
test('missing_turn_id', { ...VALID_DECISION, turn_id: undefined }, false);
test('missing_intent_family', { ...VALID_DECISION, intent_family: undefined }, false);
test('missing_obligation', { ...VALID_DECISION, obligation: undefined }, false);
test('missing_minimum_lane_class', { ...VALID_DECISION, minimum_lane_class: undefined }, false);

// Hard constant violations
test('rendering_allowed_violation', { ...VALID_DECISION, rendering_allowed: true }, false);
test('tool_execution_violation', { ...VALID_DECISION, tool_execution_allowed: true }, false);
test('memory_write_violation', { ...VALID_DECISION, memory_write_allowed: true }, false);
test('context_write_violation', { ...VALID_DECISION, context_write_allowed: true }, false);
test('mode_not_decision_only', { ...VALID_DECISION, mode: 'production' }, false);

// Unknown values
test('unknown_intent', { ...VALID_DECISION, intent_family: 'invalid_intent' }, false);
test('unknown_obligation', { ...VALID_DECISION, obligation: 'invalid_obligation' }, false);
test('unknown_lane', { ...VALID_DECISION, minimum_lane_class: 'invalid_lane' }, false);

// Null decision
test('null_decision', null, false);

console.log(`\nSchema tests: ${passed}/${passed + failed} PASS`);
if (failed > 0) process.exit(1);
