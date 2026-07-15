import { describe, expect, it } from "vitest";
import {
  M4_AUTHORITY_MODE,
  M4_CONTRACT_VERSION,
  M4_CREATED_BY,
  M4_SIGNATURE_OR_BRAND_TOKEN,
  M4_VERIFIED_ROUTE_VERSION,
  buildM4BypassFixtureMatrix,
  enforceM4VerifiedRouteFirewall,
  isM4VerifiedRoute,
  serializeM4VerifiedRoute,
  verifyM4RouteIntent,
} from "./umc-m4-verified-route.js";

describe("UMC M4 VerifiedRoute brander and direct bypass firewall", () => {
  const now = "2026-07-16T00:00:00.000Z";
  const defaultRoute = { provider: "token-broker-vmesh", model: "auto" };
  const rawProviderModel = { provider: "openai", model: "gpt-5.5" };

  it("brands a verified route with all required schema fields", () => {
    const result = verifyM4RouteIntent({
      now,
      intent: {
        source: "m2_queued_route_admission",
        turn_id: "turn-1",
        session_id: "session-1",
        channel: "telegram",
        owner_scope: "owner_turn",
        requested: rawProviderModel,
        executable: defaultRoute,
        fallback_chain: [defaultRoute, { provider: "token-solver-v4", model: "auto" }],
        capability_manifest_ref: "model-catalog:test",
        contract_version: M4_CONTRACT_VERSION,
        contract_envelope_ref: "ContractEnvelope:m3",
        authority_mode: M4_AUTHORITY_MODE,
        verification_reason: "fixture route admission verified",
      },
    });

    expect(result.status).toBe("PASS_M4_VERIFIED_ROUTE_BRANDED");
    expect(result.ok).toBe(true);
    if (!result.ok) throw new Error(result.reason);
    expect(isM4VerifiedRoute(result.verifiedRoute)).toBe(true);
    expect(result.verifiedRoute).toMatchObject({
      verified_route_version: M4_VERIFIED_ROUTE_VERSION,
      turn_id: "turn-1",
      session_id: "session-1",
      channel: "telegram",
      owner_scope: "owner_turn",
      provider: defaultRoute.provider,
      model: defaultRoute.model,
      fallback_chain: [defaultRoute, { provider: "token-solver-v4", model: "auto" }],
      capability_manifest_ref: "model-catalog:test",
      contract_version: M4_CONTRACT_VERSION,
      contract_envelope_ref: "ContractEnvelope:m3",
      authority_mode: M4_AUTHORITY_MODE,
      created_by: M4_CREATED_BY,
      created_at: now,
      verification_reason: "fixture route admission verified",
      signature_or_brand_token: M4_SIGNATURE_OR_BRAND_TOKEN,
      non_forgeable_brand: false,
      source: "m2_queued_route_admission",
      no_apply: true,
      production_enforcement: false,
    });
  });

  it("does not allow serialized or raw object literals to satisfy the non-forgeable brand", () => {
    const result = verifyM4RouteIntent({
      now,
      intent: {
        source: "default_model_config",
        owner_scope: "owner_turn",
        provider: defaultRoute.provider,
        model: defaultRoute.model,
        contract_version: M4_CONTRACT_VERSION,
        authority_mode: M4_AUTHORITY_MODE,
      },
    });
    expect(result.ok).toBe(true);
    if (!result.ok) throw new Error(result.reason);
    const serialized = serializeM4VerifiedRoute(result.verifiedRoute);
    expect(isM4VerifiedRoute(serialized)).toBe(false);
    expect(isM4VerifiedRoute(JSON.parse(JSON.stringify(result.verifiedRoute)))).toBe(false);
    expect(
      enforceM4VerifiedRouteFirewall({
        ownerScoped: true,
        executionPath: "runEmbeddedPiAgent",
        execution: defaultRoute,
        verifiedRoute: serialized,
      }),
    ).toMatchObject({
      ok: false,
      status: "HOLD_M4_FORGED_OR_DESERIALIZED_VERIFIED_ROUTE",
    });
  });

  it("allows runWithModelFallback only when execution matches a VerifiedRoute", () => {
    const result = verifyM4RouteIntent({
      now,
      intent: {
        source: "default_model_config",
        owner_scope: "owner_turn",
        provider: defaultRoute.provider,
        model: defaultRoute.model,
        contract_version: M4_CONTRACT_VERSION,
        authority_mode: M4_AUTHORITY_MODE,
      },
    });
    expect(result.ok).toBe(true);
    if (!result.ok) throw new Error(result.reason);

    expect(
      enforceM4VerifiedRouteFirewall({
        ownerScoped: true,
        executionPath: "runWithModelFallback",
        execution: defaultRoute,
        verifiedRoute: result.verifiedRoute,
      }),
    ).toMatchObject({ ok: true, status: "PASS_M4_VERIFIED_ROUTE_FIREWALL" });
  });

  it("blocks raw direct provider/model helper execution with no VerifiedRoute", () => {
    expect(
      enforceM4VerifiedRouteFirewall({
        ownerScoped: true,
        executionPath: "direct_provider_model_helper",
        execution: rawProviderModel,
      }),
    ).toMatchObject({
      ok: false,
      status: "HOLD_M4_MISSING_VERIFIED_ROUTE",
    });
  });

  it("blocks route/execution mismatches before model execution", () => {
    const result = verifyM4RouteIntent({
      now,
      intent: {
        source: "default_model_config",
        owner_scope: "owner_turn",
        provider: defaultRoute.provider,
        model: defaultRoute.model,
        contract_version: M4_CONTRACT_VERSION,
        authority_mode: M4_AUTHORITY_MODE,
      },
    });
    expect(result.ok).toBe(true);
    if (!result.ok) throw new Error(result.reason);

    expect(
      enforceM4VerifiedRouteFirewall({
        ownerScoped: true,
        executionPath: "runEmbeddedPiAgent",
        execution: rawProviderModel,
        verifiedRoute: result.verifiedRoute,
      }),
    ).toMatchObject({
      ok: false,
      status: "HOLD_M4_VERIFIED_ROUTE_EXECUTION_MISMATCH",
    });
  });

  it("treats session/channel pins as route intent only, not route authority", () => {
    expect(
      verifyM4RouteIntent({
        now,
        intent: {
          source: "session_model_pin",
          owner_scope: "owner_turn",
          provider: rawProviderModel.provider,
          model: rawProviderModel.model,
          contract_version: M4_CONTRACT_VERSION,
          authority_mode: M4_AUTHORITY_MODE,
        },
      }),
    ).toMatchObject({ ok: false, status: "HOLD_M4_ROUTE_INTENT_UNSUPPORTED_SOURCE" });
    expect(
      verifyM4RouteIntent({
        now,
        intent: {
          source: "channel_model_pin",
          owner_scope: "owner_turn",
          provider: rawProviderModel.provider,
          model: rawProviderModel.model,
          contract_version: M4_CONTRACT_VERSION,
          authority_mode: M4_AUTHORITY_MODE,
        },
      }),
    ).toMatchObject({ ok: false, status: "HOLD_M4_ROUTE_INTENT_UNSUPPORTED_SOURCE" });
  });

  it("emits typed HOLD for unsupported provider/model", () => {
    expect(
      verifyM4RouteIntent({
        now,
        eligibility: { allowedProviderModels: [`${defaultRoute.provider}/${defaultRoute.model}`] },
        intent: {
          source: "route_verifier",
          owner_scope: "owner_turn",
          provider: rawProviderModel.provider,
          model: rawProviderModel.model,
          contract_version: M4_CONTRACT_VERSION,
          authority_mode: M4_AUTHORITY_MODE,
        },
      }),
    ).toMatchObject({ ok: false, status: "HOLD_M4_ROUTE_INTENT_UNSUPPORTED_PROVIDER_MODEL" });
  });

  it("keeps non-owner/test-only paths out of owner-turn production authority", () => {
    expect(
      enforceM4VerifiedRouteFirewall({
        ownerScoped: false,
        executionPath: "test_only_provider_invocation",
        execution: rawProviderModel,
      }),
    ).toMatchObject({ ok: true, status: "PASS_M4_FIREWALL_NOT_SCOPED" });
  });

  it("emits a compatibility/bypass fixture matrix with all required rejection coverage", () => {
    const matrix = buildM4BypassFixtureMatrix(now);
    expect(matrix.map((entry) => [entry.name, entry.decision && entry.decision.status])).toEqual([
      ["default route brand passes runWithModelFallback", "PASS_M4_VERIFIED_ROUTE_FIREWALL"],
      [
        "queued raw request intercepted to default broker passes once verified",
        "PASS_M4_VERIFIED_ROUTE_FIREWALL",
      ],
      ["raw provider/model call is rejected", "HOLD_M4_MISSING_VERIFIED_ROUTE"],
      ["missing VerifiedRoute is rejected", "HOLD_M4_MISSING_VERIFIED_ROUTE"],
      ["forged VerifiedRoute is rejected", "HOLD_M4_FORGED_OR_DESERIALIZED_VERIFIED_ROUTE"],
      [
        "deserialized route is rejected until reverified",
        "HOLD_M4_FORGED_OR_DESERIALIZED_VERIFIED_ROUTE",
      ],
      ["fallback without VerifiedRoute is rejected", "HOLD_M4_MISSING_VERIFIED_ROUTE"],
      [
        "session model pin cannot directly authorize execution",
        "HOLD_M4_ROUTE_INTENT_UNSUPPORTED_SOURCE",
      ],
      [
        "channel model pin cannot directly authorize execution",
        "HOLD_M4_ROUTE_INTENT_UNSUPPORTED_SOURCE",
      ],
      ["route intent without verifier emits typed HOLD", "HOLD_M4_ROUTE_INTENT_UNAVAILABLE"],
      [
        "unsupported provider/model emits typed HOLD",
        "HOLD_M4_ROUTE_INTENT_UNSUPPORTED_PROVIDER_MODEL",
      ],
      [
        "fallback chain preserves contract and no-send authority",
        "PASS_M4_VERIFIED_ROUTE_FIREWALL",
      ],
    ]);
  });
});
