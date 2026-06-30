import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
const out = execFileSync('openclaw', ['gateway', 'call', 'commands.list', '--json'], {
  cwd: '/home/stickai/.openclaw/workspace',
  encoding: 'utf8',
  stdio: ['ignore', 'pipe', 'pipe'],
  timeout: 120000
});
fs.writeFileSync('/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r1_command_registry_visibility_repair/live_commands_list_after_patch_raw.json', out);
const j = JSON.parse(out);
const commands = j.commands || j.result?.commands || [];
const names = commands.map((c) => c.name).filter(Boolean);
const ge2 = commands.find((c) => c?.name === 'ge2' || c?.nativeName === 'ge2' || (Array.isArray(c?.textAliases) && c.textAliases.includes('/ge2')));
const report = {
  count: commands.length,
  ge2Present: Boolean(ge2),
  ge2: ge2 || null,
  pluginNames: commands.filter((c) => c.source === 'plugin').map((c) => c.name),
  fakePresent: names.includes('ge2-r1-fake-unregistered')
};
fs.writeFileSync('/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r1_command_registry_visibility_repair/live_command_list_check_20260630.json', JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));
