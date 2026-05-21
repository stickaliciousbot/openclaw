// Safety guard tests — ensures final enforcement layer strips forbidden fields
// and forces hard constants even if decision builder or schema miss them.

const { safetyGuard } = require('../src/safetyGuards');

let passed = 0;
let failed = 0;

function test(name, input, check) {
  const result = safetyGuard(input);
  if (check(result)) {
    passed++;
    return true;
  }
  failed++;
  console.log(`FAIL: ${name} — guard check failed`);
  return false;
}

// Force hard constants
const badDecision = {
  mode: 'production',
  rendering_allowed: true,
  tool_execution_allowed: true,
  memory_write_allowed: true,
  context_write_allowed: true,
  intent_family: 'simple_chat'
};
test('forces_mode_decision_only', badDecision, (r) => r.mode === 'decision_only');
test('forces_rendering_false', badDecision, (r) => r.rendering_allowed === false);
test('forces_tool_execution_false', badDecision, (r) => r.tool_execution_allowed === false);
test('forces_memory_write_false', badDecision, (r) => r.memory_write_allowed === false);
test('forces_context_write_false', badDecision, (r) => r.context_write_allowed === false);

// Strip forbidden fields
const leakyDecision = {
  ...badDecision,
  final_answer: 'hello',
  response_text: 'some text',
  tool_calls: [{ name: 'exec', args: {} }],
  tool_call: {},
  memory_operations: [{ op: 'write' }],
  context_mutations: [{ op: 'set' }],
  gateway_action: 'restart',
  route_override: 'openai-codex/gpt-5.5',
  fallback_override: ['bad-lane']
};
test('strips_final_answer', leakyDecision, (r) => r.final_answer === undefined);
test('strips_response_text', leakyDecision, (r) => r.response_text === undefined);
test('strips_tool_calls', leakyDecision, (r) => r.tool_calls === undefined);
test('strips_tool_call', leakyDecision, (r) => r.tool_call === undefined);
test('strips_memory_operations', leakyDecision, (r) => r.memory_operations === undefined);
test('strips_context_mutations', leakyDecision, (r) => r.context_mutations === undefined);
test('strips_gateway_action', leakyDecision, (r) => r.gateway_action === undefined);
test('strips_route_override', leakyDecision, (r) => r.route_override === undefined);
test('strips_fallback_override', leakyDecision, (r) => r.fallback_override === undefined);

// Preserves legit fields
test('preserves_intent', leakyDecision, (r) => r.intent_family === 'simple_chat');

// null input
test('null_safe', null, (r) => r === null);

console.log(`\nSafety tests: ${passed}/${passed + failed} PASS`);
if (failed > 0) process.exit(1);
