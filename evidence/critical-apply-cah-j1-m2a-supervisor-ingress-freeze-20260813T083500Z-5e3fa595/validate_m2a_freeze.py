#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,sys
REQ=['COMPONENT-TRUST-BOUNDARIES.json','INGRESS-ENVELOPE-CONTRACT.json','SUPERVISOR-STATE-MACHINE.json','INGRESS-IDEMPOTENCY-CONTRACT.json','PATH-OWNERSHIP-MATRIX.json','SUPERVISOR-CRASH-VECTORS.json','CONCURRENCY-FENCING-VECTORS.json','ACK-REPLAY-VECTORS.json','CHILD-LAUNCH-AND-RESULT-CONTRACT.json','RECOVERY-AUTHORITY-ORDER.json','M2B-PROMOTION-GATES.json','ZERO-EFFECT-CONTRACT.json','IMMUTABLE-INPUT-SEALS.json']
def load(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def validate(root,design):
 r=Path(root); d=Path(design); E=[]; J={}
 for n in REQ:
  p=r/n
  if not p.is_file(): E.append('missing:'+n); continue
  try:J[n]=load(p)
  except Exception:E.append('invalid_json:'+n)
 if E:return E
 # hash seal
 seal=r/'ARTIFACT-SHA256.json'
 if not seal.is_file():E.append('missing:ARTIFACT-SHA256.json')
 else:
  s=load(seal)
  for n,h in s.get('files',{}).items():
   p=(d if n=='DESIGN' else r/n)
   if not p.is_file() or sha(p)!=h:E.append('hash_mismatch:'+n)
 # schemas
 for n,o in J.items():
  if not isinstance(o.get('schema'),str) or not o['schema'].startswith('critical_apply.m2a.'):E.append('schema:'+n)
 text=d.read_text() if d.is_file() else ''
 for n in REQ+['validate_m2a_freeze.py','test_validate_m2a_freeze.py']:
  if n not in text:E.append('design_xref:'+n)
 # sole semantics/no runtime
 c=J['COMPONENT-TRUST-BOUNDARIES.json']; auth=[x['component'] for x in c['components'] if x.get('authority')=='sole semantic authority']
 if auth!=['journal_core']:E.append('semantic_owner')
 if c.get('runtime_authority') or c.get('production_authority'):E.append('runtime_or_production_authority')
 # ingress
 e=J['INGRESS-ENVELOPE-CONTRACT.json']; required={'transaction_id','command_request_sha256','contract_sha256','owner_authority_ref','scope_sha256','event_id','caller_provenance','session_provenance','surface_provenance','idempotency_key','payload_cas_refs'}
 if not required.issubset(e.get('required_fields',[])):E.append('ingress_fields')
 if e.get('untrusted_paths_allowed') or e.get('semantic_authority_from_envelope'):E.append('untrusted_ingress_authority')
 # adjacency
 sm=J['SUPERVISOR-STATE-MACHINE.json']; ts=sm['transitions']; ids=[x['id'] for x in ts]
 if len(ids)!=len(set(ids)):E.append('transition_ids')
 incoming={s:0 for s in sm['states']}; outgoing={s:0 for s in sm['states']}
 for t in ts:
  if t['to'] not in incoming:E.append('unknown_to:'+t['id'])
  else:incoming[t['to']]+=1
  if t['from'] is not None:
   if t['from'] not in outgoing:E.append('unknown_from:'+t['id'])
   else:outgoing[t['from']]+=1
 if any(incoming[s]!=1 for s in sm['states']):E.append('incomplete_incoming_adjacency')
 if any(outgoing[s]!=1 for s in sm['states'] if s!='TRANSACTION_LOCK_RELEASED'):E.append('incomplete_outgoing_adjacency')
 if sm.get('ProgressDB_authoritative') or sm.get('semantic_authority')!='canonical_journal':E.append('state_authority')
 # path one owner and nonce-ledger creator
 pm=J['PATH-OWNERSHIP-MATRIX.json']; paths=pm['paths']; names=[x['path'] for x in paths]
 if len(names)!=len(set(names)):E.append('duplicate_paths')
 if any(not x.get('creator') or not x.get('writer') for x in paths):E.append('missing_owner')
 nonce=next((x for x in paths if x['path']=='nonce-ledger/'),{})
 if nonce.get('creator')!='supervisor_materializer' or nonce.get('runner_may_mkdir') or pm.get('runner_may_create_nonce_ledger'):E.append('nonce_ledger_ownership')
 # vectors globally unique, thresholds and strict crash windows
 vecsets=[J['SUPERVISOR-CRASH-VECTORS.json']['vectors'],J['CONCURRENCY-FENCING-VECTORS.json']['vectors'],J['ACK-REPLAY-VECTORS.json']['vectors']]
 vids=[v['id'] for z in vecsets for v in z]
 if len(vids)!=len(set(vids)):E.append('vector_ids')
 cv=vecsets[0]
 if len(cv)<50:E.append('crash_threshold')
 covered={v['transition_id'] for v in cv}
 if covered!=set(ids):E.append('crash_transition_coverage')
 if any(v.get('action_allowed') is not False or v.get('call_allowed') is not False or not v.get('recovery_proofs_required') for v in cv):E.append('permissive_crash_window')
 con=vecsets[1]; same={v.get('clients') for v in con if str(v.get('id','')).startswith('CF-SAME-SCOPE-')}
 if not {2,5,20}.issubset(same):E.append('contention_thresholds')
 if not any('OVERLAP' in v['id'] for v in con):E.append('overlap_missing')
 # authority order
 ro=J['RECOVERY-AUTHORITY-ORDER.json']; expected=['canonical_journal','deterministic_reducer','terminal_manifest_and_seal','independent_witness','ProgressDB_projection','PID_registry_status','notification_projection']
 if ro.get('order')!=expected or ro.get('ProgressDB_authoritative') is not False or not ro.get('no_action_until_exact_proofs'):E.append('authority_order')
 # ACK
 ack=J['INGRESS-IDEMPOTENCY-CONTRACT.json']
 if ack.get('ProgressDB_may_decide') is not False or 'original journal-derived ACK' not in ack.get('same_proposal','') or 'HOLD' not in ack.get('different_proposal_same_event_id',''):E.append('ack_replay')
 # N04/N07 exact strength
 ch=J['CHILD-LAUNCH-AND-RESULT-CONTRACT.json']; ni=ch['nonce_integration']; req=set(ni.get('required_transitions',[]))
 if req!={f'N{i:02d}_'+x for i,x in []}: pass
 if len(req)!=11 or not all(any(x.startswith(f'N{i:02d}_') for x in req) for i in range(1,12)):E.append('nonce_N01_N11')
 n04=ni.get('N04_SAFE_RESUME_REBIND','')
 if not all(x in n04 for x in ['before any CALL_START_COMMITTED','same hashes','valid owner authority','active scope fence','otherwise retire+HOLD']):E.append('N04_weakened')
 n07=ni.get('N07_RECORD_VERIFIED_OUTCOME',[])
 if n07!=['capture governing response bytes if required','commit and sync CALL_OUTCOME_RECORDED in canonical journal','bind exact outcome event in AuthorityDB','COMMIT_FULL'] or ni.get('automatic_retry') is not False:E.append('N07_weakened')
 # promotion/zero effect
 pg=J['M2B-PROMOTION-GATES.json']; ze=J['ZERO-EFFECT-CONTRACT.json']
 if pg.get('M2A_terminal')!='STOP_BEFORE_M2B' or pg.get('runtime_integration_allowed_now'):E.append('promotion_boundary')
 if not ze.get('stop_before_M2B') or ze.get('runtime_authority') or ze.get('production_authority') or ze.get('shadow_outputs_authoritative'):E.append('zero_effect_boundary')
 return E
def main():
 r=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent
 d=Path(sys.argv[2]) if len(sys.argv)>2 else Path('/home/stickai/.openclaw/workspace/design/critical-apply-supervisor-ingress-m2a-architecture-freeze-2026-08-13.md')
 e=validate(r,d); print(json.dumps({'status':'PASS' if not e else 'HOLD','errors':e,'error_count':len(e)},indent=2)); return 0 if not e else 2
if __name__=='__main__':raise SystemExit(main())
