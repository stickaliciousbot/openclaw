#!/usr/bin/env node
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const sourceRoot = process.cwd();
const workspaceRoot = "/home/stickai/.openclaw/workspace";
const evidenceRoot =
  process.argv[2] ||
  path.join(
    workspaceRoot,
    "sharedspace/runtime-kernel-validation/universal-model-contract/m9_limited_live_action_canary",
  );
const now = process.env.M10A_COMMAND_SURFACE_NOW || "2026-07-16T13:08:00Z";
const controlScript = path.join(sourceRoot, "scripts", "m10a-owner-telegram-direct-control.mjs");
const observeScript = path.join(sourceRoot, "scripts", "m10a-owner-telegram-direct-observe.mjs");
fs.mkdirSync(evidenceRoot, { recursive: true });

function sha(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}
function writeJson(name, value) {
  const file = path.join(evidenceRoot, name);
  fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`);
  return { file: name, sha256: sha(file), status: value.status };
}
function runNode(script, args, options = {}) {
  const result = spawnSync(process.execPath, [script, ...args], {
    cwd: sourceRoot,
    encoding: "utf8",
    ...options,
  });
  let parsed = null;
  try {
    parsed = JSON.parse(result.stdout);
  } catch {}
  return { code: result.status, stdout: result.stdout, stderr: result.stderr, parsed };
}

const stateRoot = fs.mkdtempSync(path.join(os.tmpdir(), "m10a-command-fixture-"));
const exactScopeArgs = [
  "--scope-name",
  "M10A_OWNER_TELEGRAM_DIRECT_CONTRACT_ENFORCEMENT_ONLY",
  "--owner-chat-id",
  "8495203551",
  "--channel",
  "telegram_direct",
  "--agent-id",
  "main",
];
const cases = [];
function record(name, result, expectedStatus, expectedCode = 0) {
  assert.equal(result.code, expectedCode, `${name}: ${result.stderr || result.stdout}`);
  assert.ok(result.parsed, `${name}: missing JSON stdout`);
  assert.equal(result.parsed.status, expectedStatus, `${name}: ${result.stdout}`);
  cases.push({ name, code: result.code, status: result.parsed.status });
  return result.parsed;
}

record(
  "control_help",
  runNode(controlScript, ["--action", "help", "--mode", "dry-run", "--state-root", stateRoot]),
  "PASS_M10A_COMMAND_HELP",
);
record("observe_help", runNode(observeScript, ["--help"]), "PASS_M10A_OBSERVATION_COMMAND_HELP");
record(
  "status_default",
  runNode(controlScript, ["--action", "status", "--mode", "dry-run", "--state-root", stateRoot]),
  "PASS_M10A_COMMAND_STATUS_READBACK",
);
record(
  "verify_disabled_default",
  runNode(controlScript, [
    "--action",
    "verify-disabled",
    "--mode",
    "dry-run",
    "--state-root",
    stateRoot,
  ]),
  "PASS_M10A_COMMAND_VERIFY_DISABLED",
);
record(
  "enable_dry_run_exact",
  runNode(controlScript, [
    "--action",
    "enable",
    "--mode",
    "dry-run",
    "--state-root",
    stateRoot,
    ...exactScopeArgs,
  ]),
  "PASS_M10A_COMMAND_ENABLE_DRY_RUN",
);
record(
  "enable_reject_wrong_owner",
  runNode(controlScript, [
    "--action",
    "enable",
    "--mode",
    "dry-run",
    "--state-root",
    stateRoot,
    "--scope-name",
    "M10A_OWNER_TELEGRAM_DIRECT_CONTRACT_ENFORCEMENT_ONLY",
    "--owner-chat-id",
    "0000",
    "--channel",
    "telegram_direct",
    "--agent-id",
    "main",
  ]),
  "FAIL_M10A_COMMAND_SCOPE_MISMATCH",
  1,
);
record(
  "enable_apply_exact_temp_state",
  runNode(controlScript, [
    "--action",
    "enable",
    "--mode",
    "apply",
    "--state-root",
    stateRoot,
    ...exactScopeArgs,
  ]),
  "PASS_M10A_COMMAND_ENABLE_APPLIED",
);
record(
  "verify_enabled_scope",
  runNode(controlScript, [
    "--action",
    "verify-enabled-scope",
    "--mode",
    "dry-run",
    "--state-root",
    stateRoot,
    ...exactScopeArgs,
  ]),
  "PASS_M10A_COMMAND_VERIFY_ENABLED_SCOPE",
);
record(
  "disable_dry_run",
  runNode(controlScript, ["--action", "disable", "--mode", "dry-run", "--state-root", stateRoot]),
  "PASS_M10A_COMMAND_DISABLE_DRY_RUN",
);
record(
  "operator_stop_apply",
  runNode(controlScript, [
    "--action",
    "operator-stop",
    "--mode",
    "apply",
    "--state-root",
    stateRoot,
  ]),
  "PASS_M10A_COMMAND_OPERATOR_STOP_APPLIED",
);
record(
  "verify_disabled_after_stop",
  runNode(controlScript, [
    "--action",
    "verify-disabled",
    "--mode",
    "dry-run",
    "--state-root",
    stateRoot,
  ]),
  "PASS_M10A_COMMAND_VERIFY_DISABLED",
);
record(
  "rollback_not_required",
  runNode(controlScript, [
    "--action",
    "rollback-if-disable-fails",
    "--mode",
    "dry-run",
    "--state-root",
    stateRoot,
  ]),
  "PASS_M10A_COMMAND_ROLLBACK_NOT_REQUIRED",
);
record(
  "observation_dry_run",
  runNode(observeScript, [
    "--mode",
    "dry-run",
    "--state-root",
    stateRoot,
    "--duration-minutes",
    "30",
    "--cadence-minutes",
    "5",
    "--expected-probes",
    "6",
  ]),
  "PASS_M10A_OBSERVATION_COMMAND_DRY_RUN",
);

const result = {
  schema: "umc.v1.m10a.command_surface_fixture_results.v1",
  generated_utc: now,
  status: "PASS_M10A_COMMAND_SURFACE_FIXTURES",
  proof_level: "P1_SOURCE_SCRIPT_FIXTURE_ONLY_NOT_INSTALLED_NOT_LIVE_GATEWAY",
  source_scripts: [
    "scripts/m10a-owner-telegram-direct-control.mjs",
    "scripts/m10a-owner-telegram-direct-observe.mjs",
  ],
  temp_state_root: stateRoot,
  cases,
  no_production_enablement: true,
  no_gateway_restart: true,
  telegram_send_probe_count: 0,
  external_send_count: 0,
  provider_model_live_call_count: 0,
  runtime_write_tool_execution_count: 0,
  durable_memory_mutation_count: 0,
  context_bridge_mutation_count: 0,
};
const artifact = writeJson("M10A_COMMAND_SURFACE_FIXTURE_RESULTS.json", result);
console.log(JSON.stringify({ status: result.status, artifact }, null, 2));
