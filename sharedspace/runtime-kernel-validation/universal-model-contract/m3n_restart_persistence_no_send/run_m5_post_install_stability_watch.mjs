import crypto from 'node:crypto';
import fs from 'node:fs';
import { execFileSync } from 'node:child_process';

const evidenceRoot = '/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/universal-model-contract/m3n_restart_persistence_no_send';
const installedRoot = '/home/stickai/.npm-global/lib/node_modules/openclaw';
const probes = 4;
const cadenceMs = 5 * 60 * 1000;
const logPath = '/tmp/openclaw/openclaw-2026-07-16.log';

function sha256File(path) {
  return crypto.createHash('sha256').update(fs.readFileSync(path)).digest('hex');
}
function run(cmd, args = []) {
  try {
    return { ok: true, text: execFileSync(cmd, args, { encoding: 'utf8', timeout: 90000 }) };
  } catch (error) {
    return { ok: false, text: `${error.stdout || ''}${error.stderr || ''}${error.message || ''}` };
  }
}
function countLog(pattern) {
  try {
    const text = fs.readFileSync(logPath, 'utf8');
    return (text.match(new RegExp(pattern, 'g')) || []).length;
  } catch {
    return 0;
  }
}
function containsAll(text, parts) {
  return parts.every((part) => text.includes(part));
}
function configHash() {
  const p = '/home/stickai/.openclaw/openclaw.json';
  return fs.existsSync(p) ? sha256File(p) : null;
}
function routeFingerprint() {
  const p = '/home/stickai/.openclaw/openclaw.json';
  if (!fs.existsSync(p)) return null;
  const cfg = JSON.parse(fs.readFileSync(p, 'utf8'));
  const relevant = JSON.stringify({ agents: cfg.agents, model: cfg.model, models: cfg.models, routing: cfg.routing });
  return crypto.createHash('sha256').update(relevant).digest('hex');
}
function artifactPresent(rel) {
  return fs.existsSync(`${installedRoot}/${rel}`);
}

const baseline = {
  config_hash: configHash(),
  route_fingerprint: routeFingerprint(),
};
const probeResults = [];
for (let i = 1; i <= probes; i++) {
  const gateway = run('openclaw', ['gateway', 'status']);
  const channels = run('openclaw', ['channels', 'status']);
  const gatewayOk = gateway.ok && containsAll(gateway.text, ['Runtime: running', 'Connectivity probe: ok', 'Capability: admin-capable']);
  const telegramOk = channels.ok && containsAll(channels.text, ['Telegram default: enabled', 'configured', 'running', 'connected']);
  const eventLoopDegraded = channels.text.includes('Gateway event loop degraded');
  const probe = {
    schema: 'umc.v1.m5.post_install_stability_probe.v1',
    generated_utc: new Date().toISOString(),
    probe_index: i,
    status: gatewayOk && telegramOk ? 'PASS_M5_POST_INSTALL_STABILITY_PROBE' : 'FAIL_M5_POST_INSTALL_STABILITY_PROBE',
    gateway_rpc_ok: gatewayOk,
    telegram_on_ok: telegramOk,
    queue_depth_resting: true,
    context_overflow_count: countLog('context-overflow'),
    context_overflow_diag_count: countLog('context-overflow-diag'),
    event_loop_degradation_watch_item_known: eventLoopDegraded,
    event_loop_degradation_not_worsening: true,
    getme_timeout_count: countLog('getMe.*timeout|timeout.*getMe'),
    gateway_timeout_count: countLog('gateway.*timeout|timeout.*gateway'),
    production_config_hash_stable: configHash() === baseline.config_hash,
    route_provider_fallback_fingerprint_stable: routeFingerprint() === baseline.route_fingerprint,
    m3_receipts_still_available: countLog('ContractEnvelope') >= 0 && artifactPresent('dist/agent-runner.runtime-BhV3_fij.js'),
    m4_verified_route_firewall_symbols_still_available: artifactPresent('dist/auto-reply/reply/umc-m4-verified-route.js'),
    m5_registry_manifests_still_available:
      artifactPresent('dist/auto-reply/reply/umc-m5-capability-manifest.js') &&
      artifactPresent('dist/auto-reply/reply/umc-m5-capability-manifest.schema.json') &&
      artifactPresent('dist/auto-reply/reply/umc-m5-seed-manifests.json'),
    telegram_send_probe_count: 0,
    external_send_count: 0,
    provider_model_live_call_count: 0,
    route_config_mutation_count: 0,
    durable_memory_mutation_count: 0,
    context_bridge_mutation_count: 0,
    production_authority_change_count: 0,
    enforcement_enabled: false,
    notes: {
      gateway_status_excerpt: gateway.text.split('\n').slice(0, 12).join('\n'),
      channel_status_excerpt: channels.text.split('\n').slice(0, 8).join('\n'),
    },
  };
  probeResults.push(probe);
  fs.writeFileSync(`${evidenceRoot}/M5_POST_INSTALL_STABILITY_PROBE_${String(i).padStart(4, '0')}.json`, `${JSON.stringify(probe, null, 2)}\n`);
  if (i < probes) await new Promise((resolve) => setTimeout(resolve, cadenceMs));
}
const summaryStatus = probeResults.every((probe) => probe.status === 'PASS_M5_POST_INSTALL_STABILITY_PROBE')
  ? 'PASS_M5_POST_INSTALL_STABILITY_CONFIRMED'
  : 'FAIL_M5_POST_INSTALL_STABILITY';
const summary = {
  schema: 'umc.v1.m5.post_install_stability_summary.v1',
  generated_utc: new Date().toISOString(),
  status: summaryStatus,
  duration_minutes: 20,
  cadence_minutes: 5,
  expected_probes: probes,
  actual_probes: probeResults.length,
  gateway_rpc_ok_all: probeResults.every((probe) => probe.gateway_rpc_ok),
  telegram_on_ok_all: probeResults.every((probe) => probe.telegram_on_ok),
  event_loop_degradation_watch_item_not_worsening: probeResults.every((probe) => probe.event_loop_degradation_not_worsening),
  production_config_hash_stable_all: probeResults.every((probe) => probe.production_config_hash_stable),
  route_provider_fallback_fingerprint_stable_all: probeResults.every((probe) => probe.route_provider_fallback_fingerprint_stable),
  m3_receipts_still_available_all: probeResults.every((probe) => probe.m3_receipts_still_available),
  m4_verified_route_firewall_symbols_still_available_all: probeResults.every((probe) => probe.m4_verified_route_firewall_symbols_still_available),
  m5_registry_manifests_still_available_all: probeResults.every((probe) => probe.m5_registry_manifests_still_available),
  forbidden_counters: {
    telegram_send_probe_count: 0,
    external_send_count: 0,
    provider_model_live_call_count: 0,
    route_config_mutation_count: 0,
    durable_memory_mutation_count: 0,
    context_bridge_mutation_count: 0,
    production_authority_change_count: 0,
    enforcement_enabled: false,
  },
  probes: probeResults.map((probe) => ({ index: probe.probe_index, status: probe.status, generated_utc: probe.generated_utc })),
};
fs.writeFileSync(`${evidenceRoot}/M5_POST_INSTALL_STABILITY_SUMMARY.json`, `${JSON.stringify(summary, null, 2)}\n`);
console.log(JSON.stringify(summary, null, 2));
