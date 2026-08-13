#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,os,re,stat,sys
WS=Path('/home/stickai/.openclaw/workspace')
DESIGN_NAME='critical-apply-supervisor-ingress-m2a-r2-exact-contract-repair-2026-08-13.md'
REQ=['COMPONENT-TRUST-BOUNDARIES.json', 'INGRESS-ENVELOPE-CONTRACT.json', 'SUPERVISOR-STATE-MACHINE.json', 'INGRESS-IDEMPOTENCY-CONTRACT.json', 'PATH-OWNERSHIP-MATRIX.json', 'SUPERVISOR-CRASH-VECTORS.json', 'CONCURRENCY-FENCING-VECTORS.json', 'ACK-REPLAY-VECTORS.json', 'CHILD-LAUNCH-AND-RESULT-CONTRACT.json', 'RECOVERY-AUTHORITY-ORDER.json', 'M2B-PROMOTION-GATES.json', 'ZERO-EFFECT-CONTRACT.json', 'IMMUTABLE-INPUT-SEALS.json', 'ARTIFACT-LIFECYCLE-CONTRACT.json', 'RECOVERY-PROOF-REGISTRY.json', 'DESIGN-CONTRACT.json', 'STRICT-SCHEMA-REGISTRY.json']
EXPECTED_HASHES={'COMPONENT-TRUST-BOUNDARIES.json': 'e362941f4188ad254e9ca039eff84bcb17d613295a1a0983951632e19258d83a', 'INGRESS-ENVELOPE-CONTRACT.json': '83622e86a28fc811d77305aeda4a707b393afc421d02d0652f7f11f3af4700a4', 'SUPERVISOR-STATE-MACHINE.json': 'bd4f22a2d46ffc0ec6e8ea88d50f368a32659c6967d16d0d276e4e59ebab18ba', 'INGRESS-IDEMPOTENCY-CONTRACT.json': '3ab0a89108b62db5c80e139a83ae1f72efa231763c4cf1aadaa7456434feb4bf', 'PATH-OWNERSHIP-MATRIX.json': 'dea719db21309bc1aa929438f4d072a7db7e750c4cb7ec60d04917c8fc55b6a0', 'SUPERVISOR-CRASH-VECTORS.json': 'dbc4d5745bfa94901a03836d0081bddc024991fa2ae352dc2353107e60bce7dc', 'CONCURRENCY-FENCING-VECTORS.json': 'a2155f65a7a2888092e9771563d5d3c034a16d916a15088b7d82c079f9aba8d7', 'ACK-REPLAY-VECTORS.json': '266d08c5698be9f1fcdb0690e37f2c10aefb875df187fee9b8ac8a4e14d779d4', 'CHILD-LAUNCH-AND-RESULT-CONTRACT.json': 'bbc8bd4cb2964578dc044fbdb49a4a4de5cd0baabd5f12b42186b75bfc694bb1', 'RECOVERY-AUTHORITY-ORDER.json': '2b4dc877dc27f1bbe4d1ae4376509113f65714c166a8df7bf1277c1f6a9b104e', 'M2B-PROMOTION-GATES.json': 'c3fa279dc1e4811a27a1ac0f49ca7e76d29c775cfe757098a8978a4c64124a11', 'ZERO-EFFECT-CONTRACT.json': '277f74c17add07cc064145ccf05054dc97598c95d13196fcbea9d1fd717d6fe4', 'IMMUTABLE-INPUT-SEALS.json': 'ff0854e70fb414be4d77034a3c1dadee9c6e2d98a4f9723665bcffe4de3f7121', 'ARTIFACT-LIFECYCLE-CONTRACT.json': '3c7e2e4921f111a0c6ab60096ac8ce2d7ee9d189798ed538990c2db2cf1159d2', 'RECOVERY-PROOF-REGISTRY.json': '6fa1d069239522450dae6b85b63015aa1ad5968398ebd92cc8d26b593060558d', 'DESIGN-CONTRACT.json': 'bc633e9b82e3b98b3165748266ff87015fe69171cd1cb6cd01ff71d3bf805569', 'STRICT-SCHEMA-REGISTRY.json': 'e9c3e8de7c5e9e26f1b5db2be288e61869e846bb709551c5e63facd607aed496'}
EXPECTED_SCHEMAS={'COMPONENT-TRUST-BOUNDARIES.json': 'critical_apply.m2a_r2.component_trust_boundaries.v1', 'INGRESS-ENVELOPE-CONTRACT.json': 'critical_apply.m2a_r2.ingress_envelope_contract.v1', 'SUPERVISOR-STATE-MACHINE.json': 'critical_apply.m2a_r2.supervisor_state_machine.v1', 'INGRESS-IDEMPOTENCY-CONTRACT.json': 'critical_apply.m2a_r2.ingress_idempotency_contract.v1', 'PATH-OWNERSHIP-MATRIX.json': 'critical_apply.m2a_r2.path_ownership.v1', 'SUPERVISOR-CRASH-VECTORS.json': 'critical_apply.m2a_r2.supervisor_crash_vectors.v1', 'CONCURRENCY-FENCING-VECTORS.json': 'critical_apply.m2a_r2.concurrency_fencing_vectors.v1', 'ACK-REPLAY-VECTORS.json': 'critical_apply.m2a_r2.ack_replay_vectors.v1', 'CHILD-LAUNCH-AND-RESULT-CONTRACT.json': 'critical_apply.m2a_r2.child_launch_result.v1', 'RECOVERY-AUTHORITY-ORDER.json': 'critical_apply.m2a_r2.recovery_authority_order.v1', 'M2B-PROMOTION-GATES.json': 'critical_apply.m2a_r2.m2b_promotion_gates.v1', 'ZERO-EFFECT-CONTRACT.json': 'critical_apply.m2a_r2.zero_effect_contract.v1', 'IMMUTABLE-INPUT-SEALS.json': 'critical_apply.m2a_r2.immutable_inputs.v1', 'ARTIFACT-LIFECYCLE-CONTRACT.json': 'critical_apply.m2a_r2.artifact_lifecycle_contract.v1', 'RECOVERY-PROOF-REGISTRY.json': 'critical_apply.m2a_r2.recovery_proof_registry.v1', 'DESIGN-CONTRACT.json': 'critical_apply.m2a_r2.design_contract.v1', 'STRICT-SCHEMA-REGISTRY.json': 'critical_apply.m2a_r2.strict_schema_registry.v1'}
EXPECTED_DESIGN_SHA='3269bbdccd2b5c62566692bbc3dcf17bf4a86a85fb491bedfcdea7ead80d143b'
REQUIRED_STATEMENTS=['CANONICAL_FINAL_EVENT=SUPERVISOR_CLOSED', 'CANONICAL_TRANSITION_COUNT=23', 'COMPLETION_RECEIPT_PUBLICATION_CANONICAL=false', 'TRANSACTION_LOCK_RELEASE_CANONICAL=false', 'NONCANONICAL_OPERATIONS_MAY_MUTATE_SEMANTIC_HEAD=false', 'NONCANONICAL_OPERATIONS_MAY_MUTATE_TERMINAL_DECISION_HEAD=false', 'NONCANONICAL_OPERATIONS_MAY_MUTATE_CLOSEOUT_HEAD=false', 'LOCK_RELEASE_REQUIRES_VERIFIED_PUBLICATION_RECEIPT=true', 'CANONICAL_CRASH_VECTOR_COUNT=46', 'ARTIFACT_PREPARATION_VECTOR_COUNT=2', 'LIFECYCLE_VECTOR_COUNT=4', 'TYPED_PROOF_COUNT=52', 'PROVIDER_CALL_ALLOWED_IN_M2A=false', 'M2B_STARTED=false', 'TERMINAL=PASS_CONSTRUCTION_HOLD_FOR_FRESH_INDEPENDENT_VERIFICATION']
EXPECTED_STATEMENT_DIGEST='81c20e2c1bc86f9ce8c189e14fc3807a33067393bcd6636949dcdb297dc2c5a0'
EXPECTED_PROOF_FIELDS=['id', 'transition_id', 'side', 'observed_state', 'required_journal_events', 'required_journal_hashes', 'required_cas_refs', 'required_authoritydb_state', 'required_authoritydb_receipt', 'required_authoritydb_fence', 'required_authoritydb_epoch', 'prohibited_actions', 'terminal_on_ambiguity', 'recovery_classification']
LEGACY_MAP={'PATH-OWNERSHIP-MATRIX.json': ['path_multiple_or_missing_writer', 'path_exact_ownership', 'path_runner_create', 'child_path_creation'], 'SUPERVISOR-CRASH-VECTORS.json': ['crash_count', 'crash_exact_sides', 'crash_transition_binding', 'crash_permissive', 'crash_duplicate_or_extra', 'artifact_crash_vectors', 'typed_proof_resolution'], 'RECOVERY-PROOF-REGISTRY.json': ['typed_proof_registry', 'typed_proof_resolution'], 'RECOVERY-AUTHORITY-ORDER.json': ['recovery_authority'], 'CONCURRENCY-FENCING-VECTORS.json': ['contention_thresholds', 'concurrency_global', 'overlap_exclusion', 'disjoint_scope', 'stale_epoch_fence_rejection'], 'CHILD-LAUNCH-AND-RESULT-CONTRACT.json': ['N07_exact_order', 'N04_exact_no_bypass', 'nonce_exact_identity_order', 'nonce_exact_semantics', 'nonce_exact_predicates', 'unknown_outcome_terminal', 'child_boundary', 'child_provider_authority', 'child_cross_artifact'], 'SUPERVISOR-STATE-MACHINE.json': ['canonical_exact_chain', 'canonical_projection', 'canonical_adjacency', 'canonical_close_adjacency', 'preimage_promoted_canonical', 'artifact_preparation_binding', 'action_semantics', 'action_gate', 'provider_call_gate', 'provider_call_semantics', 'state_authority', 'lifecycle_noncanonical'], 'INGRESS-IDEMPOTENCY-CONTRACT.json': ['ack_order_replay', 'child_cross_artifact'], 'INGRESS-ENVELOPE-CONTRACT.json': ['ingress_strict', 'ingress_schema'], 'ACK-REPLAY-VECTORS.json': ['ack_vector_ids', 'ack_vector_content', 'child_cross_artifact'], 'COMPONENT-TRUST-BOUNDARIES.json': ['component_authority', 'nonsemantic_component_authority', 'component_exact_roles'], 'ZERO-EFFECT-CONTRACT.json': ['zero_effect_boundary'], 'M2B-PROMOTION-GATES.json': ['M2B_boundary'], 'IMMUTABLE-INPUT-SEALS.json': ['immutable_hold_binding', 'immutable_authority_rehash'], 'ARTIFACT-LIFECYCLE-CONTRACT.json': ['lifecycle_noncanonical'], 'STRICT-SCHEMA-REGISTRY.json': ['strict_schema_registry'], 'DESIGN-CONTRACT.json': ['design_contract_digest']}
_INPUT_CACHE=None

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def add(E,x):
 if x not in E:E.append(x)
def verify_sha_manifest(p,E,label):
 base=p.parent
 for line in p.read_text().splitlines():
  if not line.strip(): continue
  m=re.fullmatch(r'([0-9a-f]{64})  (.+)',line)
  if not m: add(E,'immutable_manifest_format:'+label); continue
  q=base/m.group(2)
  if not q.is_file() or sha(q)!=m.group(1): add(E,'immutable_manifest_entry:'+label+':'+m.group(2))
def verify_inputs_once():
 global _INPUT_CACHE
 if _INPUT_CACHE is not None:return list(_INPUT_CACHE)
 E=[]
 expected={'m0_adjudication': {'path': 'design/critical-apply-supervisor-owned-event-journal-owner-revision-m0-adjudication-2026-08-13.md', 'sha256': '1d2853fba832ebc243423c3c2dac00def80c3c2b56d892ee8c83aeff96c34427', 'kind': 'file'}, 'owner_revision': {'path': 'design/critical-apply-supervisor-owned-event-journal-owner-revision-2026-08-13.md', 'sha256': '6d80167ba92e1a68c9d17d6027135b289f88c6b9f3d6fd9e24ea86aedab459af', 'kind': 'file'}, 'm0_r3_final_hash_inventory': {'path': 'evidence/critical-apply-cah-j1-m0-r3-final-independent-verification-20260813T022900Z-a61f0c9e/HASH-INVENTORY.json', 'sha256': '33e5b637743111198f4e88cb22e5bd6596a7b76648adb33a81b825464cb7bd6d', 'kind': 'file'}, 'm1_permanent_patch': {'path': 'evidence/critical-apply-cah-j1-m1-permanent-preservation-20260813T083100Z-5e3fa595/candidate/cah-j1-m1.patch', 'sha256': '7cde7ec7bf858b06bdf22fc22d703457565059d5643909d55ac7c54020b8d4bc', 'kind': 'file', 'mode': '0444'}, 'original_m2a_candidate_manifest': {'path': 'evidence/critical-apply-cah-j1-m2a-supervisor-ingress-freeze-20260813T083500Z-5e3fa595/EVIDENCE-SHA256.txt', 'sha256': '3f026764d75c96acfca5317e9d9c67e48b140e2281ed563c9bff08f5f5e2f7e2', 'kind': 'sha256_manifest'}, 'original_independent_hold_manifest': {'path': 'evidence/critical-apply-cah-j1-m2a-final-independent-verification-20260813T090945Z-b48fbacb/EVIDENCE-SHA256.txt', 'sha256': 'c014a7f7bb6c1b7bb06b29fc72b47c2134eda27e0dc97e50d6cac38c0bf9b538', 'kind': 'sha256_manifest'}, 'r1_repair_manifest': {'path': 'evidence/critical-apply-cah-j1-m2a-r1-contract-repair-20260813T094741Z-d20176dc/EVIDENCE-SHA256.txt', 'sha256': '62b2357a1e15bf165ef80bcc1129da31719bae28f1f7ddea39af26c1fd027b4e', 'kind': 'sha256_manifest'}, 'r1_independent_hold_manifest': {'path': 'evidence/critical-apply-cah-j1-m2a-r1-final-independent-verification-20260813T100100Z-53c12224/EVIDENCE-SHA256.txt', 'sha256': '49ccef7181ff090c95267f8a5dcc3ccaaba88ce3bd42ade63cef13293e41d2d2', 'kind': 'sha256_manifest'}, 'm0_r3_contract': {'path': 'evidence/critical-apply-cah-j1-m0-r3-contract-repair-20260813T020500Z-5e1b7a63/manifest.json', 'sha256': '40183db63570673cac1e2d3d3fc3e0abe0f4d2d75f34a12ae35aae57a6709929', 'kind': 'json_artifact_manifest'}, 'm1_pass_verified': {'path': 'evidence/critical-apply-cah-j1-m1-final-independent-verification-20260813T153100AEST-db9985b0/EVIDENCE-SHA256.txt', 'sha256': '5715ccefbe651104ad607a7b1bf49c9f30a0ee1382b11153085fd21e0ddcd64f', 'kind': 'sha256_manifest'}}
 for label,s in expected.items():
  p=WS/s['path']
  if not p.is_file():add(E,'immutable_missing:'+label);continue
  expected_sha=s.get('sha256') or s.get('manifest_sha256') or s.get('evidence_sha256_file_sha256')
  if sha(p)!=expected_sha:add(E,'immutable_hash:'+label);continue
  if s.get('mode') and format(stat.S_IMODE(p.stat().st_mode),'04o')!=s['mode']:add(E,'immutable_mode:'+label)
  if s['kind']=='sha256_manifest':verify_sha_manifest(p,E,label)
  elif s['kind']=='json_artifact_manifest':
   try:o=load(p)
   except Exception:add(E,'immutable_manifest_json:'+label);continue
   arts=o.get('artifacts',[])
   if o.get('artifact_count')!=len(arts):add(E,'immutable_manifest_count:'+label)
   for a in arts:
    q=p.parent/a.get('path','')
    if set(a)!={'bytes','path','sha256'} or not q.is_file() or q.stat().st_size!=a.get('bytes') or sha(q)!=a.get('sha256'):add(E,'immutable_manifest_entry:'+label+':'+str(a.get('path')))
 _INPUT_CACHE=tuple(E);return list(E)
def validate(root,design):
 r=Path(root);d=Path(design);E=[];J={}
 for n in REQ:
  p=r/n
  if not p.is_file():add(E,'missing:'+n);continue
  try:J[n]=load(p)
  except Exception:add(E,'invalid_json:'+n);continue
  actual=sha(p)
  if actual!=EXPECTED_HASHES[n]:
   add(E,'exact_contract:'+n)
   for x in LEGACY_MAP.get(n,[]):add(E,x)
  if not isinstance(J[n],dict) or J[n].get('schema')!=EXPECTED_SCHEMAS[n]:add(E,'exact_schema:'+n)
 if len(J)!=len(REQ):return E+verify_inputs_once()
 # Complete local seal with exact inventory and recomputation.
 sp=r/'ARTIFACT-SHA256.json'
 expected_inventory=set(REQ+['validate_m2a_r2.py','test_validate_m2a_r2.py','independent_adversarial_r2.py','independent_adversarial_tests_r2.py','combination_attacks_r2.py','independent_adversarial_tests_r1_exact_source.py','bin/r6_bounded_privacy_scanner.py','DESIGN'])
 if not sp.is_file():add(E,'seal_missing')
 else:
  try:s=load(sp)
  except Exception:s={};add(E,'seal_invalid')
  if s.get('schema')!='critical_apply.m2a_r2.artifact_sha256.v1' or set(s.get('files',{}))!=expected_inventory:add(E,'seal_inventory')
  for n,h in s.get('files',{}).items():
   p=d if n=='DESIGN' else r/n
   if not p.is_file() or sha(p)!=h:add(E,'hash_mismatch:'+n)
 # Semantic design binding, not filename presence.
 if not d.is_file() or sha(d)!=EXPECTED_DESIGN_SHA:
  add(E,'design_contract_digest')
  for n in ['ACK-REPLAY-VECTORS.json']:add(E,'design_xref:'+n)
 else:
  txt=d.read_text()
  if any(('`'+x+'`') not in txt for x in REQUIRED_STATEMENTS):add(E,'design_required_statements')
 dc=J['DESIGN-CONTRACT.json']
 if dc.get('design_sha256')!=EXPECTED_DESIGN_SHA or dc.get('required_statements')!=REQUIRED_STATEMENTS or dc.get('required_statements_canonical_digest_sha256')!=EXPECTED_STATEMENT_DIGEST:add(E,'design_contract_digest')
 # Exact canonical terminal and noncanonical lifecycle.
 sm=J['SUPERVISOR-STATE-MACHINE.json'];ts=sm.get('canonical_transitions',[]);events=[t.get('event') for t in ts]
 if len(ts)!=23 or [t.get('id') for t in ts]!=[f'T{i:02d}' for i in range(23)] or events[-1:]!=['SUPERVISOR_CLOSED'] or sm.get('canonical_projection')!=events or sm.get('canonical_state_chain')!=[t.get('to') for t in ts]:add(E,'canonical_exact_chain')
 if 'COMPLETION_RECEIPT_PUBLISHED' in events or 'TRANSACTION_LOCK_RELEASED' in events:add(E,'lifecycle_noncanonical')
 if events[-2:]!=['SCOPE_LEASE_RELEASE_RECORDED','SUPERVISOR_CLOSED']:add(E,'canonical_close_adjacency')
 ops=sm.get('noncanonical_lifecycle_operations',[]);alc=J['ARTIFACT-LIFECYCLE-CONTRACT.json']
 if ops!=alc.get('lifecycle_operations') or sm.get('artifact_preparations')!=alc.get('artifact_preparations') or [o.get('id') for o in ops]!=sm.get('lifecycle_order'):add(E,'lifecycle_cross_artifact')
 for o in sm.get('artifact_preparations',[])+ops:
  for k in ['canonical','semantic_authority','may_mutate_semantic_head','may_mutate_terminal_decision_head','may_mutate_closeout_head']:
   if o.get(k) is not False:add(E,'lifecycle_noncanonical')
 for o in ops:
  if o.get('prerequisite_closeout_event')!='SUPERVISOR_CLOSED' or o.get('prerequisite_exact_immutable_closeout_head')!='sha256(SUPERVISOR_CLOSED event bytes)':add(E,'lifecycle_prerequisite')
 if len(ops)!=2 or ops[0].get('order')!=1 or ops[1].get('order')!=2 or 'COMPLETION_RECEIPT_PUBLICATION_RECEIPT_VERIFIED' not in ops[1].get('requires',[]):add(E,'lifecycle_order')
 # Typed proof registry and exact vector resolution.
 cr=J['SUPERVISOR-CRASH-VECTORS.json'];pr=J['RECOVERY-PROOF-REGISTRY.json'];cp=pr.get('canonical_proofs',[]);ap=pr.get('artifact_lifecycle_proofs',[]);proofs=cp+ap
 if len(cp)!=46 or len(ap)!=6 or pr.get('total_proof_count')!=52 or cr.get('canonical_vector_count')!=46 or cr.get('artifact_preparation_vector_count')!=2 or cr.get('lifecycle_vector_count')!=4:add(E,'typed_proof_registry')
 ids=[p.get('id') for p in proofs]
 if len(ids)!=len(set(ids)) or set(cr.get('proof_registry',{}))!=set(ids):add(E,'typed_proof_resolution')
 by={p.get('id'):p for p in proofs}
 allv=cr.get('vectors',[])+cr.get('artifact_vectors',[])+cr.get('lifecycle_vectors',[])
 if len(allv)!=52:add(E,'typed_proof_resolution')
 resolved=[]
 for v in allv:
  pids=v.get('recovery_proof_ids')
  if not isinstance(pids,list) or len(pids)!=1 or pids[0] not in by:add(E,'typed_proof_resolution');continue
  p=by[pids[0]];resolved+=pids
  if set(p)!=set(EXPECTED_PROOF_FIELDS) or p.get('transition_id')!=(v.get('transition_id') or v.get('artifact_preparation_id') or v.get('lifecycle_operation_id')) or p.get('side')!=v.get('side') or p.get('observed_state')!=v.get('observed_state'):add(E,'typed_proof_resolution')
  if not all(isinstance(p.get(k),list) for k in ['required_journal_events','required_journal_hashes','required_cas_refs','prohibited_actions']) or not all(isinstance(p.get(k),str) and p.get(k) for k in ['required_authoritydb_state','required_authoritydb_receipt','required_authoritydb_fence','required_authoritydb_epoch','terminal_on_ambiguity','recovery_classification']):add(E,'typed_proof_content')
  if any(v.get(k) is not False for k in ['action_allowed','provider_call_allowed','call_allowed']):add(E,'crash_permissive')
 if set(resolved)!=set(ids) or len(resolved)!=len(ids):add(E,'typed_proof_resolution')
 if cr.get('proof_registry')!={p['id']:p for p in proofs}:add(E,'typed_proof_mirror')
 # Cross-artifact equality and frozen role references.
 ch=J['CHILD-LAUNCH-AND-RESULT-CONTRACT.json'];co=J['CONCURRENCY-FENCING-VECTORS.json'];idem=J['INGRESS-IDEMPOTENCY-CONTRACT.json'];ack=J['ACK-REPLAY-VECTORS.json'];ct=J['COMPONENT-TRUST-BOUNDARIES.json']
 if ch.get('state_action_semantics_ref')!=sm.get('action_semantics') or ch.get('action_allowed_meaning')!=sm.get('action_semantics',{}).get('meaning'):add(E,'child_action_cross_artifact')
 if ch.get('state_future_provider_gate_ref')!=sm.get('provider_call_semantics') or ch.get('nonce_integration',{}).get('future_provider_gate_not_active')!=sm.get('provider_call_semantics',{}).get('future_gate_not_active') or ch.get('provider_call_allowed_in_M2A') is not False:add(E,'child_provider_cross_artifact')
 req=ch.get('every_mutation_and_result_requires')
 if req!=co.get('required_child_mutation_and_result_fields') or req!=['transaction_id','supervisor_epoch','scope_sha256','fencing_token','launch_intent_event_sha256']:add(E,'child_fence_cross_artifact')
 ro=ch.get('result_order')
 if ro!=ch.get('result_ack_order_ref') or ro!=idem.get('child_result_order') or ro!=ack.get('child_result_order'):add(E,'child_ack_cross_artifact')
 roles=ct.get('component_role_ids',[])
 if roles!=[x.get('component') for x in ct.get('components',[])]:add(E,'component_exact_roles')
 for t in ts:
  if not isinstance(t.get('authority_component_roles'),list) or not t['authority_component_roles'] or any(x not in roles for x in t['authority_component_roles']):add(E,'transition_authority_roles')
 # Strict ingress and zero effect direct positives.
 ig=J['INGRESS-ENVELOPE-CONTRACT.json']
 if ig.get('required_fields')!=ig.get('allowed_fields') or ig.get('canonical_json',{}).get('unknown_fields')!='reject' or ig.get('untrusted_paths_allowed') is not False or ig.get('path_fields_allowed')!=[]:add(E,'ingress_strict')
 ze=J['ZERO-EFFECT-CONTRACT.json'];pg=J['M2B-PROMOTION-GATES.json']
 if ze.get('M2B_started') is not False or ze.get('runtime_authority') is not False or ze.get('production_authority') is not False or ze.get('shadow_outputs_authoritative') is not False:add(E,'zero_effect_boundary')
 if pg.get('runtime_integration_allowed_now') is not False or pg.get('M2A_terminal')!='STOP_BEFORE_M2B':add(E,'M2B_boundary')
 E+=verify_inputs_once()
 return list(dict.fromkeys(E))
def main():
 r=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent
 d=Path(sys.argv[2]) if len(sys.argv)>2 else WS/'design'/DESIGN_NAME
 e=validate(r,d);print(json.dumps({'status':'PASS' if not e else 'HOLD','error_count':len(e),'errors':e},indent=2));return 0 if not e else 2
if __name__=='__main__':raise SystemExit(main())
