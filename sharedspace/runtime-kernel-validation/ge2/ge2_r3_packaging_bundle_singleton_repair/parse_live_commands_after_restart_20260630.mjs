import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
const dir = '/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r3_packaging_bundle_singleton_repair';
function run(args) {
  try { return { ok:true, stdout: execFileSync('openclaw', args, { cwd:'/home/stickai/.openclaw/workspace', encoding:'utf8', timeout:150000 }) }; }
  catch (e) { return { ok:false, status:e.status??null, stdout:e.stdout?.toString?.()??'', stderr:e.stderr?.toString?.()??String(e.message||e) }; }
}
const cases = [
  { name:'default', args:['gateway','call','commands.list','--json'] },
  { name:'telegram_both', args:['gateway','call','commands.list','--json','--params','{"provider":"telegram","scope":"both"}'] },
  { name:'telegram_text', args:['gateway','call','commands.list','--json','--params','{"provider":"telegram","scope":"text"}'] }
];
const results = [];
for (const c of cases) {
  const res = run(c.args);
  fs.writeFileSync(`${dir}/commands_list_after_restart_${c.name}.raw`, res.stdout || res.stderr || '');
  let parsed = null;
  try { parsed = JSON.parse(res.stdout); } catch {}
  const arr = Array.isArray(parsed) ? parsed : (parsed?.commands || []);
  results.push({ name:c.name, ok:res.ok, status:res.status??0, count:arr.length, ge2Present:arr.some(x=>x?.name==='ge2'||x?.nativeName==='ge2'||(x?.textAliases||[]).includes('/ge2')), fakePresent:arr.some(x=>String(x?.name||'').includes('fake')||String(x?.nativeName||'').includes('fake')), pluginNames:arr.filter(x=>x?.source==='plugin').map(x=>x.name), pluginEntries:arr.filter(x=>x?.source==='plugin') });
}
fs.writeFileSync(`${dir}/commands_list_after_restart_summary.json`, JSON.stringify({ generatedAt:new Date().toISOString(), results }, null, 2)+'\n');
console.log(JSON.stringify({ generatedAt:new Date().toISOString(), results: results.map(r=>({ name:r.name, ok:r.ok, count:r.count, ge2Present:r.ge2Present, fakePresent:r.fakePresent, pluginNames:r.pluginNames })) }, null, 2));
