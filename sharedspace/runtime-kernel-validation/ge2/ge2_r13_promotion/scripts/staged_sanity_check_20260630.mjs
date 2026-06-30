import fs from 'node:fs';
import { execFileSync } from 'node:child_process';
const names=execFileSync('git',['diff','--cached','--name-only'],{encoding:'utf8'}).trim().split(/\n/).filter(Boolean);
const forbidden=[/r7_source_snapshot_trace_report_20260630\.json$/,/r6_refined_registry_lifecycle_trace_20260630\.json$/,/\/preimage__/,/\/install_snapshots_/,/\/snapshots_/];
const bad=names.filter(n=>forbidden.some(r=>r.test(n)));
const out={status:bad.length?'FAIL':'PASS',count:names.length,bad,names};
fs.writeFileSync('sharedspace/runtime-kernel-validation/ge2/ge2_r13_promotion/staged-files-before-commit.json',JSON.stringify(out,null,2));
console.log(JSON.stringify({status:out.status,count:out.count,bad:out.bad},null,2));
if(bad.length) process.exit(2);
