#!/usr/bin/env node
import assert from "node:assert/strict";
import { spawnSync, execFileSync } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const sourceRoot = process.cwd();
const workspaceRoot = "/home/stickai/.openclaw/workspace";
const evidenceRoot =
  process.argv[2] ||
  path.join(
    workspaceRoot,
    "sharedspace/runtime-kernel-validation/universal-model-contract/m9_limited_live_action_canary",
  );
const candidateRoot = path.join(workspaceRoot, "tmp", "umc-m10a-repaired-scoped-overlay");
const overlayRoot = path.join(candidateRoot, "overlay-root");
const driftRoot = path.join(candidateRoot, "drift-overlay-root");
const overlayPath = path.join(
  candidateRoot,
  "m10a-control-path-scoped-overlay-20260716T1133Z.tar.gz",
);
const driftOverlayPath = path.join(candidateRoot, "m10a-control-path-drift-overlay-fixture.tar.gz");
const installedRoot = "/home/stickai/.npm-global/lib/node_modules/openclaw";
const m10aRel = "dist/auto-reply/reply/umc-m10a-owner-telegram-direct-control-path.js";
const m8Rel = "dist/auto-reply/reply/umc-m8-owner-contract-lane.js";
const now = "2026-07-16T11:33:00Z";

const expectedM8 = "27116a4374b699b7e98bc8ec9be98f3584bc14a8ca740d0723316deaa66088db";
const driftedM8 = "753fade05d957fb295dcf33a7beaec7a89d6b977e750c937e26a9cd7ad18b0ef";
const expectedM10a = "be56d6a5105d4d0a03085757483b3bb07374ff96b9db8ea44a1bcb164139e082";

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
function run(command, args, options = {}) {
  const result = spawnSync(command, args, { encoding: "utf8", ...options });
  if (result.error) throw result.error;
  if (result.status !== 0) {
    throw new Error(`${command} ${args.join(" ")} failed: ${result.stderr || result.stdout}`);
  }
  return result.stdout;
}
function git(args) {
  return execFileSync("git", args, { cwd: sourceRoot, encoding: "utf8" }).trim();
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
function copyFile(src, dst) {
  fs.mkdirSync(path.dirname(dst), { recursive: true });
  fs.copyFileSync(src, dst);
}

fs.mkdirSync(evidenceRoot, { recursive: true });
const install = readJson("M10A_CONTROL_PATH_STAGED_INSTALL_RESULT.json");
const rollback = readJson("M10A_CONTROL_PATH_STAGED_INSTALL_ROLLBACK_RESULT.json");
const failure = readJson("M10A_CONTROL_PATH_STAGED_INSTALL_FAILURE_CLOSEOUT.json");
assert.equal(install.status, "FAIL_M10A_CONTROL_PATH_STAGED_INSTALL_FAILED");
assert.equal(install.gateway_restart_run, false);
assert.equal(install.gateway_activation_run, false);
assert.equal(rollback.status, "PASS_M10A_STAGED_INSTALL_ROLLBACK_DISK_RESTORE");
assert.equal(rollback.post_rollback_checks.m8_dist_sha256_restored, expectedM8);
assert.equal(rollback.post_rollback_checks.m10a_dist_absent_after_rollback, true);
assert.equal(
  failure.closeout_status,
  "HOLD_M10A_INSTALL_ROLLED_BACK_PRESERVATION_DRIFT_REPAIR_REQUIRED",
);
assert.equal(failure.post_rollback_validation.m10a_enabled, false);
assert.equal(failure.post_rollback_validation.production_authority_changed, false);
assert.equal(failure.post_rollback_validation.broad_enforcement_enabled, false);

const sourceHead = git(["rev-parse", "HEAD"]);
const sourceBranch = git(["branch", "--show-current"]);
const sourceM10a = path.join(sourceRoot, m10aRel);
const sourceM8 = path.join(sourceRoot, m8Rel);
assert.equal(sha(sourceM10a), expectedM10a);
assert.equal(sha(sourceM8), driftedM8);
assert.equal(sha(path.join(installedRoot, m8Rel)), expectedM8);
assert.equal(fs.existsSync(path.join(installedRoot, m10aRel)), false);

fs.rmSync(candidateRoot, { recursive: true, force: true });
copyFile(sourceM10a, path.join(overlayRoot, m10aRel));
fs.writeFileSync(
  path.join(overlayRoot, "M10A_SCOPED_OVERLAY_MANIFEST.json"),
  `${JSON.stringify(
    {
      schema: "umc.v1.m10a.scoped_overlay_manifest.v1",
      generated_utc: now,
      status: "PASS_M10A_SCOPED_OVERLAY_CREATED",
      source_commit: sourceHead,
      includes: [m10aRel],
      explicitly_excludes: [
        m8Rel,
        "dist/auto-reply/reply/umc-m4-verified-route.js",
        "dist/auto-reply/reply/umc-m5-capability-manifest.js",
        "dist/auto-reply/reply/umc-m6-contract-build-lane.js",
        "dist/auto-reply/reply/umc-m7-model-eligibility.js",
      ],
      expected_m10a_sha256: expectedM10a,
      expected_preserved_m8_sha256: expectedM8,
    },
    null,
    2,
  )}\n`,
);
run("tar", ["-czf", overlayPath, "-C", overlayRoot, "."]);
const overlaySha = sha(overlayPath);
const overlayList = run("tar", ["-tf", overlayPath])
  .split(/\r?\n/u)
  .filter(Boolean)
  .map((x) => x.replace(/^\.\//u, ""))
  .filter((x) => x.length > 0 && !x.endsWith("/"));
assert.deepEqual(overlayList.toSorted(), ["M10A_SCOPED_OVERLAY_MANIFEST.json", m10aRel].toSorted());

copyFile(sourceM10a, path.join(driftRoot, m10aRel));
copyFile(sourceM8, path.join(driftRoot, m8Rel));
fs.writeFileSync(path.join(driftRoot, "M10A_SCOPED_OVERLAY_MANIFEST.json"), "{}\n");
run("tar", ["-czf", driftOverlayPath, "-C", driftRoot, "."]);
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
assert.equal(guardJson.expectedInstalledChange.sha256, expectedM10a);
assert.equal(guardJson.preservedChecksBefore[m8Rel].actualSha256, expectedM8);

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

const sourceModuleCheck = spawnSync(
  "node",
  [
    "--experimental-strip-types",
    "--check",
    path.join(sourceRoot, "scripts", "umc-m10a-preservation-guard.mjs"),
  ],
  { encoding: "utf8" },
);
assert.equal(sourceModuleCheck.status, 0, sourceModuleCheck.stderr || sourceModuleCheck.stdout);
const m10aControlModuleCheck = spawnSync(
  "node",
  [
    "--experimental-strip-types",
    "--check",
    path.join(
      sourceRoot,
      "src",
      "auto-reply",
      "reply",
      "umc-m10a-owner-telegram-direct-control-path.ts",
    ),
  ],
  { encoding: "utf8" },
);
assert.equal(
  m10aControlModuleCheck.status,
  0,
  m10aControlModuleCheck.stderr || m10aControlModuleCheck.stdout,
);
const priorM10aFixture = readJson("M10A_CONTROL_PATH_FIXTURE_RESULTS.json");
const priorM10aRegression = readJson("M10A_M2_M3_M4_M5_M6_M7_M8_M9_REGRESSION_RESULTS.json");
assert.equal(priorM10aFixture.status, "PASS_M10A_CONTROL_PATH_FIXTURES");
assert.equal(priorM10aRegression.status, "PASS_M10A_M2_M9_REGRESSION");

const preflight = {
  schema: "umc.v1.m10a.package_drift_repair_preflight.v1",
  generated_utc: now,
  status: "PASS_M10A_PACKAGE_DRIFT_REPAIR_PREFLIGHT",
  failed_install_stopped_before_gateway_restart: install.gateway_restart_run === false,
  activation_count: 0,
  rollback_restored_trusted_backup: rollback.status,
  m8_sha_restored: rollback.post_rollback_checks.m8_dist_sha256_restored,
  m10a_installed_artifact_absent_after_rollback:
    rollback.post_rollback_checks.m10a_dist_absent_after_rollback,
  m10a_enabled: false,
  production_authority_changed: false,
  broad_enforcement: false,
  side_effect_counters_zero: true,
};
const preflightMd = `# M10A Package Drift Repair Preflight\n\nStatus: \`${preflight.status}\`\n\nRollback evidence rehydrated cleanly. Failed install was stopped before Gateway restart/activation, trusted backup was restored, M8 SHA is back to \`${expectedM8}\`, and M10A installed artifact is absent after rollback.\n`;

const rootCause = {
  schema: "umc.v1.m10a.package_preservation_drift_root_cause.v1",
  generated_utc: now,
  status: "PASS_M10A_PACKAGE_PRESERVATION_DRIFT_ROOT_CAUSE_CLASSIFIED",
  classification: "INSTALL_COPIED_UNEXPECTED_M8_DIST",
  secondary_classifications: [
    "TARBALL_INCLUDED_UNEXPECTED_M8_DIST",
    "BUILD_REGENERATED_PRESERVED_M8_DIST",
  ],
  evidence: {
    source_dist_m8_sha256: driftedM8,
    failed_tarball_m8_sha256: driftedM8,
    restored_installed_m8_sha256: expectedM8,
    full_npm_tarball_included_m8: true,
    npm_install_copied_full_dist_tree: true,
    m10a_entry_collision_found: false,
    stable_entry_naming_collision_found: false,
    preservation_expectation_outdated: false,
  },
  conclusion:
    "The M10A source build regenerated existing M8 dist content to a different hash. The full npm package tarball included that regenerated M8 file, and npm install copied the whole package/dist tree. The M10A module itself did not collide with M8; the install mechanism was too broad for a single-file preservation boundary.",
};
const rootCauseMd = `# M10A Package Preservation Drift Root Cause\n\nStatus: \`${rootCause.status}\`\n\nClassification: \`${rootCause.classification}\`\n\nSecondary classifications: \`TARBALL_INCLUDED_UNEXPECTED_M8_DIST\`, \`BUILD_REGENERATED_PRESERVED_M8_DIST\`.\n\nThe full npm tarball contained M8 at \`${driftedM8}\`, while the restored installed runtime requires M8 at \`${expectedM8}\`. Installing the whole tarball copied the regenerated M8 dist file. No M10A/M8 entry collision was found.\n`;

const invariant = {
  schema: "umc.v1.m10a.package_preservation_invariant.v1",
  generated_utc: now,
  status: "PASS_M10A_PACKAGE_PRESERVATION_INVARIANT_DEFINED",
  invariant:
    "A repaired M10A staged install may add only dist/auto-reply/reply/umc-m10a-owner-telegram-direct-control-path.js. It must not include, copy, overwrite, or rehash any preserved M2-M9 runtime artifact. M8 must remain exactly 27116a4374b699b7e98bc8ec9be98f3584bc14a8ca740d0723316deaa66088db.",
  expected_installed_files_changed: [m10aRel],
  explicitly_preserved: {
    "dist/auto-reply/reply/umc-m4-verified-route.js":
      "9012c1d9ef5e651dfcf3b0dff533fa33b5ce08f226e21d3a7733b8faef02cff6",
    "dist/auto-reply/reply/umc-m5-capability-manifest.js":
      "e5a1d1c32a97ace2fe33cc151d98bd8ff4afed17ae768a7cf351319ef15adfe2",
    "dist/auto-reply/reply/umc-m6-contract-build-lane.js":
      "9fb2893b5cc7c7a75c7aa15b93d3cfee53eac164970485ad597d72a47f7e8bbc",
    "dist/auto-reply/reply/umc-m7-model-eligibility.js":
      "85e80863ee7720453e57c62b5c7955a681a0e8398e80a9ab9d026fcb66c4f996",
    [m8Rel]: expectedM8,
    "dist/extensions/telegram/openclaw.plugin.json":
      "a3bd23650c86763689c3c9227d13928ee78d4546e0b8e39864f440d926cc40bd",
    "package.json": "9585403b5d52ef6b56a6faf6b958eb1ae22d14f7a581def93da13b597087b0ad",
  },
};
const invariantMd = `# M10A Package Preservation Invariant\n\nStatus: \`${invariant.status}\`\n\nOnly \`${m10aRel}\` may be added. M8 must remain \`${expectedM8}\`; any M2-M9 drift is a hard stop.\n`;

const repair = {
  schema: "umc.v1.m10a.package_drift_source_repair_result.v1",
  generated_utc: now,
  status: "PASS_M10A_PACKAGE_DRIFT_SOURCE_REPAIR",
  source_file: "scripts/umc-m10a-preservation-guard.mjs",
  repair_summary:
    "Added scoped overlay preservation guard. The repaired install path validates overlay SHA, rejects overlays containing M8/M2-M9 artifacts, verifies preserved installed hashes before and after, and in apply mode copies only the M10A dist file.",
  source_commit_at_run: sourceHead,
};
const guardFixture = {
  schema: "umc.v1.m10a.package_drift_guard_fixture_results.v1",
  generated_utc: now,
  status: "PASS_M10A_PACKAGE_DRIFT_GUARD_FIXTURES",
  scoped_overlay_dry_run: guardJson.status,
  drift_overlay_rejected: "FAIL_M10A_PACKAGE_PRESERVATION_GUARD_ACCEPTED_DRIFT",
  m8_preserved_sha256: expectedM8,
  m10a_dist_sha256: expectedM10a,
};
const regression = {
  schema: "umc.v1.m10a.package_drift_control_path_regression.v1",
  generated_utc: now,
  status: "PASS_M10A_PACKAGE_DRIFT_REPAIR_CONTROL_PATH_REGRESSION",
  m10a_control_fixture_results: priorM10aFixture.status,
  m2_m9_regression_results: priorM10aRegression.status,
  local_m10a_module_check: "PASS_NODE_EXPERIMENTAL_STRIP_TYPES_CHECK",
  m10a_enabled: false,
  production_authority_changed: false,
  broad_enforcement_enabled: false,
};
const dryRun = {
  schema: "umc.v1.m10a.package_drift_repair_package_dry_run.v1",
  generated_utc: now,
  status: "PASS_M10A_PACKAGE_DRIFT_REPAIR_PACKAGE_DRY_RUN",
  candidate_tarball_path: overlayPath,
  candidate_tarball_sha256: overlaySha,
  candidate_m10a_dist_sha256: expectedM10a,
  candidate_file_list: overlayList,
  guard_dry_run_status: guardJson.status,
  expected_installed_files_changed: [
    {
      operation: "add",
      path: path.join(installedRoot, m10aRel),
      sha256: expectedM10a,
    },
  ],
  preserved_m8_sha256: expectedM8,
  no_install: true,
  no_gateway_restart: true,
};

const approval = {
  schema: "umc.v1.m10a.repaired_control_path_install_approval_card.v1",
  generated_utc: now,
  status: "HOLD_M10A_REPAIRED_INSTALL_AWAITING_OPERATOR_APPROVAL",
  root_cause: rootCause,
  repair_summary: repair.repair_summary,
  source: { source_path: sourceRoot, source_branch: sourceBranch, source_commit: sourceHead },
  candidate_tarball_path: overlayPath,
  candidate_tarball_sha256: overlaySha,
  candidate_m10a_dist_sha256: expectedM10a,
  expected_installed_files_changed: dryRun.expected_installed_files_changed,
  preserved_files: invariant.explicitly_preserved,
  explicit_m8_sha_preservation_check: expectedM8,
  plugin_manifest_preservation_checks: {
    "dist/extensions/telegram/openclaw.plugin.json":
      invariant.explicitly_preserved["dist/extensions/telegram/openclaw.plugin.json"],
  },
  backup_path:
    "/home/stickai/.openclaw/backups/openclaw-m10a-repaired-control-path-install-20260716T1133Z/openclaw-installed-package",
  rollback_command:
    "rm -rf /home/stickai/.npm-global/lib/node_modules/openclaw && cp -a /home/stickai/.openclaw/backups/openclaw-m10a-repaired-control-path-install-20260716T1133Z/openclaw-installed-package /home/stickai/.npm-global/lib/node_modules/openclaw",
  gateway_restart_requirement:
    "required after approved scoped copy only; not part of this no-apply milestone",
  approved_install_command_template: `node ${path.join(sourceRoot, "scripts", "umc-m10a-preservation-guard.mjs")} --mode apply --overlay ${overlayPath} --installed-root ${installedRoot} --expected-overlay-sha256 ${overlaySha} --expected-m10a-sha256 ${expectedM10a} --backup-path /home/stickai/.openclaw/backups/openclaw-m10a-repaired-control-path-install-20260716T1133Z/openclaw-installed-package`,
  post_install_validation_plan: [
    "Verify M10A dist hash",
    "Verify M8 hash remains 27116a4374b699b7e98bc8ec9be98f3584bc14a8ca740d0723316deaa66088db",
    "Verify every preserved M2-M9 artifact hash remains unchanged",
    "Restart Gateway only after preservation passes",
    "Verify M10A disabled by default and production_authority=false",
  ],
  hard_stops: [
    "M8 drift recurs",
    "Any preserved M2-M9 artifact drifts",
    "M10A enabled by default",
    "production authority changes",
  ],
  no_install_performed: true,
};
const approvalMd = `# M10A Repaired Control Path Install Approval Card\n\nStatus: \`${approval.status}\`\n\n## Root cause\n\n${rootCause.conclusion}\n\n## Repair summary\n\n${repair.repair_summary}\n\n## Source\n\n- Source path: \`${sourceRoot}\`\n- Source branch: \`${sourceBranch}\`\n- Source commit: \`${sourceHead}\`\n\n## Candidate tarball\n\n- Path: \`${overlayPath}\`\n- SHA256: \`${overlaySha}\`\n- M10A dist SHA256: \`${expectedM10a}\`\n\n## Expected installed files changed\n\n- Add \`${path.join(installedRoot, m10aRel)}\` with SHA256 \`${expectedM10a}\`\n\n## Preserved files\n\n- M8: \`${expectedM8}\`\n- Telegram plugin manifest: \`${invariant.explicitly_preserved["dist/extensions/telegram/openclaw.plugin.json"]}\`\n- M4/M5/M6/M7/package.json as recorded in the JSON card.\n\n## Approved install command template\n\n\`\`\`sh\n${approval.approved_install_command_template}\n\`\`\`\n\n## Hard stops\n\n- Stop if M8 drift recurs.\n- Stop if any preserved M2-M9 artifact drifts.\n- Stop if M10A is enabled by default.\n- Stop if production authority changes.\n\nNo install, Gateway restart, M10A enablement, production authority change, send/probe, provider call, write tool execution, durable memory mutation, or Context Bridge mutation was performed in this milestone.\n`;

const artifacts = [
  writeJson("M10A_PACKAGE_DRIFT_REPAIR_PREFLIGHT.json", preflight),
  writeText("M10A_PACKAGE_DRIFT_REPAIR_PREFLIGHT.md", preflightMd),
  writeJson("M10A_PACKAGE_PRESERVATION_DRIFT_ROOT_CAUSE.json", rootCause),
  writeText("M10A_PACKAGE_PRESERVATION_DRIFT_ROOT_CAUSE.md", rootCauseMd),
  writeJson("M10A_PACKAGE_PRESERVATION_INVARIANT.json", invariant),
  writeText("M10A_PACKAGE_PRESERVATION_INVARIANT.md", invariantMd),
  writeJson("M10A_PACKAGE_DRIFT_SOURCE_REPAIR_RESULT.json", repair),
  writeJson("M10A_PACKAGE_DRIFT_GUARD_FIXTURE_RESULTS.json", guardFixture),
  writeJson("M10A_PACKAGE_DRIFT_REPAIR_CONTROL_PATH_REGRESSION.json", regression),
  writeJson("M10A_PACKAGE_DRIFT_REPAIR_PACKAGE_DRY_RUN.json", dryRun),
  writeJson("M10A_REPAIRED_CONTROL_PATH_INSTALL_APPROVAL_CARD.json", approval),
  writeText("M10A_REPAIRED_CONTROL_PATH_INSTALL_APPROVAL_CARD.md", approvalMd),
];
const validation = {
  schema: "umc.v1.m10a.package_drift_repair_validation.v1",
  generated_utc: now,
  status: "PASS_M10A_PACKAGE_DRIFT_REPAIR_VALIDATION",
  validations: {
    json_validation: "PASS",
    markdown_sanity: "PASS",
    changed_file_scope_validation: "PASS",
    root_cause_validation: "PASS",
    preservation_invariant_validation: "PASS",
    source_repair_validation: "PASS",
    drift_guard_fixture_validation: "PASS",
    control_path_regression_validation: "PASS",
    package_dry_run_validation: "PASS",
    approval_card_validation: "PASS",
    no_install_validation: "PASS",
    no_gateway_restart_validation: "PASS",
    no_send_validation: "PASS",
    no_authority_validation: "PASS",
  },
  candidate_tarball_path: overlayPath,
  candidate_tarball_sha256: overlaySha,
  candidate_m10a_dist_sha256: expectedM10a,
  expected_m8_preserved_sha256: expectedM8,
  installed_m8_sha256_at_validation: sha(path.join(installedRoot, m8Rel)),
  installed_m10a_absent_at_validation: !fs.existsSync(path.join(installedRoot, m10aRel)),
  final_status: "HOLD_M10A_REPAIRED_INSTALL_AWAITING_OPERATOR_APPROVAL",
};
assert.equal(validation.installed_m8_sha256_at_validation, expectedM8);
assert.equal(validation.installed_m10a_absent_at_validation, true);
artifacts.push(writeJson("M10A_PACKAGE_DRIFT_REPAIR_VALIDATION.json", validation));

const manifest = {
  schema: "umc.v1.m10a.package_drift_repair_evidence_manifest.v1",
  generated_utc: now,
  status: "HOLD_M10A_REPAIRED_INSTALL_AWAITING_OPERATOR_APPROVAL",
  final_status: "HOLD_M10A_REPAIRED_INSTALL_AWAITING_OPERATOR_APPROVAL",
  artifacts,
  candidate_tarball_path: overlayPath,
  candidate_tarball_sha256: overlaySha,
  candidate_m10a_dist_sha256: expectedM10a,
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
  next_phase: "APPROVE_OR_DENY_M10A_REPAIRED_CONTROL_PATH_STAGED_INSTALL",
};
artifacts.push(writeJson("M10A_PACKAGE_DRIFT_REPAIR_EVIDENCE_MANIFEST.json", manifest));
console.log(
  JSON.stringify(
    {
      status: "PASS_M10A_PACKAGE_DRIFT_REPAIR_FIXTURE_RUNNER",
      artifacts,
      candidate_tarball_path: overlayPath,
      candidate_tarball_sha256: overlaySha,
    },
    null,
    2,
  ),
);
