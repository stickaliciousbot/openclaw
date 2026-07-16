#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const repoRoot = process.cwd();
const tarballPath = process.argv[2]
  ? path.resolve(process.argv[2])
  : path.resolve(repoRoot, "../workspace/tmp/umc-m4-package/openclaw-2026.5.7.tgz");
const tsdownConfigPath = path.join(repoRoot, "tsdown.config.ts");
const m4DistPath = path.join(repoRoot, "dist/auto-reply/reply/umc-m4-verified-route.js");
const sourcePath = path.join(repoRoot, "src/auto-reply/reply/umc-m4-verified-route.ts");

function sha256(filePath) {
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function readText(filePath) {
  return fs.readFileSync(filePath, "utf8");
}

function tarList(filePath) {
  const result = spawnSync("tar", ["-tzf", filePath], { encoding: "utf8" });
  if (result.status !== 0) {
    throw new Error(`tar list failed for ${filePath}: ${result.stderr || result.stdout}`);
  }
  return result.stdout.split(/\r?\n/u).filter(Boolean);
}

function tarExtract(filePath, member) {
  const result = spawnSync("tar", ["-xOzf", filePath, member], {
    encoding: "utf8",
    maxBuffer: 64 * 1024 * 1024,
  });
  if (result.status !== 0) {
    throw new Error(`tar extract failed for ${member}: ${result.stderr || result.stdout}`);
  }
  return result.stdout;
}

const tsdownConfig = readText(tsdownConfigPath);
const source = readText(sourcePath);
const sourceContainsM4 =
  source.includes("M4_VERIFIED_ROUTE_VERSION") && source.includes("enforceM4VerifiedRouteFirewall");
const tsdownIncludesM4Entry =
  tsdownConfig.includes('"auto-reply/reply/umc-m4-verified-route"') &&
  tsdownConfig.includes('"src/auto-reply/reply/umc-m4-verified-route.ts"');
const distExists = fs.existsSync(m4DistPath);
const distText = distExists ? readText(m4DistPath) : "";
const distContainsM4 =
  distText.includes("M4_VERIFIED_ROUTE_VERSION") ||
  distText.includes("VERIFIED_ROUTE_UMC_V1_M4") ||
  distText.includes("umc.v1.m4.verified_route.v1");
const tarballExists = fs.existsSync(tarballPath);
const tarballMembers = tarballExists ? tarList(tarballPath) : [];
const tarballM4Member = "package/dist/auto-reply/reply/umc-m4-verified-route.js";
const tarballContainsM4Member = tarballMembers.includes(tarballM4Member);
const tarballM4Text = tarballContainsM4Member ? tarExtract(tarballPath, tarballM4Member) : "";
const tarballContainsM4Symbols =
  tarballM4Text.includes("VERIFIED_ROUTE_UMC_V1_M4") ||
  tarballM4Text.includes("umc.v1.m4.verified_route.v1") ||
  tarballM4Text.includes("M4_VERIFIED_ROUTE_VERSION");
const agentRunnerMembers = tarballMembers.filter((entry) =>
  /package\/dist\/agent-runner\.runtime.*\.js$/u.test(entry),
);
const agentRunnerText = agentRunnerMembers
  .map((entry) => tarExtract(tarballPath, entry))
  .join("\n");
const tarballContainsM3Artifact =
  agentRunnerText.includes("ContractEnvelope") &&
  agentRunnerText.includes("DeliveryReceipt") &&
  agentRunnerText.includes("no_send");
const tarballContainsM2Hook =
  agentRunnerText.includes("resolveUmcV1DefaultRouteFromConfig") &&
  agentRunnerText.includes("applyUmcV1QueuedRouteAdmission") &&
  agentRunnerText.includes("M2Q_QUEUE_RESUME_ROUTE_ADMISSION");
const pluginManifestMembers = tarballMembers.filter((entry) =>
  entry.endsWith("openclaw.plugin.json"),
);
const telegramManifestPreserved =
  pluginManifestMembers.includes("package/dist/extensions/telegram/openclaw.plugin.json") ||
  pluginManifestMembers.includes("package/dist/extensions/zalo/openclaw.plugin.json");

const checks = {
  sourceContainsM4,
  tsdownIncludesM4Entry,
  distExists,
  distContainsM4,
  tarballExists,
  tarballContainsM4Member,
  tarballContainsM4Symbols,
  tarballContainsM3Artifact,
  tarballContainsM2Hook,
  pluginManifestCount: pluginManifestMembers.length,
  telegramOrPackagedManifestPreserved: telegramManifestPreserved,
};
const ok = Object.entries(checks).every(([key, value]) =>
  key === "pluginManifestCount" ? Number(value) > 0 : Boolean(value),
);
const result = {
  schema: "umc.v1.m4.source_build_inclusion_validation.v1",
  generated_utc: new Date().toISOString(),
  status: ok
    ? "PASS_M4_SOURCE_BUILD_INCLUSION_VALIDATION"
    : "FAIL_M4_SOURCE_BUILD_INCLUSION_VALIDATION",
  repo_root: repoRoot,
  source_path: sourcePath,
  tsdown_config_path: tsdownConfigPath,
  dist_path: m4DistPath,
  tarball_path: tarballPath,
  tarball_sha256: tarballExists ? sha256(tarballPath) : null,
  m4_tarball_member: tarballM4Member,
  agent_runner_members: agentRunnerMembers,
  plugin_manifest_count: pluginManifestMembers.length,
  checks,
  safety_counters: {
    installed_runtime_mutation_count: 0,
    direct_dist_hotpatch_count: 0,
    gateway_restart_count: 0,
    telegram_send_probe_count: 0,
    external_send_count: 0,
    provider_model_live_call_count: 0,
    route_config_mutation_count: 0,
    durable_memory_mutation_count: 0,
    context_bridge_mutation_count: 0,
    production_authority_change_count: 0,
    production_enforcement_enabled: false,
  },
};
console.log(JSON.stringify(result, null, 2));
process.exit(ok ? 0 : 1);
