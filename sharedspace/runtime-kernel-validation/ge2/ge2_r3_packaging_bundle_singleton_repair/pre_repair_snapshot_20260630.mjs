import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';
const dir='/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r3_packaging_bundle_singleton_repair';
fs.mkdirSync(dir,{recursive:true});
function sha(file){return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex')}
function copy(file){const name=file.replace(/^\//,'').replaceAll('/','__'); const dest=path.join(dir,'preimage__'+name); fs.copyFileSync(file,dest); return dest;}
function run(args, timeout=120000){try{return {ok:true,stdout:execFileSync('openclaw',args,{cwd:'/home/stickai/.openclaw/workspace',encoding:'utf8',stdio:['ignore','pipe','pipe'],timeout})}}catch(e){return{ok:false,status:e.status??null,stdout:e.stdout?.toString?.()??'',stderr:e.stderr?.toString?.()??String(e.message||e)}}}
const files=['/home/stickai/.npm-global/lib/node_modules/openclaw/dist/types-CdFhLeaX.js','/home/stickai/.openclaw/workspace/hooks/ge2-register/handler.js'];
const snapshots=files.map(file=>({file, exists:fs.existsSync(file), sha256:fs.existsSync(file)?sha(file):null, bytes:fs.existsSync(file)?fs.statSync(file).size:null, snapshotPath:fs.existsSync(file)?copy(file):null}));
const gatewayStatus=run(['gateway','status'],180000);
const commandsList=run(['gateway','call','commands.list','--json'],150000);
const pluginsList=run(['plugins','list','--json'],120000);
const r2Summary=JSON.parse(fs.readFileSync('/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r2_live_gateway_registry_authority_isolation/summary.json','utf8'));
const report={generatedAt:new Date().toISOString(), dir, r2Verified:r2Summary.classification==='GE2_R2_LIVE_GATEWAY_REGISTRY_AUTHORITY_ISOLATION_PASS_NO_APPLY', snapshots, gatewayStatus, commandsList, pluginsList, rollback:{mode:'restore preimage files then restart gateway', files:snapshots.map(s=>({target:s.file, preimage:s.snapshotPath, sha256:s.sha256}))}};
fs.writeFileSync(path.join(dir,'pre_repair_snapshot.json'),JSON.stringify(report,null,2)+'\n');
fs.writeFileSync(path.join(dir,'gateway_status_before.txt'),gatewayStatus.stdout||gatewayStatus.stderr||'');
fs.writeFileSync(path.join(dir,'commands_list_before.json'),commandsList.stdout||commandsList.stderr||'');
fs.writeFileSync(path.join(dir,'plugins_list_before.json'),pluginsList.stdout||pluginsList.stderr||'');
console.log(JSON.stringify({r2Verified:report.r2Verified, snapshots:snapshots.map(s=>({file:s.file,sha256:s.sha256,preimage:s.snapshotPath}))},null,2));
