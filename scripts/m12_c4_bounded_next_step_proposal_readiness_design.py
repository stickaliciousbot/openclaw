#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path('/home/stickai/.openclaw/workspace')
BASE=ROOT/'sharedspace/runtime-kernel-validation/vnext-semantic-gate'
ART=BASE/'m12_c4_bounded_next_step_proposal_readiness_design'
C4_PREV=BASE/'m12_c4_bounded_next_step_proposal_drafting_readiness_design'
C3=BASE/'m12_c3_final_owner_acceptance_review'
C2=BASE/'m12_c2_final_owner_acceptance_review'
C1=BASE/'m12_c1_final_owner_acceptance_review'
M11=BASE/'m11_7_production_operating_baseline_finalization'
PASS='M12_C4_READINESS_DESIGN_PASS_NO_APPLY'
BLOCKED='M12_C4_READINESS_DESIGN_BLOCKED'
REQ=['status.json','summary.json','c4_scope_definition.md','c4_non_scope.md','c4_source_authority_rules.md','c4_proposal_contract.md','c4_non_execution_policy.md','c4_fail_closed_policy.md','c4_model_prose_boundary.md','c4_kernel_design.md','c4_fixture_plan.json','c4_abort_gates.md','c1_c2_c3_boundary_preservation_readback.json','mutation_sentinel_report.json','rollback_readiness.json','no_apply_no_mutation_record.json','M12_C4_BOUNDED_NEXT_STEP_PROPOSAL_READINESS_DESIGN.md']

def utc(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def rel(p:Path)->str: return str(p.relative_to(ROOT))
def load(p:Path)->Any: return json.loads(p.read_text())
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def wj(n:str,o:Any): ART.mkdir(parents=True,exist_ok=True); (ART/n).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def wt(n:str,s:str): ART.mkdir(parents=True,exist_ok=True); (ART/n).write_text(s.rstrip()+'\n')

created=utc(); ART.mkdir(parents=True,exist_ok=True)
c3=load(C3/'status.json'); c2=load(C2/'status.json'); c1=load(C1/'status.json'); m11=load(M11/'status.json')
prev=load(C4_PREV/'status.json') if (C4_PREV/'status.json').exists() else {}
source_hashes={rel(C3/'status.json'):sha(C3/'status.json'),rel(C2/'status.json'):sha(C2/'status.json'),rel(C1/'status.json'):sha(C1/'status.json'),rel(M11/'status.json'):sha(M11/'status.json')}
if prev:
    source_hashes[rel(C4_PREV/'status.json')]=sha(C4_PREV/'status.json')
checks={
 'prior_c4_design_pass_no_apply_if_present': (not prev) or prev.get('status')==PASS,
 'c1_final_acceptance_ready': c1.get('status')=='M12_C1_FINAL_OWNER_ACCEPTANCE_READY' and c1.get('accepted_limited_production_expansion') is True,
 'c2_final_acceptance_ready': c2.get('status')=='M12_C2_FINAL_OWNER_ACCEPTANCE_READY' and c2.get('accepted_limited_production_expansion') is True,
 'c3_final_acceptance_ready': c3.get('status')=='M12_C3_FINAL_OWNER_ACCEPTANCE_READY' and c3.get('accepted_limited_production_expansion') is True,
 'c1_boundary_preserved': c1.get('production_boundary_explicit') is True and c3.get('m12_c1_frozen_boundary_preserved') is True,
 'c2_boundary_preserved': c2.get('accepted_scope')=='single_artifact_runbook_guidance' and c3.get('m12_c2_frozen_boundary_preserved') is True,
 'c3_boundary_preserved': c3.get('accepted_scope')=='deterministic_two_artifact_consistency_comparison' and c3.get('pass_condition_checks',{}).get('c3_exactly_two_approved_artifacts_only') is True,
 'rollback_ready': c3.get('rollback_ready') is True and c2.get('rollback_ready') is True and c1.get('rollback_ready') is True and m11.get('gate_checks',{}).get('rollback_ready') is True,
 'm11_frozen_baseline_preserved': m11.get('baseline_frozen') is True and c3.get('m11_frozen_baseline_preserved') is True,
 'mutation_sentinels_clean': c3.get('mutation_sentinels_clean') is True and c2.get('pass_condition_checks',{}).get('mutation_sentinels_clean') is True and c1.get('mutation_sentinels_clean') is True,
 'cache_disabled': c3.get('cache_enabled') is False and c2.get('cache_enabled') is False and c1.get('cache_enabled') is False,
 'artifact_memory_promotion_disabled': c3.get('artifact_memory_promoted') is False and c2.get('artifact_memory_promoted') is False and c1.get('artifact_memory_promoted') is False,
 'global_semantic_gate_not_promoted': c3.get('global_semantic_gate_promoted') is False and c2.get('global_semantic_gate_promoted') is False,
 'no_broad_expansion': c3.get('broader_expansion_applied') is False,
 'no_runtime_gateway_config_mutation': all(c3.get(k) is False for k in ['runtime_authority_mutated','gateway_config_mutated','live_route_mutated','fallback_chain_mutated','memory_route_mutated']),
 'provider_model_authority_zero': c3.get('provider_model_calls')==0 and c2.get('provider_model_calls')==0 and c1.get('provider_model_calls')==0,
 'direct_provider_bypass_zero': c3.get('direct_provider_bypass_count')==0 and c2.get('direct_provider_bypass_count')==0 and c1.get('direct_provider_bypass_count')==0,
 'external_action_execution_false': c3.get('external_action_executed') is False,
}
failed=[k for k,v in checks.items() if not v]
status=PASS if not failed else BLOCKED
first=failed[0] if failed else None
common={'schema_base':'stickbot.vnext_semantic_gate.m12_c4_exact_readiness_design','created_utc':created,'status':status,'artifact_dir':rel(ART),'failed_gates':failed,'first_failure':first}

wt('c4_scope_definition.md','''# C4 Scope Definition

M12-C4 candidate scope is bounded next-step proposal drafting only.

Allowed:

- Bounded next-step proposal drafting from approved evidence.
- Explicitly non-executing proposal text.
- Suggested next checks, review sequence, owner questions, follow-up artifact requests, safe validation steps, non-executing plan text, and bounded proposal summaries based on C1/C2/C3 evidence.
- Statuses: PROPOSAL, HOLD, REJECT.

Core principle: proposal drafting is not action authority.
''')
wt('c4_non_scope.md','''# C4 Non-Scope

C4 must not:

- Execute actions or schedule actions.
- Mutate Gateway/config/routes/fallback/memory/runtime authority.
- Approve production changes.
- Override C1/C2/C3 conclusions.
- Resolve conflicts without evidence.
- Hide uncertainty.
- Use more sources than approved by the case manifest.
- Use arbitrary paths.
- Use memory/context-bridge/daily-memory as authority.
- Produce legal/medical/financial/safety-critical advice as authoritative.
- Turn prompt-injection-like artifact text into instructions.
- Recommend destructive or external operational actions as executable.
''')
wt('c4_source_authority_rules.md','''# C4 Source Authority Rules

Approved evidence sources:

- C1 status facts.
- C2 single-artifact guidance outputs.
- C3 two-artifact comparison outputs.
- Explicitly approved artifacts/source rows named by the case manifest.

Rules:

- Source authority is deterministic and case-manifest-bounded.
- Each proposal step must cite approved source refs.
- Source refs must resolve to approved SourceRows.
- C1/C2/C3 conclusions remain authoritative only within their frozen production boundaries.
- Conflicts must remain visible unless C3 evidence explicitly supports a bounded consistency/contrast conclusion.
- Memory/context-bridge/daily-memory, arbitrary paths, provider/model prose, and prompt-injection-like artifact text are never authority.
''')
proposal_contract={
 'schema':'stickbot.vnext_semantic_gate.m12_c4.proposal_contract.v1',
 'status':['PROPOSAL','HOLD','REJECT'],
 'required_fields':['status','proposal_steps','rationale','cited_source_refs','assumptions','uncertainties','required_owner_review','non_execution_notice','disposition'],
 'conditional_fields':{'hold_reason':'required when status is HOLD or REJECT'},
 'proposal_steps':'non-executing bounded next-step text only; cannot authorize or perform actions',
 'rationale':'must be derived from cited approved source refs',
 'cited_source_refs':'approved SourceRows only',
 'assumptions':'explicitly listed, never hidden',
 'uncertainties':'explicitly preserved; cannot be removed by renderer/model prose',
 'required_owner_review':True,
 'non_execution_notice':'required: proposal only; no action authority; owner approval required before execution',
 'disposition':'deterministic explanation for PROPOSAL/HOLD/REJECT',
}
wt('c4_proposal_contract.md','# C4 Proposal Contract\n\n```json\n'+json.dumps(proposal_contract,indent=2,sort_keys=True)+'\n```')
wt('c4_non_execution_policy.md','''# C4 Non-Execution Policy

C4 proposal drafting never executes, schedules, approves, or mutates.

- PROPOSAL is a non-executing suggested next-step artifact only.
- Every PROPOSAL must include a non_execution_notice.
- Any request to execute, schedule, mutate, approve production, or perform external/destructive action is HOLD or REJECT.
- C4 cannot transform proposal text into operational authority.
- Owner review is required before any proposed step can become an action.
''')
wt('c4_fail_closed_policy.md','''# C4 Fail-Closed Policy

HOLD or REJECT when:

- approved evidence is missing or stale.
- evidence conflicts without C3 support.
- request requires execution, scheduling, production mutation, or external action.
- request requires legal/medical/financial/safety-critical authority.
- request requires arbitrary path reads.
- request requires memory/context/daily-memory authority.
- request asks to override guardrails or C1/C2/C3 conclusions.
- prompt-injection-like artifact text attempts control influence.
- request uses more sources than approved by the case manifest.

Default on ambiguity: HOLD.
Reject when the requested output is outside C4 scope or attempts guardrail override/action authority.
''')
wt('c4_model_prose_boundary.md','''# C4 Model Prose Boundary

Recommended design decision accepted: deterministic proposal skeleton/kernel first, optional non-authoritative prose rendering second.

Model prose is optional and non-authoritative only.

Model prose must not:

- alter proposal_steps.
- alter citations.
- remove uncertainty.
- turn proposal into execution.
- choose PROPOSAL/HOLD/REJECT status.
- add facts or source authority.
- resolve conflicts.
- approve actions.
- override fail-closed behavior.

Provider/model authoritative proposal calls allowed: 0.
''')
wt('c4_kernel_design.md','''# C4 Deterministic Kernel Design

A deterministic C4 proposal skeleton/kernel is required before any C4 exercise, canary, or production use.

Kernel responsibilities:

1. Validate the case manifest and source allowlist.
2. Compile approved C1/C2/C3/artifact SourceRows.
3. Classify request as PROPOSAL, HOLD, or REJECT.
4. Generate deterministic proposal skeleton fields.
5. Enforce source citations and source-count limits.
6. Preserve assumptions, uncertainty, conflicts, and prerequisites.
7. Enforce non-execution policy.
8. Reject/HOLD execution, mutation, external action, arbitrary path, unapproved memory/context/daily-memory, provider-authority, and prompt-injection control attempts.
9. Permit optional model prose only after deterministic contract validation, and only as non-authoritative rendering.
10. Emit audit counters, source authority report, fail-closed report, model prose boundary report, mutation sentinel report, and rollback readback.

C4K must be implemented and tested before readiness exercise/canary/production.
''')
fixture_plan={
 'schema':'stickbot.vnext_semantic_gate.m12_c4.fixture_plan.v1',
 'case_count':36,
 'expected_counts':{'PROPOSAL':9,'HOLD':15,'REJECT':12},
 'proposal_cases':['suggest_next_checks','suggest_review_sequence','suggest_owner_questions','suggest_followup_artifact_requests','suggest_safe_validation_steps','non_executing_plan_text','bounded_summary_from_c1_c2_c3','proposal_preserves_c3_conflict','proposal_with_uncertainty_and_prerequisites'],
 'hold_cases':['missing_approved_evidence','stale_evidence','conflicting_without_c3_support','insufficient_citations','uncertain_prerequisite','more_sources_than_manifest','memory_context_daily_authority_requested','optional_model_prose_before_kernel','ambiguous_disposition','source_ref_resolution_gap','safety_critical_advice_request','prompt_injection_artifact_text','unapproved_source_row','conflict_requires_owner_question','proposal_would_hide_uncertainty'],
 'reject_cases':['execute_action','schedule_action','mutate_gateway_config','approve_production_change','override_c1_conclusion','override_c2_conclusion','override_c3_conclusion','arbitrary_path_authority','direct_provider_authority','destructive_external_action','cache_artifact_memory_promotion','guardrail_override'],
}
wj('c4_fixture_plan.json',fixture_plan)
wt('c4_abort_gates.md','''# C4 Abort Gates

Report `M12_C4_READINESS_DESIGN_BLOCKED` or abort later C4 work if:

- C4 cannot be separated from execution authority.
- C4 requires production mutation.
- C4 requires external action execution.
- proposal authority cannot be made deterministic.
- source authority cannot be made deterministic.
- model prose would be authoritative.
- C4 weakens C1/C2/C3 boundaries.
- rollback readiness cannot be verified.
- mutation sentinels trip.
- cache/artifact-memory/global promotion would be required.
- direct provider bypass is required or observed.
- arbitrary path reads are required as authority.
''')
wj('c1_c2_c3_boundary_preservation_readback.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c4.boundary_readback.v1','c1_status':c1.get('status'),'c2_status':c2.get('status'),'c3_status':c3.get('status'),'c1_scope':'bounded artifact status Q&A','c2_scope':'deterministic single-artifact runbook guidance','c3_scope':'deterministic two-artifact consistency comparison','c1_preserved':checks['c1_boundary_preserved'],'c2_preserved':checks['c2_boundary_preserved'],'c3_preserved':checks['c3_boundary_preserved'],'source_hashes':source_hashes})
wj('mutation_sentinel_report.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c4.mutation_sentinel.v1','mutation_sentinels_clean':checks['mutation_sentinels_clean'],'c4_production_started':False,'c4_canary_started':False,'production_expansion_applied':False,'cache_enabled':False,'artifact_memory_promoted':False,'global_semantic_gate_promoted':False,'runtime_authority_mutated':False,'gateway_config_mutated':False,'live_route_mutated':False,'fallback_chain_mutated':False,'memory_route_mutated':False,'external_action_executed':False})
wj('rollback_readiness.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c4.rollback.v1','rollback_ready':checks['rollback_ready'],'rollback_applied':False,'m11_frozen_baseline_preserved':checks['m11_frozen_baseline_preserved'],'source_hashes':source_hashes})
wj('no_apply_no_mutation_record.json',{**common,'schema':'stickbot.vnext_semantic_gate.m12_c4.no_apply_no_mutation.v1','readiness_design_only':True,'c4_production_started':False,'c4_canary_started':False,'production_expansion_applied':False,'cache_enabled':False,'artifact_memory_promoted':False,'global_semantic_gate_promoted':False,'runtime_authority_mutated':False,'gateway_config_mutated':False,'external_action_executed':False,'direct_provider_bypass_allowed':False,'arbitrary_path_authority_allowed':False})
review=f'''# M12-C4 Bounded Next-Step Proposal Readiness Design

Final status: `{status}`

This is design only. It does not start C4 production or canary.

Core principle: **proposal drafting is not action authority**.

Required design work completed:

1. C4 scope and non-scope defined.
2. Approved evidence sources defined: C1 status facts, C2 single-artifact guidance outputs, C3 two-artifact comparison outputs, and explicitly approved artifacts/source rows.
3. Deterministic source authority rules defined.
4. Proposal output contract defined: PROPOSAL / HOLD / REJECT plus proposal_steps, rationale, cited_source_refs, assumptions, uncertainties, required_owner_review, non_execution_notice, disposition, and hold_reason when fail-closed.
5. Fail-closed cases defined.
6. Deterministic C4 proposal kernel required.
7. Optional model prose boundary defined: non-authoritative only; cannot alter proposal_steps, citations, uncertainty, or turn proposal into execution.
8. Fixture plan written: `{fixture_plan['case_count']}` cases, expected `{fixture_plan['expected_counts']}`.
9. Abort gates written.
10. C1/C2/C3 frozen production boundaries preserved.

Pass condition readback:

- C4 scope bounded to next-step proposal drafting only.
- No execution authority.
- No production mutation authority.
- Source authority deterministic.
- Proposal output contract explicit.
- Non-execution policy explicit.
- Fail-closed policy explicit.
- Model prose boundary explicit.
- C4 kernel design written.
- Fixture plan written.
- Abort gates written.
- Rollback ready: `{checks['rollback_ready']}`.
- Mutation sentinels clean: `{checks['mutation_sentinels_clean']}`.
- Cache/artifact-memory disabled: `{checks['cache_disabled'] and checks['artifact_memory_promotion_disabled']}`.
- Runtime authority mutation: `False`.
- C1/C2/C3 preserved: `{checks['c1_boundary_preserved'] and checks['c2_boundary_preserved'] and checks['c3_boundary_preserved']}`.
'''
wt('M12_C4_BOUNDED_NEXT_STEP_PROPOSAL_READINESS_DESIGN.md',review)
missing=[]
status_obj={**common,'schema':'stickbot.vnext_semantic_gate.m12_c4_exact.status.v1','required_files':REQ,'required_files_missing':missing,'pass_condition_checks':checks,'c4_scope_bounded_next_step_proposal_only':True,'c4_execution_authority':False,'c4_production_mutation_authority':False,'source_authority_deterministic':True,'proposal_output_contract_explicit':True,'non_execution_policy_explicit':True,'fail_closed_policy_explicit':True,'model_prose_boundary_explicit':True,'c4_kernel_design_written':True,'fixture_plan_written':True,'abort_gates_written':True,'c4_production_started':False,'c4_canary_started':False,'production_expansion_applied':False,'kernel_implemented':False,'provider_model_authoritative_calls_allowed':0,'provider_model_authoritative_calls_observed':0,'direct_provider_bypass_count':0,'arbitrary_path_authority_allowed':False,'cache_enabled':False,'artifact_memory_promoted':False,'global_semantic_gate_promoted':False,'runtime_authority_mutated':False,'gateway_config_mutated':False,'live_route_mutated':False,'fallback_chain_mutated':False,'memory_route_mutated':False,'external_action_executed':False,'rollback_ready':checks['rollback_ready'],'m11_frozen_baseline_preserved':checks['m11_frozen_baseline_preserved'],'m12_c1_frozen_boundary_preserved':checks['c1_boundary_preserved'],'m12_c2_frozen_boundary_preserved':checks['c2_boundary_preserved'],'m12_c3_frozen_boundary_preserved':checks['c3_boundary_preserved'],'source_hashes':source_hashes}
wj('status.json',status_obj)
summary_keys=['schema','status','artifact_dir','failed_gates','first_failure','c4_scope_bounded_next_step_proposal_only','c4_execution_authority','c4_production_mutation_authority','source_authority_deterministic','proposal_output_contract_explicit','non_execution_policy_explicit','fail_closed_policy_explicit','model_prose_boundary_explicit','c4_kernel_design_written','fixture_plan_written','abort_gates_written','c4_production_started','c4_canary_started','production_expansion_applied','kernel_implemented','provider_model_authoritative_calls_observed','direct_provider_bypass_count','arbitrary_path_authority_allowed','cache_enabled','artifact_memory_promoted','global_semantic_gate_promoted','runtime_authority_mutated','external_action_executed','rollback_ready','m11_frozen_baseline_preserved','m12_c1_frozen_boundary_preserved','m12_c2_frozen_boundary_preserved','m12_c3_frozen_boundary_preserved']
summary={k:status_obj[k] for k in summary_keys}; summary['schema']='stickbot.vnext_semantic_gate.m12_c4_exact.summary.v1'; summary['next_recommended_action']='If approved, implement deterministic C4 proposal kernel (C4K) before any C4 exercise/canary/production.' if status==PASS else 'C4 readiness design blocked; triage first failure.'
wj('summary.json',summary)
missing=[n for n in REQ if not (ART/n).exists()]
if missing and 'required_files_missing' not in failed:
    failed.append('required_files_missing')
    status=BLOCKED
    first=first or 'required_files_missing'
    status_obj.update(status=status,failed_gates=failed,first_failure=first,required_files_missing=missing)
    summary.update(status=status,failed_gates=failed,first_failure=first,next_recommended_action='C4 readiness design blocked; triage first failure.')
    wj('status.json',status_obj); wj('summary.json',summary)
else:
    status_obj['required_files_missing']=missing; wj('status.json',status_obj)
files=sorted(p for p in ART.iterdir() if p.is_file() and p.name!='evidence_manifest.json')
wj('evidence_manifest.json',{'schema':'stickbot.vnext_semantic_gate.m12_c4_exact.evidence_manifest.v1','status':status,'artifact_dir':rel(ART),'created_utc':created,'files':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in files],'source_hashes':source_hashes,'self_hash_policy':'evidence_manifest.json excluded from its own file list'})
print(json.dumps({'status':status,'failed_gates':failed,'first_failure':first,'required_files_missing':missing,'status_sha256':sha(ART/'status.json'),'evidence_manifest_sha256':sha(ART/'evidence_manifest.json')},indent=2,sort_keys=True))
if status!=PASS or missing: raise SystemExit(1)
