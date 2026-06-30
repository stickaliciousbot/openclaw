import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import net from 'node:net';

const artifactDir = '/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan';
const cwd = '/home/stickai/.openclaw/workspace';
const loaderPath = '/home/stickai/.npm-global/lib/node_modules/openclaw/dist/loader-Bfm_uDYG.js';
const reverserPath = path.join(artifactDir, 'reverser_ge2_r7_lifecycle_20260630T0812Z.mjs');
const expectedRestoredSha = 'ff2d89b04d1d5f7fb727f586a78fe92e0b52ffbe43a484551475cf140b53feb0';
const r7PatchedSha = '43bc33fa3c706ce16c3fc395da640ed6ee9041361938b84a8e8ecbd92685df6b';
const oldPid = '303370';
const logPath = '/tmp/openclaw/openclaw-2026-06-30.log';

function shaFile(file) { return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'); }
function run(cmd, args, name, timeout=120000) {
  let stdout='', stderr='', ok=true, status=0;
  try { stdout = execFileSync(cmd, args, { cwd, encoding:'utf8', stdio:['ignore','pipe','pipe'], timeout }); }
  catch (e) { ok=false; status=e.status??1; stdout=e.stdout?.toString?.()??''; stderr=e.stderr?.toString?.()??String(e.message || e); }
  fs.writeFileSync(path.join(artifactDir, `${name}.stdout.txt`), stdout);
  fs.writeFileSync(path.join(artifactDir, `${name}.stderr.txt`), stderr);
  return { ok, status, stdout, stderr };
}
function extractPid(text) {
  const patterns = [/Runtime:\s*running\s*\(pid\s+(\d+)/i, /Runtime:.*?pid\s+(\d+)/i, /PID\s*[:=]?\s*(\d+)/i, /pid\D+(\d+)/i];
  for (const p of patterns) { const m = text.match(p); if (m) return m[1]; }
  return null;
}
function serviceState(text) {
  const lower = text.toLowerCase();
  if (/service is loaded but not running/.test(lower)) return 'not-running';
  if (/runtime:\s*running/i.test(text)) return 'running';
  if (/runtime:\s*stopped/i.test(text)) return 'stopped';
  if (/state\s+deactivating/i.test(text) || /deactivating/i.test(text)) return 'deactivating';
  if (/service:.*running/i.test(text)) return 'running';
  return 'unknown';
}
function runtimeState(text) {
  if (/Runtime:\s*running/i.test(text)) return 'running';
  if (/Runtime:\s*stopped/i.test(text)) return 'stopped';
  if (/deactivating/i.test(text)) return 'deactivating';
  return 'unknown';
}
function listenerState(text) {
  if (/Listening:\s*.+18789/i.test(text) || /Listening:.*\*:18789/i.test(text)) return 'present';
  if (/Connectivity probe:\s*ok/i.test(text)) return 'present-or-probed';
  return 'unknown';
}
function connectivity(text) { return /Connectivity probe:\s*ok/i.test(text) ? 'ok' : 'not-ok-or-unknown'; }
function admin(text) { return /Capability:\s*admin-capable/i.test(text) ? 'admin-capable' : 'not-admin-or-unknown'; }
function scanLogs(label) {
  let text = '';
  try { text = fs.readFileSync(logPath, 'utf8').split('\n').slice(-400).join('\n'); } catch {}
  const fatalLines = text.split('\n').filter(line => /fatal|missing module|cannot find module|mixed-runtime|ERR_MODULE_NOT_FOUND|SyntaxError|ReferenceError/i.test(line));
  const out = { logPath, scannedTailLines: 400, fatalLikeCount: fatalLines.length, fatalLikeLines: fatalLines.slice(-40) };
  fs.writeFileSync(path.join(artifactDir, `${label}_fatal_log_scan.json`), JSON.stringify(out, null, 2) + '\n');
  return out;
}
async function tcpProbe() {
  return new Promise(resolve => {
    const sock = net.createConnection({ host:'127.0.0.1', port:18789, timeout:3000 }, () => { sock.destroy(); resolve(true); });
    sock.on('error', () => resolve(false));
    sock.on('timeout', () => { sock.destroy(); resolve(false); });
  });
}
async function healthCheck(label, runStatus=true) {
  const statusRes = runStatus ? run('openclaw', ['gateway','status'], `${label}_gateway_status`, 120000) : { ok:false, status:0, stdout:'', stderr:'' };
  const combined = `${statusRes.stdout}\n${statusRes.stderr}`;
  const tcp = await tcpProbe();
  const logs = scanLogs(label);
  const pid = extractPid(combined);
  const result = {
    label,
    statusCommandOk: statusRes.ok,
    statusExit: statusRes.status,
    pid,
    serviceState: serviceState(combined),
    runtimeState: runtimeState(combined),
    listenerState: listenerState(combined),
    tcpListenerPresent: tcp,
    connectivityProbe: connectivity(combined),
    adminCapability: admin(combined),
    pidChangedSinceRestartRequest: pid ? pid !== oldPid : false,
    fatalLogScan: logs,
    rawStatusPath: path.join(artifactDir, `${label}_gateway_status.stdout.txt`)
  };
  result.pass = result.serviceState === 'running' && result.runtimeState === 'running' && (result.listenerState === 'present' || result.tcpListenerPresent) && result.connectivityProbe === 'ok' && result.adminCapability === 'admin-capable' && result.fatalLogScan.fatalLikeCount === 0 && Boolean(result.pid) && result.pidChangedSinceRestartRequest;
  return result;
}
function summarizeCommands(name, params) {
  const args = ['gateway','call','commands.list','--json'];
  if (params) args.push('--params', JSON.stringify(params));
  const res = run('openclaw', args, `bounded_${name}_commands_list`, 120000);
  let parsed = null; try { parsed = JSON.parse(res.stdout); } catch {}
  const commands = parsed?.result?.commands || parsed?.commands || [];
  const names = commands.map(c => c?.name).filter(Boolean);
  const ge2 = commands.filter(c => c?.name === 'ge2' || c?.nativeName === 'ge2' || (c?.textAliases || []).includes('/ge2'));
  return {
    name, ok: res.ok, parseOk: Boolean(parsed), count: commands.length,
    ge2Present: ge2.length > 0, ge2Count: ge2.length,
    existingCommandsPreserved: ['pair','dreaming','phone','voice'].every(n => names.includes(n)),
    fakePresent: names.includes('fake') || names.includes('fake-command') || commands.some(c => c?.nativeName === 'fake' || (c?.textAliases||[]).includes('/fake')),
    pluginNames: commands.filter(c => c.source === 'plugin').map(c => c.name),
    ge2
  };
}

const beforeSha = shaFile(loaderPath);
const recheck = await healthCheck('bounded_recheck', true); // exactly one bounded Gateway health/status re-check before any branch
let rollback = { performed:false };
let visibility = null;
let liveHelp = { run:false, reason:'not reached' };
let liveStatus = { run:false, reason:'not reached' };
let classification;

if (recheck.pass) {
  visibility = {
    default: summarizeCommands('default', null),
    telegram_both: summarizeCommands('telegram_both', { provider:'telegram', scope:'both' }),
    telegram_text: summarizeCommands('telegram_text', { provider:'telegram', scope:'text' })
  };
  const all = Object.values(visibility);
  const visibilityPass = all.every(r => r.ok && r.parseOk && r.ge2Present && r.ge2Count === 1 && r.existingCommandsPreserved && !r.fakePresent);
  if (visibilityPass) {
    classification = 'GE2_R7_COMMAND_REGISTRY_VISIBILITY_PASS_HELP_STATUS_PENDING';
    liveHelp = { run:false, reason:'bounded recovery stopped after visibility gate per operator close-loop; help/status not executed in this script' };
    liveStatus = { run:false, reason:liveHelp.reason };
  } else if (all.some(r => r.ge2Count > 1)) {
    classification = 'GE2_R7_DUPLICATE_GE2_COMMAND_ROLLBACK_REQUIRED_NOT_PERFORMED_IN_VISIBILITY_BRANCH';
  } else if (all.some(r => !r.existingCommandsPreserved)) {
    classification = 'GE2_R7_EXISTING_COMMANDS_REGRESSED_ROLLBACK_REQUIRED_NOT_PERFORMED_IN_VISIBILITY_BRANCH';
  } else {
    classification = 'GE2_R7_COMMANDS_LIST_STILL_MISSING_GE2_ROLLBACK_REQUIRED_NOT_PERFORMED_IN_VISIBILITY_BRANCH';
  }
} else {
  classification = 'GE2_R7_HEALTH_RECHECK_FAILED_ROLLBACK_REQUIRED';
  const restore = run('node', [reverserPath, 'loader'], 'bounded_rollback_reverser', 120000);
  const restoredSha = shaFile(loaderPath);
  const restart = run('openclaw', ['gateway','restart'], 'bounded_rollback_restart', 180000);
  const post = await healthCheck('bounded_rollback_health', true);
  rollback = {
    performed:true,
    restoreCommandOk: restore.ok,
    restoreExit: restore.status,
    restoredSha,
    restoredShaMatchesExpected: restoredSha === expectedRestoredSha,
    restartCommandOk: restart.ok,
    restartExit: restart.status,
    postHealth: post
  };
  classification = post.pass && restoredSha === expectedRestoredSha ? 'GE2_R7_HEALTH_RECHECK_FAILED_ROLLBACK_RESTORED' : 'GE2_R7_ROLLBACK_HEALTH_GATE_FAILED_OPERATOR_ESCALATION';
}
const report = {
  generatedAt: new Date().toISOString(),
  initialClassification: 'GE2_R7_POST_RESTART_HEALTH_HOLD_LIVE_GATES_NOT_RUN',
  finalClassification: classification,
  boundedRecheckResult: recheck,
  pidBefore: oldPid,
  pidAfterRecheck: recheck.pid,
  loaderShaBeforeProcedure: beforeSha,
  expectedPatchedSha: r7PatchedSha,
  rollbackPerformed: rollback.performed,
  rollback,
  liveGatesRun: Boolean(visibility),
  commandsListVisibility: visibility,
  liveGe2HelpResult: liveHelp,
  liveGe2StatusResult: liveStatus,
  constraintsHonored: {
    cronCloseoutApplyRetried:false,
    patchedAnotherFile:false,
    pluginManagerBridgePatched:false,
    liveCommandsListRunOnlyIfHealthClean:Boolean(visibility) === recheck.pass,
    liveGe2HelpStatusRun:false
  }
};
const reportPath = path.join(artifactDir, 'GE2_R7_BOUNDED_RECOVERY_VERIFY_REPORT_20260630.json');
fs.writeFileSync(reportPath, JSON.stringify(report, null, 2) + '\n');
const mdPath = path.join(artifactDir, 'GE2_R7_BOUNDED_RECOVERY_VERIFY_REPORT_20260630.md');
fs.writeFileSync(mdPath, `# GE2-R7 Bounded Recovery / Verification Report\n\nFinal classification: \`${classification}\`\n\n- PID before: ${oldPid}\n- PID after re-check: ${recheck.pid ?? 'unknown'}\n- service/runtime/listener: ${recheck.serviceState} / ${recheck.runtimeState} / ${recheck.listenerState} tcp=${recheck.tcpListenerPresent}\n- connectivity/admin: ${recheck.connectivityProbe} / ${recheck.adminCapability}\n- fatal scan count: ${recheck.fatalLogScan.fatalLikeCount}\n- rollback performed: ${rollback.performed ? 'yes' : 'no'}\n- restored SHA: ${rollback.restoredSha ?? 'n/a'}\n- live gates run: ${visibility ? 'yes' : 'no'}\n- /ge2 visible: ${visibility ? Object.values(visibility).map(v => `${v.name}:${v.ge2Present}/${v.ge2Count}`).join(', ') : 'not run'}\n\nReport JSON: ${reportPath}\n`);
console.log(JSON.stringify({ reportPath, mdPath, finalClassification: classification, recheck, rollbackPerformed: rollback.performed, restoredSha: rollback.restoredSha, liveGatesRun: Boolean(visibility), visibility }, null, 2));
process.exit(classification.includes('OPERATOR_ESCALATION') ? 2 : 0);
