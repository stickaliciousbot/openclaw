#!/usr/bin/env node
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import {
  M10A_AGENT_ID,
  M10A_CHANNEL,
  M10A_CONTROL_ARTIFACT_PATH,
  M10A_OWNER_CHAT_ID,
  M10A_SCOPE_NAME,
  buildM10ADefaultControlState,
  readM10AStatus,
} from "../src/auto-reply/reply/umc-m10a-owner-telegram-direct-control-path.ts";

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

function loadState(controlPath) {
  if (!fs.existsSync(controlPath)) return buildM10ADefaultControlState();
  return buildM10ADefaultControlState(JSON.parse(fs.readFileSync(controlPath, "utf8")));
}

function emit(value, code = 0) {
  process.stdout.write(`${JSON.stringify(value, null, 2)}\n`);
  process.exit(code);
}

const PROBE_CHECKS = Object.freeze([
  "Gateway RPC OK",
  "Telegram ON/OK",
  "queue backlog 0",
  "context overflow 0",
  "context-overflow-diag 0",
  "M10A status/readback enabled only for owner Telegram direct scope",
  "owner chat id 8495203551 only",
  "production authority constrained to M10A scope",
  "broad enforcement false",
  "Web UI excluded",
  "LAN/browser excluded",
  "external sends blocked",
  "write tools blocked",
  "durable memory mutation blocked",
  "Context Bridge mutation blocked",
  "route/provider/fallback fingerprint stable except approved M10A flag",
  "M2-M9 receipts still valid",
  "missing receipt cannot pass",
  "raw provider/model bypass rejected",
  "off-switch command available",
  "rollback path available",
  "Telegram send/probe count 0 unless explicitly produced by normal owner conversation and classified",
  "external send count 0",
  "provider/model live call count unchanged except existing normal production response path if applicable",
  "runtime write-tool count 0",
  "memory mutation count 0",
  "Context Bridge mutation count 0",
]);

function main() {
  const args = parseArgs(process.argv.slice(2));
  const mode = args.mode ?? "dry-run";
  if (!["dry-run", "observe"].includes(mode)) throw new Error(`Unsupported --mode: ${mode}`);
  const durationMinutes = Number(args["duration-minutes"] ?? 30);
  const cadenceMinutes = Number(args["cadence-minutes"] ?? 5);
  const expectedProbes = Number(args["expected-probes"] ?? 6);
  const stateRoot = args["state-root"]
    ? path.resolve(args["state-root"])
    : path.join(os.homedir(), ".openclaw");
  const controlPath = args["control-path"]
    ? path.resolve(args["control-path"])
    : path.join(stateRoot, M10A_CONTROL_ARTIFACT_PATH);
  const readback = readM10AStatus(loadState(controlPath));
  const probes = Array.from({ length: expectedProbes }, (_, index) => ({
    probe_number: index + 1,
    scheduled_minute: index * cadenceMinutes,
    checks: PROBE_CHECKS,
  }));
  emit({
    schema: "umc.v1.m10a.post_enable_observation_command_result.v1",
    generated_utc: new Date().toISOString(),
    status:
      mode === "observe"
        ? "PASS_M10A_OBSERVATION_COMMAND_PLAN_READY"
        : "PASS_M10A_OBSERVATION_COMMAND_DRY_RUN",
    mode,
    duration_minutes: durationMinutes,
    cadence_minutes: cadenceMinutes,
    expected_probes: expectedProbes,
    hard_stop: true,
    scope_name: M10A_SCOPE_NAME,
    owner_chat_id: M10A_OWNER_CHAT_ID,
    channel: M10A_CHANNEL,
    agent_id: M10A_AGENT_ID,
    control_artifact_path: controlPath,
    current_readback: readback,
    probes,
    abort_statuses: {
      gateway_unhealthy: "FAIL_M10A_ABORT_GATEWAY_UNHEALTHY",
      telegram_unhealthy: "FAIL_M10A_ABORT_TELEGRAM_UNHEALTHY",
      context_overflow: "FAIL_M10A_ABORT_CONTEXT_OVERFLOW",
      scope_expansion: "FAIL_M10A_ABORT_SCOPE_EXPANSION",
      unexpected_send_or_mutation: "FAIL_M10A_ABORT_BOUNDARY_COUNTER_NONZERO",
      operator_stop: "HOLD_M10A_OPERATOR_STOP_REQUESTED",
    },
    telegram_send_probe_count: 0,
    external_send_count: 0,
    provider_model_live_call_count: 0,
    runtime_write_tool_execution_count: 0,
    durable_memory_mutation_count: 0,
    context_bridge_mutation_count: 0,
  });
}

try {
  main();
} catch (error) {
  emit(
    {
      schema: "umc.v1.m10a.post_enable_observation_command_result.v1",
      status: "FAIL_M10A_OBSERVATION_COMMAND_EXCEPTION",
      error: error instanceof Error ? error.message : String(error),
    },
    1,
  );
}
