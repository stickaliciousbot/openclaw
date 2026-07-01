// OpenClaw Stickbot Work Lifecycle Ledger — M11B disabled-by-default runtime hook config scaffold
// Sidecar/readiness module only. Do not import from live runtime paths until a later approved M11 production canary apply.

export const WORK_LIFECYCLE_INTERNAL_HOOK_ENTRY_ID = 'work-lifecycle-production-canary';

export const workLifecycleInternalHookConfigSchema = {
  $id: 'https://openclaw.local/schemas/work_lifecycle.m11b.internal_hook_config.json',
  type: 'object',
  additionalProperties: false,
  required: [],
  properties: {
    hooks: {
      type: 'object',
      additionalProperties: true,
      properties: {
        internal: {
          type: 'object',
          additionalProperties: true,
          properties: {
            enabled: { type: 'boolean', default: false },
            entries: {
              type: 'object',
              additionalProperties: true,
              properties: {
                [WORK_LIFECYCLE_INTERNAL_HOOK_ENTRY_ID]: {
                  type: 'object',
                  additionalProperties: false,
                  required: [],
                  properties: {
                    enabled: { type: 'boolean', default: false },
                    mode: { enum: ['observe_only', 'enforce_canary'], default: 'observe_only' },
                    scope: { enum: ['production_canary'], default: 'production_canary' },
                    canaryOwner: { enum: ['stickbot'], default: 'stickbot' },
                    productionPromotion: { const: false, default: false },
                    requireTerminalCloseout: { type: 'boolean', default: true },
                    requireDeliveryState: { type: 'boolean', default: true },
                    suppressFailHoldAbort: { const: false, default: false },
                    allowRuntimeSend: { const: false, default: false }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
} as const;

export function getWorkLifecycleInternalHookConfig(config = {}) {
  return config?.hooks?.internal?.entries?.[WORK_LIFECYCLE_INTERNAL_HOOK_ENTRY_ID] ?? {};
}

export function isWorkLifecycleInternalHookEnabled(config = {}) {
  const internalHooksEnabled = config?.hooks?.internal?.enabled === true;
  const entry = getWorkLifecycleInternalHookConfig(config);
  return internalHooksEnabled === true && entry?.enabled === true;
}

export function classifyWorkLifecycleHookReadiness(config = {}) {
  const entry = getWorkLifecycleInternalHookConfig(config);
  const enabled = isWorkLifecycleInternalHookEnabled(config);

  if (!enabled) {
    return {
      enabled: false,
      ready: false,
      mode: 'disabled',
      reason: 'WORK_LIFECYCLE_INTERNAL_HOOK_DISABLED_BY_DEFAULT'
    };
  }

  const invalid = [];
  if (entry.mode !== 'enforce_canary') invalid.push('mode_must_be_enforce_canary');
  if (entry.scope !== 'production_canary') invalid.push('scope_must_be_production_canary');
  if (entry.canaryOwner !== 'stickbot') invalid.push('canary_owner_must_be_stickbot');
  if (entry.productionPromotion !== false) invalid.push('production_promotion_must_remain_false');
  if (entry.requireTerminalCloseout !== true) invalid.push('require_terminal_closeout_must_be_true');
  if (entry.requireDeliveryState !== true) invalid.push('require_delivery_state_must_be_true');
  if (entry.suppressFailHoldAbort !== false) invalid.push('suppress_fail_hold_abort_must_be_false');
  if (entry.allowRuntimeSend !== false) invalid.push('allow_runtime_send_must_be_false');

  if (invalid.length > 0) {
    return {
      enabled: true,
      ready: false,
      mode: 'invalid',
      reason: 'WORK_LIFECYCLE_INTERNAL_HOOK_CONFIG_INVALID',
      invalid
    };
  }

  return {
    enabled: true,
    ready: true,
    mode: 'bounded_enforce_canary',
    reason: 'WORK_LIFECYCLE_INTERNAL_HOOK_CONFIG_READY'
  };
}

export function proposedWorkLifecycleInternalHookConfig() {
  return {
    hooks: {
      internal: {
        enabled: true,
        entries: {
          [WORK_LIFECYCLE_INTERNAL_HOOK_ENTRY_ID]: {
            enabled: true,
            mode: 'enforce_canary',
            scope: 'production_canary',
            canaryOwner: 'stickbot',
            productionPromotion: false,
            requireTerminalCloseout: true,
            requireDeliveryState: true,
            suppressFailHoldAbort: false,
            allowRuntimeSend: false
          }
        }
      }
    }
  };
}
