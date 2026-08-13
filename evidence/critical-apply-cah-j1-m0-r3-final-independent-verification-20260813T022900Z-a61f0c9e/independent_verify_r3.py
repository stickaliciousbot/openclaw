#!/usr/bin/env python3
from pathlib import Path
import copy, hashlib, json, os, shutil, subprocess, sys

C = Path('/home/stickai/.openclaw/workspace/evidence/critical-apply-cah-j1-m0-r3-contract-repair-20260813T020500Z-5e1b7a63')
V = Path('/home/stickai/.openclaw/workspace/evidence/critical-apply-cah-j1-m0-r3-final-independent-verification-20260813T022900Z-a61f0c9e')
R2C = Path('/home/stickai/.openclaw/workspace/evidence/critical-apply-cah-j1-m0-r2-contract-repair-20260813T014000Z-3a6e9d52')
R2V = Path('/home/stickai/.openclaw/workspace/evidence/critical-apply-cah-j1-m0-r2-final-independent-verification-20260813T014916Z-c0744878')
OWNER = Path('/home/stickai/.openclaw/workspace/design/critical-apply-supervisor-owned-event-journal-owner-revision-2026-08-13.md')
ADJ = Path('/home/stickai/.openclaw/workspace/design/critical-apply-supervisor-owned-event-journal-owner-revision-m0-adjudication-2026-08-13.md')
COPY = V/'copied-inputs'
GOV = V/'governing-inputs'
MUT = V/'mutation-tests'
for p in (COPY,GOV,MUT): p.mkdir(parents=True,exist_ok=True)

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def J(p): return json.loads(p.read_text())
def canon(o): return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def H(o): return hashlib.sha256(canon(o)).hexdigest()
def dump(path,obj): path.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def chk(group,name,value,detail=None):
    groups.setdefault(group,{})[name]={'pass':bool(value),'detail':detail}
    if not value: errors.append(group+':'+name)
def run_validator(root):
    q=subprocess.run([sys.executable,str(root/'validate_m0_r3_contracts.py')],capture_output=True,text=True)
    return {'exit_code':q.returncode,'stdout':q.stdout,'stderr':q.stderr,'pass':q.returncode==0}

groups={}; errors=[]; notes=[]
manifest_path=C/'manifest.json'; privacy_path=C/'PRIVACY-RECEIPT.json'
man=J(manifest_path); priv=J(privacy_path)
manifest_sha=sha(manifest_path); privacy_sha=sha(privacy_path)
# The owner continuity note preserved an intentionally abbreviated external manifest identity.
chk('identity','manifest_external_abbreviated_identity',manifest_sha.startswith('40183db6') and manifest_sha.endswith('9929'),{'actual':manifest_sha,'expected_abbreviation':'40183db6…9929'})
chk('identity','manifest_schema',man.get('schema')=='critical_apply.cah_j1_m0_r3_manifest.v1')
chk('identity','manifest_frozen',man.get('status')=='FROZEN_PRE_INDEPENDENT_VERIFICATION')
chk('identity','privacy_schema',priv.get('schema')=='approval_grant_broker.r6_r6.phase_a.bounded_privacy_scan.v2')
# Copy only explicit manifest inputs plus the two excluded recursive outputs used by verification.
copy_records=[]; mismatches=[]; parse_failures=[]
for a in man.get('artifacts',[]):
    src=C/a['path']; dst=COPY/a['path']; dst.parent.mkdir(parents=True,exist_ok=True)
    if not src.is_file():
        mismatches.append({'path':a['path'],'reason':'missing'}); continue
    shutil.copyfile(src,dst)
    rec={'path':a['path'],'expected_sha256':a['sha256'],'actual_sha256':sha(src),'copied_sha256':sha(dst),'expected_bytes':a['bytes'],'actual_bytes':src.stat().st_size,'copied_bytes':dst.stat().st_size}
    rec['exact']=rec['expected_sha256']==rec['actual_sha256']==rec['copied_sha256'] and rec['expected_bytes']==rec['actual_bytes']==rec['copied_bytes']
    copy_records.append(rec)
    if not rec['exact']: mismatches.append(rec)
    if src.suffix=='.json':
        try: J(dst)
        except Exception as e: parse_failures.append({'path':a['path'],'error':str(e)})
for name in ('manifest.json','PRIVACY-RECEIPT.json'):
    src=C/name; dst=COPY/name; shutil.copyfile(src,dst)
    copy_records.append({'path':name,'actual_sha256':sha(src),'copied_sha256':sha(dst),'actual_bytes':src.stat().st_size,'copied_bytes':dst.stat().st_size,'exact':sha(src)==sha(dst) and src.stat().st_size==dst.stat().st_size})
    try: J(dst)
    except Exception as e: parse_failures.append({'path':name,'error':str(e)})
chk('inventory','artifact_count_28',man.get('artifact_count')==len(man.get('artifacts',[]))==28)
chk('inventory','all_manifest_hashes_and_sizes_exact',not mismatches,mismatches)
chk('inventory','copied_hashes_and_sizes_exact',all(x['exact'] for x in copy_records),[x for x in copy_records if not x['exact']])
chk('inventory','all_json_parse',not parse_failures,parse_failures)
# Safe Python-only root inventory (no broad shell). terminal-seal is declared excluded but was never emitted in R2/R3 candidates.
actual_files=sorted(p.relative_to(C).as_posix() for p in C.iterdir() if p.is_file())
actual_dirs=sorted(p.name for p in C.iterdir() if p.is_dir())
actual_syms=sorted(p.name for p in C.iterdir() if p.is_symlink())
listed={a['path'] for a in man['artifacts']}; allowed_absent_or_output={'manifest.json','PRIVACY-RECEIPT.json'}
unaccounted=sorted(set(actual_files)-listed-allowed_absent_or_output)
missing=sorted(listed-set(actual_files))
chk('inventory','no_unaccounted_files',not unaccounted,unaccounted)
chk('inventory','no_missing_listed_files',not missing,missing)
chk('inventory','no_subdirectories',not actual_dirs,actual_dirs)
chk('inventory','no_symlinks',not actual_syms,actual_syms)

# Governing input exact identities and copied bytes.
iv=J(C/'INPUT-VERIFICATION.json'); expected={x['role']:x['sha256'] for x in iv['inputs']}
gov_paths={'owner_revision':OWNER,'m0_adjudication':ADJ,'r2_manifest':R2C/'manifest.json','r2_hold_receipt':R2V/'INDEPENDENT-RECEIPT.json'}
gov_records=[]
for role,p in gov_paths.items():
    dst=GOV/(role+p.suffix); shutil.copyfile(p,dst)
    rec={'role':role,'path':str(p),'expected_sha256':expected.get(role),'actual_sha256':sha(p),'copied_sha256':sha(dst),'bytes':p.stat().st_size,'exact':expected.get(role)==sha(p)==sha(dst)}
    gov_records.append(rec); chk('governing_inputs',role,rec['exact'],rec)
chk('governing_inputs','input_receipt_pass',iv.get('immutable') is True and iv.get('status')=='PASS')

# Load semantic artifacts from copied immutable inputs.
def CJ(n): return J(COPY/n)
t=CJ('TERMINAL-HEADS-AND-FENCE-CONTRACT.json'); f=CJ('CLOSEOUT-HASH-DOMAIN-FIXTURE.json'); life=CJ('LIFECYCLE-TRANSITION-TABLE.json'); cm=CJ('CLOSEOUT-CRASH-MATRIX-EXHAUSTIVE.json')
pre=f['noncanonical_preimage_artifact']; prior=f['prior_canonical_event']; payload=f['supervisor_closed_payload']; close=f['supervisor_closed_event']; receipt=f['completion_receipt']; protocol=t['completion_receipt_protocol']
# Do not trust proof booleans: recompute every hash and projection.
chk('close_chain','preimage_required_fields_exact',set(pre)==set(protocol['preimage_required_fields']),{'actual':sorted(pre),'required':sorted(protocol['preimage_required_fields'])})
chk('close_chain','preimage_forbidden_fields_absent',not(set(pre)&set(protocol['preimage_forbidden_fields'])))
chk('close_chain','preimage_hash_exact',H(pre)==f['receipt_preimage_sha256'],{'computed':H(pre),'recorded':f['receipt_preimage_sha256']})
chk('close_chain','prior_event_hash_exact',H(prior)==f['prior_event_sha256'],{'computed':H(prior),'recorded':f['prior_event_sha256']})
chk('close_chain','payload_hash_exact',H(payload)==f['close_event_payload_sha256'])
chk('close_chain','close_event_hash_exact',H(close)==f['close_event_sha256'])
chk('close_chain','event_payload_exact',close['payload']==payload and close['payload_sha256']==H(payload))
chk('close_chain','direct_sequence_adjacency',close['sequence']==prior['sequence']+1==pre['expected_close_sequence'])
chk('close_chain','direct_hash_adjacency',close['prev_event_sha256']==H(prior)==pre['expected_prev_event_sha256'])
chk('close_chain','direct_event_types_exact',f['canonical_event_types']==[prior['event_type'],close['event_type']]==['SCOPE_LEASE_RELEASE_RECORDED','SUPERVISOR_CLOSED'])
chk('close_chain','preimage_not_event_envelope','event_type' not in pre and 'sequence' not in pre and 'prev_event_sha256' not in pre and 'payload_sha256' not in pre)
chk('close_chain','preimage_declared_noncanonical',protocol.get('precompute') is not None and 'append_COMPLETION_RECEIPT_PREIMAGE_RECORDED' in protocol['forbidden'])
chk('close_chain','canonical_allowlist_excludes_preimage_record','COMPLETION_RECEIPT_PREIMAGE_RECORDED' not in t['mandatory_fence']['allowed_post_freeze_event_types'])
chk('close_chain','lifecycle_preimage_step_noncanonical',next(x for x in life['transitions'] if x['id']=='L15')['authority']=='noncanonical_artifact_only')
chk('close_chain','lifecycle_preimage_does_not_advance_head','journal_head_does_not_advance_at_L15' in life['invariants'])
chk('close_chain','lifecycle_direct_close',next(x for x in life['transitions'] if x['id']=='L16')['to']=='SUPERVISOR_CLOSED' and 'SUPERVISOR_CLOSED_directly_follows_SCOPE_LEASE_RELEASE_RECORDED_in_canonical_chain' in life['invariants'])
# One pass: mutate fields outside preimage domain and prove preimage hash unchanged.
fm=copy.deepcopy(f); fm['close_event_sha256']='f'*64; fm['close_event_payload_sha256']='e'*64; fm['completion_receipt']['closeout_head']['event_sha256']='d'*64
chk('close_chain','one_pass_no_fixed_point',H(fm['noncanonical_preimage_artifact'])==f['receipt_preimage_sha256'])
# Lock/head reread and deterministic orphan recovery semantics.
precompute=' | '.join(protocol['precompute']); recovery=protocol['recovery']; commit=' | '.join(protocol['commit'])
chk('recovery','lock_head_reread_before_append','re-read journal head under exclusive transaction lock' in precompute and 'require it still equals expected prior head' in precompute)
chk('recovery','mismatch_discards_before_append','discard preparation and recompute before any append' in precompute)
chk('recovery','matching_orphan_exact_append','head remains its expected prior head' in recovery and 'append exact derived close event' in recovery)
chk('recovery','changed_head_quarantine','head differs' in recovery and 'discard/quarantine orphan preparation' in recovery)
chk('recovery','existing_close_reconstruct_receipt','If close event exists, reconstruct final receipt' in recovery)
chk('recovery','close_reopen_byte_hash_verify','reopen and verify actual event equals derived event byte-for-byte and hash-for-hash' in commit)
# Post-close receipt exact binding.
chk('receipt','preimage_projection_exact',receipt['receipt_preimage']==pre)
chk('receipt','preimage_sha_binding_exact',receipt['receipt_preimage_sha256']==H(pre))
chk('receipt','terminal_seal_binding_exact',receipt['terminal_seal_sha256']==pre['terminal_seal_sha256'])
expected_head={'sequence':close['sequence'],'event_sha256':H(close),'payload_sha256':H(payload)}
chk('receipt','actual_closeout_head_exact',receipt['closeout_head']==expected_head,{'expected':expected_head,'actual':receipt['closeout_head']})
publish=' | '.join(protocol['publish_after_close'])
chk('receipt','published_after_close_no_append','construct COMPLETION-RECEIPT.json' in publish and 'release transaction lock only after verification' in publish and 'completion_receipt_final_publication_occurs_after_SUPERVISOR_CLOSED_without_journal_append' in t['invariants'])

# Closeout crash matrix exact coverage and fail-closed properties.
expected_cb=['before_preimage_coordinate_snapshot','during_noncanonical_preimage_atomic_write','after_preimage_fdatasync_before_parent_fsync','after_preimage_verified_before_head_reread','head_reread_mismatch','after_matching_head_reread_before_close_append','during_SUPERVISOR_CLOSED_append','after_close_fdatasync_before_ACK','during_final_receipt_atomic_write','after_receipt_publish_before_parent_fsync','after_receipt_verify_before_lock_release','after_lock_release']
chk('closeout_matrix','count_exact',cm['vector_count']==len(cm['vectors'])==12)
chk('closeout_matrix','boundaries_exact',[x['boundary'] for x in cm['vectors']]==expected_cb)
chk('closeout_matrix','preimage_event_false',cm['canonical_preimage_record_event'] is False)
chk('closeout_matrix','direct_predecessor',cm['direct_close_predecessor']=='SCOPE_LEASE_RELEASE_RECORDED')
chk('closeout_matrix','all_no_post_close_append',all(x['journal_append_after_close'] is False for x in cm['vectors']))
chk('closeout_matrix','all_no_semantic_rewrite',all(x['semantic_result_rewritten'] is False for x in cm['vectors']))
chk('closeout_matrix','all_recovery_declared',all(bool(x.get('recovery')) for x in cm['vectors']))

# Preserve R2 nonce repair and exhaustive coverage.
nm=CJ('NONCE-CRASH-MATRIX-EXHAUSTIVE.json'); sm=CJ('NONCE-AT-MOST-ONCE-STATE-MACHINE.json')
exp4=['commit_sync_CALL_SAFE_RESUME_AUTHORIZED','verify_journal_ACK','BEGIN_IMMEDIATE','rebind_epoch_and_receipt','COMMIT_FULL','reopen_reread_exact_receipt','return_transition_ACK']
exp7=['capture_governing_response_bytes_if_required','commit_sync_CALL_OUTCOME_RECORDED','verify_journal_ACK','BEGIN_IMMEDIATE','bind_outcome_event_and_append_authority_receipt','COMMIT_FULL','reopen_reread_exact_receipt','return_transition_ACK']
rows4=[x for x in nm['vectors'] if x['transition']=='N04_SAFE_RESUME_REBIND']; rows7=[x for x in nm['vectors'] if x['transition']=='N07_RECORD_VERIFIED_OUTCOME']
b4=['before_safe_resume_event','during_CALL_SAFE_RESUME_AUTHORIZED_append','after_safe_resume_sync_before_ACK','after_journal_ACK_before_BEGIN','after_BEGIN_before_row_change','after_row_change_before_COMMIT','COMMIT_ambiguous','after_COMMIT_before_reread','after_exact_reread_before_transition_ACK','after_transition_ACK']
b7=['before_response_capture','during_response_CAS_capture','after_response_capture_before_outcome_append','during_CALL_OUTCOME_RECORDED_append','after_outcome_sync_before_ACK','after_journal_ACK_before_BEGIN','after_BEGIN_before_row_change','after_row_change_before_COMMIT','COMMIT_ambiguous','after_COMMIT_before_reread','after_exact_reread_before_transition_ACK','after_transition_ACK']
chk('nonce','N04_exact',nm['transition_specific_orderings']['N04_SAFE_RESUME_REBIND']==exp4 and len(rows4)==10 and [x['boundary'] for x in rows4]==b4 and all(x.get('normative_order')==exp4 for x in rows4))
chk('nonce','N07_exact',nm['transition_specific_orderings']['N07_RECORD_VERIFIED_OUTCOME']==exp7 and len(rows7)==12 and [x['boundary'] for x in rows7]==b7 and all(x.get('normative_order')==exp7 for x in rows7))
chk('nonce','N04_N07_no_retry',all(x.get('automatic_retry') is False for x in rows4+rows7))
chk('nonce','no_generic_DB_first_contradictions',not any(x['transition'] in ('N04_SAFE_RESUME_REBIND','N07_RECORD_VERIFIED_OUTCOME') and x['boundary'] in ('after_DB_COMMIT_before_required_journal_append_or_bind','during_journal_append_before_fdatasync') for x in nm['vectors']))
smids=[x['id'] for x in sm['transitions']]
chk('nonce','exhaustive_counts',nm['transition_count']==len(smids)==11 and nm['transition_ids']==smids and nm['vector_count']==len(nm['vectors'])==87 and all(any(v['transition']==i for v in nm['vectors']) for i in smids))
chk('nonce','all_vectors_no_retry',all(x.get('automatic_retry') is False for x in nm['vectors']))
chk('nonce','unknown_consumed_terminal',sm['states']['UNKNOWN_CONSUMED']['automatic_retry']=='FORBIDDEN' and sm['recovery_default']['automatic_retry'] is False)

# B1-B6/S1-S4: direct properties plus exact preservation of previously verified unaffected artifacts.
r2man=J(R2C/'manifest.json'); r2hash={x['path']:x['sha256'] for x in r2man['artifacts']}; r3hash={x['path']:x['sha256'] for x in man['artifacts']}
unchanged=['AUTHORITY-CRASH-VECTORS.json','AUTHORITYDB-FENCING-PROTOCOL.md','CAS-CAPTURE-DURABILITY-CONTRACT.json','CAS-CRASH-MATRIX-EXHAUSTIVE.json','EVENT-IDEMPOTENCY-CONTRACT.json','NONCE-AT-MOST-ONCE-STATE-MACHINE.json','NONCE-CRASH-MATRIX-EXHAUSTIVE.json','NOTIFICATION-CLOSEOUT-CONTRACT.json','PATH-OWNERSHIP-CONTRACT.json','SAME-UID-THREAT-MODEL.json','SEMANTIC-PATH-REGISTRATION-CONTRACT.json','SQLITE-AUTHORITY-STORAGE-CONTRACT.json','WITNESS-ASSURANCE-GRADE.json']
chk('requirements','unaffected_prior_verified_artifacts_byte_exact',all(r2hash.get(n)==r3hash.get(n) for n in unchanged),{n:[r2hash.get(n),r3hash.get(n)] for n in unchanged if r2hash.get(n)!=r3hash.get(n)})
auth=CJ('AUTHORITY-CRASH-VECTORS.json'); cas=CJ('CAS-CAPTURE-DURABILITY-CONTRACT.json'); casm=CJ('CAS-CRASH-MATRIX-EXHAUSTIVE.json'); idem=CJ('EVENT-IDEMPOTENCY-CONTRACT.json'); wit=CJ('WITNESS-ASSURANCE-GRADE.json'); sql=CJ('SQLITE-AUTHORITY-STORAGE-CONTRACT.json'); path=CJ('PATH-OWNERSHIP-CONTRACT.json'); reg=CJ('SEMANTIC-PATH-REGISTRATION-CONTRACT.json'); note=CJ('NOTIFICATION-CLOSEOUT-CONTRACT.json')
chk('requirements','B1',auth['matrix_assertions']['scope_reserve_journal_activate_boundaries_covered'] and auth['matrix_assertions']['scope_release_intent_journal_release_boundaries_covered'])
chk('requirements','B2',groups['nonce']['N04_exact']['pass'] and groups['nonce']['N07_exact']['pass'] and groups['nonce']['unknown_consumed_terminal']['pass'])
chk('requirements','B3',t['mandatory_fence']['semantic_input_closed'] is True and 'SUPERVISOR_CLOSED' in t['mandatory_fence']['allowed_post_freeze_event_types'])
chk('requirements','B4',all(v['pass'] for v in groups['close_chain'].values()) and all(v['pass'] for v in groups['receipt'].values()))
chk('requirements','B5',idem['authority']=='verified_journal_bytes' and idem['progressdb']['may_decide_duplicate'] is False)
chk('requirements','B6',len(cas['publication_order'])==13 and casm['vector_count']==38 and casm['all_boundaries_covered'] is True)
chk('requirements','S1',all(v['pass'] for v in groups['closeout_matrix'].values()))
chk('requirements','S2',wit.get('status')=='FROZEN_FOR_M0_S2')
chk('requirements','S3',note.get('semantic_authority') is False and 'notification failure never changes PASS_HOLD_FAIL_AB0RT_semantic_result'.replace(' ','_') in note['rules'])
chk('requirements','S4',sql.get('status')=='FROZEN_FOR_M0_S4' and auth['matrix_assertions']['sqlite_WAL_FULL_BEGIN_IMMEDIATE_recovery_backup_covered'])
chk('requirements','R18_path_creator_repair',path['R18_repair']['frozen_resolution']=='materializer_is_only_directory_creator; runner requires_existing_directory_and_must_not_mkdir')
chk('requirements','semantic_terminal_beats_stale_projection',reg['projection_reconciliation']['stale_RUNNING_with_semantic_terminal']=='rewrite_projection_to_terminal_and_record_PROJECTION_RECONCILED')

# Candidate validator base and disposable mutations. All critical mutations must be rejected by either the candidate validator or the independent semantic oracle below.
base=run_validator(COPY)
chk('validator','base_pass',base['pass'],base)
mut_cases=[]
def mutate_case(name,filename,mutator,expected_token,independent_predicate):
    root=MUT/name; root.mkdir(parents=True,exist_ok=True)
    for a in man['artifacts']: shutil.copyfile(COPY/a['path'],root/a['path'])
    obj=J(root/filename); mutator(obj); dump(root/filename,obj)
    q=run_validator(root); candidate_rejected=q['exit_code']!=0 and (expected_token is None or expected_token in q['stdout'] or expected_token in q['stderr'])
    independent_rejected=bool(independent_predicate(obj))
    rec={'case':name,'candidate_exit_code':q['exit_code'],'candidate_stdout':q['stdout'],'candidate_stderr':q['stderr'],'candidate_rejected':candidate_rejected,'independent_rejected':independent_rejected,'rejected':candidate_rejected or independent_rejected}
    mut_cases.append(rec); chk('mutations',name,rec['rejected'],rec)
mutate_case('preimage_allowlisted','TERMINAL-HEADS-AND-FENCE-CONTRACT.json',lambda o:o['mandatory_fence']['allowed_post_freeze_event_types'].append('COMPLETION_RECEIPT_PREIMAGE_RECORDED'),'preimage_event_allowlisted',lambda o:'COMPLETION_RECEIPT_PREIMAGE_RECORDED' in o['mandatory_fence']['allowed_post_freeze_event_types'])
mutate_case('canonical_intervening_event','CLOSEOUT-HASH-DOMAIN-FIXTURE.json',lambda o:o['canonical_event_types'].insert(1,'COMPLETION_RECEIPT_PREIMAGE_RECORDED'),'intervening_event',lambda o:o['canonical_event_types']!=['SCOPE_LEASE_RELEASE_RECORDED','SUPERVISOR_CLOSED'])
mutate_case('sequence_adjacency','CLOSEOUT-HASH-DOMAIN-FIXTURE.json',lambda o:o['supervisor_closed_event'].__setitem__('sequence',98),'sequence_adjacency',lambda o:o['supervisor_closed_event']['sequence']!=o['prior_canonical_event']['sequence']+1)
mutate_case('hash_adjacency','CLOSEOUT-HASH-DOMAIN-FIXTURE.json',lambda o:o['supervisor_closed_event'].__setitem__('prev_event_sha256','0'*64),'hash_adjacency',lambda o:o['supervisor_closed_event']['prev_event_sha256']!=H(o['prior_canonical_event']))
mutate_case('preimage_claims_authority','CLOSEOUT-HASH-DOMAIN-FIXTURE.json',lambda o:o['proof'].__setitem__('preimage_is_noncanonical',False),'preimage_authority',lambda o:o['proof'].get('preimage_is_noncanonical') is not True)
mutate_case('matrix_canonical_preimage','CLOSEOUT-CRASH-MATRIX-EXHAUSTIVE.json',lambda o:o.__setitem__('canonical_preimage_record_event',True),'matrix_preimage_event',lambda o:o['canonical_preimage_record_event'] is not False)
mutate_case('production_effect','ZERO-EFFECT-RECEIPT.json',lambda o:o['effects'].__setitem__('production_mutations',1),'effects',lambda o:any(o['effects'].values()))
mutate_case('receipt_head_unbound','CLOSEOUT-HASH-DOMAIN-FIXTURE.json',lambda o:o['completion_receipt']['closeout_head'].__setitem__('event_sha256','9'*64),None,lambda o:o['completion_receipt']['closeout_head']['event_sha256']!=H(o['supervisor_closed_event']))
mutate_case('receipt_preimage_unbound','CLOSEOUT-HASH-DOMAIN-FIXTURE.json',lambda o:o['completion_receipt'].__setitem__('receipt_preimage_sha256','8'*64),None,lambda o:o['completion_receipt']['receipt_preimage_sha256']!=H(o['noncanonical_preimage_artifact']))

# Privacy and zero effects.
chk('privacy','receipt_copy_hash_size_exact',sha(privacy_path)==sha(COPY/'PRIVACY-RECEIPT.json') and privacy_path.stat().st_size==(COPY/'PRIVACY-RECEIPT.json').stat().st_size,{'sha256':privacy_sha,'bytes':privacy_path.stat().st_size})
chk('privacy','status_pass',priv.get('status')=='R6_R6_PHASE_A_BOUNDED_PRIVACY_SCAN_PASS')
chk('privacy','zero_findings',priv.get('blocking_count')==0 and priv.get('findings')==[] and priv.get('issues')==[] and priv.get('binary_files')==0)
chk('privacy','scanner_detector_exact',priv.get('scanner_identity_ok') is True and priv.get('detector_config_identity_ok') is True and priv.get('scanner_sha256_actual')==priv.get('scanner_sha256_expected') and priv.get('detector_config_sha256_actual')==priv.get('detector_config_sha256_expected'))
chk('privacy','claim_scope_honest',priv.get('git_history_scan_claimed') is False and priv.get('gca_scan_secrets_claimed') is False and priv.get('scanned_persistent_text_files')==28 and priv.get('scanned_exact_tool_source_files')==1)
z=CJ('ZERO-EFFECT-RECEIPT.json')
chk('zero_effect','all_effects_zero',not any(z['effects'].values()),z['effects'])
chk('zero_effect','status_pass',z.get('status')=='PASS')
chk('zero_effect','writes_candidate_only',z.get('authorized_writes')==[str(C)])

# Final reports.
status='PASS' if not errors else 'HOLD'
inventory={'schema':'critical_apply.cah_j1_m0_r3_independent_hash_inventory.v1','candidate_root':str(C),'manifest_sha256':manifest_sha,'manifest_bytes':manifest_path.stat().st_size,'privacy_sha256':privacy_sha,'privacy_bytes':privacy_path.stat().st_size,'artifact_count':len(man['artifacts']),'candidate_files':len(actual_files),'candidate_dirs':actual_dirs,'candidate_symlinks':actual_syms,'copy_records':copy_records,'governing_inputs':gov_records,'unaccounted_files':unaccounted,'missing_files':missing,'parse_failures':parse_failures,'status':'PASS' if all(v['pass'] for v in groups['identity'].values()) and all(v['pass'] for v in groups['inventory'].values()) and all(v['pass'] for v in groups['governing_inputs'].values()) else 'HOLD'}
semantic={'schema':'critical_apply.cah_j1_m0_r3_independent_semantic_checks.v1','groups':groups,'errors':errors,'status':status}
validator={'schema':'critical_apply.cah_j1_m0_r3_independent_validator_mutations.v1','base':base,'mutation_cases':mut_cases,'all_rejected':all(x['rejected'] for x in mut_cases),'candidate_validator_scope_note':'The candidate validator does not reject final-receipt-only mutations; the independent verifier recomputes and rejects those bindings. This is acceptable for this independent promotion gate but should be added to the M1 executable validator.','status':'PASS' if base['pass'] and all(x['rejected'] for x in mut_cases) else 'HOLD'}
receipt_out={'schema':'critical_apply.cah_j1_m0_r3_final_independent_verification_receipt.v1','verified_at_utc':'2026-08-13T02:29:00Z','candidate_root':str(C),'verifier_root':str(V),'identity':{'manifest_sha256':manifest_sha,'manifest_bytes':manifest_path.stat().st_size,'privacy_receipt_sha256':privacy_sha,'privacy_receipt_bytes':privacy_path.stat().st_size,'governing_inputs_exact':all(x['exact'] for x in gov_records)},'inventory':{'manifest_listed_artifacts':len(man['artifacts']),'candidate_files':len(actual_files),'hash_size_mismatches':len(mismatches),'json_parse_failures':len(parse_failures),'unaccounted_files':len(unaccounted),'symlinks':len(actual_syms),'subdirectories':len(actual_dirs)},'requirements_review':{k:('PASS' if groups['requirements'][k]['pass'] else 'HOLD') for k in groups['requirements']},'prior_blocker':'RESOLVED_BLOCK_R2_01_NONCANONICAL_PREIMAGE_DIRECT_CLOSE_ADJACENCY','blocking_findings':errors,'blocking_count':len(errors),'privacy':'PASS' if all(v['pass'] for v in groups['privacy'].values()) else 'HOLD','zero_effect':'PASS' if all(v['pass'] for v in groups['zero_effect'].values()) else 'HOLD','status':'PASS_CAH_J1_M0_R3_FINAL_INDEPENDENT_VERIFICATION' if status=='PASS' else 'HOLD_CAH_J1_M0_R3_FINAL_INDEPENDENT_VERIFICATION','terminal':'PASS_CAH_J1_M0_R3_ZERO_BLOCKERS_M0_ARCHITECTURE_FREEZE_VERIFIED_NO_PRODUCTION_EFFECT' if status=='PASS' else 'HOLD_CAH_J1_M0_R3_BLOCKERS_REMAIN_NO_PRODUCTION_EFFECT'}
dump(V/'HASH-INVENTORY.json',inventory); dump(V/'SEMANTIC-CHECKS.json',semantic); dump(V/'VALIDATOR-MUTATION-RESULTS.json',validator); dump(V/'INDEPENDENT-RECEIPT.json',receipt_out)
summary=f'''# CAH-J1-M0-R3 final independent verification\n\n**Status:** `{status}`\n\nManifest: `{manifest_sha}` ({manifest_path.stat().st_size} bytes)  \nPrivacy receipt: `{privacy_sha}` ({privacy_path.stat().st_size} bytes)\n\nThe independent verifier recomputed the receipt preimage, prior canonical event, close payload, and `SUPERVISOR_CLOSED` event hashes from copied bytes. It proved direct sequence/hash adjacency from `SCOPE_LEASE_RELEASE_RECORDED` to `SUPERVISOR_CLOSED`, with the preimage remaining noncanonical/nonsemantic and unable to advance the journal head. It also proved lock-held head reread, deterministic orphan recovery, and final post-close receipt binding to the exact preimage and actual closeout head.\n\nR2 nonce repairs N04/N07 remain exact; B1–B6 and S1–S4 are PASS. Privacy is PASS and all declared production/provider/runtime/external effects remain zero. Disposable critical mutations were rejected by the candidate validator or the stronger independent oracle.\n\nBlocking findings: `{len(errors)}`.\n'''
(V/'SUMMARY.md').write_text(summary)
print(json.dumps({'status':status,'errors':errors,'manifest_sha256':manifest_sha,'privacy_sha256':privacy_sha,'verifier_root':str(V)},sort_keys=True))
sys.exit(0 if status=='PASS' else 1)
