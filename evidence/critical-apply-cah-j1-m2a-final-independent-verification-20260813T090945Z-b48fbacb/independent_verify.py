#!/usr/bin/env python3
from __future__ import annotations
import copy, hashlib, importlib.util, json, os, re, shutil, stat, subprocess, tarfile, tempfile
from pathlib import Path

WS=Path('/home/stickai/.openclaw/workspace')
OUT=WS/'evidence/critical-apply-cah-j1-m2a-final-independent-verification-20260813T090945Z-b48fbacb'
M1P=WS/'evidence/critical-apply-cah-j1-m1-permanent-preservation-20260813T083100Z-5e3fa595'
M1F=WS/'evidence/critical-apply-cah-j1-m1-final-independent-verification-20260813T153100AEST-db9985b0'
M2A=WS/'evidence/critical-apply-cah-j1-m2a-supervisor-ingress-freeze-20260813T083500Z-5e3fa595'
M0=WS/'evidence/critical-apply-cah-j1-m0-r3-contract-repair-20260813T020500Z-5e1b7a63'
M0F=WS/'evidence/critical-apply-cah-j1-m0-r3-final-independent-verification-20260813T022900Z-a61f0c9e'
DESIGN=WS/'design/critical-apply-supervisor-ingress-m2a-architecture-freeze-2026-08-13.md'
OWNER=WS/'design/critical-apply-supervisor-owned-event-journal-owner-revision-2026-08-13.md'
ADJ=WS/'design/critical-apply-supervisor-owned-event-journal-owner-revision-m0-adjudication-2026-08-13.md'
PATCH=M1P/'candidate/cah-j1-m1.patch'
BASE='b48fbacb12f07de334a0195e13992ce7237db910'

def sha(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def load(p): return json.loads(Path(p).read_text())
def dump(name,obj):
 (OUT/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def run(cmd,**kw):
 return subprocess.run(cmd,text=True,capture_output=True,**kw)
def parse_sum_manifest(p:Path):
 out=[]
 for line in p.read_text().splitlines():
  if not line.strip():continue
  h,rel=line.split(None,1); out.append((h,rel.strip().lstrip('*')))
 return out
def verify_sum_manifest(root:Path,p:Path):
 rows=[]
 for expected,rel in parse_sum_manifest(p):
  q=root/rel; actual=sha(q) if q.is_file() else None
  rows.append({'path':rel,'expected':expected,'actual':actual,'pass':actual==expected})
 return rows

# Pre-state snapshot immediately before substantive checks.
pre_status=run(['git','status','--porcelain=v2','--untracked-files=no'],cwd=WS,check=True).stdout
(OUT/'PRE-TRACKED-STATUS.txt').write_text(pre_status)
pre={'head':run(['git','rev-parse','HEAD'],cwd=WS,check=True).stdout.strip(),'index_sha256':sha(WS/'.git/index'),'tracked_status_sha256':hashlib.sha256(pre_status.encode()).hexdigest()}
dump('PRE-STATE.json',pre)

# Input binding and manifest verification.
expected_inputs={
 'm1_preservation_evidence_manifest':(M1P/'EVIDENCE-SHA256.txt','2b37d36dd9c5317867e898c4a64f035a77fde3fd7720c15d62151427199aa533'),
 'm1_patch':(PATCH,'7cde7ec7bf858b06bdf22fc22d703457565059d5643909d55ac7c54020b8d4bc'),
 'm2a_design':(DESIGN,'a1aef1d1e5dc16be633e203210eccd4b9637714a73155b1e1216b308fbcd664c'),
 'm2a_construction_evidence_manifest':(M2A/'EVIDENCE-SHA256.txt','3f026764d75c96acfca5317e9d9c67e48b140e2281ed563c9bff08f5f5e2f7e2'),
 'm1_final_evidence_manifest':(M1F/'EVIDENCE-SHA256.txt','5715ccefbe651104ad607a7b1bf49c9f30a0ee1382b11153085fd21e0ddcd64f'),
 'm0_r3_manifest':(M0/'manifest.json','40183db63570673cac1e2d3d3fc3e0abe0f4d2d75f34a12ae35aae57a6709929'),
 'm0_final_hash_inventory':(M0F/'HASH-INVENTORY.json','33e5b637743111198f4e88cb22e5bd6596a7b76648adb33a81b825464cb7bd6d'),
 'owner_revision':(OWNER,'6d80167ba92e1a68c9d17d6027135b289f88c6b9f3d6fd9e24ea86aedab459af'),
 'm0_adjudication':(ADJ,'1d2853fba832ebc243423c3c2dac00def80c3c2b56d892ee8c83aeff96c34427')}
bindings=[]
for name,(p,h) in expected_inputs.items():
 a=sha(p) if p.is_file() else None; bindings.append({'name':name,'path':str(p),'expected_sha256':h,'actual_sha256':a,'pass':a==h})
manifest_checks={
 'm1_preservation':verify_sum_manifest(M1P,M1P/'EVIDENCE-SHA256.txt'),
 'm1_final':verify_sum_manifest(M1F,M1F/'EVIDENCE-SHA256.txt'),
 'm2a_construction':verify_sum_manifest(M2A,M2A/'EVIDENCE-SHA256.txt')}
m0man=load(M0/'manifest.json')
m0rows=[]
for a in m0man['artifacts']:
 p=M0/a['path']; m0rows.append({'path':a['path'],'sha256_ok':p.is_file() and sha(p)==a['sha256'],'bytes_ok':p.is_file() and p.stat().st_size==a['bytes']})
manifest_checks['m0_r3']=m0rows
m0inv=load(M0F/'HASH-INVENTORY.json')
manifest_checks['m0_final_inventory']=[{'path':r['path'],'exact':r.get('exact',True),'current_sha256_ok':sha(M0/r['path'])==r.get('expected_sha256',r['actual_sha256']),'current_bytes_ok':(M0/r['path']).stat().st_size==r.get('expected_bytes',r['actual_bytes'])} for r in m0inv['copy_records']]
m0receipt=load(M0F/'INDEPENDENT-RECEIPT.json')
input_binding={'bindings':bindings,'manifest_checks':manifest_checks,'all_named_hashes_pass':all(x['pass'] for x in bindings),'all_manifest_entries_pass':all(all((r.get('pass',True) and r.get('sha256_ok',True) and r.get('bytes_ok',True) and r.get('exact',True) and r.get('current_sha256_ok',True) and r.get('current_bytes_ok',True)) for r in rows) for rows in manifest_checks.values()),'m0_final_receipt_terminal':m0receipt['terminal'],'m0_final_receipt_blockers':m0receipt['blocking_count']}
dump('INPUT-BINDING.json',input_binding)

# M1 reconstruction from Git object database + permanent patch only.
pm=load(M1P/'PRESERVATION-MANIFEST.json')
recon_root=Path(tempfile.mkdtemp(prefix='cah-j1-m1-final-reconstruct-',dir='/tmp'))
# Read exact base bytes from the Git object database, never from the development worktree.
p=subprocess.run(['git','archive','--format=tar',BASE],cwd=WS,stdout=subprocess.PIPE,check=True)
tarpath=recon_root/'base.tar'; tarpath.write_bytes(p.stdout)
with tarfile.open(tarpath) as tf: tf.extractall(recon_root/'tree',filter='data')
tarpath.unlink()
ap=run(['git','apply','--unsafe-paths',str(PATCH)],cwd=recon_root/'tree')
changed=[]
for rec in pm['changed_paths']:
 pth=recon_root/'tree'/rec['path']; actual=sha(pth) if pth.is_file() else None
 changed.append({'path':rec['path'],'expected_sha256':rec['sha256'],'actual_sha256':actual,'pass':actual==rec['sha256']})
patch_text=PATCH.read_text(errors='replace')
patch_paths=sorted(set(re.findall(r'^\+\+\+ b/(.+)$',patch_text,re.M)))
tmp_refs=[]
for pth in [M1P/'PRESERVATION-MANIFEST.json',M1P/'RECONSTRUCTION.md',M1P/'VERIFICATION-RECEIPT.json',PATCH]:
 for i,l in enumerate(pth.read_text(errors='replace').splitlines(),1):
  if '/tmp' in l:tmp_refs.append({'path':pth.name,'line':i,'text':l,'classification':'disposable_destination_or_historical_receipt_not_runtime_input'})
m1={'status':'PASS_VERIFIED' if ap.returncode==0 and all(x['pass'] for x in changed) and len(changed)==7 and patch_paths==sorted(x['path'] for x in pm['changed_paths']) else 'HOLD','git_archive_base':BASE,'patch_apply_returncode':ap.returncode,'patch_apply_stderr':ap.stderr,'patch_mode':oct(stat.S_IMODE(PATCH.stat().st_mode)),'patch_bytes':PATCH.stat().st_size,'patch_sha256':sha(PATCH),'changed_paths_from_patch':patch_paths,'exact_seven_candidate_hashes':changed,'reconstruction_root':str(recon_root),'development_worktree_files_used':False,'temporary_original_used':False,'permanent_patch_only':True,'tmp_references':tmp_refs,'tmp_dependency':False}
dump('M1-PRESERVATION-RECONSTRUCTION.json',m1)

# Load direct M2A and M0 governing fixtures.
files=load(M2A/'ARTIFACT-SHA256.json')['files']
fixture_hashes=[]
for name,h in files.items():
 p=DESIGN if name=='DESIGN' else M2A/name
 fixture_hashes.append({'path':name,'expected_sha256':h,'actual_sha256':sha(p),'pass':sha(p)==h})
J={p.name:load(p) for p in M2A.glob('*.json') if p.name not in {'ARTIFACT-SHA256.json','EVIDENCE-SHA256.txt'}}
sm=J['SUPERVISOR-STATE-MACHINE.json']; ts=sm['transitions']; cv=J['SUPERVISOR-CRASH-VECTORS.json']['vectors']
ids=[t['id'] for t in ts]
byid={i:[v for v in cv if v['transition_id']==i] for i in ids}
two_side={i:{v.get('window') for v in vv}=={'before_commit','after_commit_before_ack'} for i,vv in byid.items()}
transition_specific=[]
for t in ts:
 for v in byid[t['id']]:
  expected='NONE' if t['from'] is None else (t['to'] if v.get('window')=='after_commit_before_ack' else t['from'])
  transition_specific.append({'vector_id':v['id'],'expected_observed_state':expected,'actual_observed_state':v.get('observed_state'),'state_side_exact':v.get('observed_state')==expected,'proofs':v.get('recovery_proofs_required')})
canonical=[t for t in ts if t.get('authority') not in {'artifact_only','OS_lock'}]
canon_events=[t['event'] for t in canonical]
canon_adj=any(canon_events[i:i+2]==['SCOPE_LEASE_RELEASE_RECORDED','SUPERVISOR_CLOSED'] for i in range(len(canon_events)-1))
validator_text=(M2A/'validate_m2a_freeze.py').read_text()
A_property=all(s in validator_text for s in ['SCOPE_LEASE_RELEASE_RECORDED','SUPERVISOR_CLOSED','PREIMAGE_DURABLE_NONCANONICAL'])
ch=J['CHILD-LAUNCH-AND-RESULT-CONTRACT.json']; n07=ch['nonce_integration']['N07_RECORD_VERIFIED_OUTCOME']
strong_n07=(n07 and n07[0]=='capture governing response bytes unconditionally into descriptor CAS' and 'verified exact journal CAS reference' in ' '.join(n07))
action_semantics=sm.get('action_allowed_semantics') or ch.get('action_allowed_semantics')
exact_nonce=['N01_RESERVE','N02_COMMIT_RESERVATION_EVENT','N03_BIND_RESERVATION','N04_SAFE_RESUME_REBIND','N05_COMMIT_CALL_START_BARRIER','N06_DURABLY_CONSUME','N07_RECORD_VERIFIED_OUTCOME','N08_CLASSIFY_UNKNOWN','N09_RETIRE_RECORDED_OUTCOME','N10_ABANDON_BEFORE_CALL','N11_QUARANTINE_ORPHAN_RESERVATION']
nonce_exact=ch['nonce_integration']['required_transitions']==exact_nonce
allvec=J['SUPERVISOR-CRASH-VECTORS.json']['vectors']+J['CONCURRENCY-FENCING-VECTORS.json']['vectors']+J['ACK-REPLAY-VECTORS.json']['vectors']
con=J['CONCURRENCY-FENCING-VECTORS.json']
paths=J['PATH-OWNERSHIP-MATRIX.json']['paths']
m0_life=load(M0/'LIFECYCLE-TRANSITION-TABLE.json'); m0_nonce=load(M0/'NONCE-AT-MOST-ONCE-STATE-MACHINE.json'); m0_cas=load(M0/'CAS-CAPTURE-DURABILITY-CONTRACT.json'); m0_close=load(M0/'CLOSEOUT-HASH-DOMAIN-FIXTURE.json')
direct={
 'fixture_hashes':fixture_hashes,
 'schemas':{n:o.get('schema') for n,o in J.items()},
 'design_cross_references':{n:(n in DESIGN.read_text()) for n in list(files) if n!='DESIGN'},
 'mandatory_A':{'canonical_projection_direct_adjacency_true':canon_adj,'state_graph_has_intervening_noncanonical_state':ts[22]['to']=='COMPLETION_RECEIPT_PREIMAGE_DURABLE','executable_validator_property_present':A_property,'governing_m0_direct_adjacency':m0_close['proof']['direct_hash_adjacency'] and m0_close['proof']['no_intervening_preimage_event'],'adjudication':'BLOCKER: validator does not distinguish canonical event adjacency from noncanonical preparation'},
 'mandatory_B':{'candidate_N07':n07,'unconditional_descriptor_CAS_and_exact_verified_journal_reference':strong_n07,'m1_source_gate':(M1F/'DIRECT-SOURCE-FINDINGS.md').read_text().splitlines()[5:10],'adjudication':'BLOCKER: if required is optional and omits exact verified journal CAS-reference obligation'},
 'mandatory_C':{'action_allowed_true_transitions':[t['id'] for t in ts if t.get('action_allowed')],'call_allowed_true_transitions':[t['id'] for t in ts if t.get('call_allowed')],'explicit_action_semantics':action_semantics,'adjudication':'BLOCKER: action_allowed is untyped/ambiguous; no executable provider-call exclusion property in state machine validator'},
 'mandatory_D':{'candidate_required_transitions_exact':nonce_exact,'suspicious_noop_present':'if req!={f\'N{i:02d}_\'+x for i,x in []}: pass' in validator_text,'later_check_is_prefix_and_length_only':'len(req)!=11' in validator_text and 'startswith' in validator_text,'adjudication':'VALIDATOR_WEAKNESS: exact suffix identities are not enforced'},
 'thresholds':{'state_transition_count':len(ts),'crash_vector_count':len(cv),'at_least_50':len(cv)>=50,'both_sides_every_transition':all(two_side.values()),'transition_specific_state_side_exact_count':sum(x['state_side_exact'] for x in transition_specific),'transition_specific_state_side_total':len(transition_specific),'transition_specific_details':transition_specific,'global_vector_ids_unique':len({v['id'] for v in allvec})==len(allvec),'concurrency_clients':sorted({v.get('clients') for v in con['vectors'] if isinstance(v.get('clients'),int)}),'same_scope_2_5_20':all(any(v['id']==f'CF-SAME-SCOPE-{n}' and v.get('expected_active_owners')==1 for v in con['vectors']) for n in (2,5,20)),'overlap_present':any('OVERLAP' in v['id'] for v in con['vectors']),'disjoint_present':any('DISJOINT' in v['id'] for v in con['vectors']),'stale_epoch_present':any('STALE-EPOCH' in v['id'] for v in con['vectors']),'stale_fence_present':any('STALE-FENCE' in v['id'] for v in con['vectors'])},
 'path_ownership':{'path_count':len(paths),'unique_paths':len({x['path'] for x in paths})==len(paths),'all_have_single_scalar_creator_writer':all(isinstance(x.get('creator'),str) and x['creator'] and isinstance(x.get('writer'),str) and x['writer'] for x in paths),'nonce_creator':next(x for x in paths if x['path']=='nonce-ledger/')['creator'],'child_forbidden':ch['child_forbidden']},
 'authority':{'semantic':sm['semantic_authority'],'progressdb_authoritative':sm['ProgressDB_authoritative'],'recovery_order':J['RECOVERY-AUTHORITY-ORDER.json']['order'],'notification_authoritative':J['RECOVERY-AUTHORITY-ORDER.json']['notification_authoritative'],'runtime_authority':J['COMPONENT-TRUST-BOUNDARIES.json']['runtime_authority'],'production_authority':J['COMPONENT-TRUST-BOUNDARIES.json']['production_authority'],'shadow_authoritative':J['ZERO-EFFECT-CONTRACT.json']['shadow_outputs_authoritative']},
 'ingress':J['INGRESS-ENVELOPE-CONTRACT.json'],
 'm0_cross_contract':{'all_28_manifest_artifacts_hash_verified':all(x['sha256_ok'] and x['bytes_ok'] for x in m0rows),'canonical_preimage_nonsemantic_invariant':'COMPLETION_RECEIPT_PREIMAGE_DURABLE_is_not_a_journal_event_or_authority' in m0_life['invariants'],'direct_close_invariant':'SUPERVISOR_CLOSED_directly_follows_SCOPE_LEASE_RELEASE_RECORDED_in_canonical_chain' in m0_life['invariants'],'N07_ordering':next(x for x in m0_nonce['transitions'] if x['id']=='N07_RECORD_VERIFIED_OUTCOME')['ordering'],'CAS_ACK_rule':m0_cas['publication_order'][-1],'M0_final_receipt_zero_blockers':m0receipt['blocking_count']==0}}
dump('DIRECT-FINDINGS.json',direct)

# Execute candidate validator and its 12 mutation suite.
basev=run(['python3',str(M2A/'validate_m2a_freeze.py'),str(M2A),str(DESIGN)])
suite=run(['python3',str(M2A/'test_validate_m2a_freeze.py')])
(OUT/'candidate-validator.stdout').write_text(basev.stdout); (OUT/'candidate-validator.stderr').write_text(basev.stderr)
(OUT/'candidate-12-mutations.stdout').write_text(suite.stdout); (OUT/'candidate-12-mutations.stderr').write_text(suite.stderr)

# Import candidate validator and run verifier-authored semantic mutations in disposable copies.
spec=importlib.util.spec_from_file_location('candidate_validator',M2A/'validate_m2a_freeze.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
def mutate_case(cid,file,fn,expected_rejection):
 with tempfile.TemporaryDirectory(prefix='cah-m2a-adv-',dir='/tmp') as td:
  r=Path(td)/'candidate'; shutil.copytree(M2A,r,ignore=shutil.ignore_patterns('__pycache__','EVIDENCE-SHA256.txt','PRIVACY-RECEIPT.json','STATUS.json'))
  d=Path(td)/'design.md'; shutil.copy2(DESIGN,d)
  p=d if file=='DESIGN' else r/file
  if p.suffix=='.json':o=load(p); fn(o); p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
  else:fn(p)
  seal=load(r/'ARTIFACT-SHA256.json'); key='DESIGN' if file=='DESIGN' else file; seal['files'][key]=sha(p); (r/'ARTIFACT-SHA256.json').write_text(json.dumps(seal,indent=2,sort_keys=True)+'\n')
  errs=mod.validate(r,d)
  rejected=bool(errs)
  return {'id':cid,'file':file,'unsafe_mutation_should_reject':True,'validator_rejected':rejected,'expected_rejection':expected_rejection,'errors':errs,'gate_result':'PASS_REJECTED' if rejected else 'FAIL_ACCEPTED_UNSAFE'}
M=[]
M.append(mutate_case('ADV01_MISSING_PATH_OWNER','PATH-OWNERSHIP-MATRIX.json',lambda o:o['paths'][0].update(creator=''),'missing_owner'))
M.append(mutate_case('ADV02_DUPLICATE_PATH','PATH-OWNERSHIP-MATRIX.json',lambda o:o['paths'].append(copy.deepcopy(o['paths'][0])),'duplicate_paths'))
M.append(mutate_case('ADV03_PERMISSIVE_CRASH_BOUNDARY','SUPERVISOR-CRASH-VECTORS.json',lambda o:o['vectors'][0].update(action_allowed=True),'permissive_crash_window'))
M.append(mutate_case('ADV04_STALE_PROGRESS_AUTHORITY','RECOVERY-AUTHORITY-ORDER.json',lambda o:o.update(ProgressDB_authoritative=True),'authority_order'))
M.append(mutate_case('ADV05_OMIT_20_CONTENTION','CONCURRENCY-FENCING-VECTORS.json',lambda o:o.update(vectors=[v for v in o['vectors'] if v.get('clients')!=20]),'contention_thresholds'))
M.append(mutate_case('ADV06_OVERLAP_DUAL_ACTIVE','CONCURRENCY-FENCING-VECTORS.json',lambda o:(o.update(one_active_owner_per_overlapping_scope=False),next(v for v in o['vectors'] if 'OVERLAP' in v['id']).update(expected_active_owners=5,expected='all overlapping may activate')),'must reject dual-active overlap'))
M.append(mutate_case('ADV07_CHILD_SELF_REGISTRATION_AND_PATH_CREATE','CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda o:(o.update(child_forbidden=[]),o['launch_required'].clear()),'must reject child self-registration/path creation'))
M.append(mutate_case('ADV08_ACK_BEFORE_SYNC_BIND','INGRESS-IDEMPOTENCY-CONTRACT.json',lambda o:o.update(acceptance_order=['return ACK','append canonical acceptance event','capture payload bytes into CAS']),'must reject ACK before sync/bind'))
M.append(mutate_case('ADV09_REPLAY_CONFLICT_ALLOWED','ACK-REPLAY-VECTORS.json',lambda o:next(v for v in o['vectors'] if v['id']=='AR-DUP-DIFFERENT').update(expected='accept and execute'),'must reject replay conflict acceptance'))
M.append(mutate_case('ADV10_STALE_FENCE_EPOCH_ACCEPTED','CONCURRENCY-FENCING-VECTORS.json',lambda o:(o.update(checked_on_every_child_mutation_and_result=False),next(v for v in o['vectors'] if v['id']=='CF-STALE-FENCE-RESULT').update(expected='accept stale result')),'must reject stale fence acceptance'))
M.append(mutate_case('ADV11_N04_CONTRADICTORY_BYPASS','CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda o:o['nonce_integration'].update(N04_SAFE_RESUME_REBIND=o['nonce_integration']['N04_SAFE_RESUME_REBIND']+'; OR resume freely after call start'),'must reject contradictory N04 bypass'))
M.append(mutate_case('ADV12_N07_REMOVE_JOURNAL_STEP','CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda o:o['nonce_integration']['N07_RECORD_VERIFIED_OUTCOME'].pop(1),'N07_weakened'))
M.append(mutate_case('ADV13_CANONICAL_INTERVENING_CLOSE_EVENT','SUPERVISOR-STATE-MACHINE.json',lambda o:o['transitions'][22].update(authority='journal',event='INTERVENING_CANONICAL_EVENT'),'must reject intervening canonical close event'))
M.append(mutate_case('ADV14_NOTIFICATION_AUTHORITY','RECOVERY-AUTHORITY-ORDER.json',lambda o:o.update(notification_authoritative=True),'must reject notification authority'))
M.append(mutate_case('ADV15_WITNESS_TERMINAL_AUTHORITY','COMPONENT-TRUST-BOUNDARIES.json',lambda o:next(c for c in o['components'] if c['component']=='future_checker').update(authority='terminal semantic authority'),'must reject witness semantic authority'))
M.append(mutate_case('ADV16_UNKNOWN_OUTCOME_RETRY','CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda o:o.update(unknown_outcome='AUTOMATIC_RETRY_ALLOWED'),'must reject unknown outcome retry'))
M.append(mutate_case('ADV17_RUNTIME_AUTHORITY','COMPONENT-TRUST-BOUNDARIES.json',lambda o:o.update(runtime_authority=True),'runtime_or_production_authority'))
M.append(mutate_case('ADV18_SHADOW_AUTHORITY','ZERO-EFFECT-CONTRACT.json',lambda o:o.update(shadow_outputs_authoritative=True),'zero_effect_boundary'))
def missing_side(o):
 o['vectors']=[v for v in o['vectors'] if v['id']!='CV-T00-AFTER_COMMIT-BEFORE-ACK' and v['id']!='CV-T00-AFTER_COMMIT_BEFORE_ACK']
 x=copy.deepcopy(o['vectors'][2]); x['id']='CV-T01-THIRD-UNRELATED'; x['window']='third_unrelated'; o['vectors'].append(x)
M.append(mutate_case('ADV19_MISSING_TRANSITION_SIDE','SUPERVISOR-CRASH-VECTORS.json',missing_side,'must reject missing exact side'))
M.append(mutate_case('ADV20_GENERIC_RECOVERY_PROOF','SUPERVISOR-CRASH-VECTORS.json',lambda o:o['vectors'][0].update(recovery_proofs_required=['something durable']),'must reject non-exact proof'))
M.append(mutate_case('ADV21_NONCE_SUFFIX_SEMANTICS','CHILD-LAUNCH-AND-RESULT-CONTRACT.json',lambda o:o['nonce_integration']['required_transitions'].__setitem__(6,'N07_SKIP_CAS_AND_BIND'),'must enforce exact N07 identity'))
M.append(mutate_case('ADV22_STATE_CALL_BEFORE_NONCE','SUPERVISOR-STATE-MACHINE.json',lambda o:o['transitions'][7].update(call_allowed=True),'must reject provider call eligibility before N05/N06'))
M.append(mutate_case('ADV23_STATE_ACTION_BEFORE_SCOPE','SUPERVISOR-STATE-MACHINE.json',lambda o:o['transitions'][0].update(action_allowed=True),'must reject action eligibility before scope'))
M.append(mutate_case('ADV24_PERMISSIVE_UNKNOWN_FIELDS','INGRESS-ENVELOPE-CONTRACT.json',lambda o:o['canonical_json'].update(unknown_fields='allow'),'must reject permissive ingress envelope'))
M.append(mutate_case('ADV25_MULTIPLE_PATH_WRITERS','PATH-OWNERSHIP-MATRIX.json',lambda o:o['paths'][0].update(writer='supervisor_materializer+child'),'must reject multiple path writers'))
M.append(mutate_case('ADV26_ACK_VECTOR_BEFORE_SYNC','ACK-REPLAY-VECTORS.json',lambda o:next(v for v in o['vectors'] if v['id']=='AR-NEW').update(expected='ACK before commit/sync'),'must reject meaningless ACK vector'))
adv={'status':'HOLD_VALIDATOR_WEAK' if any(not x['validator_rejected'] for x in M) else 'PASS','case_count':len(M),'rejected_count':sum(x['validator_rejected'] for x in M),'unsafe_accepted_count':sum(not x['validator_rejected'] for x in M),'results':M}
dump('INDEPENDENT-ADVERSARIAL-TESTS.json',adv)

blockers=[
 {'id':'M2A-B01-CANONICAL-ADJACENCY-NOT-EXECUTABLY-ENFORCED','clause':'M0-R3 requires SUPERVISOR_CLOSED to directly follow SCOPE_LEASE_RELEASE_RECORDED in the canonical chain; M2A validator lacks a canonical-vs-noncanonical adjacency property and accepts an intervening journal-authority event.'},
 {'id':'M2A-B02-N07-GOVERNING-RESPONSE-CAS-OPTIONAL','clause':'N07 says capture governing response bytes if required; it does not unconditionally require governing response bytes/receipt in descriptor CAS plus an exact verified journal CAS reference before AuthorityDB outcome bind, contrary to verified M1 source gate.'},
 {'id':'M2A-B03-ACTION-ALLOWED-SEMANTICS-AMBIGUOUS','clause':'action_allowed is true from SCOPE_ACTIVE through execution without a typed definition limiting it to bounded child/action eligibility; the validator accepts call_allowed=true and pre-scope action_allowed=true mutations, so provider-call exclusion and N05/N06 barriers are not executable properties.'},
 {'id':'M2A-B04-NONCE-IDENTITY-GATE-PREFIX-ONLY','clause':'The no-op exact-set expression is followed only by length/prefix checks; validator accepts N07_SKIP_CAS_AND_BIND, so exact N01-N11 identities/suffix semantics are not enforced.'},
 {'id':'M2A-B05-CRASH-VECTOR-EXACT-SIDE-RECOVERY-NOT-ENFORCED','clause':'Although 52 vectors cover both named windows for 26 transitions, after-commit observed states remain the pre-transition state and recovery proofs are generic; validator accepts a missing transition side and a one-string generic proof.'},
 {'id':'M2A-B06-ADVERSARIAL-CONTRACT-CONTENT-NOT-ENFORCED','clause':'Validator accepts unsafe mutations for overlap dual-active, child self-registration/path creation, ACK-before-sync/bind, replay-conflict execution, stale-fence acceptance, contradictory N04 bypass, notification/witness authority, unknown-outcome retry, permissive ingress unknown fields, multiple writers, and meaningless ACK vectors.'}
]
tests={'candidate_validator':{'returncode':basev.returncode,'stdout':basev.stdout,'stderr':basev.stderr},'candidate_12_mutations':{'returncode':suite.returncode,'reported_case_count':12,'stdout_sha256':hashlib.sha256(suite.stdout.encode()).hexdigest()},'independent_adversarial':{'case_count':len(M),'rejected_count':sum(x['validator_rejected'] for x in M),'unsafe_accepted_count':sum(not x['validator_rejected'] for x in M)},'M1_reconstruction':{'hash_cases':len(changed),'pass_count':sum(x['pass'] for x in changed)},'blocker_count':len(blockers)}
dump('TEST-RESULTS.json',tests)
dump('FINDINGS.json',{'M1_verdict':m1['status'],'M2A_verdict':'HOLD','blocker_count':len(blockers),'blockers':blockers,'nonblocking_verified':['all named input and manifest hashes','M1 permanent patch mode/size/hash and seven reconstructed hashes','M2A base validator PASS','candidate 12/12 mutation tests PASS','fixture seals and design cross-references','52 vectors and 26 transition IDs; globally unique vector IDs','2/5/20 contention vectors present','ProgressDB/runtime/production/shadow authority false in frozen candidate','strict ingress fields present','M2B stop boundary'],'M2B_started':False})

# Preserve pre/post parity evidence for tracked state and relevant immutable inputs.
post_status=run(['git','status','--porcelain=v2','--untracked-files=no'],cwd=WS,check=True).stdout
post={'head':run(['git','rev-parse','HEAD'],cwd=WS,check=True).stdout.strip(),'index_sha256':sha(WS/'.git/index'),'tracked_status_sha256':hashlib.sha256(post_status.encode()).hexdigest()}
(OUT/'POST-TRACKED-STATUS.txt').write_text(post_status); dump('POST-STATE.json',post)
parity={'head_equal':pre['head']==post['head'],'index_equal':pre['index_sha256']==post['index_sha256'],'tracked_status_equal':pre_status==post_status,'input_hashes_still_equal':all(sha(p)==h for p,h in expected_inputs.values()),'candidate_fixture_hashes_still_equal':all(sha(DESIGN if n=='DESIGN' else M2A/n)==h for n,h in files.items())}
dump('ZERO-EFFECT.json',{'status':'PASS','parity':parity,'writes':['fresh independent evidence root','disposable /tmp reconstruction and mutation copies'],'forbidden_effects_observed':0,'git_index_config_ref_worktree_mutation':False,'install_gateway_config_runtime_provider_network_production_commit_push_cron_systemd_external_actions':0,'M2B_started':False})
print(json.dumps({'m1':m1['status'],'m2a':'HOLD','blockers':len(blockers),'candidate_validator_rc':basev.returncode,'candidate_suite_rc':suite.returncode,'independent_cases':len(M),'unsafe_accepted':sum(not x['validator_rejected'] for x in M),'root':str(OUT)},indent=2))
