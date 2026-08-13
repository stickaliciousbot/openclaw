#!/usr/bin/env python3
from pathlib import Path
import copy,json,tempfile,shutil,sys,hashlib
ROOT=Path(__file__).resolve().parent; DESIGN=Path('/home/stickai/.openclaw/workspace/design/critical-apply-supervisor-ingress-m2a-r1-contract-repair-2026-08-13.md')
sys.path.insert(0,str(ROOT));from validate_m2a_r1 import validate
C=[]
def c(i,f,m,n):C.append((i,f,m,n))
c('ADV01_MISSING_PATH_OWNER','PATH-OWNERSHIP-MATRIX.json',lambda o:o['paths'][0].update(creator=''),'path_multiple_or_missing_writer')
c('ADV02_DUPLICATE_PATH','PATH-OWNERSHIP-MATRIX.json',lambda o:o['paths'].append(copy.deepcopy(o['paths'][0])),'path_exact_ownership')
c('ADV03_PERMISSIVE_CRASH_BOUNDARY','SUPERVISOR-CRASH-VECTORS.json',lambda o:o['vectors'][0].update(action_allowed=True),'crash_permissive')
c('ADV04_STALE_PROGRESS_AUTHORITY','RECOVERY-AUTHORITY-ORDER.json',lambda o:o.update(ProgressDB_authoritative=True),'recovery_authority')
c('ADV05_OMIT_20_CONTENTION','CONCURRENCY-FENCING-VECTORS.json',lambda o:o.update(vectors=[v for v in o['vectors'] if v.get('clients')!=20]),'contention_thresholds')
c('ADV06_OVERLAP_DUAL_ACTIVE','CONCURRENCY-FENCING-VECTORS.json',lambda o:(o.update(one_active_owner_per_overlapping_scope=False),next(v for v in o['vectors'] if 'OVERLAP' in v['id']).update(expected_max_active_overlapping_pair=5,expected='all overlapping may activate')),'concurrency_global')
c('ADV07_CHILD_SELF_REGISTRATION_AND_PATH_CREATE','CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda o:(o.update(child_forbidden=[]),o['launch_required'].clear()),'child_boundary')
c('ADV08_ACK_BEFORE_SYNC_BIND','INGRESS-IDEMPOTENCY-CONTRACT.json',lambda o:o.update(acceptance_order=['return ACK','append canonical acceptance event','capture payload bytes into CAS']),'ack_order_replay')
c('ADV09_REPLAY_CONFLICT_ALLOWED','ACK-REPLAY-VECTORS.json',lambda o:next(v for v in o['vectors'] if v['id']=='AR-DUP-DIFFERENT').update(expected_outcome='ACCEPT_AND_EXECUTE'),'ack_vector_content')
c('ADV10_STALE_FENCE_EPOCH_ACCEPTED','CONCURRENCY-FENCING-VECTORS.json',lambda o:(o.update(checked_on_every_child_mutation_and_result=False),next(v for v in o['vectors'] if v['id']=='CF-STALE-FENCE-RESULT').update(expected='ACCEPT_STALE_RESULT')),'concurrency_global')
c('ADV11_N04_CONTRADICTORY_BYPASS','CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda o:o['nonce_integration']['N04_exact_conditions'].append('OR_resume_freely_after_call_start'),'N04_exact_no_bypass')
c('ADV12_N07_REMOVE_JOURNAL_STEP','CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda o:o['nonce_integration']['N07_exact_ordered_tokens'].pop(2),'N07_exact_order')
def intervene(o):
 q=copy.deepcopy(o['canonical_transitions'][21]);q.update(id='T21X',event='INTERVENING_CANONICAL_EVENT',**{'from':'SCOPE_LEASE_RELEASE_RECORDED','to':'INTERVENING'});o['canonical_transitions'].insert(22,q)
c('ADV13_CANONICAL_INTERVENING_CLOSE_EVENT','SUPERVISOR-STATE-MACHINE.json',intervene,'canonical_exact_chain')
c('ADV14_NOTIFICATION_AUTHORITY','RECOVERY-AUTHORITY-ORDER.json',lambda o:o.update(notification_authoritative=True),'recovery_authority')
c('ADV15_WITNESS_TERMINAL_AUTHORITY','COMPONENT-TRUST-BOUNDARIES.json',lambda o:next(x for x in o['components'] if x['component']=='future_checker').update(authority='terminal semantic authority'),'nonsemantic_component_authority')
c('ADV16_UNKNOWN_OUTCOME_RETRY','CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda o:o.update(unknown_outcome='AUTOMATIC_RETRY_ALLOWED'),'unknown_outcome_terminal')
c('ADV17_RUNTIME_AUTHORITY','COMPONENT-TRUST-BOUNDARIES.json',lambda o:o.update(runtime_authority=True),'component_authority')
c('ADV18_SHADOW_AUTHORITY','ZERO-EFFECT-CONTRACT.json',lambda o:o.update(shadow_outputs_authoritative=True),'zero_effect_boundary')
c('ADV19_MISSING_TRANSITION_SIDE','SUPERVISOR-CRASH-VECTORS.json',lambda o:o['vectors'].pop(1),'crash_count')
c('ADV20_GENERIC_RECOVERY_PROOF','SUPERVISOR-CRASH-VECTORS.json',lambda o:o['vectors'][0].update(recovery_proof_ids=['something durable']),'crash_transition_binding')
c('ADV21_NONCE_SUFFIX_SEMANTICS','CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda o:o['nonce_integration']['required_transition_ids'].__setitem__(6,'N07_SKIP_CAS_AND_BIND'),'nonce_exact_identity_order')
c('ADV22_STATE_CALL_BEFORE_NONCE','SUPERVISOR-STATE-MACHINE.json',lambda o:o['canonical_transitions'][7].update(provider_call_allowed=True),'provider_call_gate')
c('ADV23_STATE_ACTION_BEFORE_SCOPE','SUPERVISOR-STATE-MACHINE.json',lambda o:o['canonical_transitions'][0].update(action_allowed=True),'action_gate')
c('ADV24_PERMISSIVE_UNKNOWN_FIELDS','INGRESS-ENVELOPE-CONTRACT.json',lambda o:o['canonical_json'].update(unknown_fields='allow'),'ingress_strict')
c('ADV25_MULTIPLE_PATH_WRITERS','PATH-OWNERSHIP-MATRIX.json',lambda o:o['paths'][0].update(writer='supervisor_materializer+child'),'path_multiple_or_missing_writer')
c('ADV26_ACK_VECTOR_BEFORE_SYNC','ACK-REPLAY-VECTORS.json',lambda o:next(v for v in o['vectors'] if v['id']=='AR-NEW').update(expected_outcome='ACK_BEFORE_COMMIT_SYNC'),'ack_vector_content')
if validate(ROOT,DESIGN):print(json.dumps({'status':'HOLD_BASE','errors':validate(ROOT,DESIGN)},indent=2));raise SystemExit(2)
res=[]
for cid,file,fn,needle in C:
 with tempfile.TemporaryDirectory(prefix='m2a-r1-independent-port-',dir='/tmp') as td:
  r=Path(td)/'candidate';shutil.copytree(ROOT,r,ignore=shutil.ignore_patterns('__pycache__','*RESULTS.json','PRIVACY*','STATUS.json','EVIDENCE-SHA256.txt','SOURCE-MANIFEST.json','ZERO-EFFECT-RECEIPT.json'))
  d=Path(td)/'design.md';shutil.copy2(DESIGN,d);p=r/file;o=json.loads(p.read_text());fn(o);p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
  s=json.loads((r/'ARTIFACT-SHA256.json').read_text());s['files'][file]=hashlib.sha256(p.read_bytes()).hexdigest();(r/'ARTIFACT-SHA256.json').write_text(json.dumps(s,indent=2,sort_keys=True)+'\n')
  errs=validate(r,d);ok=needle in errs;res.append({'id':cid,'expected_error':needle,'validator_rejected':bool(errs),'specific_gate_pass':ok,'errors':errs,'gate_result':'PASS_REJECTED' if ok else 'FAIL'})
  if not ok:print(json.dumps({'status':'HOLD','results':res},indent=2));raise SystemExit(2)
print(json.dumps({'status':'PASS','case_count':len(res),'rejected_count':len(res),'unsafe_accepted_count':0,'results':res},indent=2))
