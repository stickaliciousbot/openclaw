#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,sys
r=Path(__file__).resolve().parent
req=['AUTHORITYDB-FENCING-PROTOCOL.md', 'NONCE-AT-MOST-ONCE-STATE-MACHINE.json', 'SQLITE-AUTHORITY-STORAGE-CONTRACT.json', 'AUTHORITY-CRASH-VECTORS.json', 'TERMINAL-HEADS-AND-FENCE-CONTRACT.json', 'EVENT-IDEMPOTENCY-CONTRACT.json', 'CAS-CAPTURE-DURABILITY-CONTRACT.json', 'WITNESS-ASSURANCE-GRADE.json', 'CRASH-BOUNDARY-TEST-VECTORS.json', 'LIFECYCLE-TRANSITION-TABLE.json', 'SAME-UID-THREAT-MODEL.json', 'SEMANTIC-PATH-REGISTRATION-CONTRACT.json', 'PATH-OWNERSHIP-CONTRACT.json', 'NOTIFICATION-CLOSEOUT-CONTRACT.json', 'INPUT-VERIFICATION.json', 'ZERO-EFFECT-RECEIPT.json']
errors=[]
for n in req:
 p=r/n
 if not p.is_file(): errors.append('missing:'+n); continue
 if p.suffix=='.json':
  try: json.loads(p.read_text())
  except Exception as e: errors.append('json:'+n+':'+str(e))
exp={'owner_revision':'6d80167ba92e1a68c9d17d6027135b289f88c6b9f3d6fd9e24ea86aedab459af','m0_adjudication':'1d2853fba832ebc243423c3c2dac00def80c3c2b56d892ee8c83aeff96c34427'}
iv=json.loads((r/'INPUT-VERIFICATION.json').read_text())
obs={x['role']:x['observed_sha256'] for x in iv['immutable_inputs']}
if obs!=exp: errors.append('input_hashes')
nonce=json.loads((r/'NONCE-AT-MOST-ONCE-STATE-MACHINE.json').read_text())
for s in ['RESERVED_PENDING_JOURNAL','COMMITTED_NOT_USED','CALL_START_COMMITTED','OUTCOME_RECORDED','RETIRED','UNKNOWN_CONSUMED']:
 if s not in nonce['states']: errors.append('nonce_state:'+s)
term=json.loads((r/'TERMINAL-HEADS-AND-FENCE-CONTRACT.json').read_text())
if term['mandatory_fence']['event_type']!='TERMINAL_REDUCTION_PREPARED': errors.append('fence')
if set(term['heads'])!={'semantic_reduction_head','terminal_decision_head','closeout_head'}: errors.append('heads')
path=json.loads((r/'PATH-OWNERSHIP-CONTRACT.json').read_text())
row=[x for x in path['paths'] if x['path']=='nonce-ledger/']
if len(row)!=1 or row[0]['creator']!='supervisor_materializer' or row[0]['runner_may_create'] is not False: errors.append('nonce_ownership')
cas=json.loads((r/'CAS-CAPTURE-DURABILITY-CONTRACT.json').read_text())
for x in ['leaf_openat_O_RDONLY_O_NOFOLLOW']:
 if x not in cas['registration_preconditions']: errors.append('cas_openat')
life=json.loads((r/'LIFECYCLE-TRANSITION-TABLE.json').read_text())
seq=[x['to'] for x in life['transitions']]
for s in ['CLEANUP_RECORDED','TERMINAL_REDUCTION_PREPARED','TERMINAL_SEALED','SCOPE_LEASE_RELEASE_INTENT','SUPERVISOR_CLOSED','TRANSACTION_LOCK_RELEASED']:
 if s not in seq: errors.append('lifecycle:'+s)
zero=json.loads((r/'ZERO-EFFECT-RECEIPT.json').read_text())
if any(zero['effects'].values()): errors.append('effects_nonzero')
print(json.dumps({'status':'PASS' if not errors else 'HOLD','errors':errors,'required_files':len(req)},sort_keys=True))
sys.exit(0 if not errors else 1)
