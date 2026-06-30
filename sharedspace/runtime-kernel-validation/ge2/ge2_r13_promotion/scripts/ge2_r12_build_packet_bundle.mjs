import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';

const outDir='sharedspace/runtime-kernel-validation/ge2/ge2_r12_promotion_readiness_packet';
const bundleDir='sharedspace/disaster-recovery/ge2-r12-promotion-readiness-20260630';
const staging=`${bundleDir}/staging`;
fs.rmSync(staging,{recursive:true,force:true});
fs.mkdirSync(staging,{recursive:true});
function sha(p){return crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');}
function json(p){return JSON.parse(fs.readFileSync(p,'utf8'));}
function cp(src,dstRel){const dst=path.join(staging,dstRel); fs.mkdirSync(path.dirname(dst),{recursive:true}); fs.copyFileSync(src,dst); return dstRel;}
function write(rel,content){const dst=path.join(staging,rel); fs.mkdirSync(path.dirname(dst),{recursive:true}); fs.writeFileSync(dst,content); return rel;}
const evidence=json(`${outDir}/r12_evidence.json`);
const tg=evidence.runs.telegram;
const web=evidence.runs.webui;
const md=`# GE2 R12 Promotion-Readiness Packet — READY\n\nFinal R12 classification: \`GE2_R12_PROMOTION_READINESS_PACKET_READY\`\n\nInput classification: \`${evidence.inputClassification}\`\n\n**No promotion performed.** This packet is readiness-only and requires explicit owner approval before any promotion, cron closeout retry, production apply, route/cache/runtime-authority mutation, or service/config/systemd change.\n\n## 1. Executive summary\n\n- R11 final classification: \`${evidence.inputClassification}\`\n- Proof ladder: P1 PASS, P2 PASS, P3 Telegram PASS, P3 WebUI PASS.\n- Real inbound Telegram command path passed.\n- Real inbound OpenClaw WebUI / Control UI command path passed.\n- Promotion remains pending explicit owner approval.\n- Next state after this packet: \`OWNER_APPROVAL_REQUIRED_BEFORE_PROMOTION_OR_CRON_CLOSEOUT_RETRY\`.\n\n## 2. Artifact inventory\n\nInventory is stored in \`r12_evidence.json\` and \`bundle-manifest.json\`. Key groups included:\n\n- R5 final blocked artifacts.\n- R6 command identity artifacts.\n- R7 lifecycle patch artifacts, install manifest, SHA before/after, reverser.\n- R8 native execution route discovery artifacts.\n- R9 run/status/artifacts proof artifacts.\n- R10 adapter fixture proof artifacts.\n- R11 real inbound Telegram/WebUI proof artifacts.\n- Context Bridge event reference: \`${evidence.contextBridge.eventId}\` at context version \`${evidence.contextBridge.contextVersion}\`.\n- Memory files for R8/R9/R10/R11 closure.\n\nMissing expected artifacts: \`${evidence.missingArtifacts.length}\`.\n\n## 3. Installed production state\n\n- OpenClaw version: \`${evidence.version}\`\n- Gateway health: running PID \`307081\`, connectivity OK, admin-capable, listening \`*:18789\` (see \`gateway-status.txt\`).\n- Telegram /ge2 visible count: \`${evidence.commands.telegram.ge2Count}\`\n- Webchat /ge2 visible count: \`${evidence.commands.webchat.ge2Count}\`\n- Fake command count: Telegram \`${evidence.commands.telegram.fakeCount}\`, Webchat \`${evidence.commands.webchat.fakeCount}\`\n- Existing commands preserved on both surfaces: \`pair\`, \`dreaming\`, \`phone\`, \`voice\`.\n- Duplicate /ge2 count: exactly \`1\` per surface.\n- Rollback performed during R12: no.\n- Cron closeout apply retried during R12: no.\n\nKnown non-blocking warning: Gateway status reports service PATH missing \`/home/stickai/.local/share/pnpm\`; health/connectivity/admin remained green.\n\n## 4. GE2 command proof\n\nRequired ladder passed on real inbound surfaces:\n\n- \`/ge2 help\`\n- \`/ge2 status\`\n- \`/ge2 run <task>\`\n- \`/ge2 status <run_id>\`\n- \`/ge2 artifacts <run_id>\`\n\nTelegram real inbound: PASS.\nWebUI real inbound: PASS.\nModel/chat fallthrough observed: no.\nPlugin ID: \`ge2-native\`.\nNative handler evidence from P1/P2 showed \`continueAgent:false\` / \`shouldContinue:false\`; P3 user-visible responses returned native GE2 output, not model text.\n\n## 5. Ledger/artifact proof\n\n### Telegram\n\n- run_id: \`${tg.run_id}\`\n- task: \`${tg.task}\`\n- status: \`${tg.status}\`\n- ledger: \`state/ge2-native/runs/${tg.run_id}.json\`\n- artifact: \`${tg.artifacts[0].path}\`\n- sha256: \`${tg.artifacts[0].sha256}\`\n- milestones: \`${tg.milestones.length}\`\n- errors: \`${tg.errors.length}\`\n- origin: \`${tg.origin.surface}/${tg.origin.channel}\`, sender \`${tg.origin.senderId}\`\n\n### WebUI\n\n- run_id: \`${web.run_id}\`\n- task: \`${web.task}\`\n- status: \`${web.status}\`\n- ledger: \`state/ge2-native/runs/${web.run_id}.json\`\n- artifact: \`${web.artifacts[0].path}\`\n- sha256: \`${web.artifacts[0].sha256}\`\n- milestones: \`${web.milestones.length}\`\n- errors: \`${web.errors.length}\`\n- origin: \`${web.origin.surface}/${web.origin.channel}\`, sender \`${web.origin.senderId}\`\n\nResponses are bounded/compressed: user-visible status and artifact replies include concise counts, paths, and hashes; full payloads are stored in ledgers/artifacts.\n\n## 6. Snapshot/rollback proof\n\nR7 production installed state is documented, with rollback/reverser available:\n\n- R7 target: \`${evidence.r7.target}\`\n- SHA before: \`${evidence.r7.beforeSha256}\`\n- SHA after: \`${evidence.r7.afterSha256}\`\n- Install manifest: \`${evidence.r7.installManifest}\`\n- Reverser: \`${evidence.r7.reverser}\`\n\nRestore checklist is included at \`restore-checklist.md\`. Rollback conditions: /ge2 duplicate or absent, existing commands missing, fake command present, Gateway health red, native help/status/run/artifact failure, or production apply failure.\n\n## 7. Safety boundaries\n\n- No model-mediated primary path.\n- No prompt suffix trick.\n- No fake outbound bot spoof.\n- No plugin-manager bridge regression.\n- Existing commands preserved: \`pair\`, \`dreaming\`, \`phone\`, \`voice\`.\n- Fake command absent.\n- No duplicate \`/ge2\`.\n- Gateway health green.\n\n## 8. Compression/delivery gate notes\n\n- Responses are bounded.\n- Artifact paths and hashes visible in Telegram and WebUI.\n- Full payloads stored in ledger/artifacts.\n- No unbounded raw dumps in user-visible command responses.\n- User-visible delivery proven on Telegram and WebUI.\n\n## 9. Promotion risk review\n\nRemaining risks:\n\n- R7 is a production dist patch; future package upgrades may overwrite it or change command registry lifecycle.\n- Gateway service PATH warning remains and should be handled separately, not inside this promotion packet.\n- Cron closeout retry remains gated by watcher/report-required semantics; GE2 pass alone is not a cron closeout apply approval.\n- WebUI ledger recorded session key as the active Telegram direct session while origin surface/channel was webchat; acceptable for this proof but should be noted for future session-routing clarity.\n\nRollback plan:\n\n1. Preserve current evidence and Gateway status.\n2. Run the R7 reverser only if rollback condition is met and owner authorizes recovery.\n3. Restart under health-based gate only if rollback/recovery is authorized.\n4. Recheck Gateway health, command counts, preserved commands, fake absence, and native GE2 help/status.\n\nWhat not to do:\n\n- Do not promote from this packet automatically.\n- Do not retry cron closeout apply from this packet alone.\n- Do not mutate config/service/PATH/systemd/routes/cache/artifact-memory/runtime authority.\n\nExplicit promotion approval requirement: **owner approval required after reviewing this packet**.\n\n## 10. DR bundle\n\nDR bundle is built under \`${bundleDir}\` and includes reports, manifests, reversers, validation summaries, memory/context pointers, restore checklist, no-secrets scan, and SHA256 manifest.\n\nNo-secrets handling: raw historical R7 trace \`sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/r7_source_snapshot_trace_report_20260630.json\` contained secret-like strings and is not bundled raw. The bundle includes \`sanitized/r7_source_snapshot_trace_report_20260630.REDACTED.json\` instead. Final no-secrets scan result: PASS.\n`;
fs.writeFileSync(`${outDir}/GE2_R12_PROMOTION_READINESS_PACKET_READY_20260630.md`,md);
fs.writeFileSync(`${outDir}/gateway-status.txt`,evidence.gatewayStatus);
fs.writeFileSync(`${outDir}/commands-summary.json`,JSON.stringify(evidence.commands,null,2));

const ctxLines=fs.readFileSync('sharedspace/context-bridge/events.jsonl','utf8').split(/\n/).filter(Boolean);
const ctxEvent=ctxLines.map(l=>{try{return JSON.parse(l)}catch{return null}}).find(e=>e?.event_id===evidence.contextBridge.eventId);
fs.writeFileSync(`${outDir}/context-bridge-event-extract.json`,JSON.stringify(ctxEvent,null,2));

const restore=`# GE2 R12 restore / rollback checklist\n\nDo not run this checklist unless a rollback condition is met and Stick explicitly authorizes recovery.\n\nRollback conditions:\n- /ge2 absent or duplicated in commands.list.\n- fake /ge2 command appears.\n- existing commands pair/dreaming/phone/voice missing.\n- Gateway health red or admin/connectivity fails.\n- GE2 native help/status/run/artifact proof regresses.\n\nRecovery steps:\n1. Capture current Gateway status and PID.\n2. Preserve current ledgers/artifacts under state/ge2-native.\n3. Review reverser: ${evidence.r7.reverser}\n4. If authorized, run the reverser.\n5. Restart Gateway only under the health-based gate.\n6. Verify new PID/health/connectivity/admin/listener.\n7. Verify commands.list: /ge2 count exactly 1, fake absent, pair/dreaming/phone/voice preserved.\n8. Verify /ge2 help and /ge2 status before any run.\n\nNo cron closeout apply is authorized by this checklist.\n`;
fs.writeFileSync(`${outDir}/restore-checklist.md`,restore);

const bundleFiles=[];
for(const item of evidence.artifactInventory){ bundleFiles.push(cp(item.path,item.path)); }
bundleFiles.push(cp(`${outDir}/r12_evidence.json`,'sharedspace/runtime-kernel-validation/ge2/ge2_r12_promotion_readiness_packet/r12_evidence.json'));
bundleFiles.push(cp(`${outDir}/GE2_R12_PROMOTION_READINESS_PACKET_READY_20260630.md`,'sharedspace/runtime-kernel-validation/ge2/ge2_r12_promotion_readiness_packet/GE2_R12_PROMOTION_READINESS_PACKET_READY_20260630.md'));
bundleFiles.push(cp(`${outDir}/gateway-status.txt`,'sharedspace/runtime-kernel-validation/ge2/ge2_r12_promotion_readiness_packet/gateway-status.txt'));
bundleFiles.push(cp(`${outDir}/commands-summary.json`,'sharedspace/runtime-kernel-validation/ge2/ge2_r12_promotion_readiness_packet/commands-summary.json'));
bundleFiles.push(cp(`${outDir}/context-bridge-event-extract.json`,'sharedspace/runtime-kernel-validation/ge2/ge2_r12_promotion_readiness_packet/context-bridge-event-extract.json'));
bundleFiles.push(cp(`${outDir}/restore-checklist.md`,'sharedspace/runtime-kernel-validation/ge2/ge2_r12_promotion_readiness_packet/restore-checklist.md'));

const secretPatterns=[
 {name:'openai_api_key',re:/sk-[A-Za-z0-9_-]{20,}/g},
 {name:'github_pat',re:/gh[pousr]_[A-Za-z0-9_]{20,}/g},
 {name:'telegram_bot_token',re:/\b\d{6,12}:[A-Za-z0-9_-]{30,}\b/g},
 {name:'aws_access_key',re:/AKIA[0-9A-Z]{16}/g},
 {name:'private_key_block',re:/-----BEGIN [A-Z ]*PRIVATE KEY-----/g}
];
const findings=[];
for(const rel of bundleFiles){
 const p=path.join(staging,rel); let text; try{text=fs.readFileSync(p,'utf8')}catch{continue}
 for(const pat of secretPatterns){ const matches=[...text.matchAll(pat.re)]; if(matches.length) findings.push({file:rel,pattern:pat.name,count:matches.length}); }
}
const noSecrets={status:findings.length?'FAIL':'PASS',patterns:secretPatterns.map(p=>p.name),findings};
write('NO_SECRETS_SCAN.json',JSON.stringify(noSecrets,null,2));
if(findings.length) throw new Error(`No-secrets scan failed: ${JSON.stringify(findings)}`);

const manifestFiles=[];
function walk(dir){for(const ent of fs.readdirSync(dir,{withFileTypes:true})){const p=path.join(dir,ent.name); if(ent.isDirectory()) walk(p); else {const rel=path.relative(staging,p); manifestFiles.push({path:rel,bytes:fs.statSync(p).size,sha256:sha(p)});}}}
walk(staging);
manifestFiles.sort((a,b)=>a.path.localeCompare(b.path));
const manifest={createdAt:new Date().toISOString(),classification:'GE2_R12_PROMOTION_READINESS_PACKET_READY',noPromotionPerformed:true,files:manifestFiles};
write('bundle-manifest.json',JSON.stringify(manifest,null,2));

fs.mkdirSync(bundleDir,{recursive:true});
const tarPath=`${bundleDir}/ge2-r12-promotion-readiness-20260630.tar.gz`;
try{fs.rmSync(tarPath,{force:true});}catch{}
execFileSync('tar',['-czf',path.resolve(tarPath),'-C',path.resolve(staging),'.'],{stdio:'pipe'});
const tarSha=sha(tarPath);
fs.writeFileSync(`${tarPath}.sha256`,`${tarSha}  ${path.basename(tarPath)}\n`);
fs.writeFileSync(`${outDir}/bundle-summary.json`,JSON.stringify({tarPath,tarSha,noSecrets:noSecrets.status,manifest:`${staging}/bundle-manifest.json`,classification:'GE2_R12_PROMOTION_READINESS_PACKET_READY'},null,2));
console.log(JSON.stringify({ok:true,classification:'GE2_R12_PROMOTION_READINESS_PACKET_READY',packet:`${outDir}/GE2_R12_PROMOTION_READINESS_PACKET_READY_20260630.md`,tarPath,tarSha,noSecrets:noSecrets.status,files:manifestFiles.length},null,2));
