#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import {
  M10A_AGENT_ID,
  M10A_CHANNEL,
  M10A_CONTROL_ARTIFACT_PATH,
  M10A_OWNER_CHAT_ID,
  M10A_ROLLBACK_KEY,
  M10A_SCOPE_NAME,
  applyM10AControlIntent,
  buildM10ADefaultControlState,
  disableM10AControlState,
  readM10AStatus,
} from "../src/auto-reply/reply/umc-m10a-owner-telegram-direct-control-path.ts";

const ACTIONS = new Set([
  "enable",
  "disable",
  "status",
  "verify-disabled",
  "verify-enabled-scope",
  "operator-stop",
  "rollback-if-disable-fails",
]);

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!arg.startsWith("--")) throw new Error(`Unexpected positional argument: ${arg}`);
    const key = arg.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) {
      args[key] = "true";
      continue;
    }
    args[key] = next;
    i += 1;
  }
  return args;
}

function sha256File(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

function resolveStateRoot(args) {
  if (args["state-root"]) return path.resolve(args["state-root"]);
  return path.join(os.homedir(), ".openclaw");
}

function controlPathForStateRoot(stateRoot) {
  return path.join(stateRoot, M10A_CONTROL_ARTIFACT_PATH);
}

function loadState(controlPath) {
  if (!fs.existsSync(controlPath)) return buildM10ADefaultControlState();
  const parsed = JSON.parse(fs.readFileSync(controlPath, "utf8"));
  return buildM10ADefaultControlState(parsed);
}

function writeStateAtomic(controlPath, state) {
  fs.mkdirSync(path.dirname(controlPath), { recursive: true });
  const tmp = `${controlPath}.tmp-${process.pid}`;
  fs.writeFileSync(tmp, `${JSON.stringify(state, null, 2)}\n`);
  fs.renameSync(tmp, controlPath);
}

function exactScopeArgs(args) {
  return {
    scope_name: args["scope-name"],
    owner_chat_id: args["owner-chat-id"],
    channel: args.channel,
    agent_id: args["agent-id"],
  };
}

function requireExactScope(args) {
  const scope = exactScopeArgs(args);
  const failures = [];
  if (scope.scope_name !== M10A_SCOPE_NAME) failures.push("scope-name");
  if (scope.owner_chat_id !== M10A_OWNER_CHAT_ID) failures.push("owner-chat-id");
  if (scope.channel !== M10A_CHANNEL) failures.push("channel");
  if (scope.agent_id !== M10A_AGENT_ID) failures.push("agent-id");
  if (failures.length > 0) {
    return {
      ok: false,
      status: "FAIL_M10A_COMMAND_SCOPE_MISMATCH",
      failures,
      required: {
        scope_name: M10A_SCOPE_NAME,
        owner_chat_id: M10A_OWNER_CHAT_ID,
        channel: M10A_CHANNEL,
        agent_id: M10A_AGENT_ID,
      },
      supplied: scope,
    };
  }
  return { ok: true, scope };
}

function emit(value, code = 0) {
  process.stdout.write(`${JSON.stringify(value, null, 2)}\n`);
  process.exit(code);
}

function resultBase({ action, mode, stateRoot, controlPath }) {
  return {
    schema: "umc.v1.m10a.owner_telegram_direct_control_command_result.v1",
    generated_utc: new Date().toISOString(),
    action,
    mode,
    state_root: stateRoot,
    control_artifact_path: controlPath,
    scope_name: M10A_SCOPE_NAME,
    owner_chat_id: M10A_OWNER_CHAT_ID,
    channel: M10A_CHANNEL,
    agent_id: M10A_AGENT_ID,
    rollback_key: M10A_ROLLBACK_KEY,
    production_authority_changed: false,
    broad_enforcement_enabled: false,
    telegram_send_probe_count: 0,
    external_send_count: 0,
    provider_model_live_call_count: 0,
    runtime_write_tool_execution_count: 0,
    durable_memory_mutation_count: 0,
    context_bridge_mutation_count: 0,
  };
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const action = args.action;
  const mode = args.mode ?? "dry-run";
  if (!ACTIONS.has(action)) throw new Error(`Unsupported --action: ${action}`);
  if (!["dry-run", "apply"].includes(mode)) throw new Error(`Unsupported --mode: ${mode}`);

  const stateRoot = resolveStateRoot(args);
  const controlPath = args["control-path"]
    ? path.resolve(args["control-path"])
    : controlPathForStateRoot(stateRoot);
  const current = loadState(controlPath);
  const base = resultBase({ action, mode, stateRoot, controlPath });
  const scopeCheck = ["enable", "verify-enabled-scope"].includes(action)
    ? requireExactScope(args)
    : null;
  if (scopeCheck && !scopeCheck.ok)
    emit({ ...base, ...scopeCheck, readback: readM10AStatus(current) }, 1);

  if (action === "status") {
    emit({
      ...base,
      status: "PASS_M10A_COMMAND_STATUS_READBACK",
      readback: readM10AStatus(current),
      control_artifact_exists: fs.existsSync(controlPath),
    });
  }

  if (action === "verify-disabled") {
    const readback = readM10AStatus(current);
    const ok =
      readback.enabled === false &&
      readback.production_authority === false &&
      readback.broad_enforcement === false;
    emit(
      {
        ...base,
        ok,
        status: ok ? "PASS_M10A_COMMAND_VERIFY_DISABLED" : "FAIL_M10A_COMMAND_VERIFY_DISABLED",
        readback,
      },
      ok ? 0 : 1,
    );
  }

  if (action === "verify-enabled-scope") {
    const readback = readM10AStatus(current);
    const ok =
      readback.enabled === true &&
      readback.scope_name === M10A_SCOPE_NAME &&
      readback.owner_chat_id === M10A_OWNER_CHAT_ID &&
      readback.channel === M10A_CHANNEL &&
      readback.agent_id === M10A_AGENT_ID &&
      readback.contract_decision_enforcement === true &&
      readback.production_authority === false &&
      readback.broad_enforcement === false;
    emit(
      {
        ...base,
        ok,
        status: ok
          ? "PASS_M10A_COMMAND_VERIFY_ENABLED_SCOPE"
          : "FAIL_M10A_COMMAND_VERIFY_ENABLED_SCOPE",
        readback,
      },
      ok ? 0 : 1,
    );
  }

  if (action === "enable") {
    const decision = applyM10AControlIntent(current, {
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
      requested_by: args["requested-by"] ?? "m10a_owner_operator_command",
      requested_at: args["requested-at"] ?? new Date().toISOString(),
      evidence_refs: args["evidence-ref"] ? [args["evidence-ref"]] : [],
    });
    if (!decision.ok) emit({ ...base, status: decision.status, decision }, 1);
    if (mode === "apply") writeStateAtomic(controlPath, decision.state);
    emit({
      ...base,
      status:
        mode === "apply" ? "PASS_M10A_COMMAND_ENABLE_APPLIED" : "PASS_M10A_COMMAND_ENABLE_DRY_RUN",
      applied: mode === "apply",
      decision,
      readback: decision.readback,
    });
  }

  if (action === "disable") {
    const decision = disableM10AControlState({
      state: current,
      disabled_by: args["requested-by"] ?? "m10a_owner_operator_command",
      disabled_at: args["requested-at"] ?? new Date().toISOString(),
      reason: "M10A disabled by exact owner Telegram direct off-switch command.",
    });
    if (mode === "apply") writeStateAtomic(controlPath, decision.state);
    emit({
      ...base,
      status:
        mode === "apply"
          ? "PASS_M10A_COMMAND_DISABLE_APPLIED"
          : "PASS_M10A_COMMAND_DISABLE_DRY_RUN",
      applied: mode === "apply",
      decision,
      readback: decision.readback,
    });
  }

  if (action === "operator-stop") {
    const decision = applyM10AControlIntent(current, {
      request: "disable",
      operator_stop_requested: true,
      requested_by: args["requested-by"] ?? "operator_stop",
      requested_at: args["requested-at"] ?? new Date().toISOString(),
    });
    const disabled = disableM10AControlState({
      state: current,
      disabled_by: args["requested-by"] ?? "operator_stop",
      disabled_at: args["requested-at"] ?? new Date().toISOString(),
      reason: "M10A disabled by exact operator stop command.",
    });
    if (mode === "apply") writeStateAtomic(controlPath, disabled.state);
    emit({
      ...base,
      status:
        mode === "apply"
          ? "PASS_M10A_COMMAND_OPERATOR_STOP_APPLIED"
          : "PASS_M10A_COMMAND_OPERATOR_STOP_DRY_RUN",
      applied: mode === "apply",
      decision,
      readback: disabled.readback,
    });
  }

  if (action === "rollback-if-disable-fails") {
    const readback = readM10AStatus(current);
    const backupPath = args["backup-path"] ? path.resolve(args["backup-path"]) : null;
    const installedRoot = args["installed-root"] ? path.resolve(args["installed-root"]) : null;
    const disableSucceeded =
      readback.enabled === false &&
      readback.production_authority === false &&
      readback.broad_enforcement === false;
    if (disableSucceeded)
      emit({ ...base, status: "PASS_M10A_COMMAND_ROLLBACK_NOT_REQUIRED", readback });
    if (!backupPath || !installedRoot)
      emit(
        {
          ...base,
          status: "FAIL_M10A_COMMAND_ROLLBACK_BACKUP_OR_TARGET_MISSING",
          readback,
          backup_path: backupPath,
          installed_root: installedRoot,
        },
        1,
      );
    if (mode === "apply") {
      if (args["confirm-rollback"] !== "M10A_ROLLBACK_IF_DISABLE_FAILS")
        emit({ ...base, status: "FAIL_M10A_COMMAND_ROLLBACK_CONFIRMATION_REQUIRED", readback }, 1);
      fs.cpSync(backupPath, installedRoot, {
        recursive: true,
        force: true,
        dereference: false,
        preserveTimestamps: true,
      });
    }
    emit({
      ...base,
      status:
        mode === "apply"
          ? "PASS_M10A_COMMAND_ROLLBACK_APPLIED"
          : "PASS_M10A_COMMAND_ROLLBACK_DRY_RUN",
      applied: mode === "apply",
      backup_path: backupPath,
      backup_sha256_marker: fs.existsSync(backupPath)
        ? sha256File(path.join(backupPath, "package.json"))
        : null,
      readback,
    });
  }
}

try {
  main();
} catch (error) {
  emit(
    {
      schema: "umc.v1.m10a.owner_telegram_direct_control_command_result.v1",
      status: "FAIL_M10A_COMMAND_SURFACE_EXCEPTION",
      error: error instanceof Error ? error.message : String(error),
    },
    1,
  );
}
