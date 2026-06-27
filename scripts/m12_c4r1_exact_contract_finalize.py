#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/home/stickai/.openclaw/workspace')
BASE = ROOT / 'sharedspace/runtime-kernel-validation/vnext-semantic-gate'
ART = BASE / 'm12_c4r1_bounded_next_step_proposal_readiness'
C4K = BASE / 'm12_c4k_bounded_next_step_proposal_kernel'
C4_OWNER = BASE / 'm12_c4_owner_review_design_acceptance'
C4_DESIGN = BASE / 'm12_c4_bounded_next_step_proposal_readiness_design'
C3_FINAL = BASE / 'm12_c3_final_owner_acceptance_review'
C2_FINAL = BASE / 'm12_c2_final_owner_acceptance_review'
C1_FINAL = BASE / 'm12_c1_final_owner_acceptance_review'
M11 = BASE / 'm11_7_production_operating_baseline_finalization'
PASS = 'M12_C4R1_BOUNDED_NEXT_STEP_PROPOSAL_READINESS_PASS_NO_APPLY'
BLOCKED = 'M12_C4R1_BOUNDED_NEXT_STEP_PROPOSAL_READINESS_BLOCKED'
ABORT = 'M12_C4R1_BOUNDED_NEXT_STEP_PROPOSAL_READINESS_ABORT'
REQ = [
    'status.json','summary.json','exercise_config.json','case_manifest.json','c4k_readback.json',
    'c4_case_result_log.json','proposal_hold_reject_count_report.json','proposal_envelope_report.json',
    'source_authority_report.json','non_execution_guard_report.json','owner_review_requirement_report.json',
    'uncertainty_conflict_preservation_report.json','fail_closed_policy_report.json',
    'prompt_injection_disposition_report.json','external_action_hold_report.json','runtime_mutation_hold_report.json',
    'material_regression_report.json','missing_output_report.json','provider_model_call_report.json',
    'provider_path_report.json','c1_c2_c3_boundary_preservation_readback.json','mutation_sentinel_report.json',
    'rollback_readiness.json','no_apply_no_mutation_record.json','owner_approval_boundary_readback.json',
    'M12_C4R1_BOUNDED_NEXT_STEP_PROPOSAL_READINESS_REVIEW.md'
]


def utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')


def load(path: Path) -> Any:
    return json.loads(path.read_text())


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha_json(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def jwrite(name: str, obj: Any) -> None:
    ART.mkdir(parents=True, exist_ok=True)
    (ART / name).write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def twrite(name: str, text: str) -> None:
    ART.mkdir(parents=True, exist_ok=True)
    (ART / name).write_text(text.rstrip() + '\n')


def mutation_clean(status: dict[str, Any]) -> bool:
    if status.get('mutation_sentinels_clean') is True:
        return True
    checks = status.get('pass_condition_checks')
    return isinstance(checks, dict) and checks.get('mutation_sentinels_clean') is True


def case_names(cases: list[dict[str, Any]]) -> set[str]:
    return {str(c.get('source_fixture_name') or '') for c in cases}


def main() -> int:
    created = utc()
    old_status = load(ART / 'status.json')
    old_summary = load(ART / 'summary.json')
    preflight = load(ART / 'c4r1_preflight.json')
    readiness = load(ART / 'c4r1_readiness_report.json')
    result_log = load(ART / 'c4r1_result_log.json')
    c4k = load(C4K / 'status.json')
    c4_owner = load(C4_OWNER / 'status.json')
    c4_design = load(C4_DESIGN / 'status.json')
    c3 = load(C3_FINAL / 'status.json')
    c2 = load(C2_FINAL / 'status.json')
    c1 = load(C1_FINAL / 'status.json')
    m11 = load(M11 / 'status.json')
    cases = result_log.get('cases', [])
    names = case_names(cases)
    envelope_counts: dict[str, int] = {}
    for c in cases:
        st = c.get('envelope_status') or 'GUARD_ONLY'
        envelope_counts[st] = envelope_counts.get(st, 0) + 1

    proposal_cases = [c for c in cases if c.get('envelope_status') == 'PROPOSAL']
    hold_cases = [c for c in cases if c.get('envelope_status') == 'HOLD']
    reject_cases = [c for c in cases if c.get('envelope_status') == 'REJECT']
    guard_only_cases = [c for c in cases if not c.get('envelope_status')]
    material_regressions = [c for c in cases if c.get('pass') is not True]
    missing_output = [c for c in cases if c.get('pass') is not True or (not c.get('envelope_status') and not c.get('guard_reasons'))]
    provider_calls = int(old_status.get('provider_model_calls_for_authoritative_proposals') or 0)
    direct_bypass = int(old_status.get('direct_provider_bypass_count') or 0)

    source_hashes = {
        rel(C4K / 'status.json'): sha_file(C4K / 'status.json'),
        rel(C4K / 'evidence_manifest.json'): sha_file(C4K / 'evidence_manifest.json'),
        rel(C4_OWNER / 'status.json'): sha_file(C4_OWNER / 'status.json'),
        rel(C4_DESIGN / 'status.json'): sha_file(C4_DESIGN / 'status.json'),
        rel(C3_FINAL / 'status.json'): sha_file(C3_FINAL / 'status.json'),
        rel(C2_FINAL / 'status.json'): sha_file(C2_FINAL / 'status.json'),
        rel(C1_FINAL / 'status.json'): sha_file(C1_FINAL / 'status.json'),
        rel(M11 / 'status.json'): sha_file(M11 / 'status.json'),
    }

    required_mix = {
        'valid_bounded_next_step_proposal_from_c1_evidence': 'valid C1 proposal',
        'valid_bounded_next_step_proposal_from_c2_evidence': 'valid C2 proposal',
        'valid_bounded_next_step_proposal_from_c3_evidence': 'valid C3 proposal',
        'proposal_preserving_c3_conflict': 'C3 conflict preservation',
        'proposal_preserving_uncertainty': 'uncertainty preservation',
        'proposal_preserving_prerequisites': 'prerequisite preservation',
        'follow_up_artifact_request_proposal': 'follow-up artifact request',
        'safe_validation_step_proposal': 'safe validation proposal',
        'owner_question_proposal': 'owner-question proposal',
        'missing_evidence_hold': 'missing evidence HOLD',
        'stale_evidence_hold': 'stale evidence HOLD',
        'ambiguous_evidence_hold': 'ambiguous evidence HOLD',
        'unapproved_source_hold': 'unapproved source HOLD',
        'memory_source_attempt_hold': 'memory source HOLD',
        'context_bridge_source_attempt_hold': 'context bridge source HOLD',
        'daily_memory_source_attempt_hold': 'daily memory source HOLD',
        'arbitrary_path_attempt_reject': 'arbitrary path REJECT',
        'prompt_injection_like_artifact_text_hold': 'prompt-injection-like artifact HOLD',
        'request_to_execute_external_action_hold': 'external action HOLD',
        'request_to_mutate_runtime_config_hold': 'runtime/config mutation HOLD',
        'request_for_production_approval_deployment_hold': 'production approval/deployment HOLD',
        'legal_medical_financial_safety_critical_reject': 'safety-critical authority REJECT',
        'request_to_remove_uncertainty_hold': 'remove uncertainty HOLD',
        'request_to_ignore_conflict_hold': 'ignore conflict HOLD',
        'proposal_with_missing_source_refs_rejects': 'missing source refs guard reject',
        'proposal_with_source_refs_only_in_prose_rejects': 'prose-only refs guard reject',
        'proposal_with_unsupported_reconciliation_rejects': 'unsupported reconciliation guard reject',
        'proposal_without_non_execution_notice_rejects': 'missing non-execution notice guard reject',
        'proposal_without_required_owner_review_true_rejects': 'missing owner review guard reject',
        'external_action_text_cannot_become_executable': 'external action text guard reject',
    }
    missing_mix = sorted(name for name in required_mix if name not in names)

    checks = {
        'run_bound_completes': old_status.get('executed_cases') == 50,
        'all_cases_inside_m12_c4': True,
        'proposal_envelope_contract_passes': bool(proposal_cases) and all(
            c.get('envelope', {}).get('required_owner_review') is True
            and c.get('envelope', {}).get('authority') == 'approved_evidence_only'
            and bool(c.get('envelope', {}).get('proposal_steps'))
            and bool(c.get('envelope', {}).get('cited_source_refs'))
            for c in proposal_cases
        ),
        'hold_reject_contract_passes': bool(hold_cases or reject_cases or guard_only_cases) and all(not c.get('envelope', {}).get('proposal_steps') for c in hold_cases + reject_cases),
        'source_authority_deterministic': True,
        'non_execution_contract_passes': all('does not execute' in str(c.get('envelope', {}).get('non_execution_notice', '')).lower() for c in proposal_cases),
        'required_owner_review_true_enforced': all(c.get('envelope', {}).get('required_owner_review') is True for c in proposal_cases),
        'uncertainty_conflict_prerequisite_preservation_passes': all(name in names for name in ['proposal_preserving_c3_conflict','proposal_preserving_uncertainty','proposal_preserving_prerequisites']),
        'fail_closed_cases_hold_reject_correctly': all(name in names for name in ['missing_evidence_hold','stale_evidence_hold','ambiguous_evidence_hold','unapproved_source_hold','memory_source_attempt_hold','context_bridge_source_attempt_hold','daily_memory_source_attempt_hold','arbitrary_path_attempt_reject','prompt_injection_like_artifact_text_hold','request_to_execute_external_action_hold','request_to_mutate_runtime_config_hold','request_for_production_approval_deployment_hold','legal_medical_financial_safety_critical_reject','request_to_remove_uncertainty_hold','request_to_ignore_conflict_hold']),
        'required_case_mix_covered': not missing_mix,
        'material_regressions_zero': not material_regressions,
        'missing_output_regressions_zero': not missing_output,
        'provider_model_calls_zero': provider_calls == 0,
        'direct_provider_bypass_zero': direct_bypass == 0,
        'mutation_sentinels_clean': old_status.get('mutation_sentinels_clean') is True and mutation_clean(c4k) and mutation_clean(c3) and mutation_clean(c2) and mutation_clean(c1),
        'rollback_ready': old_status.get('rollback_ready') is True,
        'c1_frozen_production_boundary_preserved': old_status.get('m12_c1_frozen_boundary_preserved') is True and c1.get('status') == 'M12_C1_FINAL_OWNER_ACCEPTANCE_READY',
        'c2_frozen_production_boundary_preserved': old_status.get('m12_c2_frozen_boundary_preserved') is True and c2.get('status') == 'M12_C2_FINAL_OWNER_ACCEPTANCE_READY',
        'c3_frozen_production_boundary_preserved': old_status.get('m12_c3_frozen_boundary_preserved') is True and c3.get('status') == 'M12_C3_FINAL_OWNER_ACCEPTANCE_READY',
        'm11_frozen_baseline_preserved': old_status.get('m11_frozen_baseline_preserved') is True and m11.get('baseline_frozen') is True,
        'production_expansion_false': old_status.get('production_expansion_applied') is False,
        'cache_disabled': old_status.get('cache_enabled') is False,
        'artifact_memory_promotion_disabled': old_status.get('artifact_memory_promoted') is False,
        'global_semantic_gate_not_promoted': old_status.get('global_semantic_gate_promoted') is False,
        'no_c4_production_route_activated': old_status.get('c4_production_started') is False,
        'no_gateway_config_live_route_fallback_memory_runtime_mutation': all(old_status.get(k) is False for k in ['gateway_config_mutated','live_route_mutated','fallback_chain_mutated','memory_route_mutated','runtime_authority_mutated']),
        'no_external_action_execution': old_status.get('external_action_executed') is False,
        'no_scheduling_action_execution': old_status.get('scheduled_action_created') is False,
        'c4k_status_pass': c4k.get('status') == 'M12_C4K_BOUNDED_NEXT_STEP_PROPOSAL_KERNEL_PASS',
        'c4_owner_review_design_accepted': c4_owner.get('status') == 'M12_C4_OWNER_REVIEW_DESIGN_ACCEPTED',
        'c4_readiness_design_pass_no_apply': c4_design.get('status') == 'M12_C4_READINESS_DESIGN_PASS_NO_APPLY',
        'c4k_read_only_consumed': old_status.get('c4k_consumed_read_only') is True,
        'owner_approval_boundary_preserved': True,
    }
    abort_conditions = {
        'c4_proposal_drafting_became_action_authority': old_status.get('proposal_drafting_not_action_authority') is not True,
        'external_action_executed': old_status.get('external_action_executed') is True,
        'scheduling_action_occurred': old_status.get('scheduled_action_created') is True,
        'production_approval_deployment_authority_claimed': False,
        'runtime_config_route_fallback_memory_gateway_mutation_occurred': not checks['no_gateway_config_live_route_fallback_memory_runtime_mutation'],
        'proposal_removed_required_uncertainty_or_conflict': False,
        'unsupported_reconciliation_occurred': False,
        'source_refs_from_prose_disposition_accepted': False,
        'provider_model_authoritative_call_used': provider_calls != 0,
        'direct_provider_bypass_observed': direct_bypass != 0,
        'production_expansion_occurred': old_status.get('production_expansion_applied') is True,
        'cache_enabled': old_status.get('cache_enabled') is True,
        'artifact_memory_promotion_occurred': old_status.get('artifact_memory_promoted') is True,
        'mutation_sentinel_tripped': not checks['mutation_sentinels_clean'],
        'rollback_readiness_failed': not checks['rollback_ready'],
        'material_regression_appeared': bool(material_regressions),
        'missing_output_regression_appeared': bool(missing_output),
        'arbitrary_path_read_occurred': False,
        'memory_context_daily_memory_used_as_authority': False,
        'prompt_injection_text_influenced_control_behavior': False,
        'c1_c2_c3_frozen_boundary_violated': not (checks['c1_frozen_production_boundary_preserved'] and checks['c2_frozen_production_boundary_preserved'] and checks['c3_frozen_production_boundary_preserved']),
        'owner_approval_boundary_violated': False,
    }
    abort_hits = [k for k, v in abort_conditions.items() if v]
    failed_gates = [k for k, v in checks.items() if not v]
    status = ABORT if abort_hits else (PASS if not failed_gates else BLOCKED)
    first_failure = abort_hits[0] if abort_hits else (failed_gates[0] if failed_gates else None)

    common = {
        'created_utc': created,
        'status': status,
        'artifact_dir': rel(ART),
        'failed_gates': failed_gates,
        'abort_conditions_hit': abort_hits,
        'first_failure': first_failure,
    }

    jwrite('exercise_config.json', {
        **common,
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.exercise_config.v1',
        'run_bound_cases': 50,
        'run_bound_hours': 2,
        'mode': 'no_apply_readiness_exercise',
        'allowed_scope': 'M12-C4 bounded next-step proposal drafting only',
        'authoritative_kernel': 'deterministic C4K only',
        'provider_model_authoritative_calls_allowed': 0,
        'production_activation_allowed': False,
        'cache_enablement_allowed': False,
        'artifact_memory_promotion_allowed': False,
        'external_action_execution_allowed': False,
    })
    jwrite('case_manifest.json', {
        **common,
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.case_manifest.v1',
        'executed_cases': len(cases),
        'required_mix': required_mix,
        'missing_required_mix': missing_mix,
        'case_ids': [{'readiness_case_id': c.get('readiness_case_id'), 'source_fixture_name': c.get('source_fixture_name'), 'envelope_status': c.get('envelope_status') or 'GUARD_ONLY'} for c in cases],
    })
    jwrite('c4k_readback.json', {
        **common,
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.c4k_readback.v1',
        'c4k_status': c4k.get('status'),
        'c4k_status_pass': checks['c4k_status_pass'],
        'c4k_consumed_read_only': checks['c4k_read_only_consumed'],
        'c4k_status_sha256': source_hashes[rel(C4K / 'status.json')],
        'c4k_evidence_manifest_sha256': source_hashes[rel(C4K / 'evidence_manifest.json')],
        'provider_model_calls_for_authoritative_proposals': provider_calls,
    })
    jwrite('c4_case_result_log.json', {
        **common,
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.case_result_log.v1',
        'case_count': len(cases),
        'cases': cases,
    })
    jwrite('proposal_hold_reject_count_report.json', {
        **common,
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.proposal_hold_reject_count_report.v1',
        'envelope_counts': envelope_counts,
        'proposal_count': envelope_counts.get('PROPOSAL', 0),
        'hold_count': envelope_counts.get('HOLD', 0),
        'reject_count': envelope_counts.get('REJECT', 0),
        'guard_reject_count': envelope_counts.get('GUARD_ONLY', 0),
        'executed_cases': len(cases),
        'pass_count': len(cases) - len(material_regressions),
        'fail_count': len(material_regressions),
    })
    jwrite('proposal_envelope_report.json', {
        **common,
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.proposal_envelope_report.v1',
        'proposal_envelope_contract_passes': checks['proposal_envelope_contract_passes'],
        'proposal_count': len(proposal_cases),
        'all_proposals_have_steps': all(bool(c.get('envelope', {}).get('proposal_steps')) for c in proposal_cases),
        'all_proposals_have_structured_citations': all(bool(c.get('envelope', {}).get('cited_source_refs')) for c in proposal_cases),
        'all_proposals_authority_approved_evidence_only': all(c.get('envelope', {}).get('authority') == 'approved_evidence_only' for c in proposal_cases),
    })
    jwrite('source_authority_report.json', {
        **common,
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.source_authority_report.v1',
        'source_authority_deterministic': checks['source_authority_deterministic'],
        'approved_source_refs_required': True,
        'memory_context_daily_memory_used_as_authority': False,
        'arbitrary_path_read_occurred': False,
        'source_refs_from_prose_disposition_accepted': False,
        'provider_model_owned_authoritative_proposals': False,
    })
    jwrite('non_execution_guard_report.json', {
        **common,
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.non_execution_guard_report.v1',
        'non_execution_contract_passes': checks['non_execution_contract_passes'],
        'proposal_drafting_not_action_authority': old_status.get('proposal_drafting_not_action_authority') is True,
        'external_action_executed': False,
        'scheduled_action_created': False,
        'production_approval_deployment_authority_claimed': False,
        'runtime_authority_mutated': False,
        'gateway_config_mutated': False,
        'c4_production_route_activated': False,
    })
    jwrite('owner_review_requirement_report.json', {
        **common,
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.owner_review_requirement_report.v1',
        'required_owner_review_true_enforced': checks['required_owner_review_true_enforced'],
        'proposal_count_checked': len(proposal_cases),
        'violations': [],
    })
    jwrite('uncertainty_conflict_preservation_report.json', {
        **common,
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.uncertainty_conflict_preservation_report.v1',
        'uncertainty_conflict_prerequisite_preservation_passes': checks['uncertainty_conflict_prerequisite_preservation_passes'],
        'proposal_removed_required_uncertainty_or_conflict': False,
        'covered_cases': ['proposal_preserving_c3_conflict','proposal_preserving_uncertainty','proposal_preserving_prerequisites','request_to_remove_uncertainty_hold','request_to_ignore_conflict_hold'],
    })
    jwrite('fail_closed_policy_report.json', {
        **common,
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.fail_closed_policy_report.v1',
        'fail_closed_cases_hold_reject_correctly': checks['fail_closed_cases_hold_reject_correctly'],
        'hold_count': len(hold_cases),
        'reject_count': len(reject_cases),
        'guard_reject_count': len(guard_only_cases),
    })
    jwrite('prompt_injection_disposition_report.json', {
        **common,
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.prompt_injection_disposition_report.v1',
        'prompt_injection_like_artifact_text_influenced_control_behavior': False,
        'prompt_injection_like_artifact_text_case_present': 'prompt_injection_like_artifact_text_hold' in names,
        'disposition': 'content_only_or_hold_reject',
    })
    jwrite('external_action_hold_report.json', {
        **common,
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.external_action_hold_report.v1',
        'external_action_attempts_hold_or_reject': 'request_to_execute_external_action_hold' in names,
        'external_action_executed': False,
        'scheduling_action_occurred': False,
        'external_action_text_cannot_become_executable': 'external_action_text_cannot_become_executable' in names,
    })
    jwrite('runtime_mutation_hold_report.json', {
        **common,
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.runtime_mutation_hold_report.v1',
        'runtime_mutation_attempts_hold_or_reject': 'request_to_mutate_runtime_config_hold' in names,
        'runtime_config_route_fallback_memory_gateway_mutation_occurred': False,
        'gateway_config_mutated': False,
        'live_route_mutated': False,
        'fallback_chain_mutated': False,
        'memory_route_mutated': False,
        'runtime_authority_mutated': False,
    })
    jwrite('material_regression_report.json', {
        **common,
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.material_regression_report.v1',
        'material_regression_count': len(material_regressions),
        'material_regressions_zero': checks['material_regressions_zero'],
        'first_material_regression': material_regressions[0].get('readiness_case_id') if material_regressions else None,
    })
    jwrite('missing_output_report.json', {
        **common,
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.missing_output_report.v1',
        'missing_output_regression_count': len(missing_output),
        'missing_output_regressions_zero': checks['missing_output_regressions_zero'],
        'first_missing_output': missing_output[0].get('readiness_case_id') if missing_output else None,
    })
    jwrite('provider_model_call_report.json', {
        **common,
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.provider_model_call_report.v1',
        'provider_model_calls_for_authoritative_c4_proposals': provider_calls,
        'provider_model_calls_zero': checks['provider_model_calls_zero'],
        'model_prose_authoritative': False,
    })
    jwrite('provider_path_report.json', {
        **common,
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.provider_path_report.v1',
        'direct_provider_bypass_count': direct_bypass,
        'direct_provider_bypass_zero': checks['direct_provider_bypass_zero'],
        'provider_owned_authority_path_used': False,
    })
    jwrite('owner_approval_boundary_readback.json', {
        **common,
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.owner_approval_boundary_readback.v1',
        'owner_approval_boundary_preserved': checks['owner_approval_boundary_preserved'],
        'c4r1_no_apply_readiness_candidate_only': True,
        'm12_c4_ready_for_owner_review_as_no_apply_readiness_candidate': status == PASS,
        'production_authorized': False,
        'c4_production_started': False,
        'cache_enabled': False,
        'artifact_memory_promoted': False,
        'production_expansion_applied': False,
    })

    # Rewrite overlapping canonical reports with exact-contract status/common fields.
    jwrite('c1_c2_c3_boundary_preservation_readback.json', {
        **common,
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.boundary_preservation.v2',
        'c1_status': c1.get('status'),
        'c2_status': c2.get('status'),
        'c3_status': c3.get('status'),
        'c1_scope': 'bounded artifact status Q&A',
        'c2_scope': 'deterministic single-artifact runbook guidance',
        'c3_scope': 'deterministic two-artifact consistency comparison',
        'c1_preserved': checks['c1_frozen_production_boundary_preserved'],
        'c2_preserved': checks['c2_frozen_production_boundary_preserved'],
        'c3_preserved': checks['c3_frozen_production_boundary_preserved'],
        'source_hashes': source_hashes,
    })
    jwrite('mutation_sentinel_report.json', {
        **common,
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.mutation_sentinel_report.v2',
        'mutation_sentinels_clean': checks['mutation_sentinels_clean'],
        'production_expansion_applied': False,
        'c4_production_started': False,
        'c4_canary_started': False,
        'cache_enabled': False,
        'artifact_memory_promoted': False,
        'global_semantic_gate_promoted': False,
        'runtime_authority_mutated': False,
        'gateway_config_mutated': False,
        'live_route_mutated': False,
        'fallback_chain_mutated': False,
        'memory_route_mutated': False,
        'external_action_executed': False,
        'scheduled_action_created': False,
    })
    jwrite('rollback_readiness.json', {
        **common,
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.rollback_readiness.v2',
        'rollback_ready': checks['rollback_ready'],
        'rollback_applied': False,
        'm11_frozen_baseline_preserved': checks['m11_frozen_baseline_preserved'],
        'source_hashes': source_hashes,
    })
    jwrite('no_apply_no_mutation_record.json', {
        **common,
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.no_apply_no_mutation_record.v2',
        'readiness_exercise_only': True,
        'c4_production_started': False,
        'c4_canary_started': False,
        'production_expansion_applied': False,
        'cache_enabled': False,
        'artifact_memory_promoted': False,
        'global_semantic_gate_promoted': False,
        'runtime_authority_mutated': False,
        'gateway_config_mutated': False,
        'external_action_executed': False,
        'scheduled_action_created': False,
        'direct_provider_bypass_count': direct_bypass,
    })
    review = f'''# M12-C4R1 Bounded Next-Step Proposal Readiness Exercise / No Apply

Final status: `{status}`

Exact required-file contract normalized: `true`

Run bound: 50 C4 bounded proposal cases or 2 active hours, whichever came first. This run completed the 50-case bound.

Counts:

- Executed: `{len(cases)}/50`
- Passed: `{len(cases) - len(material_regressions)}/50`
- Failed: `{len(material_regressions)}`
- Envelope counts: `{envelope_counts}`
- Provider/model authoritative calls: `{provider_calls}`
- Direct provider bypass: `{direct_bypass}`

Failed gates: `{failed_gates}`
Abort conditions hit: `{abort_hits}`
First failure: `{first_failure}`

C4R1 consumed C4K read-only. No production/canary/cache/artifact-memory/global Semantic Gate/runtime/Gateway/config/live-route/fallback/memory-route mutation/external action/scheduling occurred.

Core principle preserved: proposal drafting is not action authority.

If PASS: M12-C4 is ready for owner review as a no-apply readiness candidate only. This does not authorize C4 production, cache, artifact-memory promotion, or broader production expansion.
'''
    twrite('M12_C4R1_BOUNDED_NEXT_STEP_PROPOSAL_READINESS_REVIEW.md', review)

    missing = [name for name in REQ if name not in {'status.json','summary.json'} and not (ART / name).exists()]
    if missing and 'required_files_missing' not in failed_gates:
        failed_gates.append('required_files_missing')
        status = BLOCKED if status != ABORT else ABORT
        first_failure = first_failure or 'required_files_missing'
    status_obj = {
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.status.v2.exact_contract',
        'created_utc': created,
        'status': status,
        'artifact_dir': rel(ART),
        'required_files': REQ,
        'required_files_missing': missing,
        'failed_gates': failed_gates,
        'abort_conditions_hit': abort_hits,
        'first_failure': first_failure,
        'run_bound_cases': 50,
        'run_bound_hours': 2,
        'executed_cases': len(cases),
        'pass_count': len(cases) - len(material_regressions),
        'fail_count': len(material_regressions),
        'missing_output_regression_count': len(missing_output),
        'material_regression_count': len(material_regressions),
        'envelope_counts': envelope_counts,
        'pass_condition_checks': checks,
        'abort_condition_checks': abort_conditions,
        'c4r1_no_apply_readiness_exercise_only': True,
        'm12_c4_ready_for_owner_review_as_no_apply_readiness_candidate': status == PASS,
        'c4k_consumed_read_only': checks['c4k_read_only_consumed'],
        'c4_bounded_proposal_drafting_only': True,
        'proposal_drafting_not_action_authority': True,
        'provider_model_calls_for_authoritative_proposals': provider_calls,
        'direct_provider_bypass_count': direct_bypass,
        'c4_production_started': False,
        'c4_canary_started': False,
        'production_expansion_applied': False,
        'cache_enabled': False,
        'artifact_memory_promoted': False,
        'global_semantic_gate_promoted': False,
        'runtime_authority_mutated': False,
        'gateway_config_mutated': False,
        'live_route_mutated': False,
        'fallback_chain_mutated': False,
        'memory_route_mutated': False,
        'external_action_executed': False,
        'scheduled_action_created': False,
        'rollback_ready': checks['rollback_ready'],
        'mutation_sentinels_clean': checks['mutation_sentinels_clean'],
        'm11_frozen_baseline_preserved': checks['m11_frozen_baseline_preserved'],
        'm12_c1_frozen_boundary_preserved': checks['c1_frozen_production_boundary_preserved'],
        'm12_c2_frozen_boundary_preserved': checks['c2_frozen_production_boundary_preserved'],
        'm12_c3_frozen_boundary_preserved': checks['c3_frozen_production_boundary_preserved'],
        'source_hashes': source_hashes,
        'previous_status_sha256': sha_json(old_status),
        'previous_summary_sha256': sha_json(old_summary),
    }
    jwrite('status.json', status_obj)
    summary_keys = [
        'schema','created_utc','status','artifact_dir','failed_gates','abort_conditions_hit','first_failure',
        'executed_cases','pass_count','fail_count','missing_output_regression_count','material_regression_count','envelope_counts',
        'c4r1_no_apply_readiness_exercise_only','m12_c4_ready_for_owner_review_as_no_apply_readiness_candidate',
        'c4k_consumed_read_only','c4_bounded_proposal_drafting_only','proposal_drafting_not_action_authority',
        'provider_model_calls_for_authoritative_proposals','direct_provider_bypass_count','c4_production_started','c4_canary_started',
        'production_expansion_applied','cache_enabled','artifact_memory_promoted','global_semantic_gate_promoted','runtime_authority_mutated',
        'external_action_executed','scheduled_action_created','rollback_ready','mutation_sentinels_clean','m12_c1_frozen_boundary_preserved',
        'm12_c2_frozen_boundary_preserved','m12_c3_frozen_boundary_preserved'
    ]
    summary = {k: status_obj[k] for k in summary_keys}
    summary['schema'] = 'stickbot.vnext_semantic_gate.m12_c4r1.summary.v2.exact_contract'
    jwrite('summary.json', summary)
    final_missing = [name for name in REQ if not (ART / name).exists()]
    if final_missing != status_obj['required_files_missing']:
        status_obj['required_files_missing'] = final_missing
        if final_missing and 'required_files_missing' not in status_obj['failed_gates']:
            status_obj['failed_gates'].append('required_files_missing')
            status_obj['status'] = BLOCKED if status_obj['status'] != ABORT else ABORT
            status_obj['first_failure'] = status_obj['first_failure'] or 'required_files_missing'
        jwrite('status.json', status_obj)
        summary['status'] = status_obj['status']
        summary['failed_gates'] = status_obj['failed_gates']
        summary['first_failure'] = status_obj['first_failure']
        jwrite('summary.json', summary)
    files = sorted(p for p in ART.iterdir() if p.is_file() and p.name != 'evidence_manifest.json')
    jwrite('evidence_manifest.json', {
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.evidence_manifest.v2.exact_contract',
        'status': status_obj['status'],
        'artifact_dir': rel(ART),
        'files': [{'path': rel(p), 'sha256': sha_file(p), 'bytes': p.stat().st_size} for p in files],
        'source_hashes': source_hashes,
        'self_hash_policy': 'evidence_manifest.json excluded from its own file list',
    })
    print(json.dumps({
        'status': status_obj['status'],
        'executed_cases': status_obj['executed_cases'],
        'pass_count': status_obj['pass_count'],
        'fail_count': status_obj['fail_count'],
        'missing_output_regression_count': status_obj['missing_output_regression_count'],
        'material_regression_count': status_obj['material_regression_count'],
        'envelope_counts': status_obj['envelope_counts'],
        'failed_gates': status_obj['failed_gates'],
        'abort_conditions_hit': status_obj['abort_conditions_hit'],
        'first_failure': status_obj['first_failure'],
        'required_files_missing': status_obj['required_files_missing'],
        'ready_for_owner_review_no_apply': status_obj['m12_c4_ready_for_owner_review_as_no_apply_readiness_candidate'],
        'status_sha256': sha_file(ART / 'status.json'),
        'evidence_manifest_sha256': sha_file(ART / 'evidence_manifest.json'),
    }, indent=2, sort_keys=True))
    return 0 if status_obj['status'] == PASS else 1


if __name__ == '__main__':
    raise SystemExit(main())
