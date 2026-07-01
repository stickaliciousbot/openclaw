// OpenClaw Stickbot Work Lifecycle Ledger — M11E prepared production-canary plugin.
// PREP-ONLY ARTIFACT: do not load this plugin unless a later owner-approved M11 apply explicitly patches Gateway config.

export const PLUGIN_ID = 'work-lifecycle-production-canary';
export const CANARY_MARKER = 'WORK_LIFECYCLE_M11_CANARY_SMOKE';

export const DEFAULT_CONFIG = Object.freeze({
  enabled: false,
  mode: 'production_canary',
  canaryOwner: 'stickbot',
  canaryMarker: CANARY_MARKER,
  productionPromotion: false,
  allowRuntimeSend: false,
  allowSyntheticReply: false,
  enforcement: 'observe_only_no_short_circuit',
  evidenceRoot: 'sharedspace/runtime-kernel-validation/work-lifecycle/m11-production-rollout'
});

export function normalizeConfig(input = {}) {
  return { ...DEFAULT_CONFIG, ...(input && typeof input === 'object' ? input : {}) };
}

export function validateConfig(input = {}) {
  const cfg = normalizeConfig(input);
  const errors = [];
  if (cfg.enabled !== true && cfg.enabled !== false) errors.push('enabled must be boolean');
  if (cfg.mode !== 'production_canary') errors.push('mode must be production_canary');
  if (cfg.canaryOwner !== 'stickbot') errors.push('canaryOwner must be stickbot');
  if (typeof cfg.canaryMarker !== 'string' || cfg.canaryMarker.length < 8) errors.push('canaryMarker must be a non-empty string');
  if (cfg.productionPromotion !== false) errors.push('productionPromotion must be false');
  if (cfg.allowRuntimeSend !== false) errors.push('allowRuntimeSend must be false');
  if (cfg.allowSyntheticReply !== false) errors.push('allowSyntheticReply must be false');
  if (cfg.enforcement !== 'observe_only_no_short_circuit') errors.push('enforcement must be observe_only_no_short_circuit');
  if (typeof cfg.evidenceRoot !== 'string' || !cfg.evidenceRoot.includes('m11-production-rollout')) errors.push('evidenceRoot must point at M11 rollout evidence');
  return errors.length === 0 ? { ok: true, value: cfg } : { ok: false, errors };
}

export function evaluateBeforeAgentReplyCanary(event = {}, ctx = {}, pluginConfig = {}) {
  const validation = validateConfig(pluginConfig);
  const cfg = validation.ok ? validation.value : normalizeConfig(pluginConfig);
  const cleanedBody = String(event?.cleanedBody ?? '');
  const boundary = {
    handled: false,
    reply: null,
    mutation: false,
    externalSend: false,
    runtimeSend: false,
    providerMessageApiCall: false,
    productionPromotion: false,
    m12Started: false
  };

  if (!validation.ok) {
    return { ...boundary, reason: 'WORK_LIFECYCLE_M11E_CONFIG_INVALID_FAIL_CLOSED', errors: validation.errors };
  }
  if (cfg.enabled !== true) {
    return { ...boundary, reason: 'WORK_LIFECYCLE_M11E_PLUGIN_DISABLED' };
  }
  if (ctx?.trigger === 'heartbeat') {
    return { ...boundary, reason: 'WORK_LIFECYCLE_M11E_HEARTBEAT_IGNORED' };
  }
  if (cleanedBody.includes(cfg.canaryMarker)) {
    return { ...boundary, reason: 'WORK_LIFECYCLE_M11E_CANARY_MARKER_OBSERVED_NO_SHORT_CIRCUIT' };
  }
  return { ...boundary, reason: 'WORK_LIFECYCLE_M11E_OUTSIDE_CANARY_MARKER_NOOP' };
}

const runtimeConfigSchema = {
  validate(value) {
    return validateConfig(value ?? {});
  },
  jsonSchema: {
    type: 'object',
    additionalProperties: false,
    properties: {
      enabled: { type: 'boolean' },
      mode: { enum: ['production_canary'] },
      canaryOwner: { const: 'stickbot' },
      canaryMarker: { type: 'string' },
      productionPromotion: { const: false },
      allowRuntimeSend: { const: false },
      allowSyntheticReply: { const: false },
      enforcement: { enum: ['observe_only_no_short_circuit'] },
      evidenceRoot: { type: 'string' }
    }
  }
};

export default {
  id: PLUGIN_ID,
  name: 'Work Lifecycle Production Canary',
  description: 'Bounded before_agent_reply production-canary observer for Work Lifecycle Ledger M11.',
  configSchema: runtimeConfigSchema,
  register(api) {
    api.on('before_agent_reply', async (event, ctx = {}) => {
      const decision = evaluateBeforeAgentReplyCanary(event, ctx, ctx?.pluginConfig ?? api.pluginConfig ?? {});
      api.logger?.debug?.(`[${PLUGIN_ID}] ${decision.reason}`);
      return { handled: false, reason: decision.reason };
    }, { priority: -100, timeoutMs: 1000 });
  }
};
