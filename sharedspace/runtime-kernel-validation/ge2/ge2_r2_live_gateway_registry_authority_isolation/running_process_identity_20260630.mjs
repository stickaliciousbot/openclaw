import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
const pid='285000';
const dir='/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r2_live_gateway_registry_authority_isolation';
function safe(fn){try{return fn()}catch(e){return {error:String(e.message||e)}}}
function sha(file){return safe(()=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'))}
const files=['/home/stickai/.npm-global/lib/node_modules/openclaw/dist/index.js','/home/stickai/.npm-global/lib/node_modules/openclaw/dist/server-methods-Dw6hzI_j.js','/home/stickai/.npm-global/lib/node_modules/openclaw/dist/commands-D2qp4St4.js','/home/stickai/.npm-global/lib/node_modules/openclaw/dist/types-CdFhLeaX.js','/home/stickai/.openclaw/extensions/ge2-command/index.mjs'];
const report={generatedAt:new Date().toISOString(), pid, proc:{cmdline:safe(()=>fs.readFileSync(`/proc/${pid}/cmdline`,'utf8').split('\0').filter(Boolean)), cwd:safe(()=>fs.readlinkSync(`/proc/${pid}/cwd`)), exe:safe(()=>fs.readlinkSync(`/proc/${pid}/exe`)), root:safe(()=>fs.readlinkSync(`/proc/${pid}/root`)), environ:safe(()=>Object.fromEntries(fs.readFileSync(`/proc/${pid}/environ`,'utf8').split('\0').filter(Boolean).map(x=>{const i=x.indexOf('='); return [x.slice(0,i), i>=0?x.slice(i+1):'']})))}, files:files.map(file=>({file, exists:fs.existsSync(file), realpath:safe(()=>fs.realpathSync(file)), sha256:fs.existsSync(file)?sha(file):null, size:fs.existsSync(file)?fs.statSync(file).size:null}))};
// redact env values except path-like keys useful for identity
if(report.proc.environ && !report.proc.environ.error){
  const keep={};
  for(const [k,v] of Object.entries(report.proc.environ)) if(['PATH','PWD','OPENCLAW_GATEWAY_PORT','NODE_ENV','HOME','USER'].includes(k)) keep[k]=v; else if(k.startsWith('OPENCLAW')) keep[k]='<redacted>';
  report.proc.environ=keep;
}
fs.writeFileSync(path.join(dir,'loaded_module_identity_report.json'), JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({pid, cmdline:report.proc.cmdline, cwd:report.proc.cwd, indexSha:report.files[0].sha256, commandsSha:report.files[2].sha256, typesSha:report.files[3].sha256},null,2));
