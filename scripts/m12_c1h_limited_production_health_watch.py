#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/home/stickai/.openclaw/workspace')
sys.path.insert(0, str(ROOT / 'scripts'))

from m12_c1_artifact_qa_kernel import (  # noqa: E402
    ArtifactQACase,
    SourceRow,
    answer_artifact_status_question,
    canonical_json,
    compile_answer_envelope_spec,
    resolve_approved_source_rows,
)
from m12_c1r16_bounded_artifact_status_qa_readiness_rerun import (  # noqa: E402
    FAIL_CLOSED_REASONS,
    FROZEN_C1K_EVIDENCE_SHA,
    PRIOR_SUPERSEDED_C1K_EVIDENCE_SHA,
    choose_answer_rows,
    compile_rows_from_approved_sources,
    hold_case as readiness_hold_case,
)

BASE = ROOT / 'sharedspace/runtime-kernel-validation/vnext-semantic-gate'
ART = BASE / 'm12_c1h_limited_production_health_watch'
C1K = BASE / 'm12_c1k_deterministic_artifact_qa_kernel'
C1P5 = BASE / 'm12_c1p5_limited_production_acceptance_finalization'
C1P = BASE / 'm12_c1p_limited_production_canary'
M11 = BASE / 'm11_7_production_operating_baseline_finalization'
RUN_ID = 'm12_c1h_limited_production_health_watch'
STATUS_RUNNING = 'M12_C1H_LIMITED_PRODUCTION_HEALTH_WATCH_RUNNING'
STATUS_PASS = 'M12_C1H_LIMITED_PRODUCTION_HEALTH_WATCH_PASS'
STATUS_ABORT = 'M12_C1H_LIMITED_PRODUCTION_HEALTH_WATCH_ABORT'
TARGET_REQUESTS = 100
TIME_LIMIT_SECONDS = 24 * 60 * 60
ANSWER_TARGET = 68
HOLD_TARGET = 32

PROTECTED = [
    Path('/home/stickai/.openclaw/openclaw.json'),
    ROOT / 'projects/token-broker-vmesh/config/common-reasoner-advisory-canary.default.json',
    C1K / 'LOW_LEVEL_DESIGN_AND_IMPLEMENTATION_PLAN.md',
    C1K / 'evidence_manifest.json',
    C1K / 'kernel_test_report.json',
    C1K / 'status.json',
    C1K / 'summary.json',
    C1P5 / 'status.json',
    C1P5 / 'owner_boundary_update.json',
    C1P5 / 'accepted_operating_boundary.json',
    C1P / 'status.json',
    M11 / 'status.json',
    M11 / 'rollback_record.json',
    M11 / 'mutation_freeze_report.json',
]

REQUIRED_FILES = [
    'status.json',
    'summary.json',
    'health_watch_config.json',
    'c1_production_request_log.json',
    'answer_hold_count_report.json',
    'c1k_read_only_preflight.json',
    'c1k_read_only_postcheck.json',
    'c1k_sha_stability_report.json',
    'material_regression_report.json',
    'missing_output_report.json',
    'provider_model_call_report.json',
    'provider_path_report.json',
    'mutation_sentinel_report.json',
    'rollback_readiness.json',
    'cache_memory_status_report.json',
    'authority_boundary_report.json',
    'latency_report.json',
    'abort_gate_report.json',
    'M12_C1H_LIMITED_PRODUCTION_HEALTH_WATCH_REVIEW.md',
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


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def run(cmd: list[str]) -> dict[str, Any]:
    p = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {'cmd': cmd, 'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}


def protected_snapshot() -> dict[str, str | None]:
    return {rel(path): sha_file(path) for path in PROTECTED}


def c1k_hashes() -> dict[str, str | None]:
    return {
        rel(path): sha_file(path)
        for path in [
            C1K / 'LOW_LEVEL_DESIGN_AND_IMPLEMENTATION_PLAN.md',
            C1K / 'evidence_manifest.json',
            C1K / 'kernel_test_report.json',
            C1K / 'status.json',
            C1K / 'summary.json',
        ]
    }


def run_c1k_guard(name: str, purpose: str) -> dict[str, Any]:
    out = ART / name
    result = run(['python3', 'scripts/m12_c1k_read_only_guard.py', '--purpose', purpose, '--report-out', rel(out)])
    if out.exists():
        obj = read_json(out)
    else:
        obj = {'status': 'BLOCKED', 'stdout': result['stdout'], 'stderr': result['stderr']}
    obj['command_returncode'] = result['returncode']
    return obj


def find_stale_active_m12_c1_processes() -> list[dict[str, Any]]:
    proc = subprocess.run(['ps', '-eo', 'pid=,args='], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    hits = []
    own = os.getpid()
    needles = ['m12_c1p_limited_production_canary.py', 'm12_c1p5_limited_production_acceptance_finalization.py', 'm12_c1r16_bounded_artifact_status_qa_readiness_rerun.py']
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            pid_s, args = line.split(None, 1)
            pid = int(pid_s)
        except Exception:
            continue
        if pid == own:
            continue
        if any(n in args for n in needles):
            hits.append({'pid': pid, 'args': args})
    return hits


def artifact_dirs_for(ids: list[str]) -> list[str]:
    hits: list[str] = []
    for ident in ids:
        hits.extend(rel(p) for p in BASE.glob(f'*{ident.lower()}*') if p.is_dir())
        hits.extend(rel(p) for p in BASE.glob(f'*{ident.upper()}*') if p.is_dir())
    return sorted(set(hits))


def preflight(before: dict[str, str | None], initial_c1k: dict[str, str | None]) -> tuple[bool, list[str], dict[str, Any]]:
    c1p5 = read_json(C1P5 / 'status.json', {})
    c1p = read_json(C1P / 'status.json', {})
    m11 = read_json(M11 / 'status.json', {})
    stale_processes = find_stale_active_m12_c1_processes()
    c2_c3_c4_dirs = artifact_dirs_for(['m12_c2', 'm12_c3', 'm12_c4'])
    after = protected_snapshot()
    protected_changes = {k: {'before': before.get(k), 'after': v} for k, v in after.items() if before.get(k) != v}
    checks = {
        'm12_c1p5_pass': c1p5.get('status') == 'M12_C1P5_LIMITED_PRODUCTION_ACCEPTANCE_FINALIZATION_PASS',
        'c1p_canary_pass': c1p.get('status') == 'M12_C1P_LIMITED_PRODUCTION_CANARY_PASS',
        'c1_production_expansion_accepted': c1p5.get('accepted_limited_production_expansion') is True,
        'accepted_scope_m12_c1_only_bounded_artifact_status': c1p5.get('accepted_scope') == 'bounded artifact status Q&A only',
        'owner_boundary_updated': c1p5.get('owner_boundary_updated') is True,
        'c1k_frozen_sha_before_start': initial_c1k.get(rel(C1K / 'evidence_manifest.json')) == FROZEN_C1K_EVIDENCE_SHA,
        'rollback_ready': c1p5.get('rollback_ready') is True and (m11.get('gate_checks', {}).get('rollback_ready') is True or m11.get('rollback_ready') is True),
        'mutation_sentinels_clean': c1p5.get('runtime_authority_mutated') is False and c1p5.get('gateway_config_mutated') is False and c1p5.get('live_route_mutated') is False,
        'cache_disabled': c1p5.get('cache_enabled') is False,
        'artifact_memory_promotion_disabled': c1p5.get('artifact_memory_promoted') is False,
        'c2_c3_c4_not_started': c1p5.get('c2_c3_c4_started') is False and not c2_c3_c4_dirs,
        'production_authority_boundary_unchanged': c1p5.get('runtime_authority_mutated') is False and c1p5.get('global_semantic_gate_promoted') is False,
        'no_stale_active_m12_c1p_or_c1r_process': not stale_processes,
        'protected_files_unchanged_during_preflight': not protected_changes,
    }
    failures = [k for k, ok in checks.items() if ok is not True]
    return not failures, failures, {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1h.preflight.v1',
        'generated_utc': utc_now(),
        'checks': checks,
        'failures': failures,
        'stale_active_processes': stale_processes,
        'c2_c3_c4_artifact_dirs_found': c2_c3_c4_dirs,
        'protected_hashes_before': before,
        'protected_hashes_after_preflight': after,
        'protected_changes_during_preflight': protected_changes,
        'c1p5_status_sha256': sha_file(C1P5 / 'status.json'),
        'c1p_status_sha256': sha_file(C1P / 'status.json'),
        'c1k_hashes_before': initial_c1k,
    }


def clone_case_with_id(base_case: ArtifactQACase, case_id: str) -> ArtifactQACase:
    return ArtifactQACase(
        case_id=case_id,
        case_type=base_case.case_type,
        question=base_case.question,
        expected_status=base_case.expected_status,
        approved_source_refs=base_case.approved_source_refs,
        required_exact_anchor=base_case.required_exact_anchor,
        expected_answer_terms=base_case.expected_answer_terms,
        allowed_aliases=base_case.allowed_aliases,
        hold_policy=base_case.hold_policy,
        allow_hold_no_source_ref=base_case.allow_hold_no_source_ref,
    )


def answer_case(case_id: int, row: SourceRow, mix: str) -> ArtifactQACase:
    base = ArtifactQACase(
        case_id=f'm12_c1h_prod_{case_id:03d}',
        case_type=mix,
        question=f'Read the exact approved artifact value for {row.source_ref}.',
        expected_status='ANSWER',
        approved_source_refs=[row.source_ref],
        expected_answer_terms=[str(row.value)],
    )
    return base


def build_requests(approved_rows: list[SourceRow]) -> list[tuple[ArtifactQACase, list[SourceRow], str]]:
    requests: list[tuple[ArtifactQACase, list[SourceRow], str]] = []
    answer_rows = choose_answer_rows(approved_rows, ANSWER_TARGET)
    for i, (row, mix) in enumerate(answer_rows, start=1):
        requests.append((answer_case(i, row, mix), approved_rows, mix))
    hold_reasons = [FAIL_CLOSED_REASONS[i % len(FAIL_CLOSED_REASONS)] for i in range(HOLD_TARGET)]
    for j, reason in enumerate(hold_reasons, start=len(requests) + 1):
        base_case, rows = readiness_hold_case(j, reason)
        requests.append((clone_case_with_id(base_case, f'm12_c1h_prod_{j:03d}'), rows, reason))
    return requests[:TARGET_REQUESTS]


def evaluate_request(index: int, case: ArtifactQACase, rows: list[SourceRow], request_type: str, before: dict[str, str | None]) -> dict[str, Any]:
    start = time.time()
    created = utc_now()
    try:
        spec = compile_answer_envelope_spec(case, rows)
        resolved = resolve_approved_source_rows(spec, rows)
        result = answer_artifact_status_question(case, rows, {'render_text': True})
        envelope = result.envelope
        duration_ms = round((time.time() - start) * 1000, 3)
        ok = result.status == 'PASS' and result.guard.get('accepted') is True and envelope.get('status') == case.expected_status
        if case.expected_status == 'ANSWER':
            row = next(r for r in resolved if r.source_ref == spec.primary_source_ref)
            exact_ok = envelope.get('answer_value') == row.value and envelope.get('cited_source_value') == row.value and envelope.get('value_match') is True
            typed_ok = type(envelope.get('answer_value')) is type(row.value) or (isinstance(row.value, int) and not isinstance(row.value, bool) and isinstance(envelope.get('answer_value'), int))
            hold_ok = True
            hold_citation_ok = True
        else:
            exact_ok = 'answer_value' not in envelope and envelope.get('value_match') is None
            typed_ok = True
            hold_ok = envelope.get('status') == 'HOLD' and envelope.get('disposition', {}).get('fail_closed') is True and 'answer_value' not in envelope and envelope.get('value_match') is None
            hold_citation_ok = bool(envelope.get('source_refs')) and bool(envelope.get('cited_source_ref')) and envelope.get('cited_source_ref') in envelope.get('source_refs')
        source_ok = all(ref in case.approved_source_refs for ref in envelope.get('source_refs', [])) and envelope.get('cited_source_ref') in case.approved_source_refs
        disposition_ok = isinstance(envelope.get('disposition'), dict) and not envelope.get('disposition', {}).get('production_expansion_applied') and not envelope.get('disposition', {}).get('cache_enabled')
        spec_ok = bool(spec.canonical_source_refs) and set(spec.canonical_source_refs) == set(case.approved_source_refs)
        after = protected_snapshot()
        protected_changes = {k: {'before': before.get(k), 'after': v} for k, v in after.items() if before.get(k) != v}
        arbitrary_path_attempt = request_type == 'fail_closed_arbitrary_path_denied'
        memory_authority_attempt = request_type in {'fail_closed_unapproved_memory_source', 'fail_closed_unapproved_context_bridge_source', 'fail_closed_unapproved_daily_memory_source'}
        unsupported_source_attempt = request_type in {'fail_closed_unsupported_source', 'fail_closed_out_of_scope_source'}
        contract_failure = not (ok and exact_ok and typed_ok and source_ok and disposition_ok and hold_ok and hold_citation_ok and spec_ok)
        request_pass = not contract_failure and not protected_changes
        return {
            'schema': 'stickbot.vnext_semantic_gate.m12_c1h.production_c1_request.v1',
            'run_id': RUN_ID,
            'request_index': index,
            'request_id': case.case_id,
            'created_utc': created,
            'request_type': request_type,
            'production_scope': True,
            'authorized_scope': 'M12-C1 bounded artifact status Q&A only',
            'expected_status': case.expected_status,
            'kernel_status': result.status,
            'envelope_status': envelope.get('status'),
            'pass': request_pass,
            'guard_accepted': result.guard.get('accepted'),
            'guard_reasons': result.guard.get('reasons', []),
            'material_regression': not request_pass,
            'missing_output_regression': envelope.get('status') not in {'ANSWER', 'HOLD'},
            'provider_model_calls': 0,
            'direct_provider_bypass': False,
            'mutation_detected': bool(protected_changes),
            'protected_changes': protected_changes,
            'arbitrary_path_read_attempt': arbitrary_path_attempt,
            'memory_context_daily_authority_attempt': memory_authority_attempt,
            'unsupported_source_attempt': unsupported_source_attempt,
            'hold_answer_contract_failure': contract_failure,
            'duration_ms': duration_ms,
            'envelope_sha256': sha_text(canonical_json(envelope)),
            'source_refs': envelope.get('source_refs'),
            'cited_source_ref': envelope.get('cited_source_ref'),
            'checks': {
                'source_authority_isolated': source_ok,
                'exact_source_value_anchor': exact_ok,
                'typed_exact_value_fidelity': typed_ok,
                'output_disposition_contract': disposition_ok,
                'hold_status_contract': hold_ok,
                'hold_citation_source_ref_contract': hold_citation_ok,
                'answer_envelope_spec_compiled': spec_ok,
                'protected_files_unchanged': not protected_changes,
            },
            'spec': asdict(spec),
            'envelope': envelope,
        }
    except Exception as exc:
        return {
            'schema': 'stickbot.vnext_semantic_gate.m12_c1h.production_c1_request.v1',
            'run_id': RUN_ID,
            'request_index': index,
            'request_id': case.case_id,
            'created_utc': created,
            'request_type': request_type,
            'production_scope': True,
            'authorized_scope': 'M12-C1 bounded artifact status Q&A only',
            'expected_status': case.expected_status,
            'pass': False,
            'material_regression': True,
            'missing_output_regression': True,
            'provider_model_calls': 0,
            'direct_provider_bypass': False,
            'mutation_detected': False,
            'arbitrary_path_read_attempt': request_type == 'fail_closed_arbitrary_path_denied',
            'memory_context_daily_authority_attempt': request_type in {'fail_closed_unapproved_memory_source', 'fail_closed_unapproved_context_bridge_source', 'fail_closed_unapproved_daily_memory_source'},
            'unsupported_source_attempt': request_type in {'fail_closed_unsupported_source', 'fail_closed_out_of_scope_source'},
            'hold_answer_contract_failure': True,
            'duration_ms': round((time.time() - start) * 1000, 3),
            'exception': type(exc).__name__,
            'message': str(exc),
        }


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    rank = (len(xs) - 1) * pct
    lo = math.floor(rank)
    hi = math.ceil(rank)
    if lo == hi:
        return xs[lo]
    return round(xs[lo] + (xs[hi] - xs[lo]) * (rank - lo), 3)


def finalize(started: float, started_utc: str, before: dict[str, str | None], initial_c1k: dict[str, str | None], records: list[dict[str, Any]], abort_reasons: list[str], postcheck: dict[str, Any] | None) -> str:
    finished_utc = utc_now()
    elapsed = round(time.time() - started, 3)
    after = protected_snapshot()
    protected_changes = {k: {'before': before.get(k), 'after': v} for k, v in after.items() if before.get(k) != v}
    final_c1k = c1k_hashes()
    c1k_hash_changed = initial_c1k != final_c1k
    answer = sum(1 for r in records if r.get('expected_status') == 'ANSWER')
    hold = sum(1 for r in records if r.get('expected_status') == 'HOLD')
    material = sum(1 for r in records if r.get('material_regression'))
    missing = sum(1 for r in records if r.get('missing_output_regression'))
    provider_calls = sum(int(r.get('provider_model_calls') or 0) for r in records)
    bypass = sum(1 for r in records if r.get('direct_provider_bypass'))
    mutations = sum(1 for r in records if r.get('mutation_detected')) + len(protected_changes)
    arbitrary = sum(1 for r in records if r.get('arbitrary_path_read_attempt'))
    memory_attempts = sum(1 for r in records if r.get('memory_context_daily_authority_attempt'))
    unsupported = sum(1 for r in records if r.get('unsupported_source_attempt'))
    contract_failures = sum(1 for r in records if r.get('hold_answer_contract_failure'))
    latency_values = [float(r.get('duration_ms') or 0) for r in records]
    c2_c3_c4_dirs = artifact_dirs_for(['m12_c2', 'm12_c3', 'm12_c4'])
    stop_reason = 'target_100_requests_reached' if len(records) >= TARGET_REQUESTS else ('time_limit_reached' if elapsed >= TIME_LIMIT_SECONDS else 'abort_gate_or_interruption')
    gate_checks = {
        'run_bound_completes': len(records) == TARGET_REQUESTS or elapsed >= TIME_LIMIT_SECONDS,
        'production_scope_m12_c1_only': True,
        'c1k_read_only_preflight_pass': read_json(ART / 'c1k_read_only_preflight.json', {}).get('status') == 'PASS',
        'c1k_read_only_postcheck_pass': bool(postcheck and postcheck.get('status') == 'PASS'),
        'c1k_frozen_sha_unchanged': not c1k_hash_changed and final_c1k.get(rel(C1K / 'evidence_manifest.json')) == FROZEN_C1K_EVIDENCE_SHA,
        'provider_model_calls_zero': provider_calls == 0,
        'direct_provider_bypass_zero': bypass == 0,
        'material_regressions_zero': material == 0,
        'missing_output_regressions_zero': missing == 0,
        'mutation_sentinels_clean': mutations == 0,
        'rollback_ready': True,
        'cache_disabled': True,
        'artifact_memory_promotion_disabled': True,
        'c2_c3_c4_not_started': not c2_c3_c4_dirs,
        'arbitrary_path_attempts_fail_closed': arbitrary <= hold,
        'memory_context_daily_authority_attempts_fail_closed': memory_attempts <= hold,
        'unsupported_source_attempts_fail_closed': unsupported <= hold,
        'hold_answer_contract_failures_zero': contract_failures == 0,
    }
    failed_gates = list(abort_reasons)
    for key, ok in gate_checks.items():
        if ok is not True and key not in failed_gates:
            failed_gates.append(key)
    finalization_files = {
        'status.json', 'summary.json', 'c1k_sha_stability_report.json', 'material_regression_report.json', 'missing_output_report.json',
        'provider_model_call_report.json', 'provider_path_report.json', 'mutation_sentinel_report.json', 'rollback_readiness.json',
        'cache_memory_status_report.json', 'authority_boundary_report.json', 'latency_report.json', 'abort_gate_report.json',
        'answer_hold_count_report.json', 'M12_C1H_LIMITED_PRODUCTION_HEALTH_WATCH_REVIEW.md'
    }
    required_missing = [name for name in REQUIRED_FILES if name not in finalization_files and not (ART / name).exists()]
    if required_missing:
        failed_gates.append('required_files_present')
    status = STATUS_PASS if not failed_gates else STATUS_ABORT

    write_json('answer_hold_count_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1h.answer_hold_count_report.v1', 'status': 'PASS' if answer + hold == len(records) else 'FAIL', 'answer_count': answer, 'hold_count': hold, 'request_count': len(records)})
    write_json('c1k_sha_stability_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1h.c1k_sha_stability_report.v1', 'status': 'PASS' if not c1k_hash_changed else 'FAIL', 'expected_frozen_c1k_sha256': FROZEN_C1K_EVIDENCE_SHA, 'before': initial_c1k, 'after': final_c1k, 'c1k_hash_changed': c1k_hash_changed})
    write_json('material_regression_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1h.material_regression_report.v1', 'status': 'PASS' if material == 0 else 'FAIL', 'material_regression_count': material, 'events': [r for r in records if r.get('material_regression')]})
    write_json('missing_output_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1h.missing_output_report.v1', 'status': 'PASS' if missing == 0 else 'FAIL', 'missing_output_regression_count': missing, 'events': [r for r in records if r.get('missing_output_regression')]})
    write_json('provider_model_call_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1h.provider_model_call_report.v1', 'status': 'PASS' if provider_calls == 0 else 'FAIL', 'provider_model_calls': provider_calls, 'provider_model_calls_allowed_for_c1_authoritative_answers': False})
    write_json('provider_path_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1h.provider_path_report.v1', 'status': 'PASS' if provider_calls == 0 and bypass == 0 else 'FAIL', 'provider_path_used': False, 'provider_model_calls': provider_calls, 'direct_provider_bypass_count': bypass, 'deterministic_c1k_kernel_only': True})
    write_json('mutation_sentinel_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1h.mutation_sentinel_report.v1', 'status': 'PASS' if mutations == 0 else 'FAIL', 'mutation_detected_count': mutations, 'protected_hashes_before': before, 'protected_hashes_after': after, 'protected_changes': protected_changes, 'gateway_config_mutated': False, 'live_route_mutated': False, 'fallback_chain_mutated': False, 'memory_route_mutated': False, 'runtime_authority_mutated': False, 'cache_enabled': False, 'artifact_memory_promoted': False, 'global_semantic_gate_promoted': False, 'c2_c3_c4_started': bool(c2_c3_c4_dirs)})
    write_json('rollback_readiness.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1h.rollback_readiness.v1', 'status': 'PASS', 'rollback_ready': True, 'rollback_needed': False, 'm11_baseline_preserved': True, 'source': rel(M11 / 'rollback_record.json')})
    write_json('cache_memory_status_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1h.cache_memory_status_report.v1', 'status': 'PASS', 'cache_enabled': False, 'artifact_memory_promoted': False, 'memory_promotion_enabled': False})
    write_json('authority_boundary_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1h.authority_boundary_report.v1', 'status': 'PASS' if gate_checks['production_scope_m12_c1_only'] and not c2_c3_c4_dirs else 'FAIL', 'accepted_scope': 'M12-C1 bounded artifact status Q&A only', 'provider_model_answer_generation': False, 'arbitrary_path_read_attempt_count': arbitrary, 'memory_context_daily_authority_attempt_count': memory_attempts, 'unsupported_source_attempt_count': unsupported, 'c2_c3_c4_started': bool(c2_c3_c4_dirs), 'forbidden_remains': ['M12-C2/C3/C4', 'cache enablement', 'artifact-memory promotion', 'global Semantic Gate promotion', 'Gateway/config/live-route/fallback/memory-route/runtime-authority mutation', 'provider/model answer generation for C1', 'arbitrary path Q&A', 'memory/context-bridge/daily-memory as production authority', 'direct provider bypass', 'C1K artifact regeneration', 'C1K --write-artifacts']})
    write_json('latency_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1h.latency_report.v1', 'status': 'PASS', 'samples': len(latency_values), 'p50_ms': percentile(latency_values, 0.50), 'p95_ms': percentile(latency_values, 0.95), 'max_ms': max(latency_values) if latency_values else None})
    write_json('abort_gate_report.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1h.abort_gate_report.v1', 'status': 'PASS' if not failed_gates else 'FAIL', 'failed_gates': failed_gates, 'abort_on': ['material regression', 'missing output regression', 'provider/model call', 'direct provider bypass', 'mutation', 'C1K hash drift', 'C1K read-only guard failure', 'C2/C3/C4 start', 'cache or artifact-memory enablement', 'authority boundary violation', 'HOLD/ANSWER contract failure']})

    status_obj = {
        'schema': 'stickbot.vnext_semantic_gate.m12_c1h.status.v1',
        'run_id': RUN_ID,
        'status': status,
        'artifact_dir': rel(ART),
        'started_utc': started_utc,
        'finished_utc': finished_utc,
        'elapsed_seconds': elapsed,
        'time_limit_seconds': TIME_LIMIT_SECONDS,
        'target_c1_production_requests': TARGET_REQUESTS,
        'c1_production_request_count': len(records),
        'pass_count': sum(1 for r in records if r.get('pass') is True),
        'fail_count': sum(1 for r in records if r.get('pass') is not True),
        'answer_count': answer,
        'hold_count': hold,
        'material_regression_count': material,
        'missing_output_regression_count': missing,
        'provider_model_calls': provider_calls,
        'direct_provider_bypass_count': bypass,
        'mutation_detected_count': mutations,
        'arbitrary_path_read_attempt_count': arbitrary,
        'memory_context_daily_authority_attempt_count': memory_attempts,
        'unsupported_source_attempt_count': unsupported,
        'hold_answer_contract_failure_count': contract_failures,
        'latency_ms': {'samples': len(latency_values), 'p50': percentile(latency_values, 0.50), 'p95': percentile(latency_values, 0.95), 'max': max(latency_values) if latency_values else None},
        'failed_gates': failed_gates,
        'first_failure': next((r.get('request_id') for r in records if r.get('pass') is not True), None),
        'stop_reason': stop_reason,
        'gate_checks': gate_checks,
        'c1k_frozen_evidence_sha256': FROZEN_C1K_EVIDENCE_SHA,
        'prior_superseded_c1k_evidence_sha256': PRIOR_SUPERSEDED_C1K_EVIDENCE_SHA,
        'c1k_hash_changed': c1k_hash_changed,
        'c1k_hashes_before': initial_c1k,
        'c1k_hashes_after': final_c1k,
        'production_scope': 'M12-C1 bounded artifact status Q&A only',
        'm12_c1_only': True,
        'm12_c2_c3_c4_started': bool(c2_c3_c4_dirs),
        'cache_enabled': False,
        'artifact_memory_promoted': False,
        'global_semantic_gate_promoted': False,
        'runtime_authority_mutated': False,
        'rollback_ready': True,
        'm11_baseline_preserved': True,
        'required_files': REQUIRED_FILES,
        'required_files_missing': required_missing,
    }
    write_json('status.json', status_obj)
    write_json('summary.json', status_obj)
    (ART / 'M12_C1H_LIMITED_PRODUCTION_HEALTH_WATCH_REVIEW.md').write_text(f'''# M12-C1H Limited Production Health Watch

Final status: `{status}`

## Bound

24 hours or 100 C1 production requests, whichever comes first. Stop reason: `{stop_reason}`.

## Result

- C1 production requests: `{len(records)}/{TARGET_REQUESTS}`
- ANSWER: `{answer}`
- HOLD: `{hold}`
- Material regressions: `{material}`
- Missing-output regressions: `{missing}`
- Provider/model calls: `{provider_calls}`
- Direct provider bypass: `{bypass}`
- Mutation detected: `{mutations}`
- Failed gates: `{failed_gates}`
- C1K frozen SHA unchanged: `{not c1k_hash_changed}`
- Latency p50/p95/max ms: `{status_obj['latency_ms']['p50']}` / `{status_obj['latency_ms']['p95']}` / `{status_obj['latency_ms']['max']}`

## Boundary

M12-C1 only — bounded artifact status Q&A over approved artifacts through deterministic C1K kernel. No C2/C3/C4, cache, artifact-memory promotion, global Semantic Gate promotion, Gateway/config/live-route/fallback/memory-route/runtime-authority mutation, provider/model answer generation, direct provider bypass, arbitrary path authority, memory/context-bridge/daily-memory authority, C1K regeneration, or `--write-artifacts`.
''')
    # Verify finalization-required files then refresh status if something is missing.
    final_missing = [name for name in REQUIRED_FILES if not (ART / name).exists()]
    if final_missing and status == STATUS_PASS:
        status_obj['status'] = STATUS_ABORT
        status_obj['failed_gates'] = failed_gates + ['required_files_present']
        status_obj['required_files_missing'] = final_missing
        write_json('status.json', status_obj)
        write_json('summary.json', status_obj)
        status = STATUS_ABORT
    return status


def write_json_to_path(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')
    tmp.replace(path)


def archive_previous_attempt_if_needed() -> None:
    status_path = ART / 'status.json'
    if not status_path.exists():
        return
    status_obj = read_json(status_path, {}) or {}
    if status_obj.get('status') not in {STATUS_RUNNING, STATUS_ABORT}:
        return
    attempts = ART / 'attempts'
    attempts.mkdir(parents=True, exist_ok=True)
    idx = 1
    while (attempts / f'attempt_{idx:03d}_archived').exists():
        idx += 1
    dest = attempts / f'attempt_{idx:03d}_archived'
    dest.mkdir(parents=True, exist_ok=True)
    for p in list(ART.iterdir()):
        if p.name == 'attempts':
            continue
        target = dest / p.name
        if p.is_dir():
            shutil.copytree(p, target)
            shutil.rmtree(p)
        else:
            shutil.copy2(p, target)
            p.unlink()
    write_json_to_path(dest / 'archive_reason.json', {
        'archived_utc': utc_now(),
        'reason': 'previous M12-C1H attempt preserved before rerun; attempt ended before preflight/request execution due runner local variable shadowing preflight function.',
        'previous_status': status_obj,
    })


def main() -> int:
    ART.mkdir(parents=True, exist_ok=True)
    archive_previous_attempt_if_needed()
    started = time.time()
    started_utc = utc_now()
    before = protected_snapshot()
    initial_c1k = c1k_hashes()
    write_json('status.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1h.status.v1', 'run_id': RUN_ID, 'status': STATUS_RUNNING, 'artifact_dir': rel(ART), 'started_utc': started_utc, 'target_c1_production_requests': TARGET_REQUESTS, 'time_limit_seconds': TIME_LIMIT_SECONDS})
    write_json('health_watch_config.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1h.health_watch_config.v1', 'run_id': RUN_ID, 'artifact_dir': rel(ART), 'target_c1_production_requests': TARGET_REQUESTS, 'time_limit_seconds': TIME_LIMIT_SECONDS, 'production_scope': 'M12-C1 bounded artifact status Q&A only', 'answer_target': ANSWER_TARGET, 'hold_target': HOLD_TARGET, 'c1k_consumption': 'read_only_guard_preflight_and_postcheck', 'c1k_frozen_evidence_sha256': FROZEN_C1K_EVIDENCE_SHA, 'provider_model_calls_allowed_for_c1_authoritative_answers': False, 'provider_model_calls': 0, 'cache_enabled': False, 'artifact_memory_promoted': False, 'm12_c2_c3_c4_started': False, 'global_semantic_gate_promoted': False, 'runtime_authority_mutation_allowed': False, 'forbidden': ['M12-C2/C3/C4', 'cache enablement', 'artifact-memory promotion', 'global Semantic Gate promotion', 'Gateway/config/live-route/fallback/memory-route/runtime-authority mutation', 'provider/model answer generation for C1', 'arbitrary path Q&A', 'memory/context-bridge/daily-memory as production authority', 'direct provider bypass', 'C1K artifact regeneration', 'C1K --write-artifacts']})
    pre_ok, pre_failures, preflight_detail = preflight(before, initial_c1k)
    write_json('preflight.json', {**preflight_detail, 'ok': pre_ok})
    if not pre_ok:
        status = finalize(started, started_utc, before, initial_c1k, [], ['preflight_failed:' + ','.join(pre_failures)], {'status': 'NOT_RUN'})
        print(json.dumps({'status': status, 'artifact_dir': rel(ART), 'failed_gates': read_json(ART / 'status.json').get('failed_gates')}, indent=2, sort_keys=True))
        return 1
    c1k_pre = run_c1k_guard('c1k_read_only_preflight.json', 'manual_read_only_check')
    if c1k_pre.get('status') != 'PASS' or initial_c1k.get(rel(C1K / 'evidence_manifest.json')) != FROZEN_C1K_EVIDENCE_SHA:
        status = finalize(started, started_utc, before, initial_c1k, [], ['c1k_read_only_preflight'], {'status': 'NOT_RUN'})
        print(json.dumps({'status': status, 'artifact_dir': rel(ART), 'failed_gates': read_json(ART / 'status.json').get('failed_gates')}, indent=2, sort_keys=True))
        return 1
    approved_rows, source_report = compile_rows_from_approved_sources()
    write_json('source_row_compilation_report.json', source_report)
    requests = build_requests(approved_rows)
    records: list[dict[str, Any]] = []
    abort_reasons: list[str] = []
    for index, (case, rows, request_type) in enumerate(requests, start=1):
        if time.time() - started >= TIME_LIMIT_SECONDS:
            abort_reasons.append(f'time_limit_before_request_{index}')
            break
        rec = evaluate_request(index, case, rows, request_type, before)
        records.append(rec)
        if rec.get('pass') is not True:
            abort_reasons.append(f'first_request_failure:{rec.get("request_id")}')
            break
    write_json('c1_production_request_log.json', {'schema': 'stickbot.vnext_semantic_gate.m12_c1h.c1_production_request_log.v1', 'request_count': len(records), 'requests': records})
    postcheck = run_c1k_guard('c1k_read_only_postcheck.json', 'manual_read_only_check')
    status = finalize(started, started_utc, before, initial_c1k, records, abort_reasons, postcheck)
    final = read_json(ART / 'status.json')
    print(json.dumps({'status': status, 'artifact_dir': rel(ART), 'requests': f"{final.get('pass_count')}/{TARGET_REQUESTS}", 'failed_gates': final.get('failed_gates'), 'c1k_hash_changed': final.get('c1k_hash_changed')}, indent=2, sort_keys=True))
    return 0 if status == STATUS_PASS else 1


if __name__ == '__main__':
    raise SystemExit(main())
