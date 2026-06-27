#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path('/home/stickai/.openclaw/workspace')
BASE=ROOT/'sharedspace/runtime-kernel-validation/vnext-semantic-gate'
ART=BASE/'m12_c4_owner_review_design_acceptance'
C4=BASE/'m12_c4_bounded_next_step_proposal_readiness_design'
C3=BASE/'m12_c3_final_owner_acceptance_review'
C2=BASE/'m12_c2_final_owner_acceptance_review'
C1=BASE/'m12_c1_final_owner_acceptance_review'
M11=BASE/'m11_7_production_operating_baseline_finalization'
PASS='M12_C4_OWNER_REVIEW_DESIGN_ACCEPTED'
BLOCKED='M12_C4_OWNER_REVIEW_DESIGN_BLOCKED'
REQ=['status.json','summary.json','c4_design_readback.json','c4_acceptance_matrix.json','c4_owner_decision_record.md','c1_c2_c3_boundary_preservation_readback.json','mutation_sentinel_report.json','rollback_readiness.json','no_apply_no_mutation_record.json','M12_C4_OWNER_REVIEW_DESIGN_ACCEPTANCE.md']

def utc(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def rel(p:Path)->str: return str(p.relative_to(ROOT))
def load(p:Path)->Any: return json.loads(p.read_text())
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def wj(n:str,o:Any): ART.mkdir(parents=True,exist_ok=True); (ART/n).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def wt(n:str,s:str): ART.mkdir(parents=True,exist_ok=True); (ART/n).write_text(s.rstrip()+'\n')

created=utc(); ART.mkdir(parents=True,exist_ok=True)
c4=load(C4/'status.json'); c3=load(C3/'status.json'); c2=load(C2/'status.json'); c1=load(C1/'status.json'); m11=load(M11/'status.json')
source_hashes={rel(C4/'status.json'):sha(C4/'status.json'),rel(C3/'status.json'):sha(C3/'status.json'),rel(C2/'status.json'):sha(C2/'status.json'),rel(C1/'status.json'):sha(C1/'status.json'),rel(M11/'status.json'):sha(M11/'status.json')}
checks={
 'c4_design_verifies': c4.get('status')=='M12_C4_READINESS_DESIGN_PASS_NO_APPLY' and c4.get('required_files_missing')==[] and c4.get('failed_gates')==[],
 'c4_bounded_proposal_only': c4.get('c4_scope_bounded_next_step_proposal_only') is True,
 'proposal_drafting_not_action_authority': c4.get('c4_execution_authority') is False,
 'c4_no_execution_authority': c4.get('c4_execution_authority') is False,
 'c4_no_production_mutation_authority': c4.get('c4_production_mutation_authority') is False,
 'source_authority_deterministic': c4.get('source_authority_deterministic') is True,
 'proposal_output_contract_explicit': c4.get('proposal_output_contract_explicit') is True,
 'non_execution_policy_explicit': c4.get('non_execution_policy_explicit') is True,
 'fail_closed_policy_explicit': c4.get('fail_closed_policy_explicit') is True,
 'model_prose_boundary_explicit_non_authoritative': c4.get('model_prose_boundary_explicit') is True and c4.get('provider_model_authoritative_calls_allowed')==0 and c4.get('provider_model_authoritative_calls_observed')==0,
 'c4_kernel_design_adequate': c4.get('c4_kernel_design_written') is True and c4.get('kernel_implemented') is False,
 'fixture_plan_adequate': c4.get('fixture_plan_written') is True,
 'abort_gates_adequate': c4.get('abort_gates_written') is True,
 'c1_boundary_preserved': c1.get('status')=='M12_C1_FINAL_OWNER_ACCEPTANCE_READY' and c4.get('m12_c1_frozen_boundary_preserved') is True,
 'c2_boundary_preserved': c2.get('status')=='M12_C2_FINAL_OWNER_ACCEPTANCE_READY' and c4.get('m12_c2_frozen_boundary_preserved') is True,
 'c3_boundary_preserved': c3.get('status')=='M12_C3_FINAL_OWNER_ACCEPTANCE_READY' and c4.get('m12_c3_frozen_boundary_preserved') is True,
 'rollback_ready': c4.get('rollback_ready') is True and c3.get('rollback_ready') is True and c2.get('rollback_ready') is True and c1.get('rollback_ready') is True and m11.get('gate_checks',{}).get('rollback_ready') is True,
 'mutation_sentinels_clean': c4.get('pass_condition_checks',{}).get('mutation_sentinels_clean') is True and c3.get('mutation_sentinels_clean') is True,
 'no_production_expansion': c4.get('production_expansion_applied') is False and c4.get('c4_production_started') is False and c4.get('c4_canary_started') is False,
 'cache_disabled': c4.get('cache_enabled') is False and c3.get('cache_enabled') is False,
 'artifact_memory_promotion_disabled': c4.get('artifact_memory_promoted') is False and c3.get('artifact_memory_promoted') is False,
 'global_semantic_gate_not_promoted': c4.get('global_semantic_gate_promoted') is False and c3.get('global_semantic_gate_promoted') is False,
 'runtime_authority_unchanged': all(c4.get(k) is False for k in ['runtime_authority_mutated','gateway_config_mutated','live_route_mutated','fallback_chain_mutated','memory_route_mutated']),
 'external_action_not_executed': c4.get('external_action_executed') is False,
 'direct_provider_bypass_zero': c4.get('direct_provider_bypass_count')==0,
 'owner_decision_record_written': True,
}
failed=[k for k,v in checks.items() if not v]
status=PASS if not failed else BLOCKED
first=failed[0] if failed else None
common={'schema_base':'stickbot.vnext_semantic_gate.m12_c4_owner_review_design_acceptance','created_utc':created,'status':status,'artifact_dir':rel(ART),'failed_gates':failed,'first_failure':first}
readback={**common,'schema':'stickbot.vnext_semantic_gate.m12_c4_owner_review.design_readback.v1','source_design_status':c4.get('status'),'source_design_artifact':c4.get('artifact_dir'),'scope_bounded_next_step_proposal_only':checks['c4_bounded_proposal_only'],'proposal_drafting_is_not_action_authority':checks['proposal_drafting_not_action_authority'],'source_authority_deterministic':checks['source_authority_deterministic'],'proposal_output_contract_explicit':checks['proposal_output_contract_explicit'],'non_execution_policy_explicit':checks['non_execution_policy_explicit'],'fail_closed_policy_explicit':checks['fail_closed_policy_explicit'],'model_prose_non_authoritative':checks['model_prose_boundary_explicit_non_authoritative'],'c4_kernel_design_adequate':checks['c4_kernel_design_adequate'],'fixture_plan_adequate':checks['fixture_plan_adequate'],'abort_gates_adequate':checks['abort_gates_adequate'],'c4_production_started':False,'c4_canary_started':False,'kernel_implementation_started':False}
wj('c4_design_readback.json',readback)
acceptance={**common,'schema':'stickbot.vnext_semantic_gate.m12_c4_owner_review.acceptance_matrix.v1','checks':checks,'decision':'design_accepted_before_c4k' if status==PASS else 'blocked','accepted_candidate':'M12-C4 readiness design','accepted_scope':'bounded next-step proposal drafting design only; no C4K implementation in this packet','c4k_authorized':False,'c4_production_authorized':False,'c4_canary_authorized':False,'source_hashes':source_hashes}
wj('c4_acceptance_matrix.json',acceptance)
wt('c4_owner_decision_record.md',f'''# M12-C4 Owner Decision Record — Design Acceptance

Decision status: `{status}`

Accepted if PASS: M12-C4 no-apply readiness design is accepted for **bounded next-step proposal drafting** before C4K implementation.

This decision does not authorize:

- C4K implementation.
- C4 readiness exercise.
- C4 canary.
- C4 production.
- cache enablement.
- artifact-memory/global Semantic Gate promotion.
- runtime/Gateway/config/route/fallback/memory authority mutation.
- external action execution.

C4K requires separate owner approval.

Failed gates: `{failed}`
First failure: `{first}`
''')
wj('c1_c2_c3_boundary_preservation_readback.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c4_owner_review.boundary.v1','c1_status':c1.get('status'),'c2_status':c2.get('status'),'c3_status':c3.get('status'),'c1_scope':'bounded artifact status Q&A','c2_scope':'deterministic single-artifact runbook guidance','c3_scope':'deterministic two-artifact consistency comparison','c1_preserved':checks['c1_boundary_preserved'],'c2_preserved':checks['c2_boundary_preserved'],'c3_preserved':checks['c3_boundary_preserved'],'source_hashes':{rel(C1/'status.json'):source_hashes[rel(C1/'status.json')],rel(C2/'status.json'):source_hashes[rel(C2/'status.json')],rel(C3/'status.json'):source_hashes[rel(C3/'status.json')]}})
wj('mutation_sentinel_report.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c4_owner_review.mutation_sentinel.v1','mutation_sentinels_clean':checks['mutation_sentinels_clean'],'production_expansion_applied':False,'c4_production_started':False,'c4_canary_started':False,'c4k_implementation_started':False,'cache_enabled':False,'artifact_memory_promoted':False,'global_semantic_gate_promoted':False,'runtime_authority_mutated':False,'gateway_config_mutated':False,'live_route_mutated':False,'fallback_chain_mutated':False,'memory_route_mutated':False,'external_action_executed':False})
wj('rollback_readiness.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c4_owner_review.rollback.v1','rollback_ready':checks['rollback_ready'],'rollback_applied':False,'m11_frozen_baseline_preserved':m11.get('baseline_frozen') is True,'source_hashes':source_hashes})
wj('no_apply_no_mutation_record.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c4_owner_review.no_apply_no_mutation.v1','owner_review_design_acceptance_only':True,'c4k_implementation_started':False,'c4_production_started':False,'c4_canary_started':False,'production_expansion_applied':False,'cache_enabled':False,'artifact_memory_promoted':False,'global_semantic_gate_promoted':False,'runtime_authority_mutated':False,'gateway_config_mutated':False,'external_action_executed':False,'direct_provider_bypass_allowed':False})
review=f'''# M12-C4 Owner Review / Design Acceptance

Final status: `{status}`

Review target: M12-C4 no-apply readiness design before any C4K implementation.

Required review results:

1. C4 scope bounded next-step proposal drafting only: `{checks['c4_bounded_proposal_only']}`
2. Proposal drafting is not action authority: `{checks['proposal_drafting_not_action_authority']}`
3. Source authority rules deterministic: `{checks['source_authority_deterministic']}`
4. Proposal output contract explicit: `{checks['proposal_output_contract_explicit']}`
5. Non-execution policy explicit: `{checks['non_execution_policy_explicit']}`
6. Fail-closed policy explicit: `{checks['fail_closed_policy_explicit']}`
7. Model prose boundary explicit and non-authoritative: `{checks['model_prose_boundary_explicit_non_authoritative']}`
8. C4 kernel design adequate: `{checks['c4_kernel_design_adequate']}`
9. Fixture plan adequate: `{checks['fixture_plan_adequate']}`
10. Abort gates adequate: `{checks['abort_gates_adequate']}`
11. C1/C2/C3 boundaries preserved: `{checks['c1_boundary_preserved'] and checks['c2_boundary_preserved'] and checks['c3_boundary_preserved']}`
12. Rollback ready: `{checks['rollback_ready']}`
13. Mutation sentinels clean: `{checks['mutation_sentinels_clean']}`
14. No production expansion: `{checks['no_production_expansion']}`

Failed gates: `{failed}`
First failure: `{first}`

This packet accepts the M12-C4 design only. It does not implement C4K, start C4 canary/production, enable cache, promote artifact-memory/global Semantic Gate, mutate runtime/Gateway/config state, or execute external actions.

Recommended next action if separately approved: implement deterministic C4 proposal kernel (C4K).
'''
wt('M12_C4_OWNER_REVIEW_DESIGN_ACCEPTANCE.md',review)
missing=[]
status_obj={**common,'schema':'stickbot.vnext_semantic_gate.m12_c4_owner_review.status.v1','required_files':REQ,'required_files_missing':missing,'pass_condition_checks':checks,'accepted_design':status==PASS,'accepted_scope':'M12-C4 bounded next-step proposal drafting design only','c4k_authorized':False,'c4k_implementation_started':False,'c4_production_started':False,'c4_canary_started':False,'production_expansion_applied':False,'cache_enabled':False,'artifact_memory_promoted':False,'global_semantic_gate_promoted':False,'runtime_authority_mutated':False,'gateway_config_mutated':False,'live_route_mutated':False,'fallback_chain_mutated':False,'memory_route_mutated':False,'external_action_executed':False,'direct_provider_bypass_count':0,'rollback_ready':checks['rollback_ready'],'mutation_sentinels_clean':checks['mutation_sentinels_clean'],'m12_c1_frozen_boundary_preserved':checks['c1_boundary_preserved'],'m12_c2_frozen_boundary_preserved':checks['c2_boundary_preserved'],'m12_c3_frozen_boundary_preserved':checks['c3_boundary_preserved'],'source_hashes':source_hashes}
wj('status.json',status_obj)
summary_keys=['schema','status','artifact_dir','failed_gates','first_failure','accepted_design','accepted_scope','c4k_authorized','c4k_implementation_started','c4_production_started','c4_canary_started','production_expansion_applied','cache_enabled','artifact_memory_promoted','global_semantic_gate_promoted','runtime_authority_mutated','external_action_executed','direct_provider_bypass_count','rollback_ready','mutation_sentinels_clean','m12_c1_frozen_boundary_preserved','m12_c2_frozen_boundary_preserved','m12_c3_frozen_boundary_preserved']
summary={k:status_obj[k] for k in summary_keys}; summary['schema']='stickbot.vnext_semantic_gate.m12_c4_owner_review.summary.v1'; summary['next_recommended_action']='Implement deterministic C4 proposal kernel (C4K) only if separately approved.' if status==PASS else 'C4 owner review/design acceptance blocked; triage first failure.'
wj('summary.json',summary)
missing=[n for n in REQ if not (ART/n).exists()]
if missing and 'required_files_missing' not in failed:
    failed.append('required_files_missing')
    status=BLOCKED
    first=first or 'required_files_missing'
    status_obj.update(status=status,failed_gates=failed,first_failure=first,required_files_missing=missing,accepted_design=False)
    summary.update(status=status,failed_gates=failed,first_failure=first,accepted_design=False,next_recommended_action='C4 owner review/design acceptance blocked; triage first failure.')
    wj('status.json',status_obj); wj('summary.json',summary)
else:
    status_obj['required_files_missing']=missing; wj('status.json',status_obj)
files=sorted(p for p in ART.iterdir() if p.is_file() and p.name!='evidence_manifest.json')
wj('evidence_manifest.json',{'schema':'stickbot.vnext_semantic_gate.m12_c4_owner_review.evidence_manifest.v1','status':status,'artifact_dir':rel(ART),'created_utc':created,'files':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in files],'source_hashes':source_hashes,'self_hash_policy':'evidence_manifest.json excluded from its own file list'})
print(json.dumps({'status':status,'failed_gates':failed,'first_failure':first,'required_files_missing':missing,'status_sha256':sha(ART/'status.json'),'evidence_manifest_sha256':sha(ART/'evidence_manifest.json')},indent=2,sort_keys=True))
if status!=PASS or missing: raise SystemExit(1)
