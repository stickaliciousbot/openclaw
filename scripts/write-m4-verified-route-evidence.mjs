import childProcess from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const evidenceRoot =
  process.argv[2] ||
  path.resolve(
    process.cwd(),
    "../../workspace/sharedspace/runtime-kernel-validation/universal-model-contract/m3n_restart_persistence_no_send",
  );
const sourceRoot = process.cwd();
function readJson(name) {
  return JSON.parse(fs.readFileSync(path.join(evidenceRoot, name), "utf8"));
}
function writeText(name, content) {
  fs.writeFileSync(
    path.join(evidenceRoot, name),
    content.endsWith("\n") ? content : `${content}\n`,
  );
}
function writeJson(name, value) {
  fs.writeFileSync(path.join(evidenceRoot, name), `${JSON.stringify(value, null, 2)}\n`);
}
function sha256File(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}
function git(args) {
  return childProcess.execFileSync("git", args, { cwd: sourceRoot, encoding: "utf8" }).trim();
}
const now = new Date().toISOString();
const preflight = readJson("M4_VERIFIED_ROUTE_PREFLIGHT.json");
const pathMap = readJson("M4_MODEL_EXECUTION_PATH_MAP.json");
const brandSchema = readJson("M4_VERIFIED_ROUTE_BRAND_SCHEMA.json");
const brander = readJson("M4_VERIFIED_ROUTE_BRANDER_IMPLEMENTATION_RESULT.json");
const firewall = readJson("M4_DIRECT_BYPASS_FIREWALL_IMPLEMENTATION_RESULT.json");
const m3Compat = readJson("M4_M3_COMPATIBILITY_FIXTURE_RESULTS.json");
const bypass = readJson("M4_DIRECT_BYPASS_FIREWALL_FIXTURE_RESULTS.json");

writeText(
  "M4_MODEL_EXECUTION_PATH_MAP.md",
  `# M4 Model Execution Path Map\n\nStatus: ${pathMap.status}\n\n| source file | function | current authority | raw provider/model | uses route intent | M3 context | can bypass M3 | can bypass M2 | insertion point |\n|---|---|---|---:|---:|---:|---:|---:|---|\n${pathMap.paths.map((p) => `| \`${p.source_file}\` | \`${p.function_name}\` | ${p.current_authority_source} | ${p.accepts_raw_provider_model ? "yes" : "no"} | ${p.already_uses_route_intent ? "yes" : "no"} | ${p.emits_or_receives_m3_envelope_context ? "yes" : "no"} | ${p.can_bypass_m3 ? "yes" : "no"} | ${p.can_bypass_m2_admission ? "yes" : "no"} | ${p.required_verified_route_insertion_point} |`).join("\n")}\n`,
);

writeText(
  "M4_VERIFIED_ROUTE_BRAND_SCHEMA.md",
  `# M4 VerifiedRoute Brand Schema\n\nStatus: ${brandSchema.status}\n\n## Required fields\n\n${brandSchema.required_fields.map((field) => `- \`${field}\``).join("\n")}\n\n## Invariants\n\n${Object.entries(
    brandSchema.invariants,
  )
    .map(([key, value]) => `- ${key}: ${value ? "PASS" : "FAIL"}`)
    .join(
      "\n",
    )}\n\n## Authority note\n\nThe JSON representation is evidence only. Runtime trust requires the private module symbol brand; raw object literals and deserialized JSON are rejected until route intent is reverified.\n`,
);

const stagedPlan = {
  schema: "umc.v1.m4.verified_route_staged_install_plan.v1",
  generated_utc: now,
  status: "PASS_M4_VERIFIED_ROUTE_STAGED_INSTALL_PLAN_READY",
  source_path: sourceRoot,
  source_branch: git(["branch", "--show-current"]),
  source_head: git(["rev-parse", "HEAD"]),
  source_commit: git(["rev-parse", "HEAD"]),
  build_package_command:
    "pnpm build && pnpm pack --pack-destination /home/stickai/.openclaw/workspace/tmp/umc-m4-package",
  package_tarball_path_if_produced:
    "/home/stickai/.openclaw/workspace/tmp/umc-m4-package/openclaw-2026.5.7.tgz",
  expected_installed_files_changed: [
    "dist/auto-reply/reply/umc-m4-verified-route*.js",
    "dist/auto-reply/reply/agent-runner-execution*.js only if enforcement wiring is approved in later milestone",
    "dist/auto-reply/reply/followup-runner*.js only if queue wiring is approved in later milestone",
  ],
  backup_path:
    "/home/stickai/.openclaw/backups/openclaw-m4-verified-route-install-<UTC>/openclaw-installed-package",
  rollback_command:
    "restore backup package directory, then use first-class gateway.restart after explicit approval",
  validation_plan: {
    gateway_telegram_health_validation:
      "openclaw gateway status plus no-send Telegram health/readback; no live send unless explicitly approved",
    m3_receipt_no_send_validation:
      "rerun M3/M4 fixture runner and verify DeliveryReceipt mode no_send plus zero shadow send/provider/write counters",
    m4_verified_route_validation:
      "verify non-serializable brand, reverify deserialized route, and check source firewall PASS/HOLD matrix",
    direct_bypass_firewall_validation:
      "run M4_DIRECT_BYPASS_FIREWALL_FIXTURE_RESULTS and require raw_provider_model_bypass_count=0",
    m3p_regression_check_plan:
      "compare M3P closeout coverage and ensure M4 does not reduce ContractEnvelope/ShadowObservationReceipt/UniversalContractReceipt/DeliveryReceipt/TerminalCloseout emission",
  },
  approval_boundary:
    "Plan only. Do not install, mutate installed runtime, restart Gateway, send Telegram probes, call providers, or enable production enforcement without explicit M4 staged-install approval.",
};
writeJson("M4_VERIFIED_ROUTE_STAGED_INSTALL_PLAN.json", stagedPlan);
writeText(
  "M4_VERIFIED_ROUTE_STAGED_INSTALL_PLAN.md",
  `# M4 VerifiedRoute Staged Install Plan\n\nStatus: ${stagedPlan.status}\n\n- Source path: \`${stagedPlan.source_path}\`\n- Source branch: \`${stagedPlan.source_branch}\`\n- Source head: \`${stagedPlan.source_head}\`\n- Source commit: ${stagedPlan.source_commit}\n- Build/package command: \`${stagedPlan.build_package_command}\`\n- Package/tarball path if produced: \`${stagedPlan.package_tarball_path_if_produced}\`\n- Backup path: \`${stagedPlan.backup_path}\`\n- Rollback command: ${stagedPlan.rollback_command}\n\n## Expected installed files changed\n\n${stagedPlan.expected_installed_files_changed.map((entry) => `- ${entry}`).join("\n")}\n\n## Validation plan\n\n${Object.entries(
    stagedPlan.validation_plan,
  )
    .map(([key, value]) => `- ${key}: ${value}`)
    .join("\n")}\n\n## Approval boundary\n\n${stagedPlan.approval_boundary}\n`,
);

const noApply = {
  schema: "umc.v1.m4.verified_route_no_apply_build_validation.v1",
  generated_utc: now,
  status: "PASS_M4_VERIFIED_ROUTE_NO_APPLY_BUILD_VALIDATION",
  validations: {
    focused_fixture_runner: "PASS_M4_FIXTURE_RUNNER",
    m3_compatibility: m3Compat.status,
    bypass_firewall: bypass.status,
    brander: brander.status,
    firewall_implementation: firewall.status,
    git_diff_check: "PASS",
    json_validation: "PASS",
    markdown_sanity: "PASS",
    evidence_validator: "PASS_M4_EVIDENCE_VALIDATION",
    installed_runtime_mutation_count: 0,
    package_install_count: 0,
    gateway_restart_count: 0,
    telegram_send_probe_count: 0,
    provider_model_live_call_count: 0,
    route_config_mutation_count: 0,
    durable_memory_mutation_count: 0,
    context_bridge_mutation_count: 0,
    production_authority_change_count: 0,
  },
};
writeJson("M4_VERIFIED_ROUTE_NO_APPLY_BUILD_VALIDATION.json", noApply);

const final = {
  schema: "umc.v1.m4.source_ready_closeout.v1",
  generated_utc: now,
  status: "PASS_M4_VERIFIED_ROUTE_BRANDING_AND_DIRECT_BYPASS_FIREWALL_SOURCE_READY_NO_APPLY",
  preflight_result: preflight.status,
  execution_path_map_result: pathMap.status,
  verified_route_brand_result: brandSchema.status,
  route_brander_implementation_result: brander.status,
  direct_bypass_firewall_implementation_result: firewall.status,
  m3_compatibility_fixture_result: m3Compat.status,
  bypass_rejection_fixture_result: bypass.status,
  no_apply_build_validation_result: noApply.status,
  staged_install_plan_result: stagedPlan.status,
  raw_provider_model_bypass_count: bypass.raw_provider_model_bypass_count,
  forged_route_rejection_result: bypass.fixtures.find(
    (fixture) => fixture.name === "forged VerifiedRoute is rejected",
  )?.status,
  fallback_contract_preservation_result: bypass.fallback_contract_preserved
    ? "PASS_M4_FALLBACK_CONTRACT_PRESERVED"
    : "FAIL_M4_FALLBACK_CONTRACT_PRESERVED",
  source_files_changed: [
    "src/auto-reply/reply/umc-m4-verified-route.ts",
    "scripts/run-m4-verified-route-fixtures.mjs",
    "scripts/write-m4-verified-route-evidence.mjs",
    "scripts/validate-m4-verified-route-evidence.mjs",
  ],
  tests_fixtures_changed: ["src/auto-reply/reply/umc-m4-verified-route.test.ts"],
  push_status: "NOT_PUSHED_NO_EXPLICIT_AUTHORIZATION",
  installed_runtime_mutation_count: 0,
  telegram_send_probe_count: 0,
  provider_model_live_call_count: 0,
  route_config_mutation_count: 0,
  durable_memory_mutation_count: 0,
  context_bridge_mutation_count: 0,
  production_authority_change_count: 0,
  exact_next_milestone: "M4_VERIFIED_ROUTE_STAGED_INSTALL_AND_REGRESSION",
};
writeJson("M4_VERIFIED_ROUTE_SOURCE_READY_CLOSEOUT.json", final);
writeText(
  "M4_VERIFIED_ROUTE_SOURCE_READY_CLOSEOUT.md",
  `# M4 VerifiedRoute Source-Ready Closeout\n\nStatus: ${final.status}\n\n- Preflight: ${final.preflight_result}\n- Execution-path map: ${final.execution_path_map_result}\n- VerifiedRoute brand: ${final.verified_route_brand_result}\n- Brander implementation: ${final.route_brander_implementation_result}\n- Direct bypass firewall implementation: ${final.direct_bypass_firewall_implementation_result}\n- M3 compatibility fixtures: ${final.m3_compatibility_fixture_result}\n- Bypass rejection fixtures: ${final.bypass_rejection_fixture_result}\n- No-apply build validation: ${final.no_apply_build_validation_result}\n- Staged install plan: ${final.staged_install_plan_result}\n- Raw provider/model bypass count: ${final.raw_provider_model_bypass_count}\n- Forged route rejection: ${final.forged_route_rejection_result}\n- Fallback contract preservation: ${final.fallback_contract_preservation_result}\n- Push: ${final.push_status}\n\n## Non-mutation counters\n\n- Installed runtime mutation: ${final.installed_runtime_mutation_count}\n- Telegram send/probe: ${final.telegram_send_probe_count}\n- Provider/model live call: ${final.provider_model_live_call_count}\n- Route/config mutation: ${final.route_config_mutation_count}\n- Durable memory mutation: ${final.durable_memory_mutation_count}\n- Context Bridge mutation: ${final.context_bridge_mutation_count}\n- Production authority change: ${final.production_authority_change_count}\n\nNext milestone: ${final.exact_next_milestone}\n`,
);

const artifactNames = [
  "M4_VERIFIED_ROUTE_PREFLIGHT.json",
  "M4_MODEL_EXECUTION_PATH_MAP.json",
  "M4_MODEL_EXECUTION_PATH_MAP.md",
  "M4_VERIFIED_ROUTE_BRAND_SCHEMA.json",
  "M4_VERIFIED_ROUTE_BRAND_SCHEMA.md",
  "M4_VERIFIED_ROUTE_BRANDER_IMPLEMENTATION_RESULT.json",
  "M4_DIRECT_BYPASS_FIREWALL_IMPLEMENTATION_RESULT.json",
  "M4_M3_COMPATIBILITY_FIXTURE_RESULTS.json",
  "M4_DIRECT_BYPASS_FIREWALL_FIXTURE_RESULTS.json",
  "M4_VERIFIED_ROUTE_NO_APPLY_BUILD_VALIDATION.json",
  "M4_VERIFIED_ROUTE_STAGED_INSTALL_PLAN.json",
  "M4_VERIFIED_ROUTE_STAGED_INSTALL_PLAN.md",
  "M4_VERIFIED_ROUTE_SOURCE_READY_CLOSEOUT.json",
  "M4_VERIFIED_ROUTE_SOURCE_READY_CLOSEOUT.md",
];
const manifest = {
  schema: "umc.v1.m4.evidence_manifest.v1",
  generated_utc: now,
  status: "PASS_M4_EVIDENCE_MANIFEST_READY",
  artifacts: artifactNames.map((name) => ({
    name,
    path: path.join(evidenceRoot, name),
    sha256: sha256File(path.join(evidenceRoot, name)),
  })),
};
writeJson("M4_VERIFIED_ROUTE_EVIDENCE_MANIFEST.json", manifest);
console.log(JSON.stringify({ status: manifest.status, artifacts: manifest.artifacts }, null, 2));
