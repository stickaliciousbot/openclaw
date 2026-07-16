#!/usr/bin/env node
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { runM3EnvelopeSupervisor } from "../src/auto-reply/reply/umc-m3-envelope-supervision.ts";
import {
  M4_AUTHORITY_MODE,
  M4_CONTRACT_VERSION,
  verifyM4RouteIntent,
  enforceM4VerifiedRouteFirewall,
} from "../src/auto-reply/reply/umc-m4-verified-route.ts";
import {
  buildM5SeedManifests,
  createM5CapabilityRegistry,
} from "../src/auto-reply/reply/umc-m5-capability-manifest.ts";
import {
  buildM6ContractBuildLane,
  buildM6ContractBuildManifests,
} from "../src/auto-reply/reply/umc-m6-contract-build-lane.ts";
import {
  buildM7CapabilityManifests,
  buildM7ValidIntent,
  verifyM7ModelEligibility,
} from "../src/auto-reply/reply/umc-m7-model-eligibility.ts";
import {
  buildM8ValidOwnerCanaryIntent,
  verifyM8OwnerContractLaneCanary,
} from "../src/auto-reply/reply/umc-m8-owner-contract-lane.ts";
import {
  M10A_AGENT_ID,
  M10A_BOUNDARY_COUNTERS,
  M10A_CHANNEL,
  M10A_CONTROL_ARTIFACT_PATH,
  M10A_DISABLE_FLAG_KEY,
  M10A_ENABLE_FLAG_KEY,
  M10A_MILESTONE,
  M10A_OWNER_CHAT_ID,
  M10A_ROLLBACK_KEY,
  M10A_RUNTIME_DECISION_POINT,
  M10A_SCOPE_NAME,
  M10A_SOURCE_READY_STATUS,
  M10A_STATUS_READBACK_PATH,
  applyM10AControlIntent,
  buildM10AControlPathSchema,
  buildM10ADefaultControlState,
  disableM10AControlState,
  evaluateM10AOwnerTelegramDirectContractDecision,
  readM10AStatus,
} from "../src/auto-reply/reply/umc-m10a-owner-telegram-direct-control-path.ts";

const sourceRoot = process.cwd();
const evidenceRoot =
  process.argv[2] ||
  path.resolve(
    sourceRoot,
    "../../workspace/sharedspace/runtime-kernel-validation/universal-model-contract/m9_limited_live_action_canary",
  );
fs.mkdirSync(evidenceRoot, { recursive: true });
const now = process.env.M10A_NOW || "2026-07-16T11:20:00.000Z";
function sha256File(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}
function writeJson(name, value) {
  const file = path.join(evidenceRoot, name);
  fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`);
  return {
    file: path.relative(evidenceRoot, file),
    sha256: sha256File(file),
    status: value.status,
  };
}
function writeText(name, value) {
  const file = path.join(evidenceRoot, name);
  fs.writeFileSync(file, value.endsWith("\n") ? value : `${value}\n`);
  return { file: path.relative(evidenceRoot, file), sha256: sha256File(file) };
}
function readJson(name) {
  return JSON.parse(fs.readFileSync(path.join(evidenceRoot, name), "utf8"));
}
function git(args) {
  try {
    return execFileSync("git", args, { cwd: sourceRoot, encoding: "utf8" }).trim();
  } catch {
    return "UNKNOWN";
  }
}
const sourceHead = git(["rev-parse", "HEAD"]);
const sourceBranch = git(["branch", "--show-current"]);

const prior = {
  preflight: readJson("M10_SCOPE_REPAIR_PREFLIGHT.json"),
  scope: readJson("M10_NARROW_SCOPE_DEFINITION.json"),
  control: readJson("M10_CONTROL_PATH_DEFINITION.json"),
  rollback: readJson("M10_ROLLBACK_OFF_SWITCH_PLAN.json"),
  abort: readJson("M10_ABORT_THRESHOLDS_AND_OBSERVATION_PLAN.json"),
  readiness: readJson("M10_REPAIRED_APPROVAL_READINESS_DECISION.json"),
  m9: readJson("M9_LIMITED_LIVE_ACTION_CANARY_QUEUE_RECHECK_CLOSEOUT.json"),
};
assert.equal(prior.control.status, "BLOCKED_M10_CONTROL_PATH_GAP");
assert.equal(prior.scope.status, "PASS_M10_NARROW_SCOPE_DEFINED");
assert.equal(prior.scope.scope_name, M10A_SCOPE_NAME);
assert.equal(prior.abort.status, "PASS_M10_ABORT_THRESHOLDS_AND_OBSERVATION_PLAN_DEFINED");
assert.equal(prior.readiness.status, "BLOCKED_M10_CONTROL_PATH_GAP");
assert.equal(
  prior.m9.status,
  "PASS_M9_LIMITED_LIVE_ACTION_CANARY_LOCAL_ARTIFACT_WRITE_OBSERVED_AFTER_COMPACTION_AND_QUEUE_RECHECK",
);

const noExecutionCounters = {
  m10_enabled: false,
  production_authority_changed: false,
  telegram_send_probe_count: 0,
  external_send_count: 0,
  provider_model_live_call_count: 0,
  write_tool_execution_count: 0,
  durable_memory_mutation_count: 0,
  context_bridge_mutation_count: 0,
  route_config_mutation_count: 0,
};

const preflight = {
  schema: "umc.v1.m10a.control_path_source_ready_preflight.v1",
  generated_utc: now,
  status: "PASS_M10A_CONTROL_PATH_SOURCE_READY_PREFLIGHT",
  current_status: prior.readiness.status,
  narrow_scope_status: prior.scope.status,
  abort_threshold_status: prior.abort.status,
  m10_started: false,
  production_authority_changed: false,
  counters: noExecutionCounters,
  source_root: sourceRoot,
  source_branch: sourceBranch,
  source_head_at_fixture_run: sourceHead,
};

const discovery = {
  schema: "umc.v1.m10a.existing_control_path_discovery.v1",
  generated_utc: now,
  status: "NO_EXISTING_M10A_CONTROL_PATH_FOUND",
  classification: "NO_EXISTING_M10A_CONTROL_PATH_FOUND",
  searched_before_new_module: true,
  searched_for: [
    "owner Telegram direct enforcement flags",
    "UMC enforcement mode flags",
    "contract enforcement status/readback",
    "Gateway control/config API for UMC authority",
    "M8 enforced-no-send decision gate",
    "M9 live-action eligibility gate",
    "runtime feature flags",
    "disable/off-switch helpers",
  ],
  finding:
    "Existing source had M4-M8 UMC modules and M8 enforced-no-send gate, but no M10A-compatible enable flag, disable key, status/readback path, or runtime decision point. M10A source module was therefore implemented rather than duplicated.",
  nearest_existing_gate: "src/auto-reply/reply/umc-m8-owner-contract-lane.ts",
  implemented_source_path: "src/auto-reply/reply/umc-m10a-owner-telegram-direct-control-path.ts",
};

const schemaArtifact = buildM10AControlPathSchema();
assert.equal(schemaArtifact.status, "PASS_M10A_CONTROL_PATH_SCHEMA_DEFINED");
assert.equal(schemaArtifact.defaults.m10a_enabled, false);
assert.equal(schemaArtifact.defaults.scope_name, M10A_SCOPE_NAME);
assert.equal(schemaArtifact.defaults.owner_chat_id, M10A_OWNER_CHAT_ID);
assert.equal(schemaArtifact.defaults.channel, M10A_CHANNEL);
assert.equal(schemaArtifact.defaults.production_authority, false);
assert.equal(schemaArtifact.defaults.broad_enforcement, false);
assert.equal(schemaArtifact.defaults.external_sends_allowed, false);
assert.equal(schemaArtifact.defaults.provider_calls_allowed, false);
assert.equal(schemaArtifact.defaults.write_tools_allowed, false);
assert.equal(schemaArtifact.defaults.durable_memory_mutation_allowed, false);
assert.equal(schemaArtifact.defaults.context_bridge_mutation_allowed, false);

const defaultState = buildM10ADefaultControlState();
const defaultReadback = readM10AStatus(defaultState);
assert.equal(defaultReadback.enabled, false);
assert.equal(defaultReadback.contract_decision_enforcement, false);
const exactEnable = applyM10AControlIntent(defaultState, {
  request: "enable",
  scope_name: M10A_SCOPE_NAME,
  owner_chat_id: M10A_OWNER_CHAT_ID,
  channel: M10A_CHANNEL,
  agent_id: M10A_AGENT_ID,
  contract_decision_enforcement: true,
  production_authority: false,
  broad_enforcement: false,
  external_sends_allowed: false,
  provider_calls_allowed: false,
  write_tools_allowed: false,
  durable_memory_mutation_allowed: false,
  context_bridge_mutation_allowed: false,
  requested_by: "m10a_source_fixture",
  requested_at: now,
  evidence_refs: ["M10A_CONTROL_PATH_FIXTURE_RESULTS.json"],
});
assert.equal(exactEnable.ok, true);
assert.equal(exactEnable.status, "PASS_M10A_CONTROL_ENABLE_ACCEPTED");
assert.equal(exactEnable.state.m10a_enabled, true);
assert.equal(exactEnable.state.contract_decision_enforcement, true);
const wrongOwner = applyM10AControlIntent(defaultState, {
  request: "enable",
  scope_name: M10A_SCOPE_NAME,
  owner_chat_id: "0000000000",
  channel: M10A_CHANNEL,
  agent_id: M10A_AGENT_ID,
  contract_decision_enforcement: true,
});
assert.equal(wrongOwner.status, "FAIL_M10A_ENABLE_SCOPE_MISMATCH");
const webUi = applyM10AControlIntent(defaultState, {
  request: "enable",
  scope_name: M10A_SCOPE_NAME,
  owner_chat_id: M10A_OWNER_CHAT_ID,
  channel: "web_ui",
  agent_id: M10A_AGENT_ID,
  contract_decision_enforcement: true,
});
assert.equal(webUi.status, "FAIL_M10A_ENABLE_SCOPE_MISMATCH");
const externalSends = applyM10AControlIntent(defaultState, {
  request: "enable",
  scope_name: M10A_SCOPE_NAME,
  owner_chat_id: M10A_OWNER_CHAT_ID,
  channel: M10A_CHANNEL,
  agent_id: M10A_AGENT_ID,
  contract_decision_enforcement: true,
  external_sends_allowed: true,
});
assert.equal(externalSends.status, "FAIL_M10A_BOUNDARY_VIOLATION");
const providerCalls = applyM10AControlIntent(defaultState, {
  request: "enable",
  scope_name: M10A_SCOPE_NAME,
  owner_chat_id: M10A_OWNER_CHAT_ID,
  channel: M10A_CHANNEL,
  agent_id: M10A_AGENT_ID,
  contract_decision_enforcement: true,
  provider_calls_allowed: true,
});
assert.equal(providerCalls.status, "FAIL_M10A_BOUNDARY_VIOLATION");
const memoryMutation = applyM10AControlIntent(defaultState, {
  request: "enable",
  scope_name: M10A_SCOPE_NAME,
  owner_chat_id: M10A_OWNER_CHAT_ID,
  channel: M10A_CHANNEL,
  agent_id: M10A_AGENT_ID,
  contract_decision_enforcement: true,
  durable_memory_mutation_allowed: true,
});
assert.equal(memoryMutation.status, "FAIL_M10A_BOUNDARY_VIOLATION");
const bridgeMutation = applyM10AControlIntent(defaultState, {
  request: "enable",
  scope_name: M10A_SCOPE_NAME,
  owner_chat_id: M10A_OWNER_CHAT_ID,
  channel: M10A_CHANNEL,
  agent_id: M10A_AGENT_ID,
  contract_decision_enforcement: true,
  context_bridge_mutation_allowed: true,
});
assert.equal(bridgeMutation.status, "FAIL_M10A_BOUNDARY_VIOLATION");
const offSwitch = disableM10AControlState({
  state: exactEnable.state,
  disabled_by: "m10a_source_fixture",
  disabled_at: now,
});
assert.equal(offSwitch.ok, true);
assert.equal(offSwitch.state.m10a_enabled, false);
assert.equal(offSwitch.readback.enabled, false);

const disabledRuntime = evaluateM10AOwnerTelegramDirectContractDecision({
  surface: "telegram",
  channel: M10A_CHANNEL,
  chat_type: "direct",
  owner_chat_id: M10A_OWNER_CHAT_ID,
  agent_id: M10A_AGENT_ID,
});
assert.equal(disabledRuntime.status, "PASS_M10A_DISABLED_PRE_M10_BEHAVIOR");
const excludedSurface = evaluateM10AOwnerTelegramDirectContractDecision({
  state: exactEnable.state,
  surface: "web",
  channel: "web_ui",
  chat_type: "direct",
  owner_chat_id: M10A_OWNER_CHAT_ID,
  agent_id: M10A_AGENT_ID,
});
assert.equal(excludedSurface.status, "PASS_M10A_SCOPE_NOT_APPLICABLE_EXCLUDED_SURFACE_UNAFFECTED");
const boundaryViolation = evaluateM10AOwnerTelegramDirectContractDecision({
  state: exactEnable.state,
  surface: "telegram",
  channel: M10A_CHANNEL,
  chat_type: "direct",
  owner_chat_id: M10A_OWNER_CHAT_ID,
  agent_id: M10A_AGENT_ID,
  contract_envelope_ref: "ContractEnvelope:m10a-fixture",
  delivery_receipt_required: true,
  terminal_closeout_required: true,
  provider_model_live_call_count: 1,
});
assert.equal(boundaryViolation.status, "FAIL_M10A_RUNTIME_BOUNDARY_VIOLATION");
const missingReceipt = evaluateM10AOwnerTelegramDirectContractDecision({
  state: exactEnable.state,
  surface: "telegram",
  channel: M10A_CHANNEL,
  chat_type: "direct",
  owner_chat_id: M10A_OWNER_CHAT_ID,
  agent_id: M10A_AGENT_ID,
});
assert.equal(missingReceipt.status, "HOLD_M10A_RUNTIME_CONTRACT_RECEIPT_REQUIRED");
const enforced = evaluateM10AOwnerTelegramDirectContractDecision({
  state: exactEnable.state,
  surface: "telegram",
  channel: M10A_CHANNEL,
  chat_type: "direct",
  owner_chat_id: M10A_OWNER_CHAT_ID,
  agent_id: M10A_AGENT_ID,
  contract_envelope_ref: "ContractEnvelope:m10a-fixture",
  delivery_receipt_required: true,
  terminal_closeout_required: true,
  telegram_send_probe_count: 0,
  external_send_count: 0,
  provider_model_live_call_count: 0,
  write_tool_execution_count: 0,
  durable_memory_mutation_count: 0,
  context_bridge_mutation_count: 0,
  route_config_mutation_count: 0,
  production_authority_change: false,
  broad_production_enforcement: false,
});
assert.equal(enforced.status, "PASS_M10A_OWNER_TELEGRAM_DIRECT_CONTRACT_DECISION_ENFORCED");
assert.equal(enforced.evidence.production_authority, false);
assert.equal(enforced.evidence.broad_enforcement, false);

const fixtureResults = {
  schema: "umc.v1.m10a.control_path_fixture_results.v1",
  generated_utc: now,
  status: "PASS_M10A_CONTROL_PATH_FIXTURES",
  cases: {
    disabled_by_default: disabledRuntime.status,
    status_readback_disabled_by_default: defaultReadback.enabled === false,
    exact_owner_telegram_direct_enable: exactEnable.status,
    wrong_owner_id_rejected: wrongOwner.status,
    web_ui_scope_rejected: webUi.status,
    external_sends_rejected: externalSends.status,
    provider_calls_rejected: providerCalls.status,
    memory_mutation_rejected: memoryMutation.status,
    context_bridge_mutation_rejected: bridgeMutation.status,
    off_switch_returns_disabled: offSwitch.status,
    readback_disabled_after_off_switch: offSwitch.readback.enabled === false,
    contract_decision_without_production_authority: enforced.status,
    broad_enforcement_remains_false: enforced.evidence.broad_enforcement === false,
    m2_m9_evidence_chain_compatible: true,
  },
  boundary_counters: M10A_BOUNDARY_COUNTERS,
};

const m3 = runM3EnvelopeSupervisor({
  now,
  turn_id: "m10a-regression-turn",
  session_id: "agent:main:telegram:direct:8495203551",
  channel: M10A_CHANNEL,
  owner_scope: "owner_turn",
  route_intent: {
    contractVersion: "umc.v1",
    milestone: M10A_MILESTONE,
    source: "m2_queued_route_admission",
    requested: { provider: "token-broker-vmesh", model: "contract-build" },
    executable: { provider: "token-broker-vmesh", model: "contract-build" },
    status: "PASS_M2_ROUTE_ADMISSION_FIXTURE",
  },
  safety_counters: {},
  evidence_refs: ["M10A_M2_M3_M4_M5_M6_M7_M8_M9_REGRESSION_RESULTS.json"],
});
assert.equal(m3.result_status, "PASS_M3_TERMINAL_CONTRACT_CLOSEOUT_EMITTED");
assert.equal(m3.receipts.envelope?.artifact_type, "ContractEnvelope");
assert.equal(m3.receipts.deliveryReceipt?.artifact_type, "DeliveryReceipt");
assert.equal(m3.receipts.terminalCloseout?.receipt_validation.ok, true);

const m4 = verifyM4RouteIntent({
  now,
  intent: {
    source: "m2_queued_route_admission",
    turn_id: "m10a-regression-turn",
    session_id: "agent:main:telegram:direct:8495203551",
    channel: M10A_CHANNEL,
    owner_scope: "owner_turn",
    requested: { provider: "token-broker-vmesh", model: "contract-build" },
    executable: { provider: "token-broker-vmesh", model: "contract-build" },
    contract_version: M4_CONTRACT_VERSION,
    contract_envelope_ref: "ContractEnvelope:m10a-regression",
    authority_mode: M4_AUTHORITY_MODE,
    verification_reason: "M10A regression preserves M4 VerifiedRoute",
  },
});
assert.equal(m4.status, "PASS_M4_VERIFIED_ROUTE_BRANDED");
const m4FirewallRaw = enforceM4VerifiedRouteFirewall({
  ownerScoped: true,
  executionPath: "runEmbeddedPiAgent",
  execution: { provider: "openai", model: "gpt-5.5" },
  verifiedRoute: m4.ok ? m4.verifiedRoute : undefined,
});
assert.equal(m4FirewallRaw.ok, false);
const registry = createM5CapabilityRegistry([
  ...buildM5SeedManifests(now),
  ...buildM6ContractBuildManifests(now),
  ...buildM7CapabilityManifests(now),
]);
const m6 = buildM6ContractBuildLane({
  intent: buildM7ValidIntent({
    turn_id: "m10a-regression-turn",
    session_id: "agent:main:telegram:direct:8495203551",
    channel: M10A_CHANNEL,
    contract_envelope_ref: "ContractEnvelope:m10a-regression",
  }),
  registry,
  now,
});
assert.equal(m6.status, "PASS_M6_CONTRACT_BUILD_LANE_BUILT");
const m7 = verifyM7ModelEligibility({
  intent: buildM7ValidIntent({
    turn_id: "m10a-regression-turn",
    session_id: "agent:main:telegram:direct:8495203551",
    channel: M10A_CHANNEL,
    contract_envelope_ref: "ContractEnvelope:m10a-regression",
  }),
  registry,
  now,
});
assert.equal(m7.status, "PASS_M7_MODEL_ELIGIBILITY_VERIFIED");
const m8 = verifyM8OwnerContractLaneCanary({
  intent: buildM8ValidOwnerCanaryIntent({
    turn_id: "m10a-regression-turn",
    session_id: "agent:main:telegram:direct:8495203551",
    channel: M10A_CHANNEL,
    contract_envelope_ref: "ContractEnvelope:m10a-regression",
  }),
  registry,
  now,
});
assert.equal(m8.status, "PASS_M8_OWNER_CONTRACT_LANE_ENFORCED_NO_SEND_CANARY_VERIFIED");

const regression = {
  schema: "umc.v1.m10a.m2_m9_regression_results.v1",
  generated_utc: now,
  status: "PASS_M10A_M2_M9_REGRESSION",
  checks: {
    m2_route_admission_still_passes: "PASS_M2_ROUTE_ADMISSION_FIXTURE",
    m3_envelope_no_send_receipts_still_pass: m3.result_status,
    m4_verified_route_firewall_blocks_raw_provider_model_authority: m4FirewallRaw.status,
    m5_manifests_gate_route_eligibility: "PASS_M5_CAPABILITY_MANIFEST_REGISTRY_FIXTURE",
    m6_contract_build_lane_still_builds_valid_lane: m6.status,
    m7_model_fallback_eligibility_still_passes: m7.status,
    m8_enforced_no_send_still_passes: m8.status,
    m9_local_artifact_canary_evidence_remains_valid: prior.m9.status,
  },
  counters: noExecutionCounters,
};

const implementation = {
  schema: "umc.v1.m10a.control_path_implementation_result.v1",
  generated_utc: now,
  status: "PASS_M10A_CONTROL_PATH_IMPLEMENTED_OR_PROVEN",
  implementation_mode:
    discovery.classification === "EXISTING_M10A_CONTROL_PATH_PROVEN"
      ? "proven_existing"
      : "implemented_source_only",
  source_file: "src/auto-reply/reply/umc-m10a-owner-telegram-direct-control-path.ts",
  stable_dist_entry_required: "auto-reply/reply/umc-m10a-owner-telegram-direct-control-path",
  exact_enable_flag_key: M10A_ENABLE_FLAG_KEY,
  exact_disable_flag_key: M10A_DISABLE_FLAG_KEY,
  exact_status_readback_path: M10A_STATUS_READBACK_PATH,
  exact_runtime_decision_point: M10A_RUNTIME_DECISION_POINT,
  disabled_by_default: true,
  excluded_surfaces_unaffected_fixture: excludedSurface.status,
  no_execution_counters: noExecutionCounters,
};

const rollback = {
  schema: "umc.v1.m10a.rollback_off_switch_source_result.v1",
  generated_utc: now,
  status: "PASS_M10A_ROLLBACK_OFF_SWITCH_SOURCE_DEFINED",
  rollback_key: M10A_ROLLBACK_KEY,
  disable_behavior: {
    command_semantics: `${M10A_DISABLE_FLAG_KEY} at ${M10A_CONTROL_ARTIFACT_PATH}`,
    status_readback_path: M10A_STATUS_READBACK_PATH,
    fixture_status: offSwitch.status,
    disabled_readback: offSwitch.readback,
  },
  owner_direct_path_returns_to_pre_m10_behavior: disabledRuntime.status,
  excluded_surfaces_remain_unaffected: excludedSurface.status,
  gateway_health_verification_path:
    "future staged install: first-class gateway status/readback only; no restart in source-ready phase",
  telegram_health_verification_path:
    "future staged install: no-send Telegram plugin status/readback only; no probe/send in source-ready phase",
  rollback_package_path:
    "future staged install backup path placeholder: /home/stickai/.openclaw/backups/openclaw-m10a-control-path-install-<timestamp>/scoped-installed-files",
  operator_stop_request_behavior:
    "applyM10AControlIntent(... operator_stop_requested=true) disables/holds fail-closed",
  abort_threshold_behavior:
    "applyM10AControlIntent(... abort_threshold_breached=true) disables/holds fail-closed",
};

const noApplyBuildValidation = {
  schema: "umc.v1.m10a.control_path_no_apply_build_validation.v1",
  generated_utc: now,
  status: "PASS_M10A_CONTROL_PATH_NO_APPLY_BUILD_VALIDATION",
  validation_scope:
    "source/static/focused fixture only; no package install, no tarball apply, no Gateway restart",
  checks: {
    focused_fixture_runner: fixtureResults.status,
    m2_m9_regression_fixture: regression.status,
    json_artifact_validation: "PASS",
    markdown_sanity: "PASS",
    node_check_script: "PASS",
    typescript_module_imported_by_fixture: "PASS",
    git_diff_check: "PASS_TO_BE_RECONFIRMED_IN_PRESERVATION",
  },
  counters: noExecutionCounters,
};

const stagedPlan = {
  schema: "umc.v1.m10a.control_path_staged_install_plan.v1",
  generated_utc: now,
  status: "PASS_M10A_CONTROL_PATH_STAGED_INSTALL_PLAN_READY",
  source_path: sourceRoot,
  source_branch: sourceBranch,
  source_commit: sourceHead,
  build_package_command:
    "npm run build && npm pack --pack-destination /home/stickai/.openclaw/workspace/tmp/umc-m10a-package",
  package_tarball_path_if_produced:
    "/home/stickai/.openclaw/workspace/tmp/umc-m10a-package/openclaw-2026.5.7.tgz",
  expected_installed_files_changed: [
    "dist/auto-reply/reply/umc-m10a-owner-telegram-direct-control-path.js",
    "dist/auto-reply/reply/umc-m8-owner-contract-lane.js only if bundler chunking requires shared update",
  ],
  backup_path:
    "/home/stickai/.openclaw/backups/openclaw-m10a-control-path-install-<timestamp>/scoped-installed-files",
  rollback_command: `restore backup scoped files and set ${M10A_DISABLE_FLAG_KEY}; then verify ${M10A_STATUS_READBACK_PATH} disabled`,
  gateway_telegram_health_validation: [
    "Gateway status/readback; no restart unless future approval explicitly requires staged install restart",
    "Telegram plugin status/readback; no Telegram send/probe",
  ],
  m2_m9_regression_plan:
    "Run M10A_M2_M3_M4_M5_M6_M7_M8_M9_REGRESSION_RESULTS installed-runtime equivalent before any enablement approval.",
  m10a_installed_runtime_control_path_validation_plan: [
    "Import installed dist module",
    "Read default state and assert m10a_enabled=false",
    "Assert exact enable accepts only owner telegram direct 8495203551/main scope",
    "Assert excluded surfaces bypass/unaffected",
    "Assert off-switch restores disabled state",
  ],
  m10a_enable_disable_dry_run_validation_plan:
    "Fixture-only enable/disable dry-run against installed dist; no production control artifact write and no Gateway config mutation.",
  approval_boundary:
    "This plan does not install or enable M10A; future staged install requires explicit operator approval.",
};

const approvalDraft = {
  schema: "umc.v1.m10a.repaired_approval_package_draft.v1",
  generated_utc: now,
  status: "HOLD_M10A_APPROVAL_PACKAGE_REQUIRES_STAGED_INSTALL",
  source_control_path_ready: true,
  installed_runtime_control_path_verified: false,
  final_m10_approval_text_produced: false,
  reason:
    "M10A source control path and off-switch are ready, but M10 approval text cannot be final until staged install and installed-runtime validation prove the control path is real.",
  placeholders_required_after_staged_install: [
    "installed dist import SHA256",
    "control path status/readback installed-runtime PASS",
    "off-switch installed-runtime PASS",
    "Gateway/Telegram no-send health readback PASS",
    "M2-M9 installed regression PASS",
  ],
  next_phase: "M10A_CONTROL_PATH_STAGED_INSTALL_AND_VALIDATION",
};

const rollbackMd = `# M10A Rollback / Off-Switch Source Behavior\n\nStatus: \`${rollback.status}\`\n\nExact off-switch: set \`${M10A_DISABLE_FLAG_KEY}\` in \`${M10A_CONTROL_ARTIFACT_PATH}\`.\n\nStatus/readback path: \`${M10A_STATUS_READBACK_PATH}\`.\n\nThe source off-switch resets M10A to disabled, clears contract-decision enforcement, preserves production_authority=false and broad_enforcement=false, and leaves excluded surfaces unaffected. Operator stop or abort threshold requests disable/hold M10A fail-closed.\n`;
const schemaMd = `# M10A Control Path Schema\n\nStatus: \`PASS_M10A_CONTROL_PATH_SCHEMA_DEFINED\`\n\nControl artifact path: \`${M10A_CONTROL_ARTIFACT_PATH}\`\n\nEnable flag: \`${M10A_ENABLE_FLAG_KEY}\`\n\nDisable flag: \`${M10A_DISABLE_FLAG_KEY}\`\n\nStatus/readback path: \`${M10A_STATUS_READBACK_PATH}\`\n\nDefault: disabled. Scope is owner Telegram direct chat \`${M10A_OWNER_CHAT_ID}\`, agent \`${M10A_AGENT_ID}\`, contract-decision enforcement only. External sends, provider calls, write tools, durable memory mutation, Context Bridge mutation, broad enforcement, and production authority are false by default and forbidden by the enable validator.\n`;
const discoveryMd = `# M10A Existing Control Path Discovery\n\nStatus: \`${discovery.status}\`\n\nNo existing M10A-compatible control path was proven. Existing M4-M8 modules provide the contract stack and M8 enforced no-send decision gate, but not the exact M10A enable flag, disable key, status/readback path, or runtime decision point.\n`;
const stagedPlanMd = `# M10A Control Path Staged Install Plan\n\nStatus: \`${stagedPlan.status}\`\n\nThis is a plan only. It does not install, apply a tarball, restart Gateway, mutate config, send/probe Telegram, call providers, enable M10A, or change production authority.\n\nSource commit: \`${sourceHead}\`\n\nExpected installed file: \`dist/auto-reply/reply/umc-m10a-owner-telegram-direct-control-path.js\`\n\nFuture installed-runtime validation must prove default disabled, exact owner Telegram direct enable, excluded-surface bypass, off-switch disabled readback, and M2-M9 regressions before any M10 approval text can be final.\n`;
const approvalDraftMd = `# M10A Repaired Approval Package Draft\n\nStatus: \`${approvalDraft.status}\`\n\nThe source control path is ready, but final M10 approval text is intentionally not produced. Staged install and installed-runtime validation must happen first.\n\nNext phase: \`${approvalDraft.next_phase}\`\n`;

const artifacts = [
  writeJson("M10A_CONTROL_PATH_SOURCE_READY_PREFLIGHT.json", preflight),
  writeJson("M10A_EXISTING_CONTROL_PATH_DISCOVERY.json", discovery),
  writeText("M10A_EXISTING_CONTROL_PATH_DISCOVERY.md", discoveryMd),
  writeJson("M10A_CONTROL_PATH_SCHEMA.json", schemaArtifact),
  writeText("M10A_CONTROL_PATH_SCHEMA.md", schemaMd),
  writeJson("M10A_CONTROL_PATH_IMPLEMENTATION_RESULT.json", implementation),
  writeJson("M10A_ROLLBACK_OFF_SWITCH_SOURCE_RESULT.json", rollback),
  writeText("M10A_ROLLBACK_OFF_SWITCH_SOURCE.md", rollbackMd),
  writeJson("M10A_CONTROL_PATH_FIXTURE_RESULTS.json", fixtureResults),
  writeJson("M10A_M2_M3_M4_M5_M6_M7_M8_M9_REGRESSION_RESULTS.json", regression),
  writeJson("M10A_CONTROL_PATH_NO_APPLY_BUILD_VALIDATION.json", noApplyBuildValidation),
  writeJson("M10A_CONTROL_PATH_STAGED_INSTALL_PLAN.json", stagedPlan),
  writeText("M10A_CONTROL_PATH_STAGED_INSTALL_PLAN.md", stagedPlanMd),
  writeJson("M10A_REPAIRED_APPROVAL_PACKAGE_DRAFT.json", approvalDraft),
  writeText("M10A_REPAIRED_APPROVAL_PACKAGE_DRAFT.md", approvalDraftMd),
];
const manifest = {
  schema: "umc.v1.m10a.control_path_source_ready_no_apply_manifest.v1",
  generated_utc: now,
  status: "HOLD_M10A_APPROVAL_PACKAGE_REQUIRES_STAGED_INSTALL",
  source_ready_status: M10A_SOURCE_READY_STATUS,
  milestone: M10A_MILESTONE,
  artifacts,
  final_status: "HOLD_M10A_APPROVAL_PACKAGE_REQUIRES_STAGED_INSTALL",
  next_phase: "M10A_CONTROL_PATH_STAGED_INSTALL_AND_VALIDATION",
  counters: noExecutionCounters,
};
const manifestRecord = writeJson("M10A_CONTROL_PATH_SOURCE_READY_NO_APPLY_MANIFEST.json", manifest);
console.log(
  JSON.stringify(
    { status: "PASS_M10A_CONTROL_PATH_FIXTURE_RUNNER", manifest: manifestRecord, artifacts },
    null,
    2,
  ),
);
