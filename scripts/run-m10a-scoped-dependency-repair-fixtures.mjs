#!/usr/bin/env node
import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

const sourceRoot = process.cwd();
const workspaceRoot = "/home/stickai/.openclaw/workspace";
const evidenceRoot =
  process.argv[2] ||
  path.join(
    workspaceRoot,
    "sharedspace/runtime-kernel-validation/universal-model-contract/m9_limited_live_action_canary",
  );
const installedRoot = "/home/stickai/.npm-global/lib/node_modules/openclaw";
const candidateRoot = path.join(workspaceRoot, "tmp", "umc-m10a-repaired-scoped-overlay-r2");
const overlayRoot = path.join(candidateRoot, "overlay-root");
const driftRoot = path.join(candidateRoot, "drift-overlay-root");
const overlayPath = path.join(
  candidateRoot,
  "m10a-control-path-scoped-overlay-r2-20260716T1200Z.tar.gz",
);
const driftOverlayPath = path.join(
  candidateRoot,
  "m10a-control-path-r2-drift-overlay-fixture.tar.gz",
);
const m10aRel = "dist/auto-reply/reply/umc-m10a-owner-telegram-direct-control-path.js";
const m8Rel = "dist/auto-reply/reply/umc-m8-owner-contract-lane.js";
const dependencyRel = "dist/umc-m8-owner-contract-lane-CdxuqyX4.js";
const manifestRel = "M10A_SCOPED_OVERLAY_MANIFEST.json";
const now = "2026-07-16T12:00:00Z";

const expectedM8 = "27116a4374b699b7e98bc8ec9be98f3584bc14a8ca740d0723316deaa66088db";
const expectedM10a = "be56d6a5105d4d0a03085757483b3bb07374ff96b9db8ea44a1bcb164139e082";
const requiredDependencies = Object.freeze({
  "dist/umc-m8-owner-contract-lane-CdxuqyX4.js":
    "70e580814a1649068dcd173d979ac31d579b5ef7ae85866753c1503133815ed7",
  "dist/umc-m7-model-eligibility-ovqh9OfD.js":
    "e25711e5809835085d4c5450f5b1fb4e479b6f9e29631b538fd1f9908e78b9bd",
  "dist/umc-m6-contract-build-lane-B49r9Ao5.js":
    "8416342de89bf8e525f477c4255c59b54f0a5a624d8a1c02dd2e783aa51a397a",
  "dist/umc-m5-capability-manifest-DBUsXqaz.js":
    "3f4dc6191a7e4ffced65b95aaeb9113964f2c9c36c1958c634fbdefb5d059745",
  "dist/umc-m4-verified-route-B8LC1Bgv.js":
    "8fd34dd344ec074204feb6231127ae0ff9bf7655f5273b864103cf5b457b5cc2",
  "dist/umc-m3-envelope-supervision-CZFFPUFB.js":
    "9af1b667eb69a32c7d7f9bd28c3bd72843e331d63cc8bf8e81399479a6a7dfba",
});
const staleCandidateSha = "be66f39008d09e8a04c848a50a3842b8553743a5bd4b0a9541218f3a32204587";

function sha(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}
function writeJson(name, value) {
  const file = path.join(evidenceRoot, name);
  fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`);
  return { file: name, bytes: fs.statSync(file).size, sha256: sha(file), status: value.status };
}
function writeText(name, value) {
  const file = path.join(evidenceRoot, name);
  fs.writeFileSync(file, value.endsWith("\n") ? value : `${value}\n`);
  return { file: name, bytes: fs.statSync(file).size, sha256: sha(file) };
}
function readJson(name) {
  return JSON.parse(fs.readFileSync(path.join(evidenceRoot, name), "utf8"));
}
function git(args) {
  return execFileSync("git", args, { cwd: sourceRoot, encoding: "utf8" }).trim();
}
function run(command, args, options = {}) {
  const result = spawnSync(command, args, { encoding: "utf8", ...options });
  if (result.error) throw result.error;
  if (result.status !== 0)
    throw new Error(`${command} ${args.join(" ")} failed: ${result.stderr || result.stdout}`);
  return result.stdout;
}
function copyFile(src, dst) {
  fs.mkdirSync(path.dirname(dst), { recursive: true });
  fs.copyFileSync(src, dst);
}
function tarCreate(root, out) {
  run("tar", [
    "--sort=name",
    "--mtime=@0",
    "--owner=0",
    "--group=0",
    "--numeric-owner",
    "-czf",
    out,
    "-C",
    root,
    ".",
  ]);
}
function tarList(out) {
  return run("tar", ["-tf", out])
    .split(/\r?\n/u)
    .filter(Boolean)
    .map((x) => x.replace(/^\.\//u, ""))
    .filter((x) => x.length > 0 && !x.endsWith("/"))
    .sort();
}
function runGuard(args) {
  return spawnSync(
    "node",
    [path.join(sourceRoot, "scripts", "umc-m10a-preservation-guard.mjs"), ...args],
    {
      cwd: sourceRoot,
      encoding: "utf8",
    },
  );
}

fs.mkdirSync(evidenceRoot, { recursive: true });
const failedCloseout = readJson(
  "M10A_REPAIRED_CONTROL_PATH_STAGED_INSTALL_AND_VALIDATION_CLOSEOUT.json",
);
const failedRuntime = readJson("M10A_REPAIRED_CONTROL_PATH_INSTALLED_RUNTIME_VERIFICATION.json");
assert.equal(failedCloseout.status, "FAIL_M10A_REPAIRED_CONTROL_PATH_STAGED_INSTALL_FAILED");
assert.equal(
  failedRuntime.status,
  "FAIL_M10A_INSTALLED_RUNTIME_VERIFICATION_MISSING_DEPENDENCY_CHUNK",
);
assert.equal(failedRuntime.missing_dependency_chunk, dependencyRel);
assert.equal(sha(path.join(installedRoot, m8Rel)), expectedM8);
assert.equal(fs.existsSync(path.join(installedRoot, m10aRel)), false);
const installedDependencyPreState = {};
for (const relativePath of Object.keys(requiredDependencies)) {
  const installedPath = path.join(installedRoot, relativePath);
  installedDependencyPreState[relativePath] = fs.existsSync(installedPath)
    ? { present: true, sha256: sha(installedPath) }
    : { present: false, sha256: null };
}
assert.equal(installedDependencyPreState[dependencyRel].present, false);

const sourceHead = git(["rev-parse", "HEAD"]);
const sourceBranch = git(["branch", "--show-current"]);
const sourceM10a = path.join(sourceRoot, m10aRel);
const sourceM8 = path.join(sourceRoot, m8Rel);
assert.equal(sha(sourceM10a), expectedM10a);
for (const [relativePath, expectedSha256] of Object.entries(requiredDependencies)) {
  assert.equal(sha(path.join(sourceRoot, relativePath)), expectedSha256);
}
assert.equal(sha(path.join(installedRoot, m8Rel)), expectedM8);

fs.rmSync(candidateRoot, { recursive: true, force: true });
copyFile(sourceM10a, path.join(overlayRoot, m10aRel));
for (const relativePath of Object.keys(requiredDependencies)) {
  copyFile(path.join(sourceRoot, relativePath), path.join(overlayRoot, relativePath));
}
fs.writeFileSync(
  path.join(overlayRoot, manifestRel),
  `${JSON.stringify(
    {
      schema: "umc.v1.m10a.scoped_overlay_manifest.v2",
      generated_utc: now,
      status: "PASS_M10A_SCOPED_DEPENDENCY_OVERLAY_CREATED",
      source_commit: sourceHead,
      includes: [m10aRel, ...Object.keys(requiredDependencies)],
      required_runtime_dependencies: requiredDependencies,
      explicitly_excludes_preserved_runtime_artifacts: [m8Rel],
      expected_m10a_sha256: expectedM10a,
      expected_preserved_m8_sha256: expectedM8,
    },
    null,
    2,
  )}\n`,
);
tarCreate(overlayRoot, overlayPath);
const overlaySha = sha(overlayPath);
const entries = tarList(overlayPath);
assert.deepEqual(entries, [manifestRel, m10aRel, ...Object.keys(requiredDependencies)].sort());
assert.notEqual(overlaySha, staleCandidateSha);

copyFile(sourceM10a, path.join(driftRoot, m10aRel));
for (const relativePath of Object.keys(requiredDependencies)) {
  copyFile(path.join(sourceRoot, relativePath), path.join(driftRoot, relativePath));
}
copyFile(sourceM8, path.join(driftRoot, m8Rel));
fs.writeFileSync(path.join(driftRoot, manifestRel), "{}\n");
tarCreate(driftRoot, driftOverlayPath);
const driftSha = sha(driftOverlayPath);

const guardArgs = [
  "--mode",
  "dry-run",
  "--overlay",
  overlayPath,
  "--installed-root",
  installedRoot,
  "--expected-overlay-sha256",
  overlaySha,
  "--expected-m10a-sha256",
  expectedM10a,
];
const guard = runGuard(guardArgs);
assert.equal(guard.status, 0, guard.stderr || guard.stdout);
const guardJson = JSON.parse(guard.stdout);
assert.equal(guardJson.status, "PASS_M10A_PACKAGE_PRESERVATION_GUARD_DRY_RUN");
for (const [relativePath, expectedSha256] of Object.entries(requiredDependencies)) {
  assert.equal(guardJson.requiredRuntimeDependencies[relativePath].actualSha256, expectedSha256);
}
assert.equal(guardJson.preservedChecksBefore[m8Rel].actualSha256, expectedM8);
assert.equal(
  guardJson.expectedInstalledChanges.length,
  1 + Object.keys(requiredDependencies).length,
);

const driftGuard = runGuard([
  "--mode",
  "dry-run",
  "--overlay",
  driftOverlayPath,
  "--installed-root",
  installedRoot,
  "--expected-overlay-sha256",
  driftSha,
  "--expected-m10a-sha256",
  expectedM10a,
]);
assert.notEqual(driftGuard.status, 0);
assert.match(driftGuard.stdout, /FAIL_M10A_PACKAGE_PRESERVATION_GUARD_ACCEPTED_DRIFT/);

const tempInstall = fs.mkdtempSync(path.join(os.tmpdir(), "m10a-r2-import-"));
run("tar", ["-xf", overlayPath, "-C", tempInstall]);
const imported = await import(pathToFileURL(path.join(tempInstall, m10aRel)).href);
const defaultState = imported.buildM10ADefaultControlState();
const readback = imported.readM10AStatus(defaultState);
assert.equal(readback.enabled, false);
assert.equal(readback.production_authority, false);
assert.equal(readback.broad_enforcement, false);
const exactEnable = imported.applyM10AControlIntent(defaultState, {
  request: "enable",
  scope_name: imported.M10A_SCOPE_NAME,
  owner_chat_id: imported.M10A_OWNER_CHAT_ID,
  channel: imported.M10A_CHANNEL,
  agent_id: imported.M10A_AGENT_ID,
  contract_decision_enforcement: true,
  production_authority: false,
  broad_enforcement: false,
  external_sends_allowed: false,
  provider_calls_allowed: false,
  write_tools_allowed: false,
  durable_memory_mutation_allowed: false,
  context_bridge_mutation_allowed: false,
});
assert.equal(exactEnable.status, "PASS_M10A_CONTROL_ENABLE_ACCEPTED");
const wrongOwner = imported.applyM10AControlIntent(defaultState, {
  request: "enable",
  scope_name: imported.M10A_SCOPE_NAME,
  owner_chat_id: "0000",
  channel: imported.M10A_CHANNEL,
  agent_id: imported.M10A_AGENT_ID,
  contract_decision_enforcement: true,
});
assert.equal(wrongOwner.status, "FAIL_M10A_ENABLE_SCOPE_MISMATCH");
const runtimeDisabled = imported.evaluateM10AOwnerTelegramDirectContractDecision({
  surface: "telegram",
  channel: imported.M10A_CHANNEL,
  chat_type: "direct",
  owner_chat_id: imported.M10A_OWNER_CHAT_ID,
  agent_id: imported.M10A_AGENT_ID,
});
assert.equal(runtimeDisabled.status, "PASS_M10A_DISABLED_PRE_M10_BEHAVIOR");

const preflight = {
  schema: "umc.v1.m10a.scoped_runtime_dependency_repair_preflight.v1",
  generated_utc: now,
  status: "PASS_M10A_SCOPED_RUNTIME_DEPENDENCY_REPAIR_PREFLIGHT",
  failed_status_rehydrated: failedCloseout.status,
  missing_dependency_chunk: dependencyRel,
  m8_preserved_sha256: expectedM8,
  installed_m10a_absent: true,
  installed_dependency_pre_state: installedDependencyPreState,
  no_apply: true,
};
const rootCause = {
  schema: "umc.v1.m10a.scoped_runtime_dependency_root_cause.v1",
  generated_utc: now,
  status: "PASS_M10A_SCOPED_RUNTIME_DEPENDENCY_ROOT_CAUSE_CLASSIFIED",
  classification: "SCOPED_OVERLAY_OMITTED_GENERATED_RUNTIME_DEPENDENCY_CHUNK",
  missing_dependency_chunk: dependencyRel,
  dependency_sha256: requiredDependencies[dependencyRel],
  required_runtime_dependencies: requiredDependencies,
  conclusion:
    "The previous scoped overlay preserved M8 but copied only the M10A entry file. The built M10A entry imports generated support chunks through the M8/M7/M6 chain, so the overlay must include the full runtime dependency closure while still excluding preserved M2-M9 entry artifacts such as the canonical M8 entry file.",
};
const sourceRepair = {
  schema: "umc.v1.m10a.scoped_runtime_dependency_source_repair.v1",
  generated_utc: now,
  status: "PASS_M10A_SCOPED_RUNTIME_DEPENDENCY_SOURCE_REPAIR_NO_APPLY",
  source_commit: sourceHead,
  source_files: [
    "scripts/umc-m10a-preservation-guard.mjs",
    "scripts/run-m10a-scoped-dependency-repair-fixtures.mjs",
  ],
  repair_summary:
    "Extended the scoped preservation guard to require, hash-check, and copy the generated runtime dependency closure alongside the M10A entry while continuing to reject preserved M2-M9 runtime entry artifacts such as the canonical M8 entry file.",
  no_apply: true,
};
const guardFixtures = {
  schema: "umc.v1.m10a.scoped_runtime_dependency_guard_fixture_results.v1",
  generated_utc: now,
  status: "PASS_M10A_SCOPED_RUNTIME_DEPENDENCY_GUARD_FIXTURES",
  good_overlay_dry_run: guardJson.status,
  drift_overlay_rejected: "FAIL_M10A_PACKAGE_PRESERVATION_GUARD_ACCEPTED_DRIFT",
  m8_preserved_sha256: expectedM8,
  m10a_sha256: expectedM10a,
  dependency_sha256: requiredDependencies[dependencyRel],
  required_runtime_dependencies: requiredDependencies,
  plugin_manifest_preserved: true,
  m10a_disabled_by_default: true,
  production_authority_false: true,
  broad_enforcement_false: true,
};
const importValidation = {
  schema: "umc.v1.m10a.scoped_runtime_dependency_temp_import_validation.v1",
  generated_utc: now,
  status: "PASS_M10A_SCOPED_RUNTIME_DEPENDENCY_TEMP_IMPORT_VALIDATION",
  temp_install_root: tempInstall,
  imported_entry: m10aRel,
  imported_dependency: dependencyRel,
  imported_dependency_closure: requiredDependencies,
  default_readback_enabled: readback.enabled,
  default_production_authority: readback.production_authority,
  default_broad_enforcement: readback.broad_enforcement,
  exact_enable_fixture_status: exactEnable.status,
  wrong_owner_fixture_status: wrongOwner.status,
  runtime_disabled_status: runtimeDisabled.status,
};
const dryRun = {
  schema: "umc.v1.m10a.scoped_runtime_dependency_package_dry_run.v1",
  generated_utc: now,
  status: "PASS_M10A_SCOPED_RUNTIME_DEPENDENCY_PACKAGE_DRY_RUN",
  candidate_tarball_path: overlayPath,
  candidate_tarball_sha256: overlaySha,
  stale_candidate_sha_rejected: staleCandidateSha,
  candidate_m10a_dist_sha256: expectedM10a,
  candidate_dependency_sha256: requiredDependencies[dependencyRel],
  candidate_dependency_closure: requiredDependencies,
  candidate_file_list: entries,
  preserved_m8_handling: "canonical M8 entry file excluded and protected by SHA guard",
  expected_installed_files_changed: guardJson.expectedInstalledChanges,
  no_install: true,
  no_gateway_restart: true,
};
const approval = {
  schema: "umc.v1.m10a.runtime_dependency_repaired_control_path_install_approval_card.v1",
  generated_utc: now,
  status: "HOLD_M10A_RUNTIME_DEPENDENCY_REPAIRED_INSTALL_AWAITING_OPERATOR_APPROVAL",
  root_cause: rootCause,
  repair_summary: sourceRepair.repair_summary,
  source: { source_path: sourceRoot, source_branch: sourceBranch, source_commit: sourceHead },
  candidate_tarball_path: overlayPath,
  candidate_tarball_sha256: overlaySha,
  candidate_m10a_dist_sha256: expectedM10a,
  candidate_dependency_sha256: requiredDependencies[dependencyRel],
  candidate_dependency_closure: requiredDependencies,
  expected_installed_files_changed: guardJson.expectedInstalledChanges,
  explicit_m8_sha_preservation_check: expectedM8,
  required_runtime_dependencies: requiredDependencies,
  backup_path:
    "/home/stickai/.openclaw/backups/openclaw-m10a-runtime-dependency-repaired-install-20260716T1200Z/openclaw-installed-package",
  approved_install_command_template: `node ${path.join(sourceRoot, "scripts", "umc-m10a-preservation-guard.mjs")} --mode apply --overlay ${overlayPath} --installed-root ${installedRoot} --expected-overlay-sha256 ${overlaySha} --expected-m10a-sha256 ${expectedM10a} --backup-path /home/stickai/.openclaw/backups/openclaw-m10a-runtime-dependency-repaired-install-20260716T1200Z/openclaw-installed-package`,
  gateway_restart_requirement:
    "required only after approved install and preservation/import checks pass",
  hard_stops: [
    "candidate SHA mismatch",
    "M8 or preserved M2-M9 drift",
    "required dependency chunk missing",
    "M10A enabled by default",
    "production authority changes",
  ],
  no_install_performed: true,
};
const approvalMd = `# M10A Runtime-Dependency Repaired Control Path Install Approval Card\n\nStatus: \`${approval.status}\`\n\n## Root cause\n\n${rootCause.conclusion}\n\n## Repair summary\n\n${sourceRepair.repair_summary}\n\n## Candidate\n\n- Path: \`${overlayPath}\`\n- SHA256: \`${overlaySha}\`\n- M10A dist SHA256: \`${expectedM10a}\`\n- Required dependency closure:\n${Object.entries(
  requiredDependencies,
)
  .map(([p, s]) => `  - \`${p}\`: \`${s}\``)
  .join(
    "\n",
  )}\n\n## Expected installed files changed\n\n${guardJson.expectedInstalledChanges.map((x) => `- ${x.operation} \`${x.path}\` SHA256 \`${x.sha256}\``).join("\n")}\n\n## Preservation\n\nM8 remains required at \`${expectedM8}\`. The canonical M8 entry file is excluded from the overlay and remains protected by the preservation guard.\n\n## Approved install command template\n\n\`\`\`sh\n${approval.approved_install_command_template}\n\`\`\`\n\nNo install, Gateway restart, M10A enablement, production authority change, send/probe, provider call, durable memory mutation, or Context Bridge mutation was performed in this no-apply repair.\n`;

const artifacts = [
  writeJson("M10A_SCOPED_RUNTIME_DEPENDENCY_REPAIR_PREFLIGHT.json", preflight),
  writeText(
    "M10A_SCOPED_RUNTIME_DEPENDENCY_REPAIR_PREFLIGHT.md",
    `# M10A Scoped Runtime Dependency Repair Preflight\n\nStatus: \`${preflight.status}\`\n\nMissing dependency chunk rehydrated: \`${dependencyRel}\`. M8 remains preserved at \`${expectedM8}\`; M10A is absent from installed runtime after rollback.\n`,
  ),
  writeJson("M10A_SCOPED_RUNTIME_DEPENDENCY_ROOT_CAUSE.json", rootCause),
  writeText(
    "M10A_SCOPED_RUNTIME_DEPENDENCY_ROOT_CAUSE.md",
    `# M10A Scoped Runtime Dependency Root Cause\n\nStatus: \`${rootCause.status}\`\n\nClassification: \`${rootCause.classification}\`\n\n${rootCause.conclusion}\n`,
  ),
  writeJson("M10A_SCOPED_RUNTIME_DEPENDENCY_SOURCE_REPAIR_RESULT.json", sourceRepair),
  writeText(
    "M10A_SCOPED_RUNTIME_DEPENDENCY_SOURCE_REPAIR.md",
    `# M10A Scoped Runtime Dependency Source Repair\n\nStatus: \`${sourceRepair.status}\`\n\n${sourceRepair.repair_summary}\n`,
  ),
  writeJson("M10A_SCOPED_RUNTIME_DEPENDENCY_GUARD_FIXTURE_RESULTS.json", guardFixtures),
  writeJson("M10A_SCOPED_RUNTIME_DEPENDENCY_TEMP_IMPORT_VALIDATION.json", importValidation),
  writeJson("M10A_SCOPED_RUNTIME_DEPENDENCY_PACKAGE_DRY_RUN_RESULT.json", dryRun),
  writeJson("M10A_RUNTIME_DEPENDENCY_REPAIRED_CONTROL_PATH_INSTALL_APPROVAL_CARD.json", approval),
  writeText("M10A_RUNTIME_DEPENDENCY_REPAIRED_CONTROL_PATH_INSTALL_APPROVAL_CARD.md", approvalMd),
];
const manifest = {
  schema: "umc.v1.m10a.scoped_runtime_dependency_repair_evidence_manifest.v1",
  generated_utc: now,
  status: "HOLD_M10A_RUNTIME_DEPENDENCY_REPAIRED_INSTALL_AWAITING_OPERATOR_APPROVAL",
  final_status: "HOLD_M10A_RUNTIME_DEPENDENCY_REPAIRED_INSTALL_AWAITING_OPERATOR_APPROVAL",
  artifacts,
  candidate_tarball_path: overlayPath,
  candidate_tarball_sha256: overlaySha,
  candidate_m10a_dist_sha256: expectedM10a,
  candidate_dependency_sha256: requiredDependencies[dependencyRel],
  candidate_dependency_closure: requiredDependencies,
  expected_m8_preserved_sha256: expectedM8,
  m10a_enabled: false,
  production_authority_changed: false,
  gateway_restart_count: 0,
  telegram_send_probe_count: 0,
  external_send_count: 0,
  provider_model_live_call_count: 0,
  write_tool_execution_count: 0,
  durable_memory_mutation_count: 0,
  context_bridge_mutation_count: 0,
  next_phase: "APPROVE_OR_DENY_M10A_RUNTIME_DEPENDENCY_REPAIRED_STAGED_INSTALL",
};
artifacts.push(writeJson("M10A_SCOPED_RUNTIME_DEPENDENCY_REPAIR_EVIDENCE_MANIFEST.json", manifest));
console.log(
  JSON.stringify(
    {
      status: manifest.status,
      candidate_tarball_path: overlayPath,
      candidate_tarball_sha256: overlaySha,
      artifacts,
    },
    null,
    2,
  ),
);
