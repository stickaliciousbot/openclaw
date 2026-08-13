#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,sys
r=Path(__file__).resolve().parent
err=[]
def J(n):
 try:return json.loads((r/n).read_text())
 except Exception as e:err.append('json:'+n+':'+str(e));return {}
def H(o):return hashlib.sha256(json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
req=['AUTHORITYDB-FENCING-PROTOCOL.md', 'NONCE-AT-MOST-ONCE-STATE-MACHINE.json', 'SQLITE-AUTHORITY-STORAGE-CONTRACT.json', 'AUTHORITY-CRASH-VECTORS.json', 'TERMINAL-HEADS-AND-FENCE-CONTRACT.json', 'EVENT-IDEMPOTENCY-CONTRACT.json', 'CAS-CAPTURE-DURABILITY-CONTRACT.json', 'WITNESS-ASSURANCE-GRADE.json', 'LIFECYCLE-TRANSITION-TABLE.json', 'SAME-UID-THREAT-MODEL.json', 'SEMANTIC-PATH-REGISTRATION-CONTRACT.json', 'PATH-OWNERSHIP-CONTRACT.json', 'NOTIFICATION-CLOSEOUT-CONTRACT.json', 'NONCE-CRASH-MATRIX-EXHAUSTIVE.json', 'CAS-CRASH-MATRIX-EXHAUSTIVE.json', 'CLOSEOUT-CRASH-MATRIX-EXHAUSTIVE.json', 'CLOSEOUT-HASH-DOMAIN-FIXTURE.json', 'CRASH-BOUNDARY-TEST-VECTORS.json', 'M0-R2-CORRECTION-LEDGER.json', 'INPUT-VERIFICATION.json', 'ZERO-EFFECT-RECEIPT.json']
for n in req:
 if not (r/n).is_file():err.append('missing:'+n)
for n in [x for x in req if x.endswith('.json')]:J(n)
t=J('TERMINAL-HEADS-AND-FENCE-CONTRACT.json');p=t.get('completion_receipt_protocol',{});pre=set(p.get('preimage_required_fields',[]));forbid=set(p.get('preimage_forbidden_fields',[]))
if pre&forbid:err.append('hash_domains_overlap')
for x in ['close_event_payload_sha256','close_event_sha256','closeout_head']:
 if x in pre:err.append('circular_preimage:'+x)
f=J('CLOSEOUT-HASH-DOMAIN-FIXTURE.json')
if H(f.get('receipt_preimage',{}))!=f.get('receipt_preimage_sha256'):err.append('fixture_preimage')
if H(f.get('supervisor_closed_payload',{}))!=f.get('close_event_payload_sha256'):err.append('fixture_payload')
if H(f.get('supervisor_closed_event',{}))!=f.get('close_event_sha256'):err.append('fixture_event')
if f.get('completion_receipt',{}).get('receipt_preimage_sha256')!=f.get('receipt_preimage_sha256'):err.append('fixture_receipt')
if any(x in f.get('receipt_preimage',{}) for x in forbid):err.append('fixture_forbidden')
nm=J('NONCE-CRASH-MATRIX-EXHAUSTIVE.json');orders=nm.get('transition_specific_orderings',{})
exp4=['commit_sync_CALL_SAFE_RESUME_AUTHORIZED','verify_journal_ACK','BEGIN_IMMEDIATE','rebind_epoch_and_receipt','COMMIT_FULL','reopen_reread_exact_receipt','return_transition_ACK']
exp7=['capture_governing_response_bytes_if_required','commit_sync_CALL_OUTCOME_RECORDED','verify_journal_ACK','BEGIN_IMMEDIATE','bind_outcome_event_and_append_authority_receipt','COMMIT_FULL','reopen_reread_exact_receipt','return_transition_ACK']
if orders.get('N04_SAFE_RESUME_REBIND')!=exp4:err.append('N04_order')
if orders.get('N07_RECORD_VERIFIED_OUTCOME')!=exp7:err.append('N07_order')
for tid,exp,minn in [('N04_SAFE_RESUME_REBIND',exp4,10),('N07_RECORD_VERIFIED_OUTCOME',exp7,12)]:
 rows=[x for x in nm.get('vectors',[]) if x.get('transition')==tid]
 if len(rows)<minn:err.append(tid+'_sparse')
 if any(x.get('normative_order')!=exp for x in rows):err.append(tid+'_vector_order')
 # journal must be durable/ACKed before DB BEGIN boundary in each exact sequence.
 idx_begin=next((i for i,x in enumerate(rows) if 'after_BEGIN' in x.get('boundary','')),None);idx_j=next((i for i,x in enumerate(rows) if 'after_journal_ACK' in x.get('boundary','')),None)
 if idx_begin is None or idx_j is None or idx_j>=idx_begin:err.append(tid+'_boundary_order')
z=J('ZERO-EFFECT-RECEIPT.json')
if any(z.get('effects',{}).values()):err.append('effects')
print(json.dumps({'status':'PASS' if not err else 'HOLD','errors':err,'required_files':len(req),'nonce_vectors':nm.get('vector_count'),'N04_vectors':len([x for x in nm.get('vectors',[]) if x.get('transition')=='N04_SAFE_RESUME_REBIND']),'N07_vectors':len([x for x in nm.get('vectors',[]) if x.get('transition')=='N07_RECORD_VERIFIED_OUTCOME']),'closeout_fixture':f.get('status')},sort_keys=True))
sys.exit(0 if not err else 1)
