import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const dir = '/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r1_command_registry_visibility_repair';
fs.mkdirSync(dir, { recursive: true });

function run(label, command, args, options = {}) {
  const startedAt = new Date().toISOString();
  try {
    const stdout = execFileSync(command, args, {
      cwd: '/home/stickai/.openclaw/workspace',
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: options.timeout ?? 120000
    });
    return { label, ok: true, command: [command, ...args], startedAt, finishedAt: new Date().toISOString(), stdout };
  } catch (error) {
    return {
      label,
      ok: false,
      command: [command, ...args],
      startedAt,
      finishedAt: new Date().toISOString(),
      status: error.status ?? null,
      stdout: error.stdout?.toString?.() ?? '',
      stderr: error.stderr?.toString?.() ?? String(error.message || error)
    };
  }
}

const evidence = {};
evidence.gatewayStatus = run('gateway-status', 'openclaw', ['gateway', 'status'], { timeout: 180000 });
evidence.pluginsInspect = run('plugins-inspect-ge2-command', 'openclaw', ['plugins', 'inspect', 'ge2-command', '--json']);
evidence.pluginsList = run('plugins-list', 'openclaw', ['plugins', 'list', '--json']);
evidence.commandsList = run('commands-list', 'openclaw', ['gateway', 'call', 'commands.list', '--json']);
evidence.tasksRunning = run('tasks-running', 'openclaw', ['tasks', 'list', '--status', 'running', '--json']);

function parseJson(result) {
  try { return JSON.parse(result.stdout); } catch { return null; }
}

const commandsJson = parseJson(evidence.commandsList);
const commands = commandsJson?.commands || commandsJson?.result?.commands || [];
const ge2Command = commands.find((cmd) => cmd?.name === 'ge2' || cmd?.nativeName === 'ge2' || (Array.isArray(cmd?.textAliases) && cmd.textAliases.includes('/ge2'))) || null;
const pluginNames = commands.filter((cmd) => cmd?.source === 'plugin').map((cmd) => cmd.name);

const pluginsJson = parseJson(evidence.pluginsList);
const plugins = pluginsJson?.plugins || (Array.isArray(pluginsJson) ? pluginsJson : []);
const ge2Plugin = plugins.find((plugin) => plugin.id === 'ge2-command' || String(plugin.source || '').includes('ge2-command')) || null;
const commandPlugins = plugins
  .filter((plugin) => Array.isArray(plugin.commands) && plugin.commands.length)
  .map((plugin) => ({ id: plugin.id, status: plugin.status, source: plugin.source, enabled: plugin.enabled, commands: plugin.commands, error: plugin.error || null }));

const statusText = evidence.gatewayStatus.stdout || '';
const pidMatch = statusText.match(/Runtime: running \(pid (\d+)/);
const pid = pidMatch?.[1] || null;

const logPath = '/tmp/openclaw/openclaw-2026-06-30.log';
let restartLogTail = [];
try {
  const lines = fs.readFileSync(logPath, 'utf8').split(/\n/).filter(Boolean);
  restartLogTail = lines.filter((line) =>
    line.includes('GE2-R1 command registry visibility repair') ||
    line.includes('still draining 2 active task(s) and 1 active embedded run(s) before restart') ||
    line.includes('shutdown started: gateway restarting') ||
    line.includes('restart mode: full process restart') ||
    line.includes('loading configuration…') ||
    line.includes('drain timeout reached')
  ).slice(-120);
} catch (error) {
  restartLogTail = [`failed to read ${logPath}: ${error.message}`];
}

evidence.summary = {
  generatedAt: new Date().toISOString(),
  gatewayPid: pid,
  gatewayHealthOk: /Connectivity probe: ok/.test(statusText) && /Capability: admin-capable/.test(statusText),
  ge2PluginDiscovered: Boolean(ge2Plugin),
  ge2Plugin,
  commandPlugins,
  ge2CommandPresent: Boolean(ge2Command),
  ge2Command,
  publicPluginCommandNames: pluginNames,
  fakeCommandPresent: commands.some((cmd) => cmd?.name === 'ge2-r1-fake-unregistered'),
  restartBlocked: pid === '282797',
  restartLogTail
};

fs.writeFileSync(path.join(dir, 'final_evidence_20260630.json'), JSON.stringify(evidence, null, 2));
fs.writeFileSync(path.join(dir, 'gateway_status_final.txt'), evidence.gatewayStatus.stdout || evidence.gatewayStatus.stderr || '');
fs.writeFileSync(path.join(dir, 'plugins_inspect_ge2_command_final.json'), evidence.pluginsInspect.stdout || JSON.stringify(evidence.pluginsInspect, null, 2));
fs.writeFileSync(path.join(dir, 'plugins_list_final.json'), evidence.pluginsList.stdout || JSON.stringify(evidence.pluginsList, null, 2));
fs.writeFileSync(path.join(dir, 'commands_list_final.json'), evidence.commandsList.stdout || JSON.stringify(evidence.commandsList, null, 2));
fs.writeFileSync(path.join(dir, 'tasks_running_final.json'), evidence.tasksRunning.stdout || JSON.stringify(evidence.tasksRunning, null, 2));
fs.writeFileSync(path.join(dir, 'restart_log_tail_final.json'), JSON.stringify(restartLogTail, null, 2));
console.log(JSON.stringify(evidence.summary, null, 2));
