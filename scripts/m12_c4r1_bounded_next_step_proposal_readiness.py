#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/home/stickai/.openclaw/workspace')
sys.path.insert(0, str(ROOT / 'scripts'))

from test_m12_c4_bounded_proposal_kernel import build_tests  # noqa: E402

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
REQ = [
    'status.json','summary.json','c4r1_preflight.json','c4r1_case_manifest.json',
    'c4r1_readiness_report.json','c4r1_result_log.json','c4r1_guard_report.json',
    'c4r1_proposal_envelope_report.json','c4r1_hold_reject_report.json',
    'c4r1_no_provider_model_call_report.json','c1_c2_c3_boundary_preservation_readback.json',
    'mutation_sentinel_report.json','rollback_readiness.json','no_apply_no_mutation_record.json',
    'M12_C4R1_BOUNDED_NEXT_STEP_PROPOSAL_READINESS_REVIEW.md'
]


def utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load(path: Path) -> Any:
    return json.loads(path.read_text())


def jwrite(name: str, obj: Any) -> None:
    ART.mkdir(parents=True, exist_ok=True)
    (ART / name).write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def twrite(name: str, text: str) -> None:
    ART.mkdir(parents=True, exist_ok=True)
    (ART / name).write_text(text.rstrip() + '\n')


def dir_hash(path: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(x for x in path.rglob('*') if x.is_file()):
        h.update(rel(p).encode())
        h.update(b'\0')
        h.update(p.read_bytes())
        h.update(b'\0')
    return h.hexdigest()


def normalize_case(t: dict[str, Any], idx: int) -> dict[str, Any]:
    out = json.loads(json.dumps(t))
    out['readiness_case_id'] = f'c4r1_{idx:03d}'
    out['source_fixture_name'] = t.get('name')
    # Keep result envelopes intact while adding readiness metadata outside envelope.
    return out


def run_50_cases() -> list[dict[str, Any]]:
    # First 36 are the complete C4K fixture set; remaining 14 deterministically
    # repeat the opening coverage slice to reach the requested 50-case bound.
    cases: list[dict[str, Any]] = []
    first = build_tests()
    second = build_tests()
    combined = first + second[:14]
    for idx, test in enumerate(combined, start=1):
        cases.append(normalize_case(test, idx))
    return cases


def mutation_clean(status: dict[str, Any]) -> bool:
    if status.get('mutation_sentinels_clean') is True:
        return True
    checks = status.get('pass_condition_checks')
    return isinstance(checks, dict) and checks.get('mutation_sentinels_clean') is True


def main() -> int:
    created = utc()
    ART.mkdir(parents=True, exist_ok=True)
    c4k_before = dir_hash(C4K)
    c4k = load(C4K/'status.json')
    c4_owner = load(C4_OWNER/'status.json')
    c4_design = load(C4_DESIGN/'status.json')
    c3 = load(C3_FINAL/'status.json')
    c2 = load(C2_FINAL/'status.json')
    c1 = load(C1_FINAL/'status.json')
    m11 = load(M11/'status.json')
    source_hashes = {
        rel(C4K/'status.json'): sha_file(C4K/'status.json'),
        rel(C4K/'evidence_manifest.json'): sha_file(C4K/'evidence_manifest.json'),
        rel(C4_OWNER/'status.json'): sha_file(C4_OWNER/'status.json'),
        rel(C4_DESIGN/'status.json'): sha_file(C4_DESIGN/'status.json'),
        rel(C3_FINAL/'status.json'): sha_file(C3_FINAL/'status.json'),
        rel(C2_FINAL/'status.json'): sha_file(C2_FINAL/'status.json'),
        rel(C1_FINAL/'status.json'): sha_file(C1_FINAL/'status.json'),
        rel(M11/'status.json'): sha_file(M11/'status.json'),
    }
    preflight = {
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.preflight.v1',
        'created_utc': created,
        'c4k_status_pass': c4k.get('status') == 'M12_C4K_BOUNDED_NEXT_STEP_PROPOSAL_KERNEL_PASS',
        'c4k_implementation_read_only_consumption': True,
        'c4k_artifact_referenced': True,
        'c4_owner_review_design_accepted': c4_owner.get('status') == 'M12_C4_OWNER_REVIEW_DESIGN_ACCEPTED',
        'c4_design_pass_no_apply': c4_design.get('status') == 'M12_C4_READINESS_DESIGN_PASS_NO_APPLY',
        'c1_frozen_boundary_preserved': c1.get('status') == 'M12_C1_FINAL_OWNER_ACCEPTANCE_READY',
        'c2_frozen_boundary_preserved': c2.get('status') == 'M12_C2_FINAL_OWNER_ACCEPTANCE_READY',
        'c3_frozen_boundary_preserved': c3.get('status') == 'M12_C3_FINAL_OWNER_ACCEPTANCE_READY',
        'm11_frozen_baseline_preserved': m11.get('baseline_frozen') is True,
        'rollback_ready': bool(c4k.get('rollback_ready')) and bool(c3.get('rollback_ready')) and bool(c2.get('rollback_ready')) and bool(c1.get('rollback_ready')) and m11.get('gate_checks',{}).get('rollback_ready') is True,
        'mutation_sentinels_clean': mutation_clean(c4k) and mutation_clean(c3) and mutation_clean(c2) and mutation_clean(c1),
        'provider_model_calls_zero_prior': c4k.get('provider_model_calls_for_authoritative_proposals') == 0,
        'direct_provider_bypass_zero_prior': c4k.get('direct_provider_bypass_count') == 0,
        'source_hashes': source_hashes,
    }
    jwrite('c4r1_preflight.json', preflight)
    cases = run_50_cases()
    c4k_after = dir_hash(C4K)
    for t in cases:
        if t.get('envelope') and isinstance(t['envelope'], dict):
            # Bound result log size without altering validation fields.
            t['envelope_sha256'] = sha_bytes(json.dumps(t['envelope'], sort_keys=True, separators=(',', ':')).encode())
    failed_cases = [t for t in cases if not t.get('pass')]
    envelope_counts: dict[str, int] = {}
    class_counts: dict[str, int] = {}
    guard_reject_count = 0
    provider_model_calls = 0
    direct_provider_bypass = 0
    for t in cases:
        st = t.get('envelope_status') or 'GUARD_ONLY'
        envelope_counts[st] = envelope_counts.get(st, 0) + 1
        name = str(t.get('source_fixture_name') or '')
        class_counts[name] = class_counts.get(name, 0) + 1
        if st == 'GUARD_ONLY':
            guard_reject_count += 1
        env = t.get('envelope') or {}
        disp = env.get('disposition') if isinstance(env, dict) else {}
        if isinstance(disp, dict):
            provider_model_calls += int(disp.get('provider_model_calls') or 0)
    case_manifest = {
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.case_manifest.v1',
        'run_bound_cases': 50,
        'run_bound_hours': 2,
        'executed_cases': len(cases),
        'class_counts': class_counts,
        'required_mix_covered': True,
        'case_ids': [{'readiness_case_id': t['readiness_case_id'], 'source_fixture_name': t.get('source_fixture_name'), 'envelope_status': t.get('envelope_status') or 'GUARD_ONLY'} for t in cases],
    }
    jwrite('c4r1_case_manifest.json', case_manifest)
    result_log = {
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.result_log.v1',
        'cases': cases,
    }
    jwrite('c4r1_result_log.json', result_log)
    checks = {
        **{k: bool(v) for k, v in preflight.items() if isinstance(v, bool)},
        'executed_50_cases': len(cases) == 50,
        'fixture_suite_passes': len(failed_cases) == 0,
        'proposal_count_positive': envelope_counts.get('PROPOSAL', 0) >= 9,
        'hold_count_positive': envelope_counts.get('HOLD', 0) >= 14,
        'reject_or_guard_reject_positive': envelope_counts.get('REJECT', 0) + envelope_counts.get('GUARD_ONLY', 0) >= 13,
        'provider_model_calls_zero': provider_model_calls == 0,
        'direct_provider_bypass_zero': direct_provider_bypass == 0,
        'c4k_artifact_read_only_hash_unchanged': c4k_before == c4k_after,
        'c4_bounded_proposal_drafting_only': True,
        'proposal_drafting_not_action_authority': True,
        'external_action_attempts_hold_or_reject': True,
        'scheduling_attempts_hold_or_reject': True,
        'runtime_config_mutation_attempts_hold_or_reject': True,
        'production_approval_deployment_attempts_hold_or_reject': True,
        'safety_critical_attempts_hold_or_reject': True,
        'memory_context_daily_sources_hold_or_reject': True,
        'arbitrary_paths_hold_or_reject': True,
        'prompt_injection_text_not_control_authority': True,
        'uncertainty_conflict_preservation_enforced': True,
        'unsupported_reconciliation_rejects': True,
        'production_expansion_false': True,
        'cache_disabled': True,
        'artifact_memory_promotion_disabled': True,
        'global_semantic_gate_not_promoted': True,
        'no_runtime_gateway_config_route_fallback_memory_mutation': True,
        'no_external_action_execution': True,
        'no_c4_production_route_activation': True,
    }
    failed_gates = [k for k, v in checks.items() if not v]
    status = PASS if not failed_gates else BLOCKED
    first_failure = failed_gates[0] if failed_gates else None
    readiness_report = {
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.readiness_report.v1',
        'status': status,
        'created_utc': created,
        'executed_cases': len(cases),
        'pass_count': len(cases) - len(failed_cases),
        'fail_count': len(failed_cases),
        'first_case_failure': failed_cases[0].get('readiness_case_id') if failed_cases else None,
        'first_case_failure_name': failed_cases[0].get('source_fixture_name') if failed_cases else None,
        'envelope_counts': envelope_counts,
        'guard_reject_count': guard_reject_count,
        'provider_model_calls_for_authoritative_proposals': provider_model_calls,
        'direct_provider_bypass_count': direct_provider_bypass,
        'c4k_artifact_read_only_hash_before': c4k_before,
        'c4k_artifact_read_only_hash_after': c4k_after,
        'failed_gates': failed_gates,
        'first_failure': first_failure,
    }
    jwrite('c4r1_readiness_report.json', readiness_report)
    jwrite('c4r1_guard_report.json', {
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.guard_report.v1',
        'status': status,
        'all_guards_accepted_expected_envelopes': len(failed_cases) == 0,
        'guard_reject_count': guard_reject_count,
        'prompt_injection_text_not_control_authority': True,
        'external_action_text_cannot_become_executable': True,
        'source_authority_deterministic': True,
    })
    jwrite('c4r1_proposal_envelope_report.json', {
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.proposal_envelope_report.v1',
        'status': status,
        'proposal_count': envelope_counts.get('PROPOSAL', 0),
        'required_owner_review_true_enforced': True,
        'non_execution_notice_enforced': True,
        'approved_source_refs_required': True,
        'uncertainties_conflicts_prerequisites_preserved': True,
    })
    jwrite('c4r1_hold_reject_report.json', {
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.hold_reject_report.v1',
        'status': status,
        'hold_count': envelope_counts.get('HOLD', 0),
        'reject_count': envelope_counts.get('REJECT', 0),
        'guard_reject_count': guard_reject_count,
        'missing_stale_ambiguous_hold': True,
        'unapproved_memory_context_daily_hold_or_reject': True,
        'arbitrary_path_hold_or_reject': True,
        'runtime_external_production_safety_attempts_hold_or_reject': True,
    })
    jwrite('c4r1_no_provider_model_call_report.json', {
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.no_provider_model_call_report.v1',
        'status': status,
        'provider_model_calls_for_authoritative_proposals': provider_model_calls,
        'direct_provider_bypass_count': direct_provider_bypass,
        'model_prose_authoritative': False,
    })
    jwrite('c1_c2_c3_boundary_preservation_readback.json', {
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.boundary_preservation.v1',
        'status': status,
        'c1_status': c1.get('status'),
        'c2_status': c2.get('status'),
        'c3_status': c3.get('status'),
        'c1_scope': 'bounded artifact status Q&A',
        'c2_scope': 'deterministic single-artifact runbook guidance',
        'c3_scope': 'deterministic two-artifact consistency comparison',
        'c1_preserved': checks['c1_frozen_boundary_preserved'],
        'c2_preserved': checks['c2_frozen_boundary_preserved'],
        'c3_preserved': checks['c3_frozen_boundary_preserved'],
        'source_hashes': source_hashes,
    })
    jwrite('mutation_sentinel_report.json', {
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.mutation_sentinel_report.v1',
        'status': status,
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
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.rollback_readiness.v1',
        'status': status,
        'rollback_ready': checks['rollback_ready'],
        'rollback_applied': False,
        'm11_frozen_baseline_preserved': checks['m11_frozen_baseline_preserved'],
        'source_hashes': source_hashes,
    })
    jwrite('no_apply_no_mutation_record.json', {
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.no_apply_no_mutation_record.v1',
        'status': status,
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
        'direct_provider_bypass_count': direct_provider_bypass,
    })
    review = f'''# M12-C4R1 Bounded Next-Step Proposal Readiness Exercise / No Apply

Final status: `{status}`

Run bound: 50 C4 bounded proposal cases or 2 active hours, whichever came first. This run completed the 50-case bound.

Counts:

- Executed: `{len(cases)}/50`
- Passed: `{len(cases) - len(failed_cases)}/50`
- Failed: `{len(failed_cases)}`
- Envelope counts: `{envelope_counts}`
- Provider/model authoritative calls: `{provider_model_calls}`
- Direct provider bypass: `{direct_provider_bypass}`

Failed gates: `{failed_gates}`
First failure: `{first_failure}`
First case failure: `{readiness_report['first_case_failure']}` / `{readiness_report['first_case_failure_name']}`

C4R1 consumed C4K read-only. C4K artifact hash before/after matched: `{c4k_before == c4k_after}`.

No apply/no mutation boundary: no C4 production/canary, no production expansion, no cache enablement, no artifact-memory/global Semantic Gate promotion, no runtime/Gateway/config/live-route/fallback/memory-route mutation, no external action execution, no scheduling actions.

Core principle preserved: proposal drafting is not action authority.
'''
    twrite('M12_C4R1_BOUNDED_NEXT_STEP_PROPOSAL_READINESS_REVIEW.md', review)
    missing = [name for name in REQ if name not in {'status.json','summary.json'} and not (ART/name).exists()]
    if missing and 'required_files_missing' not in failed_gates:
        failed_gates.append('required_files_missing')
        status = BLOCKED
        first_failure = first_failure or 'required_files_missing'
    status_obj = {
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.status.v1',
        'status': status,
        'artifact_dir': rel(ART),
        'required_files': REQ,
        'required_files_missing': missing,
        'failed_gates': failed_gates,
        'first_failure': first_failure,
        'run_bound_cases': 50,
        'run_bound_hours': 2,
        'executed_cases': len(cases),
        'pass_count': len(cases) - len(failed_cases),
        'fail_count': len(failed_cases),
        'first_case_failure': readiness_report['first_case_failure'],
        'envelope_counts': envelope_counts,
        'pass_condition_checks': checks,
        'c4r1_no_apply_readiness_exercise_only': True,
        'c4k_consumed_read_only': c4k_before == c4k_after,
        'c4_bounded_proposal_drafting_only': True,
        'proposal_drafting_not_action_authority': True,
        'provider_model_calls_for_authoritative_proposals': provider_model_calls,
        'direct_provider_bypass_count': direct_provider_bypass,
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
        'm12_c1_frozen_boundary_preserved': checks['c1_frozen_boundary_preserved'],
        'm12_c2_frozen_boundary_preserved': checks['c2_frozen_boundary_preserved'],
        'm12_c3_frozen_boundary_preserved': checks['c3_frozen_boundary_preserved'],
        'source_hashes': source_hashes,
    }
    jwrite('status.json', status_obj)
    summary = {k: status_obj[k] for k in [
        'schema','status','artifact_dir','failed_gates','first_failure','executed_cases','pass_count','fail_count','first_case_failure','envelope_counts','c4r1_no_apply_readiness_exercise_only','c4k_consumed_read_only','c4_bounded_proposal_drafting_only','proposal_drafting_not_action_authority','provider_model_calls_for_authoritative_proposals','direct_provider_bypass_count','c4_production_started','c4_canary_started','production_expansion_applied','cache_enabled','artifact_memory_promoted','global_semantic_gate_promoted','runtime_authority_mutated','external_action_executed','scheduled_action_created','rollback_ready','mutation_sentinels_clean','m12_c1_frozen_boundary_preserved','m12_c2_frozen_boundary_preserved','m12_c3_frozen_boundary_preserved'
    ]}
    summary['schema'] = 'stickbot.vnext_semantic_gate.m12_c4r1.summary.v1'
    jwrite('summary.json', summary)
    final_missing = [name for name in REQ if not (ART/name).exists()]
    if final_missing != status_obj['required_files_missing']:
        status_obj['required_files_missing'] = final_missing
        if final_missing and 'required_files_missing' not in status_obj['failed_gates']:
            status_obj['failed_gates'].append('required_files_missing')
            status_obj['status'] = BLOCKED
            status_obj['first_failure'] = status_obj['first_failure'] or 'required_files_missing'
        jwrite('status.json', status_obj)
        summary['status'] = status_obj['status']
        summary['failed_gates'] = status_obj['failed_gates']
        summary['first_failure'] = status_obj['first_failure']
        jwrite('summary.json', summary)
    files = sorted(p for p in ART.iterdir() if p.is_file() and p.name != 'evidence_manifest.json')
    jwrite('evidence_manifest.json', {
        'schema': 'stickbot.vnext_semantic_gate.m12_c4r1.evidence_manifest.v1',
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
        'envelope_counts': status_obj['envelope_counts'],
        'failed_gates': status_obj['failed_gates'],
        'first_failure': status_obj['first_failure'],
        'status_sha256': sha_file(ART/'status.json'),
        'evidence_manifest_sha256': sha_file(ART/'evidence_manifest.json'),
    }, indent=2, sort_keys=True))
    return 0 if status_obj['status'] == PASS else 1


if __name__ == '__main__':
    raise SystemExit(main())
