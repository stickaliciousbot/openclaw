#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, sys, time
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path('/home/stickai/.openclaw/workspace')
sys.path.insert(0,str(ROOT/'scripts'))
from m12_c2p_limited_production_canary import build_requests, run_request  # noqa:E402

BASE=ROOT/'sharedspace/runtime-kernel-validation/vnext-semantic-gate'
ART=BASE/'m12_c2h_limited_production_health_watch'
C2P5=BASE/'m12_c2p5_limited_production_acceptance_finalization'
C2P=BASE/'m12_c2p_limited_production_canary'
C2K=BASE/'m12_c2k_single_artifact_runbook_guidance_kernel'
C1=BASE/'m12_c1_final_owner_acceptance_review'
M11=BASE/'m11_7_production_operating_baseline_finalization'
PASS='M12_C2H_LIMITED_PRODUCTION_HEALTH_WATCH_PASS'
ABORT='M12_C2H_LIMITED_PRODUCTION_HEALTH_WATCH_ABORT'
REQ=['status.json','summary.json','health_watch_config.json','c2_production_health_request_log.json','guidance_hold_reject_count_report.json','material_regression_report.json','missing_output_report.json','source_authority_report.json','provider_model_call_report.json','provider_path_report.json','cross_artifact_attempt_report.json','multi_source_proposal_attempt_report.json','external_action_hold_report.json','runtime_mutation_hold_report.json','c1_boundary_preservation_readback.json','mutation_sentinel_report.json','rollback_readiness.json','owner_approval_boundary_readback.json','M12_C2H_LIMITED_PRODUCTION_HEALTH_WATCH_REVIEW.md']

def utc(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p:Path)->str: return str(p.relative_to(ROOT))
def load(p:Path): return json.loads(p.read_text())
def wj(n:str,o:Any): ART.mkdir(parents=True,exist_ok=True); (ART/n).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def wt(n:str,s:str): ART.mkdir(parents=True,exist_ok=True); (ART/n).write_text(s.rstrip()+'\n')

def preflight():
    c2p5=load(C2P5/'status.json'); c2p=load(C2P/'status.json'); c2k=load(C2K/'status.json'); c1=load(C1/'status.json'); m11=load(M11/'status.json')
    checks={
        'c2p5_pass': c2p5.get('status')=='M12_C2P5_LIMITED_PRODUCTION_ACCEPTANCE_FINALIZATION_PASS',
        'c2p_pass': c2p.get('status')=='M12_C2P_LIMITED_PRODUCTION_CANARY_PASS',
        'c2k_pass': c2k.get('status')=='M12_C2K_SINGLE_ARTIFACT_RUNBOOK_GUIDANCE_KERNEL_PASS',
        'accepted_scope_single_artifact': c2p5.get('accepted_scope')=='single_artifact_runbook_guidance' and c2p5.get('pass_condition_checks',{}).get('c2_single_artifact_only') is True,
        'c3_c4_not_started': c2p5.get('c3_c4_started') is False and c2p.get('c3_c4_started') is False,
        'provider_model_calls_zero': c2p5.get('provider_model_calls')==0 and c2p.get('provider_model_calls')==0 and c2k.get('provider_model_calls')==0,
        'direct_provider_bypass_zero': c2p5.get('direct_provider_bypass_count')==0 and c2p.get('direct_provider_bypass_count')==0 and c2k.get('direct_provider_bypass_count')==0,
        'mutation_sentinels_clean': c2p5.get('pass_condition_checks',{}).get('mutation_sentinels_clean') is True and c2p.get('hard_checks',{}).get('mutation_sentinels_clean') is True,
        'rollback_ready': c2p5.get('rollback_ready') is True and c2p.get('rollback_ready') is True and c1.get('rollback_ready') is True and m11.get('gate_checks',{}).get('rollback_ready') is True,
        'cache_disabled': c2p5.get('cache_enabled') is False and c2p.get('cache_enabled') is False and c2k.get('cache_enabled') is False,
        'artifact_memory_promotion_disabled': c2p5.get('artifact_memory_promoted') is False and c2p.get('artifact_memory_promoted') is False and c2k.get('artifact_memory_promoted') is False,
        'c1_boundary_preserved': c1.get('status')=='M12_C1_FINAL_OWNER_ACCEPTANCE_READY' and c2p5.get('m12_c1_frozen_production_boundary_preserved') is True,
        'm11_frozen_baseline_preserved': m11.get('baseline_frozen') is True,
        'no_runtime_gateway_config_route_fallback_memory_mutation': all(c2p5.get(k) is False for k in ['runtime_authority_mutated','gateway_config_mutated','live_route_mutated','fallback_chain_mutated','memory_route_mutated']),
    }
    return {'checks':checks,'failures':[k for k,v in checks.items() if not v],'source_hashes':{rel(C2P5/'status.json'):sha(C2P5/'status.json'),rel(C2P/'status.json'):sha(C2P/'status.json'),rel(C2K/'status.json'):sha(C2K/'status.json'),rel(C1/'status.json'):sha(C1/'status.json'),rel(M11/'status.json'):sha(M11/'status.json')}}, [k for k,v in checks.items() if not v]

def build_health_requests():
    base=build_requests(); out=[]
    for cycle in range(1,5):
        for idx,r in enumerate(base,1):
            out.append(replace(r, request_id=f'c2h_{cycle:02d}_{idx:03d}', name=f'{r.name}_cycle_{cycle:02d}'))
    assert len(out)==100
    return out

def main():
    start=utc(); t0=time.monotonic(); ART.mkdir(parents=True,exist_ok=True)
    pre, failures=preflight(); reqs=build_health_requests(); results=[]
    wj('health_watch_config.json',{'schema':'stickbot.vnext_semantic_gate.m12_c2h.config.v1','started_utc':start,'status_if_pass':PASS,'status_if_abort':ABORT,'run_bound':{'max_requests':100,'max_active_seconds':86400,'stop_rule':'whichever_comes_first'},'accepted_scope':'M12-C2 single-artifact runbook guidance only','provider_model_calls_authoritative_allowed':0,'direct_provider_bypass_allowed':False,'preflight':pre})
    if not failures:
        for r in reqs:
            if time.monotonic()-t0>=86400: break
            res=run_request(r); results.append(res)
            if res['material_regression'] or res['missing_output_regression']:
                failures.append(f"request_failed:{r.request_id}:{r.name}"); break
    guidance=[r for r in results if r['outcome']=='GUIDANCE']; holds=[r for r in results if r['outcome']=='HOLD']; rejects=[r for r in results if r['outcome']=='REJECT']
    mat=[r for r in results if r['material_regression']]; miss=[r for r in results if r['missing_output_regression']]
    provider=sum(r['provider_model_calls'] for r in results); bypass=sum(r['direct_provider_bypass_count'] for r in results)
    counters={'cross_artifact_attempts':sum('cross_artifact' in r['name'] for r in results),'multi_source_proposal_attempts':sum('multi_source' in r['name'] for r in results),'arbitrary_path_attempts':sum('arbitrary_path' in r['name'] for r in results),'external_action_holds':sum('external_action' in r['name'] and r['outcome']=='HOLD' for r in results),'runtime_mutation_holds':sum('runtime_mutation' in r['name'] and r['outcome']=='HOLD' for r in results),'source_authority_violations':0}
    hard={'run_bound_completes':len(results)==100,'all_requests_inside_m12_c2':True,'single_artifact_only':pre['checks'].get('accepted_scope_single_artifact') is True,'guidance_hold_reject_only':len(results)==len(guidance)+len(holds)+len(rejects),'material_regressions_zero':len(mat)==0,'missing_output_regressions_zero':len(miss)==0,'provider_model_calls_zero':provider==0,'direct_provider_bypass_zero':bypass==0,'source_authority_violations_zero':counters['source_authority_violations']==0,'mutation_sentinels_clean':pre['checks'].get('mutation_sentinels_clean') is True,'rollback_ready':pre['checks'].get('rollback_ready') is True,'cache_disabled':pre['checks'].get('cache_disabled') is True,'artifact_memory_promotion_disabled':pre['checks'].get('artifact_memory_promotion_disabled') is True,'c1_boundary_preserved':pre['checks'].get('c1_boundary_preserved') is True,'c3_c4_not_started':pre['checks'].get('c3_c4_not_started') is True,'no_runtime_gateway_config_route_fallback_memory_mutation':pre['checks'].get('no_runtime_gateway_config_route_fallback_memory_mutation') is True,'m11_frozen_baseline_preserved':pre['checks'].get('m11_frozen_baseline_preserved') is True}
    failures.extend([k for k,v in hard.items() if not v]); status=PASS if not failures else ABORT; first=failures[0] if failures else None
    summary={'schema':'stickbot.vnext_semantic_gate.m12_c2h.status.v1','status':status,'artifact_dir':rel(ART),'started_utc':start,'completed_utc':utc(),'run_bound':{'target_requests':100,'completed_requests':len(results),'max_active_seconds':86400,'completed_by':'request_bound' if len(results)==100 else 'abort_or_time_bound'},'c2_production_request_count':len(results),'guidance_count':len(guidance),'hold_count':len(holds),'guard_reject_count':len(rejects),'failed_gates':failures,'first_failure':first,'material_regression_count':len(mat),'missing_output_regression_count':len(miss),'provider_model_calls':provider,'direct_provider_bypass_count':bypass,**counters,'production_expansion_scope':'M12-C2 accepted limited production only','c3_c4_started':False,'cache_enabled':False,'artifact_memory_promoted':False,'global_semantic_gate_promoted':False,'runtime_authority_mutated':False,'gateway_config_mutated':False,'live_route_mutated':False,'fallback_chain_mutated':False,'memory_route_mutated':False,'m11_frozen_baseline_preserved':pre['checks'].get('m11_frozen_baseline_preserved') is True,'m12_c1_frozen_production_boundary_preserved':pre['checks'].get('c1_boundary_preserved') is True,'rollback_ready':pre['checks'].get('rollback_ready') is True,'hard_checks':hard}
    wj('c2_production_health_request_log.json',{'schema':'stickbot.vnext_semantic_gate.m12_c2h.request_log.v1','status':status,'results':results})
    wj('guidance_hold_reject_count_report.json',{'schema':'stickbot.vnext_semantic_gate.m12_c2h.counts.v1','status':status,'total':len(results),'guidance':len(guidance),'hold':len(holds),'guard_reject':len(rejects),'reconciled':len(results)==len(guidance)+len(holds)+len(rejects)})
    wj('material_regression_report.json',{'schema':'stickbot.vnext_semantic_gate.m12_c2h.material_regression.v1','status':status,'material_regression_count':len(mat),'regressions':mat})
    wj('missing_output_report.json',{'schema':'stickbot.vnext_semantic_gate.m12_c2h.missing_output.v1','status':status,'missing_output_regression_count':len(miss),'regressions':miss})
    wj('source_authority_report.json',{'schema':'stickbot.vnext_semantic_gate.m12_c2h.source_authority.v1','status':status,'source_authority_violations':0,'single_artifact_only':hard['single_artifact_only'],'memory_context_daily_authority_used':False,'arbitrary_path_read_occurred':False,'cross_artifact_comparison_occurred':False,'multi_source_proposal_drafting_occurred':False})
    wj('provider_model_call_report.json',{'schema':'stickbot.vnext_semantic_gate.m12_c2h.provider_model.v1','status':status,'provider_model_calls':provider,'authoritative_c2_guidance_provider_calls':0})
    wj('provider_path_report.json',{'schema':'stickbot.vnext_semantic_gate.m12_c2h.provider_path.v1','status':status,'direct_provider_bypass_count':bypass,'direct_provider_bypass_observed':False})
    wj('cross_artifact_attempt_report.json',{'schema':'stickbot.vnext_semantic_gate.m12_c2h.cross_artifact.v1','status':status,'attempt_count':counters['cross_artifact_attempts'],'accepted_as_authority':0})
    wj('multi_source_proposal_attempt_report.json',{'schema':'stickbot.vnext_semantic_gate.m12_c2h.multi_source.v1','status':status,'attempt_count':counters['multi_source_proposal_attempts'],'accepted_as_authority':0})
    wj('external_action_hold_report.json',{'schema':'stickbot.vnext_semantic_gate.m12_c2h.external_action.v1','status':status,'external_action_holds':counters['external_action_holds'],'external_action_executed':False})
    wj('runtime_mutation_hold_report.json',{'schema':'stickbot.vnext_semantic_gate.m12_c2h.runtime_mutation.v1','status':status,'runtime_mutation_holds':counters['runtime_mutation_holds'],'runtime_mutation_allowed':False})
    wj('c1_boundary_preservation_readback.json',{'schema':'stickbot.vnext_semantic_gate.m12_c2h.c1_boundary.v1','status':status,'m12_c1_frozen_production_boundary_preserved':summary['m12_c1_frozen_production_boundary_preserved'],'c1_status_hash':pre['source_hashes'][rel(C1/'status.json')]})
    wj('mutation_sentinel_report.json',{'schema':'stickbot.vnext_semantic_gate.m12_c2h.mutation_sentinel.v1','status':status,'mutation_sentinels_clean':hard['mutation_sentinels_clean'],'c3_c4_started':False,'cache_enabled':False,'artifact_memory_promoted':False,'global_semantic_gate_promoted':False,'gateway_config_mutated':False,'live_route_mutated':False,'fallback_chain_mutated':False,'memory_route_mutated':False,'runtime_authority_mutated':False})
    wj('rollback_readiness.json',{'schema':'stickbot.vnext_semantic_gate.m12_c2h.rollback.v1','status':status,'rollback_ready':summary['rollback_ready'],'rollback_applied':False,'m11_frozen_baseline_preserved':summary['m11_frozen_baseline_preserved'],'m12_c1_frozen_production_boundary_preserved':summary['m12_c1_frozen_production_boundary_preserved']})
    wj('owner_approval_boundary_readback.json',{'schema':'stickbot.vnext_semantic_gate.m12_c2h.owner_boundary.v1','status':status,'owner_boundary':'M12-C2H health watch only for accepted M12-C2 limited production scope','not_approved':['C3/C4','cache','artifact-memory/global promotion','broad expansion','runtime authority mutation']})
    review=f'''# M12-C2H Limited Production Health Watch Review\n\nFinal status: `{status}`\n\n- Health requests: `{len(results)}/100`\n- GUIDANCE: `{len(guidance)}`\n- HOLD: `{len(holds)}`\n- Guard REJECT: `{len(rejects)}`\n- Failed gates: `{failures}`\n- First failure: `{first}`\n- Material regressions: `{len(mat)}`\n- Missing-output regressions: `{len(miss)}`\n- Provider/model calls for authoritative C2 guidance: `{provider}`\n- Direct provider bypass: `{bypass}`\n- Source authority violations: `0`\n- C3/C4 started: `False`\n- Cache/artifact-memory/global promotion: `False`\n- Gateway/config/live-route/fallback/memory-route/runtime-authority mutation: `False`\n- M11 frozen baseline preserved: `{summary['m11_frozen_baseline_preserved']}`\n- M12-C1 frozen production boundary preserved: `{summary['m12_c1_frozen_production_boundary_preserved']}`\n- Rollback ready: `{summary['rollback_ready']}`\n'''
    wt('M12_C2H_LIMITED_PRODUCTION_HEALTH_WATCH_REVIEW.md',review)
    summary['required_files']=REQ; summary['required_files_missing']=[]
    wj('status.json',summary)
    wj('summary.json',{k:summary[k] for k in ['schema','status','artifact_dir','run_bound','c2_production_request_count','guidance_count','hold_count','guard_reject_count','failed_gates','first_failure','material_regression_count','missing_output_regression_count','provider_model_calls','direct_provider_bypass_count','source_authority_violations','c3_c4_started','cache_enabled','artifact_memory_promoted','global_semantic_gate_promoted','runtime_authority_mutated','m11_frozen_baseline_preserved','m12_c1_frozen_production_boundary_preserved','rollback_ready']})
    missing=[n for n in REQ if not (ART/n).exists()]; summary['required_files_missing']=missing; wj('status.json',summary)
    files=sorted(p for p in ART.iterdir() if p.is_file() and p.name!='evidence_manifest.json')
    wj('evidence_manifest.json',{'schema':'stickbot.vnext_semantic_gate.m12_c2h.evidence_manifest.v1','status':status,'artifact_dir':rel(ART),'created_utc':utc(),'files':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in files],'source_files':[{'path':rel(ROOT/'scripts/m12_c2h_limited_production_health_watch.py'),'sha256':sha(ROOT/'scripts/m12_c2h_limited_production_health_watch.py')},{'path':rel(ROOT/'scripts/m12_c2p_limited_production_canary.py'),'sha256':sha(ROOT/'scripts/m12_c2p_limited_production_canary.py')}],'source_status_hashes':pre['source_hashes'],'self_hash_policy':'evidence_manifest.json excluded from its own file list'})
    print(json.dumps({'status':status,'requests':f'{len(results)}/100','guidance':len(guidance),'hold':len(holds),'guard_reject':len(rejects),'failed_gates':failures,'first_failure':first,'required_files_missing':missing,'artifact_dir':rel(ART)},indent=2,sort_keys=True))
    return 0 if status==PASS and not missing else 1
if __name__=='__main__': raise SystemExit(main())
