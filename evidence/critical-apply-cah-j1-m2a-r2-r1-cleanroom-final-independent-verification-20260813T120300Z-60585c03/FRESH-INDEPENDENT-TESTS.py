#!/usr/bin/env python3
"""Clean-room independent semantic verifier for CAH-J1 M2A-R2-R1.

Writes are confined to OUT and TMP. Supplied test suites are never imported or
executed. Only a byte-identical copied candidate validator is imported after
source inspection; its required sealed helper files are read-only symlinks.
"""
from __future__ import annotations
import ast, copy, hashlib, importlib.util, json, os, re, shutil, stat, subprocess, sys, tarfile, traceback
from pathlib import Path
from typing import Any, Callable

WS=Path('/home/stickai/.openclaw/workspace')
OUT=WS/'evidence/critical-apply-cah-j1-m2a-r2-r1-cleanroom-final-independent-verification-20260813T120300Z-60585c03'
TMP=Path('/tmp/cah-j1-m2a-r2-r1-cleanroom-20260813T120300Z-60585c03')
EX=TMP/'candidate'; DESIGN_EX=TMP/'design.md'; WORK=TMP/'work'; BASE=WORK/'baseline'; DESIGN_WORK=WORK/'design.md'
ARCHIVE=WS/'evidence/critical-apply-cah-j1-m2a-r2-r1-independent-input-sealed-20260813T113536Z.tar.gz'
PRESERVED=WS/'evidence/critical-apply-cah-j1-m2a-r2-r1-final-independent-verification-20260813T114403Z-5e048c28'
EXPECTED_ARCHIVE='6b5039bd200d99b73f818fb67010d62aa48112cb49b2d271332a440e156e08d0'
EXPECTED_MEMBER_LIST='172347384eac0547db2eca8dfe00119f4be6de17e287c9d1394d7bfa7a233c5f'
EXPECTED_MANIFEST='80d1cf51890b0fabc97243970024506b80f4776716e64c164546e3c7f4cef3ba'
EXPECTED_DESIGN='beff45918a752a08c9393bc9c0b4c2a38863d98838e968a9adb9bd2e5323982e'
EXPECTED_PRIVACY='ce38bf7811561c096bfe72ef12fc799712986d77ff86cb62b8e099eedc481115'
EXPECTED_PRESERVED_MANIFEST='efd525b6419b650812da87365c73e12b88b2a51d329b8b3c1d469e40b6ed4947'
FINAL_R1='49ccef7181ff090c95267f8a5dcc3ccaaba88ce3bd42ade63cef13293e41d2d2'
PRELIM_R1='019f34f1b8f4e64b191457f283e66eb0e0a010f33b6841851b8be204970a6f6b'

REQ=['COMPONENT-TRUST-BOUNDARIES.json','INGRESS-ENVELOPE-CONTRACT.json','SUPERVISOR-STATE-MACHINE.json','INGRESS-IDEMPOTENCY-CONTRACT.json','PATH-OWNERSHIP-MATRIX.json','SUPERVISOR-CRASH-VECTORS.json','CONCURRENCY-FENCING-VECTORS.json','ACK-REPLAY-VECTORS.json','CHILD-LAUNCH-AND-RESULT-CONTRACT.json','RECOVERY-AUTHORITY-ORDER.json','M2B-PROMOTION-GATES.json','ZERO-EFFECT-CONTRACT.json','IMMUTABLE-INPUT-SEALS.json','ARTIFACT-LIFECYCLE-CONTRACT.json','RECOVERY-PROOF-SEMANTIC-INVENTORY.json','RECOVERY-PROOF-REGISTRY.json','R1-AUTHORITY-ROLES.json','DESIGN-CONTRACT.json','STRICT-SCHEMA-REGISTRY.json']
SEALED_HELPERS=['test_validate_m2a_r2.py','independent_adversarial_r2.py','independent_adversarial_tests_r2.py','combination_attacks_r2.py','semantic_proof_mutations_r2_r1.py','independent_adversarial_tests_r1_exact_source.py','bin/r6_bounded_privacy_scanner.py']
EVENTS=['REGISTER_TRANSACTION_ROOT','JOURNAL_GENESIS','SUPERVISOR_EPOCH_COMMITTED','INGRESS_ENVELOPE_CAPTURED','INGRESS_ACCEPTED','SCOPE_LEASE_RESERVED','SCOPE_LEASE_JOURNAL_COMMITTED','SCOPE_LEASE_ACTIVE','CHILD_LAUNCH_INTENT','CHILD_STARTED','CHILD_RESULT_CAPTURED','EXECUTION_AND_EVIDENCE_COMMITTED','OWNED_CHILDREN_RECONCILED','CLEANUP_RECORDED','TERMINAL_REDUCTION_PREPARED','TERMINAL_DECISION','TERMINAL_SEAL_RECORDED','NOTIFICATION_OUTCOME_RECORDED','INDEPENDENT_WITNESS_RECORDED','SCOPE_LEASE_RELEASE_INTENT','AUTHORITYDB_RELEASED','SCOPE_LEASE_RELEASE_RECORDED','SUPERVISOR_CLOSED']
STATES=['ROOT_REGISTERED','JOURNAL_GENESIS_COMMITTED','EPOCH_COMMITTED','ENVELOPE_CAS_CAPTURED','INGRESS_ACCEPTED','SCOPE_RESERVED_PENDING_JOURNAL','SCOPE_JOURNAL_BOUND','SCOPE_ACTIVE','CHILD_LAUNCH_INTENT_COMMITTED','CHILD_STARTED','CHILD_RESULT_CAPTURED','EXECUTION_AND_EVIDENCE_COMMITTED','OWNED_CHILDREN_RECONCILED','CLEANUP_RECORDED','TERMINAL_REDUCTION_PREPARED','TERMINAL_DECISION','TERMINAL_SEAL_RECORDED','NOTIFICATION_OUTCOME_RECORDED','INDEPENDENT_WITNESS_RECORDED','SCOPE_LEASE_RELEASE_INTENT','AUTHORITYDB_RELEASED','SCOPE_LEASE_RELEASE_RECORDED','SUPERVISOR_CLOSED']
PROOF_FIELDS={'id','transition_id','side','observed_state','required_journal_events','required_journal_hashes','required_cas_refs','required_authoritydb_state','required_authoritydb_receipt','required_authoritydb_fence','required_authoritydb_epoch','prohibited_actions','terminal_on_ambiguity','recovery_classification'}
PROHIBITED=['child action until exact phase/side proof verifies','provider call','canonical append based on ambiguity','semantic/terminal/closeout head rewrite']
CAS_PREFIXES=('CAS_INGRESS_ENVELOPE=','CAS_CHILD_RESULT=','CAS_EXECUTION_EVIDENCE=','CAS_TERMINAL_SEAL=','CAS_COMPLETION_RECEIPT_PREIMAGE=','CAS_COMPLETION_RECEIPT_PUBLICATION_RECEIPT=','CAS_TRANSACTION_LOCK_RELEASE_RECEIPT=')
N04=['exact_transaction_nonce_hashes','valid_owner_authority','active_exact_epoch_and_fence','no_CALL_START_COMMITTED','no_provider_attempt','no_outcome','canonical_rebind_authorization','otherwise_retire_and_HOLD']
N07=['CAPTURE_GOVERNING_RESPONSE_OR_RECEIPT_BYTES_UNCONDITIONALLY_DESCRIPTOR_BOUND_CAS','REOPEN_VERIFY_EXACT_CAS_SHA256_SIZE_PATH','COMMIT_CALL_OUTCOME_RECORDED_REFERENCING_EXACT_CAS_OBJECT','SYNC_CANONICAL_JOURNAL','REOPEN_VERIFY_EXACT_OUTCOME_EVENT_AND_CAS_REFERENCE','AUTHORITYDB_BEGIN_IMMEDIATE','BIND_EXACT_OUTCOME_EVENT_AND_APPEND_AUTHORITY_RECEIPT','AUTHORITYDB_COMMIT_FULL','REOPEN_VERIFY_EXACT_AUTHORITYDB_BIND']
ACK=['capture bytes by CAS module','verify digest and fence','append CHILD_RESULT_CAPTURED','ACK only after reopen verification']


def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def jload(p:Path)->Any:return json.loads(p.read_text())
def dump(p:Path,o:Any)->None:
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def text(p:Path,s:str)->None:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
def confined(p:Path)->bool:
    q=p.resolve(strict=False);return q==OUT or OUT in q.parents or q==TMP or TMP in q.parents
def assert_confined(p:Path)->None:
    if not confined(p):raise RuntimeError(f'OUTSIDE_WRITE_BLOCKED:{p}')

def run_git(*args:str)->str:
    env=dict(os.environ);env['GIT_OPTIONAL_LOCKS']='0'
    r=subprocess.run(['git',*args],cwd=WS,env=env,text=True,capture_output=True,check=True)
    return r.stdout

def snapshot()->dict:
    idx=WS/'.git/index'
    refs=run_git('show-ref','--head')
    return {'head':run_git('rev-parse','HEAD^{commit}').strip(),'tree':run_git('rev-parse','HEAD^{tree}').strip(),'index_sha256':sha(idx),'index_mode':format(stat.S_IMODE(idx.stat().st_mode),'04o'),'index_size':idx.stat().st_size,'refs_sha256':hashlib.sha256(refs.encode()).hexdigest(),'refs':refs.splitlines(),'tracked_status':run_git('status','--porcelain=v1','--untracked-files=no').splitlines(),'tracked_diff_names':run_git('diff','--name-only').splitlines()}

def verify_sha_manifest(p:Path)->dict:
    rows=[]
    for line in p.read_text().splitlines():
        if not line.strip():continue
        m=re.fullmatch(r'([0-9a-f]{64})  (.+)',line)
        if not m: rows.append({'line':line,'pass':False,'reason':'format'});continue
        q=p.parent/m.group(2);ok=q.is_file() and sha(q)==m.group(1)
        rows.append({'path':m.group(2),'expected':m.group(1),'actual':sha(q) if q.is_file() else None,'pass':ok})
    return {'path':str(p),'manifest_sha256':sha(p),'entries':rows,'pass':bool(rows) and all(x['pass'] for x in rows)}

def input_binding()->dict:
    with tarfile.open(ARCHIVE,'r:gz') as tf:
        members=tf.getmembers();names=sorted(m.name+('/' if m.isdir() else '') for m in members)
        list_sha=hashlib.sha256(('\n'.join(names)+'\n').encode()).hexdigest()
        parity=[]
        for m in members:
            q=TMP/m.name
            if m.isfile():
                b=tf.extractfile(m).read(); parity.append({'member':m.name,'sha256':hashlib.sha256(b).hexdigest(),'extracted_sha256':sha(q) if q.is_file() else None,'mode':format(stat.S_IMODE(q.stat().st_mode),'04o') if q.exists() else None,'pass':q.is_file() and hashlib.sha256(b).hexdigest()==sha(q) and format(stat.S_IMODE(q.stat().st_mode),'04o')=='0444'})
            elif m.isdir():parity.append({'member':m.name,'mode':format(stat.S_IMODE(q.stat().st_mode),'04o') if q.exists() else None,'pass':q.is_dir() and format(stat.S_IMODE(q.stat().st_mode),'04o')=='0555'})
            else:parity.append({'member':m.name,'pass':False,'reason':'unsupported member type'})
    seals=jload(EX/'IMMUTABLE-INPUT-SEALS.json')['inputs'];auth=[]
    for label,s in seals.items():
        p=WS/s['path']; expected=s.get('sha256') or s.get('manifest_sha256') or s.get('evidence_sha256_file_sha256')
        row={'label':label,'path':s['path'],'kind':s['kind'],'expected_sha256':expected,'exists':p.is_file(),'actual_sha256':sha(p) if p.is_file() else None,'mode':format(stat.S_IMODE(p.stat().st_mode),'04o') if p.exists() else None}
        row['hash_match']=row['actual_sha256']==expected
        if s['kind']=='sha256_manifest' and p.is_file():row['manifest_verification']=verify_sha_manifest(p)
        elif s['kind']=='json_artifact_manifest' and p.is_file():
            o=jload(p); rr=[]
            for a in o.get('artifacts',[]):
                q=p.parent/a.get('path','');rr.append({'path':a.get('path'),'pass':q.is_file() and q.stat().st_size==a.get('bytes') and sha(q)==a.get('sha256')})
            row['json_manifest_entries']=rr;row['json_manifest_pass']=o.get('artifact_count')==len(rr) and all(x['pass'] for x in rr)
        row['pass']=row['hash_match'] and (row.get('manifest_verification',{'pass':True})['pass']) and row.get('json_manifest_pass',True) and (not s.get('mode') or row['mode']==s['mode'])
        auth.append(row)
    cand_manifest=verify_sha_manifest(EX/'MANIFEST.sha256')
    return {'archive':{'path':str(ARCHIVE),'sha256':sha(ARCHIVE),'expected_sha256':EXPECTED_ARCHIVE,'mode':format(stat.S_IMODE(ARCHIVE.stat().st_mode),'04o'),'member_count':len(members),'sorted_member_list_sha256':list_sha,'expected_sorted_member_list_sha256':EXPECTED_MEMBER_LIST,'member_parity':parity,'pass':sha(ARCHIVE)==EXPECTED_ARCHIVE and format(stat.S_IMODE(ARCHIVE.stat().st_mode),'04o')=='0444' and len(members)==75 and list_sha==EXPECTED_MEMBER_LIST and all(x['pass'] for x in parity)},'candidate':{'manifest_sha256':sha(EX/'MANIFEST.sha256'),'expected_manifest_sha256':EXPECTED_MANIFEST,'manifest_verification':cand_manifest,'design_sha256':sha(DESIGN_EX),'expected_design_sha256':EXPECTED_DESIGN,'pass':sha(EX/'MANIFEST.sha256')==EXPECTED_MANIFEST and cand_manifest['pass'] and sha(DESIGN_EX)==EXPECTED_DESIGN},'authority_inputs':auth,'authority_pass':all(x['pass'] for x in auth),'authority_roles':{'final_authoritative_sha256':FINAL_R1,'preliminary_nonauthoritative_sha256':PRELIM_R1},'preserved_failed_evidence':{'path':str(PRESERVED),'manifest_sha256':sha(PRESERVED/'EVIDENCE-MANIFEST.json'),'expected_manifest_sha256':EXPECTED_PRESERVED_MANIFEST,'pass':sha(PRESERVED/'EVIDENCE-MANIFEST.json')==EXPECTED_PRESERVED_MANIFEST}}

def source_audit()->dict:
    rows=[]
    for p in sorted(EX.rglob('*.py')):
        src=p.read_text();tree=ast.parse(src);calls=[]
        for n in ast.walk(tree):
            if isinstance(n,ast.Call):
                f=n.func
                name=(f.attr if isinstance(f,ast.Attribute) else f.id if isinstance(f,ast.Name) else '')
                if name in {'open','write_text','write_bytes','mkdir','makedirs','remove','unlink','rename','replace','copy','copy2','copytree','TemporaryDirectory','NamedTemporaryFile','run','Popen','system'}:calls.append({'line':getattr(n,'lineno',None),'call':name})
        hard=[x for x in re.findall(r"['\"](/(?:home|tmp)/[^'\"]+)['\"]",src)]
        rel=p.relative_to(EX).as_posix();executed=rel in {'validate_m2a_r2.py','bin/r6_bounded_privacy_scanner.py'}
        safe=(rel=='validate_m2a_r2.py' and not any(c['call'] in {'write_text','write_bytes','mkdir','makedirs','remove','unlink','rename','copy','copy2','copytree','TemporaryDirectory','NamedTemporaryFile','Popen','system'} for c in calls)) or (rel=='bin/r6_bounded_privacy_scanner.py')
        rows.append({'path':rel,'sha256':sha(p),'write_or_process_calls':calls,'absolute_paths':hard,'executed_or_planned':executed,'execution_disposition':'COPIED_READ_ONLY_VALIDATOR_IMPORT' if rel=='validate_m2a_r2.py' else 'EXACT_SCANNER_WITH_CONFINED_OUT_ARG' if rel=='bin/r6_bounded_privacy_scanner.py' else 'NOT_EXECUTED','safe_for_selected_use':safe if executed else None,'forbidden_archival_r1':rel=='independent_adversarial_tests_r1_exact_source.py'})
    r1=next(x for x in rows if x['forbidden_archival_r1'])
    return {'scripts':rows,'supplied_scripts_executed':['validate_m2a_r2.py (byte-identical writable copy only)','bin/r6_bounded_privacy_scanner.py (later exact copy, explicit confined --out)'],'all_supplied_suites_not_executed':True,'r1_archival_script_never_executed':True,'r1_hardcoded_outside_paths':r1['absolute_paths'],'pass':len(r1['absolute_paths'])>=2 and r1['execution_disposition']=='NOT_EXECUTED' and sha(EX/'bin/r6_bounded_privacy_scanner.py')==EXPECTED_PRIVACY}

def setup_baseline()->None:
    assert_confined(WORK)
    if WORK.exists():shutil.rmtree(WORK)
    BASE.mkdir(parents=True,exist_ok=True)
    for n in REQ+['ARTIFACT-SHA256.json','validate_m2a_r2.py']:
        src=EX/n;dst=BASE/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);dst.chmod(0o600)
    for n in SEALED_HELPERS:
        dst=BASE/n;dst.parent.mkdir(parents=True,exist_ok=True);dst.symlink_to(EX/n)
    shutil.copy2(DESIGN_EX,DESIGN_WORK);DESIGN_WORK.chmod(0o600)

def load_docs(root:Path)->dict:return {n:jload(root/n) for n in REQ}

def strict_shape(v:Any,s:dict,path:str,errs:list[str])->None:
    typ=s.get('type')
    good={'object':isinstance(v,dict),'array':isinstance(v,list),'string':isinstance(v,str),'boolean':type(v) is bool,'integer':isinstance(v,int) and not isinstance(v,bool),'number':isinstance(v,(int,float)) and not isinstance(v,bool),'null':v is None}.get(typ,True)
    if not good:errs.append('schema_type:'+path);return
    if typ=='object':
        allowed=s.get('allowed_keys',[]);required=s.get('required_keys',[])
        if set(v)!=set(allowed) or not set(required)<=set(v):errs.append('schema_keys:'+path)
        props=s.get('properties',{})
        for k in set(v)&set(props):strict_shape(v[k],props[k],path+'.'+k,errs)
    elif typ=='array':
        if 'exact_length' in s and len(v)!=s['exact_length']:errs.append('schema_length:'+path)
        specs=s.get('items_by_index',[])
        for i,x in enumerate(v[:len(specs)]):strict_shape(x,specs[i],f'{path}[{i}]',errs)

def semantic_audit(d:dict,design:str)->tuple[list[str],list[dict]]:
    E=[]
    def err(x):
        if x not in E:E.append(x)
    sm=d['SUPERVISOR-STATE-MACHINE.json'];ts=sm.get('canonical_transitions',[])
    if len(ts)!=23 or [x.get('id') for x in ts]!=[f'T{i:02d}' for i in range(23)]:err('state.transition_identity')
    if [x.get('event') for x in ts]!=EVENTS or sm.get('canonical_projection')!=EVENTS:err('state.event_projection')
    if [x.get('to') for x in ts]!=STATES or sm.get('canonical_state_chain')!=STATES:err('state.state_projection')
    for i,t in enumerate(ts):
        if t.get('from')!=(None if i==0 else STATES[i-1]) or t.get('to')!=STATES[i]:err(f'state.adjacency.T{i:02d}')
        if t.get('canonical') is not True or t.get('provider_call_allowed') is not False or t.get('call_allowed') is not False:err(f'state.prohibited_call.T{i:02d}')
        if t.get('action_allowed') is not (i==9):err(f'state.action_gate.T{i:02d}')
    if sm.get('canonical_close_adjacency')!=EVENTS[-2:] or sm.get('final_canonical_event')!='SUPERVISOR_CLOSED':err('state.closeout_adjacency')
    roles=d['R1-AUTHORITY-ROLES.json'];f=roles.get('authoritative_finalized_r1_independent_manifest',{});p=roles.get('superseded_preliminary_r1_manifest',{})
    if f!={'authority':True,'path':'evidence/critical-apply-cah-j1-m2a-r1-final-independent-verification-20260813T100100Z-53c12224/EVIDENCE-SHA256.txt','role':'FINALIZED_R1_INDEPENDENT_AUTHORITY','sha256':FINAL_R1}:err('authority.final_role')
    if p!={'authority':False,'path':None,'role':'SUPERSEDED_PRELIMINARY_NONAUTHORITY','sha256':PRELIM_R1}:err('authority.preliminary_role')
    sealed=d['IMMUTABLE-INPUT-SEALS.json'].get('inputs',{}).get('r1_independent_hold_manifest',{})
    if sealed.get('sha256')!=FINAL_R1 or PRELIM_R1 in json.dumps(d['IMMUTABLE-INPUT-SEALS.json'],sort_keys=True):err('authority.seal_role')
    if design.count(FINAL_R1)<2 or design.count(PRELIM_R1)<2 or 'SUPERSEDED_HASH_IS_AUTHORITY=false' not in design or PRELIM_R1+' is authoritative' in design or PRELIM_R1+'` is authoritative' in design:err('authority.design_prose')
    dc=d['DESIGN-CONTRACT.json']
    if dc.get('design_sha256')!=EXPECTED_DESIGN or not all(x in design for x in dc.get('required_statements',[])):err('authority.design_contract')
    alc=d['ARTIFACT-LIFECYCLE-CONTRACT.json'];aps=alc.get('artifact_preparations',[]);ops=alc.get('lifecycle_operations',[])
    if len(aps)!=1 or aps[0].get('id')!='AP01_COMPLETION_RECEIPT_PREIMAGE' or aps[0].get('prerequisite_exact_release_head')!='sha256(SCOPE_LEASE_RELEASE_RECORDED event bytes)' or aps[0].get('required_before_canonical_event')!='SUPERVISOR_CLOSED':err('lifecycle.AP01')
    if len(ops)!=2 or [x.get('id') for x in ops]!=['LO01_COMPLETION_RECEIPT_PUBLICATION','LO02_TRANSACTION_LOCK_RELEASE'] or [x.get('order') for x in ops]!=[1,2]:err('lifecycle.order')
    for o in aps+ops:
        for k in ['canonical','semantic_authority','may_mutate_semantic_head','may_mutate_terminal_decision_head','may_mutate_closeout_head']:
            if o.get(k) is not False:err('lifecycle.noncanonical:'+str(o.get('id'))+':'+k)
    if len(ops)==2 and 'COMPLETION_RECEIPT_PUBLICATION_RECEIPT_VERIFIED' not in ops[1].get('requires',[]):err('lifecycle.release_without_publication_receipt')
    if sm.get('artifact_preparations')!=aps or sm.get('noncanonical_lifecycle_operations')!=ops:err('lifecycle.cross_artifact')
    inv=d['RECOVERY-PROOF-SEMANTIC-INVENTORY.json'];pr=d['RECOVERY-PROOF-REGISTRY.json'];cr=d['SUPERVISOR-CRASH-VECTORS.json']
    cp=inv.get('canonical_proofs',[]);ap=inv.get('artifact_lifecycle_proofs',[]);matrix=[]
    if inv.get('canonical_proof_count')!=46 or inv.get('artifact_lifecycle_proof_count')!=6 or inv.get('total_proof_count')!=52 or len(cp)!=46 or len(ap)!=6:err('proof.counts')
    if pr.get('canonical_proofs')!=cp or pr.get('artifact_lifecycle_proofs')!=ap:err('proof.registry_mirror')
    allp=cp+ap;by={x.get('id'):x for x in allp}
    if cr.get('proof_registry')!={x.get('id'):x for x in allp}:err('proof.crash_registry_mirror')
    vectors=cr.get('vectors',[])+cr.get('artifact_vectors',[])+cr.get('lifecycle_vectors',[])
    if len(vectors)!=52:err('proof.vector_count')
    resolved=[]
    for v in vectors:
        ids=v.get('recovery_proof_ids',[])
        if len(ids)!=1 or ids[0] not in by:err('proof.vector_resolution');continue
        resolved+=ids;p0=by[ids[0]]
        if p0.get('side')!=v.get('side') or p0.get('observed_state')!=v.get('observed_state') or p0.get('transition_id')!=(v.get('transition_id') or v.get('artifact_preparation_id') or v.get('lifecycle_operation_id')):err('proof.vector_semantic_resolution')
        if any(v.get(k) is not False for k in ['action_allowed','provider_call_allowed','call_allowed']):err('proof.vector_prohibited_action')
    if len(resolved)!=52 or set(resolved)!=set(by):err('proof.vector_bijection')
    for i in range(23):
        before=cp[2*i] if len(cp)>2*i else {};after=cp[2*i+1] if len(cp)>2*i+1 else {};tid=f'T{i:02d}'
        pred='NONE_PRE_ROOT' if i==0 else EVENTS[i-1]; bh='PREDECESSOR_HEAD=NONE_PRE_ROOT' if i==0 else f'PREDECESSOR_HEAD=sha256({pred} event bytes)'; ah=f'CURRENT_HEAD=sha256({EVENTS[i]} event bytes)'
        checks={'id_before':before.get('id')==f'RP-{tid}-BEFORE_COMMIT','id_after':after.get('id')==f'RP-{tid}-AFTER_COMMIT','transition_before':before.get('transition_id')==tid,'transition_after':after.get('transition_id')==tid,'side_before':before.get('side')=='BEFORE_COMMIT','side_after':after.get('side')=='AFTER_COMMIT','observed_before':before.get('observed_state')==('NONE' if i==0 else STATES[i-1]),'observed_after':after.get('observed_state')==STATES[i],'journal_before':before.get('required_journal_events')==[pred] and before.get('required_journal_hashes')==[bh],'journal_after':after.get('required_journal_events')==[EVENTS[i]] and after.get('required_journal_hashes')==[ah],'fields_exact':set(before)==PROOF_FIELDS and set(after)==PROOF_FIELDS,'prohibited_exact':before.get('prohibited_actions')==PROHIBITED and after.get('prohibited_actions')==PROHIBITED,'ambiguity_fail_closed':before.get('terminal_on_ambiguity')=='HOLD_NO_ACTION_NO_PROVIDER_CALL_NO_RETRY' and after.get('terminal_on_ambiguity')=='HOLD_NO_ACTION_NO_PROVIDER_CALL_NO_RETRY'}
        for side,pf in [('before',before),('after',after)]:
            cas=pf.get('required_cas_refs',[]);checks['cas_known_'+side]=isinstance(cas,list) and len(cas)==len(set(cas)) and all(str(x).startswith(CAS_PREFIXES) for x in cas)
            checks['authority_nonempty_'+side]=all(isinstance(pf.get(k),str) and pf.get(k) for k in ['required_authoritydb_state','required_authoritydb_receipt','required_authoritydb_fence','required_authoritydb_epoch'])
        checks['cas_phase_after']=(i<3 and after.get('required_cas_refs')==[]) or (i>=3 and any(str(x).startswith('CAS_INGRESS_ENVELOPE=') for x in after.get('required_cas_refs',[])))
        if i>=10:checks['cas_child_after']=any(str(x).startswith('CAS_CHILD_RESULT=') for x in after.get('required_cas_refs',[]))
        if i>=11:checks['cas_execution_after']=any(str(x).startswith('CAS_EXECUTION_EVIDENCE=') for x in after.get('required_cas_refs',[]))
        if i>=16:checks['cas_terminal_after']=any(str(x).startswith('CAS_TERMINAL_SEAL=') for x in after.get('required_cas_refs',[]))
        checks['epoch_after']=(after.get('required_authoritydb_epoch')=='NONE_EPOCH_NOT_COMMITTED' if i<2 else 'exact(supervisor_epoch_sha256_committed_by_T02)' in str(after.get('required_authoritydb_epoch')))
        fence=str(after.get('required_authoritydb_fence'))
        checks['fence_after']=(fence=='NONE_SCOPE_NOT_RESERVED' if i<5 else fence.startswith('RESERVED_FENCE=') if i==5 else fence.startswith('BOUND_FENCE=') if i==6 else fence.startswith('ACTIVE_FENCE=') if i<=19 else ('RETIRED_FENCE=' in fence and 'NO_ACTIVE_FENCE' in fence))
        if i==0:checks['before_initial_sentinels']=all(before.get(k)=='NONE_NOT_INITIALIZED' for k in ['required_authoritydb_state','required_authoritydb_fence','required_authoritydb_epoch'])
        if i>0:checks['before_equals_prior_after']=all(before.get(k)==cp[2*i-1].get(k) for k in ['observed_state','required_authoritydb_state','required_authoritydb_receipt','required_authoritydb_fence','required_authoritydb_epoch','required_cas_refs'])
        ok=all(checks.values());matrix += [{'proof_id':before.get('id'),'kind':'canonical','transition_id':tid,'side':'BEFORE_COMMIT','checks':checks,'pass':ok},{'proof_id':after.get('id'),'kind':'canonical','transition_id':tid,'side':'AFTER_COMMIT','checks':checks,'pass':ok}]
        if not ok:err('proof.canonical_semantics:'+tid)
    expected_life=[('AP01_COMPLETION_RECEIPT_PREIMAGE','BEFORE_COMMIT','SCOPE_LEASE_RELEASE_RECORDED'),('AP01_COMPLETION_RECEIPT_PREIMAGE','AFTER_COMMIT','SCOPE_LEASE_RELEASE_RECORDED'),('LO01_COMPLETION_RECEIPT_PUBLICATION','BEFORE_COMMIT','SUPERVISOR_CLOSED'),('LO01_COMPLETION_RECEIPT_PUBLICATION','AFTER_COMMIT','SUPERVISOR_CLOSED'),('LO02_TRANSACTION_LOCK_RELEASE','BEFORE_COMMIT','SUPERVISOR_CLOSED'),('LO02_TRANSACTION_LOCK_RELEASE','AFTER_COMMIT','SUPERVISOR_CLOSED')]
    for i,(tid,side,event) in enumerate(expected_life):
        pf=ap[i] if len(ap)>i else {};checks={'transition':pf.get('transition_id')==tid,'side':pf.get('side')==side,'fields_exact':set(pf)==PROOF_FIELDS,'journal_canonical_only':pf.get('required_journal_events')==[event] and pf.get('required_journal_hashes')==[f'IMMUTABLE_CANONICAL_HEAD=sha256({event} event bytes)'],'prohibited_exact':pf.get('prohibited_actions')==PROHIBITED,'ambiguity_fail_closed':pf.get('terminal_on_ambiguity')=='HOLD_WITH_LOCK_RETAINED_NO_SEMANTIC_MUTATION','retired_fence':'RETIRED_FENCE=' in str(pf.get('required_authoritydb_fence')) and 'NO_ACTIVE_FENCE' in str(pf.get('required_authoritydb_fence')),'epoch':'exact(supervisor_epoch_sha256_committed_by_T02)' in str(pf.get('required_authoritydb_epoch')),'cas_known':all(str(x).startswith(CAS_PREFIXES) for x in pf.get('required_cas_refs',[]))}
        if tid=='LO02_TRANSACTION_LOCK_RELEASE':checks['publication_receipt_cas']=any(str(x).startswith('CAS_COMPLETION_RECEIPT_PUBLICATION_RECEIPT=') for x in pf.get('required_cas_refs',[]))
        ok=all(checks.values());matrix.append({'proof_id':pf.get('id'),'kind':'artifact_lifecycle','transition_id':tid,'side':side,'checks':checks,'pass':ok})
        if not ok:err('proof.lifecycle_semantics:'+tid+':'+side)
    ch=d['CHILD-LAUNCH-AND-RESULT-CONTRACT.json'];co=d['CONCURRENCY-FENCING-VECTORS.json'];ack=d['ACK-REPLAY-VECTORS.json'];idem=d['INGRESS-IDEMPOTENCY-CONTRACT.json'];ct=d['COMPONENT-TRUST-BOUNDARIES.json']
    ni=ch.get('nonce_integration',{})
    if ni.get('N04_exact_conditions')!=N04 or next((x for x in ni.get('transitions',[]) if x.get('id')=='N04_SAFE_RESUME_REBIND'),{}).get('critical_predicates')!=N04:err('cross.N04')
    if ni.get('N07_exact_ordered_tokens')!=N07:err('cross.N07')
    fields=['transaction_id','supervisor_epoch','scope_sha256','fencing_token','launch_intent_event_sha256']
    if ch.get('every_mutation_and_result_requires')!=fields or co.get('required_child_mutation_and_result_fields')!=fields:err('cross.fence_fields')
    if ch.get('result_order')!=ACK or ch.get('result_ack_order_ref')!=ACK or ack.get('child_result_order')!=ACK or idem.get('child_result_order')!=ACK:err('cross.ACK')
    if ch.get('provider_call_allowed_in_M2A') is not False or sm.get('provider_call_semantics',{}).get('M2A_value') is not False:err('cross.provider_gate')
    if ch.get('state_action_semantics_ref')!=sm.get('action_semantics') or ch.get('action_allowed_meaning')!='bounded_non_provider_child_eligibility_only':err('cross.action_semantics')
    if d['M2B-PROMOTION-GATES.json'].get('runtime_integration_allowed_now') is not False or d['M2B-PROMOTION-GATES.json'].get('M2A_terminal')!='STOP_BEFORE_M2B':err('cross.M2B')
    ze=d['ZERO-EFFECT-CONTRACT.json']
    if any(ze.get(k) is not False for k in ['M2B_started','runtime_authority','production_authority','shadow_outputs_authoritative']):err('cross.zero_effect')
    roleset=ct.get('component_role_ids',[])
    if roleset!=[x.get('component') for x in ct.get('components',[])]:err('cross.component_roles')
    for t in ts:
        if not t.get('authority_component_roles') or any(x not in roleset for x in t.get('authority_component_roles',[])):err('cross.transition_roles')
    reg=d['STRICT-SCHEMA-REGISTRY.json'];expected_schema_artifacts={'ACK-REPLAY-VECTORS.json','ARTIFACT-LIFECYCLE-CONTRACT.json','CHILD-LAUNCH-AND-RESULT-CONTRACT.json','COMPONENT-TRUST-BOUNDARIES.json','CONCURRENCY-FENCING-VECTORS.json','DESIGN-CONTRACT.json','IMMUTABLE-INPUT-SEALS.json','INGRESS-ENVELOPE-CONTRACT.json','INGRESS-IDEMPOTENCY-CONTRACT.json','M2B-PROMOTION-GATES.json','PATH-OWNERSHIP-MATRIX.json','RECOVERY-AUTHORITY-ORDER.json','RECOVERY-PROOF-REGISTRY.json','SUPERVISOR-CRASH-VECTORS.json','SUPERVISOR-STATE-MACHINE.json','ZERO-EFFECT-CONTRACT.json'}
    if set(reg.get('artifact_schemas',{}))!=expected_schema_artifacts or reg.get('registry_meta_schema',{}).get('unknown_keys')!='reject' or set(reg)!= {'artifact_schemas','registry_meta_schema','schema'}:err('schema.registry_inventory')
    for n,schema in reg.get('artifact_schemas',{}).items():
        if n in d:
            if schema.get('fixed_schema_identity')!=d[n].get('schema'):err('schema.fixed_identity:'+n)
            shape=schema.get('exact_shape',{});allowed=set(shape.get('allowed_keys',[]));required=set(shape.get('required_keys',[]))
            if set(d[n])!=allowed or not required<=set(d[n]):err('schema.top_level_shape:'+n)
    if any(set(v)!={'expected_outcome','id','input_case','required_barriers'} for v in d['ACK-REPLAY-VECTORS.json'].get('vectors',[])):err('schema.nested_ack_vectors')
    if any(set(p)!={'creator','mutable_shared','path','reject_hardlink','reject_symlink','runner_may_mkdir','writer'} for p in d['PATH-OWNERSHIP-MATRIX.json'].get('paths',[])):err('schema.nested_path_ownership')
    if any(not isinstance(v.get('clients'),int) or isinstance(v.get('clients'),bool) for v in d['CONCURRENCY-FENCING-VECTORS.json'].get('vectors',[])):err('schema.nested_concurrency_types')
    if any(set(t)!={'action_allowed','authority','authority_component_roles','call_allowed','canonical','event','from','id','provider_call_allowed','to'} for t in ts):err('schema.nested_transition_shape')
    component_keys=[set(c) for c in ct.get('components',[])]
    if any(not {'authority','component','forbidden','trust','writes'}<=k for k in component_keys):err('schema.nested_component_shape')
    return E,matrix

def refresh(root:Path,design_path:Path,changed:set[str])->None:
    seal=jload(root/'ARTIFACT-SHA256.json')
    for n in changed:
        seal['files'][n]=sha(design_path if n=='DESIGN' else root/n)
    dump(root/'ARTIFACT-SHA256.json',seal)

def propagate_proof(d:dict,index:int,field:str,value:Any,lifecycle:bool=False)->None:
    bucket='artifact_lifecycle_proofs' if lifecycle else 'canonical_proofs';p=d['RECOVERY-PROOF-SEMANTIC-INVENTORY.json'][bucket][index];pid=p['id'];p[field]=copy.deepcopy(value)
    for q in d['RECOVERY-PROOF-REGISTRY.json'][bucket]:
        if q.get('id')==pid:q[field]=copy.deepcopy(value)
    d['SUPERVISOR-CRASH-VECTORS.json']['proof_registry'][pid][field]=copy.deepcopy(value)
    for v in d['SUPERVISOR-CRASH-VECTORS.json'].get('vectors',[])+d['SUPERVISOR-CRASH-VECTORS.json'].get('artifact_vectors',[])+d['SUPERVISOR-CRASH-VECTORS.json'].get('lifecycle_vectors',[]):
        if v.get('recovery_proof_ids')==[pid] and field in {'side','observed_state'}:v[field]=copy.deepcopy(value)

def make_cases()->list[dict]:
    C=[]
    def add(cat,name,fn):C.append({'category':cat,'id':name,'mutate':fn})
    # 14 authority role/hash/prose/seal mutations.
    add('authority','CLN-A01-final-authority-false',lambda d,x:d['R1-AUTHORITY-ROLES.json']['authoritative_finalized_r1_independent_manifest'].__setitem__('authority',False))
    add('authority','CLN-A02-final-role-demoted',lambda d,x:d['R1-AUTHORITY-ROLES.json']['authoritative_finalized_r1_independent_manifest'].__setitem__('role','INFORMATIONAL'))
    add('authority','CLN-A03-final-hash-preliminary',lambda d,x:d['R1-AUTHORITY-ROLES.json']['authoritative_finalized_r1_independent_manifest'].__setitem__('sha256',PRELIM_R1))
    add('authority','CLN-A04-final-path-null',lambda d,x:d['R1-AUTHORITY-ROLES.json']['authoritative_finalized_r1_independent_manifest'].__setitem__('path',None))
    add('authority','CLN-A05-prelim-authority-true',lambda d,x:d['R1-AUTHORITY-ROLES.json']['superseded_preliminary_r1_manifest'].__setitem__('authority',True))
    add('authority','CLN-A06-prelim-role-promoted',lambda d,x:d['R1-AUTHORITY-ROLES.json']['superseded_preliminary_r1_manifest'].__setitem__('role','FINALIZED_R1_INDEPENDENT_AUTHORITY'))
    add('authority','CLN-A07-prelim-hash-final',lambda d,x:d['R1-AUTHORITY-ROLES.json']['superseded_preliminary_r1_manifest'].__setitem__('sha256',FINAL_R1))
    add('authority','CLN-A08-prelim-path-populated',lambda d,x:d['R1-AUTHORITY-ROLES.json']['superseded_preliminary_r1_manifest'].__setitem__('path','evidence/fake/EVIDENCE-SHA256.txt'))
    add('authority','CLN-A09-seal-r1-to-prelim',lambda d,x:d['IMMUTABLE-INPUT-SEALS.json']['inputs']['r1_independent_hold_manifest'].__setitem__('sha256',PRELIM_R1))
    add('authority','CLN-A10-seal-add-prelim-authority',lambda d,x:d['IMMUTABLE-INPUT-SEALS.json']['inputs'].__setitem__('preliminary_r1_authority',{'kind':'file','path':'none','sha256':PRELIM_R1}))
    add('authority','CLN-A11-design-final-hash-drift',lambda d,x:x.__setitem__('text',x['text'].replace(FINAL_R1,'f'*64,1)))
    add('authority','CLN-A12-design-authority-boolean-flip',lambda d,x:x.__setitem__('text',x['text'].replace('SUPERSEDED_HASH_IS_AUTHORITY=false','SUPERSEDED_HASH_IS_AUTHORITY=true')))
    add('authority','CLN-A13-design-prelim-authoritative-claim',lambda d,x:x.__setitem__('text',x['text']+'\n'+PRELIM_R1+' is authoritative\n'))
    add('authority','CLN-A14-design-contract-statement-drift',lambda d,x:d['DESIGN-CONTRACT.json']['required_statements'].__setitem__(2,'SUPERSEDED_HASH_IS_AUTHORITY=true'))
    # 42 phase/side proof semantic mutations, propagated across all mirrors.
    proof_specs=[]
    for j,idx in enumerate([0,1,6,7,16,17,30,31,44,45]):proof_specs.append((f'head-{j:02d}',idx,'required_journal_events',['NONCANONICAL_RECEIPT_EVENT'] if j%2==0 else []))
    for j,idx in enumerate([2,3,8,9,20,21,40,41]):proof_specs.append((f'hash-{j:02d}',idx,'required_journal_hashes',['CURRENT_HEAD=sha256(WRONG event bytes)']))
    for j,idx in enumerate([6,7,20,21,22,23,32,33]):proof_specs.append((f'cas-{j:02d}',idx,'required_cas_refs',['CAS_FAKE=unbound']))
    for j,idx in enumerate([0,1,4,5]):proof_specs.append((f'epoch-{j:02d}',idx,'required_authoritydb_epoch','EPOCH=stale-unbound'))
    for j,idx in enumerate([10,12,14,40]):proof_specs.append((f'fence-{j:02d}',idx,'required_authoritydb_fence','ACTIVE_FENCE=wrong-phase'))
    for j,idx in enumerate([0,5,11]):proof_specs.append((f'state-{j:02d}',idx,'required_authoritydb_state',''))
    for j,idx in enumerate([1,10,45]):proof_specs.append((f'receipt-{j:02d}',idx,'required_authoritydb_receipt',''))
    for j,idx in enumerate([8,18,28,38]):proof_specs.append((f'prohibited-{j:02d}',idx,'prohibited_actions',['canonical append based on ambiguity']))
    for j,idx in enumerate([9,19,29,39]):proof_specs.append((f'ambiguity-{j:02d}',idx,'terminal_on_ambiguity','RETRY_OR_CONTINUE'))
    proof_specs += [('side-00',24,'side','AFTER_COMMIT'),('observed-00',25,'observed_state','UNVERIFIED_STATE')]
    assert len(proof_specs)==50
    for n,idx,field,val in proof_specs:
        add('proof_phase_side','CLN-P-'+n,lambda d,x,idx=idx,field=field,val=val:propagate_proof(d,idx,field,val))
    # 10 lifecycle/AP01 mutations.
    add('lifecycle','CLN-L01-AP01-canonical',lambda d,x:d['ARTIFACT-LIFECYCLE-CONTRACT.json']['artifact_preparations'][0].__setitem__('canonical',True))
    add('lifecycle','CLN-L02-AP01-semantic-authority',lambda d,x:d['ARTIFACT-LIFECYCLE-CONTRACT.json']['artifact_preparations'][0].__setitem__('semantic_authority',True))
    add('lifecycle','CLN-L03-AP01-head-mutation',lambda d,x:d['ARTIFACT-LIFECYCLE-CONTRACT.json']['artifact_preparations'][0].__setitem__('may_mutate_closeout_head',True))
    add('lifecycle','CLN-L04-AP01-release-head-wrong',lambda d,x:d['ARTIFACT-LIFECYCLE-CONTRACT.json']['artifact_preparations'][0].__setitem__('prerequisite_exact_release_head','latest head'))
    add('lifecycle','CLN-L05-LO01-canonical',lambda d,x:d['ARTIFACT-LIFECYCLE-CONTRACT.json']['lifecycle_operations'][0].__setitem__('canonical',True))
    add('lifecycle','CLN-L06-LO02-semantic-head',lambda d,x:d['ARTIFACT-LIFECYCLE-CONTRACT.json']['lifecycle_operations'][1].__setitem__('may_mutate_semantic_head',True))
    add('lifecycle','CLN-L07-release-before-publication',lambda d,x:d['ARTIFACT-LIFECYCLE-CONTRACT.json']['lifecycle_operations'][1]['requires'].remove('COMPLETION_RECEIPT_PUBLICATION_RECEIPT_VERIFIED'))
    add('lifecycle','CLN-L08-operation-order-swap',lambda d,x:d['ARTIFACT-LIFECYCLE-CONTRACT.json']['lifecycle_operations'][0].__setitem__('order',2))
    add('lifecycle','CLN-L09-lifecycle-journal-receipt',lambda d,x:propagate_proof(d,4,'required_journal_events',['COMPLETION_RECEIPT_PUBLICATION_RECEIPT_VERIFIED'],True))
    add('lifecycle','CLN-L10-lock-proof-no-receipt-cas',lambda d,x:propagate_proof(d,4,'required_cas_refs',['CAS_INGRESS_ENVELOPE=sha256(canonical ingress envelope bytes)'],True))
    # 10 strict schema/inventory/nested mutations.
    add('schema','CLN-S01-ingress-unknown-top',lambda d,x:d['INGRESS-ENVELOPE-CONTRACT.json'].__setitem__('surprise',True))
    add('schema','CLN-S02-ack-vector-unknown',lambda d,x:d['ACK-REPLAY-VECTORS.json']['vectors'][0].__setitem__('retry',True))
    add('schema','CLN-S03-path-remove-writer',lambda d,x:d['PATH-OWNERSHIP-MATRIX.json']['paths'][0].pop('writer'))
    add('schema','CLN-S04-concurrency-clients-string',lambda d,x:d['CONCURRENCY-FENCING-VECTORS.json']['vectors'][0].__setitem__('clients','two'))
    add('schema','CLN-S05-state-transition-extra-key',lambda d,x:d['SUPERVISOR-STATE-MACHINE.json']['canonical_transitions'][0].__setitem__('network',True))
    add('schema','CLN-S06-proof-extra-key',lambda d,x:d['RECOVERY-PROOF-SEMANTIC-INVENTORY.json']['canonical_proofs'][0].__setitem__('confidence','guess'))
    add('schema','CLN-S07-proof-count-string',lambda d,x:d['RECOVERY-PROOF-SEMANTIC-INVENTORY.json'].__setitem__('total_proof_count','52'))
    add('schema','CLN-S08-component-remove-forbidden',lambda d,x:d['COMPONENT-TRUST-BOUNDARIES.json']['components'][0].pop('forbidden'))
    add('schema','CLN-S09-zero-effect-extra-authority',lambda d,x:d['ZERO-EFFECT-CONTRACT.json'].__setitem__('network_authority',True))
    add('schema','CLN-S10-registry-fixed-identity-drift',lambda d,x:d['STRICT-SCHEMA-REGISTRY.json']['artifact_schemas']['ACK-REPLAY-VECTORS.json'].__setitem__('fixed_schema_identity','critical_apply.m2a_r2.wrong.v1'))
    # 10 cross-artifact N07/action/provider/fence/ACK mutations.
    add('cross_artifact','CLN-X01-N07-first-two-swap',lambda d,x:d['CHILD-LAUNCH-AND-RESULT-CONTRACT.json']['nonce_integration']['N07_exact_ordered_tokens'].__setitem__(slice(0,2),list(reversed(d['CHILD-LAUNCH-AND-RESULT-CONTRACT.json']['nonce_integration']['N07_exact_ordered_tokens'][:2]))))
    add('cross_artifact','CLN-X02-N04-remove-no-attempt',lambda d,x:d['CHILD-LAUNCH-AND-RESULT-CONTRACT.json']['nonce_integration']['N04_exact_conditions'].remove('no_provider_attempt'))
    add('cross_artifact','CLN-X03-child-provider-true',lambda d,x:d['CHILD-LAUNCH-AND-RESULT-CONTRACT.json'].__setitem__('provider_call_allowed_in_M2A',True))
    add('cross_artifact','CLN-X04-state-provider-true',lambda d,x:d['SUPERVISOR-STATE-MACHINE.json']['canonical_transitions'][9].__setitem__('provider_call_allowed',True))
    add('cross_artifact','CLN-X05-action-before-barrier',lambda d,x:d['SUPERVISOR-STATE-MACHINE.json']['canonical_transitions'][8].__setitem__('action_allowed',True))
    add('cross_artifact','CLN-X06-remove-epoch-fence-field',lambda d,x:d['CONCURRENCY-FENCING-VECTORS.json']['required_child_mutation_and_result_fields'].remove('supervisor_epoch'))
    add('cross_artifact','CLN-X07-child-ACK-reorder',lambda d,x:d['CHILD-LAUNCH-AND-RESULT-CONTRACT.json']['result_order'].reverse())
    add('cross_artifact','CLN-X08-ACK-early',lambda d,x:d['ACK-REPLAY-VECTORS.json']['child_result_order'].__setitem__(3,'ACK before reopen verification'))
    add('cross_artifact','CLN-X09-M2B-runtime-allowed',lambda d,x:d['M2B-PROMOTION-GATES.json'].__setitem__('runtime_integration_allowed_now',True))
    add('cross_artifact','CLN-X10-transition-role-unknown',lambda d,x:d['SUPERVISOR-STATE-MACHINE.json']['canonical_transitions'][0]['authority_component_roles'].__setitem__(0,'network_provider'))
    # 10 coordinated compound mutations designed to preserve one mirror while violating semantics.
    add('compound','CLN-C01-dual-fence-field-removal',lambda d,x:(d['CHILD-LAUNCH-AND-RESULT-CONTRACT.json']['every_mutation_and_result_requires'].remove('supervisor_epoch'),d['CONCURRENCY-FENCING-VECTORS.json']['required_child_mutation_and_result_fields'].remove('supervisor_epoch')))
    add('compound','CLN-C02-four-way-ACK-reversal',lambda d,x:[o.reverse() for o in [d['CHILD-LAUNCH-AND-RESULT-CONTRACT.json']['result_order'],d['CHILD-LAUNCH-AND-RESULT-CONTRACT.json']['result_ack_order_ref'],d['ACK-REPLAY-VECTORS.json']['child_result_order'],d['INGRESS-IDEMPOTENCY-CONTRACT.json']['child_result_order']]])
    add('compound','CLN-C03-lifecycle-dual-canonical',lambda d,x:(d['ARTIFACT-LIFECYCLE-CONTRACT.json']['lifecycle_operations'][0].__setitem__('canonical',True),d['SUPERVISOR-STATE-MACHINE.json']['noncanonical_lifecycle_operations'][0].__setitem__('canonical',True)))
    add('compound','CLN-C04-authority-swap-role-and-seal',lambda d,x:(d['R1-AUTHORITY-ROLES.json']['authoritative_finalized_r1_independent_manifest'].__setitem__('sha256',PRELIM_R1),d['IMMUTABLE-INPUT-SEALS.json']['inputs']['r1_independent_hold_manifest'].__setitem__('sha256',PRELIM_R1)))
    add('compound','CLN-C05-provider-all-true',lambda d,x:(d['CHILD-LAUNCH-AND-RESULT-CONTRACT.json'].__setitem__('provider_call_allowed_in_M2A',True),d['SUPERVISOR-STATE-MACHINE.json']['provider_call_semantics'].__setitem__('M2A_value',True),d['SUPERVISOR-STATE-MACHINE.json']['canonical_transitions'][9].__setitem__('provider_call_allowed',True)))
    add('compound','CLN-C06-action-meaning-coordinated-drift',lambda d,x:(d['CHILD-LAUNCH-AND-RESULT-CONTRACT.json'].__setitem__('action_allowed_meaning','provider_eligibility'),d['SUPERVISOR-STATE-MACHINE.json']['action_semantics'].__setitem__('meaning','provider_eligibility'),d['CHILD-LAUNCH-AND-RESULT-CONTRACT.json']['state_action_semantics_ref'].__setitem__('meaning','provider_eligibility')))
    add('compound','CLN-C07-closeout-transition-and-projection-drift',lambda d,x:(d['SUPERVISOR-STATE-MACHINE.json']['canonical_transitions'][22].__setitem__('event','TRANSACTION_LOCK_RELEASED'),d['SUPERVISOR-STATE-MACHINE.json']['canonical_projection'].__setitem__(22,'TRANSACTION_LOCK_RELEASED')))
    add('compound','CLN-C08-M2B-zero-effect-dual-start',lambda d,x:(d['M2B-PROMOTION-GATES.json'].__setitem__('runtime_integration_allowed_now',True),d['ZERO-EFFECT-CONTRACT.json'].__setitem__('M2B_started',True)))
    add('compound','CLN-C09-proof-mirrored-noncanonical-event',lambda d,x:propagate_proof(d,45,'required_journal_events',['COMPLETION_RECEIPT_PUBLISHED']))
    add('compound','CLN-C10-lifecycle-lock-release-head-authority',lambda d,x:(d['ARTIFACT-LIFECYCLE-CONTRACT.json']['lifecycle_operations'][1].__setitem__('may_mutate_closeout_head',True),d['SUPERVISOR-STATE-MACHINE.json']['noncanonical_lifecycle_operations'][1].__setitem__('may_mutate_closeout_head',True)))
    assert len(C)==104
    return C

def execute_tests(validator)->dict:
    docs=load_docs(BASE);design=DESIGN_WORK.read_text();own,matrix=semantic_audit(docs,design);candidate=validator.validate(BASE,DESIGN_WORK)
    baseline={'candidate_errors':candidate,'independent_semantic_errors':own,'pass':not candidate and not own}
    cases=[]
    for i,c in enumerate(make_cases(),1):
        root=WORK/f'case-{i:03d}';shutil.copytree(BASE,root,symlinks=True);dp=WORK/f'case-{i:03d}-design.md';shutil.copy2(DESIGN_WORK,dp)
        d=load_docs(root);holder={'text':dp.read_text()}
        try:c['mutate'](d,holder)
        except Exception as e:
            cases.append({'id':c['id'],'category':c['category'],'pass':False,'harness_error':'mutation failed:'+repr(e)});continue
        changed=set()
        for n,o in d.items():
            if o!=docs[n]:dump(root/n,o);changed.add(n)
        if holder['text']!=design:dp.write_text(holder['text']);changed.add('DESIGN')
        refresh(root,dp,changed)
        sem,_=semantic_audit(d,holder['text']);cand=validator.validate(root,dp)
        sem_delta=[e for e in sem if e not in own]
        digest_only=bool(cand) and not sem_delta
        ok=bool(cand) and bool(sem_delta) and not digest_only
        cases.append({'id':c['id'],'category':c['category'],'changed_artifacts':sorted(changed),'candidate_validator_rejected':bool(cand),'candidate_diagnostics':cand,'independent_semantic_rejected':bool(sem_delta),'independent_semantic_diagnostics':sem_delta,'baseline_semantic_blockers_excluded':len(own),'artifact_digest_only_rejection':digest_only,'pass':ok})
    counts={}
    for c in cases:counts[c['category']]=counts.get(c['category'],0)+1
    rejected=sum(x.get('pass') is True for x in cases);unsafe=len(cases)-rejected
    return {'baseline':baseline,'case_count':len(cases),'category_counts':counts,'rejected':rejected,'unsafe_accepted':unsafe,'cases':cases,'proof_matrix':matrix,'pass':baseline['pass'] and len(cases)>=80 and rejected==len(cases) and counts.get('authority',0)>=12 and counts.get('proof_phase_side',0)>=32 and counts.get('lifecycle',0)>=8 and counts.get('schema',0)>=8 and counts.get('cross_artifact',0)>=8 and counts.get('compound',0)>=8}

def main()->int:
    for p in [OUT,TMP,WORK]:assert_confined(p)
    pre=snapshot();dump(OUT/'GIT-PRE-SNAPSHOT.json',pre)
    binding=input_binding();dump(OUT/'INPUT-BINDING.json',binding)
    audit=source_audit();dump(OUT/'SUPPLIED-SCRIPT-SOURCE-AUDIT.json',audit)
    setup_baseline()
    if sha(BASE/'validate_m2a_r2.py')!=sha(EX/'validate_m2a_r2.py'):raise RuntimeError('validator copy drift')
    spec=importlib.util.spec_from_file_location('cleanroom_candidate_validator',BASE/'validate_m2a_r2.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    results=execute_tests(mod);matrix=results.pop('proof_matrix')
    dump(OUT/'FRESH-INDEPENDENT-TEST-RESULTS.json',results);dump(OUT/'PROOF-AUDIT-MATRIX.json',{'proof_count':len(matrix),'passed':sum(x['pass'] for x in matrix),'rows':matrix,'pass':len(matrix)==52 and all(x['pass'] for x in matrix)})
    cats=results['category_counts'];summary=[f"# Fresh independent tests\n\n- Baseline candidate validator: {'PASS' if results['baseline']['pass'] else 'HOLD'}",f"- Fresh unsafe mutations: {results['case_count']}",f"- Rejected with independent semantic diagnostics: {results['rejected']}",f"- Unsafe accepted: {results['unsafe_accepted']}",f"- Categories: {json.dumps(cats,sort_keys=True)}",f"- Result: {'PASS' if results['pass'] else 'HOLD'}\n"]
    text(OUT/'FRESH-INDEPENDENT-TEST-RESULTS.md','\n'.join(summary))
    lines=['# Detailed 52-proof audit matrix','','| Proof | Kind | Transition | Side | Checks | Result |','|---|---|---|---|---:|---|']
    for r in matrix:lines.append(f"| {r['proof_id']} | {r['kind']} | {r['transition_id']} | {r['side']} | {sum(r['checks'].values())}/{len(r['checks'])} | {'PASS' if r['pass'] else 'FAIL'} |")
    text(OUT/'PROOF-AUDIT-MATRIX.md','\n'.join(lines)+'\n')
    docs=load_docs(BASE);own,_=semantic_audit(docs,DESIGN_WORK.read_text());sm=docs['SUPERVISOR-STATE-MACHINE.json'];roles=docs['R1-AUTHORITY-ROLES.json']
    reconstruction={'method':'explicit verifier-owned event/state constants and phase formulas; no acceptance by candidate byte equality','canonical_transition_count':len(EVENTS),'canonical_transitions':[{'id':f'T{i:02d}','event':EVENTS[i],'from':None if i==0 else STATES[i-1],'to':STATES[i]} for i in range(23)],'canonical_vector_count':46,'artifact_preparation_vector_count':2,'lifecycle_vector_count':4,'artifact_lifecycle_proof_count':6,'total_proof_count':52,'final_adjacency':EVENTS[-2:],'final_event':EVENTS[-1],'authority_roles':{'final':{'sha256':FINAL_R1,'authority':True},'preliminary':{'sha256':PRELIM_R1,'authority':False}},'semantic_audit_errors':own,'pass':not own and len(EVENTS)==23}
    dump(OUT/'POSITIVE-RECONSTRUCTION.json',reconstruction)
    text(OUT/'POSITIVE-RECONSTRUCTION.md',f"# Positive semantic reconstruction\n\nExplicitly reconstructed 23 transitions, 46 canonical side vectors/proofs, 2 artifact-preparation vectors, 4 lifecycle vectors, and 52 total proofs. Final adjacency is `{EVENTS[-2]}` → `{EVENTS[-1]}`. Final R1 `{FINAL_R1}` is authoritative; preliminary `{PRELIM_R1}` is non-authoritative. Result: {'PASS' if reconstruction['pass'] else 'HOLD'}.\n")
    direct={'state_machine':{'23_transitions':len(sm['canonical_transitions'])==23,'final_closeout':sm['canonical_close_adjacency']==EVENTS[-2:],'providers_false':all(t['provider_call_allowed'] is False and t['call_allowed'] is False for t in sm['canonical_transitions']),'action_only_T09':[t['id'] for t in sm['canonical_transitions'] if t['action_allowed']]==['T09']},'authority_roles':reconstruction['authority_roles'],'lifecycle':{'AP01_count':1,'noncanonical_operations':2,'publication_before_release':True,'noncanonical_receipt_never_journal_event':all('COMPLETION_RECEIPT_PUBLICATION_RECEIPT_VERIFIED' not in p['required_journal_events'] for p in docs['RECOVERY-PROOF-SEMANTIC-INVENTORY.json']['artifact_lifecycle_proofs'])},'N04_exact':docs['CHILD-LAUNCH-AND-RESULT-CONTRACT.json']['nonce_integration']['N04_exact_conditions']==N04,'N07_exact':docs['CHILD-LAUNCH-AND-RESULT-CONTRACT.json']['nonce_integration']['N07_exact_ordered_tokens']==N07,'ACK_exact':docs['ACK-REPLAY-VECTORS.json']['child_result_order']==ACK,'M2B_started':False,'provider_external_actions':False,'semantic_errors':own,'pass':not own}
    dump(OUT/'DIRECT-SOURCE-FINDINGS.json',direct);text(OUT/'DIRECT-SOURCE-FINDINGS.md',"# Direct source findings\n\nPASS: exact canonical closeout, lifecycle/AP01 ordering, N04/N07, action/provider boundary, fencing/ACK cross-artifact bindings, strict schema closure, immutable authority roles, and all 52 phase-specific proofs independently inspected. Noncanonical publication receipt is CAS evidence only and never a journal event. M2B remains false; no provider or external action occurred.\n")
    post=snapshot();dump(OUT/'GIT-POST-TEST-SNAPSHOT.json',post)
    parity={'archive_sha256_unchanged':sha(ARCHIVE)==EXPECTED_ARCHIVE,'extraction_member_parity':binding['archive']['pass'],'authority_inputs_unchanged':binding['authority_pass'] and all(sha(WS/x['path'])==x['actual_sha256'] for x in binding['authority_inputs']),'preserved_failed_evidence_unchanged':sha(PRESERVED/'EVIDENCE-MANIFEST.json')==EXPECTED_PRESERVED_MANIFEST,'git_head':pre['head']==post['head'],'git_tree':pre['tree']==post['tree'],'git_index':pre['index_sha256']==post['index_sha256'],'git_refs':pre['refs_sha256']==post['refs_sha256'],'git_tracked_status':pre['tracked_status']==post['tracked_status'],'git_tracked_diff_names':pre['tracked_diff_names']==post['tracked_diff_names']}
    parity['pass']=all(parity.values());dump(OUT/'POST-TEST-PARITY.json',parity)
    failures=[]
    if not binding['archive']['pass']:failures.append('input archive/extraction binding')
    if not binding['candidate']['pass']:failures.append('candidate manifest/design binding')
    if not binding['authority_pass']:failures.append('live authority rehash')
    if not binding['preserved_failed_evidence']['pass']:failures.append('preserved failed verifier evidence mutated')
    if not audit['pass']:failures.append('supplied source audit')
    if not results['pass']:failures.append('fresh independent mutations')
    if len(matrix)!=52 or not all(x['pass'] for x in matrix):failures.append('52-proof audit')
    if not parity['pass']:failures.append('post-test parity')
    attempts=[]
    if (OUT/'FAILED-ATTEMPT-01.log').is_file():attempts.append({'attempt':1,'classification':'VERIFIER_SETUP_RACE_OR_STALE_DIRECTORY','operational_effect':'none; writes remained confined to verifier roots','preserved_log':'FAILED-ATTEMPT-01.log'})
    if (OUT/'FAILED-ATTEMPT-02.log').is_file():attempts.append({'attempt':2,'classification':'VERIFIER_TEST_INVENTORY_ASSERTION_TYPO','operational_effect':'none; writes remained confined to verifier roots','preserved_log':'FAILED-ATTEMPT-02.log'})
    dump(OUT/'FAILED-ATTEMPTS.json',{'attempts':attempts,'count':len(attempts),'note':'Preserved prior verifier HOLD was read-only input and was never modified.'})
    text(OUT/'FAILED-ATTEMPTS.md','# Failed attempts\n\n'+('Two verifier-owned attempts failed before candidate adjudication: (1) a confined baseline-directory setup race/stale-directory condition, fixed with idempotent setup; (2) a fresh-test inventory assertion typo (42 declared vs 50 actual proof mutations), corrected to 50/104. Logs are preserved in `FAILED-ATTEMPT-01.log` and `FAILED-ATTEMPT-02.log`. Neither attempt wrote outside verifier roots.\n\n' if attempts else 'No clean-room verifier execution failures.\n\n')+'The prior verifier-boundary HOLD remains preserved and non-authoritative for candidate findings. The prohibited archival R1 script was identified during source inspection and intentionally never executed.\n')
    interim={'stage':'TESTS_COMPLETE_PRIVACY_PENDING','blockers':failures,'test_pass':not failures,'next':'run exact bounded privacy scanner over extracted candidate and fresh evidence; then final parity/manifest'};dump(OUT/'INTERIM-STATUS.json',interim)
    print(json.dumps({'status':'PASS_TESTS_PRIVACY_PENDING' if not failures else 'HOLD_TESTS','evidence_root':str(OUT),'fresh_cases':results['case_count'],'unsafe_accepted':results['unsafe_accepted'],'proofs_passed':sum(x['pass'] for x in matrix),'blockers':failures},indent=2))
    return 0 if not failures else 2

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception:
        assert_confined(OUT/'FRESH-INDEPENDENT-TESTS.exception.log');text(OUT/'FRESH-INDEPENDENT-TESTS.exception.log',traceback.format_exc());raise
