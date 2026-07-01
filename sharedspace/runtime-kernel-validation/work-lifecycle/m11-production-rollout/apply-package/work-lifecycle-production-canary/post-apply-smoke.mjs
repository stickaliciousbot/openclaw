import assert from 'node:assert/strict';
import plugin, {
  CANARY_MARKER,
  DEFAULT_CONFIG,
  evaluateBeforeAgentReplyCanary
} from './index.mjs';

const registered = [];
const api = {
  pluginConfig: { ...DEFAULT_CONFIG, enabled: true },
  logger: { debug() {}, info() {}, warn() {}, error() {} },
  on(hookName, handler, opts) {
    registered.push({ hookName, handler, opts });
  }
};

plugin.register(api);
assert.equal(registered.length, 1);
assert.equal(registered[0].hookName, 'before_agent_reply');
assert.equal(registered[0].opts.timeoutMs, 1000);

const localDecision = evaluateBeforeAgentReplyCanary(
  { cleanedBody: `local synthetic ${CANARY_MARKER}` },
  { trigger: 'user', agentId: 'main', messageProvider: 'telegram', sessionKey: 'redacted-session-key' },
  api.pluginConfig
);
assert.equal(localDecision.handled, false);
assert.equal(localDecision.externalSend, false);
assert.equal(localDecision.runtimeSend, false);
assert.equal(localDecision.providerMessageApiCall, false);
assert.equal(localDecision.productionPromotion, false);

const hookDecision = await registered[0].handler(
  { cleanedBody: `local synthetic ${CANARY_MARKER}` },
  { trigger: 'user', agentId: 'main', messageProvider: 'telegram', pluginConfig: api.pluginConfig }
);
assert.deepEqual(hookDecision, { handled: false, reason: 'WORK_LIFECYCLE_M11E_CANARY_MARKER_OBSERVED_NO_SHORT_CIRCUIT' });

console.log(JSON.stringify({
  ok: true,
  marker: 'M11E_POST_APPLY_LOCAL_SYNTHETIC_SMOKE_PASS',
  pluginId: plugin.id,
  hook: registered[0].hookName,
  handled: hookDecision.handled,
  sendsMessages: false,
  productionPromotion: false
}, null, 2));
