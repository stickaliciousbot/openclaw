import fs from 'node:fs';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';

const outDir='sharedspace/runtime-kernel-validation/ge2/ge2_r13_promotion';
fs.mkdirSync(outDir,{recursive:true});
const paths={
  r12Packet:'sharedspace/runtime-kernel-validation/ge2/ge2_r12_promotion_readiness_packet/GE2_R12_PROMOTION_READINESS_PACKET_READY_20260630.md',
  evidence:'sharedspace/runtime-kernel-validation/ge2/ge2_r12_promotion_readiness_packet/r12_evidence.json',
  checklist:'sharedspace/runtime-kernel-validation/ge2/ge2_r12_promotion_readiness_packet/restore-checklist.md',
  drBundle:'sharedspace/disaster-recovery/ge2-r12-promotion-readiness-20260630/ge2-r12-promotion-readiness-20260630.tar.gz',
  noSecrets:'sharedspace/runtime-kernel-validation/ge2/ge2_r12_promotion_readiness_packet/NO_SECRETS_SCAN.json',
  events:'sharedspace/context-bridge/events.jsonl',
  memoryDaily:'memory/2026-06-30.md',
  memoryLong:'MEMORY.md'
};
const expectedDrSha='474408c1ad4c4850ed21ded2c2231fc1e1e668fc4a4995d29a594e1b1c915c2d';
function sha(p){return crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');}
function json(p){return JSON.parse(fs.readFileSync(p,'utf8'));}
function sh(cmd,args){return execFileSync(cmd,args,{encoding:'utf8',maxBuffer:20*1024*1024});}
function call(method,params){return JSON.parse(sh('openclaw',['gateway','call',method,'--json','--params',JSON.stringify(params)]));}
function commandSummary(provider){
 const data=call('commands.list',{provider,scope:'text'}); const cmds=data.commands||[];
 const ge2Entries=cmds.filter(c=>c.name==='ge2'||(c.textAliases||[]).includes('/ge2'));
 const fakeEntries=cmds.filter(c=>c.name==='ge2-fake'||(c.textAliases||[]).includes('/ge2-fake'));
 const preserved=Object.fromEntries(['pair','dreaming','phone','voice'].map(k=>[k,cmds.some(c=>c.name===k||(c.textAliases||[]).includes('/'+k))]));
 return {provider,total:cmds.length,ge2Count:ge2Entries.length,fakeCount:fakeEntries.length,preserved,ge2Entries:ge2Entries.map(c=>({name:c.name,pluginId:c.pluginId,source:c.source,scope:c.scope,textAliases:c.textAliases}))};
}
function assert(cond,msg){if(!cond) throw new Error(msg);}

const startedAt=new Date().toISOString();
for (const [name,p] of Object.entries(paths)) if (name!=='events' && name!=='memoryDaily' && name!=='memoryLong') assert(fs.existsSync(p),`missing required path ${name}: ${p}`);
assert(sha(paths.drBundle)===expectedDrSha,`DR bundle SHA mismatch: ${sha(paths.drBundle)}`);
const noSecrets=json(paths.noSecrets); assert(noSecrets.status==='PASS','no-secrets scan not PASS');
const evidence=json(paths.evidence); assert(evidence.classification==='GE2_R12_PROMOTION_READINESS_PACKET_READY','R12 evidence classification not READY');
const version=sh('openclaw',['--version']).trim();
const gatewayStatus=sh('openclaw',['gateway','status']);
assert(/Runtime: running/.test(gatewayStatus),'Gateway runtime not running');
assert(/Connectivity probe: ok/.test(gatewayStatus),'Gateway connectivity not ok');
assert(/Capability: admin-capable/.test(gatewayStatus),'Gateway not admin-capable');
const commands={telegram:commandSummary('telegram'),webchat:commandSummary('webchat')};
for (const surface of ['telegram','webchat']) {
 const c=commands[surface];
 assert(c.ge2Count===1,`${surface} /ge2 count ${c.ge2Count}`);
 assert(c.fakeCount===0,`${surface} fake count ${c.fakeCount}`);
 for (const k of ['pair','dreaming','phone','voice']) assert(c.preserved[k]===true,`${surface} missing ${k}`);
}
const eventId='evt-20260630T103800Z-ge2-native-command-surface-promoted';
const lines=fs.existsSync(paths.events)?fs.readFileSync(paths.events,'utf8').split(/\n/).filter(Boolean):[];
let maxContext=0; let already=false;
for (const line of lines) { const e=JSON.parse(line); if(Number.isFinite(e.context_version)) maxContext=Math.max(maxContext,e.context_version); if(e.event_id===eventId) already=true; }
const packetSha=sha(paths.r12Packet);
const evidenceSha=sha(paths.evidence);
const checklistSha=sha(paths.checklist);
const promotionRecordPath=`${outDir}/GE2_NATIVE_COMMAND_SURFACE_PROMOTED_20260630.md`;
const promotionJsonPath=`${outDir}/promotion-record.json`;
const record={
 classification:'GE2_NATIVE_COMMAND_SURFACE_PROMOTED',
 promotedAt:startedAt,
 r12Classification:'GE2_R12_PROMOTION_READINESS_PACKET_READY',
 r11Classification:'GE2_R11_REAL_INBOUND_GATEWAY_TELEGRAM_WEBUI_PASS_PROMOTION_PENDING',
 r12Packet:paths.r12Packet,
 r12PacketSha256:packetSha,
 evidenceManifest:paths.evidence,
 evidenceManifestSha256:evidenceSha,
 restoreChecklist:paths.checklist,
 restoreChecklistSha256:checklistSha,
 drBundle:paths.drBundle,
 drBundleSha256:expectedDrSha,
 noSecretsScan:paths.noSecrets,
 noSecretsStatus:noSecrets.status,
 proofSummary:{P1:'PASS installed-dist matcher/handler harness',P2:'PASS Telegram/WebUI adapter fixture paths',P3Telegram:'PASS real inbound Telegram',P3WebUI:'PASS real inbound WebUI',commands:['/ge2 help','/ge2 status','/ge2 run <task>','/ge2 status <run_id>','/ge2 artifacts <run_id>'],ledgerArtifactHash:'PASS',modelChatFallthrough:'not observed'},
 productionHealth:{version,gatewayStatusSummary:'running, connectivity ok, admin-capable, listening *:18789',commands},
 boundaries:{runtimeCodeChanged:false,configChanged:false,servicePathSystemdChanged:false,gatewayRestarted:false,rollbackPerformed:false,cronCloseoutApply:false,routeCacheArtifactMemoryRuntimeAuthorityMutation:false},
 promotionMeaning:'Current GE2 native command surface state is promoted/durable as proven production command surface. This does not authorize cron closeout apply by itself.'
};
fs.writeFileSync(promotionJsonPath,JSON.stringify(record,null,2));
const md=`# GE2 Native Command Surface — PROMOTED\n\nFinal classification: \`GE2_NATIVE_COMMAND_SURFACE_PROMOTED\`\n\nPromoted at: \`${startedAt}\`\n\n## Scope\n\nThis promotion marks the current GE2 native command surface as promoted and durable. No runtime code, Gateway config, service/PATH/systemd setting, model route, cache, artifact-memory, or runtime-authority state was changed during R13. No cron closeout apply was retried.\n\n## Basis\n\n- R12 packet: \`${paths.r12Packet}\`\n- R12 packet SHA256: \`${packetSha}\`\n- Evidence manifest: \`${paths.evidence}\`\n- Evidence manifest SHA256: \`${evidenceSha}\`\n- Restore checklist: \`${paths.checklist}\`\n- Restore checklist SHA256: \`${checklistSha}\`\n- DR bundle: \`${paths.drBundle}\`\n- DR bundle SHA256: \`${expectedDrSha}\`\n- No-secrets scan: \`${noSecrets.status}\`\n\n## Proof summary\n\n- P1 installed-dist matcher/handler harness: PASS\n- P2 Telegram/WebUI adapter fixture paths: PASS\n- P3 real inbound Telegram path: PASS\n- P3 real inbound WebUI path: PASS\n- \`/ge2 help\`: PASS\n- \`/ge2 status\`: PASS\n- \`/ge2 run <task>\`: PASS\n- \`/ge2 status <run_id>\`: PASS\n- \`/ge2 artifacts <run_id>\`: PASS\n- Ledger/artifact/hash proof: PASS\n- Model/chat fallthrough: not observed\n\n## Current production health\n\n- OpenClaw: \`${version}\`\n- Gateway: running, connectivity OK, admin-capable, listening \`*:18789\`\n- Telegram /ge2 count: \`${commands.telegram.ge2Count}\`\n- WebUI /ge2 count: \`${commands.webchat.ge2Count}\`\n- Fake command count: Telegram \`${commands.telegram.fakeCount}\`, WebUI \`${commands.webchat.fakeCount}\`\n- Preserved commands: \`pair\`, \`dreaming\`, \`phone\`, \`voice\`\n\nKnown non-blocking warning remains: Gateway service PATH missing \`/home/stickai/.local/share/pnpm\`.\n\n## Rollback / recovery reference\n\nUse restore checklist only if a rollback condition is met and Stick explicitly authorizes recovery:\n\`${paths.checklist}\`\n\nR7 reverser is referenced by the R12 packet and evidence manifest.\n\n## Boundaries\n\n- Production code touched during R13: no\n- Gateway restarted during R13: no\n- Rollback performed during R13: no\n- Cron closeout apply during R13: no\n- Config/service/PATH/systemd mutation: no\n- Route/cache/artifact-memory/runtime-authority mutation: no\n\n## Next\n\nGE2 command surface promotion is complete. Cron closeout retry remains a separate owner-gated action and still requires watcher/report-required semantics to be respected.\n`;
fs.writeFileSync(promotionRecordPath,md);
record.promotionRecordPath=promotionRecordPath;
record.promotionRecordSha256=sha(promotionRecordPath);
fs.writeFileSync(promotionJsonPath,JSON.stringify(record,null,2));

if(!already){
 const event={
  agent_id:'main', channel:'operator', context_version:maxContext+1,
  dedupe_key:'dk-ge2-native-command-surface-promoted-20260630T1038Z',
  entity_id:'ge2-native-command-surface', event_id:eventId,
  event_type:'ge2_native_command_surface_promoted', memory_id:'memory/2026-06-30-ge2-r13-promotion.md',
  payload:{classification:record.classification,promotedAt:startedAt,r12Packet:paths.r12Packet,r12PacketSha256:packetSha,drBundle:paths.drBundle,drBundleSha256:expectedDrSha,promotionRecord:promotionRecordPath,promotionRecordSha256:record.promotionRecordSha256,noSecretsStatus:noSecrets.status,commands,health:'Gateway running/connectivity ok/admin-capable',boundaries:record.boundaries,next:'cron closeout retry remains separately owner-gated'},
  reducer_version:1,
  source_refs:[promotionRecordPath,promotionJsonPath,paths.r12Packet,paths.evidence,paths.checklist,paths.drBundle,paths.noSecrets],
  status:'PASS',
  summary:'GE2 native command surface promoted/durable after R12 readiness packet; no runtime/config/service mutation, no Gateway restart, no rollback, no cron closeout apply.',
  ts:'2026-06-30T10:38:00Z'
 };
 fs.appendFileSync(paths.events,JSON.stringify(event)+'\n');
}
// parse validate events
let parsedEvents=0; for(const [idx,line] of fs.readFileSync(paths.events,'utf8').split(/\n/).entries()){if(!line.trim()) continue; try{JSON.parse(line); parsedEvents++;}catch(e){throw new Error(`events parse failed line ${idx+1}: ${e.message}`)}}
fs.writeFileSync(`${outDir}/gateway-status.txt`,gatewayStatus);
fs.writeFileSync(`${outDir}/commands-summary.json`,JSON.stringify(commands,null,2));
fs.writeFileSync(`${outDir}/r13-validation-summary.json`,JSON.stringify({ok:true,classification:record.classification,eventId,contextVersion:already?maxContext:maxContext+1,parsedEvents,promotionRecordPath,promotionRecordSha256:record.promotionRecordSha256,promotionJsonPath,drBundleSha256:expectedDrSha,packetSha,evidenceSha,noSecretsStatus:noSecrets.status,boundaries:record.boundaries},null,2));
console.log(JSON.stringify({ok:true,classification:record.classification,promotionRecordPath,promotionRecordSha256:record.promotionRecordSha256,eventId,contextVersion:already?maxContext:maxContext+1,parsedEvents,drBundleSha256:expectedDrSha,gatewayRestarted:false,rollbackPerformed:false,cronCloseoutApply:false},null,2));
