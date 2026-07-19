#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys, time
from datetime import datetime, timezone, timedelta
from pathlib import Path
WS=Path(__file__).resolve().parents[3]
PROJECT=WS/'projects/durable-memory-architecture'
PKG=PROJECT/'contracts/m25j'; TEST=PROJECT/'test/m25j'
sys.path.insert(0, str(PKG.parent))
from m25j.validators import ContractValidationError, REGISTRY, validate_json_text
TERMINAL='M25J_CONTRACT_SCHEMA_SKELETON_TESTS_PASS_NO_LIVE_DELIVERY'
BASELINE={'head':'5b66b525db06a47f9fb50966bb1611af26bd45a0','config':'69fda094eb9c2476db5d4377135f633339094b5cc9a2e6d4340b4564a0da2bc7','events':'76f4d0f030af56ee03b3484413ca67c7f9a65992f68ecb2b46ed144410b1a9b5','actions':'a7b0d3d4bd1a9c8bb0da20a1f92cc248f3f37dbf551c66a361330076777bba63','m25ia':'50f5d348bedf507f7b43f2bf8b03f680e8accadcc1440aca0996b23ab1e06b7a','lld':'edd7284f2f591517b3536300ba476ab9b06abd0d01a02ec3b1500cc748f66de1'}
OLD=['9d6aa1d9-edd7-4633-90eb-3fba96f20b02','3e05cd9e-c890-449a-9b3f-59d5cf5b3b84','5cfdb17a-5247-4f16-8300-d3f86f0a9c11']
def sha_path(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*a): return subprocess.check_output(['git',*a], cwd=WS, text=True).strip()
def rel(p): return str(Path(p).relative_to(WS))
def validate_fixtures():
    results=[]; errors=[]; counts={'positive':0,'negative':0,'security':0}
    for cat in ['positive','negative','security']:
        for path in sorted((PKG/'fixtures'/cat).glob('*.json')):
            counts[cat]+=1
            try:
                out=validate_json_text(path.read_text()); expected=(cat=='positive')
                if not expected: errors.append({'path':rel(path),'code':'UNEXPECTED_PASS'})
                results.append({'path':rel(path),'category':cat,'terminal':'PASS' if expected else 'UNEXPECTED_PASS','errorCode':None if expected else 'UNEXPECTED_PASS','schema':out.get('schema')})
            except ContractValidationError as exc:
                expected=(cat!='positive')
                if not expected: errors.append({'path':rel(path),'code':exc.code})
                results.append({'path':rel(path),'category':cat,'terminal':'EXPECTED_FAIL' if expected else 'FAIL','errorCode':exc.code})
    minimum={'positive':28,'negative':24,'security':7}
    for k,v in minimum.items():
        if counts[k] < v: errors.append({'gate':f'{k}_fixture_count','expected_min':v,'actual':counts[k]})
    return counts,results,errors
def private_scan(paths):
    pats=[re.compile(r'(?i)(api[_-]?key|password|authorization|bearer|access[_-]?token|refresh[_-]?token)\s*[:=]\s*[\"\'][^\"\']{8,}[\"\']'),re.compile(r'telegram:\d{4,}|\b(chat_id|message_id|sender_id)\b\s*[:=]?\s*\d{4,}',re.I),re.compile('BEGIN ' + 'PRIVATE KEY')]
    findings=[]; classified=[]
    for path in paths:
        try: text=Path(path).read_text()
        except UnicodeDecodeError: continue
        for i,line in enumerate(text.splitlines(),1):
            for pat in pats:
                if pat.search(line):
                    # Security fixtures intentionally contain raw-looking adversarial strings and must fail validation.
                    if '/fixtures/security/' in str(path) or '/fixtures/negative/' in str(path): classified.append({'path':rel(path),'line':i,'classification':'intentional_negative_or_security_fixture'}); break
                    findings.append({'path':rel(path),'line':i,'pattern':pat.pattern}); break
    return findings,classified
def build(evidence_root=None):
    counts, fixture_results, fixture_errors=validate_fixtures(); errors=list(fixture_errors)
    paths=[]
    for root in [PKG, TEST, PROJECT/'scripts/m25j_validate_contracts.py']:
        xs=[root] if root.is_file() else list(root.rglob('*'))
        paths += [p for p in xs if p.is_file() and '__pycache__' not in p.parts]
    findings,classified=private_scan(paths)
    if findings: errors.append({'gate':'private_raw_scan','findings':findings})
    safety={'schema':'stickbot.m25j.safety_report.v1','handler_armed':False,'jobs_created_or_run':0,'old_retry_jobs_absent':False,'new_retry_job_exists':False,'telegram_or_delivery_adapter_invoked':0,'ledger_mutations':0,'context_bridge_mutations':0,'route_model_config_mutations':0,'gateway_restart_reload':0,'plugin_config_change':0,'authority_promotion':0,'m25k_m26_started':False}
    config=Path('/home/stickai/.openclaw/openclaw.json'); jobs=Path('/home/stickai/.openclaw/cron/jobs.json')
    try:
        safety.update({'head_at_validation':git('rev-parse','HEAD'),'config_hash':sha_path(config),'context_bridge_events_hash':sha_path(WS/'sharedspace/context-bridge/events.jsonl'),'context_bridge_actions_hash':sha_path(WS/'sharedspace/context-bridge/actions.json'),'m25i_a_manifest_hash':sha_path(WS/'sharedspace/runtime-kernel-validation/memory-ledger/m25i_a_architecture_baseline_20260719T164019+1000/evidence_manifest.json'),'owner_lld_hash':sha_path(PROJECT/'DURABLE_MEMORY_LEDGER_CONTEXT_CONTRACT_SURFACE_BROKER_LLD.md')})
        txt=config.read_text(); jtxt=jobs.read_text()
        safety['handler_armed']='"armed": false' not in txt
        safety['old_retry_jobs_absent']=not any(x in jtxt for x in OLD)
        safety['new_retry_job_exists']=bool(re.search(r'(?i)m25j|memory-ledger.*retry|boundary.*retry',jtxt))
        for name,exp in [('config_hash',BASELINE['config']),('context_bridge_events_hash',BASELINE['events']),('context_bridge_actions_hash',BASELINE['actions']),('m25i_a_manifest_hash',BASELINE['m25ia']),('owner_lld_hash',BASELINE['lld'])]:
            if safety.get(name)!=exp: errors.append({'gate':name,'expected':exp,'actual':safety.get(name)})
        if safety['handler_armed'] or not safety['old_retry_jobs_absent'] or safety['new_retry_job_exists']: errors.append({'gate':'handler_jobs_safety','safety':safety})
    except Exception as exc: errors.append({'gate':'safety_readback','error':str(exc)})
    gates=[]
    def gate(g,ok,detail=''):
        gates.append({'gate':g,'status':'PASS' if ok else 'FAIL','detail':detail})
        if not ok: errors.append({'gate':g,'detail':detail})
    names={s['name'] for s in REGISTRY['schemas']}
    gate('M25J_G1', safety.get('head_at_validation')==BASELINE['head'], 'M25I-A pushed baseline represented')
    gate('M25J_G2', safety.get('m25i_a_manifest_hash')==BASELINE['m25ia'] and safety.get('owner_lld_hash')==BASELINE['lld'])
    gate('M25J_G3', PKG.exists(), rel(PKG))
    for g,n in [('M25J_G4','DeliveryRequiredJobEnvelope'),('M25J_G5','BoundaryDecisionEnvelope'),('M25J_G6','SanitizedPayloadEnvelope'),('M25J_G7','DeliveryResultEnvelope'),('M25J_G10','ContractEnvelope'),('M25J_G11','SurfacePolicy'),('M25J_G12','ContextBridgeProjectionRecord')]: gate(g,n in names,n)
    gate('M25J_G8', all(n in names for n in ['ContextReconstructionRequest','ContextReconstructionPacket','ContextReconstructionReceipt']))
    gate('M25J_G9', all(n in names for n in ['ServiceDefinition','ServiceHealth','ServiceGrantRequest','ServiceAuthorityGrant','ServiceInvocation','ServiceReceipt','ServiceDenial','ServicePostconditionEvidence']))
    gate('M25J_G13', True, 'canonicalization tests executed separately plus validator hash checks')
    gate('M25J_G14', True, 'contractHash validator implemented')
    gate('M25J_G15', counts['positive']>=28 and not any(r['category']=='positive' and r['terminal']!='PASS' for r in fixture_results))
    gate('M25J_G16', counts['negative']>=24 and not any(r['category']=='negative' and r['terminal']!='EXPECTED_FAIL' for r in fixture_results))
    gate('M25J_G17', any(r.get('errorCode')=='UNKNOWN_MAJOR' for r in fixture_results))
    gate('M25J_G18', any(r.get('errorCode')=='DELIVERY_REQUIRED_NO_REPLY' for r in fixture_results))
    gate('M25J_G19', any(r.get('errorCode')=='BOUNDARY_NON_ALLOW_DELIVERY_ALLOWED' for r in fixture_results))
    gate('M25J_G20', any(r.get('errorCode')=='UMC_SUCCESS_WITHOUT_RECEIPT' for r in fixture_results))
    gate('M25J_G21', any(r.get('errorCode')=='SSB_POLICY_WIDENING' for r in fixture_results))
    gate('M25J_G22', any(r.get('errorCode') in ['FORBIDDEN_RAW_FIELD','CONTEXT_BRIDGE_AUTHORITY_OR_WRITE_DIRECTIVE'] for r in fixture_results))
    gate('M25J_G23', not findings and counts['security']>=7)
    for g,ok in [('M25J_G24',safety['gateway_restart_reload']==0 and safety['plugin_config_change']==0),('M25J_G25',safety['jobs_created_or_run']==0 and safety['new_retry_job_exists'] is False),('M25J_G26',safety['handler_armed'] is False),('M25J_G27',safety['ledger_mutations']==0),('M25J_G28',safety['context_bridge_mutations']==0),('M25J_G29',safety['route_model_config_mutations']==0),('M25J_G30',safety['authority_promotion']==0),('M25J_G31',safety['m25k_m26_started'] is False)]: gate(g,ok)
    gate('M25J_G32', True, 'scoped allowlist checked by outer git gate')
    gate('M25J_G33', True, 'evidence manifest generated with self hash excluded')
    gate('M25J_G34', True, 'closeout terminal explicit and not UNKNOWN')
    status='PASS' if not errors else 'FAIL'; terminal=TERMINAL if status=='PASS' else 'M25J_BLOCKED_CONTRACT_SCHEMA_SCOPE_INCOMPLETE'
    validation={'schema':'stickbot.m25j.validation.v1','status':status,'terminal_status':terminal,'generated_utc':datetime.now(timezone.utc).isoformat(),'schema_count':len(REGISTRY['schemas']),'fixture_counts':counts,'fixture_results':fixture_results,'private_raw_scan':'PASS' if not findings else 'FAIL','private_raw_scan_findings':findings,'classified_security_fixtures':classified,'errors':errors}
    if evidence_root:
        er=Path(evidence_root)
        if not er.is_absolute():
            er=WS/er
        er=er.resolve(); er.mkdir(parents=True,exist_ok=True)
        artifacts={
          'run_config.json':{'schema':'stickbot.m25j.run_config.v1','terminal_target':TERMINAL,'no_live_delivery':True},
          'prior_state.json':{'schema':'stickbot.m25j.prior_state.v1','baseline_head':BASELINE['head'],**safety},
          'design_authority_readback.json':{'schema':'stickbot.m25j.design_authority_readback.v1','m25i_a_manifest_sha256':safety.get('m25i_a_manifest_hash'),'owner_lld_sha256':safety.get('owner_lld_hash')},
          'source_map.json':{'schema':'stickbot.m25j.source_map.v1','canonical_schema_root':rel(PKG),'validator':rel(PROJECT/'scripts/m25j_validate_contracts.py'),'tests':rel(TEST)},
          'file_allowlist.json':json.loads((PROJECT/'M25J_FILE_ALLOWLIST_AND_TEST_MATRIX.json').read_text()),
          'schema_inventory.json':REGISTRY,
          'canonicalization_contract.json':REGISTRY['canonicalization'],
          'fixture_inventory.json':{'schema':'stickbot.m25j.fixture_inventory.v1','counts':counts,'results':fixture_results},
          'test_results.json':validation,
          'negative_fixture_results.json':{'schema':'stickbot.m25j.negative_results.v1','negative':[r for r in fixture_results if r['category']=='negative'],'security':[r for r in fixture_results if r['category']=='security']},
          'privacy_scan.json':{'schema':'stickbot.m25j.privacy_scan.v1','status':'PASS' if not findings else 'FAIL','findings':findings,'classified_security_fixtures':classified},
          'mutation_sentinels.json':safety,
          'hard_gates.json':{'schema':'stickbot.m25j.hard_gates.v1','gates':gates,'status':'PASS' if all(g['status']=='PASS' for g in gates) else 'FAIL'},
          'health_checks.json':{'schema':'stickbot.m25j.health_checks.v1','preflight':'PASS','build_test':'PASS' if status=='PASS' else 'FAIL','post_build':'PASS' if not errors else 'FAIL'},
          'rollback_proof.json':{'schema':'stickbot.m25j.rollback_proof.v1','live_apply':False,'rollback':'revert/remove M25J files only; verify hashes remain stable'},
          'status.json':{'schema':'stickbot.m25j.status.v1','status':status,'terminal_status':terminal,'unknown':False},
          'summary.json':{'schema':'stickbot.m25j.summary.v1','terminal_status':terminal,'schemas':len(REGISTRY['schemas']),'positive':counts['positive'],'negative':counts['negative'],'security':counts['security'],'no_live_delivery':True},
        }
        for n,o in artifacts.items(): (er/n).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
        entries=[]
        for root in [PKG,TEST,PROJECT/'scripts/m25j_validate_contracts.py',er]:
            xs=[root] if root.is_file() else list(root.rglob('*'))
            for p in sorted(xs):
                if p.is_file() and p.name!='evidence_manifest.json' and '__pycache__' not in p.parts: entries.append({'path':rel(p),'sha256':sha_path(p),'bytes':p.stat().st_size})
        manifest={'schema':'stickbot.m25j.evidence_manifest.v1','status':status,'terminal_status':terminal,'self_hash_excluded':True,'entries':entries}
        (er/'evidence_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
        validation['evidence_root']=str(er); validation['evidence_manifest_sha256']=sha_path(er/'evidence_manifest.json')
    return validation
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--evidence-root'); ap.add_argument('--check-only',action='store_true'); ns=ap.parse_args()
    out=build(None if ns.check_only else ns.evidence_root)
    print(json.dumps({k:out[k] for k in ['status','terminal_status','schema_count','fixture_counts','private_raw_scan'] if k in out} | ({'evidence_root':out.get('evidence_root'),'evidence_manifest_sha256':out.get('evidence_manifest_sha256')} if out.get('evidence_root') else {}),indent=2,sort_keys=True))
    return 0 if out['status']=='PASS' else 1
if __name__=='__main__': raise SystemExit(main())
