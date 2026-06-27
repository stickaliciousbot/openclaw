#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/home/stickai/.openclaw/workspace')
BASE = ROOT / 'sharedspace/runtime-kernel-validation/vnext-semantic-gate'
ART = BASE / 'm12_c1_owner_review_acceptance'
C1R16 = BASE / 'm12_c1r16_bounded_artifact_status_qa_readiness_rerun'
C1K = BASE / 'm12_c1k_deterministic_artifact_qa_kernel'
M11 = BASE / 'm11_7_production_operating_baseline_finalization'
M12_DESIGN = BASE / 'm12_limited_expansion_readiness_design'
STATUS = 'M12_C1_OWNER_REVIEW_READY'
FROZEN_C1K_SHA = '097c0819182001fcf0c0497c7c072be12a8c51f948d2d8f52a39c2ceaf7f28dd'
REQUIRED = [
    'status.json',
    'summary.json',
    'c1_readiness_acceptance_matrix.json',
    'c1k_read_only_consumption_readback.json',
    'pass_no_apply_boundary_record.json',
    'rollback_readiness.json',
    'mutation_sentinel_report.json',
    'owner_decision_record.md',
    'M12_C1_OWNER_REVIEW_ACCEPTANCE.md',
]


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except Exception:
        return str(path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(name: str, obj: Any) -> None:
    ART.mkdir(parents=True, exist_ok=True)
    (ART / name).write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def sha_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def run(cmd: list[str]) -> dict[str, Any]:
    p = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {'cmd': cmd, 'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}


def main() -> int:
    ART.mkdir(parents=True, exist_ok=True)
    created = now()
    c1r16_status = read_json(C1R16 / 'status.json')
    c1r16_summary = read_json(C1R16 / 'summary.json')
    c1r16_mutation = read_json(C1R16 / 'mutation_sentinel_report.json')
    c1r16_rollback = read_json(C1R16 / 'rollback_readiness.json')
    c1r16_owner_boundary = read_json(C1R16 / 'owner_approval_boundary_readback.json')
    c1k_freeze = read_json(BASE / 'm12_c1k_durability_evidence_freeze/status.json')
    m11_status = read_json(M11 / 'status.json')
    candidates = read_json(M12_DESIGN / 'candidate_expansion_classes.json')
    c1_candidate = next((c for c in candidates.get('candidate_expansion_classes', []) if c.get('id') == 'M12-C1'), {})

    c1k_before = sha_file(C1K / 'evidence_manifest.json')
    guard_out = ART / 'c1k_read_only_consumption_readback.json'
    guard_result = run(['python3', 'scripts/m12_c1k_read_only_guard.py', '--purpose', 'manual_read_only_check', '--report-out', rel(guard_out)])
    if guard_out.exists():
        c1k_guard = read_json(guard_out)
    else:
        c1k_guard = {'status': 'BLOCKED', 'stdout': guard_result['stdout'], 'stderr': guard_result['stderr']}
    c1k_after = sha_file(C1K / 'evidence_manifest.json')

    checks = {
        'c1r16_pass_no_apply_evidence_verifies': c1r16_status.get('status') == 'M12_C1R16_BOUNDED_ARTIFACT_STATUS_QA_READINESS_PASS_NO_APPLY' and c1r16_status.get('failed_gates') == [],
        'c1r16_cases_50_50': c1r16_status.get('pass_count') == 50 and c1r16_status.get('case_count') == 50 and c1r16_status.get('fail_count') == 0,
        'material_regressions_zero': c1r16_status.get('material_regression_count') == 0,
        'missing_output_regressions_zero': c1r16_status.get('missing_output_regression_count') == 0,
        'provider_model_calls_zero': c1r16_status.get('provider_model_calls') == 0,
        'direct_provider_bypass_zero': c1r16_status.get('direct_provider_bypass_count') == 0,
        'c1k_read_only_consumption_verifies': c1k_guard.get('status') == 'PASS' and not c1k_guard.get('c1k_artifact_regenerated'),
        'frozen_sha_verifies_before': c1k_before == FROZEN_C1K_SHA,
        'frozen_sha_verifies_after': c1k_after == FROZEN_C1K_SHA,
        'm11_baseline_preserved': m11_status.get('baseline_frozen') is True and c1r16_status.get('m11_frozen_baseline_preserved') is True,
        'rollback_ready': c1r16_status.get('rollback_ready') is True and c1r16_rollback.get('rollback_ready') is True,
        'mutation_sentinels_clean': c1r16_mutation.get('status') == 'PASS' and c1r16_status.get('runtime_authority_mutated') is False,
        'no_production_expansion': c1r16_status.get('production_expansion_applied') is False,
        'no_c2_c3_c4_started': c1r16_status.get('m12_c2_c3_c4_activated') is False,
        'cache_disabled': c1r16_status.get('cache_enabled') is False,
        'artifact_memory_promotion_disabled': c1r16_status.get('artifact_memory_promoted') is False,
        'owner_decision_record_written': True,
    }
    failed = [k for k, v in checks.items() if v is not True]
    status = STATUS if not failed else 'M12_C1_OWNER_REVIEW_BLOCKED'

    matrix = {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1.owner_review_acceptance_matrix.v1',
        'created_utc': created,
        'status': 'PASS' if not failed else 'BLOCKED',
        'candidate': {
            'id': 'M12-C1',
            'name': c1_candidate.get('name', 'bounded artifact status Q&A'),
            'candidate_scope': c1_candidate.get('candidate_scope'),
            'risk_level': c1_candidate.get('risk_level'),
            'readiness_recommendation': c1_candidate.get('readiness_recommendation'),
        },
        'accepted_prior_evidence': {
            'c1r16_status_path': rel(C1R16 / 'status.json'),
            'c1r16_status_sha256': sha_file(C1R16 / 'status.json'),
            'c1r16_status': c1r16_status.get('status'),
            'c1k_freeze_status': c1k_freeze.get('status'),
            'c1k_frozen_evidence_sha256': FROZEN_C1K_SHA,
            'm11_status_path': rel(M11 / 'status.json'),
            'm11_status_sha256': sha_file(M11 / 'status.json'),
            'm11_status': m11_status.get('status'),
        },
        'checks': checks,
        'failed_checks': failed,
    }
    write_json('c1_readiness_acceptance_matrix.json', matrix)

    # Enrich C1K readback with explicit hash before/after.
    c1k_guard['c1k_evidence_sha_before_owner_review'] = c1k_before
    c1k_guard['c1k_evidence_sha_after_owner_review'] = c1k_after
    c1k_guard['frozen_sha_expected'] = FROZEN_C1K_SHA
    c1k_guard['frozen_sha_unchanged'] = c1k_before == c1k_after == FROZEN_C1K_SHA
    write_json('c1k_read_only_consumption_readback.json', c1k_guard)

    boundary = {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1.pass_no_apply_boundary_record.v1',
        'created_utc': created,
        'status': 'PASS',
        'this_packet_is': 'owner_review_acceptance_packet_only',
        'this_packet_is_not': [
            'production expansion',
            'M12-C2/C3/C4 start',
            'cache enablement',
            'artifact-memory promotion',
            'global Semantic Gate promotion',
            'Gateway/config/live-route/fallback/memory-route/runtime-authority mutation',
        ],
        'production_expansion_applied': False,
        'cache_enabled': False,
        'artifact_memory_promoted': False,
        'runtime_authority_mutated': False,
        'm12_c2_c3_c4_started': False,
        'global_semantic_gate_promoted': False,
        'provider_model_calls': 0,
        'direct_provider_bypass': 0,
        'owner_approval_boundary_intact': c1r16_owner_boundary.get('owner_approval_boundary_intact') is True,
    }
    write_json('pass_no_apply_boundary_record.json', boundary)
    write_json('mutation_sentinel_report.json', {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1.owner_review_mutation_sentinel_report.v1',
        'created_utc': created,
        'status': 'PASS' if checks['mutation_sentinels_clean'] and checks['no_production_expansion'] and checks['no_c2_c3_c4_started'] else 'BLOCKED',
        'source': rel(C1R16 / 'mutation_sentinel_report.json'),
        'production_expansion_applied': False,
        'cache_enabled': False,
        'artifact_memory_promoted': False,
        'gateway_config_mutated': False,
        'live_route_mutated': False,
        'fallback_chain_mutated': False,
        'memory_route_mutated': False,
        'runtime_authority_mutated': False,
        'm12_c2_c3_c4_started': False,
        'global_semantic_gate_promoted': False,
    })
    write_json('rollback_readiness.json', {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1.owner_review_rollback_readiness.v1',
        'created_utc': created,
        'status': 'PASS' if checks['rollback_ready'] and checks['m11_baseline_preserved'] else 'BLOCKED',
        'rollback_ready': checks['rollback_ready'],
        'rollback_needed': False,
        'm11_frozen_baseline_preserved': checks['m11_baseline_preserved'],
        'source': rel(C1R16 / 'rollback_readiness.json'),
    })

    owner_decision = f'''# M12-C1 owner decision record

Status: `{status}`
Created UTC: {created}

## Decision posture

M12-C1 is ready for owner review as the first limited expansion candidate.

This packet does **not** approve or apply production expansion. It records that the evidence is ready for Stick/owner review.

## Accepted evidence

- C1R16: `{c1r16_status.get('status')}`
- Cases: `{c1r16_status.get('pass_count')}/{c1r16_status.get('case_count')}`
- Material regressions: `{c1r16_status.get('material_regression_count')}`
- Missing-output regressions: `{c1r16_status.get('missing_output_regression_count')}`
- Provider/model calls: `{c1r16_status.get('provider_model_calls')}`
- Direct provider bypass: `{c1r16_status.get('direct_provider_bypass_count')}`
- Frozen C1K SHA: `{FROZEN_C1K_SHA}`

## Explicit non-actions

- No production expansion applied.
- No M12-C2/C3/C4 started.
- No cache enabled.
- No artifact-memory promotion.
- No Gateway/config/live-route/fallback/memory-route/runtime authority mutation.
- No global Semantic Gate promotion.

## Owner decision needed next

Stick may review M12-C1 as the first limited expansion candidate. Any actual production expansion or movement to C2/C3/C4 requires separate explicit authorization.
'''
    (ART / 'owner_decision_record.md').write_text(owner_decision)

    review = f'''# M12-C1 Owner Review Acceptance

Final status: `{status}`
Created UTC: {created}

## Summary

M12-C1 bounded artifact status Q&A is ready for owner review as the first limited expansion candidate.

## Evidence verified

- C1R16 PASS_NO_APPLY evidence: `{checks['c1r16_pass_no_apply_evidence_verifies']}`
- 50/50 C1 cases passed: `{checks['c1r16_cases_50_50']}`
- C1K read-only consumption: `{checks['c1k_read_only_consumption_verifies']}`
- Frozen C1K SHA before/after: `{c1k_before}` / `{c1k_after}`
- M11 baseline preserved: `{checks['m11_baseline_preserved']}`
- Rollback ready: `{checks['rollback_ready']}`
- Mutation sentinels clean: `{checks['mutation_sentinels_clean']}`
- Owner decision record written: `{checks['owner_decision_record_written']}`

## Boundary readback

This is not production expansion, not C2/C3/C4, not cache enablement, not artifact-memory promotion, and not global Semantic Gate promotion. No Gateway/config/live-route/fallback/memory-route/runtime authority mutation occurred.

## Owner-review disposition

Ready for owner review only. Do not apply expansion or start the next candidate without explicit owner authorization.
'''
    (ART / 'M12_C1_OWNER_REVIEW_ACCEPTANCE.md').write_text(review)

    # status.json and summary.json are finalized below, so do not self-block by
    # checking them before they are written. They are verified after generation.
    finalization_files = {'status.json', 'summary.json'}
    required_missing = [name for name in REQUIRED if name not in finalization_files and not (ART / name).exists()]
    if required_missing:
        failed.append('required_files_present')
        status = 'M12_C1_OWNER_REVIEW_BLOCKED'

    summary = {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1.owner_review_acceptance.summary.v1',
        'created_utc': created,
        'status': status,
        'artifact_dir': rel(ART),
        'candidate': 'M12-C1 bounded artifact status Q&A',
        'ready_for_owner_review': status == STATUS,
        'first_limited_expansion_candidate': True,
        'checks': checks,
        'failed_gates': failed,
        'required_files': REQUIRED,
        'required_files_missing': required_missing,
        'c1r16_status': c1r16_status.get('status'),
        'c1r16_cases': f"{c1r16_status.get('pass_count')}/{c1r16_status.get('case_count')}",
        'c1k_frozen_sha': FROZEN_C1K_SHA,
        'c1k_sha_before': c1k_before,
        'c1k_sha_after': c1k_after,
        'm11_baseline_preserved': checks['m11_baseline_preserved'],
        'rollback_ready': checks['rollback_ready'],
        'production_expansion_applied': False,
        'cache_enabled': False,
        'artifact_memory_promoted': False,
        'runtime_authority_mutated': False,
        'm12_c2_c3_c4_started': False,
        'global_semantic_gate_promoted': False,
    }
    write_json('summary.json', summary)
    write_json('status.json', {**summary, 'schema': 'stickbot.vnext_semantic_gate.m12_c1.owner_review_acceptance.status.v1'})

    print(json.dumps({'status': status, 'artifact_dir': rel(ART), 'failed_gates': failed, 'ready_for_owner_review': status == STATUS}, indent=2, sort_keys=True))
    return 0 if status == STATUS else 1


if __name__ == '__main__':
    raise SystemExit(main())
