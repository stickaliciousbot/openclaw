import {
  M4_AUTHORITY_MODE,
  M4_CONTRACT_VERSION,
  type M4RouteIntent,
  type M4RouteRef,
  type M4RouteVerifierResult,
  verifyM4RouteIntent,
} from "./umc-m4-verified-route.ts";

export const M5_CAPABILITY_MANIFEST_VERSION = "umc.v1.m5.capability_manifest.v1" as const;
export const M5_REGISTRY_VERSION = "umc.v1.m5.capability_manifest_registry.v1" as const;
export const M5_MILESTONE = "M5_CAPABILITY_MANIFEST_REGISTRY_NO_SEND" as const;
export const M5_REQUIRED_DELIVERY_MODE = "no_send" as const;
export const M5_REQUIRED_AUTHORITY_MODE = M4_AUTHORITY_MODE;

export type M5ComponentType =
  | "model"
  | "provider"
  | "adapter"
  | "lane"
  | "fallback_chain"
  | "tool_runtime";

export type M5MemoryPolicy = "no_durable_mutation" | "read_only";
export type M5ContextBridgePolicy = "no_mutation" | "read_only";
export type M5ExternalSendPolicy = "denied";

export type M5CapabilityManifest = {
  manifest_version: typeof M5_CAPABILITY_MANIFEST_VERSION;
  component_id: string;
  component_type: M5ComponentType;
  provider?: string;
  model?: string;
  adapter_id?: string;
  lane_id?: string;
  supports_verified_route: boolean;
  supports_contract_envelope: boolean;
  supports_shadow_observation_receipt: boolean;
  supports_universal_contract_receipt: boolean;
  supports_delivery_receipt: boolean;
  supported_delivery_modes: string[];
  supports_terminal_closeout: boolean;
  supports_tool_supervision: boolean;
  supports_postcondition_policy: boolean;
  supports_no_send: boolean;
  supports_fallback_contract_preservation: boolean;
  supports_observe_only: boolean;
  supports_enforcement: boolean;
  authority_modes: string[];
  allowed_tool_classes: string[];
  disallowed_tool_classes: string[];
  memory_policy: M5MemoryPolicy;
  context_bridge_policy: M5ContextBridgePolicy;
  external_send_policy: M5ExternalSendPolicy;
  verified_by: string;
  verified_at: string;
  evidence_refs: string[];
};

export type M5RequiredCapabilities = {
  verifiedRoute: boolean;
  contractEnvelope: boolean;
  shadowObservationReceipt: boolean;
  universalContractReceipt: boolean;
  deliveryReceipt: boolean;
  deliveryMode: typeof M5_REQUIRED_DELIVERY_MODE;
  terminalCloseout: boolean;
  toolSupervision: boolean;
  postconditionPolicy: boolean;
  noSend: boolean;
  fallbackContractPreservation: boolean;
  observeOnly: boolean;
  authorityMode: typeof M5_REQUIRED_AUTHORITY_MODE;
};

export const M5_REQUIRED_CAPABILITIES: M5RequiredCapabilities = Object.freeze({
  verifiedRoute: true,
  contractEnvelope: true,
  shadowObservationReceipt: true,
  universalContractReceipt: true,
  deliveryReceipt: true,
  deliveryMode: M5_REQUIRED_DELIVERY_MODE,
  terminalCloseout: true,
  toolSupervision: true,
  postconditionPolicy: true,
  noSend: true,
  fallbackContractPreservation: true,
  observeOnly: true,
  authorityMode: M5_REQUIRED_AUTHORITY_MODE,
});

export type M5ManifestStatus =
  | "PASS_M5_CAPABILITY_MANIFEST_ACCEPTED"
  | "HOLD_M5_CAPABILITY_MANIFEST_MISSING"
  | "HOLD_M5_CAPABILITY_UNSUPPORTED"
  | "FAIL_M5_CAPABILITY_MANIFEST_INVALID";

export type M5RouteEligibilityStatus =
  | "PASS_M5_ROUTE_ELIGIBILITY_VERIFIED"
  | "HOLD_M5_CAPABILITY_MANIFEST_MISSING"
  | "HOLD_M5_CAPABILITY_UNSUPPORTED"
  | "FAIL_M5_CAPABILITY_MANIFEST_INVALID"
  | "FAIL_M5_ROUTE_ELIGIBILITY_M4_REJECTED";

export type M5AcceptedManifest = {
  ok: true;
  status: "PASS_M5_CAPABILITY_MANIFEST_ACCEPTED";
  manifest: M5CapabilityManifest;
  normalized: M5CapabilityManifest;
  evidence_refs: string[];
};

export type M5RejectedManifest = {
  ok: false;
  status: Exclude<M5ManifestStatus, "PASS_M5_CAPABILITY_MANIFEST_ACCEPTED">;
  component_id?: string;
  reason: string;
  missing_fields?: string[];
  unsupported_capabilities?: string[];
  manifest?: Partial<M5CapabilityManifest>;
};

export type M5ManifestValidationResult = M5AcceptedManifest | M5RejectedManifest;

export type M5CapabilityRegistry = {
  registry_version: typeof M5_REGISTRY_VERSION;
  manifests: Map<string, M5CapabilityManifest>;
  accepted: M5AcceptedManifest[];
  rejected: M5RejectedManifest[];
};

export type M5RouteEligibilityResult =
  | {
      ok: true;
      status: "PASS_M5_ROUTE_ELIGIBILITY_VERIFIED";
      manifest_refs: string[];
      m4: Extract<M4RouteVerifierResult, { ok: true }>;
      verifiedRoute: Extract<M4RouteVerifierResult, { ok: true }>["verifiedRoute"];
    }
  | {
      ok: false;
      status: Exclude<M5RouteEligibilityStatus, "PASS_M5_ROUTE_ELIGIBILITY_VERIFIED">;
      reason: string;
      manifest_refs?: string[];
      manifest_result?: M5RejectedManifest;
      m4?: M4RouteVerifierResult;
    };

const COMPONENT_TYPES = new Set<M5ComponentType>([
  "model",
  "provider",
  "adapter",
  "lane",
  "fallback_chain",
  "tool_runtime",
]);

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function normalizeString(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function normalizeBoolean(value: unknown, defaultValue = false): boolean {
  return typeof value === "boolean" ? value : defaultValue;
}

function normalizeStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return [...new Set(value.map(normalizeString).filter(Boolean) as string[])];
}

function normalizeComponentId(manifest: Pick<M5CapabilityManifest, "component_id">): string {
  return manifest.component_id;
}

export function routeKey(route: Pick<M4RouteRef, "provider" | "model">): string {
  return `${route.provider}/${route.model}`;
}

export function componentIdForRoute(route: Pick<M4RouteRef, "provider" | "model">): string {
  return `model:${routeKey(route)}`;
}

export function normalizeM5CapabilityManifest(input: unknown): M5CapabilityManifest | null {
  const record = asRecord(input);
  if (!record) {
    return null;
  }

  const componentType = normalizeString(record.component_type) as M5ComponentType | undefined;
  const componentId = normalizeString(record.component_id);
  if (!componentId || !componentType || !COMPONENT_TYPES.has(componentType)) {
    return null;
  }

  return {
    manifest_version: M5_CAPABILITY_MANIFEST_VERSION,
    component_id: componentId,
    component_type: componentType,
    provider: normalizeString(record.provider),
    model: normalizeString(record.model),
    adapter_id: normalizeString(record.adapter_id),
    lane_id: normalizeString(record.lane_id),
    supports_verified_route: normalizeBoolean(record.supports_verified_route),
    supports_contract_envelope: normalizeBoolean(record.supports_contract_envelope),
    supports_shadow_observation_receipt: normalizeBoolean(
      record.supports_shadow_observation_receipt,
    ),
    supports_universal_contract_receipt: normalizeBoolean(
      record.supports_universal_contract_receipt,
    ),
    supports_delivery_receipt: normalizeBoolean(record.supports_delivery_receipt),
    supported_delivery_modes: normalizeStringArray(record.supported_delivery_modes),
    supports_terminal_closeout: normalizeBoolean(record.supports_terminal_closeout),
    supports_tool_supervision: normalizeBoolean(record.supports_tool_supervision),
    supports_postcondition_policy: normalizeBoolean(record.supports_postcondition_policy),
    supports_no_send: normalizeBoolean(record.supports_no_send),
    supports_fallback_contract_preservation: normalizeBoolean(
      record.supports_fallback_contract_preservation,
    ),
    supports_observe_only: normalizeBoolean(record.supports_observe_only),
    supports_enforcement: normalizeBoolean(record.supports_enforcement, false),
    authority_modes: normalizeStringArray(record.authority_modes),
    allowed_tool_classes: normalizeStringArray(record.allowed_tool_classes),
    disallowed_tool_classes: normalizeStringArray(record.disallowed_tool_classes),
    memory_policy: record.memory_policy === "read_only" ? "read_only" : "no_durable_mutation",
    context_bridge_policy:
      record.context_bridge_policy === "read_only" ? "read_only" : "no_mutation",
    external_send_policy: "denied",
    verified_by: normalizeString(record.verified_by) ?? "umc_m5_source_fixture",
    verified_at: normalizeString(record.verified_at) ?? "1970-01-01T00:00:00.000Z",
    evidence_refs: normalizeStringArray(record.evidence_refs),
  };
}

function requiredFieldFailures(manifest: M5CapabilityManifest): string[] {
  const missing: string[] = [];
  if (!manifest.manifest_version) missing.push("manifest_version");
  if (!manifest.component_id) missing.push("component_id");
  if (!manifest.component_type) missing.push("component_type");
  if (!manifest.verified_by) missing.push("verified_by");
  if (!manifest.verified_at) missing.push("verified_at");
  if (!Array.isArray(manifest.evidence_refs) || manifest.evidence_refs.length === 0) {
    missing.push("evidence_refs");
  }
  if (manifest.component_type === "model" && (!manifest.provider || !manifest.model)) {
    missing.push("provider/model");
  }
  return missing;
}

function unsupportedCapabilities(
  manifest: M5CapabilityManifest,
  required = M5_REQUIRED_CAPABILITIES,
): string[] {
  const unsupported: string[] = [];
  if (required.verifiedRoute && !manifest.supports_verified_route) {
    unsupported.push("supports_verified_route");
  }
  if (required.contractEnvelope && !manifest.supports_contract_envelope) {
    unsupported.push("supports_contract_envelope");
  }
  if (required.shadowObservationReceipt && !manifest.supports_shadow_observation_receipt) {
    unsupported.push("supports_shadow_observation_receipt");
  }
  if (required.universalContractReceipt && !manifest.supports_universal_contract_receipt) {
    unsupported.push("supports_universal_contract_receipt");
  }
  if (required.deliveryReceipt && !manifest.supports_delivery_receipt) {
    unsupported.push("supports_delivery_receipt");
  }
  if (!manifest.supported_delivery_modes.includes(required.deliveryMode)) {
    unsupported.push("supported_delivery_modes:no_send");
  }
  if (required.terminalCloseout && !manifest.supports_terminal_closeout) {
    unsupported.push("supports_terminal_closeout");
  }
  if (required.toolSupervision && !manifest.supports_tool_supervision) {
    unsupported.push("supports_tool_supervision");
  }
  if (required.postconditionPolicy && !manifest.supports_postcondition_policy) {
    unsupported.push("supports_postcondition_policy");
  }
  if (required.noSend && !manifest.supports_no_send) {
    unsupported.push("supports_no_send");
  }
  if (required.fallbackContractPreservation && !manifest.supports_fallback_contract_preservation) {
    unsupported.push("supports_fallback_contract_preservation");
  }
  if (required.observeOnly && !manifest.supports_observe_only) {
    unsupported.push("supports_observe_only");
  }
  if (!manifest.authority_modes.includes(required.authorityMode)) {
    unsupported.push("authority_modes:observe_only_no_send");
  }
  return unsupported;
}

function contradictoryManifestFailures(manifest: M5CapabilityManifest): string[] {
  const failures: string[] = [];
  if (manifest.manifest_version !== M5_CAPABILITY_MANIFEST_VERSION) {
    failures.push("manifest_version");
  }
  if (manifest.supports_enforcement) {
    failures.push("supports_enforcement must remain false for M5");
  }
  if (manifest.external_send_policy !== "denied") {
    failures.push("external_send_policy must be denied");
  }
  if (manifest.memory_policy !== "no_durable_mutation" && manifest.memory_policy !== "read_only") {
    failures.push("memory_policy");
  }
  if (
    manifest.context_bridge_policy !== "no_mutation" &&
    manifest.context_bridge_policy !== "read_only"
  ) {
    failures.push("context_bridge_policy");
  }
  if (manifest.authority_modes.some((mode) => mode !== M5_REQUIRED_AUTHORITY_MODE)) {
    failures.push("authority_modes cannot grant production authority");
  }
  return failures;
}

export function validateM5CapabilityManifest(
  input: unknown,
  required = M5_REQUIRED_CAPABILITIES,
): M5ManifestValidationResult {
  const normalized = normalizeM5CapabilityManifest(input);
  if (!normalized) {
    return {
      ok: false,
      status: "FAIL_M5_CAPABILITY_MANIFEST_INVALID",
      reason: "manifest is not an object with valid component_id and component_type",
    };
  }

  const missing = requiredFieldFailures(normalized);
  if (missing.length > 0) {
    return {
      ok: false,
      status: "FAIL_M5_CAPABILITY_MANIFEST_INVALID",
      component_id: normalized.component_id,
      reason: `manifest missing required fields: ${missing.join(", ")}`,
      missing_fields: missing,
      manifest: normalized,
    };
  }

  const contradictions = contradictoryManifestFailures(normalized);
  if (contradictions.length > 0) {
    return {
      ok: false,
      status: "FAIL_M5_CAPABILITY_MANIFEST_INVALID",
      component_id: normalized.component_id,
      reason: `manifest is contradictory or authority-expanding: ${contradictions.join(", ")}`,
      unsupported_capabilities: contradictions,
      manifest: normalized,
    };
  }

  const unsupported = unsupportedCapabilities(normalized, required);
  if (unsupported.length > 0) {
    return {
      ok: false,
      status: "HOLD_M5_CAPABILITY_UNSUPPORTED",
      component_id: normalized.component_id,
      reason: `manifest lacks M5 no-send capability: ${unsupported.join(", ")}`,
      unsupported_capabilities: unsupported,
      manifest: normalized,
    };
  }

  return {
    ok: true,
    status: "PASS_M5_CAPABILITY_MANIFEST_ACCEPTED",
    manifest: normalized,
    normalized,
    evidence_refs: normalized.evidence_refs,
  };
}

export function createM5CapabilityRegistry(inputs: readonly unknown[]): M5CapabilityRegistry {
  const manifests = new Map<string, M5CapabilityManifest>();
  const accepted: M5AcceptedManifest[] = [];
  const rejected: M5RejectedManifest[] = [];

  for (const input of inputs) {
    const result = validateM5CapabilityManifest(input);
    if (result.ok) {
      const id = normalizeComponentId(result.manifest);
      if (manifests.has(id)) {
        rejected.push({
          ok: false,
          status: "FAIL_M5_CAPABILITY_MANIFEST_INVALID",
          component_id: id,
          reason: `duplicate manifest for ${id}`,
          manifest: result.manifest,
        });
        continue;
      }
      manifests.set(id, result.manifest);
      accepted.push(result);
      continue;
    }
    rejected.push(result);
  }

  return {
    registry_version: M5_REGISTRY_VERSION,
    manifests,
    accepted,
    rejected,
  };
}

export function getM5ManifestForComponent(
  registry: M5CapabilityRegistry,
  componentId: string,
): M5AcceptedManifest | M5RejectedManifest {
  const manifest = registry.manifests.get(componentId);
  if (!manifest) {
    return {
      ok: false,
      status: "HOLD_M5_CAPABILITY_MANIFEST_MISSING",
      component_id: componentId,
      reason: `missing M5 capability manifest for ${componentId}`,
    };
  }
  return {
    ok: true,
    status: "PASS_M5_CAPABILITY_MANIFEST_ACCEPTED",
    manifest,
    normalized: manifest,
    evidence_refs: manifest.evidence_refs,
  };
}

function normalizeRoute(value: Partial<M4RouteRef> | undefined): M4RouteRef | null {
  const provider = normalizeString(value?.provider);
  const model = normalizeString(value?.model);
  return provider && model ? { provider, model } : null;
}

function collectRouteManifestRefs(
  registry: M5CapabilityRegistry,
  routes: readonly M4RouteRef[],
): { ok: true; manifest_refs: string[] } | { ok: false; result: M5RejectedManifest } {
  const refs: string[] = [];
  for (const route of routes) {
    const componentId = componentIdForRoute(route);
    const manifestResult = getM5ManifestForComponent(registry, componentId);
    if (!manifestResult.ok) {
      return { ok: false, result: manifestResult };
    }
    refs.push(manifestResult.manifest.component_id);
  }
  return { ok: true, manifest_refs: refs };
}

export function verifyM5RouteEligibility(params: {
  registry: M5CapabilityRegistry;
  intent: M4RouteIntent;
  now?: string;
}): M5RouteEligibilityResult {
  const executable =
    normalizeRoute(params.intent.executable) ??
    normalizeRoute({ provider: params.intent.provider, model: params.intent.model }) ??
    normalizeRoute(params.intent.requested);
  if (!executable) {
    return {
      ok: false,
      status: "FAIL_M5_ROUTE_ELIGIBILITY_M4_REJECTED",
      reason:
        "route intent did not normalize to executable provider/model before M5 manifest check",
    };
  }

  const fallbackChain = (params.intent.fallback_chain ?? [])
    .map(normalizeRoute)
    .filter(Boolean) as M4RouteRef[];
  const routes = [
    executable,
    ...fallbackChain.filter((route) => routeKey(route) !== routeKey(executable)),
  ];
  const refs = collectRouteManifestRefs(params.registry, routes);
  if (!refs.ok) {
    return {
      ok: false,
      status: refs.result.status,
      reason: refs.result.reason,
      manifest_result: refs.result,
    };
  }

  const m4 = verifyM4RouteIntent({
    intent: {
      ...params.intent,
      capability_manifest_ref: refs.manifest_refs.join(","),
      contract_version: M4_CONTRACT_VERSION,
      authority_mode: M4_AUTHORITY_MODE,
    },
    eligibility: {
      allowedProviderModels: routes.map(routeKey),
      fallbackChain: routes,
      capabilityManifestRef: refs.manifest_refs.join(","),
    },
    now: params.now,
  });

  if (!m4.ok) {
    return {
      ok: false,
      status: "FAIL_M5_ROUTE_ELIGIBILITY_M4_REJECTED",
      reason: m4.reason,
      manifest_refs: refs.manifest_refs,
      m4,
    };
  }

  return {
    ok: true,
    status: "PASS_M5_ROUTE_ELIGIBILITY_VERIFIED",
    manifest_refs: refs.manifest_refs,
    m4,
    verifiedRoute: m4.verifiedRoute,
  };
}

export function buildM5NoSendManifest(params: {
  component_id: string;
  component_type: M5ComponentType;
  provider?: string;
  model?: string;
  adapter_id?: string;
  lane_id?: string;
  verified_by?: string;
  verified_at?: string;
  evidence_refs?: string[];
  allowed_tool_classes?: string[];
  disallowed_tool_classes?: string[];
}): M5CapabilityManifest {
  return {
    manifest_version: M5_CAPABILITY_MANIFEST_VERSION,
    component_id: params.component_id,
    component_type: params.component_type,
    provider: params.provider,
    model: params.model,
    adapter_id: params.adapter_id,
    lane_id: params.lane_id,
    supports_verified_route: true,
    supports_contract_envelope: true,
    supports_shadow_observation_receipt: true,
    supports_universal_contract_receipt: true,
    supports_delivery_receipt: true,
    supported_delivery_modes: [M5_REQUIRED_DELIVERY_MODE],
    supports_terminal_closeout: true,
    supports_tool_supervision: true,
    supports_postcondition_policy: true,
    supports_no_send: true,
    supports_fallback_contract_preservation: true,
    supports_observe_only: true,
    supports_enforcement: false,
    authority_modes: [M5_REQUIRED_AUTHORITY_MODE],
    allowed_tool_classes: params.allowed_tool_classes ?? [],
    disallowed_tool_classes: params.disallowed_tool_classes ?? [
      "external_send",
      "durable_memory_write",
    ],
    memory_policy: "no_durable_mutation",
    context_bridge_policy: "no_mutation",
    external_send_policy: "denied",
    verified_by: params.verified_by ?? "umc_m5_source_fixture",
    verified_at: params.verified_at ?? "2026-07-16T00:45:00.000Z",
    evidence_refs: params.evidence_refs ?? ["M5_CAPABILITY_MANIFEST_SCHEMA.json"],
  };
}

export function buildM5SeedManifests(now = "2026-07-16T00:45:00.000Z"): M5CapabilityManifest[] {
  return [
    buildM5NoSendManifest({
      component_id: "lane:owner-turn-primary",
      component_type: "lane",
      lane_id: "owner-turn-primary",
      verified_at: now,
      evidence_refs: ["M4_VERIFIED_ROUTE_STAGED_INSTALL_AND_REGRESSION_CLOSEOUT.json"],
    }),
    buildM5NoSendManifest({
      component_id: componentIdForRoute({ provider: "openai-codex", model: "gpt-5.5" }),
      component_type: "model",
      provider: "openai-codex",
      model: "gpt-5.5",
      verified_at: now,
      evidence_refs: ["M4_VERIFIED_ROUTE_STAGED_INSTALL_AND_REGRESSION_CLOSEOUT.json"],
    }),
    buildM5NoSendManifest({
      component_id: componentIdForRoute({ provider: "ollama", model: "deepseek-v4-pro:cloud" }),
      component_type: "model",
      provider: "ollama",
      model: "deepseek-v4-pro:cloud",
      verified_at: now,
      evidence_refs: ["M4_VERIFIED_ROUTE_INSTALL_APPROVAL_CARD_R2.json"],
    }),
    buildM5NoSendManifest({
      component_id: componentIdForRoute({ provider: "token-broker-vmesh", model: "auto" }),
      component_type: "model",
      provider: "token-broker-vmesh",
      model: "auto",
      verified_at: now,
      evidence_refs: ["M4_DIRECT_BYPASS_INSTALLED_RUNTIME_REGRESSION_RESULT.json"],
    }),
    buildM5NoSendManifest({
      component_id: "adapter:m3-envelope-supervision",
      component_type: "adapter",
      adapter_id: "m3-envelope-supervision",
      verified_at: now,
      evidence_refs: ["M3P_OWNER_TURN_SHADOW_COVERAGE_SOAK_CLOSEOUT.json"],
    }),
    buildM5NoSendManifest({
      component_id: "adapter:m4-verified-route-firewall",
      component_type: "adapter",
      adapter_id: "m4-verified-route-firewall",
      verified_at: now,
      evidence_refs: ["M4_VERIFIED_ROUTE_INSTALLED_RUNTIME_VERIFICATION.json"],
    }),
    buildM5NoSendManifest({
      component_id: "adapter:telegram-delivery-no-send-observation",
      component_type: "adapter",
      adapter_id: "telegram",
      verified_at: now,
      evidence_refs: ["M4_POST_INSTALL_STABILITY_SUMMARY.json"],
      disallowed_tool_classes: ["telegram_send", "external_send", "durable_memory_write"],
    }),
    buildM5NoSendManifest({
      component_id: "tool_runtime:supervision-boundary",
      component_type: "tool_runtime",
      adapter_id: "tool-runtime-supervision-boundary",
      verified_at: now,
      evidence_refs: ["M4_M3_POST_INSTALL_REGRESSION_RESULT.json"],
      allowed_tool_classes: ["read_only", "fixture_only"],
      disallowed_tool_classes: ["external_send", "provider_live_call", "durable_memory_write"],
    }),
  ];
}
