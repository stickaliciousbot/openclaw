import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
const raw = execFileSync('openclaw', ['plugins', 'list', '--json'], {
  cwd: '/home/stickai/.openclaw/workspace',
  encoding: 'utf8',
  stdio: ['ignore', 'pipe', 'pipe'],
  timeout: 120000
});
fs.writeFileSync('/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r1_command_registry_visibility_repair/plugins_list_raw_20260630.json', raw);
const data = JSON.parse(raw);
const plugins = data.plugins || data || [];
const ge2 = plugins.find((plugin) => plugin.id === 'ge2-command' || String(plugin.source || '').includes('ge2-command')) || null;
const commandPlugins = plugins.filter((plugin) => Array.isArray(plugin.commands) && plugin.commands.length).map((plugin) => ({ id: plugin.id, status: plugin.status, source: plugin.source, commands: plugin.commands, enabled: plugin.enabled, error: plugin.error || null }));
const report = { ge2, commandPlugins, diagnostics: data.diagnostics || [] };
fs.writeFileSync('/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r1_command_registry_visibility_repair/plugin_registry_extract_20260630.json', JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));
