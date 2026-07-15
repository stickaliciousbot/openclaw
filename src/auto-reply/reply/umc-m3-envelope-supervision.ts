export const M3_CONTRACT_VERSION = "umc.v1.m3" as const;
export const AUTHORITY_MODE = "observe_only" as const;
export const DELIVERY_MODE = "no_send" as const;
export const OWNER_SCOPE = "owner_turn" as const;
export const PRODUCTION_PATH = "unchanged" as const;

export const REQUIRED_ZERO_COUNTERS = [
  "shadow_telegram_send_count",
  "shadow_external_send_count",
  "shadow_provider_model_live_call_count",
  "shadow_real_write_tool_count",
  "shadow_durable_memory_mutation_count",
  "shadow_context_bridge_mutation_count",
  "shadow_route_config_mutation_count",
  "production_authority_change_count",
] as const;

export type M3SafetyCounters = Record<(typeof REQUIRED_ZERO_COUNTERS)[number], number> & {
  ambient_owner_chat_delivery_count: number;
};

export type M3RouteIntent = {
  contractVersion?: string;
  milestone?: string;
  source?: string;
  requested?: { provider?: string; model?: string };
  executable?: { provider?: string; model?: string };
  status?: string;
  updatedAt?: string;
  [key: string]: unknown;
};

export type M3EnvelopeInput = {
  now?: string;
  turn_id?: string;
  session_id?: string;
  channel?: string;
  owner_scope?: string;
  route_intent?: M3RouteIntent | null;
  tool_proposals?: Array<{
    name?: string;
    kind?: string;
    type?: string;
    write?: boolean;
    mutates?: boolean;
  }>;
  safety_counters?: Partial<M3SafetyCounters>;
  ambient_owner_chat_delivery_count?: number;
  evidence_refs?: string[];
};

export type M3BaseReceipt = {
  contract_version: typeof M3_CONTRACT_VERSION;
  turn_id?: string;
  session_id?: string;
  channel?: string;
  owner_scope?: string;
  route_intent: M3RouteIntent | null;
  authority_mode: typeof AUTHORITY_MODE;
  delivery_mode: typeof DELIVERY_MODE;
  tool_policy: {
    mode: typeof AUTHORITY_MODE;
    real_write_tools: "blocked";
    provider_model_calls: "forbidden";
    external_sends: "forbidden";
  };
  postcondition_policy: {
    delivery_mode: typeof DELIVERY_MODE;
    production_path: typeof PRODUCTION_PATH;
    required_receipts: readonly string[];
    required_zero_counters: readonly string[];
  };
  safety_counters: M3SafetyCounters;
  timestamps: { observed_at: string; emitted_at: string; closed_at: string };
  result_status: string;
  reason: string;
  evidence_refs: string[];
  production_path: typeof PRODUCTION_PATH;
};

export type ContractEnvelope = M3BaseReceipt & {
  artifact_type: "ContractEnvelope";
  m2_route_admission_hook_terms: string[];
};

export type ShadowObservationReceipt = M3BaseReceipt & {
  artifact_type: "ShadowObservationReceipt";
  envelope_ref?: string;
  observation_mode: "shadow_observe_only";
  provider_model_live_call: false;
};

export type ToolSupervisionReceipt = M3BaseReceipt & {
  artifact_type: "ToolSupervisionReceipt";
  envelope_ref?: string;
  proposals: Array<{
    name: string;
    kind: string;
    requested: true;
    executed: false;
    mutates: boolean;
    disposition: "blocked_observe_only_no_real_write" | "observed_not_executed";
    reason: string;
  }>;
  real_write_tool_execution_count: 0;
  provider_model_live_call_count: 0;
  external_send_count: 0;
};

export type DeliveryReceipt = M3BaseReceipt & {
  artifact_type: "DeliveryReceipt";
  envelope_ref?: string;
  mode: typeof DELIVERY_MODE;
  delivered: false;
  telegram_send: false;
  external_send: false;
  production_delivery_classification: "AMBIENT_OWNER_CHAT_DELIVERY_SEPARATE_FROM_SHADOW_NO_SEND";
  ambient_owner_chat_delivery_count: number;
};

export type UniversalContractReceipt = M3BaseReceipt & {
  artifact_type: "UniversalContractReceipt";
  envelope_ref?: string;
  receipt_refs: Record<string, string | null>;
  delivery_mode_verified: boolean;
};

export type TerminalContractCloseout = M3BaseReceipt & {
  artifact_type: "TerminalContractCloseout";
  receipt_validation: { ok: boolean; missing: string[] };
  forbidden_counter_nonzero: boolean;
};

export type M3EnvelopeSupervisorResult = {
  supervisor_active: boolean;
  result_status: string;
  reason: string;
  production_path: typeof PRODUCTION_PATH;
  ambient_delivery_classification?: "AMBIENT_OWNER_CHAT_DELIVERY_SEPARATE_FROM_SHADOW_NO_SEND";
  safety_counters: M3SafetyCounters;
  receipts: Partial<{
    envelope: ContractEnvelope;
    shadowObservationReceipt: ShadowObservationReceipt;
    toolSupervisionReceipt: ToolSupervisionReceipt;
    deliveryReceipt: DeliveryReceipt;
    universalContractReceipt: UniversalContractReceipt;
    terminalCloseout: TerminalContractCloseout;
  }>;
};

const DEFAULT_TOOL_POLICY = {
  mode: AUTHORITY_MODE,
  real_write_tools: "blocked",
  provider_model_calls: "forbidden",
  external_sends: "forbidden",
} as const;

const DEFAULT_POSTCONDITION_POLICY = {
  delivery_mode: DELIVERY_MODE,
  production_path: PRODUCTION_PATH,
  required_receipts: [
    "ContractEnvelope",
    "ShadowObservationReceipt",
    "ToolSupervisionReceipt",
    "DeliveryReceipt",
    "UniversalContractReceipt",
    "TerminalContractCloseout",
  ],
  required_zero_counters: REQUIRED_ZERO_COUNTERS,
} as const;

export function createZeroSafetyCounters(
  overrides: Partial<M3SafetyCounters> = {},
): M3SafetyCounters {
  return {
    shadow_telegram_send_count: Number(overrides.shadow_telegram_send_count || 0),
    shadow_external_send_count: Number(overrides.shadow_external_send_count || 0),
    shadow_provider_model_live_call_count: Number(
      overrides.shadow_provider_model_live_call_count || 0,
    ),
    shadow_real_write_tool_count: Number(overrides.shadow_real_write_tool_count || 0),
    shadow_durable_memory_mutation_count: Number(
      overrides.shadow_durable_memory_mutation_count || 0,
    ),
    shadow_context_bridge_mutation_count: Number(
      overrides.shadow_context_bridge_mutation_count || 0,
    ),
    shadow_route_config_mutation_count: Number(overrides.shadow_route_config_mutation_count || 0),
    production_authority_change_count: Number(overrides.production_authority_change_count || 0),
    ambient_owner_chat_delivery_count: Number(overrides.ambient_owner_chat_delivery_count || 0),
  };
}

export function hasNonZeroForbiddenCounter(counters: M3SafetyCounters): boolean {
  return REQUIRED_ZERO_COUNTERS.some((key) => Number(counters[key] || 0) !== 0);
}

function timestampSet(now = new Date().toISOString()) {
  return { observed_at: now, emitted_at: now, closed_at: now };
}

function baseContractFields(
  input: M3EnvelopeInput,
  timestamps: ReturnType<typeof timestampSet>,
  safetyCounters: M3SafetyCounters,
  resultStatus: string,
  reason: string,
): M3BaseReceipt {
  return {
    contract_version: M3_CONTRACT_VERSION,
    turn_id: input.turn_id,
    session_id: input.session_id,
    channel: input.channel,
    owner_scope: input.owner_scope,
    route_intent: input.route_intent ?? null,
    authority_mode: AUTHORITY_MODE,
    delivery_mode: DELIVERY_MODE,
    tool_policy: DEFAULT_TOOL_POLICY,
    postcondition_policy: DEFAULT_POSTCONDITION_POLICY,
    safety_counters: safetyCounters,
    timestamps,
    result_status: resultStatus,
    reason,
    evidence_refs: Array.isArray(input.evidence_refs) ? [...input.evidence_refs] : [],
    production_path: PRODUCTION_PATH,
  };
}

export function isEligibleOwnerTurn(input: M3EnvelopeInput): boolean {
  return input.owner_scope === OWNER_SCOPE;
}

export function hasRouteIntent(input: M3EnvelopeInput): boolean {
  return Boolean(input.route_intent && typeof input.route_intent === "object");
}

export function buildContractEnvelope(
  input: M3EnvelopeInput,
  timestamps = timestampSet(input.now),
  safetyCounters = createZeroSafetyCounters(input.safety_counters),
): ContractEnvelope {
  return {
    artifact_type: "ContractEnvelope",
    ...baseContractFields(
      input,
      timestamps,
      safetyCounters,
      "PASS_M3_CONTRACT_ENVELOPE_EMITTED",
      "eligible owner turn with M2 route intent",
    ),
    m2_route_admission_hook_terms: [
      "resolveUmcV1DefaultRouteFromConfig",
      "isUmcV1QueuedOwnerScope",
      "applyUmcV1QueuedRouteAdmission",
      "umcV1QueuedRouteIntent",
    ],
  };
}

export function buildShadowObservationReceipt(
  envelope: ContractEnvelope,
  input: M3EnvelopeInput,
  safetyCounters = envelope.safety_counters,
  timestamps = envelope.timestamps,
): ShadowObservationReceipt {
  return {
    artifact_type: "ShadowObservationReceipt",
    ...baseContractFields(
      input,
      timestamps,
      safetyCounters,
      "PASS_M3_SHADOW_OBSERVATION_RECEIPT_EMITTED",
      "shadow observation captured without authority or send side effects",
    ),
    envelope_ref: envelope.turn_id,
    observation_mode: "shadow_observe_only",
    provider_model_live_call: false,
  };
}

export function buildToolSupervisionReceipt(
  envelope: ContractEnvelope,
  input: M3EnvelopeInput,
  safetyCounters = envelope.safety_counters,
  timestamps = envelope.timestamps,
): ToolSupervisionReceipt {
  const proposals = Array.isArray(input.tool_proposals) ? input.tool_proposals : [];
  return {
    artifact_type: "ToolSupervisionReceipt",
    ...baseContractFields(
      input,
      timestamps,
      safetyCounters,
      "PASS_M3_TOOL_SUPERVISION_RECEIPT_EMITTED",
      "tool proposals supervised without execution",
    ),
    envelope_ref: envelope.turn_id,
    proposals: proposals.map((proposal) => {
      const kind = proposal.kind || proposal.type || "unknown";
      const mutates = Boolean(proposal.mutates || proposal.write || kind === "write");
      return {
        name: proposal.name || "unnamed_tool_proposal",
        kind,
        requested: true,
        executed: false,
        mutates,
        disposition: mutates ? "blocked_observe_only_no_real_write" : "observed_not_executed",
        reason: mutates
          ? "M3 observe-only supervisor forbids real write tools"
          : "M3 observe-only supervisor records proposal only",
      } as const;
    }),
    real_write_tool_execution_count: 0,
    provider_model_live_call_count: 0,
    external_send_count: 0,
  };
}

export function buildDeliveryReceipt(
  envelope: ContractEnvelope,
  input: M3EnvelopeInput,
  safetyCounters = envelope.safety_counters,
  timestamps = envelope.timestamps,
): DeliveryReceipt {
  return {
    artifact_type: "DeliveryReceipt",
    ...baseContractFields(
      input,
      timestamps,
      safetyCounters,
      "PASS_M3_DELIVERY_RECEIPT_NO_SEND_EMITTED",
      "delivery receipt emitted in no_send mode",
    ),
    envelope_ref: envelope.turn_id,
    mode: DELIVERY_MODE,
    delivered: false,
    telegram_send: false,
    external_send: false,
    production_delivery_classification: "AMBIENT_OWNER_CHAT_DELIVERY_SEPARATE_FROM_SHADOW_NO_SEND",
    ambient_owner_chat_delivery_count: Number(input.ambient_owner_chat_delivery_count || 0),
  };
}

export function buildUniversalContractReceipt(parts: {
  envelope: ContractEnvelope;
  shadowObservationReceipt?: ShadowObservationReceipt;
  toolSupervisionReceipt?: ToolSupervisionReceipt;
  deliveryReceipt?: DeliveryReceipt;
}): UniversalContractReceipt {
  const input: M3EnvelopeInput = parts.envelope;
  return {
    artifact_type: "UniversalContractReceipt",
    ...baseContractFields(
      input,
      parts.envelope.timestamps,
      parts.envelope.safety_counters,
      "PASS_M3_UNIVERSAL_CONTRACT_RECEIPT_EMITTED",
      "all required M3 observe-only receipts bound",
    ),
    envelope_ref: parts.envelope.turn_id,
    receipt_refs: {
      contract_envelope: parts.envelope.artifact_type,
      shadow_observation_receipt: parts.shadowObservationReceipt?.artifact_type ?? null,
      tool_supervision_receipt: parts.toolSupervisionReceipt?.artifact_type ?? null,
      delivery_receipt: parts.deliveryReceipt?.artifact_type ?? null,
    },
    delivery_mode_verified: parts.deliveryReceipt?.mode === DELIVERY_MODE,
  };
}

export function validateRequiredReceipts(receipts: M3EnvelopeSupervisorResult["receipts"]): {
  ok: boolean;
  missing: string[];
} {
  const missing: string[] = [];
  if (receipts.envelope?.artifact_type !== "ContractEnvelope") missing.push("envelope");
  if (receipts.shadowObservationReceipt?.artifact_type !== "ShadowObservationReceipt") {
    missing.push("shadowObservationReceipt");
  }
  if (receipts.toolSupervisionReceipt?.artifact_type !== "ToolSupervisionReceipt") {
    missing.push("toolSupervisionReceipt");
  }
  if (receipts.deliveryReceipt?.artifact_type !== "DeliveryReceipt")
    missing.push("deliveryReceipt");
  if (receipts.deliveryReceipt && receipts.deliveryReceipt.mode !== DELIVERY_MODE) {
    missing.push("deliveryReceipt.mode:no_send");
  }
  if (receipts.universalContractReceipt?.artifact_type !== "UniversalContractReceipt") {
    missing.push("universalContractReceipt");
  }
  return { ok: missing.length === 0, missing };
}

export function buildTerminalContractCloseout(
  parts: M3EnvelopeSupervisorResult["receipts"] & { input?: M3EnvelopeInput },
  resultStatus?: string,
  reason?: string,
): TerminalContractCloseout {
  const input = (parts.envelope ?? parts.input ?? {}) as M3EnvelopeInput;
  const safetyCounters =
    parts.envelope?.safety_counters ?? createZeroSafetyCounters(input.safety_counters);
  const timestamps = parts.envelope?.timestamps ?? timestampSet(input.now);
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
    ...baseContractFields(input, timestamps, safetyCounters, terminalStatus, terminalReason ?? ""),
    receipt_validation: validation,
    forbidden_counter_nonzero: forbiddenCounterNonZero,
  };
}

export function runM3EnvelopeSupervisor(input: M3EnvelopeInput): M3EnvelopeSupervisorResult {
  const safetyCounters = createZeroSafetyCounters({
    ...(input.safety_counters ?? {}),
    ambient_owner_chat_delivery_count: input.ambient_owner_chat_delivery_count ?? 0,
  });
  if (!isEligibleOwnerTurn(input)) {
    return {
      supervisor_active: false,
      result_status: "SKIP_M3_SUPERVISOR_NOT_OWNER_OR_UNGATED",
      reason: "M3 supervisor activates only for owner_turn scope",
      production_path: PRODUCTION_PATH,
      safety_counters: safetyCounters,
      receipts: {},
    };
  }
  if (!hasRouteIntent(input)) {
    const terminalCloseout = buildTerminalContractCloseout(
      { input },
      "HOLD_M3_ROUTE_INTENT_MISSING",
      "eligible owner turn is missing M2 route intent; do not pass M3",
    );
    return {
      supervisor_active: true,
      result_status: terminalCloseout.result_status,
      reason: terminalCloseout.reason,
      production_path: PRODUCTION_PATH,
      safety_counters: terminalCloseout.safety_counters,
      receipts: { terminalCloseout },
    };
  }
  const envelope = buildContractEnvelope(input, timestampSet(input.now), safetyCounters);
  const shadowObservationReceipt = buildShadowObservationReceipt(envelope, input);
  const toolSupervisionReceipt = buildToolSupervisionReceipt(envelope, input);
  const deliveryReceipt = buildDeliveryReceipt(envelope, input);
  const universalContractReceipt = buildUniversalContractReceipt({
    envelope,
    shadowObservationReceipt,
    toolSupervisionReceipt,
    deliveryReceipt,
  });
  const terminalCloseout = buildTerminalContractCloseout({
    envelope,
    shadowObservationReceipt,
    toolSupervisionReceipt,
    deliveryReceipt,
    universalContractReceipt,
  });
  return {
    supervisor_active: true,
    result_status: terminalCloseout.result_status,
    reason: terminalCloseout.reason,
    production_path: PRODUCTION_PATH,
    ambient_delivery_classification: "AMBIENT_OWNER_CHAT_DELIVERY_SEPARATE_FROM_SHADOW_NO_SEND",
    safety_counters: terminalCloseout.safety_counters,
    receipts: {
      envelope,
      shadowObservationReceipt,
      toolSupervisionReceipt,
      deliveryReceipt,
      universalContractReceipt,
      terminalCloseout,
    },
  };
}
