import crypto from "node:crypto";

export const M4_VERIFIED_ROUTE_VERSION = "umc.v1.m4.verified_route.v1" as const;
export const M4_CONTRACT_VERSION = "umc.v1" as const;
export const M4_MILESTONE = "M4_VERIFIED_ROUTE_BRANDING_AND_DIRECT_BYPASS_FIREWALL" as const;
export const M4_SIGNATURE_OR_BRAND_TOKEN = "VERIFIED_ROUTE_UMC_V1_M4" as const;
export const M4_AUTHORITY_MODE = "observe_only_no_send" as const;
export const M4_CREATED_BY = "umc_v1_m4_route_verifier" as const;

const VERIFIED_ROUTE_BRAND: unique symbol = Symbol("openclaw.umc.m4.verified_route.brand");

type VerifiedRoutePrivateBrand = {
  readonly [VERIFIED_ROUTE_BRAND]: true;
};

export type M4RouteSource =
  | "default_model_config"
  | "m2_queued_route_admission"
  | "route_verifier"
  | "fallback_candidate"
  | "mock_fixture_factory";

export type M4RouteIntentSource =
  | M4RouteSource
  | "session_model_pin"
  | "channel_model_pin"
  | "model_directive"
  | "direct_provider_model_helper"
  | "test_only_provider_invocation"
  | "unknown";

export type M4ExecutionPath =
  | "runWithModelFallback"
  | "runEmbeddedPiAgent"
  | "queued_owner_turn"
  | "telegram_direct_owner_turn"
  | "fallback_route"
  | "session_channel_model_pin"
  | "default_provider_model_config"
  | "direct_provider_model_helper"
  | "test_only_provider_invocation";

export type M4RouteRef = {
  provider: string;
  model: string;
};

export type M4RouteIntent = {
  source?: M4RouteIntentSource;
  turn_id?: string;
  session_id?: string;
  channel?: string;
  owner_scope?: "owner_turn" | "fixture" | "non_owner_or_unscoped" | string;
  provider?: string;
  model?: string;
  requested?: Partial<M4RouteRef>;
  executable?: Partial<M4RouteRef>;
  fallback_chain?: Array<Partial<M4RouteRef>>;
  capability_manifest_ref?: string;
  contract_version?: string;
  contract_envelope_ref?: string;
  authority_mode?: string;
  verification_reason?: string;
};

export type M4RouteEligibility = {
  allowedProviderModels?: readonly string[];
  allowedProviders?: readonly string[];
  fallbackChain?: readonly M4RouteRef[];
  capabilityManifestRef?: string;
};

export type M4VerifiedRouteSerializable = {
  verified_route_version: typeof M4_VERIFIED_ROUTE_VERSION;
  route_id: string;
  turn_id?: string;
  session_id?: string;
  channel?: string;
  owner_scope: "owner_turn" | "fixture" | "non_owner_or_unscoped";
  provider: string;
  model: string;
  fallback_chain: M4RouteRef[];
  capability_manifest_ref?: string;
  contract_version: typeof M4_CONTRACT_VERSION;
  contract_envelope_ref?: string;
  authority_mode: typeof M4_AUTHORITY_MODE;
  created_by: typeof M4_CREATED_BY;
  created_at: string;
  verification_reason: string;
  signature_or_brand_token: typeof M4_SIGNATURE_OR_BRAND_TOKEN;
  /** Always false in JSON/plain objects. Runtime trust requires the private symbol brand. */
  non_forgeable_brand: false;
  source: M4RouteSource;
  no_apply: true;
  production_enforcement: false;
};

export type M4VerifiedRoute = M4VerifiedRouteSerializable & VerifiedRoutePrivateBrand;

export type M4RouteVerifierStatus =
  | "PASS_M4_VERIFIED_ROUTE_BRANDED"
  | "HOLD_M4_ROUTE_INTENT_UNAVAILABLE"
  | "HOLD_M4_ROUTE_INTENT_MISSING_PROVIDER_MODEL"
  | "HOLD_M4_ROUTE_INTENT_UNSUPPORTED_PROVIDER_MODEL"
  | "HOLD_M4_ROUTE_INTENT_UNSUPPORTED_SOURCE"
  | "FAIL_M4_ROUTE_INTENT_MALFORMED";

export type M4RouteVerifierResult =
  | {
      ok: true;
      status: "PASS_M4_VERIFIED_ROUTE_BRANDED";
      verifiedRoute: M4VerifiedRoute;
    }
  | {
      ok: false;
      status: Exclude<M4RouteVerifierStatus, "PASS_M4_VERIFIED_ROUTE_BRANDED">;
      reason: string;
      intent?: M4RouteIntent;
    };

export type M4FirewallDecision =
  | {
      ok: true;
      status: "PASS_M4_VERIFIED_ROUTE_FIREWALL" | "PASS_M4_FIREWALL_NOT_SCOPED";
      reason: string;
      verifiedRoute?: M4VerifiedRoute;
    }
  | {
      ok: false;
      status:
        | "HOLD_M4_MISSING_VERIFIED_ROUTE"
        | "HOLD_M4_FORGED_OR_DESERIALIZED_VERIFIED_ROUTE"
        | "HOLD_M4_VERIFIED_ROUTE_EXECUTION_MISMATCH"
        | "HOLD_M4_FALLBACK_CONTRACT_AUTHORITY_LOST";
      reason: string;
      execution: M4RouteRef;
    };

const ROUTE_AUTHORITY_SOURCES = new Set<M4RouteSource>([
  "default_model_config",
  "m2_queued_route_admission",
  "route_verifier",
  "fallback_candidate",
  "mock_fixture_factory",
]);

function normalizePart(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function normalizeScope(value: unknown): M4VerifiedRouteSerializable["owner_scope"] {
  if (value === "owner_turn" || value === "fixture" || value === "non_owner_or_unscoped") {
    return value;
  }
  return "non_owner_or_unscoped";
}

function normalizeRouteRef(value: Partial<M4RouteRef> | undefined): M4RouteRef | undefined {
  const provider = normalizePart(value?.provider);
  const model = normalizePart(value?.model);
  if (!provider || !model) {
    return undefined;
  }
  return { provider, model };
}

function routeKey(route: M4RouteRef): string {
  return `${route.provider}/${route.model}`;
}

function sameRoute(a: M4RouteRef, b: M4RouteRef): boolean {
  return routeKey(a) === routeKey(b);
}

function normalizeFallbackChain(
  primary: M4RouteRef,
  chain: readonly Partial<M4RouteRef>[] | undefined,
): M4RouteRef[] {
  const normalized = (chain ?? [])
    .map((entry) => normalizeRouteRef(entry))
    .filter(Boolean) as M4RouteRef[];
  if (normalized.length === 0 || !sameRoute(normalized[0], primary)) {
    return [primary, ...normalized.filter((entry) => !sameRoute(entry, primary))];
  }
  return normalized;
}

function routeId(params: {
  turnId?: string;
  sessionId?: string;
  channel?: string;
  provider: string;
  model: string;
  contractEnvelopeRef?: string;
  createdAt: string;
}): string {
  const hash = crypto
    .createHash("sha256")
    .update(
      JSON.stringify({
        turnId: params.turnId,
        sessionId: params.sessionId,
        channel: params.channel,
        provider: params.provider,
        model: params.model,
        contractEnvelopeRef: params.contractEnvelopeRef,
        createdAt: params.createdAt,
      }),
    )
    .digest("hex")
    .slice(0, 24);
  return `m4vr_${hash}`;
}

function isProviderModelAllowed(route: M4RouteRef, eligibility?: M4RouteEligibility): boolean {
  const allowedProviderModels = eligibility?.allowedProviderModels;
  if (allowedProviderModels && allowedProviderModels.length > 0) {
    return allowedProviderModels.includes(routeKey(route));
  }
  const allowedProviders = eligibility?.allowedProviders;
  if (allowedProviders && allowedProviders.length > 0) {
    return allowedProviders.includes(route.provider);
  }
  return true;
}

function isRouteAuthoritySource(source: unknown): source is M4RouteSource {
  return typeof source === "string" && ROUTE_AUTHORITY_SOURCES.has(source as M4RouteSource);
}

export function isM4VerifiedRoute(value: unknown): value is M4VerifiedRoute {
  return (
    Boolean(value) &&
    typeof value === "object" &&
    (value as Partial<M4VerifiedRoute>)[VERIFIED_ROUTE_BRAND] === true &&
    (value as Partial<M4VerifiedRoute>).verified_route_version === M4_VERIFIED_ROUTE_VERSION &&
    (value as Partial<M4VerifiedRoute>).signature_or_brand_token === M4_SIGNATURE_OR_BRAND_TOKEN &&
    (value as Partial<M4VerifiedRoute>).created_by === M4_CREATED_BY &&
    (value as Partial<M4VerifiedRoute>).non_forgeable_brand === false
  );
}

export function serializeM4VerifiedRoute(route: M4VerifiedRoute): M4VerifiedRouteSerializable {
  const { [VERIFIED_ROUTE_BRAND]: _brand, ...serializable } = route;
  return serializable;
}

export function verifyM4RouteIntent(params: {
  intent?: M4RouteIntent | null;
  eligibility?: M4RouteEligibility;
  now?: string;
  createdBy?: typeof M4_CREATED_BY | "umc_v1_m4_mock_fixture_factory";
}): M4RouteVerifierResult {
  const intent = params.intent;
  if (!intent || typeof intent !== "object") {
    return {
      ok: false,
      status: "HOLD_M4_ROUTE_INTENT_UNAVAILABLE",
      reason: "route intent is required before owner-turn provider/model execution",
    };
  }

  if (intent.contract_version && intent.contract_version !== M4_CONTRACT_VERSION) {
    return {
      ok: false,
      status: "FAIL_M4_ROUTE_INTENT_MALFORMED",
      reason: `unsupported contract_version ${intent.contract_version}`,
      intent,
    };
  }
  if (intent.authority_mode && intent.authority_mode !== M4_AUTHORITY_MODE) {
    return {
      ok: false,
      status: "FAIL_M4_ROUTE_INTENT_MALFORMED",
      reason: `unsupported authority_mode ${intent.authority_mode}`,
      intent,
    };
  }

  const source = intent.source ?? "unknown";
  if (!isRouteAuthoritySource(source)) {
    return {
      ok: false,
      status: "HOLD_M4_ROUTE_INTENT_UNSUPPORTED_SOURCE",
      reason: `${source} can produce route intent but cannot directly create route authority`,
      intent,
    };
  }

  const executable =
    normalizeRouteRef(intent.executable) ??
    normalizeRouteRef({ provider: intent.provider, model: intent.model }) ??
    normalizeRouteRef(intent.requested);
  if (!executable) {
    return {
      ok: false,
      status: "HOLD_M4_ROUTE_INTENT_MISSING_PROVIDER_MODEL",
      reason: "route intent did not normalize to provider/model",
      intent,
    };
  }

  if (!isProviderModelAllowed(executable, params.eligibility)) {
    return {
      ok: false,
      status: "HOLD_M4_ROUTE_INTENT_UNSUPPORTED_PROVIDER_MODEL",
      reason: `${routeKey(executable)} is not eligible for this route authority`,
      intent,
    };
  }

  const createdAt = params.now ?? new Date().toISOString();
  const fallbackChain = normalizeFallbackChain(
    executable,
    params.eligibility?.fallbackChain ?? intent.fallback_chain,
  );
  const serializable: M4VerifiedRouteSerializable = {
    verified_route_version: M4_VERIFIED_ROUTE_VERSION,
    route_id: routeId({
      turnId: intent.turn_id,
      sessionId: intent.session_id,
      channel: intent.channel,
      provider: executable.provider,
      model: executable.model,
      contractEnvelopeRef: intent.contract_envelope_ref,
      createdAt,
    }),
    turn_id: intent.turn_id,
    session_id: intent.session_id,
    channel: intent.channel,
    owner_scope: normalizeScope(intent.owner_scope),
    provider: executable.provider,
    model: executable.model,
    fallback_chain: fallbackChain,
    capability_manifest_ref:
      intent.capability_manifest_ref ?? params.eligibility?.capabilityManifestRef,
    contract_version: M4_CONTRACT_VERSION,
    contract_envelope_ref: intent.contract_envelope_ref,
    authority_mode: M4_AUTHORITY_MODE,
    created_by: M4_CREATED_BY,
    created_at: createdAt,
    verification_reason:
      intent.verification_reason ?? "route intent verified by UMC M4 source-level route verifier",
    signature_or_brand_token: M4_SIGNATURE_OR_BRAND_TOKEN,
    non_forgeable_brand: false,
    source,
    no_apply: true,
    production_enforcement: false,
  };
  const verifiedRoute = Object.freeze({
    ...serializable,
    [VERIFIED_ROUTE_BRAND]: true as const,
  });
  return { ok: true, status: "PASS_M4_VERIFIED_ROUTE_BRANDED", verifiedRoute };
}

export function createM4MockVerifiedRouteForFixtures(params: {
  intent: M4RouteIntent;
  eligibility?: M4RouteEligibility;
  now?: string;
}): M4VerifiedRoute {
  const result = verifyM4RouteIntent({
    intent: { ...params.intent, source: "mock_fixture_factory" },
    eligibility: params.eligibility,
    now: params.now,
  });
  if (!result.ok) {
    throw new Error(result.reason);
  }
  return result.verifiedRoute;
}

export function enforceM4VerifiedRouteFirewall(params: {
  ownerScoped: boolean;
  executionPath: M4ExecutionPath;
  execution: M4RouteRef;
  verifiedRoute?: unknown;
}): M4FirewallDecision {
  const execution = normalizeRouteRef(params.execution);
  if (!execution) {
    return {
      ok: false,
      status: "HOLD_M4_VERIFIED_ROUTE_EXECUTION_MISMATCH",
      reason: `${params.executionPath} execution provider/model is malformed`,
      execution: { provider: "", model: "" },
    };
  }

  if (!params.ownerScoped) {
    return {
      ok: true,
      status: "PASS_M4_FIREWALL_NOT_SCOPED",
      reason: `${params.executionPath} is outside owner-turn VerifiedRoute firewall scope`,
    };
  }

  if (!params.verifiedRoute) {
    return {
      ok: false,
      status: "HOLD_M4_MISSING_VERIFIED_ROUTE",
      reason: `${params.executionPath} attempted raw provider/model execution without VerifiedRoute authority`,
      execution,
    };
  }

  if (!isM4VerifiedRoute(params.verifiedRoute)) {
    return {
      ok: false,
      status: "HOLD_M4_FORGED_OR_DESERIALIZED_VERIFIED_ROUTE",
      reason: `${params.executionPath} received a forged, stale, or deserialized VerifiedRoute; reverify route intent first`,
      execution,
    };
  }

  if (
    params.verifiedRoute.contract_version !== M4_CONTRACT_VERSION ||
    params.verifiedRoute.authority_mode !== M4_AUTHORITY_MODE
  ) {
    return {
      ok: false,
      status: "HOLD_M4_FALLBACK_CONTRACT_AUTHORITY_LOST",
      reason: `${params.executionPath} route lost contract_version or observe-only/no-send authority`,
      execution,
    };
  }

  if (
    !sameRoute(execution, {
      provider: params.verifiedRoute.provider,
      model: params.verifiedRoute.model,
    })
  ) {
    return {
      ok: false,
      status: "HOLD_M4_VERIFIED_ROUTE_EXECUTION_MISMATCH",
      reason: `${params.executionPath} execution target does not match VerifiedRoute authority`,
      execution,
    };
  }

  const fallbackChain = params.verifiedRoute.fallback_chain;
  if (
    !Array.isArray(fallbackChain) ||
    fallbackChain.length === 0 ||
    fallbackChain.some((route) => !normalizeRouteRef(route))
  ) {
    return {
      ok: false,
      status: "HOLD_M4_FALLBACK_CONTRACT_AUTHORITY_LOST",
      reason: `${params.executionPath} fallback chain is missing or malformed`,
      execution,
    };
  }

  return {
    ok: true,
    status: "PASS_M4_VERIFIED_ROUTE_FIREWALL",
    reason: `${params.executionPath} execution is authorized by non-serializable VerifiedRoute brand`,
    verifiedRoute: params.verifiedRoute,
  };
}

export function buildM4BypassFixtureMatrix(now = "2026-07-16T00:00:00.000Z") {
  const defaultRoute = { provider: "token-broker-vmesh", model: "auto" };
  const rawRequested = { provider: "openai", model: "gpt-5.5" };
  const verifiedDefault = verifyM4RouteIntent({
    now,
    intent: {
      source: "default_model_config",
      owner_scope: "owner_turn",
      provider: defaultRoute.provider,
      model: defaultRoute.model,
      contract_version: M4_CONTRACT_VERSION,
      authority_mode: M4_AUTHORITY_MODE,
      contract_envelope_ref: "ContractEnvelope:m3-fixture",
    },
  });
  const verifiedQueued = verifyM4RouteIntent({
    now,
    intent: {
      source: "m2_queued_route_admission",
      owner_scope: "owner_turn",
      requested: rawRequested,
      executable: defaultRoute,
      contract_version: M4_CONTRACT_VERSION,
      authority_mode: M4_AUTHORITY_MODE,
      contract_envelope_ref: "ContractEnvelope:m3-fixture",
    },
  });
  const sessionPinIntent = verifyM4RouteIntent({
    now,
    intent: {
      source: "session_model_pin",
      owner_scope: "owner_turn",
      provider: rawRequested.provider,
      model: rawRequested.model,
      contract_version: M4_CONTRACT_VERSION,
      authority_mode: M4_AUTHORITY_MODE,
    },
  });
  const unsupported = verifyM4RouteIntent({
    now,
    eligibility: { allowedProviderModels: [routeKey(defaultRoute)] },
    intent: {
      source: "route_verifier",
      owner_scope: "owner_turn",
      provider: rawRequested.provider,
      model: rawRequested.model,
      contract_version: M4_CONTRACT_VERSION,
      authority_mode: M4_AUTHORITY_MODE,
    },
  });
  const verifiedForFallback = verifyM4RouteIntent({
    now,
    intent: {
      source: "fallback_candidate",
      owner_scope: "owner_turn",
      provider: defaultRoute.provider,
      model: defaultRoute.model,
      fallback_chain: [defaultRoute, { provider: "token-solver-v4", model: "auto" }],
      contract_version: M4_CONTRACT_VERSION,
      authority_mode: M4_AUTHORITY_MODE,
    },
  });

  const serializedRoute = verifiedDefault.ok
    ? JSON.parse(JSON.stringify(verifiedDefault.verifiedRoute))
    : undefined;
  const forgedRoute = verifiedDefault.ok
    ? { ...serializeM4VerifiedRoute(verifiedDefault.verifiedRoute), non_forgeable_brand: true }
    : undefined;

  return [
    {
      name: "default route brand passes runWithModelFallback",
      decision:
        verifiedDefault.ok &&
        enforceM4VerifiedRouteFirewall({
          ownerScoped: true,
          executionPath: "runWithModelFallback",
          execution: defaultRoute,
          verifiedRoute: verifiedDefault.verifiedRoute,
        }),
    },
    {
      name: "queued raw request intercepted to default broker passes once verified",
      decision:
        verifiedQueued.ok &&
        enforceM4VerifiedRouteFirewall({
          ownerScoped: true,
          executionPath: "queued_owner_turn",
          execution: defaultRoute,
          verifiedRoute: verifiedQueued.verifiedRoute,
        }),
    },
    {
      name: "raw provider/model call is rejected",
      decision: enforceM4VerifiedRouteFirewall({
        ownerScoped: true,
        executionPath: "direct_provider_model_helper",
        execution: rawRequested,
      }),
    },
    {
      name: "missing VerifiedRoute is rejected",
      decision: enforceM4VerifiedRouteFirewall({
        ownerScoped: true,
        executionPath: "runEmbeddedPiAgent",
        execution: defaultRoute,
      }),
    },
    {
      name: "forged VerifiedRoute is rejected",
      decision: enforceM4VerifiedRouteFirewall({
        ownerScoped: true,
        executionPath: "runEmbeddedPiAgent",
        execution: defaultRoute,
        verifiedRoute: forgedRoute,
      }),
    },
    {
      name: "deserialized route is rejected until reverified",
      decision: enforceM4VerifiedRouteFirewall({
        ownerScoped: true,
        executionPath: "fallback_route",
        execution: defaultRoute,
        verifiedRoute: serializedRoute,
      }),
    },
    {
      name: "fallback without VerifiedRoute is rejected",
      decision: enforceM4VerifiedRouteFirewall({
        ownerScoped: true,
        executionPath: "fallback_route",
        execution: defaultRoute,
      }),
    },
    {
      name: "session model pin cannot directly authorize execution",
      decision: sessionPinIntent,
    },
    {
      name: "channel model pin cannot directly authorize execution",
      decision: verifyM4RouteIntent({
        now,
        intent: {
          source: "channel_model_pin",
          owner_scope: "owner_turn",
          provider: rawRequested.provider,
          model: rawRequested.model,
          contract_version: M4_CONTRACT_VERSION,
          authority_mode: M4_AUTHORITY_MODE,
        },
      }),
    },
    {
      name: "route intent without verifier emits typed HOLD",
      decision: verifyM4RouteIntent({ now, intent: undefined }),
    },
    {
      name: "unsupported provider/model emits typed HOLD",
      decision: unsupported,
    },
    {
      name: "fallback chain preserves contract and no-send authority",
      decision:
        verifiedForFallback.ok &&
        enforceM4VerifiedRouteFirewall({
          ownerScoped: true,
          executionPath: "fallback_route",
          execution: defaultRoute,
          verifiedRoute: verifiedForFallback.verifiedRoute,
        }),
    },
  ];
}
