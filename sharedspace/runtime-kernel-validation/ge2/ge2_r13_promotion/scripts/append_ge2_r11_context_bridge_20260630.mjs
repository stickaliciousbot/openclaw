import fs from 'node:fs';
import crypto from 'node:crypto';

const eventsPath = 'sharedspace/context-bridge/events.jsonl';
const finalReport = 'sharedspace/runtime-kernel-validation/ge2/ge2_r11_real_inbound_gateway_smoke/GE2_R11_REAL_INBOUND_GATEWAY_TELEGRAM_WEBUI_PASS_PROMOTION_PENDING_20260630.md';
const memoryFinal = 'memory/2026-06-30-ge2-r11-final-pass.md';
const telegramLedger = 'state/ge2-native/runs/ge2-20260630101117-1fa6ed4d.json';
const webuiLedger = 'state/ge2-native/runs/ge2-20260630102318-ae4b5942.json';
const telegramArtifact = 'state/ge2-native/artifacts/ge2-20260630101117-1fa6ed4d/run-summary.json';
const webuiArtifact = 'state/ge2-native/artifacts/ge2-20260630102318-ae4b5942/run-summary.json';

function sha256(path) {
  return crypto.createHash('sha256').update(fs.readFileSync(path)).digest('hex');
}
function readJson(path) {
  return JSON.parse(fs.readFileSync(path, 'utf8'));
}
function maxContextVersion(lines) {
  let max = 0;
  for (const line of lines) {
    if (!line.trim()) continue;
    try {
      const parsed = JSON.parse(line);
      if (Number.isFinite(parsed.context_version)) max = Math.max(max, parsed.context_version);
    } catch {}
  }
  return max;
}

const lines = fs.existsSync(eventsPath) ? fs.readFileSync(eventsPath, 'utf8').split(/\n/).filter(Boolean) : [];
const eventId = 'evt-20260630T102500Z-ge2-r11-real-inbound-telegram-webui-pass';
if (lines.some((line) => {
  try { return JSON.parse(line).event_id === eventId; } catch { return false; }
})) {
  console.log(JSON.stringify({ ok: true, alreadyPresent: true, eventId }, null, 2));
  process.exit(0);
}

const telegramRun = readJson(telegramLedger);
const webuiRun = readJson(webuiLedger);
const event = {
  agent_id: 'main',
  channel: 'operator',
  context_version: maxContextVersion(lines) + 1,
  dedupe_key: 'dk-ge2-r11-real-inbound-telegram-webui-pass-20260630T1025Z',
  entity_id: 'ge2-native-command-surface-r11',
  event_id: eventId,
  event_type: 'ge2_r11_real_inbound_gateway_pass',
  memory_id: memoryFinal,
  payload: {
    final_classification: 'GE2_R11_REAL_INBOUND_GATEWAY_TELEGRAM_WEBUI_PASS_PROMOTION_PENDING',
    proof_level: 'P3',
    telegram: {
      status: 'PASS',
      run_id: telegramRun.run_id,
      task: telegramRun.task,
      run_status: telegramRun.status,
      origin: telegramRun.origin,
      milestones: telegramRun.milestones?.length ?? null,
      artifacts: telegramRun.artifacts?.length ?? null,
      errors: telegramRun.errors?.length ?? null,
      artifact_path: telegramRun.artifacts?.[0]?.path,
      artifact_sha256: telegramRun.artifacts?.[0]?.sha256,
      local_artifact_sha256: sha256(telegramArtifact)
    },
    webui: {
      status: 'PASS',
      run_id: webuiRun.run_id,
      task: webuiRun.task,
      run_status: webuiRun.status,
      origin: webuiRun.origin,
      milestones: webuiRun.milestones?.length ?? null,
      artifacts: webuiRun.artifacts?.length ?? null,
      errors: webuiRun.errors?.length ?? null,
      artifact_path: webuiRun.artifacts?.[0]?.path,
      artifact_sha256: webuiRun.artifacts?.[0]?.sha256,
      local_artifact_sha256: sha256(webuiArtifact)
    },
    gateway_health_after_webui_proof: {
      runtime: 'running pid 307081 active',
      connectivity: 'ok',
      capability: 'admin-capable',
      listening: '*:18789'
    },
    boundaries: {
      production_patch: false,
      gateway_restart: false,
      rollback: false,
      cron_closeout_apply: false,
      promotion: false,
      model_chat_fallthrough_observed: false
    },
    final_report_sha256: sha256(finalReport),
    memory_final_sha256: sha256(memoryFinal),
    next_state: 'GE2_R12_PROMOTION_READINESS_PACKET_PENDING',
    user_requested_context_bridge_write_at: '2026-06-30T10:27:00Z',
    requester_surface: 'openclaw-control-ui'
  },
  reducer_version: 1,
  source_refs: [
    finalReport,
    memoryFinal,
    telegramLedger,
    webuiLedger,
    telegramArtifact,
    webuiArtifact,
    'memory/2026-06-30-ge2-r11-telegram-p3-pass.md',
    'memory/2026-06-30-ge2-r11-telegram-run-accepted-addendum.md',
    'memory/2026-06-30-ge2-r11-telegram-p3-partial-addendum.md'
  ],
  status: 'PASS',
  summary: 'GE2 R11 real inbound Gateway command proof passed on both Telegram direct chat and OpenClaw WebUI/Control UI; R12 promotion-readiness packet is next, with no production patch/restart/rollback/cron apply/promotion performed.',
  ts: '2026-06-30T10:25:00Z'
};
fs.appendFileSync(eventsPath, JSON.stringify(event) + '\n');

let parsed = 0;
for (const [idx, line] of fs.readFileSync(eventsPath, 'utf8').split(/\n/).entries()) {
  if (!line.trim()) continue;
  try { JSON.parse(line); parsed += 1; }
  catch (error) { throw new Error(`events.jsonl parse failed at line ${idx + 1}: ${error.message}`); }
}
console.log(JSON.stringify({ ok: true, eventId, contextVersion: event.context_version, parsedEvents: parsed, finalReportSha256: event.payload.final_report_sha256 }, null, 2));
