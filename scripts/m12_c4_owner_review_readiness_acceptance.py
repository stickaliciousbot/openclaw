#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/home/stickai/.openclaw/workspace')
BASE = ROOT / 'sharedspace/runtime-kernel-validation/vnext-semantic-gate'
ART = BASE / 'm12_c4_owner_review_readiness_acceptance'
C4R1 = BASE / 'm12_c4r1_bounded_next_step_proposal_readiness'
C4K = BASE / 'm12_c4k_bounded_next_step_proposal_kernel'
C4_DESIGN_ACCEPT = BASE / 'm12_c4_owner_review_design_acceptance'
C3_FINAL = BASE / 'm12_c3_final_owner_acceptance_review'
C2_FINAL = BASE / 'm12_c2_final_owner_acceptance_review'
C1_FINAL = BASE / 'm12_c1_final_owner_acceptance_review'
M11 = BASE / 'm11_7_production_operating_baseline_finalization'
PASS = 'M12_C4_OWNER_REVIEW_READINESS_ACCEPTED'
BLOCKED = 'M12_C4_OWNER_REVIEW_READINESS_BLOCKED'
REQ = [
    'status.json','summary.json','c4_readiness_acceptance_matrix.json','c4r1_readiness_readback.json',
    'c4_owner_decision_record.md','owner_approval_boundary_readback.json',
    'c1_c2_c3_boundary_preservation_readback.json','mutation_sentinel_report.json',
    'rollback_readiness.json','no_apply_no_mutation_record.json',
    'M12_C4_OWNER_REVIEW_READINESS_ACCEPTANCE.md'
]


def utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')


def load(p: Path) -> Any:
    return json.loads(p.read_text())


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


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


def main() -> int:
    created = utc()
    ART.mkdir(parents=True, exist_ok=True)
    c4r1 = load(C4R1/'status.json')
    c4k = load(C4K/'status.json')
    c4_design_accept = load(C4_DESIGN_ACCEPT/'status.json')
    c3 = load(C3_FINAL/'status.json')
    c2 = load(C2_FINAL/'status.json')
    c1 = load(C1_FINAL/'status.json')
    m11 = load(M11/'status.json')
    source_hashes = {
        rel(C4R1/'status.json'): sha(C4R1/'status.json'),
        rel(C4R1/'evidence_manifest.json'): sha(C4R1/'evidence_manifest.json'),
        rel(C4K/'status.json'): sha(C4K/'status.json'),
        rel(C4_DESIGN_ACCEPT/'status.json'): sha(C4_DESIGN_ACCEPT/'status.json'),
        rel(C3_FINAL/'status.json'): sha(C3_FINAL/'status.json'),
        rel(C2_FINAL/'status.json'): sha(C2_FINAL/'status.json'),
        rel(C1_FINAL/'status.json'): sha(C1_FINAL/'status.json'),
        rel(M11/'status.json'): sha(M11/'status.json'),
    }
    checks = {
        'c4_design_acceptance_present': c4_design_accept.get('status') == 'M12_C4_OWNER_REVIEW_DESIGN_ACCEPTED',
        'c4k_kernel_pass': c4k.get('status') == 'M12_C4K_BOUNDED_NEXT_STEP_PROPOSAL_KERNEL_PASS',
        'c4r1_readiness_pass_no_apply': c4r1.get('status') == 'M12_C4R1_BOUNDED_NEXT_STEP_PROPOSAL_READINESS_PASS_NO_APPLY',
        'c4r1_50_case_bound_complete': c4r1.get('executed_cases') == 50 and c4r1.get('pass_count') == 50 and c4r1.get('fail_count') == 0,
        'c4r1_required_file_contract_exact': c4r1.get('required_files_missing') == [],
        'c4_ready_for_owner_review_no_apply_candidate': c4r1.get('m12_c4_ready_for_owner_review_as_no_apply_readiness_candidate') is True,
        'proposal_envelope_contract_passed': c4r1.get('pass_condition_checks',{}).get('proposal_envelope_contract_passes') is True,
        'hold_reject_contract_passed': c4r1.get('pass_condition_checks',{}).get('hold_reject_contract_passes') is True,
        'source_authority_deterministic': c4r1.get('pass_condition_checks',{}).get('source_authority_deterministic') is True,
        'non_execution_contract_passed': c4r1.get('pass_condition_checks',{}).get('non_execution_contract_passes') is True,
        'owner_review_required_for_proposals': c4r1.get('pass_condition_checks',{}).get('required_owner_review_true_enforced') is True,
        'uncertainty_conflict_prerequisite_preserved': c4r1.get('pass_condition_checks',{}).get('uncertainty_conflict_prerequisite_preservation_passes') is True,
        'fail_closed_policy_passed': c4r1.get('pass_condition_checks',{}).get('fail_closed_cases_hold_reject_correctly') is True,
        'material_regressions_zero': c4r1.get('material_regression_count') == 0,
        'missing_output_regressions_zero': c4r1.get('missing_output_regression_count') == 0,
        'provider_model_calls_zero': c4r1.get('provider_model_calls_for_authoritative_proposals') == 0,
        'direct_provider_bypass_zero': c4r1.get('direct_provider_bypass_count') == 0,
        'mutation_sentinels_clean': mutation_clean(c4r1) and mutation_clean(c4k) and mutation_clean(c3) and mutation_clean(c2) and mutation_clean(c1),
        'rollback_ready': c4r1.get('rollback_ready') is True and c4k.get('rollback_ready') is True and c3.get('rollback_ready') is True and c2.get('rollback_ready') is True and c1.get('rollback_ready') is True and m11.get('gate_checks',{}).get('rollback_ready') is True,
        'c1_boundary_preserved': c4r1.get('m12_c1_frozen_boundary_preserved') is True and c1.get('status') == 'M12_C1_FINAL_OWNER_ACCEPTANCE_READY',
        'c2_boundary_preserved': c4r1.get('m12_c2_frozen_boundary_preserved') is True and c2.get('status') == 'M12_C2_FINAL_OWNER_ACCEPTANCE_READY',
        'c3_boundary_preserved': c4r1.get('m12_c3_frozen_boundary_preserved') is True and c3.get('status') == 'M12_C3_FINAL_OWNER_ACCEPTANCE_READY',
        'm11_baseline_preserved': c4r1.get('m11_frozen_baseline_preserved') is True and m11.get('baseline_frozen') is True,
        'production_expansion_false': c4r1.get('production_expansion_applied') is False,
        'cache_disabled': c4r1.get('cache_enabled') is False,
        'artifact_memory_promotion_disabled': c4r1.get('artifact_memory_promoted') is False,
        'global_semantic_gate_not_promoted': c4r1.get('global_semantic_gate_promoted') is False,
        'no_c4_production_route_active': c4r1.get('c4_production_started') is False,
        'no_c4_canary_started': c4r1.get('c4_canary_started') is False,
        'no_gateway_config_live_route_fallback_memory_runtime_mutation': all(c4r1.get(k) is False for k in ['gateway_config_mutated','live_route_mutated','fallback_chain_mutated','memory_route_mutated','runtime_authority_mutated']),
        'no_external_action_or_scheduling': c4r1.get('external_action_executed') is False and c4r1.get('scheduled_action_created') is False,
        'owner_approval_boundary_preserved': c4r1.get('pass_condition_checks',{}).get('owner_approval_boundary_preserved') is True,
    }
    failed = [k for k,v in checks.items() if not v]
    status = PASS if not failed else BLOCKED
    first_failure = failed[0] if failed else None
    common = {'created_utc': created, 'status': status, 'artifact_dir': rel(ART), 'failed_gates': failed, 'first_failure': first_failure}
    accepted_scope = 'M12-C4 bounded next-step proposal drafting no-apply readiness candidate only'
    jwrite('c4_readiness_acceptance_matrix.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4.owner_readiness_acceptance_matrix.v1', 'checks': checks, 'accepted_scope': accepted_scope if status == PASS else None, 'c4_limited_production_canary_authorized': False, 'c4_production_authorized': False, 'cache_authorized': False, 'artifact_memory_promotion_authorized': False, 'production_expansion_authorized': False, 'source_hashes': source_hashes})
    jwrite('c4r1_readiness_readback.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4.owner_readiness_readback.v1', 'c4r1_status': c4r1.get('status'), 'executed_cases': c4r1.get('executed_cases'), 'pass_count': c4r1.get('pass_count'), 'fail_count': c4r1.get('fail_count'), 'envelope_counts': c4r1.get('envelope_counts'), 'material_regression_count': c4r1.get('material_regression_count'), 'missing_output_regression_count': c4r1.get('missing_output_regression_count'), 'status_sha256': source_hashes[rel(C4R1/'status.json')], 'evidence_manifest_sha256': source_hashes[rel(C4R1/'evidence_manifest.json')]})
    twrite('c4_owner_decision_record.md', f'''# M12-C4 Owner Decision Record — Readiness Acceptance

Decision status: `{status}`

If PASS, accepted scope: **{accepted_scope}**.

This accepts C4 as ready for owner review as a no-apply readiness candidate before any limited production canary.

This does not authorize:

- C4 limited production canary.
- C4 production route activation.
- production expansion.
- cache enablement.
- artifact-memory/global Semantic Gate promotion.
- runtime/Gateway/config/live-route/fallback/memory-route mutation.
- external action execution or scheduling.

Failed gates: `{failed}`
First failure: `{first_failure}`
''')
    jwrite('owner_approval_boundary_readback.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4.owner_approval_boundary_readback.v1', 'owner_approval_boundary_preserved': checks['owner_approval_boundary_preserved'], 'readiness_candidate_accepted': status == PASS, 'limited_production_canary_authorized': False, 'production_authorized': False, 'requires_separate_owner_approval_for_canary': True})
    jwrite('c1_c2_c3_boundary_preservation_readback.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4.owner_readiness_boundary_preservation.v1', 'c1_status': c1.get('status'), 'c2_status': c2.get('status'), 'c3_status': c3.get('status'), 'c1_scope': 'bounded artifact status Q&A', 'c2_scope': 'deterministic single-artifact runbook guidance', 'c3_scope': 'deterministic two-artifact consistency comparison', 'c1_preserved': checks['c1_boundary_preserved'], 'c2_preserved': checks['c2_boundary_preserved'], 'c3_preserved': checks['c3_boundary_preserved'], 'source_hashes': source_hashes})
    jwrite('mutation_sentinel_report.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4.owner_readiness_mutation_sentinel.v1', 'mutation_sentinels_clean': checks['mutation_sentinels_clean'], 'production_expansion_applied': False, 'c4_production_started': False, 'c4_canary_started': False, 'cache_enabled': False, 'artifact_memory_promoted': False, 'global_semantic_gate_promoted': False, 'runtime_authority_mutated': False, 'gateway_config_mutated': False, 'live_route_mutated': False, 'fallback_chain_mutated': False, 'memory_route_mutated': False, 'external_action_executed': False, 'scheduled_action_created': False})
    jwrite('rollback_readiness.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4.owner_readiness_rollback.v1', 'rollback_ready': checks['rollback_ready'], 'rollback_applied': False, 'm11_frozen_baseline_preserved': checks['m11_baseline_preserved'], 'source_hashes': source_hashes})
    jwrite('no_apply_no_mutation_record.json', {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4.owner_readiness_no_apply_no_mutation.v1', 'readiness_acceptance_only': True, 'limited_production_canary_started': False, 'production_expansion_applied': False, 'cache_enabled': False, 'artifact_memory_promoted': False, 'global_semantic_gate_promoted': False, 'runtime_authority_mutated': False, 'gateway_config_mutated': False, 'external_action_executed': False, 'scheduled_action_created': False})
    review = f'''# M12-C4 Owner Review / Readiness Acceptance

Final status: `{status}`

Purpose: accept C4 as a no-apply readiness candidate before any C4 limited production canary.

Accepted scope if PASS: **{accepted_scope}**.

Evidence:

- C4 design acceptance: `{c4_design_accept.get('status')}`
- C4K kernel: `{c4k.get('status')}`
- C4R1 readiness: `{c4r1.get('status')}`
- C4R1 cases: `{c4r1.get('pass_count')}/{c4r1.get('executed_cases')}`
- Envelope counts: `{c4r1.get('envelope_counts')}`
- Material regressions: `{c4r1.get('material_regression_count')}`
- Missing-output regressions: `{c4r1.get('missing_output_regression_count')}`
- Provider/model authoritative calls: `{c4r1.get('provider_model_calls_for_authoritative_proposals')}`
- Direct provider bypass: `{c4r1.get('direct_provider_bypass_count')}`

Failed gates: `{failed}`
First failure: `{first_failure}`

Boundary: no C4 canary/production, no production expansion, no cache/artifact-memory/global Semantic Gate promotion, no runtime/Gateway/config/live-route/fallback/memory-route mutation, no external action or scheduling execution.

If PASS: M12-C4 is ready for owner review as a no-apply readiness candidate only. A C4 limited production canary requires separate owner approval.
'''
    twrite('M12_C4_OWNER_REVIEW_READINESS_ACCEPTANCE.md', review)
    missing = [name for name in REQ if name not in {'status.json','summary.json'} and not (ART/name).exists()]
    if missing and 'required_files_missing' not in failed:
        failed.append('required_files_missing')
        status = BLOCKED
        first_failure = first_failure or 'required_files_missing'
    status_obj = {**common, 'schema': 'stickbot.vnext_semantic_gate.m12_c4.owner_readiness_acceptance_status.v1', 'status': status, 'failed_gates': failed, 'first_failure': first_failure, 'required_files': REQ, 'required_files_missing': missing, 'accepted_scope': accepted_scope if status == PASS else None, 'readiness_candidate_accepted': status == PASS, 'm12_c4_ready_for_owner_review_as_no_apply_readiness_candidate': status == PASS, 'c4_limited_production_canary_authorized': False, 'c4_production_authorized': False, 'production_expansion_applied': False, 'cache_enabled': False, 'artifact_memory_promoted': False, 'global_semantic_gate_promoted': False, 'provider_model_calls_for_authoritative_proposals': c4r1.get('provider_model_calls_for_authoritative_proposals'), 'direct_provider_bypass_count': c4r1.get('direct_provider_bypass_count'), 'external_action_executed': False, 'scheduled_action_created': False, 'runtime_authority_mutated': False, 'gateway_config_mutated': False, 'live_route_mutated': False, 'fallback_chain_mutated': False, 'memory_route_mutated': False, 'rollback_ready': checks['rollback_ready'], 'mutation_sentinels_clean': checks['mutation_sentinels_clean'], 'm11_frozen_baseline_preserved': checks['m11_baseline_preserved'], 'm12_c1_frozen_boundary_preserved': checks['c1_boundary_preserved'], 'm12_c2_frozen_boundary_preserved': checks['c2_boundary_preserved'], 'm12_c3_frozen_boundary_preserved': checks['c3_boundary_preserved'], 'pass_condition_checks': checks, 'source_hashes': source_hashes}
    jwrite('status.json', status_obj)
    summary = {k: status_obj[k] for k in ['schema','created_utc','status','artifact_dir','failed_gates','first_failure','accepted_scope','readiness_candidate_accepted','m12_c4_ready_for_owner_review_as_no_apply_readiness_candidate','c4_limited_production_canary_authorized','c4_production_authorized','production_expansion_applied','cache_enabled','artifact_memory_promoted','global_semantic_gate_promoted','provider_model_calls_for_authoritative_proposals','direct_provider_bypass_count','external_action_executed','scheduled_action_created','runtime_authority_mutated','rollback_ready','mutation_sentinels_clean','m12_c1_frozen_boundary_preserved','m12_c2_frozen_boundary_preserved','m12_c3_frozen_boundary_preserved']}
    summary['schema'] = 'stickbot.vnext_semantic_gate.m12_c4.owner_readiness_acceptance_summary.v1'
    jwrite('summary.json', summary)
    final_missing = [name for name in REQ if not (ART/name).exists()]
    if final_missing != status_obj['required_files_missing']:
        status_obj['required_files_missing'] = final_missing
        if final_missing and 'required_files_missing' not in status_obj['failed_gates']:
            status_obj['failed_gates'].append('required_files_missing')
            status_obj['status'] = BLOCKED
            status_obj['first_failure'] = status_obj['first_failure'] or 'required_files_missing'
        jwrite('status.json', status_obj)
        summary['status'] = status_obj['status']; summary['failed_gates'] = status_obj['failed_gates']; summary['first_failure'] = status_obj['first_failure']
        jwrite('summary.json', summary)
    files = sorted(p for p in ART.iterdir() if p.is_file() and p.name != 'evidence_manifest.json')
    jwrite('evidence_manifest.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c4.owner_readiness_acceptance_manifest.v1', 'status': status_obj['status'], 'artifact_dir': rel(ART), 'files': [{'path': rel(p), 'sha256': sha(p), 'bytes': p.stat().st_size} for p in files], 'source_hashes': source_hashes, 'self_hash_policy': 'evidence_manifest.json excluded from its own file list'})
    print(json.dumps({'status': status_obj['status'], 'failed_gates': status_obj['failed_gates'], 'first_failure': status_obj['first_failure'], 'required_files_missing': status_obj['required_files_missing'], 'readiness_candidate_accepted': status_obj['readiness_candidate_accepted'], 'status_sha256': sha(ART/'status.json'), 'evidence_manifest_sha256': sha(ART/'evidence_manifest.json')}, indent=2, sort_keys=True))
    return 0 if status_obj['status'] == PASS else 1


if __name__ == '__main__':
    raise SystemExit(main())
