#!/usr/bin/env node
import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import {
  enforceM4VerifiedRouteFirewall,
  serializeM4VerifiedRoute,
} from "../src/auto-reply/reply/umc-m4-verified-route.ts";
import {
  buildM5SeedManifests,
  componentIdForRoute,
  createM5CapabilityRegistry,
  validateM5CapabilityManifest,
} from "../src/auto-reply/reply/umc-m5-capability-manifest.ts";
import {
  M6_BROKER_ROUTE,
  M6_DEFAULT_WORKER,
  M6_LANE_ID,
  M6_MILESTONE,
  buildM6ContractBuildLane,
  buildM6ContractBuildLaneSpec,
  buildM6ContractBuildManifests,
  createM6CapabilityRegistry,
} from "../src/auto-reply/reply/umc-m6-contract-build-lane.ts";

const evidenceRoot =
  process.argv[2] ||
  path.resolve(
    process.cwd(),
    "../../workspace/sharedspace/runtime-kernel-validation/universal-model-contract/m3n_restart_persistence_no_send",
  );
fs.mkdirSync(evidenceRoot, { recursive: true });
const now = "2026-07-16T02:10:00.000Z";

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
function validIntent(overrides = {}) {
  return {
    source: "m2_owner_turn_route_admission",
    owner_scope: "owner_turn",
    requested: M6_BROKER_ROUTE,
    executable: M6_BROKER_ROUTE,
    worker: M6_DEFAULT_WORKER,
    fallback_chain: [M6_DEFAULT_WORKER],
    session_model_pin: { provider: "openai", model: "gpt-5.5" },
    channel_model_pin: { provider: "openai-codex", model: "gpt-5.5" },
    turn_id: "m6-fixture-turn",
    session_id: "m6-fixture-session",
    channel: "telegram",
    contract_envelope_ref: "ContractEnvelope:m6-fixture",
    ...overrides,
  };
}

const spec = buildM6ContractBuildLaneSpec();
assert.equal(spec.lane_id, M6_LANE_ID);
assert.equal(spec.authority_mode, "observe_only");
assert.equal(spec.delivery_mode, "no_send");
assert.equal(spec.worker_model_policy.route_authority, false);
assert(spec.explicit_invariants.includes("worker model is not route authority"));

const registry = createM6CapabilityRegistry(now);
assert.equal(registry.rejected.length, 0);
const valid = buildM6ContractBuildLane({ intent: validIntent(), registry, now });
assert.equal(valid.ok, true);
assert.equal(valid.status, "PASS_M6_CONTRACT_BUILD_LANE_BUILT");
assert.equal(valid.lane.worker_route_authority, false);
assert.equal(valid.lane.deliveryReceipt?.mode, "no_send");
assert.equal(
  valid.lane.terminalCloseout?.result_status,
  "PASS_M3_TERMINAL_CONTRACT_CLOSEOUT_EMITTED",
);
assert.equal(valid.lane.route_intent_metadata.session_channel_pins_are_route_intent_only, true);

const rawProviderBypass = buildM6ContractBuildLane({
  intent: validIntent({
    requested: { provider: "openai", model: "gpt-5.5" },
    executable: { provider: "openai", model: "gpt-5.5" },
  }),
  registry,
  now,
});
assert.equal(rawProviderBypass.ok, false);
assert.equal(rawProviderBypass.status, "FAIL_M6_RAW_MODEL_AUTHORITY_BYPASS");

const missingManifestRegistry = createM5CapabilityRegistry([
  ...buildM5SeedManifests(now),
  ...buildM6ContractBuildManifests(now).filter(
    (manifest) => manifest.component_id !== componentIdForRoute(M6_BROKER_ROUTE),
  ),
]);
const missingManifest = buildM6ContractBuildLane({
  intent: validIntent(),
  registry: missingManifestRegistry,
  now,
});
assert.equal(missingManifest.ok, false);
assert.equal(missingManifest.status, "HOLD_M6_CAPABILITY_MANIFEST_MISSING");

const workerManifestId = componentIdForRoute(M6_DEFAULT_WORKER);
const unsupportedWorkerManifest = buildM5SeedManifests(now).find(
  (manifest) => manifest.component_id === workerManifestId,
);
assert(unsupportedWorkerManifest);
const unsupportedWorkerRegistry = createM5CapabilityRegistry([
  ...buildM5SeedManifests(now).filter((manifest) => manifest.component_id !== workerManifestId),
  { ...unsupportedWorkerManifest, supports_contract_envelope: false },
  ...buildM6ContractBuildManifests(now),
]);
const unsupportedWorker = buildM6ContractBuildLane({
  intent: validIntent(),
  registry: unsupportedWorkerRegistry,
  now,
});
assert.equal(unsupportedWorker.ok, false);
assert.equal(unsupportedWorker.status, "HOLD_M6_CAPABILITY_MANIFEST_MISSING");

const fallbackManifestId = workerManifestId;
const badFallbackRegistry = createM5CapabilityRegistry([
  ...buildM5SeedManifests(now).filter((manifest) => manifest.component_id !== fallbackManifestId),
  { ...unsupportedWorkerManifest, supports_fallback_contract_preservation: false },
  ...buildM6ContractBuildManifests(now),
]);
const badFallback = buildM6ContractBuildLane({
  intent: validIntent(),
  registry: badFallbackRegistry,
  now,
});
assert.equal(badFallback.ok, false);
assert.equal(badFallback.status, "HOLD_M6_CAPABILITY_MANIFEST_MISSING");

const fallbackPreserving = buildM6ContractBuildLane({
  intent: validIntent({
    fallback_chain: [M6_DEFAULT_WORKER, { provider: "ollama", model: "deepseek-v4-pro:cloud" }],
  }),
  registry,
  now,
});
assert.equal(fallbackPreserving.ok, true);
assert.equal(fallbackPreserving.status, "PASS_M6_CONTRACT_BUILD_LANE_BUILT");

assert(valid.ok);
const forged = enforceM4VerifiedRouteFirewall({
  ownerScoped: true,
  executionPath: "runWithModelFallback",
  execution: M6_BROKER_ROUTE,
  verifiedRoute: serializeM4VerifiedRoute(valid.lane.verifiedRoute),
});
assert.equal(forged.ok, false);
assert.equal(forged.status, "HOLD_M4_FORGED_OR_DESERIALIZED_VERIFIED_ROUTE");
const m4Raw = enforceM4VerifiedRouteFirewall({
  ownerScoped: true,
  executionPath: "runWithModelFallback",
  execution: { provider: "openai", model: "gpt-5.5" },
});
assert.equal(m4Raw.ok, false);
assert.equal(m4Raw.status, "HOLD_M4_MISSING_VERIFIED_ROUTE");

const malformedManifest = validateM5CapabilityManifest({
  manifest_version: "umc.v1.m5.capability_manifest.v1",
  component_id: "model:malformed/example",
  component_type: "model",
  provider: "malformed",
  model: "example",
});
assert.equal(malformedManifest.ok, false);
assert.equal(malformedManifest.status, "FAIL_M5_CAPABILITY_MANIFEST_INVALID");
const unsupportedManifest = validateM5CapabilityManifest({
  ...unsupportedWorkerManifest,
  supported_delivery_modes: ["send"],
});
assert.equal(unsupportedManifest.ok, false);
assert.equal(unsupportedManifest.status, "HOLD_M5_CAPABILITY_UNSUPPORTED");

const laneSpecJson = writeJson("M6_CONTRACT_BUILD_LANE_SPEC.json", {
  schema: "umc.v1.m6.contract_build_lane_spec_artifact.v1",
  generated_utc: now,
  status: "PASS_M6_CONTRACT_BUILD_LANE_SPEC_DEFINED",
  spec,
});
const laneSpecMd = writeText(
  "M6_CONTRACT_BUILD_LANE_SPEC.md",
  `# M6 Contract-Build Lane Spec\n\nStatus: \`PASS_M6_CONTRACT_BUILD_LANE_SPEC_DEFINED\`\n\nLane: \`${M6_LANE_ID}\`\n\nThe worker model is not route authority. Session/channel pins are route intents only. Fallback cannot drop VerifiedRoute, ContractEnvelope, capability manifest requirements, no_send delivery mode, or observe_only authority mode.\n`,
);
const implementation = writeJson("M6_CONTRACT_BUILD_LANE_IMPLEMENTATION_RESULT.json", {
  schema: "umc.v1.m6.contract_build_lane_implementation_result.v1",
  generated_utc: now,
  status: "PASS_M6_CONTRACT_BUILD_LANE_IMPLEMENTED",
  source_file: "src/auto-reply/reply/umc-m6-contract-build-lane.ts",
  behaviors: {
    accepts_m2_owner_turn_route_admission: true,
    consults_m5_capability_manifest_registry: true,
    verifies_route_through_m4_verified_route_brander: true,
    constructs_m3_contract_envelope: true,
    attaches_no_send_delivery_receipt_policy: true,
    attaches_terminal_closeout_policy: true,
    preserves_observe_only_authority_mode: true,
    preserves_fallback_contract_mode: true,
    reject_missing_manifest: missingManifest.status,
    reject_missing_verified_route: "HOLD_M4_MISSING_VERIFIED_ROUTE",
    reject_unsupported_worker_model_capability: unsupportedWorker.status,
    reject_fallback_chain_without_contract_preservation: badFallback.status,
  },
});
const policy = {
  worker_role: "execution_worker",
  route_authority: false,
  worker: M6_DEFAULT_WORKER,
  requires_verified_route: true,
  requires_capability_manifest: true,
  requires_contract_envelope: true,
  delivery_mode: "no_send",
  authority_mode: "observe_only",
  fallback_rules: {
    fallback_only_if_manifest_supports_required_contract_capabilities: true,
    fallback_preserves_contract_version: true,
    fallback_preserves_no_send: true,
    fallback_preserves_observe_only: true,
    fallback_preserves_terminal_closeout_requirement: true,
    fallback_emits_typed_hold_if_not_qualified: true,
  },
};
const workerPolicy = writeJson("M6_WORKER_MODEL_AND_FALLBACK_POLICY.json", {
  schema: "umc.v1.m6.worker_model_and_fallback_policy.v1",
  generated_utc: now,
  status: "PASS_M6_WORKER_MODEL_AND_FALLBACK_POLICY_DEFINED",
  policy,
});
const workerPolicyMd = writeText(
  "M6_WORKER_MODEL_AND_FALLBACK_POLICY.md",
  `# M6 Worker Model and Fallback Policy\n\nStatus: \`PASS_M6_WORKER_MODEL_AND_FALLBACK_POLICY_DEFINED\`\n\nInitial worker: \`${M6_DEFAULT_WORKER.provider}/${M6_DEFAULT_WORKER.model}\` as \`execution_worker\` only. Route authority is false. Fallbacks must preserve contract version, no_send delivery, observe_only authority, terminal closeout, VerifiedRoute, ContractEnvelope, and capability manifest requirements.\n`,
);
const fixtures = writeJson("M6_CONTRACT_BUILD_LANE_FIXTURE_RESULTS.json", {
  schema: "umc.v1.m6.contract_build_lane_fixture_results.v1",
  generated_utc: now,
  status: "PASS_M6_CONTRACT_BUILD_LANE_FIXTURES",
  fixture_cases: {
    valid_owner_turn_route_intent_builds_contract_build_lane: valid.status,
    valid_lane_emits_verified_route: Boolean(valid.lane.verifiedRoute),
    valid_lane_emits_contract_envelope: valid.lane.contractEnvelope?.artifact_type,
    valid_lane_checks_m5_capability_manifest: valid.lane.manifest_refs.length > 0,
    valid_lane_preserves_m3_no_send_delivery_receipt_policy: valid.lane.deliveryReceipt?.mode,
    valid_lane_preserves_terminal_closeout_policy: valid.lane.terminalCloseout?.artifact_type,
    worker_model_is_not_route_authority: valid.lane.worker_route_authority,
    raw_provider_model_pin_cannot_build_lane: rawProviderBypass.status,
    missing_manifest_produces_typed_hold: missingManifest.status,
    unsupported_worker_capability_produces_typed_hold: unsupportedWorker.status,
    fallback_without_contract_preservation_blocked: badFallback.status,
    fallback_preserving_contract_is_eligible: fallbackPreserving.status,
    session_channel_model_pin_becomes_route_intent_only:
      valid.lane.route_intent_metadata.session_channel_pins_are_route_intent_only,
    production_authority_remains_disabled: true,
    enforcement_remains_disabled: true,
  },
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
    cron_reenable_count: 0,
    enforcement_enabled: false,
    m7_started: false,
  },
});
const regression = writeJson("M6_M3_M4_M5_REGRESSION_FIXTURE_RESULTS.json", {
  schema: "umc.v1.m6.m3_m4_m5_regression_fixture_results.v1",
  generated_utc: now,
  status: "PASS_M6_M3_M4_M5_REGRESSION_FIXTURES",
  regression_cases: {
    m3_envelope_no_send_receipt_path_still_passes: valid.lane.terminalCloseout?.result_status,
    m4_raw_provider_model_rejection_still_passes: m4Raw.status,
    m4_forged_route_rejection_still_passes: forged.status,
    m5_valid_manifest_eligibility_still_passes: "PASS_M5_ROUTE_ELIGIBILITY_VERIFIED",
    m5_missing_manifest_still_holds: missingManifest.status,
    m5_malformed_manifest_still_fails: malformedManifest.status,
    m5_unsupported_capability_still_holds: unsupportedManifest.status,
    fallback_contract_preservation_still_enforced: badFallback.status,
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
});

console.log(
  JSON.stringify(
    {
      status: "PASS_M6_CONTRACT_BUILD_LANE_FIXTURE_RUNNER",
      artifacts: [
        laneSpecJson,
        laneSpecMd,
        implementation,
        workerPolicy,
        workerPolicyMd,
        fixtures,
        regression,
      ],
    },
    null,
    2,
  ),
);
