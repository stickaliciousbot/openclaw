import fs from 'node:fs';
import { execFileSync } from 'node:child_process';
import crypto from 'node:crypto';
import path from 'node:path';

const outDir='sharedspace/runtime-kernel-validation/ge2/ge2_r12_promotion_readiness_packet';
fs.mkdirSync(outDir,{recursive:true});
function sh(cmd,args,opts={}){return execFileSync(cmd,args,{encoding:'utf8',maxBuffer:20*1024*1024,...opts});}
function sha(p){return fs.existsSync(p)?crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex'):null;}
function json(p){return JSON.parse(fs.readFileSync(p,'utf8'));}
function gatewayCall(method, params){return JSON.parse(sh('openclaw',['gateway','call',method,'--json','--params',JSON.stringify(params)]));}
function commandSummary(provider){
 const data=gatewayCall('commands.list',{provider,scope:'text'}); const cmds=data.commands||[];
 const ge2Entries=cmds.filter(c=>c.name==='ge2'||(c.textAliases||[]).includes('/ge2'));
 const fake=cmds.filter(c=>c.name==='ge2-fake'||(c.textAliases||[]).includes('/ge2-fake'));
 const preserved=Object.fromEntries(['pair','dreaming','phone','voice'].map(k=>[k,cmds.some(c=>c.name===k||(c.textAliases||[]).includes('/'+k))]));
 return {provider,total:cmds.length,ge2Count:ge2Entries.length,fakeCount:fake.length,preserved,ge2Entries:ge2Entries.map(c=>({name:c.name,pluginId:c.pluginId,source:c.source,scope:c.scope,textAliases:c.textAliases,description:c.description,acceptsArgs:c.acceptsArgs}))};
}
function walk(dir){
 const out=[]; if(!fs.existsSync(dir)) return out;
 for(const ent of fs.readdirSync(dir,{withFileTypes:true})){
  const p=path.join(dir,ent.name); if(ent.isDirectory()) out.push(...walk(p)); else out.push(p);
 }
 return out;
}
const artifactCandidates=[
 'sharedspace/runtime-kernel-validation/ge2/ge2_r5_native_command_surface/GE2_R5_FINAL_BLOCKED.md',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r5_native_command_surface/final_blocked_summary.json',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r5_native_command_surface/install_manifest_20260630T0715Z.json',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r6_command_module_identity/R6_REQUESTED_DECISION_TABLE_AND_CLOSEOUT.md',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r6_command_module_identity/R6_REQUESTED_DECISION_TABLE_AND_CLOSEOUT.json',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r6_command_module_identity/final_diagnosis_summary.json',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/r7_loader_lifecycle_exact_target_and_repair_plan.md',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/r7_closeout_manifest_20260630.json',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/r7_source_snapshot_manifest_20260630.json',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/r7_source_snapshot_trace_report_20260630.json',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/install_manifest_ge2_r7_lifecycle_20260630T0812Z.json',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/reverser_ge2_r7_lifecycle_20260630T0812Z.mjs',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/GE2_R7_BOUNDED_RECOVERY_CLOSE_LOOP_20260630.md',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r8_native_execution_route_discovery/GE2_R8_NATIVE_EXECUTION_ROUTE_DISCOVERY_REPORT_20260630.json',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r8_native_execution_route_discovery/GE2_R8_NATIVE_EXECUTION_ROUTE_DISCOVERY_REPORT_20260630.md',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r9_native_run_lifecycle_proof/GE2_R9_NATIVE_HANDLER_RUN_STATUS_ARTIFACTS_CORRECTED_REPORT_20260630.json',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r9_native_run_lifecycle_proof/GE2_R9_NATIVE_HANDLER_RUN_STATUS_ARTIFACTS_CORRECTED_REPORT_20260630.md',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r10_adapter_fixture_proof/GE2_R10_FINAL_OWNER_REQUIRED_REPORT_20260630.md',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r10_adapter_fixture_proof/GE2_R10_ADAPTER_FIXTURE_TELEGRAM_WEBUI_CORRECTED_REPORT_20260630.json',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r10_adapter_fixture_proof/GE2_R10_ADAPTER_FIXTURE_TELEGRAM_WEBUI_CORRECTED_REPORT_20260630.md',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r11_real_inbound_gateway_smoke/GE2_R11_PHASE1_REAL_INBOUND_ENTRYPOINTS_AND_BLOCKERS_20260630.json',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r11_real_inbound_gateway_smoke/GE2_R11_PHASE1_REAL_INBOUND_ENTRYPOINTS_AND_BLOCKERS_20260630.md',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r11_real_inbound_gateway_smoke/GE2_R11_REAL_INBOUND_GATEWAY_TELEGRAM_WEBUI_PASS_PROMOTION_PENDING_20260630.md',
 'memory/2026-06-30-ge2-r8-result.md',
 'memory/2026-06-30-ge2-r9-result.md',
 'memory/2026-06-30-ge2-r10-result.md',
 'memory/2026-06-30-ge2-r11-final-pass.md',
 'memory/2026-06-30-ge2-r11-telegram-p3-pass.md',
 'sharedspace/context-bridge/events.jsonl'
];
const existingArtifacts=artifactCandidates.filter(p=>fs.existsSync(p)).map(p=>({path:p,sha256:sha(p),bytes:fs.statSync(p).size}));
const missingArtifacts=artifactCandidates.filter(p=>!fs.existsSync(p));
const telegramRun=json('state/ge2-native/runs/ge2-20260630101117-1fa6ed4d.json');
const webuiRun=json('state/ge2-native/runs/ge2-20260630102318-ae4b5942.json');
const report={
 generatedAt:new Date().toISOString(),
 classification:'GE2_R12_PROMOTION_READINESS_PACKET_READY',
 inputClassification:'GE2_R11_REAL_INBOUND_GATEWAY_TELEGRAM_WEBUI_PASS_PROMOTION_PENDING',
 noPromotionPerformed:true,
 version:sh('openclaw',['--version']).trim(),
 gatewayStatus:sh('openclaw',['gateway','status']),
 commands:{telegram:commandSummary('telegram'),webchat:commandSummary('webchat')},
 contextBridge:{eventId:'evt-20260630T102500Z-ge2-r11-real-inbound-telegram-webui-pass',contextVersion:150,status:'PASS',parsedEvents:89,finalReportSha256:'f61b34e98afecab09e50a1999c552483d6f577e034935bbc52c27985eb7ba5ec'},
 proofLadder:{P1:'PASS installed-dist matcher/handler harness',P2:'PASS Telegram/WebUI adapter fixture paths',P3Telegram:'PASS real inbound Gateway Telegram path',P3WebUI:'PASS real inbound OpenClaw WebUI path'},
 runs:{telegram:telegramRun,webui:webuiRun},
 artifactInventory:existingArtifacts,
 missingArtifacts,
 r7:{target:'/home/stickai/.npm-global/lib/node_modules/openclaw/dist/loader-Bfm_uDYG.js',beforeSha256:'ff2d89b04d1d5f7fb727f586a78fe92e0b52ffbe43a484551475cf140b53feb0',afterSha256:'43bc33fa3c706ce16c3fc395da640ed6ee9041361938b84a8e8ecbd92685df6b',installManifest:'sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/install_manifest_ge2_r7_lifecycle_20260630T0812Z.json',reverser:'sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/reverser_ge2_r7_lifecycle_20260630T0812Z.mjs'},
 boundaries:{productionPatch:false,gatewayRestart:false,rollback:false,cronCloseoutApply:false,promotion:false,configServicePathSystemdMutation:false,routeCacheArtifactMemoryRuntimeAuthorityMutation:false,additionalLiveSmoke:false},
 nextState:'OWNER_APPROVAL_REQUIRED_BEFORE_PROMOTION_OR_CRON_CLOSEOUT_RETRY'
};
fs.writeFileSync(`${outDir}/r12_evidence.json`,JSON.stringify(report,null,2));
console.log(JSON.stringify({ok:true,outDir,classification:report.classification,missingArtifacts,telegramGe2Count:report.commands.telegram.ge2Count,webchatGe2Count:report.commands.webchat.ge2Count},null,2));
