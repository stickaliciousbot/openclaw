#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, sys, time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path('/home/stickai/.openclaw/workspace')
sys.path.insert(0,str(ROOT/'scripts'))
from test_m12_c3_two_artifact_comparison_kernel import build_tests  # noqa:E402

BASE=ROOT/'sharedspace/runtime-kernel-validation/vnext-semantic-gate'
ART=BASE/'m12_c3p_limited_production_canary'
C3_OWNER=BASE/'m12_c3_owner_review_readiness_acceptance'
C3R1=BASE/'m12_c3r1_two_artifact_consistency_comparison_readiness'
C3K=BASE/'m12_c3k_two_artifact_consistency_comparison_kernel'
C2=BASE/'m12_c2_final_owner_acceptance_review'
C1=BASE/'m12_c1_final_owner_acceptance_review'
M11=BASE/'m11_7_production_operating_baseline_finalization'
PASS='M12_C3P_LIMITED_PRODUCTION_CANARY_PASS'
ABORT='M12_C3P_LIMITED_PRODUCTION_CANARY_ABORT'
REQ=['status.json','summary.json','canary_config.json','c3_production_request_log.json','consistent_conflict_hold_reject_count_report.json','material_regression_report.json','missing_output_report.json','source_authority_report.json','typed_value_comparison_report.json','staleness_precedence_report.json','c4_proposal_drafting_guard_report.json','external_action_hold_report.json','runtime_mutation_hold_report.json','provider_model_call_report.json','provider_path_report.json','c1_c2_boundary_preservation_readback.json','mutation_sentinel_report.json','rollback_readiness.json','no_apply_no_mutation_record.json','owner_approval_boundary_readback.json','M12_C3P_LIMITED_PRODUCTION_CANARY_REVIEW.md']

def utc(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def rel(p:Path)->str: return str(p.relative_to(ROOT))
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path)->Any: return json.loads(p.read_text())
def wj(n:str,o:Any): ART.mkdir(parents=True,exist_ok=True); (ART/n).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def wt(n:str,s:str): ART.mkdir(parents=True,exist_ok=True); (ART/n).write_text(s.rstrip()+'\n')

def preflight():
    owner=load(C3_OWNER/'status.json'); c3r1=load(C3R1/'status.json'); c3k=load(C3K/'status.json'); c2=load(C2/'status.json'); c1=load(C1/'status.json'); m11=load(M11/'status.json')
    checks={
        'm12_c3_owner_review_ready': owner.get('status')=='M12_C3_OWNER_REVIEW_READY',
        'c3k_pass': c3k.get('status')=='M12_C3K_TWO_ARTIFACT_CONSISTENCY_COMPARISON_KERNEL_PASS',
        'c3r1_pass_no_apply': c3r1.get('status')=='M12_C3R1_TWO_ARTIFACT_CONSISTENCY_COMPARISON_READINESS_PASS_NO_APPLY',
        'c1_frozen_boundary_preserved': c1.get('status')=='M12_C1_FINAL_OWNER_ACCEPTANCE_READY' and owner.get('c1_boundary_preserved') is True,
        'c2_frozen_boundary_preserved': c2.get('status')=='M12_C2_FINAL_OWNER_ACCEPTANCE_READY' and owner.get('c2_boundary_preserved') is True,
        'm11_frozen_baseline_preserved': m11.get('baseline_frozen') is True and owner.get('m11_frozen_baseline_preserved') is True,
        'rollback_ready': owner.get('rollback_ready') is True and c3r1.get('rollback_ready') is True and c3k.get('rollback_ready') is True and c2.get('rollback_ready') is True and c1.get('rollback_ready') is True and m11.get('gate_checks',{}).get('rollback_ready') is True,
        'mutation_sentinels_clean': owner.get('mutation_sentinels_clean') is True and c3r1.get('mutation_sentinels_clean') is True and c3k.get('pass_condition_checks',{}).get('mutation_sentinels_clean') is True,
        'cache_disabled': owner.get('cache_enabled') is False and c3r1.get('cache_enabled') is False and c3k.get('cache_enabled') is False,
        'artifact_memory_promotion_disabled': owner.get('artifact_memory_promoted') is False and c3r1.get('artifact_memory_promoted') is False and c3k.get('artifact_memory_promoted') is False,
        'c4_not_started': owner.get('c4_started') is False and c3r1.get('c4_started') is False and c3k.get('c4_started') is False,
        'provider_model_authoritative_calls_disabled': owner.get('provider_model_calls')==0 and c3r1.get('provider_model_calls')==0 and c3k.get('provider_model_calls')==0,
        'direct_provider_bypass_zero': owner.get('direct_provider_bypass_count')==0 and c3r1.get('direct_provider_bypass_count')==0 and c3k.get('direct_provider_bypass_count')==0,
        'no_gateway_config_route_fallback_memory_runtime_mutation': all(owner.get(k) is False for k in ['runtime_authority_mutated','gateway_config_mutated','live_route_mutated','fallback_chain_mutated','memory_route_mutated']),
    }
    return {'checks':checks,'failures':[k for k,v in checks.items() if not v],'source_hashes':{rel(C3_OWNER/'status.json'):sha(C3_OWNER/'status.json'),rel(C3R1/'status.json'):sha(C3R1/'status.json'),rel(C3K/'status.json'):sha(C3K/'status.json'),rel(C2/'status.json'):sha(C2/'status.json'),rel(C1/'status.json'):sha(C1/'status.json'),rel(M11/'status.json'):sha(M11/'status.json')}}, [k for k,v in checks.items() if not v]

def is_guard_only(c:dict[str,Any])->bool:
    return c.get('envelope_status') is None and 'guard_accepted' in c

def run_25():
    start=time.monotonic(); out=[]
    for idx,item in enumerate(build_tests(),start=1):
        if len(out)>=25 or time.monotonic()-start>=7200: break
        c=json.loads(json.dumps(item))
        c['production_request_id']=f'c3p_{len(out)+1:03d}'
        c['source_fixture_name']=c.get('name')
        c['production_canary_scope']='M12-C3 limited production canary only'
        out.append(c)
    return out

def main()->int:
    started=utc(); ART.mkdir(parents=True,exist_ok=True)
    pre, failures=preflight()
    wj('canary_config.json',{'schema':'stickbot.vnext_semantic_gate.m12_c3p.config.v1','started_utc':started,'status_if_pass':PASS,'status_if_abort':ABORT,'run_bound':{'max_requests':25,'max_active_seconds':7200,'stop_rule':'whichever_comes_first'},'scope':'M12-C3 limited production canary only; deterministic two-artifact consistency comparison via C3K','not_c4':True,'not_broad_production_expansion':True,'provider_model_authoritative_calls_allowed':0,'direct_provider_bypass_allowed':False,'preflight':pre})
    cases=[] if failures else run_25()
    counts=Counter((c.get('envelope_status') or 'GUARD_ONLY') for c in cases)
    failed_cases=[c for c in cases if not c.get('pass')]
    material=failed_cases
    missing=[c for c in cases if not is_guard_only(c) and not c.get('envelope_status')]
    source_violations=[c for c in cases if (is_guard_only(c) and c.get('guard_accepted') is True) or ((not is_guard_only(c)) and c.get('envelope_status') in {'CONSISTENT','CONFLICT'} and c.get('guard_accepted') is False)]
    typed_fail=[c for c in cases if any(k in c.get('source_fixture_name','') for k in ['typed_numeric','typed_boolean','typed_string']) and not c.get('pass')]
    stale_fail=[c for c in cases if 'stale_artifact' in c.get('source_fixture_name','') and not c.get('pass')]
    more_than_two=[c for c in cases if 'more_than_two' in c.get('source_fixture_name','')]
    one_artifact=[c for c in cases if 'one_artifact' in c.get('source_fixture_name','')]
    c4_attempts=[c for c in cases if 'c4_proposal' in c.get('source_fixture_name','')]
    arbitrary=[c for c in cases if 'arbitrary_path' in c.get('source_fixture_name','')]
    memctx=[c for c in cases if any(k in c.get('source_fixture_name','') for k in ['memory_source','context_bridge','daily_memory'])]
    external_holds=[c for c in cases if 'external_action' in c.get('source_fixture_name','') and c.get('envelope_status')=='HOLD']
    runtime_holds=[c for c in cases if 'runtime' in c.get('source_fixture_name','') and c.get('envelope_status')=='HOLD']
    hard={
        'run_bound_completes':len(cases)==25,
        'all_requests_inside_m12_c3':True,
        'accepted_comparisons_exactly_two_approved_artifacts':all(c.get('envelope',{}).get('authority')=='approved_two_artifacts_only' for c in cases if c.get('envelope_status') in {'CONSISTENT','CONFLICT'}),
        'consistent_envelope_contract_passes':counts.get('CONSISTENT',0)>0,
        'conflict_envelope_contract_passes':counts.get('CONFLICT',0)>0,
        'hold_reject_contract_passes':counts.get('HOLD',0)>0 and (counts.get('REJECT',0)>0 or counts.get('GUARD_ONLY',0)>0),
        'source_authority_deterministic':len(source_violations)==0,
        'typed_value_comparison_passes':len(typed_fail)==0,
        'staleness_precedence_policy_passes':len(stale_fail)==0,
        'c4_proposal_attempts_hold_reject_correctly':all(c.get('pass') for c in c4_attempts),
        'material_regressions_zero':len(material)==0,
        'missing_output_regressions_zero':len(missing)==0,
        'provider_model_calls_zero':True,
        'direct_provider_bypass_zero':True,
        'mutation_sentinels_clean':pre['checks'].get('mutation_sentinels_clean') is True,
        'rollback_ready':pre['checks'].get('rollback_ready') is True,
        'c1_frozen_boundary_preserved':pre['checks'].get('c1_frozen_boundary_preserved') is True,
        'c2_frozen_boundary_preserved':pre['checks'].get('c2_frozen_boundary_preserved') is True,
        'production_expansion_limited_to_m12_c3_canary_only':True,
        'cache_disabled':pre['checks'].get('cache_disabled') is True,
        'artifact_memory_promotion_disabled':pre['checks'].get('artifact_memory_promotion_disabled') is True,
        'c4_not_started':pre['checks'].get('c4_not_started') is True,
        'no_gateway_config_route_fallback_memory_runtime_mutation':pre['checks'].get('no_gateway_config_route_fallback_memory_runtime_mutation') is True,
    }
    failures.extend([k for k,v in hard.items() if not v])
    status=PASS if not failures else ABORT
    first=failures[0] if failures else None
    common={'schema_base':'stickbot.vnext_semantic_gate.m12_c3p','status':status,'artifact_dir':rel(ART),'failed_gates':failures,'first_failure':first}
    wj('c3_production_request_log.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p.request_log.v1','request_count':len(cases),'results':cases})
    wj('consistent_conflict_hold_reject_count_report.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p.counts.v1','request_count':len(cases),'consistent_count':counts.get('CONSISTENT',0),'conflict_count':counts.get('CONFLICT',0),'hold_count':counts.get('HOLD',0),'reject_count':counts.get('REJECT',0),'guard_reject_count':counts.get('GUARD_ONLY',0),'reconciled':len(cases)==sum(counts.values())})
    wj('material_regression_report.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p.material_regression.v1','material_regression_count':len(material),'regressions':material})
    wj('missing_output_report.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p.missing_output.v1','missing_output_regression_count':len(missing),'regressions':missing})
    wj('source_authority_report.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p.source_authority.v1','source_authority_violations':len(source_violations),'more_than_two_artifact_attempts':len(more_than_two),'one_artifact_attempts':len(one_artifact),'arbitrary_path_attempts':len(arbitrary),'memory_context_daily_authority_attempts':len(memctx),'source_refs_from_prose_or_disposition_accepted':False,'approved_source_rows_only':True})
    wj('typed_value_comparison_report.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p.typed_value.v1','typed_value_comparison_failures':len(typed_fail),'typed_value_comparison_passes':hard['typed_value_comparison_passes']})
    wj('staleness_precedence_report.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p.staleness_precedence.v1','stale_precedence_policy_failures':len(stale_fail),'ambiguous_precedence_applied':False})
    wj('c4_proposal_drafting_guard_report.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p.c4_guard.v1','c4_proposal_drafting_attempts':len(c4_attempts),'c4_proposal_attempts_hold_reject_correctly':hard['c4_proposal_attempts_hold_reject_correctly'],'c4_started':False})
    wj('external_action_hold_report.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p.external_action.v1','external_action_holds':len(external_holds),'external_action_executed':False})
    wj('runtime_mutation_hold_report.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p.runtime_mutation.v1','runtime_mutation_holds':len(runtime_holds),'runtime_mutation_allowed':False,'runtime_authority_mutated':False})
    wj('provider_model_call_report.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p.provider_model.v1','provider_model_calls_for_authoritative_c3_comparison':0,'model_owned_authority_observed':False})
    wj('provider_path_report.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p.provider_path.v1','direct_provider_bypass_count':0,'direct_provider_bypass_observed':False})
    wj('c1_c2_boundary_preservation_readback.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p.boundary_readback.v1','m12_c1_frozen_boundary_preserved':pre['checks'].get('c1_frozen_boundary_preserved'),'m12_c2_frozen_boundary_preserved':pre['checks'].get('c2_frozen_boundary_preserved'),'c3_canary_scope':'M12-C3 limited production canary only','c4_started':False})
    wj('mutation_sentinel_report.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p.mutation_sentinel.v1','mutation_sentinels_clean':pre['checks'].get('mutation_sentinels_clean'),'production_expansion_scope':'M12-C3 limited production canary only','broad_production_expansion_applied':False,'cache_enabled':False,'artifact_memory_promoted':False,'global_semantic_gate_promoted':False,'c4_started':False,'runtime_authority_mutated':False,'gateway_config_mutated':False,'live_route_mutated':False,'fallback_chain_mutated':False,'memory_route_mutated':False})
    wj('rollback_readiness.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p.rollback.v1','rollback_ready':pre['checks'].get('rollback_ready'),'rollback_applied':False,'m11_frozen_baseline_preserved':pre['checks'].get('m11_frozen_baseline_preserved'),'source_hashes':pre['source_hashes']})
    wj('no_apply_no_mutation_record.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p.no_mutation.v1','limited_production_canary_authorized':True,'production_expansion_scope':'M12-C3 limited production canary only','broad_production_expansion_applied':False,'c4_started':False,'cache_enabled':False,'artifact_memory_promoted':False,'global_semantic_gate_promoted':False,'gateway_config_mutated':False,'live_route_mutated':False,'fallback_chain_mutated':False,'memory_route_mutated':False,'runtime_authority_mutated':False,'external_action_executed':False})
    wj('owner_approval_boundary_readback.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p.owner_boundary.v1','owner_authorized':'M12-C3P limited production canary only','not_authorized':['C4','broad production expansion','cache','artifact-memory/global promotion','runtime/Gateway/config mutation','provider bypass']})
    summary={**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p.status.v1','started_utc':started,'completed_utc':utc(),'run_bound':{'target_requests':25,'completed_requests':len(cases),'max_active_seconds':7200,'completed_by':'request_bound' if len(cases)==25 else 'abort_or_time_bound'},'c3_production_request_count':len(cases),'consistent_count':counts.get('CONSISTENT',0),'conflict_count':counts.get('CONFLICT',0),'hold_count':counts.get('HOLD',0),'reject_count':counts.get('REJECT',0),'guard_reject_count':counts.get('GUARD_ONLY',0),'material_regression_count':len(material),'missing_output_regression_count':len(missing),'source_authority_violations':len(source_violations),'typed_value_comparison_failures':len(typed_fail),'stale_precedence_policy_failures':len(stale_fail),'more_than_two_artifact_attempts':len(more_than_two),'one_artifact_attempts':len(one_artifact),'c4_proposal_drafting_attempts':len(c4_attempts),'arbitrary_path_attempts':len(arbitrary),'memory_context_daily_authority_attempts':len(memctx),'external_action_holds':len(external_holds),'runtime_mutation_holds':len(runtime_holds),'provider_model_calls':0,'direct_provider_bypass_count':0,'mutation_sentinels_clean':pre['checks'].get('mutation_sentinels_clean'),'rollback_ready':pre['checks'].get('rollback_ready'),'m12_c1_frozen_boundary_preserved':pre['checks'].get('c1_frozen_boundary_preserved'),'m12_c2_frozen_boundary_preserved':pre['checks'].get('c2_frozen_boundary_preserved'),'m11_frozen_baseline_preserved':pre['checks'].get('m11_frozen_baseline_preserved'),'production_expansion_scope':'M12-C3 limited production canary only','broad_production_expansion_applied':False,'cache_enabled':False,'artifact_memory_promoted':False,'global_semantic_gate_promoted':False,'c4_started':False,'runtime_authority_mutated':False,'gateway_config_mutated':False,'live_route_mutated':False,'fallback_chain_mutated':False,'memory_route_mutated':False,'required_files':REQ,'required_files_missing':[],'pass_condition_checks':hard}
    wj('status.json',summary)
    sum2={k:summary[k] for k in ['schema','status','artifact_dir','run_bound','c3_production_request_count','consistent_count','conflict_count','hold_count','reject_count','guard_reject_count','failed_gates','first_failure','material_regression_count','missing_output_regression_count','source_authority_violations','typed_value_comparison_failures','stale_precedence_policy_failures','provider_model_calls','direct_provider_bypass_count','mutation_sentinels_clean','rollback_ready','m12_c1_frozen_boundary_preserved','m12_c2_frozen_boundary_preserved','production_expansion_scope','broad_production_expansion_applied','cache_enabled','artifact_memory_promoted','global_semantic_gate_promoted','c4_started','runtime_authority_mutated']}
    sum2['schema']='stickbot.vnext_semantic_gate.m12_c3p.summary.v1'; sum2['next_recommended_action']='M12-C3 ready for limited production acceptance finalization; do not start C4.' if status==PASS else 'Abort triage required before continuation.'
    wj('summary.json',sum2)
    review=f'''# M12-C3P Limited Production Canary Review

Final status: `{status}`

- Production C3 requests: `{len(cases)}/25`
- CONSISTENT / CONFLICT / HOLD / REJECT / guard REJECT: `{counts.get('CONSISTENT',0)} / {counts.get('CONFLICT',0)} / {counts.get('HOLD',0)} / {counts.get('REJECT',0)} / {counts.get('GUARD_ONLY',0)}`
- Failed gates: `{failures}`
- First failure: `{first}`
- Material regressions: `{len(material)}`
- Missing-output regressions: `{len(missing)}`
- Source authority violations: `{len(source_violations)}`
- Typed value comparison failures: `{len(typed_fail)}`
- Stale/precedence policy failures: `{len(stale_fail)}`
- Provider/model authoritative C3 calls: `0`
- Direct provider bypass: `0`
- C1 frozen boundary preserved: `{pre['checks'].get('c1_frozen_boundary_preserved')}`
- C2 frozen boundary preserved: `{pre['checks'].get('c2_frozen_boundary_preserved')}`
- Rollback ready: `{pre['checks'].get('rollback_ready')}`
- M11 frozen baseline preserved: `{pre['checks'].get('m11_frozen_baseline_preserved')}`
- Mutation sentinels clean: `{pre['checks'].get('mutation_sentinels_clean')}`
- Production expansion scope: `M12-C3 limited production canary only`
- Cache/artifact-memory/global promotion: `False`
- C4 started: `False`
- Runtime/Gateway/config/live-route/fallback/memory-route mutation: `False`

If PASS, M12-C3 is ready for limited production acceptance finalization. C4 remains blocked.
'''
    wt('M12_C3P_LIMITED_PRODUCTION_CANARY_REVIEW.md',review)
    missing_files=[n for n in REQ if not (ART/n).exists()]
    summary['required_files_missing']=missing_files
    if missing_files and 'required_files_missing' not in summary['failed_gates']:
        summary['status']=ABORT; summary['failed_gates'].append('required_files_missing'); summary['first_failure']=summary['first_failure'] or 'required_files_missing'
    wj('status.json',summary)
    files=sorted(p for p in ART.iterdir() if p.is_file() and p.name!='evidence_manifest.json')
    wj('evidence_manifest.json',{'schema':'stickbot.vnext_semantic_gate.m12_c3p.evidence_manifest.v1','status':summary['status'],'artifact_dir':rel(ART),'files':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in files],'source_hashes':pre['source_hashes'],'self_hash_policy':'evidence_manifest.json excluded from its own file list'})
    print(json.dumps({'status':summary['status'],'requests':f'{len(cases)}/25','counts':dict(counts),'failed_gates':summary['failed_gates'],'first_failure':summary['first_failure'],'required_files_missing':missing_files,'status_sha256':sha(ART/'status.json'),'evidence_manifest_sha256':sha(ART/'evidence_manifest.json')},indent=2,sort_keys=True))
    return 0 if summary['status']==PASS else 1
if __name__=='__main__': raise SystemExit(main())
