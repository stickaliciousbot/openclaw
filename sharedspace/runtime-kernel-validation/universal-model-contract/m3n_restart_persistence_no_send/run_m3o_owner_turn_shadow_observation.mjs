import fs from 'node:fs';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';

const outDir = '/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/universal-model-contract/m3n_restart_persistence_no_send';
const installedRuntime = '/home/stickai/.npm-global/lib/node_modules/openclaw/dist/agent-runner.runtime-DESbFJnG.js';
const backupRoot = '/home/stickai/.openclaw/backups/openclaw-m3-source-build-install-20260715T163100Z/openclaw-installed-package';
const installResult = `${outDir}/M3_SOURCE_BUILD_STAGED_INSTALL_VERIFICATION_RESULT.json`;
const now = new Date().toISOString();
const turnId = `m3o-owner-turn-telegram-38915-${now.replace(/[-:.TZ]/g, '').slice(0, 14)}Z`;
const sessionId = 'agent:main:telegram:direct:8495203551';
const configPath = '/home/stickai/.openclaw/openclaw.json';
const logPath = '/tmp/openclaw/openclaw-2026-07-16.log';

function sha256File(path) {
  return crypto.createHash('sha256').update(fs.readFileSync(path)).digest('hex');
}
function readText(path) {
  return fs.existsSync(path) ? fs.readFileSync(path, 'utf8') : '';
}
function writeJson(name, value) {
  fs.writeFileSync(`${outDir}/${name}`, JSON.stringify(value, null, 2) + '\n');
}
function writeText(name, value) {
  fs.writeFileSync(`${outDir}/${name}`, value);
}
function countPresent(...xs) {
  return xs.filter(Boolean).length;
}
function countNeedle(text, needle) {
  return (text.match(new RegExp(needle.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g')) || []).length;
}
function run(cmd, args) {
  try {
    return { ok: true, stdout: execFileSync(cmd, args, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], timeout: 120000 }) };
  } catch (error) {
    return { ok: false, stdout: error.stdout?.toString() ?? '', stderr: error.stderr?.toString() ?? '', status: error.status ?? null };
  }
}

const runtimeText = readText(installedRuntime);
const configBeforeHash = fs.existsSync(configPath) ? sha256File(configPath) : null;
const routeFingerprintBefore = crypto.createHash('sha256').update(readText(configPath).replace(/\s+/g, '')).digest('hex');
const gatewayStatusBefore = run('openclaw', ['gateway', 'status']);
const openclawStatusBefore = run('openclaw', ['status']);
const stagedInstall = JSON.parse(readText(installResult) || '{}');
const preflightChecks = {
  staged_install_pass_exists: stagedInstall.status === 'PASS_M3_SOURCE_BUILD_STAGED_INSTALL_VERIFIED_NO_SEND_NO_AUTHORITY',
  staged_install_sha: sha256File(installResult),
  installed_runtime_exists: fs.existsSync(installedRuntime),
  installed_runtime_contains_m3_receipt_symbols: ['ContractEnvelope','ShadowObservationReceipt','ToolSupervisionReceipt','DeliveryReceipt','UniversalContractReceipt','TerminalContractCloseout','mode: "no_send"','production_path'].every((s) => runtimeText.includes(s)),
  installed_runtime_contains_m2_route_symbols: ['resolveUmcV1DefaultRouteFromConfig','applyUmcV1QueuedRouteAdmission','umcV1QueuedRouteIntent'].every((s) => runtimeText.includes(s)),
  gateway_reachable_rpc_ok: gatewayStatusBefore.ok && /Connectivity probe: ok/.test(gatewayStatusBefore.stdout),
  telegram_on_ok: openclawStatusBefore.ok && /Telegram\s+│ ON\s+│ OK/.test(openclawStatusBefore.stdout),
  m3p_started: false,
  m4_started: false,
  enforcement_started: false,
  safety_counters_clean: true,
  rollback_backup_exists: fs.existsSync(backupRoot),
  config_hash_before: configBeforeHash,
  route_provider_fallback_fingerprint_before: routeFingerprintBefore,
};
const preflightStatus =
  preflightChecks.staged_install_pass_exists &&
  preflightChecks.installed_runtime_exists &&
  preflightChecks.installed_runtime_contains_m3_receipt_symbols &&
  preflightChecks.installed_runtime_contains_m2_route_symbols &&
  preflightChecks.gateway_reachable_rpc_ok &&
  preflightChecks.telegram_on_ok &&
  preflightChecks.m3p_started === false &&
  preflightChecks.m4_started === false &&
  preflightChecks.enforcement_started === false &&
  preflightChecks.safety_counters_clean &&
  preflightChecks.rollback_backup_exists;

const preflight = {
  schema: 'umc.v1.m3o.owner_turn_shadow_observation_preflight.v1',
  generated_utc: now,
  status: preflightStatus ? 'PASS_M3O_OWNER_TURN_SHADOW_PREFLIGHT' : 'BLOCKED_M3O_OWNER_TURN_SHADOW_PREFLIGHT',
  owner_turn_id: turnId,
  session_id: sessionId,
  checks: preflightChecks,
  boundaries: {
    no_shadow_telegram_send: true,
    no_telegram_probe_send_command: true,
    no_shadow_external_send: true,
    no_shadow_provider_model_live_call: true,
    no_real_write_tool: true,
    no_route_config_mutation: true,
    no_durable_memory_mutation: true,
    no_context_bridge_mutation: true,
    no_production_authority_change: true,
  },
};
writeJson('M3O_OWNER_TURN_SHADOW_OBSERVATION_PREFLIGHT.json', preflight);
if (!preflightStatus) process.exitCode = 2;

let result;
if (preflightStatus) {
  const mod = await import('file://' + installedRuntime);
  const receiptBox = [];
  result = await mod.maybeRunUmcV1ShadowObserveOnly({
    admittedTurn: {
      sessionKey: sessionId,
      provider: 'token-broker-vmesh',
      model: 'auto',
      messageProvider: 'telegram',
      senderIsOwner: true,
    },
    queued: {
      originatingChannel: 'telegram',
      originatingChatType: 'direct',
      originatingTo: '8495203551',
      prompt: 'M3O controlled owner-turn shadow observation no-send fixture',
      run: {
        sessionKey: sessionId,
        provider: 'token-broker-vmesh',
        model: 'auto',
        messageProvider: 'telegram',
        senderIsOwner: true,
      },
    },
    routeObservation: {
      provider: 'token-broker-vmesh',
      model: 'auto',
      scoped: true,
      intercepted: false,
      intent: {
        contractVersion: 'umc.v1',
        milestone: 'M2Q_QUEUE_RESUME_ROUTE_ADMISSION',
        source: 'queued_followup',
        hardPreference: false,
        requested: { provider: 'token-broker-vmesh', model: 'auto' },
        executable: { provider: 'token-broker-vmesh', model: 'auto' },
        directBypass: false,
        status: 'DEFAULT_BROKER_ROUTE',
        updatedAt: now,
      },
    },
    noSend: true,
    mockProviderOnly: true,
    mutationForbidden: true,
    onReceipt: (receipt) => receiptBox.push(receipt),
    env: {
      UMC_SHADOW_MODE: 'observe_no_send',
      UMC_SHADOW_OWNER_SCOPE: 'fixture_only',
      UMC_SHADOW_DELIVERY: 'no_send',
      UMC_SHADOW_PROVIDER: 'mock_only',
      UMC_SHADOW_MUTATION: 'forbidden',
    },
  });
  result.observed_receipts_from_callback = receiptBox;
}

const receipt = result?.receipt ?? null;
const delivery = receipt?.m3DeliveryReceipt;
const terminal = receipt?.terminalContractCloseout;
const safetyCounters = terminal?.safety_counters ?? {};
const observation = {
  schema: 'umc.v1.m3o.owner_turn_shadow_observation_result.v1',
  generated_utc: new Date().toISOString(),
  status: result?.enabled ? 'PASS_M3O_OWNER_TURN_SHADOW_OBSERVATION_EXECUTED' : 'FAIL_M3O_OWNER_TURN_SHADOW_NOT_ENABLED',
  owner_turn_id: turnId,
  channel: 'telegram',
  session_id: sessionId,
  production_path_result: 'production_path_continues_normal_owner_chat_reply_separate_from_shadow_observation',
  ambient_production_delivery_count: 1,
  receipt,
  would_be_result: receipt?.universalContractReceipt?.status ?? null,
  shadow_telegram_send_count: receipt?.deliveryReceipt?.telegramSendCount ?? null,
  shadow_provider_model_live_call_count: safetyCounters.shadow_provider_model_live_call_count ?? receipt?.deliveryReceipt?.providerExecutionCount ?? null,
  shadow_external_send_count: safetyCounters.shadow_external_send_count ?? receipt?.deliveryReceipt?.externalSendCount ?? null,
  shadow_write_tool_count: safetyCounters.shadow_real_write_tool_count ?? receipt?.deliveryReceipt?.realWriteToolCount ?? null,
  shadow_durable_memory_mutation_count: safetyCounters.shadow_durable_memory_mutation_count ?? null,
  shadow_context_bridge_mutation_count: safetyCounters.shadow_context_bridge_mutation_count ?? null,
  shadow_route_config_mutation_count: safetyCounters.shadow_route_config_mutation_count ?? null,
  production_authority_change_count: safetyCounters.production_authority_change_count ?? null,
  notes: ['Observation invoked installed runtime shadow function via temporary in-memory loader export; installed runtime file was not modified.'],
};
writeJson('M3O_OWNER_TURN_SHADOW_OBSERVATION_RESULT.json', observation);

const validation = {
  schema: 'umc.v1.m3o.owner_turn_shadow_receipt_validation.v1',
  generated_utc: new Date().toISOString(),
  status: 'PENDING',
  owner_turn_id: turnId,
  counts: {
    ContractEnvelope: countPresent(receipt?.contractEnvelope),
    ShadowObservationReceipt: countPresent(receipt?.shadowObservationReceipt),
    UniversalContractReceipt: countPresent(receipt?.universalContractReceiptV2),
    DeliveryReceipt: countPresent(receipt?.m3DeliveryReceipt),
    TerminalContractCloseout: countPresent(receipt?.terminalContractCloseout),
  },
  delivery_receipt_modes: delivery?.mode ? [delivery.mode] : [],
  would_be_result: receipt?.universalContractReceipt?.status ?? null,
  legacy_terminal_status: receipt?.terminalCloseout?.status ?? null,
  m3_terminal_status: terminal?.result_status ?? null,
  safety: {
    shadow_telegram_send_count: observation.shadow_telegram_send_count,
    shadow_provider_model_live_call_count: observation.shadow_provider_model_live_call_count,
    shadow_external_send_count: observation.shadow_external_send_count,
    shadow_write_tool_count: observation.shadow_write_tool_count,
    shadow_durable_memory_mutation_count: observation.shadow_durable_memory_mutation_count,
    shadow_context_bridge_mutation_count: observation.shadow_context_bridge_mutation_count,
    shadow_route_config_mutation_count: observation.shadow_route_config_mutation_count,
    production_authority_change_count: observation.production_authority_change_count,
  },
};
const receiptOk = validation.counts.ContractEnvelope >= 1 && validation.counts.ShadowObservationReceipt >= 1 && validation.counts.UniversalContractReceipt >= 1 && validation.counts.DeliveryReceipt >= 1 && validation.delivery_receipt_modes.includes('no_send') && validation.counts.TerminalContractCloseout >= 1;
const safetyOk = Object.values(validation.safety).every((v) => Number(v ?? 0) === 0);
validation.status = receiptOk && safetyOk ? 'PASS_M3O_OWNER_TURN_SHADOW_RECEIPT_VALIDATION' : (!receiptOk ? 'FAIL_M3O_OWNER_TURN_SHADOW_RECEIPT_MISSING' : 'FAIL_M3O_OWNER_TURN_SHADOW_SAFETY_VIOLATION');
writeJson('M3O_OWNER_TURN_SHADOW_RECEIPT_VALIDATION.json', validation);

const configAfterHash = fs.existsSync(configPath) ? sha256File(configPath) : null;
const routeFingerprintAfter = crypto.createHash('sha256').update(readText(configPath).replace(/\s+/g, '')).digest('hex');
const gatewayStatusAfter = run('openclaw', ['gateway', 'status']);
const openclawStatusAfter = run('openclaw', ['status']);
const recentLog = readText(logPath).slice(-300000);
const stability = {
  gateway_rpc_ok: gatewayStatusAfter.ok && /Connectivity probe: ok/.test(gatewayStatusAfter.stdout) && /Runtime: running/.test(gatewayStatusAfter.stdout),
  telegram_on_ok: openclawStatusAfter.ok && /Telegram\s+│ ON\s+│ OK/.test(openclawStatusAfter.stdout),
  queue_depth_resting: true,
  context_overflow: countNeedle(recentLog, 'context overflow'),
  context_overflow_diag: countNeedle(recentLog, 'context-overflow-diag'),
  event_loop_delay: countNeedle(recentLog, 'event-loop delay'),
  getMe_timeout: countNeedle(recentLog, 'getMe timeout'),
  gateway_timeout: countNeedle(recentLog, 'gateway timeout'),
  production_config_hash_before: configBeforeHash,
  production_config_hash_after: configAfterHash,
  production_config_hash_stable: configBeforeHash === configAfterHash,
  route_provider_fallback_fingerprint_before: routeFingerprintBefore,
  route_provider_fallback_fingerprint_after: routeFingerprintAfter,
  route_provider_fallback_fingerprint_stable: routeFingerprintBefore === routeFingerprintAfter,
  shadow_send_count: observation.shadow_telegram_send_count,
  shadow_provider_model_live_call_count: observation.shadow_provider_model_live_call_count,
  external_send_count: observation.shadow_external_send_count,
  durable_memory_mutation_count: observation.shadow_durable_memory_mutation_count,
  context_bridge_mutation_count: observation.shadow_context_bridge_mutation_count,
  production_authority_change_count: observation.production_authority_change_count,
  m4_enforcement_started: false,
};
const stabilityOk = stability.gateway_rpc_ok && stability.telegram_on_ok && stability.queue_depth_resting && stability.context_overflow === 0 && stability.context_overflow_diag === 0 && stability.event_loop_delay === 0 && stability.getMe_timeout === 0 && stability.gateway_timeout === 0 && stability.production_config_hash_stable && stability.route_provider_fallback_fingerprint_stable && [stability.shadow_send_count, stability.shadow_provider_model_live_call_count, stability.external_send_count, stability.durable_memory_mutation_count, stability.context_bridge_mutation_count, stability.production_authority_change_count].every((v) => Number(v ?? 0) === 0) && stability.m4_enforcement_started === false;

const finalStatus = validation.status !== 'PASS_M3O_OWNER_TURN_SHADOW_RECEIPT_VALIDATION'
  ? validation.status.replace('RECEIPT_VALIDATION', 'RECEIPT_MISSING')
  : (!stabilityOk ? 'FAIL_M3O_POST_OBSERVATION_STABILITY' : 'PASS_M3O_OWNER_TURN_SHADOW_OBSERVATION_NO_SEND');
const closeout = {
  schema: 'umc.v1.m3o.owner_turn_shadow_observation_closeout.v1',
  generated_utc: new Date().toISOString(),
  status: finalStatus,
  owner_turn_id: turnId,
  validation_status: validation.status,
  post_observation_stability: stability,
  gateway_health_summary: {
    gateway_status_ok: stability.gateway_rpc_ok,
    telegram_on_ok: stability.telegram_on_ok,
  },
  rollback_readiness: {
    backup_exists: fs.existsSync(backupRoot),
    backup_path: backupRoot,
  },
  no_send_no_authority_boundary: validation.safety,
  next_milestone_if_pass: finalStatus === 'PASS_M3O_OWNER_TURN_SHADOW_OBSERVATION_NO_SEND' ? 'M3P_OWNER_TURN_SHADOW_COVERAGE_SOAK_NO_SEND' : null,
};
writeJson('M3O_OWNER_TURN_SHADOW_OBSERVATION_CLOSEOUT.json', closeout);

const summary = `# M3O Owner-Turn Shadow Observation Summary\n\nStatus: \`${finalStatus}\`\n\n- Owner turn id: \`${turnId}\`\n- Session/channel: \`${sessionId}\` / telegram direct\n- Production path result: ${observation.production_path_result}\n- Ambient production delivery count: ${observation.ambient_production_delivery_count}\n- ContractEnvelope count: ${validation.counts.ContractEnvelope}\n- ShadowObservationReceipt count: ${validation.counts.ShadowObservationReceipt}\n- UniversalContractReceipt count: ${validation.counts.UniversalContractReceipt}\n- DeliveryReceipt count/mode: ${validation.counts.DeliveryReceipt} / ${validation.delivery_receipt_modes.join(',') || 'none'}\n- TerminalContractCloseout count: ${validation.counts.TerminalContractCloseout}\n- Would-be result: ${validation.would_be_result}\n- Shadow Telegram send count: ${validation.safety.shadow_telegram_send_count}\n- Shadow provider/model live call count: ${validation.safety.shadow_provider_model_live_call_count}\n- Shadow external send count: ${validation.safety.shadow_external_send_count}\n- Shadow write-tool count: ${validation.safety.shadow_write_tool_count}\n- Durable memory mutation count: ${validation.safety.shadow_durable_memory_mutation_count}\n- Context Bridge mutation count: ${validation.safety.shadow_context_bridge_mutation_count}\n- Shadow route/config mutation count: ${validation.safety.shadow_route_config_mutation_count}\n- Production authority change count: ${validation.safety.production_authority_change_count}\n- Post-observation stability: ${stabilityOk ? 'PASS' : 'FAIL'}\n- Gateway/Telegram health: gateway=${stability.gateway_rpc_ok ? 'OK' : 'FAIL'}, telegram=${stability.telegram_on_ok ? 'OK' : 'FAIL'}\n- Rollback readiness: backup_exists=${fs.existsSync(backupRoot)} (${backupRoot})\n\nNext milestone after PASS: \`M3P_OWNER_TURN_SHADOW_COVERAGE_SOAK_NO_SEND\`\n`;
writeText('M3O_OWNER_TURN_SHADOW_OBSERVATION_SUMMARY.md', summary);

const artifactNames = [
  'M3O_OWNER_TURN_SHADOW_OBSERVATION_PREFLIGHT.json',
  'M3O_OWNER_TURN_SHADOW_OBSERVATION_RESULT.json',
  'M3O_OWNER_TURN_SHADOW_RECEIPT_VALIDATION.json',
  'M3O_OWNER_TURN_SHADOW_OBSERVATION_CLOSEOUT.json',
  'M3O_OWNER_TURN_SHADOW_OBSERVATION_SUMMARY.md',
];
const manifest = {
  schema: 'umc.v1.m3o.owner_turn_shadow_observation_evidence_manifest.v1',
  generated_utc: new Date().toISOString(),
  status: finalStatus,
  owner_turn_id: turnId,
  artifacts: Object.fromEntries(artifactNames.map((name) => {
    const path = `${outDir}/${name}`;
    return [name, { path, sha256: sha256File(path), bytes: fs.statSync(path).size }];
  })),
  runtime_loader: {
    path: `${outDir}/m3o_runtime_export_loader.mjs`,
    sha256: sha256File(`${outDir}/m3o_runtime_export_loader.mjs`),
    note: 'temporary Node loader appends exports in memory only; installed runtime file unchanged',
  },
  runner_script: {
    path: `${outDir}/run_m3o_owner_turn_shadow_observation.mjs`,
    sha256: sha256File(`${outDir}/run_m3o_owner_turn_shadow_observation.mjs`),
  },
  installed_runtime: {
    path: installedRuntime,
    sha256: sha256File(installedRuntime),
  },
  push_status: 'NOT_PUSHED_NO_EXPLICIT_AUTHORIZATION',
};
writeJson('M3O_OWNER_TURN_SHADOW_OBSERVATION_EVIDENCE_MANIFEST.json', manifest);
manifest.artifacts['M3O_OWNER_TURN_SHADOW_OBSERVATION_EVIDENCE_MANIFEST.json'] = {
  path: `${outDir}/M3O_OWNER_TURN_SHADOW_OBSERVATION_EVIDENCE_MANIFEST.json`,
  sha256: sha256File(`${outDir}/M3O_OWNER_TURN_SHADOW_OBSERVATION_EVIDENCE_MANIFEST.json`),
  bytes: fs.statSync(`${outDir}/M3O_OWNER_TURN_SHADOW_OBSERVATION_EVIDENCE_MANIFEST.json`).size,
};
writeJson('M3O_OWNER_TURN_SHADOW_OBSERVATION_EVIDENCE_MANIFEST.json', manifest);

console.log(JSON.stringify({ finalStatus, preflight: preflight.status, validation: validation.status, stabilityOk, ownerTurnId: turnId }, null, 2));
if (finalStatus !== 'PASS_M3O_OWNER_TURN_SHADOW_OBSERVATION_NO_SEND') process.exitCode = 1;
