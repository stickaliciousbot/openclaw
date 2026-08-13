#!/usr/bin/env python3
from pathlib import Path
import copy,hashlib,json,shutil,sys,tempfile
ROOT=Path(__file__).resolve().parent
DESIGN=Path('/home/stickai/.openclaw/workspace/design/critical-apply-supervisor-ingress-m2a-r2-r1-coherence-repair-2026-08-13.md')
sys.path.insert(0,str(ROOT));from validate_m2a_r2 import validate
def load(p):return json.loads(Path(p).read_text())
def dump(p,o):Path(p).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
CASES=[]
def c(i,ops):CASES.append((i,ops))
def op(f,fn):return(f,fn)
c('R2C01_LIFECYCLE_CANONICAL',[op('ARTIFACT-LIFECYCLE-CONTRACT.json',lambda o:o['lifecycle_operations'][0].update(canonical=True))])
c('R2C02_LIFECYCLE_SEMANTIC_AUTHORITY',[op('SUPERVISOR-STATE-MACHINE.json',lambda o:o['noncanonical_lifecycle_operations'][0].update(semantic_authority=True))])
c('R2C03_PUBLICATION_MUTATES_CLOSEOUT_HEAD',[op('ARTIFACT-LIFECYCLE-CONTRACT.json',lambda o:o['lifecycle_operations'][0].update(may_mutate_closeout_head=True))])
c('R2C04_LOCK_RELEASE_MUTATES_TERMINAL_HEAD',[op('SUPERVISOR-STATE-MACHINE.json',lambda o:o['noncanonical_lifecycle_operations'][1].update(may_mutate_terminal_decision_head=True))])
c('R2C05_MISSING_CLOSEOUT_PREREQUISITE',[op('ARTIFACT-LIFECYCLE-CONTRACT.json',lambda o:o['lifecycle_operations'][0].pop('prerequisite_exact_immutable_closeout_head'))])
c('R2C06_WRONG_LIFECYCLE_ORDER',[op('SUPERVISOR-STATE-MACHINE.json',lambda o:o['noncanonical_lifecycle_operations'].reverse())])
c('R2C07_RELEASE_WITHOUT_PUBLICATION_RECEIPT',[op('ARTIFACT-LIFECYCLE-CONTRACT.json',lambda o:o['lifecycle_operations'][1]['requires'].remove('COMPLETION_RECEIPT_PUBLICATION_RECEIPT_VERIFIED'))])
c('R2C08_PROOF_UNRESOLVED',[op('SUPERVISOR-CRASH-VECTORS.json',lambda o:o['vectors'][0].update(recovery_proof_ids=['RP-NOT-FOUND']))])
c('R2C09_PROOF_DUPLICATE_ID',[op('RECOVERY-PROOF-REGISTRY.json',lambda o:o['canonical_proofs'][1].update(id=o['canonical_proofs'][0]['id']))])
c('R2C10_PROOF_CROSS_SIDE_REUSE',[op('SUPERVISOR-CRASH-VECTORS.json',lambda o:o['vectors'][1].update(recovery_proof_ids=o['vectors'][0]['recovery_proof_ids']))])
c('R2C11_PROOF_WRONG_OBSERVED_STATE',[op('RECOVERY-PROOF-REGISTRY.json',lambda o:o['canonical_proofs'][0].update(observed_state='UNTRUSTED'))])
c('R2C12_PROOF_MISSING_TYPED_FIELD',[op('RECOVERY-PROOF-REGISTRY.json',lambda o:o['canonical_proofs'][0].pop('required_authoritydb_epoch'))])
c('R2C13_VECTOR_ACTION_AND_SCHEMA_EXTENSION',[op('SUPERVISOR-CRASH-VECTORS.json',lambda o:(o['vectors'][0].update(action_allowed=True),o['vectors'][0].update(extra_provider_flag=True)))])
c('R2C14_CHILD_CONCURRENCY_DUAL_DRIFT',[op('CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda o:o['every_mutation_and_result_requires'].remove('supervisor_epoch')),op('CONCURRENCY-FENCING-VECTORS.json',lambda o:o['required_child_mutation_and_result_fields'].remove('supervisor_epoch'))])
c('R2C15_CHILD_ACK_TRIPLE_DRIFT',[op('CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda o:o.update(result_order=['ACK first'])),op('INGRESS-IDEMPOTENCY-CONTRACT.json',lambda o:o.update(child_result_order=['ACK first'])),op('ACK-REPLAY-VECTORS.json',lambda o:o.update(child_result_order=['ACK first']))])
c('R2C16_PATH_COMPONENT_AUTHORITY_COMBO',[op('PATH-OWNERSHIP-MATRIX.json',lambda o:o['paths'][0].update(writer='child')),op('COMPONENT-TRUST-BOUNDARIES.json',lambda o:o['components'][0].update(authority='sole semantic authority'))])
c('R2C17_SCHEMA_PREFIX_AND_UNKNOWN_NESTED',[op('SUPERVISOR-STATE-MACHINE.json',lambda o:(o.update(schema=o['schema']+'_EVIL'),o['canonical_transitions'][0].update(provider=True)))])
c('R2C18_IMMUTABLE_SEAL_AND_DESIGN_CONTRADICTION',[op('IMMUTABLE-INPUT-SEALS.json',lambda o:o['inputs']['r1_independent_hold_manifest'].update(sha256='0'*64)),op('DESIGN',lambda p:p.write_text(p.read_text()+'\nProvider calls are allowed.\n'))])
if validate(ROOT,DESIGN):print(json.dumps({'status':'HOLD_BASE','errors':validate(ROOT,DESIGN)},indent=2));raise SystemExit(2)
res=[]
for cid,ops in CASES:
 with tempfile.TemporaryDirectory(prefix='cah-j1-m2a-r2-combo-',dir='/tmp') as td:
  r=Path(td)/'root';shutil.copytree(ROOT,r,ignore=shutil.ignore_patterns('__pycache__','*RESULTS.json','PRIVACY-RECEIPT.json','EVIDENCE-SHA256.txt'))
  d=Path(td)/'design.md';shutil.copy2(DESIGN,d);changed=[]
  for f,fn in ops:
   p=d if f=='DESIGN' else r/f
   if f=='DESIGN':fn(p);key='DESIGN'
   else:o=load(p);fn(o);dump(p,o);key=f
   changed.append((key,p))
  seal=load(r/'ARTIFACT-SHA256.json')
  for key,p in changed:seal['files'][key]=sha(p)
  dump(r/'ARTIFACT-SHA256.json',seal)
  errors=validate(r,d);res.append({'id':cid,'validator_rejected':bool(errors),'errors':errors})
obj={'schema':'critical_apply.m2a_r2.combination_attacks.v1','status':'PASS' if all(x['validator_rejected'] for x in res) else 'HOLD','case_count':len(res),'rejected_count':sum(x['validator_rejected'] for x in res),'unsafe_accepted_count':sum(not x['validator_rejected'] for x in res),'results':res}
print(json.dumps(obj,indent=2));raise SystemExit(0 if obj['status']=='PASS' else 2)
