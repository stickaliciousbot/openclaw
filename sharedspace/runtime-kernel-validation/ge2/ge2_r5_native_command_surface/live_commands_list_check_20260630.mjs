import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
const dir='/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r5_native_command_surface';
function call(name, params){
  const args=['gateway','call','commands.list','--json'];
  if(params) args.push('--params', JSON.stringify(params));
  let stdout='', stderr='', ok=true, status=0;
  try{stdout=execFileSync('openclaw',args,{encoding:'utf8',cwd:'/home/stickai/.openclaw/workspace',stdio:['ignore','pipe','pipe'],timeout:120000});}
  catch(e){ok=false;status=e.status??1;stdout=e.stdout?.toString?.()??'';stderr=e.stderr?.toString?.()??String(e.message||e)}
  fs.writeFileSync(`${dir}/commands_list_r5_${name}.raw`, stdout || stderr);
  let parsed=null; try{parsed=JSON.parse(stdout)}catch{}
  const commands=parsed?.result?.commands||parsed?.commands||[];
  const names=commands.map(c=>c.name);
  const ge2=commands.find(c=>c.name==='ge2'||c.nativeName==='ge2'||(c.textAliases||[]).includes('/ge2'))||null;
  return {name, ok, status, count:commands.length, ge2Present:Boolean(ge2), ge2, fakePresent:names.includes('fake')||names.includes('fake-command'), pluginNames:commands.filter(c=>c.source==='plugin').map(c=>c.name)};
}
const results=[call('default'),call('telegram_both',{provider:'telegram',scope:'both'}),call('telegram_text',{provider:'telegram',scope:'text'})];
const summary={generatedAt:new Date().toISOString(), results};
fs.writeFileSync(`${dir}/commands_list_r5_summary.json`, JSON.stringify(summary,null,2)+'\n');
console.log(JSON.stringify(summary,null,2));
