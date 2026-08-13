#!/usr/bin/env python3
from pathlib import Path
import copy, hashlib, json, shutil, sys, tempfile

ROOT=Path('/tmp/cah-j1-m2a-r1-verify-53c12224')
DESIGN=Path('/home/stickai/.openclaw/workspace/design/critical-apply-supervisor-ingress-m2a-r1-contract-repair-2026-08-13.md')
OUT=Path('/home/stickai/.openclaw/workspace/evidence/critical-apply-cah-j1-m2a-r1-final-independent-verification-20260813T100100Z-53c12224/INDEPENDENT-ADVERSARIAL-TESTS.json')
sys.path.insert(0,str(ROOT))
from validate_m2a_r1 import validate

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def op(file, fn): return (file,fn)
CASES=[]
def case(cid, operations, clause): CASES.append((cid,operations,clause))

def jset(path, value):
 def f(o):
  x=o
  for k in path[:-1]: x=x[k]
  x[path[-1]]=value
 return f

def jdel(path):
 def f(o):
  x=o
  for k in path[:-1]: x=x[k]
  del x[path[-1]]
 return f

# Exact port of all 26 prior independently authored unsafe mutations.
case('P01_MISSING_PATH_OWNER',[op('PATH-OWNERSHIP-MATRIX.json',lambda o:o['paths'][0].update(creator=''))],'single creator/writer')
case('P02_DUPLICATE_PATH',[op('PATH-OWNERSHIP-MATRIX.json',lambda o:o['paths'].append(copy.deepcopy(o['paths'][0])))],'unique paths')
case('P03_PERMISSIVE_CRASH_BOUNDARY',[op('SUPERVISOR-CRASH-VECTORS.json',lambda o:o['vectors'][0].update(action_allowed=True))],'crash action false')
case('P04_STALE_PROGRESS_AUTHORITY',[op('RECOVERY-AUTHORITY-ORDER.json',lambda o:o.update(ProgressDB_authoritative=True))],'journal authority')
case('P05_OMIT_20_CONTENTION',[op('CONCURRENCY-FENCING-VECTORS.json',lambda o:o.update(vectors=[v for v in o['vectors'] if v.get('clients')!=20]))],'2/5/20')
case('P06_OVERLAP_DUAL_ACTIVE',[op('CONCURRENCY-FENCING-VECTORS.json',lambda o:(o.update(one_active_owner_per_overlapping_scope=False),next(v for v in o['vectors'] if 'OVERLAP' in v['id']).update(expected_max_active_overlapping_pair=5,expected='all overlapping may activate'))) ],'overlap exclusion')
case('P07_CHILD_SELF_REGISTRATION_PATH_CREATE',[op('CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda o:(o.update(child_forbidden=[]),o['launch_required'].clear()))],'child boundary')
case('P08_ACK_BEFORE_SYNC_BIND',[op('INGRESS-IDEMPOTENCY-CONTRACT.json',lambda o:o.update(acceptance_order=['return ACK','append canonical acceptance event','capture payload bytes into CAS']))],'ACK barrier order')
case('P09_REPLAY_CONFLICT_ALLOWED',[op('ACK-REPLAY-VECTORS.json',lambda o:next(v for v in o['vectors'] if v['id']=='AR-DUP-DIFFERENT').update(expected_outcome='ACCEPT_AND_EXECUTE'))],'replay conflict HOLD')
case('P10_STALE_FENCE_EPOCH_ACCEPTED',[op('CONCURRENCY-FENCING-VECTORS.json',lambda o:(o.update(checked_on_every_child_mutation_and_result=False),next(v for v in o['vectors'] if v['id']=='CF-STALE-FENCE-RESULT').update(expected='ACCEPT_STALE_RESULT'))) ],'stale fence reject')
case('P11_N04_CONTRADICTORY_BYPASS',[op('CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda o:o['nonce_integration']['N04_exact_conditions'].append('OR_resume_freely_after_call_start'))],'N04 no bypass')
case('P12_N07_REMOVE_JOURNAL_STEP',[op('CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda o:o['nonce_integration']['N07_exact_ordered_tokens'].pop(2))],'N07 exact order')
def intervene(o):
 q=copy.deepcopy(o['canonical_transitions'][21]);q.update(id='T21X',event='INTERVENING_CANONICAL_EVENT',**{'from':'SCOPE_LEASE_RELEASE_RECORDED','to':'INTERVENING'});o['canonical_transitions'].insert(22,q)
case('P13_CANONICAL_INTERVENING_CLOSE_EVENT',[op('SUPERVISOR-STATE-MACHINE.json',intervene)],'direct canonical adjacency')
case('P14_NOTIFICATION_AUTHORITY',[op('RECOVERY-AUTHORITY-ORDER.json',lambda o:o.update(notification_authoritative=True))],'notification nonsemantic')
case('P15_WITNESS_TERMINAL_AUTHORITY',[op('COMPONENT-TRUST-BOUNDARIES.json',lambda o:next(x for x in o['components'] if x['component']=='future_checker').update(authority='terminal semantic authority'))],'witness nonsemantic')
case('P16_UNKNOWN_OUTCOME_RETRY',[op('CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda o:o.update(unknown_outcome='AUTOMATIC_RETRY_ALLOWED'))],'unknown terminal')
case('P17_RUNTIME_AUTHORITY',[op('COMPONENT-TRUST-BOUNDARIES.json',lambda o:o.update(runtime_authority=True))],'runtime nonauthority')
case('P18_SHADOW_AUTHORITY',[op('ZERO-EFFECT-CONTRACT.json',lambda o:o.update(shadow_outputs_authoritative=True))],'shadow nonauthority')
case('P19_MISSING_TRANSITION_SIDE',[op('SUPERVISOR-CRASH-VECTORS.json',lambda o:o['vectors'].pop(1))],'exact before/after')
case('P20_GENERIC_RECOVERY_PROOF',[op('SUPERVISOR-CRASH-VECTORS.json',lambda o:o['vectors'][0].update(recovery_proof_ids=['something durable']))],'side-specific proof')
case('P21_NONCE_SUFFIX_SEMANTICS',[op('CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda o:o['nonce_integration']['required_transition_ids'].__setitem__(6,'N07_SKIP_CAS_AND_BIND'))],'exact nonce identities')
case('P22_STATE_CALL_BEFORE_NONCE',[op('SUPERVISOR-STATE-MACHINE.json',lambda o:o['canonical_transitions'][7].update(provider_call_allowed=True))],'provider gate false')
case('P23_STATE_ACTION_BEFORE_SCOPE',[op('SUPERVISOR-STATE-MACHINE.json',lambda o:o['canonical_transitions'][0].update(action_allowed=True))],'action gate')
case('P24_PERMISSIVE_UNKNOWN_FIELDS',[op('INGRESS-ENVELOPE-CONTRACT.json',lambda o:o['canonical_json'].update(unknown_fields='allow'))],'strict ingress')
case('P25_MULTIPLE_PATH_WRITERS',[op('PATH-OWNERSHIP-MATRIX.json',lambda o:o['paths'][0].update(writer='supervisor_materializer+child'))],'scalar writer')
case('P26_ACK_VECTOR_BEFORE_SYNC',[op('ACK-REPLAY-VECTORS.json',lambda o:next(v for v in o['vectors'] if v['id']=='AR-NEW').update(expected_outcome='ACK_BEFORE_COMMIT_SYNC'))],'meaningful ACK')

# Fresh independent mutations: strictness, cross-artifact consistency, authority binding, and combinations.
case('F27_NEAR_PREFIX_SCHEMA_ACCEPTANCE',[op('SUPERVISOR-STATE-MACHINE.json',lambda o:o.update(schema='critical_apply.m2a_EVIL'))],'exact schema identity')
case('F28_UNKNOWN_STATE_TOP_LEVEL',[op('SUPERVISOR-STATE-MACHINE.json',lambda o:o.update(untrusted_extension={'provider_call_allowed':True}))],'strict schema no unknowns')
case('F29_UNKNOWN_CRASH_VECTOR_FIELD',[op('SUPERVISOR-CRASH-VECTORS.json',lambda o:o['vectors'][0].update(untrusted_authority='provider'))],'strict nested schema')
case('F30_CHILD_ACTION_MEANING_PROVIDER',[op('CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda o:o.update(action_allowed_meaning='provider_call_eligibility'))],'state-child action consistency')
case('F31_CHILD_MUTATION_FENCE_REMOVED',[op('CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda o:o['every_mutation_and_result_requires'].remove('supervisor_epoch'))],'child/concurrency fence consistency')
case('F32_CHILD_RESULT_ACK_FIRST',[op('CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda o:o.update(result_order=['ACK immediately','capture bytes later']))],'child/ACK ordering consistency')
case('F33_CHILD_FUTURE_GATE_OMITS_N06',[op('CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda o:o['nonce_integration']['future_provider_gate_not_active'].pop(1))],'future N05+N06 complete inactive')
case('F34_STATE_ACTION_REQUIRES_OMIT_SCOPE',[op('SUPERVISOR-STATE-MACHINE.json',lambda o:o['action_semantics']['requires'].pop(0))],'typed bounded action barriers')
case('F35_DECLARED_CLOSE_ADJACENCY_WRONG',[op('SUPERVISOR-STATE-MACHINE.json',lambda o:o.update(canonical_close_adjacency=['SUPERVISOR_CLOSED','COMPLETION_RECEIPT_PUBLISHED']))],'declaration-derived consistency')
case('F36_CANONICAL_STATE_CHAIN_DRIFT',[op('SUPERVISOR-STATE-MACHINE.json',lambda o:o['canonical_state_chain'].__setitem__(9,'PROVIDER_CALL_ACTIVE'))],'state/transition exact consistency')
case('F37_TRANSITION_AUTHORITY_PROVIDER',[op('SUPERVISOR-STATE-MACHINE.json',lambda o:o['canonical_transitions'][9].update(authority='provider'))],'transition/component authority consistency')
def first_from(o): o['canonical_transitions'][0]['from']='UNTRUSTED'; o['vectors'][0]['observed_state']='UNTRUSTED'
# This combination is split across artifacts below.
case('F38_FIRST_PREIMAGE_FROM_AND_CRASH_COMBO',[op('SUPERVISOR-STATE-MACHINE.json',lambda o:o['canonical_transitions'][0].update({'from':'UNTRUSTED'})),op('SUPERVISOR-CRASH-VECTORS.json',lambda o:o['vectors'][0].update(observed_state='UNTRUSTED'))],'exact initial transition')
case('F39_ACK_INPUT_CASE_MEANINGLESS',[op('ACK-REPLAY-VECTORS.json',lambda o:o['vectors'][0].update(input_case='x'))],'meaningful typed ACK inputs')
case('F40_SAME_SCOPE_VECTOR_MADE_DISJOINT',[op('CONCURRENCY-FENCING-VECTORS.json',lambda o:next(v for v in o['vectors'] if v['id']=='CF-SAME-SCOPE-5').update(scopes=['a','b','c','d','e']))],'content/expected concurrency consistency')
case('F41_OVERLAP_VECTOR_MADE_DISJOINT',[op('CONCURRENCY-FENCING-VECTORS.json',lambda o:next(v for v in o['vectors'] if 'OVERLAP' in v['id']).update(scopes=['a','b','c','d','e']))],'overlap content')
case('F42_DISJOINT_VECTOR_MADE_IDENTICAL',[op('CONCURRENCY-FENCING-VECTORS.json',lambda o:next(v for v in o['vectors'] if 'DISJOINT' in v['id']).update(scopes=['same']*20))],'disjoint content')
case('F43_PATH_RENAMED_UNTRUSTED',[op('PATH-OWNERSHIP-MATRIX.json',lambda o:o['paths'][0].update(path='/untrusted/absolute/path'))],'exact trusted path inventory')
case('F44_SCALAR_WRITER_WRONG_AUTHORITY',[op('PATH-OWNERSHIP-MATRIX.json',lambda o:o['paths'][0].update(writer='untrusted_child'))],'exact creator/writer authority')
case('F45_COMPONENT_CAS_AUTHORITY_REMOVED',[op('COMPONENT-TRUST-BOUNDARIES.json',lambda o:next(x for x in o['components'] if x['component']=='descriptor_cas').update(authority='none'))],'component contract equality')
case('F46_UNKNOWN_COMPONENT_ADDED',[op('COMPONENT-TRUST-BOUNDARIES.json',lambda o:o['components'].append({'component':'untrusted_provider','authority':'none'}))],'strict component schema')
case('F47_M0_R3_BINDING_TAMPER',[op('IMMUTABLE-INPUT-SEALS.json',lambda o:o['inputs']['m0_r3_contract'].update(manifest_sha256='0'*64))],'all M0-R3 inputs bound')
case('F48_M1_PASS_BINDING_TAMPER',[op('IMMUTABLE-INPUT-SEALS.json',lambda o:o['inputs']['m1_pass_verified'].update(evidence_sha256_file_sha256='0'*64))],'M1 preservation authority bound')
case('F49_DESIGN_CONTRADICTION',[op('DESIGN',lambda p:p.write_text(p.read_text()+'\nContradiction: provider calls and runtime activation are now allowed in M2A.\n'))],'substantive design cross-reference')
case('F50_TRANSITION_UNKNOWN_PROVIDER_FLAG',[op('SUPERVISOR-STATE-MACHINE.json',lambda o:o['canonical_transitions'][0].update(provider_authority_granted=True))],'strict transition schema')
case('F51_ACK_UNKNOWN_EXECUTION_FLAG',[op('ACK-REPLAY-VECTORS.json',lambda o:o['vectors'][2].update(execute_on_conflict=True))],'strict ACK schema')
case('F52_MULTI_ARTIFACT_AUTHORITY_WEAKENING',[op('SUPERVISOR-STATE-MACHINE.json',lambda o:(o['canonical_transitions'][9].update(authority='provider'),o['action_semantics'].update(requires=[]))),op('CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda o:(o.update(action_allowed_meaning='provider call'),o['every_mutation_and_result_requires'].clear())),op('CONCURRENCY-FENCING-VECTORS.json',lambda o:o.update(checked_on_every_child_mutation_and_result=False))],'combination authority/fence attack')
case('F53_N07_ALTERNATE_CAS_AND_REORDER_COMBO',[op('CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda o:o['nonce_integration'].update(N07_exact_ordered_tokens=['TRUST_PROVIDER_SHA','AUTHORITYDB_BEGIN_IMMEDIATE','JOURNAL_LATER']))],'alternate CAS combination')
case('F54_INGRESS_AND_M2B_ACTIVATION_COMBO',[op('INGRESS-ENVELOPE-CONTRACT.json',lambda o:(o.update(untrusted_paths_allowed=True),o['canonical_json'].update(unknown_fields='allow'))),op('M2B-PROMOTION-GATES.json',lambda o:o.update(runtime_integration_allowed_now=True))],'ingress+activation combination')
case('F55_NONCE_ORDER_DUPLICATE_SUFFIX_COMBO',[op('CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda o:(o['nonce_integration']['required_transition_ids'].__setitem__(6,'N06_DURABLY_CONSUME'),o['nonce_integration']['transitions'][6].update(id='N07_ALT',order=6,semantic='provider direct')))],'nonce full equality combination')
case('F56_CRASH_SIDE_STATE_PROOF_COMBO',[op('SUPERVISOR-CRASH-VECTORS.json',lambda o:(o['vectors'][0].update(side='AFTER_COMMIT',observed_state='ROOT_REGISTERED',recovery_proof_ids=['generic']),o['vectors'][1].update(side='AFTER_COMMIT')))],'crash side/state/proof combination')

base_errors=validate(ROOT,DESIGN)
if base_errors:
 print(json.dumps({'status':'HOLD_BASE','errors':base_errors},indent=2)); raise SystemExit(2)

# Positive direct assertions against M0-R3/M1 mandatory semantics; these do not trust validator success.
sm=json.loads((ROOT/'SUPERVISOR-STATE-MACHINE.json').read_text())
cv=json.loads((ROOT/'SUPERVISOR-CRASH-VECTORS.json').read_text())
ch=json.loads((ROOT/'CHILD-LAUNCH-AND-RESULT-CONTRACT.json').read_text())
events=[t['event'] for t in sm['canonical_transitions']]
close_i=events.index('SUPERVISOR_CLOSED')
direct_checks=[
 {'id':'D01_RELEASE_CLOSE_ADJACENT','pass':events[close_i-1:close_i+1]==['SCOPE_LEASE_RELEASE_RECORDED','SUPERVISOR_CLOSED']},
 {'id':'D02_SUPERVISOR_CLOSED_FINAL_CANONICAL','pass':close_i==len(events)-1,'actual_canonical_after_close':events[close_i+1:]},
 {'id':'D03_RECEIPT_PUBLICATION_ARTIFACT_ONLY','pass':'COMPLETION_RECEIPT_PUBLISHED' not in events},
 {'id':'D04_LOCK_RELEASE_NOT_CANONICAL_EVENT','pass':'TRANSACTION_LOCK_RELEASED' not in events},
 {'id':'D05_CLOSEOUT_HEAD_IMMUTABLE_BY_PUBLICATION','pass':sm.get('receipt_publication_alters_closeout_head') is False},
 {'id':'D06_TYPED_PROOF_REGISTRY_PRESENT','pass':isinstance(cv.get('proof_registry'),dict) and bool(cv.get('proof_registry'))},
 {'id':'D07_ALL_VECTOR_PROOFS_RESOLVE_WITH_CONTENT','pass':False},
 {'id':'D08_CHILD_ACTION_MEANING_MATCHES_STATE','pass':ch.get('action_allowed_meaning')==sm.get('action_semantics',{}).get('meaning')},
 {'id':'D09_CHILD_FUTURE_GATE_MATCHES_STATE','pass':ch.get('nonce_integration',{}).get('future_provider_gate_not_active')==sm.get('provider_call_semantics',{}).get('future_gate_not_active')},
]
reg=cv.get('proof_registry',{})
if isinstance(reg,dict) and reg:
 direct_checks[6]['pass']=all(pid in reg and isinstance(reg[pid],dict) and bool(reg[pid]) for v in cv.get('vectors',[])+cv.get('artifact_vectors',[]) for pid in v.get('recovery_proof_ids',[]))

results=[]
for cid,operations,clause in CASES:
 with tempfile.TemporaryDirectory(prefix='cah-j1-m2a-r1-independent-',dir='/tmp') as td:
  r=Path(td)/'candidate'; shutil.copytree(ROOT,r,ignore=shutil.ignore_patterns('__pycache__'))
  d=Path(td)/'design.md'; shutil.copy2(DESIGN,d)
  changed=[]
  for file,fn in operations:
   p=d if file=='DESIGN' else r/file
   if file=='DESIGN': fn(p); key='DESIGN'
   else:
    o=json.loads(p.read_text()); fn(o); p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n'); key=file
   changed.append((key,p))
  seal=json.loads((r/'ARTIFACT-SHA256.json').read_text())
  for key,p in changed: seal['files'][key]=sha(p)
  (r/'ARTIFACT-SHA256.json').write_text(json.dumps(seal,indent=2,sort_keys=True)+'\n')
  errors=validate(r,d); rejected=bool(errors)
  results.append({'id':cid,'clause':clause,'validator_rejected':rejected,'gate_result':'PASS_REJECTED' if rejected else 'FAIL_ACCEPTED_UNSAFE','errors':errors})

obj={'schema':'critical_apply.m2a_r1.final_independent_adversarial.v1','status':'PASS' if all(x['validator_rejected'] for x in results) and all(x['pass'] for x in direct_checks) else 'HOLD','base_validator_errors':base_errors,'case_count':len(results),'rejected_count':sum(x['validator_rejected'] for x in results),'unsafe_accepted_count':sum(not x['validator_rejected'] for x in results),'direct_check_count':len(direct_checks),'direct_failure_count':sum(not x['pass'] for x in direct_checks),'direct_checks':direct_checks,'results':results}
OUT.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:obj[k] for k in ['status','case_count','rejected_count','unsafe_accepted_count','direct_check_count','direct_failure_count']},indent=2))
raise SystemExit(0 if obj['status']=='PASS' else 2)
