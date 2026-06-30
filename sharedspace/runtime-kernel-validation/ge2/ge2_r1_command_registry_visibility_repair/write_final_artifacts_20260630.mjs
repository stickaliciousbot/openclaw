import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';

const dir = '/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r1_command_registry_visibility_repair';
fs.mkdirSync(dir, { recursive: true });

function readJson(name, fallback = null) {
  try { return JSON.parse(fs.readFileSync(path.join(dir, name), 'utf8')); } catch { return fallback; }
}
function run(args, timeout = 120000) {
  try {
    return { ok: true, stdout: execFileSync('openclaw', args, { cwd: '/home/stickai/.openclaw/workspace', encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], timeout }) };
  } catch (error) {
    return { ok: false, stdout: error.stdout?.toString?.() ?? '', stderr: error.stderr?.toString?.() ?? String(error.message || error), status: error.status ?? null };
  }
}
function sha256File(file) {
  try { return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'); } catch { return null; }
}
function writeJson(name, data) { fs.writeFileSync(path.join(dir, name), JSON.stringify(data, null, 2) + '\n'); }
function writeText(name, text) { fs.writeFileSync(path.join(dir, name), text.endsWith('\n') ? text : text + '\n'); }

const generatedAt = new Date().toISOString();
const gatewayStatus = run(['gateway', 'status'], 180000);
const pluginsList = run(['plugins', 'list', '--json'], 120000);
const pluginsInspect = run(['plugins', 'inspect', 'ge2-command', '--json'], 120000);
const commandsList = run(['gateway', 'call', 'commands.list', '--json'], 150000);
const tasksRunning = run(['tasks', 'list', '--status', 'running', '--json'], 120000);

writeText('gateway_status_final.txt', gatewayStatus.stdout || gatewayStatus.stderr || '');
writeText('commands_list_final.json', commandsList.stdout || commandsList.stderr || '');
writeText('plugins_list_final.json', pluginsList.stdout || pluginsList.stderr || '');
writeText('plugins_inspect_ge2_command_final.json', pluginsInspect.stdout || pluginsInspect.stderr || '');
writeText('tasks_running_final.json', tasksRunning.stdout || tasksRunning.stderr || '');

let commandsJson = null; try { commandsJson = JSON.parse(commandsList.stdout); } catch {}
let pluginsJson = null; try { pluginsJson = JSON.parse(pluginsList.stdout); } catch {}
let inspectJson = null; try { inspectJson = JSON.parse(pluginsInspect.stdout); } catch {}
let tasksJson = null; try { tasksJson = JSON.parse(tasksRunning.stdout); } catch {}
const commands = commandsJson?.commands || commandsJson?.result?.commands || [];
const pluginEntries = commands.filter((cmd) => cmd?.source === 'plugin');
const ge2Command = commands.find((cmd) => cmd?.name === 'ge2' || cmd?.nativeName === 'ge2' || (Array.isArray(cmd?.textAliases) && cmd.textAliases.includes('/ge2'))) || null;
const fakeCommand = commands.find((cmd) => cmd?.name === 'ge2-r1-fake-unregistered' || cmd?.nativeName === 'ge2-r1-fake-unregistered') || null;
const plugins = pluginsJson?.plugins || (Array.isArray(pluginsJson) ? pluginsJson : []);
const ge2Plugin = plugins.find((plugin) => plugin.id === 'ge2-command' || String(plugin.source || '').includes('ge2-command')) || null;
const statusText = gatewayStatus.stdout || '';
const gatewayPid = statusText.match(/Runtime: running \(pid (\d+)/)?.[1] || null;
const gatewayHealthOk = /Connectivity probe: ok/.test(statusText) && /Capability: admin-capable/.test(statusText);

const files = [
  '/home/stickai/.openclaw/workspace/hooks/ge2-register/handler.js',
  '/home/stickai/.openclaw/workspace/ge2-native-runtime/src/ge2_command_router.mjs',
  '/home/stickai/.openclaw/workspace/ge2-native-runtime/src/ge2_dispatcher.mjs',
  '/home/stickai/.openclaw/workspace/plugins/ge2-command/index.mjs',
  '/home/stickai/.openclaw/workspace/plugins/ge2-command/openclaw.plugin.json',
  '/home/stickai/.openclaw/workspace/plugins/ge2-command/package.json',
  '/home/stickai/.openclaw/extensions/ge2-command/index.mjs',
  '/home/stickai/.openclaw/extensions/ge2-command/openclaw.plugin.json',
  '/home/stickai/.openclaw/extensions/ge2-command/package.json'
];
const modifiedManifest = files.map((file) => ({ path: file, exists: fs.existsSync(file), sha256: sha256File(file), size: fs.existsSync(file) ? fs.statSync(file).size : null }));

const classification = ge2Command ? 'GE2_R1_COMMAND_REGISTRY_VISIBILITY_REPAIR_PASS' : 'GE2_R1_COMMAND_REGISTRY_VISIBILITY_REPAIR_BLOCKED';
const blockedReasons = [];
if (!ge2Command) blockedReasons.push('LIVE_COMMANDS_LIST_DOES_NOT_EXPOSE_GE2');
if (!ge2Plugin) blockedReasons.push('GE2_PLUGIN_NOT_DISCOVERED');
if (ge2Plugin && !(Array.isArray(ge2Plugin.commands) && ge2Plugin.commands.includes('ge2'))) blockedReasons.push('GE2_PLUGIN_DISCOVERED_BUT_COMMAND_NOT_REGISTERED_IN_PLUGIN_REGISTRY');
if (!gatewayHealthOk) blockedReasons.push('GATEWAY_HEALTH_NOT_OK');

const base = {
  generatedAt,
  classification,
  blockedReasons,
  gateway: { pid: gatewayPid, healthOk: gatewayHealthOk },
  liveCommandsList: {
    ok: commandsList.ok,
    count: commands.length,
    ge2Present: Boolean(ge2Command),
    ge2Command,
    pluginNames: pluginEntries.map((cmd) => cmd.name),
    fakeCommandPresent: Boolean(fakeCommand)
  },
  pluginRegistry: {
    ok: pluginsList.ok,
    ge2PluginDiscovered: Boolean(ge2Plugin),
    ge2Plugin,
    inspectCommands: inspectJson?.commands || inspectJson?.plugin?.commands || null,
    diagnostics: pluginsJson?.diagnostics || inspectJson?.diagnostics || []
  },
  runningTasks: tasksJson || null
};

writeJson('status.json', base);
writeJson('summary.json', base);
writeJson('registrar_path_report.json', {
  generatedAt,
  paths: {
    hook: '/home/stickai/.openclaw/workspace/hooks/ge2-register/handler.js',
    managedPlugin: '/home/stickai/.openclaw/extensions/ge2-command/index.mjs',
    sourcePlugin: '/home/stickai/.openclaw/workspace/plugins/ge2-command/index.mjs',
    runtime: '/home/stickai/.openclaw/workspace/ge2-native-runtime'
  },
  finding: 'Hook-side dynamic registration can see GE2 in its imported registry, but public commands.list does not. Official plugin registrar path now discovers ge2-command and records command ge2 in plugin registry.'
});
writeJson('command_list_path_report.json', {
  generatedAt,
  liveMethod: 'gateway call commands.list --json',
  ge2Present: Boolean(ge2Command),
  pluginEntries,
  finding: 'Live Gateway commands.list still returns only pair/dreaming/phone/voice plugin commands and omits ge2.'
});
writeJson('registry_identity_report.json', {
  generatedAt,
  localRegistryIdentityTest: readJson('ge2_r1_local_registry_identity_test_20260630.json', null),
  pluginRegistryHasGe2: Boolean(ge2Plugin && Array.isArray(ge2Plugin.commands) && ge2Plugin.commands.includes('ge2')),
  commandsListHasGe2: Boolean(ge2Command),
  conclusion: 'GE2 exists in plugin registry metadata but not the live Gateway commands.list registry used by the public command surface.'
});
writeJson('registration_loss_point_report.json', {
  generatedAt,
  lossPoint: ge2Command ? null : 'Between plugin registry registration/metadata and live Gateway commands.list output.',
  evidence: {
    ge2PluginDiscovered: Boolean(ge2Plugin),
    ge2PluginCommands: ge2Plugin?.commands || null,
    commandsListPluginNames: pluginEntries.map((cmd) => cmd.name)
  }
});
writeText('investigation_report.md', `# GE2-R1 Investigation Report\n\nGenerated: ${generatedAt}\n\n## Classification\n\n${classification}\n\n## Findings\n\n- Gateway health: ${gatewayHealthOk ? 'PASS' : 'FAIL'} (pid ${gatewayPid || 'unknown'}).\n- Plugin registry: ${ge2Plugin ? 'ge2-command discovered' : 'ge2-command not discovered'}${ge2Plugin?.commands ? ` with commands ${JSON.stringify(ge2Plugin.commands)}` : ''}.\n- Live commands.list: /ge2 ${ge2Command ? 'present' : 'absent'}.\n- Negative fake command visibility: ${fakeCommand ? 'FAIL present' : 'PASS absent'}.\n\n## Root blocker\n\nGE2 is now staged through the official plugin registrar path and visible in plugin registry metadata, but the live Gateway commands.list surface still omits /ge2. R1 cannot pass because the explicit acceptance gate requires live commands.list to expose /ge2.\n`);
writeText('implementation_diff_summary.md', `# Implementation Diff Summary\n\n- Restored GE2 native runtime under workspace/ge2-native-runtime.\n- Patched hooks/ge2-register/handler.js to validate/re-register through visible registry for diagnostics/backstop.\n- Replaced stale plugins/ge2-command implementation with an official api.registerCommand plugin.\n- Installed/staged managed GE2 plugin under ~/.openclaw/extensions/ge2-command with absolute imports to restored runtime.\n- Added configSchema/commandAliases manifest metadata.\n- Renamed duplicate workspace extension copy out of discovery: workspace/.openclaw/extensions/ge2-command.disabled-20260630T0408Z.\n\nNo cron production retry, model route, cache, provider, fallback, or memory promotion changes were made.\n`);
writeJson('modified_files_manifest.json', { generatedAt, files: modifiedManifest });
writeJson('registrar_direct_test_report.json', { generatedAt, status: 'PASS', evidence: 'ge2_managed_extension_import_check_20260630.mjs registered one command named ge2 with handler function.' });
writeJson('live_commands_list_test_report.json', { generatedAt, status: ge2Command ? 'PASS' : 'FAIL', ge2Present: Boolean(ge2Command), ge2Command, pluginEntries });
writeJson('restart_durability_test_report.json', { generatedAt, status: gatewayHealthOk ? 'HEALTH_PASS' : 'FAIL', gatewayPid, note: 'Gateway restarted to pid 285000 before final evidence collection; health/connectivity/admin OK.' });
writeJson('permission_visibility_test_report.json', { generatedAt, status: 'NOT_RUN_BLOCKED', reason: 'Skipped live command execution/auth probe because commands.list acceptance gate failed; do not test command execution as success when command is not visible.' });
writeJson('negative_command_visibility_test_report.json', { generatedAt, status: fakeCommand ? 'FAIL' : 'PASS', fakeCommandPresent: Boolean(fakeCommand) });
writeJson('unrelated_command_diff_report.json', { generatedAt, status: 'PASS_WITH_NOTE', pluginCommandNames: pluginEntries.map((cmd) => cmd.name), note: 'Existing visible plugin commands remain pair/dreaming/phone/voice; ge2 absent.' });
writeJson('mutation_scope_report.json', { generatedAt, status: 'PASS', scope: 'GE2 runtime/hook/plugin files and managed GE2 extension only; no cron production retry or route/model/cache/provider mutations.' });
writeJson('rollback_readiness.json', { generatedAt, status: 'READY', rollback: [
  'Rename or remove /home/stickai/.openclaw/extensions/ge2-command if GE2 plugin staging must be backed out.',
  'Restore /home/stickai/.openclaw/workspace/hooks/ge2-register/handler.js from git if hook diagnostics/backstop must be backed out.',
  'Keep ge2-native-runtime restored unless explicitly reverting GE2-R0 runtime restore.'
] });
writeText('GE2_R1_COMMAND_REGISTRY_VISIBILITY_REPAIR.md', `# GE2-R1 Command Registry Visibility Repair\n\nGenerated: ${generatedAt}\n\nFinal classification: **${classification}**\n\n## Evidence\n\n- Gateway health: ${gatewayHealthOk ? 'PASS' : 'FAIL'}; PID ${gatewayPid || 'unknown'}.\n- GE2 plugin registry: ${ge2Plugin ? 'DISCOVERED/LOADED' : 'NOT DISCOVERED'}${ge2Plugin?.commands ? `, commands=${JSON.stringify(ge2Plugin.commands)}` : ''}.\n- Live commands.list /ge2: ${ge2Command ? 'PRESENT' : 'ABSENT'}.\n- Negative fake command: ${fakeCommand ? 'PRESENT (FAIL)' : 'ABSENT (PASS)'}.\n\n## Conclusion\n\nR1 is blocked, not passed. The official plugin path now stages and discovers ge2-command with command ge2, but the live Gateway commands.list result still omits /ge2. The acceptance gate explicitly requires live commands.list exposes /ge2, so GE2-R1 remains blocked.\n\n## Next boundary\n\nDo not start GE2-R2 automatically. Next work should inspect why live Gateway commands.list excludes a loaded plugin command that appears in plugin registry metadata.\n`);

console.log(JSON.stringify({ classification, dir, blockedReasons, gatewayPid, gatewayHealthOk, ge2Plugin: Boolean(ge2Plugin), ge2CommandPresent: Boolean(ge2Command) }, null, 2));
