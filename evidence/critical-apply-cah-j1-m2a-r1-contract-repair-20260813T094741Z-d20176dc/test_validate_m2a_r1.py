#!/usr/bin/env python3
from pathlib import Path
import copy, json, tempfile, shutil, sys, hashlib
ROOT=Path(__file__).resolve().parent
DESIGN=Path('/home/stickai/.openclaw/workspace/design/critical-apply-supervisor-ingress-m2a-r1-contract-repair-2026-08-13.md')
sys.path.insert(0,str(ROOT)); from validate_m2a_r1 import validate
CASES=[]
def case(name,file,mut,needle):CASES.append((name,file,mut,needle))
# Original 12 preserved
case('ORIG01_remove_owner','PATH-OWNERSHIP-MATRIX.json',lambda x:x['paths'][0].update(creator=''),'path_multiple_or_missing_writer')
case('ORIG02_allow_action_crash','SUPERVISOR-CRASH-VECTORS.json',lambda x:x['vectors'][0].update(action_allowed=True),'crash_permissive')
case('ORIG03_reorder_authority','RECOVERY-AUTHORITY-ORDER.json',lambda x:x['order'].reverse(),'recovery_authority')
case('ORIG04_weaken_N07','CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda x:x['nonce_integration']['N07_exact_ordered_tokens'].pop(1),'N07_exact_order')
case('ORIG05_weaken_N04','CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda x:x['nonce_integration'].update(N04_exact_conditions=['resume freely']),'N04_exact_no_bypass')
case('ORIG06_progress_authoritative','RECOVERY-AUTHORITY-ORDER.json',lambda x:x.update(ProgressDB_authoritative=True),'recovery_authority')
case('ORIG07_omit_20_contention','CONCURRENCY-FENCING-VECTORS.json',lambda x:x.update(vectors=[v for v in x['vectors'] if v.get('clients')!=20]),'contention_thresholds')
case('ORIG08_runner_mkdir_nonce','PATH-OWNERSHIP-MATRIX.json',lambda x:next(v for v in x['paths'] if v['path']=='nonce-ledger/').update(runner_may_mkdir=True),'path_runner_create')
case('ORIG09_runtime_authority','COMPONENT-TRUST-BOUNDARIES.json',lambda x:x.update(runtime_authority=True),'component_authority')
case('ORIG10_drop_crash_vectors','SUPERVISOR-CRASH-VECTORS.json',lambda x:x.update(vectors=x['vectors'][:20]),'crash_count')
case('ORIG11_duplicate_vector_id','ACK-REPLAY-VECTORS.json',lambda x:x['vectors'][1].update(id='AR-NEW'),'ack_vector_ids')
case('ORIG12_missing_design_xref','DESIGN',lambda x:None,'design_xref:ACK-REPLAY-VECTORS.json')
# B01 canonical projection/adjacency
case('B01_intervening_canonical_event','SUPERVISOR-STATE-MACHINE.json',lambda x:x['canonical_transitions'].insert(22,dict(x['canonical_transitions'][21],id='T21X',event='INTERVENING_CANONICAL',**{'from':'SCOPE_LEASE_RELEASE_RECORDED','to':'INTERVENING'})),'canonical_exact_chain')
case('B01_wrong_close_from','SUPERVISOR-STATE-MACHINE.json',lambda x:next(t for t in x['canonical_transitions'] if t['event']=='SUPERVISOR_CLOSED').update({'from':'COMPLETION_RECEIPT_PREIMAGE_DURABLE'}),'canonical_adjacency')
case('B01_promote_preimage_state','SUPERVISOR-STATE-MACHINE.json',lambda x:x['canonical_state_chain'].append('COMPLETION_RECEIPT_PREIMAGE_DURABLE'),'preimage_promoted_canonical')
case('B01_artifact_wrong_head','SUPERVISOR-STATE-MACHINE.json',lambda x:x['artifact_preparations'][0].update(bound_to_release_head_sha256=False),'artifact_preparation_binding')
# B02 N07 optional/skipped/fake/reorder
case('B02_N07_optional','CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda x:x['nonce_integration']['N07_exact_ordered_tokens'].__setitem__(0,'CAPTURE_IF_REQUIRED'),'N07_exact_order')
case('B02_N07_skip_CAS','CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda x:x['nonce_integration']['N07_exact_ordered_tokens'].__delitem__(0),'N07_exact_order')
case('B02_N07_fake_CAS','CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda x:x['nonce_integration']['N07_exact_ordered_tokens'].__setitem__(1,'TRUST_REPORTED_SHA'),'N07_exact_order')
case('B02_N07_bind_early','CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda x:x['nonce_integration']['N07_exact_ordered_tokens'].reverse(),'N07_exact_order')
# B03 action/provider semantics
case('B03_provider_true','SUPERVISOR-STATE-MACHINE.json',lambda x:x['canonical_transitions'][9].update(provider_call_allowed=True),'provider_call_gate')
case('B03_call_alias_true','SUPERVISOR-STATE-MACHINE.json',lambda x:x['canonical_transitions'][9].update(call_allowed=True),'provider_call_gate')
case('B03_action_prescope','SUPERVISOR-STATE-MACHINE.json',lambda x:x['canonical_transitions'][0].update(action_allowed=True),'action_gate')
case('B03_action_before_launch_barrier','SUPERVISOR-STATE-MACHINE.json',lambda x:x['canonical_transitions'][8].update(action_allowed=True),'action_gate')
case('B03_action_after_execution','SUPERVISOR-STATE-MACHINE.json',lambda x:x['canonical_transitions'][12].update(action_allowed=True),'action_gate')
case('B03_child_provider_authority','CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda x:x.update(child_launch_implies_provider_authority=True),'child_provider_authority')
# B04 nonce exact identity/action/order/duplicate/missing
case('B04_suffix','CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda x:x['nonce_integration']['required_transition_ids'].__setitem__(6,'N07_SKIP_CAS'),'nonce_exact_identity_order')
case('B04_semantic_action','CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda x:x['nonce_integration']['transitions'][6].update(semantic='record outcome directly in DB'),'nonce_exact_semantics')
case('B04_order','CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda x:x['nonce_integration']['transitions'][5].update(order=7),'nonce_exact_identity_order')
case('B04_duplicate','CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda x:x['nonce_integration']['required_transition_ids'].__setitem__(5,'N05_COMMIT_CALL_START_BARRIER'),'nonce_exact_identity_order')
case('B04_missing','CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda x:x['nonce_integration']['transitions'].pop(),'nonce_exact_identity_order')
case('B04_predicate_removed','CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda x:x['nonce_integration']['transitions'][5]['critical_predicates'].pop(),'nonce_exact_predicates')
# B05 crash missing/duplicate/wrong state/proof/binding/permissive/artifact
case('B05_missing_side','SUPERVISOR-CRASH-VECTORS.json',lambda x:x['vectors'].pop(0),'crash_count')
case('B05_duplicate_side','SUPERVISOR-CRASH-VECTORS.json',lambda x:x['vectors'].__setitem__(1,copy.deepcopy(x['vectors'][0])),'crash_exact_sides')
case('B05_wrong_observed','SUPERVISOR-CRASH-VECTORS.json',lambda x:x['vectors'][1].update(observed_state='WRONG'),'crash_transition_binding')
case('B05_generic_proof','SUPERVISOR-CRASH-VECTORS.json',lambda x:x['vectors'][0].update(recovery_proof_ids=['something durable']),'crash_transition_binding')
case('B05_wrong_transition_binding','SUPERVISOR-CRASH-VECTORS.json',lambda x:x['vectors'][0].update(transition_id='T01'),'crash_exact_sides')
case('B05_provider_permissive','SUPERVISOR-CRASH-VECTORS.json',lambda x:x['vectors'][0].update(provider_call_allowed=True),'crash_permissive')
case('B05_artifact_count','SUPERVISOR-CRASH-VECTORS.json',lambda x:x['artifact_vectors'].pop(),'artifact_crash_vectors')
case('B05_artifact_promoted','SUPERVISOR-CRASH-VECTORS.json',lambda x:x['artifact_vectors'][0].update(transition_id='T21'),'artifact_crash_vectors')
# Direct B06 content gates
case('B06_overlap_dual_active','CONCURRENCY-FENCING-VECTORS.json',lambda x:next(v for v in x['vectors'] if 'OVERLAP' in v['id']).update(expected_max_active_overlapping_pair=2),'overlap_exclusion')
case('B06_stale_epoch_accept','CONCURRENCY-FENCING-VECTORS.json',lambda x:next(v for v in x['vectors'] if v['id']=='CF-STALE-EPOCH').update(expected='ACCEPT'),'stale_epoch_fence_rejection')
case('B06_child_create','PATH-OWNERSHIP-MATRIX.json',lambda x:x.update(child_may_create_shared_path=True),'child_path_creation')
case('B06_ack_early','INGRESS-IDEMPOTENCY-CONTRACT.json',lambda x:x['acceptance_order'].insert(0,x['acceptance_order'].pop()),'ack_order_replay')
case('B06_replay_execute','INGRESS-IDEMPOTENCY-CONTRACT.json',lambda x:x.update(different_proposal_same_event_id='ACCEPT_AND_EXECUTE'),'ack_order_replay')
case('B06_N04_bypass','CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda x:x['nonce_integration']['N04_exact_conditions'].append('OR_resume_freely'),'N04_exact_no_bypass')
case('B06_notification_authority','RECOVERY-AUTHORITY-ORDER.json',lambda x:x.update(notification_authoritative=True),'recovery_authority')
case('B06_witness_authority','COMPONENT-TRUST-BOUNDARIES.json',lambda x:x.update(WitnessDB_semantic_authority=True),'component_authority')
case('B06_unknown_retry','CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda x:x.update(unknown_outcome='AUTOMATIC_RETRY_ALLOWED'),'unknown_outcome_terminal')
case('B06_ingress_unknown','INGRESS-ENVELOPE-CONTRACT.json',lambda x:x['canonical_json'].update(unknown_fields='allow'),'ingress_strict')
case('B06_ingress_path','INGRESS-ENVELOPE-CONTRACT.json',lambda x:x.update(untrusted_paths_allowed=True),'ingress_strict')
case('B06_multiple_writer','PATH-OWNERSHIP-MATRIX.json',lambda x:x['paths'][0].update(writer='a+b'),'path_multiple_or_missing_writer')
case('B06_meaningless_ack','ACK-REPLAY-VECTORS.json',lambda x:x['vectors'][0].update(required_barriers=[]),'ack_vector_content')
case('B06_shadow_authority','ZERO-EFFECT-CONTRACT.json',lambda x:x.update(shadow_outputs_authoritative=True),'zero_effect_boundary')
case('B06_runtime_authority','COMPONENT-TRUST-BOUNDARIES.json',lambda x:x.update(runtime_authority=True),'component_authority')

def refreshed_copy(td,file,mut):
 t=Path(td)/'root';shutil.copytree(ROOT,t,ignore=shutil.ignore_patterns('__pycache__','TEST-RESULTS.json','VALIDATION-RESULTS.json','PRIVACY*','STATUS.json','EVIDENCE-SHA256.txt','SOURCE-MANIFEST.json','ZERO-EFFECT-RECEIPT.json'))
 d=Path(td)/'design.md';shutil.copy2(DESIGN,d)
 if file=='DESIGN':d.write_text(d.read_text().replace('ACK-REPLAY-VECTORS.json','ACK_REPLAY_REMOVED.json'))
 else:
  p=t/file;o=json.loads(p.read_text());mut(o);p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
 seal=t/'ARTIFACT-SHA256.json';s=json.loads(seal.read_text());key='DESIGN' if file=='DESIGN' else file;target=d if file=='DESIGN' else t/file;s['files'][key]=hashlib.sha256(target.read_bytes()).hexdigest();seal.write_text(json.dumps(s,indent=2,sort_keys=True)+'\n')
 return t,d
base=validate(ROOT,DESIGN)
if base:print(json.dumps({'status':'HOLD_BASE','errors':base},indent=2));raise SystemExit(2)
results=[]
for name,file,mut,needle in CASES:
 with tempfile.TemporaryDirectory(prefix='m2a-r1-mut-',dir='/tmp') as td:
  t,d=refreshed_copy(td,file,mut);errs=validate(t,d);ok=needle in errs;results.append({'id':name,'expected_error':needle,'pass':ok,'errors':errs})
  if not ok:print(json.dumps({'status':'HOLD_MUTATION','results':results},indent=2));raise SystemExit(2)
print(json.dumps({'status':'PASS','positive_fixture_count':1,'case_count':len(results),'rejected_count':sum(x['pass'] for x in results),'results':results},indent=2))
