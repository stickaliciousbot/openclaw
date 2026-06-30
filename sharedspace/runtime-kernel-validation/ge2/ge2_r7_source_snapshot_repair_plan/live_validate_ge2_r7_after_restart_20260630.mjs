import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const artifactDir = '/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan';
const cwd = '/home/stickai/.openclaw/workspace';
const loaderPath = '/home/stickai/.npm-global/lib/node_modules/openclaw/dist/loader-Bfm_uDYG.js';
const reverserPath = path.join(artifactDir, 'reverser_ge2_r7_lifecycle_20260630T0812Z.mjs');
function shaFile(file) { return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'); }
function runOpenClaw(args, name, timeout=120000) {
  let stdout='', stderr='', ok=true, status=0;
  try { stdout = execFileSync('openclaw', args, { cwd, encoding:'utf8', stdio:['ignore','pipe','pipe'], timeout }); }
  catch (e) { ok=false; status=e.status??1; stdout=e.stdout?.toString?.()??''; stderr=e.stderr?.toString?.()??String(e.message||e); }
  fs.writeFileSync(path.join(artifactDir, `${name}.stdout.txt`), stdout);
  fs.writeFileSync(path.join(artifactDir, `${name}.stderr.txt`), stderr);
  return { ok, status, stdout, stderr };
}
function extractPid(text) {
  const m = text.match(/PID\s*[:=]?\s*(\d+)/i) || text.match(/pid\D+(\d+)/i);
  return m?.[1] ?? null;
}
function commandNames(commands) { return commands.map(c => c?.name).filter(Boolean); }
function ge2Matches(c) { return c?.name === 'ge2' || c?.nativeName === 'ge2' || (c?.textAliases || []).includes('/ge2'); }
function summarizeCommands(name, params) {
  const args = ['gateway','call','commands.list','--json'];
  if (params) args.push('--params', JSON.stringify(params));
  const res = runOpenClaw(args, `live_commands_list_r7_${name}`);
  let parsed = null;
  try { parsed = JSON.parse(res.stdout); } catch {}
  const commands = parsed?.result?.commands || parsed?.commands || [];
  const names = commandNames(commands);
  const ge2 = commands.filter(ge2Matches);
  return {
    name, params: params ?? null, ok: res.ok, status: res.status,
    count: commands.length,
    ge2Present: ge2.length > 0,
    ge2Count: ge2.length,
    ge2,
    existingCommandsPreserved: ['pair','dreaming','phone','voice'].every(n => names.includes(n)),
    fakePresent: names.includes('fake') || names.includes('fake-command') || commands.some(c => c?.nativeName === 'fake' || (c?.textAliases||[]).includes('/fake')),
    pluginNames: commands.filter(c => c.source === 'plugin').map(c => c.name),
    parseOk: Boolean(parsed)
  };
}
function rollback(reason) {
  const rb = runOpenClaw(['gateway','status'], 'rollback_pre_status_capture', 120000);
  let restore = { ok:false, status:1, stdout:'', stderr:'not attempted' };
  try {
    restore = { ok:true, status:0, stdout: execFileSync('node', [reverserPath, 'loader'], { cwd, encoding:'utf8', stdio:['ignore','pipe','pipe'], timeout:120000 }), stderr:'' };
  } catch (e) {
    restore = { ok:false, status:e.status??1, stdout:e.stdout?.toString?.()??'', stderr:e.stderr?.toString?.()??String(e.message||e) };
  }
  fs.writeFileSync(path.join(artifactDir, 'rollback_restore.stdout.txt'), restore.stdout);
  fs.writeFileSync(path.join(artifactDir, 'rollback_restore.stderr.txt'), restore.stderr);
  const restart = runOpenClaw(['gateway','restart'], 'rollback_restart', 180000);
  const post = runOpenClaw(['gateway','status'], 'rollback_post_status', 120000);
  return { performed:true, reason, preStatusOk: rb.ok, restore, restart, postStatusOk: post.ok, postPid: extractPid(post.stdout + post.stderr), loaderSha256AfterRollback: shaFile(loaderPath) };
}
const previousPid = '303370';
const status = runOpenClaw(['gateway','status'], 'live_gateway_status_r7_after_restart');
const currentPid = extractPid(status.stdout + status.stderr);
const healthAdminOk = status.ok && /admin/i.test(status.stdout + status.stderr) && /(ok|healthy|running|listening|connected)/i.test(status.stdout + status.stderr);
const lists = [
  summarizeCommands('default'),
  summarizeCommands('telegram_both', { provider:'telegram', scope:'both' }),
  summarizeCommands('telegram_text', { provider:'telegram', scope:'text' })
];
const allListOk = lists.every(r => r.ok && r.parseOk && r.ge2Present && r.ge2Count === 1 && r.existingCommandsPreserved && !r.fakePresent);
let help = null, statusCmd = null;
if (healthAdminOk && allListOk) {
  // Live smoke uses gateway native command surface when available; if this environment lacks a direct native-command RPC, classify as not-run instead of spoofing.
  // We intentionally do not send Telegram/model-mediated /ge2 here.
  help = { run: false, reason: 'No non-model direct native-command RPC established in this script; commands.list visibility gate passed, help/status smoke remains pending.' };
  statusCmd = { run: false, reason: help.reason };
}
let rollbackResult = { performed:false };
let classification;
if (!healthAdminOk) {
  rollbackResult = rollback('Gateway health/admin failed after R7 restart');
  classification = 'GE2_R7_HEALTH_GATE_FAILED_ROLLBACK_RESTORED';
} else if (!lists.every(r => r.existingCommandsPreserved)) {
  rollbackResult = rollback('Existing commands regressed after R7 restart');
  classification = 'GE2_R7_EXISTING_COMMANDS_REGRESSED_ROLLBACK_RESTORED';
} else if (lists.some(r => r.fakePresent)) {
  rollbackResult = rollback('Fake command appeared after R7 restart');
  classification = 'GE2_R7_EXISTING_COMMANDS_REGRESSED_ROLLBACK_RESTORED';
} else if (lists.some(r => r.ge2Count > 1)) {
  rollbackResult = rollback('Duplicate /ge2 command appeared after R7 restart');
  classification = 'GE2_R7_DUPLICATE_GE2_COMMAND_ROLLBACK_RESTORED';
} else if (!lists.every(r => r.ge2Present)) {
  rollbackResult = rollback('/ge2 still absent after confirmed lifecycle target patch');
  classification = 'GE2_R7_COMMANDS_LIST_STILL_MISSING_GE2_ROLLBACK_RESTORED';
} else if (help?.run === false || statusCmd?.run === false) {
  classification = 'GE2_R7_COMMAND_REGISTRY_VISIBILITY_PASS_HELP_STATUS_PENDING';
} else {
  classification = 'GE2_R7_NATIVE_COMMAND_SURFACE_HELP_STATUS_PASS_RUN_PENDING';
}
const report = {
  generatedAt: new Date().toISOString(),
  classification,
  patchTargetTable: [
    { file:'types-CdFhLeaX.js', role:'registry storage/API', needsPatch:false },
    { file:'loader-Bfm_uDYG.js', role:'lifecycle clear/restore/register/cache/activate', needsPatch:true },
    { file:'server-methods-Dw6hzI_j.js', role:'commands.list handler', needsPatch:false },
    { file:'commands-D2qp4St4.js', role:'slash matcher/native handler', needsPatch:false }
  ],
  changedFiles: [loaderPath],
  installManifestPath: path.join(artifactDir, 'install_manifest_ge2_r7_lifecycle_20260630T0812Z.json'),
  reverserPath,
  beforeSha256: 'ff2d89b04d1d5f7fb727f586a78fe92e0b52ffbe43a484551475cf140b53feb0',
  afterSha256: '43bc33fa3c706ce16c3fc395da640ed6ee9041361938b84a8e8ecbd92685df6b',
  currentLoaderSha256: shaFile(loaderPath),
  localValidationResult: 'GE2_R7_LOCAL_REGISTRY_VALIDATION_PASS_RESTART_READY',
  oldGatewayPid: previousPid,
  newGatewayPid: currentPid,
  healthAdminResult: { ok: healthAdminOk, statusOk: status.ok, statusCode: status.status },
  commandsList: {
    default: lists[0],
    telegram_both: lists[1],
    telegram_text: lists[2]
  },
  existingCommandsPreserved: lists.every(r => r.existingCommandsPreserved),
  fakeCommandAbsent: lists.every(r => !r.fakePresent),
  duplicateGe2Count: Math.max(...lists.map(r => r.ge2Count)),
  liveGe2HelpResult: help,
  liveGe2StatusResult: statusCmd,
  rollbackPerformed: rollbackResult.performed,
  rollback: rollbackResult
};
const reportPath = path.join(artifactDir, 'GE2_R7_FINAL_REPORT_20260630.json');
fs.writeFileSync(reportPath, JSON.stringify(report, null, 2) + '\n');
const md = `# GE2-R7 Final Report\n\nClassification: \`${classification}\`\n\n- Changed files: ${report.changedFiles.join(', ')}\n- Install manifest: ${report.installManifestPath}\n- Reverser: ${report.reverserPath}\n- SHA: ${report.beforeSha256} -> ${report.afterSha256}\n- Local validation: ${report.localValidationResult}\n- Gateway PID: ${report.oldGatewayPid} -> ${report.newGatewayPid ?? 'unknown'}\n- Health/admin: ${healthAdminOk ? 'PASS' : 'FAIL'}\n- commands.list default: ge2=${lists[0].ge2Present} count=${lists[0].ge2Count} existing=${lists[0].existingCommandsPreserved} fake=${lists[0].fakePresent}\n- commands.list telegram/both: ge2=${lists[1].ge2Present} count=${lists[1].ge2Count} existing=${lists[1].existingCommandsPreserved} fake=${lists[1].fakePresent}\n- commands.list telegram/text: ge2=${lists[2].ge2Present} count=${lists[2].ge2Count} existing=${lists[2].existingCommandsPreserved} fake=${lists[2].fakePresent}\n- Duplicate /ge2 count max: ${report.duplicateGe2Count}\n- Live /ge2 help: ${help?.run === false ? 'not run — direct native RPC not established' : JSON.stringify(help)}\n- Live /ge2 status: ${statusCmd?.run === false ? 'not run — direct native RPC not established' : JSON.stringify(statusCmd)}\n- Rollback performed: ${rollbackResult.performed ? 'yes' : 'no'}\n`;
const mdPath = path.join(artifactDir, 'GE2_R7_FINAL_REPORT_20260630.md');
fs.writeFileSync(mdPath, md);
console.log(JSON.stringify({ reportPath, mdPath, classification, healthAdminOk, newGatewayPid: currentPid, lists, rollbackPerformed: rollbackResult.performed }, null, 2));
process.exit(rollbackResult.performed || !healthAdminOk || !allListOk ? (classification.includes('ROLLBACK') ? 2 : 1) : 0);
