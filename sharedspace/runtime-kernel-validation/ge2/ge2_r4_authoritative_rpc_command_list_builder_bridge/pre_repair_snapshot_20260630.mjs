import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';
const dir='/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r4_authoritative_rpc_command_list_builder_bridge';
fs.mkdirSync(dir,{recursive:true});
function sha(file){return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex')}
function copy(file){const dest=path.join(dir,'preimage__'+file.replace(/^\//,'').replaceAll('/','__')); fs.copyFileSync(file,dest); return dest;}
function run(args, timeout=150000){try{return {ok:true,status:0,stdout:execFileSync('openclaw',args,{cwd:'/home/stickai/.openclaw/workspace',encoding:'utf8',stdio:['ignore','pipe','pipe'],timeout})}}catch(e){return{ok:false,status:e.status??null,stdout:e.stdout?.toString?.()??'',stderr:e.stderr?.toString?.()??String(e.message||e)}}}
const files=['/home/stickai/.npm-global/lib/node_modules/openclaw/dist/server-methods-Dw6hzI_j.js','/home/stickai/.npm-global/lib/node_modules/openclaw/dist/commands-D2qp4St4.js','/home/stickai/.npm-global/lib/node_modules/openclaw/dist/types-CdFhLeaX.js'];
const snapshots=files.map(file=>({file,sha256:sha(file),bytes:fs.statSync(file).size,snapshotPath:copy(file)}));
const gatewayStatus=run(['gateway','status'],120000);
const commandsList=run(['gateway','call','commands.list','--json'],150000);
const pluginsList=run(['plugins','list','--json'],120000);
const r3=JSON.parse(fs.readFileSync('/home/stickai/.openclaw/workspace/sharedspace/runtime-kernel-validation/ge2/ge2_r3_packaging_bundle_singleton_repair/final_blocked_summary.json','utf8'));
const report={generatedAt:new Date().toISOString(), classification:'GE2_R4_PRE_REPAIR_SNAPSHOT_READY', r3Verified:r3.classification==='GE2_R3_BLOCKED_LIVE_COMMANDS_LIST_OMITS_GE2_AFTER_SINGLETON_AND_EFFECTIVE_REGISTRY_BRIDGE'&&r3.pass===false, snapshots, gatewayStatus:{ok:gatewayStatus.ok,status:gatewayStatus.status,stdout:gatewayStatus.stdout,stderr:gatewayStatus.stderr}, commandsList:{ok:commandsList.ok,status:commandsList.status,stdout:commandsList.stdout,stderr:commandsList.stderr}, pluginsList:{ok:pluginsList.ok,status:pluginsList.status,stdout:pluginsList.stdout,stderr:pluginsList.stderr}, rollback:{mode:'restore preimage files then restart gateway',files:snapshots.map(s=>({target:s.file,preimage:s.snapshotPath,sha256:s.sha256}))}};
fs.writeFileSync(path.join(dir,'pre_repair_snapshot.json'),JSON.stringify(report,null,2)+'\n');
fs.writeFileSync(path.join(dir,'gateway_status_before.txt'),gatewayStatus.stdout||gatewayStatus.stderr||'');
fs.writeFileSync(path.join(dir,'commands_list_before.json'),commandsList.stdout||commandsList.stderr||'');
fs.writeFileSync(path.join(dir,'plugins_list_before.json'),pluginsList.stdout||pluginsList.stderr||'');
console.log(JSON.stringify({r3Verified:report.r3Verified,snapshots:snapshots.map(s=>({file:s.file,sha256:s.sha256,preimage:s.snapshotPath}))},null,2));
