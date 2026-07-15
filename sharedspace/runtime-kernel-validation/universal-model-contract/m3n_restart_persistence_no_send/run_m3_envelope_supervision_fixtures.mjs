#!/usr/bin/env node
import { writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import {
  DELIVERY_MODE,
  PRODUCTION_PATH,
  REQUIRED_ZERO_COUNTERS,
  runM3EnvelopeSupervisor,
  validateRequiredReceipts,
  buildTerminalContractCloseout
} from "./umc_m3_envelope_supervision.mjs";

const NOW = "2026-07-15T15:33:00Z";
const OUT_JSON = "M3_ENVELOPE_SUPERVISION_FIXTURE_RESULTS.json";
const OUT_JSONL = "M3_ENVELOPE_SUPERVISION_FIXTURE_RECEIPTS.jsonl";

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function assertCase(condition, message) {
  if (!condition) throw new Error(message);
}

function zeroForbiddenCounters(counters) {
  return REQUIRED_ZERO_COUNTERS.every((key) => Number(counters?.[key] || 0) === 0);
}

const baseRouteIntent = {
  contractVersion: "umc.v1",
  source: "m2_route_admission",
  selected_model_before_admission: "ollama/deepseek-v4-pro:cloud",
  forced_model_after_admission: "openai-codex/gpt-5.5",
  terms: [
    "resolveUmcV1DefaultRouteFromConfig",
    "isUmcV1QueuedOwnerScope",
    "applyUmcV1QueuedRouteAdmission",
    "umcV1QueuedRouteIntent"
  ]
};

const eligibleInput = {
  now: NOW,
  turn_id: "telegram:8495203551:fixture-m3-owner-turn",
  session_id: "agent:main:telegram:direct:8495203551",
  channel: "telegram",
  owner_scope: "owner_turn",
  route_intent: baseRouteIntent,
  tool_proposals: [
    { name: "message.send", kind: "write", mutates: true },
    { name: "memory_search", kind: "read", mutates: false }
  ],
  ambient_owner_chat_delivery_count: 1,
  evidence_refs: [
    "M3_ENVELOPE_TOOLS_DELIVERY_SUPERVISION_HANDOFF.md",
    "M3_ENVELOPE_TOOLS_DELIVERY_SUPERVISION_PLAN.json"
  ]
};

const cases = [];
const receiptLines = [];

function record(name, result, checks) {
  const pass = Object.values(checks).every(Boolean);
  const row = {
    name,
    status: pass ? "PASS" : "FAIL",
    result_status: result.result_status,
    checks
  };
  cases.push(row);
  if (result.receipts) {
    for (const [key, receipt] of Object.entries(result.receipts)) {
      receiptLines.push(JSON.stringify({ case: name, key, receipt }));
    }
  }
  if (!pass) throw new Error(`${name} failed: ${JSON.stringify(checks)}`);
}

const eligible = runM3EnvelopeSupervisor(eligibleInput);
record("eligible_owner_turn_emits_all_m3_receipts_no_send", eligible, {
  supervisor_active: eligible.supervisor_active === true,
  emits_contract_envelope: eligible.receipts.envelope?.artifact_type === "ContractEnvelope",
  emits_shadow_observation_receipt: eligible.receipts.shadowObservationReceipt?.artifact_type === "ShadowObservationReceipt",
  emits_tool_supervision_receipt: eligible.receipts.toolSupervisionReceipt?.artifact_type === "ToolSupervisionReceipt",
  emits_delivery_receipt_no_send: eligible.receipts.deliveryReceipt?.artifact_type === "DeliveryReceipt" && eligible.receipts.deliveryReceipt.mode === DELIVERY_MODE,
  emits_universal_contract_receipt: eligible.receipts.universalContractReceipt?.artifact_type === "UniversalContractReceipt",
  emits_terminal_closeout: eligible.receipts.terminalCloseout?.artifact_type === "TerminalContractCloseout",
  terminal_status_pass: eligible.result_status === "PASS_M3_TERMINAL_CONTRACT_CLOSEOUT_EMITTED",
  production_response_path_unchanged: eligible.production_path === PRODUCTION_PATH,
  ambient_owner_chat_delivery_classified_separately: eligible.ambient_delivery_classification === "AMBIENT_OWNER_CHAT_DELIVERY_SEPARATE_FROM_SHADOW_NO_SEND",
  shadow_telegram_send_count_zero: eligible.safety_counters.shadow_telegram_send_count === 0,
  shadow_external_send_count_zero: eligible.safety_counters.shadow_external_send_count === 0,
  shadow_provider_model_live_call_count_zero: eligible.safety_counters.shadow_provider_model_live_call_count === 0,
  shadow_real_write_tool_count_zero: eligible.safety_counters.shadow_real_write_tool_count === 0,
  shadow_durable_memory_mutation_count_zero: eligible.safety_counters.shadow_durable_memory_mutation_count === 0,
  shadow_context_bridge_mutation_count_zero: eligible.safety_counters.shadow_context_bridge_mutation_count === 0,
  shadow_route_config_mutation_count_zero: eligible.safety_counters.shadow_route_config_mutation_count === 0,
  production_authority_change_count_zero: eligible.safety_counters.production_authority_change_count === 0,
  all_forbidden_counters_zero: zeroForbiddenCounters(eligible.safety_counters),
  write_tool_proposal_not_executed: eligible.receipts.toolSupervisionReceipt.proposals.some((p) => p.name === "message.send" && p.executed === false && p.disposition === "blocked_observe_only_no_real_write")
});

const nonOwner = runM3EnvelopeSupervisor({
  ...eligibleInput,
  turn_id: "fixture-non-owner",
  owner_scope: "group_turn"
});
record("non_owner_or_ungated_turn_does_not_activate", nonOwner, {
  supervisor_inactive: nonOwner.supervisor_active === false,
  skip_status: nonOwner.result_status === "SKIP_M3_SUPERVISOR_NOT_OWNER_OR_UNGATED",
  no_receipts_emitted: Object.keys(nonOwner.receipts || {}).length === 0,
  production_response_path_unchanged: nonOwner.production_path === PRODUCTION_PATH,
  all_forbidden_counters_zero: zeroForbiddenCounters(nonOwner.safety_counters)
});

const missingRouteIntent = runM3EnvelopeSupervisor({
  ...eligibleInput,
  turn_id: "fixture-missing-route-intent",
  route_intent: null
});
record("missing_route_intent_produces_typed_hold_not_pass", missingRouteIntent, {
  supervisor_active: missingRouteIntent.supervisor_active === true,
  hold_status: missingRouteIntent.result_status === "HOLD_M3_ROUTE_INTENT_MISSING",
  not_pass: !String(missingRouteIntent.result_status).startsWith("PASS"),
  terminal_closeout_emitted: missingRouteIntent.receipts.terminalCloseout?.artifact_type === "TerminalContractCloseout",
  production_response_path_unchanged: missingRouteIntent.production_path === PRODUCTION_PATH,
  all_forbidden_counters_zero: zeroForbiddenCounters(missingRouteIntent.safety_counters)
});

const missingReceiptParts = { ...eligible.receipts };
delete missingReceiptParts.deliveryReceipt;
const validation = validateRequiredReceipts(missingReceiptParts);
const missingReceiptCloseout = buildTerminalContractCloseout(missingReceiptParts);
record("missing_required_receipt_produces_fail_not_pass", { result_status: missingReceiptCloseout.result_status, receipts: { terminalCloseout: missingReceiptCloseout }, safety_counters: eligible.safety_counters, production_path: PRODUCTION_PATH }, {
  validation_failed: validation.ok === false,
  delivery_receipt_missing_detected: validation.missing.includes("deliveryReceipt"),
  fail_status: missingReceiptCloseout.result_status === "FAIL_M3_REQUIRED_RECEIPT_MISSING",
  not_pass: !String(missingReceiptCloseout.result_status).startsWith("PASS"),
  all_forbidden_counters_zero: zeroForbiddenCounters(eligible.safety_counters)
});

const nonZeroCounter = runM3EnvelopeSupervisor({
  ...eligibleInput,
  turn_id: "fixture-nonzero-forbidden-counter",
  safety_counters: { shadow_telegram_send_count: 1 }
});
record("nonzero_forbidden_counter_fails_terminal_closeout", nonZeroCounter, {
  supervisor_active: nonZeroCounter.supervisor_active === true,
  fail_status: nonZeroCounter.result_status === "FAIL_M3_SAFETY_COUNTER_NONZERO",
  not_pass: !String(nonZeroCounter.result_status).startsWith("PASS"),
  shadow_telegram_send_counter_detected: nonZeroCounter.safety_counters.shadow_telegram_send_count === 1,
  production_response_path_unchanged: nonZeroCounter.production_path === PRODUCTION_PATH
});

const summaryChecks = {
  eligible_owner_turn_emits_contract_envelope: true,
  eligible_owner_turn_emits_shadow_observation_receipt: true,
  eligible_owner_turn_emits_delivery_receipt_mode_no_send: true,
  eligible_owner_turn_emits_universal_contract_receipt: true,
  eligible_owner_turn_emits_terminal_closeout: true,
  production_response_path_unchanged: true,
  ambient_owner_chat_delivery_classified_separately: true,
  shadow_telegram_send_count: 0,
  shadow_external_send_count: 0,
  shadow_provider_model_live_call_count: 0,
  shadow_real_write_tool_count: 0,
  shadow_durable_memory_mutation_count: 0,
  shadow_context_bridge_mutation_count: 0,
  shadow_route_config_mutation_count: 0,
  production_authority_change_count: 0,
  non_owner_or_ungated_turn_does_not_activate: true,
  missing_route_intent_typed_hold_not_pass: true,
  missing_required_receipt_fail_not_pass: true,
  nonzero_forbidden_counter_fail_not_pass: true
};

const result = {
  schema: "umc.v1.m3.envelope_supervision_fixture_results.v1",
  generated_utc: NOW,
  status: "PASS_M3_ENVELOPE_SUPERVISION_FIXTURES",
  source_files: [
    "umc_m3_envelope_supervision.mjs",
    "run_m3_envelope_supervision_fixtures.mjs"
  ],
  cases,
  summary_checks: summaryChecks,
  receipt_jsonl_path: OUT_JSONL,
  receipt_jsonl_sha256: sha256(receiptLines.join("\n") + "\n"),
  hard_boundaries_observed: {
    installed_runtime_mutation_count: 0,
    telegram_send_probe_count: 0,
    external_send_count: 0,
    provider_model_shadow_call_count: 0,
    real_write_tool_execution_count: 0,
    durable_memory_mutation_count: 0,
    context_bridge_mutation_count: 0,
    route_config_mutation_count: 0,
    production_authority_change_count: 0,
    m3o_rerun_count: 0,
    m3p_started: false,
    m4_started: false,
    enforcement_started: false
  }
};

writeFileSync(OUT_JSONL, receiptLines.join("\n") + "\n", "utf8");
writeFileSync(OUT_JSON, JSON.stringify(result, null, 2) + "\n", "utf8");
console.log("PASS_M3_ENVELOPE_SUPERVISION_FIXTURES");
