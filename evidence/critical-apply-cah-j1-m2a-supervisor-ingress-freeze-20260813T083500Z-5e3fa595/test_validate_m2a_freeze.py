#!/usr/bin/env python3
from pathlib import Path
import copy,json,tempfile,shutil,sys
ROOT=Path(__file__).resolve().parent
DESIGN=Path('/home/stickai/.openclaw/workspace/design/critical-apply-supervisor-ingress-m2a-architecture-freeze-2026-08-13.md')
sys.path.insert(0,str(ROOT)); from validate_m2a_freeze import validate
CASES=[]
def case(name,file,mut,needle):CASES.append((name,file,mut,needle))
case('remove_owner','PATH-OWNERSHIP-MATRIX.json',lambda x:x['paths'][0].update({'creator':''}),'missing_owner')
case('allow_action_early','SUPERVISOR-CRASH-VECTORS.json',lambda x:x['vectors'][0].update({'action_allowed':True}),'permissive_crash_window')
case('reorder_authority','RECOVERY-AUTHORITY-ORDER.json',lambda x:x['order'].reverse(),'authority_order')
case('weaken_N07','CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda x:x['nonce_integration']['N07_RECORD_VERIFIED_OUTCOME'].pop(1),'N07_weakened')
case('weaken_N04','CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda x:x['nonce_integration'].update({'N04_SAFE_RESUME_REBIND':'resume freely'}),'N04_weakened')
case('progress_authoritative','RECOVERY-AUTHORITY-ORDER.json',lambda x:x.update({'ProgressDB_authoritative':True}),'authority_order')
case('omit_20_contention','CONCURRENCY-FENCING-VECTORS.json',lambda x:x.update({'vectors':[v for v in x['vectors'] if v.get('clients')!=20]}),'contention_thresholds')
case('runner_mkdir_nonce','PATH-OWNERSHIP-MATRIX.json',lambda x:next(v for v in x['paths'] if v['path']=='nonce-ledger/').update({'runner_may_mkdir':True}),'nonce_ledger_ownership')
case('runtime_authority','COMPONENT-TRUST-BOUNDARIES.json',lambda x:x.update({'runtime_authority':True}),'runtime_or_production_authority')
case('drop_crash_vectors','SUPERVISOR-CRASH-VECTORS.json',lambda x:x.update({'vectors':x['vectors'][:20]}),'crash_threshold')
case('duplicate_vector_id','ACK-REPLAY-VECTORS.json',lambda x:x['vectors'][1].update({'id':'AR-NEW'}),'vector_ids')
case('missing_design_xref','DESIGN',lambda x:None,'design_xref:ACK-REPLAY-VECTORS.json')
results=[]
for name,file,mut,needle in CASES:
 with tempfile.TemporaryDirectory() as td:
  t=Path(td)/'root'; shutil.copytree(ROOT,t,ignore=shutil.ignore_patterns('__pycache__','TEST-RESULTS.json','VALIDATION-RESULTS.json','PRIVACY*','STATUS.json','EVIDENCE-SHA256.txt'))
  d=Path(td)/'design.md'; shutil.copy2(DESIGN,d)
  if file=='DESIGN':d.write_text(d.read_text().replace('ACK-REPLAY-VECTORS.json','ACK_REPLAY_REMOVED.json'))
  else:
   p=t/file; o=json.loads(p.read_text()); mut(o); p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
  # refresh target hash so semantic validator, not seal mismatch, proves rejection
  seal=t/'ARTIFACT-SHA256.json'; s=json.loads(seal.read_text()); key='DESIGN' if file=='DESIGN' else file
  import hashlib; target=d if file=='DESIGN' else t/file; s['files'][key]=hashlib.sha256(target.read_bytes()).hexdigest(); seal.write_text(json.dumps(s,indent=2,sort_keys=True)+'\n')
  errs=validate(t,d); ok=any(needle in e for e in errs); results.append({'id':name,'expected_error':needle,'pass':ok,'errors':errs})
  if not ok: print(json.dumps(results,indent=2)); raise SystemExit(2)
print(json.dumps({'status':'PASS','case_count':len(results),'results':results},indent=2))
