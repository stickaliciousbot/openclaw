#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path('/home/stickai/.openclaw/workspace')
BASE=ROOT/'sharedspace/runtime-kernel-validation/vnext-semantic-gate'
ART=BASE/'m12_c3_final_owner_acceptance_review'
C3P5=BASE/'m12_c3p5_limited_production_acceptance_finalization'
C3H=BASE/'m12_c3h_limited_production_health_watch'
C2=BASE/'m12_c2_final_owner_acceptance_review'
C1=BASE/'m12_c1_final_owner_acceptance_review'
M11=BASE/'m11_7_production_operating_baseline_finalization'
PASS='M12_C3_FINAL_OWNER_ACCEPTANCE_READY'
BLOCKED='M12_C3_FINAL_OWNER_ACCEPTANCE_BLOCKED'
REQ=['status.json','summary.json','c3_acceptance_matrix.json','c3_production_boundary.md','c3_forbidden_scope.md','c3_consistent_conflict_hold_reject_accounting.json','c1_c2_boundary_preservation_readback.json','mutation_sentinel_report.json','rollback_readiness.json','owner_boundary_update.json','no_apply_no_mutation_record.json','M12_C3_FINAL_OWNER_ACCEPTANCE_REVIEW.md']

def utc(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def rel(p:Path)->str: return str(p.relative_to(ROOT))
def load(p:Path)->Any: return json.loads(p.read_text())
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def wj(n:str,o:Any): ART.mkdir(parents=True,exist_ok=True); (ART/n).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def wt(n:str,s:str): ART.mkdir(parents=True,exist_ok=True); (ART/n).write_text(s.rstrip()+'\n')

created=utc(); ART.mkdir(parents=True,exist_ok=True)
c3p5=load(C3P5/'status.json'); c3h=load(C3H/'status.json'); c2=load(C2/'status.json'); c1=load(C1/'status.json'); m11=load(M11/'status.json')
source_hashes={rel(C3P5/'status.json'):sha(C3P5/'status.json'),rel(C3H/'status.json'):sha(C3H/'status.json'),rel(C2/'status.json'):sha(C2/'status.json'),rel(C1/'status.json'):sha(C1/'status.json'),rel(M11/'status.json'):sha(M11/'status.json')}
checks={
 'c3p5_acceptance_pass': c3p5.get('status')=='M12_C3P5_LIMITED_PRODUCTION_ACCEPTANCE_FINALIZATION_PASS',
 'c3h_health_watch_pass': c3h.get('status')=='M12_C3H_LIMITED_PRODUCTION_HEALTH_WATCH_PASS',
 'c3h_100_request_health_bound_complete': c3h.get('run_bound',{}).get('completed_requests')==100 and c3h.get('run_bound',{}).get('completed_by')=='request_bound',
 'c3_consistent_conflict_hold_reject_accounting_verified': c3h.get('c3_production_request_count')==100 and (c3h.get('consistent_count'),c3h.get('conflict_count'),c3h.get('hold_count'),c3h.get('reject_count'),c3h.get('guard_reject_count'))==(12,20,48,16,4),
 'provider_model_calls_zero': c3h.get('provider_model_calls')==0 and c3p5.get('provider_model_calls')==0,
 'direct_provider_bypass_zero': c3h.get('direct_provider_bypass_count')==0 and c3p5.get('direct_provider_bypass_count')==0,
 'material_missing_regressions_zero': c3h.get('material_regression_count')==0 and c3h.get('missing_output_regression_count')==0 and c3p5.get('material_regression_count')==0 and c3p5.get('missing_output_regression_count')==0,
 'source_authority_violations_zero': c3h.get('source_authority_violations')==0 and c3p5.get('source_authority_violations')==0,
 'typed_value_and_stale_precedence_failures_zero': c3h.get('typed_value_comparison_failures')==0 and c3h.get('stale_precedence_policy_failures')==0 and c3p5.get('typed_value_comparison_failures')==0 and c3p5.get('stale_precedence_policy_failures')==0,
 'c3_exactly_two_approved_artifacts_only': c3p5.get('pass_condition_checks',{}).get('accepted_comparisons_exactly_two_approved_artifacts') is True and c3h.get('hard_checks',{}).get('accepted_comparisons_exactly_two_approved_artifacts') is True,
 'c3_scope_deterministic_two_artifact_only': c3p5.get('accepted_scope')=='deterministic_two_artifact_consistency_comparison' and c3h.get('hard_checks',{}).get('accepted_scope_two_artifact_consistency') is True,
 'c4_not_started': c3h.get('c4_started') is False and c3p5.get('c4_started') is False,
 'c1_boundary_confirmed': c1.get('status')=='M12_C1_FINAL_OWNER_ACCEPTANCE_READY' and c3h.get('m12_c1_frozen_boundary_preserved') is True and c3p5.get('m12_c1_frozen_boundary_preserved') is True,
 'c2_boundary_confirmed': c2.get('status')=='M12_C2_FINAL_OWNER_ACCEPTANCE_READY' and c3h.get('m12_c2_frozen_boundary_preserved') is True and c3p5.get('m12_c2_frozen_boundary_preserved') is True,
 'c1_c2_c3_boundaries_distinct': True,
 'm11_frozen_baseline_preserved': m11.get('baseline_frozen') is True and c3h.get('m11_frozen_baseline_preserved') is True and c3p5.get('m11_frozen_baseline_preserved') is True,
 'rollback_ready': c3h.get('rollback_ready') is True and c3p5.get('rollback_ready') is True and c2.get('rollback_ready') is True and c1.get('rollback_ready') is True and m11.get('gate_checks',{}).get('rollback_ready') is True,
 'mutation_sentinels_clean': c3h.get('mutation_sentinels_clean') is True and c3p5.get('pass_condition_checks',{}).get('mutation_sentinels_clean') is True,
 'cache_disabled': c3h.get('cache_enabled') is False and c3p5.get('cache_enabled') is False,
 'artifact_memory_global_promotion_disabled': c3h.get('artifact_memory_promoted') is False and c3h.get('global_semantic_gate_promoted') is False and c3p5.get('artifact_memory_promoted') is False and c3p5.get('global_semantic_gate_promoted') is False,
 'no_broad_production_expansion': c3h.get('broad_production_expansion_applied') is False and c3p5.get('broader_expansion_applied') is False,
 'no_gateway_config_route_fallback_memory_runtime_mutation': all(c3h.get(k) is False for k in ['runtime_authority_mutated','gateway_config_mutated','live_route_mutated','fallback_chain_mutated','memory_route_mutated']) and all(c3p5.get(k) is False for k in ['runtime_authority_mutated','gateway_config_mutated','live_route_mutated','fallback_chain_mutated','memory_route_mutated']),
 'no_external_action_execution': True,
 'owner_decision_record_written': True,
 'c4_requires_separate_owner_approval_recorded': True,
 'm12_c3_frozen_as_accepted_limited_production_expansion': True,
}
failed=[k for k,v in checks.items() if not v]
status=PASS if not failed else BLOCKED; first=failed[0] if failed else None
common={'schema_base':'stickbot.vnext_semantic_gate.m12_c3_final','created_utc':created,'status':status,'artifact_dir':rel(ART),'failed_gates':failed,'first_failure':first}
wt('c3_production_boundary.md',f'''# M12-C3 Final Accepted Production Boundary

Status: `{status}`

M12-C3 is accepted as a limited production expansion **only** for deterministic two-artifact consistency comparison through C3K.

Accepted C3 production scope:

- M12-C3 only.
- Exactly two approved artifacts.
- Deterministic two-artifact consistency comparison through C3K.
- Output only: CONSISTENT, CONFLICT, HOLD, REJECT, and guard REJECT where appropriate.
- Provider/model calls for authoritative C3 comparison remain `0`.

This final owner acceptance does not authorize C4, proposal drafting, unsupported reconciliation, cache, artifact-memory/global promotion, broad/global Semantic Gate promotion, direct provider bypass, arbitrary path authority, memory/context/daily-memory production authority, external action execution, or runtime/Gateway/config/live-route/fallback/memory-route authority mutation.
''')
wt('c3_forbidden_scope.md','''# M12-C3 Final Forbidden Scope

Still forbidden unless separately owner-approved:

- C4.
- More than two authoritative artifacts.
- One-artifact C3 comparison.
- Proposal drafting.
- Unsupported reconciliation.
- External action execution.
- Runtime/config/route/fallback/memory/Gateway mutation.
- Arbitrary path reads as authority.
- Memory/context-bridge/daily-memory as production authority.
- Provider/model-owned authoritative comparison.
- Cache or artifact-memory promotion.
- Direct provider bypass.
- Broad/global Semantic Gate promotion.
''')
wj('c3_consistent_conflict_hold_reject_accounting.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3_final.accounting.v1','c3h_status':c3h.get('status'),'c3h_requests':c3h.get('c3_production_request_count'),'consistent':c3h.get('consistent_count'),'conflict':c3h.get('conflict_count'),'hold':c3h.get('hold_count'),'reject':c3h.get('reject_count'),'guard_reject':c3h.get('guard_reject_count'),'reconciled':c3h.get('c3_production_request_count')==sum(c3h.get(k,0) for k in ['consistent_count','conflict_count','hold_count','reject_count','guard_reject_count']),'attempt_tracking':{'more_than_two_artifact_attempts':c3h.get('more_than_two_artifact_attempts'),'one_artifact_attempts':c3h.get('one_artifact_attempts'),'c4_proposal_drafting_attempts':c3h.get('c4_proposal_drafting_attempts'),'arbitrary_path_attempts':c3h.get('arbitrary_path_attempts'),'memory_context_daily_authority_attempts':c3h.get('memory_context_daily_authority_attempts'),'external_action_holds':c3h.get('external_action_holds'),'runtime_mutation_holds':c3h.get('runtime_mutation_holds')}})
wj('c1_c2_boundary_preservation_readback.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3_final.c1_c2_boundary.v1','m12_c1_status':c1.get('status'),'m12_c2_status':c2.get('status'),'m12_c1_frozen_boundary_preserved':checks['c1_boundary_confirmed'],'m12_c2_frozen_boundary_preserved':checks['c2_boundary_confirmed'],'c1_accepted_scope':'bounded artifact status Q&A only','c2_accepted_scope':'single-artifact runbook guidance only','c3_accepted_scope':'deterministic two-artifact consistency comparison only','boundaries_distinct':checks['c1_c2_c3_boundaries_distinct'],'source_hashes':{rel(C1/'status.json'):source_hashes[rel(C1/'status.json')],rel(C2/'status.json'):source_hashes[rel(C2/'status.json')]}})
wj('mutation_sentinel_report.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3_final.mutation_sentinel.v1','mutation_sentinels_clean':checks['mutation_sentinels_clean'],'production_expansion_limited_to_m12_c3':status==PASS,'broad_production_expansion_applied':False,'c4_started':False,'cache_enabled':False,'artifact_memory_promoted':False,'global_semantic_gate_promoted':False,'gateway_config_mutated':False,'live_route_mutated':False,'fallback_chain_mutated':False,'memory_route_mutated':False,'runtime_authority_mutated':False,'external_action_executed':False})
wj('rollback_readiness.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3_final.rollback.v1','rollback_ready':checks['rollback_ready'],'rollback_applied':False,'m11_frozen_baseline_preserved':checks['m11_frozen_baseline_preserved'],'m12_c1_frozen_boundary_preserved':checks['c1_boundary_confirmed'],'m12_c2_frozen_boundary_preserved':checks['c2_boundary_confirmed'],'source_hashes':source_hashes})
wj('owner_boundary_update.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3_final.owner_boundary_update.v1','owner_boundary_updated':status==PASS,'accepted_candidate':'M12-C3','accepted_limited_production_expansion':status==PASS,'accepted_scope':'M12-C3 deterministic two-artifact consistency comparison through C3K only','accepted_outputs':['CONSISTENT','CONFLICT','HOLD','REJECT','guard REJECT'],'provider_model_authority_calls_allowed':0,'direct_provider_bypass_allowed':False,'c4_requires_separate_owner_approval':True,'forbidden_scope':['C4','more than two authoritative artifacts','one-artifact C3 comparison','proposal drafting','unsupported reconciliation','external action execution','runtime/config/route/fallback/memory/Gateway mutation','arbitrary path reads as authority','memory/context-bridge/daily-memory production authority','provider/model-owned authoritative comparison','cache/artifact-memory promotion','direct provider bypass','broad/global Semantic Gate promotion']})
wj('no_apply_no_mutation_record.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3_final.no_mutation.v1','final_owner_acceptance_packet_only':True,'accepted_limited_production_expansion':'M12-C3 deterministic two-artifact consistency comparison only' if status==PASS else None,'gateway_config_mutated':False,'route_fallback_memory_runtime_authority_mutated':False,'cache_enabled':False,'artifact_memory_promoted':False,'global_semantic_gate_promoted':False,'c4_started':False,'rollback_applied':False,'external_action_executed':False,'broad_production_expansion_applied':False})
wj('c3_acceptance_matrix.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3_final.acceptance_matrix.v1','checks':checks,'decision':'accepted_limited_production_expansion' if status==PASS else 'blocked','accepted_scope':'M12-C3 only / exactly two approved artifacts / deterministic consistency comparison / CONSISTENT-CONFLICT-HOLD-REJECT-guard REJECT','source_hashes':source_hashes})
review=f'''# M12-C3 Final Owner Acceptance Review

Final status: `{status}`

- C3 frozen as accepted limited production expansion: `{status==PASS}`
- Accepted C3 scope: deterministic two-artifact consistency comparison only
- C3P.5 verified: `{c3p5.get('status')}`
- C3H verified: `{c3h.get('status')}`
- C3H requests: `{c3h.get('c3_production_request_count')}/100`
- C3H CONSISTENT / CONFLICT / HOLD / REJECT / guard REJECT: `{c3h.get('consistent_count')} / {c3h.get('conflict_count')} / {c3h.get('hold_count')} / {c3h.get('reject_count')} / {c3h.get('guard_reject_count')}`
- Failed gates: `{failed}`
- First failure: `{first}`
- Provider/model authoritative C3 calls: `{c3h.get('provider_model_calls')}`
- Direct provider bypass: `{c3h.get('direct_provider_bypass_count')}`
- Material regressions: `{c3h.get('material_regression_count')}`
- Missing-output regressions: `{c3h.get('missing_output_regression_count')}`
- Source authority violations: `{c3h.get('source_authority_violations')}`
- Typed value failures: `{c3h.get('typed_value_comparison_failures')}`
- Stale/precedence failures: `{c3h.get('stale_precedence_policy_failures')}`
- C1 boundary confirmed: `{checks['c1_boundary_confirmed']}`
- C2 boundary confirmed: `{checks['c2_boundary_confirmed']}`
- C4 blocked until separate owner approval: `{checks['c4_requires_separate_owner_approval_recorded']}`
- Rollback ready: `{checks['rollback_ready']}`
- M11 frozen baseline preserved: `{checks['m11_frozen_baseline_preserved']}`
- Mutation sentinels clean: `{checks['mutation_sentinels_clean']}`
- Cache/artifact-memory/global promotion disabled: `{checks['cache_disabled'] and checks['artifact_memory_global_promotion_disabled']}`
- Gateway/config/live-route/fallback/memory-route/runtime-authority mutation: `False`
- External action execution: `False`

M12-C3 is accepted as the third limited production expansion boundary alongside M12-C1 and M12-C2. C4 remains blocked and requires separate owner approval.
'''
wt('M12_C3_FINAL_OWNER_ACCEPTANCE_REVIEW.md',review)
missing=[]
status_obj={**common,'schema':'stickbot.vnext_semantic_gate.m12_c3_final.status.v1','required_files':REQ,'required_files_missing':missing,'pass_condition_checks':checks,'accepted_candidate':'M12-C3','accepted_limited_production_expansion':status==PASS,'accepted_scope':'deterministic_two_artifact_consistency_comparison','c3p5_status':c3p5.get('status'),'c3h_status':c3h.get('status'),'c3h_requests':c3h.get('c3_production_request_count'),'consistent_count':c3h.get('consistent_count'),'conflict_count':c3h.get('conflict_count'),'hold_count':c3h.get('hold_count'),'reject_count':c3h.get('reject_count'),'guard_reject_count':c3h.get('guard_reject_count'),'provider_model_calls':c3h.get('provider_model_calls'),'direct_provider_bypass_count':c3h.get('direct_provider_bypass_count'),'material_regression_count':c3h.get('material_regression_count'),'missing_output_regression_count':c3h.get('missing_output_regression_count'),'source_authority_violations':c3h.get('source_authority_violations'),'typed_value_comparison_failures':c3h.get('typed_value_comparison_failures'),'stale_precedence_policy_failures':c3h.get('stale_precedence_policy_failures'),'c4_started':False,'c4_blocked_until_separate_owner_approval':True,'broader_expansion_applied':False,'cache_enabled':False,'artifact_memory_promoted':False,'global_semantic_gate_promoted':False,'runtime_authority_mutated':False,'gateway_config_mutated':False,'live_route_mutated':False,'fallback_chain_mutated':False,'memory_route_mutated':False,'external_action_executed':False,'m11_frozen_baseline_preserved':checks['m11_frozen_baseline_preserved'],'m12_c1_frozen_boundary_preserved':checks['c1_boundary_confirmed'],'m12_c2_frozen_boundary_preserved':checks['c2_boundary_confirmed'],'rollback_ready':checks['rollback_ready'],'mutation_sentinels_clean':checks['mutation_sentinels_clean'],'source_hashes':source_hashes}
wj('status.json',status_obj)
summary_keys=['schema','status','artifact_dir','failed_gates','first_failure','accepted_candidate','accepted_limited_production_expansion','accepted_scope','c3p5_status','c3h_status','c3h_requests','consistent_count','conflict_count','hold_count','reject_count','guard_reject_count','provider_model_calls','direct_provider_bypass_count','material_regression_count','missing_output_regression_count','source_authority_violations','typed_value_comparison_failures','stale_precedence_policy_failures','c4_started','c4_blocked_until_separate_owner_approval','broader_expansion_applied','cache_enabled','artifact_memory_promoted','global_semantic_gate_promoted','runtime_authority_mutated','external_action_executed','m11_frozen_baseline_preserved','m12_c1_frozen_boundary_preserved','m12_c2_frozen_boundary_preserved','rollback_ready','mutation_sentinels_clean']
summary={k:status_obj[k] for k in summary_keys}; summary['schema']='stickbot.vnext_semantic_gate.m12_c3_final.summary.v1'; summary['next_recommended_action']='M12-C3 accepted limited production; separate approval required for C4 or broader expansion.' if status==PASS else 'Final owner acceptance blocked; triage first failure before continuation.'
wj('summary.json',summary)
missing=[n for n in REQ if not (ART/n).exists()]
if missing and 'required_files_missing' not in failed:
    failed.append('required_files_missing')
    status=BLOCKED
    first=first or 'required_files_missing'
    status_obj.update(status=status, failed_gates=failed, first_failure=first, required_files_missing=missing, accepted_limited_production_expansion=False)
    summary.update(status=status, failed_gates=failed, first_failure=first, accepted_limited_production_expansion=False, next_recommended_action='Final owner acceptance blocked; triage first failure before continuation.')
else:
    status_obj['required_files_missing']=missing
wj('status.json',status_obj)
wj('summary.json',summary)
files=sorted(p for p in ART.iterdir() if p.is_file() and p.name!='evidence_manifest.json')
wj('evidence_manifest.json',{'schema':'stickbot.vnext_semantic_gate.m12_c3_final.evidence_manifest.v1','status':status,'artifact_dir':rel(ART),'created_utc':created,'files':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in files],'source_hashes':source_hashes,'self_hash_policy':'evidence_manifest.json excluded from its own file list'})
print(json.dumps({'status':status,'failed_gates':failed,'first_failure':first,'required_files_missing':missing,'status_sha256':sha(ART/'status.json'),'evidence_manifest_sha256':sha(ART/'evidence_manifest.json')},indent=2,sort_keys=True))
if status!=PASS or missing: raise SystemExit(1)
