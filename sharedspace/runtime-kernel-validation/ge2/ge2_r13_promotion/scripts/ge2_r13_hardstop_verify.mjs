import fs from 'node:fs';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';

const outDir='sharedspace/runtime-kernel-validation/ge2/ge2_r13_promotion';
fs.mkdirSync(outDir,{recursive:true});
const required={
  r12Packet:'sharedspace/runtime-kernel-validation/ge2/ge2_r12_promotion_readiness_packet/GE2_R12_PROMOTION_READINESS_PACKET_READY_20260630.md',
  evidenceManifest:'sharedspace/runtime-kernel-validation/ge2/ge2_r12_promotion_readiness_packet/r12_evidence.json',
  restoreChecklist:'sharedspace/runtime-kernel-validation/ge2/ge2_r12_promotion_readiness_packet/restore-checklist.md',
  r12DrBundle:'sharedspace/disaster-recovery/ge2-r12-promotion-readiness-20260630/ge2-r12-promotion-readiness-20260630.tar.gz',
  noSecretsScan:'sharedspace/runtime-kernel-validation/ge2/ge2_r12_promotion_readiness_packet/NO_SECRETS_SCAN.json',
  promotionRecord:'sharedspace/runtime-kernel-validation/ge2/ge2_r13_promotion/GE2_NATIVE_COMMAND_SURFACE_PROMOTED_20260630.md',
  r13BundleSummary:'sharedspace/disaster-recovery/ge2-r13-promotion-20260630/bundle-summary.json',
  r13Bundle:'sharedspace/disaster-recovery/ge2-r13-promotion-20260630/ge2-r13-promotion-20260630.tar.gz'
};
const expectedR12DrSha='474408c1ad4c4850ed21ded2c2231fc1e1e668fc4a4995d29a594e1b1c915c2d';
function sha(p){return crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');}
function sh(cmd,args){return execFileSync(cmd,args,{encoding:'utf8',maxBuffer:25*1024*1024});}
function call(method,params){return JSON.parse(sh('openclaw',['gateway','call',method,'--json','--params',JSON.stringify(params)]));}
function commands(provider){
 const data=call('commands.list',{provider,scope:'text'}); const list=data.commands||[];
 const ge2=list.filter(c=>c.name==='ge2'||(c.textAliases||[]).includes('/ge2'));
 const fake=list.filter(c=>c.name==='ge2-fake'||(c.textAliases||[]).includes('/ge2-fake'));
 const preserved=Object.fromEntries(['pair','dreaming','phone','voice'].map(k=>[k,list.some(c=>c.name===k||(c.textAliases||[]).includes('/'+k))]));
 return {provider,total:list.length,ge2Count:ge2.length,fakeCount:fake.length,preserved,ge2:ge2.map(c=>({name:c.name,source:c.source,scope:c.scope,textAliases:c.textAliases,pluginId:c.pluginId}))};
}
const failures=[];
for (const [k,p] of Object.entries(required)) if(!fs.existsSync(p)) failures.push(`missing:${k}:${p}`);
let status=''; let healthGreen=false;
try { status=sh('openclaw',['gateway','status']); healthGreen=/Runtime: running/.test(status)&&/Connectivity probe: ok/.test(status)&&/Capability: admin-capable/.test(status); if(!healthGreen) failures.push('health:not-green'); } catch(e){ failures.push('health:status-command-failed'); status=String(e); }
let cmd={};
try { cmd.telegram=commands('telegram'); cmd.webchat=commands('webchat'); for (const s of ['telegram','webchat']) { if(cmd[s].ge2Count!==1) failures.push(`${s}:ge2-count:${cmd[s].ge2Count}`); if(cmd[s].fakeCount!==0) failures.push(`${s}:fake-count:${cmd[s].fakeCount}`); for(const k of ['pair','dreaming','phone','voice']) if(cmd[s].preserved[k]!==true) failures.push(`${s}:missing-preserved:${k}`); } } catch(e) { failures.push('commands-list-failed:'+e.message); }
let r12DrSha=null; let noSecrets=null; let r13Summary=null; let r13Sha=null;
if(fs.existsSync(required.r12DrBundle)){ r12DrSha=sha(required.r12DrBundle); if(r12DrSha!==expectedR12DrSha) failures.push(`r12-dr-sha-mismatch:${r12DrSha}`); }
if(fs.existsSync(required.noSecretsScan)){ try{ noSecrets=JSON.parse(fs.readFileSync(required.noSecretsScan,'utf8')); if(noSecrets.status!=='PASS') failures.push(`no-secrets:${noSecrets.status}`); } catch(e){ failures.push('no-secrets:parse-failed'); } }
if(fs.existsSync(required.r13BundleSummary)){ try{ r13Summary=JSON.parse(fs.readFileSync(required.r13BundleSummary,'utf8')); if(r13Summary.noSecretsScan!=='PASS') failures.push(`r13-no-secrets:${r13Summary.noSecretsScan}`); } catch(e){ failures.push('r13-summary:parse-failed'); } }
if(fs.existsSync(required.r13Bundle)){ r13Sha=sha(required.r13Bundle); if(r13Summary?.sha256 && r13Sha!==r13Summary.sha256) failures.push(`r13-sha-mismatch:${r13Sha}`); }
const classification=failures.length?'GE2_NATIVE_COMMAND_SURFACE_PROMOTION_BLOCKED_HARD_STOP_GATE':'GE2_NATIVE_COMMAND_SURFACE_PROMOTED_PUSH_BLOCKED_HANDOFF_PRESERVED';
const report={classification,checkedAt:new Date().toISOString(),failures,healthGreen,commands:cmd,r12DrBundle:required.r12DrBundle,r12DrSha256:r12DrSha,r12DrShaMatches:r12DrSha===expectedR12DrSha,noSecretsStatus:noSecrets?.status,r13Bundle:required.r13Bundle,r13BundleSha256:r13Sha,r13BundleNoSecrets:r13Summary?.noSecretsScan,promotionRecord:required.promotionRecord,promotionRecordExists:fs.existsSync(required.promotionRecord),gitPushStatus:'blocked_not_attempted_due_preexisting_dirty_workspace',handoffPreserved:true,productionRuntimeTouched:false,gatewayRestarted:false,rollbackPerformed:false};
const jsonPath=`${outDir}/hardstop-push-blocked-handoff-preserved-verification.json`;
const mdPath=`${outDir}/GE2_NATIVE_COMMAND_SURFACE_PROMOTED_PUSH_BLOCKED_HANDOFF_PRESERVED_20260630.md`;
fs.writeFileSync(jsonPath,JSON.stringify(report,null,2));
const md=`# GE2 R13 Hard-stop Verification\n\nFinal classification: \`${classification}\`\n\nChecked at: \`${report.checkedAt}\`\n\n## Hard-stop gates\n\n- Current health green: ${healthGreen?'PASS':'FAIL'}\n- Telegram \`/ge2\` visible exactly once: ${cmd.telegram?.ge2Count===1?'PASS':'FAIL'}\n- WebUI/Webchat \`/ge2\` visible exactly once: ${cmd.webchat?.ge2Count===1?'PASS':'FAIL'}\n- Fake command absent: ${cmd.telegram?.fakeCount===0&&cmd.webchat?.fakeCount===0?'PASS':'FAIL'}\n- Preserved commands \`pair,dreaming,phone,voice\`: ${['telegram','webchat'].every(s=>cmd[s]&&Object.values(cmd[s].preserved).every(Boolean))?'PASS':'FAIL'}\n- R12 packet exists: ${fs.existsSync(required.r12Packet)?'PASS':'FAIL'}\n- Evidence manifest exists: ${fs.existsSync(required.evidenceManifest)?'PASS':'FAIL'}\n- Restore checklist exists: ${fs.existsSync(required.restoreChecklist)?'PASS':'FAIL'}\n- R12 DR bundle validates: ${r12DrSha===expectedR12DrSha?'PASS':'FAIL'}\n- R12 no-secrets scan remains PASS: ${noSecrets?.status==='PASS'?'PASS':'FAIL'}\n- Promotion record written: ${fs.existsSync(required.promotionRecord)?'PASS':'FAIL'}\n- R13 handoff bundle preserved: ${fs.existsSync(required.r13Bundle)&&r13Summary?.noSecretsScan==='PASS'?'PASS':'FAIL'}\n\n## Paths\n\n- Promotion record: \`${required.promotionRecord}\`\n- R12 packet: \`${required.r12Packet}\`\n- Evidence manifest: \`${required.evidenceManifest}\`\n- Restore checklist: \`${required.restoreChecklist}\`\n- R12 DR bundle: \`${required.r12DrBundle}\`\n- R12 DR SHA256: \`${r12DrSha}\`\n- R13 handoff bundle: \`${required.r13Bundle}\`\n- R13 handoff SHA256: \`${r13Sha}\`\n\n## Push / handoff\n\nGitHub push/clean commit remains blocked/not attempted because the workspace has a broad pre-existing unrelated dirty tree. Handoff is preserved in the R13 bundle.\n\n## Boundaries\n\n- Production runtime touched: no\n- Gateway restarted: no\n- Rollback performed: no\n- Cron closeout apply retried: no\n\nFailures: ${failures.length?failures.map(f=>'`'+f+'`').join(', '):'none'}\n`;
fs.writeFileSync(mdPath,md);
console.log(JSON.stringify({classification,failures,jsonPath,mdPath,r12DrSha,r13Sha,noSecrets:noSecrets?.status,healthGreen,telegramGe2:cmd.telegram?.ge2Count,webchatGe2:cmd.webchat?.ge2Count},null,2));
if(failures.length) process.exit(2);
