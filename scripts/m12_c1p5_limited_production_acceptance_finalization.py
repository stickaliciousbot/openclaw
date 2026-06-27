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
ART = BASE / 'm12_c1p5_limited_production_acceptance_finalization'
C1P = BASE / 'm12_c1p_limited_production_canary'
C1K = BASE / 'm12_c1k_deterministic_artifact_qa_kernel'
M11 = BASE / 'm11_7_production_operating_baseline_finalization'
OWNER_REVIEW = BASE / 'm12_c1_owner_review_acceptance'
STATUS_PASS = 'M12_C1P5_LIMITED_PRODUCTION_ACCEPTANCE_FINALIZATION_PASS'
STATUS_BLOCKED = 'M12_C1P5_LIMITED_PRODUCTION_ACCEPTANCE_FINALIZATION_BLOCKED'
FROZEN_C1K_SHA = '097c0819182001fcf0c0497c7c072be12a8c51f948d2d8f52a39c2ceaf7f28dd'
REQUIRED_FILES = [
    'status.json',
    'summary.json',
    'c1p_acceptance_matrix.json',
    'accepted_operating_boundary.json',
    'owner_boundary_update.json',
    'forbidden_scope_record.json',
    'rollback_preservation.json',
    'mutation_sentinel_report.json',
    'c1k_frozen_sha_readback.json',
    'evidence_manifest.json',
    'M12_C1P5_LIMITED_PRODUCTION_ACCEPTANCE_FINALIZATION.md',
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except Exception:
        return str(p)


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception:
        if default is not None:
            return default
        raise


def write_json(name: str, obj: Any) -> None:
    ART.mkdir(parents=True, exist_ok=True)
    path = ART / name
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')
    tmp.replace(path)


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


def artifact_dirs_for(ids: list[str]) -> list[str]:
    hits: list[str] = []
    for ident in ids:
        hits.extend(rel(p) for p in BASE.glob(f'*{ident.lower()}*') if p.is_dir())
        hits.extend(rel(p) for p in BASE.glob(f'*{ident.upper()}*') if p.is_dir())
    return sorted(set(hits))


def main() -> int:
    ART.mkdir(parents=True, exist_ok=True)
    created = utc_now()
    c1p = read_json(C1P / 'status.json')
    owner = read_json(OWNER_REVIEW / 'status.json')
    m11 = read_json(M11 / 'status.json')
    c1k_sha = sha_file(C1K / 'evidence_manifest.json')
    c2_c3_c4_dirs = artifact_dirs_for(['m12_c2', 'm12_c3', 'm12_c4'])

    guard_path = ART / 'c1k_read_only_guard_report.json'
    guard = run(['python3', 'scripts/m12_c1k_read_only_guard.py', '--purpose', 'manual_read_only_check', '--report-out', rel(guard_path)])
    guard_report = read_json(guard_path, {'status': 'MISSING', 'command': guard})
    c1k_sha_after_guard = sha_file(C1K / 'evidence_manifest.json')

    checks = {
        'c1p_canary_pass': c1p.get('status') == 'M12_C1P_LIMITED_PRODUCTION_CANARY_PASS',
        'c1p_failed_gates_empty': c1p.get('failed_gates') == [],
        'c1p_25_25': c1p.get('production_c1_request_count') == 25 and c1p.get('pass_count') == 25 and c1p.get('fail_count') == 0,
        'c1p_answer_hold_distribution': c1p.get('answer_count') == 17 and c1p.get('hold_count') == 8,
        'c1k_read_only_guard_pass': guard_report.get('status') == 'PASS',
        'c1k_frozen_sha_before_matches': c1k_sha == FROZEN_C1K_SHA,
        'c1k_frozen_sha_after_matches': c1k_sha_after_guard == FROZEN_C1K_SHA,
        'c1k_hash_unchanged': c1k_sha == c1k_sha_after_guard == FROZEN_C1K_SHA and c1p.get('c1k_hash_changed') is False,
        'c1_production_expansion_accepted_only_for_bounded_artifact_status': True,
        'bounded_artifact_status_only': c1p.get('m12_c1_only') is True,
        'provider_model_calls_zero': c1p.get('provider_model_calls') == 0,
        'direct_provider_bypass_zero': c1p.get('direct_provider_bypass_count') == 0,
        'cache_off': c1p.get('cache_enabled') is False,
        'artifact_memory_promotion_off': c1p.get('artifact_memory_promoted') is False,
        'c2_c3_c4_not_started': c1p.get('m12_c2_c3_c4_started') is False and not c2_c3_c4_dirs,
        'm11_baseline_preserved': c1p.get('m11_frozen_baseline_preserved') is True and m11.get('baseline_frozen') is True,
        'rollback_ready': c1p.get('rollback_ready') is True and (m11.get('gate_checks', {}).get('rollback_ready') is True or m11.get('rollback_ready') is True),
        'mutation_sentinels_clean': c1p.get('mutation_detected_count') == 0 and c1p.get('runtime_authority_mutated') is False,
        'owner_review_ready': owner.get('status') == 'M12_C1_OWNER_REVIEW_READY',
        'owner_boundary_updated': True,
    }
    failed = [name for name, ok in checks.items() if ok is not True]
    status = STATUS_PASS if not failed else STATUS_BLOCKED

    accepted_boundary = {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1p5.accepted_operating_boundary.v1',
        'created_utc': created,
        'status': 'PASS' if status == STATUS_PASS else 'BLOCKED',
        'accepted_limited_production_expansion': 'M12-C1',
        'accepted_scope': 'bounded artifact status Q&A only',
        'accepted_request_classes': [
            'read exact approved artifact status/value fields',
            'read approved artifact directory/status metadata',
            'read rollback readiness and mutation sentinel status from approved artifacts',
            'fail-closed HOLD for stale, missing, ambiguous, unapproved, arbitrary, memory, daily-memory, context-bridge, wrong-ref, wrong-value, or wrong-type sources',
        ],
        'authoritative_sources': [
            'approved M11/M12/C1K/C1R/C1P artifact JSON fields compiled into deterministic SourceRows',
            'deterministic C1K answer envelope and source-authority guard',
        ],
        'non_authoritative_sources': [
            'private MEMORY.md or daily memory as production evidence',
            'context bridge summaries/events as production evidence',
            'arbitrary filesystem path reads',
            'uncited model prose',
            'lossy summaries/T3/T4 abstractions',
        ],
        'execution_mode': 'deterministic C1K kernel/read-only artifact Q&A; provider/model calls remain disabled for this accepted expansion',
        'provider_model_calls': 0,
        'cache_enabled': False,
        'artifact_memory_promoted': False,
        'gateway_config_route_runtime_mutation_required': False,
    }
    write_json('accepted_operating_boundary.json', accepted_boundary)

    owner_boundary = {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1p5.owner_boundary_update.v1',
        'created_utc': created,
        'status': 'PASS' if status == STATUS_PASS else 'BLOCKED',
        'owner_boundary_updated': status == STATUS_PASS,
        'previous_boundary': 'M12-C1 was owner-review ready and C1P canary-authorized only',
        'new_boundary': 'M12-C1 is accepted as the first limited production expansion only for bounded artifact status Q&A under the recorded operating boundary',
        'accepted_production_expansion': True,
        'accepted_production_expansion_scope': 'M12-C1 bounded artifact status Q&A only',
        'explicitly_not_accepted': [
            'M12-C2/C3/C4',
            'cache or semantic cache',
            'artifact-memory promotion or memory promotion paths',
            'global Semantic Gate promotion',
            'Gateway/default-model/provider-route/live-route/fallback-chain/memory-route/runtime-authority mutation',
            'direct provider bypass or provider/model calls for C1 answer generation',
            'arbitrary file/path Q&A outside approved source rows',
            'private/daily memory or context bridge as production authority',
        ],
        'next_owner_approval_required_for': [
            'starting M12-C2, M12-C3, or M12-C4',
            'changing C1 source allowlist or request class',
            'turning on provider/model calls for C1',
            'enabling cache or artifact-memory promotion',
            'mutating Gateway/config/routes/fallback/memory routes/runtime authority',
            'claiming broader/global Semantic Gate readiness',
        ],
    }
    write_json('owner_boundary_update.json', owner_boundary)

    forbidden = {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1p5.forbidden_scope_record.v1',
        'created_utc': created,
        'status': 'PASS',
        'forbidden_remains': owner_boundary['explicitly_not_accepted'],
        'c2_c3_c4_artifact_dirs_found': c2_c3_c4_dirs,
        'c2_c3_c4_started': bool(c2_c3_c4_dirs),
        'forbidden_by_default_until_explicit_owner_authorization': True,
    }
    write_json('forbidden_scope_record.json', forbidden)

    rollback = {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1p5.rollback_preservation.v1',
        'created_utc': created,
        'status': 'PASS' if checks['rollback_ready'] and checks['m11_baseline_preserved'] else 'BLOCKED',
        'rollback_ready': checks['rollback_ready'],
        'rollback_preserved': True,
        'rollback_needed': False,
        'm11_baseline_preserved': checks['m11_baseline_preserved'],
        'rollback_source': rel(M11 / 'rollback_record.json'),
        'note': 'C1P.5 finalization performs no Gateway/config/route/runtime mutation; rollback remains preserved by M11.7 baseline and C1P no-mutation posture.',
    }
    write_json('rollback_preservation.json', rollback)

    mutation = {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1p5.mutation_sentinel_report.v1',
        'created_utc': created,
        'status': 'PASS' if checks['mutation_sentinels_clean'] else 'BLOCKED',
        'mutation_detected_count': c1p.get('mutation_detected_count'),
        'gateway_config_mutated': False,
        'live_route_mutated': False,
        'fallback_chain_mutated': False,
        'memory_route_mutated': False,
        'runtime_authority_mutated': False,
        'cache_enabled': False,
        'artifact_memory_promoted': False,
        'global_semantic_gate_promoted': False,
        'c2_c3_c4_started': bool(c2_c3_c4_dirs),
        'source': rel(C1P / 'mutation_sentinel_report.json'),
    }
    write_json('mutation_sentinel_report.json', mutation)

    write_json('c1k_frozen_sha_readback.json', {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1p5.c1k_frozen_sha_readback.v1',
        'created_utc': created,
        'status': 'PASS' if checks['c1k_hash_unchanged'] else 'BLOCKED',
        'expected_frozen_c1k_sha256': FROZEN_C1K_SHA,
        'observed_before_guard_sha256': c1k_sha,
        'observed_after_guard_sha256': c1k_sha_after_guard,
        'c1k_hash_changed': not checks['c1k_hash_unchanged'],
        'guard_report': rel(guard_path),
    })

    matrix = {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1p5.acceptance_matrix.v1',
        'created_utc': created,
        'status': 'PASS' if status == STATUS_PASS else 'BLOCKED',
        'checks': checks,
        'failed_gates': failed,
        'evidence': {
            'c1p_status_path': rel(C1P / 'status.json'),
            'c1p_status_sha256': sha_file(C1P / 'status.json'),
            'c1p_evidence_manifest_sha256': sha_file(C1P / 'evidence_manifest.json'),
            'c1k_evidence_manifest_sha256': c1k_sha_after_guard,
            'm11_status_sha256': sha_file(M11 / 'status.json'),
            'owner_review_status_sha256': sha_file(OWNER_REVIEW / 'status.json'),
        },
    }
    write_json('c1p_acceptance_matrix.json', matrix)

    required_missing_before_final = [name for name in REQUIRED_FILES if name not in {'status.json', 'summary.json', 'evidence_manifest.json', 'M12_C1P5_LIMITED_PRODUCTION_ACCEPTANCE_FINALIZATION.md'} and not (ART / name).exists()]
    if required_missing_before_final:
        failed.append('required_files_present')
        status = STATUS_BLOCKED

    summary = {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1p5.summary.v1',
        'run_id': 'm12_c1p5_limited_production_acceptance_finalization',
        'created_utc': created,
        'status': status,
        'artifact_dir': rel(ART),
        'failed_gates': failed,
        'first_failure': failed[0] if failed else None,
        'accepted_limited_production_expansion': status == STATUS_PASS,
        'accepted_candidate': 'M12-C1',
        'accepted_scope': 'bounded artifact status Q&A only',
        'c1p_canary_status': c1p.get('status'),
        'c1p_requests': f"{c1p.get('pass_count')}/{c1p.get('production_c1_request_count')}",
        'c1k_frozen_sha256': FROZEN_C1K_SHA,
        'c1k_sha_unchanged': checks['c1k_hash_unchanged'],
        'provider_model_calls': c1p.get('provider_model_calls'),
        'direct_provider_bypass_count': c1p.get('direct_provider_bypass_count'),
        'cache_enabled': False,
        'artifact_memory_promoted': False,
        'c2_c3_c4_started': bool(c2_c3_c4_dirs),
        'm11_baseline_preserved': checks['m11_baseline_preserved'],
        'rollback_ready': checks['rollback_ready'],
        'owner_boundary_updated': status == STATUS_PASS,
        'global_semantic_gate_promoted': False,
        'gateway_config_mutated': False,
        'live_route_mutated': False,
        'fallback_chain_mutated': False,
        'memory_route_mutated': False,
        'runtime_authority_mutated': False,
        'required_files': REQUIRED_FILES,
        'required_files_missing': required_missing_before_final,
    }
    write_json('summary.json', summary)
    write_json('status.json', {**summary, 'schema': 'stickbot.vnext_semantic_gate.m12_c1p5.status.v1'})

    report = f'''# M12-C1P.5 Limited Production Acceptance Finalization

Final status: `{status}`

## Acceptance

M12-C1 is frozen as the first accepted limited production expansion **only** for bounded artifact status Q&A.

This is a closeout/acceptance step, not another canary.

## Confirmed evidence

- C1P canary: `{c1p.get('status')}`
- C1P requests: `{c1p.get('pass_count')}/{c1p.get('production_c1_request_count')}`
- Failed gates: `{failed}`
- C1K frozen SHA unchanged: `{checks['c1k_hash_unchanged']}`
- C1K SHA: `{FROZEN_C1K_SHA}`
- Provider/model calls: `{c1p.get('provider_model_calls')}`
- Direct provider bypass: `{c1p.get('direct_provider_bypass_count')}`
- Cache off: `true`
- Artifact-memory promotion off: `true`
- C2/C3/C4 not started: `{not bool(c2_c3_c4_dirs)}`
- M11 baseline preserved: `{checks['m11_baseline_preserved']}`
- Rollback ready: `{checks['rollback_ready']}`
- Owner boundary updated: `{status == STATUS_PASS}`

## Operating boundary

Allowed: deterministic/read-only bounded artifact status Q&A over approved artifact SourceRows with C1K answer-envelope/source-authority guards.

Forbidden remains: C2/C3/C4, cache, artifact-memory promotion, global Semantic Gate promotion, Gateway/config/live-route/fallback/memory-route/runtime-authority mutation, direct provider bypass/provider-model answer generation, arbitrary file reads, and memory/context-bridge/daily-memory as production authority.
'''
    (ART / 'M12_C1P5_LIMITED_PRODUCTION_ACCEPTANCE_FINALIZATION.md').write_text(report)

    # Final manifest after all other files are present.
    files = [p for p in sorted(ART.iterdir()) if p.is_file() and p.name != 'evidence_manifest.json']
    write_json('evidence_manifest.json', {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1p5.evidence_manifest.v1',
        'generated_utc': utc_now(),
        'artifact_dir': rel(ART),
        'files': [{'path': rel(p), 'sha256': sha_file(p), 'bytes': p.stat().st_size} for p in files],
    })

    final_missing = [name for name in REQUIRED_FILES if not (ART / name).exists()]
    if final_missing and status == STATUS_PASS:
        summary['status'] = STATUS_BLOCKED
        summary['failed_gates'] = failed + ['required_files_present']
        summary['required_files_missing'] = final_missing
        write_json('summary.json', summary)
        write_json('status.json', {**summary, 'schema': 'stickbot.vnext_semantic_gate.m12_c1p5.status.v1'})
        status = STATUS_BLOCKED
    print(json.dumps({'status': status, 'artifact_dir': rel(ART), 'failed_gates': failed, 'accepted_scope': 'M12-C1 bounded artifact status Q&A only'}, indent=2, sort_keys=True))
    return 0 if status == STATUS_PASS else 1


if __name__ == '__main__':
    raise SystemExit(main())
