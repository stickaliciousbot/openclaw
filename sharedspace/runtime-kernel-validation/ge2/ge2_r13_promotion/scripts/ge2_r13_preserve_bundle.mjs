import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';

const root=process.cwd();
const base='sharedspace/disaster-recovery/ge2-r13-promotion-20260630';
const staging=path.join(base,'staging');
fs.rmSync(base,{recursive:true,force:true});
fs.mkdirSync(staging,{recursive:true});
const include=[
 'sharedspace/runtime-kernel-validation/ge2/ge2_r13_promotion/GE2_NATIVE_COMMAND_SURFACE_PROMOTED_20260630.md',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r13_promotion/promotion-record.json',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r13_promotion/r13-validation-summary.json',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r13_promotion/commands-summary.json',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r13_promotion/gateway-status.txt',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r12_promotion_readiness_packet/GE2_R12_PROMOTION_READINESS_PACKET_READY_20260630.md',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r12_promotion_readiness_packet/r12_evidence.json',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r12_promotion_readiness_packet/restore-checklist.md',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r12_promotion_readiness_packet/NO_SECRETS_SCAN.json',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r12_promotion_readiness_packet/bundle-summary.json',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r12_promotion_readiness_packet/sanitized/r7_source_snapshot_trace_report_20260630.REDACTED.json',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/reverser_ge2_r7_lifecycle_20260630T0812Z.mjs',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/r7_closeout_manifest_20260630.json',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r11_real_inbound_gateway_smoke/GE2_R11_REAL_INBOUND_GATEWAY_TELEGRAM_WEBUI_PASS_PROMOTION_PENDING_20260630.md',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r10_adapter_fixture_proof/GE2_R10_FINAL_OWNER_REQUIRED_REPORT_20260630.md',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r9_native_run_lifecycle_proof/GE2_R9_NATIVE_HANDLER_RUN_STATUS_ARTIFACTS_CORRECTED_REPORT_20260630.md',
 'memory/2026-06-30-ge2-r13-promotion.md',
 'memory/2026-06-30-ge2-r12-promotion-readiness-packet-ready.md',
 'memory/2026-06-30-ge2-r11-final-pass.md',
 'memory/lessons-learned-ge2-native-command-surface-promotion-2026-06-30.md',
 'ge2-native-runtime/README.md',
 'ge2-native-runtime/src/ge2_artifacts.mjs',
 'ge2-native-runtime/src/ge2_command_router.mjs',
 'ge2-native-runtime/src/ge2_dispatcher.mjs',
 'ge2-native-runtime/src/ge2_ledger.mjs',
 'ge2-native-runtime/src/ge2_milestones.mjs',
 'ge2-native-runtime/src/ge2_runtime.mjs',
 'ge2-native-runtime/src/ge2_snapshot.mjs',
 'plugins/ge2-command/index.mjs',
 'plugins/ge2-command/openclaw.plugin.json',
 'plugins/ge2-command/package.json'
];
const copied=[]; const missing=[];
for (const rel of include){
 const src=path.join(root,rel); if(!fs.existsSync(src)){missing.push(rel); continue;}
 const dst=path.join(staging,rel); fs.mkdirSync(path.dirname(dst),{recursive:true}); fs.copyFileSync(src,dst); copied.push(rel);
}
const manifest={classification:'GE2_NATIVE_COMMAND_SURFACE_PROMOTED',purpose:'R13 promotion preservation bundle; selected docs/source/evidence only; excludes raw secret-like R7 trace and private config',createdAt:new Date().toISOString(),copied,missing,sourceCommit:null,gitCommitStatus:'not_committed_due_preexisting_dirty_workspace'};
try { manifest.sourceCommit=execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(); } catch {}
fs.writeFileSync(path.join(staging,'MANIFEST.json'),JSON.stringify(manifest,null,2));
const patterns=[
 ['openai_api_key',/sk-[A-Za-z0-9_-]{20,}/g],
 ['github_pat',/gh[pousr]_[A-Za-z0-9_]{20,}/g],
 ['telegram_bot_token',/\b\d{6,}:[A-Za-z0-9_-]{20,}\b/g],
 ['aws_access_key',/AKIA[0-9A-Z]{16}/g],
 ['private_key_block',/-----BEGIN [A-Z ]*PRIVATE KEY-----/g]
];
const findings=[];
function walk(d){ for(const ent of fs.readdirSync(d,{withFileTypes:true})){ const p=path.join(d,ent.name); if(ent.isDirectory()) walk(p); else { const buf=fs.readFileSync(p); if(buf.length>2*1024*1024) continue; const txt=buf.toString('utf8'); for(const [name,re] of patterns){ const m=txt.match(re); if(m) findings.push({file:path.relative(staging,p),pattern:name,count:m.length}); } } } }
walk(staging);
const scan={status:findings.length?'FAIL':'PASS',patterns:patterns.map(p=>p[0]),findings};
fs.writeFileSync(path.join(staging,'NO_SECRETS_SCAN.json'),JSON.stringify(scan,null,2));
if (findings.length) throw new Error('secret scan failed: '+JSON.stringify(findings));
const tarPath=path.join(base,'ge2-r13-promotion-20260630.tar.gz');
execFileSync('tar',['-C',staging,'-czf',path.join(root,tarPath),'.']);
const sha=crypto.createHash('sha256').update(fs.readFileSync(tarPath)).digest('hex');
const summary={classification:'GE2_NATIVE_COMMAND_SURFACE_PROMOTED',tarPath,sha256:sha,noSecretsScan:'PASS',copiedCount:copied.length,missing,gitCommitStatus:manifest.gitCommitStatus,sourceCommit:manifest.sourceCommit};
fs.writeFileSync(path.join(base,'bundle-summary.json'),JSON.stringify(summary,null,2));
fs.writeFileSync(path.join(base,'ge2-r13-promotion-20260630.tar.gz.sha256'),`${sha}  ge2-r13-promotion-20260630.tar.gz\n`);
console.log(JSON.stringify(summary,null,2));
