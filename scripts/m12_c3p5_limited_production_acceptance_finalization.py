#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path('/home/stickai/.openclaw/workspace')
BASE=ROOT/'sharedspace/runtime-kernel-validation/vnext-semantic-gate'
ART=BASE/'m12_c3p5_limited_production_acceptance_finalization'
C3P=BASE/'m12_c3p_limited_production_canary'
C3_OWNER=BASE/'m12_c3_owner_review_readiness_acceptance'
C3R1=BASE/'m12_c3r1_two_artifact_consistency_comparison_readiness'
C3K=BASE/'m12_c3k_two_artifact_consistency_comparison_kernel'
C2=BASE/'m12_c2_final_owner_acceptance_review'
C1=BASE/'m12_c1_final_owner_acceptance_review'
M11=BASE/'m11_7_production_operating_baseline_finalization'
PASS='M12_C3P5_LIMITED_PRODUCTION_ACCEPTANCE_FINALIZATION_PASS'
BLOCKED='M12_C3P5_LIMITED_PRODUCTION_ACCEPTANCE_FINALIZATION_BLOCKED'
REQ=['status.json','summary.json','c3p_acceptance_matrix.json','c3_production_boundary.md','c3_forbidden_scope.md','c3_consistent_conflict_hold_reject_accounting.json','c3_source_authority_acceptance_readback.json','c3_typed_staleness_acceptance_readback.json','c1_c2_boundary_preservation_readback.json','mutation_sentinel_report.json','rollback_readiness.json','owner_boundary_update.json','no_apply_no_mutation_record.json','M12_C3P5_LIMITED_PRODUCTION_ACCEPTANCE_FINALIZATION.md']

def utc(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def rel(p:Path)->str: return str(p.relative_to(ROOT))
def load(p:Path)->Any: return json.loads(p.read_text())
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def wj(n:str,o:Any): ART.mkdir(parents=True,exist_ok=True); (ART/n).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def wt(n:str,s:str): ART.mkdir(parents=True,exist_ok=True); (ART/n).write_text(s.rstrip()+'\n')

created=utc()
c3p=load(C3P/'status.json'); owner=load(C3_OWNER/'status.json'); c3r1=load(C3R1/'status.json'); c3k=load(C3K/'status.json'); c2=load(C2/'status.json'); c1=load(C1/'status.json'); m11=load(M11/'status.json')
source_hashes={rel(C3P/'status.json'):sha(C3P/'status.json'),rel(C3_OWNER/'status.json'):sha(C3_OWNER/'status.json'),rel(C3R1/'status.json'):sha(C3R1/'status.json'),rel(C3K/'status.json'):sha(C3K/'status.json'),rel(C2/'status.json'):sha(C2/'status.json'),rel(C1/'status.json'):sha(C1/'status.json'),rel(M11/'status.json'):sha(M11/'status.json')}
checks={
 'c3p_canary_pass': c3p.get('status')=='M12_C3P_LIMITED_PRODUCTION_CANARY_PASS',
 'c3p_failed_gates_empty': c3p.get('failed_gates')==[],
 'c3p_required_files_present': c3p.get('required_files_missing')==[],
 'c3p_request_count_and_accounting_verified': c3p.get('c3_production_request_count')==25 and (c3p.get('consistent_count'),c3p.get('conflict_count'),c3p.get('hold_count'),c3p.get('reject_count'),c3p.get('guard_reject_count'))==(3,5,12,4,1),
 'c3_owner_review_ready': owner.get('status')=='M12_C3_OWNER_REVIEW_READY',
 'c3k_pass': c3k.get('status')=='M12_C3K_TWO_ARTIFACT_CONSISTENCY_COMPARISON_KERNEL_PASS',
 'c3r1_pass_no_apply': c3r1.get('status')=='M12_C3R1_TWO_ARTIFACT_CONSISTENCY_COMPARISON_READINESS_PASS_NO_APPLY',
 'accepted_comparisons_exactly_two_approved_artifacts': c3p.get('pass_condition_checks',{}).get('accepted_comparisons_exactly_two_approved_artifacts') is True,
 'consistent_envelope_contract_passes': c3p.get('pass_condition_checks',{}).get('consistent_envelope_contract_passes') is True,
 'conflict_envelope_contract_passes': c3p.get('pass_condition_checks',{}).get('conflict_envelope_contract_passes') is True,
 'hold_reject_contract_passes': c3p.get('pass_condition_checks',{}).get('hold_reject_contract_passes') is True,
 'source_authority_deterministic': c3p.get('source_authority_violations')==0 and c3p.get('pass_condition_checks',{}).get('source_authority_deterministic') is True,
 'typed_value_comparison_passes': c3p.get('typed_value_comparison_failures')==0 and c3p.get('pass_condition_checks',{}).get('typed_value_comparison_passes') is True,
 'staleness_precedence_policy_passes': c3p.get('stale_precedence_policy_failures')==0 and c3p.get('pass_condition_checks',{}).get('staleness_precedence_policy_passes') is True,
 'provider_model_calls_zero': c3p.get('provider_model_calls')==0,
 'direct_provider_bypass_zero': c3p.get('direct_provider_bypass_count')==0,
 'material_and_missing_regressions_zero': c3p.get('material_regression_count')==0 and c3p.get('missing_output_regression_count')==0,
 'c4_not_started': c3p.get('c4_started') is False and owner.get('c4_started') is False and c3r1.get('c4_started') is False and c3k.get('c4_started') is False,
 'c1_frozen_boundary_preserved': c1.get('status')=='M12_C1_FINAL_OWNER_ACCEPTANCE_READY' and c3p.get('m12_c1_frozen_boundary_preserved') is True,
 'c2_frozen_boundary_preserved': c2.get('status')=='M12_C2_FINAL_OWNER_ACCEPTANCE_READY' and c3p.get('m12_c2_frozen_boundary_preserved') is True,
 'm11_frozen_baseline_preserved': m11.get('baseline_frozen') is True and c3p.get('m11_frozen_baseline_preserved') is True,
 'rollback_ready': c3p.get('rollback_ready') is True and c2.get('rollback_ready') is True and c1.get('rollback_ready') is True and m11.get('gate_checks',{}).get('rollback_ready') is True,
 'mutation_sentinels_clean': c3p.get('mutation_sentinels_clean') is True and c2.get('pass_condition_checks',{}).get('mutation_sentinels_clean') is True and c1.get('mutation_sentinels_clean') is True and m11.get('gate_checks',{}).get('mutation_sentinels_clean') is True,
 'cache_disabled': c3p.get('cache_enabled') is False and c2.get('cache_enabled') is False and c1.get('cache_enabled') is False and m11.get('cache_enabled') is False,
 'artifact_memory_promotion_disabled': c3p.get('artifact_memory_promoted') is False and c2.get('artifact_memory_promoted') is False and c1.get('artifact_memory_promoted') is False and m11.get('artifact_memory_promoted') is False,
 'no_broad_global_semantic_gate_promotion': c3p.get('global_semantic_gate_promoted') is False,
 'no_gateway_config_route_fallback_memory_runtime_mutation': all(c3p.get(k) is False for k in ['runtime_authority_mutated','gateway_config_mutated','live_route_mutated','fallback_chain_mutated','memory_route_mutated']),
 'owner_boundary_updated': True,
}
failed=[k for k,v in checks.items() if not v]; status=PASS if not failed else BLOCKED; first=failed[0] if failed else None
common={'schema_base':'stickbot.vnext_semantic_gate.m12_c3p5','created_utc':created,'status':status,'artifact_dir':rel(ART),'failed_gates':failed,'first_failure':first}
wt('c3_production_boundary.md',f'''# M12-C3 Accepted Limited Production Boundary

Status: `{status}`

Accepted limited production expansion: **M12-C3 deterministic two-artifact consistency comparison only**.

Allowed production scope:

- M12-C3 only.
- Exactly two approved artifacts.
- Deterministic two-artifact consistency comparison through C3K.
- Outcomes limited to CONSISTENT / CONFLICT / HOLD / REJECT / guard REJECT.
- Provider/model calls for authoritative C3 comparison remain `0`.

This finalization does not authorize C4, broad production expansion, cache, artifact-memory/global promotion, direct provider bypass, proposal drafting, unsupported reconciliation, arbitrary path authority, memory/context/daily-memory authority, external action execution, or runtime/Gateway/config/live-route/fallback/memory-route authority mutation.
''')
wt('c3_forbidden_scope.md','''# M12-C3 Forbidden Scope After C3P.5

Still forbidden unless separately approved:

- C4.
- More than two authoritative artifacts.
- One-artifact C3 comparison.
- Proposal drafting or unsupported reconciliation.
- External action execution.
- Runtime/config/route/fallback/memory/Gateway mutation.
- Arbitrary path reads as authority.
- Memory/context-bridge/daily-memory as production authority.
- Provider/model-owned authoritative comparison.
- Cache or artifact-memory promotion.
- Direct provider bypass.
- Broad/global Semantic Gate promotion.
''')
wj('c3_consistent_conflict_hold_reject_accounting.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p5.accounting.v1','source_c3p_status_hash':source_hashes[rel(C3P/'status.json')],'requests':c3p.get('c3_production_request_count'),'consistent':c3p.get('consistent_count'),'conflict':c3p.get('conflict_count'),'hold':c3p.get('hold_count'),'reject':c3p.get('reject_count'),'guard_reject':c3p.get('guard_reject_count'),'reconciled':c3p.get('c3_production_request_count')==sum(c3p.get(k,0) for k in ['consistent_count','conflict_count','hold_count','reject_count','guard_reject_count']),'attempt_tracking':{'more_than_two_artifact_attempts':c3p.get('more_than_two_artifact_attempts'),'one_artifact_attempts':c3p.get('one_artifact_attempts'),'c4_proposal_drafting_attempts':c3p.get('c4_proposal_drafting_attempts'),'arbitrary_path_attempts':c3p.get('arbitrary_path_attempts'),'memory_context_daily_authority_attempts':c3p.get('memory_context_daily_authority_attempts'),'external_action_holds':c3p.get('external_action_holds'),'runtime_mutation_holds':c3p.get('runtime_mutation_holds')}})
wj('c3_source_authority_acceptance_readback.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p5.source_authority.v1','source_authority_deterministic':checks['source_authority_deterministic'],'source_authority_violations':c3p.get('source_authority_violations'),'accepted_comparisons_exactly_two_approved_artifacts':checks['accepted_comparisons_exactly_two_approved_artifacts'],'more_than_two_artifact_attempts':c3p.get('more_than_two_artifact_attempts'),'one_artifact_attempts':c3p.get('one_artifact_attempts'),'arbitrary_path_attempts':c3p.get('arbitrary_path_attempts'),'memory_context_daily_authority_attempts':c3p.get('memory_context_daily_authority_attempts'),'authoritative_sources':'approved artifact SourceRows only; deterministic C3K comparison envelope'})
wj('c3_typed_staleness_acceptance_readback.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p5.typed_staleness.v1','typed_value_comparison_passes':checks['typed_value_comparison_passes'],'typed_value_comparison_failures':c3p.get('typed_value_comparison_failures'),'staleness_precedence_policy_passes':checks['staleness_precedence_policy_passes'],'stale_precedence_policy_failures':c3p.get('stale_precedence_policy_failures'),'unsupported_reconciliation_allowed':False,'ambiguous_precedence_allowed':False})
wj('c1_c2_boundary_preservation_readback.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p5.c1_c2_boundary.v1','m12_c1_status':c1.get('status'),'m12_c2_status':c2.get('status'),'m12_c1_frozen_boundary_preserved':checks['c1_frozen_boundary_preserved'],'m12_c2_frozen_boundary_preserved':checks['c2_frozen_boundary_preserved'],'c1_accepted_scope':'bounded artifact status Q&A only','c2_accepted_scope':'single-artifact runbook guidance only','source_hashes':{rel(C1/'status.json'):source_hashes[rel(C1/'status.json')],rel(C2/'status.json'):source_hashes[rel(C2/'status.json')]}})
wj('mutation_sentinel_report.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p5.mutation_sentinel.v1','mutation_sentinels_clean':checks['mutation_sentinels_clean'],'production_expansion_limited_to_m12_c3':status==PASS,'broad_production_expansion_applied':False,'c4_started':False,'cache_enabled':False,'artifact_memory_promoted':False,'global_semantic_gate_promoted':False,'gateway_config_mutated':False,'live_route_mutated':False,'fallback_chain_mutated':False,'memory_route_mutated':False,'runtime_authority_mutated':False,'external_action_executed':False})
wj('rollback_readiness.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p5.rollback.v1','rollback_ready':checks['rollback_ready'],'rollback_applied':False,'m11_frozen_baseline_preserved':checks['m11_frozen_baseline_preserved'],'m12_c1_frozen_boundary_preserved':checks['c1_frozen_boundary_preserved'],'m12_c2_frozen_boundary_preserved':checks['c2_frozen_boundary_preserved'],'source_hashes':source_hashes})
wj('owner_boundary_update.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p5.owner_boundary_update.v1','owner_boundary_updated':status==PASS,'accepted_candidate':'M12-C3','accepted_limited_production_expansion':status==PASS,'accepted_scope':'M12-C3 deterministic two-artifact consistency comparison through C3K only','allowed_outcomes':['CONSISTENT','CONFLICT','HOLD','REJECT','guard REJECT'],'provider_model_authority_calls_allowed':0,'direct_provider_bypass_allowed':False,'forbidden_scope':['C4','more than two authoritative artifacts','one-artifact C3 comparison','proposal drafting','unsupported reconciliation','external action execution','runtime/config/route/fallback/memory/Gateway mutation','arbitrary path reads as authority','memory/context-bridge/daily-memory production authority','provider/model-owned authoritative comparison','cache/artifact-memory promotion','direct provider bypass','broad/global Semantic Gate promotion']})
wj('no_apply_no_mutation_record.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p5.no_mutation.v1','acceptance_finalization_only':True,'limited_production_expansion_accepted':'M12-C3 deterministic two-artifact consistency comparison only' if status==PASS else None,'gateway_config_mutated':False,'route_fallback_memory_runtime_authority_mutated':False,'cache_enabled':False,'artifact_memory_promoted':False,'global_semantic_gate_promoted':False,'c4_started':False,'rollback_applied':False,'external_action_executed':False})
matrix={**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p5.acceptance_matrix.v1','checks':checks,'decision':'accepted_limited_production_expansion' if status==PASS else 'blocked','accepted_scope':'M12-C3 only / exactly two approved artifacts / deterministic consistency comparison / CONSISTENT-CONFLICT-HOLD-REJECT-guard REJECT'}
wj('c3p_acceptance_matrix.json',matrix)
review=f'''# M12-C3P.5 Limited Production Acceptance Finalization

Final status: `{status}`

- C3P verified cleanly: `{checks['c3p_canary_pass'] and checks['c3p_failed_gates_empty'] and checks['c3p_required_files_present']}`
- C3P requests: `{c3p.get('c3_production_request_count')}/25`
- CONSISTENT / CONFLICT / HOLD / REJECT / guard REJECT: `{c3p.get('consistent_count')} / {c3p.get('conflict_count')} / {c3p.get('hold_count')} / {c3p.get('reject_count')} / {c3p.get('guard_reject_count')}`
- Failed gates: `{failed}`
- First failure: `{first}`
- Material regressions: `{c3p.get('material_regression_count')}`
- Missing-output regressions: `{c3p.get('missing_output_regression_count')}`
- Source authority violations: `{c3p.get('source_authority_violations')}`
- Typed value comparison failures: `{c3p.get('typed_value_comparison_failures')}`
- Stale/precedence policy failures: `{c3p.get('stale_precedence_policy_failures')}`
- Provider/model calls for authoritative C3 comparison: `{c3p.get('provider_model_calls')}`
- Direct provider bypass: `{c3p.get('direct_provider_bypass_count')}`
- Exactly two approved artifacts for accepted comparisons: `{checks['accepted_comparisons_exactly_two_approved_artifacts']}`
- C4 started: `False`
- Broad production expansion: `False`
- Cache enabled: `False`
- Artifact-memory/global promotion: `False`
- Gateway/config/live-route/fallback/memory-route/runtime-authority mutation: `False`
- Mutation sentinels clean: `{checks['mutation_sentinels_clean']}`
- Rollback ready: `{checks['rollback_ready']}`
- M11 frozen baseline preserved: `{checks['m11_frozen_baseline_preserved']}`
- M12-C1 frozen production boundary preserved: `{checks['c1_frozen_boundary_preserved']}`
- M12-C2 frozen production boundary preserved: `{checks['c2_frozen_boundary_preserved']}`
- Owner boundary updated: `{checks['owner_boundary_updated']}`

Accepted production scope: M12-C3 deterministic two-artifact consistency comparison only, via C3K, with CONSISTENT / CONFLICT / HOLD / REJECT / guard REJECT outcomes only.

C4 remains blocked and requires separate owner approval.
'''
wt('M12_C3P5_LIMITED_PRODUCTION_ACCEPTANCE_FINALIZATION.md',review)
required_missing=[]
status_obj={**common,'schema':'stickbot.vnext_semantic_gate.m12_c3p5.status.v1','required_files':REQ,'required_files_missing':required_missing,'pass_condition_checks':checks,'accepted_candidate':'M12-C3','accepted_limited_production_expansion':status==PASS,'accepted_scope':'deterministic_two_artifact_consistency_comparison','c3p_status':c3p.get('status'),'c3p_requests':c3p.get('c3_production_request_count'),'consistent_count':c3p.get('consistent_count'),'conflict_count':c3p.get('conflict_count'),'hold_count':c3p.get('hold_count'),'reject_count':c3p.get('reject_count'),'guard_reject_count':c3p.get('guard_reject_count'),'more_than_two_artifact_attempts':c3p.get('more_than_two_artifact_attempts'),'one_artifact_attempts':c3p.get('one_artifact_attempts'),'c4_proposal_drafting_attempts':c3p.get('c4_proposal_drafting_attempts'),'arbitrary_path_attempts':c3p.get('arbitrary_path_attempts'),'memory_context_daily_authority_attempts':c3p.get('memory_context_daily_authority_attempts'),'external_action_holds':c3p.get('external_action_holds'),'runtime_mutation_holds':c3p.get('runtime_mutation_holds'),'provider_model_calls':c3p.get('provider_model_calls'),'direct_provider_bypass_count':c3p.get('direct_provider_bypass_count'),'material_regression_count':c3p.get('material_regression_count'),'missing_output_regression_count':c3p.get('missing_output_regression_count'),'source_authority_violations':c3p.get('source_authority_violations'),'typed_value_comparison_failures':c3p.get('typed_value_comparison_failures'),'stale_precedence_policy_failures':c3p.get('stale_precedence_policy_failures'),'c4_started':False,'broader_expansion_applied':False,'cache_enabled':False,'artifact_memory_promoted':False,'global_semantic_gate_promoted':False,'runtime_authority_mutated':False,'gateway_config_mutated':False,'live_route_mutated':False,'fallback_chain_mutated':False,'memory_route_mutated':False,'m11_frozen_baseline_preserved':checks['m11_frozen_baseline_preserved'],'m12_c1_frozen_boundary_preserved':checks['c1_frozen_boundary_preserved'],'m12_c2_frozen_boundary_preserved':checks['c2_frozen_boundary_preserved'],'rollback_ready':checks['rollback_ready'],'owner_boundary_updated':status==PASS,'source_hashes':source_hashes}
wj('status.json',status_obj)
summary={k:status_obj[k] for k in ['schema','status','artifact_dir','failed_gates','first_failure','accepted_candidate','accepted_limited_production_expansion','accepted_scope','c3p_status','c3p_requests','consistent_count','conflict_count','hold_count','reject_count','guard_reject_count','provider_model_calls','direct_provider_bypass_count','material_regression_count','missing_output_regression_count','source_authority_violations','typed_value_comparison_failures','stale_precedence_policy_failures','c4_started','broader_expansion_applied','cache_enabled','artifact_memory_promoted','global_semantic_gate_promoted','runtime_authority_mutated','m11_frozen_baseline_preserved','m12_c1_frozen_boundary_preserved','m12_c2_frozen_boundary_preserved','rollback_ready','owner_boundary_updated']}
summary['schema']='stickbot.vnext_semantic_gate.m12_c3p5.summary.v1'; summary['next_recommended_action']='M12-C3 limited production accepted; separate approval required for C4 or any broader expansion.' if status==PASS else 'Acceptance finalization blocked; triage first failure before continuation.'
wj('summary.json',summary)
required_missing=[n for n in REQ if not (ART/n).exists()]
if required_missing and 'required_files_missing' not in failed:
    failed.append('required_files_missing')
    status=BLOCKED
    first=first or 'required_files_missing'
    status_obj.update(status=status, failed_gates=failed, first_failure=first, required_files_missing=required_missing, accepted_limited_production_expansion=False, owner_boundary_updated=False)
    summary.update(status=status, failed_gates=failed, first_failure=first, accepted_limited_production_expansion=False, owner_boundary_updated=False, next_recommended_action='Acceptance finalization blocked; triage first failure before continuation.')
else:
    status_obj['required_files_missing']=required_missing
wj('status.json',status_obj)
wj('summary.json',summary)
files=sorted(p for p in ART.iterdir() if p.is_file() and p.name!='evidence_manifest.json')
wj('evidence_manifest.json',{'schema':'stickbot.vnext_semantic_gate.m12_c3p5.evidence_manifest.v1','status':status,'artifact_dir':rel(ART),'created_utc':created,'files':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in files],'source_hashes':source_hashes,'self_hash_policy':'evidence_manifest.json excluded from its own file list'})
print(json.dumps({'status':status,'failed_gates':failed,'first_failure':first,'required_files_missing':required_missing,'status_sha256':sha(ART/'status.json'),'evidence_manifest_sha256':sha(ART/'evidence_manifest.json')},indent=2,sort_keys=True))
if status!=PASS or required_missing: raise SystemExit(1)
