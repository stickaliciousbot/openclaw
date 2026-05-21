// Decision builder — assembles a complete decision object from policy modules.
// Orchestrates classification → obligation → support → tools → route → safety.
// Deterministic. No LLM.

const { classify } = require('./visibleTextClassifier');
const { analyze } = require('./obligationAnalyzer');
const { required: requiredSupport } = require('./supportPolicy');
const { requiredCapabilities } = require('./toolPolicy');
const { minimumLane } = require('./routePolicy');
const { evaluate: evaluateFailClosed } = require('./failClosedPolicy');
const { score: ambiguityScore } = require('./ambiguityPolicy');
const { createHash } = require('crypto');

function hashText(text) {
  if (!text) return 'sha256:empty';
  return 'sha256:' + createHash('sha256').update(text, 'utf8').digest('hex').substring(0, 16);
}

function buildDecision(input) {
  const visible_user_text = input.visible_user_text || '';
  const contextPolicy = input.context_policy || {};
  const previousState = input.previous_state || {};

  const hash = input.visible_user_text_hash || hashText(visible_user_text);
  const intentFamily = classify(visible_user_text, contextPolicy);
  const obligation = analyze(intentFamily, previousState);
  const support = requiredSupport(intentFamily);
  const capabilities = requiredCapabilities(intentFamily);
  const lane = minimumLane(intentFamily);
  const failClosed = evaluateFailClosed(intentFamily);
  const ambiguity = ambiguityScore(visible_user_text, contextPolicy);

  const decision = {
    decision_schema: 'common-reasoner-decision.v1',
    service: 'common-reasoner-vmesh',
    mode: 'decision_only',
    turn_id: input.turn_id || '',
    visible_user_text_hash: hash,
    intent_family: intentFamily,
    obligation: obligation,
    required_support: support,
    required_capabilities: capabilities,
    minimum_lane_class: lane,
    safe_escalation_allowed: failClosed.safe_escalation_allowed,
    fail_closed_if_unavailable: failClosed.fail_closed_if_unavailable,
    rendering_allowed: false,
    tool_execution_allowed: false,
    memory_write_allowed: false,
    context_write_allowed: false,
    policy_reasons: [`intent classified as '${intentFamily}' from visible user text`],
    confidence: 1.0 - ambiguity.score,
    ambiguity_score: ambiguity.score
  };

  return decision;
}

module.exports = { buildDecision };
