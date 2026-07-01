// OpenClaw Stickbot Work Lifecycle Ledger — M11B bounded runtime hook scaffold
// Disabled-by-default readiness adapter. Do not import from live runtime paths until a later approved M11 production canary apply.

import { classifyWorkLifecycleHookReadiness } from './work-runtime-hook-config.ts';

export class WorkRuntimeCanaryHookError extends Error {
  constructor(code, message, details = {}) {
    super(message);
    this.name = 'WorkRuntimeCanaryHookError';
    this.code = code;
    this.details = details;
  }
}

export function makeNoopDecision(reason = 'WORK_LIFECYCLE_RUNTIME_HOOK_DISABLED_BY_DEFAULT') {
  return {
    action: 'NOOP',
    enforcementActive: false,
    allowed: true,
    reason,
    mutation: false,
    externalSend: false,
    productionPromotion: false
  };
}

export function evaluateWorkLifecycleRuntimeCanary({ config = {}, event = {}, runRecord = null } = {}) {
  const readiness = classifyWorkLifecycleHookReadiness(config);
  if (!readiness.ready) {
    return makeNoopDecision(readiness.reason);
  }

  if (event.scope !== 'production_canary' || event.canaryOwner !== 'stickbot') {
    return makeNoopDecision('EVENT_OUTSIDE_WORK_LIFECYCLE_PRODUCTION_CANARY_SCOPE');
  }

  if (event.type === 'before_next_milestone') {
    const closeoutStatus = runRecord?.closeoutStatus;
    const terminalCloseouts = new Set(['PASS_PUSHED', 'PASS_LOCAL_VALIDATED', 'FAIL', 'HOLD', 'ABORT', 'SUPERSEDED']);
    if (!terminalCloseouts.has(closeoutStatus)) {
      return {
        action: 'HOLD',
        enforcementActive: true,
        allowed: false,
        reason: 'MISSING_REQUIRED_CLOSEOUT',
        mutation: false,
        externalSend: false,
        productionPromotion: false
      };
    }
  }

  if (event.type === 'before_terminal_closeout') {
    const delivery = event.deliveryState ?? {};
    if (delivery.assumed === true || (delivery.delivered !== true && delivery.queued !== true && delivery.recorded !== true)) {
      return {
        action: 'HOLD',
        enforcementActive: true,
        allowed: false,
        reason: 'TERMINAL_DELIVERY_STATE_NOT_DURABLE',
        mutation: false,
        externalSend: false,
        productionPromotion: false
      };
    }
  }

  return {
    action: 'ALLOW',
    enforcementActive: true,
    allowed: true,
    reason: 'WORK_LIFECYCLE_CANARY_GATES_SATISFIED',
    mutation: false,
    externalSend: false,
    productionPromotion: false
  };
}

export function assertNoLiveWorkLifecycleEnforcement(config = {}) {
  const decision = evaluateWorkLifecycleRuntimeCanary({
    config,
    event: { type: 'before_next_milestone', scope: 'production_canary', canaryOwner: 'stickbot' },
    runRecord: { closeoutStatus: null }
  });

  if (decision.enforcementActive === true || decision.action !== 'NOOP') {
    throw new WorkRuntimeCanaryHookError('LIVE_ENFORCEMENT_UNEXPECTED', 'Work Lifecycle enforcement must remain inactive unless explicitly enabled', { decision });
  }

  return decision;
}
