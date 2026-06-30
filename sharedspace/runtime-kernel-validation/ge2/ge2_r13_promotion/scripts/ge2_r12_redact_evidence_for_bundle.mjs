import fs from 'node:fs';
import crypto from 'node:crypto';
const outDir='sharedspace/runtime-kernel-validation/ge2/ge2_r12_promotion_readiness_packet';
const raw='sharedspace/runtime-kernel-validation/ge2/ge2_r7_source_snapshot_repair_plan/r7_source_snapshot_trace_report_20260630.json';
const redacted=`${outDir}/sanitized/r7_source_snapshot_trace_report_20260630.REDACTED.json`;
fs.mkdirSync(`${outDir}/sanitized`,{recursive:true});
const patterns=[/sk-[A-Za-z0-9_-]{20,}/g,/gh[pousr]_[A-Za-z0-9_]{20,}/g,/\b\d{6,12}:[A-Za-z0-9_-]{30,}\b/g,/AKIA[0-9A-Z]{16}/g,/-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----/g];
let text=fs.readFileSync(raw,'utf8');
let redactions=0;
for(const re of patterns){ text=text.replace(re,()=>{redactions++; return '[REDACTED_SECRET_LIKE_VALUE]';}); }
fs.writeFileSync(redacted,text);
function sha(p){return crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');}
const evPath=`${outDir}/r12_evidence.json`;
const ev=JSON.parse(fs.readFileSync(evPath,'utf8'));
ev.artifactInventory=ev.artifactInventory.filter(x=>x.path!==raw);
ev.artifactInventory.push({path:redacted,sha256:sha(redacted),bytes:fs.statSync(redacted).size,sanitizedFrom:raw,redactions});
ev.redactions=[...(ev.redactions||[]),{raw,redacted,redactions,reason:'secret-like patterns excluded from DR bundle'}];
fs.writeFileSync(evPath,JSON.stringify(ev,null,2));
console.log(JSON.stringify({ok:true,raw,redacted,redactions,redactedSha256:sha(redacted)},null,2));
