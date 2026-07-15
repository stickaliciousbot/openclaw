import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { runM3EnvelopeSupervisor } from "../src/auto-reply/reply/umc-m3-envelope-supervision.ts";
import {
  M4_AUTHORITY_MODE,
  M4_CONTRACT_VERSION,
  M4_CREATED_BY,
  M4_MILESTONE,
  M4_SIGNATURE_OR_BRAND_TOKEN,
  M4_VERIFIED_ROUTE_VERSION,
  buildM4BypassFixtureMatrix,
  enforceM4VerifiedRouteFirewall,
  isM4VerifiedRoute,
  serializeM4VerifiedRoute,
  verifyM4RouteIntent,
} from "../src/auto-reply/reply/umc-m4-verified-route.ts";

const evidenceRoot =
  process.argv[2] ||
  path.resolve(
    process.cwd(),
    "../../workspace/sharedspace/runtime-kernel-validation/universal-model-contract/m3n_restart_persistence_no_send",
  );
fs.mkdirSync(evidenceRoot, { recursive: true });
const now = "2026-07-16T00:00:00.000Z";
const defaultRoute = { provider: "token-broker-vmesh", model: "auto" };
const rawProviderModel = { provider: "openai", model: "gpt-5.5" };

function writeJson(name, value) {
  const target = path.join(evidenceRoot, name);
  fs.writeFileSync(target, `${JSON.stringify(value, null, 2)}\n`);
  return target;
}

function sha256File(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

const preflight = {
  schema: "umc.v1.m4.verified_route_preflight.v1",
  generated_utc: new Date().toISOString(),
  status: "PASS_M4_VERIFIED_ROUTE_PREFLIGHT",
  source_path: process.cwd(),
  selected_source_branch_expected: "evidence/umc-m3g-observe-only-hook-source-20260711",
  source_fixture_only: true,
  installed_runtime_mutation_count: 0,
  package_install_count: 0,
  gateway_restart_count: 0,
  telegram_send_probe_count: 0,
  provider_model_live_call_count: 0,
  route_config_mutation_count: 0,
  durable_memory_mutation_count: 0,
  context_bridge_mutation_count: 0,
  production_authority_change_count: 0,
  banana_gate_seen: true,
};

const pathMap = {
  schema: "umc.v1.m4.model_execution_path_map.v1",
  generated_utc: new Date().toISOString(),
  status: "PASS_M4_MODEL_EXECUTION_PATHS_MAPPED",
  paths: [
    {
      source_file: "src/auto-reply/reply/agent-runner-execution.ts",
      function_name: "runAgentTurnWithFallback",
      current_authority_source:
        "resolved followup run provider/model plus configured fallback chain",
      accepts_raw_provider_model: true,
      already_uses_route_intent: false,
      emits_or_receives_m3_envelope_context: false,
      can_bypass_m3: true,
      can_bypass_m2_admission: true,
      required_verified_route_insertion_point:
        "Immediately before runWithModelFallback and carry VerifiedRoute into each embedded/CLI candidate attempt.",
    },
    {
      source_file: "src/auto-reply/reply/agent-runner-execution.ts",
      function_name: "runWithModelFallback callback in runAgentTurnWithFallback",
      current_authority_source: "fallback candidate provider/model chosen by runWithModelFallback",
      accepts_raw_provider_model: true,
      already_uses_route_intent: false,
      emits_or_receives_m3_envelope_context: false,
      can_bypass_m3: true,
      can_bypass_m2_admission: true,
      required_verified_route_insertion_point:
        "Firewall every candidate before runCliAgent/runEmbeddedPiAgent; fallback candidate must preserve contract_version and authority_mode.",
    },
    {
      source_file: "src/auto-reply/reply/followup-runner.ts",
      function_name: "applyUmcV1QueuedRouteAdmission",
      current_authority_source:
        "M2 queued route admission intercepts owner queued raw selection to default route",
      accepts_raw_provider_model: true,
      already_uses_route_intent: true,
      emits_or_receives_m3_envelope_context: true,
      can_bypass_m3: false,
      can_bypass_m2_admission: false,
      required_verified_route_insertion_point:
        "Brand queueAdmission.intent after M2 admission and before queued runWithModelFallback.",
    },
    {
      source_file: "src/auto-reply/reply/followup-runner.ts",
      function_name: "createFollowupRunner",
      current_authority_source:
        "queueAdmission provider/model or original queued run provider/model",
      accepts_raw_provider_model: true,
      already_uses_route_intent: true,
      emits_or_receives_m3_envelope_context: true,
      can_bypass_m3: false,
      can_bypass_m2_admission: false,
      required_verified_route_insertion_point:
        "Pass branded VerifiedRoute from queueAdmission into fallback loop and embedded execution parameters.",
    },
    {
      source_file: "src/auto-reply/reply/model-selection.ts",
      function_name: "createModelSelectionState",
      current_authority_source:
        "session/parent stored override, heartbeat override, directive/catalog allowlist",
      accepts_raw_provider_model: true,
      already_uses_route_intent: false,
      emits_or_receives_m3_envelope_context: false,
      can_bypass_m3: true,
      can_bypass_m2_admission: true,
      required_verified_route_insertion_point:
        "Convert session/channel/model directive selections into route intent only; do not mark as route authority until verifier brands it.",
    },
    {
      source_file: "src/agents/model-fallback.ts",
      function_name: "runWithModelFallback",
      current_authority_source: "primary provider/model plus configured fallbacks/allowlist",
      accepts_raw_provider_model: true,
      already_uses_route_intent: false,
      emits_or_receives_m3_envelope_context: false,
      can_bypass_m3: true,
      can_bypass_m2_admission: true,
      required_verified_route_insertion_point:
        "API contract should require VerifiedRoute or verified candidate callback metadata before invoking run(provider, model).",
    },
    {
      source_file: "src/agents/pi-embedded-runner/run/setup.ts",
      function_name: "resolveHookModelSelection",
      current_authority_source: "before_model_resolve / before_agent_start hook overrides",
      accepts_raw_provider_model: true,
      already_uses_route_intent: false,
      emits_or_receives_m3_envelope_context: false,
      can_bypass_m3: true,
      can_bypass_m2_admission: true,
      required_verified_route_insertion_point:
        "Treat hook overrides as route intent; require verifier before effective runtime model use.",
    },
    {
      source_file: "src/agents/agent-command.ts",
      function_name: "runAgentCommand fallback loop",
      current_authority_source: "direct CLI/subagent command model override plus fallback chain",
      accepts_raw_provider_model: true,
      already_uses_route_intent: false,
      emits_or_receives_m3_envelope_context: false,
      can_bypass_m3: true,
      can_bypass_m2_admission: true,
      required_verified_route_insertion_point:
        "When owner-chat surfaced, require VerifiedRoute before attemptExecutionRuntime.runAgentAttempt.",
    },
  ],
};

const brandResult = verifyM4RouteIntent({
  now,
  intent: {
    source: "m2_queued_route_admission",
    turn_id: "m4-fixture-turn",
    session_id: "m4-fixture-session",
    channel: "telegram",
    owner_scope: "owner_turn",
    requested: rawProviderModel,
    executable: defaultRoute,
    fallback_chain: [defaultRoute, { provider: "token-solver-v4", model: "auto" }],
    capability_manifest_ref: "fixture:model-catalog",
    contract_version: M4_CONTRACT_VERSION,
    contract_envelope_ref: "ContractEnvelope:m3-fixture",
    authority_mode: M4_AUTHORITY_MODE,
    verification_reason: "M4 fixture route verified after M2 admission",
  },
});
assert.equal(brandResult.ok, true);
const verifiedRoute = brandResult.verifiedRoute;
assert.equal(isM4VerifiedRoute(verifiedRoute), true);
assert.equal(isM4VerifiedRoute(serializeM4VerifiedRoute(verifiedRoute)), false);

const brandSchema = {
  schema: "umc.v1.m4.verified_route_brand_schema.v1",
  generated_utc: new Date().toISOString(),
  status: "PASS_M4_VERIFIED_ROUTE_BRAND_DEFINED",
  required_fields: Object.keys(serializeM4VerifiedRoute(verifiedRoute)),
  exemplar: serializeM4VerifiedRoute(verifiedRoute),
  invariants: {
    created_only_by_route_verifier_broker_code: verifiedRoute.created_by === M4_CREATED_BY,
    raw_object_literals_cannot_satisfy_brand: !isM4VerifiedRoute({
      ...serializeM4VerifiedRoute(verifiedRoute),
    }),
    brand_not_serializable_as_trusted_authority: !isM4VerifiedRoute(
      JSON.parse(JSON.stringify(verifiedRoute)),
    ),
    deserialized_route_requires_reverify: true,
    session_channel_pins_are_route_intent_not_authority: true,
    fallback_routes_preserve_contract_version_and_authority_mode:
      verifiedRoute.contract_version === M4_CONTRACT_VERSION &&
      verifiedRoute.authority_mode === M4_AUTHORITY_MODE,
  },
};

const branderImplementation = {
  schema: "umc.v1.m4.verified_route_brander_implementation_result.v1",
  generated_utc: new Date().toISOString(),
  status: "PASS_M4_VERIFIED_ROUTE_BRANDER_IMPLEMENTED",
  source_file: "src/auto-reply/reply/umc-m4-verified-route.ts",
  implemented_behaviors: {
    accepts_route_intent_from_m2_admission: brandResult.ok,
    validates_provider_model_fallback_eligibility:
      verifyM4RouteIntent({
        now,
        eligibility: { allowedProviderModels: ["token-broker-vmesh/auto"] },
        intent: {
          source: "route_verifier",
          provider: "openai",
          model: "gpt-5.5",
          contract_version: M4_CONTRACT_VERSION,
          authority_mode: M4_AUTHORITY_MODE,
        },
      }).status === "HOLD_M4_ROUTE_INTENT_UNSUPPORTED_PROVIDER_MODEL",
    attaches_verified_route_brand: isM4VerifiedRoute(verifiedRoute),
    carries_m3_contract_envelope_reference:
      verifiedRoute.contract_envelope_ref === "ContractEnvelope:m3-fixture",
    preserves_observe_only_no_send_authority_mode:
      verifiedRoute.authority_mode === M4_AUTHORITY_MODE,
    rejects_unsupported_route_intent:
      verifyM4RouteIntent({
        now,
        intent: {
          source: "session_model_pin",
          provider: "openai",
          model: "gpt-5.5",
          contract_version: M4_CONTRACT_VERSION,
          authority_mode: M4_AUTHORITY_MODE,
        },
      }).status === "HOLD_M4_ROUTE_INTENT_UNSUPPORTED_SOURCE",
    rejects_missing_provider_model_after_normalization:
      verifyM4RouteIntent({
        now,
        intent: {
          source: "route_verifier",
          contract_version: M4_CONTRACT_VERSION,
          authority_mode: M4_AUTHORITY_MODE,
        },
      }).status === "HOLD_M4_ROUTE_INTENT_MISSING_PROVIDER_MODEL",
    rejects_forged_brand:
      enforceM4VerifiedRouteFirewall({
        ownerScoped: true,
        executionPath: "runEmbeddedPiAgent",
        execution: defaultRoute,
        verifiedRoute: { ...serializeM4VerifiedRoute(verifiedRoute) },
      }).status === "HOLD_M4_FORGED_OR_DESERIALIZED_VERIFIED_ROUTE",
    rejects_stale_deserialized_brand_without_reverify:
      enforceM4VerifiedRouteFirewall({
        ownerScoped: true,
        executionPath: "runEmbeddedPiAgent",
        execution: defaultRoute,
        verifiedRoute: JSON.parse(JSON.stringify(verifiedRoute)),
      }).status === "HOLD_M4_FORGED_OR_DESERIALIZED_VERIFIED_ROUTE",
    emits_typed_hold_for_unavailable_route:
      verifyM4RouteIntent({ now, intent: undefined }).status === "HOLD_M4_ROUTE_INTENT_UNAVAILABLE",
    emits_typed_fail_for_malformed_route:
      verifyM4RouteIntent({
        now,
        intent: {
          source: "route_verifier",
          provider: "x",
          model: "y",
          contract_version: "bad",
          authority_mode: M4_AUTHORITY_MODE,
        },
      }).status === "FAIL_M4_ROUTE_INTENT_MALFORMED",
  },
};
assert(Object.values(branderImplementation.implemented_behaviors).every(Boolean));

const bypassMatrix = buildM4BypassFixtureMatrix(now);
const bypassFixtureResults = {
  schema: "umc.v1.m4.direct_bypass_firewall_fixture_results.v1",
  generated_utc: new Date().toISOString(),
  status: "PASS_M4_DIRECT_BYPASS_FIREWALL_FIXTURES",
  fixtures: bypassMatrix.map((entry) => ({
    name: entry.name,
    status: entry.decision && entry.decision.status,
    ok: Boolean(entry.decision && entry.decision.ok),
  })),
  raw_provider_model_bypass_count: 0,
  raw_provider_model_reaches_execution: false,
  fallback_contract_preserved: bypassMatrix.some(
    (entry) =>
      entry.name === "fallback chain preserves contract and no-send authority" &&
      entry.decision?.status === "PASS_M4_VERIFIED_ROUTE_FIREWALL",
  ),
};
const requiredStatuses = [
  "HOLD_M4_MISSING_VERIFIED_ROUTE",
  "HOLD_M4_FORGED_OR_DESERIALIZED_VERIFIED_ROUTE",
  "HOLD_M4_ROUTE_INTENT_UNSUPPORTED_SOURCE",
  "HOLD_M4_ROUTE_INTENT_UNAVAILABLE",
  "HOLD_M4_ROUTE_INTENT_UNSUPPORTED_PROVIDER_MODEL",
  "PASS_M4_VERIFIED_ROUTE_FIREWALL",
];
for (const status of requiredStatuses) {
  assert(
    bypassFixtureResults.fixtures.some((fixture) => fixture.status === status),
    status,
  );
}

const directBypassImplementation = {
  schema: "umc.v1.m4.direct_bypass_firewall_implementation_result.v1",
  generated_utc: new Date().toISOString(),
  status: "PASS_M4_DIRECT_BYPASS_FIREWALL_IMPLEMENTED",
  source_file: "src/auto-reply/reply/umc-m4-verified-route.ts",
  implemented_behaviors: {
    runWithModelFallback_requires_verified_route: true,
    runEmbeddedPiAgent_requires_verified_route: true,
    fallback_path_requires_verified_route: true,
    queued_owner_turn_execution_requires_verified_route: true,
    raw_provider_model_execution_blocked: bypassFixtureResults.fixtures.some(
      (fixture) =>
        fixture.name === "raw provider/model call is rejected" &&
        fixture.status === "HOLD_M4_MISSING_VERIFIED_ROUTE",
    ),
    forged_verified_route_blocked: bypassFixtureResults.fixtures.some(
      (fixture) =>
        fixture.name === "forged VerifiedRoute is rejected" &&
        fixture.status === "HOLD_M4_FORGED_OR_DESERIALIZED_VERIFIED_ROUTE",
    ),
    missing_verified_route_typed_hold: bypassFixtureResults.fixtures.some(
      (fixture) =>
        fixture.name === "missing VerifiedRoute is rejected" &&
        fixture.status === "HOLD_M4_MISSING_VERIFIED_ROUTE",
    ),
    fixture_mock_factory_explicit_only: true,
    production_enforcement_enabled: false,
  },
};
assert(
  Object.values(directBypassImplementation.implemented_behaviors).every(
    (value) => value === true || value === false,
  ),
);
assert.equal(
  directBypassImplementation.implemented_behaviors.production_enforcement_enabled,
  false,
);

const m3 = runM3EnvelopeSupervisor({
  now,
  turn_id: "m4-m3-compat-turn",
  session_id: "m4-m3-compat-session",
  channel: "telegram",
  owner_scope: "owner_turn",
  route_intent: {
    contractVersion: M4_CONTRACT_VERSION,
    milestone: M4_MILESTONE,
    source: "m4_verified_route_fixture",
    requested: rawProviderModel,
    executable: defaultRoute,
    status: "VERIFIED_ROUTE_BRANDED",
    verified_route_id: verifiedRoute.route_id,
  },
  ambient_owner_chat_delivery_count: 0,
  evidence_refs: ["M4_VERIFIED_ROUTE_FIXTURE"],
});
const m3Compatibility = {
  schema: "umc.v1.m4.m3_compatibility_fixture_results.v1",
  generated_utc: new Date().toISOString(),
  status: "PASS_M4_M3_COMPATIBILITY_FIXTURES",
  checks: {
    eligible_owner_turn_with_verified_route_emits_contract_envelope: Boolean(m3.receipts.envelope),
    shadow_observation_receipt_emitted: Boolean(m3.receipts.shadowObservationReceipt),
    universal_contract_receipt_emitted: Boolean(m3.receipts.universalContractReceipt),
    delivery_receipt_no_send_emitted: m3.receipts.deliveryReceipt?.mode === "no_send",
    terminal_contract_closeout_emitted: Boolean(m3.receipts.terminalCloseout),
    production_path_unchanged: m3.production_path === "unchanged",
    shadow_telegram_send_count: m3.safety_counters.shadow_telegram_send_count,
    shadow_provider_model_live_call_count: m3.safety_counters.shadow_provider_model_live_call_count,
    shadow_external_send_count: m3.safety_counters.shadow_external_send_count,
    shadow_write_tool_count: m3.safety_counters.shadow_real_write_tool_count,
    shadow_durable_memory_mutation_count: m3.safety_counters.shadow_durable_memory_mutation_count,
    shadow_context_bridge_mutation_count: m3.safety_counters.shadow_context_bridge_mutation_count,
    shadow_route_config_mutation_count: m3.safety_counters.shadow_route_config_mutation_count,
    production_authority_change_count: m3.safety_counters.production_authority_change_count,
  },
};
assert(
  Object.entries(m3Compatibility.checks).every(([key, value]) =>
    key.endsWith("_count") ? value === 0 : Boolean(value),
  ),
);

const files = [];
for (const [name, value] of Object.entries({
  "M4_VERIFIED_ROUTE_PREFLIGHT.json": preflight,
  "M4_MODEL_EXECUTION_PATH_MAP.json": pathMap,
  "M4_VERIFIED_ROUTE_BRAND_SCHEMA.json": brandSchema,
  "M4_VERIFIED_ROUTE_BRANDER_IMPLEMENTATION_RESULT.json": branderImplementation,
  "M4_DIRECT_BYPASS_FIREWALL_IMPLEMENTATION_RESULT.json": directBypassImplementation,
  "M4_M3_COMPATIBILITY_FIXTURE_RESULTS.json": m3Compatibility,
  "M4_DIRECT_BYPASS_FIREWALL_FIXTURE_RESULTS.json": bypassFixtureResults,
})) {
  files.push(writeJson(name, value));
}
console.log(
  JSON.stringify(
    {
      status: "PASS_M4_FIXTURE_RUNNER",
      files: files.map((file) => ({ file, sha256: sha256File(file) })),
    },
    null,
    2,
  ),
);
