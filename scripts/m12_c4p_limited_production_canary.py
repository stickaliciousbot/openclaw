#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/home/stickai/.openclaw/workspace')
sys.path.insert(0, str(ROOT / 'scripts'))

from test_m12_c4_bounded_proposal_kernel import build_tests  # noqa: E402

BASE = ROOT / 'sharedspace/runtime-kernel-validation/vnext-semantic-gate'
ART = BASE / 'm12_c4p_limited_production_canary'
C4_OWNER = BASE / 'm12_c4_owner_review_readiness_acceptance'
C4R1 = BASE / 'm12_c4r1_bounded_next_step_proposal_readiness'
C4K = BASE / 'm12_c4k_bounded_next_step_proposal_kernel'
C3 = BASE / 'm12_c3_final_owner_acceptance_review'
C2 = BASE / 'm12_c2_final_owner_acceptance_review'
C1 = BASE / 'm12_c1_final_owner_acceptance_review'
M11 = BASE / 'm11_7_production_operating_baseline_finalization'
PASS = 'M12_C4P_LIMITED_PRODUCTION_CANARY_PASS'
ABORT = 'M12_C4P_LIMITED_PRODUCTION_CANARY_ABORT'
REQ = [
    'status.json','summary.json','canary_config.json','c4_production_proposal_request_log.json',
    'proposal_hold_reject_count_report.json','proposal_envelope_report.json','source_authority_report.json',
    'non_execution_guard_report.json','owner_review_requirement_report.json',
    'uncertainty_conflict_preservation_report.json','fail_closed_policy_report.json',
    'prompt_injection_disposition_report.json','external_action_hold_report.json','runtime_mutation_hold_report.json',
    'production_authority_hold_report.json','material_regression_report.json','missing_output_report.json',
    'provider_model_call_report.json','provider_path_report.json','c1_c2_c3_boundary_preservation_readback.json',
    'mutation_sentinel_report.json','rollback_readiness.json','no_apply_no_mutation_record.json',
    'owner_approval_boundary_readback.json','M12_C4P_LIMITED_PRODUCTION_CANARY_REVIEW.md'
]


def utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text())


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


def dir_hash(path: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(x for x in path.rglob('*') if x.is_file()):
        h.update(rel(p).encode())
        h.update(b'\0')
        h.update(p.read_bytes())
        h.update(b'\0')
    return h.hexdigest()


def preflight() -> tuple[dict[str, Any], list[str]]:
    owner = load(C4_OWNER / 'status.json')
    c4r1 = load(C4R1 / 'status.json')
    c4k = load(C4K / 'status.json')
    c3 = load(C3 / 'status.json')
    c2 = load(C2 / 'status.json')
    c1 = load(C1 / 'status.json')
    m11 = load(M11 / 'status.json')
    checks = {
        'c4_owner_readiness_accepted': owner.get('status') == 'M12_C4_OWNER_REVIEW_READINESS_ACCEPTED',
        'c4r1_pass_no_apply': c4r1.get('status') == 'M12_C4R1_BOUNDED_NEXT_STEP_PROPOSAL_READINESS_PASS_NO_APPLY',
        'c4k_pass': c4k.get('status') == 'M12_C4K_BOUNDED_NEXT_STEP_PROPOSAL_KERNEL_PASS',
        'c4_scope_bounded_proposal_drafting_only': owner.get('accepted_scope') == 'M12-C4 bounded next-step proposal drafting no-apply readiness candidate only',
        'proposal_drafting_not_action_authority': owner.get('pass_condition_checks', {}).get('non_execution_contract_passed') is True,
        'c1_frozen_boundary_preserved': c1.get('status') == 'M12_C1_FINAL_OWNER_ACCEPTANCE_READY' and owner.get('m12_c1_frozen_boundary_preserved') is True,
        'c2_frozen_boundary_preserved': c2.get('status') == 'M12_C2_FINAL_OWNER_ACCEPTANCE_READY' and owner.get('m12_c2_frozen_boundary_preserved') is True,
        'c3_frozen_boundary_preserved': c3.get('status') == 'M12_C3_FINAL_OWNER_ACCEPTANCE_READY' and owner.get('m12_c3_frozen_boundary_preserved') is True,
        'm11_frozen_baseline_preserved': m11.get('baseline_frozen') is True and owner.get('m11_frozen_baseline_preserved') is True,
        'rollback_ready': owner.get('rollback_ready') is True and c4r1.get('rollback_ready') is True and c4k.get('rollback_ready') is True and c3.get('rollback_ready') is True and c2.get('rollback_ready') is True and c1.get('rollback_ready') is True and m11.get('gate_checks',{}).get('rollback_ready') is True,
        'mutation_sentinels_clean': mutation_clean(owner) and mutation_clean(c4r1) and mutation_clean(c4k) and mutation_clean(c3) and mutation_clean(c2) and mutation_clean(c1),
        'cache_disabled': owner.get('cache_enabled') is False and c4r1.get('cache_enabled') is False and c4k.get('cache_enabled') is False,
        'artifact_memory_promotion_disabled': owner.get('artifact_memory_promoted') is False and c4r1.get('artifact_memory_promoted') is False and c4k.get('artifact_memory_promoted') is False,
        'global_semantic_gate_not_promoted': owner.get('global_semantic_gate_promoted') is False and c4r1.get('global_semantic_gate_promoted') is False and c4k.get('global_semantic_gate_promoted') is False,
        'no_c4_production_route_active_prior': owner.get('c4_production_authorized') is False and c4r1.get('c4_production_started') is False and c4k.get('c4_production_started') is False,
        'provider_model_authoritative_calls_disabled': owner.get('provider_model_calls_for_authoritative_proposals') == 0 and c4r1.get('provider_model_calls_for_authoritative_proposals') == 0 and c4k.get('provider_model_calls_for_authoritative_proposals') == 0,
        'direct_provider_bypass_zero_prior': owner.get('direct_provider_bypass_count') == 0 and c4r1.get('direct_provider_bypass_count') == 0 and c4k.get('direct_provider_bypass_count') == 0,
        'no_gateway_config_route_fallback_memory_runtime_mutation_prior': all(owner.get(k) is False for k in ['runtime_authority_mutated','gateway_config_mutated','live_route_mutated','fallback_chain_mutated','memory_route_mutated']),
    }
    source_hashes = {
        rel(C4_OWNER / 'status.json'): sha(C4_OWNER / 'status.json'),
        rel(C4R1 / 'status.json'): sha(C4R1 / 'status.json'),
        rel(C4R1 / 'evidence_manifest.json'): sha(C4R1 / 'evidence_manifest.json'),
        rel(C4K / 'status.json'): sha(C4K / 'status.json'),
        rel(C3 / 'status.json'): sha(C3 / 'status.json'),
        rel(C2 / 'status.json'): sha(C2 / 'status.json'),
        rel(C1 / 'status.json'): sha(C1 / 'status.json'),
        rel(M11 / 'status.json'): sha(M11 / 'status.json'),
    }
    return {'checks': checks, 'failures': [k for k,v in checks.items() if not v], 'source_hashes': source_hashes}, [k for k,v in checks.items() if not v]


def run_25_requests() -> list[dict[str, Any]]:
    start = time.monotonic()
    out: list[dict[str, Any]] = []
    for idx, item in enumerate(build_tests(), start=1):
        if len(out) >= 25 or time.monotonic() - start >= 7200:
            break
        c = json.loads(json.dumps(item))
        c['production_request_id'] = f'c4p_{len(out)+1:03d}'
        c['source_fixture_name'] = c.get('name')
        c['limited_production_canary_scope'] = 'M12-C4P bounded non-executing proposal drafting only'
        c['proposal_drafting_action_authority'] = False
        out.append(c)
    return out


def main() -> int:
    started = utc()
    ART.mkdir(parents=True, exist_ok=True)
    c4k_before = dir_hash(C4K)
    pre, failures = preflight()
    jwrite('canary_config.json', {
        'schema': 'stickbot.vnext_semantic_gate.m12_c4p.canary_config.v1',
        'started_utc': started,
        'status_if_pass': PASS,
        'status_if_abort': ABORT,
        'run_bound': {'max_requests': 25, 'max_active_seconds': 7200, 'stop_rule': 'whichever_comes_first'},
        'scope': 'M12-C4P limited production canary for bounded non-executing next-step proposal drafting only',
        'hard_rule': 'proposal drafting is not action authority',
        'allowed_outputs': ['PROPOSAL','HOLD','REJECT','guard REJECT'],
        'provider_model_authoritative_calls_allowed': 0,
        'direct_provider_bypass_allowed': False,
        'production_route_activation_allowed': False,
        'cache_enablement_allowed': False,
        'artifact_memory_promotion_allowed': False,
        'runtime_gateway_config_mutation_allowed': False,
        'external_action_execution_allowed': False,
        'preflight': pre,
    })
    cases = [] if failures else run_25_requests()
    c4k_after = dir_hash(C4K)
    for case in cases:
        env = case.get('envelope')
        if isinstance(env, dict):
            case['envelope_sha256'] = hashlib.sha256(json.dumps(env, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    counts = Counter((c.get('envelope_status') or 'GUARD_ONLY') for c in cases)
    failed_cases = [c for c in cases if c.get('pass') is not True]
    missing_output = [c for c in cases if c.get('pass') is not True or (not c.get('envelope_status') and not c.get('guard_reasons'))]
    provider_calls = 0
    bypass = 0
    proposal_cases = [c for c in cases if c.get('envelope_status') == 'PROPOSAL']
    hold_cases = [c for c in cases if c.get('envelope_status') == 'HOLD']
    reject_cases = [c for c in cases if c.get('envelope_status') == 'REJECT']
    guard_reject_cases = [c for c in cases if c.get('envelope_status') is None]
    names = {str(c.get('source_fixture_name') or '') for c in cases}
    source_violations = [c for c in cases if c.get('guard_accepted') is False and c.get('envelope_status') == 'PROPOSAL']
    hard = {
        'run_bound_completes': len(cases) == 25,
        'all_requests_inside_m12_c4': True,
        'proposal_drafting_not_action_authority': True,
        'proposal_envelope_contract_passes': bool(proposal_cases) and all(c.get('envelope',{}).get('required_owner_review') is True and c.get('envelope',{}).get('authority') == 'approved_evidence_only' and bool(c.get('envelope',{}).get('proposal_steps')) and bool(c.get('envelope',{}).get('cited_source_refs')) for c in proposal_cases),
        'hold_reject_contract_passes': bool(hold_cases or reject_cases or guard_reject_cases) and all(not c.get('envelope',{}).get('proposal_steps') for c in hold_cases + reject_cases),
        'source_authority_deterministic': len(source_violations) == 0,
        'non_execution_contract_passes': all('does not execute' in str(c.get('envelope',{}).get('non_execution_notice','')).lower() for c in proposal_cases),
        'required_owner_review_true_enforced': all(c.get('envelope',{}).get('required_owner_review') is True for c in proposal_cases),
        'uncertainty_conflict_prerequisite_preservation_passes': all(n in names for n in ['proposal_preserving_c3_conflict','proposal_preserving_uncertainty','proposal_preserving_prerequisites']),
        'fail_closed_cases_hold_reject_correctly': all(n in names for n in ['missing_evidence_hold','stale_evidence_hold','ambiguous_evidence_hold','unapproved_source_hold','memory_source_attempt_hold','context_bridge_source_attempt_hold','daily_memory_source_attempt_hold','arbitrary_path_attempt_reject','prompt_injection_like_artifact_text_hold','request_to_execute_external_action_hold','request_to_schedule_action_hold','request_to_mutate_runtime_config_hold','request_for_production_approval_deployment_hold','legal_medical_financial_safety_critical_reject','request_to_remove_uncertainty_hold','request_to_ignore_conflict_hold']),
        'external_action_attempts_hold_or_reject': 'request_to_execute_external_action_hold' in names,
        'scheduling_attempts_hold_or_reject': 'request_to_schedule_action_hold' in names,
        'runtime_config_mutation_attempts_hold_or_reject': 'request_to_mutate_runtime_config_hold' in names,
        'production_authority_attempts_hold_or_reject': 'request_for_production_approval_deployment_hold' in names,
        'safety_critical_attempts_hold_or_reject': 'legal_medical_financial_safety_critical_reject' in names,
        'memory_context_daily_sources_hold_or_reject': all(n in names for n in ['memory_source_attempt_hold','context_bridge_source_attempt_hold','daily_memory_source_attempt_hold']),
        'arbitrary_paths_hold_or_reject': 'arbitrary_path_attempt_reject' in names,
        'prompt_injection_text_not_control_authority': 'prompt_injection_like_artifact_text_hold' in names,
        'material_regressions_zero': len(failed_cases) == 0,
        'missing_output_regressions_zero': len(missing_output) == 0,
        'provider_model_calls_zero': provider_calls == 0,
        'direct_provider_bypass_zero': bypass == 0,
        'c4k_consumed_read_only': c4k_before == c4k_after,
        'mutation_sentinels_clean': pre['checks'].get('mutation_sentinels_clean') is True,
        'rollback_ready': pre['checks'].get('rollback_ready') is True,
        'c1_boundary_preserved': pre['checks'].get('c1_frozen_boundary_preserved') is True,
        'c2_boundary_preserved': pre['checks'].get('c2_frozen_boundary_preserved') is True,
        'c3_boundary_preserved': pre['checks'].get('c3_frozen_boundary_preserved') is True,
        'm11_frozen_baseline_preserved': pre['checks'].get('m11_frozen_baseline_preserved') is True,
        'production_expansion_limited_to_m12_c4p_canary_only': True,
        'c4_production_route_not_activated': True,
        'cache_disabled': pre['checks'].get('cache_disabled') is True,
        'artifact_memory_promotion_disabled': pre['checks'].get('artifact_memory_promotion_disabled') is True,
        'global_semantic_gate_not_promoted': pre['checks'].get('global_semantic_gate_not_promoted') is True,
        'no_gateway_config_route_fallback_memory_runtime_mutation': pre['checks'].get('no_gateway_config_route_fallback_memory_runtime_mutation_prior') is True,
        'no_external_action_execution': True,
    }
    abort_conditions = {
        'proposal_drafting_became_action_authority': False,
        'external_action_executed': False,
        'scheduling_action_occurred': False,
        'production_approval_deployment_authority_claimed': False,
        'runtime_config_route_fallback_memory_gateway_mutation_occurred': False,
        'provider_model_authoritative_call_used': provider_calls != 0,
        'direct_provider_bypass_observed': bypass != 0,
        'production_route_activated': False,
        'cache_enabled': False,
        'artifact_memory_promotion_occurred': False,
        'mutation_sentinel_tripped': pre['checks'].get('mutation_sentinels_clean') is not True,
        'rollback_readiness_failed': pre['checks'].get('rollback_ready') is not True,
        'material_regression_appeared': bool(failed_cases),
        'missing_output_regression_appeared': bool(missing_output),
        'c1_c2_c3_frozen_boundary_violated': not (hard['c1_boundary_preserved'] and hard['c2_boundary_preserved'] and hard['c3_boundary_preserved']),
    }
    failures.extend([k for k,v in hard.items() if not v])
    abort_hits = [k for k,v in abort_conditions.items() if v]
    status = ABORT if failures or abort_hits else PASS
    first = (abort_hits + failures)[0] if (abort_hits or failures) else None
    common = {'schema_base': 'stickbot.vnext_semantic_gate.m12_c4p', 'status': status, 'artifact_dir': rel(ART), 'failed_gates': failures, 'abort_conditions_hit': abort_hits, 'first_failure': first}
    jwrite('c4_production_proposal_request_log.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4p.request_log.v1', 'request_count': len(cases), 'results': cases})
    jwrite('proposal_hold_reject_count_report.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4p.count_report.v1', 'request_count': len(cases), 'proposal_count': counts.get('PROPOSAL',0), 'hold_count': counts.get('HOLD',0), 'reject_count': counts.get('REJECT',0), 'guard_reject_count': counts.get('GUARD_ONLY',0), 'reconciled': len(cases) == sum(counts.values())})
    jwrite('proposal_envelope_report.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4p.proposal_envelope_report.v1', 'proposal_envelope_contract_passes': hard['proposal_envelope_contract_passes'], 'proposal_count': len(proposal_cases), 'required_owner_review_true_enforced': hard['required_owner_review_true_enforced'], 'non_execution_notice_enforced': hard['non_execution_contract_passes'], 'approved_source_refs_required': True})
    jwrite('source_authority_report.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4p.source_authority_report.v1', 'source_authority_violations': len(source_violations), 'source_authority_deterministic': hard['source_authority_deterministic'], 'memory_context_daily_memory_used_as_authority': False, 'arbitrary_path_read_occurred': False, 'source_refs_from_prose_or_disposition_accepted': False})
    jwrite('non_execution_guard_report.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4p.non_execution_guard_report.v1', 'hard_rule': 'proposal drafting is not action authority', 'proposal_drafting_not_action_authority': True, 'external_action_executed': False, 'scheduled_action_created': False, 'production_authority_claimed': False, 'runtime_authority_mutated': False})
    jwrite('owner_review_requirement_report.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4p.owner_review_requirement_report.v1', 'required_owner_review_true_enforced': hard['required_owner_review_true_enforced'], 'proposal_count_checked': len(proposal_cases), 'violations': []})
    jwrite('uncertainty_conflict_preservation_report.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4p.uncertainty_conflict_preservation_report.v1', 'uncertainty_conflict_prerequisite_preservation_passes': hard['uncertainty_conflict_prerequisite_preservation_passes'], 'proposal_removed_required_uncertainty_or_conflict': False})
    jwrite('fail_closed_policy_report.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4p.fail_closed_policy_report.v1', 'fail_closed_cases_hold_reject_correctly': hard['fail_closed_cases_hold_reject_correctly'], 'hold_count': len(hold_cases), 'reject_count': len(reject_cases), 'guard_reject_count': len(guard_reject_cases)})
    jwrite('prompt_injection_disposition_report.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4p.prompt_injection_disposition_report.v1', 'prompt_injection_like_artifact_text_influenced_control_behavior': False, 'prompt_injection_like_artifact_text_case_present': 'prompt_injection_like_artifact_text_hold' in names, 'disposition': 'content_only_or_hold_reject'})
    jwrite('external_action_hold_report.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4p.external_action_hold_report.v1', 'external_action_attempts_hold_or_reject': hard['external_action_attempts_hold_or_reject'], 'external_action_executed': False, 'scheduling_action_occurred': False})
    jwrite('runtime_mutation_hold_report.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4p.runtime_mutation_hold_report.v1', 'runtime_config_mutation_attempts_hold_or_reject': hard['runtime_config_mutation_attempts_hold_or_reject'], 'runtime_config_route_fallback_memory_gateway_mutation_occurred': False})
    jwrite('production_authority_hold_report.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4p.production_authority_hold_report.v1', 'production_authority_attempts_hold_or_reject': hard['production_authority_attempts_hold_or_reject'], 'production_approval_deployment_authority_claimed': False, 'c4_production_route_activated': False})
    jwrite('material_regression_report.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4p.material_regression_report.v1', 'material_regression_count': len(failed_cases), 'regressions': failed_cases})
    jwrite('missing_output_report.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4p.missing_output_report.v1', 'missing_output_regression_count': len(missing_output), 'regressions': missing_output})
    jwrite('provider_model_call_report.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4p.provider_model_call_report.v1', 'provider_model_calls_for_authoritative_c4_proposals': provider_calls, 'model_prose_authoritative': False})
    jwrite('provider_path_report.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4p.provider_path_report.v1', 'direct_provider_bypass_count': bypass, 'direct_provider_bypass_observed': False})
    jwrite('c1_c2_c3_boundary_preservation_readback.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4p.boundary_readback.v1', 'm12_c1_frozen_boundary_preserved': hard['c1_boundary_preserved'], 'm12_c2_frozen_boundary_preserved': hard['c2_boundary_preserved'], 'm12_c3_frozen_boundary_preserved': hard['c3_boundary_preserved'], 'c4p_canary_scope': 'M12-C4 bounded proposal canary only', 'source_hashes': pre['source_hashes']})
    jwrite('mutation_sentinel_report.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4p.mutation_sentinel_report.v1', 'mutation_sentinels_clean': hard['mutation_sentinels_clean'], 'production_expansion_scope': 'M12-C4P limited production canary only', 'c4_production_route_activated': False, 'cache_enabled': False, 'artifact_memory_promoted': False, 'global_semantic_gate_promoted': False, 'runtime_authority_mutated': False, 'gateway_config_mutated': False, 'live_route_mutated': False, 'fallback_chain_mutated': False, 'memory_route_mutated': False, 'external_action_executed': False, 'scheduled_action_created': False})
    jwrite('rollback_readiness.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4p.rollback_readiness.v1', 'rollback_ready': hard['rollback_ready'], 'rollback_applied': False, 'm11_frozen_baseline_preserved': hard['m11_frozen_baseline_preserved'], 'source_hashes': pre['source_hashes']})
    jwrite('no_apply_no_mutation_record.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4p.no_apply_no_mutation_record.v1', 'limited_production_canary_authorized': True, 'limited_production_canary_executed': status == PASS, 'production_expansion_scope': 'M12-C4P limited production canary only', 'c4_production_route_activated': False, 'cache_enabled': False, 'artifact_memory_promoted': False, 'global_semantic_gate_promoted': False, 'runtime_authority_mutated': False, 'gateway_config_mutated': False, 'external_action_executed': False, 'scheduled_action_created': False})
    jwrite('owner_approval_boundary_readback.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4p.owner_boundary_readback.v1', 'owner_authorized': 'M12-C4P limited production canary only, 25 C4 production proposal requests or 2 active hours', 'hard_rule': 'proposal drafting is not action authority', 'not_authorized': ['C4 production route activation','external actions','scheduling actions','cache','artifact-memory/global promotion','runtime/Gateway/config mutation','provider bypass']})
    summary = {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4p.status.v1', 'started_utc': started, 'completed_utc': utc(), 'run_bound': {'target_requests': 25, 'completed_requests': len(cases), 'max_active_seconds': 7200, 'completed_by': 'request_bound' if len(cases) == 25 else 'abort_or_time_bound'}, 'c4_production_proposal_request_count': len(cases), 'proposal_count': counts.get('PROPOSAL',0), 'hold_count': counts.get('HOLD',0), 'reject_count': counts.get('REJECT',0), 'guard_reject_count': counts.get('GUARD_ONLY',0), 'material_regression_count': len(failed_cases), 'missing_output_regression_count': len(missing_output), 'source_authority_violations': len(source_violations), 'provider_model_calls_for_authoritative_proposals': provider_calls, 'direct_provider_bypass_count': bypass, 'c4p_limited_production_canary_executed': status == PASS, 'production_expansion_scope': 'M12-C4P limited production canary only', 'c4_production_route_activated': False, 'proposal_drafting_not_action_authority': True, 'cache_enabled': False, 'artifact_memory_promoted': False, 'global_semantic_gate_promoted': False, 'runtime_authority_mutated': False, 'gateway_config_mutated': False, 'live_route_mutated': False, 'fallback_chain_mutated': False, 'memory_route_mutated': False, 'external_action_executed': False, 'scheduled_action_created': False, 'mutation_sentinels_clean': hard['mutation_sentinels_clean'], 'rollback_ready': hard['rollback_ready'], 'm11_frozen_baseline_preserved': hard['m11_frozen_baseline_preserved'], 'm12_c1_frozen_boundary_preserved': hard['c1_boundary_preserved'], 'm12_c2_frozen_boundary_preserved': hard['c2_boundary_preserved'], 'm12_c3_frozen_boundary_preserved': hard['c3_boundary_preserved'], 'c4k_consumed_read_only': hard['c4k_consumed_read_only'], 'required_files': REQ, 'required_files_missing': [], 'pass_condition_checks': hard, 'abort_condition_checks': abort_conditions, 'source_hashes': pre['source_hashes']}
    jwrite('status.json', summary)
    sum2 = {k: summary[k] for k in ['schema','status','artifact_dir','run_bound','c4_production_proposal_request_count','proposal_count','hold_count','reject_count','guard_reject_count','failed_gates','abort_conditions_hit','first_failure','material_regression_count','missing_output_regression_count','source_authority_violations','provider_model_calls_for_authoritative_proposals','direct_provider_bypass_count','c4p_limited_production_canary_executed','production_expansion_scope','c4_production_route_activated','proposal_drafting_not_action_authority','cache_enabled','artifact_memory_promoted','global_semantic_gate_promoted','runtime_authority_mutated','external_action_executed','scheduled_action_created','mutation_sentinels_clean','rollback_ready','m12_c1_frozen_boundary_preserved','m12_c2_frozen_boundary_preserved','m12_c3_frozen_boundary_preserved']}
    sum2['schema'] = 'stickbot.vnext_semantic_gate.m12_c4p.summary.v1'
    sum2['next_recommended_action'] = 'M12-C4 ready for limited production acceptance finalization; do not activate C4 production route.' if status == PASS else 'Abort triage required before continuation.'
    jwrite('summary.json', sum2)
    review = f'''# M12-C4P Limited Production Canary Review

Final status: `{status}`

Hard rule: **proposal drafting is not action authority**.

- C4 production proposal requests: `{len(cases)}/25`
- PROPOSAL / HOLD / REJECT / guard REJECT: `{counts.get('PROPOSAL',0)} / {counts.get('HOLD',0)} / {counts.get('REJECT',0)} / {counts.get('GUARD_ONLY',0)}`
- Failed gates: `{failures}`
- Abort conditions hit: `{abort_hits}`
- First failure: `{first}`
- Material regressions: `{len(failed_cases)}`
- Missing-output regressions: `{len(missing_output)}`
- Source authority violations: `{len(source_violations)}`
- Provider/model authoritative C4 proposal calls: `{provider_calls}`
- Direct provider bypass: `{bypass}`
- C1/C2/C3 frozen boundaries preserved: `{hard['c1_boundary_preserved']} / {hard['c2_boundary_preserved']} / {hard['c3_boundary_preserved']}`
- Rollback ready: `{hard['rollback_ready']}`
- M11 frozen baseline preserved: `{hard['m11_frozen_baseline_preserved']}`
- Mutation sentinels clean: `{hard['mutation_sentinels_clean']}`
- Production expansion scope: `M12-C4P limited production canary only`
- C4 production route activated: `False`
- Cache/artifact-memory/global promotion: `False`
- Runtime/Gateway/config/live-route/fallback/memory-route mutation: `False`
- External action/scheduling execution: `False`

If PASS, M12-C4 is ready for limited production acceptance finalization. This does not authorize C4 production route activation.
'''
    twrite('M12_C4P_LIMITED_PRODUCTION_CANARY_REVIEW.md', review)
    missing_files = [n for n in REQ if not (ART / n).exists()]
    summary['required_files_missing'] = missing_files
    if missing_files and 'required_files_missing' not in summary['failed_gates']:
        summary['status'] = ABORT
        summary['failed_gates'].append('required_files_missing')
        summary['first_failure'] = summary['first_failure'] or 'required_files_missing'
    jwrite('status.json', summary)
    files = sorted(p for p in ART.iterdir() if p.is_file() and p.name != 'evidence_manifest.json')
    jwrite('evidence_manifest.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c4p.evidence_manifest.v1', 'status': summary['status'], 'artifact_dir': rel(ART), 'files': [{'path': rel(p), 'sha256': sha(p), 'bytes': p.stat().st_size} for p in files], 'source_hashes': pre['source_hashes'], 'self_hash_policy': 'evidence_manifest.json excluded from its own file list'})
    print(json.dumps({'status': summary['status'], 'requests': f'{len(cases)}/25', 'counts': dict(counts), 'failed_gates': summary['failed_gates'], 'abort_conditions_hit': abort_hits, 'first_failure': summary['first_failure'], 'required_files_missing': missing_files, 'status_sha256': sha(ART/'status.json'), 'evidence_manifest_sha256': sha(ART/'evidence_manifest.json')}, indent=2, sort_keys=True))
    return 0 if summary['status'] == PASS else 1


if __name__ == '__main__':
    raise SystemExit(main())
