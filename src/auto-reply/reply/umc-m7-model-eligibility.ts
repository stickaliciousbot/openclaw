import type { M4RouteRef } from "./umc-m4-verified-route.ts";
import {
  M5_REQUIRED_AUTHORITY_MODE,
  M5_REQUIRED_DELIVERY_MODE,
  buildM5NoSendManifest,
  buildM5SeedManifests,
  componentIdForRoute,
  createM5CapabilityRegistry,
  getM5ManifestForComponent,
  routeKey,
  type M5CapabilityManifest,
  type M5CapabilityRegistry,
  type M5ManifestValidationResult,
  type M5RejectedManifest,
} from "./umc-m5-capability-manifest.ts";
import {
  M6_AUTHORITY_MODE,
  M6_BROKER_ROUTE,
  M6_DEFAULT_WORKER,
  M6_DELIVERY_MODE,
  M6_LANE_ID,
  buildM6ContractBuildLane,
  buildM6ContractBuildManifests,
  type M6ContractBuildLaneResult,
  type M6RouteIntentInput,
} from "./umc-m6-contract-build-lane.ts";

export const M7_MILESTONE = "M7_MODEL_ELIGIBILITY_AND_FALLBACK_EQUIVALENCE_NO_SEND" as const;
export const M7_POLICY_VERSION = "umc.v1.m7.model_eligibility_policy.v1" as const;
export const M7_EQUIVALENCE_VERSION = "umc.v1.m7.fallback_equivalence_contract.v1" as const;
export const M7_DEFAULT_PRIMARY_WORKER: M4RouteRef = M6_DEFAULT_WORKER;
export const M7_DEFAULT_FALLBACK_WORKER: M4RouteRef = Object.freeze({
  provider: "ollama",
  model: "deepseek-v4-pro:cloud",
});
export const M7_PRIMARY_ADAPTER_ID = "adapter:openai-codex/default" as const;
export const M7_FALLBACK_ADAPTER_ID = "adapter:ollama/default" as const;

export type M7EligibilityStatus =
  | "PASS_M7_MODEL_ELIGIBILITY_VERIFIED"
  | "HOLD_M7_CAPABILITY_MANIFEST_MISSING"
  | "FAIL_M7_CAPABILITY_MANIFEST_INVALID"
  | "HOLD_M7_UNSUPPORTED_NO_SEND"
  | "HOLD_M7_UNSUPPORTED_CONTRACT_ENVELOPE"
  | "HOLD_M7_UNSUPPORTED_DELIVERY_RECEIPT"
  | "HOLD_M7_FALLBACK_CONTRACT_DROP"
  | "HOLD_M7_FALLBACK_AUTHORITY_MODE_CHANGED"
  | "HOLD_M7_FALLBACK_DELIVERY_MODE_CHANGED"
  | "FAIL_M7_RAW_MODEL_AUTHORITY_BYPASS"
  | "FAIL_M7_CONTRACT_BUILD_LANE_REJECTED";

export type M7WorkerRolePolicy = {
  worker_role: "execution_worker";
  route_authority: false;
  requires_verified_route: true;
  requires_capability_manifest: true;
  requires_contract_envelope: true;
  delivery_mode: typeof M6_DELIVERY_MODE;
  authority_mode: typeof M6_AUTHORITY_MODE;
};

export type M7EligibilityPolicy = {
  policy_version: typeof M7_POLICY_VERSION;
  milestone: typeof M7_MILESTONE;
  eligible_primary_worker: M4RouteRef;
  eligible_primary_adapter_id: typeof M7_PRIMARY_ADAPTER_ID;
  eligible_fallback_worker: M4RouteRef;
  eligible_fallback_adapter_id: typeof M7_FALLBACK_ADAPTER_ID;
  worker_policy: M7WorkerRolePolicy;
  required_capability_manifest_fields: string[];
  required_verified_route_behavior: "valid_m4_verified_route_required";
  required_contract_envelope_behavior: "contract_envelope_required";
  required_delivery_receipt_behavior: "delivery_receipt_no_send_required";
  required_terminal_closeout_behavior: "terminal_contract_closeout_required";
  fallback_contract_preservation: true;
  fallback_authority_preservation: typeof M6_AUTHORITY_MODE;
  fallback_no_send_preservation: typeof M6_DELIVERY_MODE;
  fallback_observe_only_preservation: true;
  ineligible_model_behavior: {
    missing_manifest: "HOLD_M7_CAPABILITY_MANIFEST_MISSING";
    malformed_manifest: "FAIL_M7_CAPABILITY_MANIFEST_INVALID";
    unsupported_capability: "typed_HOLD";
    raw_provider_model_authority: "FAIL_M7_RAW_MODEL_AUTHORITY_BYPASS";
  };
};

export type M7FallbackEquivalenceContract = {
  contract_version: typeof M7_EQUIVALENCE_VERSION;
  equivalent_only_if_preserves: readonly string[];
  forbidden_changes: readonly string[];
  no_provider_model_route_authority: true;
};

export type M7ModelEligibilityResult =
  | {
      ok: true;
      status: "PASS_M7_MODEL_ELIGIBILITY_VERIFIED";
      primary_worker: M4RouteRef;
      fallback_chain: M4RouteRef[];
      primary_adapter_id: string;
      fallback_adapter_ids: string[];
      m6: Extract<M6ContractBuildLaneResult, { ok: true }>;
      evidence: {
        primary_manifest: string;
        primary_adapter_manifest: string;
        fallback_manifest_refs: string[];
        fallback_adapter_manifest_refs: string[];
        verifiedRoute_preserved: true;
        contractEnvelope_preserved: true;
        deliveryReceipt_no_send_preserved: true;
        terminalCloseout_preserved: true;
        worker_model_route_authority: false;
      };
    }
  | {
      ok: false;
      status: Exclude<M7EligibilityStatus, "PASS_M7_MODEL_ELIGIBILITY_VERIFIED">;
      reason: string;
      component_id?: string;
      manifest_status?: string;
      unsupported_capabilities?: string[];
      m6_status?: string;
    };

export function buildM7EligibilityPolicy(
  primary: M4RouteRef = M7_DEFAULT_PRIMARY_WORKER,
  fallback: M4RouteRef = M7_DEFAULT_FALLBACK_WORKER,
): M7EligibilityPolicy {
  return {
    policy_version: M7_POLICY_VERSION,
    milestone: M7_MILESTONE,
    eligible_primary_worker: primary,
    eligible_primary_adapter_id: M7_PRIMARY_ADAPTER_ID,
    eligible_fallback_worker: fallback,
    eligible_fallback_adapter_id: M7_FALLBACK_ADAPTER_ID,
    worker_policy: {
      worker_role: "execution_worker",
      route_authority: false,
      requires_verified_route: true,
      requires_capability_manifest: true,
      requires_contract_envelope: true,
      delivery_mode: M6_DELIVERY_MODE,
      authority_mode: M6_AUTHORITY_MODE,
    },
    required_capability_manifest_fields: [
      "supports_verified_route",
      "supports_contract_envelope",
      "supports_delivery_receipt",
      "supported_delivery_modes:no_send",
      "supports_terminal_closeout",
      "supports_tool_supervision",
      "supports_postcondition_policy",
      "supports_no_send",
      "supports_fallback_contract_preservation",
      "supports_observe_only",
      "authority_modes:observe_only",
      "external_send_policy:denied",
      "memory_policy:no_durable_mutation",
      "context_bridge_policy:no_mutation",
    ],
    required_verified_route_behavior: "valid_m4_verified_route_required",
    required_contract_envelope_behavior: "contract_envelope_required",
    required_delivery_receipt_behavior: "delivery_receipt_no_send_required",
    required_terminal_closeout_behavior: "terminal_contract_closeout_required",
    fallback_contract_preservation: true,
    fallback_authority_preservation: M6_AUTHORITY_MODE,
    fallback_no_send_preservation: M6_DELIVERY_MODE,
    fallback_observe_only_preservation: true,
    ineligible_model_behavior: {
      missing_manifest: "HOLD_M7_CAPABILITY_MANIFEST_MISSING",
      malformed_manifest: "FAIL_M7_CAPABILITY_MANIFEST_INVALID",
      unsupported_capability: "typed_HOLD",
      raw_provider_model_authority: "FAIL_M7_RAW_MODEL_AUTHORITY_BYPASS",
    },
  };
}

export function buildM7FallbackEquivalenceContract(): M7FallbackEquivalenceContract {
  return {
    contract_version: M7_EQUIVALENCE_VERSION,
    equivalent_only_if_preserves: [
      "VerifiedRoute",
      "ContractEnvelope",
      "capability manifest eligibility",
      "delivery_mode no_send",
      "authority_mode observe_only",
      "terminal closeout",
      "tool policy",
      "postcondition policy",
      "safety counters",
      "no provider/model route authority",
    ],
    forbidden_changes: [
      "drop VerifiedRoute",
      "drop ContractEnvelope",
      "drop capability manifest requirement",
      "change delivery_mode",
      "change authority_mode",
      "skip terminal closeout",
      "gain route authority",
      "send externally",
      "call live provider by default",
    ],
    no_provider_model_route_authority: true,
  };
}

export function buildM7CapabilityManifests(
  now = "2026-07-16T03:55:00.000Z",
): M5CapabilityManifest[] {
  return [
    buildM5NoSendManifest({
      component_id: M7_PRIMARY_ADAPTER_ID,
      component_type: "adapter",
      adapter_id: M7_PRIMARY_ADAPTER_ID.replace(/^adapter:/u, ""),
      verified_at: now,
      evidence_refs: ["M7_MODEL_ELIGIBILITY_POLICY.json"],
      allowed_tool_classes: ["no_send_model_adapter", "fixture_only"],
    }),
    buildM5NoSendManifest({
      component_id: M7_FALLBACK_ADAPTER_ID,
      component_type: "adapter",
      adapter_id: M7_FALLBACK_ADAPTER_ID.replace(/^adapter:/u, ""),
      verified_at: now,
      evidence_refs: ["M7_MODEL_ELIGIBILITY_POLICY.json"],
      allowed_tool_classes: ["no_send_model_adapter", "fixture_only"],
    }),
    buildM5NoSendManifest({
      component_id: "fallback_chain:m7-primary-to-ollama-cloud",
      component_type: "fallback_chain",
      verified_at: now,
      evidence_refs: ["M7_FALLBACK_EQUIVALENCE_CONTRACT.json"],
      allowed_tool_classes: ["fixture_only", "read_only"],
    }),
  ];
}

export function createM7CapabilityRegistry(now?: string): M5CapabilityRegistry {
  return createM5CapabilityRegistry([
    ...buildM5SeedManifests(now),
    ...buildM6ContractBuildManifests(now),
    ...buildM7CapabilityManifests(now),
  ]);
}

function rejectedForComponent(
  registry: M5CapabilityRegistry,
  componentId: string,
): M5RejectedManifest | null {
  return registry.rejected.find((entry) => entry.component_id === componentId) ?? null;
}

function classifyManifestProblem(
  result: M5ManifestValidationResult | M5RejectedManifest,
  componentId: string,
  context: "primary" | "fallback" | "adapter",
): M7ModelEligibilityResult {
  if (result.status === "HOLD_M5_CAPABILITY_MANIFEST_MISSING") {
    return {
      ok: false,
      status: "HOLD_M7_CAPABILITY_MANIFEST_MISSING",
      reason: result.reason,
      component_id: componentId,
      manifest_status: result.status,
    };
  }
  if (result.status === "FAIL_M5_CAPABILITY_MANIFEST_INVALID") {
    return {
      ok: false,
      status: "FAIL_M7_CAPABILITY_MANIFEST_INVALID",
      reason: result.reason,
      component_id: componentId,
      manifest_status: result.status,
      unsupported_capabilities: result.unsupported_capabilities,
    };
  }

  const unsupported = result.unsupported_capabilities ?? [];
  const status = unsupported.some((item) => item.includes("supports_contract_envelope"))
    ? context === "fallback"
      ? "HOLD_M7_FALLBACK_CONTRACT_DROP"
      : "HOLD_M7_UNSUPPORTED_CONTRACT_ENVELOPE"
    : unsupported.some((item) => item.includes("supports_delivery_receipt"))
      ? "HOLD_M7_UNSUPPORTED_DELIVERY_RECEIPT"
      : unsupported.some((item) => item.includes("supported_delivery_modes:no_send"))
        ? context === "fallback"
          ? "HOLD_M7_FALLBACK_DELIVERY_MODE_CHANGED"
          : "HOLD_M7_UNSUPPORTED_NO_SEND"
        : unsupported.some((item) => item.includes("authority_modes"))
          ? "HOLD_M7_FALLBACK_AUTHORITY_MODE_CHANGED"
          : unsupported.some((item) => item.includes("supports_fallback_contract_preservation"))
            ? "HOLD_M7_FALLBACK_CONTRACT_DROP"
            : "HOLD_M7_CAPABILITY_MANIFEST_MISSING";
  return {
    ok: false,
    status,
    reason: result.reason,
    component_id: componentId,
    manifest_status: result.status,
    unsupported_capabilities: unsupported,
  };
}

function requireAcceptedManifest(
  registry: M5CapabilityRegistry,
  componentId: string,
  context: "primary" | "fallback" | "adapter",
): { ok: true; manifest: M5CapabilityManifest } | M7ModelEligibilityResult {
  const accepted = getM5ManifestForComponent(registry, componentId);
  if (accepted.ok) {
    return { ok: true, manifest: accepted.manifest };
  }
  const rejected = rejectedForComponent(registry, componentId);
  return classifyManifestProblem(rejected ?? accepted, componentId, context);
}

function routeAdapterId(route: M4RouteRef): string {
  if (route.provider === M7_DEFAULT_PRIMARY_WORKER.provider) return M7_PRIMARY_ADAPTER_ID;
  if (route.provider === M7_DEFAULT_FALLBACK_WORKER.provider) return M7_FALLBACK_ADAPTER_ID;
  return `adapter:${route.provider}/default`;
}

function uniqueRoutes(routes: M4RouteRef[]): M4RouteRef[] {
  const seen = new Set<string>();
  return routes.filter((route) => {
    const key = routeKey(route);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

export function verifyM7ModelEligibility(params: {
  intent: M6RouteIntentInput;
  registry?: M5CapabilityRegistry;
  primary_worker?: M4RouteRef;
  fallback_chain?: M4RouteRef[];
  now?: string;
}): M7ModelEligibilityResult {
  const now = params.now ?? new Date().toISOString();
  const registry = params.registry ?? createM7CapabilityRegistry(now);
  const primary = params.primary_worker ?? M7_DEFAULT_PRIMARY_WORKER;
  const fallbackChain = uniqueRoutes(params.fallback_chain ?? [M7_DEFAULT_FALLBACK_WORKER]);

  const primaryManifest = requireAcceptedManifest(
    registry,
    componentIdForRoute(primary),
    "primary",
  );
  if (!primaryManifest.ok) return primaryManifest;
  const primaryAdapterId = routeAdapterId(primary);
  const primaryAdapter = requireAcceptedManifest(registry, primaryAdapterId, "adapter");
  if (!primaryAdapter.ok) return primaryAdapter;

  const fallbackManifestRefs: string[] = [];
  const fallbackAdapterManifestRefs: string[] = [];
  for (const fallback of fallbackChain) {
    const manifest = requireAcceptedManifest(registry, componentIdForRoute(fallback), "fallback");
    if (!manifest.ok) return manifest;
    fallbackManifestRefs.push(manifest.manifest.component_id);
    const adapterId = routeAdapterId(fallback);
    const adapter = requireAcceptedManifest(registry, adapterId, "adapter");
    if (!adapter.ok) return adapter;
    fallbackAdapterManifestRefs.push(adapter.manifest.component_id);
  }

  const m6 = buildM6ContractBuildLane({
    intent: {
      ...params.intent,
      worker: primary,
      fallback_chain: fallbackChain,
    },
    registry,
    worker: primary,
    now,
  });
  if (!m6.ok) {
    return {
      ok: false,
      status:
        m6.status === "FAIL_M6_RAW_MODEL_AUTHORITY_BYPASS"
          ? "FAIL_M7_RAW_MODEL_AUTHORITY_BYPASS"
          : "FAIL_M7_CONTRACT_BUILD_LANE_REJECTED",
      reason: m6.reason,
      m6_status: m6.status,
    };
  }

  if (m6.lane.delivery_mode !== M6_DELIVERY_MODE) {
    return {
      ok: false,
      status: "HOLD_M7_FALLBACK_DELIVERY_MODE_CHANGED",
      reason: `contract-build lane delivery mode changed to ${m6.lane.delivery_mode}`,
    };
  }
  if (m6.lane.authority_mode !== M6_AUTHORITY_MODE) {
    return {
      ok: false,
      status: "HOLD_M7_FALLBACK_AUTHORITY_MODE_CHANGED",
      reason: `contract-build lane authority mode changed to ${m6.lane.authority_mode}`,
    };
  }

  return {
    ok: true,
    status: "PASS_M7_MODEL_ELIGIBILITY_VERIFIED",
    primary_worker: primary,
    fallback_chain: fallbackChain,
    primary_adapter_id: primaryAdapterId,
    fallback_adapter_ids: fallbackChain.map(routeAdapterId),
    m6,
    evidence: {
      primary_manifest: primaryManifest.manifest.component_id,
      primary_adapter_manifest: primaryAdapter.manifest.component_id,
      fallback_manifest_refs: fallbackManifestRefs,
      fallback_adapter_manifest_refs: fallbackAdapterManifestRefs,
      verifiedRoute_preserved: true,
      contractEnvelope_preserved: true,
      deliveryReceipt_no_send_preserved: true,
      terminalCloseout_preserved: true,
      worker_model_route_authority: false,
    },
  };
}

export function buildM7ValidIntent(overrides: M6RouteIntentInput = {}): M6RouteIntentInput {
  return {
    source: "m2_owner_turn_route_admission",
    owner_scope: "owner_turn",
    requested: M6_BROKER_ROUTE,
    executable: M6_BROKER_ROUTE,
    worker: M7_DEFAULT_PRIMARY_WORKER,
    fallback_chain: [M7_DEFAULT_FALLBACK_WORKER],
    session_model_pin: { provider: "openai", model: "gpt-5.5" },
    channel_model_pin: { provider: "openai-codex", model: "gpt-5.5" },
    turn_id: "m7-fixture-turn",
    session_id: "m7-fixture-session",
    channel: "telegram",
    contract_envelope_ref: "ContractEnvelope:m7-model-eligibility",
    ...overrides,
  };
}

export const M7_POLICY_BOUNDARY_COUNTERS = Object.freeze({
  telegram_send_probe_count: 0,
  external_send_count: 0,
  provider_model_live_call_count: 0,
  route_config_mutation_count: 0,
  durable_memory_mutation_count: 0,
  context_bridge_mutation_count: 0,
  production_authority_change_count: 0,
  cron_reenable_count: 0,
  m8_started: false,
  enforcement_enabled: false,
});
