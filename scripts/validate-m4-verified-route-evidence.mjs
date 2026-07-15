import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const evidenceRoot =
  process.argv[2] ||
  path.resolve(
    process.cwd(),
    "../../workspace/sharedspace/runtime-kernel-validation/universal-model-contract/m3n_restart_persistence_no_send",
  );
const requiredJson = [
  ["M4_VERIFIED_ROUTE_PREFLIGHT.json", "PASS_M4_VERIFIED_ROUTE_PREFLIGHT"],
  ["M4_MODEL_EXECUTION_PATH_MAP.json", "PASS_M4_MODEL_EXECUTION_PATHS_MAPPED"],
  ["M4_VERIFIED_ROUTE_BRAND_SCHEMA.json", "PASS_M4_VERIFIED_ROUTE_BRAND_DEFINED"],
  [
    "M4_VERIFIED_ROUTE_BRANDER_IMPLEMENTATION_RESULT.json",
    "PASS_M4_VERIFIED_ROUTE_BRANDER_IMPLEMENTED",
  ],
  [
    "M4_DIRECT_BYPASS_FIREWALL_IMPLEMENTATION_RESULT.json",
    "PASS_M4_DIRECT_BYPASS_FIREWALL_IMPLEMENTED",
  ],
  ["M4_M3_COMPATIBILITY_FIXTURE_RESULTS.json", "PASS_M4_M3_COMPATIBILITY_FIXTURES"],
  ["M4_DIRECT_BYPASS_FIREWALL_FIXTURE_RESULTS.json", "PASS_M4_DIRECT_BYPASS_FIREWALL_FIXTURES"],
  [
    "M4_VERIFIED_ROUTE_NO_APPLY_BUILD_VALIDATION.json",
    "PASS_M4_VERIFIED_ROUTE_NO_APPLY_BUILD_VALIDATION",
  ],
  [
    "M4_VERIFIED_ROUTE_STAGED_INSTALL_PLAN.json",
    "PASS_M4_VERIFIED_ROUTE_STAGED_INSTALL_PLAN_READY",
  ],
  [
    "M4_VERIFIED_ROUTE_SOURCE_READY_CLOSEOUT.json",
    "PASS_M4_VERIFIED_ROUTE_BRANDING_AND_DIRECT_BYPASS_FIREWALL_SOURCE_READY_NO_APPLY",
  ],
  ["M4_VERIFIED_ROUTE_EVIDENCE_MANIFEST.json", "PASS_M4_EVIDENCE_MANIFEST_READY"],
];
const requiredMd = [
  "M4_MODEL_EXECUTION_PATH_MAP.md",
  "M4_VERIFIED_ROUTE_BRAND_SCHEMA.md",
  "M4_VERIFIED_ROUTE_STAGED_INSTALL_PLAN.md",
  "M4_VERIFIED_ROUTE_SOURCE_READY_CLOSEOUT.md",
];
const results = [];
for (const [name, expectedStatus] of requiredJson) {
  const file = path.join(evidenceRoot, name);
  const parsed = JSON.parse(fs.readFileSync(file, "utf8"));
  if (parsed.status !== expectedStatus) {
    throw new Error(`${name} expected ${expectedStatus} got ${parsed.status}`);
  }
  results.push({
    name,
    status: parsed.status,
    sha256: crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex"),
  });
}
for (const name of requiredMd) {
  const file = path.join(evidenceRoot, name);
  const text = fs.readFileSync(file, "utf8");
  if (!text.includes("Status:") || text.includes("FAIL_")) {
    throw new Error(`${name} markdown sanity failed`);
  }
  results.push({
    name,
    status: "PASS_MARKDOWN_SANITY",
    sha256: crypto.createHash("sha256").update(text).digest("hex"),
  });
}
const closeout = JSON.parse(
  fs.readFileSync(path.join(evidenceRoot, "M4_VERIFIED_ROUTE_SOURCE_READY_CLOSEOUT.json"), "utf8"),
);
const zeroCounters = [
  "installed_runtime_mutation_count",
  "telegram_send_probe_count",
  "provider_model_live_call_count",
  "route_config_mutation_count",
  "durable_memory_mutation_count",
  "context_bridge_mutation_count",
  "production_authority_change_count",
];
for (const key of zeroCounters) {
  if (closeout[key] !== 0) {
    throw new Error(`${key} expected 0 got ${closeout[key]}`);
  }
}
console.log(JSON.stringify({ status: "PASS_M4_EVIDENCE_VALIDATION", results }, null, 2));
