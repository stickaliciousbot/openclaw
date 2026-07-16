import type { M4RouteRef } from "./umc-m4-verified-route.ts";
import type { M5CapabilityRegistry } from "./umc-m5-capability-manifest.ts";
import {
  M6_AUTHORITY_MODE,
  M6_BROKER_ROUTE,
  M6_DELIVERY_MODE,
  M6_LANE_ID,
  type M6RouteIntentInput,
} from "./umc-m6-contract-build-lane.ts";
import {
  M7_DEFAULT_FALLBACK_WORKER,
  M7_DEFAULT_PRIMARY_WORKER,
  M7_POLICY_BOUNDARY_COUNTERS,
  buildM7EligibilityPolicy,
  buildM7FallbackEquivalenceContract,
  buildM7ValidIntent,
  createM7CapabilityRegistry,
  verifyM7ModelEligibility,
  type M7ModelEligibilityResult,
} from "./umc-m7-model-eligibility.ts";

export const M8_MILESTONE = "M8_OWNER_CONTRACT_LANE_ENFORCED_NO_SEND_CANARY" as const;
export const M8_SOURCE_READY_STATUS =
  "PASS_M8_OWNER_CONTRACT_LANE_ENFORCED_NO_SEND_CANARY_SOURCE_READY_NO_APPLY" as const;
export const M8_POLICY_VERSION =
  "umc.v1.m8.owner_contract_lane_enforced_no_send_canary_policy.v1" as const;
export const M8_CANARY_CONTRACT_VERSION =
  "umc.v1.m8.owner_contract_lane_enforced_no_send_canary_contract.v1" as const;
export const M8_ENFORCEMENT_MODE = "fixture_only_enforced_no_send_canary" as const;
export const M8_AUTHORITY_MODE = "enforced_no_send" as const;
export const M8_OWNER_SCOPE = "owner_turn" as const;
export const M8_FORBIDDEN_SCOPE = "broad_production" as const;

export type M8CanaryStatus =
  | "PASS_M8_OWNER_CONTRACT_LANE_ENFORCED_NO_SEND_CANARY_VERIFIED"
  | "HOLD_M8_OWNER_SCOPE_REQUIRED"
  | "HOLD_M8_NO_SEND_REQUIRED"
  | "HOLD_M8_ENFORCED_NO_SEND_REQUIRED"
  | "HOLD_M8_CONTRACT_LANE_REQUIRED"
  | "HOLD_M8_LIVE_ACTION_CANARY_FORBIDDEN"
  | "HOLD_M8_M7_ELIGIBILITY_NOT_VERIFIED"
  | "FAIL_M8_RAW_MODEL_AUTHORITY_BYPASS"
  | "FAIL_M8_WORKER_MODEL_ROUTE_AUTHORITY"
  | "FAIL_M8_PRODUCTION_AUTHORITY_CHANGE"
  | "FAIL_M8_BROAD_PRODUCTION_ENFORCEMENT_FORBIDDEN"
  | "FAIL_M8_SEND_OR_PROVIDER_CALL_BOUNDARY_VIOLATION";

export type M8OwnerContractLanePolicy = {
  policy_version: typeof M8_POLICY_VERSION;
  milestone: typeof M8_MILESTONE;
  enforcement_mode: typeof M8_ENFORCEMENT_MODE;
  source_ready_status: typeof M8_SOURCE_READY_STATUS;
  eligible_scope: typeof M8_OWNER_SCOPE;
  forbidden_scope: typeof M8_FORBIDDEN_SCOPE;
  lane_id: typeof M6_LANE_ID;
  required_route: typeof M6_BROKER_ROUTE;
  primary_worker: M4RouteRef;
  fallback_worker: M4RouteRef;
  required_delivery_mode: typeof M6_DELIVERY_MODE;
  required_authority_mode: typeof M8_AUTHORITY_MODE;
  underlying_lane_authority_mode: typeof M6_AUTHORITY_MODE;
  m7_prerequisite: "PASS_M7_MODEL_ELIGIBILITY_STAGED_INSTALL_AND_REGRESSION";
  source_fixture_only: true;
  installed_runtime_mutation_allowed: false;
  live_action_canary_allowed: false;
  broad_production_enforcement_allowed: false;
  production_authority_change_allowed: false;
  raw_provider_model_authority_allowed: false;
  worker_model_route_authority_allowed: false;
  no_send_required: true;
  external_send_allowed: false;
  provider_model_live_call_allowed: false;
  route_config_mutation_allowed: false;
  durable_memory_mutation_allowed: false;
  context_bridge_mutation_allowed: false;
  m9_allowed: false;
};

export type M8OwnerContractLaneCanaryContract = {
  contract_version: typeof M8_CANARY_CONTRACT_VERSION;
  enforcement_mode: typeof M8_ENFORCEMENT_MODE;
  enforced_in_source_fixtures_only: true;
  allow_decision: "ALLOW_OWNER_CONTRACT_LANE_NO_SEND_ONLY";
  deny_decision: "DENY_OR_HOLD_ANY_NON_OWNER_SEND_LIVE_OR_RAW_AUTHORITY";
  prerequisites: readonly string[];
  required_preservations: readonly string[];
  forbidden_actions: readonly string[];
  terminal_closeout_required: true;
};

export type M8CanaryIntent = M6RouteIntentInput & {
  canary_scope?: "source_fixture" | "live_action" | "broad_production";
  delivery_mode?: string;
  authority_mode?: string;
  production_authority_change?: boolean;
  broad_production_enforcement?: boolean;
  live_action_canary?: boolean;
  telegram_send_probe_count?: number;
  external_send_count?: number;
  provider_model_live_call_count?: number;
  route_config_mutation_count?: number;
  durable_memory_mutation_count?: number;
  context_bridge_mutation_count?: number;
  m9_started?: boolean;
  enforcement_enabled?: boolean;
};

export type M8CanaryResult =
  | {
      ok: true;
      status: "PASS_M8_OWNER_CONTRACT_LANE_ENFORCED_NO_SEND_CANARY_VERIFIED";
      decision: "ALLOW_OWNER_CONTRACT_LANE_NO_SEND_ONLY";
      policy: M8OwnerContractLanePolicy;
      canary_contract: M8OwnerContractLaneCanaryContract;
      m7: Extract<M7ModelEligibilityResult, { ok: true }>;
      evidence: {
        owner_scope: typeof M8_OWNER_SCOPE;
        lane_id: typeof M6_LANE_ID;
        delivery_mode: typeof M6_DELIVERY_MODE;
        authority_mode: typeof M8_AUTHORITY_MODE;
        underlying_lane_authority_mode: typeof M6_AUTHORITY_MODE;
        enforcement_mode: typeof M8_ENFORCEMENT_MODE;
        source_fixture_only: true;
        verifiedRoute_preserved: true;
        contractEnvelope_preserved: true;
        deliveryReceipt_no_send_preserved: true;
        terminalCloseout_preserved: true;
        fallback_contract_preserved: true;
        worker_model_route_authority: false;
        production_authority_change: false;
        broad_production_enforcement: false;
        live_action_canary: false;
      };
    }
  | {
      ok: false;
      status: Exclude<
        M8CanaryStatus,
        "PASS_M8_OWNER_CONTRACT_LANE_ENFORCED_NO_SEND_CANARY_VERIFIED"
      >;
      decision: "DENY_OR_HOLD_ANY_NON_OWNER_SEND_LIVE_OR_RAW_AUTHORITY";
      reason: string;
      m7_status?: string;
      boundary_counters?: Record<string, unknown>;
    };

export function buildM8OwnerContractLanePolicy(
  primary: M4RouteRef = M7_DEFAULT_PRIMARY_WORKER,
  fallback: M4RouteRef = M7_DEFAULT_FALLBACK_WORKER,
): M8OwnerContractLanePolicy {
  return {
    policy_version: M8_POLICY_VERSION,
    milestone: M8_MILESTONE,
    enforcement_mode: M8_ENFORCEMENT_MODE,
    source_ready_status: M8_SOURCE_READY_STATUS,
    eligible_scope: M8_OWNER_SCOPE,
    forbidden_scope: M8_FORBIDDEN_SCOPE,
    lane_id: M6_LANE_ID,
    required_route: M6_BROKER_ROUTE,
    primary_worker: primary,
    fallback_worker: fallback,
    required_delivery_mode: M6_DELIVERY_MODE,
    required_authority_mode: M8_AUTHORITY_MODE,
    underlying_lane_authority_mode: M6_AUTHORITY_MODE,
    m7_prerequisite: "PASS_M7_MODEL_ELIGIBILITY_STAGED_INSTALL_AND_REGRESSION",
    source_fixture_only: true,
    installed_runtime_mutation_allowed: false,
    live_action_canary_allowed: false,
    broad_production_enforcement_allowed: false,
    production_authority_change_allowed: false,
    raw_provider_model_authority_allowed: false,
    worker_model_route_authority_allowed: false,
    no_send_required: true,
    external_send_allowed: false,
    provider_model_live_call_allowed: false,
    route_config_mutation_allowed: false,
    durable_memory_mutation_allowed: false,
    context_bridge_mutation_allowed: false,
    m9_allowed: false,
  };
}

export function buildM8OwnerContractLaneCanaryContract(): M8OwnerContractLaneCanaryContract {
  return {
    contract_version: M8_CANARY_CONTRACT_VERSION,
    enforcement_mode: M8_ENFORCEMENT_MODE,
    enforced_in_source_fixtures_only: true,
    allow_decision: "ALLOW_OWNER_CONTRACT_LANE_NO_SEND_ONLY",
    deny_decision: "DENY_OR_HOLD_ANY_NON_OWNER_SEND_LIVE_OR_RAW_AUTHORITY",
    prerequisites: [
      "PASS_M7_MODEL_ELIGIBILITY_STAGED_INSTALL_AND_REGRESSION",
      "PASS_M7_MODEL_ELIGIBILITY_VERIFIED",
      "PASS_M7_FALLBACK_EQUIVALENCE_INSTALLED_REGRESSION",
    ],
    required_preservations: [
      "owner_turn scope",
      "M6 contract-build lane",
      "M7 model eligibility",
      "M7 fallback equivalence",
      "VerifiedRoute",
      "ContractEnvelope",
      "DeliveryReceipt mode no_send",
      "terminal closeout",
      "enforced_no_send canary authority",
      "underlying M6/M7 lane authority remains observe_only",
      "worker model route_authority false",
      "zero send/provider/config/memory/context-bridge counters",
    ],
    forbidden_actions: [
      "installed runtime mutation in source-ready milestone",
      "package install",
      "tarball apply",
      "Gateway restart",
      "Telegram send/probe",
      "external send",
      "provider/model live call",
      "route/fallback/config production mutation",
      "durable memory mutation",
      "Context Bridge mutation",
      "production authority change",
      "M9 start",
      "live-action canary",
      "broad production enforcement",
    ],
    terminal_closeout_required: true,
  };
}

export function buildM8ValidOwnerCanaryIntent(
  overrides: Partial<M8CanaryIntent> = {},
): M8CanaryIntent {
  return {
    ...buildM7ValidIntent({
      turn_id: "m8-fixture-turn",
      session_id: "m8-fixture-session",
      contract_envelope_ref: "ContractEnvelope:m8-owner-contract-lane-canary",
    }),
    canary_scope: "source_fixture",
    delivery_mode: M6_DELIVERY_MODE,
    authority_mode: M8_AUTHORITY_MODE,
    production_authority_change: false,
    broad_production_enforcement: false,
    live_action_canary: false,
    telegram_send_probe_count: 0,
    external_send_count: 0,
    provider_model_live_call_count: 0,
    route_config_mutation_count: 0,
    durable_memory_mutation_count: 0,
    context_bridge_mutation_count: 0,
    m9_started: false,
    enforcement_enabled: false,
    ...overrides,
  };
}

function boundaryViolation(intent: M8CanaryIntent): boolean {
  return Boolean(
    (intent.telegram_send_probe_count ?? 0) > 0 ||
    (intent.external_send_count ?? 0) > 0 ||
    (intent.provider_model_live_call_count ?? 0) > 0 ||
    (intent.route_config_mutation_count ?? 0) > 0 ||
    (intent.durable_memory_mutation_count ?? 0) > 0 ||
    (intent.context_bridge_mutation_count ?? 0) > 0 ||
    intent.m9_started,
  );
}

function hold(
  status: Exclude<M8CanaryStatus, "PASS_M8_OWNER_CONTRACT_LANE_ENFORCED_NO_SEND_CANARY_VERIFIED">,
  reason: string,
  intent?: M8CanaryIntent,
  m7Status?: string,
): M8CanaryResult {
  return {
    ok: false,
    status,
    decision: "DENY_OR_HOLD_ANY_NON_OWNER_SEND_LIVE_OR_RAW_AUTHORITY",
    reason,
    ...(m7Status ? { m7_status: m7Status } : {}),
    ...(intent
      ? {
          boundary_counters: {
            telegram_send_probe_count: intent.telegram_send_probe_count ?? 0,
            external_send_count: intent.external_send_count ?? 0,
            provider_model_live_call_count: intent.provider_model_live_call_count ?? 0,
            route_config_mutation_count: intent.route_config_mutation_count ?? 0,
            durable_memory_mutation_count: intent.durable_memory_mutation_count ?? 0,
            context_bridge_mutation_count: intent.context_bridge_mutation_count ?? 0,
            m9_started: Boolean(intent.m9_started),
            enforcement_enabled: Boolean(intent.enforcement_enabled),
          },
        }
      : {}),
  };
}

export function verifyM8OwnerContractLaneCanary(params: {
  intent: M8CanaryIntent;
  registry?: M5CapabilityRegistry;
  primary_worker?: M4RouteRef;
  fallback_chain?: M4RouteRef[];
  now?: string;
}): M8CanaryResult {
  const policy = buildM8OwnerContractLanePolicy(
    params.primary_worker ?? M7_DEFAULT_PRIMARY_WORKER,
    params.fallback_chain?.[0] ?? M7_DEFAULT_FALLBACK_WORKER,
  );
  const canaryContract = buildM8OwnerContractLaneCanaryContract();
  const intent = params.intent;

  if (intent.owner_scope !== M8_OWNER_SCOPE) {
    return hold(
      "HOLD_M8_OWNER_SCOPE_REQUIRED",
      "M8 source canary is owner_turn scoped only",
      intent,
    );
  }
  if (intent.canary_scope === "live_action" || intent.live_action_canary) {
    return hold(
      "HOLD_M8_LIVE_ACTION_CANARY_FORBIDDEN",
      "M8 source-ready milestone forbids live-action canary execution",
      intent,
    );
  }
  if (intent.canary_scope === M8_FORBIDDEN_SCOPE || intent.broad_production_enforcement) {
    return hold(
      "FAIL_M8_BROAD_PRODUCTION_ENFORCEMENT_FORBIDDEN",
      "M8 source-ready milestone forbids broad production enforcement",
      intent,
    );
  }
  if (intent.production_authority_change) {
    return hold(
      "FAIL_M8_PRODUCTION_AUTHORITY_CHANGE",
      "M8 source-ready milestone cannot change production authority",
      intent,
    );
  }
  if (intent.delivery_mode !== M6_DELIVERY_MODE) {
    return hold("HOLD_M8_NO_SEND_REQUIRED", "M8 enforced canary requires no_send delivery", intent);
  }
  if (intent.authority_mode !== M8_AUTHORITY_MODE) {
    return hold(
      "HOLD_M8_ENFORCED_NO_SEND_REQUIRED",
      "M8 enforced canary requires enforced_no_send authority",
      intent,
    );
  }
  const requestedIsBroker =
    intent.requested?.provider === M6_BROKER_ROUTE.provider &&
    intent.requested.model === M6_BROKER_ROUTE.model;
  const executableIsBroker =
    intent.executable?.provider === M6_BROKER_ROUTE.provider &&
    intent.executable.model === M6_BROKER_ROUTE.model;
  if (!requestedIsBroker || !executableIsBroker) {
    return hold(
      "FAIL_M8_RAW_MODEL_AUTHORITY_BYPASS",
      "M8 source canary rejects any requested or executable raw provider/model authority",
      intent,
    );
  }
  if (boundaryViolation(intent)) {
    return hold(
      "FAIL_M8_SEND_OR_PROVIDER_CALL_BOUNDARY_VIOLATION",
      "M8 source-ready boundary counters must remain zero",
      intent,
    );
  }

  const registry = params.registry ?? createM7CapabilityRegistry(params.now);
  const m7 = verifyM7ModelEligibility({
    intent,
    registry,
    primary_worker: params.primary_worker,
    fallback_chain: params.fallback_chain,
    now: params.now,
  });
  if (!m7.ok) {
    return hold(
      m7.status === "FAIL_M7_RAW_MODEL_AUTHORITY_BYPASS"
        ? "FAIL_M8_RAW_MODEL_AUTHORITY_BYPASS"
        : "HOLD_M8_M7_ELIGIBILITY_NOT_VERIFIED",
      m7.reason,
      intent,
      m7.status,
    );
  }
  if (
    m7.evidence.worker_model_route_authority !== false ||
    m7.m6.lane.worker_route_authority !== false
  ) {
    return hold(
      "FAIL_M8_WORKER_MODEL_ROUTE_AUTHORITY",
      "M8 source canary forbids worker model route authority",
      intent,
      m7.status,
    );
  }

  return {
    ok: true,
    status: "PASS_M8_OWNER_CONTRACT_LANE_ENFORCED_NO_SEND_CANARY_VERIFIED",
    decision: "ALLOW_OWNER_CONTRACT_LANE_NO_SEND_ONLY",
    policy,
    canary_contract: canaryContract,
    m7,
    evidence: {
      owner_scope: M8_OWNER_SCOPE,
      lane_id: M6_LANE_ID,
      delivery_mode: M6_DELIVERY_MODE,
      authority_mode: M8_AUTHORITY_MODE,
      underlying_lane_authority_mode: M6_AUTHORITY_MODE,
      enforcement_mode: M8_ENFORCEMENT_MODE,
      source_fixture_only: true,
      verifiedRoute_preserved: true,
      contractEnvelope_preserved: true,
      deliveryReceipt_no_send_preserved: true,
      terminalCloseout_preserved: true,
      fallback_contract_preserved: true,
      worker_model_route_authority: false,
      production_authority_change: false,
      broad_production_enforcement: false,
      live_action_canary: false,
    },
  };
}

export const M8_POLICY_BOUNDARY_COUNTERS = Object.freeze({
  ...M7_POLICY_BOUNDARY_COUNTERS,
  installed_runtime_mutation_count: 0,
  package_install_count: 0,
  tarball_apply_count: 0,
  gateway_restart_count: 0,
  live_action_canary_count: 0,
  broad_production_enforcement_count: 0,
  m9_started: false,
  enforcement_enabled: false,
});
