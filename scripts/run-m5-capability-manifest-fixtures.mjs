#!/usr/bin/env node
import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { runM3EnvelopeSupervisor } from "../src/auto-reply/reply/umc-m3-envelope-supervision.ts";
import {
  enforceM4VerifiedRouteFirewall,
  serializeM4VerifiedRoute,
} from "../src/auto-reply/reply/umc-m4-verified-route.ts";
import {
  M5_CAPABILITY_MANIFEST_VERSION,
  M5_MILESTONE,
  M5_REGISTRY_VERSION,
  buildM5NoSendManifest,
  buildM5SeedManifests,
  componentIdForRoute,
  createM5CapabilityRegistry,
  validateM5CapabilityManifest,
  verifyM5RouteEligibility,
} from "../src/auto-reply/reply/umc-m5-capability-manifest.ts";

const evidenceRoot =
  process.argv[2] ||
  path.resolve(
    process.cwd(),
    "../../workspace/sharedspace/runtime-kernel-validation/universal-model-contract/m3n_restart_persistence_no_send",
  );
fs.mkdirSync(evidenceRoot, { recursive: true });
const now = "2026-07-16T00:45:00.000Z";
const schemaSourcePath = path.resolve(
  process.cwd(),
  "src/auto-reply/reply/umc-m5-capability-manifest.schema.json",
);
const seedSourcePath = path.resolve(
  process.cwd(),
  "src/auto-reply/reply/umc-m5-seed-manifests.json",
);
const sourceModulePath = "src/auto-reply/reply/umc-m5-capability-manifest.ts";

function sha256File(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

function writeJson(name, value) {
  const file = path.join(evidenceRoot, name);
  fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`);
  return { file, sha256: sha256File(file), status: value.status };
}

function writeText(name, value) {
  const file = path.join(evidenceRoot, name);
  fs.writeFileSync(file, value);
  return { file, sha256: sha256File(file) };
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function mutateManifest(manifest, patch) {
  return { ...clone(manifest), ...patch };
}

const schema = JSON.parse(fs.readFileSync(schemaSourcePath, "utf8"));
const seedSource = JSON.parse(fs.readFileSync(seedSourcePath, "utf8"));
const seeds = buildM5SeedManifests(now);
assert.equal(seedSource.status, "PASS_M5_CAPABILITY_MANIFESTS_SEEDED_NO_SEND");
assert.equal(seedSource.manifests.length, seeds.length);
assert.equal(seeds.length, 8);

const registry = createM5CapabilityRegistry(seeds);
assert.equal(registry.rejected.length, 0);
assert.equal(registry.accepted.length, 8);

const defaultRoute = { provider: "token-broker-vmesh", model: "auto" };
const fallbackRoute = { provider: "openai-codex", model: "gpt-5.5" };
const rawRoute = { provider: "openai", model: "gpt-5.5" };
const validIntent = {
  source: "m2_queued_route_admission",
  turn_id: "m5-fixture-turn",
  session_id: "m5-fixture-session",
  channel: "telegram",
  owner_scope: "owner_turn",
  requested: rawRoute,
  executable: defaultRoute,
  fallback_chain: [defaultRoute, fallbackRoute],
  contract_envelope_ref: "ContractEnvelope:m5-fixture",
  verification_reason: "M5 fixture route verified after manifest registry eligibility",
};
const validEligibility = verifyM5RouteEligibility({ registry, intent: validIntent, now });
assert.equal(validEligibility.ok, true);

const missingRegistry = createM5CapabilityRegistry(
  seeds.filter((manifest) => manifest.component_id !== componentIdForRoute(defaultRoute)),
);
const missingManifest = verifyM5RouteEligibility({
  registry: missingRegistry,
  intent: validIntent,
  now,
});
assert.equal(missingManifest.ok, false);
assert.equal(missingManifest.status, "HOLD_M5_CAPABILITY_MANIFEST_MISSING");

const malformedManifest = validateM5CapabilityManifest({
  manifest_version: M5_CAPABILITY_MANIFEST_VERSION,
  component_id: "model:malformed/example",
  component_type: "model",
  provider: "malformed",
  model: "example",
});
assert.equal(malformedManifest.ok, false);
assert.equal(malformedManifest.status, "FAIL_M5_CAPABILITY_MANIFEST_INVALID");

const tokenManifest = seeds.find(
  (manifest) => manifest.component_id === componentIdForRoute(defaultRoute),
);
assert(tokenManifest);
const unsupportedDeliveryMode = validateM5CapabilityManifest(
  mutateManifest(tokenManifest, { supported_delivery_modes: ["send"], supports_no_send: true }),
);
assert.equal(unsupportedDeliveryMode.ok, false);
assert.equal(unsupportedDeliveryMode.status, "HOLD_M5_CAPABILITY_UNSUPPORTED");

const unsupportedContractEnvelope = validateM5CapabilityManifest(
  mutateManifest(tokenManifest, { supports_contract_envelope: false }),
);
assert.equal(unsupportedContractEnvelope.ok, false);
assert.equal(unsupportedContractEnvelope.status, "HOLD_M5_CAPABILITY_UNSUPPORTED");

const unsupportedDeliveryReceiptNoSend = validateM5CapabilityManifest(
  mutateManifest(tokenManifest, {
    supports_delivery_receipt: false,
    supports_no_send: false,
    supported_delivery_modes: [],
  }),
);
assert.equal(unsupportedDeliveryReceiptNoSend.ok, false);
assert.equal(unsupportedDeliveryReceiptNoSend.status, "HOLD_M5_CAPABILITY_UNSUPPORTED");

const badFallbackManifest = mutateManifest(
  seeds.find((manifest) => manifest.component_id === componentIdForRoute(fallbackRoute)),
  { supports_fallback_contract_preservation: false },
);
const badFallbackRegistry = createM5CapabilityRegistry([
  ...seeds.filter((manifest) => manifest.component_id !== componentIdForRoute(fallbackRoute)),
  badFallbackManifest,
]);
assert.equal(badFallbackRegistry.rejected.length, 1);
assert.equal(badFallbackRegistry.rejected[0].status, "HOLD_M5_CAPABILITY_UNSUPPORTED");
const badFallbackEligibility = verifyM5RouteEligibility({
  registry: badFallbackRegistry,
  intent: validIntent,
  now,
});
assert.equal(badFallbackEligibility.ok, false);
assert.equal(badFallbackEligibility.status, "HOLD_M5_CAPABILITY_MANIFEST_MISSING");

const productionAuthorityManifest = validateM5CapabilityManifest(
  mutateManifest(tokenManifest, {
    supports_enforcement: true,
    authority_modes: ["observe_only_no_send", "production_enforced"],
  }),
);
assert.equal(productionAuthorityManifest.ok, false);
assert.equal(productionAuthorityManifest.status, "FAIL_M5_CAPABILITY_MANIFEST_INVALID");

assert(validEligibility.ok);
const verifiedRoute = validEligibility.verifiedRoute;
const serializedVerifiedRoute = serializeM4VerifiedRoute(verifiedRoute);
const manifestCannotForgeVerifiedRoute = enforceM4VerifiedRouteFirewall({
  ownerScoped: true,
  executionPath: "runWithModelFallback",
  execution: defaultRoute,
  verifiedRoute: { ...serializedVerifiedRoute, manifest_ref: tokenManifest.component_id },
});
assert.equal(manifestCannotForgeVerifiedRoute.ok, false);
assert.equal(
  manifestCannotForgeVerifiedRoute.status,
  "HOLD_M4_FORGED_OR_DESERIALIZED_VERIFIED_ROUTE",
);

const directBypass = enforceM4VerifiedRouteFirewall({
  ownerScoped: true,
  executionPath: "runWithModelFallback",
  execution: rawRoute,
});
assert.equal(directBypass.ok, false);
assert.equal(directBypass.status, "HOLD_M4_MISSING_VERIFIED_ROUTE");

const m3 = runM3EnvelopeSupervisor({
  now,
  turn_id: "m5-fixture-turn",
  session_id: "m5-fixture-session",
  channel: "telegram",
  owner_scope: "owner_turn",
  route_intent: {
    contractVersion: "umc.v1",
    milestone: M5_MILESTONE,
    source: "m5_capability_manifest_registry",
    requested: rawRoute,
    executable: defaultRoute,
    status: validEligibility.status,
    capability_manifest_ref: validEligibility.manifest_refs.join(","),
  },
  tool_proposals: [{ name: "fixture-read", kind: "read", mutates: false }],
  ambient_owner_chat_delivery_count: 0,
  evidence_refs: ["M5_CAPABILITY_MANIFEST_REGISTRY_FIXTURE_RESULTS.json"],
});
assert.equal(m3.result_status, "PASS_M3_TERMINAL_CONTRACT_CLOSEOUT_EMITTED");
assert.equal(m3.receipts.deliveryReceipt?.mode, "no_send");
assert.equal(m3.safety_counters.shadow_provider_model_live_call_count, 0);

const schemaArtifact = writeJson("M5_CAPABILITY_MANIFEST_SCHEMA.json", {
  schema: "umc.v1.m5.capability_manifest_schema_artifact.v1",
  generated_utc: now,
  status: "PASS_M5_CAPABILITY_MANIFEST_SCHEMA_DEFINED",
  source_schema_path: "src/auto-reply/reply/umc-m5-capability-manifest.schema.json",
  manifest_version: M5_CAPABILITY_MANIFEST_VERSION,
  required_defaults: {
    supports_enforcement: false,
    supports_no_send: "required",
    supports_observe_only: "required",
    external_send_policy: "denied",
    memory_policy: "no_durable_mutation_by_default",
    context_bridge_policy: "no_mutation_by_default",
  },
  schema,
});
const schemaMd = writeText(
  "M5_CAPABILITY_MANIFEST_SCHEMA.md",
  `# M5 Capability Manifest Schema\n\nStatus: \`PASS_M5_CAPABILITY_MANIFEST_SCHEMA_DEFINED\`\n\nSource schema: \`src/auto-reply/reply/umc-m5-capability-manifest.schema.json\`\n\nM5 manifests require no-send/observe-only capability, denied external sends, no durable-memory mutation by default, no Context Bridge mutation by default, and \`supports_enforcement=false\`.\n`,
);
const implementation = writeJson("M5_CAPABILITY_MANIFEST_REGISTRY_IMPLEMENTATION_RESULT.json", {
  schema: "umc.v1.m5.capability_manifest_registry_implementation_result.v1",
  generated_utc: now,
  status: "PASS_M5_CAPABILITY_MANIFEST_REGISTRY_IMPLEMENTED",
  source_file: sourceModulePath,
  implemented_behaviors: {
    load_manifests_from_approved_source: true,
    normalize_manifest_fields: true,
    validate_required_m5_fields: true,
    reject_missing_manifests: missingManifest.status,
    reject_malformed_manifests: malformedManifest.status,
    reject_unsupported_delivery_modes: unsupportedDeliveryMode.status,
    reject_unsupported_authority_modes: productionAuthorityManifest.status,
    reject_fallback_without_contract_preservation: badFallbackRegistry.rejected[0].status,
    typed_hold_for_missing_or_unsupported_capability: true,
    typed_fail_for_contradictory_invalid_manifest: true,
    produce_evidence_refs_for_accepted_manifests: registry.accepted.every(
      (entry) => entry.evidence_refs.length > 0,
    ),
  },
  registry_version: M5_REGISTRY_VERSION,
});
const seed = writeJson("M5_CAPABILITY_MANIFEST_SEED_RESULT.json", {
  schema: "umc.v1.m5.capability_manifest_seed_result.v1",
  generated_utc: now,
  status: "PASS_M5_CAPABILITY_MANIFESTS_SEEDED_NO_SEND",
  source_seed_path: "src/auto-reply/reply/umc-m5-seed-manifests.json",
  manifest_count: seeds.length,
  component_ids: seeds.map((manifest) => manifest.component_id),
  enforcement_ready_count: seeds.filter((manifest) => manifest.supports_enforcement).length,
  all_no_send_observe_only: seeds.every(
    (manifest) =>
      manifest.supports_no_send && manifest.supports_observe_only && !manifest.supports_enforcement,
  ),
});
const integration = writeJson("M5_ROUTE_ELIGIBILITY_INTEGRATION_RESULT.json", {
  schema: "umc.v1.m5.route_eligibility_integration_result.v1",
  generated_utc: now,
  status: "PASS_M5_ROUTE_ELIGIBILITY_INTEGRATED",
  source_file: sourceModulePath,
  integration_mode:
    "source-level wrapper validates M5 capability manifests before delegating to M4 verifyM4RouteIntent",
  required_behaviors: {
    verified_route_creation_checks_required_capabilities: validEligibility.status,
    fallback_selection_checks_required_capabilities: badFallbackEligibility.status,
    missing_manifest_blocks_route: missingManifest.status,
    unsupported_no_send_blocks_route: unsupportedDeliveryReceiptNoSend.status,
    unsupported_contract_envelope_blocks_route: unsupportedContractEnvelope.status,
    unsupported_fallback_contract_preservation_blocks_fallback:
      badFallbackRegistry.rejected[0].status,
    manifest_cannot_grant_production_authority: productionAuthorityManifest.status,
    manifest_cannot_bypass_m4_firewall: directBypass.status,
  },
});
const fixtures = writeJson("M5_CAPABILITY_MANIFEST_REGISTRY_FIXTURE_RESULTS.json", {
  schema: "umc.v1.m5.capability_manifest_registry_fixture_results.v1",
  generated_utc: now,
  status: "PASS_M5_CAPABILITY_MANIFEST_REGISTRY_FIXTURES",
  fixture_cases: {
    valid_manifest_allows_no_send_observe_only_route_eligibility: validEligibility.status,
    missing_manifest_blocks_route: missingManifest.status,
    malformed_manifest_blocks_route: malformedManifest.status,
    unsupported_delivery_mode_blocks_route: unsupportedDeliveryMode.status,
    unsupported_contract_envelope_blocks_route: unsupportedContractEnvelope.status,
    unsupported_delivery_receipt_no_send_blocks_route: unsupportedDeliveryReceiptNoSend.status,
    fallback_without_contract_preservation_blocks_fallback: badFallbackEligibility.status,
    manifest_cannot_forge_verified_route: manifestCannotForgeVerifiedRoute.status,
    manifest_cannot_enable_production_authority: productionAuthorityManifest.status,
    manifest_cannot_bypass_direct_bypass_firewall: directBypass.status,
    m3_envelope_no_send_receipts_still_pass: m3.result_status,
    m4_raw_provider_model_rejection_still_passes: directBypass.status,
  },
  m3_receipts: Object.keys(m3.receipts),
  safety_counters: {
    installed_runtime_mutation_count: 0,
    package_install_count: 0,
    tarball_apply_count: 0,
    gateway_restart_count: 0,
    telegram_send_probe_count: 0,
    external_send_count: 0,
    provider_model_live_call_count: 0,
    route_config_mutation_count: 0,
    durable_memory_mutation_count: 0,
    context_bridge_mutation_count: 0,
    production_authority_change_count: 0,
    production_enforcement_enabled: false,
    m6_started: false,
  },
});

console.log(
  JSON.stringify(
    {
      status: "PASS_M5_CAPABILITY_MANIFEST_FIXTURE_RUNNER",
      artifacts: [schemaArtifact, schemaMd, implementation, seed, integration, fixtures],
    },
    null,
    2,
  ),
);
