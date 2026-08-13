#!/usr/bin/env python3
import hashlib,json,shutil
from pathlib import Path
ws=Path('/home/stickai/.openclaw/workspace')
out=ws/'evidence/critical-apply-cah-j1-m2a-final-independent-verification-20260813T090945Z-b48fbacb'
cand=ws/'evidence/critical-apply-cah-j1-m2a-supervisor-ingress-freeze-20260813T083500Z-5e3fa595'
design=ws/'design/critical-apply-supervisor-ingress-m2a-architecture-freeze-2026-08-13.md'
scan=out/'scan-inputs'; scan.mkdir(exist_ok=True)
source_names=['COMPONENT-TRUST-BOUNDARIES.json','INGRESS-ENVELOPE-CONTRACT.json','SUPERVISOR-STATE-MACHINE.json','INGRESS-IDEMPOTENCY-CONTRACT.json','PATH-OWNERSHIP-MATRIX.json','SUPERVISOR-CRASH-VECTORS.json','CONCURRENCY-FENCING-VECTORS.json','ACK-REPLAY-VECTORS.json','CHILD-LAUNCH-AND-RESULT-CONTRACT.json','RECOVERY-AUTHORITY-ORDER.json','M2B-PROMOTION-GATES.json','ZERO-EFFECT-CONTRACT.json','IMMUTABLE-INPUT-SEALS.json','ARTIFACT-SHA256.json','validate_m2a_freeze.py','test_validate_m2a_freeze.py']
for name in source_names: shutil.copy2(cand/name,scan/name)
shutil.copy2(design,scan/'M2A-DESIGN.md')
scanner=cand/'bin/r6_bounded_privacy_scanner.py'; (out/'bin').mkdir(exist_ok=True)
scanner_dst=out/'bin/r6_bounded_privacy_scanner.py'
if not scanner_dst.exists(): shutil.copy2(scanner,scanner_dst)
# Exact hash-bound inputs include design, every M2A fixture/validator/test file, scanner, and current independent receipts/source.
rels=['bin/r6_bounded_privacy_scanner.py']+[f'scan-inputs/{x}' for x in source_names+['M2A-DESIGN.md']]+['START.md','PRE-REPO-STATE.md','PRE-TRACKED-STATUS.txt','PRE-STATE.json','INPUT-BINDING.json','M1-PRESERVATION-RECONSTRUCTION.json','DIRECT-FINDINGS.json','INDEPENDENT-ADVERSARIAL-TESTS.json','TEST-RESULTS.json','FINDINGS.json','ZERO-EFFECT.json','independent_verify.py','prepare_privacy_scan.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
obj={'schema':'critical_apply.cah_j1.m2a.final_independent_privacy_inputs.v1','files':{r:{'sha256':sha(out/r)} for r in sorted(rels)}}
(out/'frozen-tool-identities.json').write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
print(json.dumps({'copied_candidate_inputs':len(source_names)+1,'exact_scan_inputs':len(rels),'scanner_sha256':sha(out/'bin/r6_bounded_privacy_scanner.py')},indent=2))
