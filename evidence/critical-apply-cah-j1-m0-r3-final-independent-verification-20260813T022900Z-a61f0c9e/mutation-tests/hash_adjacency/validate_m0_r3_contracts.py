#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,sys
r=Path(__file__).resolve().parent;err=[]
def J(n):
 try:return json.loads((r/n).read_text())
 except Exception as e:err.append('json:'+n+':'+str(e));return {}
def H(o):return hashlib.sha256(json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
req=['AUTHORITYDB-FENCING-PROTOCOL.md', 'NONCE-AT-MOST-ONCE-STATE-MACHINE.json', 'SQLITE-AUTHORITY-STORAGE-CONTRACT.json', 'AUTHORITY-CRASH-VECTORS.json', 'TERMINAL-HEADS-AND-FENCE-CONTRACT.json', 'EVENT-IDEMPOTENCY-CONTRACT.json', 'CAS-CAPTURE-DURABILITY-CONTRACT.json', 'WITNESS-ASSURANCE-GRADE.json', 'LIFECYCLE-TRANSITION-TABLE.json', 'SAME-UID-THREAT-MODEL.json', 'SEMANTIC-PATH-REGISTRATION-CONTRACT.json', 'PATH-OWNERSHIP-CONTRACT.json', 'NOTIFICATION-CLOSEOUT-CONTRACT.json', 'NONCE-CRASH-MATRIX-EXHAUSTIVE.json', 'CAS-CRASH-MATRIX-EXHAUSTIVE.json', 'CLOSEOUT-CRASH-MATRIX-EXHAUSTIVE.json', 'CLOSEOUT-HASH-DOMAIN-FIXTURE.json', 'CRASH-BOUNDARY-TEST-VECTORS.json', 'M0-R3-CORRECTION-LEDGER.json', 'INPUT-VERIFICATION.json', 'ZERO-EFFECT-RECEIPT.json']
for n in req:
 if not (r/n).is_file():err.append('missing:'+n)
for n in [x for x in req if x.endswith('.json')]:J(n)
t=J('TERMINAL-HEADS-AND-FENCE-CONTRACT.json');allow=t.get('mandatory_fence',{}).get('allowed_post_freeze_event_types',[])
if 'COMPLETION_RECEIPT_PREIMAGE_RECORDED' in allow:err.append('preimage_event_allowlisted')
if 'append_COMPLETION_RECEIPT_PREIMAGE_RECORDED' not in t.get('completion_receipt_protocol',{}).get('forbidden',[]):err.append('preimage_event_not_forbidden')
l=J('LIFECYCLE-TRANSITION-TABLE.json');seq=[x.get('to') for x in l.get('transitions',[])]
if 'COMPLETION_RECEIPT_PREIMAGE_RECORDED' in seq:err.append('preimage_event_lifecycle')
if not(seq.index('SCOPE_LEASE_RELEASE_RECORDED')<seq.index('COMPLETION_RECEIPT_PREIMAGE_DURABLE')<seq.index('SUPERVISOR_CLOSED')):err.append('lifecycle_order')
f=J('CLOSEOUT-HASH-DOMAIN-FIXTURE.json');prior=f.get('prior_canonical_event',{});close=f.get('supervisor_closed_event',{});pre=f.get('noncanonical_preimage_artifact',{})
if H(prior)!=f.get('prior_event_sha256'):err.append('prior_hash')
if close.get('sequence')!=prior.get('sequence',-2)+1:err.append('sequence_adjacency')
if close.get('prev_event_sha256')!=f.get('prior_event_sha256'):err.append('hash_adjacency')
if H(pre)!=f.get('receipt_preimage_sha256'):err.append('preimage_hash')
if H(f.get('supervisor_closed_payload',{}))!=f.get('close_event_payload_sha256'):err.append('payload_hash')
if H(close)!=f.get('close_event_sha256'):err.append('close_hash')
if f.get('canonical_event_types')!=['SCOPE_LEASE_RELEASE_RECORDED','SUPERVISOR_CLOSED']:err.append('intervening_event')
if not f.get('proof',{}).get('preimage_is_noncanonical'):err.append('preimage_authority')
cm=J('CLOSEOUT-CRASH-MATRIX-EXHAUSTIVE.json')
if cm.get('canonical_preimage_record_event') is not False:err.append('matrix_preimage_event')
if cm.get('vector_count',0)<12:err.append('matrix_sparse')
z=J('ZERO-EFFECT-RECEIPT.json')
if any(z.get('effects',{}).values()):err.append('effects')
print(json.dumps({'status':'PASS' if not err else 'HOLD','errors':err,'required_files':len(req),'fixture':f.get('status'),'closeout_vectors':cm.get('vector_count'),'direct_adjacency':f.get('proof',{}).get('direct_hash_adjacency') and f.get('proof',{}).get('direct_sequence_adjacency')},sort_keys=True));sys.exit(0 if not err else 1)
