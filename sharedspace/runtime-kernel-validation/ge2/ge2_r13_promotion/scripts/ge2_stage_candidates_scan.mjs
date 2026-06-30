import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
const roots=[
 'ge2-native-runtime',
 'plugins/ge2-command',
 'hooks/ge2-register',
 'sharedspace/runtime-kernel-validation/ge2',
 'sharedspace/disaster-recovery/ge2-r12-promotion-readiness-20260630',
 'sharedspace/disaster-recovery/ge2-r13-promotion-20260630'
];
const extra=[
 'MEMORY.md',
 'memory/2026-06-30.md',
 'memory/2026-06-30-ge2-r8-intake.md',
 'memory/2026-06-30-ge2-r8-result.md',
 'memory/2026-06-30-ge2-r9-intake.md',
 'memory/2026-06-30-ge2-r9-result.md',
 'memory/2026-06-30-ge2-r9-result-intake-final.md',
 'memory/2026-06-30-ge2-r10-intake.md',
 'memory/2026-06-30-ge2-r10-result.md',
 'memory/2026-06-30-ge2-r11-intake.md',
 'memory/2026-06-30-ge2-r11-result.md',
 'memory/2026-06-30-ge2-r11-telegram-p3-pass.md',
 'memory/2026-06-30-ge2-r11-telegram-p3-partial-addendum.md',
 'memory/2026-06-30-ge2-r11-telegram-run-accepted-addendum.md',
 'memory/2026-06-30-ge2-r11-final-pass.md',
 'memory/2026-06-30-ge2-r12-promotion-readiness-packet-ready.md',
 'memory/2026-06-30-ge2-r13-promotion.md',
 'memory/2026-06-30-ge2-r13-push-blocked-handoff-preserved.md',
 'memory/lessons-learned-ge2-native-command-surface-promotion-2026-06-30.md',
 'sharedspace/context-bridge/events.jsonl'
];
const excludeExact=new Set([
 'sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/r7_source_snapshot_trace_report_20260630.json',
 'sharedspace/runtime-kernel-validation/ge2/ge2_r6_command_module_identity/r6_refined_registry_lifecycle_trace_20260630.json'
]);
const excludeSubstrings=[
 '/snapshots_',
 '/install_snapshots_',
 '/preimage__',
 '/node_modules/',
 '/.git/'
];
const files=[];
function addFile(p){ p=p.replace(/^\.\//,''); if(!fs.existsSync(p)) return; const st=fs.statSync(p); if(st.isDirectory()) walk(p); else files.push(p); }
function walk(dir){ for(const ent of fs.readdirSync(dir,{withFileTypes:true})){ const p=path.join(dir,ent.name); const rel=p.replace(/^\.\//,''); if(excludeExact.has(rel)||excludeSubstrings.some(s=>rel.includes(s))) continue; if(ent.isDirectory()) walk(rel); else files.push(rel); } }
for(const r of roots) addFile(r);
for(const e of extra) addFile(e);
const uniq=[...new Set(files)].sort();
const patterns=[
 ['openai_api_key',/sk-[A-Za-z0-9_-]{20,}/g],
 ['github_pat',/gh[pousr]_[A-Za-z0-9_]{20,}/g],
 ['telegram_bot_token',/\b\d{6,}:[A-Za-z0-9_-]{20,}\b/g],
 ['aws_access_key',/AKIA[0-9A-Z]{16}/g],
 ['private_key_block',/-----BEGIN [A-Z ]*PRIVATE KEY-----/g]
];
const findings=[]; const skippedBinary=[];
for(const f of uniq){
 const buf=fs.readFileSync(f); const ext=path.extname(f).toLowerCase();
 if(buf.includes(0)||['.gz','.png','.jpg','.jpeg','.webp','.zip'].includes(ext)){ skippedBinary.push(f); continue; }
 if(buf.length>5*1024*1024){ skippedBinary.push(f); continue; }
 const txt=buf.toString('utf8');
 for(const [name,re] of patterns){ const m=txt.match(re); if(m) findings.push({file:f,pattern:name,count:m.length}); }
}
const out={status:findings.length?'FAIL':'PASS',count:uniq.length,findings,skippedBinary,excluded:[...excludeExact],files:uniq};
fs.writeFileSync('sharedspace/runtime-kernel-validation/ge2/ge2_r13_promotion/git-candidate-secret-scan.json',JSON.stringify(out,null,2));
console.log(JSON.stringify({status:out.status,count:out.count,findings:out.findings,skippedBinary:out.skippedBinary.length,excluded:out.excluded},null,2));
if(findings.length) process.exit(2);
if(process.argv.includes('--stage')){
 const batches=[]; for(let i=0;i<uniq.length;i+=100) batches.push(uniq.slice(i,i+100));
 for(const batch of batches) execFileSync('git',['add','--',...batch],{stdio:'inherit'});
 console.log(JSON.stringify({staged:true,count:uniq.length},null,2));
}
