import {
  M8_AUTHORITY_MODE,
  M8_ENFORCEMENT_MODE,
  buildM8ValidOwnerCanaryIntent,
  verifyM8OwnerContractLaneCanary,
  type M8CanaryResult,
} from "./umc-m8-owner-contract-lane.ts";

export const M10A_MILESTONE =
  "M10A_OWNER_TELEGRAM_DIRECT_CONTRACT_ENFORCEMENT_CONTROL_PATH" as const;
export const M10A_SOURCE_READY_STATUS = "PASS_M10A_CONTROL_PATH_SOURCE_READY_NO_APPLY" as const;
export const M10A_SCHEMA_VERSION = "umc.v1.m10a.owner_telegram_direct_control.v1" as const;
export const M10A_SCOPE_NAME = "M10A_OWNER_TELEGRAM_DIRECT_CONTRACT_ENFORCEMENT_ONLY" as const;
export const M10A_OWNER_CHAT_ID = "8495203551" as const;
export const M10A_CHANNEL = "telegram_direct" as const;
export const M10A_AGENT_ID = "main" as const;
export const M10A_CONTROL_ARTIFACT_PATH =
  "state/umc-v1/m10a-owner-telegram-direct-enforcement/control.json" as const;
export const M10A_ENABLE_FLAG_KEY = "m10a_enabled" as const;
export const M10A_DISABLE_FLAG_KEY = "m10a_enabled=false" as const;
export const M10A_STATUS_READBACK_PATH = "umc.m10a.ownerTelegramDirect.status" as const;
export const M10A_RUNTIME_DECISION_POINT =
  "auto-reply/reply/umc-m10a-owner-telegram-direct-control-path.evaluateM10AOwnerTelegramDirectContractDecision" as const;
export const M10A_ROLLBACK_KEY = "M10A_DISABLE_OWNER_TELEGRAM_DIRECT_CONTRACT_ENFORCEMENT" as const;
export const M10A_FALLBACK_POLICY = "preserve_m2_m9_contract_stack_fail_closed" as const;

export type M10AControlState = {
  schema: typeof M10A_SCHEMA_VERSION;
  m10a_enabled: boolean;
  scope_name: typeof M10A_SCOPE_NAME;
  owner_chat_id: typeof M10A_OWNER_CHAT_ID;
  channel: typeof M10A_CHANNEL;
  agent_id: typeof M10A_AGENT_ID;
  contract_decision_enforcement: boolean;
  production_authority: false;
  broad_enforcement: false;
  external_sends_allowed: false;
  provider_calls_allowed: false;
  write_tools_allowed: false;
  durable_memory_mutation_allowed: false;
  context_bridge_mutation_allowed: false;
  fallback_policy: typeof M10A_FALLBACK_POLICY;
  rollback_key: typeof M10A_ROLLBACK_KEY;
  enabled_by: string | null;
  enabled_at: string | null;
  disabled_by: string | null;
  disabled_at: string | null;
  status_reason: string;
  evidence_refs: string[];
};

export type M10AControlIntent = Partial<M10AControlState> & {
  request: "enable" | "disable" | "status";
  requested_by?: string;
  requested_at?: string;
  surface?: string;
  abort_threshold_breached?: boolean;
  operator_stop_requested?: boolean;
};

export type M10ARuntimeDecisionInput = {
  state?: M10AControlState;
  surface: string;
  channel: string;
  chat_type: "direct" | "group" | "supergroup" | "channel" | string;
  owner_chat_id?: string;
  agent_id?: string;
  contract_envelope_ref?: string;
  delivery_receipt_required?: boolean;
  terminal_closeout_required?: boolean;
  telegram_send_probe_count?: number;
  external_send_count?: number;
  provider_model_live_call_count?: number;
  write_tool_execution_count?: number;
  durable_memory_mutation_count?: number;
  context_bridge_mutation_count?: number;
  route_config_mutation_count?: number;
  production_authority_change?: boolean;
  broad_production_enforcement?: boolean;
};

export type M10AStatusReadback = {
  status_path: typeof M10A_STATUS_READBACK_PATH;
  control_artifact_path: typeof M10A_CONTROL_ARTIFACT_PATH;
  enabled: boolean;
  scope_name: typeof M10A_SCOPE_NAME;
  owner_chat_id: typeof M10A_OWNER_CHAT_ID;
  channel: typeof M10A_CHANNEL;
  agent_id: typeof M10A_AGENT_ID;
  contract_decision_enforcement: boolean;
  production_authority: false;
  broad_enforcement: false;
  status_reason: string;
  rollback_key: typeof M10A_ROLLBACK_KEY;
  fail_closed: true;
};

export type M10AControlDecision =
  | {
      ok: true;
      status:
        | "PASS_M10A_CONTROL_DEFAULT_DISABLED"
        | "PASS_M10A_CONTROL_ENABLE_ACCEPTED"
        | "PASS_M10A_CONTROL_DISABLE_ACCEPTED"
        | "PASS_M10A_STATUS_READBACK";
      state: M10AControlState;
      readback: M10AStatusReadback;
    }
  | {
      ok: false;
      status:
        | "FAIL_M10A_ENABLE_SCOPE_MISMATCH"
        | "FAIL_M10A_OWNER_SCOPE_REQUIRED"
        | "FAIL_M10A_CHANNEL_SCOPE_REQUIRED"
        | "FAIL_M10A_AGENT_SCOPE_REQUIRED"
        | "FAIL_M10A_BOUNDARY_VIOLATION"
        | "FAIL_M10A_PRODUCTION_AUTHORITY_FORBIDDEN"
        | "FAIL_M10A_BROAD_ENFORCEMENT_FORBIDDEN"
        | "HOLD_M10A_OPERATOR_STOP_OR_ABORT_THRESHOLD";
      reason: string;
      readback: M10AStatusReadback;
    };

export type M10ARuntimeDecision =
  | {
      ok: true;
      status:
        | "PASS_M10A_DISABLED_PRE_M10_BEHAVIOR"
        | "PASS_M10A_SCOPE_NOT_APPLICABLE_EXCLUDED_SURFACE_UNAFFECTED"
        | "PASS_M10A_OWNER_TELEGRAM_DIRECT_CONTRACT_DECISION_ENFORCED";
      decision:
        | "BYPASS_M10A_DISABLED"
        | "BYPASS_M10A_EXCLUDED_SURFACE"
        | "ALLOW_CONTRACT_DECISION_ENFORCEMENT_ONLY";
      readback: M10AStatusReadback;
      m8?: Extract<M8CanaryResult, { ok: true }>;
      evidence: Record<string, unknown>;
    }
  | {
      ok: false;
      status:
        | "FAIL_M10A_RUNTIME_BOUNDARY_VIOLATION"
        | "FAIL_M10A_RUNTIME_M8_REGRESSION"
        | "HOLD_M10A_RUNTIME_CONTRACT_RECEIPT_REQUIRED";
      decision: "FAIL_CLOSED";
      reason: string;
      readback: M10AStatusReadback;
      m8_status?: string;
      evidence: Record<string, unknown>;
    };

export function buildM10ADefaultControlState(
  overrides: Partial<M10AControlState> = {},
): M10AControlState {
  return {
    schema: M10A_SCHEMA_VERSION,
    m10a_enabled: false,
    scope_name: M10A_SCOPE_NAME,
    owner_chat_id: M10A_OWNER_CHAT_ID,
    channel: M10A_CHANNEL,
    agent_id: M10A_AGENT_ID,
    contract_decision_enforcement: false,
    production_authority: false,
    broad_enforcement: false,
    external_sends_allowed: false,
    provider_calls_allowed: false,
    write_tools_allowed: false,
    durable_memory_mutation_allowed: false,
    context_bridge_mutation_allowed: false,
    fallback_policy: M10A_FALLBACK_POLICY,
    rollback_key: M10A_ROLLBACK_KEY,
    enabled_by: null,
    enabled_at: null,
    disabled_by: null,
    disabled_at: null,
    status_reason: "M10A disabled by default; pre-M10 behavior preserved.",
    evidence_refs: [],
    ...overrides,
  };
}

export function buildM10AControlPathSchema() {
  return {
    schema: "umc.v1.m10a.control_path_schema_artifact.v1",
    status: "PASS_M10A_CONTROL_PATH_SCHEMA_DEFINED",
    control_schema_version: M10A_SCHEMA_VERSION,
    control_artifact_path: M10A_CONTROL_ARTIFACT_PATH,
    enable_flag_key: M10A_ENABLE_FLAG_KEY,
    disable_flag_key: M10A_DISABLE_FLAG_KEY,
    status_readback_path: M10A_STATUS_READBACK_PATH,
    runtime_decision_point: M10A_RUNTIME_DECISION_POINT,
    required_fields: [
      "m10a_enabled",
      "scope_name",
      "owner_chat_id",
      "channel",
      "agent_id",
      "contract_decision_enforcement",
      "production_authority",
      "broad_enforcement",
      "external_sends_allowed",
      "provider_calls_allowed",
      "write_tools_allowed",
      "durable_memory_mutation_allowed",
      "context_bridge_mutation_allowed",
      "fallback_policy",
      "rollback_key",
      "enabled_by",
      "enabled_at",
      "disabled_by",
      "disabled_at",
      "status_reason",
      "evidence_refs",
    ],
    defaults: buildM10ADefaultControlState(),
  };
}

export function readM10AStatus(
  state: M10AControlState = buildM10ADefaultControlState(),
): M10AStatusReadback {
  return {
    status_path: M10A_STATUS_READBACK_PATH,
    control_artifact_path: M10A_CONTROL_ARTIFACT_PATH,
    enabled: state.m10a_enabled,
    scope_name: state.scope_name,
    owner_chat_id: state.owner_chat_id,
    channel: state.channel,
    agent_id: state.agent_id,
    contract_decision_enforcement: state.contract_decision_enforcement,
    production_authority: state.production_authority,
    broad_enforcement: state.broad_enforcement,
    status_reason: state.status_reason,
    rollback_key: state.rollback_key,
    fail_closed: true,
  };
}

function isExactM10AScope(intent: Partial<M10AControlState>): boolean {
  return (
    intent.scope_name === M10A_SCOPE_NAME &&
    intent.owner_chat_id === M10A_OWNER_CHAT_ID &&
    intent.channel === M10A_CHANNEL &&
    intent.agent_id === M10A_AGENT_ID
  );
}

function hasForbiddenAuthority(intent: Partial<M10AControlState>): boolean {
  return Boolean(
    intent.production_authority ||
    intent.broad_enforcement ||
    intent.external_sends_allowed ||
    intent.provider_calls_allowed ||
    intent.write_tools_allowed ||
    intent.durable_memory_mutation_allowed ||
    intent.context_bridge_mutation_allowed,
  );
}

export function disableM10AControlState(
  params: {
    state?: M10AControlState;
    disabled_by?: string;
    disabled_at?: string;
    reason?: string;
  } = {},
): Extract<M10AControlDecision, { ok: true }> {
  const state = buildM10ADefaultControlState({
    ...(params.state ?? {}),
    m10a_enabled: false,
    contract_decision_enforcement: false,
    production_authority: false,
    broad_enforcement: false,
    external_sends_allowed: false,
    provider_calls_allowed: false,
    write_tools_allowed: false,
    durable_memory_mutation_allowed: false,
    context_bridge_mutation_allowed: false,
    disabled_by: params.disabled_by ?? "m10a_source_off_switch",
    disabled_at: params.disabled_at ?? null,
    status_reason: params.reason ?? "M10A disabled by exact off-switch; pre-M10 behavior restored.",
  });
  return {
    ok: true,
    status: "PASS_M10A_CONTROL_DISABLE_ACCEPTED",
    state,
    readback: readM10AStatus(state),
  };
}

export function applyM10AControlIntent(
  current: M10AControlState = buildM10ADefaultControlState(),
  intent: M10AControlIntent,
): M10AControlDecision {
  if (intent.operator_stop_requested || intent.abort_threshold_breached) {
    const disabled = disableM10AControlState({
      state: current,
      disabled_by: intent.requested_by ?? "operator_or_abort_threshold",
      disabled_at: intent.requested_at ?? null,
      reason: "M10A disabled/held because operator stop or abort threshold was requested.",
    });
    return {
      ok: false,
      status: "HOLD_M10A_OPERATOR_STOP_OR_ABORT_THRESHOLD",
      reason: "Operator stop or abort threshold disables M10A fail-closed.",
      readback: disabled.readback,
    };
  }

  if (intent.request === "status") {
    return {
      ok: true,
      status: "PASS_M10A_STATUS_READBACK",
      state: current,
      readback: readM10AStatus(current),
    };
  }
  if (intent.request === "disable") {
    return disableM10AControlState({
      state: current,
      disabled_by: intent.requested_by,
      disabled_at: intent.requested_at,
      reason: "M10A disabled by exact disable intent.",
    });
  }

  const readback = readM10AStatus(current);
  if (!isExactM10AScope(intent)) {
    return {
      ok: false,
      status: "FAIL_M10A_ENABLE_SCOPE_MISMATCH",
      reason: "M10A enable requires exact owner Telegram direct scope.",
      readback,
    };
  }
  if (hasForbiddenAuthority(intent)) {
    return {
      ok: false,
      status: "FAIL_M10A_BOUNDARY_VIOLATION",
      reason: "M10A enable intent attempted a forbidden authority or mutation capability.",
      readback,
    };
  }
  if (intent.contract_decision_enforcement !== true) {
    return {
      ok: false,
      status: "FAIL_M10A_ENABLE_SCOPE_MISMATCH",
      reason: "M10A enable requires contract_decision_enforcement=true and no other authority.",
      readback,
    };
  }

  const enabled = buildM10ADefaultControlState({
    m10a_enabled: true,
    contract_decision_enforcement: true,
    enabled_by: intent.requested_by ?? "m10a_source_fixture",
    enabled_at: intent.requested_at ?? null,
    disabled_by: null,
    disabled_at: null,
    status_reason: "M10A enabled for owner Telegram direct contract decision enforcement only.",
    evidence_refs: intent.evidence_refs ?? [],
  });
  return {
    ok: true,
    status: "PASS_M10A_CONTROL_ENABLE_ACCEPTED",
    state: enabled,
    readback: readM10AStatus(enabled),
  };
}

function isExactRuntimeScope(input: M10ARuntimeDecisionInput): boolean {
  return (
    input.surface === "telegram" &&
    input.channel === M10A_CHANNEL &&
    input.chat_type === "direct" &&
    input.owner_chat_id === M10A_OWNER_CHAT_ID &&
    input.agent_id === M10A_AGENT_ID
  );
}

function hasRuntimeBoundaryViolation(input: M10ARuntimeDecisionInput): boolean {
  return Boolean(
    (input.telegram_send_probe_count ?? 0) > 0 ||
    (input.external_send_count ?? 0) > 0 ||
    (input.provider_model_live_call_count ?? 0) > 0 ||
    (input.write_tool_execution_count ?? 0) > 0 ||
    (input.durable_memory_mutation_count ?? 0) > 0 ||
    (input.context_bridge_mutation_count ?? 0) > 0 ||
    (input.route_config_mutation_count ?? 0) > 0 ||
    input.production_authority_change ||
    input.broad_production_enforcement,
  );
}

export function evaluateM10AOwnerTelegramDirectContractDecision(
  input: M10ARuntimeDecisionInput,
): M10ARuntimeDecision {
  const state = input.state ?? buildM10ADefaultControlState();
  const readback = readM10AStatus(state);
  const boundaryCounters = {
    telegram_send_probe_count: input.telegram_send_probe_count ?? 0,
    external_send_count: input.external_send_count ?? 0,
    provider_model_live_call_count: input.provider_model_live_call_count ?? 0,
    write_tool_execution_count: input.write_tool_execution_count ?? 0,
    durable_memory_mutation_count: input.durable_memory_mutation_count ?? 0,
    context_bridge_mutation_count: input.context_bridge_mutation_count ?? 0,
    route_config_mutation_count: input.route_config_mutation_count ?? 0,
    production_authority_change: Boolean(input.production_authority_change),
    broad_production_enforcement: Boolean(input.broad_production_enforcement),
  };

  if (!state.m10a_enabled || !state.contract_decision_enforcement) {
    return {
      ok: true,
      status: "PASS_M10A_DISABLED_PRE_M10_BEHAVIOR",
      decision: "BYPASS_M10A_DISABLED",
      readback,
      evidence: { boundaryCounters, disabled_by_default: true },
    };
  }

  if (!isExactRuntimeScope(input)) {
    return {
      ok: true,
      status: "PASS_M10A_SCOPE_NOT_APPLICABLE_EXCLUDED_SURFACE_UNAFFECTED",
      decision: "BYPASS_M10A_EXCLUDED_SURFACE",
      readback,
      evidence: { boundaryCounters, excluded_surface_unaffected: true },
    };
  }

  if (hasRuntimeBoundaryViolation(input)) {
    return {
      ok: false,
      status: "FAIL_M10A_RUNTIME_BOUNDARY_VIOLATION",
      decision: "FAIL_CLOSED",
      reason: "M10A runtime boundary counters and authority/mutation flags must remain zero/false.",
      readback,
      evidence: { boundaryCounters },
    };
  }
  if (
    !input.contract_envelope_ref ||
    input.delivery_receipt_required !== true ||
    input.terminal_closeout_required !== true
  ) {
    return {
      ok: false,
      status: "HOLD_M10A_RUNTIME_CONTRACT_RECEIPT_REQUIRED",
      decision: "FAIL_CLOSED",
      reason:
        "M10A requires M3 envelope, delivery receipt, and terminal closeout before enforcement.",
      readback,
      evidence: { boundaryCounters },
    };
  }

  const m8 = verifyM8OwnerContractLaneCanary({
    intent: buildM8ValidOwnerCanaryIntent({
      turn_id: "m10a-owner-telegram-direct-fixture-turn",
      session_id: "agent:main:telegram:direct:8495203551",
      channel: M10A_CHANNEL,
      contract_envelope_ref: input.contract_envelope_ref,
      authority_mode: M8_AUTHORITY_MODE,
      telegram_send_probe_count: 0,
      external_send_count: 0,
      provider_model_live_call_count: 0,
      route_config_mutation_count: 0,
      durable_memory_mutation_count: 0,
      context_bridge_mutation_count: 0,
      enforcement_enabled: false,
      m9_started: false,
    }),
  });
  if (!m8.ok) {
    return {
      ok: false,
      status: "FAIL_M10A_RUNTIME_M8_REGRESSION",
      decision: "FAIL_CLOSED",
      reason: "M10A cannot enforce if M8 enforced no-send semantics regress.",
      readback,
      m8_status: m8.status,
      evidence: { boundaryCounters, m8_enforcement_mode: M8_ENFORCEMENT_MODE },
    };
  }

  return {
    ok: true,
    status: "PASS_M10A_OWNER_TELEGRAM_DIRECT_CONTRACT_DECISION_ENFORCED",
    decision: "ALLOW_CONTRACT_DECISION_ENFORCEMENT_ONLY",
    readback,
    m8,
    evidence: {
      boundaryCounters,
      m2_route_admission_preserved: true,
      m3_envelope_receipts_preserved: true,
      m4_verified_route_preserved: true,
      m5_capability_manifest_preserved: true,
      m6_contract_build_lane_preserved: true,
      m7_model_fallback_eligibility_preserved: true,
      m8_enforced_no_send_preserved: true,
      m9_live_action_eligibility_bounded: true,
      production_authority: false,
      broad_enforcement: false,
    },
  };
}

export const M10A_BOUNDARY_COUNTERS = Object.freeze({
  m10a_enabled: false,
  production_authority_change_count: 0,
  broad_enforcement_count: 0,
  telegram_send_probe_count: 0,
  external_send_count: 0,
  provider_model_live_call_count: 0,
  write_tool_execution_count: 0,
  route_config_mutation_count: 0,
  durable_memory_mutation_count: 0,
  context_bridge_mutation_count: 0,
});
