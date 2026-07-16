import assert from 'node:assert/strict';
import fs from 'node:fs';
import { pathToFileURL } from 'node:url';

const root = '/home/stickai/.npm-global/lib/node_modules/openclaw';
const now = '2026-07-16T01:34:00.000Z';
const m5 = await import(pathToFileURL(`${root}/dist/auto-reply/reply/umc-m5-capability-manifest.js`).href);
const m4 = await import(pathToFileURL(`${root}/dist/auto-reply/reply/umc-m4-verified-route.js`).href);

const schema = JSON.parse(fs.readFileSync(`${root}/dist/auto-reply/reply/umc-m5-capability-manifest.schema.json`, 'utf8'));
const seedPayload = JSON.parse(fs.readFileSync(`${root}/dist/auto-reply/reply/umc-m5-seed-manifests.json`, 'utf8'));
assert.equal(schema.properties.manifest_version.const, 'umc.v1.m5.capability_manifest.v1');
assert.equal(seedPayload.status, 'PASS_M5_CAPABILITY_MANIFESTS_SEEDED_NO_SEND');
assert.equal(seedPayload.manifests.length, 8);

const seeds = m5.buildM5SeedManifests(now);
const registry = m5.createM5CapabilityRegistry(seeds);
assert.equal(registry.rejected.length, 0);
assert.equal(registry.accepted.length, 8);

const defaultRoute = { provider: 'token-broker-vmesh', model: 'auto' };
const fallbackRoute = { provider: 'openai-codex', model: 'gpt-5.5' };
const rawRoute = { provider: 'openai', model: 'gpt-5.5' };
const validIntent = {
  source: 'm2_queued_route_admission',
  turn_id: 'm5-installed-fixture-turn',
  session_id: 'm5-installed-fixture-session',
  channel: 'telegram',
  owner_scope: 'owner_turn',
  requested: rawRoute,
  executable: defaultRoute,
  fallback_chain: [defaultRoute, fallbackRoute],
  contract_envelope_ref: 'ContractEnvelope:m5-installed-fixture',
  verification_reason: 'M5 installed runtime fixture route verified after manifest registry eligibility',
};

const valid = m5.verifyM5RouteEligibility({ registry, intent: validIntent, now });
assert.equal(valid.ok, true);
assert.equal(valid.status, 'PASS_M5_ROUTE_ELIGIBILITY_VERIFIED');

const missingRegistry = m5.createM5CapabilityRegistry(
  seeds.filter((manifest) => manifest.component_id !== m5.componentIdForRoute(defaultRoute)),
);
const missing = m5.verifyM5RouteEligibility({ registry: missingRegistry, intent: validIntent, now });
assert.equal(missing.ok, false);
assert.equal(missing.status, 'HOLD_M5_CAPABILITY_MANIFEST_MISSING');

const malformed = m5.validateM5CapabilityManifest({
  manifest_version: 'umc.v1.m5.capability_manifest.v1',
  component_id: 'model:malformed/example',
  component_type: 'model',
  provider: 'malformed',
  model: 'example',
});
assert.equal(malformed.ok, false);
assert.equal(malformed.status, 'FAIL_M5_CAPABILITY_MANIFEST_INVALID');

const tokenManifest = seeds.find((manifest) => manifest.component_id === m5.componentIdForRoute(defaultRoute));
assert(tokenManifest);
const unsupportedDelivery = m5.validateM5CapabilityManifest({ ...tokenManifest, supported_delivery_modes: ['send'] });
assert.equal(unsupportedDelivery.ok, false);
assert.equal(unsupportedDelivery.status, 'HOLD_M5_CAPABILITY_UNSUPPORTED');
const unsupportedEnvelope = m5.validateM5CapabilityManifest({ ...tokenManifest, supports_contract_envelope: false });
assert.equal(unsupportedEnvelope.ok, false);
assert.equal(unsupportedEnvelope.status, 'HOLD_M5_CAPABILITY_UNSUPPORTED');
const unsupportedDeliveryReceipt = m5.validateM5CapabilityManifest({
  ...tokenManifest,
  supports_delivery_receipt: false,
  supports_no_send: false,
  supported_delivery_modes: [],
});
assert.equal(unsupportedDeliveryReceipt.ok, false);
assert.equal(unsupportedDeliveryReceipt.status, 'HOLD_M5_CAPABILITY_UNSUPPORTED');

const fallbackManifest = seeds.find((manifest) => manifest.component_id === m5.componentIdForRoute(fallbackRoute));
const badFallbackRegistry = m5.createM5CapabilityRegistry([
  ...seeds.filter((manifest) => manifest.component_id !== m5.componentIdForRoute(fallbackRoute)),
  { ...fallbackManifest, supports_fallback_contract_preservation: false },
]);
assert.equal(badFallbackRegistry.rejected[0].status, 'HOLD_M5_CAPABILITY_UNSUPPORTED');
const badFallback = m5.verifyM5RouteEligibility({ registry: badFallbackRegistry, intent: validIntent, now });
assert.equal(badFallback.ok, false);
assert.equal(badFallback.status, 'HOLD_M5_CAPABILITY_MANIFEST_MISSING');

const productionAuthority = m5.validateM5CapabilityManifest({
  ...tokenManifest,
  supports_enforcement: true,
  authority_modes: ['observe_only_no_send', 'production_enforced'],
});
assert.equal(productionAuthority.ok, false);
assert.equal(productionAuthority.status, 'FAIL_M5_CAPABILITY_MANIFEST_INVALID');

const serialized = m4.serializeM4VerifiedRoute(valid.verifiedRoute);
const forged = m4.enforceM4VerifiedRouteFirewall({
  ownerScoped: true,
  executionPath: 'runWithModelFallback',
  execution: defaultRoute,
  verifiedRoute: serialized,
});
assert.equal(forged.ok, false);
assert.equal(forged.status, 'HOLD_M4_FORGED_OR_DESERIALIZED_VERIFIED_ROUTE');
const directBypass = m4.enforceM4VerifiedRouteFirewall({
  ownerScoped: true,
  executionPath: 'runWithModelFallback',
  execution: rawRoute,
});
assert.equal(directBypass.ok, false);
assert.equal(directBypass.status, 'HOLD_M4_MISSING_VERIFIED_ROUTE');

const missingVerifiedRoute = m4.enforceM4VerifiedRouteFirewall({
  ownerScoped: true,
  executionPath: 'runEmbeddedPiAgent',
  execution: defaultRoute,
});
assert.equal(missingVerifiedRoute.ok, false);
assert.equal(missingVerifiedRoute.status, 'HOLD_M4_MISSING_VERIFIED_ROUTE');

const result = {
  status: 'PASS_M5_INSTALLED_RUNTIME_REGRESSION_HARNESS',
  m5: {
    schema_present: true,
    registry_present: true,
    seed_manifests_present: true,
    route_eligibility_integration_present: true,
    valid_manifest_route_eligibility: valid.status,
    missing_manifest_route_eligibility: missing.status,
    malformed_manifest_route_eligibility: malformed.status,
    unsupported_delivery_mode: unsupportedDelivery.status,
    unsupported_contract_envelope: unsupportedEnvelope.status,
    unsupported_delivery_receipt_no_send: unsupportedDeliveryReceipt.status,
    fallback_without_contract_preservation: badFallback.status,
    production_authority_prevention: productionAuthority.status,
  },
  m4: {
    manifest_cannot_forge_verified_route: forged.status,
    manifest_cannot_bypass_direct_bypass_firewall: directBypass.status,
    missing_verified_route_rejected: missingVerifiedRoute.status,
    raw_provider_model_rejected_before_execution: directBypass.status,
  },
  safety_counters: {
    telegram_send_probe_count: 0,
    external_send_count: 0,
    provider_model_live_call_count: 0,
    route_config_mutation_count: 0,
    durable_memory_mutation_count: 0,
    context_bridge_mutation_count: 0,
    production_authority_change_count: 0,
    enforcement_enabled: false,
  },
};
console.log(JSON.stringify(result, null, 2));
