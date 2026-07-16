#!/usr/bin/env node
import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import {
  buildM5NoSendManifest,
  buildM5SeedManifests,
  componentIdForRoute,
  createM5CapabilityRegistry,
  validateM5CapabilityManifest,
} from "../src/auto-reply/reply/umc-m5-capability-manifest.ts";
import {
  M6_BROKER_ROUTE,
  buildM6ContractBuildManifests,
  buildM6ContractBuildLane,
  createM6CapabilityRegistry,
} from "../src/auto-reply/reply/umc-m6-contract-build-lane.ts";
import {
  M7_DEFAULT_FALLBACK_WORKER,
  M7_DEFAULT_PRIMARY_WORKER,
  M7_FALLBACK_ADAPTER_ID,
  M7_PRIMARY_ADAPTER_ID,
  M7_POLICY_BOUNDARY_COUNTERS,
  buildM7CapabilityManifests,
  buildM7EligibilityPolicy,
  buildM7FallbackEquivalenceContract,
  buildM7ValidIntent,
  createM7CapabilityRegistry,
  verifyM7ModelEligibility,
} from "../src/auto-reply/reply/umc-m7-model-eligibility.ts";

const evidenceRoot =
  process.argv[2] ||
  path.resolve(
    process.cwd(),
    "../../workspace/sharedspace/runtime-kernel-validation/universal-model-contract/m3n_restart_persistence_no_send",
  );
fs.mkdirSync(evidenceRoot, { recursive: true });
const now = "2026-07-16T03:58:00.000Z";
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
function registryWith(replacements = [], removals = []) {
  const remove = new Set(removals);
  const base = [
    ...buildM5SeedManifests(now),
    ...buildM6ContractBuildManifests(now),
    ...buildM7CapabilityManifests(now),
  ].filter((manifest) => !remove.has(manifest.component_id));
  return createM5CapabilityRegistry([...base, ...replacements]);
}
function cloneManifestFor(route, patch) {
  const manifest = buildM5NoSendManifest({
    component_id: componentIdForRoute(route),
    component_type: "model",
    provider: route.provider,
    model: route.model,
    verified_at: now,
    evidence_refs: ["M7_MODEL_FALLBACK_ELIGIBILITY_MATRIX.json"],
  });
  return { ...manifest, ...patch };
}
function cloneAdapterManifest(adapterId, patch) {
  const manifest = buildM5NoSendManifest({
    component_id: adapterId,
    component_type: "adapter",
    adapter_id: adapterId.replace(/^adapter:/u, ""),
    verified_at: now,
    evidence_refs: ["M7_MODEL_FALLBACK_ELIGIBILITY_MATRIX.json"],
  });
  return { ...manifest, ...patch };
}

const policy = buildM7EligibilityPolicy();
assert.equal(policy.worker_policy.worker_role, "execution_worker");
assert.equal(policy.worker_policy.route_authority, false);
assert.equal(policy.worker_policy.delivery_mode, "no_send");
assert.equal(policy.worker_policy.authority_mode, "observe_only");
const equivalence = buildM7FallbackEquivalenceContract();
assert.equal(equivalence.no_provider_model_route_authority, true);

const registry = createM7CapabilityRegistry(now);
assert.equal(registry.rejected.length, 0);
const eligiblePrimary = verifyM7ModelEligibility({
  intent: buildM7ValidIntent(),
  registry,
  now,
});
assert.equal(eligiblePrimary.ok, true);
assert.equal(eligiblePrimary.status, "PASS_M7_MODEL_ELIGIBILITY_VERIFIED");
assert.equal(eligiblePrimary.evidence.worker_model_route_authority, false);
assert.equal(eligiblePrimary.m6.status, "PASS_M6_CONTRACT_BUILD_LANE_BUILT");

const eligibleFallback = verifyM7ModelEligibility({
  intent: buildM7ValidIntent(),
  registry,
  fallback_chain: [M7_DEFAULT_FALLBACK_WORKER],
  now,
});
assert.equal(eligibleFallback.ok, true);
assert.equal(eligibleFallback.status, "PASS_M7_MODEL_ELIGIBILITY_VERIFIED");

const missingManifestRoute = { provider: "missing-provider", model: "missing-model" };
const missingManifest = verifyM7ModelEligibility({
  intent: buildM7ValidIntent(),
  registry,
  primary_worker: missingManifestRoute,
  fallback_chain: [M7_DEFAULT_FALLBACK_WORKER],
  now,
});
assert.equal(missingManifest.ok, false);
assert.equal(missingManifest.status, "HOLD_M7_CAPABILITY_MANIFEST_MISSING");

const malformedRoute = { provider: "malformed", model: "invalid-manifest" };
const malformedRegistry = registryWith(
  [
    {
      manifest_version: "umc.v1.m5.capability_manifest.v1",
      component_id: componentIdForRoute(malformedRoute),
      component_type: "model",
      provider: malformedRoute.provider,
      model: malformedRoute.model,
    },
  ],
  [componentIdForRoute(malformedRoute)],
);
const malformedManifest = verifyM7ModelEligibility({
  intent: buildM7ValidIntent(),
  registry: malformedRegistry,
  primary_worker: malformedRoute,
  fallback_chain: [M7_DEFAULT_FALLBACK_WORKER],
  now,
});
assert.equal(malformedManifest.ok, false);
assert.equal(malformedManifest.status, "FAIL_M7_CAPABILITY_MANIFEST_INVALID");

const unsupportedNoSendRoute = { provider: "unsupported", model: "no-send" };
const unsupportedNoSendRegistry = registryWith(
  [
    cloneManifestFor(unsupportedNoSendRoute, {
      supported_delivery_modes: ["send"],
      supports_no_send: false,
    }),
  ],
  [componentIdForRoute(unsupportedNoSendRoute)],
);
const unsupportedNoSend = verifyM7ModelEligibility({
  intent: buildM7ValidIntent(),
  registry: unsupportedNoSendRegistry,
  primary_worker: unsupportedNoSendRoute,
  fallback_chain: [M7_DEFAULT_FALLBACK_WORKER],
  now,
});
assert.equal(unsupportedNoSend.ok, false);
assert.equal(unsupportedNoSend.status, "HOLD_M7_UNSUPPORTED_NO_SEND");

const unsupportedEnvelopeRoute = { provider: "unsupported", model: "contract-envelope" };
const unsupportedEnvelopeRegistry = registryWith(
  [cloneManifestFor(unsupportedEnvelopeRoute, { supports_contract_envelope: false })],
  [componentIdForRoute(unsupportedEnvelopeRoute)],
);
const unsupportedEnvelope = verifyM7ModelEligibility({
  intent: buildM7ValidIntent(),
  registry: unsupportedEnvelopeRegistry,
  primary_worker: unsupportedEnvelopeRoute,
  fallback_chain: [M7_DEFAULT_FALLBACK_WORKER],
  now,
});
assert.equal(unsupportedEnvelope.ok, false);
assert.equal(unsupportedEnvelope.status, "HOLD_M7_UNSUPPORTED_CONTRACT_ENVELOPE");

const unsupportedReceiptRoute = { provider: "unsupported", model: "delivery-receipt" };
const unsupportedReceiptRegistry = registryWith(
  [cloneManifestFor(unsupportedReceiptRoute, { supports_delivery_receipt: false })],
  [componentIdForRoute(unsupportedReceiptRoute)],
);
const unsupportedReceipt = verifyM7ModelEligibility({
  intent: buildM7ValidIntent(),
  registry: unsupportedReceiptRegistry,
  primary_worker: unsupportedReceiptRoute,
  fallback_chain: [M7_DEFAULT_FALLBACK_WORKER],
  now,
});
assert.equal(unsupportedReceipt.ok, false);
assert.equal(unsupportedReceipt.status, "HOLD_M7_UNSUPPORTED_DELIVERY_RECEIPT");

const fallbackDropRegistry = registryWith(
  [cloneManifestFor(M7_DEFAULT_FALLBACK_WORKER, { supports_contract_envelope: false })],
  [componentIdForRoute(M7_DEFAULT_FALLBACK_WORKER)],
);
const fallbackDrop = verifyM7ModelEligibility({
  intent: buildM7ValidIntent(),
  registry: fallbackDropRegistry,
  fallback_chain: [M7_DEFAULT_FALLBACK_WORKER],
  now,
});
assert.equal(fallbackDrop.ok, false);
assert.equal(fallbackDrop.status, "HOLD_M7_FALLBACK_CONTRACT_DROP");

const fallbackDeliveryRegistry = registryWith(
  [
    cloneManifestFor(M7_DEFAULT_FALLBACK_WORKER, {
      supported_delivery_modes: ["send"],
      supports_no_send: false,
    }),
  ],
  [componentIdForRoute(M7_DEFAULT_FALLBACK_WORKER)],
);
const fallbackDeliveryChange = verifyM7ModelEligibility({
  intent: buildM7ValidIntent(),
  registry: fallbackDeliveryRegistry,
  fallback_chain: [M7_DEFAULT_FALLBACK_WORKER],
  now,
});
assert.equal(fallbackDeliveryChange.ok, false);
assert.equal(fallbackDeliveryChange.status, "HOLD_M7_FALLBACK_DELIVERY_MODE_CHANGED");

const fallbackAuthorityRegistry = registryWith(
  [
    cloneManifestFor(M7_DEFAULT_FALLBACK_WORKER, {
      authority_modes: ["production"],
      supports_observe_only: false,
    }),
  ],
  [componentIdForRoute(M7_DEFAULT_FALLBACK_WORKER)],
);
const fallbackAuthorityChange = verifyM7ModelEligibility({
  intent: buildM7ValidIntent(),
  registry: fallbackAuthorityRegistry,
  fallback_chain: [M7_DEFAULT_FALLBACK_WORKER],
  now,
});
assert.equal(fallbackAuthorityChange.ok, false);
assert.equal(fallbackAuthorityChange.status, "FAIL_M7_CAPABILITY_MANIFEST_INVALID");

const rawProviderPin = verifyM7ModelEligibility({
  intent: buildM7ValidIntent({
    requested: { provider: "openai", model: "gpt-5.5" },
    executable: { provider: "openai", model: "gpt-5.5" },
  }),
  registry,
  now,
});
assert.equal(rawProviderPin.ok, false);
assert.equal(rawProviderPin.status, "FAIL_M7_RAW_MODEL_AUTHORITY_BYPASS");

const rawM6 = buildM6ContractBuildLane({
  intent: buildM7ValidIntent({
    requested: { provider: "openai", model: "gpt-5.5" },
    executable: { provider: "openai", model: "gpt-5.5" },
  }),
  registry,
  now,
});
assert.equal(rawM6.ok, false);
assert.equal(rawM6.status, "FAIL_M6_RAW_MODEL_AUTHORITY_BYPASS");
const validM6 = buildM6ContractBuildLane({ intent: buildM7ValidIntent(), registry, now });
assert.equal(validM6.ok, true);
assert.equal(validM6.status, "PASS_M6_CONTRACT_BUILD_LANE_BUILT");
assert.equal(validM6.lane.deliveryReceipt?.mode, "no_send");
assert.equal(validM6.lane.worker_route_authority, false);

const malformedM5 = validateM5CapabilityManifest({
  component_id: "model:malformed/example",
  component_type: "model",
});
assert.equal(malformedM5.ok, false);
assert.equal(malformedM5.status, "FAIL_M5_CAPABILITY_MANIFEST_INVALID");

const matrix = {
  primary_eligible_worker: {
    route: M7_DEFAULT_PRIMARY_WORKER,
    result: eligiblePrimary.status,
  },
  configured_fallback_chain: [
    { route: M7_DEFAULT_FALLBACK_WORKER, result: eligibleFallback.status },
  ],
  missing_manifest_model: { route: missingManifestRoute, result: missingManifest.status },
  malformed_manifest_model: { route: malformedRoute, result: malformedManifest.status },
  unsupported_no_send_model: { route: unsupportedNoSendRoute, result: unsupportedNoSend.status },
  unsupported_contract_envelope_model: {
    route: unsupportedEnvelopeRoute,
    result: unsupportedEnvelope.status,
  },
  unsupported_delivery_receipt_model: {
    route: unsupportedReceiptRoute,
    result: unsupportedReceipt.status,
  },
  fallback_preserving_contract: {
    route: M7_DEFAULT_FALLBACK_WORKER,
    result: eligibleFallback.status,
  },
  fallback_dropping_contract: { route: M7_DEFAULT_FALLBACK_WORKER, result: fallbackDrop.status },
  fallback_changing_authority_mode: {
    route: M7_DEFAULT_FALLBACK_WORKER,
    result: fallbackAuthorityChange.status,
  },
  fallback_changing_delivery_mode: {
    route: M7_DEFAULT_FALLBACK_WORKER,
    result: fallbackDeliveryChange.status,
  },
  raw_provider_model_pin: {
    route: { provider: "openai", model: "gpt-5.5" },
    result: rawProviderPin.status,
  },
};

const policyArtifact = writeJson("M7_MODEL_ELIGIBILITY_POLICY.json", {
  schema: "umc.v1.m7.model_eligibility_policy_artifact.v1",
  generated_utc: now,
  status: "PASS_M7_MODEL_ELIGIBILITY_POLICY_DEFINED",
  policy,
  boundary_counters: M7_POLICY_BOUNDARY_COUNTERS,
});
const policyMd = writeText(
  "M7_MODEL_ELIGIBILITY_POLICY.md",
  `# M7 Model Eligibility Policy\n\nStatus: \`PASS_M7_MODEL_ELIGIBILITY_POLICY_DEFINED\`\n\nPrimary worker: \`${M7_DEFAULT_PRIMARY_WORKER.provider}/${M7_DEFAULT_PRIMARY_WORKER.model}\` as \`execution_worker\` only. Route authority is \`false\`. Eligibility requires M5 manifest acceptance, M4 VerifiedRoute via the M6 contract-build lane, ContractEnvelope, DeliveryReceipt \`no_send\`, TerminalContractCloseout, and observe-only authority. Session/channel model pins remain route intent only.\n`,
);
const matrixArtifact = writeJson("M7_MODEL_FALLBACK_ELIGIBILITY_MATRIX.json", {
  schema: "umc.v1.m7.model_fallback_eligibility_matrix.v1",
  generated_utc: now,
  status: "PASS_M7_MODEL_FALLBACK_MATRIX_DEFINED",
  matrix,
  boundary_counters: M7_POLICY_BOUNDARY_COUNTERS,
});
const matrixMd = writeText(
  "M7_MODEL_FALLBACK_ELIGIBILITY_MATRIX.md",
  `# M7 Model/Fallback Eligibility Matrix\n\nStatus: \`PASS_M7_MODEL_FALLBACK_MATRIX_DEFINED\`\n\nThe matrix covers eligible primary, configured fallback, missing/malformed manifests, unsupported no_send/ContractEnvelope/DeliveryReceipt models, contract-preserving and contract-dropping fallbacks, authority/delivery-mode changes, and raw provider/model pin rejection.\n`,
);
const implementation = writeJson("M7_MODEL_ELIGIBILITY_CHECKER_IMPLEMENTATION_RESULT.json", {
  schema: "umc.v1.m7.model_eligibility_checker_implementation_result.v1",
  generated_utc: now,
  status: "PASS_M7_MODEL_ELIGIBILITY_CHECKER_IMPLEMENTED",
  source_file: "src/auto-reply/reply/umc-m7-model-eligibility.ts",
  behaviors: {
    valid_primary_worker_qualifies_only_through_manifest_verifiedroute_contract_lane:
      eligiblePrimary.status,
    valid_fallback_qualifies_only_if_contract_preserved: eligibleFallback.status,
    missing_manifest_returns_typed_hold: missingManifest.status,
    malformed_manifest_returns_typed_fail: malformedManifest.status,
    unsupported_no_send_returns_typed_hold: unsupportedNoSend.status,
    unsupported_contract_envelope_returns_typed_hold: unsupportedEnvelope.status,
    unsupported_delivery_receipt_returns_typed_hold: unsupportedReceipt.status,
    fallback_dropping_contract_returns_typed_hold: fallbackDrop.status,
    fallback_changing_authority_mode_returns_typed_hold_or_fail: fallbackAuthorityChange.status,
    fallback_changing_delivery_mode_returns_typed_hold_or_fail: fallbackDeliveryChange.status,
    raw_provider_model_pin_cannot_qualify: rawProviderPin.status,
    session_channel_model_pin_remains_route_intent_only:
      eligiblePrimary.m6.lane.route_intent_metadata.session_channel_pins_are_route_intent_only,
  },
  boundary_counters: M7_POLICY_BOUNDARY_COUNTERS,
});
const equivalenceArtifact = writeJson("M7_FALLBACK_EQUIVALENCE_CONTRACT.json", {
  schema: "umc.v1.m7.fallback_equivalence_contract_artifact.v1",
  generated_utc: now,
  status: "PASS_M7_FALLBACK_EQUIVALENCE_CONTRACT_DEFINED",
  equivalence,
  boundary_counters: M7_POLICY_BOUNDARY_COUNTERS,
});
const equivalenceMd = writeText(
  "M7_FALLBACK_EQUIVALENCE_CONTRACT.md",
  `# M7 Fallback Equivalence Contract\n\nStatus: \`PASS_M7_FALLBACK_EQUIVALENCE_CONTRACT_DEFINED\`\n\nA fallback is equivalent only if it preserves VerifiedRoute, ContractEnvelope, capability manifest eligibility, delivery_mode \`no_send\`, authority_mode \`observe_only\`, terminal closeout, tool policy, postcondition policy, safety counters, and no provider/model route authority.\n`,
);
const fixtures = writeJson("M7_MODEL_ELIGIBILITY_AND_FALLBACK_FIXTURE_RESULTS.json", {
  schema: "umc.v1.m7.model_eligibility_and_fallback_fixture_results.v1",
  generated_utc: now,
  status: "PASS_M7_MODEL_ELIGIBILITY_AND_FALLBACK_FIXTURES",
  fixture_cases: {
    eligible_primary_worker_qualifies: eligiblePrimary.status,
    eligible_fallback_preserving_contract_qualifies: eligibleFallback.status,
    missing_manifest_blocks_with_hold: missingManifest.status,
    malformed_manifest_fails: malformedManifest.status,
    unsupported_no_send_blocks: unsupportedNoSend.status,
    unsupported_contract_envelope_blocks: unsupportedEnvelope.status,
    unsupported_delivery_receipt_blocks: unsupportedReceipt.status,
    fallback_dropping_contract_envelope_blocks: fallbackDrop.status,
    fallback_changing_delivery_mode_blocks: fallbackDeliveryChange.status,
    fallback_changing_authority_mode_blocks: fallbackAuthorityChange.status,
    raw_provider_model_pin_rejected: rawProviderPin.status,
    session_channel_model_pin_cannot_become_authority:
      eligiblePrimary.m6.lane.route_intent_metadata.session_channel_pins_are_route_intent_only,
    worker_model_route_authority_remains_false:
      eligiblePrimary.evidence.worker_model_route_authority,
    contract_build_lane_remains_valid: validM6.status,
    m3_envelope_no_send_receipts_still_pass: validM6.lane.deliveryReceipt?.mode,
    m4_raw_provider_model_bypass_still_blocked: rawM6.status,
    m5_manifest_registry_behavior_still_passes: registry.rejected.length === 0,
  },
  boundary_counters: M7_POLICY_BOUNDARY_COUNTERS,
});
const liveDecision = writeJson("M7_LIVE_CALL_QUALIFICATION_DECISION.json", {
  schema: "umc.v1.m7.live_call_qualification_decision.v1",
  generated_utc: now,
  status: "SKIP_M7_LIVE_MODEL_CALL_QUALIFICATION_NOT_REQUIRED",
  reason:
    "Focused source/fixture evidence qualifies model/fallback contract behavior; no live provider/model call is required or approved.",
  provider_model_live_call_count: 0,
  approval_required_for_future_live_call: true,
  boundary_counters: M7_POLICY_BOUNDARY_COUNTERS,
});
const regression = writeJson("M7_M3_M4_M5_M6_REGRESSION_RESULTS.json", {
  schema: "umc.v1.m7.m3_m4_m5_m6_regression_results.v1",
  generated_utc: now,
  status: "PASS_M7_M3_M4_M5_M6_REGRESSION",
  regression: {
    m3_envelope_no_send_receipts_still_pass: validM6.lane.deliveryReceipt?.mode,
    m4_verified_route_firewall_blocks_raw_provider_model_authority: rawM6.status,
    m5_manifests_gate_route_eligibility: malformedM5.status,
    m6_contract_build_lane_builds_valid_contract_qualified_lane: validM6.status,
    fallback_preservation_still_enforced: fallbackDrop.status,
    provider_model_live_call_occurred: false,
    telegram_send_probe_occurred: false,
    route_config_mutation_occurred: false,
    durable_memory_mutation_occurred: false,
    context_bridge_mutation_occurred: false,
    production_authority_change_occurred: false,
  },
  boundary_counters: M7_POLICY_BOUNDARY_COUNTERS,
});
const noApply = writeJson("M7_MODEL_ELIGIBILITY_NO_APPLY_BUILD_VALIDATION.json", {
  schema: "umc.v1.m7.model_eligibility_no_apply_build_validation.v1",
  generated_utc: now,
  status: "PASS_M7_MODEL_ELIGIBILITY_NO_APPLY_BUILD_VALIDATION",
  validation_results: {
    fixture_runner: "PASS_M7_MODEL_ELIGIBILITY_FIXTURE_RUNNER",
    source_imports_via_tsx: "PASS",
    node_check_script: "PASS",
    json_validation: "PENDING_FINAL_VALIDATION",
    git_diff_check: "PENDING_FINAL_VALIDATION",
    full_build: "NOT_RUN_SOURCE_NO_APPLY_MILESTONE; staged install plan only",
  },
  boundary_counters: M7_POLICY_BOUNDARY_COUNTERS,
});
const stagedInstallPlan = writeJson("M7_MODEL_ELIGIBILITY_STAGED_INSTALL_PLAN.json", {
  schema: "umc.v1.m7.model_eligibility_staged_install_plan.v1",
  generated_utc: now,
  status: "PASS_M7_MODEL_ELIGIBILITY_STAGED_INSTALL_PLAN_READY",
  do_not_install_in_this_milestone: true,
  source: {
    path: "/home/stickai/.openclaw/worktrees/umc-m3g-observe-only-hook-source-20260711",
    branch: "evidence/umc-m3g-observe-only-hook-source-20260711",
    head: "RECORDED_AFTER_SOURCE_COMMIT",
    source_commit: "RECORDED_AFTER_SOURCE_COMMIT",
  },
  build_package: {
    command:
      "/home/stickai/.openclaw/workspace/tmp/openclaw-start-ack-pnpm-shim/pnpm build && npm pack --ignore-scripts",
    package_tarball_path: "TBD_IN_M7_MODEL_ELIGIBILITY_STAGED_INSTALL_AND_REGRESSION",
  },
  expected_installed_files_changed: ["dist/auto-reply/reply/umc-m7-model-eligibility.js"],
  backup_path_template:
    "/home/stickai/.openclaw/backups/openclaw-m7-model-eligibility-install-<UTC>/openclaw-installed-package",
  rollback_command:
    "npm install -g --ignore-scripts /home/stickai/.openclaw/workspace/tmp/umc-m6-package/openclaw-2026.5.7.tgz && openclaw gateway restart",
  health_validation: {
    gateway: "openclaw gateway status must report running/connectivity/admin-capable",
    telegram:
      "openclaw channels status must report Telegram enabled/configured/running/connected; no Telegram send/probe",
  },
  regression_plan: {
    m3: "Verify envelope/no-send receipts and terminal closeout.",
    m4: "Verify raw provider/model authority remains blocked.",
    m5: "Verify model/adapter manifests gate route eligibility.",
    m6: "Verify contract-build lane still builds contract-qualified lane.",
    m7: "Verify installed model eligibility and fallback equivalence checker statuses.",
  },
  approval_boundary:
    "No install, Gateway restart, Telegram probe, provider/model live call, config mutation, authority, enforcement, or M8 without explicit staged-install approval.",
  boundary_counters: M7_POLICY_BOUNDARY_COUNTERS,
});
const stagedInstallPlanMd = writeText(
  "M7_MODEL_ELIGIBILITY_STAGED_INSTALL_PLAN.md",
  `# M7 Model Eligibility Staged Install Plan\n\nStatus: \`PASS_M7_MODEL_ELIGIBILITY_STAGED_INSTALL_PLAN_READY\`\n\nThis is a staged install plan only. Do not install in \`M7_MODEL_ELIGIBILITY_AND_FALLBACK_EQUIVALENCE_NO_SEND\`.\n\nExpected installed file: \`dist/auto-reply/reply/umc-m7-model-eligibility.js\`.\n\nValidation after future approval must cover Gateway/Telegram health, M3/M4/M5/M6 regressions, and installed M7 eligibility/fallback equivalence checks. No Telegram send/probe, live provider call, config mutation, production authority, enforcement, or M8 is authorized by this plan.\n`,
);

console.log(
  JSON.stringify(
    {
      status: "PASS_M7_MODEL_ELIGIBILITY_FIXTURE_RUNNER",
      artifacts: [
        policyArtifact,
        policyMd,
        matrixArtifact,
        matrixMd,
        implementation,
        equivalenceArtifact,
        equivalenceMd,
        fixtures,
        liveDecision,
        regression,
        noApply,
        stagedInstallPlan,
        stagedInstallPlanMd,
      ],
      key_results: {
        eligiblePrimary: eligiblePrimary.status,
        eligibleFallback: eligibleFallback.status,
        missingManifest: missingManifest.status,
        malformedManifest: malformedManifest.status,
        fallbackDrop: fallbackDrop.status,
        rawProviderPin: rawProviderPin.status,
        workerRouteAuthority: eligiblePrimary.evidence.worker_model_route_authority,
      },
    },
    null,
    2,
  ),
);
