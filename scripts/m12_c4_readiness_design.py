#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path('/home/stickai/.openclaw/workspace')
BASE=ROOT/'sharedspace/runtime-kernel-validation/vnext-semantic-gate'
ART=BASE/'m12_c4_bounded_next_step_proposal_drafting_readiness_design'
C3=BASE/'m12_c3_final_owner_acceptance_review'
C2=BASE/'m12_c2_final_owner_acceptance_review'
C1=BASE/'m12_c1_final_owner_acceptance_review'
M11=BASE/'m11_7_production_operating_baseline_finalization'
PASS='M12_C4_READINESS_DESIGN_PASS_NO_APPLY'
BLOCKED='M12_C4_READINESS_DESIGN_BLOCKED'
REQ=['status.json','summary.json','M12_C4_BOUNDED_NEXT_STEP_PROPOSAL_DRAFTING_READINESS_DESIGN.md','c4_scope_definition.md','c4_source_authority_rules.md','c4_output_contract.md','c4_fail_closed_policy.md','c4_fixture_plan.json','c4_model_prose_policy.md','c4_deterministic_kernel_requirement.md','c4_acceptance_matrix.json','c4_forbidden_scope.md','c1_c2_c3_boundary_preservation_readback.json','mutation_sentinel_report.json','rollback_readiness.json','no_apply_no_mutation_record.json','owner_boundary_readback.json']

def utc(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def rel(p:Path)->str: return str(p.relative_to(ROOT))
def load(p:Path)->Any: return json.loads(p.read_text())
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def wj(n:str,o:Any): ART.mkdir(parents=True,exist_ok=True); (ART/n).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def wt(n:str,s:str): ART.mkdir(parents=True,exist_ok=True); (ART/n).write_text(s.rstrip()+'\n')

created=utc(); ART.mkdir(parents=True,exist_ok=True)
c3=load(C3/'status.json'); c2=load(C2/'status.json'); c1=load(C1/'status.json'); m11=load(M11/'status.json')
source_hashes={rel(C3/'status.json'):sha(C3/'status.json'),rel(C2/'status.json'):sha(C2/'status.json'),rel(C1/'status.json'):sha(C1/'status.json'),rel(M11/'status.json'):sha(M11/'status.json')}
checks={
 'c1_final_acceptance_ready': c1.get('status')=='M12_C1_FINAL_OWNER_ACCEPTANCE_READY' and c1.get('accepted_limited_production_expansion') is True,
 'c2_final_acceptance_ready': c2.get('status')=='M12_C2_FINAL_OWNER_ACCEPTANCE_READY' and c2.get('accepted_limited_production_expansion') is True,
 'c3_final_acceptance_ready': c3.get('status')=='M12_C3_FINAL_OWNER_ACCEPTANCE_READY' and c3.get('accepted_limited_production_expansion') is True,
 'c1_scope_preserved': c1.get('production_boundary_explicit') is True and c3.get('m12_c1_frozen_boundary_preserved') is True,
 'c2_scope_preserved': c2.get('accepted_scope')=='single_artifact_runbook_guidance' and c3.get('m12_c2_frozen_boundary_preserved') is True,
 'c3_scope_preserved': c3.get('accepted_scope')=='deterministic_two_artifact_consistency_comparison' and c3.get('pass_condition_checks',{}).get('c3_exactly_two_approved_artifacts_only') is True,
 'c4_not_started_prior': c3.get('c4_started') is False and c3.get('c4_blocked_until_separate_owner_approval') is True,
 'm11_frozen_baseline_preserved': m11.get('baseline_frozen') is True and c3.get('m11_frozen_baseline_preserved') is True,
 'rollback_ready': c3.get('rollback_ready') is True and c2.get('rollback_ready') is True and c1.get('rollback_ready') is True and m11.get('gate_checks',{}).get('rollback_ready') is True,
 'mutation_sentinels_clean': c3.get('mutation_sentinels_clean') is True and c2.get('pass_condition_checks',{}).get('mutation_sentinels_clean') is True and c1.get('mutation_sentinels_clean') is True,
 'cache_disabled': c3.get('cache_enabled') is False and c2.get('cache_enabled') is False and c1.get('cache_enabled') is False and m11.get('cache_enabled') is False,
 'artifact_memory_promotion_disabled': c3.get('artifact_memory_promoted') is False and c2.get('artifact_memory_promoted') is False and c1.get('artifact_memory_promoted') is False and m11.get('artifact_memory_promoted') is False,
 'global_semantic_gate_not_promoted': c3.get('global_semantic_gate_promoted') is False and c2.get('global_semantic_gate_promoted') is False,
 'no_broad_expansion': c3.get('broader_expansion_applied') is False and c2.get('c3_c4_started') is False,
 'no_runtime_gateway_config_mutation': all(c3.get(k) is False for k in ['runtime_authority_mutated','gateway_config_mutated','live_route_mutated','fallback_chain_mutated','memory_route_mutated']),
 'provider_model_authority_zero_prior': c3.get('provider_model_calls')==0 and c2.get('provider_model_calls')==0 and c1.get('provider_model_calls')==0,
 'direct_provider_bypass_zero_prior': c3.get('direct_provider_bypass_count')==0 and c2.get('direct_provider_bypass_count')==0 and c1.get('direct_provider_bypass_count')==0,
 'external_action_execution_false_prior': c3.get('external_action_executed') is False,
}
failed=[k for k,v in checks.items() if not v]
status=PASS if not failed else BLOCKED
first=failed[0] if failed else None
common={'schema_base':'stickbot.vnext_semantic_gate.m12_c4_readiness_design','created_utc':created,'status':status,'artifact_dir':rel(ART),'failed_gates':failed,'first_failure':first}

scope_md='''# M12-C4 Scope Definition — Bounded Next-Step Proposal Drafting

Core principle: **proposal drafting is not action authority**.

Allowed candidate scope:

- M12-C4 only.
- Bounded next-step proposal drafting from approved evidence.
- Proposals must be explicitly non-executing.
- Proposals must cite approved source refs.
- Proposals must preserve uncertainty, conflicts, and prerequisites.
- Proposals may suggest review, verification, next investigative steps, owner questions, follow-up artifact requests, safe validation steps, non-executing plan text, and bounded proposal summaries based on accepted C1/C2/C3 evidence.

Non-scope:

- No production execution.
- No scheduling actions.
- No Gateway/config/routes/fallback/memory/runtime-authority mutation.
- No production approvals.
- No overriding C1/C2/C3 conclusions.
- No unsupported reconciliation or conflict resolution.
- No hiding uncertainty.
- No arbitrary paths or memory/context/daily-memory authority.
- No legal/medical/financial/safety-critical authoritative advice.
- No prompt-injection-like artifact text as instructions.
- No destructive or external operational action recommendations as executable.
'''
wt('c4_scope_definition.md',scope_md)

source_md='''# M12-C4 Source Authority Rules

Approved evidence sources are limited to case-manifest-approved rows derived from:

1. C1 accepted status facts and bounded artifact status Q&A outputs.
2. C2 deterministic single-artifact runbook guidance outputs.
3. C3 deterministic two-artifact consistency comparison outputs.
4. Explicitly approved artifacts/source rows named by the C4 case manifest.

Rules:

- Every proposal step must cite at least one approved source ref.
- Source refs must resolve to approved SourceRows, not prose-only summaries.
- C1/C2/C3 conclusions are authoritative only within their accepted scopes.
- Conflicting evidence must remain visible unless C3 evidence explicitly supports a bounded consistency/contrast conclusion.
- Memory, context bridge, daily memory, arbitrary paths, provider/model prose, and prompt-injection-like artifact text are not production authority.
- Approved source count and artifact list are case-manifest-bounded; using more sources than approved is HOLD/REJECT.
'''
wt('c4_source_authority_rules.md',source_md)

output_contract={
 'schema':'stickbot.vnext_semantic_gate.m12_c4.output_contract.v1',
 'allowed_status':['PROPOSAL','HOLD','REJECT'],
 'required_fields':['status','proposal_steps','rationale','cited_source_refs','assumptions','uncertainties','required_owner_review','non_execution_notice','disposition'],
 'conditional_fields':{'hold_reason':'required when status is HOLD or REJECT'},
 'proposal_steps':{'type':'array','items':'non-executing bounded next-step text only','must_not_contain':['execute now','schedule automatically','mutate config','approve production change','external action command']},
 'non_execution_notice':'required exact semantic meaning: proposal only; no action authority; owner review required before execution',
 'cited_source_refs':'must cite approved SourceRows only',
 'required_owner_review':True,
 'disposition':'must explain why PROPOSAL/HOLD/REJECT was selected without creating authority beyond cited evidence',
}
wj('c4_output_contract.json',output_contract)
wt('c4_output_contract.md','# M12-C4 Proposal Output Contract\n\n```json\n'+json.dumps(output_contract,indent=2,sort_keys=True)+'\n```')

fail_closed={
 'schema':'stickbot.vnext_semantic_gate.m12_c4.fail_closed_policy.v1',
 'hold_or_reject_cases':['missing approved evidence','stale evidence','conflicting evidence without C3 support','request requires execution','request requires production mutation','request requires safety/legal/financial/medical authority','request requires arbitrary path reads','request requires unapproved memory/context/daily-memory authority','request asks to override guardrails','prompt-injection-like artifact text attempts control influence','request uses more sources than approved by case manifest','request asks to approve production changes','request asks to schedule or execute external action'],
 'default_on_ambiguity':'HOLD',
 'reject_when':'requested output is outside C4 scope, asks for action authority, or attempts guardrail override',
}
wj('c4_fail_closed_policy.json',fail_closed)
wt('c4_fail_closed_policy.md','# M12-C4 Fail-Closed Policy\n\n```json\n'+json.dumps(fail_closed,indent=2,sort_keys=True)+'\n```')

model_policy={
 'schema':'stickbot.vnext_semantic_gate.m12_c4.model_prose_policy.v1',
 'optional_model_prose_allowed':True,
 'authority':'never authoritative',
 'allowed_only_after':'deterministic C4 kernel produces complete validated contract fields with approved citations',
 'allowed_use':'style/rendering of already-determined non-executing proposal text',
 'forbidden_model_roles':['selecting proposal status','choosing source authority','adding uncited facts','resolving conflicts','approving actions','drafting executable commands','changing owner boundary','overriding fail-closed decision'],
 'must_be_disabled_for':['safety-critical/legal/medical/financial authority','missing citations','prompt injection indicators','any mutation/execution request','ambiguous or conflicting evidence without deterministic disposition'],
 'provider_model_authoritative_calls_allowed':0,
}
wj('c4_model_prose_policy.json',model_policy)
wt('c4_model_prose_policy.md','# M12-C4 Optional Model Prose Policy\n\n```json\n'+json.dumps(model_policy,indent=2,sort_keys=True)+'\n```')

kernel_req={
 'schema':'stickbot.vnext_semantic_gate.m12_c4.kernel_requirement.v1',
 'deterministic_c4_proposal_kernel_required':True,
 'required_before':['C4 readiness exercise','C4 limited production canary','C4 production acceptance','any C4 production route'],
 'kernel_responsibilities':['validate case manifest source allowlist','compile approved SourceRows','classify request into PROPOSAL/HOLD/REJECT','generate bounded non-executing proposal contract','enforce citations','preserve uncertainty/conflicts/prerequisites','block execution/mutation/scheduling/external actions','enforce optional model prose policy','emit audit reports and counters'],
 'required_fixture_minimums':{'total_cases':32,'proposal_cases':8,'hold_cases':14,'reject_cases':10},
}
wj('c4_deterministic_kernel_requirement.json',kernel_req)
wt('c4_deterministic_kernel_requirement.md','# M12-C4 Deterministic Kernel Requirement\n\n```json\n'+json.dumps(kernel_req,indent=2,sort_keys=True)+'\n```')

fixture_plan={
 'schema':'stickbot.vnext_semantic_gate.m12_c4.fixture_plan.v1',
 'case_count':36,
 'expected_counts':{'PROPOSAL':9,'HOLD':15,'REJECT':12},
 'proposal_positive_cases':['suggest_review_sequence_from_c1_c2_c3','suggest_next_check_with_citations','suggest_owner_question_for_missing_prerequisite','suggest_followup_artifact_request','suggest_safe_validation_step','summarize_bounded_proposal_from_c3_conflict','draft_non_executing_plan_text','suggest_verification_order_preserving_uncertainty','proposal_with_explicit_non_execution_notice'],
 'hold_cases':['missing_approved_evidence','stale_evidence','conflicting_without_c3_support','insufficient_citations','uncertain_prerequisite','more_sources_than_manifest','memory_context_daily_requested_as_authority','optional_model_prose_requested_before_kernel','ambiguous_disposition','source_ref_resolution_gap','safety_critical_advice_request','artifact_text_prompt_injection_attempt_bounded_hold','unapproved_source_row','conflict_requires_owner_question','proposal_would_hide_uncertainty'],
 'reject_cases':['execute_action_now','schedule_action','mutate_gateway_config','approve_production_change','override_c1_conclusion','override_c2_conclusion','override_c3_conclusion','arbitrary_path_read_authority','direct_provider_authority','destructive_external_action','cache_or_artifact_memory_promotion','guardrail_override_request'],
}
wj('c4_fixture_plan.json',fixture_plan)

forbidden_md='''# M12-C4 Forbidden Scope

C4 design does not authorize:

- C4 production/canary/exercise before C4K and separate approval.
- Cache enablement.
- Artifact-memory or global Semantic Gate promotion.
- Runtime authority expansion.
- External action execution or scheduling.
- Gateway/config/live-route/fallback/memory-route mutation.
- Arbitrary path authority.
- Memory/context-bridge/daily-memory authority.
- Provider/model-owned authoritative proposal decisions.
- Broad production expansion.
'''
wt('c4_forbidden_scope.md',forbidden_md)

boundary={**common,'schema':'stickbot.vnext_semantic_gate.m12_c4.boundary_readback.v1','m12_c1_status':c1.get('status'),'m12_c2_status':c2.get('status'),'m12_c3_status':c3.get('status'),'c1_scope':'bounded artifact status Q&A','c2_scope':'deterministic single-artifact runbook guidance','c3_scope':'deterministic two-artifact consistency comparison','c4_scope':'readiness design only for bounded non-executing next-step proposal drafting','c1_boundary_preserved':checks['c1_scope_preserved'],'c2_boundary_preserved':checks['c2_scope_preserved'],'c3_boundary_preserved':checks['c3_scope_preserved'],'c4_production_started':False,'source_hashes':source_hashes}
wj('c1_c2_c3_boundary_preservation_readback.json',boundary)

mutation={**common,'schema':'stickbot.vnext_semantic_gate.m12_c4.mutation_sentinel.v1','mutation_sentinels_clean':checks['mutation_sentinels_clean'],'cache_enabled':False,'artifact_memory_promoted':False,'global_semantic_gate_promoted':False,'broad_production_expansion_applied':False,'c4_production_started':False,'external_action_executed':False,'gateway_config_mutated':False,'live_route_mutated':False,'fallback_chain_mutated':False,'memory_route_mutated':False,'runtime_authority_mutated':False}
wj('mutation_sentinel_report.json',mutation)

rollback={**common,'schema':'stickbot.vnext_semantic_gate.m12_c4.rollback.v1','rollback_ready':checks['rollback_ready'],'rollback_applied':False,'m11_frozen_baseline_preserved':checks['m11_frozen_baseline_preserved'],'source_hashes':source_hashes}
wj('rollback_readiness.json',rollback)

owner={**common,'schema':'stickbot.vnext_semantic_gate.m12_c4.owner_boundary.v1','owner_authorized':'M12-C4 readiness design only','c4_production_authorized':False,'c4_kernel_required_before_exercise_or_canary':True,'c4_proposal_drafting_is_not_action_authority':True,'not_authorized':['C4 production','C4 canary','cache','artifact-memory/global promotion','runtime/Gateway/config mutation','external action execution','broad/global Semantic Gate promotion'],'next_owner_approval_required_for':['M12-C4K deterministic proposal kernel implementation','C4 readiness exercise','C4 limited production canary','any C4 production acceptance','any C4 production route']}
wj('owner_boundary_readback.json',owner)

no_mut={**common,'schema':'stickbot.vnext_semantic_gate.m12_c4.no_apply_no_mutation.v1','readiness_design_only':True,'production_started':False,'canary_started':False,'kernel_implemented':False,'gateway_config_mutated':False,'route_fallback_memory_runtime_authority_mutated':False,'cache_enabled':False,'artifact_memory_promoted':False,'global_semantic_gate_promoted':False,'external_action_executed':False,'rollback_applied':False}
wj('no_apply_no_mutation_record.json',no_mut)

acceptance={**common,'schema':'stickbot.vnext_semantic_gate.m12_c4.acceptance_matrix.v1','checks':checks,'decision':'readiness_design_pass_no_apply' if status==PASS else 'blocked','c4_kernel_required':True,'optional_model_prose_policy':model_policy,'fixture_plan_summary':{'case_count':fixture_plan['case_count'],'expected_counts':fixture_plan['expected_counts']},'source_hashes':source_hashes}
wj('c4_acceptance_matrix.json',acceptance)

review=f'''# M12-C4 Readiness Design / Bounded Next-Step Proposal Drafting

Final status: `{status}`

Purpose: no-apply readiness design for bounded next-step proposal drafting.

Core principle: **proposal drafting is not action authority**.

Verified prior state:

- C1 accepted boundary preserved: `{checks['c1_scope_preserved']}` — bounded artifact status Q&A only.
- C2 accepted boundary preserved: `{checks['c2_scope_preserved']}` — deterministic single-artifact runbook guidance only.
- C3 accepted boundary preserved: `{checks['c3_scope_preserved']}` — deterministic two-artifact consistency comparison only.
- Latest C3 status: `{c3.get('status')}`.
- C4 production started: `False`.
- Failed gates: `{failed}`.
- First failure: `{first}`.
- Provider/model authoritative calls prior: `0`.
- Direct provider bypass prior: `0`.
- Rollback ready: `{checks['rollback_ready']}`.
- M11 frozen baseline preserved: `{checks['m11_frozen_baseline_preserved']}`.
- Mutation sentinels clean: `{checks['mutation_sentinels_clean']}`.
- Cache/artifact-memory/global promotion: `False`.
- Runtime/Gateway/config/live-route/fallback/memory-route mutation: `False`.
- External action execution: `False`.

Design outputs:

- C4 scope/non-scope defined.
- Approved evidence sources defined: C1 status facts, C2 guidance outputs, C3 comparison outputs, and explicitly approved artifacts/source rows.
- Source authority rules defined.
- Proposal output contract defined: PROPOSAL / HOLD / REJECT with proposal_steps, rationale, cited_source_refs, assumptions, uncertainties, required_owner_review, non_execution_notice, disposition, and hold_reason when fail-closed.
- Fail-closed policy defined.
- Deterministic C4 proposal kernel required before readiness exercise/canary/production.
- Optional model prose policy defined: allowed only as non-authoritative rendering after deterministic contract validation; never authority.
- Fixture plan defined: `{fixture_plan['case_count']}` cases with expected `{fixture_plan['expected_counts']}`.

This packet does not start C4 production, enable cache, promote artifact-memory/global Semantic Gate, expand runtime authority, execute external actions, or mutate Gateway/config/routes/fallback/memory/runtime authority.
'''
wt('M12_C4_BOUNDED_NEXT_STEP_PROPOSAL_DRAFTING_READINESS_DESIGN.md',review)

missing=[]
status_obj={**common,'schema':'stickbot.vnext_semantic_gate.m12_c4.status.v1','required_files':REQ,'required_files_missing':missing,'pass_condition_checks':checks,'accepted_prior_boundaries':{'c1':'bounded_artifact_status_qa','c2':'single_artifact_runbook_guidance','c3':'two_artifact_consistency_comparison'},'c4_readiness_design_created':status==PASS,'c4_production_started':False,'c4_canary_started':False,'c4_kernel_required':True,'kernel_implemented':False,'optional_model_prose_allowed_non_authoritative_only':True,'provider_model_authoritative_calls_allowed':0,'provider_model_authoritative_calls_observed':0,'direct_provider_bypass_count':0,'cache_enabled':False,'artifact_memory_promoted':False,'global_semantic_gate_promoted':False,'broad_production_expansion_applied':False,'runtime_authority_mutated':False,'gateway_config_mutated':False,'live_route_mutated':False,'fallback_chain_mutated':False,'memory_route_mutated':False,'external_action_executed':False,'rollback_ready':checks['rollback_ready'],'m11_frozen_baseline_preserved':checks['m11_frozen_baseline_preserved'],'m12_c1_frozen_boundary_preserved':checks['c1_scope_preserved'],'m12_c2_frozen_boundary_preserved':checks['c2_scope_preserved'],'m12_c3_frozen_boundary_preserved':checks['c3_scope_preserved'],'source_hashes':source_hashes}
wj('status.json',status_obj)
summary_keys=['schema','status','artifact_dir','failed_gates','first_failure','c4_readiness_design_created','c4_production_started','c4_canary_started','c4_kernel_required','kernel_implemented','optional_model_prose_allowed_non_authoritative_only','provider_model_authoritative_calls_observed','direct_provider_bypass_count','cache_enabled','artifact_memory_promoted','global_semantic_gate_promoted','broad_production_expansion_applied','runtime_authority_mutated','external_action_executed','rollback_ready','m11_frozen_baseline_preserved','m12_c1_frozen_boundary_preserved','m12_c2_frozen_boundary_preserved','m12_c3_frozen_boundary_preserved']
summary={k:status_obj[k] for k in summary_keys}; summary['schema']='stickbot.vnext_semantic_gate.m12_c4.summary.v1'; summary['next_recommended_action']='If approved, implement deterministic C4 proposal kernel (C4K) before any C4 exercise/canary/production.' if status==PASS else 'C4 readiness design blocked; triage first failure.'
wj('summary.json',summary)
missing=[n for n in REQ if not (ART/n).exists()]
if missing and 'required_files_missing' not in failed:
    failed.append('required_files_missing'); status=BLOCKED; first=first or 'required_files_missing'; status_obj.update(status=status,failed_gates=failed,first_failure=first,required_files_missing=missing,c4_readiness_design_created=False); summary.update(status=status,failed_gates=failed,first_failure=first,c4_readiness_design_created=False,next_recommended_action='C4 readiness design blocked; triage first failure.'); wj('status.json',status_obj); wj('summary.json',summary)
else:
    status_obj['required_files_missing']=missing; wj('status.json',status_obj)
files=sorted(p for p in ART.iterdir() if p.is_file() and p.name!='evidence_manifest.json')
wj('evidence_manifest.json',{'schema':'stickbot.vnext_semantic_gate.m12_c4.evidence_manifest.v1','status':status,'artifact_dir':rel(ART),'created_utc':created,'files':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in files],'source_hashes':source_hashes,'self_hash_policy':'evidence_manifest.json excluded from its own file list'})
print(json.dumps({'status':status,'failed_gates':failed,'first_failure':first,'required_files_missing':missing,'status_sha256':sha(ART/'status.json'),'evidence_manifest_sha256':sha(ART/'evidence_manifest.json')},indent=2,sort_keys=True))
if status!=PASS or missing: raise SystemExit(1)
