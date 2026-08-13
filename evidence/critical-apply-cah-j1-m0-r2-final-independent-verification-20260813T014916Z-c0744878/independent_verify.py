#!/usr/bin/env python3
from pathlib import Path
import json, hashlib, os, subprocess, sys, copy, tempfile
C=Path('/home/stickai/.openclaw/workspace/evidence/critical-apply-cah-j1-m0-r2-contract-repair-20260813T014000Z-3a6e9d52')
V=Path('/home/stickai/.openclaw/workspace/evidence/critical-apply-cah-j1-m0-r2-final-independent-verification-20260813T014916Z-c0744878')
EXPECTED_MANIFEST='697e1eb6ad2e6a263b539c3d1ccf353c3b635f17d77841083d11cf99f8cbb235'
EXPECTED_PRIVACY='d7092f98a9f2e6bb62acb385a4fc156155a474e8947dc0595404a7719316c4ad'
def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def J(p): return json.loads(p.read_text())
def H(o): return hashlib.sha256(json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
errors=[]; notes=[]
# Static filesystem + JSON.
all_files=sorted(p for p in C.rglob('*') if p.is_file())
all_dirs=sorted(p for p in C.rglob('*') if p.is_dir())
syms=sorted(p for p in C.rglob('*') if p.is_symlink())
parsed=[]; parse_fail=[]
for p in all_files:
 if p.suffix=='.json':
  try: J(p); parsed.append(p.name)
  except Exception as e: parse_fail.append({'path':p.name,'error':str(e)})
if parse_fail: errors.append('JSON_PARSE_FAILURE')
# Manifest exact and complete listed set.
manp=C/'manifest.json'; privp=C/'PRIVACY-RECEIPT.json'; man=J(manp)
if sha(manp)!=EXPECTED_MANIFEST: errors.append('EXPECTED_MANIFEST_IDENTITY')
if sha(privp)!=EXPECTED_PRIVACY: errors.append('EXPECTED_PRIVACY_IDENTITY')
mis=[]
for a in man['artifacts']:
 p=C/a['path']; actual_sha=sha(p) if p.is_file() else None; actual_bytes=p.stat().st_size if p.is_file() else None
 if actual_sha!=a['sha256'] or actual_bytes!=a['bytes']:
  mis.append({'path':a['path'],'expected_sha':a['sha256'],'actual_sha':actual_sha,'expected_bytes':a['bytes'],'actual_bytes':actual_bytes})
if mis: errors.append('MANIFEST_MISMATCH')
listed={x['path'] for x in man['artifacts']}; excluded=set(man.get('excluded_nonrecursive_outputs',[])); actual={p.relative_to(C).as_posix() for p in all_files}
unaccounted=sorted(actual-listed-excluded)
missing_listed=sorted(listed-actual)
if unaccounted: errors.append('UNACCOUNTED_CANDIDATE_FILES')
if missing_listed: errors.append('MISSING_LISTED_FILES')
# Governing identities: locate exact expected files in known evidence roots.
iv=J(C/'INPUT-VERIFICATION.json')
expected_inputs={x['role']:x['sha256'] for x in iv['inputs']}
known={
 'owner_revision':Path('/home/stickai/.openclaw/workspace/design/critical-apply-supervisor-owned-event-journal-owner-revision-2026-08-13.md'),
 'm0_adjudication':Path('/home/stickai/.openclaw/workspace/design/critical-apply-supervisor-owned-event-journal-owner-revision-m0-adjudication-2026-08-13.md'),
 'r1_manifest':Path('/home/stickai/.openclaw/workspace/evidence/critical-apply-cah-j1-m0-r1-contract-repair-20260813T013000Z-8d2f6c41/manifest.json'),
 'r1_hold_receipt':Path('/home/stickai/.openclaw/workspace/evidence/critical-apply-cah-j1-m0-r1-final-independent-verification-20260813T013200Z-7c91a4e2/INDEPENDENT-RECEIPT.json'),
}
input_results={}
for role,target in expected_inputs.items():
 p=known.get(role); actual_sha=sha(p) if p and p.is_file() else None
 input_results[role]={'expected_sha256':target,'path':str(p) if p else None,'actual_sha256':actual_sha,'exact':actual_sha==target}
 if actual_sha!=target: errors.append('GOVERNING_INPUT_'+role)
# Fixture exact one-pass calculations.
f=J(C/'CLOSEOUT-HASH-DOMAIN-FIXTURE.json'); t=J(C/'TERMINAL-HEADS-AND-FENCE-CONTRACT.json'); pr=t['completion_receipt_protocol']
forbidden=set(pr['preimage_forbidden_fields']); required=set(pr['preimage_required_fields']); fixture_pre=set(f['receipt_preimage'])
fixture_checks={
 'required_fields_exact':fixture_pre==required,
 'forbidden_fields_absent':not bool(fixture_pre&forbidden),
 'preimage_sha_exact':H(f['receipt_preimage'])==f['receipt_preimage_sha256'],
 'payload_sha_exact':H(f['supervisor_closed_payload'])==f['close_event_payload_sha256'],
 'event_sha_exact':H(f['supervisor_closed_event'])==f['close_event_sha256'],
 'event_payload_projection_exact':f['supervisor_closed_event']['payload']==f['supervisor_closed_payload'],
 'event_payload_sha_field_exact':f['supervisor_closed_event']['payload_sha256']==f['close_event_payload_sha256'],
 'event_prior_head_exact':f['supervisor_closed_event']['sequence']==f['receipt_preimage']['expected_close_sequence'] and f['supervisor_closed_event']['prev_event_sha256']==f['receipt_preimage']['expected_prev_event_sha256'],
 'receipt_preimage_projection_exact':f['completion_receipt']['receipt_preimage']==f['receipt_preimage'],
 'receipt_preimage_sha_exact':f['completion_receipt']['receipt_preimage_sha256']==f['receipt_preimage_sha256'],
 'receipt_actual_head_exact':f['completion_receipt']['closeout_head']=={'sequence':f['supervisor_closed_event']['sequence'],'event_sha256':f['close_event_sha256'],'payload_sha256':f['close_event_payload_sha256']},
 'payload_only_binds_fixed_preimage_and_frozen_refs':set(f['supervisor_closed_payload'])=={'schema','transaction_id','receipt_preimage_sha256','semantic_result','terminal_decision_head','terminal_seal_sha256'},
}
# Event derivation is one-pass and preimage invariant if close-derived values are altered externally.
mut=copy.deepcopy(f); mut['close_event_sha256']='f'*64; mut['close_event_payload_sha256']='e'*64; mut['completion_receipt']['closeout_head']['event_sha256']='d'*64
fixture_checks['preimage_hash_independent_of_close_derived_fields']=H(mut['receipt_preimage'])==f['receipt_preimage_sha256']
if not all(fixture_checks.values()): errors.append('CLOSEOUT_FIXTURE_SEMANTICS')
# Closeout matrix coverage/no append/rewrite.
cm=J(C/'CLOSEOUT-CRASH-MATRIX-EXHAUSTIVE.json'); cb=[x['boundary'] for x in cm['vectors']]
expected_cb=['before_preimage_construction','during_preimage_atomic_write','after_preimage_fsync_before_PREIMAGE_RECORDED','after_PREIMAGE_RECORDED_sync_before_close_event','during_SUPERVISOR_CLOSED_append','after_SUPERVISOR_CLOSED_fdatasync_before_ACK','after_close_verify_before_receipt_publish','during_receipt_atomic_write','after_receipt_publish_before_parent_fsync','after_parent_fsync_before_receipt_verify','after_receipt_verify_before_lock_release','after_lock_release']
life=J(C/'LIFECYCLE-TRANSITION-TABLE.json')
life_tos=[x['to'] for x in life['transitions']]
close_checks={
 'boundary_array_exact':cb==expected_cb,
 'all_no_append_after_close':all(x['journal_append_after_close'] is False for x in cm['vectors']),
 'no_semantic_rewrite':all(x['semantic_result_rewritten'] is False for x in cm['vectors']),
 'recovery_declared_all':all(bool(x.get('recovery')) for x in cm['vectors']),
 'preimage_record_event_is_mandatory_before_close':life_tos.index('COMPLETION_RECEIPT_PREIMAGE_RECORDED') < life_tos.index('SUPERVISOR_CLOSED') and 'COMPLETION_RECEIPT_PREIMAGE_RECORDED' in t['mandatory_fence']['allowed_post_freeze_event_types'],
 'fixture_models_preimage_record_event': 'completion_receipt_preimage_recorded_event' in f,
 'fixture_proves_close_prev_equals_preimage_record_hash': bool(f.get('completion_receipt_preimage_recorded_event')) and f['supervisor_closed_event']['prev_event_sha256']==H(f['completion_receipt_preimage_recorded_event']),
 'fixed_preimage_hash_excludes_future_close_envelope_coordinates': 'expected_close_sequence' not in required and 'expected_prev_event_sha256' not in required,
}
# The first four are matrix hygiene. The last three are mandatory chain-construction checks:
# a PREIMAGE_RECORDED append advances the prior head after preimage hashing, so future close
# coordinates cannot be in that same hash domain unless a fixed point is specified.
if not all(close_checks.values()): errors.append('CLOSEOUT_CHAIN_CONSTRUCTION')
# Nonce N04/N07 arrays, exact boundary sequences, state monotonicity, no generic contradictory rows.
nm=J(C/'NONCE-CRASH-MATRIX-EXHAUSTIVE.json')
exp4=['commit_sync_CALL_SAFE_RESUME_AUTHORIZED','verify_journal_ACK','BEGIN_IMMEDIATE','rebind_epoch_and_receipt','COMMIT_FULL','reopen_reread_exact_receipt','return_transition_ACK']
exp7=['capture_governing_response_bytes_if_required','commit_sync_CALL_OUTCOME_RECORDED','verify_journal_ACK','BEGIN_IMMEDIATE','bind_outcome_event_and_append_authority_receipt','COMMIT_FULL','reopen_reread_exact_receipt','return_transition_ACK']
rows4=[x for x in nm['vectors'] if x['transition']=='N04_SAFE_RESUME_REBIND']; rows7=[x for x in nm['vectors'] if x['transition']=='N07_RECORD_VERIFIED_OUTCOME']
b4=['before_safe_resume_event','during_CALL_SAFE_RESUME_AUTHORIZED_append','after_safe_resume_sync_before_ACK','after_journal_ACK_before_BEGIN','after_BEGIN_before_row_change','after_row_change_before_COMMIT','COMMIT_ambiguous','after_COMMIT_before_reread','after_exact_reread_before_transition_ACK','after_transition_ACK']
b7=['before_response_capture','during_response_CAS_capture','after_response_capture_before_outcome_append','during_CALL_OUTCOME_RECORDED_append','after_outcome_sync_before_ACK','after_journal_ACK_before_BEGIN','after_BEGIN_before_row_change','after_row_change_before_COMMIT','COMMIT_ambiguous','after_COMMIT_before_reread','after_exact_reread_before_transition_ACK','after_transition_ACK']
nonce_checks={
 'declared_N04_order_exact':nm['transition_specific_orderings']['N04_SAFE_RESUME_REBIND']==exp4,
 'declared_N07_order_exact':nm['transition_specific_orderings']['N07_RECORD_VERIFIED_OUTCOME']==exp7,
 'N04_count_10':len(rows4)==10,'N07_count_12':len(rows7)==12,
 'N04_vector_orders_exact':all(x.get('normative_order')==exp4 for x in rows4),
 'N07_vector_orders_exact':all(x.get('normative_order')==exp7 for x in rows7),
 'N04_boundaries_exact': [x['boundary'] for x in rows4]==b4,
 'N07_boundaries_exact': [x['boundary'] for x in rows7]==b7,
 'N04_journal_ACK_before_DB_BEGIN':rows4[3]['journal_state']=='durable_safe_resume_ACKed' and rows4[4]['journal_state']=='durable_safe_resume_ACKed',
 'N07_response_then_journal_ACK_before_DB_BEGIN':rows7[2]['journal_state']=='response_CAS_durable_no_event' and rows7[5]['journal_state']=='durable_outcome_ACKed' and rows7[6]['journal_state']=='durable_outcome_ACKed',
 'all_N04_N07_no_retry':all(x.get('automatic_retry') is False for x in rows4+rows7),
 'no_N04_generic_DB_first_rows':not any(x['transition']=='N04_SAFE_RESUME_REBIND' and ('after_DB_COMMIT_before_required_journal_append_or_bind' in x['boundary'] or 'during_journal_append_before_fdatasync' in x['boundary']) for x in nm['vectors']),
 'no_N07_generic_DB_first_rows':not any(x['transition']=='N07_RECORD_VERIFIED_OUTCOME' and ('after_DB_COMMIT_before_required_journal_append_or_bind' in x['boundary'] or 'during_journal_append_before_fdatasync' in x['boundary']) for x in nm['vectors']),
}
if not all(nonce_checks.values()): errors.append('N04_N07_MATRIX')
# Exhaustive transition ID/count claims and fail closed defaults.
sm=J(C/'NONCE-AT-MOST-ONCE-STATE-MACHINE.json'); smids=[x['id'] for x in sm['transitions']]; mids=nm['transition_ids']; counts={i:sum(1 for x in nm['vectors'] if x['transition']==i) for i in mids}
coverage_checks={'transition_ids_exact':smids==mids,'transition_count_exact':nm['transition_count']==len(smids)==11,'vector_count_exact':nm['vector_count']==len(nm['vectors'])==87,'every_transition_has_vectors':all(counts[i]>0 for i in smids),'unclassified_fail_closed':nm['unclassified']=='UNKNOWN_CONSUMED_OR_HOLD_NO_ACTION_NO_RETRY','all_vectors_no_auto_retry':all(x.get('automatic_retry') is False for x in nm['vectors'])}
if not all(coverage_checks.values()): errors.append('NONCE_EXHAUSTIVENESS')
# Candidate validator and mutation tests proving exact order array comparisons.
val=C/'validate_m0_r2_contracts.py'; base=subprocess.run([sys.executable,str(val)],capture_output=True,text=True)
validator={'exit_code':base.returncode,'stdout':base.stdout,'stderr':base.stderr,'base_pass':base.returncode==0}
with tempfile.TemporaryDirectory(dir=V) as td:
 td=Path(td)
 for p in C.iterdir():
  if p.is_file(): (td/p.name).write_bytes(p.read_bytes())
 # N04 declared and vectors mutated consistently. A count-only/boundary-only validator would miss this.
 m=J(td/'NONCE-CRASH-MATRIX-EXHAUSTIVE.json'); bad4=exp4.copy(); bad4[0],bad4[2]=bad4[2],bad4[0]; m['transition_specific_orderings']['N04_SAFE_RESUME_REBIND']=bad4
 for x in m['vectors']:
  if x['transition']=='N04_SAFE_RESUME_REBIND': x['normative_order']=bad4
 (td/'NONCE-CRASH-MATRIX-EXHAUSTIVE.json').write_text(json.dumps(m,indent=2,sort_keys=True)+'\n')
 q=subprocess.run([sys.executable,str(td/'validate_m0_r2_contracts.py')],capture_output=True,text=True)
 validator['N04_order_mutation_rejected']=q.returncode!=0 and 'N04_order' in q.stdout
 # Restore and mutate N07 consistently.
 (td/'NONCE-CRASH-MATRIX-EXHAUSTIVE.json').write_bytes((C/'NONCE-CRASH-MATRIX-EXHAUSTIVE.json').read_bytes()); m=J(td/'NONCE-CRASH-MATRIX-EXHAUSTIVE.json'); bad7=exp7.copy(); bad7[1],bad7[3]=bad7[3],bad7[1]; m['transition_specific_orderings']['N07_RECORD_VERIFIED_OUTCOME']=bad7
 for x in m['vectors']:
  if x['transition']=='N07_RECORD_VERIFIED_OUTCOME': x['normative_order']=bad7
 (td/'NONCE-CRASH-MATRIX-EXHAUSTIVE.json').write_text(json.dumps(m,indent=2,sort_keys=True)+'\n')
 q=subprocess.run([sys.executable,str(td/'validate_m0_r2_contracts.py')],capture_output=True,text=True)
 validator['N07_order_mutation_rejected']=q.returncode!=0 and 'N07_order' in q.stdout
if not all([validator['base_pass'],validator['N04_order_mutation_rejected'],validator['N07_order_mutation_rejected']]): errors.append('VALIDATOR_ENFORCEMENT')
# Privacy receipt internal assertions.
priv=J(privp)
privacy_checks={'expected_identity':sha(privp)==EXPECTED_PRIVACY,'status_pass':priv.get('status')=='R6_R6_PHASE_A_BOUNDED_PRIVACY_SCAN_PASS','blocking_zero':priv.get('blocking_count')==0,'findings_empty':priv.get('findings')==[],'issues_empty':priv.get('issues')==[],'scanner_identity':priv.get('scanner_identity_ok') is True,'detector_identity':priv.get('detector_config_identity_ok') is True,'no_git_or_gca_claim':priv.get('git_history_scan_claimed') is False and priv.get('gca_scan_secrets_claimed') is False}
if not all(privacy_checks.values()): errors.append('PRIVACY')
# Zero effects candidate.
z=J(C/'ZERO-EFFECT-RECEIPT.json'); zero_checks={'all_effects_zero':not any(z.get('effects',{}).values()),'candidate_status':z.get('status')=='PASS','authorized_writes_candidate_only':z.get('authorized_writes')==[str(C)]}
if not all(zero_checks.values()): errors.append('CANDIDATE_ZERO_EFFECT')
# Save reports.
mechanical={'schema':'critical_apply.cah_j1_m0_r2_independent_mechanical.v1','manifest_sha256':sha(manp),'privacy_sha256':sha(privp),'candidate_files':len(all_files),'candidate_dirs_below_root':len(all_dirs),'candidate_symlinks':len(syms),'json_files_parsed':len(parsed),'json_parse_failures':parse_fail,'manifest_artifact_count':man['artifact_count'],'manifest_hash_size_mismatches':mis,'unaccounted_files':unaccounted,'missing_listed_files':missing_listed,'governing_inputs':input_results,'status':'PASS' if not any(e.startswith(('EXPECTED_','MANIFEST_','JSON_','UNACCOUNTED_','MISSING_','GOVERNING_')) for e in errors) else 'HOLD'}
semantic={'schema':'critical_apply.cah_j1_m0_r2_independent_semantic_checks.v1','fixture_checks':fixture_checks,'closeout_checks':close_checks,'nonce_checks':nonce_checks,'coverage_checks':coverage_checks,'transition_vector_counts':counts,'privacy_checks':privacy_checks,'zero_checks':zero_checks,'errors':errors,'status':'PASS' if not errors else 'HOLD'}
(V/'HASH-INVENTORY.json').write_text(json.dumps(mechanical,indent=2,sort_keys=True)+'\n')
(V/'SEMANTIC-CHECKS.json').write_text(json.dumps(semantic,indent=2,sort_keys=True)+'\n')
(V/'VALIDATOR-RUN.json').write_text(json.dumps(validator,indent=2,sort_keys=True)+'\n')
print(json.dumps({'errors':errors,'mechanical':mechanical['status'],'semantic':semantic['status'],'validator':validator},sort_keys=True))
sys.exit(0 if not errors else 1)
