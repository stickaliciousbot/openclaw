#!/usr/bin/env python3
from pathlib import Path
import json, hashlib, sys, re
REQ=['COMPONENT-TRUST-BOUNDARIES.json','INGRESS-ENVELOPE-CONTRACT.json','SUPERVISOR-STATE-MACHINE.json','INGRESS-IDEMPOTENCY-CONTRACT.json','PATH-OWNERSHIP-MATRIX.json','SUPERVISOR-CRASH-VECTORS.json','CONCURRENCY-FENCING-VECTORS.json','ACK-REPLAY-VECTORS.json','CHILD-LAUNCH-AND-RESULT-CONTRACT.json','RECOVERY-AUTHORITY-ORDER.json','M2B-PROMOTION-GATES.json','ZERO-EFFECT-CONTRACT.json','IMMUTABLE-INPUT-SEALS.json']
DESIGN_NAME='critical-apply-supervisor-ingress-m2a-r1-contract-repair-2026-08-13.md'
NONCE_IDS=['N01_RESERVE','N02_COMMIT_RESERVATION_EVENT','N03_BIND_RESERVATION','N04_SAFE_RESUME_REBIND','N05_COMMIT_CALL_START_BARRIER','N06_DURABLY_CONSUME','N07_RECORD_VERIFIED_OUTCOME','N08_CLASSIFY_UNKNOWN','N09_RETIRE_RECORDED_OUTCOME','N10_ABANDON_BEFORE_CALL','N11_QUARANTINE_ORPHAN_RESERVATION']
N07=['CAPTURE_GOVERNING_RESPONSE_OR_RECEIPT_BYTES_UNCONDITIONALLY_DESCRIPTOR_BOUND_CAS','REOPEN_VERIFY_EXACT_CAS_SHA256_SIZE_PATH','COMMIT_CALL_OUTCOME_RECORDED_REFERENCING_EXACT_CAS_OBJECT','SYNC_CANONICAL_JOURNAL','REOPEN_VERIFY_EXACT_OUTCOME_EVENT_AND_CAS_REFERENCE','AUTHORITYDB_BEGIN_IMMEDIATE','BIND_EXACT_OUTCOME_EVENT_AND_APPEND_AUTHORITY_RECEIPT','AUTHORITYDB_COMMIT_FULL','REOPEN_VERIFY_EXACT_AUTHORITYDB_BIND']
EVENTS=['REGISTER_TRANSACTION_ROOT','JOURNAL_GENESIS','SUPERVISOR_EPOCH_COMMITTED','INGRESS_ENVELOPE_CAPTURED','INGRESS_ACCEPTED','SCOPE_LEASE_RESERVED','SCOPE_LEASE_JOURNAL_COMMITTED','SCOPE_LEASE_ACTIVE','CHILD_LAUNCH_INTENT','CHILD_STARTED','CHILD_RESULT_CAPTURED','EXECUTION_AND_EVIDENCE_COMMITTED','OWNED_CHILDREN_RECONCILED','CLEANUP_RECORDED','TERMINAL_REDUCTION_PREPARED','TERMINAL_DECISION','TERMINAL_SEAL_RECORDED','NOTIFICATION_OUTCOME_RECORDED','INDEPENDENT_WITNESS_RECORDED','SCOPE_LEASE_RELEASE_INTENT','AUTHORITYDB_RELEASED','SCOPE_LEASE_RELEASE_RECORDED','SUPERVISOR_CLOSED','COMPLETION_RECEIPT_PUBLISHED','TRANSACTION_LOCK_RELEASED']
AUTH_ORDER=['canonical_journal','deterministic_reducer','terminal_manifest_and_seal','independent_witness','ProgressDB_projection','PID_registry_status','notification_projection']
ACK_ORDER=['capture all required payload bytes into descriptor-bound CAS','reopen verify exact CAS sha256 size path','append canonical acceptance event referencing exact CAS objects','sync canonical journal','reopen verify exact event bytes and CAS references','bind required AuthorityDB receipt if event reserves authority','COMMIT_FULL AuthorityDB','reopen verify exact AuthorityDB bind','return ACK']
ACK_EXPECT={'AR-NEW':('COMMIT_THEN_ORIGINAL_ACK',['CAS_REOPEN_VERIFIED','JOURNAL_SYNC_REOPEN_VERIFIED','AUTHORITYDB_BIND_REOPEN_VERIFIED_IF_REQUIRED']),'AR-DUP-SAME':('ORIGINAL_ACK_NO_APPEND_NO_EXECUTION',['ORIGINAL_JOURNAL_EVENT_REOPEN_VERIFIED']),'AR-DUP-DIFFERENT':('INTEGRITY_CONFLICT_HOLD_NO_EXECUTION_NO_ACTION_NO_PROVIDER_CALL',['EVENT_ID_MATCH','PROPOSAL_SHA_MISMATCH']),'AR-CRASH-POSTSYNC':('RETRY_RETURNS_ORIGINAL_ACK_NO_APPEND',['JOURNAL_SYNC_REOPEN_VERIFIED']),'AR-PROGRESS-DELETED':('JOURNAL_DECIDES_DUPLICATE',['CANONICAL_JOURNAL_REOPEN_VERIFIED']),'AR-PROGRESS-STALE':('DISCARD_PROJECTION_JOURNAL_DECIDES',['CANONICAL_JOURNAL_REOPEN_VERIFIED']),'AR-CAS-MISSING':('HOLD_NO_ACCEPTANCE_ACK_NO_EXECUTION',['CAS_REQUIRED','CAS_REOPEN_FAILED']),'AR-AUTH-BIND-MISSING':('HOLD_NO_AUTHORITY_ACK_NO_EXECUTION',['AUTHORITYDB_BIND_REQUIRED','AUTHORITYDB_REOPEN_FAILED'])}
def load(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def add(E,x):
 if x not in E:E.append(x)
def validate(root,design):
 r=Path(root); d=Path(design); E=[]; J={}
 for n in REQ:
  p=r/n
  if not p.is_file():add(E,'missing:'+n);continue
  try:J[n]=load(p)
  except Exception:add(E,'invalid_json:'+n)
 if len(J)!=len(REQ):return E
 # seal and schemas
 sp=r/'ARTIFACT-SHA256.json'
 if not sp.is_file():add(E,'seal_missing')
 else:
  try:s=load(sp)
  except Exception:s={};add(E,'seal_invalid')
  expected=set(REQ+['validate_m2a_r1.py','test_validate_m2a_r1.py','independent_adversarial_r1.py','DESIGN'])
  if set(s.get('files',{}))!=expected:add(E,'seal_inventory')
  for n,h in s.get('files',{}).items():
   p=d if n=='DESIGN' else r/n
   if not p.is_file() or sha(p)!=h:add(E,'hash_mismatch:'+n)
 for n,o in J.items():
  if not isinstance(o,dict) or not isinstance(o.get('schema'),str) or not o['schema'].startswith('critical_apply.m2a'):add(E,'schema:'+n)
 text=d.read_text() if d.is_file() else ''
 for n in REQ+['validate_m2a_r1.py','test_validate_m2a_r1.py','independent_adversarial_r1.py']:
  if n not in text:add(E,'design_xref:'+n)
 # canonical chain and direct close adjacency
 sm=J['SUPERVISOR-STATE-MACHINE.json']; ts=sm.get('canonical_transitions',[]); ids=[x.get('id') for x in ts]; events=[x.get('event') for x in ts]
 if ids!=[f'T{i:02d}' for i in range(25)] or events!=EVENTS:add(E,'canonical_exact_chain')
 if sm.get('canonical_projection')!=EVENTS:add(E,'canonical_projection')
 if len(ts)==25:
  for i,t in enumerate(ts):
   if t.get('canonical') is not True or (i and t.get('from')!=ts[i-1].get('to')):add(E,'canonical_adjacency')
  ix=events.index('SCOPE_LEASE_RELEASE_RECORDED') if 'SCOPE_LEASE_RELEASE_RECORDED' in events else -2
  if ix<0 or events[ix:ix+2]!=['SCOPE_LEASE_RELEASE_RECORDED','SUPERVISOR_CLOSED'] or ts[ix+1].get('from')!='SCOPE_LEASE_RELEASE_RECORDED':add(E,'canonical_close_adjacency')
 if 'COMPLETION_RECEIPT_PREIMAGE_DURABLE' in sm.get('canonical_state_chain',[]) or any('PREIMAGE' in str(x.get('event')) for x in ts):add(E,'preimage_promoted_canonical')
 ap=sm.get('artifact_preparations',[])
 if ap!=[{'id':'AP01_COMPLETION_RECEIPT_PREIMAGE','canonical':False,'event':'COMPLETION_RECEIPT_PREIMAGE_DURABLE_NONCANONICAL','bound_to_release_event':'SCOPE_LEASE_RELEASE_RECORDED','bound_to_release_head_sha256':True,'required_before_canonical_event':'SUPERVISOR_CLOSED','introduces_canonical_state':False}]:add(E,'artifact_preparation_binding')
 asem=sm.get('action_semantics',{}); psem=sm.get('provider_call_semantics',{})
 if asem.get('meaning')!='bounded_non_provider_child_eligibility_only' or asem.get('true_transition_ids')!=['T09'] or asem.get('false_before_barriers') is not True or asem.get('false_after_result_execution_or_release') is not True or asem.get('child_launch_implies_provider_authority') is not False:add(E,'action_semantics')
 for t in ts:
  want=t.get('id')=='T09'
  if t.get('action_allowed') is not want:add(E,'action_gate')
  if t.get('provider_call_allowed') is not False or t.get('call_allowed') is not False:add(E,'provider_call_gate')
 if psem.get('M2A_value') is not False or psem.get('legacy_call_allowed_alias')!='strict_false' or psem.get('future_gate_not_active')!=['N05_CALL_START_COMMITTED journal barrier','N06 AuthorityDB durable consume','active exact epoch and fence','valid owner authority','immutable request hashes']:add(E,'provider_call_semantics')
 if sm.get('semantic_authority')!='canonical_journal' or sm.get('ProgressDB_authoritative') is not False:add(E,'state_authority')
 # exact canonical and artifact crash sides/proofs
 cr=J['SUPERVISOR-CRASH-VECTORS.json']; cv=cr.get('vectors',[]); av=cr.get('artifact_vectors',[])
 if len(cv)!=50 or cr.get('canonical_transition_count')!=25:add(E,'crash_count')
 seen=set()
 for t in ts:
  for side,obs in [('BEFORE_COMMIT',t.get('from') if t.get('from') is not None else 'NONE'),('AFTER_COMMIT',t.get('to'))]:
   matches=[v for v in cv if v.get('transition_id')==t.get('id') and v.get('side')==side]
   if len(matches)!=1:add(E,'crash_exact_sides');continue
   v=matches[0]; expected_id=f"CV-{t['id']}-{side}"; proofs=[f"RP-{t['id']}-{side}-JOURNAL-HEAD",f"RP-{t['id']}-{side}-EPOCH-FENCE",f"RP-{t['id']}-{side}-BOUND-ARTIFACTS"]
   if v.get('id')!=expected_id or v.get('observed_state')!=obs or v.get('recovery_proof_ids')!=proofs:add(E,'crash_transition_binding')
   if v.get('action_allowed') is not False or v.get('provider_call_allowed') is not False or v.get('call_allowed') is not False:add(E,'crash_permissive')
   seen.add(v.get('id'))
 if len(seen)!=len(cv):add(E,'crash_duplicate_or_extra')
 expected_av=[]
 for side in ['BEFORE_COMMIT','AFTER_COMMIT']:
  expected_av.append({'id':f'AV-AP01-{side}','artifact_preparation_id':'AP01_COMPLETION_RECEIPT_PREIMAGE','side':side,'bound_to_release_event':'SCOPE_LEASE_RELEASE_RECORDED','recovery_proof_ids':[f'ARP-AP01-{side}-RELEASE-HEAD',f'ARP-AP01-{side}-PREIMAGE-SHA-SIZE'],'action_allowed':False,'provider_call_allowed':False,'call_allowed':False})
 if av!=expected_av:add(E,'artifact_crash_vectors')
 # child/nonce exact semantics
 ch=J['CHILD-LAUNCH-AND-RESULT-CONTRACT.json']; ni=ch.get('nonce_integration',{}); nts=ni.get('transitions',[])
 if ni.get('required_transition_ids')!=NONCE_IDS or [x.get('id') for x in nts]!=NONCE_IDS or [x.get('order') for x in nts]!=list(range(1,12)):add(E,'nonce_exact_identity_order')
 expected_sem=['reserve exact nonce under active scope fence','commit reservation event in canonical journal','bind reservation event in AuthorityDB with COMMIT_FULL','safe resume only before call start under all exact predicates','commit CALL_START_COMMITTED canonical journal barrier','durably consume in AuthorityDB with COMMIT_FULL','record verified outcome with unconditional descriptor CAS before AuthorityDB bind','classify uncertain started call UNKNOWN_CONSUMED terminal','retire recorded outcome without retry','abandon only when no call may have started','quarantine orphan reservation and HOLD']
 if [x.get('semantic') for x in nts]!=expected_sem:add(E,'nonce_exact_semantics')
 base=['exact_transaction_nonce_hashes','valid_owner_authority','active_exact_epoch_and_fence']
 for i,x in enumerate(nts):
  want=base[:]
  if i==3:want+=['no_CALL_START_COMMITTED','no_provider_attempt','no_outcome','canonical_rebind_authorization','otherwise_retire_and_HOLD']
  if i==4:want+=['immutable_request_hashes','canonical_journal_synced_reopened']
  if i==5:want+=['N05_exact_event_reference','AuthorityDB_COMMIT_FULL_reopened']
  if x.get('critical_predicates')!=want:add(E,'nonce_exact_predicates')
 if ni.get('N04_exact_conditions')!=(nts[3].get('critical_predicates') if len(nts)>3 else None) or 'otherwise_retire_and_HOLD' not in ni.get('N04_exact_conditions',[]):add(E,'N04_exact_no_bypass')
 if ni.get('N07_exact_ordered_tokens')!=N07:add(E,'N07_exact_order')
 if ni.get('automatic_retry') is not False or ni.get('new_call_after_unknown') is not False or ch.get('unknown_outcome')!='UNKNOWN_CONSUMED_TERMINAL_NO_RETRY_NO_NEW_CALL':add(E,'unknown_outcome_terminal')
 if ch.get('child_forbidden')!=['self-registration','create shared path','mkdir nonce-ledger/','write journal','write CAS directly','write AuthorityDB','write ProgressDB as authority','provider call in M2A'] or ch.get('launch_required')!=['immutable registration sha256','journal genesis and current epoch verified','scope active in journal and AuthorityDB','launch intent canonical ACK','exact fencing token','existing supervisor-created run root and nonce-ledger/']:add(E,'child_boundary')
 if ch.get('provider_call_allowed_in_M2A') is not False or ch.get('child_launch_implies_provider_authority') is not False:add(E,'child_provider_authority')
 # ingress and ACK exact
 ig=J['INGRESS-ENVELOPE-CONTRACT.json']; rf=['schema_version','transaction_id','command_request_sha256','contract_sha256','owner_authority_ref','scope_sha256','event_id','caller_provenance','session_provenance','surface_provenance','idempotency_key','payload_cas_refs']
 if ig.get('required_fields')!=rf or ig.get('allowed_fields')!=rf or ig.get('canonical_json',{}).get('unknown_fields')!='reject' or ig.get('untrusted_paths_allowed') is not False or ig.get('path_fields_allowed')!=[] or ig.get('semantic_authority_from_envelope') is not False:add(E,'ingress_strict')
 xs=ig.get('executable_schema',{})
 if xs.get('type')!='object' or xs.get('additionalProperties') is not False or xs.get('required')!=rf or set(xs.get('properties',{}))!=set(rf):add(E,'ingress_schema')
 ac=J['INGRESS-IDEMPOTENCY-CONTRACT.json']
 if ac.get('acceptance_order')!=ACK_ORDER or ac.get('ack_before_all_required_barriers') is not False or ac.get('different_proposal_same_event_id')!='INTEGRITY_CONFLICT_HOLD_NO_EXECUTION_NO_ACTION_NO_PROVIDER_CALL' or ac.get('same_proposal')!='return original journal-derived ACK without append or execution' or ac.get('ProgressDB_may_decide') is not False:add(E,'ack_order_replay')
 ar=J['ACK-REPLAY-VECTORS.json'].get('vectors',[])
 if [x.get('id') for x in ar]!=list(ACK_EXPECT):add(E,'ack_vector_ids')
 for x in ar:
  want=ACK_EXPECT.get(x.get('id'))
  if not want or x.get('expected_outcome')!=want[0] or x.get('required_barriers')!=want[1] or not x.get('input_case'):add(E,'ack_vector_content')
 # concurrency
 co=J['CONCURRENCY-FENCING-VECTORS.json']; vec=co.get('vectors',[])
 if co.get('one_active_owner_per_overlapping_scope') is not True or co.get('checked_on_every_child_mutation_and_result') is not True or co.get('fencing_token_passed_to_child') is not True:add(E,'concurrency_global')
 for n in (2,5,20):
  x=next((v for v in vec if v.get('id')==f'CF-SAME-SCOPE-{n}'),None)
  if not x or x.get('clients')!=n or x.get('expected_active_owners')!=1 or x.get('expected_holds')!=n-1:add(E,'contention_thresholds')
 ov=next((v for v in vec if 'OVERLAP' in v.get('id','')),None); dj=next((v for v in vec if 'DISJOINT' in v.get('id','')),None)
 if not ov or ov.get('expected_max_active_overlapping_pair')!=1 or ov.get('expected')!='no pair of overlapping scopes active simultaneously':add(E,'overlap_exclusion')
 if not dj or dj.get('expected_active_owners')!=20:add(E,'disjoint_scope')
 for sid,key in [('CF-STALE-EPOCH','stale_epoch_result'),('CF-STALE-FENCE-RESULT','stale_fence_result')]:
  x=next((v for v in vec if v.get('id')==sid),None)
  if not x or x.get('expected')!='REJECT_HOLD_NO_MUTATION' or co.get(key)!='REJECT_HOLD_NO_MUTATION':add(E,'stale_epoch_fence_rejection')
 # ownership exact scalar and no child creation
 pm=J['PATH-OWNERSHIP-MATRIX.json']; paths=pm.get('paths',[]); names=[x.get('path') for x in paths]
 if len(names)!=12 or len(names)!=len(set(names)) or pm.get('exactly_one_creator_writer_per_mutable_path') is not True:add(E,'path_exact_ownership')
 for x in paths:
  if x.get('mutable_shared') is True and (not isinstance(x.get('creator'),str) or not x.get('creator') or not isinstance(x.get('writer'),str) or not x.get('writer') or re.search(r'[+,|&]',x.get('writer','')+x.get('creator',''))):add(E,'path_multiple_or_missing_writer')
  if x.get('runner_may_mkdir') is not False:add(E,'path_runner_create')
 if pm.get('child_may_create_shared_path') is not False or pm.get('child_may_self_register') is not False or pm.get('runner_may_create_nonce_ledger') is not False:add(E,'child_path_creation')
 # semantic authorities
 ct=J['COMPONENT-TRUST-BOUNDARIES.json']; sole=[x.get('component') for x in ct.get('components',[]) if x.get('authority')=='sole semantic authority']
 if sole!=['journal_core'] or ct.get('runtime_authority') is not False or ct.get('production_authority') is not False or ct.get('WitnessDB_semantic_authority') is not False or ct.get('notification_semantic_authority') is not False or ct.get('shadow_outputs_authoritative') is not False:add(E,'component_authority')
 for x in ct.get('components',[]):
  if x.get('component') in {'future_checker','notification_projection','ProgressDB'} and ('semantic authority' in str(x.get('authority')).lower() or x.get('authority') not in {'witness only','none'}):add(E,'nonsemantic_component_authority')
 ro=J['RECOVERY-AUTHORITY-ORDER.json']
 if ro.get('order')!=AUTH_ORDER or ro.get('ProgressDB_authoritative') is not False or ro.get('PID_authoritative') is not False or ro.get('notification_authoritative') is not False or ro.get('WitnessDB_semantic_authority') is not False or ro.get('no_action_until_exact_proofs') is not True or ro.get('unknown_child_or_provider_outcome')!='UNKNOWN_CONSUMED_TERMINAL_NO_RETRY_NO_NEW_CALL':add(E,'recovery_authority')
 # preservation/promotions
 ze=J['ZERO-EFFECT-CONTRACT.json']; pg=J['M2B-PROMOTION-GATES.json']; im=J['IMMUTABLE-INPUT-SEALS.json']
 if not ze.get('stop_before_M2B') or ze.get('M2B_started') is not False or ze.get('runtime_authority') or ze.get('production_authority') or ze.get('shadow_outputs_authoritative'):add(E,'zero_effect_boundary')
 if pg.get('M2A_terminal')!='STOP_BEFORE_M2B' or pg.get('runtime_integration_allowed_now'):add(E,'M2B_boundary')
 oi=im.get('inputs',{}).get('original_m2a_candidate',{}); ih=im.get('inputs',{}).get('independent_m2a_hold',{})
 if oi.get('manifest_sha256')!='3f026764d75c96acfca5317e9d9c67e48b140e2281ed563c9bff08f5f5e2f7e2' or ih.get('manifest_sha256')!='c014a7f7bb6c1b7bb06b29fc72b47c2134eda27e0dc97e50d6cac38c0bf9b538' or ih.get('verdict')!='HOLD':add(E,'immutable_hold_binding')
 return E
def main():
 r=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent
 d=Path(sys.argv[2]) if len(sys.argv)>2 else Path('/home/stickai/.openclaw/workspace/design')/DESIGN_NAME
 e=validate(r,d);print(json.dumps({'status':'PASS' if not e else 'HOLD','error_count':len(e),'errors':e},indent=2));return 0 if not e else 2
if __name__=='__main__':raise SystemExit(main())
