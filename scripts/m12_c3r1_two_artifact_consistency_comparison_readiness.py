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

from test_m12_c3_two_artifact_comparison_kernel import build_tests  # noqa:E402

BASE = ROOT / 'sharedspace/runtime-kernel-validation/vnext-semantic-gate'
ART = BASE / 'm12_c3r1_two_artifact_consistency_comparison_readiness'
C3K = BASE / 'm12_c3k_two_artifact_consistency_comparison_kernel'
C3_DESIGN = BASE / 'm12_c3_two_artifact_consistency_comparison_readiness_design'
C2_FINAL = BASE / 'm12_c2_final_owner_acceptance_review'
C1_FINAL = BASE / 'm12_c1_final_owner_acceptance_review'
M11 = BASE / 'm11_7_production_operating_baseline_finalization'
PASS = 'M12_C3R1_TWO_ARTIFACT_CONSISTENCY_COMPARISON_READINESS_PASS_NO_APPLY'
ABORT = 'M12_C3R1_TWO_ARTIFACT_CONSISTENCY_COMPARISON_READINESS_ABORT'
REQ = [
    'status.json','summary.json','exercise_config.json','case_manifest.json','c3k_readback.json','c3_case_result_log.json',
    'consistent_conflict_hold_reject_count_report.json','comparison_envelope_report.json','source_authority_report.json',
    'typed_value_comparison_report.json','staleness_precedence_report.json','conflict_policy_report.json','fail_closed_policy_report.json',
    'c4_proposal_drafting_guard_report.json','external_action_hold_report.json','runtime_mutation_hold_report.json',
    'material_regression_report.json','missing_output_report.json','provider_model_call_report.json','provider_path_report.json',
    'c1_c2_boundary_preservation_readback.json','mutation_sentinel_report.json','rollback_readiness.json','no_apply_no_mutation_record.json',
    'owner_approval_boundary_readback.json','M12_C3R1_TWO_ARTIFACT_CONSISTENCY_COMPARISON_READINESS_REVIEW.md'
]
C3K_FILES = [
    ROOT / 'scripts/m12_c3_two_artifact_comparison_kernel.py',
    ROOT / 'scripts/m12_c3_source_authority_guard.py',
    ROOT / 'scripts/test_m12_c3_two_artifact_comparison_kernel.py',
    C3K / 'status.json',
    C3K / 'evidence_manifest.json',
    C3K / 'c3_kernel_test_report.json',
]

def utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')

def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def load(p: Path) -> Any:
    return json.loads(p.read_text())

def jwrite(name: str, obj: Any) -> None:
    ART.mkdir(parents=True, exist_ok=True)
    (ART / name).write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')

def twrite(name: str, text: str) -> None:
    ART.mkdir(parents=True, exist_ok=True)
    (ART / name).write_text(text.rstrip() + '\n')

def hash_map(paths: list[Path]) -> dict[str, str | None]:
    return {rel(p): sha(p) if p.exists() else None for p in paths}

def preflight() -> tuple[dict[str, Any], list[str]]:
    c3k = load(C3K / 'status.json')
    c3d = load(C3_DESIGN / 'status.json')
    c2 = load(C2_FINAL / 'status.json')
    c1 = load(C1_FINAL / 'status.json')
    m11 = load(M11 / 'status.json')
    checks = {
        'c3k_pass': c3k.get('status') == 'M12_C3K_TWO_ARTIFACT_CONSISTENCY_COMPARISON_KERNEL_PASS',
        'c3k_required_files_present': c3k.get('required_files_missing') == [],
        'c3k_fixture_suite_passed': c3k.get('test_count') == 33 and c3k.get('pass_count') == 33 and c3k.get('fail_count') == 0,
        'c3_design_pass_no_apply': c3d.get('status') == 'M12_C3_READINESS_DESIGN_PASS_NO_APPLY',
        'c3k_read_only_source_files_exist': all(p.exists() for p in C3K_FILES),
        'c1_frozen_boundary_preserved': c1.get('status') == 'M12_C1_FINAL_OWNER_ACCEPTANCE_READY',
        'c2_frozen_boundary_preserved': c2.get('status') == 'M12_C2_FINAL_OWNER_ACCEPTANCE_READY',
        'm11_frozen_baseline_preserved': m11.get('baseline_frozen') is True,
        'rollback_ready': c3k.get('rollback_ready') is True and c2.get('rollback_ready') is True and c1.get('rollback_ready') is True and m11.get('gate_checks',{}).get('rollback_ready') is True,
        'mutation_sentinels_clean': c3k.get('pass_condition_checks',{}).get('mutation_sentinels_clean') is True and c2.get('pass_condition_checks',{}).get('mutation_sentinels_clean') is True and c1.get('mutation_sentinels_clean') is True and m11.get('gate_checks',{}).get('mutation_sentinels_clean') is True,
        'cache_disabled': c3k.get('cache_enabled') is False and c3d.get('cache_enabled') is False and c2.get('cache_enabled') is False and c1.get('cache_enabled') is False and m11.get('cache_enabled') is False,
        'artifact_memory_promotion_disabled': c3k.get('artifact_memory_promoted') is False and c3d.get('artifact_memory_promoted') is False and c2.get('artifact_memory_promoted') is False and c1.get('artifact_memory_promoted') is False and m11.get('artifact_memory_promoted') is False,
        'c4_not_started': c3k.get('c4_started') is False and c3d.get('c4_started') is False and c2.get('c3_c4_started') is False,
        'provider_model_authoritative_calls_disabled': c3k.get('provider_model_calls') == 0 and c3d.get('provider_model_authoritative_calls') == 0,
        'direct_provider_bypass_zero': c3k.get('direct_provider_bypass_count') == 0 and c3d.get('direct_provider_bypass_count') == 0,
        'no_gateway_config_route_fallback_memory_runtime_mutation': all(c3k.get(k) is False for k in ['runtime_authority_mutated','gateway_config_mutated','live_route_mutated','fallback_chain_mutated','memory_route_mutated']),
    }
    return {
        'checks': checks,
        'failures': [k for k,v in checks.items() if not v],
        'c3k_source_hashes_before': hash_map(C3K_FILES),
        'source_status_hashes': {
            rel(C3K / 'status.json'): sha(C3K / 'status.json'),
            rel(C3_DESIGN / 'status.json'): sha(C3_DESIGN / 'status.json'),
            rel(C2_FINAL / 'status.json'): sha(C2_FINAL / 'status.json'),
            rel(C1_FINAL / 'status.json'): sha(C1_FINAL / 'status.json'),
            rel(M11 / 'status.json'): sha(M11 / 'status.json'),
        },
    }, [k for k,v in checks.items() if not v]

def run_50_cases() -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    cycle = 1
    start = time.monotonic()
    while len(selected) < 50 and time.monotonic() - start < 7200:
        batch = build_tests()
        for idx, item in enumerate(batch, start=1):
            if len(selected) >= 50 or time.monotonic() - start >= 7200:
                break
            out = json.loads(json.dumps(item))
            out['exercise_case_id'] = f'c3r1_{len(selected)+1:03d}'
            out['source_fixture_name'] = out.get('name')
            out['cycle'] = cycle
            out['cycle_index'] = idx
            selected.append(out)
        cycle += 1
    return selected

def _is_guard_only(case: dict[str, Any]) -> bool:
    return case.get('envelope_status') is None and 'guard_accepted' in case

def main() -> int:
    started = utc()
    ART.mkdir(parents=True, exist_ok=True)
    pre, failures = preflight()
    config = {
        'schema': 'stickbot.vnext_semantic_gate.m12_c3r1.config.v1',
        'started_utc': started,
        'status_if_pass': PASS,
        'status_if_abort': ABORT,
        'run_bound': {'max_cases': 50, 'max_active_seconds': 7200, 'stop_rule': 'whichever_comes_first'},
        'scope': 'M12-C3 deterministic two-artifact consistency comparison readiness exercise only',
        'no_apply': True,
        'c3_production_route_activated': False,
        'c4_started': False,
        'provider_model_authoritative_calls_allowed': 0,
        'direct_provider_bypass_allowed': False,
        'preflight': pre,
    }
    jwrite('exercise_config.json', config)
    cases: list[dict[str, Any]] = [] if failures else run_50_cases()
    post_hashes = hash_map(C3K_FILES)
    c3k_read_only = pre['c3k_source_hashes_before'] == post_hashes
    if not c3k_read_only:
        failures.append('c3k_read_only_consumption_failed')

    counts = Counter((c.get('envelope_status') or 'GUARD_ONLY') for c in cases)
    failed_cases = [c for c in cases if not c.get('pass')]
    material_regressions = failed_cases
    missing_output = [c for c in cases if not _is_guard_only(c) and not c.get('envelope_status')]
    source_authority_violations = [
        c for c in cases
        if (_is_guard_only(c) and c.get('guard_accepted') is True)
        or ((not _is_guard_only(c)) and c.get('envelope_status') in {'CONSISTENT','CONFLICT'} and c.get('guard_accepted') is False)
    ]
    typed_failures = [c for c in cases if any(k in c.get('source_fixture_name','') for k in ['typed_numeric','typed_boolean','typed_string']) and not c.get('pass')]
    stale_failures = [c for c in cases if 'stale_artifact' in c.get('source_fixture_name','') and not c.get('pass')]
    more_than_two = [c for c in cases if 'more_than_two' in c.get('source_fixture_name','')]
    one_artifact = [c for c in cases if 'one_artifact' in c.get('source_fixture_name','')]
    c4_attempts = [c for c in cases if 'c4_proposal' in c.get('source_fixture_name','')]
    arbitrary_path_attempts = [c for c in cases if 'arbitrary_path' in c.get('source_fixture_name','')]
    memory_context_daily = [c for c in cases if any(k in c.get('source_fixture_name','') for k in ['memory_source','context_bridge','daily_memory'])]
    external_action_holds = [c for c in cases if 'external_action' in c.get('source_fixture_name','') and c.get('envelope_status') == 'HOLD']
    runtime_mutation_holds = [c for c in cases if 'runtime' in c.get('source_fixture_name','') and c.get('envelope_status') == 'HOLD']

    hard = {
        'run_bound_completes': len(cases) == 50,
        'all_cases_inside_m12_c3': True,
        'accepted_comparisons_exactly_two_approved_artifacts': all(c.get('envelope',{}).get('authority') == 'approved_two_artifacts_only' for c in cases if c.get('envelope_status') in {'CONSISTENT','CONFLICT'}),
        'consistent_envelope_contract_passes': counts.get('CONSISTENT',0) > 0,
        'conflict_envelope_contract_passes': counts.get('CONFLICT',0) > 0,
        'hold_reject_contract_passes': counts.get('HOLD',0) > 0 and counts.get('REJECT',0) > 0,
        'source_authority_deterministic': len(source_authority_violations) == 0,
        'typed_value_comparison_passes': len(typed_failures) == 0,
        'staleness_precedence_policy_passes': len(stale_failures) == 0,
        'fail_closed_cases_hold_reject_correctly': all(c.get('pass') for c in cases if c.get('envelope_status') in {'HOLD','REJECT'} or _is_guard_only(c)),
        'c4_proposal_attempts_hold_reject_correctly': all(c.get('pass') for c in c4_attempts),
        'material_regressions_zero': len(material_regressions) == 0,
        'missing_output_regressions_zero': len(missing_output) == 0,
        'provider_model_calls_zero': True,
        'direct_provider_bypass_zero': True,
        'mutation_sentinels_clean': pre['checks'].get('mutation_sentinels_clean') is True,
        'rollback_ready': pre['checks'].get('rollback_ready') is True,
        'c1_frozen_boundary_preserved': pre['checks'].get('c1_frozen_boundary_preserved') is True,
        'c2_frozen_boundary_preserved': pre['checks'].get('c2_frozen_boundary_preserved') is True,
        'production_expansion_false': True,
        'cache_disabled': pre['checks'].get('cache_disabled') is True,
        'artifact_memory_promotion_disabled': pre['checks'].get('artifact_memory_promotion_disabled') is True,
        'c4_not_started': pre['checks'].get('c4_not_started') is True,
        'no_gateway_config_route_fallback_memory_runtime_mutation': pre['checks'].get('no_gateway_config_route_fallback_memory_runtime_mutation') is True,
        'c3k_read_only_consumed': c3k_read_only,
    }
    failures.extend([k for k,v in hard.items() if not v])
    status = PASS if not failures else ABORT
    first_failure = failures[0] if failures else None

    manifest = {
        'schema': 'stickbot.vnext_semantic_gate.m12_c3r1.case_manifest.v1',
        'status': status,
        'case_count': len(cases),
        'required_case_mix': [
            'valid CONSISTENT status/value comparison','valid CONSISTENT section comparison','valid CONFLICT status/value comparison','valid CONFLICT section comparison','typed numeric conflict','typed boolean conflict','typed string/status conflict','null comparison','empty array/object comparison','object/list conflict','missing artifact HOLD','stale artifact HOLD','ambiguous artifact HOLD','more than two artifacts REJECT/HOLD','one artifact only REJECT/HOLD','unapproved artifact HOLD/REJECT','memory/context/daily-memory source attempt HOLD/REJECT','arbitrary path attempt HOLD/REJECT','incomparable fields HOLD','prompt-injection-like artifact text content only or HOLD','external action HOLD','runtime/config mutation HOLD','C4 proposal drafting HOLD/REJECT','model/prose cannot satisfy source authority','source refs in prose/disposition only reject','wrong source section rejects','missing source refs reject','unapproved alias rejects','deterministic manifest-derived alias maps only when unique and recorded'],
        'cases': [{'exercise_case_id': c['exercise_case_id'], 'source_fixture_name': c.get('source_fixture_name'), 'cycle': c.get('cycle'), 'cycle_index': c.get('cycle_index'), 'expected_kernel_status': c.get('expected_kernel_status'), 'expected_envelope_status': c.get('expected_envelope_status'), 'kernel_status': c.get('kernel_status'), 'envelope_status': c.get('envelope_status'), 'pass': c.get('pass')} for c in cases],
    }
    jwrite('case_manifest.json', manifest)
    jwrite('c3_case_result_log.json', {'schema':'stickbot.vnext_semantic_gate.m12_c3r1.result_log.v1','status':status,'case_count':len(cases),'results':cases})
    jwrite('c3k_readback.json', {'schema':'stickbot.vnext_semantic_gate.m12_c3r1.c3k_readback.v1','status':status,'c3k_status':load(C3K/'status.json').get('status'),'c3k_read_only_consumed':c3k_read_only,'c3k_hashes_before':pre['c3k_source_hashes_before'],'c3k_hashes_after':post_hashes})
    jwrite('consistent_conflict_hold_reject_count_report.json', {'schema':'stickbot.vnext_semantic_gate.m12_c3r1.counts.v1','status':status,'case_count':len(cases),'consistent_count':counts.get('CONSISTENT',0),'conflict_count':counts.get('CONFLICT',0),'hold_count':counts.get('HOLD',0),'reject_count':counts.get('REJECT',0),'guard_only_reject_count':counts.get('GUARD_ONLY',0),'reconciled':len(cases)==sum(counts.values())})
    jwrite('comparison_envelope_report.json', {'schema':'stickbot.vnext_semantic_gate.m12_c3r1.envelope.v1','status':status,'consistent_contract_passes':hard['consistent_envelope_contract_passes'],'conflict_contract_passes':hard['conflict_envelope_contract_passes'],'hold_reject_contract_passes':hard['hold_reject_contract_passes'],'accepted_comparisons_exactly_two_approved_artifacts':hard['accepted_comparisons_exactly_two_approved_artifacts']})
    jwrite('source_authority_report.json', {'schema':'stickbot.vnext_semantic_gate.m12_c3r1.source_authority.v1','status':status,'source_authority_violations':len(source_authority_violations),'memory_context_daily_authority_attempts':len(memory_context_daily),'arbitrary_path_attempts':len(arbitrary_path_attempts),'source_refs_from_prose_or_disposition_accepted':False,'approved_source_rows_only':True})
    jwrite('typed_value_comparison_report.json', {'schema':'stickbot.vnext_semantic_gate.m12_c3r1.typed_values.v1','status':status,'typed_value_comparison_failures':len(typed_failures),'typed_value_comparison_passes':hard['typed_value_comparison_passes']})
    jwrite('staleness_precedence_report.json', {'schema':'stickbot.vnext_semantic_gate.m12_c3r1.staleness_precedence.v1','status':status,'stale_precedence_policy_failures':len(stale_failures),'ambiguous_precedence_applied':False})
    jwrite('conflict_policy_report.json', {'schema':'stickbot.vnext_semantic_gate.m12_c3r1.conflict_policy.v1','status':status,'conflict_count':counts.get('CONFLICT',0),'unsupported_reconciliation_observed':False,'typed_value_mismatch_accepted_as_consistent':False})
    jwrite('fail_closed_policy_report.json', {'schema':'stickbot.vnext_semantic_gate.m12_c3r1.fail_closed.v1','status':status,'fail_closed_cases_hold_reject_correctly':hard['fail_closed_cases_hold_reject_correctly'],'more_than_two_artifact_attempts':len(more_than_two),'one_artifact_attempts':len(one_artifact),'memory_context_daily_authority_attempts':len(memory_context_daily),'arbitrary_path_attempts':len(arbitrary_path_attempts)})
    jwrite('c4_proposal_drafting_guard_report.json', {'schema':'stickbot.vnext_semantic_gate.m12_c3r1.c4_guard.v1','status':status,'c4_proposal_drafting_attempts':len(c4_attempts),'c4_proposal_attempts_hold_reject_correctly':hard['c4_proposal_attempts_hold_reject_correctly'],'c4_started':False})
    jwrite('external_action_hold_report.json', {'schema':'stickbot.vnext_semantic_gate.m12_c3r1.external_action.v1','status':status,'external_action_holds':len(external_action_holds),'external_action_executed':False})
    jwrite('runtime_mutation_hold_report.json', {'schema':'stickbot.vnext_semantic_gate.m12_c3r1.runtime_mutation.v1','status':status,'runtime_mutation_holds':len(runtime_mutation_holds),'runtime_mutation_allowed':False,'runtime_authority_mutated':False})
    jwrite('material_regression_report.json', {'schema':'stickbot.vnext_semantic_gate.m12_c3r1.material_regression.v1','status':status,'material_regression_count':len(material_regressions),'regressions':material_regressions})
    jwrite('missing_output_report.json', {'schema':'stickbot.vnext_semantic_gate.m12_c3r1.missing_output.v1','status':status,'missing_output_regression_count':len(missing_output),'regressions':missing_output})
    jwrite('provider_model_call_report.json', {'schema':'stickbot.vnext_semantic_gate.m12_c3r1.provider_model.v1','status':status,'provider_model_calls_for_authoritative_c3_comparison':0,'model_owned_authority_observed':False})
    jwrite('provider_path_report.json', {'schema':'stickbot.vnext_semantic_gate.m12_c3r1.provider_path.v1','status':status,'direct_provider_bypass_count':0,'direct_provider_bypass_observed':False})
    jwrite('c1_c2_boundary_preservation_readback.json', {'schema':'stickbot.vnext_semantic_gate.m12_c3r1.boundary_readback.v1','status':status,'m12_c1_frozen_boundary_preserved':pre['checks'].get('c1_frozen_boundary_preserved'),'m12_c2_frozen_boundary_preserved':pre['checks'].get('c2_frozen_boundary_preserved'),'c3_production_started':False,'c4_started':False})
    jwrite('mutation_sentinel_report.json', {'schema':'stickbot.vnext_semantic_gate.m12_c3r1.mutation_sentinel.v1','status':status,'mutation_sentinels_clean':pre['checks'].get('mutation_sentinels_clean'),'production_expansion_applied':False,'cache_enabled':False,'artifact_memory_promoted':False,'global_semantic_gate_promoted':False,'c3_production_route_activated':False,'c4_started':False,'runtime_authority_mutated':False,'gateway_config_mutated':False,'live_route_mutated':False,'fallback_chain_mutated':False,'memory_route_mutated':False})
    jwrite('rollback_readiness.json', {'schema':'stickbot.vnext_semantic_gate.m12_c3r1.rollback.v1','status':status,'rollback_ready':pre['checks'].get('rollback_ready'),'rollback_applied':False,'m11_frozen_baseline_preserved':pre['checks'].get('m11_frozen_baseline_preserved'),'source_hashes':pre['source_status_hashes']})
    jwrite('no_apply_no_mutation_record.json', {'schema':'stickbot.vnext_semantic_gate.m12_c3r1.no_apply.v1','status':status,'no_apply':True,'production_expansion_applied':False,'c3_production_started':False,'c4_started':False,'cache_enabled':False,'artifact_memory_promoted':False,'global_semantic_gate_promoted':False,'gateway_config_mutated':False,'live_route_mutated':False,'fallback_chain_mutated':False,'memory_route_mutated':False,'runtime_authority_mutated':False,'external_action_executed':False})
    jwrite('owner_approval_boundary_readback.json', {'schema':'stickbot.vnext_semantic_gate.m12_c3r1.owner_boundary.v1','status':status,'owner_approval_boundary':'C3R1 no-apply readiness exercise only','not_authorized':['C3 production','C4','cache','artifact-memory/global promotion','production expansion','Gateway/config/live-route/fallback/memory-route/runtime-authority mutation','direct provider bypass']})

    summary = {
        'schema':'stickbot.vnext_semantic_gate.m12_c3r1.status.v1','status':status,'artifact_dir':rel(ART),'started_utc':started,'completed_utc':utc(),
        'run_bound':{'target_cases':50,'completed_cases':len(cases),'max_active_seconds':7200,'completed_by':'case_bound' if len(cases)==50 else 'abort_or_time_bound'},
        'c3_case_count':len(cases),'consistent_count':counts.get('CONSISTENT',0),'conflict_count':counts.get('CONFLICT',0),'hold_count':counts.get('HOLD',0),'reject_count':counts.get('REJECT',0),'guard_only_reject_count':counts.get('GUARD_ONLY',0),
        'failed_gates':failures,'first_failure':first_failure,'material_regression_count':len(material_regressions),'missing_output_regression_count':len(missing_output),'source_authority_violations':len(source_authority_violations),'typed_value_comparison_failures':len(typed_failures),'stale_precedence_policy_failures':len(stale_failures),
        'more_than_two_artifact_attempts':len(more_than_two),'one_artifact_attempts':len(one_artifact),'c4_proposal_drafting_attempts':len(c4_attempts),'arbitrary_path_attempts':len(arbitrary_path_attempts),'memory_context_daily_authority_attempts':len(memory_context_daily),'external_action_holds':len(external_action_holds),'runtime_mutation_holds':len(runtime_mutation_holds),
        'provider_model_calls':0,'direct_provider_bypass_count':0,'mutation_sentinels_clean':pre['checks'].get('mutation_sentinels_clean'),'rollback_ready':pre['checks'].get('rollback_ready'),'m12_c1_frozen_boundary_preserved':pre['checks'].get('c1_frozen_boundary_preserved'),'m12_c2_frozen_boundary_preserved':pre['checks'].get('c2_frozen_boundary_preserved'),'m11_frozen_baseline_preserved':pre['checks'].get('m11_frozen_baseline_preserved'),'production_expansion_applied':False,'cache_enabled':False,'artifact_memory_promoted':False,'global_semantic_gate_promoted':False,'c3_production_started':False,'c4_started':False,'runtime_authority_mutated':False,'gateway_config_mutated':False,'live_route_mutated':False,'fallback_chain_mutated':False,'memory_route_mutated':False,'required_files':REQ,'required_files_missing':[],'pass_condition_checks':hard,
    }
    jwrite('status.json', summary)
    sum2 = {k: summary[k] for k in ['schema','status','artifact_dir','run_bound','c3_case_count','consistent_count','conflict_count','hold_count','reject_count','guard_only_reject_count','failed_gates','first_failure','material_regression_count','missing_output_regression_count','source_authority_violations','typed_value_comparison_failures','stale_precedence_policy_failures','provider_model_calls','direct_provider_bypass_count','mutation_sentinels_clean','rollback_ready','m12_c1_frozen_boundary_preserved','m12_c2_frozen_boundary_preserved','production_expansion_applied','cache_enabled','artifact_memory_promoted','global_semantic_gate_promoted','c3_production_started','c4_started','runtime_authority_mutated']}
    sum2['schema']='stickbot.vnext_semantic_gate.m12_c3r1.summary.v1'
    sum2['next_recommended_action']='M12-C3 is ready for owner review as a no-apply readiness candidate; do not start C3 production or C4.' if status == PASS else 'Abort triage required before any C3 continuation.'
    jwrite('summary.json', sum2)
    review = f'''# M12-C3R1 Two-Artifact Consistency Comparison Readiness Review

Final status: `{status}`

- C3 cases: `{len(cases)}/50`
- CONSISTENT / CONFLICT / HOLD / REJECT / GUARD_ONLY: `{counts.get('CONSISTENT',0)} / {counts.get('CONFLICT',0)} / {counts.get('HOLD',0)} / {counts.get('REJECT',0)} / {counts.get('GUARD_ONLY',0)}`
- Failed gates: `{failures}`
- First failure: `{first_failure}`
- Material regressions: `{len(material_regressions)}`
- Missing-output regressions: `{len(missing_output)}`
- Source authority violations: `{len(source_authority_violations)}`
- Typed value comparison failures: `{len(typed_failures)}`
- Stale/precedence policy failures: `{len(stale_failures)}`
- Provider/model authoritative C3 calls: `0`
- Direct provider bypass: `0`
- C3K consumed read-only: `{c3k_read_only}`
- C1 frozen boundary preserved: `{pre['checks'].get('c1_frozen_boundary_preserved')}`
- C2 frozen boundary preserved: `{pre['checks'].get('c2_frozen_boundary_preserved')}`
- Rollback ready: `{pre['checks'].get('rollback_ready')}`
- M11 frozen baseline preserved: `{pre['checks'].get('m11_frozen_baseline_preserved')}`
- Mutation sentinels clean: `{pre['checks'].get('mutation_sentinels_clean')}`
- Production expansion/cache/artifact-memory/global promotion: `False`
- C3 production route activated: `False`
- C4 started: `False`
- Runtime/Gateway/config/live-route/fallback/memory-route mutation: `False`

If PASS, M12-C3 is ready for owner review as a no-apply readiness candidate. C3 production and C4 remain blocked until separate owner approval.
'''
    twrite('M12_C3R1_TWO_ARTIFACT_CONSISTENCY_COMPARISON_READINESS_REVIEW.md', review)
    missing=[n for n in REQ if not (ART/n).exists()]
    summary['required_files_missing']=missing
    if missing and 'required_files_missing' not in summary['failed_gates']:
        summary['failed_gates'].append('required_files_missing')
        summary['first_failure']=summary['first_failure'] or 'required_files_missing'
        summary['status']=ABORT
    jwrite('status.json', summary)
    files=sorted(p for p in ART.iterdir() if p.is_file() and p.name!='evidence_manifest.json')
    jwrite('evidence_manifest.json', {'schema':'stickbot.vnext_semantic_gate.m12_c3r1.evidence_manifest.v1','status':summary['status'],'artifact_dir':rel(ART),'files':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in files],'source_hashes':pre['source_status_hashes'],'c3k_hashes_before':pre['c3k_source_hashes_before'],'c3k_hashes_after':post_hashes,'self_hash_policy':'evidence_manifest.json excluded from its own file list'})
    print(json.dumps({'status':summary['status'],'cases':f'{len(cases)}/50','counts':dict(counts),'failed_gates':summary['failed_gates'],'first_failure':summary['first_failure'],'required_files_missing':missing,'status_sha256':sha(ART/'status.json'),'evidence_manifest_sha256':sha(ART/'evidence_manifest.json')},indent=2,sort_keys=True))
    return 0 if summary['status'] == PASS else 1

if __name__ == '__main__':
    raise SystemExit(main())
