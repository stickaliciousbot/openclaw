import {
  DELIVERY_MODE as M3_DELIVERY_MODE,
  runM3EnvelopeSupervisor,
} from "./umc-m3-envelope-supervision.ts";
import {
  M4_AUTHORITY_MODE,
  M4_CONTRACT_VERSION,
  type M4RouteIntent,
  type M4RouteRef,
} from "./umc-m4-verified-route.ts";
import {
  buildM5NoSendManifest,
  buildM5SeedManifests,
  componentIdForRoute,
  createM5CapabilityRegistry,
  routeKey,
  type M5CapabilityManifest,
  type M5CapabilityRegistry,
  verifyM5RouteEligibility,
} from "./umc-m5-capability-manifest.ts";

export const M6_MILESTONE = "M6_TOKEN_BROKER_VMESH_CONTRACT_BUILD_LANE_SOURCE_NO_APPLY" as const;
export const M6_LANE_ID = "token-broker-vmesh/contract-build" as const;
export const M6_LANE_VERSION = "umc.v1.m6.contract_build_lane.v1" as const;
export const M6_CONTRACT_VERSION = "umc.v1.m6" as const;
export const M6_AUTHORITY_MODE = "observe_only" as const;
export const M6_VERIFIED_ROUTE_AUTHORITY_MODE = M4_AUTHORITY_MODE;
export const M6_DELIVERY_MODE = M3_DELIVERY_MODE;
export const M6_OWNER_SCOPE = "owner_turn" as const;
export const M6_DEFAULT_WORKER: M4RouteRef = Object.freeze({
  provider: "openai-codex",
  model: "gpt-5.5",
});
export const M6_BROKER_ROUTE: M4RouteRef = Object.freeze({
  provider: "token-broker-vmesh",
  model: "contract-build",
});

export type M6WorkerModelPolicy = {
  worker_role: "execution_worker";
  route_authority: false;
  requires_verified_route: true;
  requires_capability_manifest: true;
  requires_contract_envelope: true;
  delivery_mode: typeof M6_DELIVERY_MODE;
  authority_mode: typeof M6_AUTHORITY_MODE;
  worker: M4RouteRef;
};

export type M6ContractBuildLaneSpec = {
  lane_id: typeof M6_LANE_ID;
  lane_version: typeof M6_LANE_VERSION;
  contract_version: typeof M6_CONTRACT_VERSION;
  authority_mode: typeof M6_AUTHORITY_MODE;
  verified_route_authority_mode: typeof M6_VERIFIED_ROUTE_AUTHORITY_MODE;
  delivery_mode: typeof M6_DELIVERY_MODE;
  eligible_owner_scope: typeof M6_OWNER_SCOPE;
  route_intent_input: "m2_owner_turn_route_admission";
  verified_route_requirement: "required_before_execution";
  contract_envelope_requirement: "required";
  capability_manifest_requirement: "required_for_broker_worker_and_fallbacks";
  fallback_chain_requirement: "must_preserve_contract";
  worker_model_policy: M6WorkerModelPolicy;
  tool_policy: {
    real_write_tools: "blocked";
    provider_model_live_calls: "forbidden_in_source_fixture";
    external_sends: "forbidden";
  };
  postcondition_policy: {
    terminal_closeout_required: true;
    no_send_delivery_required: true;
    zero_forbidden_counters_required: true;
  };
  delivery_policy: {
    mode: typeof M6_DELIVERY_MODE;
    telegram_send_probe_authorized: false;
    external_send_authorized: false;
  };
  terminal_closeout_policy: { required: true };
  safety_counter_policy: {
    telegram_send_probe_count: 0;
    external_send_count: 0;
    provider_model_live_call_count: 0;
    route_config_mutation_count: 0;
    durable_memory_mutation_count: 0;
    context_bridge_mutation_count: 0;
    production_authority_change_count: 0;
    enforcement_enabled: false;
  };
  explicit_invariants: string[];
};

export type M6BuildStatus =
  | "PASS_M6_CONTRACT_BUILD_LANE_BUILT"
  | "HOLD_M6_CAPABILITY_MANIFEST_MISSING"
  | "HOLD_M6_CAPABILITY_UNSUPPORTED"
  | "HOLD_M6_MISSING_VERIFIED_ROUTE"
  | "HOLD_M6_FALLBACK_CONTRACT_NOT_PRESERVED"
  | "FAIL_M6_RAW_MODEL_AUTHORITY_BYPASS"
  | "FAIL_M6_INVALID_ROUTE_INTENT";

export type M6RouteIntentInput = {
  source?: string;
  owner_scope?: string;
  requested?: Partial<M4RouteRef>;
  executable?: Partial<M4RouteRef>;
  worker?: Partial<M4RouteRef>;
  fallback_chain?: Partial<M4RouteRef>[];
  session_model_pin?: Partial<M4RouteRef>;
  channel_model_pin?: Partial<M4RouteRef>;
  turn_id?: string;
  session_id?: string;
  channel?: string;
  contract_envelope_ref?: string;
};

export type M6ContractBuildLaneResult =
  | {
      ok: true;
      status: "PASS_M6_CONTRACT_BUILD_LANE_BUILT";
      lane: {
        lane_id: typeof M6_LANE_ID;
        lane_version: typeof M6_LANE_VERSION;
        contract_version: typeof M6_CONTRACT_VERSION;
        authority_mode: typeof M6_AUTHORITY_MODE;
        verified_route_authority_mode: typeof M6_VERIFIED_ROUTE_AUTHORITY_MODE;
        delivery_mode: typeof M6_DELIVERY_MODE;
        broker_route: M4RouteRef;
        worker: M4RouteRef;
        worker_route_authority: false;
        verifiedRoute: unknown;
        manifest_refs: string[];
        contractEnvelope: unknown;
        deliveryReceipt: unknown;
        terminalCloseout: unknown;
        fallback_chain: M4RouteRef[];
        route_intent_metadata: Record<string, unknown>;
      };
      receipts: ReturnType<typeof runM3EnvelopeSupervisor>["receipts"];
    }
  | {
      ok: false;
      status: Exclude<M6BuildStatus, "PASS_M6_CONTRACT_BUILD_LANE_BUILT">;
      reason: string;
      route_intent_metadata?: Record<string, unknown>;
      m5_status?: string;
      m4_status?: string;
    };

function normalizeRoute(value: Partial<M4RouteRef> | undefined): M4RouteRef | null {
  const provider =
    typeof value?.provider === "string" && value.provider.trim() ? value.provider : null;
  const model = typeof value?.model === "string" && value.model.trim() ? value.model : null;
  return provider && model ? { provider, model } : null;
}

export function buildM6ContractBuildLaneSpec(
  worker: M4RouteRef = M6_DEFAULT_WORKER,
): M6ContractBuildLaneSpec {
  return {
    lane_id: M6_LANE_ID,
    lane_version: M6_LANE_VERSION,
    contract_version: M6_CONTRACT_VERSION,
    authority_mode: M6_AUTHORITY_MODE,
    verified_route_authority_mode: M6_VERIFIED_ROUTE_AUTHORITY_MODE,
    delivery_mode: M6_DELIVERY_MODE,
    eligible_owner_scope: M6_OWNER_SCOPE,
    route_intent_input: "m2_owner_turn_route_admission",
    verified_route_requirement: "required_before_execution",
    contract_envelope_requirement: "required",
    capability_manifest_requirement: "required_for_broker_worker_and_fallbacks",
    fallback_chain_requirement: "must_preserve_contract",
    worker_model_policy: {
      worker_role: "execution_worker",
      route_authority: false,
      requires_verified_route: true,
      requires_capability_manifest: true,
      requires_contract_envelope: true,
      delivery_mode: M6_DELIVERY_MODE,
      authority_mode: M6_AUTHORITY_MODE,
      worker,
    },
    tool_policy: {
      real_write_tools: "blocked",
      provider_model_live_calls: "forbidden_in_source_fixture",
      external_sends: "forbidden",
    },
    postcondition_policy: {
      terminal_closeout_required: true,
      no_send_delivery_required: true,
      zero_forbidden_counters_required: true,
    },
    delivery_policy: {
      mode: M6_DELIVERY_MODE,
      telegram_send_probe_authorized: false,
      external_send_authorized: false,
    },
    terminal_closeout_policy: { required: true },
    safety_counter_policy: {
      telegram_send_probe_count: 0,
      external_send_count: 0,
      provider_model_live_call_count: 0,
      route_config_mutation_count: 0,
      durable_memory_mutation_count: 0,
      context_bridge_mutation_count: 0,
      production_authority_change_count: 0,
      enforcement_enabled: false,
    },
    explicit_invariants: [
      "worker model is not route authority",
      "session/channel pins are route intents only",
      "fallback cannot drop VerifiedRoute",
      "fallback cannot drop ContractEnvelope",
      "fallback cannot drop capability manifest requirements",
      "fallback cannot change no_send delivery mode",
      "fallback cannot change observe_only authority mode",
    ],
  };
}

export function buildM6ContractBuildManifests(
  now = "2026-07-16T02:10:00.000Z",
): M5CapabilityManifest[] {
  return [
    buildM5NoSendManifest({
      component_id: componentIdForRoute(M6_BROKER_ROUTE),
      component_type: "model",
      provider: M6_BROKER_ROUTE.provider,
      model: M6_BROKER_ROUTE.model,
      verified_at: now,
      evidence_refs: ["M6_CONTRACT_BUILD_LANE_SPEC.json"],
    }),
    buildM5NoSendManifest({
      component_id: `lane:${M6_LANE_ID}`,
      component_type: "lane",
      lane_id: M6_LANE_ID,
      verified_at: now,
      evidence_refs: ["M6_CONTRACT_BUILD_LANE_SPEC.json"],
      allowed_tool_classes: ["fixture_only", "read_only"],
      disallowed_tool_classes: [
        "external_send",
        "provider_live_call",
        "durable_memory_write",
        "context_bridge_write",
        "production_authority_change",
      ],
    }),
  ];
}

export function createM6CapabilityRegistry(now?: string): M5CapabilityRegistry {
  return createM5CapabilityRegistry([
    ...buildM5SeedManifests(now),
    ...buildM6ContractBuildManifests(now),
  ]);
}

function isRawProviderAuthorityBypass(input: M6RouteIntentInput, brokerRoute: M4RouteRef): boolean {
  const executable = normalizeRoute(input.executable);
  const requested = normalizeRoute(input.requested);
  if (executable && routeKey(executable) !== routeKey(brokerRoute)) {
    return true;
  }
  return !executable && requested !== null && routeKey(requested) !== routeKey(brokerRoute);
}

function normalizeFallbacks(input: M6RouteIntentInput, worker: M4RouteRef): M4RouteRef[] {
  const explicit = (input.fallback_chain ?? []).map(normalizeRoute).filter(Boolean) as M4RouteRef[];
  const routes = [worker, ...explicit];
  const seen = new Set<string>();
  return routes.filter((route) => {
    const key = routeKey(route);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

export function buildM6ContractBuildLane(params: {
  intent: M6RouteIntentInput;
  registry?: M5CapabilityRegistry;
  worker?: M4RouteRef;
  now?: string;
}): M6ContractBuildLaneResult {
  const now = params.now ?? new Date().toISOString();
  const worker = normalizeRoute(params.worker) ?? M6_DEFAULT_WORKER;
  const brokerRoute = M6_BROKER_ROUTE;
  const registry = params.registry ?? createM6CapabilityRegistry(now);
  const spec = buildM6ContractBuildLaneSpec(worker);
  const routeIntentMetadata = {
    source: params.intent.source,
    requested: params.intent.requested ?? null,
    executable: params.intent.executable ?? null,
    session_model_pin: params.intent.session_model_pin ?? null,
    channel_model_pin: params.intent.channel_model_pin ?? null,
    session_channel_pins_are_route_intent_only: true,
    worker_route_authority: false,
  };

  if (params.intent.source !== "m2_owner_turn_route_admission") {
    return {
      ok: false,
      status: "FAIL_M6_INVALID_ROUTE_INTENT",
      reason: "M6 contract-build lane accepts only M2 owner-turn route admission input",
      route_intent_metadata: routeIntentMetadata,
    };
  }
  if (params.intent.owner_scope !== M6_OWNER_SCOPE) {
    return {
      ok: false,
      status: "FAIL_M6_INVALID_ROUTE_INTENT",
      reason: "M6 contract-build lane requires owner_turn scope",
      route_intent_metadata: routeIntentMetadata,
    };
  }
  if (isRawProviderAuthorityBypass(params.intent, brokerRoute)) {
    return {
      ok: false,
      status: "FAIL_M6_RAW_MODEL_AUTHORITY_BYPASS",
      reason:
        "raw provider/model cannot become M6 route authority; broker contract-build lane is required",
      route_intent_metadata: routeIntentMetadata,
    };
  }

  const fallbackChain = normalizeFallbacks(params.intent, worker);
  const m5Intent: M4RouteIntent = {
    // M6 composes from an M2 owner-turn admission; keep the M4 authority source
    // as the M2 admission vocabulary so M6 cannot invent a new raw route authority.
    source: "m2_queued_route_admission",
    turn_id: params.intent.turn_id,
    session_id: params.intent.session_id,
    channel: params.intent.channel,
    owner_scope: params.intent.owner_scope,
    requested: normalizeRoute(params.intent.requested) ?? brokerRoute,
    executable: brokerRoute,
    fallback_chain: fallbackChain,
    contract_version: M4_CONTRACT_VERSION,
    authority_mode: M4_AUTHORITY_MODE,
    contract_envelope_ref:
      params.intent.contract_envelope_ref ?? "ContractEnvelope:m6-contract-build-lane",
    verification_reason: "M6 contract-build lane verified via M5 manifests and M4 VerifiedRoute",
  };
  const m5 = verifyM5RouteEligibility({ registry, intent: m5Intent, now });
  if (!m5.ok) {
    const holdStatus =
      m5.status === "HOLD_M5_CAPABILITY_MANIFEST_MISSING"
        ? "HOLD_M6_CAPABILITY_MANIFEST_MISSING"
        : m5.status === "HOLD_M5_CAPABILITY_UNSUPPORTED"
          ? "HOLD_M6_CAPABILITY_UNSUPPORTED"
          : "HOLD_M6_FALLBACK_CONTRACT_NOT_PRESERVED";
    return {
      ok: false,
      status: holdStatus,
      reason: m5.reason,
      route_intent_metadata: routeIntentMetadata,
      m5_status: m5.status,
    };
  }

  const m3 = runM3EnvelopeSupervisor({
    now,
    turn_id: params.intent.turn_id,
    session_id: params.intent.session_id,
    channel: params.intent.channel,
    owner_scope: params.intent.owner_scope,
    route_intent: {
      contractVersion: M6_CONTRACT_VERSION,
      milestone: M6_MILESTONE,
      source: "m6_contract_build_lane",
      requested: params.intent.requested ?? brokerRoute,
      executable: brokerRoute,
      worker,
      fallback_chain: fallbackChain,
      lane_id: M6_LANE_ID,
      worker_route_authority: false,
      capability_manifest_ref: m5.manifest_refs.join(","),
      status: m5.status,
    },
    tool_proposals: [],
    ambient_owner_chat_delivery_count: 0,
    evidence_refs: ["M6_CONTRACT_BUILD_LANE_FIXTURE_RESULTS.json"],
  });
  if (m3.result_status !== "PASS_M3_TERMINAL_CONTRACT_CLOSEOUT_EMITTED") {
    return {
      ok: false,
      status: "HOLD_M6_MISSING_VERIFIED_ROUTE",
      reason: `M3 terminal closeout did not pass: ${m3.result_status}`,
      route_intent_metadata: routeIntentMetadata,
      m5_status: m5.status,
    };
  }

  return {
    ok: true,
    status: "PASS_M6_CONTRACT_BUILD_LANE_BUILT",
    lane: {
      lane_id: spec.lane_id,
      lane_version: spec.lane_version,
      contract_version: spec.contract_version,
      authority_mode: spec.authority_mode,
      verified_route_authority_mode: spec.verified_route_authority_mode,
      delivery_mode: spec.delivery_mode,
      broker_route: brokerRoute,
      worker,
      worker_route_authority: false,
      verifiedRoute: m5.verifiedRoute,
      manifest_refs: m5.manifest_refs,
      contractEnvelope: m3.receipts.envelope,
      deliveryReceipt: m3.receipts.deliveryReceipt,
      terminalCloseout: m3.receipts.terminalCloseout,
      fallback_chain: fallbackChain,
      route_intent_metadata: routeIntentMetadata,
    },
    receipts: m3.receipts,
  };
}
