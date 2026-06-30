import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
const variants = [
  { label: 'default', params: {} },
  { label: 'scope_text', params: { scope: 'text' } },
  { label: 'scope_both_provider_telegram', params: { scope: 'both', provider: 'telegram' } },
  { label: 'scope_text_provider_telegram', params: { scope: 'text', provider: 'telegram' } },
  { label: 'scope_native_provider_telegram', params: { scope: 'native', provider: 'telegram' } }
];
function call(params) {
  const args = ['gateway', 'call', 'commands.list', '--json'];
  if (Object.keys(params).length) args.push('--params', JSON.stringify(params));
  return execFileSync('openclaw', args, {
    cwd: '/home/stickai/.openclaw/workspace',
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
    timeout: 120000
  });
}
const reports = [];
for (const variant of variants) {
  const raw = call(variant.params);
  const j = JSON.parse(raw);
  const commands = j.commands || j.result?.commands || [];
  const ge2 = commands.find((c) => c?.name === 'ge2' || c?.nativeName === 'ge2' || (Array.isArray(c?.textAliases) && c.textAliases.includes('/ge2')));
  reports.push({
    label: variant.label,
    params: variant.params,
    count: commands.length,
    ge2Present: Boolean(ge2),
    ge2: ge2 || null,
    pluginEntries: commands.filter((c) => c.source === 'plugin').map((c) => ({ name: c.name, nativeName: c.nativeName, textAliases: c.textAliases, scope: c.scope }))
  });
}
fs.writeFileSync('/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r1_command_registry_visibility_repair/commands_list_surface_matrix_20260630.json', JSON.stringify(reports, null, 2));
console.log(JSON.stringify(reports, null, 2));
