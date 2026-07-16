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
} from "../src/auto-reply/reply/umc-m5-capability-manifest.ts";
import { buildM6ContractBuildManifests } from "../src/auto-reply/reply/umc-m6-contract-build-lane.ts";
import {
  M7_DEFAULT_FALLBACK_WORKER,
  M7_DEFAULT_PRIMARY_WORKER,
  buildM7CapabilityManifests,
  buildM7EligibilityPolicy,
  buildM7FallbackEquivalenceContract,
} from "../src/auto-reply/reply/umc-m7-model-eligibility.ts";
import {
  M8_ENFORCEMENT_MODE,
  M8_MILESTONE,
  M8_POLICY_BOUNDARY_COUNTERS,
  M8_SOURCE_READY_STATUS,
  buildM8OwnerContractLaneCanaryContract,
  buildM8OwnerContractLanePolicy,
  buildM8ValidOwnerCanaryIntent,
  verifyM8OwnerContractLaneCanary,
} from "../src/auto-reply/reply/umc-m8-owner-contract-lane.ts";

const evidenceRoot =
  process.argv[2] ||
  path.resolve(
    process.cwd(),
    "../../workspace/sharedspace/runtime-kernel-validation/universal-model-contract/m3n_restart_persistence_no_send",
  );
fs.mkdirSync(evidenceRoot, { recursive: true });
const now = "2026-07-16T05:10:00.000Z";
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
  return {
    ...buildM5NoSendManifest({
      component_id: componentIdForRoute(route),
      component_type: "model",
      provider: route.provider,
      model: route.model,
      verified_at: now,
      evidence_refs: ["M8_OWNER_CONTRACT_LANE_ENFORCED_NO_SEND_CANARY_FIXTURE_RESULTS.json"],
    }),
    ...patch,
  };
}
function statusOf(result) {
  return result.status;
}

const m7CloseoutFile = path.join(
  evidenceRoot,
  "M7_MODEL_ELIGIBILITY_STAGED_INSTALL_AND_REGRESSION_CLOSEOUT.json",
);
const m7Closeout = JSON.parse(fs.readFileSync(m7CloseoutFile, "utf8"));
assert.equal(m7Closeout.status, "PASS_M7_MODEL_ELIGIBILITY_STAGED_INSTALL_AND_REGRESSION");
assert.equal(m7Closeout.next_milestone, "M8_OWNER_CONTRACT_LANE_ENFORCED_NO_SEND_CANARY");

const preflight = {
  schema: "umc.v1.m8.owner_contract_lane_enforced_no_send_canary_preflight.v1",
  generated_utc: now,
  status: "PASS_M8_OWNER_CONTRACT_LANE_ENFORCED_NO_SEND_CANARY_PREFLIGHT",
  milestone: M8_MILESTONE,
  m7_prerequisite_status: m7Closeout.status,
  m7_source_head_installed: m7Closeout.source_head_installed,
  m7_tarball_sha256: m7Closeout.tarball_sha256,
  m8_not_already_started: true,
  m9_not_started: true,
  source_fixture_only: true,
  no_apply_boundary: {
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
    m9_started: false,
    enforcement_enabled: false,
  },
};
const policy = buildM8OwnerContractLanePolicy();
assert.equal(policy.enforcement_mode, M8_ENFORCEMENT_MODE);
assert.equal(policy.source_fixture_only, true);
assert.equal(policy.broad_production_enforcement_allowed, false);
assert.equal(policy.production_authority_change_allowed, false);
assert.equal(policy.no_send_required, true);
const canaryContract = buildM8OwnerContractLaneCanaryContract();
assert.equal(canaryContract.enforced_in_source_fixtures_only, true);
assert.equal(canaryContract.terminal_closeout_required, true);
assert.ok(canaryContract.forbidden_actions.includes("Telegram send/probe"));
assert.equal(
  M8_SOURCE_READY_STATUS,
  "PASS_M8_OWNER_CONTRACT_LANE_ENFORCED_NO_SEND_CANARY_SOURCE_READY_NO_APPLY",
);

const valid = verifyM8OwnerContractLaneCanary({ intent: buildM8ValidOwnerCanaryIntent(), now });
assert.equal(valid.ok, true);
assert.equal(valid.status, "PASS_M8_OWNER_CONTRACT_LANE_ENFORCED_NO_SEND_CANARY_VERIFIED");
assert.equal(valid.evidence.worker_model_route_authority, false);
assert.equal(valid.evidence.delivery_mode, "no_send");
assert.equal(valid.evidence.production_authority_change, false);
assert.equal(valid.evidence.broad_production_enforcement, false);
assert.equal(valid.evidence.live_action_canary, false);

const nonOwner = verifyM8OwnerContractLaneCanary({
  intent: buildM8ValidOwnerCanaryIntent({ owner_scope: "group_turn" }),
  now,
});
assert.equal(statusOf(nonOwner), "HOLD_M8_OWNER_SCOPE_REQUIRED");
const sendMode = verifyM8OwnerContractLaneCanary({
  intent: buildM8ValidOwnerCanaryIntent({ delivery_mode: "send" }),
  now,
});
assert.equal(statusOf(sendMode), "HOLD_M8_NO_SEND_REQUIRED");
const productionAuthority = verifyM8OwnerContractLaneCanary({
  intent: buildM8ValidOwnerCanaryIntent({ production_authority_change: true }),
  now,
});
assert.equal(statusOf(productionAuthority), "FAIL_M8_PRODUCTION_AUTHORITY_CHANGE");
const broadProduction = verifyM8OwnerContractLaneCanary({
  intent: buildM8ValidOwnerCanaryIntent({
    canary_scope: "broad_production",
    broad_production_enforcement: true,
  }),
  now,
});
assert.equal(statusOf(broadProduction), "FAIL_M8_BROAD_PRODUCTION_ENFORCEMENT_FORBIDDEN");
const liveAction = verifyM8OwnerContractLaneCanary({
  intent: buildM8ValidOwnerCanaryIntent({ canary_scope: "live_action", live_action_canary: true }),
  now,
});
assert.equal(statusOf(liveAction), "HOLD_M8_LIVE_ACTION_CANARY_FORBIDDEN");
const boundarySend = verifyM8OwnerContractLaneCanary({
  intent: buildM8ValidOwnerCanaryIntent({ telegram_send_probe_count: 1 }),
  now,
});
assert.equal(statusOf(boundarySend), "FAIL_M8_SEND_OR_PROVIDER_CALL_BOUNDARY_VIOLATION");
const rawProvider = verifyM8OwnerContractLaneCanary({
  intent: buildM8ValidOwnerCanaryIntent({
    requested: { provider: "openai", model: "gpt-5.5" },
    executable: { provider: "openai", model: "gpt-5.5" },
  }),
  now,
});
assert.equal(statusOf(rawProvider), "FAIL_M8_RAW_MODEL_AUTHORITY_BYPASS");
const rawProviderViaContractCheck = verifyM8OwnerContractLaneCanary({
  intent: buildM8ValidOwnerCanaryIntent({
    requested: { provider: "openai", model: "gpt-5.5" },
  }),
  now,
});
assert.equal(statusOf(rawProviderViaContractCheck), "FAIL_M8_RAW_MODEL_AUTHORITY_BYPASS");
const missingManifestRoute = { provider: "missing-provider", model: "missing-model" };
const missingManifest = verifyM8OwnerContractLaneCanary({
  intent: buildM8ValidOwnerCanaryIntent(),
  primary_worker: missingManifestRoute,
  now,
});
assert.equal(statusOf(missingManifest), "HOLD_M8_M7_ELIGIBILITY_NOT_VERIFIED");
const fallbackDropRegistry = registryWith(
  [cloneManifestFor(M7_DEFAULT_FALLBACK_WORKER, { supports_contract_envelope: false })],
  [componentIdForRoute(M7_DEFAULT_FALLBACK_WORKER)],
);
const fallbackDrop = verifyM8OwnerContractLaneCanary({
  intent: buildM8ValidOwnerCanaryIntent(),
  registry: fallbackDropRegistry,
  fallback_chain: [M7_DEFAULT_FALLBACK_WORKER],
  now,
});
assert.equal(statusOf(fallbackDrop), "HOLD_M8_M7_ELIGIBILITY_NOT_VERIFIED");
const noM9 = verifyM8OwnerContractLaneCanary({
  intent: buildM8ValidOwnerCanaryIntent({ m9_started: true }),
  now,
});
assert.equal(statusOf(noM9), "FAIL_M8_SEND_OR_PROVIDER_CALL_BOUNDARY_VIOLATION");

const policyArtifact = {
  schema: "umc.v1.m8.owner_contract_lane_enforced_no_send_canary_policy.v1",
  generated_utc: now,
  status: "PASS_M8_OWNER_CONTRACT_LANE_ENFORCED_NO_SEND_CANARY_POLICY_DEFINED",
  policy,
  m7_policy: buildM7EligibilityPolicy(),
  boundary_counters: M8_POLICY_BOUNDARY_COUNTERS,
};
const policyMd = `# M8 Owner Contract Lane Enforced No-Send Canary Policy\n\nStatus: \`PASS_M8_OWNER_CONTRACT_LANE_ENFORCED_NO_SEND_CANARY_POLICY_DEFINED\`\n\nM8 is source/fixture-only. It allows only owner-turn contract-lane decisions that preserve M7 eligibility/fallback equivalence, M6 contract-build lane, no-send delivery, observe-only authority, terminal closeout, and zero send/provider/config/memory/context mutations.\n\nBroad production enforcement, live-action canaries, raw provider/model authority, worker route authority, Telegram probes/sends, provider live calls, durable memory writes, Context Bridge mutation, package install/apply, Gateway restart, and M9 are forbidden.\n`;
const contractArtifact = {
  schema: "umc.v1.m8.owner_contract_lane_enforced_no_send_canary_contract.v1",
  generated_utc: now,
  status: "PASS_M8_OWNER_CONTRACT_LANE_ENFORCED_NO_SEND_CANARY_CONTRACT_DEFINED",
  canary_contract: canaryContract,
  fallback_equivalence_contract: buildM7FallbackEquivalenceContract(),
  boundary_counters: M8_POLICY_BOUNDARY_COUNTERS,
};
const contractMd = `# M8 Owner Contract Lane Enforced No-Send Canary Contract\n\nStatus: \`PASS_M8_OWNER_CONTRACT_LANE_ENFORCED_NO_SEND_CANARY_CONTRACT_DEFINED\`\n\nAllow decision: \`${canaryContract.allow_decision}\`\n\nDeny/HOLD decision: \`${canaryContract.deny_decision}\`\n\nThe canary is enforced only in source fixtures and cannot perform live action or broad production enforcement.\n`;
const fixtureResults = {
  schema: "umc.v1.m8.owner_contract_lane_enforced_no_send_canary_fixture_results.v1",
  generated_utc: now,
  status: "PASS_M8_OWNER_CONTRACT_LANE_ENFORCED_NO_SEND_CANARY_FIXTURES",
  fixture_cases: {
    valid_owner_contract_lane_no_send: valid.status,
    non_owner_scope: nonOwner.status,
    send_delivery_blocked: sendMode.status,
    production_authority_change_blocked: productionAuthority.status,
    broad_production_enforcement_blocked: broadProduction.status,
    live_action_canary_blocked: liveAction.status,
    send_probe_boundary_violation_blocked: boundarySend.status,
    raw_provider_executable_blocked_by_m8: rawProvider.status,
    raw_provider_requested_blocked_by_m7: rawProviderViaContractCheck.status,
    missing_manifest_blocks_via_m7: missingManifest.status,
    fallback_contract_drop_blocks_via_m7: fallbackDrop.status,
    m9_start_blocked: noM9.status,
    worker_model_route_authority: valid.evidence.worker_model_route_authority,
    delivery_mode: valid.evidence.delivery_mode,
    authority_mode: valid.evidence.authority_mode,
  },
  source_fixture_only: true,
  live_action_canary_executed: false,
  boundary_counters: M8_POLICY_BOUNDARY_COUNTERS,
};
const regression = {
  schema: "umc.v1.m8.m3_m4_m5_m6_m7_source_regression_results.v1",
  generated_utc: now,
  status: "PASS_M8_M3_M4_M5_M6_M7_SOURCE_REGRESSION",
  results: {
    m3_receipts_preserved_via_m7_m6: valid.m7.m6.lane.deliveryReceipt?.mode,
    m4_verified_route_preserved: valid.m7.evidence.verifiedRoute_preserved,
    m5_manifests_preserved: valid.m7.evidence.primary_manifest,
    m6_contract_build_lane_preserved: valid.m7.m6.status,
    m7_model_eligibility_preserved: valid.m7.status,
    fallback_equivalence_preserved: valid.evidence.fallback_contract_preserved,
    raw_provider_model_authority_blocked: rawProviderViaContractCheck.status,
    worker_model_route_authority: valid.evidence.worker_model_route_authority,
  },
  boundary_counters: M8_POLICY_BOUNDARY_COUNTERS,
};
const liveDecision = {
  schema: "umc.v1.m8.live_action_canary_decision.v1",
  generated_utc: now,
  status: "SKIP_M8_LIVE_ACTION_CANARY_NOT_APPROVED_SOURCE_READY_ONLY",
  reason:
    "User explicitly requested source/fixture/no-apply only; no live-action canary, no sends/probes, no provider calls, no broad enforcement.",
  boundary_counters: M8_POLICY_BOUNDARY_COUNTERS,
};
const noApplyBuildValidation = {
  schema: "umc.v1.m8.no_apply_build_validation.v1",
  generated_utc: now,
  status: "PASS_M8_OWNER_CONTRACT_LANE_NO_APPLY_BUILD_VALIDATION_PENDING_FULL_BUILD",
  validation_results: {
    fixture_runner: "PASS_M8_OWNER_CONTRACT_LANE_FIXTURE_RUNNER",
    source_imports_via_tsx: "PASS",
    node_check_script: "PENDING_FINAL_VALIDATION",
    git_diff_check: "PENDING_FINAL_VALIDATION",
    full_build: "PENDING_FINAL_VALIDATION",
  },
  boundary_counters: M8_POLICY_BOUNDARY_COUNTERS,
};
const stagedInstallPlan = {
  schema: "umc.v1.m8.owner_contract_lane_staged_install_plan.v1",
  generated_utc: now,
  status: "PASS_M8_OWNER_CONTRACT_LANE_STAGED_INSTALL_PLAN_READY_NO_APPLY",
  do_not_install_in_this_milestone: true,
  source: {
    path: "/home/stickai/.openclaw/worktrees/umc-m3g-observe-only-hook-source-20260711",
    branch: "evidence/umc-m3g-observe-only-hook-source-20260711",
    source_commit: "PENDING_M8_SOURCE_COMMIT",
  },
  expected_installed_files_changed: ["dist/auto-reply/reply/umc-m8-owner-contract-lane.js"],
  approval_boundary:
    "No install, package apply, Gateway restart, Telegram probe/send, provider/model live call, config mutation, authority change, enforcement, M9, or live canary without explicit future approval.",
  boundary_counters: M8_POLICY_BOUNDARY_COUNTERS,
};
const stagedInstallPlanMd = `# M8 Owner Contract Lane Staged Install Plan\n\nStatus: \`PASS_M8_OWNER_CONTRACT_LANE_STAGED_INSTALL_PLAN_READY_NO_APPLY\`\n\nThis source-ready milestone does not install. A future staged install would require an exact approval card, package SHA, backup, install command, Gateway restart requirement, installed-runtime checks, regression, and stability evidence.\n`;

const artifacts = [
  writeJson("M8_OWNER_CONTRACT_LANE_ENFORCED_NO_SEND_CANARY_PREFLIGHT.json", preflight),
  writeJson("M8_OWNER_CONTRACT_LANE_ENFORCED_NO_SEND_CANARY_POLICY.json", policyArtifact),
  writeText("M8_OWNER_CONTRACT_LANE_ENFORCED_NO_SEND_CANARY_POLICY.md", policyMd),
  writeJson("M8_OWNER_CONTRACT_LANE_ENFORCED_NO_SEND_CANARY_CONTRACT.json", contractArtifact),
  writeText("M8_OWNER_CONTRACT_LANE_ENFORCED_NO_SEND_CANARY_CONTRACT.md", contractMd),
  writeJson("M8_OWNER_CONTRACT_LANE_ENFORCED_NO_SEND_CANARY_FIXTURE_RESULTS.json", fixtureResults),
  writeJson("M8_M3_M4_M5_M6_M7_SOURCE_REGRESSION_RESULTS.json", regression),
  writeJson("M8_LIVE_ACTION_CANARY_DECISION.json", liveDecision),
  writeJson("M8_OWNER_CONTRACT_LANE_NO_APPLY_BUILD_VALIDATION.json", noApplyBuildValidation),
  writeJson("M8_OWNER_CONTRACT_LANE_STAGED_INSTALL_PLAN.json", stagedInstallPlan),
  writeText("M8_OWNER_CONTRACT_LANE_STAGED_INSTALL_PLAN.md", stagedInstallPlanMd),
];
console.log(
  JSON.stringify({ status: "PASS_M8_OWNER_CONTRACT_LANE_FIXTURE_RUNNER", artifacts }, null, 2),
);
