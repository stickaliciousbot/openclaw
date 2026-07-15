// Source-only M3 envelope/tools/delivery supervision prototype.
// This file is deliberately pure: no Telegram sends, no external sends, no
// provider/model calls, no real tool execution, no durable memory writes, no
// Context Bridge writes, no route/config mutation, and no production authority
// changes. It is not installed into the OpenClaw runtime in this milestone.

export const M3_CONTRACT_VERSION = "umc.v1.m3";
export const AUTHORITY_MODE = "observe_only";
export const DELIVERY_MODE = "no_send";
export const OWNER_SCOPE = "owner_turn";
export const PRODUCTION_PATH = "unchanged";

export const REQUIRED_ZERO_COUNTERS = Object.freeze([
  "shadow_telegram_send_count",
  "shadow_external_send_count",
  "shadow_provider_model_live_call_count",
  "shadow_real_write_tool_count",
  "shadow_durable_memory_mutation_count",
  "shadow_context_bridge_mutation_count",
  "shadow_route_config_mutation_count",
  "production_authority_change_count"
]);

const DEFAULT_TOOL_POLICY = Object.freeze({
  mode: "observe_only",
  real_write_tools: "blocked",
  provider_model_calls: "forbidden",
  external_sends: "forbidden"
});

const DEFAULT_POSTCONDITION_POLICY = Object.freeze({
  delivery_mode: DELIVERY_MODE,
  production_path: PRODUCTION_PATH,
  required_receipts: [
    "ContractEnvelope",
    "ShadowObservationReceipt",
    "ToolSupervisionReceipt",
    "DeliveryReceipt",
    "UniversalContractReceipt",
    "TerminalContractCloseout"
  ],
  required_zero_counters: REQUIRED_ZERO_COUNTERS
});

export function createZeroSafetyCounters(overrides = {}) {
  const counters = {
    shadow_telegram_send_count: 0,
    shadow_external_send_count: 0,
    shadow_provider_model_live_call_count: 0,
    shadow_real_write_tool_count: 0,
    shadow_durable_memory_mutation_count: 0,
    shadow_context_bridge_mutation_count: 0,
    shadow_route_config_mutation_count: 0,
    production_authority_change_count: 0,
    ambient_owner_chat_delivery_count: 0
  };
  for (const [key, value] of Object.entries(overrides || {})) {
    if (Object.prototype.hasOwnProperty.call(counters, key)) {
      counters[key] = Number(value || 0);
    }
  }
  return counters;
}

export function hasNonZeroForbiddenCounter(counters) {
  return REQUIRED_ZERO_COUNTERS.some((key) => Number(counters?.[key] || 0) !== 0);
}

function timestampSet(now = new Date().toISOString()) {
  return {
    observed_at: now,
    emitted_at: now,
    closed_at: now
  };
}

function evidenceRefs(input) {
  return Array.isArray(input?.evidence_refs) ? [...input.evidence_refs] : [];
}

function baseContractFields(input, timestamps, safetyCounters, resultStatus, reason) {
  return {
    contract_version: M3_CONTRACT_VERSION,
    turn_id: input.turn_id,
    session_id: input.session_id,
    channel: input.channel,
    owner_scope: input.owner_scope,
    route_intent: input.route_intent ?? null,
    authority_mode: AUTHORITY_MODE,
    delivery_mode: DELIVERY_MODE,
    tool_policy: input.tool_policy ?? DEFAULT_TOOL_POLICY,
    postcondition_policy: input.postcondition_policy ?? DEFAULT_POSTCONDITION_POLICY,
    safety_counters: safetyCounters,
    timestamps,
    result_status: resultStatus,
    reason,
    evidence_refs: evidenceRefs(input)
  };
}

export function isEligibleOwnerTurn(input) {
  return input?.owner_scope === OWNER_SCOPE && input?.m3_supervision_enabled !== false;
}

export function hasRouteIntent(input) {
  return Boolean(input?.route_intent && typeof input.route_intent === "object");
}

export function buildContractEnvelope(input, timestamps = timestampSet(input?.now), safetyCounters = createZeroSafetyCounters(input?.safety_counters)) {
  return {
    artifact_type: "ContractEnvelope",
    ...baseContractFields(input, timestamps, safetyCounters, "PASS_M3_CONTRACT_ENVELOPE_EMITTED", "eligible owner turn with M2 route intent"),
    production_path: PRODUCTION_PATH,
    m2_route_admission_hook_terms: [
      "resolveUmcV1DefaultRouteFromConfig",
      "isUmcV1QueuedOwnerScope",
      "applyUmcV1QueuedRouteAdmission",
      "umcV1QueuedRouteIntent"
    ]
  };
}

export function buildShadowObservationReceipt(envelope, input, safetyCounters = envelope.safety_counters, timestamps = envelope.timestamps) {
  return {
    artifact_type: "ShadowObservationReceipt",
    ...baseContractFields(input, timestamps, safetyCounters, "PASS_M3_SHADOW_OBSERVATION_RECEIPT_EMITTED", "shadow observation captured without authority or send side effects"),
    envelope_ref: envelope.turn_id,
    observation_mode: "shadow_observe_only",
    provider_model_live_call: false,
    production_path: PRODUCTION_PATH
  };
}

export function classifyToolProposal(proposal = {}) {
  const kind = proposal.kind || proposal.type || "unknown";
  const isWrite = kind === "write" || proposal.write === true || proposal.mutates === true;
  return {
    name: proposal.name || "unnamed_tool_proposal",
    kind,
    requested: true,
    executed: false,
    mutates: Boolean(proposal.mutates || isWrite),
    disposition: isWrite ? "blocked_observe_only_no_real_write" : "observed_not_executed",
    reason: isWrite ? "M3 observe-only supervisor forbids real write tools" : "M3 observe-only supervisor records proposal only"
  };
}

export function buildToolSupervisionReceipt(envelope, input, safetyCounters = envelope.safety_counters, timestamps = envelope.timestamps) {
  const proposals = Array.isArray(input.tool_proposals) ? input.tool_proposals : [];
  return {
    artifact_type: "ToolSupervisionReceipt",
    ...baseContractFields(input, timestamps, safetyCounters, "PASS_M3_TOOL_SUPERVISION_RECEIPT_EMITTED", "tool proposals supervised without execution"),
    envelope_ref: envelope.turn_id,
    proposals: proposals.map(classifyToolProposal),
    real_write_tool_execution_count: 0,
    provider_model_live_call_count: 0,
    external_send_count: 0,
    production_path: PRODUCTION_PATH
  };
}

export function buildDeliveryReceipt(envelope, input, safetyCounters = envelope.safety_counters, timestamps = envelope.timestamps) {
  return {
    artifact_type: "DeliveryReceipt",
    ...baseContractFields(input, timestamps, safetyCounters, "PASS_M3_DELIVERY_RECEIPT_NO_SEND_EMITTED", "delivery receipt emitted in no_send mode"),
    envelope_ref: envelope.turn_id,
    mode: DELIVERY_MODE,
    delivered: false,
    telegram_send: false,
    external_send: false,
    production_delivery_classification: "AMBIENT_OWNER_CHAT_DELIVERY_SEPARATE_FROM_SHADOW_NO_SEND",
    ambient_owner_chat_delivery_count: Number(input.ambient_owner_chat_delivery_count || 0),
    production_path: PRODUCTION_PATH
  };
}

export function buildUniversalContractReceipt(parts, timestamps = parts?.envelope?.timestamps ?? timestampSet()) {
  const { envelope, shadowObservationReceipt, toolSupervisionReceipt, deliveryReceipt } = parts;
  const safetyCounters = envelope?.safety_counters ?? createZeroSafetyCounters();
  return {
    artifact_type: "UniversalContractReceipt",
    ...baseContractFields(envelope, timestamps, safetyCounters, "PASS_M3_UNIVERSAL_CONTRACT_RECEIPT_EMITTED", "all required M3 observe-only receipts bound"),
    envelope_ref: envelope.turn_id,
    receipt_refs: {
      contract_envelope: envelope.artifact_type,
      shadow_observation_receipt: shadowObservationReceipt?.artifact_type ?? null,
      tool_supervision_receipt: toolSupervisionReceipt?.artifact_type ?? null,
      delivery_receipt: deliveryReceipt?.artifact_type ?? null
    },
    delivery_mode_verified: deliveryReceipt?.mode === DELIVERY_MODE,
    production_path: PRODUCTION_PATH
  };
}

export function validateRequiredReceipts(receipts) {
  const required = {
    envelope: "ContractEnvelope",
    shadowObservationReceipt: "ShadowObservationReceipt",
    toolSupervisionReceipt: "ToolSupervisionReceipt",
    deliveryReceipt: "DeliveryReceipt",
    universalContractReceipt: "UniversalContractReceipt"
  };
  const missing = [];
  for (const [key, artifactType] of Object.entries(required)) {
    if (receipts?.[key]?.artifact_type !== artifactType) missing.push(key);
  }
  if (receipts?.deliveryReceipt && receipts.deliveryReceipt.mode !== DELIVERY_MODE) {
    missing.push("deliveryReceipt.mode:no_send");
  }
  return {
    ok: missing.length === 0,
    missing
  };
}

export function buildTerminalContractCloseout(parts, resultStatus, reason, timestamps = parts?.envelope?.timestamps ?? timestampSet()) {
  const input = parts?.envelope ?? parts?.input ?? {};
  const safetyCounters = parts?.envelope?.safety_counters ?? createZeroSafetyCounters(input?.safety_counters);
  const validation = validateRequiredReceipts(parts);
  const forbiddenCounterNonZero = hasNonZeroForbiddenCounter(safetyCounters);
  let terminalStatus = resultStatus;
  let terminalReason = reason;
  if (!terminalStatus) {
    if (!validation.ok) {
      terminalStatus = "FAIL_M3_REQUIRED_RECEIPT_MISSING";
      terminalReason = `missing required receipt(s): ${validation.missing.join(",")}`;
    } else if (forbiddenCounterNonZero) {
      terminalStatus = "FAIL_M3_SAFETY_COUNTER_NONZERO";
      terminalReason = "one or more forbidden shadow/prod mutation counters is non-zero";
    } else {
      terminalStatus = "PASS_M3_TERMINAL_CONTRACT_CLOSEOUT_EMITTED";
      terminalReason = "all required M3 observe-only receipts emitted with zero forbidden counters";
    }
  }
  return {
    artifact_type: "TerminalContractCloseout",
    ...baseContractFields(input, timestamps, safetyCounters, terminalStatus, terminalReason),
    receipt_validation: validation,
    forbidden_counter_nonzero: forbiddenCounterNonZero,
    production_path: PRODUCTION_PATH
  };
}

export function runM3EnvelopeSupervisor(input) {
  const timestamps = timestampSet(input?.now);
  const safetyCounters = createZeroSafetyCounters({
    ...(input?.safety_counters || {}),
    ambient_owner_chat_delivery_count: input?.ambient_owner_chat_delivery_count || 0
  });

  if (!isEligibleOwnerTurn(input)) {
    return {
      supervisor_active: false,
      result_status: "SKIP_M3_SUPERVISOR_NOT_OWNER_OR_UNGATED",
      reason: "M3 supervisor activates only for gated owner_turn scope",
      production_path: PRODUCTION_PATH,
      safety_counters: safetyCounters,
      receipts: {}
    };
  }

  if (!hasRouteIntent(input)) {
    const closeout = buildTerminalContractCloseout(
      { input },
      "HOLD_M3_ROUTE_INTENT_MISSING",
      "eligible owner turn is missing M2 route intent; do not pass M3",
      timestamps
    );
    return {
      supervisor_active: true,
      result_status: closeout.result_status,
      reason: closeout.reason,
      production_path: PRODUCTION_PATH,
      safety_counters: safetyCounters,
      receipts: { terminalCloseout: closeout }
    };
  }

  const envelope = buildContractEnvelope(input, timestamps, safetyCounters);
  const shadowObservationReceipt = buildShadowObservationReceipt(envelope, input, safetyCounters, timestamps);
  const toolSupervisionReceipt = buildToolSupervisionReceipt(envelope, input, safetyCounters, timestamps);
  const deliveryReceipt = buildDeliveryReceipt(envelope, input, safetyCounters, timestamps);
  const universalContractReceipt = buildUniversalContractReceipt({ envelope, shadowObservationReceipt, toolSupervisionReceipt, deliveryReceipt }, timestamps);
  const terminalCloseout = buildTerminalContractCloseout({ envelope, shadowObservationReceipt, toolSupervisionReceipt, deliveryReceipt, universalContractReceipt }, undefined, undefined, timestamps);

  return {
    supervisor_active: true,
    result_status: terminalCloseout.result_status,
    reason: terminalCloseout.reason,
    production_path: PRODUCTION_PATH,
    ambient_delivery_classification: "AMBIENT_OWNER_CHAT_DELIVERY_SEPARATE_FROM_SHADOW_NO_SEND",
    safety_counters: safetyCounters,
    receipts: {
      envelope,
      shadowObservationReceipt,
      toolSupervisionReceipt,
      deliveryReceipt,
      universalContractReceipt,
      terminalCloseout
    }
  };
}
