#!/usr/bin/env python3
from pathlib import Path
import json,sys
r=Path(__file__).resolve().parent
req=['AUTHORITYDB-FENCING-PROTOCOL.md', 'NONCE-AT-MOST-ONCE-STATE-MACHINE.json', 'SQLITE-AUTHORITY-STORAGE-CONTRACT.json', 'AUTHORITY-CRASH-VECTORS.json', 'TERMINAL-HEADS-AND-FENCE-CONTRACT.json', 'EVENT-IDEMPOTENCY-CONTRACT.json', 'CAS-CAPTURE-DURABILITY-CONTRACT.json', 'WITNESS-ASSURANCE-GRADE.json', 'LIFECYCLE-TRANSITION-TABLE.json', 'SAME-UID-THREAT-MODEL.json', 'SEMANTIC-PATH-REGISTRATION-CONTRACT.json', 'PATH-OWNERSHIP-CONTRACT.json', 'NOTIFICATION-CLOSEOUT-CONTRACT.json', 'NONCE-CRASH-MATRIX-EXHAUSTIVE.json', 'CAS-CRASH-MATRIX-EXHAUSTIVE.json', 'CLOSEOUT-CRASH-MATRIX-EXHAUSTIVE.json', 'CRASH-BOUNDARY-TEST-VECTORS.json', 'M0-R1-CORRECTION-LEDGER.json', 'INPUT-VERIFICATION.json', 'ZERO-EFFECT-RECEIPT.json']
err=[]
def J(n):
 try:return json.loads((r/n).read_text())
 except Exception as e:err.append('json:'+n+':'+str(e));return {}
for n in req:
 if not (r/n).is_file():err.append('missing:'+n)
for n in [x for x in req if x.endswith('.json')]:J(n)
t=J('TERMINAL-HEADS-AND-FENCE-CONTRACT.json'); allow=t.get('mandatory_fence',{}).get('allowed_post_freeze_event_types',[])
for x in ['OWNED_CHILD_RECONCILIATION_RECORDED','CLEANUP_RECORDED']:
 if x in allow:err.append('post_freeze:'+x)
for x in ['TERMINAL_DECISION','TERMINAL_SEAL_RECORDED','SUPERVISOR_CLOSED']:
 if x not in allow:err.append('allow_missing:'+x)
if 'completion_receipt_protocol' not in t:err.append('receipt_protocol')
l=J('LIFECYCLE-TRANSITION-TABLE.json'); seq=[x.get('to') for x in l.get('transitions',[])]
need=['CLEANUP_RECORDED','TERMINAL_REDUCTION_PREPARED','TERMINAL_SEAL_RECORDED','COMPLETION_RECEIPT_PREIMAGE_RECORDED','SUPERVISOR_CLOSED','COMPLETION_RECEIPT_PUBLISHED_VERIFIED','TRANSACTION_LOCK_RELEASED']
for x in need:
 if x not in seq:err.append('lifecycle:'+x)
if not(seq.index('CLEANUP_RECORDED')<seq.index('TERMINAL_REDUCTION_PREPARED')):err.append('cleanup_order')
if not(seq.index('SUPERVISOR_CLOSED')<seq.index('COMPLETION_RECEIPT_PUBLISHED_VERIFIED')<seq.index('TRANSACTION_LOCK_RELEASED')):err.append('close_order')
n=J('NONCE-AT-MOST-ONCE-STATE-MACHINE.json'); nm=J('NONCE-CRASH-MATRIX-EXHAUSTIVE.json'); tids={x['id'] for x in n.get('transitions',[])}; covered={x['transition'] for x in nm.get('vectors',[]) if 'transition' in x}
if tids-covered:err.append('nonce_missing:'+','.join(sorted(tids-covered)))
for tid in tids:
 if len([x for x in nm.get('vectors',[]) if x.get('transition')==tid])<3:err.append('nonce_sparse:'+tid)
c=J('CAS-CAPTURE-DURABILITY-CONTRACT.json'); cm=J('CAS-CRASH-MATRIX-EXHAUSTIVE.json')
if cm.get('publication_steps')!=c.get('publication_order'):err.append('cas_steps')
if cm.get('edge_vectors')!=2*len(c.get('publication_order',[])):err.append('cas_edges')
cl=J('CLOSEOUT-CRASH-MATRIX-EXHAUSTIVE.json')
if cl.get('vector_count',0)<10:err.append('close_vectors')
z=J('ZERO-EFFECT-RECEIPT.json')
if any(z.get('effects',{}).values()):err.append('effects')
print(json.dumps({'status':'PASS' if not err else 'HOLD','errors':err,'required_files':len(req),'nonce_transitions':len(tids),'nonce_vectors':nm.get('vector_count'),'cas_steps':len(c.get('publication_order',[])),'cas_vectors':cm.get('vector_count'),'closeout_vectors':cl.get('vector_count')},sort_keys=True))
sys.exit(0 if not err else 1)
